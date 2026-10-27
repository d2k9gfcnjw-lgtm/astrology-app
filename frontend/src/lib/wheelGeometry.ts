import { norm } from './angles'

/** Wheel convention: the Ascendant points left; longitude grows counterclockwise. */
export function pointOnWheel(lon: number, r: number, asc: number, c: number): { x: number; y: number } {
  const th = ((180 + (lon - asc)) * Math.PI) / 180
  return { x: c + r * Math.cos(th), y: c - r * Math.sin(th) }
}

/** The inverse: which longitude a point (x, y) sits on, given the centre and the Ascendant. */
export function lonFromPoint(x: number, y: number, asc: number, c: number): number {
  const th = (Math.atan2(c - y, x - c) * 180) / Math.PI // counterclockwise from +x
  return norm(th - 180 + asc)
}
