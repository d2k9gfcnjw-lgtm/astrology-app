import type { Settings, TransitSettings } from '../lib/types'

const ALL_BODIES = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'chiron', 'node', 'lilith']
const POINTS = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'asc', 'dsc', 'mc', 'ic', 'node', 'chiron', 'lilith', 'fortune']
const CUSPS = Array.from({ length: 12 }, (_, i) => `cusp_${i + 1}`)
const ASPECTS = ['conjunction', 'opposition', 'trine', 'square', 'sextile', 'quincunx', 'semisextile', 'semisquare', 'sesquiquadrate']
const toggle = (list: string[], k: string) => (list.includes(k) ? list.filter((x) => x !== k) : [...list, k])

export function SettingsDrawer({ settings, onChange, onClose }: { settings: Settings; onChange: (s: Settings) => void; onClose: () => void }) {
  const set = (patch: Partial<Settings>) => onChange({ ...settings, ...patch })
  const tset = (patch: Partial<TransitSettings>) => onChange({ ...settings, transits: { ...settings.transits, ...patch } })
  const t = settings.transits
  const orb = (k: string, v: number) => onChange({ ...settings, aspects: { ...settings.aspects, orbs: { ...settings.aspects.orbs, [k]: v } } })
  return (
    <div className="settings">
      <div className="library-head"><h2>Settings</h2><button className="secondary" onClick={onClose}>Close</button></div>
      <label>Zodiac<select value={settings.zodiac} onChange={(e) => set({ zodiac: e.target.value as Settings['zodiac'] })}><option value="tropical">Tropical</option><option value="sidereal">Sidereal</option></select></label>
      {settings.zodiac === 'sidereal' && <label>Ayanamsa<select value={settings.ayanamsa} onChange={(e) => set({ ayanamsa: e.target.value as Settings['ayanamsa'] })}><option value="lahiri">Lahiri</option><option value="fagan_bradley">Fagan-Bradley</option><option value="raman">Raman</option><option value="krishnamurti">Krishnamurti</option></select></label>}
      <label>Houses<select value={settings.house_system} onChange={(e) => set({ house_system: e.target.value as Settings['house_system'] })}><option value="placidus">Placidus</option><option value="whole_sign">Whole Sign</option></select></label>
      <label>Node<select value={settings.node_type} onChange={(e) => set({ node_type: e.target.value as Settings['node_type'] })}><option value="true">True</option><option value="mean">Mean</option></select></label>
      <label>Lilith<select value={settings.lilith_type} onChange={(e) => set({ lilith_type: e.target.value as Settings['lilith_type'] })}><option value="mean">Mean</option><option value="true">True (osculating)</option></select></label>
      <label>Part of Fortune<select value={settings.fortune_formula} onChange={(e) => set({ fortune_formula: e.target.value as Settings['fortune_formula'] })}><option value="sect">Reversed at night</option><option value="day">Day formula always</option></select></label>
      <fieldset><legend>Show</legend>
        <label><input type="checkbox" checked={settings.include_node} onChange={(e) => set({ include_node: e.target.checked })} /> Node</label>
        <label><input type="checkbox" checked={settings.include_chiron} onChange={(e) => set({ include_chiron: e.target.checked })} /> Chiron</label>
        <label><input type="checkbox" checked={settings.include_lilith} onChange={(e) => set({ include_lilith: e.target.checked })} /> Lilith</label>
        <label><input type="checkbox" checked={settings.include_fortune} onChange={(e) => set({ include_fortune: e.target.checked })} /> Part of Fortune</label>
      </fieldset>
      <fieldset><legend>Aspect orbs (each side of exact)</legend>
        {['conjunction', 'opposition', 'trine', 'square', 'sextile'].map((k) => (
          <label key={k}>{k}<input type="number" step="0.5" min={0} max={15} value={settings.aspects.orbs[k]} onChange={(e) => orb(k, Number(e.target.value))} /></label>
        ))}
        <label>Sun/Moon bonus<input type="number" step="0.5" min={0} max={5} value={settings.aspects.luminary_bonus} onChange={(e) => onChange({ ...settings, aspects: { ...settings.aspects, luminary_bonus: Number(e.target.value) } })} /></label>
        <label><input type="checkbox" checked={settings.aspects.include_points} onChange={(e) => onChange({ ...settings, aspects: { ...settings.aspects, include_points: e.target.checked } })} /> Aspects to Node, Chiron, Lilith, Fortune</label>
        <label><input type="checkbox" checked={settings.aspects.minor_aspects} onChange={(e) => onChange({ ...settings, aspects: { ...settings.aspects, minor_aspects: e.target.checked } })} /> Minor aspects (orb {settings.aspects.minor_orb}°)</label>
      </fieldset>
      <h2>Transits</h2>
      <fieldset><legend>Transiting bodies in the report</legend>
        {ALL_BODIES.map((b) => <label key={b}><input type="checkbox" checked={t.bodies.includes(b)} onChange={() => tset({ bodies: toggle(t.bodies, b) })} /> {b}</label>)}
      </fieldset>
      <fieldset><legend>Transit orbs per body (each side)</legend>
        {ALL_BODIES.map((b) => <label key={b}>{b}<input type="number" step="0.5" min={0} max={10} value={t.orbs[b] ?? 2} onChange={(e) => tset({ orbs: { ...t.orbs, [b]: Number(e.target.value) } })} /></label>)}
      </fieldset>
      <fieldset><legend>Natal points</legend>
        {POINTS.map((p) => <label key={p}><input type="checkbox" checked={t.natal_points.includes(p)} onChange={() => tset({ natal_points: toggle(t.natal_points, p) })} /> {p.toUpperCase() === p.toUpperCase() && ['asc', 'dsc', 'mc', 'ic'].includes(p) ? p.toUpperCase() : p}</label>)}
        <label><input type="checkbox" checked={CUSPS.every((c) => t.natal_points.includes(c))} onChange={(e) => tset({ natal_points: e.target.checked ? [...t.natal_points.filter((p) => !CUSPS.includes(p)), ...CUSPS] : t.natal_points.filter((p) => !CUSPS.includes(p)) })} /> all house cusps</label>
      </fieldset>
      <fieldset><legend>Transit aspects</legend>
        {ASPECTS.map((a) => <label key={a}><input type="checkbox" checked={t.aspects.includes(a)} onChange={() => tset({ aspects: toggle(t.aspects, a) })} /> {a}</label>)}
      </fieldset>
      <fieldset><legend>Report sections</legend>
        <label><input type="checkbox" checked={t.include_ingresses} onChange={(e) => tset({ include_ingresses: e.target.checked })} /> House ingresses</label>
        <label><input type="checkbox" checked={t.include_sign_ingresses} onChange={(e) => tset({ include_sign_ingresses: e.target.checked })} /> Sign ingresses</label>
        <label><input type="checkbox" checked={t.include_stations} onChange={(e) => tset({ include_stations: e.target.checked })} /> Stations</label>
      </fieldset>
    </div>
  )
}
