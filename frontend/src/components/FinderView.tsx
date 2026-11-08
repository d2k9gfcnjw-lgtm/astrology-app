import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { BODY_NAMES } from '../lib/angles'
import type { CityResult, FinderResult, PlaceScore, Subject } from '../lib/types'
import { FinderMap } from './FinderMap'
import type { FeatureCollection } from 'geojson'

const GOALS = [['', 'No particular goal'], ['career', 'Career'], ['love', 'Love'], ['money', 'Money'], ['health', 'Health'], ['rest', 'Rest and protection'], ['inner_work', 'Inner work']]
const fmt = (iso: string) => iso.replace('T', ' ').slice(0, 16)
const stars = (n: number) => '★'.repeat(n) + '☆'.repeat(5 - n)
const houses = (h: number[]) => (h.length === 2 ? `${h[0]} and ${h[1]}` : String(h[0] ?? '–'))

function ScoreCard({ p, title }: { p: PlaceScore; title: string }) {
  return (
    <div className={`score-card tier-${p.tier}`}>
      <div className="score-head"><b>{title}</b> <span className="tier">{p.tier}</span> <span>{stars(p.stars)}</span> <small>{p.total > 0 ? '+' : ''}{p.total}</small></div>
      <div className="score-facts">
        <span>Asc in natal {p.facts.asc_natal_house}</span><span>Sun {houses(p.facts.sun_houses)}</span><span>Mars {houses(p.facts.mars_houses)}</span>
        {p.dominant && <span>{BODY_NAMES[p.dominant]} dominant</span>}
        {p.facts.stelliums.map((s) => <span key={s.house}>stellium {s.house}: {s.bodies.map((b) => BODY_NAMES[b]).join(', ')}</span>)}
        <span>{fmt(p.local_datetime)} {p.timezone ?? ''}</span>
      </div>
      {p.reasons.filter((r) => r.points <= -200).map((r, i) => <div key={i} className="reason hard">✖ {r.text}</div>)}
      {p.gains.length > 0 && <div className="reason-group"><b>Gains</b>{p.gains.map((r, i) => <div key={i} className="reason gain">+{r.points} {r.text}</div>)}</div>}
      {p.costs.filter((r) => r.points > -200).length > 0 && <div className="reason-group"><b>Price</b>{p.costs.filter((r) => r.points > -200).map((r, i) => <div key={i} className="reason cost">{r.points} {r.text}</div>)}</div>}
      {p.cautions.length > 0 && <div className="reason-group"><b>Cautions</b>{p.cautions.map((c, i) => <div key={i} className="reason caution">⚠ {c}</div>)}</div>}
      {p.robustness?.birth_time_tests && (
        <div className="reason-group"><b>Birth-time test</b>
          <div className="reason">Ascendant {p.robustness.asc_cusp_distance}° from the nearest natal cusp. {Object.entries(p.robustness.birth_time_tests).map(([k, v]) => `${k} min: ${v}`).join(' · ')}</div>
        </div>
      )}
      {p.versus_base && (p.versus_base.fixes?.length || p.versus_base.worsens?.length) ? (
        <div className="reason-group"><b>Versus home</b>
          {p.versus_base.fixes?.map((t, i) => <div key={`f${i}`} className="reason gain">fixes: {t}</div>)}
          {p.versus_base.worsens?.map((t, i) => <div key={`w${i}`} className="reason cost">adds: {t}</div>)}
          {p.marginal_vs_base && <div className="reason caution">Home is already clean and the gain is small: a marginal trip (SRG 19).</div>}
        </div>
      ) : null}
    </div>
  )
}

interface Props { subject: Subject | null; defaultYear: number; onOpenReturn: (year: number, lat: number, lon: number, name: string) => void }

export function FinderView({ subject, defaultYear, onOpenReturn }: Props) {
  const [year, setYear] = useState(defaultYear + 1)
  const [goal, setGoal] = useState('')
  const [floor, setFloor] = useState(15000)
  const [km, setKm] = useState(250)
  const [exclude, setExclude] = useState('')
  const [precessed, setPrecessed] = useState(false)
  const [safety, setSafety] = useState(true)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [result, setResult] = useState<FinderResult | null>(null)
  const [selected, setSelected] = useState<CityResult | null>(null)
  const [tierFilter, setTierFilter] = useState<string>('all')
  const [land, setLand] = useState<FeatureCollection | null>(null)
  const [query, setQuery] = useState('')

  useEffect(() => { fetch('/api/finder/land').then((r) => r.json()).then(setLand).catch(() => setLand(null)) }, [])

  const run = useCallback(async () => {
    if (!subject) return
    setBusy(true); setErr(null)
    try {
      const r = await api.finderRun({ subject_id: subject.id, year, goal: goal || null, population_floor: floor, airport_max_km: km,
        exclude_countries: exclude.split(',').map((x) => x.trim().toUpperCase()).filter(Boolean), precessed, safety_cusp_filter: safety, grid_step: 1 })
      setResult(r); setSelected(null)
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }, [subject, year, goal, floor, km, exclude, precessed, safety])

  const list = useMemo(() => {
    if (!result) return []
    const q = query.trim().toLowerCase()
    return result.cities.filter((c) => (tierFilter === 'all' ? c.tier !== 'disqualified' : c.tier === tierFilter)).filter((c) => !q || c.name.toLowerCase().includes(q) || c.country.toLowerCase() === q).slice(0, 300)
  }, [result, tierFilter, query])

  if (!subject) return <div className="empty-state">Save the chart to the library first; the finder works on saved charts.</div>

  return (
    <div className="finder">
      <div className="finder-form">
        <label>Year<input type="number" value={year} onChange={(e) => setYear(Number(e.target.value) || year)} /></label>
        <label>Goal<select value={goal} onChange={(e) => setGoal(e.target.value)}>{GOALS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></label>
        <label>City population at least<input type="number" step={5000} value={floor} onChange={(e) => setFloor(Number(e.target.value) || 0)} /></label>
        <label>Airport within km<input type="number" step={10} value={km} onChange={(e) => setKm(Number(e.target.value) || 0)} /></label>
        <label>Exclude countries<input value={exclude} placeholder="e.g. RU, CN" onChange={(e) => setExclude(e.target.value)} /></label>
        <label className="switch"><input type="checkbox" checked={precessed} onChange={(e) => setPrecessed(e.target.checked)} /> Precessed</label>
        <label className="switch"><input type="checkbox" checked={safety} onChange={(e) => setSafety(e.target.checked)} /> Ascendant ≥ 2.5° from natal cusps (SRG 7)</label>
        <button className="active" onClick={() => void run()} disabled={busy}>{busy ? 'Searching the world…' : 'Run finder'}</button>
        {err && <div className="error">{err}</div>}
      </div>
      <FinderMap result={result} selected={selected} onSelectCity={setSelected} onClickPlace={(lat, lon) => onOpenReturn(year, lat, lon, `${lat.toFixed(2)}, ${lon.toFixed(2)}`)} landGeoJson={land} />
      {result && (
        <div className="finder-body">
          <div className="finder-list">
            <div className="finder-list-head">
              <span className="hint">Several places can all be good; each has its price. {result.counts.best ?? 0} best · {result.counts.safe ?? 0} safe · {result.counts.marginal ?? 0} marginal · {result.counts.disqualified ?? 0} out</span>
              <select value={tierFilter} onChange={(e) => setTierFilter(e.target.value)}><option value="all">Best, safe and marginal</option><option value="best">Best</option><option value="safe">Safe</option><option value="marginal">Marginal</option><option value="disqualified">Disqualified</option></select>
              <input placeholder="Filter by city or country code" value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>
            <div className="scroll"><table>
              <thead><tr><th>Place</th><th>Tier</th><th>Stars</th><th>Airport</th><th>Local SR time</th><th>Asc natal</th><th>Sun</th><th>Mars</th><th>Dominant</th></tr></thead>
              <tbody>{list.map((c) => (
                <tr key={`${c.name}-${c.country}-${c.lat}`} className={`tier-${c.tier}${selected === c ? ' selected' : ''}`} onClick={() => setSelected(c)}>
                  <td>{c.name}{c.admin1 && ['US', 'CA', 'AU'].includes(c.country) ? `, ${c.admin1}` : ''}, {c.country}</td><td>{c.tier}{c.robustness?.flips ? ' ⚠' : ''}</td><td>{stars(c.stars)} <small>{c.total}</small></td>
                  <td>{c.airport_code} {c.airport_km} km</td><td className="nowrap">{fmt(c.local_datetime)}</td><td>{c.facts.asc_natal_house}</td><td>{houses(c.facts.sun_houses)}</td><td>{houses(c.facts.mars_houses)}</td><td>{c.dominant ? BODY_NAMES[c.dominant] : ''}</td>
                </tr>))}</tbody>
            </table></div>
          </div>
          <div className="finder-side">
            {selected ? (
              <>
                <ScoreCard p={selected} title={`${selected.name}, ${selected.country}`} />
                <button onClick={() => onOpenReturn(year, selected.lat, selected.lon, `${selected.name}, ${selected.country}`)}>Open this return</button>
              </>
            ) : <div className="hint">Click a city on the map or in the list.</div>}
            <div className="context-panel">
              <h3>The year's transits</h3>
              {result.context.themes.map((t, i) => <div key={i} className="reason">{t}</div>)}
              {result.context.heavy_hits.length > 0 && <div className="reason caution">Heavy hits: {result.context.heavy_hits.map((h) => `${BODY_NAMES[h.body]} ${h.aspect} ${h.natal_point.toUpperCase()} (${h.local_datetime.slice(0, 10)})`).join('; ')}</div>}
            </div>
            <ScoreCard p={result.base} title="Base (home)" />
            <ScoreCard p={result.previous} title="Previous return (home)" />
          </div>
        </div>
      )}
    </div>
  )
}
