"""Local time -> UT, Julian Day, and flags for offsets that deserve a second look.

Policy (CLAUDE.md): never guess a time zone silently. The offset actually used
is always reported; a manual override always wins; births before 1970 and in
wartime years are flagged "check offset".
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from timezonefinder import TimezoneFinder

from . import ephemeris
from .models import Moment

WARTIME_RANGES = ((1914, 1919), (1939, 1947))  # inclusive; every country, deliberately broad
PRE_1970_BOUNDARY = 1970

FLAG_PRE_1970 = "pre_1970"
FLAG_WARTIME = "wartime"
FLAG_AMBIGUOUS = "ambiguous_local_time"
FLAG_NONEXISTENT = "nonexistent_local_time"
FLAG_NO_ZONE = "no_zone_for_location"
FLAG_OVERRIDDEN = "offset_overridden"

FLAG_TEXT = {
    FLAG_PRE_1970: "Born before 1970: check the offset against a historical source (local mean time, old DST rules).",
    FLAG_WARTIME: "Wartime year: many countries used special daylight or double summer time. Check the offset.",
    FLAG_AMBIGUOUS: "This clock time happened twice (clocks went back). The first occurrence was used; override if needed.",
    FLAG_NONEXISTENT: "This clock time never happened (clocks jumped forward). Check the time or the offset.",
    FLAG_NO_ZONE: "No time zone is defined at these coordinates (ocean?). The offset you gave was used.",
    FLAG_OVERRIDDEN: "A manual UTC offset was used instead of the time zone's own offset.",
}

_finder: TimezoneFinder | None = None


class NoTimeZoneError(ValueError):
    """No usable time zone; the caller must supply a UTC offset."""


def _timezone_finder() -> TimezoneFinder:
    global _finder
    if _finder is None:
        _finder = TimezoneFinder(in_memory=True)
    return _finder


def zone_name_for(lat: float, lon: float) -> str | None:
    """IANA zone at the coordinates, or None at sea. Nautical 'Etc/GMT+n' zones are not real local
    time zones, so they count as no zone: the caller must state the offset."""
    name = _timezone_finder().timezone_at(lat=lat, lng=lon)
    if name is None or name.startswith("Etc/"):
        return None
    return name


_OFFSET_RE = re.compile(r"^([+-])(\d{1,2})(?::?(\d{2}))?(?::?(\d{2}))?$")


def parse_offset(text: str | timedelta) -> timedelta:
    if isinstance(text, timedelta):
        return text
    m = _OFFSET_RE.match(text.strip())
    if not m:
        raise ValueError(f"UTC offset must look like +05:30 or -04:00, got {text!r}")
    sign, hh, mm, ss = m.groups()
    delta = timedelta(hours=int(hh), minutes=int(mm or 0), seconds=int(ss or 0))
    if delta > timedelta(hours=14):
        raise ValueError(f"UTC offset out of range: {text!r}")
    return -delta if sign == "-" else delta


def format_offset(delta: timedelta) -> str:
    total = int(round(delta.total_seconds()))
    sign = "-" if total < 0 else "+"
    total = abs(total)
    hh, rem = divmod(total, 3600)
    mm, ss = divmod(rem, 60)
    return f"{sign}{hh:02d}:{mm:02d}" + (f":{ss:02d}" if ss else "")


def julian_day_ut(utc: datetime) -> float:
    hour = utc.hour + utc.minute / 60 + (utc.second + utc.microsecond / 1e6) / 3600
    return ephemeris.julday(utc.year, utc.month, utc.day, hour)


def resolve_moment(
    local_dt: datetime,
    lat: float,
    lon: float,
    tz_name: str | None = None,
    offset_override: str | timedelta | None = None,
) -> Moment:
    """Turn a naive local clock time at a place into UT and Julian Day, reporting the offset and flags."""
    if local_dt.tzinfo is not None:
        raise ValueError("local_dt must be naive wall-clock time; pass the zone or offset separately")

    flags: list[str] = []
    zone: ZoneInfo | None = None

    if tz_name is not None:
        try:
            zone = ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise NoTimeZoneError(f"Unknown time zone name {tz_name!r}") from exc
    else:
        tz_name = zone_name_for(lat, lon)
        if tz_name is not None:
            zone = ZoneInfo(tz_name)
        else:
            flags.append(FLAG_NO_ZONE)
            if offset_override is None:
                nautical = _timezone_finder().timezone_at(lat=lat, lng=lon)
                hint = f" Nautical zone there would be {nautical}." if nautical else ""
                raise NoTimeZoneError(
                    f"No time zone found at lat {lat}, lon {lon}. Give a UTC offset explicitly.{hint}"
                )

    zone_offset: timedelta | None = None
    if zone is not None:
        aware = local_dt.replace(tzinfo=zone, fold=0)
        zone_offset = aware.utcoffset()
        if local_dt.replace(tzinfo=zone, fold=1).utcoffset() != zone_offset:
            flags.append(FLAG_AMBIGUOUS)
        round_trip = aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
        if round_trip != local_dt:
            flags.append(FLAG_NONEXISTENT)

    if offset_override is not None:
        offset = parse_offset(offset_override)
        if zone_offset is not None and offset != zone_offset:
            flags.append(FLAG_OVERRIDDEN)
        elif zone_offset is None:
            flags.append(FLAG_OVERRIDDEN)
    else:
        assert zone_offset is not None
        offset = zone_offset

    if local_dt.year < PRE_1970_BOUNDARY:
        flags.append(FLAG_PRE_1970)
    if any(a <= local_dt.year <= b for a, b in WARTIME_RANGES):
        flags.append(FLAG_WARTIME)

    utc_naive = local_dt - offset
    jd_ut = julian_day_ut(utc_naive)
    dt_days = ephemeris.delta_t_days(jd_ut)

    return Moment(
        local_datetime=local_dt,
        timezone=tz_name,
        utc_offset=format_offset(offset),
        utc_offset_seconds=int(offset.total_seconds()),
        utc_datetime=utc_naive.replace(tzinfo=timezone.utc),
        jd_ut=jd_ut,
        jd_tt=jd_ut + dt_days,
        delta_t_sec=dt_days * 86400,
        flags=tuple(flags),
    )


def moment_from_jd(jd_ut: float) -> Moment:
    """A Moment for a Julian Day (UT) with no civil time attached: local = UTC, offset +00:00, no flags."""
    import swisseph as swe
    y, m, d, h = swe.revjul(jd_ut, swe.GREG_CAL)
    total = round(h * 3600 * 1000)  # milliseconds
    hh, rem = divmod(total, 3600 * 1000)
    mm, rem = divmod(rem, 60 * 1000)
    ss, ms = divmod(rem, 1000)
    utc_naive = datetime(y, m, d, hh, mm, ss, ms * 1000)
    dt_days = ephemeris.delta_t_days(jd_ut)
    return Moment(local_datetime=utc_naive, timezone="UTC", utc_offset="+00:00", utc_offset_seconds=0,
                  utc_datetime=utc_naive.replace(tzinfo=timezone.utc), jd_ut=jd_ut, jd_tt=jd_ut + dt_days,
                  delta_t_sec=dt_days * 86400, flags=())


# Convenience aliases used by the tests and API.
def _utc_offset_str(self: Moment) -> str:  # pragma: no cover - thin alias
    return self.utc_offset


Moment.utc_offset_str = property(_utc_offset_str)  # type: ignore[attr-defined]
