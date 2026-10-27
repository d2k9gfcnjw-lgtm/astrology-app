import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from './lib/api'
import { DEFAULT_SETTINGS, type Chart, type Keyframe, type Settings, type Subject, type SubjectIn, type WheelData } from './lib/types'
import { type StepUnit, dateFromJd, isoLocal, jdNow, stepJd, stepWall, wallClock } from './lib/time'
import { wheelFromChart, wheelFromFrame } from './lib/wheelData'
import { useSpin } from './lib/useSpin'
import { Wheel } from './components/Wheel'
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
  const [view, setView] = useState<'wheel' | 'table'>('wheel')
  const [panel, setPanel] = useState<Panel>('library')
  const [editing, setEditing] = useState<Subject | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [highlight, setHighlight] = useState<string | null>(null)
  const [spinSpeed, setSpinSpeed] = useState(3600)
  const [spinning, setSpinning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 900)

  const setJd = useCallback((v: number) => { jdRef.current = v; setJdState(v) }, [])

  // Fetch the full chart whenever the instant, place or settings change (not while spinning).
  useEffect(() => {
    if (spinning) return
    let live = true
    api.chartAt(jd, place.lat, place.lon, settings).then((c) => { if (live) { setChart(c); setFrame(null); setError(null) } }).catch((e) => live && setError(e.message))
    return () => { live = false }
  }, [jd, place.lat, place.lon, settings, spinning])

  const onFrame = useCallback((f: Keyframe) => { setFrame(f); setJdState(f.jd_ut) }, [])
  const onStop = useCallback((v: number) => { setSpinning(false); setJd(v) }, [setJd])
  const spin = useSpin({ jdRef, lat: place.lat, lon: place.lon, settings, speed: spinSpeed, onFrame, onStop })
  const onSpinRate = useCallback((r: number) => { if (r !== 0) setSpinning(true); spin.setRate(r) }, [spin])

  const wall = useMemo(() => wallClock(dateFromJd(jd), place.timezone), [jd, place.timezone])

  const wheel: WheelData | null = useMemo(() => {
    if (frame) return wheelFromFrame(frame, settings.aspects)
    return chart ? wheelFromChart(chart) : null
  }, [frame, chart, settings.aspects])

  const openSubject = useCallback(async (s: Subject) => {
    try {
      const c = await api.subjectChart(s.id)
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
      const pl: Place = { lat: s.lat, lon: s.lon, name: s.place_name, timezone: c.moment.timezone }
      setSubject(null)
      setNatal({ jd: c.moment.jd_ut, place: pl, flags: c.moment.flags })
      setPlace(pl)
      setJd(c.moment.jd_ut)
      setPanel('library')
    } catch (e) { setError((e as Error).message) }
  }, [settings, setJd])

  const step = useCallback(async (amount: number, unit: StepUnit) => {
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
        <h1>{subject?.name ?? (natal ? 'Unsaved chart' : 'Astrology workstation')}</h1>
        <div className="header-actions">
          <button className={view === 'wheel' ? 'active' : ''} onClick={() => setView('wheel')}>Wheel</button>
          <button className={view === 'table' ? 'active' : ''} onClick={() => setView('table')}>Table</button>
          <button onClick={() => { setPanel('settings'); setSidebarOpen(true) }}>Settings</button>
        </div>
      </header>
      <div className="sidebar">
        {panel === 'library' && <Library selectedId={subject?.id ?? null} refreshKey={refreshKey} onOpen={openSubject} onEdit={(s) => { setEditing(s); setPanel('form') }} onNew={() => { setEditing(null); setPanel('form') }} />}
        {panel === 'form' && <SubjectForm initial={editing} onSaved={(s) => { setRefreshKey((k) => k + 1); void openSubject(s) }} onPreview={preview} onCancel={() => setPanel('library')} />}
        {panel === 'settings' && <SettingsDrawer settings={settings} onChange={setSettings} onClose={() => setPanel('library')} />}
      </div>
      <main>
        {error && <div className="error banner">{error}</div>}
        {chart?.houses.warnings.map((w) => <div key={w} className="flag banner">⚠ {w}</div>)}
        {!wheel && !error && <div className="empty-state">Pick a chart from the library or create a new one.</div>}
        {wheel && view === 'wheel' && <div className="wheel-wrap"><Wheel data={wheel} highlight={highlight} onSelect={setHighlight} /></div>}
        {chart && view === 'table' && <TableView chart={chart} highlight={highlight} onSelect={setHighlight} />}
        {chart && (
          <div className="provenance">
            {chart.provenance.house_system} · {chart.provenance.zodiac}{chart.provenance.ayanamsa ? ` (${chart.provenance.ayanamsa})` : ''} · {chart.provenance.node_type} node · {chart.is_day ? 'day' : 'night'} chart
            {natal && natal.flags.length > 0 && <span className="flag"> · natal offset flags: {natal.flags.join(', ')}</span>}
          </div>
        )}
      </main>
      <footer>
        <TimeControls wall={wall} timezone={place.timezone} jd={jd} flags={[]} onStep={step} onSetLocal={setLocal} onNow={() => setJd(jdNow())}
          onNatal={() => { if (natal) { setPlace(natal.place); setJd(natal.jd) } }} hasNatal={natal !== null}
          spinSpeed={spinSpeed} onSpinSpeed={setSpinSpeed} onSpinRate={onSpinRate} spinning={spinning} />
        <LocationLock locked={locked} onLock={setLocked} placeName={place.name} lat={place.lat} lon={place.lon} onPlace={changePlace} relocatedFrom={relocatedFrom} />
      </footer>
    </div>
  )
}
