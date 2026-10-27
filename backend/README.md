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
