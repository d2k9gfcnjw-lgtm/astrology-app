"""Solar returns against the owner's astro.com aimed solar return sheets (local only)."""
from __future__ import annotations

import pytest

from app.engine.chart import calculate_chart
from app.engine.models import ChartInput, Settings
from app.engine.returns import solar_return

from .conftest import PLANET_KEYS, angle_diff

ARCMIN = 1 / 60
pytestmark = pytest.mark.golden


def _natal(g):
    n = g.natal
    return calculate_chart(ChartInput(datetime_local=n.datetime_local, lat=n.lat, lon=n.lon, timezone=n.timezone), Settings())


def test_instant_within_a_minute_of_astro_com(golden_sr):
    sr = solar_return(_natal(golden_sr), golden_sr.year, golden_sr.lat, golden_sr.lon)
    assert abs(sr.jd_ut - golden_sr.jd_ut) * 86400 < 60
    assert sr.local_datetime.startswith(golden_sr.datetime_local.strftime("%Y-%m-%dT%H:%M"))
    assert sr.local_datetime.endswith(golden_sr.utc_offset_used)
    assert sr.timezone == golden_sr.timezone
    assert sr.year == golden_sr.year and sr.kind == "solar"


@pytest.mark.parametrize("key", PLANET_KEYS + ["chiron"])
def test_positions_at_astro_com_instant(golden_sr, key):
    sr = solar_return(_natal(golden_sr), golden_sr.year, golden_sr.lat, golden_sr.lon, at_jd=golden_sr.jd_ut)
    assert angle_diff(sr.chart.planets[key].lon, golden_sr.planets[key]["lon"]) < ARCMIN
    assert sr.chart.planet_houses[key] == golden_sr.planets[key]["house"]


@pytest.mark.parametrize("house", range(1, 13))
def test_cusps_at_astro_com_instant(golden_sr, house):
    sr = solar_return(_natal(golden_sr), golden_sr.year, golden_sr.lat, golden_sr.lon, at_jd=golden_sr.jd_ut)
    assert sr.chart.houses.system_used == "placidus"
    assert angle_diff(sr.chart.houses.cusps[house], golden_sr.cusps[house]) < 2 * ARCMIN


def test_sun_is_on_natal_sun_at_solved_instant(golden_sr):
    natal = _natal(golden_sr)
    sr = solar_return(natal, golden_sr.year, golden_sr.lat, golden_sr.lon)
    assert angle_diff(sr.chart.planets["sun"].lon, natal.planets["sun"].lon) < 1 / 3600
