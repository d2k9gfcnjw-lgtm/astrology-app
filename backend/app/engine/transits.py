"""Transit hits, ingresses, stations and the year-ahead report (solar return to solar return)."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from .models import Chart, Settings, TransitSettings
from .solver import Track, jd_from_utc
from .time import moment_from_jd

ASPECT_ANGLES = {"conjunction": 0.0, "opposition": 180.0, "trine": 120.0, "square": 90.0, "sextile": 60.0,
                 "semisextile": 30.0, "semisquare": 45.0, "sesquiquadrate": 135.0, "quincunx": 150.0}
SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
PAD_DAYS = {"moon": 5, "sun": 30, "mercury": 60, "venus": 90, "mars": 180, "jupiter": 300, "saturn": 500,
            "uranus": 700, "neptune": 900, "pluto": 1000, "chiron": 600, "node": 300, "lilith": 300}


EDGE = 1 / 86400  # one second: a window is [start, end) with the end hit solved separately


def in_window(jd: float, jd0: float, jd1: float) -> bool:
    return jd0 - EDGE <= jd < jd1 - EDGE


class Hit(BaseModel):
    model_config = ConfigDict(frozen=True)
    jd_ut: float
    utc_datetime: str
    local_datetime: str
    body: str
    aspect: str
    angle: float
    natal_point: str
    natal_lon: float
    transit_lon: float
    retrograde: bool
    pass_index: int
    pass_count: int
    orb: float
    orb_enter_jd: float | None
    orb_exit_jd: float | None
    orb_enter_local: str | None
    orb_exit_local: str | None


class Ingress(BaseModel):
    model_config = ConfigDict(frozen=True)
    jd_ut: float
    utc_datetime: str
    local_datetime: str
    body: str
    kind: str              # "house" or "sign"
    entered: str           # "7" for a house, "Sco" for a sign
    retrograde: bool
    lon: float


class StationEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    jd_ut: float
    utc_datetime: str
    local_datetime: str
    body: str
    kind: str
    lon: float
    near: list[dict]       # [{"natal_point": "sun", "orb": 0.8}]


class YearAhead(BaseModel):
    model_config = ConfigDict(frozen=True)
    year: int
    jd_start: float
    jd_end: float
    utc_start: str
    utc_end: str
    local_start: str
    local_end: str
    timezone: str | None
    settings: TransitSettings
    hits: list[Hit]
    ingresses: list[Ingress]
    stations: list[StationEvent]
    counts: dict[str, int]


def _utc_iso(jd: float) -> str:
    return moment_from_jd(jd).utc_datetime.replace(tzinfo=None).isoformat(timespec="seconds")


def _local_iso(jd: float, tz: str | None) -> str:
    dt = moment_from_jd(jd).utc_datetime
    if tz:
        dt = dt.astimezone(ZoneInfo(tz))
    return dt.isoformat(timespec="minutes")


def natal_points(chart: Chart, ts: TransitSettings) -> dict[str, float]:
    pool: dict[str, float] = {k: v.lon for k, v in chart.planets.items()}
    pool.update({"asc": chart.houses.asc, "dsc": chart.houses.dsc, "mc": chart.houses.mc, "ic": chart.houses.ic})
    if chart.fortune is not None:
        pool["fortune"] = chart.fortune.lon
    for i in range(1, 13):
        pool[f"cusp_{i}"] = chart.houses.cusps[i]
    return {k: pool[k] for k in ts.natal_points if k in pool}


def solar_return_instant(chart: Chart, year: int) -> float:
    """The instant in `year` when the transiting Sun is exactly on the natal Sun's degree."""
    birth = chart.moment.utc_datetime
    centre = jd_from_utc(datetime(year, birth.month, min(birth.day, 28), birth.hour, birth.minute))
    for pad in (3, 10, 40):
        hits = Track("sun", centre - pad, centre + pad, chart.settings).crossings(chart.planets["sun"].lon)
        if hits:
            return min(hits, key=lambda h: abs(h.jd_ut - centre)).jd_ut
    raise ValueError(f"no solar return found in {year}")


def _span(track: Track, target: float, orb: float, jd_hit: float) -> tuple[float | None, float | None]:
    edges = sorted(c.jd_ut for c in track.crossings((target - orb) % 360) + track.crossings((target + orb) % 360))
    before = [e for e in edges if e < jd_hit - 1e-6]
    after = [e for e in edges if e > jd_hit + 1e-6]
    return (before[-1] if before else None), (after[0] if after else None)


def transit_hits(chart: Chart, ts: TransitSettings, jd0: float, jd1: float, timezone_name: str | None = None) -> list[Hit]:
    points = natal_points(chart, ts)
    out: list[Hit] = []
    for body in ts.bodies:
        pad = PAD_DAYS.get(body, 300)
        track = Track(body, jd0 - pad, jd1 + pad, chart.settings)
        orb = ts.orbs.get(body, 2.0)
        for point, plon in points.items():
            for aspect in ts.aspects:
                angle = ASPECT_ANGLES[aspect]
                targets = sorted({(plon + angle) % 360, (plon - angle) % 360})
                for target in targets:
                    for c in track.crossings(target):
                        if not in_window(c.jd_ut, jd0, jd1):
                            continue
                        enter, exit_ = _span(track, target, orb, c.jd_ut)
                        out.append(Hit(
                            jd_ut=c.jd_ut, utc_datetime=_utc_iso(c.jd_ut), local_datetime=_local_iso(c.jd_ut, timezone_name),
                            body=body, aspect=aspect, angle=angle, natal_point=point, natal_lon=plon, transit_lon=target,
                            retrograde=c.retrograde, pass_index=c.pass_index, pass_count=c.pass_count, orb=orb,
                            orb_enter_jd=enter, orb_exit_jd=exit_,
                            orb_enter_local=_local_iso(enter, timezone_name) if enter else None,
                            orb_exit_local=_local_iso(exit_, timezone_name) if exit_ else None,
                        ))
    out.sort(key=lambda h: h.jd_ut)
    return _dedupe_axes(out)


AXIS_PARTNER = {"asc": "dsc", "dsc": "asc", "mc": "ic", "ic": "mc"}
for _i in range(1, 13):
    AXIS_PARTNER[f"cusp_{_i}"] = f"cusp_{(_i + 5) % 12 + 1}"
PREFERRED_POINT = {"dsc": "asc", "ic": "mc"}


def _dedupe_axes(hits: list[Hit]) -> list[Hit]:
    """A square to the AC is the same instant as a square to the DC, a conjunction to the DC is an
    opposition to the AC: keep one row per instant and body, preferring AC/MC and the conjunction."""
    keep: list[Hit] = []
    for h in hits:
        dup = None
        for k in keep:
            if k.body == h.body and abs(k.jd_ut - h.jd_ut) < EDGE and AXIS_PARTNER.get(k.natal_point) == h.natal_point:
                dup = k
                break
        if dup is None:
            keep.append(h)
            continue
        rank = lambda x: (x.aspect != "conjunction", x.natal_point in PREFERRED_POINT, x.natal_point.startswith("cusp_") and int(x.natal_point[5:]) > 6)
        if rank(h) < rank(dup):
            keep[keep.index(dup)] = h
    return keep


def ingresses(chart: Chart, ts: TransitSettings, jd0: float, jd1: float, timezone_name: str | None = None) -> list[Ingress]:
    out: list[Ingress] = []
    for body in ts.bodies:
        track = Track(body, jd0, jd1, chart.settings)
        if ts.include_ingresses:
            for h in range(1, 13):
                for c in track.crossings(chart.houses.cusps[h]):
                    if not in_window(c.jd_ut, jd0, jd1):
                        continue
                    entered = h if not c.retrograde else (12 if h == 1 else h - 1)
                    out.append(Ingress(jd_ut=c.jd_ut, utc_datetime=_utc_iso(c.jd_ut), local_datetime=_local_iso(c.jd_ut, timezone_name),
                                       body=body, kind="house", entered=str(entered), retrograde=c.retrograde, lon=c.lon))
        if ts.include_sign_ingresses:
            for k in range(12):
                for c in track.crossings(k * 30.0):
                    if not in_window(c.jd_ut, jd0, jd1):
                        continue
                    entered = SIGNS[k] if not c.retrograde else SIGNS[(k - 1) % 12]
                    out.append(Ingress(jd_ut=c.jd_ut, utc_datetime=_utc_iso(c.jd_ut), local_datetime=_local_iso(c.jd_ut, timezone_name),
                                       body=body, kind="sign", entered=entered, retrograde=c.retrograde, lon=c.lon))
    out.sort(key=lambda i: i.jd_ut)
    return out


def station_events(chart: Chart, ts: TransitSettings, jd0: float, jd1: float, timezone_name: str | None = None) -> list[StationEvent]:
    points = natal_points(chart, ts)
    out: list[StationEvent] = []
    for body in ts.bodies:
        if body in ("sun", "moon"):
            continue
        orb = ts.orbs.get(body, 2.0)
        for st in Track(body, jd0, jd1, chart.settings).stations():
            if not in_window(st.jd_ut, jd0, jd1):
                continue
            near = []
            for point, plon in points.items():
                for aspect in ts.aspects:
                    angle = ASPECT_ANGLES[aspect]
                    sep = abs(((st.lon - plon + 180) % 360) - 180)
                    d = abs(sep - angle)
                    if d <= orb:
                        near.append({"natal_point": point, "aspect": aspect, "orb": round(d, 2)})
            out.append(StationEvent(jd_ut=st.jd_ut, utc_datetime=_utc_iso(st.jd_ut), local_datetime=_local_iso(st.jd_ut, timezone_name),
                                    body=body, kind=st.kind, lon=st.lon, near=near))
    out.sort(key=lambda s: s.jd_ut)
    return out


def year_ahead(chart: Chart, year: int, ts: TransitSettings, timezone: str | None = None) -> YearAhead:
    jd0 = solar_return_instant(chart, year)
    jd1 = solar_return_instant(chart, year + 1)
    hits = transit_hits(chart, ts, jd0, jd1, timezone)
    ing = ingresses(chart, ts, jd0, jd1, timezone) if (ts.include_ingresses or ts.include_sign_ingresses) else []
    sts = station_events(chart, ts, jd0, jd1, timezone) if ts.include_stations else []
    counts: dict[str, int] = {b: 0 for b in ts.bodies}
    for h in hits:
        counts[h.body] = counts.get(h.body, 0) + 1
    return YearAhead(year=year, jd_start=jd0, jd_end=jd1, utc_start=_utc_iso(jd0), utc_end=_utc_iso(jd1),
                     local_start=_local_iso(jd0, timezone), local_end=_local_iso(jd1, timezone), timezone=timezone,
                     settings=ts, hits=hits, ingresses=ing, stations=sts, counts=counts)
