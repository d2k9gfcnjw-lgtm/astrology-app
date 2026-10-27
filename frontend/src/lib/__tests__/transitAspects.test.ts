import { describe, expect, it } from 'vitest'
import { groupHitsByBody, transitAspects } from '../transitAspects'
import { DEFAULT_TRANSITS } from '../types'

describe('transit aspects', () => {
  it('uses the transiting body\'s own orb', () => {
    const natal = { sun: 100, mc: 10 }
    const both = transitAspects({ jupiter: 102.5, pluto: 102.5 }, natal, DEFAULT_TRANSITS)
    expect(both.length).toBe(2)
    expect(both.every((a) => a.a === 'jupiter')).toBe(true)
    expect(transitAspects({ pluto: 101.4 }, natal, DEFAULT_TRANSITS)[0]).toMatchObject({ a: 'pluto', b: 'sun', type: 'conjunction' })
    expect(transitAspects({ saturn: 280.5 }, natal, DEFAULT_TRANSITS)[0]).toMatchObject({ b: 'sun', type: 'opposition' })
  })

  it('skips bodies and points that are switched off', () => {
    expect(transitAspects({ moon: 100 }, { sun: 100 }, DEFAULT_TRANSITS)).toEqual([])
    expect(transitAspects({ mars: 100 }, { node: 100 }, DEFAULT_TRANSITS)).toEqual([])
  })

  it('groups in the given order with unknown bodies last', () => {
    const g = groupHitsByBody([{ body: 'mars' }, { body: 'pluto' }, { body: 'mars' }, { body: 'moon' }], ['pluto', 'mars'])
    expect(g.map((x) => [x.body, x.items.length])).toEqual([['pluto', 1], ['mars', 2], ['moon', 1]])
  })
})
