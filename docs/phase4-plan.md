# Phase 4 plan: solar and lunar returns

Status: approved 27 Oct 2026 with the answers below; implemented on this branch.

## What Phase 4 delivers

The exact solar return instant for any year, the SR chart for any place
(the finder's building block), a bi-wheel against the natal chart, the SR
Ascendant's natal house, the previous SR and the base ("stay home") SR side
by side with the chosen one, and lunar returns the same way. Tested against
the three aimed solar returns you saved (Concepción 2025, Anchorage 2026,
Hilo 2027), now transcribed to `golden/sr_01..03.yaml` (local, never pushed).

## 1. Tests first

- **Golden solar returns**: for each sheet, the instant I solve must fall
  within 60 seconds of astro.com's (they print the chart at the rounded
  minute; the Julian Day on the sheet gives that minute exactly). At their
  instant, every planet within 1′ and every Placidus cusp within 2′ at the
  relocated place, house numbers as printed, local time and offset as
  printed (Chile −04:00, Alaska daylight −08:00, Hawaii −10:00 with the UT
  date rolling over).
- **Base and previous SR**: the base SR is just the same instant at the
  natal place; the previous SR is year − 1. Checked for consistency with the
  Phase 3 year window (the SR instant that starts the transit year is the
  same instant).
- **SR Ascendant's natal house** and every SR planet's natal house, computed
  with the natal cusps (Placidus or Whole Sign per the chart's settings).
- **Precession toggle**: the precessed SR targets the natal Sun's degree
  carried forward by precession (about 50″ a year); the test checks it comes
  a few hours after the tropical one and grows with age.
- **Lunar returns**: all 13 or 14 returns in a year, each with the Moon on
  the natal Moon to the second; a chart for any one of them.

## 2. Backend

- `engine/returns.py`: `solar_return(natal, year, lat, lon, precessed)` and
  `lunar_returns(natal, jd_start, jd_end)` built on the Phase 3 solver and
  the location-lock primitive; a `ReturnChart` that carries the SR chart,
  the local time at the chosen place (zone from the coordinates), the SR
  angles' natal houses, every SR planet's natal house, planets within your
  12° of an SR angle, and the base and previous SR charts.
- Endpoints: `GET /api/subjects/{id}/solar-return?year=&lat=&lon=&precessed=`
  (also a POST for unsaved charts), `GET /api/subjects/{id}/lunar-returns?year=`
  and `.../lunar-return?jd=&lat=&lon=`.

## 3. Frontend

- **Returns** button beside Transits: a year picker, "Solar" or "Lunar", the
  place (defaults to the natal place; city search and lat/lon as in location
  lock; later the map), and a precession toggle (off by default per CLAUDE.md).
- The SR shown either alone or as a bi-wheel around the natal chart (toggle),
  with the table view one tap away. A facts strip under the wheel: local
  SR time and zone, SR Ascendant sign and natal house, SR MC natal house,
  SR Sun and Moon houses, planets within 12° of an angle, stelliums.
- **Side by side**: three small wheels, previous SR, chosen SR, base SR,
  each with the same facts strip, so a relocation reads at a glance against
  staying home and against the year just ending.
- **Lunar**: the year's lunar returns as a list with their dates; pick one to
  show it; same place controls.
- "Save as chart" puts the chosen return in the library as an event (for the
  outcome notes of Phase 7).
- Vitest for the facts strip helpers; screenshots at both widths.

## 4. Done means

All tests pass including the three golden SRs; the Concepción, Anchorage and
Hilo charts render as on your sheets; committed and pushed.

## Questions for you

1. The facts strip: SR Ascendant sign and natal house, MC natal house, Sun
   and Moon houses, planets within 12° of angles, stelliums. Anything else
   you always look at first?
2. Lunar returns: default place the natal place, same as solar? And include
   them in the side-by-side view, or keep lunar simple (one chart at a time)?

## Owner's answers (27 Oct 2026)

- Facts strip: the SR Ascendant's natal house (its sign does not matter), the house(s) of
  the Sun and of Mars, and any stellium. No MC natal house.
- Four Thirty-Rules items added to `rules/rules.yaml`: the 2.5° dual-house rule for every
  planet (returns, transits, radix); a stellium across the 1st/12th read as an Ascendant in
  the 12th, even with benefics; a stellium in the 8th read the same way; Mars and Saturn
  never in the same return house except the 3rd and 9th.
- Lunar returns default to the place the person currently lives; the base solar return
  defaults to that same place. So each chart gets a "lives in" place beside the birth place.
- Previous SR: computed at the home place unless the owner later picks a saved return.
