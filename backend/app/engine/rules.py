"""Reads rules/rules.yaml (the owner's Discepolo rules). Nothing astrological is hardcoded here."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "rules.yaml"


@dataclass(frozen=True)
class Rules:
    cusp_orb_degrees: float
    angular_orb_degrees: float
    sr_asc_hard_filter_houses: list[int]
    mars_saturn_allowed_houses: list[int]
    stellium_min_bodies: int
    stellium_1_12_text: str
    stellium_8_text: str
    mars_saturn_text: str
    sr_asc_text: str
    raw: dict


def _filter(raw: dict, rule_id: str) -> dict:
    for f in raw.get("hard_filters", []):
        if f.get("id") == rule_id:
            return f
    return {}


@lru_cache(maxsize=1)
def load_rules(path: Path | str = RULES_PATH) -> Rules:
    raw = yaml.safe_load(Path(path).read_text())
    ms = _filter(raw, "mars_saturn_same_house")
    s112 = _filter(raw, "stellium_1_12_reads_as_asc_in_12")
    s8 = _filter(raw, "stellium_8_reads_as_asc_in_12")
    asc = _filter(raw, "sr_asc_in_natal_1_6_12")
    return Rules(
        cusp_orb_degrees=float(raw.get("cusp_orb_degrees", 2.5)),
        angular_orb_degrees=float(raw.get("angular_orb_degrees", 12)),
        sr_asc_hard_filter_houses=list(asc.get("houses", [1, 6, 12])),
        mars_saturn_allowed_houses=list(ms.get("allowed_houses", [3, 9])),
        stellium_min_bodies=int(s112.get("min_bodies", 3)),
        stellium_1_12_text=str(s112.get("description", "")).strip(),
        stellium_8_text=str(s8.get("description", "")).strip(),
        mars_saturn_text=str(ms.get("description", "")).strip(),
        sr_asc_text=str(asc.get("description", "")).strip(),
        raw=raw,
    )
