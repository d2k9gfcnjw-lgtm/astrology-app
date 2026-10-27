# Project: Personal astrology workstation

## Who this is for
One serious practitioner of Western tropical astrology who also uses Jyotish.
Accuracy beats features. A wrong chart is worse than a missing feature.

## What this app is
A web app that runs locally: Python backend + React frontend, opened in the
browser at a localhost address. Code, data files and saved charts live in this
folder. It must work with no internet. Hosting online (for phone access) is a
later, optional step and must not change the architecture.

## Non-negotiable accuracy rules
- All positions come from Swiss Ephemeris (pyswisseph) with the .se1 data files,
  never Moshier fallback. Fail loudly if data files are missing.
- Every chart stores: local time, UTC offset actually used, time zone name,
  lat/long, house system, zodiac, ayanamsa (if sidereal), node type.
- Every calculation is covered by tests against the golden charts in /golden,
  copied from astro.com. Planet longitudes must match within 1 arc minute,
  house cusps within 2 arc minutes.
- Never guess a time zone silently. Show the offset used and allow override.
  Flag births before 1970 and wartime years as "check offset".

## Stack
- Backend: Python 3.12, FastAPI, pyswisseph, numpy, timezonefinder, zoneinfo.
- Frontend: React + TypeScript (Vite). Chart wheels in SVG; D3 for drag.
- Map: MapLibre GL + deck.gl heat map layer, OpenStreetMap-based tiles.
- Storage: SQLite (local file). Birth data encrypted at rest.
- Data files in /data: Swiss Ephemeris .se1, GeoNames cities15000,
  OurAirports airports.csv, Natural Earth land polygons.
  /data is gitignored; provide a script (scripts/fetch_data.py) to download it.

## Core model
One entity: ChartSubject (person, event, place, question) with tags,
notes, birth/event datetime, location, and a time-confidence field
(exact, within 5 min, within 30 min, unknown).

## Chart settings (user toggles, saved per chart)
- Zodiac: tropical (default) or sidereal.
- Houses: Placidus (default) or Whole Sign. Fall back to Whole Sign with a
  warning when Placidus fails at high latitude (about 66 degrees and above).
- Bodies: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune,
  Pluto. Optional toggles: True/Mean Node, Chiron, Lilith, Part of Fortune.

## Display requirements
- Wheel is easy to read at a glance: element colors per sign, clear glyphs,
  degree and minute next to every planet (e.g. 14°32'), retrograde marker,
  house cusp degrees, aspect lines colored by aspect type.
- Automatic label spreading for stelliums, with leader lines to true degree.
- A table view of the same data, always one tap away.
- Responsive down to phone width. (Installable home-screen app only matters
  once hosted; build responsive now, PWA later.)

## Feature modules (build in this order; one phase per session)
1. Natal chart engine + golden tests.
2. Natal wheel + table view + chart library (create, search, tag).
3. House system toggle, Vedic view (Lahiri default, North and South Indian
   styles, nakshatras, Vimshottari dasha, D9 navamsa).
4. Transits: bi-wheel, time scrubber, drag a transit planet to move time
   (handle retrograde ambiguity with next/previous exact dates).
5. Secondary progressions (choose progressed-angle method; show which) and
   zodiacal releasing from Spirit and Fortune, every convention a setting,
   shown as a zoomable timeline with L1 to L4, peaks, loosing of the bond.
6. Solar returns and lunar returns: exact moment, relocation to any place,
   tropical non-precessed default with a precession toggle.
7. Aimed solar return finder (Ciro Discepolo method). See section below.
8. Astrocartography lines on the same map, PNG/PDF export, outcome journal.

## Aimed solar return finder
- The SR instant is global; only angles and houses vary by place.
- Rules live in rules/rules.yaml (weights, hard filters, cusp orb, goal
  profiles), never hardcoded. Every score must explain itself in plain language.
- Inputs: person, SR year, goal profile, population floor, max distance to
  airport, include/exclude countries, birth time uncertainty.
- Outputs: global heat map (ocean and empty land masked), ranked cities near
  large airports with scheduled service, local date/time of the SR there,
  placements summary, score, star rating, robustness margin in degrees,
  and comparison with the home location.

## Model use (owner's plan)
- Fable 5.1: phase planning, zodiacal releasing, SR timing solver, retrograde
  transit drag, the rule engine, and independent audits in a fresh session.
- Opus 5.5: everyday building. Sonnet 5.5: small visual and copy tweaks.

## How to work
- Start each module in plan mode. Wait for my approval before coding.
- Write tests first for any calculation. Run them before saying done.
- After UI work, take a screenshot and check it yourself.
- Small commits with clear messages. Never delete user chart data.
- Never commit birth data, the SQLite file, or /data to git.
- If an astrology convention is ambiguous, ask me instead of choosing.
- Detailed background lives in docs/reference.md; phase prompts in
  docs/phase-prompts.md; open decisions in docs/reference.md under
  "Open questions".
