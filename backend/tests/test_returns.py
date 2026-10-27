"""Solar and lunar returns: instant, relocation, natal houses, rule flags, precession."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.engine.chart import calculate_chart
from app.engine.houses import house_of
from app.engine.models import ChartInput, Settings
from app.engine.returns import (
    dual_houses, lunar_return, lunar_return_instants, return_set, solar_return, solar_return_instant, stelliums,
)
from app.engine.rules import load_rules
from app.engine.transits import solar_return_instant as transit_sr_instant

from .conftest import angle_diff

CHICAGO = ChartInput(datetime_local=datetime(2024, 11, 3, 7, 50), lat=41.85, lon=-87.65)
OSLO = ChartInput(datetime_local=datetime(1992, 7, 23, 4, 23), lat=59.9167, lon=10.75)


def test_rules_file_is_read():
    r = load_rules()
    assert r.cusp_orb_degrees == 2.5 and r.angular_orb_degrees == 12
    assert r.sr_asc_hard_filter_houses == [1, 6, 12]
    assert r.mars_saturn_allowed_houses == [3, 9]
    assert r.stellium_min_bodies == 3


def test_same_instant_as_transit_year_window():
    natal = calculate_chart(OSLO, Settings())
    assert abs(solar_return_instant(natal, 2026) - transit_sr_instant(natal, 2026)) < 1e-9


def test_relocation_keeps_planets_and_moves_houses():
    natal = calculate_chart(OSLO, Settings())
    home = solar_return(natal, 2026, 59.9167, 10.75)
    away = solar_return(natal, 2026, -33.45, -70.6667)
    assert home.jd_ut == away.jd_ut
    assert home.chart.planets == away.chart.planets
    assert home.chart.houses.asc != away.chart.houses.asc
    assert away.timezone == "America/Santiago" and home.timezone == "Europe/Oslo"
    assert away.place == {"lat": -33.45, "lon": -70.6667, "name": ""}


def test_natal_houses_of_sr_points():
    natal = calculate_chart(OSLO, Settings())
    sr = solar_return(natal, 2026, 59.9167, 10.75)
    assert sr.natal_house_of["asc"] == house_of(sr.chart.houses.asc, natal.houses.cusps)
    assert sr.natal_house_of["mc"] == house_of(sr.chart.houses.mc, natal.houses.cusps)
    assert sr.natal_house_of["sun"] == natal.planet_houses["sun"]  # the Sun is back on its natal degree
    assert set(sr.natal_house_of) >= {"asc", "mc", "sun", "moon", "mars", "saturn"}


def test_dual_houses_within_cusp_orb():
    cusps = {i: (i - 1) * 30.0 for i in range(1, 13)}
    assert dual_houses(15.0, cusps, 2.5) == [1]
    assert dual_houses(28.0, cusps, 2.5) == [1, 2]     # 2 deg before cusp 2
    assert dual_houses(31.0, cusps, 2.5) == [2, 1]     # 1 deg after cusp 2: works in both, primary first
    assert dual_houses(359.0, cusps, 2.5) == [12, 1]


def test_stelliums_and_rule_flags():
    rules = load_rules()
    houses = {"sun": [12], "venus": [12], "mercury": [1, 12], "mars": [3], "saturn": [3], "jupiter": [8], "moon": [8], "pluto": [8]}
    st = stelliums(houses, rules)
    assert {"house": 12, "bodies": ["sun", "venus", "mercury"]} in st
    assert any(s["house"] == 8 and set(s["bodies"]) == {"jupiter", "moon", "pluto"} for s in st)


def test_rule_flags_on_a_real_return():
    natal = calculate_chart(CHICAGO, Settings())
    sr = solar_return(natal, 2025, 41.85, -87.65)
    assert isinstance(sr.flags, list)
    for f in sr.flags:
        assert f["id"] in {"mars_saturn_same_house", "stellium_1_12_reads_as_asc_in_12", "stellium_8_reads_as_asc_in_12", "sr_asc_in_natal_1_6_12"}
        assert f["text"]
    assert sr.houses_of["mars"] and all(1 <= h <= 12 for h in sr.houses_of["mars"])
    assert all(a["orb"] <= 12 for a in sr.angular)


def test_mars_saturn_flag_fires_when_together():
    natal = calculate_chart(CHICAGO, Settings())
    # find a lunar return where Mars and Saturn share a house; synthetic check via the helper instead
    from app.engine.returns import rule_flags
    rules = load_rules()
    flags = rule_flags({"mars": [5], "saturn": [5]}, {"asc": 2}, [], rules)
    assert [f["id"] for f in flags] == ["mars_saturn_same_house"]
    assert rule_flags({"mars": [3], "saturn": [3]}, {"asc": 2}, [], rules) == []
    assert rule_flags({"mars": [4, 5], "saturn": [5]}, {"asc": 2}, [], rules)[0]["id"] == "mars_saturn_same_house"
    hard = rule_flags({}, {"asc": 12}, [], rules)
    assert hard[0]["id"] == "sr_asc_in_natal_1_6_12"


def test_precessed_return_comes_later_and_grows_with_age():
    natal = calculate_chart(OSLO, Settings())
    t1 = solar_return(natal, 2000, 59.9167, 10.75).jd_ut
    p1 = solar_return(natal, 2000, 59.9167, 10.75, precessed=True).jd_ut
    t2 = solar_return(natal, 2026, 59.9167, 10.75).jd_ut
    p2 = solar_return(natal, 2026, 59.9167, 10.75, precessed=True).jd_ut
    assert 0 < (p1 - t1) * 24 < 6          # about 8 years * 50 arcsec = 6.7 arcmin of Sun motion = ~2.7 h
    assert (p2 - t2) > (p1 - t1) * 3


def test_return_set_previous_and_base():
    natal = calculate_chart(OSLO, Settings())
    rs = return_set(natal, 2026, chosen=(-33.45, -70.6667), home=(41.85, -87.65))
    assert rs.chosen.year == 2026 and rs.previous.year == 2025 and rs.base.year == 2026
    assert rs.chosen.jd_ut == rs.base.jd_ut
    assert rs.base.place["lat"] == 41.85 and rs.previous.place["lat"] == 41.85
    assert rs.base.chart.planets == rs.chosen.chart.planets


def test_lunar_returns_in_a_year():
    natal = calculate_chart(OSLO, Settings())
    instants = lunar_return_instants(natal, 2026)
    assert 12 <= len(instants) <= 14
    for jd in instants:
        lr = lunar_return(natal, jd, 59.9167, 10.75)
        assert lr.kind == "lunar"
        assert angle_diff(lr.chart.planets["moon"].lon, natal.planets["moon"].lon) < 1 / 3600
    assert instants == sorted(instants)
    assert all(27 < b - a < 28 for a, b in zip(instants, instants[1:]))
