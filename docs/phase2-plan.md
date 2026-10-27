# Phase 2 plan: wheel, time travel and location lock

Status: approved 27 Oct 2026 (natal orbs 8/6 +1 luminaries, transit orb 2 to confirm, key file) and implemented on this branch.

## What Phase 2 delivers

The app you can actually open: a chart entry form with city search, a chart
library, the natal wheel in SVG with the table view one tap away, time
stepping and fluid spin, and location lock. No transits yet (Phase 3).

## 0. Tooling (needs your OK)

Node.js is needed for the React frontend and is not on the Mac. I will
download the official Node LTS build from nodejs.org as a plain archive and
unpack it under your home folder (`~/.local/node`), the same low-touch way
`uv` was installed: no admin password, nothing else changes.

## 1. Backend additions (Python, tests first)

- **Chart library**: SQLite file `data/charts.sqlite` (gitignored). One table
  for ChartSubject per CLAUDE.md: kind (person, event, place, question), name,
  tags, notes, local datetime, time confidence (exact, within 5 min, within
  30 min, unknown), place name, lat/lon, time zone, offset override, chart
  settings. Birth fields (datetime, place, lat/lon, notes) are encrypted at
  rest with a key stored in `data/keys/charts.key` (created on first run,
  gitignored). Endpoints: list with search and tag filter, create, update,
  delete (soft delete to `deleted_at`, never destroyed, per "never delete
  user chart data").
- **City search**: `scripts/fetch_data.py` gains GeoNames cities15000;
  loaded into a search table (name, ascii name, alternate names, country,
  admin region, population, lat/lon, time zone). `GET /api/cities?q=` returns
  the best 10 by prefix match, biggest population first.
- **Chart at any instant**: `POST /api/chart/at` with `jd_ut`, lat, lon and
  settings. This is what time travel and location lock call. Also a batch form
  (a list of jd_ut values) so spin mode can fetch keyframes in one call.
- **Aspects**: computed server side from a settings block (aspect set and
  orbs, see question 2) so the wheel and the table agree.

## 2. Frontend (Vite + React + TypeScript)

- Layout: library panel, wheel in the middle, time controls underneath,
  settings drawer. Collapses to one column at phone width; wheel scales to
  the viewport.
- **Entry form**: name, kind, date, time, time confidence, city search with
  autocomplete (falls back to manual lat/lon), zone and offset shown with the
  flags from Phase 1 and an override field, tags, notes.
- **Wheel (SVG)**: sign ring with element colors, house cusps with degrees,
  planet glyphs with degree and minute (14°32'), retrograde mark, aspect
  lines colored by type, ASC/MC/DSC/IC marked. Glyphs drawn as SVG paths so
  they look the same on every device.
- **Label spreading**: planets closer than a minimum angular gap are pushed
  apart along the ring, each with a leader line back to its true degree.
  Tested with four planets inside 6 degrees, as the phase prompt asks.
- **Table view**: toggle button; same data as the wheel: body, sign,
  degree, house, speed, retrograde, declination; cusps; aspects grid.
- **Time stepping**: forward and back buttons, unit picker (second, minute,
  hour, day, week, month, year, custom amount and unit), a now button, and
  direct date and time entry.
- **Spin mode**: hold a button or drag a dial to play time at a chosen speed
  (from 1 second per second to 1 year per second). To stay smooth, the
  frontend fetches keyframes a few times a second and interpolates angles
  and planets between them for every animation frame, so the angles turn
  without stutter even if a request is late.
- **Location lock**: a toggle that freezes the instant. While on, city
  search or manual lat/lon changes only the place; planets stay put and only
  cusps and angles move. Map click arrives with the map in Phase 6.
- (Deferred) URL state for bookmarking a view; not needed until hosting.

## 3. Tests

- Backend pytest: encryption round trip and that the raw SQLite file never
  contains a plaintext birth date; city search ranking; chart-at endpoint
  equals calculate_chart for the same instant; batch keyframes; aspects with
  orbs.
- Frontend Vitest: label spreading (four planets within 6 degrees get
  distinct slots, leader lines point to the true degree), time stepping
  across month ends and leap years, keyframe interpolation across the 360/0
  boundary.
- Manual check: screenshots at desktop and phone width, which I review
  myself before saying done.

## 4. Done means

All tests pass, screenshots look right at both widths, the Phase 1 golden
chart renders correctly on the wheel, and the work is committed and pushed.

## Questions for you

1. OK to install Node the way described in section 0?
2. Default aspect set and orbs for the wheel. Proposal: conjunction,
   opposition, trine, square at 8 degrees; sextile at 6; Moon and Sun get
   1 degree more; no minor aspects by default. All adjustable in settings.
3. Encryption key: a key file on this Mac (no password to type, protected
   by your Mac login) or a passphrase you type when the app starts? I
   recommend the key file for now; a passphrase can be added in Phase 7
   with encrypted backups.
