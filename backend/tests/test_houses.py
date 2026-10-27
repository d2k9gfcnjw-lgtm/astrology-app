"""House systems: Placidus default, Whole Sign, high-latitude fallback."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.engine.houses import houses_at
from app.engine.models import Settings
from app.engine.time import resolve_moment

JD = resolve_moment(datetime(1992, 7, 23, 4, 23), 59.9167, 10.75, tz_name="Europe/Oslo").jd_ut


def test_whole_sign_cusps_are_sign_boundaries():
    h = houses_at(JD, 59.9167, 10.75, Settings(house_system="whole_sign"))
    assert h.system_used == "whole_sign"
    asc_sign_start = (h.asc // 30) * 30
    for i in range(1, 13):
        assert h.cusps[i] == pytest.approx((asc_sign_start + 30 * (i - 1)) % 360)
    # Angles are unchanged by the house system.
    p = houses_at(JD, 59.9167, 10.75, Settings(house_system="placidus"))
    assert h.asc == pytest.approx(p.asc) and h.mc == pytest.approx(p.mc)


@pytest.mark.parametrize("lat", [69.65, -70.0, 66.0, 80.0])
def test_placidus_falls_back_to_whole_sign_at_high_latitude(lat):
    h = houses_at(JD, lat, 18.96, Settings(house_system="placidus"))
    assert h.system_used == "whole_sign"
    assert any("Placidus" in w and "Whole Sign" in w for w in h.warnings)
    assert h.cusps[1] % 30 == pytest.approx(0)


def test_placidus_ok_just_below_threshold():
    h = houses_at(JD, 65.9, 18.96, Settings(house_system="placidus"))
    assert h.system_used == "placidus"
    assert h.warnings == ()


def test_cusp_order_and_opposites():
    h = houses_at(JD, 41.85, -87.65, Settings())
    for i in range(1, 7):
        assert (h.cusps[i] + 180) % 360 == pytest.approx(h.cusps[i + 6] % 360, abs=1e-9)
    # cusps increase counterclockwise through the zodiac
    for i in range(1, 12):
        assert 0 < (h.cusps[i + 1] - h.cusps[i]) % 360 < 180


def test_sidereal_houses_shift_by_ayanamsa():
    trop = houses_at(JD, 41.85, -87.65, Settings())
    sid = houses_at(JD, 41.85, -87.65, Settings(zodiac="sidereal", ayanamsa="lahiri"))
    shift = (trop.asc - sid.asc) % 360
    assert 23.5 < shift < 24.5  # Lahiri in 1992 is about 23°45'
    assert (trop.mc - sid.mc) % 360 == pytest.approx(shift, abs=1e-6)
    assert sid.ayanamsa_degrees == pytest.approx(shift, abs=1e-6)
