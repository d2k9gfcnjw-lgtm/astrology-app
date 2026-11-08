"""The rule engine: every point comes from rules/rules.yaml and carries its sentence and page."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..rules import Rules
from .context import TransitContext

BENEFICS = ("venus", "jupiter")
HARD_POINTS = -200
NAMES = {"sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus", "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
         "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto"}


@dataclass
class Facts:
    asc_natal_house: int
    houses_of: dict[str, list[int]]        # SR house(s) per planet, primary first
    angular: list[dict]                    # [{"body", "angle", "orb"}]
    asc_cusp_distance: float               # degrees from the SR Ascendant to the nearest natal cusp
    sr_asc_house_primary: dict | None = None


@dataclass
class Reason:
    rule: str
    points: float
    text: str
    body: str | None = None
    status: str = ""

    def to_dict(self) -> dict:
        return {"rule": self.rule, "points": round(self.points, 1), "text": self.text, "body": self.body, "status": self.status}


@dataclass
class Score:
    disqualified: bool
    total: float
    stars: int
    reasons: list[Reason]
    gains: list[Reason]
    costs: list[Reason]
    cautions: list[str]
    dominant: str | None
    tier: str

    def to_dict(self) -> dict:
        return {"disqualified": self.disqualified, "total": round(self.total, 1), "stars": self.stars, "tier": self.tier,
                "dominant": self.dominant, "reasons": [r.to_dict() for r in self.reasons], "gains": [r.to_dict() for r in self.gains],
                "costs": [r.to_dict() for r in self.costs], "cautions": self.cautions}


def _entry(v: Any) -> tuple[float | None, str, dict]:
    """A table entry is 'hard', a number, or {weight, text, goals, cautions, ...}."""
    if v == "hard":
        return None, "", {}
    if isinstance(v, (int, float)):
        return float(v), "", {}
    if isinstance(v, dict):
        return float(v.get("weight", 0)), str(v.get("text", "")), v
    return 0.0, "", {}


def _fade(orb: float, full: float, half_at: float) -> float:
    if orb <= full:
        return 1.0
    if orb >= half_at:
        return 0.5
    return 1.0 - 0.5 * (orb - full) / (half_at - full)


def tier_for(total: float, disqualified: bool, raw: dict) -> str:
    if disqualified:
        return "disqualified"
    t = raw.get("tiers", {"best": 40, "safe": -10})
    if total >= t["best"]:
        return "best"
    if total >= t["safe"]:
        return "safe"
    return "marginal"


def stars_for(total: float, thresholds: list[float]) -> int:
    return sum(1 for t in thresholds if total >= t)


def score_facts(facts: Facts, ctx: TransitContext, rules: Rules, goal: str | None, safety_cusp_filter: bool = True) -> Score:
    raw = rules.raw
    reasons: list[Reason] = []
    cautions: list[str] = []
    hard = False
    ho = facts.houses_of
    stellium_bodies = raw.get("stellium_bodies", list(NAMES))
    min_bodies = rules.stellium_min_bodies

    def in_house(body: str, houses: set[int]) -> bool:
        return any(h in houses for h in ho.get(body, []))

    # ---- hard filters --------------------------------------------------------------------
    for f in raw["hard_filters"]:
        fid = f["id"]
        hit = False
        text = str(f.get("description", "")).strip()
        if fid == "sr_asc_in_natal_1_6_12":
            hit = facts.asc_natal_house in f["houses"]
            text = f"Return Ascendant in natal house {facts.asc_natal_house}. {text}"
        elif fid in ("sun_in_sr_1_6_12", "mars_in_sr_1_6_12"):
            body = f["body"]
            bad = [h for h in ho.get(body, []) if h in f["houses"]]
            hit = bool(bad)
            text = f"{NAMES[body]} in return house {bad[0] if bad else ''}. {text}"
        elif fid == "stellium_in_sr_1_6_12":
            for h in f["houses"]:
                members = [b for b in stellium_bodies if h in ho.get(b, [])]
                if len(members) >= min_bodies:
                    hit, text = True, f"Stellium in return house {h} ({', '.join(NAMES[m] for m in members)}). {text}"
                    break
            if not hit:
                for pair in f.get("span_pairs", []):
                    members = [b for b in stellium_bodies if any(h in ho.get(b, []) for h in pair)]
                    if len(members) >= min_bodies:
                        hit, text = True, f"Stellium across return houses {pair[0]} and {pair[1]} ({', '.join(NAMES[m] for m in members)}). {text}"
                        break
        elif fid == "stellium_in_sr_8":
            members = [b for b in stellium_bodies if 8 in ho.get(b, [])]
            hit = len(members) >= min_bodies
            text = f"Stellium in return house 8 ({', '.join(NAMES[m] for m in members)}). {text}"
        elif fid == "mars_saturn_same_house":
            shared = sorted((set(ho.get("mars", [])) & set(ho.get("saturn", []))) - set(f["allowed_houses"]))
            hit = bool(shared)
            text = f"Mars and Saturn share return house {shared[0] if shared else ''}. {text}"
        elif fid == "sr_asc_near_natal_cusp":
            hit = safety_cusp_filter and facts.asc_cusp_distance < float(f["min_degrees"])
            text = f"Return Ascendant only {facts.asc_cusp_distance:.1f}° from a natal cusp. {text}"
        if hit:
            hard = True
            reasons.append(Reason(fid, HARD_POINTS, text, status=str(f.get("status", ""))))

    goal_profile = raw.get("goal_profiles", {}).get(goal or "", {}) if goal else {}
    heavy = bool(ctx.heavy_hits)

    # ---- SR Ascendant in the natal houses -------------------------------------------------
    entry = raw["sr_asc_natal_house"].get(facts.asc_natal_house)
    w, text, meta = _entry(entry)
    if w is not None:
        pts = w
        if goal and goal in meta.get("goals", {}):
            pts += float(meta["goals"][goal])
        key = f"sr_asc_natal_house.{facts.asc_natal_house}"
        if key in goal_profile:
            pts *= float(goal_profile[key])
        for c in meta.get("cautions", []):
            cautions.append(c)
        if facts.asc_natal_house == 10 and heavy:
            h = ctx.heavy_hits[0]
            reasons.append(Reason("heavy_transit_cancels_natal_10th", 0.0,
                                  f"The +{int(w)} for the natal 10th is cancelled: {NAMES[h['body']]} {h['aspect']} natal {h['natal_point']} this year (TR 14).", status="core"))
        else:
            reasons.append(Reason("sr_asc_natal_house", pts, f"Return Ascendant in natal house {facts.asc_natal_house}: {text}", status=str(meta.get("status", ""))))

    # ---- the Sun's own house -----------------------------------------------------------------
    sun_houses = ho.get("sun", [])
    if sun_houses:
        entry = raw["sun_sr_house"].get(sun_houses[0])
        w, text, meta = _entry(entry)
        if w is not None and (w or text):
            pts = w + (float(meta.get("goals", {}).get(goal, 0)) if goal else 0.0)
            key = f"sun_sr_house.{sun_houses[0]}"
            if key in goal_profile:
                pts *= float(goal_profile[key])
            reasons.append(Reason("sun_sr_house", pts, f"Sun in return house {sun_houses[0]}: {text}", body="sun", status=str(meta.get("status", ""))))

    # ---- planets in the return houses ------------------------------------------------------
    for body, table in raw["planet_sr_house"].items():
        houses = ho.get(body, [])
        if not houses or not isinstance(table, dict):
            continue
        entries = []
        for h in houses:
            v = table.get(h)
            if v is None or v == "hard":
                continue
            w, text, meta = _entry(v)
            entries.append((h, w, text, meta))
        if not entries:
            continue
        if body in BENEFICS:
            # Katia: a benefic working in two houses is a gift to both
            for h, w, text, meta in entries:
                pts = w + (float(meta.get("goals", {}).get(goal, 0)) if goal else 0.0)
                if pts or text:
                    reasons.append(Reason("planet_sr_house", pts, f"{NAMES[body]} in return house {h}: {text}", body=body))
        else:
            h, w, text, meta = min(entries, key=lambda e: e[1])  # SRG 23: the worse house counts
            reasons.append(Reason("planet_sr_house", w, f"{NAMES[body]} in return house {h}: {text}", body=body))

    # ---- angular bonuses, Saturn dominates ---------------------------------------------------
    full = float(raw.get("bonus_full_orb_degrees", 5))
    half_at = float(raw.get("bonus_half_orb_degrees", 12))
    sat_rule = next((o for o in raw.get("overrides", []) if o["id"] == "saturn_dominates_angle"), None)
    saturn_angles = set()
    if sat_rule:
        for a in facts.angular:
            if a["body"] == "saturn" and a["orb"] <= float(sat_rule["orb_degrees"]) and a["angle"] in sat_rule["angles"]:
                saturn_angles.add(a["angle"])
    for a in facts.angular:
        table = raw["angular_bonuses"].get(a["body"])
        if not table or a["angle"] not in table:
            continue
        base_pts = float(table[a["angle"]])
        if a["angle"] in saturn_angles:
            reasons.append(Reason("saturn_dominates_angle", 0.0, f"Saturn within {sat_rule['orb_degrees']}° of the {a['angle'].upper()} cancels {NAMES[a['body']]}'s bonus there (SRG 24).", body=a["body"], status="core"))
            continue
        pts = base_pts * _fade(float(a["orb"]), full, half_at)
        if "angular_bonuses" in goal_profile:
            pts *= float(goal_profile["angular_bonuses"])
        reasons.append(Reason("angular_bonus", pts, f"{NAMES[a['body']]} {a['orb']:.1f}° from the {a['angle'].upper()}: {table.get('text', '')}", body=a["body"], status=str(table.get("status", ""))))

    # ---- transits modulate ---------------------------------------------------------------------
    sat28 = next((o for o in raw.get("overrides", []) if o["id"] == "saturn_transit_2_8_penalises_jupiter_2_8"), None)
    saturn_28 = ctx.saturn_in_natal_2_or_8 or any(h in (2, 8) for h in ctx.houses_transited.get("saturn", []))
    if sat28 and saturn_28 and any(h in (2, 8) for h in ho.get("jupiter", [])):
        reasons.append(Reason("saturn_transit_2_8_penalises_jupiter_2_8", float(sat28["weight"]),
                              "Saturn transits the natal 2nd or 8th this year, so Jupiter in the return 2nd or 8th means money going out (SRG 11, p. 175).", body="jupiter", status="core"))

    # ---- Katia's practice -----------------------------------------------------------------------
    k = raw.get("katia", {})
    dominant = None
    dom = k.get("dominant_planet")
    if dom and facts.angular:
        closest = min(facts.angular, key=lambda a: a["orb"])
        if closest["orb"] <= float(dom["orb_degrees"]):
            dominant = closest["body"]
            w = float(dom["weights"].get(dominant, 0))
            if w:
                reasons.append(Reason("dominant_planet", w, f"{NAMES[dominant]} dominant ({closest['orb']:.1f}° from the {closest['angle'].upper()}): {dom['text']}", body=dominant, status="confirm (Katia)"))
            elif dominant in ("saturn", "neptune", "mars", "uranus", "pluto"):
                cautions.append(f"{NAMES[dominant]} is the dominant planet ({closest['orb']:.1f}° from the {closest['angle'].upper()}): it colours the whole year (Katia).")
    ms = k.get("malefic_straddles_cusp")
    if ms:
        for body in ms["bodies"]:
            if len(ho.get(body, [])) == 2:
                reasons.append(Reason("malefic_straddles_cusp", float(ms["weight"]), f"{NAMES[body]} works in houses {ho[body][0]} and {ho[body][1]}: {ms['text']}", body=body, status="confirm (Katia)"))
    bs = k.get("benefic_shares_house_with_malefic")
    if bs:
        for mal in bs["malefics"]:
            table = raw["planet_sr_house"].get(mal, {})
            mh = {h for h in ho.get(mal, []) if isinstance(table, dict) and _entry(table.get(h))[0] is not None and (_entry(table.get(h))[0] or 0) < 0}
            for ben in bs["benefics"]:
                shared = mh & set(ho.get(ben, []))
                if shared:
                    reasons.append(Reason("benefic_shares_house_with_malefic", float(bs["weight"]), f"{NAMES[ben]} beside {NAMES[mal]} in house {sorted(shared)[0]}: {bs['text']}", body=ben, status="confirm (Katia)"))
                    break
    st = k.get("avoid_stacking_with_transit")
    if st:
        for body in st["bodies"]:
            stacked = set(ho.get(body, [])) & set(ctx.houses_entered.get(body, []))
            if stacked:
                reasons.append(Reason("avoid_stacking_with_transit", float(st["weight"]), f"{NAMES[body]} in return house {sorted(stacked)[0]} while transiting {NAMES[body]} enters natal house {sorted(stacked)[0]} this year: {st['text']}", body=body, status="confirm (Katia)"))
    gp = k.get("goal_placements", {}).get(goal or "")
    if gp:
        for body, table in gp.items():
            if body == "sr_asc_natal_house":
                if facts.asc_natal_house in table:
                    reasons.append(Reason("goal_placement", float(table[facts.asc_natal_house]), f"Return Ascendant in natal house {facts.asc_natal_house} serves the goal '{goal}'.", status="confirm (Katia)"))
                continue
            for h in ho.get(body, []):
                if h in table:
                    reasons.append(Reason("goal_placement", float(table[h]), f"{NAMES[body]} in return house {h} serves the goal '{goal}'.", body=body, status="confirm (Katia)"))

    total = sum(r.points for r in reasons if r.points > HARD_POINTS)
    stars = 0 if hard else stars_for(total, [float(t) for t in raw["star_rating"]["thresholds"]])
    gains = [r for r in reasons if r.points > 0]
    costs = [r for r in reasons if r.points < 0]
    return Score(disqualified=hard, total=total, stars=stars, reasons=reasons, gains=gains, costs=costs, cautions=cautions,
                 dominant=dominant, tier=tier_for(total, hard, raw))
