"""Shared fixtures: golden charts from /golden (gitignored, real birth data)."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = ROOT / "golden"

SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]

PLANET_KEYS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
EXTRA_KEYS = ["mean_node", "true_node", "chiron"]


def parse_longitude(text: str) -> float:
    """'Tau 5 39 32' -> 35.6589 degrees."""
    sign, d, m, s = text.split()
    return SIGNS.index(sign) * 30 + int(d) + int(m) / 60 + int(s) / 3600


def parse_signed(text: str) -> float:
    """'-0 1 19' -> -0.0219 deg; '0 58 26' -> 0.9739 deg."""
    neg = text.strip().startswith("-")
    d, m, s = text.replace("-", "").split()
    val = int(d) + int(m) / 60 + int(s) / 3600
    return -val if neg else val


def parse_ns(text: str) -> float:
    """'3 57 52 S' -> -3.9644 deg."""
    d, m, s, hemi = text.split()
    val = int(d) + int(m) / 60 + int(s) / 3600
    return -val if hemi == "S" else val


def angle_diff(a: float, b: float) -> float:
    """Smallest absolute difference between two longitudes in degrees."""
    return abs((a - b + 180) % 360 - 180)


class GoldenChart:
    def __init__(self, path: Path):
        self.path = path
        raw = yaml.safe_load(path.read_text())
        self.name = raw["name"]
        self.datetime_local = datetime.strptime(str(raw["datetime_local"]), "%Y-%m-%d %H:%M")
        self.datetime_utc = datetime.strptime(str(raw["datetime_utc"]), "%Y-%m-%d %H:%M")
        self.timezone = raw["timezone"]
        self.utc_offset_used = raw["utc_offset_used"]
        self.lat = float(raw["lat"])
        self.lon = float(raw["lon"])
        self.house_system = raw["house_system"]
        self.zodiac = raw["zodiac"]
        self.jd_tt = float(raw["jd_tt"])
        self.delta_t_sec = float(raw["delta_t_sec"])
        self.expect_flags = raw.get("expect_flags", [])
        self.planets = {}
        for key, row in raw["planets"].items():
            self.planets[key] = {
                "lon": parse_longitude(row["lon"]),
                "house": int(row["house"]),
                "speed": parse_signed(row["speed"]),
                "lat": parse_ns(row["lat"]),
                "dec": parse_ns(row["dec"]),
                "retrograde": bool(row.get("retrograde", False)),
            }
        self.cusps = {int(k): parse_longitude(v["lon"]) for k, v in raw["cusps"].items()}
        self.cusp_dec = {int(k): parse_ns(v["dec"]) for k, v in raw["cusps"].items()}

    def __repr__(self) -> str:
        return f"<Golden {self.path.name}: {self.name}>"


def load_golden_charts() -> list[GoldenChart]:
    files = sorted(GOLDEN_DIR.glob("natal_*.yaml"))
    return [GoldenChart(p) for p in files]


GOLDEN = load_golden_charts()


def pytest_collection_modifyitems(config, items):
    if not GOLDEN:
        skip = pytest.mark.skip(reason=f"No golden charts in {GOLDEN_DIR} (see golden/README.md). Tests cannot prove accuracy.")
        for item in items:
            if "golden" in item.keywords:
                item.add_marker(skip)


def pytest_configure(config):
    config.addinivalue_line("markers", "golden: needs the astro.com golden charts in /golden")


@pytest.fixture(params=GOLDEN or [None], ids=[g.path.stem for g in GOLDEN] or ["no-golden"])
def golden(request) -> GoldenChart:
    if request.param is None:
        pytest.skip("no golden charts available")
    return request.param
