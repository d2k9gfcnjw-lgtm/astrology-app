import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import type { City } from '../lib/types'

export function CitySearch({ value, onPick, placeholder = 'City search' }: { value: string; onPick: (c: City) => void; placeholder?: string }) {
  const [q, setQ] = useState(value)
  const [hits, setHits] = useState<City[]>([])
  const [open, setOpen] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const timer = useRef<number | null>(null)

  useEffect(() => setQ(value), [value])

  useEffect(() => {
    if (timer.current) window.clearTimeout(timer.current)
    if (!open || q.trim().length < 2) { setHits([]); return }
    timer.current = window.setTimeout(() => {
      api.cities(q).then((h) => { setHits(h); setErr(null) }).catch((e) => setErr(String(e.message)))
    }, 150)
  }, [q, open])

  return (
    <div className="city-search">
      <input value={q} placeholder={placeholder} onChange={(e) => { setQ(e.target.value); setOpen(true) }} onFocus={() => setOpen(true)} onBlur={() => window.setTimeout(() => setOpen(false), 150)} />
      {err && <div className="error">{err}</div>}
      {open && hits.length > 0 && (
        <ul className="dropdown">
          {hits.map((c) => (
            <li key={c.geonameid} onMouseDown={() => { onPick(c); setQ(c.label); setOpen(false) }}>
              <span>{c.label}</span><small>{c.timezone} · {c.lat.toFixed(2)}, {c.lon.toFixed(2)}</small>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
