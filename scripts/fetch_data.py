#!/usr/bin/env python3
"""Download the data files the app needs into /data (gitignored).

Phase 1: Swiss Ephemeris .se1 files from the official Astrodienst GitHub
mirror (https://github.com/aloistr/swisseph, folder ephe/). Later phases add
GeoNames cities, OurAirports and Natural Earth to this same script.

Usage:  python3 scripts/fetch_data.py [--ephe-only] [--force]
Works with the system Python 3 (standard library only).
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EPHE_DIR = DATA / "ephe"
EPHE_BASE_URL = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/"

# Each file covers 600 years. _06 = 600-1200 CE, _12 = 1200-1800, _18 = 1800-2400, _24 = 2400-3000.
# sepl = planets, semo = Moon, seas = main asteroids incl. Chiron (valid 675-4650 CE).
EPHE_FILES = [
    f"{prefix}_{block}.se1"
    for prefix in ("sepl", "semo", "seas")
    for block in ("06", "12", "18", "24")
]
MIN_SIZE_BYTES = 100_000  # a truncated download or an HTML error page is smaller


def download(url: str, dest: Path) -> int:
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "astrology-app fetch_data"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as out:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)
    size = tmp.stat().st_size
    if size < MIN_SIZE_BYTES or tmp.read_bytes()[:8] == b"<!DOCTYP":
        tmp.unlink()
        raise RuntimeError(f"{dest.name}: download looks wrong ({size} bytes)")
    tmp.replace(dest)
    return size


def fetch_ephemeris(force: bool) -> bool:
    EPHE_DIR.mkdir(parents=True, exist_ok=True)
    ok = True
    for name in EPHE_FILES:
        dest = EPHE_DIR / name
        if dest.exists() and dest.stat().st_size >= MIN_SIZE_BYTES and not force:
            print(f"  have   {name} ({dest.stat().st_size:,} bytes)")
            continue
        try:
            size = download(EPHE_BASE_URL + name, dest)
            print(f"  fetched {name} ({size:,} bytes)")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"  FAILED {name}: {exc}", file=sys.stderr)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ephe-only", action="store_true", help="only the Swiss Ephemeris files (default for now)")
    parser.add_argument("--force", action="store_true", help="re-download files that are already present")
    args = parser.parse_args()
    print(f"Swiss Ephemeris files -> {EPHE_DIR}")
    ok = fetch_ephemeris(args.force)
    if not ok:
        print("Some files failed. Re-run the script; it skips files already present.", file=sys.stderr)
        return 1
    print("Done. Ephemeris covers 600 CE to 3000 CE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
