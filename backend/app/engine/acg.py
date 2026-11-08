"""Astrocartography: planetary angle lines, parans, and what is within orb at a place.

In mundo (default): the body itself is on the horizon or meridian, like astro.com's AstroClick Travel.
Zodiacal: the body's ecliptic degree (latitude zero) is on the angle. Geocentric, no refraction.
Verified 8 Nov 2026 against three AstroClick readouts (56, 15, 189 km) to within 0.5 km; AstroClick uses the Mean Node.
"""
from __future__ import annotations

import math

import numpy as np
import swisseph as swe
from pydantic import BaseModel, ConfigDict, Field

from . import ephemeris as eph
from .chart import chart_at
from .models import Chart, Settings
from .planets import planets_at
from .solver import body_id

PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
ANGLES = ("asc", "dsc", "mc", "ic")
EARTH_KM = 6371.0
LAT_STEP = 0.5


class AcgSettings(BaseModel):
    model_config = ConfigDict(frozen=True)
    bodies: list[str] = Field(default_factory=lambda: list(PLANETS))
    angles: list[str] = Field(default_factory=lambda: list(ANGLES))
    method: str = "mundo"            # or "zodiacal"
    orb_km: float = 300.0            # owner 8 Nov 2026
    paran_orb_lat: float = 1.0
    include_parans: bool = True


class Line(BaseModel):
    body: str
    angle: str
    points: list[list[tuple[float, float]]]   # segments of (lon, lat), split at the antimeridian


class Paran(BaseModel):
    body_a: str
    angle_a: str
    body_b: str
    angle_b: str
    lat: float


class LineHit(BaseModel):
    body: str
    angle: str
    km: float
    deg: float


class AtPlace(BaseModel):
    chart: Chart
    lines: list[LineHit]
    parans: list[Paran]
    orb_km: float


def gmst_degrees(jd_ut: float) -> float:
    return (swe.sidtime(jd_ut) * 15.0) % 360


def _wrap180(x: float) -> float:
    return ((x + 180) % 360) - 180


def _equatorial(jd_ut: float, settings: Settings, acg: AcgSettings) -> dict[str, tuple[float, float]]:
    """(right ascension, declination) per body for the chosen method."""
    out = {}
    planets = planets_at(jd_ut, settings)
    if acg.method == "zodiacal":
        eps = eph.obliquity_ut(jd_ut)
        for b in acg.bodies:
            if b not in planets:
                continue
            xx, _ = eph.calc_ut(jd_ut, body_id(b, settings), 0)   # tropical longitude whatever the zodiac setting
            out[b] = eph.ecliptic_to_equatorial(xx[0] % 360, 0.0, eps)
    else:
        for b in acg.bodies:
            if b in planets:
                out[b] = (planets[b].right_ascension, planets[b].declination)
    return out


def angular_lst(ra: float, dec: float, angle: str, lat: float) -> float | None:
    """Local sidereal time (degrees) at which a body with (ra, dec) is on the angle at this latitude."""
    if angle == "mc":
        return ra % 360
    if angle == "ic":
        return (ra + 180) % 360
    x = -math.tan(math.radians(lat)) * math.tan(math.radians(dec))
    if abs(x) > 1:
        return None
    h0 = math.degrees(math.acos(x))
    return (ra - h0) % 360 if angle == "asc" else (ra + h0) % 360


def _segments(points: list[tuple[float, float] | None]) -> list[list[tuple[float, float]]]:
    segs: list[list[tuple[float, float]]] = []
    cur: list[tuple[float, float]] = []
    for p in points:
        if p is None:
            if cur:
                segs.append(cur)
            cur = []
            continue
        if cur and abs(p[0] - cur[-1][0]) > 180:
            segs.append(cur)
            cur = []
        cur.append(p)
    if cur:
        segs.append(cur)
    return segs


def lines_at(jd_ut: float, settings: Settings, acg: AcgSettings) -> list[Line]:
    gmst = gmst_degrees(jd_ut)
    lats = np.arange(-89.5, 89.5 + 1e-9, LAT_STEP)
    out: list[Line] = []
    for body, (ra, dec) in _equatorial(jd_ut, settings, acg).items():
        for angle in acg.angles:
            if angle in ("mc", "ic"):
                lon = _wrap180((angular_lst(ra, dec, angle, 0.0) or 0.0) - gmst)
                out.append(Line(body=body, angle=angle, points=[[(lon, -89.5), (lon, 89.5)]]))
                continue
            pts: list[tuple[float, float] | None] = []
            for lat in lats:
                lst = angular_lst(ra, dec, angle, float(lat))
                pts.append(None if lst is None else (_wrap180(lst - gmst), float(lat)))
            out.append(Line(body=body, angle=angle, points=_segments(pts)))
    return out


def parans_at(jd_ut: float, settings: Settings, acg: AcgSettings) -> list[Paran]:
    eq = _equatorial(jd_ut, settings, acg)
    bodies = [b for b in acg.bodies if b in eq]
    lats = np.arange(-89.0, 89.0 + 1e-9, LAT_STEP)
    out: list[Paran] = []
    for i, a in enumerate(bodies):
        for b in bodies[i + 1:]:
            for aa in ANGLES:
                for ab in ANGLES:
                    if aa in ("mc", "ic") and ab in ("mc", "ic"):
                        continue
                    def f(lat: float) -> float | None:
                        la = angular_lst(*eq[a], aa, lat)
                        lb = angular_lst(*eq[b], ab, lat)
                        return None if la is None or lb is None else _wrap180(la - lb)
                    prev = None
                    for lat in lats:
                        v = f(float(lat))
                        if v is not None and prev is not None and prev[1] * v <= 0 and abs(v - prev[1]) < 180:
                            lo, hi = prev[0], float(lat)
                            flo = prev[1]
                            for _ in range(40):
                                mid = (lo + hi) / 2
                                fm = f(mid)
                                if fm is None:
                                    break
                                if (fm > 0) == (flo > 0):
                                    lo, flo = mid, fm
                                else:
                                    hi = mid
                            out.append(Paran(body_a=a, angle_a=aa, body_b=b, angle_b=ab, lat=round((lo + hi) / 2, 4)))
                        prev = None if v is None else (float(lat), v)
    out.sort(key=lambda p: p.lat)
    return out


def _unit(lat: float, lon: float) -> np.ndarray:
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])


def distance_to_line_km(points: list[list[tuple[float, float]]], lat: float, lon: float) -> float:
    """Great-circle distance from a place to a polyline of (lon, lat) points."""
    p = _unit(lat, lon)
    best = math.inf
    for seg in points:
        for (lon1, lat1), (lon2, lat2) in zip(seg, seg[1:]):
            a, b = _unit(lat1, lon1), _unit(lat2, lon2)
            n = np.cross(a, b)
            nn = np.linalg.norm(n)
            if nn < 1e-12:
                continue
            n = n / nn
            # projection of p onto the great circle plane; check it lies between a and b
            proj = p - np.dot(p, n) * n
            proj = proj / np.linalg.norm(proj)
            inside = np.dot(np.cross(a, proj), n) >= -1e-9 and np.dot(np.cross(proj, b), n) >= -1e-9
            if inside:
                d = math.asin(max(-1.0, min(1.0, abs(float(np.dot(p, n))))))
            else:
                d = min(math.acos(max(-1.0, min(1.0, float(np.dot(p, a))))), math.acos(max(-1.0, min(1.0, float(np.dot(p, b))))))
            best = min(best, d)
        if len(seg) == 1:
            a = _unit(seg[0][1], seg[0][0])
            best = min(best, math.acos(max(-1.0, min(1.0, float(np.dot(p, a))))))
    return best * EARTH_KM


def at_place(jd_ut: float, lat: float, lon: float, settings: Settings, acg: AcgSettings) -> AtPlace:
    hits = []
    for line in lines_at(jd_ut, settings, acg):
        km = distance_to_line_km(line.points, lat, lon)
        if km <= acg.orb_km:
            hits.append(LineHit(body=line.body, angle=line.angle, km=round(km, 1), deg=round(km / (EARTH_KM * math.pi / 180), 2)))
    hits.sort(key=lambda h: h.km)
    parans = [p for p in parans_at(jd_ut, settings, acg) if abs(p.lat - lat) <= acg.paran_orb_lat] if acg.include_parans else []
    return AtPlace(chart=chart_at(jd_ut, lat, lon, settings), lines=hits, parans=parans, orb_km=acg.orb_km)
