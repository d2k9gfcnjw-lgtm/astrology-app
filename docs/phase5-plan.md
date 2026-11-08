# Phase 5 plan: the aimed solar return finder

Status: waiting for owner approval. Rules and answers: `rules/rules.yaml` (v2), `docs/phase5-answers.md`.

## The approach in one paragraph

The finder does what the book and Katia do, in order: first protection (the
hard filters), then the holistic context (which areas of life the slow
transits are stimulating this year, what last year's return set up, the
goals), then the price of each option. It never claims a single best place:
results come in tiers (safe, good, marginal, disqualified) and every result
prints its gains, its costs and its cautions in plain words with the page
of the book. Katia's point that several places can all be good is the
default shape of the output.

## 1. Tests first (`backend/tests/test_finder*.py`)

- Hand-made returns: Mars in the 12th is disqualified with the TR 5 text;
  Jupiter on the MC with a quiet year and the Ascendant in natal 10 ranks
  first; the same with Saturn square the natal Sun that year loses the
  natal-tenth bonus (TR 14); Saturn within orb of the MC cancels Jupiter's
  bonus (SRG 24); a planet 1° past a bad cusp counts as inside (SRG 23); a
  result 1° from a natal cusp is unsafe (SRG 7) and reappears when that
  filter is switched off; the 30/45-minute-earlier birth test flips a
  verdict and costs a star; a result is "marginal" when the base is already
  clean and the gain is small (SRG 19).
- Transit context: the themes list for a synthetic chart names the natal
  houses each slow planet transits during the year and the heavy aspects to
  Sun, Moon, Ascendant, MC with their dates, using the book's orbs (TR 23).
- Geography: the land mask says Paris is land and the mid-Atlantic is not;
  the city list keeps only places above the floor within the airport
  distance of a large airport with scheduled service, with the airport code
  and distance.
- Local only: your three real aimed returns (Concepción, Anchorage, Hilo)
  must not be disqualified by the rules, since Katia chose them. That is the
  first calibration check; her other readings go in `reference/case-studies/`
  (gitignored) and become further checks as you add them.

## 2. Backend

- `engine/finder/scoring.py`: the rule engine. Input: a return chart (Phase
  4), the natal chart, the year's transit context, the goal, the rules file.
  Output: disqualified or a score, the star rating, and a reasons list, each
  reason with rule id, points, sentence and book page; plus gains, costs,
  cautions, and what it fixes or worsens against the base return.
- `engine/finder/context.py`: the year's transit themes from the Phase 3
  report, slow planets first (Jupiter to Pluto): houses transited, heavy
  aspects to the four natal points, Saturn through natal 2nd or 8th (for
  SRG 11), and a plain summary line for the results page.
- `engine/finder/geo.py`: Natural Earth land mask, the airport table (large
  airports with scheduled service, about 1,150), candidate cities from
  GeoNames by population floor and airport distance.
- `engine/finder/search.py`: the pipeline. SR instant, natal cusps, 1° grid
  of the inhabited latitudes with the ocean masked, 0.25° refinement around
  the best cells, then every candidate city scored, the robustness tests on
  the city results, tiering, and the comparison with the base return.
- Endpoint `POST /api/finder/run` with subject, year, goal, population floor,
  airport distance, countries to exclude, precession, and the safety filter
  switches; returns the heat grid, the tiered city list, the transit
  themes, the base and previous returns. A run takes a few seconds; the
  result is cached per subject and year until the rules or inputs change.

## 3. Frontend (Finder button)

- Inputs on the left: year, goal, population floor, airport distance,
  exclusions, birth-time uncertainty (from the chart), precession, the
  safety filters, and a "Run" button with progress.
- The map: MapLibre with the heat layer (green safe, amber marginal, grey
  disqualified, ocean and empty land masked). Online it shows OpenStreetMap
  tiles under the heat; offline it still works with the Natural Earth
  coastlines, as CLAUDE.md requires. Click a city marker or anywhere on land
  to see that place's return (Phase 4 view) with its reasons.
- The list: tiers, then score and stars inside a tier, each row with city,
  country, airport code and distance, local SR date and time, the facts
  strip (Ascendant's natal house, Sun, Mars, stelliums), gains and costs in
  words, the robustness margin in degrees and the birth-time test, and
  "versus home". A panel beside the list shows the year's transit themes
  and the previous return so the choice is made in context.
- "Many good places": the safe tier is shown as a group with a note that
  the flavours differ, not as a single winner.

## 4. Done means

All tests pass, your three past returns are not disqualified, the map and
list render at both widths, a run on your chart for next year completes in
under 30 seconds, and the work is committed and pushed.

## Questions

None that need an answer before coding; the weights are the ones you
approved and all remain editable in the rules file. If you have one of
Katia's readings as a file, put it in `reference/case-studies/` now and I
will use it as the first calibration case.
