import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'

// Vite serves the worker as a module; MapLibre must be told where it is.
maplibregl.setWorkerUrl(workerUrl)
import type { FeatureCollection } from 'geojson'
import type { CityResult, FinderResult } from '../lib/types'

const TIER_COLOR: Record<string, string> = { best: '#1b9e77', safe: '#7fc97f', marginal: '#fdb863', disqualified: '#9e9e9e' }

/** Heat image from the grid cells: one pixel per cell, equirectangular, so MapLibre can drape it as an image source. */
function heatImage(res: FinderResult): { url: string; coords: [[number, number], [number, number], [number, number], [number, number]] } {
  const step = res.grid.step
  const latMin = Number(res.options.lat_min ?? -60)
  const latMax = Number(res.options.lat_max ?? 66)
  const w = Math.round(360 / step)
  const h = Math.round((latMax - latMin) / step) + 1
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')!
  const img = ctx.createImageData(w, h)
  const scores = res.grid.cells.filter((c) => c.score !== null).map((c) => c.score as number)
  const lo = Math.min(...scores, -40)
  const hi = Math.max(...scores, 40)
  for (const c of res.grid.cells) {
    if (Math.abs((c.lat - latMin) / step - Math.round((c.lat - latMin) / step)) > 1e-6) continue // refined cells are drawn as markers, not pixels
    const x = Math.round((c.lon + 180) / step)
    const y = h - 1 - Math.round((c.lat - latMin) / step)
    if (x < 0 || x >= w || y < 0 || y >= h) continue
    const i = (y * w + x) * 4
    if (c.score === null) { img.data[i] = 120; img.data[i + 1] = 120; img.data[i + 2] = 120; img.data[i + 3] = 150; continue }
    const t = (c.score - lo) / (hi - lo)
    // amber (low) -> green (high)
    img.data[i] = Math.round(253 * (1 - t) + 27 * t)
    img.data[i + 1] = Math.round(184 * (1 - t) + 158 * t)
    img.data[i + 2] = Math.round(99 * (1 - t) + 119 * t)
    img.data[i + 3] = 170
  }
  ctx.putImageData(img, 0, 0)
  const top = latMax + step / 2
  const bottom = latMin - step / 2
  return { url: canvas.toDataURL(), coords: [[-180 - step / 2, top], [180 - step / 2, top], [180 - step / 2, bottom], [-180 - step / 2, bottom]] }
}

interface Props {
  result: FinderResult | null
  selected: CityResult | null
  onSelectCity: (c: CityResult) => void
  onClickPlace: (lat: number, lon: number) => void
  landGeoJson: FeatureCollection | null
}

export function FinderMap({ result, selected, onSelectCity, onClickPlace, landGeoJson }: Props) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [ready, setReady] = useState(false)
  const markers = useRef<maplibregl.Marker[]>([])

  useEffect(() => {
    if (!el.current || map.current) return
    const m = new maplibregl.Map({
      container: el.current,
      style: {
        version: 8,
        sources: {
          osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' },
        },
        layers: [
          { id: 'bg', type: 'background', paint: { 'background-color': '#dfe9f3' } },
          { id: 'osm', type: 'raster', source: 'osm', paint: { 'raster-opacity': 0.55 } },
        ],
      },
      center: [0, 20], zoom: 1.2, attributionControl: {},
    })
    m.addControl(new maplibregl.NavigationControl(), 'top-right')
    // 'load' can be missed or never fire while raster tiles are pending: also watch styledata and poll briefly.
    m.on('load', () => setReady(true))
    m.on('styledata', () => { if (m.isStyleLoaded()) setReady(true) })
    const poll = window.setInterval(() => { if (m.isStyleLoaded() || m.loaded()) { setReady(true); window.clearInterval(poll) } }, 250)
    window.setTimeout(() => window.clearInterval(poll), 15000)
    // The container can be sized after the map is created (hidden tab, phone layout): keep the canvas in step.
    const ro = new ResizeObserver(() => m.resize())
    ro.observe(el.current)
    window.setTimeout(() => m.resize(), 300)
    m.on('click', (e: maplibregl.MapMouseEvent) => onClickPlace(e.lngLat.lat, e.lngLat.lng))
    map.current = m
    return () => { window.clearInterval(poll); ro.disconnect(); m.remove(); map.current = null }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Natural Earth land: works offline when tiles do not load.
  useEffect(() => {
    const m = map.current
    if (!m || !landGeoJson) return
    const add = () => {
      if (m.getSource('land')) return
      m.addSource('land', { type: 'geojson', data: landGeoJson })
      m.addLayer({ id: 'land-fill', type: 'fill', source: 'land', paint: { 'fill-color': '#f1efe8', 'fill-opacity': 0.9 } }, 'osm')
      m.addLayer({ id: 'land-line', type: 'line', source: 'land', paint: { 'line-color': '#777', 'line-width': 0.6 } })
    }
    if (ready) add()
  }, [landGeoJson, ready])

  useEffect(() => {
    const m = map.current
    if (!m) return
    const apply = () => {
      if (m.getLayer('heat')) m.removeLayer('heat')
      if (m.getSource('heat')) m.removeSource('heat')
      markers.current.forEach((mk) => mk.remove())
      markers.current = []
      if (!result) return
      const { url, coords } = heatImage(result)
      m.addSource('heat', { type: 'image', url, coordinates: coords })
      m.addLayer({ id: 'heat', type: 'raster', source: 'heat', paint: { 'raster-opacity': 0.75, 'raster-resampling': 'nearest' } })
      // Spread the markers: the best place of each neighbourhood, so one lucky region does not hide the others.
      const placed: CityResult[] = []
      const far = (a: CityResult, b: CityResult) => {
        const dLat = a.lat - b.lat
        const dLon = (a.lon - b.lon) * Math.cos((a.lat * Math.PI) / 180)
        return Math.sqrt(dLat * dLat + dLon * dLon) > 2.5
      }
      for (const c of result.cities) {
        if (c.tier === 'disqualified') continue
        if (placed.every((p) => far(p, c))) placed.push(c)
        if (placed.length >= 160) break
      }
      for (const c of placed) {
        const d = document.createElement('div')
        d.className = `city-marker ${c.tier}${selected && selected.name === c.name && selected.country === c.country ? ' selected' : ''}`
        d.title = `${c.name}, ${c.country}: ${c.tier} ${c.total}`
        d.style.background = TIER_COLOR[c.tier]
        d.addEventListener('click', (ev) => { ev.stopPropagation(); onSelectCity(c) })
        markers.current.push(new maplibregl.Marker({ element: d }).setLngLat([c.lon, c.lat]).addTo(m))
      }
    }
    if (ready) apply()
  }, [result, selected, onSelectCity, ready])

  return <div ref={el} className="finder-map" />
}
