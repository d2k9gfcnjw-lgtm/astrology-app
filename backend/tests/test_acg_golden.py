"""Astrocartography against astro.com AstroClick Travel readouts (local golden file)."""
from __future__ import annotations

import pytest
import yaml

from app.engine.acg import AcgSettings, at_place, lines_at, distance_to_line_km, parans_at
from app.engine.chart import calculate_chart
from app.engine.models import ChartInput, Settings

from .conftest import GOLDEN_DIR, GoldenChart

ACG = GOLDEN_DIR / "acg_01.yaml"
pytestmark = [pytest.mark.golden, pytest.mark.skipif(not ACG.exists(), reason="no AstroClick golden file")]


@pytest.fixture(scope="module")
def data():
    raw = yaml.safe_load(ACG.read_text())
    g = GoldenChart(GOLDEN_DIR / raw["natal"])
    # astro.com's AstroClick Travel draws the Mean Node (the True Node line sits about 90 km away in Chicago).
    natal = calculate_chart(ChartInput(datetime_local=g.datetime_local, lat=g.lat, lon=g.lon, timezone=g.timezone), Settings(node_type="mean"))
    acg = AcgSettings(bodies=["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto", "node"], orb_km=400)
    return raw, natal, acg


def test_nearest_line_and_distance_match_astro_com(data):
    raw, natal, acg = data
    jd = natal.moment.jd_ut
    lines = {(l.body, l.angle): l for l in lines_at(jd, natal.settings, acg)}
    for p in raw["places"]:
        exp = p["nearest"]
        km = distance_to_line_km(lines[(exp["body"], exp["angle"])].points, p["lat"], p["lon"])
        assert abs(km - exp["km"]) <= 6, (p["name"], exp, km)
        res = at_place(jd, p["lat"], p["lon"], natal.settings, acg)
        assert res.lines and (res.lines[0].body, res.lines[0].angle) == (exp["body"], exp["angle"]), (p["name"], res.lines[:3])


def test_parans_at_the_same_latitude_match_astro_com(data):
    raw, natal, acg = data
    parans = parans_at(natal.moment.jd_ut, natal.settings, acg)
    for p in raw["places"]:
        for exp in p["parans"]:
            found = [q for q in parans if {(q.body_a, q.angle_a), (q.body_b, q.angle_b)} == {(exp["body_a"], exp["angle_a"]), (exp["body_b"], exp["angle_b"])}]
            assert found, (p["name"], exp)
            assert any(abs(q.lat - p["lat"]) <= 2.0 for q in found), (p["name"], exp, [q.lat for q in found])
