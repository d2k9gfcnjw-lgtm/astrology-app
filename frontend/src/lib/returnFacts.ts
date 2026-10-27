import { BODY_NAMES } from './angles'
import type { ReturnChart } from './types'

/** "7" or "7 and 8" for a planet that works in two houses (within the cusp orb). */
export function describeHouses(houses: number[] | undefined): string {
  if (!houses || houses.length === 0) return '–'
  return houses.length === 1 ? String(houses[0]) : `${houses[0]} and ${houses[1]}`
}

export interface Fact { label: string; value: string; warn?: boolean }

/** The owner's at-a-glance facts: Ascendant's natal house, Sun and Mars houses, stelliums, angular planets. */
export function returnFacts(r: ReturnChart): Fact[] {
  const facts: Fact[] = [
    { label: 'Asc in natal house', value: String(r.natal_house_of.asc), warn: [1, 6, 12].includes(r.natal_house_of.asc) },
    { label: 'Sun in house', value: describeHouses(r.houses_of.sun) },
    { label: 'Mars in house', value: describeHouses(r.houses_of.mars) },
  ]
  if (r.stelliums.length) facts.push({ label: 'Stellium', value: r.stelliums.map((s) => `house ${s.house}: ${s.bodies.map((b) => BODY_NAMES[b] ?? b).join(', ')}`).join('; '), warn: r.stelliums.some((s) => [1, 12, 8].includes(s.house)) })
  else facts.push({ label: 'Stellium', value: 'none' })
  if (r.angular.length) facts.push({ label: 'On an angle', value: r.angular.map((a) => `${BODY_NAMES[a.body] ?? a.body} ${a.angle.toUpperCase()} ${a.orb.toFixed(1)}°`).join(', ') })
  return facts
}
