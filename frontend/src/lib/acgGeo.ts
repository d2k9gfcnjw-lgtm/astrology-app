import type { AcgLine, Paran } from './types'
import { BODY_COLORS } from './angles'
import type { Feature, FeatureCollection, LineString } from 'geojson'

export { BODY_COLORS } from './angles'
export const ANGLE_DASH: Record<string, number[] | undefined> = { asc: undefined, dsc: [2, 2], mc: undefined, ic: [2, 2] }

/** Lines as GeoJSON features, one per segment, with body and angle properties. */
export function linesToGeoJson(lines: AcgLine[]): FeatureCollection<LineString> {
  const features: Feature<LineString>[] = []
  for (const l of lines) {
    for (const seg of l.points) {
      if (seg.length < 2) continue
      features.push({ type: 'Feature', properties: { body: l.body, angle: l.angle, color: BODY_COLORS[l.body] ?? '#333', dashed: l.angle === 'dsc' || l.angle === 'ic' ? 1 : 0 }, geometry: { type: 'LineString', coordinates: seg } })
    }
  }
  return { type: 'FeatureCollection', features }
}

export function paransToGeoJson(parans: Paran[]): FeatureCollection<LineString> {
  return {
    type: 'FeatureCollection',
    features: parans.map((p) => ({ type: 'Feature', properties: { label: `${p.body_a} ${p.angle_a.toUpperCase()} / ${p.body_b} ${p.angle_b.toUpperCase()}`, lat: p.lat },
      geometry: { type: 'LineString', coordinates: [[-180, p.lat], [-90, p.lat], [0, p.lat], [90, p.lat], [180, p.lat]] } })),
  }
}

/** Pixel width of an orb band of `km` at a given zoom and latitude (Web Mercator metres per pixel at zoom 0 = 156543). */
export function orbPixels(km: number, zoom: number, lat: number): number {
  const metersPerPixel = (156543.03 * Math.cos((lat * Math.PI) / 180)) / Math.pow(2, zoom)
  return (km * 1000 * 2) / metersPerPixel
}
