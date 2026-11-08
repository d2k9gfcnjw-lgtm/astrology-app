import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from './lib/api'
import { DEFAULT_SETTINGS, type Chart, type Keyframe, type Settings, type Subject, type SubjectIn, type WheelData } from './lib/types'
import { type StepUnit, dateFromJd, isoLocal, jdNow, stepJd, stepWall, wallClock } from './lib/time'
import { wheelFromChart, wheelFromFrame } from './lib/wheelData'
import { useSpin } from './lib/useSpin'
import { Wheel, type TransitRing } from './components/Wheel'
import { YearAheadView } from './components/YearAheadView'
import { ReturnsView } from './components/ReturnsView'
import { FinderView } from './components/FinderView'
import { AcgView } from './components/AcgView'
import type { FinderResult } from './lib/types'
import type { FeatureCollection } from 'geojson'
import { transitAspects } from './lib/transitAspects'
import type { SolveHit } from './lib/types'
import { TableView } from './components/TableView'
import { Library } from './components/Library'
import { SubjectForm } from './components/SubjectForm'
import { TimeControls } from './components/TimeControls'
import { LocationLock } from './components/LocationLock'
import { SettingsDrawer } from './components/SettingsDrawer'

type Panel = 'library' | 'form' | 'settings'

interface Place { lat: number; lon: number; name: string; timezone: string | null }

export default function App() {
  const [subject, setSubject] = useState<Subject | null>(null)
  const [natal, setNatal] = useState<{ jd: number; place: Place; flags: string[] } | null>(null)
  const [jd, setJdState] = useState<number>(() => jdNow())
  const jdRef = useRef(jd)
  const [place, setPlace] = useState<Place>({ lat: 0, lon: 0, name: '', timezone: null })
  const [locked, setLocked] = useState(false)
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS)
  const [chart, setChart] = useState<Chart | null>(null)
  const [frame, setFrame] = useState<Keyframe | null>(null)
  const [view, setView] = useState<'wheel' | 'transits' | 'year' | 'returns' | 'finder' | 'map' | 'table'>('wheel')
  const [natalChart, setNatalChart] = useState<Chart | null>(null)
  const [finderJump, setFinderJump] = useState<{ year: number; lat: number; lon: number; name: string } | null>(null)
  const [finderResult, setFinderResult] = useState<FinderResult | null>(null)
  const [live, setLive] = useState(false)
  const [land, setLand] = useState<FeatureCollection | null>(null)
  useEffect(() => { fetch('/api/finder/land').then((r) => r.json()).then(setLand).catch(() => setLand(null)) }, [])
  const [solveMenu, setSolveMenu] = useState<{ body: string; lon: number; hits: SolveHit[]; chosen: number } | null>(null)
  const [panel, setPanel] = useState<Panel>('library')
  const [editing, setEditing] = useState<Subject | null>(null)
  const [newOwner, setNewOwner] = useState<Subject | null>(null)
  const [people, setPeople] = useState<Subject[]>([])
  const [refreshKey, setRefreshKey] = useState(0)
  useEffect(() => { api.subjects().then((xs) => setPeople(xs.filter((x) => x.kind === 'person'))).catch(() => undefined) }, [refreshKey])
  const [highlight, setHighlight] = useState<string | null>(null)
  const [spinSpeed, setSpinSpeed] = useState(3600)
  const [spinning, setSpinning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 900)

  const setJd = useCallback((v: number) => { jdRef.current = v; setJdState(v) }, [])

  // Chart of the moment: keep the clock on "now" while live is on (every 10 s; the Ascendant moves about 2.5 deg in that time).
  useEffect(() => {
    if (!live) return
    setJd(jdNow())
    const id = window.setInterval(() => setJd(jdNow()), 10000)
    return () => window.clearInterval(id)
  }, [live, setJd])

  const showNowSky = useCallback(() => {
    const home = subject && subject.home_lat !== null && subject.home_lon !== null
      ? { lat: subject.home_lat, lon: subject.home_lon, name: subject.home_place_name, timezone: subject.home_timezone }
      : natal ? natal.place : place
    setPlace(home)
    setLocked(false)
    setView('wheel')
    setLive(true)
  }, [subject, natal, place])

  // Fetch the full chart whenever the instant, place or settings change (not while spinning).
  useEffect(() => {
    if (spinning) return
    let live = true
    api.chartAt(jd, place.lat, place.lon, settings).then((c) => { if (live) { setChart(c); setFrame(null); setError(null) } }).catch((e) => live && setError(e.message))
    return () => { live = false }
  }, [jd, place.lat, place.lon, settings, spinning])

  // The natal chart (fixed instant, current place) is the inner wheel of the bi-wheel.
  useEffect(() => {
    if (!natal) { setNatalChart(null); return }
    let live = true
    api.chartAt(natal.jd, place.lat, place.lon, settings).then((c) => { if (live) setNatalChart(c) }).catch(() => undefined)
    return () => { live = false }
  }, [natal, place.lat, place.lon, settings])

  const onFrame = useCallback((f: Keyframe) => { setFrame(f); setJdState(f.jd_ut) }, [])
  const onStop = useCallback((v: number) => { setSpinning(false); setJd(v) }, [setJd])
  const spin = useSpin({ jdRef, lat: place.lat, lon: place.lon, settings, speed: spinSpeed, onFrame, onStop })
  const onSpinRate = useCallback((r: number) => { if (r !== 0) { setSpinning(true); setLive(false) } spin.setRate(r) }, [spin])

  const wall = useMemo(() => wallClock(dateFromJd(jd), place.timezone), [jd, place.timezone])

  const wheel: WheelData | null = useMemo(() => {
    if (frame) return wheelFromFrame(frame, settings.aspects)
    return chart ? wheelFromChart(chart) : null
  }, [frame, chart, settings.aspects])

  const natalWheel: WheelData | null = useMemo(() => (natalChart ? wheelFromChart(natalChart) : null), [natalChart])

  const onDrop = useCallback(async (body: string, lon: number) => {
    try {
      const r = await api.solve(body, lon, jdRef.current, settings)
      const hits = [...r.previous, ...r.next]
      if (!r.nearest || hits.length === 0) { setError(`${body} does not reach that degree within the search window`); return }
      setJd(r.nearest.jd_ut)
      setSolveMenu(hits.length > 1 ? { body, lon, hits, chosen: hits.findIndex((h) => h.jd_ut === r.nearest!.jd_ut) } : null)
    } catch (e) { setError((e as Error).message) }
  }, [settings, setJd])

  const transitRing: TransitRing | null = useMemo(() => {
    if (view !== 'transits' || !wheel || !natalWheel) return null
    const tl: Record<string, number> = {}
    for (const [k, v] of Object.entries(wheel.planets)) tl[k] = v.lon
    const nl: Record<string, number> = {}
    for (const [k, v] of Object.entries(natalWheel.planets)) nl[k] = v.lon
    nl.asc = natalWheel.asc; nl.dsc = (natalWheel.asc + 180) % 360; nl.mc = natalWheel.mc; nl.ic = (natalWheel.mc + 180) % 360
    natalWheel.cusps.forEach((c, i) => { nl[`cusp_${i + 1}`] = c })
    // In the wheel every transiting body is drawn; the report's body list only decides the aspect lines.
    return { planets: wheel.planets, aspects: transitAspects(tl, nl, settings.transits), onDrop }
  }, [view, wheel, natalWheel, settings.transits, onDrop])

  const defaultYear = useMemo(() => {
    if (!natal) return new Date().getFullYear()
    const birth = dateFromJd(natal.jd)
    const now = new Date()
    const thisYearBirthday = new Date(Date.UTC(now.getUTCFullYear(), birth.getUTCMonth(), birth.getUTCDate(), birth.getUTCHours(), birth.getUTCMinutes()))
    return now >= thisYearBirthday ? now.getUTCFullYear() : now.getUTCFullYear() - 1
  }, [natal])

  const openSubject = useCallback(async (s: Subject) => {
    try {
      const c = await api.subjectChart(s.id)
      setLive(false)
      const pl: Place = { lat: s.lat, lon: s.lon, name: s.place_name, timezone: c.moment.timezone }
      setSubject(s)
      setNatal({ jd: c.moment.jd_ut, place: pl, flags: c.moment.flags })
      setPlace(pl)
      setJd(c.moment.jd_ut)
      setLocked(false)
      setSettings({ ...DEFAULT_SETTINGS, ...(s.settings as Partial<Settings>) })
      setPanel('library')
      setError(null)
      if (window.innerWidth <= 900) setSidebarOpen(false)
    } catch (e) { setError((e as Error).message) }
  }, [setJd])

  const preview = useCallback(async (s: SubjectIn) => {
    try {
      const c = await api.chart({ datetime_local: s.datetime_local, lat: s.lat, lon: s.lon, timezone: s.timezone, utc_offset_override: s.utc_offset_override }, settings)
      setLive(false)
      const pl: Place = { lat: s.lat, lon: s.lon, name: s.place_name, timezone: c.moment.timezone }
      setSubject(null)
      setNatal({ jd: c.moment.jd_ut, place: pl, flags: c.moment.flags })
      setPlace(pl)
      setJd(c.moment.jd_ut)
      setPanel('library')
    } catch (e) { setError((e as Error).message) }
  }, [settings, setJd])

  const step = useCallback(async (amount: number, unit: StepUnit) => {
    setLive(false)
    if (unit === 'month' || unit === 'year') {
      const w = stepWall(wall, amount, unit)
      try {
        const r = await api.resolveTime(isoLocal(w), place.lat, place.lon, place.timezone, null)
        setJd(r.jd_ut)
      } catch (e) { setError((e as Error).message) }
    } else {
      setJd((stepJd(jd, amount, unit) as { jd: number }).jd)
    }
  }, [jd, wall, place, setJd])

  const setLocal = useCallback(async (iso: string) => {
    setLive(false)
    try {
      const r = await api.resolveTime(iso, place.lat, place.lon, place.timezone, null)
      setJd(r.jd_ut)
      setError(null)
    } catch (e) { setError((e as Error).message) }
  }, [place, setJd])

  const changePlace = useCallback(async (lat: number, lon: number, name: string, timezone: string | null) => {
    const next: Place = { lat, lon, name, timezone }
    if (locked) { setPlace(next); return }
    // Lock off: keep the same local clock time, re-resolve it in the new zone.
    try {
      const r = await api.resolveTime(isoLocal(wall), lat, lon, timezone, null)
      setPlace({ ...next, timezone: r.timezone })
      setJd(r.jd_ut)
    } catch (e) { setError((e as Error).message) }
  }, [locked, wall, setJd])

  const relocatedFrom: [number, number] | null = natal && (natal.place.lat !== place.lat || natal.place.lon !== place.lon) ? [natal.place.lat, natal.place.lon] : null

  return (
    <div className={`app${sidebarOpen ? '' : ' sidebar-closed'}`}>
      <header>
        <button className="icon" onClick={() => setSidebarOpen((v) => !v)} title="Charts">☰</button>
        <h1>{live ? 'Chart of the moment' : subject?.name ?? (natal ? 'Unsaved chart' : 'Astrology workstation')}{live && <small className="live"> · live</small>}</h1>
        <div className="header-actions">
          <button className={live ? 'active' : ''} onClick={showNowSky} title="The sky right now, kept up to date">Now sky</button>
          <button className={view === 'wheel' && !live ? 'active' : ''} onClick={() => { setLive(false); setView('wheel') }}>Wheel</button>
          <button className={view === 'transits' ? 'active' : ''} onClick={() => setView('transits')} disabled={!natal}>Transits</button>
          <button className={view === 'year' ? 'active' : ''} onClick={() => setView('year')} disabled={!natal}>Year ahead</button>
          <button className={view === 'returns' ? 'active' : ''} onClick={() => setView('returns')} disabled={!natal}>Returns</button>
          <button className={view === 'finder' ? 'active' : ''} onClick={() => setView('finder')} disabled={!subject}>Finder</button>
          <button className={view === 'map' ? 'active' : ''} onClick={() => setView('map')} disabled={!natal}>Map</button>
          <button className={view === 'table' ? 'active' : ''} onClick={() => setView('table')}>Table</button>
          <button onClick={() => { setPanel('settings'); setSidebarOpen(true) }}>Settings</button>
        </div>
      </header>
      <div className="sidebar">
        {panel === 'library' && <Library selectedId={subject?.id ?? null} refreshKey={refreshKey} onOpen={openSubject} onEdit={(s) => { setEditing(s); setNewOwner(null); setPanel('form') }} onNew={(owner) => { setEditing(null); setNewOwner(owner ?? null); setPanel('form') }} />}
        {panel === 'form' && <SubjectForm initial={editing} owner={newOwner} people={people} onSaved={(s) => { setRefreshKey((k) => k + 1); void openSubject(s) }} onPreview={preview} onCancel={() => setPanel('library')} />}
        {panel === 'settings' && <SettingsDrawer settings={settings} onChange={setSettings} onClose={() => setPanel('library')} />}
      </div>
      <main>
        {error && <div className="error banner">{error}</div>}
        {chart?.houses.warnings.map((w) => <div key={w} className="flag banner">⚠ {w}</div>)}
        {!wheel && !error && <div className="empty-state">Pick a chart from the library or create a new one.</div>}
        {wheel && view === 'wheel' && <div className="wheel-wrap"><Wheel data={wheel} highlight={highlight} onSelect={setHighlight} /></div>}
        {view === 'transits' && natalWheel && <div className="wheel-wrap"><Wheel data={natalWheel} transits={transitRing} highlight={highlight} onSelect={setHighlight} /></div>}
        {view === 'transits' && solveMenu && (
          <div className="solve-menu">
            <span>{solveMenu.body} at {solveMenu.lon.toFixed(2)}°: {solveMenu.hits.length} passes.</span>
            {solveMenu.hits.map((h, i) => (
              <button key={h.jd_ut} className={i === solveMenu.chosen ? 'active' : ''} onClick={() => { setJd(h.jd_ut); setSolveMenu({ ...solveMenu, chosen: i }) }}>
                {h.utc_datetime.slice(0, 16).replace('T', ' ')} UT{h.retrograde ? ' ℞' : ''} ({h.pass_index}/{h.pass_count})
              </button>
            ))}
            <button className="secondary" onClick={() => setSolveMenu(null)}>×</button>
          </div>
        )}
        {view === 'year' && (
          <YearAheadView subject={subject} natalInput={!subject && natal ? { datetime_local: isoLocal(wallClock(dateFromJd(natal.jd), natal.place.timezone)), lat: natal.place.lat, lon: natal.place.lon, timezone: natal.place.timezone, utc_offset_override: null } : null}
            settings={settings} defaultYear={defaultYear} onJump={(j) => { setJd(j); setView('transits') }} />
        )}
        {view === 'returns' && natal && (
          <ReturnsView subject={subject} natalInput={!subject ? { datetime_local: isoLocal(wallClock(dateFromJd(natal.jd), natal.place.timezone)), lat: natal.place.lat, lon: natal.place.lon, timezone: natal.place.timezone, utc_offset_override: null } : null}
            natalPlace={{ lat: natal.place.lat, lon: natal.place.lon, name: natal.place.name }} settings={settings} defaultYear={finderJump?.year ?? defaultYear} natalWheelData={natalWheel} initialPlace={finderJump ? { lat: finderJump.lat, lon: finderJump.lon, name: finderJump.name } : null}
            onJump={(j, pl) => { setLive(false); setLocked(true); setPlace({ lat: pl.lat, lon: pl.lon, name: pl.name, timezone: null }); setJd(j); setView('wheel') }}
            onSaved={(s) => { setRefreshKey((k) => k + 1); void openSubject(s) }} />
        )}
        {view === 'finder' && <FinderView subject={subject} defaultYear={defaultYear} result={finderResult} onResult={setFinderResult} land={land} onOpenReturn={(y, lat, lon, name) => { setFinderJump({ year: y, lat, lon, name }); setView('returns') }} />}
        {view === 'map' && natal && <AcgView subject={subject} natalJd={natal.jd} clockJd={jd} settings={settings} defaultYear={defaultYear} finderResult={finderResult} landGeoJson={land}
          onOpenPlace={(j, lat, lon, name) => { setLive(false); setLocked(true); setPlace({ lat, lon, name, timezone: null }); setJd(j); setView('wheel') }} />}
        {chart && view === 'table' && <TableView chart={chart} highlight={highlight} onSelect={setHighlight} />}
        {chart && view !== 'year' && view !== 'returns' && view !== 'finder' && view !== 'map' && (
          <div className="provenance">
            {chart.provenance.house_system} · {chart.provenance.zodiac}{chart.provenance.ayanamsa ? ` (${chart.provenance.ayanamsa})` : ''} · {chart.provenance.node_type} node · {chart.is_day ? 'day' : 'night'} chart
            {natal && natal.flags.length > 0 && <span className="flag"> · natal offset flags: {natal.flags.join(', ')}</span>}
          </div>
        )}
      </main>
      <footer>
        <TimeControls wall={wall} timezone={place.timezone} jd={jd} flags={[]} onStep={step} onSetLocal={setLocal} onNow={() => { setLive(false); setJd(jdNow()) }}
          onNatal={() => { if (natal) { setLive(false); setPlace(natal.place); setJd(natal.jd) } }} hasNatal={natal !== null}
          spinSpeed={spinSpeed} onSpinSpeed={setSpinSpeed} onSpinRate={onSpinRate} spinning={spinning} />
        <LocationLock locked={locked} onLock={setLocked} placeName={place.name} lat={place.lat} lon={place.lon} onPlace={changePlace} relocatedFrom={relocatedFrom} />
      </footer>
    </div>
  )
}
