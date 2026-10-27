import { useMemo, useRef, useState } from 'react'
import { ASPECT_STYLE, BODY_NAMES, BODY_ORDER, ELEMENT_COLORS, ELEMENT_OF_SIGN, SIGN_NAMES, formatDM, norm } from '../lib/angles'
import { BODY_PATHS, Glyph, SIGN_PATHS } from '../lib/glyphs'
import { spreadLabels } from '../lib/spread'
import { lonFromPoint, pointOnWheel } from '../lib/wheelGeometry'
import type { Aspect, WheelData } from '../lib/types'

const SIZE = 600
const C = SIZE / 2
const R_OUTER = 292
const R_SIGN_IN = 258
const R_HOUSE_NUM = 246
const R_TICK = 256
const R_GLYPH = 222
const R_DEG = 196
const R_DEG_ALT = 182 // second row for degree labels when neighbours are close
const R_ASPECT = 160
const LABEL_GAP = 9 // degrees between planet labels at the glyph radius
// Transit ring (bi-wheel) outside the sign ring
const R_T_IN = 300
const R_T_GLYPH = 320
const R_T_DEG = 345
const R_T_OUT = 358

export interface TransitRing {
  planets: Record<string, { lon: number; retrograde: boolean }>
  aspects: Aspect[]                      // transit-to-natal aspects (a = transit body, b = natal point)
  onDrop?: (body: string, lon: number) => void
}

interface Props {
  data: WheelData
  transits?: TransitRing | null
  highlight?: string | null
  onSelect?: (key: string | null) => void
}

const NATAL_LABELS: Record<string, string> = { asc: 'AC', dsc: 'DC', mc: 'MC', ic: 'IC' }

export function Wheel({ data, transits, highlight, onSelect }: Props) {
  const asc = data.asc
  const toXY = (lon: number, r: number) => pointOnWheel(lon, r, asc, C)
  const svgRef = useRef<SVGSVGElement>(null)
  const [drag, setDrag] = useState<{ body: string; lon: number } | null>(null)

  const keys = useMemo(() => BODY_ORDER.filter((k) => k in data.planets), [data.planets])
  const spread = useMemo(() => spreadLabels(keys.map((k) => data.planets[k].lon), LABEL_GAP), [keys, data.planets])

  const natalLon = (key: string): number | undefined => {
    if (key in data.planets) return data.planets[key].lon
    if (key === 'asc') return data.asc
    if (key === 'dsc') return norm(data.asc + 180)
    if (key === 'mc') return data.mc
    if (key === 'ic') return norm(data.mc + 180)
    const m = /^cusp_(\d+)$/.exec(key)
    if (m) return data.cusps[Number(m[1]) - 1]
    return undefined
  }

  const signWedges = []
  for (let i = 0; i < 12; i++) {
    const a0 = toXY(i * 30, R_OUTER)
    const a1 = toXY(i * 30 + 30, R_OUTER)
    const b0 = toXY(i * 30, R_SIGN_IN)
    const b1 = toXY(i * 30 + 30, R_SIGN_IN)
    const mid = toXY(i * 30 + 15, (R_OUTER + R_SIGN_IN) / 2)
    const color = ELEMENT_COLORS[ELEMENT_OF_SIGN[i]]
    signWedges.push(
      <g key={i}>
        <path d={`M${a0.x} ${a0.y}A${R_OUTER} ${R_OUTER} 0 0 0 ${a1.x} ${a1.y}L${b1.x} ${b1.y}A${R_SIGN_IN} ${R_SIGN_IN} 0 0 1 ${b0.x} ${b0.y}Z`} fill={color} fillOpacity={0.16} stroke={color} strokeOpacity={0.6} strokeWidth={0.8} />
        <Glyph d={SIGN_PATHS[i]} x={mid.x} y={mid.y} size={20} color={color} strokeWidth={1.8} title={SIGN_NAMES[i]} />
      </g>,
    )
  }

  const cuspLines = data.cusps.map((lon, i) => {
    const isAngle = i === 0 || i === 3 || i === 6 || i === 9
    const a = toXY(lon, R_SIGN_IN)
    const b = toXY(lon, R_ASPECT)
    const next = data.cusps[(i + 1) % 12]
    const midLon = lon + ((next - lon + 360) % 360) / 2
    const n = toXY(midLon, R_HOUSE_NUM)
    const dl = toXY(lon, R_SIGN_IN + 11)
    let rot = -(180 + (lon - asc)) + 90 // tangent to the ring
    rot = ((rot % 360) + 360) % 360
    if (rot > 90 && rot < 270) rot -= 180 // never upside down
    return (
      <g key={i} className="cusp">
        <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={isAngle ? '#222' : '#888'} strokeWidth={isAngle ? 2.2 : 0.8} />
        <text x={n.x} y={n.y} className="house-num" textAnchor="middle" dominantBaseline="middle">{i + 1}</text>
        <text x={dl.x} y={dl.y} className="cusp-deg" textAnchor="middle" dominantBaseline="middle" transform={`rotate(${rot} ${dl.x} ${dl.y})`}>{formatDM(lon)}</text>
      </g>
    )
  })

  const angleLabels = [
    { lon: data.asc, text: 'AC' }, { lon: data.mc, text: 'MC' }, { lon: norm(data.asc + 180), text: 'DC' }, { lon: norm(data.mc + 180), text: 'IC' },
  ].map(({ lon, text }) => {
    const p = toXY(lon, transits ? R_T_OUT + 12 : R_OUTER + 14)
    return <text key={text} x={p.x} y={p.y} className="angle-label" textAnchor="middle" dominantBaseline="middle">{text}</text>
  })

  const natalAspectLines = data.aspects.map((a, i) => {
    const pa = data.planets[a.a]
    const pb = data.planets[a.b]
    if (!pa || !pb) return null
    const s = ASPECT_STYLE[a.type] ?? ASPECT_STYLE.quincunx
    const p = toXY(pa.lon, R_ASPECT)
    const q = toXY(pb.lon, R_ASPECT)
    const dim = (highlight && highlight !== a.a && highlight !== a.b) || transits
    return <line key={i} x1={p.x} y1={p.y} x2={q.x} y2={q.y} stroke={s.color} strokeWidth={s.width} strokeDasharray={s.dash} opacity={dim ? 0.15 : 1 - a.orb / a.max_orb * 0.5}><title>{`${BODY_NAMES[a.a]} ${a.type} ${BODY_NAMES[a.b]} (orb ${a.orb.toFixed(2)}°)`}</title></line>
  })

  const transitAspectLines = (transits?.aspects ?? []).map((a, i) => {
    const t = transits?.planets[a.a]
    const nl = natalLon(a.b)
    if (!t || nl === undefined) return null
    const s = ASPECT_STYLE[a.type] ?? ASPECT_STYLE.quincunx
    const p = toXY(t.lon, R_ASPECT)
    const q = toXY(nl, R_ASPECT)
    const dim = highlight && highlight !== a.a && highlight !== a.b
    return <line key={`t${i}`} x1={p.x} y1={p.y} x2={q.x} y2={q.y} stroke={s.color} strokeWidth={s.width + 0.4} strokeDasharray={s.dash} opacity={dim ? 0.15 : 1 - a.orb / a.max_orb * 0.6}><title>{`transit ${BODY_NAMES[a.a]} ${a.type} natal ${NATAL_LABELS[a.b] ?? BODY_NAMES[a.b] ?? a.b} (orb ${a.orb.toFixed(2)}°)`}</title></line>
  })

  // Stagger the degree text inward when neighbouring labels sit close together.
  const degRadius = keys.map(() => R_DEG)
  const bySpread = keys.map((_, i) => i).sort((a, b) => spread[a] - spread[b])
  for (let n = 1; n < bySpread.length; n++) {
    const prev = bySpread[n - 1]
    const cur = bySpread[n]
    if (norm(spread[cur] - spread[prev]) < 12 && degRadius[prev] === R_DEG) degRadius[cur] = R_DEG_ALT
  }
  const planetMarks = keys.map((k, i) => {
    const body = data.planets[k]
    const tick0 = toXY(body.lon, R_SIGN_IN)
    const tick1 = toXY(body.lon, R_TICK - 6)
    const g = toXY(spread[i], R_GLYPH)
    const lead = toXY(spread[i], R_GLYPH + 13)
    const d = toXY(spread[i], degRadius[i])
    const sel = highlight === k
    return (
      <g key={k} className={`planet${sel ? ' selected' : ''}`} onClick={() => onSelect?.(sel ? null : k)} style={{ cursor: 'pointer' }}>
        <line x1={tick0.x} y1={tick0.y} x2={tick1.x} y2={tick1.y} stroke="#333" strokeWidth={1.5} />
        <line x1={tick1.x} y1={tick1.y} x2={lead.x} y2={lead.y} stroke="#999" strokeWidth={0.7} />
        <Glyph d={BODY_PATHS[k]} x={g.x} y={g.y} size={24} color={sel ? '#b5179e' : '#111'} strokeWidth={2} title={BODY_NAMES[k]} />
        <text x={d.x} y={d.y} className="planet-deg" textAnchor="middle" dominantBaseline="middle">
          {formatDM(body.lon)}{body.retrograde ? '℞' : ''}
        </text>
      </g>
    )
  })

  // ---- transit ring -------------------------------------------------------
  const tKeys = useMemo(() => (transits ? BODY_ORDER.filter((k) => k in transits.planets) : []), [transits])
  const tSpread = useMemo(() => (transits ? spreadLabels(tKeys.map((k) => transits.planets[k].lon), LABEL_GAP) : []), [tKeys, transits])

  const svgPoint = (e: React.PointerEvent): { x: number; y: number } | null => {
    const svg = svgRef.current
    if (!svg) return null
    const ctm = svg.getScreenCTM()
    if (!ctm) return null
    const pt = new DOMPoint(e.clientX, e.clientY).matrixTransform(ctm.inverse())
    return { x: pt.x, y: pt.y }
  }

  const transitMarks = tKeys.map((k, i) => {
    const body = transits!.planets[k]
    const tick0 = toXY(body.lon, R_OUTER)
    const tick1 = toXY(body.lon, R_T_IN + 4)
    const g = toXY(tSpread[i], R_T_GLYPH)
    const lead = toXY(tSpread[i], R_T_GLYPH - 12)
    const d = toXY(tSpread[i], R_T_DEG)
    const sel = highlight === k
    const beingDragged = drag?.body === k
    return (
      <g key={`t-${k}`} className={`planet transit${sel ? ' selected' : ''}`} style={{ cursor: transits?.onDrop ? 'grab' : 'pointer', opacity: beingDragged ? 0.35 : 1 }}
        onClick={() => { if (!drag) onSelect?.(sel ? null : k) }}
        onPointerDown={(e) => {
          if (!transits?.onDrop) return
          e.preventDefault()
          ;(e.currentTarget.ownerSVGElement ?? e.currentTarget).setPointerCapture?.(e.pointerId)
          setDrag({ body: k, lon: body.lon })
        }}>
        <line x1={tick0.x} y1={tick0.y} x2={tick1.x} y2={tick1.y} stroke="#1d4ed8" strokeWidth={1.6} />
        <line x1={tick1.x} y1={tick1.y} x2={lead.x} y2={lead.y} stroke="#9bb" strokeWidth={0.7} />
        <Glyph d={BODY_PATHS[k]} x={g.x} y={g.y} size={22} color={sel ? '#b5179e' : '#1d4ed8'} strokeWidth={2} title={`transit ${BODY_NAMES[k]}`} />
        <text x={d.x} y={d.y} className="planet-deg transit-deg" textAnchor="middle" dominantBaseline="middle">
          {formatDM(body.lon)}{body.retrograde ? '℞' : ''}
        </text>
      </g>
    )
  })

  const ghost = drag ? (() => {
    const g = toXY(drag.lon, R_T_GLYPH)
    const d = toXY(drag.lon, R_T_DEG)
    const t0 = toXY(drag.lon, R_OUTER)
    const t1 = toXY(drag.lon, R_T_IN + 4)
    return (
      <g className="drag-ghost" pointerEvents="none">
        <line x1={t0.x} y1={t0.y} x2={t1.x} y2={t1.y} stroke="#b5179e" strokeWidth={2} />
        <Glyph d={BODY_PATHS[drag.body]} x={g.x} y={g.y} size={24} color="#b5179e" strokeWidth={2.2} />
        <text x={d.x} y={d.y} className="planet-deg" fill="#b5179e" textAnchor="middle" dominantBaseline="middle">{formatDM(drag.lon)} {SIGN_NAMES[Math.floor(norm(drag.lon) / 30)].slice(0, 3)}</text>
      </g>
    )
  })() : null

  const vb = transits ? `-${R_T_OUT - C + 16} -${R_T_OUT - C + 16} ${2 * R_T_OUT + 32} ${2 * R_T_OUT + 32}` : `0 0 ${SIZE} ${SIZE}`

  return (
    <svg ref={svgRef} viewBox={vb} className={`wheel${transits ? ' biwheel' : ''}`} role="img" aria-label="Chart wheel"
      onPointerMove={(e) => { if (!drag) return; const p = svgPoint(e); if (p) setDrag({ body: drag.body, lon: lonFromPoint(p.x, p.y, asc, C) }) }}
      onPointerUp={() => { if (drag) { transits?.onDrop?.(drag.body, drag.lon); setDrag(null) } }}
      onPointerCancel={() => setDrag(null)}>
      {transits && <circle cx={C} cy={C} r={R_T_OUT} fill="#f7f9ff" stroke="#1d4ed8" strokeOpacity={0.5} strokeWidth={1} />}
      {transits && <circle cx={C} cy={C} r={R_T_IN} fill="none" stroke="#1d4ed8" strokeOpacity={0.3} strokeWidth={0.8} />}
      <circle cx={C} cy={C} r={R_OUTER} fill="#fff" stroke="#333" strokeWidth={1} />
      {signWedges}
      <circle cx={C} cy={C} r={R_SIGN_IN} fill="none" stroke="#333" strokeWidth={1} />
      <circle cx={C} cy={C} r={R_ASPECT} fill="#fbfbfb" stroke="#333" strokeWidth={0.8} />
      {natalAspectLines}
      {transitAspectLines}
      {cuspLines}
      {angleLabels}
      {planetMarks}
      {transitMarks}
      {ghost}
      {data.systemUsed === 'whole_sign' && <text x={C} y={C} className="wheel-note" textAnchor="middle">Whole Sign</text>}
    </svg>
  )
}
