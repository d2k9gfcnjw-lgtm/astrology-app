import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Subject } from '../lib/types'

interface Props {
  selectedId: string | null
  refreshKey: number
  onOpen: (s: Subject) => void
  onEdit: (s: Subject) => void
  onNew: () => void
}

export function Library({ selectedId, refreshKey, onOpen, onEdit, onNew }: Props) {
  const [q, setQ] = useState('')
  const [tag, setTag] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [items, setItems] = useState<Subject[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    api.subjects(q || undefined, tag || undefined).then((s) => { setItems(s); setErr(null) }).catch((e) => setErr(e.message))
    api.tags().then(setTags).catch(() => undefined)
  }, [q, tag, refreshKey])

  const remove = async (s: Subject) => {
    if (!window.confirm(`Remove "${s.name}" from the library? It can be restored later.`)) return
    await api.deleteSubject(s.id)
    setItems((xs) => xs.filter((x) => x.id !== s.id))
  }

  return (
    <aside className="library">
      <div className="library-head">
        <h2>Charts</h2>
        <button onClick={onNew}>+ New</button>
      </div>
      <input placeholder="Search name, place, tag" value={q} onChange={(e) => setQ(e.target.value)} />
      {tags.length > 0 && (
        <select value={tag} onChange={(e) => setTag(e.target.value)}>
          <option value="">All tags</option>
          {tags.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      )}
      {err && <div className="error">{err}</div>}
      <ul>
        {items.map((s) => (
          <li key={s.id} className={s.id === selectedId ? 'selected' : ''}>
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
        ))}
        {items.length === 0 && <li className="empty">No charts yet.</li>}
      </ul>
    </aside>
  )
}
