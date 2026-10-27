// Astrological glyphs as SVG paths in a 20x20 box (stroke based), so they look the same on every device.
export const SIGN_PATHS: string[] = [
  'M4 15C4 6 10 5 10 12 10 5 16 6 16 15M10 12v6', // Aries
  'M4 3a6 6 0 0 0 12 0M10 17.5a5 5 0 1 0 0-10 5 5 0 0 0 0 10z', // Taurus
  'M4 4c4 1.5 8 1.5 12 0M4 16c4-1.5 8-1.5 12 0M7.5 5v10M12.5 5v10', // Gemini
  'M3 8c3-4 11-4 14 0M17 12c-3 4-11 4-14 0M8 8.5a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM16 11.5a2 2 0 1 1-4 0 2 2 0 0 1 4 0z', // Cancer
  'M5 15a2.5 2.5 0 1 0 2.5-2.5c0-3-3-5-1-8a3.5 3.5 0 0 1 6 2c0 3-3 5-3 8 0 1.5 1 2.5 3 2.5', // Leo
  'M3 5v10M3 6c1.5-2 4-2 4 1v8M7 6c1.5-2 4-2 4 1v8M11 6c1.5-2 4-2 4 1v6c0 3-2 5-5 6M15 13c2 0 3 1 3 3', // Virgo
  'M3 13h4a3.5 3.5 0 0 1 6 0h4M3 17h14', // Libra
  'M3 5v10M3 6c1.5-2 4-2 4 1v8M7 6c1.5-2 4-2 4 1v8M11 6c1.5-2 4-2 4 1v7c0 2 1 3 3 3M16.5 15.5 18 17l-1.5 1.5', // Scorpio
  'M4 16 16 4M10 4h6v6M6 10l4 4', // Sagittarius
  'M3 6c2-2 4-1 4 1v8l4-8c1-2 4-2 4 1 0 3-3 4-4 3-1-1 0-3 2-3s3 2 2 4-3 3-5 3', // Capricorn
  'M3 8l3-3 3 3 3-3 3 3 3-3M3 15l3-3 3 3 3-3 3 3 3-3', // Aquarius
  'M5 3c4 3 4 11 0 14M15 3c-4 3-4 11 0 14M4 10h12', // Pisces
]

export const BODY_PATHS: Record<string, string> = {
  sun: 'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0zM11.2 10a1.2 1.2 0 1 1-2.4 0 1.2 1.2 0 0 1 2.4 0z',
  moon: 'M12 3a7 7 0 1 0 0 14 5.5 5.5 0 1 1 0-14z',
  mercury: 'M13.5 9a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0zM6.5 3a3.5 3.5 0 0 0 7 0M10 12.5v5M7.5 15.5h5',
  venus: 'M14 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM10 11v7M7 15h6',
  mars: 'M12.5 11.5a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM11.3 8.7 16.5 3.5M12 3.5h4.5V8',
  jupiter: 'M4 6c2-3 6-3 6 0 0 2-2 4-6 7h10M13 3v16',
  saturn: 'M6 3h5M8.5 3v14M8.5 9c2-2 6-2 6 1 0 3-3 5-3 8 0 1 1 1.5 2 1',
  uranus: 'M10 4v8M5 3v9M15 3v9M5 7h10M12.5 14.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z',
  neptune: 'M10 3v15M6 16h8M5 4v4a5 5 0 0 0 10 0V4',
  pluto: 'M13 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM5 7a5 5 0 0 0 10 0M10 12v6M7 15h6',
  node: 'M6 17a3 3 0 1 1 1.5-5.5A6 6 0 0 1 10 4a6 6 0 0 1 2.5 7.5A3 3 0 1 1 14 17',
  chiron: 'M13 15a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM10 12V3M7 5l3 3 3-3',
  lilith: 'M11 3a5 5 0 1 0 0 10 4 4 0 1 1 0-10zM10 13v5M7.5 15.5h5',
  fortune: 'M16 10a6 6 0 1 1-12 0 6 6 0 0 1 12 0zM5.8 5.8l8.4 8.4M14.2 5.8l-8.4 8.4',
}

interface GlyphProps {
  d: string
  x: number
  y: number
  size: number
  color?: string
  strokeWidth?: number
  title?: string
}

/** Draw a 20x20 glyph centred at (x, y) scaled to `size` px. */
export function Glyph({ d, x, y, size, color = 'currentColor', strokeWidth = 1.7, title }: GlyphProps) {
  const s = size / 20
  return (
    <g transform={`translate(${x - size / 2} ${y - size / 2}) scale(${s})`} fill="none" stroke={color} strokeWidth={strokeWidth / s} strokeLinecap="round" strokeLinejoin="round">
      {title && <title>{title}</title>}
      <path d={d} />
    </g>
  )
}
