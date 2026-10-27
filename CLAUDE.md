# Project: Personal astrology workstation

## Who this is for
One serious practitioner of Western tropical astrology, for personal use only
(never offered to others, so the free AGPL Swiss Ephemeris license applies).
Accuracy beats features. A wrong chart is worse than a missing feature.

## Priorities (owner's words, in order)
1. Aimed solar return finder (Ciro Discepolo method) and astrocartography.
2. Accurate charts with a wheel you can spin through time fluidly.
3. Tertiary: Vedic (only for gemstone checks), secondary progressions,
   zodiacal releasing. Build these last; keep them simple.

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

## Time travel and relocation (core interaction)
- Step the chart forward or back by second, minute, hour, day, week, month,
  year (and custom). Also a fluid "spin" mode: hold or drag to play time
  continuously at a chosen speed, smooth enough to watch the angles turn.
- Location lock: freeze the moment (planet positions do not move) and change
  only the place, by city search or by clicking the map. Only angles and
  house cusps change. This is the same operation the SR finder and
  relocated charts use; one function, `houses_at(jd_ut, lat, lon, settings)`,
  separate from planet positions.

## Feature modules (build in this order; one phase per session)
1. Engine + golden tests: planets, houses, angles; houses computed
   separately from planets so any moment can be relocated.
2. Natal wheel + table view + chart library, time stepping (second to year),
   fluid spin, and location lock.
3. Transits: bi-wheel, drag a transit planet to move time (next/previous exact
   dates for retrograde passes), and a year-ahead transit report from one
   birthday to the next with every exact hit, including all retrograde passes.
4. Solar and lunar returns: exact instant, relocation, bi-wheel with natal,
   SR Ascendant's natal house, previous SR and home ("base") SR side by side.
5. Aimed solar return finder (Ciro Discepolo method). See section below.
6. Astrocartography: lines, parans, orb bands, click-to-relocate charts.
7. Polish: PNG/PDF export, outcome journal, encrypted backups.
8. Tertiary: Vedic gemstone view, secondary progressions, zodiacal releasing.

## Aimed solar return finder
- The SR instant is global; only angles and houses vary by place.
- Rules live in rules/rules.yaml (weights, hard filters, cusp orb, goal
  profiles), never hardcoded. Every score must explain itself in plain language.
- It always considers four charts together:
  1. the natal chart (natal houses for the SR Ascendant rule, intercepted signs);
  2. the transits of the coming year, birthday to birthday (which natal points
     and houses are under pressure or supported, with exact dates);
  3. the previous solar return (what the current year set up);
  4. the base solar return: the chart if the native stays home.
  How each of these changes the score is a rule in rules.yaml with status
  "confirm" until the owner checks it against Discepolo's books. Ask the owner
  before inventing any weighting.
- Inputs: person, SR year, home location, goal profile, population floor,
  max distance to airport, include/exclude countries, birth time uncertainty.
- Outputs: global heat map (ocean and empty land masked), ranked cities near
  large airports with scheduled service, local date/time of the SR there,
  placements summary, score, star rating, robustness margin in degrees,
  what it fixes or worsens compared with the base SR, and the year's major
  transits listed beside the result.

## Astrocartography
- Lines: ASC, DSC, MC, IC for each body, drawn on the same MapLibre map as
  the finder, toggle per planet and per angle.
- Parans: latitudes where two bodies are angular at the same time, drawn as
  horizontal lines; list them with the pair and angles involved.
- Orb of influence: a shaded band around each line, width a setting (km or
  degrees), with strength fading toward the edge.
- Click anywhere (or search a city) to open the relocated chart for that place
  using location lock; show which lines and parans are within orb there.
- Works for natal, any solar return, and any moment.

## Vedic (tertiary, gemstone checks only)
- Defaults: Lahiri ayanamsa, whole sign houses, mean node, North Indian chart.
  All four are settings.
- Show: lagna and lagna lord, lord of every house, functional benefics and
  malefics for the lagna, yogakaraka, and karakas (natural and Jaimini chara;
  7 or 8 chara karakas is a setting). Schools disagree on functional status:
  ask the owner which table to use before coding it.
- Nakshatras, dasha and D9 only if asked later.

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
