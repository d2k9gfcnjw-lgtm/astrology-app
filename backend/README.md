# Backend (Phase 1: engine)

Python 3.12, FastAPI, pyswisseph. Managed with [uv](https://docs.astral.sh/uv/).

## First time

```bash
python3 scripts/fetch_data.py        # Swiss Ephemeris files -> data/ephe (run from the repo root)
cd backend && uv sync                # creates .venv with Python 3.12 and every dependency
```

## Run

```bash
cd backend && uv run pytest -q                       # all tests (golden tests need /golden/*.yaml)
cd backend && uv run uvicorn app.main:app --reload   # API on http://127.0.0.1:8000 (docs at /docs)
```

## Layout

- `app/engine/ephemeris.py`: data-file check (fails loudly), Swiss Ephemeris wrapper that rejects Moshier.
- `app/engine/time.py`: local time -> UT and Julian Day; offset used, zone, and the "check offset" flags.
- `app/engine/planets.py`: `planets_at(jd_ut, settings)`: location independent.
- `app/engine/houses.py`: `houses_at(jd_ut, lat, lon, settings)`: the location-lock primitive.
- `app/engine/chart.py`: `calculate_chart()`, `relocate_chart()`, Part of Fortune, house placement.
- `app/main.py`: `/api/health`, `/api/time/resolve`, `/api/chart`, `/api/houses`.
- `tests/`: golden charts (`/golden/natal_*.yaml`, never committed), time zones, relocation, houses, ephemeris, extras, API.

## Golden chart file format

See `golden/README.md`. Strings are `"Sign deg min sec"` for longitudes, signed `"deg min sec"`
per day for speeds, and `"deg min sec N|S"` for latitudes and declinations.

## Phase 5: the finder

- `app/engine/finder/scoring.py`: the rule engine; every point from `rules/rules.yaml` with its sentence and page.
- `app/engine/finder/context.py`: the year's transit themes (slow planets, the book's orbs and aspects).
- `app/engine/finder/geo.py`: Natural Earth land mask, airports with scheduled service, candidate cities.
- `app/engine/finder/search.py`: SR instant, 1° grid with 0.25° refinement, city scoring, birth-time robustness, tiers, versus home.
- `POST /api/finder/run`, `GET /api/finder/land`. A world run takes about 15 seconds.
- Calibration: `reference/case-studies/2027-expected.yaml` (local) drives `tests/test_finder_search.py::test_katias_nine_places_2027`.

## Phase 6: astrocartography

- `app/engine/acg.py`: lines (in mundo default, zodiacal option), parans, distance to a line, what is within orb at a place.
- `POST /api/acg/lines`, `POST /api/acg/at`. Verified against astro.com AstroClick Travel readouts (local `golden/acg_01.yaml`); AstroClick draws the Mean Node.
