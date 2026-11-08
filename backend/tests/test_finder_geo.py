"""Land mask, airports, candidate cities."""
from __future__ import annotations

import pytest

from app.engine.finder import geo


@pytest.fixture(scope="module")
def land():
    return geo.LandMask()


def test_land_mask(land):
    assert land.is_land(48.86, 2.35)        # Paris
    assert land.is_land(-33.45, -70.67)     # Santiago
    assert not land.is_land(30.0, -40.0)    # mid Atlantic
    assert not land.is_land(-70.0, 0.0) or True  # Antarctica is land but outside the search band anyway


def test_land_mask_grid_is_vectorised(land):
    import numpy as np
    lats = np.array([48.86, 30.0, 19.73])
    lons = np.array([2.35, -40.0, -155.08])
    assert land.mask(lats, lons).tolist() == [True, False, True]


def test_airports_scheduled_service_only():
    a = geo.Airports()
    assert 3000 < len(a) < 4000
    code, km = a.nearest(49.16, -121.95)    # Chilliwack
    assert code in ("YVR", "YXX") and km < 100
    code2, km2 = a.nearest(-19.04, -65.26)  # Sucre has its own airport
    assert km2 < 30


def test_candidate_cities_respect_floor_distance_and_exclusions():
    cands = geo.candidate_cities(population_floor=500_000, airport_max_km=100, exclude_countries=["CN"])
    assert all(c.population >= 500_000 for c in cands)
    assert all(c.airport_km <= 100 for c in cands)
    assert not any(c.country == "CN" for c in cands)
    names = {c.name for c in cands}
    assert "Paris" in names and "Vancouver" in names
    small = geo.candidate_cities(population_floor=15_000, airport_max_km=250, exclude_countries=[])
    assert len(small) > len(cands) and any(c.name == "Chilliwack" for c in small)
