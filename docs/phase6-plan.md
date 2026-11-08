# Phase 6 plan: astrocartography

Status: waiting for owner approval.

## What Phase 6 delivers

The planetary lines on the same map the finder uses, for the natal chart,
any solar return, or any moment from time travel: ASC, DSC, MC and IC lines
per body with toggles, parans as horizontal lines with a list of the pairs,
a shaded orb band around every line whose width is a setting, and click (or
city search) anywhere to open the relocated chart there with the lines and
parans within orb listed.

## 1. The maths, and how it is tested

- **MC and IC lines** are meridians: the body culminates where the local
  sidereal time equals its right ascension, so the line's longitude is the
  body's right ascension minus Greenwich sidereal time; the IC line is 180°
  away. Test: on the Sun's MC line at 12:00 UT the Sun's hour angle is zero,
  and the line lies within the equation of time of the Greenwich meridian.
- **ASC and DSC lines** are the curves where the body is on the horizon,
  rising or setting: at each latitude the hour angle of rising comes from
  cos H = −tan φ · tan δ, so the line exists only where |tan φ · tan δ| ≤ 1
  (bodies with high declination have no rising line near the poles). The
  line is sampled every half degree of latitude. Test: at every sampled
  point Swiss Ephemeris's own horizon calculation gives altitude 0 within an
  arcminute, rising on the ASC line and setting on the DSC line.
- **In mundo versus zodiacal.** astro.com's AstroClick Travel draws the body
  itself on the horizon and meridian (in mundo). That is the default; the
  zodiacal method (the body's ecliptic degree on the angle) is a toggle.
- **Parans**: for a pair of bodies, the latitudes at which one is on an
  angle at the same sidereal time as the other is on an angle (rise, set,
  culminate, anticulminate). Found by scanning latitude and solving the
  crossing to a hundredth of a degree. Test: at the found latitude both
  bodies' angular times agree to a second; a pair with no crossing returns
  none; the Sun to Moon paran count for a synthetic chart is stable.
- **Orb and "within orb at this place"**: distance from a place to each line
  along the ground (great-circle kilometres, also shown in degrees), lines
  sorted by distance, parans within ± the paran orb in latitude.
- **Golden test**: if you give me AstroClick Travel's readout for three
  cities (click a city on astro.com's map: it lists the lines nearby with
  their distances), those become `golden/acg_01.yaml` (local) and a test
  that my distances match within a few kilometres.

## 2. Backend

- `engine/acg.py`: `lines_at(jd_ut, settings, bodies)` returning each line
  as a list of (lon, lat) points split at the antimeridian; `parans_at(...)`;
  `at_place(jd_ut, lat, lon, settings, orb)` returning the relocated chart's
  facts plus the lines and parans within orb with their distances.
- Endpoints: `POST /api/acg/lines` (instant, bodies, method), `POST
  /api/acg/at` (instant, place, orb). Works for any instant: natal, a return
  (its instant from Phase 4), or the time-travel clock.

## 3. Frontend

- A **Map** button. The same MapLibre map as the finder, with the chart
  source chosen at the top: natal, the time-travel instant, or a solar or
  lunar return by year. Toggles per body and per angle (ASC, DSC, MC, IC),
  a parans toggle, the orb width (km or degrees) and the method.
- Lines coloured per body with the angle marked at the line's ends; orb
  bands drawn as translucent wide strokes that fade toward the edge; parans
  as dashed horizontal lines labelled with the pair.
- Click anywhere, or search a city, to open a side panel with the relocated
  chart's facts (the Phase 4 strip) and the lines and parans within orb at
  that place, nearest first; "Open this chart" sends the place to the wheel
  with location lock on, or to the Returns view for a return.
- The finder's heat layer can be shown underneath, so a candidate city's
  lines are read together with its score.
- Vitest for the line-segmenting and distance helpers; screenshots at both
  widths.

## 4. Done means

All tests pass (and the golden AstroClick distances if you supply them),
the lines for your natal chart look like astro.com's map, click-to-relocate
works from the map and from city search, and the work is committed and
pushed.

## Questions

1. Orb band width default. Astrocartography practice ranges from about 100
   to 300 miles; I propose 300 km with the band fading to nothing at the
   edge, adjustable in km or degrees.
2. Parans: default the ten planets, Chiron and the Node as toggles; paran orb
   ±1° of latitude. OK?
3. Method default in mundo (as astro.com), zodiacal as a toggle. OK?
4. Can you click three cities on astro.com's AstroClick Travel map for your
   natal chart and paste what it lists (the lines and their distances)? That
   gives the golden test.
