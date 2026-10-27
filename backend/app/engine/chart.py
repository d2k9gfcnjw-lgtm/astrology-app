"""calculate_chart(): resolve the moment, planets_at + houses_at, then the derived values."""
from __future__ import annotations

from .aspects import find_aspects
from .houses import house_of, houses_at
from .models import BodyPosition, Chart, ChartInput, Houses, Moment, Provenance, Settings, format_longitude
from .planets import planets_at
from .time import resolve_moment


def part_of_fortune(asc: float, sun: float, moon: float, is_day: bool) -> float:
    """Day: ASC + Moon - Sun. Night: ASC + Sun - Moon."""
    return (asc + moon - sun) % 360 if is_day else (asc + sun - moon) % 360


def sun_is_above_horizon(sun_lon: float, asc: float) -> bool:
    """Day birth: the Sun is on the MC side of the ASC-DSC axis (ecliptic longitude between DSC and ASC)."""
    dsc = (asc + 180) % 360
    return (sun_lon - dsc) % 360 < 180


def _fortune_body(lon: float, houses: Houses) -> BodyPosition:
    from . import ephemeris as eph
    shift = houses.ayanamsa_degrees or 0.0
    ra, dec = eph.ecliptic_to_equatorial((lon + shift) % 360, 0.0, houses.obliquity)
    sign, within, text = format_longitude(lon)
    return BodyPosition(lon=lon, lat=0.0, dist=0.0, speed_lon=0.0, speed_lat=0.0, right_ascension=ra,
                        declination=dec, retrograde=False, sign=sign, sign_degrees=within, formatted=text)


def _assemble(moment: Moment, planets: dict[str, BodyPosition], houses: Houses, settings: Settings,
              lat: float, lon: float, relocated_from: tuple[float, float] | None) -> Chart:
    is_day = sun_is_above_horizon(planets["sun"].lon, houses.asc)
    fortune = None
    if settings.include_fortune:
        use_day_formula = True if settings.fortune_formula == "day" else is_day
        fortune = _fortune_body(part_of_fortune(houses.asc, planets["sun"].lon, planets["moon"].lon, use_day_formula), houses)
    placements = {key: house_of(body.lon, houses.cusps) for key, body in planets.items()}
    if fortune is not None:
        placements["fortune"] = house_of(fortune.lon, houses.cusps)
    provenance = Provenance(
        local_time=moment.local_datetime,
        utc_offset=moment.utc_offset,
        timezone=moment.timezone,
        lat=lat,
        lon=lon,
        house_system=houses.system_used,
        zodiac=settings.zodiac,
        ayanamsa=settings.ayanamsa if settings.zodiac == "sidereal" else None,
        node_type=settings.node_type,
        lilith_type=settings.lilith_type,
        fortune_formula=settings.fortune_formula,
        time_flags=moment.flags,
        relocated_from=relocated_from,
    )
    aspects = find_aspects(planets, settings.aspects)
    return Chart(moment=moment, planets=planets, houses=houses, fortune=fortune, planet_houses=placements,
                 is_day=is_day, provenance=provenance, settings=settings, aspects=aspects)


def calculate_chart(subject: ChartInput, settings: Settings) -> Chart:
    moment = resolve_moment(subject.datetime_local, subject.lat, subject.lon,
                            tz_name=subject.timezone, offset_override=subject.utc_offset_override)
    planets = planets_at(moment.jd_ut, settings)
    houses = houses_at(moment.jd_ut, subject.lat, subject.lon, settings)
    return _assemble(moment, planets, houses, settings, subject.lat, subject.lon, None)


def chart_at(jd_ut: float, lat: float, lon: float, settings: Settings) -> Chart:
    """Chart for any instant given as Julian Day (UT): the time-travel primitive. The moment is
    reported in UTC with a +00:00 offset since no civil clock time was entered."""
    from datetime import timedelta
    from .time import moment_from_jd
    moment = moment_from_jd(jd_ut)
    planets = planets_at(jd_ut, settings)
    houses = houses_at(jd_ut, lat, lon, settings)
    return _assemble(moment, planets, houses, settings, lat, lon, None)


def relocate_chart(chart: Chart, lat: float, lon: float) -> Chart:
    """Location lock: same instant and planets, new place. Only houses, angles and placements change."""
    houses = houses_at(chart.moment.jd_ut, lat, lon, chart.settings)
    origin = chart.provenance.relocated_from or (chart.provenance.lat, chart.provenance.lon)
    return _assemble(chart.moment, chart.planets, houses, chart.settings, lat, lon, origin)
