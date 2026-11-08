"""The rule engine on hand-made return charts. Every number comes from rules/rules.yaml."""
from __future__ import annotations

import pytest

from app.engine.finder.context import TransitContext
from app.engine.finder.scoring import Facts, score_facts
from app.engine.rules import load_rules

R = load_rules()


def facts(**over) -> Facts:
    """A neutral return: nothing in the danger houses, nothing on an angle."""
    base = dict(
        asc_natal_house=4, houses_of={"sun": [3], "moon": [9], "mercury": [3], "venus": [4], "mars": [4], "jupiter": [9],
                                       "saturn": [3], "uranus": [3], "neptune": [3], "pluto": [11]},
        angular=[], asc_cusp_distance=10.0, sr_asc_house_primary={"sun": 3, "venus": 4, "jupiter": 9, "mars": 5, "saturn": 2},
    )
    base.update(over)
    return Facts(**base)


QUIET = TransitContext.empty()


def test_neutral_chart_scores_near_zero_and_is_not_disqualified():
    s = score_facts(facts(), QUIET, R, goal=None)
    assert not s.disqualified
    assert -30 < s.total < 30
    assert s.stars >= 2


@pytest.mark.parametrize("house", [1, 6, 12])
def test_mars_in_danger_house_disqualifies_with_the_book_text(house):
    s = score_facts(facts(houses_of={**facts().houses_of, "mars": [house]}), QUIET, R, goal=None)
    assert s.disqualified
    assert any(r.rule == "mars_in_sr_1_6_12" and "TR 5" in r.text for r in s.reasons)


def test_sun_and_ascendant_danger_houses_disqualify():
    assert score_facts(facts(houses_of={**facts().houses_of, "sun": [12]}), QUIET, R, goal=None).disqualified
    assert score_facts(facts(asc_natal_house=6), QUIET, R, goal=None).disqualified


def test_dual_house_counts_the_worse_house():
    # Mars 1 degree past the 6th cusp works in 5 and 6: the 6th counts (SRG 23).
    s = score_facts(facts(houses_of={**facts().houses_of, "mars": [5, 6]}), QUIET, R, goal=None)
    assert s.disqualified


def test_stellium_rules():
    h = facts().houses_of
    assert score_facts(facts(houses_of={**h, "sun": [12], "venus": [12], "mercury": [1]}), QUIET, R, goal=None).disqualified  # 12+1 span
    assert score_facts(facts(houses_of={**h, "jupiter": [8], "venus": [8], "mercury": [8]}), QUIET, R, goal=None).disqualified  # 8th, benefics too
    assert not score_facts(facts(houses_of={**h, "jupiter": [7], "venus": [7], "mercury": [7]}), QUIET, R, goal=None).disqualified  # 7th is allowed


def test_mars_saturn_same_house_except_3_and_9():
    h = facts().houses_of
    assert score_facts(facts(houses_of={**h, "mars": [5], "saturn": [5]}), QUIET, R, goal=None).disqualified
    assert not score_facts(facts(houses_of={**h, "mars": [9], "saturn": [9]}), QUIET, R, goal=None).disqualified


def test_jupiter_on_mc_ranks_above_everything_and_saturn_cancels_it():
    good = score_facts(facts(asc_natal_house=10, angular=[{"body": "jupiter", "angle": "mc", "orb": 1.0}]), QUIET, R, goal=None)
    assert not good.disqualified and good.total >= 50
    assert any(r.rule == "angular_bonus" and r.body == "jupiter" and r.points == 30 for r in good.reasons)
    assert any(r.rule == "sr_asc_natal_house" and r.points == 30 for r in good.reasons)
    saturn = score_facts(facts(asc_natal_house=10, angular=[{"body": "jupiter", "angle": "mc", "orb": 1.0}, {"body": "saturn", "angle": "mc", "orb": 4.0}]), QUIET, R, goal=None)
    assert not any(r.rule == "angular_bonus" and r.body == "jupiter" for r in saturn.reasons)
    assert any(r.rule == "saturn_dominates_angle" for r in saturn.reasons)


def test_bonus_fades_between_5_and_12_degrees():
    full = score_facts(facts(angular=[{"body": "jupiter", "angle": "mc", "orb": 4.9}]), QUIET, R, goal=None)
    half = score_facts(facts(angular=[{"body": "jupiter", "angle": "mc", "orb": 12.0}]), QUIET, R, goal=None)
    pts = lambda s: next(r.points for r in s.reasons if r.rule == "angular_bonus")
    assert pts(full) == 30 and pts(half) == 15


def test_heavy_transit_cancels_the_natal_tenth():
    ctx = TransitContext.empty()
    ctx.heavy_hits.append({"body": "saturn", "aspect": "square", "natal_point": "sun", "local_datetime": "2027-06-01T00:00", "orb": 1.0})
    s = score_facts(facts(asc_natal_house=10), ctx, R, goal=None)
    assert not any(r.rule == "sr_asc_natal_house" and r.points > 0 for r in s.reasons)
    assert any(r.rule == "heavy_transit_cancels_natal_10th" for r in s.reasons)


def test_saturn_through_natal_2_or_8_penalises_jupiter_in_2_or_8():
    ctx = TransitContext.empty()
    ctx.houses_transited["saturn"] = [8]
    s = score_facts(facts(houses_of={**facts().houses_of, "jupiter": [8]}), ctx, R, goal=None)
    assert any(r.rule == "saturn_transit_2_8_penalises_jupiter_2_8" and r.points == -15 for r in s.reasons)


def test_katia_rules():
    h = facts().houses_of
    # dominant Venus
    s = score_facts(facts(angular=[{"body": "venus", "angle": "ic", "orb": 1.0}]), QUIET, R, goal=None)
    assert s.dominant == "venus" and any(r.rule == "dominant_planet" and r.points == 25 for r in s.reasons)
    # Neptune straddling two houses
    s2 = score_facts(facts(houses_of={**h, "neptune": [6, 7]}), QUIET, R, goal=None)
    assert any(r.rule == "malefic_straddles_cusp" and r.body == "neptune" for r in s2.reasons)
    # Venus beside Saturn in the 6th softens it
    s3 = score_facts(facts(houses_of={**h, "saturn": [6], "venus": [6]}), QUIET, R, goal=None)
    assert any(r.rule == "benefic_shares_house_with_malefic" and r.points == 10 for r in s3.reasons)
    # no stacking with the year's transit
    ctx = TransitContext.empty(); ctx.houses_entered["saturn"] = [6]
    s4 = score_facts(facts(houses_of={**h, "saturn": [6]}), ctx, R, goal=None)
    assert any(r.rule == "avoid_stacking_with_transit" and r.body == "saturn" for r in s4.reasons)


def test_goal_changes_the_score_and_the_explanation():
    f = facts(houses_of={**facts().houses_of, "venus": [5]})
    love = score_facts(f, QUIET, R, goal="love")
    none = score_facts(f, QUIET, R, goal=None)
    assert love.total > none.total
    assert any(r.rule == "goal_placement" and r.body == "venus" and r.points == 20 for r in love.reasons)


def test_reasons_split_into_gains_costs_and_cautions():
    s = score_facts(facts(asc_natal_house=10, houses_of={**facts().houses_of, "saturn": [6]}), QUIET, R, goal=None)
    assert any(g.points > 0 for g in s.gains) and any(c.points < 0 for c in s.costs)
    assert any("SRG 6" in c for c in s.cautions)
    assert all(r.text for r in s.reasons)


def test_unsafe_ascendant_near_cusp_can_be_switched_off():
    f = facts(asc_cusp_distance=1.2)
    assert score_facts(f, QUIET, R, goal=None).disqualified
    assert not score_facts(f, QUIET, R, goal=None, safety_cusp_filter=False).disqualified
