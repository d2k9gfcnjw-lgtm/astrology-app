import { describe, expect, it } from 'vitest'
import { addMonths, dateFromJd, jdFromDate, stepJd, wallClock, isoLocal } from '../time'

describe('julian day', () => {
  it('J2000', () => {
    expect(jdFromDate(new Date(Date.UTC(2000, 0, 1, 12)))).toBeCloseTo(2451545.0, 9)
    expect(dateFromJd(2451545.0).toISOString()).toBe('2000-01-01T12:00:00.000Z')
  })
})

describe('stepping', () => {
  it('steps exact units in UT', () => {
    const r = stepJd(2451545.0, 90, 'minute') as { jd: number }
    expect(r.jd).toBeCloseTo(2451545.0 + 90 / 1440, 9)
    expect((stepJd(2451545.0, -2, 'week') as { jd: number }).jd).toBeCloseTo(2451531.0, 9)
  })

  it('clamps month ends and leap years', () => {
    const w = { year: 2024, month: 1, day: 31, hour: 12, minute: 0, second: 0, offset: '+00:00', zoneAbbrev: 'UTC' }
    expect(addMonths(w, 1)).toMatchObject({ year: 2024, month: 2, day: 29 })
    expect(addMonths(w, 13)).toMatchObject({ year: 2025, month: 2, day: 28 })
    expect(addMonths(w, -2)).toMatchObject({ year: 2023, month: 11, day: 30 })
    expect(addMonths({ ...w, month: 2, day: 29 }, 12)).toMatchObject({ year: 2025, month: 2, day: 28 })
  })

  it('reads the wall clock in a zone, including the DST offset', () => {
    const d = new Date('2024-11-03T13:50:00Z')
    const w = wallClock(d, 'America/Chicago')
    expect(isoLocal(w)).toBe('2024-11-03T07:50:00')
    expect(w.offset).toBe('-06:00')
    const summer = wallClock(new Date('2024-07-04T13:50:00Z'), 'America/Chicago')
    expect(summer.offset).toBe('-05:00')
    expect(wallClock(d, null).offset).toBe('+00:00')
  })
})
