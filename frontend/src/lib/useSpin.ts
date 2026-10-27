import { useCallback, useEffect, useRef } from 'react'
import { api } from './api'
import { frameAt } from './interpolate'
import type { Keyframe, Settings } from './types'

const FRAMES_PER_BATCH = 24
const BATCH_SECONDS = 3 // of real time at the current rate

/**
 * Fluid spin: advances jd every animation frame at rate*speed simulated seconds per real second,
 * drawing from interpolated keyframes fetched in batches ahead of the playhead.
 */
export function useSpin(opts: {
  jdRef: React.MutableRefObject<number>
  lat: number
  lon: number
  settings: Settings
  speed: number
  onFrame: (f: Keyframe) => void
  onStop: (jd: number) => void
}) {
  const rate = useRef(0)
  const raf = useRef<number | null>(null)
  const last = useRef(0)
  const lastTick = useRef(0)
  const frames = useRef<Keyframe[]>([])
  const inflight = useRef<Promise<void> | null>(null)
  const { jdRef, lat, lon, settings, speed, onFrame, onStop } = opts

  useEffect(() => { frames.current = [] }, [lat, lon, settings, speed])

  const fetchWindow = useCallback((fromJd: number, dir: number) => {
    if (inflight.current) return inflight.current
    const span = (speed * BATCH_SECONDS) / 86400
    const jds = Array.from({ length: FRAMES_PER_BATCH }, (_, i) => fromJd + dir * (span * (i - 1)) / (FRAMES_PER_BATCH - 2))
    const sorted = [...jds].sort((a, b) => a - b)
    inflight.current = api.keyframes(sorted, lat, lon, settings).then((fs) => {
      const merged = [...frames.current.filter((f) => f.jd_ut < sorted[0] - 1e-9 || f.jd_ut > sorted[sorted.length - 1] + 1e-9), ...fs].sort((a, b) => a.jd_ut - b.jd_ut)
      frames.current = merged.filter((f) => Math.abs(f.jd_ut - jdRef.current) < span * 4)
    }).catch(() => undefined).finally(() => { inflight.current = null })
    return inflight.current
  }, [lat, lon, settings, speed, jdRef])

  const tick = useCallback((now: number) => {
    const dt = Math.min(0.1, (now - last.current) / 1000)
    last.current = now
    if (rate.current === 0) { raf.current = null; return }
    const dir = Math.sign(rate.current)
    jdRef.current += (rate.current * speed * dt) / 86400
    const f = frameAt(frames.current, jdRef.current)
    const span = (speed * BATCH_SECONDS) / 86400
    const edge = dir > 0 ? frames.current[frames.current.length - 1]?.jd_ut : frames.current[0]?.jd_ut
    if (f === null || edge === undefined || Math.abs(edge - jdRef.current) < span * 0.4) void fetchWindow(jdRef.current, dir || 1)
    if (f) onFrame(f)
    raf.current = requestAnimationFrame(tick)
    lastTick.current = performance.now()
  }, [speed, onFrame, onStop, fetchWindow, jdRef])

  const setRate = useCallback((r: number) => {
    const was = rate.current
    rate.current = r
    if (r !== 0 && was === 0 && raf.current === null) {
      last.current = performance.now()
      void fetchWindow(jdRef.current, Math.sign(r))
      raf.current = requestAnimationFrame(tick)
    } else if (r === 0 && was !== 0) {
      // Stop right away rather than waiting for the next animation frame.
      if (raf.current !== null) cancelAnimationFrame(raf.current)
      raf.current = null
      onStop(jdRef.current)
    }
  }, [fetchWindow, tick, jdRef, onStop])

  useEffect(() => () => { if (raf.current) cancelAnimationFrame(raf.current) }, [])

  // Watchdog: if the browser dropped our animation frame while playing, start it again.
  useEffect(() => {
    const id = window.setInterval(() => {
      if (rate.current !== 0 && performance.now() - lastTick.current > 300) {
        if (raf.current !== null) cancelAnimationFrame(raf.current)
        last.current = performance.now()
        raf.current = requestAnimationFrame(tick)
      }
    }, 300)
    return () => window.clearInterval(id)
  }, [tick])

  return { setRate, isSpinning: () => rate.current !== 0 }
}
