# Phase prompts

Run one phase per session, in plan mode. Do not start the next phase until its
tests pass and the screen looks right to you. Each prompt assumes CLAUDE.md is
in the project folder. Suggested model is in brackets.

Order follows your priorities: accurate engine and time travel first, then
transits and returns (the inputs the finder needs), then the finder and
astrocartography, and the tertiary features last.

## Phase 1: Engine and golden tests [Fable 5.1]

```text
Read CLAUDE.md. Set up the backend: FastAPI app, pyswisseph with .se1 data
files in /data/ephe (write scripts/fetch_data.py to download them). Build
two separate functions: planets_at(jd_ut, settings) returning longitudes,
latitudes, declinations and speeds (for retrograde), and houses_at(jd_ut,
lat, lon, settings) returning cusps, ASC and MC. calculate_chart() combines
them. Use the golden charts in /golden. Write the tests first, then the
code, and show me the test results. Also show the UTC offset logic and how
you flag uncertain historical time zones.
```

## Phase 2: Wheel, time travel and location lock [Opus 5.5]

```text
Build the frontend: chart entry form (city search from GeoNames with
autocomplete, date, time, time confidence), ChartSubject library with tags
and search, and the natal wheel in SVG per the display requirements in
CLAUDE.md, with the table view toggle. Add time stepping forward and back by
second, minute, hour, day, week, month, year and a custom step, plus a fluid
spin mode (hold or drag to play time at a chosen speed) that stays smooth.
Add location lock: freeze the moment and change only the place, so only
angles and cusps move. Test label spreading with four planets within 6
degrees. Screenshot desktop and phone widths and fix anything hard to read.
```

## Phase 3: Transits and the year ahead [Fable 5.1 for solvers, Opus for UI]

```text
Add a transit bi-wheel (natal inside, transits outside) using the Phase 2
time controls and a now button. Let me drag any transit planet around the
wheel: solve for the datetime when it reaches that degree, and when there
are several (retrograde), offer previous and next exact dates. Then build a
year-ahead report from one birthday to the next: every exact transit to
natal planets and angles, with all retrograde passes, ingresses into natal
houses, and stations near natal points. Make the aspect set and orbs
settings. Write tests for the exact-time solver first.
```

## Phase 4: Solar and lunar returns [Fable 5.1]

```text
Add solar returns: solve the exact SR instant for any year to under 1
second, show the SR chart for any location via location lock, a bi-wheel
against natal, and the SR Ascendant's natal house. Show the previous SR and
the base SR (home location) side by side with the selected one. Default
tropical non-precessed with a precession toggle. Add lunar returns the same
way. Add golden tests for three SR charts I will copy from astro.com.
```

## Phase 5: Aimed solar return finder [Fable 5.1]

```text
Build the finder described in CLAUDE.md, reading rules/rules.yaml (do not
hardcode rules). It must consider natal, the coming year's transits (Phase 3
report), the previous SR and the base SR. Before coding, list how you
propose each of those four inputs affects the score and wait for my answers;
I own Discepolo's "Solar Returns", "Transits and Solar Returns" and "Lunar
Returns". Pipeline: SR instant, natal cusps, global 1 degree grid with ocean
mask and 0.25 degree refinement, then every GeoNames city above the
population floor within the airport distance of an OurAirports large airport
with scheduled service. For each result: score, plain-language explanation,
star rating, robustness margin (degrees to the nearest flipping cusp, and
survival under birth time +/- my uncertainty), and what it fixes or worsens
versus the base SR. Show the heat map, ranked list with airport code and
distance, local SR date and time, and the year's major transits beside it.
First write unit tests for the rule engine using hand-made charts.
```

## Phase 6: Astrocartography [Fable 5.1 for line and paran math, Opus for map]

```text
Add astrocartography to the finder map, per CLAUDE.md: ASC, DSC, MC, IC lines
per body with toggles, parans as latitude lines with a list of pairs and
angles, and a shaded orb band around every line (width a setting). Clicking
the map or searching a city opens the relocated chart there via location
lock and lists which lines and parans are within orb. Works for natal, any
SR, and any moment. Test line positions against astro.com's AstroClick
Travel map for my chart at a few cities.
```

## Phase 7: Polish [Opus 5.5]

```text
Add PNG and PDF export of any wheel and map, a one-year outcome note on each
solar return, and encrypted local backups. Then do a full review: run every
test, check every screen at phone width, and list anything that still feels
slow or confusing.
```

## Phase 8: Tertiary features [Opus 5.5, Fable for zodiacal releasing]

```text
Add three small modules, one at a time, asking me about conventions first.
1. Vedic gemstone view per CLAUDE.md: lagna and lord, house lords, functional
   benefics and malefics, yogakaraka, natural and chara karakas. Ask me which
   functional-status table to use.
2. Secondary progressions as a tri-wheel option with progressed-to-natal
   aspects and a progressed-angle method setting.
3. Zodiacal releasing from Spirit and Fortune with every convention a
   setting, printed on the timeline.
```

## Audit [Fable 5.1, fresh session that did not write the code]

```text
You did not write this code. Audit the calculation engine, the transit and
SR solvers, the finder rule engine and the astrocartography math against
CLAUDE.md and the golden tests. Look for silent errors: time zone handling,
retrograde edge cases, house assignment near cusps, line positions near the
poles. Report findings ranked by severity with a failing test for each. Do
not fix anything yet.
```
