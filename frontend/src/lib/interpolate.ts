import type { Keyframe } from './types'
import { diff, norm } from './angles'

export function lerpAngle(a: number, b: number, t: number): number {
  return norm(a + diff(a, b) * t)
}

/** Interpolate every angle in two keyframes at fraction t (0 = f0, 1 = f1). */
export function interpolateFrames(f0: Keyframe, f1: Keyframe, t: number): Keyframe {
  const planets: Record<string, number> = {}
  const speeds: Record<string, number> = {}
  for (const k of Object.keys(f0.planets)) {
    planets[k] = lerpAngle(f0.planets[k], f1.planets[k], t)
    speeds[k] = f0.speeds[k] + (f1.speeds[k] - f0.speeds[k]) * t
  }
  return {
    jd_ut: f0.jd_ut + (f1.jd_ut - f0.jd_ut) * t,
    planets,
    speeds,
    cusps: f0.cusps.map((c, i) => lerpAngle(c, f1.cusps[i], t)),
    asc: lerpAngle(f0.asc, f1.asc, t),
    mc: lerpAngle(f0.mc, f1.mc, t),
    system_used: t < 0.5 ? f0.system_used : f1.system_used,
  }
}

/** Frame at jd from a sorted keyframe list, or null if jd is outside the covered range. */
export function frameAt(frames: Keyframe[], jd: number): Keyframe | null {
  if (frames.length === 0) return null
  if (jd < frames[0].jd_ut || jd > frames[frames.length - 1].jd_ut) return null
  let lo = 0
  let hi = frames.length - 1
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1
    if (frames[mid].jd_ut <= jd) lo = mid
    else hi = mid
  }
  const f0 = frames[lo]
  const f1 = frames[hi]
  if (f1.jd_ut === f0.jd_ut) return f0
  return interpolateFrames(f0, f1, (jd - f0.jd_ut) / (f1.jd_ut - f0.jd_ut))
}
