"""Part of Fortune, Lilith, nodes and sidereal mode. No astro.com values yet for Fortune/Lilith:
these are self-consistency tests until the owner adds golden numbers."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.engine.chart import calculate_chart, part_of_fortune
from app.engine.models import ChartInput, Settings
from app.engine.planets import planets_at
from app.engine.time import resolve_moment

from .conftest import angle_diff

# Synthetic golden subjects only (no real birth data in the repo).
OSLO = ChartInput(datetime_local=datetime(1992, 7, 23, 4, 23), lat=59.9167, lon=10.75)      # Sun in house 1: night birth
CHICAGO = ChartInput(datetime_local=datetime(2024, 11, 3, 7, 50), lat=41.85, lon=-87.65)   # Sun in house 12: day birth


def test_fortune_formula_by_sect():
    assert part_of_fortune(asc=10.0, sun=100.0, moon=200.0, is_day=True) == pytest.approx((10 + 200 - 100) % 360)
    assert part_of_fortune(asc=10.0, sun=100.0, moon=200.0, is_day=False) == pytest.approx((10 + 100 - 200) % 360)


def test_night_birth_uses_reversed_formula_by_default():
    c = calculate_chart(OSLO, Settings())
    assert c.is_day is False
    expected = (c.houses.asc + c.planets["sun"].lon - c.planets["moon"].lon) % 360
    assert angle_diff(c.fortune.lon, expected) < 1e-9


def test_day_birth_uses_day_formula():
    c = calculate_chart(CHICAGO, Settings())
    assert c.is_day is True
    expected = (c.houses.asc + c.planets["moon"].lon - c.planets["sun"].lon) % 360
    assert angle_diff(c.fortune.lon, expected) < 1e-9


def test_day_only_toggle_ignores_sect():
    c = calculate_chart(OSLO, Settings(fortune_formula="day"))
    expected = (c.houses.asc + c.planets["moon"].lon - c.planets["sun"].lon) % 360
    assert angle_diff(c.fortune.lon, expected) < 1e-9


def test_lilith_mean_vs_true_differ_and_are_selectable():
    m = resolve_moment(OSLO.datetime_local, OSLO.lat, OSLO.lon)
    mean = planets_at(m.jd_ut, Settings(lilith_type="mean"))["lilith"]
    true = planets_at(m.jd_ut, Settings(lilith_type="true"))["lilith"]
    assert mean.variant == "mean" and true.variant == "true"
    assert angle_diff(mean.lon, true.lon) > 0.5
    assert angle_diff(mean.lon, true.lon) < 40


def test_optional_bodies_can_be_switched_off():
    m = resolve_moment(OSLO.datetime_local, OSLO.lat, OSLO.lon)
    pos = planets_at(m.jd_ut, Settings(include_chiron=False, include_lilith=False, include_node=False))
    assert set(pos) == {"sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"}


def test_sidereal_equals_tropical_minus_ayanamsa():
    m = resolve_moment(OSLO.datetime_local, OSLO.lat, OSLO.lon)
    trop = planets_at(m.jd_ut, Settings())
    sid = planets_at(m.jd_ut, Settings(zodiac="sidereal", ayanamsa="lahiri"))
    shifts = {k: (trop[k].lon - sid[k].lon) % 360 for k in trop}
    first = next(iter(shifts.values()))
    assert 23.7 < first < 23.8  # Lahiri 1992 ≈ 23°45'
    for k, v in shifts.items():
        assert v == pytest.approx(first, abs=1e-6), k


def test_chart_records_ayanamsa_when_sidereal():
    c = calculate_chart(OSLO, Settings(zodiac="sidereal"))
    assert c.provenance.zodiac == "sidereal"
    assert c.provenance.ayanamsa == "lahiri"
    assert c.houses.ayanamsa_degrees is not None
