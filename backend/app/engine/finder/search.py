"""The finder pipeline: SR instant, grid with land mask, candidate cities, scoring, robustness, tiers, versus home."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import timedelta
from typing import Any

import numpy as np
from pydantic import BaseModel

from ..chart import calculate_chart, chart_at
from ..houses import house_of, houses_at
from ..models import Chart, ChartInput
from ..planets import planets_at
from ..returns import ReturnChart, dual_houses, solar_return, solar_return_instant
from ..rules import load_rules
from ..time import moment_from_jd, zone_name_for
from .context import TransitContext, build_context
from .geo import Candidate, candidate_cities, land_mask
from .scoring import Facts, Reason, Score, score_facts

PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
TIER_ORDER = {"best": 0, "safe": 1, "marginal": 2, "disqualified": 3}


@dataclass
class FinderOptions:
    goal: str | None = None
    population_floor: int = 15000
    airport_max_km: float = 250.0
    exclude_countries: list[str] = field(default_factory=list)
    precessed: bool = False
    safety_cusp_filter: bool = True
    birth_uncertainty_minutes: int = 0
    grid_step: float = 1.0
    refine: bool = True
    lat_min: float = -60.0
    lat_max: float = 66.0
    robustness_top: int = 80


def facts_at(natal: Chart, planets: dict, houses, rules) -> Facts:
    cusps = houses.cusps
    ho = {p: dual_houses(planets[p].lon, cusps, rules.cusp_orb_degrees, rules.cusp_orb_before_degrees) for p in PLANETS}
    angles = {"asc": houses.asc, "mc": houses.mc, "dsc": houses.dsc, "ic": houses.ic}
    angular = []
    for p in PLANETS:
        for name, lon in angles.items():
            orb = abs(((planets[p].lon - lon + 180) % 360) - 180)
            if orb <= rules.angular_orb_degrees:
                angular.append({"body": p, "angle": name, "orb": round(orb, 2)})
    angular.sort(key=lambda a: a["orb"])
    dist = min(abs(((houses.asc - c + 180) % 360) - 180) for c in natal.houses.cusps.values())
    return Facts(asc_natal_house=house_of(houses.asc, natal.houses.cusps), houses_of=ho, angular=angular, asc_cusp_distance=dist)


class PlaceScore(BaseModel):
    lat: float
    lon: float
    jd_ut: float
    utc_datetime: str
    local_datetime: str
    timezone: str | None
    disqualified: bool
    tier: str
    total: float
    stars: int
    dominant: str | None
    facts: dict
    reasons: list[dict]
    gains: list[dict]
    costs: list[dict]
    cautions: list[str]
    robustness: dict = {}
    versus_base: dict = {}
    marginal_vs_base: bool = False


def _local(jd: float, lat: float, lon: float) -> tuple[str, str | None]:
    from zoneinfo import ZoneInfo
    tz = zone_name_for(lat, lon)
    dt = moment_from_jd(jd).utc_datetime + timedelta(seconds=30)
    return (dt.astimezone(ZoneInfo(tz)) if tz else dt).isoformat(timespec="minutes"), tz


def _score_at(natal: Chart, planets: dict, jd: float, lat: float, lon: float, ctx: TransitContext, rules, options: FinderOptions) -> tuple[Score, Facts]:
    houses = houses_at(jd, lat, lon, natal.settings)
    f = facts_at(natal, planets, houses, rules)
    return score_facts(f, ctx, rules, options.goal, options.safety_cusp_filter), f


def _facts_summary(f: Facts, rules) -> dict:
    st = []
    per: dict[int, list[str]] = {}
    for b, hs in f.houses_of.items():
        for h in hs:
            per.setdefault(h, []).append(b)
    for h, bodies in sorted(per.items()):
        if len(bodies) >= rules.stellium_min_bodies:
            st.append({"house": h, "bodies": bodies})
    return {"asc_natal_house": f.asc_natal_house, "sun_houses": f.houses_of["sun"], "mars_houses": f.houses_of["mars"],
            "houses_of": f.houses_of, "stelliums": st, "angular": f.angular, "asc_cusp_distance": round(f.asc_cusp_distance, 2)}


def _place(natal, planets, jd, lat, lon, ctx, rules, options) -> tuple[PlaceScore, Score, Facts]:
    s, f = _score_at(natal, planets, jd, lat, lon, ctx, rules, options)
    local, tz = _local(jd, lat, lon)
    ps = PlaceScore(lat=lat, lon=lon, jd_ut=jd, utc_datetime=moment_from_jd(jd).utc_datetime.replace(tzinfo=None).isoformat(timespec="seconds"),
                    local_datetime=local, timezone=tz, disqualified=s.disqualified, tier=s.tier, total=round(s.total, 1), stars=s.stars,
                    dominant=s.dominant, facts=_facts_summary(f, rules), reasons=[r.to_dict() for r in s.reasons],
                    gains=[r.to_dict() for r in s.gains], costs=[r.to_dict() for r in s.costs], cautions=s.cautions)
    return ps, s, f


def _shifted_natals(natal: Chart, options: FinderOptions) -> dict[str, Chart]:
    """Natal charts recomputed as if born earlier or later (SRG 7, plus the chart's own uncertainty)."""
    rules = load_rules()
    shifts = {str(m): m for m in rules.raw["robustness"]["birth_time_shifts_minutes"]}
    if options.birth_uncertainty_minutes:
        shifts[f"u+{options.birth_uncertainty_minutes}"] = options.birth_uncertainty_minutes
        shifts[f"u-{options.birth_uncertainty_minutes}"] = -options.birth_uncertainty_minutes
    out = {}
    for label, minutes in shifts.items():
        inp = ChartInput(datetime_local=natal.moment.local_datetime + timedelta(minutes=minutes), lat=natal.provenance.lat, lon=natal.provenance.lon,
                         timezone=natal.moment.timezone, utc_offset_override=natal.moment.utc_offset if "offset_overridden" in natal.moment.flags else None)
        out[label] = calculate_chart(inp, natal.settings)
    return out


def _robustness(ps: PlaceScore, f: Facts, natal: Chart, shifted: dict[str, tuple[Chart, float, dict]], ctx, rules, options) -> dict:
    """Birth-time tests: the book's fixed 30/45-minute shifts (SRG 7) and the chart's own uncertainty.
    Labels starting with 'u' are the chart's own uncertainty; the others are the book's."""
    tests = {}
    warn = False
    tier_hit = None
    cfg = rules.raw["robustness"]
    for label, (nat2, jd2, planets2) in shifted.items():
        s2, _ = _score_at(nat2, planets2, jd2, ps.lat, ps.lon, ctx, rules, options)
        own = label.startswith("u")
        counts = (own and cfg.get("uncertainty_shifts_affect_tier", True)) or (not own and cfg.get("fixed_shifts_affect_tier", False))
        if s2.disqualified and not ps.disqualified:
            tests[label] = "disqualified: " + next((r.text for r in s2.reasons if r.points <= -200), "")
            warn = True
            if counts:
                tier_hit = cfg.get("disqualified_under_shift_tier", "marginal")
        elif TIER_ORDER[s2.tier] > TIER_ORDER[ps.tier]:
            tests[label] = f"drops to {s2.tier}"
            warn = True
            if counts and tier_hit is None:
                tier_hit = "one_tier"
        else:
            tests[label] = "holds"
    return {"asc_cusp_distance": round(f.asc_cusp_distance, 2), "birth_time_tests": tests, "flips": warn, "tier_hit": tier_hit}


def _apply_robustness(r: PlaceScore, rob: dict, rules) -> None:
    r.robustness = rob
    hit = rob.get("tier_hit")
    if not hit or r.disqualified:
        return
    if hit == "one_tier":
        if r.tier in ("best", "safe"):
            r.tier = "safe" if r.tier == "best" else "marginal"
    else:
        r.tier = hit
    r.stars = max(0, r.stars - int(rules.raw["robustness"].get("flip_costs_stars", 1)))


def _shifted(natal: Chart, year: int, options: FinderOptions) -> dict[str, tuple[Chart, float, dict]]:
    out = {}
    for label, nat2 in _shifted_natals(natal, options).items():
        jd2 = solar_return_instant(nat2, year, options.precessed)
        out[label] = (nat2, jd2, planets_at(jd2, nat2.settings))
    return out


def _versus(ps: PlaceScore, base: PlaceScore) -> dict:
    key = lambda r: (r["rule"], r.get("body"))
    base_costs = {key(r): r for r in base.costs + [r for r in base.reasons if r["points"] <= -200]}
    here_costs = {key(r): r for r in ps.costs + [r for r in ps.reasons if r["points"] <= -200]}
    fixes = [r["text"] for k, r in base_costs.items() if k not in here_costs]
    worsens = [r["text"] for k, r in here_costs.items() if k not in base_costs]
    return {"fixes": fixes, "worsens": worsens, "base_total": base.total, "base_tier": base.tier}


def score_place(natal: Chart, year: int, lat: float, lon: float, home: tuple[float, float], options: FinderOptions,
                ctx: TransitContext | None = None, jd: float | None = None, base: PlaceScore | None = None,
                robustness: bool = True, shifted: dict | None = None) -> PlaceScore:
    rules = load_rules()
    jd = jd if jd is not None else solar_return_instant(natal, year, options.precessed)
    planets = planets_at(jd, natal.settings)
    ctx = ctx or build_context(natal, year, natal.moment.timezone)
    ps, s, f = _place(natal, planets, jd, lat, lon, ctx, rules, options)
    if robustness and not ps.disqualified:
        shifted = shifted if shifted is not None else _shifted(natal, year, options)
        _apply_robustness(ps, _robustness(ps, f, natal, shifted, ctx, rules, options), rules)
    if base is None and (lat, lon) != home:
        base, _, _ = _place(natal, planets, jd, home[0], home[1], ctx, rules, options)
    if base is not None:
        ps.versus_base = _versus(ps, base)
        ps.marginal_vs_base = (not base.disqualified) and (ps.total - base.total) < float(rules.raw["context_charts"]["base_sr"]["marginal_gain_points"])
    return ps


class GridCell(BaseModel):
    lat: float
    lon: float
    score: float | None
    tier: str


class Grid(BaseModel):
    step: float
    cells: list[GridCell]


class CityResult(PlaceScore):
    name: str
    country: str
    admin1: str
    population: int
    airport_code: str
    airport_km: float


class FinderResult(BaseModel):
    year: int
    jd_sr: float
    goal: str | None
    options: dict
    context: dict
    grid: Grid
    cities: list[CityResult]
    base: PlaceScore
    previous: PlaceScore
    counts: dict[str, int]


def run_finder(natal: Chart, year: int, home: tuple[float, float], options: FinderOptions) -> FinderResult:
    rules = load_rules()
    jd = solar_return_instant(natal, year, options.precessed)
    planets = planets_at(jd, natal.settings)
    ctx = build_context(natal, year, natal.moment.timezone)
    base, _, _ = _place(natal, planets, jd, home[0], home[1], ctx, rules, options)
    prev_jd = solar_return_instant(natal, year - 1, options.precessed)
    prev_planets = planets_at(prev_jd, natal.settings)
    prev_ctx = build_context(natal, year - 1, natal.moment.timezone)
    previous, _, _ = _place(natal, prev_planets, prev_jd, home[0], home[1], prev_ctx, rules, options)

    # ---- grid ---------------------------------------------------------------------------------------
    step = options.grid_step
    lats = np.arange(options.lat_min, options.lat_max + 1e-9, step)
    lons = np.arange(-180.0, 180.0, step)
    glat, glon = np.meshgrid(lats, lons, indexing="ij")
    flat_lat, flat_lon = glat.ravel(), glon.ravel()
    land = land_mask().mask(flat_lat, flat_lon)
    cells: list[GridCell] = []
    scored: list[tuple[float, float, float]] = []
    for la, lo, on_land in zip(flat_lat, flat_lon, land):
        if not on_land:
            continue
        s, _ = _score_at(natal, planets, jd, float(la), float(lo), ctx, rules, options)
        cells.append(GridCell(lat=float(la), lon=float(lo), score=None if s.disqualified else round(s.total, 1), tier=s.tier))
        if not s.disqualified:
            scored.append((s.total, float(la), float(lo)))
    if options.refine and scored:
        scored.sort(reverse=True)
        fine = step / 4
        seen = set()
        for _, la, lo in scored[:20]:
            for dla in np.arange(0, step, fine):
                for dlo in np.arange(0, step, fine):
                    key = (round(la + dla, 4), round(lo + dlo, 4))
                    if key in seen or (dla == 0 and dlo == 0):
                        continue
                    seen.add(key)
                    if not land_mask().is_land(key[0], key[1]):
                        continue
                    s, _ = _score_at(natal, planets, jd, key[0], key[1], ctx, rules, options)
                    cells.append(GridCell(lat=key[0], lon=key[1], score=None if s.disqualified else round(s.total, 1), tier=s.tier))

    # ---- cities ------------------------------------------------------------------------------------
    cands = candidate_cities(options.population_floor, options.airport_max_km, options.exclude_countries)
    results: list[CityResult] = []
    for c in cands:
        ps, s, f = _place(natal, planets, jd, c.lat, c.lon, ctx, rules, options)
        results.append(CityResult(**ps.model_dump(), name=c.name, country=c.country, admin1=c.admin1, population=c.population,
                                  airport_code=c.airport_code, airport_km=round(c.airport_km, 1)))
    results.sort(key=lambda r: (TIER_ORDER[r.tier], -r.total, -r.population))
    # robustness on the top candidates (SRG 7 and the chart's own uncertainty)
    shifted = _shifted(natal, year, options)
    top = [r for r in results if not r.disqualified][: options.robustness_top]
    for r in top:
        houses = houses_at(jd, r.lat, r.lon, natal.settings)
        f = facts_at(natal, planets, houses, rules)
        _apply_robustness(r, _robustness(r, f, natal, shifted, ctx, rules, options), rules)
        r.versus_base = _versus(r, base)
        r.marginal_vs_base = (not base.disqualified) and (r.total - base.total) < float(rules.raw["context_charts"]["base_sr"]["marginal_gain_points"])
    results.sort(key=lambda r: (TIER_ORDER[r.tier], -r.total, -r.population))
    counts: dict[str, int] = {}
    for r in results:
        counts[r.tier] = counts.get(r.tier, 0) + 1
    return FinderResult(year=year, jd_sr=jd, goal=options.goal, options=asdict(options), context=ctx.to_dict(), grid=Grid(step=step, cells=cells),
                        cities=results, base=base, previous=previous, counts=counts)
