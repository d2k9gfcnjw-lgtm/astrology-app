"""planets_at(jd_ut, settings): positions of every body. Location is deliberately not an input."""
from __future__ import annotations

from . import ephemeris as eph
from .models import BodyPosition, Settings, format_longitude

CORE_BODIES = (
    ("sun", eph.SUN), ("moon", eph.MOON), ("mercury", eph.MERCURY), ("venus", eph.VENUS),
    ("mars", eph.MARS), ("jupiter", eph.JUPITER), ("saturn", eph.SATURN), ("uranus", eph.URANUS),
    ("neptune", eph.NEPTUNE), ("pluto", eph.PLUTO),
)


def _zodiac_flags(settings: Settings) -> int:
    if settings.zodiac == "sidereal":
        eph.set_sidereal_mode(settings.ayanamsa)
        return eph.FLG_SIDEREAL
    return 0


def _body(jd_ut: float, body_id: int, flags: int, variant: str | None = None) -> BodyPosition:
    ecl, _ = eph.calc_ut(jd_ut, body_id, flags)
    # Equatorial coordinates are always computed tropically (right ascension has no ayanamsa).
    equ, _ = eph.calc_ut(jd_ut, body_id, (flags & ~eph.FLG_SIDEREAL) | eph.FLG_EQUATORIAL)
    lon = ecl[0] % 360
    sign, within, text = format_longitude(lon)
    return BodyPosition(
        lon=lon,
        lat=ecl[1],
        dist=ecl[2],
        speed_lon=ecl[3],
        speed_lat=ecl[4],
        right_ascension=equ[0] % 360,
        declination=equ[1],
        retrograde=ecl[3] < 0,
        sign=sign,
        sign_degrees=within,
        formatted=text,
        variant=variant,
    )


def planets_at(jd_ut: float, settings: Settings) -> dict[str, BodyPosition]:
    """Longitudes, latitudes, declinations and speeds for the chart's bodies at one instant (UT)."""
    flags = _zodiac_flags(settings)
    out: dict[str, BodyPosition] = {key: _body(jd_ut, body_id, flags) for key, body_id in CORE_BODIES}
    if settings.include_node:
        node_id = eph.TRUE_NODE if settings.node_type == "true" else eph.MEAN_NODE
        out["node"] = _body(jd_ut, node_id, flags, variant=settings.node_type)
    if settings.include_chiron:
        out["chiron"] = _body(jd_ut, eph.CHIRON, flags)
    if settings.include_lilith:
        lilith_id = eph.MEAN_APOG if settings.lilith_type == "mean" else eph.OSCU_APOG
        out["lilith"] = _body(jd_ut, lilith_id, flags, variant=settings.lilith_type)
    return out
