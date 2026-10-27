import type { Aspect, TransitSettings } from './types'

const ANGLES: Record<string, number> = { conjunction: 0, opposition: 180, trine: 120, square: 90, sextile: 60, semisextile: 30, semisquare: 45, sesquiquadrate: 135, quincunx: 150 }

/** Transit-to-natal aspects within each transiting body's own orb (same rule as the backend report). */
export function transitAspects(transits: Record<string, number>, natal: Record<string, number>, ts: TransitSettings): Aspect[] {
  const out: Aspect[] = []
  for (const body of ts.bodies) {
    const tl = transits[body]
    if (tl === undefined) continue
    const maxOrb = ts.orbs[body] ?? 2
    for (const point of ts.natal_points) {
      const nl = natal[point]
      if (nl === undefined) continue
      const sep = Math.abs(((tl - nl + 540) % 360) - 180)
      let best: Aspect | null = null
      for (const type of ts.aspects) {
        const angle = ANGLES[type]
        const orb = Math.abs(sep - angle)
        if (orb <= maxOrb && (!best || orb < best.orb)) best = { a: body, b: point, type, angle, separation: sep, orb, max_orb: maxOrb, applying: false, exact: orb < 1e-9 }
      }
      if (best) out.push(best)
    }
  }
  return out.sort((x, y) => x.orb - y.orb)
}

export function groupHitsByBody<T extends { body: string }>(items: T[], order: string[]): { body: string; items: T[] }[] {
  const map = new Map<string, T[]>()
  for (const it of items) map.set(it.body, [...(map.get(it.body) ?? []), it])
  const keys = [...order.filter((b) => map.has(b)), ...[...map.keys()].filter((b) => !order.includes(b))]
  return keys.map((body) => ({ body, items: map.get(body)! }))
}
