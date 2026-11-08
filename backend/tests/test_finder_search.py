"""The whole pipeline on the synthetic Oslo chart, and Katia's nine places on the owner's chart (local only)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from app.engine.chart import calculate_chart
from app.engine.finder.search import FinderOptions, run_finder
from app.engine.models import ChartInput, Settings

from .conftest import GOLDEN_DIR, GoldenChart

OSLO = ChartInput(datetime_local=datetime(1992, 7, 23, 4, 23), lat=59.9167, lon=10.75)
EXPECTED = Path(__file__).resolve().parents[2] / "reference" / "case-studies" / "2027-expected.yaml"


def test_pipeline_on_synthetic_chart():
    natal = calculate_chart(OSLO, Settings())
    res = run_finder(natal, 2027, home=(59.9167, 10.75), options=FinderOptions(population_floor=1_000_000, airport_max_km=100, grid_step=5.0, refine=False))
    assert res.year == 2027 and res.jd_sr > 0
    assert res.grid.step == 5.0 and len(res.grid.cells) > 500
    assert any(c.score is None for c in res.grid.cells)         # ocean / disqualified cells carry no score
    assert any(c.score is not None for c in res.grid.cells)
    tiers = {c.tier for c in res.cities}
    assert tiers <= {"best", "safe", "marginal", "disqualified"}
    assert any(c.tier != "disqualified" for c in res.cities)
    top = [c for c in res.cities if c.tier != "disqualified"][:5]
    for c in top:
        assert c.airport_code and c.airport_km <= 100
        assert c.local_datetime and c.reasons and c.facts["asc_natal_house"]
        assert c.robustness["asc_cusp_distance"] >= 2.5
        assert set(c.robustness["birth_time_tests"]) == {"-45", "-30"}
        assert c.robustness["tier_hit"] is None  # the book's fixed shifts only warn
    assert res.base.lat == 59.9167 and res.previous.jd_ut < res.jd_sr - 300
    assert res.context["themes"]
    # the list is ordered by tier then score
    order = [("best", "safe", "marginal", "disqualified").index(c.tier) for c in res.cities]
    assert order == sorted(order)


@pytest.mark.golden
@pytest.mark.skipif(not EXPECTED.exists() or not (GOLDEN_DIR / "natal_01.yaml").exists(), reason="local calibration files missing")
def test_katias_nine_places_2027():
    exp = yaml.safe_load(EXPECTED.read_text())
    g = GoldenChart(GOLDEN_DIR / exp["natal"])
    natal = calculate_chart(ChartInput(datetime_local=g.datetime_local, lat=g.lat, lon=g.lon, timezone=g.timezone), Settings())
    from app.engine.finder.context import build_context
    from app.engine.finder.search import _shifted, score_place
    opts = FinderOptions()
    ctx = build_context(natal, exp["year"], g.timezone)
    shifted = _shifted(natal, exp["year"], opts)
    results = {p["name"]: score_place(natal, exp["year"], p["lat"], p["lon"], home=(g.lat, g.lon), options=opts, ctx=ctx, shifted=shifted) for p in exp["places"]}
    for name, r in results.items():
        print(name, r.tier, r.total, r.robustness.get("birth_time_tests"))
    for p in exp["places"]:
        r = results[p["name"]]
        if p["tier"] == "dangerous":
            assert r.disqualified, (p["name"], r.reasons)
        elif p["tier"] == "not_good":
            assert r.disqualified or r.tier == "marginal", (p["name"], r.tier, r.reasons)
        elif p["tier"] == "unclear":
            continue
        else:
            assert not r.disqualified, (p["name"], [x["text"] for x in r.reasons if x["points"] < -100])
            assert r.tier in ("best", "safe"), (p["name"], r.tier, r.total)
    assert results["Ceduna"].tier == "best" and results["Chilliwack"].tier == "best"
    assert results["Chilliwack"].total > results["Santiago"].total
    assert any("Saturn" in c["text"] and "6" in c["text"] for c in results["Chilliwack"].costs)
