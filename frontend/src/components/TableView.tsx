import { BODY_NAMES, BODY_ORDER, SIGN_NAMES, formatDM, signIndex } from '../lib/angles'
import type { BodyPosition, Chart } from '../lib/types'

const dms = (v: number) => {
  const sign = v < 0 ? '-' : '+'
  const total = Math.round(Math.abs(v) * 60)
  const d = Math.floor(total / 60)
  const m = total % 60
  return `${sign}${d}°${m.toString().padStart(2, '0')}'`
}

export function TableView({ chart, highlight, onSelect }: { chart: Chart; highlight?: string | null; onSelect?: (k: string | null) => void }) {
  const rows: [string, BodyPosition][] = BODY_ORDER.filter((k) => k in chart.planets).map((k) => [k, chart.planets[k]])
  if (chart.fortune) rows.push(['fortune', chart.fortune])
  return (
    <div className="table-view">
      <table>
        <thead>
          <tr><th>Body</th><th>Position</th><th>Sign</th><th>House</th><th>Speed/day</th><th>Lat</th><th>Decl</th></tr>
        </thead>
        <tbody>
          {rows.map(([k, b]) => (
            <tr key={k} className={highlight === k ? 'selected' : ''} onClick={() => onSelect?.(highlight === k ? null : k)}>
              <td>{BODY_NAMES[k]}{b.variant ? ` (${b.variant})` : ''}</td>
              <td>{formatDM(b.lon)}{b.retrograde ? ' ℞' : ''}</td>
              <td>{SIGN_NAMES[signIndex(b.lon)]}</td>
              <td>{chart.planet_houses[k]}</td>
              <td>{k === 'fortune' ? '' : dms(b.speed_lon)}</td>
              <td>{k === 'fortune' ? '' : dms(b.lat)}</td>
              <td>{dms(b.declination)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <table>
        <thead><tr><th>House</th><th>Cusp</th><th>Sign</th><th>Decl</th></tr></thead>
        <tbody>
          {Array.from({ length: 12 }, (_, i) => i + 1).map((h) => {
            const lon = chart.houses.cusps[String(h)]
            const label = h === 1 ? 'AC' : h === 10 ? 'MC' : h === 7 ? 'DC' : h === 4 ? 'IC' : String(h)
            return <tr key={h}><td>{label}</td><td>{formatDM(lon)}</td><td>{SIGN_NAMES[signIndex(lon)]}</td><td>{dms(chart.houses.cusp_declinations[String(h)])}</td></tr>
          })}
        </tbody>
      </table>
      <table>
        <thead><tr><th>Aspect</th><th>Orb</th><th></th></tr></thead>
        <tbody>
          {chart.aspects.map((a, i) => (
            <tr key={i} className={highlight && (highlight === a.a || highlight === a.b) ? 'selected' : ''}>
              <td>{BODY_NAMES[a.a]} {a.type} {BODY_NAMES[a.b]}</td>
              <td>{a.orb.toFixed(2)}°</td>
              <td>{a.exact ? 'exact' : a.applying ? 'applying' : 'separating'}</td>
            </tr>
          ))}
          {chart.aspects.length === 0 && <tr><td colSpan={3}>No aspects within orb</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
