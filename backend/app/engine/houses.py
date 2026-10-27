"""houses_at(jd_ut, lat, lon, settings): cusps and angles only. This is the location-lock primitive."""
from __future__ import annotations

import swisseph as swe

from . import ephemeris as eph
from .models import Houses, Settings

HSYS = {"placidus": b"P", "whole_sign": b"W"}


def houses_at(jd_ut: float, lat: float, lon: float, settings: Settings) -> Houses:
    eph.info()  # make sure the ephemeris path is set (nutation/obliquity use the files)
    warnings: list[str] = []
    requested = settings.house_system
    used = requested
    if requested == "placidus" and abs(lat) >= settings.placidus_fallback_latitude:
        used = "whole_sign"
        warnings.append(
            f"Placidus is not defined at latitude {lat:.2f}° (limit {settings.placidus_fallback_latitude}°); "
            "Whole Sign houses were used instead."
        )

    flags = 0
    ayanamsa = None
    if settings.zodiac == "sidereal":
        eph.set_sidereal_mode(settings.ayanamsa)
        flags |= eph.FLG_SIDEREAL
        ayanamsa = eph.ayanamsa_ut(jd_ut, settings.ayanamsa)

    cusps_raw, ascmc = swe.houses_ex(jd_ut, lat, lon, HSYS[used], flags)
    cusps = {i + 1: cusps_raw[i] % 360 for i in range(12)}
    asc, mc, armc, vertex = ascmc[0] % 360, ascmc[1] % 360, ascmc[2] % 360, ascmc[3] % 360

    obliquity = eph.obliquity_ut(jd_ut)
    # Declination needs tropical longitude; add the ayanamsa back if sidereal.
    shift = ayanamsa or 0.0
    cusp_dec = {i: eph.ecliptic_to_equatorial((c + shift) % 360, 0.0, obliquity)[1] for i, c in cusps.items()}

    return Houses(
        cusps=cusps,
        cusp_declinations=cusp_dec,
        asc=asc,
        mc=mc,
        dsc=(asc + 180) % 360,
        ic=(mc + 180) % 360,
        vertex=vertex,
        armc=armc,
        obliquity=obliquity,
        system_used=used,
        system_requested=requested,
        warnings=tuple(warnings),
        ayanamsa_degrees=ayanamsa,
    )


def house_of(lon: float, cusps: dict[int, float]) -> int:
    """House number of a longitude: the house whose cusp it has passed and whose next cusp it has not."""
    for h in range(1, 13):
        start = cusps[h]
        end = cusps[1 if h == 12 else h + 1]
        if (lon - start) % 360 < (end - start) % 360:
            return h
    raise ValueError(f"longitude {lon} not placed; cusps {cusps}")
