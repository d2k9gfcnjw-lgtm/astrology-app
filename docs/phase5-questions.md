# Phase 5: questions before the finder is coded

CLAUDE.md says: ask the owner before inventing any weighting. This is that list.
Answer with the books open; a "keep" next to a proposal is enough. Everything
you answer lands in `rules/rules.yaml`, nothing in code.

## How the finder will work (for orientation)

1. Solve the SR instant (Phase 4). Planets are fixed; only angles and houses
   change with the place.
2. Score a 1° grid of the inhabited world (about 60°S to 66°N) with the land
   mask, refine to 0.25° around the best areas, then score every GeoNames
   city above the population floor within the chosen distance of a large
   airport with scheduled service (OurAirports).
3. For every candidate: hard filters first (fail = disqualified, with the
   reason), then penalties and bonuses from the rules, multiplied by the
   goal profile, then a star rating. Every number comes with its sentence.
4. Stress test: how many degrees of Ascendant movement until a cusp flips a
   verdict, and whether the verdict survives your birth time ± its
   uncertainty.

## A. The natal chart (SR Ascendant in the natal houses)

Today: hard filter for natal 1st, 6th, 12th; bonus +30 for natal 10th under
the career goal; nothing for the other houses.

1. Give the whole table: for each natal house 1 to 12 where the SR Ascendant
   may fall, is it good, neutral or bad, with a weight, and does it depend on
   the goal? (Example: natal 7th for love, natal 2nd for money.)
2. Does the SR MC's natal house matter at all? (You said no for the facts
   strip; confirm "not scored".)
3. Intercepted natal signs: the file gives +5 when an SR cusp falls in a sign
   intercepted natally. Keep, change or drop?

## B. The year's transits (Phase 3 report)

Today: display only (weight 0).

4. Should a heavy transit to a natal planet (Saturn, Uranus, Neptune, Pluto
   by conjunction, square or opposition, within your orbs) change the score?
   Proposals, pick any:
   - a. Avoid placing that natal-planet's SR counterpart in the 1st, 6th or
     12th or on an angle (extra penalty).
   - b. Prefer SR charts that put benefics on the natal house the transit
     stresses (support).
   - c. Keep transits as information beside the result, no score change.
5. Do Jupiter transits earn a bonus anywhere?

## C. The previous solar return

Today: display only.

6. Does last year's SR change this year's choice at all? For example, avoid
   the same emphasised house two years in a row, or no rule.

## D. The base solar return (staying home)

Today: every result reports what it fixes or worsens versus the base.

7. Should "fixes a hard filter the base chart has" earn extra points, or is
   the comparison just information? Any penalty for a result that is worse
   than staying home on some count while better on others?

## E. Placement rules already in the file (confirm or change each weight)

8. Sun, Moon, Mars, Saturn, Uranus, Neptune, Pluto in SR 12th −60, 1st −45,
   6th −40. Keep the planet list? (Is the Sun really a malefic here? The
   Moon?) Keep the weights?
9. Three or more bodies in the 1st, 6th or 12th: −60. With your new rule the
   1st/12th stellium reads as an Ascendant in the 12th: should it be a hard
   filter instead of −60? And the 8th-house stellium: hard filter?
10. Mars, Saturn or outer planets in the 7th or 8th: −20 (marked confirm).
11. Jupiter or Venus within 12° of an angle: MC +30, ASC +25, DSC +20,
    IC +20. Does the bonus fade with the orb (full at 0°, nothing at 12°),
    or is it flat inside 12°?
12. Sun in SR 10th or 11th: +25 (confirm). Where else is the Sun good or bad,
    per goal?
13. Saturn near the SR MC cancels any benefic bonus at the MC. Keep? Does
    Saturn anywhere on an angle cancel the bonus on that angle?
14. Mars and Saturn in the same house except 3rd and 9th: now a hard filter.
    Confirm it disqualifies rather than penalises.
15. The 2.5° dual-house rule: when a planet works in two houses, does a
    penalty apply if either house is bad, or only the primary house?
16. Anything the file is missing that you always check: Moon's house, Venus's
    house, the ruler of the SR Ascendant, the SR 8th house, retrogrades?

## F. Goals, stars and robustness

17. Goal profiles in the file: career, love, rest, money, inner_work. Keep
    these five? Add or rename any?
18. Star thresholds are placeholders (−60, −20, 10, 40, 70). Fine to tune
    after we see real scores on your charts?
19. Minimum robustness: should a result be hidden if a cusp flip is within
    N degrees (say 2.5°) or within your birth time uncertainty, or just
    shown with a warning?

## G. Practical defaults (the open questions in docs/reference.md)

20. Population floor for cities (proposal 100,000) and maximum distance from
    a large airport (proposal 150 km).
21. Countries or regions to always exclude, if any.
22. OK to download the two remaining data files: OurAirports `airports.csv`
    (about 10 MB) and Natural Earth land polygons (about 5 MB)?
