"""Exact-time solver: when a body reaches a longitude, and when it stations.

Bodies are sampled on a step suited to their speed, split at stations so motion is monotonic
within each segment, and every sign change of the angular distance is refined by bisection to
well under one second. Retrograde passes over the same degree are numbered (k of n).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

from . import ephemeris as eph
from .models import Settings

BODY_IDS = {
    "sun": eph.SUN, "moon": eph.MOON, "mercury": eph.MERCURY, "venus": eph.VENUS, "mars": eph.MARS,
    "jupiter": eph.JUPITER, "saturn": eph.SATURN, "uranus": eph.URANUS, "neptune": eph.NEPTUNE, "pluto": eph.PLUTO,
    "chiron": eph.CHIRON,
}
STEP_DAYS = {"moon": 0.1, "sun": 0.5, "mercury": 0.25, "venus": 0.25, "mars": 0.5, "jupiter": 1.0, "saturn": 1.0,
             "uranus": 2.0, "neptune": 2.0, "pluto": 2.0, "chiron": 1.0, "node": 1.0, "lilith": 1.0}
PRECISION_DAYS = 1e-6  # about 0.09 second
# How far around an instant the drag solver looks for previous and next crossings.
PAD_SOLVE_DAYS = {"moon": 45, "sun": 400, "mercury": 400, "venus": 600, "mars": 900, "jupiter": 800, "saturn": 1100,
                  "uranus": 1500, "neptune": 1800, "pluto": 2200, "chiron": 1800, "node": 400, "lilith": 400}


@dataclass(frozen=True)
class Crossing:
    jd_ut: float
    lon: float
    retrograde: bool
    pass_index: int
    pass_count: int


@dataclass(frozen=True)
class Station:
    jd_ut: float
    kind: str  # "retrograde" (turning backward) or "direct"
    lon: float


def jd_from_utc(dt: datetime) -> float:
    return eph.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + (dt.second + dt.microsecond / 1e6) / 3600)


def body_id(key: str, settings: Settings) -> int:
    if key == "node":
        return eph.TRUE_NODE if settings.node_type == "true" else eph.MEAN_NODE
    if key == "lilith":
        return eph.MEAN_APOG if settings.lilith_type == "mean" else eph.OSCU_APOG
    return BODY_IDS[key]


def _flags(settings: Settings) -> int:
    if settings.zodiac == "sidereal":
        eph.set_sidereal_mode(settings.ayanamsa)
        return eph.FLG_SIDEREAL
    return 0


def lon_speed(key: str, jd: float, settings: Settings) -> tuple[float, float]:
    xx, _ = eph.calc_ut(jd, body_id(key, settings), _flags(settings))
    return xx[0] % 360, xx[3]


class Track:
    """A body sampled over a window: the shared input for every crossing and station search."""

    def __init__(self, key: str, jd0: float, jd1: float, settings: Settings):
        self.key, self.settings = key, settings
        step = STEP_DAYS[key]
        n = max(2, int(np.ceil((jd1 - jd0) / step)) + 1)
        self.jds = np.linspace(jd0, jd1, n)
        lons, speeds = [], []
        for j in self.jds:
            lo, sp = lon_speed(key, float(j), settings)
            lons.append(lo)
            speeds.append(sp)
        self.lons = np.array(lons)
        self.speeds = np.array(speeds)
        self._stations: list[Station] | None = None

    # -- stations -------------------------------------------------------
    def stations(self) -> list[Station]:
        if self._stations is not None:
            return self._stations
        out: list[Station] = []
        s = self.speeds
        for i in range(len(s) - 1):
            if s[i] == 0 or (s[i] > 0) == (s[i + 1] > 0):
                continue
            a, b = float(self.jds[i]), float(self.jds[i + 1])
            sa = float(s[i])
            while b - a > PRECISION_DAYS:
                m = (a + b) / 2
                _, sm = lon_speed(self.key, m, self.settings)
                if (sm > 0) == (sa > 0):
                    a, sa = m, sm
                else:
                    b = m
            jd = (a + b) / 2
            lon, _ = lon_speed(self.key, jd, self.settings)
            out.append(Station(jd_ut=jd, kind="retrograde" if sa > 0 else "direct", lon=lon))
        self._stations = out
        return out

    # -- crossings -----------------------------------------------------
    def crossings(self, target: float) -> list[Crossing]:
        d = ((self.lons - target + 180) % 360) - 180
        raw: list[tuple[float, bool]] = []
        for i in range(len(d) - 1):
            d0, d1 = float(d[i]), float(d[i + 1])
            if d0 == 0:
                raw.append((float(self.jds[i]), bool(self.speeds[i] < 0)))
                continue
            if (d0 > 0) == (d1 > 0) or abs(d1 - d0) > 180:
                continue
            a, b = float(self.jds[i]), float(self.jds[i + 1])
            da = d0
            while b - a > PRECISION_DAYS:
                m = (a + b) / 2
                lm, _ = lon_speed(self.key, m, self.settings)
                dm = ((lm - target + 180) % 360) - 180
                if (dm > 0) == (da > 0):
                    a, da = m, dm
                else:
                    b = m
            jd = (a + b) / 2
            _, sp = lon_speed(self.key, jd, self.settings)
            raw.append((jd, sp < 0))
        if d[-1] == 0:
            raw.append((float(self.jds[-1]), bool(self.speeds[-1] < 0)))
        # A degree crossed twice within one step (just past a station) hides from the sign test:
        # look at steps that contain a station and both ends on the same side but very close.
        for st in self.stations():
            if any(abs(st.jd_ut - j) < STEP_DAYS[self.key] * 1.5 for j, _ in raw):
                continue
            dist = ((st.lon - target + 180) % 360) - 180
            if abs(dist) < 1.0:
                # the body touched the target before turning: solve on each side of the station
                step = STEP_DAYS[self.key]
                for side in (-1, 1):
                    a, b = (st.jd_ut - 3 * step, st.jd_ut) if side < 0 else (st.jd_ut, st.jd_ut + 3 * step)
                    la, _ = lon_speed(self.key, a, self.settings)
                    lb, _ = lon_speed(self.key, b, self.settings)
                    da_ = ((la - target + 180) % 360) - 180
                    db_ = ((lb - target + 180) % 360) - 180
                    if (da_ > 0) == (db_ > 0):
                        continue
                    while b - a > PRECISION_DAYS:
                        m = (a + b) / 2
                        lm, _ = lon_speed(self.key, m, self.settings)
                        dm = ((lm - target + 180) % 360) - 180
                        if (dm > 0) == (da_ > 0):
                            a, da_ = m, dm
                        else:
                            b = m
                    jd = (a + b) / 2
                    if self.jds[0] <= jd <= self.jds[-1] and not any(abs(jd - j) < 1e-4 for j, _ in raw):
                        _, sp = lon_speed(self.key, jd, self.settings)
                        raw.append((jd, sp < 0))
        raw.sort()
        return _number_passes(raw, target)


def _number_passes(raw: list[tuple[float, bool]], target: float) -> list[Crossing]:
    """Consecutive crossings with alternating direction belong to one retrograde loop."""
    groups: list[list[tuple[float, bool]]] = []
    for item in raw:
        if groups and groups[-1][-1][1] != item[1]:
            groups[-1].append(item)
        else:
            groups.append([item])
    out: list[Crossing] = []
    for g in groups:
        for k, (jd, retro) in enumerate(g, start=1):
            out.append(Crossing(jd_ut=jd, lon=target % 360, retrograde=retro, pass_index=k, pass_count=len(g)))
    return out


def crossings(key: str, target: float, jd0: float, jd1: float, settings: Settings) -> list[Crossing]:
    """Every instant in [jd0, jd1) when the body is exactly on `target` longitude."""
    hits = Track(key, jd0, jd1, settings).crossings(target)
    return [h for h in hits if h.jd_ut < jd1]


def stations(key: str, jd0: float, jd1: float, settings: Settings) -> list[Station]:
    return [s for s in Track(key, jd0, jd1, settings).stations() if s.jd_ut < jd1]
