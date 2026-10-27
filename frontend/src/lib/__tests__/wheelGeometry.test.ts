import { describe, expect, it } from 'vitest'
import { lonFromPoint, pointOnWheel } from '../wheelGeometry'

describe('wheel geometry', () => {
  it('puts the Ascendant on the left and the IC at the bottom', () => {
    const asc = 100
    expect(pointOnWheel(asc, 10, asc, 0)).toMatchObject({ x: -10 })
    const ic = pointOnWheel(asc + 90, 10, asc, 0)
    expect(ic.x).toBeCloseTo(0)
    expect(ic.y).toBeCloseTo(10)
  })

  it('inverts pointOnWheel for every longitude', () => {
    const asc = 212.5
    for (let lon = 0; lon < 360; lon += 7.3) {
      const p = pointOnWheel(lon, 250, asc, 300)
      expect(lonFromPoint(p.x, p.y, asc, 300)).toBeCloseTo(lon % 360, 6)
    }
  })
})
