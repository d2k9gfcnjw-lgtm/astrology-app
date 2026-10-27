# Phase 1 plan: engine and golden tests

Status: approved 27 Oct 2026 and implemented on this branch; all 244 tests pass.

## What Phase 1 delivers

A Python backend that turns a birth moment and place into exact positions,
tested against the five astro.com data sheets in `golden/`. No wheel, no
database, no frontend yet (those are Phase 2).

## 0. Tooling (needs your OK)

The Mac has only Python 3.9 and no Homebrew or Node. CLAUDE.md asks for
Python 3.12. Recommended: install `uv` (Astral's Python tool) with its
official one-line installer. It puts itself and a private Python 3.12 under
your home folder, needs no admin password, and nothing else on the Mac
changes. `uv` also creates the virtualenv and installs pyswisseph, FastAPI,
numpy, timezonefinder and pytest from `backend/pyproject.toml`.

Fallback if you prefer not to: the python.org 3.12 installer (a click-through
.pkg), then plain `venv` and `pip`.

Node is not needed until Phase 2.

## 1. Golden charts → test data

Transcribe the five sheets into `golden/natal_01.yaml` … `natal_05.yaml`
(gitignored, never pushed): name, local time, time zone, offset used, lat/lon,
Julian Day (TT) and ΔT, and for Sun through Pluto plus Mean Node, True Node
and Chiron: longitude, house number, speed, latitude, declination; and the 12
Placidus cusps with declinations.

| # | Sheet | Local time | UT | Offset | Why it matters |
|---|-------|-----------|----|--------|----------------|
| 1 | your natal chart (US East, summer) | evening | next day | −4 EDT | date rolls over in UT |
| 2 | a real person, US East, 1960s | early morning | same day | −5 EST | pre-1970 ("check offset") |
| 3 | Santiago, 12 Jan 1955 (synthetic) | 07:22 | 11:22 | −4 | Southern Hemisphere and pre-1970 |
| 4 | Oslo, 23 Jul 1992 (synthetic) | 04:23 | 02:23 | +2 CEST | 59°55′ N, Placidus still valid |
| 5 | Chicago, 3 Nov 2024 (synthetic) | 07:50 | 13:50 | −6 CST | DST ended at 02:00 that morning |

All five offsets agree with the IANA time zone database, so the automatic
offset will reproduce them. Charts 2 and 3 are still flagged "check offset".

## 2. Tests first (pytest, `backend/tests/`)

Written before any engine code; they fail until the engine exists.

- `test_golden.py`: for each YAML, planet longitudes within 1′, cusps and
  ASC/MC within 2′; also latitude and declination within 1′, speed within 2″
  per day, house number of each planet exact, Julian Day (TT) within 1 second,
  ΔT within 0.5 s. Retrograde flag must match the ℞ on the sheet.
- `test_time.py`: local → UT for all five charts; the Chicago 02:00 DST fold
  (ambiguous hour) and a spring-forward gap are reported, not guessed; years
  before 1970 and wartime years (1914–1919, 1939–1947) carry the
  "check offset" flag; a manual offset override wins over the zone; a place
  with no zone (open ocean) requires an explicit offset.
- `test_relocation.py`: `planets_at` ignores location; `houses_at` for the
  same instant in Chicago vs Oslo changes only cusps and angles.
- `test_houses.py`: Placidus at 69.6° N (Tromsø) falls back to Whole Sign
  with a warning; Whole Sign cusps are 0° of each sign from the ASC sign.
- `test_ephemeris.py`: with the data folder missing or empty the engine
  raises at startup, and every position call asserts the Swiss Ephemeris
  flag (never Moshier).
- `test_extras.py`: Part of Fortune by sect (reversed at night) and the
  day-only toggle, computed from golden Sun/Moon/ASC; True vs Mean Node
  selection; Lilith mean vs true selection; sidereal = tropical − Lahiri
  ayanamsa. (Lilith and Fortune are not on the sheets, so these are
  self-consistency tests until you add astro.com values.)

## 3. Engine (`backend/app/engine/`)

- `ephemeris.py`: sets the ephemeris path to `data/ephe`, checks the needed
  `.se1` files exist, fails loudly otherwise. Wraps `swe.calc_ut` and checks
  the returned flags say SWIEPH.
- `time.py`: `resolve_moment(local_datetime, lat, lon, tz_name=None,
  offset_override=None)` → UT datetime, JD (UT), JD (TT), ΔT, offset used,
  zone name, and a list of flags: `pre_1970`, `wartime`, `ambiguous_dst`,
  `nonexistent_local_time`, `no_zone_for_location`, `offset_overridden`.
  Zone comes from `timezonefinder` at the coordinates unless given.
- `planets.py`: `planets_at(jd_ut, settings)` → per body: longitude,
  latitude, distance, speed, declination, retrograde flag. Bodies: Sun …
  Pluto, plus optional node (true/mean), Chiron, Lilith (mean/true).
- `houses.py`: `houses_at(jd_ut, lat, lon, settings)` → 12 cusps, ASC, MC,
  DSC, IC, vertex, ARMC, obliquity, cusp declinations, plus
  `house_system_used` and a warning when Placidus fell back to Whole Sign
  (|lat| ≥ 66°). Sidereal applied here too so cusps and planets agree.
- `chart.py`: `calculate_chart(subject_input, settings)` = resolve time,
  planets_at, houses_at, then derived values: house of each planet, Part of
  Fortune (sect-aware), and the stored provenance block CLAUDE.md requires
  (local time, offset used, zone, lat/lon, house system, zodiac, ayanamsa,
  node type).
- `models.py`: pydantic models for settings, input and output.

Settings defaults: tropical, Placidus, True Node, mean Lilith, Fortune
reversed at night, Lahiri when sidereal, cusp fallback 66°.

## 4. API (`backend/app/main.py`, FastAPI)

- `GET /api/health`: ephemeris path, files found, Swiss Ephemeris version.
- `POST /api/chart`: body = birth data + settings → full chart JSON.
- `POST /api/houses`: jd_ut + lat/lon + settings → cusps only (the location
  lock primitive Phase 2 and the finder reuse).
- `POST /api/time/resolve`: shows offset, zone and flags before saving.

## 5. Data script (`scripts/fetch_data.py`)

Downloads Swiss Ephemeris `.se1` files from the official Astrodienst GitHub
mirror into `data/ephe/`: planets, Moon and asteroids files covering
600 CE to 3000 CE (about 15 MB; Chiron's orbit is only valid 675–4650 CE
anyway). Verifies each file by size, skips files already present. Cities,
airports and land polygons are added to the same script in later phases.

## 6. Done means

- All tests pass; I post the pytest output and a table of the largest
  deviation per chart.
- `uvicorn` runs and `POST /api/chart` returns a chart.
- Commits on the working branch, pushed; `golden/` and `data/` stay local.

## Questions for you

1. OK to install `uv` and Python 3.12 the way described in section 0?
2. Wartime flag years: I propose 1914–1919 and 1939–1947 for every country.
   Say if you want a different range.

Nothing else is ambiguous enough to need a decision before coding.
