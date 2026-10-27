/** Julian Day helpers and wall-clock stepping. JD here is always UT. */

export const JD_UNIX_EPOCH = 2440587.5
export const DAY_MS = 86400000

export type StepUnit = 'second' | 'minute' | 'hour' | 'day' | 'week' | 'month' | 'year'

export const UNIT_SECONDS: Record<Exclude<StepUnit, 'month' | 'year'>, number> = {
  second: 1,
  minute: 60,
  hour: 3600,
  day: 86400,
  week: 604800,
}

export function jdFromDate(d: Date): number {
  return d.getTime() / DAY_MS + JD_UNIX_EPOCH
}

export function dateFromJd(jd: number): Date {
  return new Date((jd - JD_UNIX_EPOCH) * DAY_MS)
}

export function jdNow(): number {
  return jdFromDate(new Date())
}

/** Parts of the wall clock in a zone for an instant, via Intl (the browser's zone database). */
export interface WallClock {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  second: number
  offset: string
  zoneAbbrev: string
}

export function wallClock(d: Date, timeZone: string | null): WallClock {
  const tz = timeZone ?? 'UTC'
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', timeZoneName: 'longOffset',
  }).formatToParts(d)
  const get = (t: string) => parts.find((p) => p.type === t)?.value ?? ''
  const offRaw = get('timeZoneName') // GMT+02:00 or GMT
  const offset = offRaw === 'GMT' ? '+00:00' : offRaw.replace('GMT', '')
  const abbrev = new Intl.DateTimeFormat('en-US', { timeZone: tz, timeZoneName: 'short' }).formatToParts(d).find((p) => p.type === 'timeZoneName')?.value ?? ''
  return {
    year: Number(get('year')), month: Number(get('month')), day: Number(get('day')),
    hour: Number(get('hour')), minute: Number(get('minute')), second: Number(get('second')),
    offset, zoneAbbrev: abbrev,
  }
}

export function formatWall(w: WallClock, withSeconds = true): string {
  const p = (n: number) => n.toString().padStart(2, '0')
  const date = `${w.year}-${p(w.month)}-${p(w.day)}`
  const time = `${p(w.hour)}:${p(w.minute)}${withSeconds ? `:${p(w.second)}` : ''}`
  return `${date} ${time}`
}

/** ISO local string "YYYY-MM-DDTHH:MM:SS" without zone, as the backend expects. */
export function isoLocal(w: WallClock): string {
  const p = (n: number) => n.toString().padStart(2, '0')
  return `${w.year}-${p(w.month)}-${p(w.day)}T${p(w.hour)}:${p(w.minute)}:${p(w.second)}`
}

export const daysInMonth = (year: number, month: number) => new Date(Date.UTC(year, month, 0)).getUTCDate()

/** Add months (or years as 12 months) to a wall clock, clamping the day so 31 Jan + 1 month = 28/29 Feb. */
export function addMonths(w: WallClock, months: number): WallClock {
  const total = w.year * 12 + (w.month - 1) + months
  const year = Math.floor(total / 12)
  const month = (total % 12) + 1
  const day = Math.min(w.day, daysInMonth(year, month))
  return { ...w, year, month, day }
}

/**
 * Step an instant. Seconds through weeks are exact multiples of UT seconds; months and years move the
 * wall clock in the subject's zone and return the new local time for the backend to resolve.
 */
export function stepJd(jd: number, amount: number, unit: StepUnit): { jd: number } | { localIso: string } {
  if (unit === 'month' || unit === 'year') {
    throw new Error('use stepWall for month and year')
  }
  return { jd: jd + (amount * UNIT_SECONDS[unit]) / 86400 }
}

export function stepWall(w: WallClock, amount: number, unit: 'month' | 'year'): WallClock {
  return addMonths(w, unit === 'year' ? amount * 12 : amount)
}

/** Playback speeds for spin mode, in simulated seconds per real second. */
export const SPIN_SPEEDS: { label: string; perSecond: number }[] = [
  { label: '1 s/s', perSecond: 1 },
  { label: '1 min/s', perSecond: 60 },
  { label: '10 min/s', perSecond: 600 },
  { label: '1 h/s', perSecond: 3600 },
  { label: '6 h/s', perSecond: 21600 },
  { label: '1 day/s', perSecond: 86400 },
  { label: '1 week/s', perSecond: 604800 },
  { label: '1 month/s', perSecond: 2629800 },
  { label: '1 year/s', perSecond: 31557600 },
]
