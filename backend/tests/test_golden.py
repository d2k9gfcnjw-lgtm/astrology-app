"""Every calculation against the astro.com golden charts.

Tolerances from CLAUDE.md: planet longitudes within 1 arc minute, house cusps
within 2 arc minutes. Latitude and declination within 1', speeds within 2"/day.
"""
from __future__ import annotations

import pytest

from app.engine.chart import calculate_chart
from app.engine.models import ChartInput, Settings
from app.engine.planets import planets_at
from app.engine.houses import houses_at
from app.engine.time import resolve_moment

from .conftest import PLANET_KEYS, angle_diff

ARCMIN = 1 / 60
ARCSEC = 1 / 3600

pytestmark = pytest.mark.golden


def _moment(golden):
    return resolve_moment(golden.datetime_local, golden.lat, golden.lon, tz_name=golden.timezone)


def test_julian_day_and_delta_t(golden):
    m = _moment(golden)
    # astro.com prints JD in TT to 6 decimals (0.09 s); local time is given to the minute.
    assert abs(m.jd_tt - golden.jd_tt) * 86400 < 1.0, f"JD(TT) off by {(m.jd_tt - golden.jd_tt) * 86400:.2f} s"
    assert abs(m.delta_t_sec - golden.delta_t_sec) < 0.5


def test_offset_and_utc(golden):
    m = _moment(golden)
    assert m.utc_offset_str == golden.utc_offset_used
    assert m.utc_datetime.replace(tzinfo=None) == golden.datetime_utc
    assert m.timezone == golden.timezone
    for flag in golden.expect_flags:
        assert flag in m.flags, f"expected flag {flag}, got {m.flags}"
    if "pre_1970" not in golden.expect_flags:
        assert "pre_1970" not in m.flags


@pytest.mark.parametrize("key", PLANET_KEYS)
def test_planet_longitude(golden, key):
    m = _moment(golden)
    pos = planets_at(m.jd_ut, Settings())
    assert angle_diff(pos[key].lon, golden.planets[key]["lon"]) < ARCMIN, (
        f"{key}: got {pos[key].lon:.4f}, expected {golden.planets[key]['lon']:.4f}"
    )


@pytest.mark.parametrize("key", PLANET_KEYS)
def test_planet_latitude_declination_speed(golden, key):
    m = _moment(golden)
    pos = planets_at(m.jd_ut, Settings())
    exp = golden.planets[key]
    assert abs(pos[key].lat - exp["lat"]) < ARCMIN
    assert abs(pos[key].declination - exp["dec"]) < ARCMIN
    assert abs(pos[key].speed_lon - exp["speed"]) < 2 * ARCSEC
    assert pos[key].retrograde == exp["retrograde"]


@pytest.mark.parametrize("node_type", ["true", "mean"])
def test_node(golden, node_type):
    m = _moment(golden)
    pos = planets_at(m.jd_ut, Settings(node_type=node_type))
    exp = golden.planets[f"{node_type}_node"]
    assert pos["node"].variant == node_type
    assert angle_diff(pos["node"].lon, exp["lon"]) < ARCMIN
    assert abs(pos["node"].speed_lon - exp["speed"]) < 2 * ARCSEC
    assert abs(pos["node"].declination - exp["dec"]) < ARCMIN


def test_chiron(golden):
    m = _moment(golden)
    pos = planets_at(m.jd_ut, Settings())
    exp = golden.planets["chiron"]
    assert angle_diff(pos["chiron"].lon, exp["lon"]) < ARCMIN
    assert abs(pos["chiron"].lat - exp["lat"]) < ARCMIN
    assert abs(pos["chiron"].declination - exp["dec"]) < ARCMIN
    assert pos["chiron"].retrograde == exp["retrograde"]


@pytest.mark.parametrize("house", range(1, 13))
def test_placidus_cusps(golden, house):
    m = _moment(golden)
    h = houses_at(m.jd_ut, golden.lat, golden.lon, Settings())
    assert h.system_used == "placidus"
    assert h.warnings == ()
    assert angle_diff(h.cusps[house], golden.cusps[house]) < 2 * ARCMIN, (
        f"cusp {house}: got {h.cusps[house]:.4f}, expected {golden.cusps[house]:.4f}"
    )
    assert abs(h.cusp_declinations[house] - golden.cusp_dec[house]) < 2 * ARCMIN


def test_angles(golden):
    m = _moment(golden)
    h = houses_at(m.jd_ut, golden.lat, golden.lon, Settings())
    assert angle_diff(h.asc, golden.cusps[1]) < 2 * ARCMIN
    assert angle_diff(h.mc, golden.cusps[10]) < 2 * ARCMIN
    assert angle_diff(h.dsc, (golden.cusps[1] + 180) % 360) < 2 * ARCMIN
    assert angle_diff(h.ic, (golden.cusps[10] + 180) % 360) < 2 * ARCMIN


def test_full_chart_house_placement_and_provenance(golden):
    chart = calculate_chart(
        ChartInput(datetime_local=golden.datetime_local, lat=golden.lat, lon=golden.lon, timezone=golden.timezone),
        Settings(),
    )
    for key in PLANET_KEYS + ["chiron"]:
        assert chart.planet_houses[key] == golden.planets[key]["house"], (
            f"{key} in house {chart.planet_houses[key]}, sheet says {golden.planets[key]['house']}"
        )
    assert chart.planet_houses["node"] == golden.planets["true_node"]["house"]
    prov = chart.provenance
    assert prov.local_time == golden.datetime_local
    assert prov.utc_offset == golden.utc_offset_used
    assert prov.timezone == golden.timezone
    assert (prov.lat, prov.lon) == (golden.lat, golden.lon)
    assert prov.house_system == "placidus"
    assert prov.zodiac == "tropical"
    assert prov.ayanamsa is None
    assert prov.node_type == "true"
