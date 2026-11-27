export type PaletteId = '01' | '02' | '03' | '04'

export type Palette = {
  id: PaletteId
  name: string
  high: string
  low: string
}

/** 参考 SHAP 配色图四套方案：high=暖色/高值，low=冷色/低值 */
export const PALETTES: Palette[] = [
  { id: '01', name: 'Coral / Blue-Grey', high: '#E59A9A', low: '#5D7B93' },
  { id: '02', name: 'Mint / Eggplant', high: '#A8C69F', low: '#4B3B55' },
  { id: '03', name: 'Amber / Slate', high: '#D4A373', low: '#5E738F' },
  { id: '04', name: 'Raspberry / Teal', high: '#AF6B84', low: '#2D6A6A' },
]

export function applyPalette(palette: Palette) {
  const root = document.documentElement
  root.style.setProperty('--palette-high', palette.high)
  root.style.setProperty('--palette-low', palette.low)
}

export function mix(hex: string, ratio: number) {
  // ratio 0 → low feel toward white, 1 → full color
  const n = hex.replace('#', '')
  const r = parseInt(n.slice(0, 2), 16)
  const g = parseInt(n.slice(2, 4), 16)
  const b = parseInt(n.slice(4, 6), 16)
  const rr = Math.round(r + (255 - r) * (1 - ratio))
  const gg = Math.round(g + (255 - g) * (1 - ratio))
  const bb = Math.round(b + (255 - b) * (1 - ratio))
  return `#${[rr, gg, bb].map((v) => v.toString(16).padStart(2, '0')).join('')}`
}
