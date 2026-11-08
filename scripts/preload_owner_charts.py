#!/usr/bin/env python3
"""Load the owner's local golden charts (natal_01 and sr_01..03, never in git) into the encrypted chart library.

Run from the repo root:  backend/.venv/bin/python scripts/preload_owner_charts.py
Safe to run again: charts that already exist (same name) are skipped.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.storage import ChartLibrary, SubjectIn  # noqa: E402

GOLDEN = ROOT / "golden"


def load(name: str) -> dict:
    return yaml.safe_load((GOLDEN / name).read_text())


def main() -> int:
    lib = ChartLibrary()
    existing = {s.name for s in lib.list(include_deleted=True)}
    natal = load("natal_01.yaml")
    items = [SubjectIn(name=natal["name"].replace(" natal", ""), kind="person", tags=["me", "natal"], notes="Golden chart (astro.com).",
                       datetime_local=datetime.strptime(str(natal["datetime_local"]), "%Y-%m-%d %H:%M"), time_confidence="exact",
                       place_name=natal.get("place", ""), lat=float(natal["lat"]), lon=float(natal["lon"]), timezone=natal["timezone"])]
    for f in sorted(p.name for p in GOLDEN.glob("sr_*.yaml")):
        sr = load(f)
        place = sr.get("place", "")
        items.append(SubjectIn(name=f"ASR {sr['year']} {place.split(',')[0] or f}", kind="event", tags=["solar-return", "asr", str(sr["year"])],
                               notes=f"Aimed solar return (astro.com): {sr['name']}.",
                               datetime_local=datetime.strptime(str(sr["datetime_local"]), "%Y-%m-%d %H:%M"), time_confidence="exact",
                               place_name=place, lat=float(sr["lat"]), lon=float(sr["lon"]), timezone=sr["timezone"]))
    plans = GOLDEN / "asr_plans.yaml"
    if plans.exists():
        from zoneinfo import ZoneInfo
        from app.engine.chart import calculate_chart
        from app.engine.models import ChartInput, Settings
        from app.engine.returns import solar_return
        pl = yaml.safe_load(plans.read_text())
        nat = load(pl["natal"])
        chart = calculate_chart(ChartInput(datetime_local=datetime.strptime(str(nat["datetime_local"]), "%Y-%m-%d %H:%M"), lat=float(nat["lat"]),
                                           lon=float(nat["lon"]), timezone=nat["timezone"]), Settings())
        for q in pl["plans"]:
            sr = solar_return(chart, int(q["year"]), float(q["lat"]), float(q["lon"]), place_name=q.get("place", q["name"]))
            local = datetime.fromisoformat(sr.local_datetime).replace(tzinfo=None)
            items.append(SubjectIn(name=f"ASR {q['year']} {q['name']} ({q.get('status', 'planned')})", kind="event", tags=["solar-return"] + list(q.get("tags", [])),
                                   notes=f"Computed by the app: {sr.utc_datetime} UT at {q.get('place', q['name'])}.", datetime_local=local,
                                   time_confidence="exact", place_name=q.get("place", q["name"]), lat=float(q["lat"]), lon=float(q["lon"]), timezone=sr.timezone))
    for s in items:
        if s.name in existing:
            print(f"  have    {s.name}")
            continue
        lib.create(s)
        print(f"  added   {s.name}")
    print(f"Library: {lib.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
