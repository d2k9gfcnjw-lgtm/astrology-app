# Frontend (Phase 2: wheel, time travel, location lock)

Vite + React + TypeScript. Node lives in `~/.local/node` on this Mac (not on the Terminal PATH).

```bash
cd frontend && npm install            # once
cd frontend && npm run dev            # http://localhost:5173, proxies /api to the backend on :8000
cd frontend && npx vitest run         # label spreading, time stepping, keyframe interpolation
cd frontend && npm run build          # type-check + production bundle in dist/
```

Both servers at once from the Claude desktop app: `.claude/launch.json` has `backend` and `frontend`.

## Layout

- `src/lib/types.ts`: mirrors of the backend JSON models and the default settings.
- `src/lib/api.ts`: fetch wrappers for every endpoint.
- `src/lib/time.ts`: Julian Day, wall clock in a zone (Intl), stepping by second to year.
- `src/lib/interpolate.ts`: keyframe interpolation for spin mode (shortest arc across 0/360).
- `src/lib/spread.ts`: label spreading for stelliums; leader lines point at the true degree.
- `src/lib/useSpin.ts`: the spin loop (requestAnimationFrame, batched keyframes, watchdog).
- `src/lib/glyphs.tsx`: sign and body glyphs as SVG paths.
- `src/components/Wheel.tsx`: the SVG wheel (ASC left, element colours, cusps, aspects, labels).
- `src/components/TableView.tsx`: the same data as tables (bodies, cusps, aspects).
- `src/components/TimeControls.tsx`, `SpinDial.tsx`: stepping, now, natal, hold/drag spin.
- `src/components/LocationLock.tsx`: freeze the instant and change only the place.
- `src/components/SubjectForm.tsx`, `CitySearch.tsx`, `Library.tsx`, `SettingsDrawer.tsx`.
