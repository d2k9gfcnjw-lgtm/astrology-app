"""FastAPI surface for the engine. Run: uv run uvicorn app.main:app --reload"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .engine import ephemeris
from .engine.chart import calculate_chart
from .engine.ephemeris import EphemerisDataMissing
from .engine.houses import houses_at
from .engine.models import Chart, ChartInput, Houses, Moment, Settings
from .engine.time import FLAG_TEXT, NoTimeZoneError, resolve_moment


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


@app.get("/api/health")
def health():
    try:
        info = ephemeris.info()
    except EphemerisDataMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "status": "ok",
        "ephemeris": {"mode": "swieph", "path": str(info.path), "files": list(info.files), "version": info.swisseph_version},
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
