import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { FeatureCollection } from 'geojson'
import { api } from '../lib/api'
import { BODY_NAMES } from '../lib/angles'
import { BODY_COLORS, linesToGeoJson, orbPixels, paransToGeoJson } from '../lib/acgGeo'
import { DEFAULT_ACG, type AcgAt, type AcgLines, type AcgSettings, type City, type FinderResult, type Settings, type Subject } from '../lib/types'
import { CitySearch } from './CitySearch'

type Source = 'natal' | 'clock' | 'solar'
const ANGLE_LABEL: Record<string, string> = { asc: 'ASC', dsc: 'DSC', mc: 'MC', ic: 'IC' }
const ALL_BODIES = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'chiron', 'node']
const fmt = (iso: string) => iso.replace('T', ' ').slice(0, 16)

interface Props {
  subject: Subject | null
  natalJd: number | null
  clockJd: number
  settings: Settings
  defaultYear: number
  finderResult: FinderResult | null
  landGeoJson: FeatureCollection | null
  onOpenPlace: (jd: number, lat: number, lon: number, name: string) => void
}

export function AcgView(p: Props) {
  const [source, setSource] = useState<Source>('natal')
  const [year, setYear] = useState(p.defaultYear + 1)
  const [acg, setAcg] = useState<AcgSettings>(DEFAULT_ACG)
  const [jd, setJd] = useState<number | null>(p.natalJd)
  const [data, setData] = useState<AcgLines | null>(null)
  const [at, setAt] = useState<AcgAt | null>(null)
  const [atName, setAtName] = useState('')
  const [showHeat, setShowHeat] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [ready, setReady] = useState(false)
  const marker = useRef<maplibregl.Marker | null>(null)

  // Which instant the lines belong to
  useEffect(() => {
    if (source === 'natal') setJd(p.natalJd)
    else if (source === 'clock') setJd(p.clockJd)
    else if (p.subject) api.solarReturn(p.subject.id, year, null, false).then((r) => setJd(r.chosen.jd_ut)).catch((e) => setErr(e.message))
  }, [source, year, p.natalJd, p.clockJd, p.subject])

  useEffect(() => {
    if (jd === null) return
    setBusy(true)
    api.acgLines(jd, p.settings, acg).then((d) => { setData(d); setErr(null) }).catch((e) => setErr(e.message)).finally(() => setBusy(false))
  }, [jd, p.settings, acg])

  const clickPlace = useCallback(async (lat: number, lon: number, name: string) => {
    if (jd === null) return
    try {
      const r = await api.acgAt(jd, lat, lon, p.settings, acg)
      setAt(r); setAtName(name); setErr(null)
      if (map.current) {
        marker.current?.remove()
        marker.current = new maplibregl.Marker({ color: '#b5179e' }).setLngLat([lon, lat]).addTo(map.current)
      }
    } catch (e) { setErr((e as Error).message) }
  }, [jd, p.settings, acg])

  // the map
  useEffect(() => {
    if (!el.current || map.current) return
    const m = new maplibregl.Map({
      container: el.current,
      style: { version: 8, sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } },
        layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#dfe9f3' } }, { id: 'osm', type: 'raster', source: 'osm', paint: { 'raster-opacity': 0.55 } }] },
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
    map.current = m
    return () => { window.clearInterval(poll); ro.disconnect(); m.remove(); map.current = null }
  }, [])

  useEffect(() => {
    const m = map.current
    if (!m) return
    const h = (e: maplibregl.MapMouseEvent) => void clickPlace(e.lngLat.lat, e.lngLat.lng, `${e.lngLat.lat.toFixed(2)}, ${e.lngLat.lng.toFixed(2)}`)
    m.on('click', h)
    return () => { m.off('click', h) }
  }, [clickPlace])

  useEffect(() => {
    const m = map.current
    if (!m || !p.landGeoJson) return
    const add = () => {
      if (m.getSource('land')) return
      m.addSource('land', { type: 'geojson', data: p.landGeoJson! })
      m.addLayer({ id: 'land-fill', type: 'fill', source: 'land', paint: { 'fill-color': '#f1efe8', 'fill-opacity': 0.9 } }, 'osm')
      m.addLayer({ id: 'land-line', type: 'line', source: 'land', paint: { 'line-color': '#777', 'line-width': 0.6 } })
    }
    if (ready) add()
  }, [p.landGeoJson, ready])

  // lines, orb bands, parans
  useEffect(() => {
    const m = map.current
    if (!m) return
    const apply = () => {
      for (const id of ['acg-orb', 'acg-lines', 'acg-line-labels', 'acg-parans']) if (m.getLayer(id)) m.removeLayer(id)
      for (const id of ['acg', 'parans']) if (m.getSource(id)) m.removeSource(id)
      if (!data) return
      m.addSource('acg', { type: 'geojson', data: linesToGeoJson(data.lines) })
      m.addSource('parans', { type: 'geojson', data: paransToGeoJson(data.parans) })
      const w0 = orbPixels(acg.orb_km, 0, 35)
      m.addLayer({ id: 'acg-orb', type: 'line', source: 'acg', paint: { 'line-color': ['get', 'color'], 'line-opacity': 0.18, 'line-blur': 3,
        'line-width': ['interpolate', ['exponential', 2], ['zoom'], 0, w0, 12, w0 * 4096] } })
      m.addLayer({ id: 'acg-lines', type: 'line', source: 'acg', paint: { 'line-color': ['get', 'color'], 'line-width': 1.6, 'line-dasharray': ['case', ['==', ['get', 'dashed'], 1], ['literal', [2, 2]], ['literal', [1, 0]]] } })
      m.addLayer({ id: 'acg-line-labels', type: 'symbol', source: 'acg', layout: { 'symbol-placement': 'line', 'symbol-spacing': 600, 'text-field': ['concat', ['get', 'body'], ' ', ['upcase', ['get', 'angle']]], 'text-size': 10, 'text-font': ['Open Sans Regular'], 'text-keep-upright': true },
        paint: { 'text-color': ['get', 'color'], 'text-halo-color': '#fff', 'text-halo-width': 1.2 } })
      if (acg.include_parans) {
        // faint lines only; the parans near the clicked place are listed in the panel
        m.addLayer({ id: 'acg-parans', type: 'line', source: 'parans', paint: { 'line-color': '#555', 'line-width': 0.6, 'line-dasharray': [1, 4], 'line-opacity': 0.35 } }, 'acg-orb')
      }
    }
    if (ready) apply()
  }, [data, acg.orb_km, acg.include_parans, ready])

  // optional finder heat underneath (separate method, separate layer)
  useEffect(() => {
    const m = map.current
    if (!m) return
    const apply = () => {
      if (m.getLayer('heat')) m.removeLayer('heat')
      if (m.getSource('heat')) m.removeSource('heat')
      if (!showHeat || !p.finderResult) return
      const res = p.finderResult
      const step = res.grid.step
      const latMin = Number(res.options.lat_min ?? -60), latMax = Number(res.options.lat_max ?? 66)
      const w = Math.round(360 / step), h = Math.round((latMax - latMin) / step) + 1
      const canvas = document.createElement('canvas'); canvas.width = w; canvas.height = h
      const ctx = canvas.getContext('2d')!; const img = ctx.createImageData(w, h)
      const scores = res.grid.cells.filter((c) => c.score !== null).map((c) => c.score as number)
      const lo = Math.min(...scores, -40), hi = Math.max(...scores, 40)
      for (const c of res.grid.cells) {
        const x = Math.round((c.lon + 180) / step), y = h - 1 - Math.round((c.lat - latMin) / step)
        if (x < 0 || x >= w || y < 0 || y >= h) continue
        const i = (y * w + x) * 4
        if (c.score === null) { img.data[i] = 120; img.data[i + 1] = 120; img.data[i + 2] = 120; img.data[i + 3] = 110; continue }
        const t = (c.score - lo) / (hi - lo)
        img.data[i] = Math.round(253 * (1 - t) + 27 * t); img.data[i + 1] = Math.round(184 * (1 - t) + 158 * t); img.data[i + 2] = Math.round(99 * (1 - t) + 119 * t); img.data[i + 3] = 120
      }
      ctx.putImageData(img, 0, 0)
      m.addSource('heat', { type: 'image', url: canvas.toDataURL(), coordinates: [[-180 - step / 2, latMax + step / 2], [180 - step / 2, latMax + step / 2], [180 - step / 2, latMin - step / 2], [-180 - step / 2, latMin - step / 2]] })
      m.addLayer({ id: 'heat', type: 'raster', source: 'heat', paint: { 'raster-opacity': 0.6, 'raster-resampling': 'nearest' } }, m.getLayer('acg-orb') ? 'acg-orb' : undefined)
    }
    if (ready) apply()
  }, [showHeat, p.finderResult, data, ready])

  const toggle = (list: string[], k: string) => (list.includes(k) ? list.filter((x) => x !== k) : [...list, k])
  const pick = (c: City) => { void clickPlace(c.lat, c.lon, c.label); map.current?.flyTo({ center: [c.lon, c.lat], zoom: 4 }) }
  const title = useMemo(() => source === 'natal' ? 'Natal lines' : source === 'clock' ? 'Lines for the time-travel instant' : `Solar return ${year} lines`, [source, year])

  if (p.natalJd === null) return <div className="empty-state">Open a chart first.</div>

  return (
    <div className="acg">
      <div className="acg-form">
        <div className="seg">
          <button className={source === 'natal' ? 'active' : ''} onClick={() => setSource('natal')}>Natal</button>
          <button className={source === 'clock' ? 'active' : ''} onClick={() => setSource('clock')}>Time travel</button>
          <button className={source === 'solar' ? 'active' : ''} onClick={() => setSource('solar')} disabled={!p.subject}>Solar return</button>
        </div>
        {source === 'solar' && <label>Year<input type="number" value={year} onChange={(e) => setYear(Number(e.target.value) || year)} /></label>}
        <label>Orb km<input type="number" step={50} value={acg.orb_km} onChange={(e) => setAcg({ ...acg, orb_km: Number(e.target.value) || 0 })} /></label>
        <label>Method<select value={acg.method} onChange={(e) => setAcg({ ...acg, method: e.target.value as AcgSettings['method'] })}><option value="mundo">In mundo (astro.com)</option><option value="zodiacal">Zodiacal</option></select></label>
        <label className="switch"><input type="checkbox" checked={acg.include_parans} onChange={(e) => setAcg({ ...acg, include_parans: e.target.checked })} /> Parans</label>
        <label className="switch"><input type="checkbox" checked={showHeat} disabled={!p.finderResult} onChange={(e) => setShowHeat(e.target.checked)} /> Finder heat underneath (separate layer)</label>
        <label>Go to<CitySearch value="" onPick={pick} placeholder="City" /></label>
        {busy && <span className="hint">computing…</span>}
      </div>
      <div className="acg-toggles">
        {ALL_BODIES.map((b) => <button key={b} className={`chip${acg.bodies.includes(b) ? ' on' : ''}`} style={{ borderColor: BODY_COLORS[b] }} onClick={() => setAcg({ ...acg, bodies: toggle(acg.bodies, b) })}>{BODY_NAMES[b] ?? b}</button>)}
        <span className="sep" />
        {['asc', 'dsc', 'mc', 'ic'].map((a) => <button key={a} className={`chip${acg.angles.includes(a) ? ' on' : ''}`} onClick={() => setAcg({ ...acg, angles: toggle(acg.angles, a) })}>{ANGLE_LABEL[a]}</button>)}
        <span className="hint">solid = ASC and MC, dashed = DSC and IC · {title}</span>
      </div>
      {err && <div className="error">{err}</div>}
      <div ref={el} className="finder-map acg-map" />
      <div className="acg-body">
        <div className="acg-panel">
          {at ? (
            <>
              <h3>{atName}</h3>
              <div className="score-facts">
                <span>ASC {at.chart.planets && `${at.chart.houses.asc.toFixed(1)}°`}</span>
                <span>Sun house {at.chart.planet_houses.sun}</span><span>Moon house {at.chart.planet_houses.moon}</span><span>Mars house {at.chart.planet_houses.mars}</span>
                <span>{fmt(at.chart.moment.utc_datetime)} UT</span>
              </div>
              <b>Lines within {at.orb_km} km</b>
              {at.lines.length === 0 && <div className="reason">none</div>}
              {at.lines.map((l, i) => <div key={i} className="reason" style={{ color: BODY_COLORS[l.body] }}>{BODY_NAMES[l.body] ?? l.body} {ANGLE_LABEL[l.angle]} line, {l.km} km ({l.deg}°)</div>)}
              <b>Parans at this latitude (±{acg.paran_orb_lat}°)</b>
              {at.parans.length === 0 && <div className="reason">none</div>}
              {at.parans.map((q, i) => <div key={i} className="reason">{BODY_NAMES[q.body_a] ?? q.body_a} {ANGLE_LABEL[q.angle_a]} with {BODY_NAMES[q.body_b] ?? q.body_b} {ANGLE_LABEL[q.angle_b]}, latitude {q.lat.toFixed(1)}°</div>)}
              <button onClick={() => jd !== null && p.onOpenPlace(jd, at.chart.provenance.lat, at.chart.provenance.lon, atName)}>Open the chart there</button>
            </>
          ) : <div className="hint">Click the map or search a city to see the relocated chart and the lines within orb.</div>}
        </div>
        <div className="acg-panel">
          <h3>Parans {data ? `(${data.parans.length})` : ''}</h3>
          <div className="scroll paran-list">{data?.parans.map((q, i) => <div key={i} className="reason">{q.lat.toFixed(1)}°: {BODY_NAMES[q.body_a] ?? q.body_a} {ANGLE_LABEL[q.angle_a]} with {BODY_NAMES[q.body_b] ?? q.body_b} {ANGLE_LABEL[q.angle_b]}</div>)}</div>
        </div>
      </div>
    </div>
  )
}
