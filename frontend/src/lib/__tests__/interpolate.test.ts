import { describe, expect, it } from 'vitest'
import { frameAt, interpolateFrames, lerpAngle } from '../interpolate'
import type { Keyframe } from '../types'

const frame = (jd: number, sun: number, asc: number): Keyframe => ({
  jd_ut: jd, planets: { sun }, speeds: { sun: 1 }, cusps: Array(12).fill(asc), asc, mc: (asc + 270) % 360, system_used: 'placidus',
})

describe('interpolation', () => {
  it('takes the short way round across 360/0', () => {
    expect(lerpAngle(350, 10, 0.5)).toBeCloseTo(0)
    expect(lerpAngle(10, 350, 0.25)).toBeCloseTo(5)
  })

  it('interpolates planets, cusps and angles', () => {
    const f = interpolateFrames(frame(0, 100, 355), frame(1, 102, 5), 0.5)
    expect(f.planets.sun).toBeCloseTo(101)
    expect(f.asc).toBeCloseTo(0)
    expect(f.cusps[3]).toBeCloseTo(0)
    expect(f.jd_ut).toBe(0.5)
  })

  it('finds the right pair in a list and reports gaps', () => {
    const frames = [frame(0, 0, 0), frame(1, 10, 10), frame(2, 20, 20)]
    expect(frameAt(frames, 1.5)!.planets.sun).toBeCloseTo(15)
    expect(frameAt(frames, 2)!.planets.sun).toBeCloseTo(20)
    expect(frameAt(frames, 2.5)).toBeNull()
    expect(frameAt(frames, -1)).toBeNull()
  })
})
