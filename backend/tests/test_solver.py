"""Exact-time solver: when does a body reach a longitude, and when does it station."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.engine import ephemeris
from app.engine.models import Settings
from app.engine.planets import planets_at
from app.engine.solver import crossings, stations, jd_from_utc
from app.engine.time import moment_from_jd

from .conftest import angle_diff

S = Settings()


def jd(y, m, d, hh=0, mm=0):
    return jd_from_utc(datetime(y, m, d, hh, mm))


def utc(j):
    return moment_from_jd(j).utc_datetime.replace(tzinfo=None)


def test_march_equinox_2024():
    hits = crossings("sun", 0.0, jd(2024, 3, 1), jd(2024, 4, 1), S)
    assert len(hits) == 1
    when = utc(hits[0].jd_ut)
    assert abs((when - datetime(2024, 3, 20, 3, 6)).total_seconds()) < 120  # USNO: 03:06 UT
    assert hits[0].retrograde is False and (hits[0].pass_index, hits[0].pass_count) == (1, 1)
    assert angle_diff(planets_at(hits[0].jd_ut, S)["sun"].lon, 0.0) < 1 / 3600


def test_moon_crosses_aries_point_every_month():
    hits = crossings("moon", 0.0, jd(2024, 1, 1), jd(2024, 12, 31), S)
    assert len(hits) == 13
    for h in hits:
        assert angle_diff(planets_at(h.jd_ut, S)["moon"].lon, 0.0) < 1 / 3600


def test_mercury_stations_april_2024():
    st = stations("mercury", jd(2024, 3, 1), jd(2024, 5, 15), S)
    assert [s.kind for s in st] == ["retrograde", "direct"]
    assert utc(st[0].jd_ut).date() in (datetime(2024, 4, 1).date(), datetime(2024, 4, 2).date())
    assert utc(st[1].jd_ut).date() == datetime(2024, 4, 25).date()
    for s in st:
        assert abs(planets_at(s.jd_ut, S)["mercury"].speed_lon) < 1e-4


def test_mars_triple_pass_2022_2023():
    # Mars stationed retrograde at 25 Gemini on 30 Oct 2022 and direct at 8 Gemini on 12 Jan 2023:
    # 15 Gemini (75 deg) was crossed three times.
    hits = crossings("mars", 75.0, jd(2022, 7, 1), jd(2023, 6, 1), S)
    assert len(hits) == 3
    assert [(h.pass_index, h.pass_count) for h in hits] == [(1, 3), (2, 3), (3, 3)]
    assert [h.retrograde for h in hits] == [False, True, False]
    assert utc(hits[0].jd_ut).month == 9 and utc(hits[0].jd_ut).year == 2022
    assert utc(hits[1].jd_ut).month == 12 and utc(hits[1].jd_ut).year == 2022
    assert utc(hits[2].jd_ut).year == 2023 and utc(hits[2].jd_ut).month in (2, 3)
    for h in hits:
        assert angle_diff(planets_at(h.jd_ut, S)["mars"].lon, 75.0) < 1 / 3600


def test_passes_not_grouped_across_separate_loops():
    # The Sun crosses 0 Aries once a year: each is its own 1-of-1 pass.
    hits = crossings("sun", 0.0, jd(2023, 1, 1), jd(2025, 12, 31), S)
    assert len(hits) == 3
    assert all((h.pass_index, h.pass_count) == (1, 1) for h in hits)


def test_crossing_near_station_is_not_missed():
    # Mercury stationed direct at about 15°59' Aries on 25 Apr 2024: a degree just past the station
    # is crossed twice within a few days.
    st = stations("mercury", jd(2024, 4, 1), jd(2024, 5, 15), S)
    lon_direct = planets_at(st[1].jd_ut, S)["mercury"].lon
    target = (lon_direct + 0.3) % 360
    hits = crossings("mercury", target, jd(2024, 4, 15), jd(2024, 5, 15), S)
    assert len(hits) == 2
    assert hits[0].retrograde is True and hits[1].retrograde is False
    assert 0 < hits[1].jd_ut - hits[0].jd_ut < 10


def test_window_edges_and_empty():
    assert crossings("sun", 0.0, jd(2024, 4, 1), jd(2024, 5, 1), S) == []
    assert stations("sun", jd(2024, 1, 1), jd(2024, 12, 31), S) == []


def test_sidereal_setting_is_respected():
    trop = crossings("sun", 0.0, jd(2024, 3, 1), jd(2024, 5, 1), S)
    sid = crossings("sun", 0.0, jd(2024, 3, 1), jd(2024, 5, 1), Settings(zodiac="sidereal"))
    assert len(trop) == 1 and len(sid) == 1
    assert 20 < sid[0].jd_ut - trop[0].jd_ut < 28  # Lahiri 0 Aries comes about 24 days later
