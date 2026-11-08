"""The year's transit context for the finder: slow planets first, the book's orbs and aspects (TR 12, 14, 16, 23, 28)."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..houses import house_of
from ..models import Chart, TransitSettings
from ..rules import load_rules
from ..solver import lon_speed
from ..transits import year_ahead

SLOW = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
NAMES = {"jupiter": "Jupiter", "saturn": "Saturn", "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto"}
POINT = {"sun": "Sun", "moon": "Moon", "asc": "Ascendant", "mc": "MC"}


@dataclass
class TransitContext:
    jd_start: float = 0.0
    jd_end: float = 0.0
    houses_transited: dict[str, list[int]] = field(default_factory=dict)   # natal houses each slow planet occupies this year
    houses_entered: dict[str, list[int]] = field(default_factory=dict)     # natal houses entered (direct motion) this year
    heavy_hits: list[dict] = field(default_factory=list)                   # Saturn..Pluto dissonant to Sun, Moon, ASC, MC
    jupiter_hits: list[dict] = field(default_factory=list)
    saturn_in_natal_2_or_8: bool = False
    themes: list[str] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "TransitContext":
        return cls()

    def to_dict(self) -> dict:
        return {"jd_start": self.jd_start, "jd_end": self.jd_end, "houses_transited": self.houses_transited,
                "houses_entered": self.houses_entered, "heavy_hits": self.heavy_hits, "jupiter_hits": self.jupiter_hits,
                "saturn_in_natal_2_or_8": self.saturn_in_natal_2_or_8, "themes": self.themes}


def build_context(natal: Chart, year: int, timezone: str | None = None) -> TransitContext:
    rules = load_rules()
    yt = rules.raw["context_charts"]["year_transits"]
    orbs = dict(yt["orbs"])
    ts = TransitSettings(bodies=SLOW, natal_points=["sun", "moon", "asc", "mc"], aspects=list(yt["dissonant_aspects"]) + ["trine"],
                         orbs=orbs, minor_orbs={b: min(o, 2.0) for b, o in orbs.items()},
                         include_ingresses=True, include_sign_ingresses=False, include_stations=False)
    rep = year_ahead(natal, year, ts, timezone)
    ctx = TransitContext(jd_start=rep.jd_start, jd_end=rep.jd_end)
    heavy = set(yt["heavy_bodies"])
    dissonant = set(yt["dissonant_aspects"])
    for h in rep.hits:
        d = {"body": h.body, "aspect": h.aspect, "natal_point": h.natal_point, "local_datetime": h.local_datetime,
             "orb": h.orb, "pass_index": h.pass_index, "pass_count": h.pass_count, "retrograde": h.retrograde}
        if h.body in heavy and h.aspect in dissonant:
            ctx.heavy_hits.append(d)
        elif h.body == "jupiter":
            ctx.jupiter_hits.append(d)
    # natal houses occupied: sample every ~2 weeks through the year
    n = 27
    for body in SLOW:
        seen: list[int] = []
        for i in range(n):
            jd = rep.jd_start + (rep.jd_end - rep.jd_start) * i / (n - 1)
            lon, _ = lon_speed(body, jd, natal.settings)
            h = house_of(lon, natal.houses.cusps)
            if h not in seen:
                seen.append(h)
        ctx.houses_transited[body] = seen
        ctx.houses_entered[body] = sorted({int(i.entered) for i in rep.ingresses if i.body == body and i.kind == "house" and not i.retrograde} & set(seen))
    ctx.saturn_in_natal_2_or_8 = any(h in (2, 8) for h in ctx.houses_transited.get("saturn", []))
    for body in SLOW:
        houses = ctx.houses_transited[body]
        hits = [h for h in ctx.heavy_hits + ctx.jupiter_hits if h["body"] == body]
        parts = [f"{NAMES[body]} through natal house{'s' if len(houses) > 1 else ''} {', '.join(map(str, houses))}"]
        if hits:
            seen_keys = []
            for h in hits:
                key = (h["aspect"], h["natal_point"])
                if key not in seen_keys:
                    seen_keys.append(key)
            parts.append("; " + ", ".join(f"{a} {POINT[p]}" for a, p in seen_keys))
        ctx.themes.append("".join(parts))
    return ctx
