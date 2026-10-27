# Phase 3 plan: transits and the year ahead

Status: approved 27 Oct 2026 (answers below) and implemented on this branch.

## What Phase 3 delivers

A transit bi-wheel (natal inside, transits outside) on top of the Phase 2
time controls, dragging a transit planet to jump to the exact moment it
reaches a degree (with previous and next dates when the planet is
retrograde), and a year-ahead transit report from one birthday to the next
with every exact hit, every retrograde pass, house ingresses and stations.
These are the inputs the solar return finder (Phase 5) needs.

## 1. Tests first (backend, pytest)

- **Exact-time solver**: for a body, a target longitude and a time window,
  find every instant the body is exactly on that longitude, to under one
  second. Checked against known events: the March equinox 2024 (Sun at 0°
  Aries, 20 March 2024 03:06 UT), a full Moon, Mercury's retrograde and
  direct stations in 2024, and a triple pass (Mars crossing one degree three
  times during its 2022 to 2023 retrograde). Every solved instant is also
  verified by recomputing the position at that instant.
- **Stations**: instants where a planet's speed is zero (retrograde and
  direct), same precision.
- **Report completeness**: for a synthetic natal chart, the year-ahead report
  contains the Sun's return to its natal degree exactly once, each Moon
  conjunction to natal Sun about 13 times when the Moon is switched on, and
  no hit outside the window.
- **Transit aspects with their own orbs** (2° default, marked "confirm" until
  you check the Thirty Rules), independent of the natal wheel orbs.

## 2. Backend

- `engine/solver.py`: `crossings(body, target_lon, jd_start, jd_end)`
  samples the body at a step suited to its speed (Moon hours, outer planets
  days), brackets every sign change of the angular distance, and refines each
  with bisection to one second. `stations(body, jd_start, jd_end)` does the
  same for speed. Returns pass numbers (1 of 3, 2 of 3, 3 of 3) so retrograde
  loops are explicit.
- `engine/transits.py`:
  - `transit_hits(natal, settings, jd_start, jd_end)`: every exact aspect
    (the transit aspect set) from each transit body to each natal point
    (planets, ASC, MC; Node, Chiron, Lilith, Fortune and all cusps as
    toggles). Each hit: UT and local instant, transit body, aspect, natal
    point, retrograde flag, pass k of n.
  - house ingresses: a transit body crossing a natal cusp (Placidus or Whole
    Sign, per the chart's settings), and sign ingresses.
  - stations in the year, with any natal point within the transit orb.
  - `year_ahead(subject, year)`: the window runs from the exact solar return
    instant of that year to the next one (the Sun back on its natal degree,
    solved with the same solver), which is Discepolo's birthday-to-birthday.
- Endpoints: `POST /api/transits/solve` (body, target longitude, around an
  instant: previous and next exact times, all passes of the current loop),
  `GET /api/subjects/{id}/year-ahead?year=`, and the bi-wheel uses the
  existing `/api/chart/at` with the natal chart's cusps.

## 3. Frontend

- **Bi-wheel**: natal wheel inside as in Phase 2; transit ring outside with
  glyphs, degrees and retrograde marks; aspect lines from transit bodies to
  natal points in the transit orbs; the natal houses stay fixed. The Phase 2
  time controls, spin and Now button drive it.
- **Drag a transit planet**: grab a transit glyph and move it around the
  ring; on release the app solves the instant that planet reaches that
  degree and jumps there. If the planet reaches it more than once
  (retrograde loop) a small list offers every date, previous and next, and
  the closest is chosen by default.
- **Year-ahead report**: a page per subject and year with the window shown
  as local dates, filters (bodies, aspects, natal points, ingresses,
  stations), grouped by transit body or in date order, each row jumps the
  bi-wheel to that instant. Count badges per body so the heavy years are
  visible at a glance.
- Settings: transit aspect set and orbs, transit bodies (Moon off by default
  in the report, on in the wheel), natal points to include.
- Vitest: pointer angle to longitude mapping for the drag; report grouping.

## 4. Done means

All tests pass, the bi-wheel and the report look right at desktop and phone
width, dragging a retrograde planet offers the right dates, and the work is
committed and pushed.

## Questions for you

1. Birthday to birthday as the exact solar return instants (recommended) or
   calendar midnight to midnight?
2. Transit bodies in the report by default: Sun, Mercury, Venus, Mars,
   Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron. Moon off by default
   (about 500 hits a year); on as a toggle. OK?
3. Natal points by default: the ten planets plus ASC and MC. Node, Chiron,
   Lilith, Fortune and the other cusps as toggles. OK?
4. Transit orb 2° on each side for every aspect, same aspect set as the natal
   wheel (conjunction, opposition, trine, square, sextile), minors off. OK as
   a starting point, to be checked against the Thirty Rules?

## Owner's answers (27 Oct 2026)

- The year runs from the exact solar return instant (Sun on its natal degree) to the next one.
- Transit bodies by importance: **primary** Jupiter, Saturn, Uranus, Neptune, Pluto;
  **secondary** Mars and Venus (their retrogrades keep them in a sign a long time),
  Mercury (retrogrades are nice to know); Sun and Moon aspects matter little for the
  year. Report defaults: Sun and Moon off, Chiron and Lilith off, all as toggles.
- Natal points: the ten planets and all four angles (AC, DC, MC, IC). Node, Chiron,
  Lilith, Fortune and the other cusps as toggles. House cusp degrees always visible.
- Transit orbs per transiting body: 3° for Sun through Jupiter and Saturn; 2° for Uranus;
  1.5° for Neptune and Pluto ("1 to 2 degrees for the slow outer movers"). All settings.
- Each hit in the report shows the exact instant and the span while within orb.
- Report grouping defaults to the primary bodies first.
