import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Kind, ResolvedTime, Subject, SubjectIn, TimeConfidence } from '../lib/types'
import { CitySearch } from './CitySearch'

const EMPTY: SubjectIn = {
  name: '', kind: 'person', tags: [], notes: '', datetime_local: '', time_confidence: 'exact', place_name: '',
  lat: 0, lon: 0, timezone: null, utc_offset_override: null,
  home_place_name: '', home_lat: null, home_lon: null, home_timezone: null, settings: {},
}

interface Props {
  initial?: Subject | null
  onSaved: (s: Subject) => void
  onPreview: (s: SubjectIn) => void
  onCancel: () => void
}

export function SubjectForm({ initial, onSaved, onPreview, onCancel }: Props) {
  const [f, setF] = useState<SubjectIn>(initial ? { ...initial } : EMPTY)
  const [date, setDate] = useState(initial ? initial.datetime_local.slice(0, 10) : '')
  const [time, setTime] = useState(initial ? initial.datetime_local.slice(11, 19) : '')
  const [tags, setTags] = useState(initial ? initial.tags.join(', ') : '')
  const [resolved, setResolved] = useState<ResolvedTime | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const set = (patch: Partial<SubjectIn>) => setF((x) => ({ ...x, ...patch }))
  const datetime = date && time ? `${date}T${time.length === 5 ? `${time}:00` : time}` : ''

  useEffect(() => {
    if (!datetime || (f.lat === 0 && f.lon === 0 && !f.place_name)) { setResolved(null); return }
    api.resolveTime(datetime, f.lat, f.lon, f.timezone, f.utc_offset_override).then((r) => { setResolved(r); setErr(null) }).catch((e) => { setResolved(null); setErr(e.message) })
  }, [datetime, f.lat, f.lon, f.timezone, f.utc_offset_override, f.place_name])

  const build = (): SubjectIn | null => {
    if (!f.name.trim()) { setErr('Give the chart a name'); return null }
    if (!datetime) { setErr('Date and time are needed'); return null }
    return { ...f, datetime_local: datetime, tags: tags.split(',').map((t) => t.trim()).filter(Boolean) }
  }

  const save = async () => {
    const s = build()
    if (!s) return
    setBusy(true)
    try {
      onSaved(initial ? await api.updateSubject(initial.id, s) : await api.createSubject(s))
    } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }

  return (
    <form className="subject-form" onSubmit={(e) => { e.preventDefault(); void save() }}>
      <h2>{initial ? 'Edit chart' : 'New chart'}</h2>
      <label>Name<input value={f.name} onChange={(e) => set({ name: e.target.value })} autoFocus /></label>
      <div className="row">
        <label>Kind
          <select value={f.kind} onChange={(e) => set({ kind: e.target.value as Kind })}>
            <option value="person">Person</option><option value="event">Event</option><option value="place">Place</option><option value="question">Question</option>
          </select>
        </label>
        <label>Time confidence
          <select value={f.time_confidence} onChange={(e) => set({ time_confidence: e.target.value as TimeConfidence })}>
            <option value="exact">Exact</option><option value="within_5_min">Within 5 min</option><option value="within_30_min">Within 30 min</option><option value="unknown">Unknown</option>
          </select>
        </label>
      </div>
      <div className="row">
        <label>Date<input type="date" value={date} onChange={(e) => setDate(e.target.value)} required /></label>
        <label>Local time<input type="time" step={1} value={time} onChange={(e) => setTime(e.target.value)} required /></label>
      </div>
      <label>Place
        <CitySearch value={f.place_name} onPick={(c) => set({ place_name: c.label, lat: c.lat, lon: c.lon, timezone: c.timezone })} />
      </label>
      <div className="row">
        <label>Latitude<input type="number" step="0.0001" value={f.lat} onChange={(e) => set({ lat: Number(e.target.value) })} /></label>
        <label>Longitude<input type="number" step="0.0001" value={f.lon} onChange={(e) => set({ lon: Number(e.target.value) })} /></label>
      </div>
      <div className="row">
        <label>Time zone<input value={f.timezone ?? ''} placeholder="from coordinates" onChange={(e) => set({ timezone: e.target.value || null })} /></label>
        <label>Offset override<input value={f.utc_offset_override ?? ''} placeholder="e.g. -05:00" onChange={(e) => set({ utc_offset_override: e.target.value || null })} /></label>
      </div>
      {resolved && (
        <div className={`resolved${resolved.flags.length ? ' flagged' : ''}`}>
          <div>Zone <b>{resolved.timezone ?? 'none'}</b>, offset used <b>{resolved.utc_offset}</b>, UT {resolved.utc_datetime.replace('T', ' ').slice(0, 16)}</div>
          {resolved.flags.map((fl) => <div key={fl} className="flag">⚠ {resolved.flag_text[fl]}</div>)}
        </div>
      )}
      <label>Lives in <small>(default place for lunar returns and the base solar return)</small>
        <CitySearch value={f.home_place_name} onPick={(c) => set({ home_place_name: c.label, home_lat: c.lat, home_lon: c.lon, home_timezone: c.timezone })} placeholder="City where the person lives now" />
      </label>
      <label>Tags<input value={tags} placeholder="comma separated" onChange={(e) => setTags(e.target.value)} /></label>
      <label>Notes<textarea value={f.notes} rows={2} onChange={(e) => set({ notes: e.target.value })} /></label>
      {err && <div className="error">{err}</div>}
      <div className="row buttons">
        <button type="submit" disabled={busy}>{initial ? 'Save changes' : 'Save to library'}</button>
        <button type="button" onClick={() => { const s = build(); if (s) onPreview(s) }}>Show without saving</button>
        <button type="button" className="secondary" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}
