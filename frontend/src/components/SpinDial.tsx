import { useEffect, useRef } from 'react'
import { drag } from 'd3-drag'
import { select } from 'd3-selection'

/**
 * A knob: drag it away from the top to play time. Right of top = forward, left = backward; the further
 * from the top, the faster, up to the chosen speed. Release to stop. The knob snaps back.
 */
export function SpinDial({ onRate, size = 96 }: { onRate: (rate: number) => void; size?: number }) {
  const ref = useRef<SVGSVGElement>(null)
  const knob = useRef<SVGCircleElement>(null)
  const c = size / 2
  const r = size / 2 - 10

  useEffect(() => {
    if (!ref.current || !knob.current) return
    const svg = ref.current
    const k = select(knob.current)
    const angleOf = (x: number, y: number) => Math.atan2(x - c, c - y) // 0 at top, + clockwise
    const behaviour = drag<SVGCircleElement, unknown>()
      .container(svg)
      .on('drag', (ev) => {
        let a = angleOf(ev.x, ev.y)
        a = Math.max(-Math.PI * 0.95, Math.min(Math.PI * 0.95, a))
        k.attr('cx', c + r * Math.sin(a)).attr('cy', c - r * Math.cos(a))
        onRate(Math.sign(a) * Math.pow(Math.abs(a) / Math.PI, 1.5))
      })
      .on('end', () => { k.attr('cx', c).attr('cy', c - r); onRate(0) })
    k.call(behaviour)
    return () => { k.on('.drag', null) }
  }, [c, r, onRate])

  return (
    <svg ref={ref} width={size} height={size} className="spin-dial" aria-label="Spin dial: drag to play time">
      <circle cx={c} cy={c} r={r} fill="none" stroke="#bbb" strokeWidth={6} />
      <path d={`M${c} ${c - r}A${r} ${r} 0 0 1 ${c + r * Math.sin(Math.PI * 0.95)} ${c - r * Math.cos(Math.PI * 0.95)}`} fill="none" stroke="#2a9d8f" strokeWidth={6} opacity={0.5} />
      <path d={`M${c} ${c - r}A${r} ${r} 0 0 0 ${c - r * Math.sin(Math.PI * 0.95)} ${c - r * Math.cos(Math.PI * 0.95)}`} fill="none" stroke="#e76f51" strokeWidth={6} opacity={0.5} />
      <text x={c} y={c + 4} textAnchor="middle" className="dial-text">drag</text>
      <circle ref={knob} cx={c} cy={c - r} r={9} fill="#333" style={{ cursor: 'grab' }} />
    </svg>
  )
}
