"""The year's transit context, slow planets first, with the book's orbs."""
from __future__ import annotations

from datetime import datetime

from app.engine.chart import calculate_chart
from app.engine.finder.context import TransitContext, build_context
from app.engine.models import ChartInput, Settings

OSLO = ChartInput(datetime_local=datetime(1992, 7, 23, 4, 23), lat=59.9167, lon=10.75)


def test_context_lists_houses_and_heavy_hits():
    natal = calculate_chart(OSLO, Settings())
    ctx = build_context(natal, 2027, timezone="Europe/Oslo")
    assert isinstance(ctx, TransitContext)
    assert set(ctx.houses_transited) >= {"jupiter", "saturn", "uranus", "neptune", "pluto"}
    for body, houses in ctx.houses_transited.items():
        assert houses and all(1 <= h <= 12 for h in houses)
    assert all(h["body"] in {"saturn", "uranus", "neptune", "pluto"} for h in ctx.heavy_hits)
    assert all(h["aspect"] in {"conjunction", "square", "opposition", "semisquare", "sesquiquadrate"} for h in ctx.heavy_hits)
    assert all(h["natal_point"] in {"sun", "moon", "asc", "mc"} for h in ctx.heavy_hits)
    assert ctx.themes and all(t.startswith(("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")) for t in ctx.themes)
    assert isinstance(ctx.saturn_in_natal_2_or_8, bool)
    assert ctx.jd_start < ctx.jd_end


def test_houses_entered_subset_of_transited():
    natal = calculate_chart(OSLO, Settings())
    ctx = build_context(natal, 2027, timezone="Europe/Oslo")
    for body, entered in ctx.houses_entered.items():
        assert set(entered) <= set(ctx.houses_transited[body])
