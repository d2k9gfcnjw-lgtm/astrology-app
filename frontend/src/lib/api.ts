import type { Chart, City, Keyframe, ResolvedTime, Settings, Subject, SubjectIn } from './types'

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
}
