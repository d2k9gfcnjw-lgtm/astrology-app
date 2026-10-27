export const SIGNS = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
export const SIGN_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
export const ELEMENT_OF_SIGN = ['fire', 'earth', 'air', 'water', 'fire', 'earth', 'air', 'water', 'fire', 'earth', 'air', 'water'] as const
export const ELEMENT_COLORS: Record<string, string> = { fire: '#e4572e', earth: '#3a9d5d', air: '#e3b505', water: '#2e86de' }

export const BODY_ORDER = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'node', 'chiron', 'lilith', 'fortune']
export const BODY_NAMES: Record<string, string> = {
  sun: 'Sun', moon: 'Moon', mercury: 'Mercury', venus: 'Venus', mars: 'Mars', jupiter: 'Jupiter', saturn: 'Saturn',
  uranus: 'Uranus', neptune: 'Neptune', pluto: 'Pluto', node: 'Node', chiron: 'Chiron', lilith: 'Lilith', fortune: 'Fortune',
}

export const ASPECT_STYLE: Record<string, { color: string; dash?: string; width: number }> = {
  conjunction: { color: '#2a9d8f', width: 1.6 },
  opposition: { color: '#c1121f', width: 1.6 },
  square: { color: '#e5383b', width: 1.4 },
  trine: { color: '#1d4ed8', width: 1.4 },
  sextile: { color: '#4895ef', width: 1.1, dash: '4 3' },
  quincunx: { color: '#7b7b7b', width: 1, dash: '2 3' },
  semisextile: { color: '#9a9a9a', width: 1, dash: '2 3' },
  semisquare: { color: '#9a9a9a', width: 1, dash: '2 3' },
  sesquiquadrate: { color: '#9a9a9a', width: 1, dash: '2 3' },
}

export const norm = (d: number) => ((d % 360) + 360) % 360

/** Signed shortest difference b - a in degrees, in (-180, 180]. */
export const diff = (a: number, b: number) => ((b - a + 540) % 360) - 180

/** Degrees and minutes within the sign, rounded to the minute: 14°32' */
export function formatDM(lon: number): string {
  const within = norm(lon) % 30
  let total = Math.round(within * 60)
  if (total >= 30 * 60) total = 30 * 60 - 1
  const d = Math.floor(total / 60)
  const m = total % 60
  return `${d}°${m.toString().padStart(2, '0')}'`
}

export function signIndex(lon: number): number {
  return Math.floor(norm(lon) / 30)
}

export function signOf(lon: number): string {
  return SIGNS[signIndex(lon)]
}
