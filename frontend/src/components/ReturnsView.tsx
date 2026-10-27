import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { returnFacts } from '../lib/returnFacts'
import { wheelFromChart } from '../lib/wheelData'
import type { City, LunarInstant, ReturnChart, ReturnSet, Settings, Subject, SubjectIn } from '../lib/types'
import { CitySearch } from './CitySearch'
import { TableView } from './TableView'
import { Wheel } from './Wheel'

type Place = { lat: number; lon: number; name: string }
const fmt = (iso: string) => iso.replace('T', ' ').slice(0, 16)

interface Props {
  subject: Subject | null
  natalInput: { datetime_local: string; lat: number; lon: number; timezone: string | null; utc_offset_override: string | null } | null
  natalPlace: Place
  settings: Settings
  defaultYear: number
  natalWheelData: ReturnType<typeof wheelFromChart> | null
  onJump: (jd: number, place: Place) => void
  onSaved: (s: Subject) => void
}

function FactsStrip({ r }: { r: ReturnChart }) {
  return (
    <div className="facts">
      <div className="fact"><span>Local time</span><b>{fmt(r.local_datetime)}</b><small>{r.timezone ?? 'UTC'}{r.precessed ? ' · precessed' : ''}</small></div>
      {returnFacts(r).map((f) => <div key={f.label} className={`fact${f.warn ? ' warn' : ''}`}><span>{f.label}</span><b>{f.value}</b></div>)}
      {r.flags.map((f) => <div key={f.id} className="fact flag-text">⚠ {f.text}</div>)}
    </div>
  )
}

export function ReturnsView(p: Props) {
  const home: Place = p.subject && p.subject.home_lat !== null && p.subject.home_lon !== null
    ? { lat: p.subject.home_lat, lon: p.subject.home_lon, name: p.subject.home_place_name }
    : p.natalPlace
  const [kind, setKind] = useState<'solar' | 'lunar'>('solar')
  const [year, setYear] = useState(p.defaultYear)
  const [place, setPlace] = useState<Place>(home)
  const [precessed, setPrecessed] = useState(false)
  const [layout, setLayout] = useState<'wheel' | 'biwheel' | 'table'>('biwheel')
  const [set, setSet] = useState<ReturnSet | null>(null)
  const [lunars, setLunars] = useState<LunarInstant[]>([])
  const [lunar, setLunar] = useState<ReturnChart | null>(null)
  const [lunarJd, setLunarJd] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => setYear(p.defaultYear), [p.defaultYear])
  useEffect(() => setPlace(home), [home.lat, home.lon]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (kind !== 'solar' || (!p.subject && !p.natalInput)) return
    setBusy(true)
    const q = p.subject
      ? api.solarReturn(p.subject.id, year, place, precessed)
      : api.solarReturnUnsaved(p.natalInput!, null, year, place, precessed, p.settings)
    q.then((r) => { setSet(r); setErr(null) }).catch((e) => setErr(e.message)).finally(() => setBusy(false))
  }, [kind, year, place, precessed, p.subject, p.natalInput, p.settings])

  useEffect(() => {
    if (kind !== 'lunar' || !p.subject) return
    api.lunarReturns(p.subject.id, year).then((xs) => { setLunars(xs); setErr(null); if (xs.length && (lunarJd === null || !xs.some((x) => x.jd_ut === lunarJd))) setLunarJd(xs[0].jd_ut) }).catch((e) => setErr(e.message))
  }, [kind, year, p.subject]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (kind !== 'lunar' || !p.subject || lunarJd === null) return
    setBusy(true)
    api.lunarReturn(p.subject.id, lunarJd, place).then((r) => { setLunar(r); setErr(null) }).catch((e) => setErr(e.message)).finally(() => setBusy(false))
  }, [kind, lunarJd, place, p.subject])

  const pick = (c: City) => setPlace({ lat: c.lat, lon: c.lon, name: c.label })
  const shown: ReturnChart | null = kind === 'solar' ? set?.chosen ?? null : lunar
  const shownWheel = useMemo(() => (shown ? wheelFromChart(shown.chart) : null), [shown])

  const saveAsChart = useCallback(async () => {
    if (!shown) return
    const name = `${p.subject?.name ?? 'Chart'} ${kind === 'solar' ? 'SR' : 'LR'} ${shown.year}${shown.place.name ? ` ${shown.place.name}` : ''}`
    const s: SubjectIn = {
      name, kind: 'event', tags: [kind === 'solar' ? 'solar-return' : 'lunar-return'], notes: '',
      datetime_local: shown.local_datetime.slice(0, 16) + ':00', time_confidence: 'exact', place_name: shown.place.name,
      lat: shown.place.lat, lon: shown.place.lon, timezone: shown.timezone, utc_offset_override: null,
      home_place_name: '', home_lat: null, home_lon: null, home_timezone: null, settings: {},
    }
    try { p.onSaved(await api.createSubject(s)) } catch (e) { setErr((e as Error).message) }
  }, [shown, kind, p])

  if (!p.subject && !p.natalInput) return <div className="empty-state">Open a chart first.</div>

  const smallWheel = (r: ReturnChart, title: string) => (
    <div className="small-return" key={title}>
      <h4>{title} <small>{r.year}{r.place.name ? ` · ${r.place.name}` : ''}</small></h4>
      <Wheel data={wheelFromChart(r.chart)} />
      <FactsStrip r={r} />
    </div>
  )

  return (
    <div className="returns">
      <div className="returns-head">
        <div className="seg">
          <button className={kind === 'solar' ? 'active' : ''} onClick={() => setKind('solar')}>Solar</button>
          <button className={kind === 'lunar' ? 'active' : ''} onClick={() => setKind('lunar')} disabled={!p.subject} title={p.subject ? '' : 'Save the chart first'}>Lunar</button>
        </div>
        <label>Year<input type="number" value={year} onChange={(e) => setYear(Number(e.target.value) || year)} /></label>
        <label>Place<CitySearch value={place.name} onPick={pick} placeholder="City for the return" /></label>
        <button className="secondary" onClick={() => setPlace(home)} disabled={place.lat === home.lat && place.lon === home.lon}>Home</button>
        {kind === 'solar' && <label className="switch"><input type="checkbox" checked={precessed} onChange={(e) => setPrecessed(e.target.checked)} /> Precessed</label>}
        <div className="seg">
          <button className={layout === 'wheel' ? 'active' : ''} onClick={() => setLayout('wheel')}>Return</button>
          <button className={layout === 'biwheel' ? 'active' : ''} onClick={() => setLayout('biwheel')}>Around natal</button>
          <button className={layout === 'table' ? 'active' : ''} onClick={() => setLayout('table')}>Table</button>
        </div>
        {shown && <button onClick={() => p.onJump(shown.jd_ut, shown.place)}>Open in time travel</button>}
        {shown && p.subject && <button onClick={() => void saveAsChart()}>Save as chart</button>}
        {busy && <span className="hint">computing…</span>}
      </div>
      {err && <div className="error">{err}</div>}
      {kind === 'lunar' && lunars.length > 0 && (
        <div className="lunar-list">
          {lunars.map((l) => <button key={l.jd_ut} className={l.jd_ut === lunarJd ? 'active' : ''} onClick={() => setLunarJd(l.jd_ut)}>{fmt(l.local_datetime).slice(0, 10)}</button>)}
          <small>Lunar returns of {year} at home ({lunars[0].timezone})</small>
        </div>
      )}
      {shown && shownWheel && (
        <div className="return-main">
          {layout === 'table' ? <TableView chart={shown.chart} /> : (
            <div className="wheel-wrap">
              {layout === 'biwheel' && p.natalWheelData
                ? <Wheel data={p.natalWheelData} transits={{ planets: shownWheel.planets, aspects: [] }} />
                : <Wheel data={shownWheel} />}
            </div>
          )}
          <FactsStrip r={shown} />
          {layout === 'biwheel' && <small className="hint">Natal inside, the return outside in blue. House numbers and cusps are natal; the return\'s own houses are on the "Return" layout and in the table.</small>}
        </div>
      )}
      {kind === 'solar' && set && (
        <div className="side-by-side">
          {smallWheel(set.previous, 'Previous')}
          {smallWheel(set.chosen, 'Chosen')}
          {smallWheel(set.base, 'Base (home)')}
        </div>
      )}
    </div>
  )
}
