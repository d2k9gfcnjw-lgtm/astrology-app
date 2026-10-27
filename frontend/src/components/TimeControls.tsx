import { useState } from 'react'
import { SPIN_SPEEDS, type StepUnit, type WallClock, formatWall } from '../lib/time'
import { SpinDial } from './SpinDial'

interface Props {
  wall: WallClock
  timezone: string | null
  jd: number
  flags: string[]
  onStep: (amount: number, unit: StepUnit) => void
  onSetLocal: (iso: string) => void
  onNow: () => void
  onNatal: () => void
  hasNatal: boolean
  spinSpeed: number
  onSpinSpeed: (perSecond: number) => void
  onSpinRate: (rate: number) => void
  spinning: boolean
}

const UNITS: StepUnit[] = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']

export function TimeControls(p: Props) {
  const [unit, setUnit] = useState<StepUnit>('day')
  const [amount, setAmount] = useState(1)
  const [editing, setEditing] = useState<string | null>(null)
  const pad = (n: number) => n.toString().padStart(2, '0')
  const localIso = `${p.wall.year}-${pad(p.wall.month)}-${pad(p.wall.day)}T${pad(p.wall.hour)}:${pad(p.wall.minute)}:${pad(p.wall.second)}`

  return (
    <div className="time-controls">
      <div className="clock">
        <input type="datetime-local" step={1} value={editing ?? localIso} onChange={(e) => setEditing(e.target.value)}
          onBlur={() => { if (editing && editing !== localIso) p.onSetLocal(editing.length === 16 ? `${editing}:00` : editing); setEditing(null) }}
          onKeyDown={(e) => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }} />
        <span className="zone">{p.timezone ?? 'UTC'} ({p.wall.offset}{p.wall.zoneAbbrev ? `, ${p.wall.zoneAbbrev}` : ''})</span>
        <span className="jd">JD {p.jd.toFixed(5)} · {formatWall(p.wall)} local</span>
        {p.flags.length > 0 && <span className="flag">⚠ {p.flags.join(', ')}</span>}
      </div>
      <div className="steps">
        <button onClick={() => p.onStep(-amount, unit)} title="Step back">◀</button>
        <input type="number" min={1} value={amount} onChange={(e) => setAmount(Math.max(1, Number(e.target.value) || 1))} />
        <select value={unit} onChange={(e) => setUnit(e.target.value as StepUnit)}>
          {UNITS.map((u) => <option key={u} value={u}>{u}{amount === 1 ? '' : 's'}</option>)}
        </select>
        <button onClick={() => p.onStep(amount, unit)} title="Step forward">▶</button>
        <button onClick={p.onNow}>Now</button>
        <button onClick={p.onNatal} disabled={!p.hasNatal}>Natal</button>
      </div>
      <div className="spin">
        <label>Spin
          <select value={p.spinSpeed} onChange={(e) => p.onSpinSpeed(Number(e.target.value))}>
            {SPIN_SPEEDS.map((s) => <option key={s.perSecond} value={s.perSecond}>{s.label}</option>)}
          </select>
        </label>
        <button className={p.spinning ? 'active' : ''} onPointerDown={() => p.onSpinRate(-1)} onPointerUp={() => p.onSpinRate(0)} onPointerLeave={() => p.onSpinRate(0)} title="Hold to play backward">◀◀</button>
        <SpinDial onRate={p.onSpinRate} size={64} />
        <button className={p.spinning ? 'active' : ''} onPointerDown={() => p.onSpinRate(1)} onPointerUp={() => p.onSpinRate(0)} onPointerLeave={() => p.onSpinRate(0)} title="Hold to play forward">▶▶</button>
      </div>
    </div>
  )
}
