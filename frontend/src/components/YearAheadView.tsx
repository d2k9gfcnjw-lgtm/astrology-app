import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { BODY_NAMES, formatDM, signOf } from '../lib/angles'
import { groupHitsByBody } from '../lib/transitAspects'
import type { Settings, Subject, TransitHit, YearAhead } from '../lib/types'

const POINT_LABEL: Record<string, string> = { asc: 'AC', dsc: 'DC', mc: 'MC', ic: 'IC' }
const label = (k: string) => POINT_LABEL[k] ?? BODY_NAMES[k] ?? k.replace('cusp_', 'cusp ')
const fmt = (iso: string) => iso.replace('T', ' ').slice(0, 16)

interface Props {
  subject: Subject | null
  natalInput: { datetime_local: string; lat: number; lon: number; timezone: string | null; utc_offset_override: string | null } | null
  settings: Settings
  defaultYear: number
  onJump: (jd: number) => void
}

export function YearAheadView({ subject, natalInput, settings, defaultYear, onJump }: Props) {
  const [year, setYear] = useState(defaultYear)
  const [report, setReport] = useState<YearAhead | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [byBody, setByBody] = useState(true)
  const [bodies, setBodies] = useState<Set<string> | null>(null)
  const [showIngress, setShowIngress] = useState(true)
  const [showStations, setShowStations] = useState(true)

  useEffect(() => setYear(defaultYear), [defaultYear])

  useEffect(() => {
    if (!subject && !natalInput) return
    setBusy(true)
    const p = subject ? api.yearAhead(subject.id, year) : api.yearAheadUnsaved(natalInput!, year, settings)
    p.then((r) => { setReport(r); setErr(null); setBodies(null) }).catch((e) => setErr(e.message)).finally(() => setBusy(false))
  }, [subject, natalInput, year, settings])

  const order = useMemo(() => report ? ['pluto', 'neptune', 'uranus', 'saturn', 'jupiter', 'chiron', 'mars', 'venus', 'mercury', 'sun', 'moon', 'node', 'lilith'] : [], [report])
  const visible = useMemo(() => report ? report.hits.filter((h) => !bodies || bodies.has(h.body)) : [], [report, bodies])
  const groups = useMemo(() => groupHitsByBody(visible, order), [visible, order])

  const toggleBody = (b: string) => setBodies((cur) => {
    const next = new Set(cur ?? Object.keys(report?.counts ?? {}))
    if (next.has(b)) next.delete(b)
    else next.add(b)
    return next
  })

  if (!subject && !natalInput) return <div className="empty-state">Open a chart first.</div>

  const row = (h: TransitHit) => (
    <tr key={`${h.body}-${h.natal_point}-${h.aspect}-${h.jd_ut}`} onClick={() => onJump(h.jd_ut)} title="Show this moment on the bi-wheel">
      <td className="nowrap">{fmt(h.local_datetime)}</td>
      {!byBody && <td>{BODY_NAMES[h.body]}{h.retrograde ? ' ℞' : ''}</td>}
      <td>{h.aspect}</td>
      <td>{label(h.natal_point)} <small>{formatDM(h.natal_lon)} {signOf(h.natal_lon)}</small></td>
      <td className="nowrap">{h.pass_count > 1 ? `${h.pass_index} of ${h.pass_count}${h.retrograde ? ' ℞' : ''}` : h.retrograde ? '℞' : ''}</td>
      <td className="nowrap"><small>{h.orb_enter_local ? fmt(h.orb_enter_local).slice(0, 10) : '…'} → {h.orb_exit_local ? fmt(h.orb_exit_local).slice(0, 10) : '…'}</small></td>
    </tr>
  )

  return (
    <div className="year-ahead">
      <div className="year-head">
        <label>Year<input type="number" value={year} onChange={(e) => setYear(Number(e.target.value) || year)} /></label>
        {report && <span className="window">Solar return {fmt(report.local_start)} → next {fmt(report.local_end)}{report.timezone ? ` (${report.timezone})` : ''}</span>}
        <label className="switch"><input type="checkbox" checked={byBody} onChange={(e) => setByBody(e.target.checked)} /> Group by planet</label>
        <label className="switch"><input type="checkbox" checked={showIngress} onChange={(e) => setShowIngress(e.target.checked)} /> Ingresses</label>
        <label className="switch"><input type="checkbox" checked={showStations} onChange={(e) => setShowStations(e.target.checked)} /> Stations</label>
        {busy && <span className="hint">computing…</span>}
      </div>
      {err && <div className="error">{err}</div>}
      {report && (
        <div className="badges">
          {order.filter((b) => b in report.counts).map((b) => (
            <button key={b} className={`badge${!bodies || bodies.has(b) ? ' on' : ''}`} onClick={() => toggleBody(b)}>{BODY_NAMES[b]} <b>{report.counts[b]}</b></button>
          ))}
          <span className="hint">Bodies, orbs and natal points are in Settings. Click a row to see it on the bi-wheel.</span>
        </div>
      )}
      {report && byBody && groups.map((g) => (
        <section key={g.body}>
          <h3>{BODY_NAMES[g.body]} <small>{g.items.length} exact hits</small></h3>
          <table><thead><tr><th>Local time</th><th>Aspect</th><th>Natal point</th><th>Pass</th><th>Within orb</th></tr></thead>
            <tbody>{g.items.map(row)}</tbody></table>
        </section>
      ))}
      {report && !byBody && (
        <table><thead><tr><th>Local time</th><th>Transit</th><th>Aspect</th><th>Natal point</th><th>Pass</th><th>Within orb</th></tr></thead>
          <tbody>{visible.map(row)}</tbody></table>
      )}
      {report && showIngress && report.ingresses.length > 0 && (
        <section>
          <h3>Ingresses <small>{report.ingresses.length}</small></h3>
          <table><thead><tr><th>Local time</th><th>Transit</th><th>Enters</th><th></th></tr></thead>
            <tbody>{report.ingresses.filter((i) => !bodies || bodies.has(i.body)).map((i) => (
              <tr key={`${i.body}${i.kind}${i.jd_ut}`} onClick={() => onJump(i.jd_ut)}>
                <td className="nowrap">{fmt(i.local_datetime)}</td><td>{BODY_NAMES[i.body]}{i.retrograde ? ' ℞' : ''}</td>
                <td>{i.kind === 'house' ? `natal house ${i.entered}` : i.entered}</td><td><small>{i.retrograde ? 'retrograde, back into' : ''}</small></td>
              </tr>))}</tbody></table>
        </section>
      )}
      {report && showStations && report.stations.length > 0 && (
        <section>
          <h3>Stations <small>{report.stations.length}</small></h3>
          <table><thead><tr><th>Local time</th><th>Transit</th><th>Turns</th><th>At</th><th>Near natal</th></tr></thead>
            <tbody>{report.stations.filter((s) => !bodies || bodies.has(s.body)).map((s) => (
              <tr key={`${s.body}${s.jd_ut}`} onClick={() => onJump(s.jd_ut)}>
                <td className="nowrap">{fmt(s.local_datetime)}</td><td>{BODY_NAMES[s.body]}</td><td>{s.kind}</td>
                <td>{formatDM(s.lon)} {signOf(s.lon)}</td>
                <td><small>{s.near.map((n) => `${n.aspect} ${label(n.natal_point)} (${n.orb}°)`).join(', ') || '–'}</small></td>
              </tr>))}</tbody></table>
        </section>
      )}
    </div>
  )
}
