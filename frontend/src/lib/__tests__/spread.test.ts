import { describe, expect, it } from 'vitest'
import { spreadLabels } from '../spread'
import { diff } from '../angles'

describe('spreadLabels', () => {
  it('leaves well separated labels alone', () => {
    expect(spreadLabels([10, 50, 90], 7)).toEqual([10, 50, 90])
  })

  it('spreads four planets within 6 degrees to distinct slots', () => {
    const truth = [100, 101.5, 103, 106]
    const out = spreadLabels(truth, 7)
    const sorted = [...out].sort((a, b) => a - b)
    for (let i = 1; i < sorted.length; i++) expect(sorted[i] - sorted[i - 1]).toBeGreaterThanOrEqual(7 - 1e-6)
    // order is kept and the group stays centred on its true centre
    expect(out[0] < out[1] && out[1] < out[2] && out[2] < out[3]).toBe(true)
    const centreTrue = truth.reduce((s, v) => s + v, 0) / 4
    const centreOut = out.reduce((s, v) => s + v, 0) / 4
    expect(Math.abs(centreOut - centreTrue)).toBeLessThan(0.5)
  })

  it('handles the 360/0 boundary', () => {
    const out = spreadLabels([358, 1, 3], 8)
    const gaps = [diff(out[0], out[1]), diff(out[1], out[2])]
    for (const g of gaps) expect(g).toBeGreaterThanOrEqual(8 - 1e-6)
    expect(Math.abs(diff(out[1], 1))).toBeLessThan(8)
  })

  it('never moves a label by more than it must', () => {
    const out = spreadLabels([10, 12], 6)
    expect(Math.abs(diff(out[0], 8))).toBeLessThan(1e-6)
    expect(Math.abs(diff(out[1], 14))).toBeLessThan(1e-6)
  })
})
