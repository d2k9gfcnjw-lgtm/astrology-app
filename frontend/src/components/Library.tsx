import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import type { Subject } from '../lib/types'

interface Props {
  selectedId: string | null
  refreshKey: number
  onOpen: (s: Subject) => void
  onEdit: (s: Subject) => void
  onNew: (owner?: Subject) => void
}

export function Library({ selectedId, refreshKey, onOpen, onEdit, onNew }: Props) {
  const [q, setQ] = useState('')
  const [tag, setTag] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [items, setItems] = useState<Subject[]>([])
  const [err, setErr] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())

  useEffect(() => {
    api.subjects(q || undefined, tag || undefined).then((s) => { setItems(s); setErr(null) }).catch((e) => setErr(e.message))
    api.tags().then(setTags).catch(() => undefined)
  }, [q, tag, refreshKey])

  const groups = useMemo(() => {
    const people = items.filter((s) => s.kind === 'person').sort((a, b) => a.name.localeCompare(b.name))
    const byOwner = new Map<string, Subject[]>()
    const orphans: Subject[] = []
    for (const s of items) {
      if (s.kind === 'person') continue
      if (s.owner_id && people.some((p) => p.id === s.owner_id)) byOwner.set(s.owner_id, [...(byOwner.get(s.owner_id) ?? []), s])
      else orphans.push(s)
    }
    const sortCharts = (xs: Subject[]) => xs.sort((a, b) => a.datetime_local.localeCompare(b.datetime_local))
    return { people, byOwner: new Map([...byOwner].map(([k, v]) => [k, sortCharts(v)])), orphans: sortCharts(orphans) }
  }, [items])

  const remove = async (s: Subject) => {
    if (!window.confirm(`Remove "${s.name}" from the library? It can be restored later.`)) return
    await api.deleteSubject(s.id)
    setItems((xs) => xs.filter((x) => x.id !== s.id))
  }
  const toggle = (id: string) => setCollapsed((c) => { const n = new Set(c); if (n.has(id)) n.delete(id); else n.add(id); return n })

  const chartRow = (s: Subject) => (
    <li key={s.id} className={`chart-row${s.id === selectedId ? ' selected' : ''}`}>
      <button className="link" onClick={() => onOpen(s)}>
        <b>{s.name}</b>
        <small>{s.datetime_local.replace('T', ' ').slice(0, 16)} · {s.place_name || `${s.lat.toFixed(2)}, ${s.lon.toFixed(2)}`}</small>
        {s.tags.length > 0 && <small className="tags">{s.tags.join(', ')}</small>}
      </button>
      <span className="actions">
        <button className="icon" title="Edit" onClick={() => onEdit(s)}>✎</button>
        <button className="icon" title="Remove" onClick={() => void remove(s)}>🗑</button>
      </span>
    </li>
  )

  return (
    <aside className="library">
      <div className="library-head">
        <h2>People</h2>
        <button onClick={() => onNew()}>+ Person</button>
      </div>
      <input placeholder="Search name, place, tag" value={q} onChange={(e) => setQ(e.target.value)} />
      {tags.length > 0 && (
        <select value={tag} onChange={(e) => setTag(e.target.value)}>
          <option value="">All tags</option>
          {tags.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      )}
      {err && <div className="error">{err}</div>}
      <ul className="people">
        {groups.people.map((p) => (
          <li key={p.id} className={`person${p.id === selectedId ? ' selected' : ''}`}>
            <div className="person-head">
              <button className="icon" onClick={() => toggle(p.id)} title={collapsed.has(p.id) ? 'Show charts' : 'Hide charts'}>{collapsed.has(p.id) ? '▸' : '▾'}</button>
              <button className="link" onClick={() => onOpen(p)}>
                <b>{p.name}</b>
                <small>born {p.datetime_local.replace('T', ' ').slice(0, 16)} · {p.place_name}</small>
                <small className={p.home_place_name ? 'home' : 'home missing'}>{p.home_place_name ? `lives in ${p.home_place_name}` : 'home not set'}</small>
              </button>
              <span className="actions">
                <button className="icon" title="Edit person and home" onClick={() => onEdit(p)}>✎</button>
                <button className="icon" title="Add a chart for this person" onClick={() => onNew(p)}>+</button>
                <button className="icon" title="Remove" onClick={() => void remove(p)}>🗑</button>
              </span>
            </div>
            {!collapsed.has(p.id) && <ul className="charts">{(groups.byOwner.get(p.id) ?? []).map(chartRow)}
              {(groups.byOwner.get(p.id) ?? []).length === 0 && <li className="empty">no returns or events yet</li>}</ul>}
          </li>
        ))}
        {groups.orphans.length > 0 && (
          <li className="person"><div className="person-head"><b>Other charts</b> <small>(no owner; edit to assign one)</small></div><ul className="charts">{groups.orphans.map(chartRow)}</ul></li>
        )}
        {groups.people.length === 0 && groups.orphans.length === 0 && <li className="empty">No charts yet.</li>}
      </ul>
    </aside>
  )
}
