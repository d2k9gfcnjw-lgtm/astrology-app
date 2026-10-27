# Reference: Astrology App Build Plan

Exported from the planning doc, October 2026, with the licensing section corrected.

## Setup

| Piece | Recommendation | Why |
| --- | --- | --- |
| Where it lives | Web app running locally: code and chart data in this folder, opened in the browser at a local address. Host online later only for phone access. | Needs a real Python engine and large data files; keeps birth data private; works offline |
| Build tool | Claude Code (desktop app or terminal), plan mode on for each new phase | Sees every file, runs tests, rereads CLAUDE.md every session |
| Planning and hard parts | Fable 5.1: phase planning, zodiacal releasing, SR timing solver, retrograde transit drag, rule engine | Where a quiet mistake is costliest |
| Everyday building | Opus 5.5: wheel drawing, forms, map, fixes | Capable enough, stretches usage further |
| Independent audit | Fresh Fable 5.1 session that did not write the code | Keeps the work from grading itself |
| Small tweaks | Sonnet 5.5 for colors, layout, copy | Low-risk changes |
| Calculation engine | Python 3.12, FastAPI, pyswisseph, numpy | Same engine as astro.com |
| Front end | React + TypeScript (Vite), SVG wheel, D3 for dragging | Crisp at any size, every glyph clickable |
| World map | MapLibre GL, OpenStreetMap-based tiles, deck.gl heat map | No per-request fees |
| Storage | SQLite file on your machine | Private; Postgres only if hosted |
| Version control | Private GitHub repo | Roll back any phase; backup off your computer |

No astrology connector is needed. GitHub is the only connection that matters.

## Data sources

| Need | Source | License | Notes |
| --- | --- | --- | --- |
| Planets, houses, sidereal modes | Swiss Ephemeris via pyswisseph + .se1 files | AGPL or paid Professional License | Built on NASA JPL ephemerides |
| Cities | GeoNames cities15000 | Free, attribution | Population ranks real cities over villages |
| Airports | OurAirports airports.csv | Public domain | type = large_airport, scheduled_service = yes (about 1,174 worldwide) |
| Time zone for a coordinate | timezonefinder + IANA tz via zoneinfo | Free | Check pre-1970 offsets |
| Land vs ocean mask | Natural Earth land polygons | Public domain | Greys out ocean and empty land |
| Ground truth | astro.com charts saved by hand | Free | The /golden folder |

## Licensing (corrected)

Swiss Ephemeris is dual licensed: AGPL (free) or the Swiss Ephemeris
Professional License from Astrodienst (paid, valid 6 years).

What triggers obligations is who uses the software, not whether money changes hands:

- Using the app yourself, locally or hosted only for you: fine under AGPL.
- Charging clients for readings you produce with it: fine under AGPL. You sell
  your interpretation and chart images, not access to the program.
- Letting anyone else use a hosted version, free or paid: AGPL requires you to
  offer them the full source code of the whole app. To keep the code private,
  buy the Professional License instead.

Not legal advice. Before opening access to others, read Astrodienst's terms or
ask them directly.

## How the finder works

The SR instant is the same everywhere, so planet signs and degrees are fixed;
only angles and house cusps change with location.

1. Solve the exact SR moment (UT): transiting Sun reaches natal Sun longitude.
   Default tropical non-precessed; precession toggle for comparison.
2. Freeze planet positions at that instant.
3. Compute natal cusps from the birth place (needed for the SR Ascendant in
   natal houses rule).
4. Score a 1° global grid (about 60°S to 66°N), masking oceans and empty land;
   refine to 0.25° around the best areas.
5. Score every city above the population floor within the set distance of a
   large airport with scheduled service.
6. Stress-test: degrees to the nearest flipping cusp, and survival under birth
   time plus or minus the stated uncertainty.
7. Output: heat map plus ranked list (airport code and distance, local SR date
   and time, plain-language reason, margin, comparison with home).

Good zones appear as north to south bands, slightly tilted: the Ascendant
tracks local sidereal time, which tracks longitude (roughly 1° of longitude
moves the SR Ascendant about 1°).

Rules live in rules/rules.yaml. Rows marked "confirm" are assumptions to check
against Discepolo's books.

## Traps and upgrades

- Historical time zones: pre-1970, wartime and rural births often used local
  mean time. Show the offset used; allow override.
- Birth time precision: 4 minutes moves the Ascendant about 1°. Store time
  confidence; widen the finder's stress test to match.
- Placidus fails above about 66° latitude: fall back to whole sign with a warning.
- Lunar returns: build them in; aimed lunar returns later with the same engine.
- Astrocartography: the finder map can draw ASC, DSC, MC, IC lines cheaply.
- Zodiacal releasing conventions vary (lot formulas by sect, 360 vs 365.25 day
  years, Capricorn/Aquarius handling, loosing of the bond): every one a setting.
- Progressed angles: solar arc, Naibod, quotidian differ. Show the active one.
- Vedic defaults: Lahiri, whole sign, mean node, chart style, nakshatras,
  Vimshottari dasha, D9.
- Dragging a retrograding planet hits a degree several times: offer previous
  and next exact dates.
- Crowded degrees: label spreading with leader lines.
- One ChartSubject type for people, events, places, questions.
- Outcome journal: one-year follow-up per solar return to improve the rules.
- Privacy: local and encrypted by default.

## Verification checklist

- [ ] 5 golden natal charts pass (planets within 1', cusps within 2')
- [ ] Vedic chart matches a trusted Jyotish program (sign, nakshatra, dasha)
- [ ] Three past solar returns match astro.com to the minute, one relocated
- [ ] Zodiacal releasing matches a hand calculation for your chart
- [ ] Rule engine passes hand-built cases (one disqualified, one ranked first)
- [ ] Independent Fable audit in a fresh session

## Open questions

- [ ] Only for you, or will others ever use it? (license, local vs hosted)
- [ ] Which Discepolo books do you own? Check "confirm" rules against
      "Transits and Solar Returns" and "Aimed Solar and Lunar Returns"
- [ ] Zodiacal releasing conventions you follow
- [ ] Ayanamsa if not Lahiri; North or South Indian chart style
- [ ] Default population floor and airport distance
- [ ] Countries or regions to always exclude

## Sources

- Aimed Solar Revolutions: The 34 Golden Rules (Kerykeion):
  https://kerykeion.net/content/learn-astrology/branches-aimed-solar-revolutions
- Discepolo, Solar Returns, book description:
  https://www.buscalibre.cl/libro-solar-returns/9781463656584/p/25379900
- Swiss Ephemeris overview and licensing: https://www.astro.com/swisseph/swephinfo_e.htm
- Swiss Ephemeris license file: https://sources.debian.org/src/libswe/2.10.03-3.1/LICENSE
- Swiss Ephemeris Professional License contract: https://www.astro.com/swisseph/secont_e.pdf
- OurAirports open data: https://ourairports.com/data/
- OurAirports data dictionary: https://ourairports.com/help/data-dictionary.html
- OurAirports counts by type: https://datahub.io/datapressr/airports
