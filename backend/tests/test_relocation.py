"""planets_at ignores the place; houses_at is the only thing that moves."""
from __future__ import annotations

from datetime import datetime

from app.engine.houses import houses_at
from app.engine.models import ChartInput, Settings
from app.engine.planets import planets_at
from app.engine.time import resolve_moment
from app.engine.chart import calculate_chart, relocate_chart


def test_planets_do_not_depend_on_location():
    m = resolve_moment(datetime(2024, 11, 3, 7, 50), 41.85, -87.65)
    a = planets_at(m.jd_ut, Settings())
    b = planets_at(m.jd_ut, Settings())
    assert a == b  # pure function of jd_ut and settings
    assert "lat" not in planets_at.__code__.co_varnames[: planets_at.__code__.co_argcount]


def test_houses_change_with_place_only():
    m = resolve_moment(datetime(2024, 11, 3, 7, 50), 41.85, -87.65)
    chicago = houses_at(m.jd_ut, 41.85, -87.65, Settings())
    oslo = houses_at(m.jd_ut, 59.9167, 10.75, Settings())
    assert chicago.asc != oslo.asc
    assert chicago.mc != oslo.mc
    # Same moment -> same sidereal time at Greenwich, so ARMC differs exactly by longitude difference.
    diff = (oslo.armc - chicago.armc) % 360
    assert abs(diff - ((10.75 - (-87.65)) % 360)) < 1e-6


def test_relocated_chart_keeps_planets_and_moment():
    inp = ChartInput(datetime_local=datetime(2024, 11, 3, 7, 50), lat=41.85, lon=-87.65)
    home = calculate_chart(inp, Settings())
    away = relocate_chart(home, 59.9167, 10.75)
    assert away.moment == home.moment
    assert away.planets == home.planets
    assert away.houses.asc != home.houses.asc
    assert away.provenance.lat == 59.9167 and away.provenance.lon == 10.75
    assert away.provenance.relocated_from == (41.85, -87.65)
    for k, v in away.planets.items():  # placements recomputed against the new cusps
        assert away.planet_houses[k] == _house_of(v.lon, away.houses.cusps)
    assert away.planet_houses["fortune"] == _house_of(away.fortune.lon, away.houses.cusps)
    assert away.fortune != home.fortune  # Part of Fortune follows the new Ascendant


def _house_of(lon, cusps):
    for h in range(1, 13):
        start = cusps[h]
        end = cusps[1 if h == 12 else h + 1]
        if (lon - start) % 360 < (end - start) % 360:
            return h
    raise AssertionError
