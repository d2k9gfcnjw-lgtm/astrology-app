"""Local time -> UT, offsets and the flags for uncertain historical offsets."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.engine.time import resolve_moment, NoTimeZoneError


def test_dst_summer_offset_and_date_rollover_new_york():
    m = resolve_moment(datetime(2010, 7, 4, 22, 13), 40.7128, -74.0060)
    assert m.timezone == "America/New_York"
    assert m.utc_offset_str == "-04:00"
    assert m.utc_datetime.replace(tzinfo=None) == datetime(2010, 7, 5, 2, 13)
    assert "pre_1970" not in m.flags and "wartime" not in m.flags


def test_zone_found_from_coordinates_when_not_given():
    m = resolve_moment(datetime(1992, 7, 23, 4, 23), 59.9167, 10.75)
    assert m.timezone == "Europe/Oslo"
    assert m.utc_offset_str == "+02:00"


def test_dst_end_morning_chicago_is_standard_time():
    m = resolve_moment(datetime(2024, 11, 3, 7, 50), 41.85, -87.65, tz_name="America/Chicago")
    assert m.utc_offset_str == "-06:00"
    assert "ambiguous_local_time" not in m.flags


def test_ambiguous_hour_is_flagged_not_guessed_silently():
    # 01:30 on 3 Nov 2024 happened twice in Chicago (CDT then CST).
    m = resolve_moment(datetime(2024, 11, 3, 1, 30), 41.85, -87.65, tz_name="America/Chicago")
    assert "ambiguous_local_time" in m.flags
    assert m.utc_offset_str == "-05:00"  # first occurrence (daylight time), stated openly
    m2 = resolve_moment(datetime(2024, 11, 3, 1, 30), 41.85, -87.65, tz_name="America/Chicago", offset_override="-06:00")
    assert m2.utc_offset_str == "-06:00"
    assert "offset_overridden" in m2.flags
    assert m2.utc_datetime - m.utc_datetime == timedelta(hours=1)


def test_nonexistent_local_time_is_flagged():
    # 02:30 on 10 Mar 2024 never happened in Chicago (clocks jumped 02:00 -> 03:00).
    m = resolve_moment(datetime(2024, 3, 10, 2, 30), 41.85, -87.65, tz_name="America/Chicago")
    assert "nonexistent_local_time" in m.flags


def test_pre_1970_flag():
    m = resolve_moment(datetime(1955, 1, 12, 7, 22), -33.45, -70.6667)
    assert m.timezone == "America/Santiago"
    assert m.utc_offset_str == "-04:00"
    assert "pre_1970" in m.flags


@pytest.mark.parametrize("year", [1914, 1917, 1919, 1939, 1943, 1947])
def test_wartime_flag(year):
    m = resolve_moment(datetime(year, 6, 1, 12, 0), 51.5, -0.12, tz_name="Europe/London")
    assert "wartime" in m.flags
    assert "pre_1970" in m.flags


@pytest.mark.parametrize("year", [1913, 1920, 1938, 1948])
def test_no_wartime_flag_outside_range(year):
    m = resolve_moment(datetime(year, 6, 1, 12, 0), 51.5, -0.12, tz_name="Europe/London")
    assert "wartime" not in m.flags


def test_override_wins_over_zone():
    m = resolve_moment(datetime(1955, 1, 12, 7, 22), -33.45, -70.6667, offset_override="-03:00")
    assert m.utc_offset_str == "-03:00"
    assert m.utc_datetime.replace(tzinfo=None) == datetime(1955, 1, 12, 10, 22)
    assert "offset_overridden" in m.flags
    assert m.timezone == "America/Santiago"  # still reported for the record


def test_open_ocean_needs_explicit_offset():
    with pytest.raises(NoTimeZoneError):
        resolve_moment(datetime(2000, 1, 1, 12, 0), 0.0, -150.0)
    m = resolve_moment(datetime(2000, 1, 1, 12, 0), 0.0, -150.0, offset_override="-10:00")
    assert m.utc_offset_str == "-10:00"
    assert "no_zone_for_location" in m.flags
    assert m.timezone is None


def test_unknown_zone_name_rejected():
    with pytest.raises(NoTimeZoneError):
        resolve_moment(datetime(2000, 1, 1), 0.0, 0.0, tz_name="Mars/Olympus")


def test_julian_day_of_j2000():
    m = resolve_moment(datetime(2000, 1, 1, 12, 0), 0.0, 0.0, tz_name="UTC")
    assert abs(m.jd_ut - 2451545.0) < 1e-9
    assert 60 < m.delta_t_sec < 70
