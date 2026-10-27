"""FastAPI surface for the engine. Run: uv run uvicorn app.main:app --reload"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from fastapi import Query, Response

from .cities import DEFAULT_SOURCE, City, CityIndex
from .engine import ephemeris
from .engine.chart import calculate_chart, chart_at
from .engine.ephemeris import EphemerisDataMissing
from .engine.houses import houses_at
from .engine.models import Chart, ChartInput, Houses, Moment, Settings
from .engine.planets import planets_at
from .engine.time import FLAG_TEXT, NoTimeZoneError, resolve_moment
from .storage import ChartLibrary, Subject, SubjectIn

_library: ChartLibrary | None = None
_cities: CityIndex | None = None


def library() -> ChartLibrary:
    global _library
    if _library is None:
        _library = ChartLibrary()
    return _library


def city_index() -> CityIndex:
    global _cities
    if _cities is None:
        _cities = CityIndex()
        if not _cities.is_built():
            if DEFAULT_SOURCE.exists():
                _cities.build_from_file(DEFAULT_SOURCE)
            else:
                raise HTTPException(status_code=503, detail="City data missing. Run `python3 scripts/fetch_data.py`.")
    return _cities


@asynccontextmanager
async def lifespan(app: FastAPI):
    ephemeris.init_ephemeris()  # fail loudly at startup if the .se1 files are missing
    yield


app = FastAPI(title="Astrology workstation engine", version="0.1.0", lifespan=lifespan)


class ChartRequest(BaseModel):
    subject: ChartInput
    settings: Settings = Field(default_factory=Settings)


class HousesRequest(BaseModel):
    jd_ut: float
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    settings: Settings = Field(default_factory=Settings)


class ResolveTimeRequest(BaseModel):
    datetime_local: datetime
    lat: float
    lon: float
    timezone: str | None = None
    utc_offset_override: str | None = None


class ResolveTimeResponse(Moment):
    flag_text: dict[str, str]


class ChartAtRequest(BaseModel):
    jd_ut: float
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    settings: Settings = Field(default_factory=Settings)


class BatchRequest(BaseModel):
    jd_uts: list[float] = Field(max_length=2000)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    settings: Settings = Field(default_factory=Settings)


class Keyframe(BaseModel):
    jd_ut: float
    planets: dict[str, float]      # longitude only
    speeds: dict[str, float]
    cusps: list[float]
    asc: float
    mc: float
    system_used: str


class CityOut(BaseModel):
    geonameid: int
    name: str
    country: str
    admin1: str
    population: int
    lat: float
    lon: float
    timezone: str
    label: str


@app.get("/api/health")
def health():
    try:
        info = ephemeris.info()
    except EphemerisDataMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    lib = library()
    return {
        "status": "ok",
        "ephemeris": {"mode": "swieph", "path": str(info.path), "files": list(info.files), "version": info.swisseph_version},
        "library": {"db_path": str(lib.db_path), "key_path": str(lib.key_path)},
        "cities": {"source_present": DEFAULT_SOURCE.exists()},
    }


@app.post("/api/time/resolve", response_model=ResolveTimeResponse)
def resolve_time(req: ResolveTimeRequest):
    try:
        m = resolve_moment(req.datetime_local, req.lat, req.lon, req.timezone, req.utc_offset_override)
    except (NoTimeZoneError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ResolveTimeResponse(**m.model_dump(), flag_text={f: FLAG_TEXT[f] for f in m.flags})


@app.post("/api/chart", response_model=Chart)
def chart(req: ChartRequest):
    try:
        return calculate_chart(req.subject, req.settings)
    except (NoTimeZoneError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EphemerisDataMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/houses", response_model=Houses)
def houses(req: HousesRequest):
    try:
        return houses_at(req.jd_ut, req.lat, req.lon, req.settings)
    except EphemerisDataMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/chart/at", response_model=Chart)
def chart_at_instant(req: ChartAtRequest):
    try:
        return chart_at(req.jd_ut, req.lat, req.lon, req.settings)
    except EphemerisDataMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/chart/at/batch")
def chart_at_batch(req: BatchRequest) -> dict[str, list[Keyframe]]:
    """Compact keyframes for spin mode: longitudes, speeds, cusps and angles for many instants in one call."""
    frames: list[Keyframe] = []
    try:
        for jd in req.jd_uts:
            p = planets_at(jd, req.settings)
            h = houses_at(jd, req.lat, req.lon, req.settings)
            frames.append(Keyframe(jd_ut=jd, planets={k: v.lon for k, v in p.items()}, speeds={k: v.speed_lon for k, v in p.items()},
                                   cusps=[h.cusps[i] for i in range(1, 13)], asc=h.asc, mc=h.mc, system_used=h.system_used))
    except EphemerisDataMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"frames": frames}


def _city_out(c: City) -> CityOut:
    region = f", {c.admin1}" if c.admin1 and c.country in ("US", "CA", "AU") else ""
    return CityOut(geonameid=c.geonameid, name=c.name, country=c.country, admin1=c.admin1, population=c.population,
                   lat=c.lat, lon=c.lon, timezone=c.timezone, label=f"{c.name}{region}, {c.country}")


@app.get("/api/cities", response_model=list[CityOut])
def cities(q: str = Query(min_length=1, max_length=80), limit: int = Query(10, ge=1, le=50)):
    return [_city_out(c) for c in city_index().search(q, limit=limit)]


@app.get("/api/subjects", response_model=list[Subject])
def list_subjects(q: str | None = None, tag: str | None = None, include_deleted: bool = False):
    return library().list(query=q, tag=tag, include_deleted=include_deleted)


@app.get("/api/subjects/tags", response_model=list[str])
def list_tags():
    return library().tags()


@app.post("/api/subjects", response_model=Subject, status_code=201)
def create_subject(s: SubjectIn):
    return library().create(s)


@app.get("/api/subjects/{sid}", response_model=Subject)
def get_subject(sid: str):
    try:
        return library().get(sid)
    except KeyError:
        raise HTTPException(status_code=404, detail="subject not found")


@app.put("/api/subjects/{sid}", response_model=Subject)
def update_subject(sid: str, s: SubjectIn):
    try:
        return library().update(sid, s)
    except KeyError:
        raise HTTPException(status_code=404, detail="subject not found")


@app.delete("/api/subjects/{sid}", status_code=204)
def delete_subject(sid: str):
    try:
        library().delete(sid)
    except KeyError:
        raise HTTPException(status_code=404, detail="subject not found")
    return Response(status_code=204)


@app.post("/api/subjects/{sid}/restore", response_model=Subject)
def restore_subject(sid: str):
    try:
        return library().restore(sid)
    except KeyError:
        raise HTTPException(status_code=404, detail="subject not found")


@app.get("/api/subjects/{sid}/chart", response_model=Chart)
def subject_chart(sid: str, lat: float | None = None, lon: float | None = None):
    """The subject's chart; pass lat and lon to relocate it (location lock)."""
    try:
        s = library().get(sid)
    except KeyError:
        raise HTTPException(status_code=404, detail="subject not found")
    settings = Settings(**s.settings) if s.settings else Settings()
    try:
        chart = calculate_chart(ChartInput(datetime_local=s.datetime_local, lat=s.lat, lon=s.lon, timezone=s.timezone,
                                           utc_offset_override=s.utc_offset_override), settings)
    except (NoTimeZoneError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if lat is not None and lon is not None:
        from .engine.chart import relocate_chart
        chart = relocate_chart(chart, lat, lon)
    return chart
