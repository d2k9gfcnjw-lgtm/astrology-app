import type { Chart, City, Keyframe, LunarInstant, ResolvedTime, ReturnChart, ReturnSet, Settings, SolveResult, Subject, SubjectIn, YearAhead } from './types'

async function call<T>(method: string, url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: body === undefined ? {} : { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const j = await res.json()
      detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch {
      /* keep statusText */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  health: () => call<{ status: string; library: { db_path: string; key_path: string } }>('GET', '/api/health'),
  resolveTime: (datetime_local: string, lat: number, lon: number, timezone: string | null, utc_offset_override: string | null) =>
    call<ResolvedTime>('POST', '/api/time/resolve', { datetime_local, lat, lon, timezone, utc_offset_override }),
  chart: (subject: { datetime_local: string; lat: number; lon: number; timezone: string | null; utc_offset_override: string | null }, settings: Settings) =>
    call<Chart>('POST', '/api/chart', { subject, settings }),
  chartAt: (jd_ut: number, lat: number, lon: number, settings: Settings) =>
    call<Chart>('POST', '/api/chart/at', { jd_ut, lat, lon, settings }),
  keyframes: (jd_uts: number[], lat: number, lon: number, settings: Settings) =>
    call<{ frames: Keyframe[] }>('POST', '/api/chart/at/batch', { jd_uts, lat, lon, settings }).then((r) => r.frames),
  cities: (q: string) => call<City[]>('GET', `/api/cities?q=${encodeURIComponent(q)}`),
  subjects: (q?: string, tag?: string) => {
    const p = new URLSearchParams()
    if (q) p.set('q', q)
    if (tag) p.set('tag', tag)
    const qs = p.toString()
    return call<Subject[]>('GET', `/api/subjects${qs ? `?${qs}` : ''}`)
  },
  tags: () => call<string[]>('GET', '/api/subjects/tags'),
  subject: (id: string) => call<Subject>('GET', `/api/subjects/${id}`),
  createSubject: (s: SubjectIn) => call<Subject>('POST', '/api/subjects', s),
  updateSubject: (id: string, s: SubjectIn) => call<Subject>('PUT', `/api/subjects/${id}`, s),
  deleteSubject: (id: string) => call<void>('DELETE', `/api/subjects/${id}`),
  subjectChart: (id: string) => call<Chart>('GET', `/api/subjects/${id}/chart`),
  solve: (body: string, target_lon: number, jd_ut: number, settings: Settings) =>
    call<SolveResult>('POST', '/api/transits/solve', { body, target_lon, jd_ut, settings }),
  solarReturn: (id: string, year: number, place: { lat: number; lon: number; name: string } | null, precessed: boolean) => {
    const p = new URLSearchParams({ year: String(year), precessed: String(precessed) })
    if (place) { p.set('lat', String(place.lat)); p.set('lon', String(place.lon)); p.set('place_name', place.name) }
    return call<ReturnSet>('GET', `/api/subjects/${id}/solar-return?${p}`)
  },
  solarReturnUnsaved: (subject: { datetime_local: string; lat: number; lon: number; timezone: string | null; utc_offset_override: string | null },
    home: { lat: number; lon: number; name: string } | null, year: number, place: { lat: number; lon: number; name: string } | null, precessed: boolean, settings: Settings) =>
    call<ReturnSet>('POST', '/api/returns/solar', { subject, home, year, lat: place?.lat ?? null, lon: place?.lon ?? null, place_name: place?.name ?? '', precessed, settings }),
  lunarReturns: (id: string, year: number) => call<LunarInstant[]>('GET', `/api/subjects/${id}/lunar-returns?year=${year}`),
  lunarReturn: (id: string, jd_ut: number, place: { lat: number; lon: number; name: string } | null) => {
    const p = new URLSearchParams({ jd_ut: String(jd_ut) })
    if (place) { p.set('lat', String(place.lat)); p.set('lon', String(place.lon)); p.set('place_name', place.name) }
    return call<ReturnChart>('GET', `/api/subjects/${id}/lunar-return?${p}`)
  },
  yearAhead: (id: string, year: number) => call<YearAhead>('GET', `/api/subjects/${id}/year-ahead?year=${year}`),
  yearAheadUnsaved: (subject: { datetime_local: string; lat: number; lon: number; timezone: string | null; utc_offset_override: string | null }, year: number, settings: Settings) =>
    call<YearAhead>('POST', '/api/transits/year-ahead', { subject, year, settings }),
}
