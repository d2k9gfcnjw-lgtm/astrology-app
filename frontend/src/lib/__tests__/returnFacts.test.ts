import { describe, expect, it } from 'vitest'
import { describeHouses, returnFacts } from '../returnFacts'
import type { ReturnChart } from '../types'

describe('return facts', () => {
  it('describes single and dual houses', () => {
    expect(describeHouses([7])).toBe('7')
    expect(describeHouses([7, 8])).toBe('7 and 8')
    expect(describeHouses(undefined)).toBe('–')
  })

  it('lists the owner\'s facts in order and flags the hard cases', () => {
    const r = {
      natal_house_of: { asc: 12 }, houses_of: { sun: [10], mars: [2, 3] },
      stelliums: [{ house: 8, bodies: ['jupiter', 'moon', 'pluto'] }], angular: [{ body: 'sun', angle: 'mc', orb: 3.2 }], flags: [],
    } as unknown as ReturnChart
    const f = returnFacts(r)
    expect(f.map((x) => x.label)).toEqual(['Asc in natal house', 'Sun in house', 'Mars in house', 'Stellium', 'On an angle'])
    expect(f[0]).toMatchObject({ value: '12', warn: true })
    expect(f[2].value).toBe('2 and 3')
    expect(f[3].warn).toBe(true)
    expect(f[4].value).toBe('Sun MC 3.2°')
  })
})
