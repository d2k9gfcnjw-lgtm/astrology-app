import { diff, norm } from './angles'

/**
 * Push labels apart so none are closer than minGap degrees around the ring, while keeping their
 * cyclic order and staying as close to the true degree as possible. Returns the display angle
 * for each input, in the same order as the input.
 */
export function spreadLabels(trueAngles: number[], minGap: number, iterations = 200): number[] {
  const n = trueAngles.length
  if (n < 2) return trueAngles.map(norm)
  if (n * minGap >= 360) minGap = 360 / n // cannot fit otherwise
  const order = trueAngles.map((a, i) => ({ a: norm(a), i })).sort((x, y) => x.a - y.a)
  const pos = order.map((o) => o.a)
  for (let it = 0; it < iterations; it++) {
    let moved = false
    for (let k = 0; k < n; k++) {
      const j = (k + 1) % n
      const gap = k === n - 1 ? pos[j] + 360 - pos[k] : pos[j] - pos[k]
      if (gap < minGap - 1e-9) {
        const push = (minGap - gap) / 2
        pos[k] -= push
        pos[j] += push
        moved = true
      }
    }
    if (!moved) break
  }
  // pull everything back toward the true degrees without re-introducing overlaps
  const mean = pos.reduce((s, p, k) => s + diff(p, order[k].a), 0) / n
  const out = new Array<number>(n)
  order.forEach((o, k) => (out[o.i] = norm(pos[k] + mean)))
  return out
}
