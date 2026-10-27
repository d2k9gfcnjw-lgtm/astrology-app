# Phase prompts

Run one phase per session, in plan mode. Do not start the next phase until its
tests pass and the screen looks right to you. Each prompt assumes CLAUDE.md is
in the project folder. Suggested model is in brackets.

## Phase 1: Engine and golden tests [Fable 5.1]

```text
Read CLAUDE.md. Set up the backend: FastAPI app, pyswisseph with .se1 data
files in /data/ephe (write scripts/fetch_data.py to download them), and a
calculate_chart() function returning planet longitudes, speeds (for
retrograde), house cusps, ASC and MC for any datetime + location + settings.
Use the golden charts in /golden. Write the tests first, then the code, and
show me the test results. Also show the UTC offset logic and how you flag
uncertain historical time zones.
```

## Phase 2: Natal wheel and chart library [Opus 5.5]

```text
Build the frontend: chart entry form (city search from GeoNames with
autocomplete, date, time, time confidence), ChartSubject library with tags
and search, and the natal wheel in SVG per the display requirements in
CLAUDE.md. Include the table view toggle. Test label spreading with a chart
that has four planets within 6 degrees. Screenshot desktop and phone widths
and fix anything hard to read before reporting back.
```

## Phase 3: Houses toggle and Vedic view [Opus 5.5, Fable for the dasha math]

```text
Add the Placidus / Whole Sign toggle with the high-latitude fallback. Then
add a Vedic tab for the same chart: sidereal Lahiri (other ayanamsas as a
setting), whole sign, mean node, North and South Indian chart styles,
nakshatra and pada for every body, Vimshottari dasha periods to 3 levels
with current period highlighted, and the D9 navamsa. Add golden tests from
a trusted Jyotish source I will provide.
```

## Phase 4: Transits you can move [Fable 5.1 for drag solver, Opus for UI]

```text
Add a transit bi-wheel (natal inside, transits outside) with a time
scrubber (minute, hour, day, month, year steps) and a now button. Let me
drag any transit planet around the wheel: solve for the datetime when it
reaches that degree, and when there are several (retrograde), offer previous
and next exact dates. List exact transit-to-natal aspects for the visible
window with dates. Keep it smooth on a phone width.
```

## Phase 5: Progressions and zodiacal releasing [Fable 5.1]

```text
Add secondary progressions (day for a year) as a tri-wheel option and a
progressed-to-natal aspect list with exact dates. Make progressed-angle
method a setting and show the active one. Then add zodiacal releasing from
Spirit and Fortune: day/night lot formulas, period lengths by sign, L1 to L4,
peak periods angular to Fortune, loosing of the bond. Every convention is a
setting with my choice printed on the timeline. Before coding, list each
convention you need me to decide and wait for my answers.
```

## Phase 6: Solar and lunar returns [Fable 5.1]

```text
Add solar returns: solve the exact SR instant for any year to under 1
second, show the SR chart for any location, a bi-wheel against natal, and
the SR Ascendant's natal house. Default tropical non-precessed with a
precession toggle. Add lunar returns the same way. Add golden tests for
three SR charts I will copy from astro.com.
```

## Phase 7: Aimed solar return finder [Fable 5.1]

```text
Build the finder described in CLAUDE.md, reading rules/rules.yaml (do not
hardcode rules). Pipeline: SR instant, natal cusps, global 1 degree grid with
ocean mask and 0.25 degree refinement, then every GeoNames city above the
population floor within the airport distance of an OurAirports large airport
with scheduled service. For each result compute a score, a plain-language
explanation, a star rating, and a robustness margin (degrees to the nearest
flipping cusp, and survival under birth time +/- my uncertainty). Show the
heat map, the ranked list with airport code and distance, local SR date and
time, and a comparison with my home location. First write unit tests for the
rule engine using hand-made charts where I know the right answer.
```

## Phase 8: Polish [Opus 5.5]

```text
Add astrocartography lines on the finder map, PNG and PDF export of any
wheel, a one-year outcome note on each solar return, and encrypted local
backups. Then do a full review: run every test, check every screen at phone
width, and list anything that still feels slow or confusing.
```

## Audit [Fable 5.1, fresh session that did not write the code]

```text
You did not write this code. Audit the calculation engine, the SR solver,
zodiacal releasing and the finder rule engine against CLAUDE.md and the
golden tests. Look for silent errors: time zone handling, retrograde edge
cases, house assignment near cusps, day/night chart logic. Report findings
ranked by severity with a failing test for each. Do not fix anything yet.
```
