import type { Aspect, AspectSettings, Chart, Keyframe, WheelData } from './types'

export function wheelFromChart(c: Chart): WheelData {
  const planets: WheelData['planets'] = {}
  for (const [k, v] of Object.entries(c.planets)) planets[k] = { lon: v.lon, retrograde: v.retrograde }
  if (c.fortune) planets.fortune = { lon: c.fortune.lon, retrograde: false }
  return {
    planets,
    cusps: Array.from({ length: 12 }, (_, i) => c.houses.cusps[String(i + 1)]),
    asc: c.houses.asc,
    mc: c.houses.mc,
    aspects: c.aspects,
    systemUsed: c.houses.system_used,
  }
}

const MAJOR: Record<string, number> = { conjunction: 0, sextile: 60, square: 90, trine: 120, opposition: 180 }
const MINOR: Record<string, number> = { semisextile: 30, semisquare: 45, sesquiquadrate: 135, quincunx: 150 }

/** Client-side aspects for spin frames (same rule as the backend: orb on each side, luminary bonus). */
export function aspectsFromLongitudes(lons: Record<string, number>, settings: AspectSettings): Aspect[] {
  const table = { ...MAJOR, ...(settings.minor_aspects ? MINOR : {}) }
  const points = new Set(['node', 'chiron', 'lilith', 'fortune'])
  const keys = Object.keys(lons).filter((k) => settings.include_points || !points.has(k))
  const out: Aspect[] = []
  for (let i = 0; i < keys.length; i++) {
    for (let j = i + 1; j < keys.length; j++) {
      const a = keys[i]
      const b = keys[j]
      const sep = Math.abs(((lons[a] - lons[b] + 540) % 360) - 180)
      const bonus = a === 'sun' || a === 'moon' || b === 'sun' || b === 'moon' ? settings.luminary_bonus : 0
      let best: Aspect | null = null
      for (const [type, angle] of Object.entries(table)) {
        const maxOrb = (type in MAJOR ? settings.orbs[type] ?? settings.minor_orb : settings.minor_orb) + bonus
        const orb = Math.abs(sep - angle)
        if (orb <= maxOrb && (!best || orb < best.orb)) best = { a, b, type, angle, separation: sep, orb, max_orb: maxOrb, applying: false, exact: orb < 1e-9 }
      }
      if (best) out.push(best)
    }
  }
  return out
}

export function wheelFromFrame(f: Keyframe, settings: AspectSettings, includeAspects = true): WheelData {
  const planets: WheelData['planets'] = {}
  for (const [k, lon] of Object.entries(f.planets)) planets[k] = { lon, retrograde: f.speeds[k] < 0 }
  return { planets, cusps: f.cusps, asc: f.asc, mc: f.mc, aspects: includeAspects ? aspectsFromLongitudes(f.planets, settings) : [], systemUsed: f.system_used }
}
