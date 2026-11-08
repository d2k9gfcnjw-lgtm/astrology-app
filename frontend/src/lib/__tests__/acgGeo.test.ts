import { describe, expect, it } from 'vitest'
import { linesToGeoJson, orbPixels, paransToGeoJson } from '../acgGeo'

describe('astrocartography map helpers', () => {
  it('turns line segments into features with colours and dashes', () => {
    const fc = linesToGeoJson([{ body: 'mars', angle: 'dsc', points: [[[10, -80], [11, 0], [12, 80]], [[170, 0]]] }])
    expect(fc.features).toHaveLength(1)
    expect(fc.features[0].properties).toMatchObject({ body: 'mars', angle: 'dsc', dashed: 1 })
    expect(fc.features[0].geometry.coordinates).toHaveLength(3)
  })

  it('draws parans as horizontal lines with labels', () => {
    const fc = paransToGeoJson([{ body_a: 'sun', angle_a: 'mc', body_b: 'moon', angle_b: 'asc', lat: 41.5 }])
    expect(fc.features[0].properties?.label).toBe('sun MC / moon ASC')
    expect(fc.features[0].geometry.coordinates.every((c) => c[1] === 41.5)).toBe(true)
  })

  it('scales the orb band with zoom', () => {
    expect(orbPixels(300, 1, 0)).toBeCloseTo(7.67, 1)
    expect(orbPixels(300, 3, 0)).toBeCloseTo(orbPixels(300, 1, 0) * 4, 5)
    expect(orbPixels(300, 1, 60)).toBeGreaterThan(orbPixels(300, 1, 0))
  })
})
