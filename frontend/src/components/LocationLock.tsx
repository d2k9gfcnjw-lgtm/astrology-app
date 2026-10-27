import { CitySearch } from './CitySearch'
import type { City } from '../lib/types'

interface Props {
  locked: boolean
  onLock: (v: boolean) => void
  placeName: string
  lat: number
  lon: number
  onPlace: (lat: number, lon: number, name: string, timezone: string | null) => void
  relocatedFrom: [number, number] | null
}

export function LocationLock(p: Props) {
  const pick = (c: City) => p.onPlace(c.lat, c.lon, c.label, c.timezone)
  return (
    <div className={`location${p.locked ? ' locked' : ''}`}>
      <label className="switch"><input type="checkbox" checked={p.locked} onChange={(e) => p.onLock(e.target.checked)} /> Location lock</label>
      <span className="hint">{p.locked ? 'Moment frozen: only houses and angles move.' : 'Changing the place keeps the same local clock time.'}</span>
      <CitySearch value={p.placeName} onPick={pick} placeholder="Relocate to city" />
      <span className="coords">
        <input type="number" step="0.01" value={p.lat} onChange={(e) => p.onPlace(Number(e.target.value), p.lon, '', null)} />
        <input type="number" step="0.01" value={p.lon} onChange={(e) => p.onPlace(p.lat, Number(e.target.value), '', null)} />
      </span>
      {p.relocatedFrom && <span className="hint">Relocated from {p.relocatedFrom[0].toFixed(2)}, {p.relocatedFrom[1].toFixed(2)}</span>}
    </div>
  )
}
