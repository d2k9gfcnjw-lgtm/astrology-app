// Mirrors of the backend JSON models (backend/app/engine/models.py and main.py).

export type Zodiac = 'tropical' | 'sidereal'
export type HouseSystem = 'placidus' | 'whole_sign'

export interface AspectSettings {
  orbs: Record<string, number>
  luminary_bonus: number
  minor_aspects: boolean
  minor_orb: number
  include_points: boolean
}

export interface TransitSettings {
  bodies: string[]
  natal_points: string[]
  aspects: string[]
  orbs: Record<string, number>
  minor_orbs: Record<string, number>
  include_ingresses: boolean
  include_sign_ingresses: boolean
  include_stations: boolean
}

export const DEFAULT_TRANSITS: TransitSettings = {
  bodies: ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'],
  natal_points: ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'asc', 'dsc', 'mc', 'ic'],
  aspects: ['conjunction', 'opposition', 'square', 'trine', 'semisquare', 'sesquiquadrate'],
  minor_orbs: { sun: 2.5, moon: 2.5, mercury: 2.5, venus: 2.5, mars: 2.5, jupiter: 2, saturn: 2, uranus: 1.5, neptune: 1.5, pluto: 1, chiron: 1.5, node: 1.5, lilith: 1.5 },
  orbs: { sun: 3, moon: 3, mercury: 3, venus: 3, mars: 3, jupiter: 3, saturn: 3, uranus: 2, neptune: 1.5, pluto: 1.5, chiron: 2, node: 2, lilith: 2 },
  include_ingresses: true,
  include_sign_ingresses: true,
  include_stations: true,
}

export interface Settings {
  zodiac: Zodiac
  ayanamsa: 'lahiri' | 'fagan_bradley' | 'raman' | 'krishnamurti'
  house_system: HouseSystem
  placidus_fallback_latitude: number
  node_type: 'true' | 'mean'
  lilith_type: 'mean' | 'true'
  fortune_formula: 'sect' | 'day'
  include_node: boolean
  include_chiron: boolean
  include_lilith: boolean
  include_fortune: boolean
  aspects: AspectSettings
  transits: TransitSettings
}

export const DEFAULT_SETTINGS: Settings = {
  zodiac: 'tropical',
  ayanamsa: 'lahiri',
  house_system: 'placidus',
  placidus_fallback_latitude: 66,
  node_type: 'true',
  lilith_type: 'mean',
  fortune_formula: 'sect',
  include_node: true,
  include_chiron: true,
  include_lilith: true,
  include_fortune: true,
  aspects: {
    orbs: { conjunction: 8, opposition: 8, trine: 8, square: 8, sextile: 6 },
    luminary_bonus: 1,
    minor_aspects: false,
    minor_orb: 2,
    include_points: false,
  },
  transits: DEFAULT_TRANSITS,
}

export interface BodyPosition {
  lon: number
  lat: number
  dist: number
  speed_lon: number
  speed_lat: number
  right_ascension: number
  declination: number
  retrograde: boolean
  sign: string
  sign_degrees: number
  formatted: string
  variant: string | null
}

export interface Houses {
  cusps: Record<string, number>
  cusp_declinations: Record<string, number>
  asc: number
  mc: number
  dsc: number
  ic: number
  vertex: number
  armc: number
  obliquity: number
  system_used: HouseSystem
  system_requested: HouseSystem
  warnings: string[]
  ayanamsa_degrees: number | null
}

export interface Moment {
  local_datetime: string
  timezone: string | null
  utc_offset: string
  utc_offset_seconds: number
  utc_datetime: string
  jd_ut: number
  jd_tt: number
  delta_t_sec: number
  flags: string[]
}

export interface Aspect {
  a: string
  b: string
  type: string
  angle: number
  separation: number
  orb: number
  max_orb: number
  applying: boolean
  exact: boolean
}

export interface Provenance {
  local_time: string
  utc_offset: string
  timezone: string | null
  lat: number
  lon: number
  house_system: HouseSystem
  zodiac: Zodiac
  ayanamsa: string | null
  node_type: string
  time_flags: string[]
  relocated_from: [number, number] | null
}

export interface Chart {
  aspects: Aspect[]
  moment: Moment
  planets: Record<string, BodyPosition>
  houses: Houses
  fortune: BodyPosition | null
  planet_houses: Record<string, number>
  is_day: boolean
  provenance: Provenance
  settings: Settings
}

export interface Keyframe {
  jd_ut: number
  planets: Record<string, number>
  speeds: Record<string, number>
  cusps: number[]
  asc: number
  mc: number
  system_used: HouseSystem
}

export interface City {
  geonameid: number
  name: string
  country: string
  admin1: string
  population: number
  lat: number
  lon: number
  timezone: string
  label: string
}

export type Kind = 'person' | 'event' | 'place' | 'question'
export type TimeConfidence = 'exact' | 'within_5_min' | 'within_30_min' | 'unknown'

export interface SubjectIn {
  name: string
  kind: Kind
  tags: string[]
  notes: string
  datetime_local: string
  time_confidence: TimeConfidence
  place_name: string
  lat: number
  lon: number
  timezone: string | null
  utc_offset_override: string | null
  home_place_name: string
  home_lat: number | null
  home_lon: number | null
  home_timezone: string | null
  settings: Partial<Settings>
}

export interface Subject extends SubjectIn {
  id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface ResolvedTime extends Moment {
  flag_text: Record<string, string>
}

/** What the wheel draws. Built from a full Chart at rest, or from an interpolated keyframe while spinning. */
export interface WheelData {
  planets: Record<string, { lon: number; retrograde: boolean }>
  cusps: number[]
  asc: number
  mc: number
  aspects: Aspect[]
  systemUsed: HouseSystem
}

export interface TransitHit {
  jd_ut: number
  utc_datetime: string
  local_datetime: string
  body: string
  aspect: string
  angle: number
  natal_point: string
  natal_lon: number
  transit_lon: number
  retrograde: boolean
  pass_index: number
  pass_count: number
  orb: number
  orb_enter_jd: number | null
  orb_exit_jd: number | null
  orb_enter_local: string | null
  orb_exit_local: string | null
}

export interface Ingress {
  jd_ut: number
  utc_datetime: string
  local_datetime: string
  body: string
  kind: 'house' | 'sign'
  entered: string
  retrograde: boolean
  lon: number
}

export interface StationEvent {
  jd_ut: number
  utc_datetime: string
  local_datetime: string
  body: string
  kind: 'retrograde' | 'direct'
  lon: number
  near: { natal_point: string; aspect: string; orb: number }[]
}

export interface YearAhead {
  year: number
  jd_start: number
  jd_end: number
  utc_start: string
  utc_end: string
  local_start: string
  local_end: string
  timezone: string | null
  settings: TransitSettings
  hits: TransitHit[]
  ingresses: Ingress[]
  stations: StationEvent[]
  counts: Record<string, number>
}

export interface SolveHit {
  jd_ut: number
  utc_datetime: string
  retrograde: boolean
  pass_index: number
  pass_count: number
}

export interface SolveResult {
  previous: SolveHit[]
  next: SolveHit[]
  nearest: SolveHit | null
}

export interface ReturnChart {
  kind: 'solar' | 'lunar'
  year: number
  jd_ut: number
  utc_datetime: string
  local_datetime: string
  timezone: string | null
  place: { lat: number; lon: number; name: string }
  precessed: boolean
  chart: Chart
  natal_house_of: Record<string, number>
  houses_of: Record<string, number[]>
  angular: { body: string; angle: string; orb: number }[]
  stelliums: { house: number; bodies: string[] }[]
  flags: { id: string; severity: string; text: string }[]
}

export interface ReturnSet {
  chosen: ReturnChart
  previous: ReturnChart
  base: ReturnChart
}

export interface LunarInstant {
  jd_ut: number
  utc_datetime: string
  local_datetime: string
  timezone: string | null
}

export interface Reason { rule: string; points: number; text: string; body: string | null; status: string }

export interface PlaceScore {
  lat: number
  lon: number
  jd_ut: number
  utc_datetime: string
  local_datetime: string
  timezone: string | null
  disqualified: boolean
  tier: 'best' | 'safe' | 'marginal' | 'disqualified'
  total: number
  stars: number
  dominant: string | null
  facts: { asc_natal_house: number; sun_houses: number[]; mars_houses: number[]; houses_of: Record<string, number[]>; stelliums: { house: number; bodies: string[] }[]; angular: { body: string; angle: string; orb: number }[]; asc_cusp_distance: number }
  reasons: Reason[]
  gains: Reason[]
  costs: Reason[]
  cautions: string[]
  robustness: { asc_cusp_distance?: number; birth_time_tests?: Record<string, string>; flips?: boolean; tier_hit?: string | null }
  versus_base: { fixes?: string[]; worsens?: string[]; base_total?: number; base_tier?: string }
  marginal_vs_base: boolean
}

export interface CityResult extends PlaceScore {
  name: string
  country: string
  admin1: string
  population: number
  airport_code: string
  airport_km: number
}

export interface FinderResult {
  year: number
  jd_sr: number
  goal: string | null
  options: Record<string, unknown>
  context: { themes: string[]; heavy_hits: { body: string; aspect: string; natal_point: string; local_datetime: string }[]; houses_transited: Record<string, number[]>; houses_entered: Record<string, number[]> }
  grid: { step: number; cells: { lat: number; lon: number; score: number | null; tier: string }[] }
  cities: CityResult[]
  base: PlaceScore
  previous: PlaceScore
  counts: Record<string, number>
}

export interface FinderRequest {
  subject_id: string
  year: number
  goal: string | null
  population_floor: number
  airport_max_km: number
  exclude_countries: string[]
  precessed: boolean
  safety_cusp_filter: boolean
  grid_step: number
}

export interface AcgSettings {
  bodies: string[]
  angles: string[]
  method: 'mundo' | 'zodiacal'
  orb_km: number
  paran_orb_lat: number
  include_parans: boolean
}

export const DEFAULT_ACG: AcgSettings = {
  bodies: ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'],
  angles: ['asc', 'dsc', 'mc', 'ic'],
  method: 'mundo',
  orb_km: 300,
  paran_orb_lat: 1,
  include_parans: true,
}

export interface AcgLine { body: string; angle: string; points: [number, number][][] }
export interface Paran { body_a: string; angle_a: string; body_b: string; angle_b: string; lat: number }
export interface AcgLines { lines: AcgLine[]; parans: Paran[] }
export interface AcgAt { chart: Chart; lines: { body: string; angle: string; km: number; deg: number }[]; parans: Paran[]; orb_km: number }
