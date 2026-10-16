// The home banner: Mount Olympus at dusk, drawn as an engraved plate. Ridges are filled close
// to the page colour and outlined in ink, so the plate reads on light and dark skins alike; the
// sky glows with the trail blaze; a band of cloud wraps the mountain's shoulders, as it does on
// the real Olympus; a dashed trail climbs past one camp flag per path to the summit, where the
// caduceus, Hermes's herald's staff, stands in place of a flag. A flag fills once that path's
// Field Record is created, and the staff fills when every path is done. Inline SVG only: no
// image, no network. Text never sits on the art without a scrim, and every word is full-contrast ink.

import { jsx, jsxs } from 'react/jsx-runtime'

const W = 1200
const H = 320
const SKY = 40

export const BANNER_RIDGES = {
  far: 'M0 214 L80 186 L150 198 L240 156 L320 174 L420 128 L500 154 L580 116 L660 144 L760 96 L840 124 L930 86 L1010 110 L1100 74 L1200 98 L1200 320 L0 320 Z',
  main: 'M0 262 L120 238 L220 252 L330 208 L430 228 L540 172 L640 196 L740 142 L820 162 L880 118 L918 102 L944 84 L962 90 L982 66 L1000 58 L1012 70 L1026 64 L1038 74 L1058 88 L1090 112 L1150 132 L1200 126 L1200 320 L0 320 Z',
  near: 'M0 302 L140 282 L260 294 L380 264 L500 282 L620 252 L760 274 L880 242 L1000 264 L1120 238 L1200 252 L1200 320 L0 320 Z',
}
export const BANNER_TRAIL = 'M430 318 C480 292 520 264 560 250 S630 238 660 222 S730 200 760 192 S820 172 850 160 S900 140 930 125 S975 84 1000 60'
export const BANNER_CAMPS = [
  { x: 560, y: 250 }, { x: 660, y: 222 }, { x: 760, y: 192 }, { x: 850, y: 160 }, { x: 930, y: 125 },
]
export const BANNER_SUMMIT = { x: 1000, y: 58 }

const crest = d => d.replace(/ L1200 320 L0 320 Z$/, '')

/** Cloud banks on the mountain's shoulders: soft, flat-bottomed, drawn over the ridges and under the trail. */
export const BANNER_CLOUDS = [
  'M600 182 C612 168 640 166 652 176 C664 160 700 160 712 176 C730 170 756 176 760 188 L600 188 Z',
  'M690 116 C700 104 726 102 736 112 C748 98 784 98 794 112 C810 106 836 110 840 118 L690 118 Z',
  'M1040 140 C1050 128 1074 126 1084 136 C1096 122 1128 124 1138 138 C1156 134 1180 140 1184 150 L1040 150 Z',
]

/** The caduceus: a staff, two wings at the head and two snakes wound around it. */
function Caduceus({ x, y, done }) {
  const h = 42
  const top = y - h
  const snake = side => {
    const pts = []
    for (let k = 0; k <= 32; k++) {
      const t = k / 32
      const yy = y - 6 - t * (h - 16)
      const xx = x + side * Math.sin(t * Math.PI * 2.5) * (6 - t * 2)
      pts.push(`${xx.toFixed(1)} ${yy.toFixed(1)}`)
    }
    return `M${pts.join(' L')}`
  }
  const wing = side => `M${x} ${top + 8} C${x + side * 8} ${top - 2} ${x + side * 18} ${top - 4} ${x + side * 24} ${top} C${x + side * 18} ${top + 2} ${x + side * 16} ${top + 6} ${x + side * 20} ${top + 8} C${x + side * 13} ${top + 9} ${x + side * 8} ${top + 12} ${x} ${top + 12} Z`
  return jsxs('g', { className: 'fa-bn-cad', 'data-done': done ? '' : undefined, children: [
    jsx('path', { className: 'fa-bn-wing', d: wing(-1) }),
    jsx('path', { className: 'fa-bn-wing', d: wing(1) }),
    jsx('line', { className: 'fa-bn-staff', x1: x, y1: y, x2: x, y2: top + 4 }),
    jsx('circle', { className: 'fa-bn-orb', cx: x, cy: top + 2, r: 3.4 }),
    jsx('path', { className: 'fa-bn-snake', d: snake(1) }),
    jsx('path', { className: 'fa-bn-snake', d: snake(-1) }),
    jsx('circle', { className: 'fa-bn-camp', cx: x, cy: y, r: 4.5 }),
  ] })
}

/** Contour rings around the summit, slightly irregular so they read as terrain, not a target. */
export function bannerContours(count = 15) {
  const out = []
  for (let i = 0; i < count; i++) {
    const rx = 46 + i * 48
    const ry = rx * 0.4
    const pts = []
    for (let k = 0; k <= 48; k++) {
      const a = (k / 48) * Math.PI * 2
      const wobble = 1 + 0.06 * Math.sin(a * 3 + i * 0.9) + 0.035 * Math.sin(a * 7 - i * 1.3)
      pts.push(`${(BANNER_SUMMIT.x + Math.cos(a) * rx * wobble).toFixed(1)} ${(BANNER_SUMMIT.y + 6 + Math.sin(a) * ry * wobble).toFixed(1)}`)
    }
    out.push({ d: `M${pts.join(' L')} Z`, index: i % 5 === 4 })
  }
  return out
}
const RINGS = bannerContours()

function Flag({ x, y, done, label, summit = false }) {
  const pole = summit ? 34 : 22
  const reach = summit ? 22 : 14
  const drop = summit ? 14 : 10
  return jsxs('g', { className: 'fa-bn-flag', 'data-done': done ? '' : undefined, 'data-summit': summit ? '' : undefined, children: [
    jsx('line', { className: 'fa-bn-pole', x1: x, y1: y, x2: x, y2: y - pole }),
    jsx('path', { className: 'fa-bn-cloth', d: `M${x} ${y - pole} L${x + reach} ${y - pole + drop / 2} L${x} ${y - pole + drop} Z` }),
    jsx('circle', { className: 'fa-bn-camp', cx: x, cy: y, r: summit ? 4.5 : 3.5 }),
    label ? jsx('text', { className: 'fa-bn-label', x: x - 6, y: y - pole + 4, textAnchor: 'end', children: label }) : null,
  ] })
}

/** The plate on its own, sized by its container; the summit stays in view at any width. */
export function BannerArt({ camps = [], summitDone = false }) {
  return jsxs('svg', { className: 'fa-bn-art', viewBox: `0 ${-SKY} ${W} ${H + SKY}`, preserveAspectRatio: 'xMaxYMax slice', 'aria-hidden': 'true', focusable: 'false', children: [
    jsxs('defs', { children: [
      jsxs('linearGradient', { id: 'fa-bn-sky', x1: 0, y1: 0, x2: 0, y2: 1, children: [
        jsx('stop', { offset: '0', className: 'fa-bn-sky-top' }),
        jsx('stop', { offset: '0.6', className: 'fa-bn-sky-mid' }),
        jsx('stop', { offset: '1', className: 'fa-bn-sky-low' }),
      ] }),
      jsx('clipPath', { id: 'fa-bn-main-clip', children: jsx('path', { d: BANNER_RIDGES.main }) }),
    ] }),
    jsx('rect', { y: -SKY, width: W, height: H + SKY, fill: 'url(#fa-bn-sky)' }),
    jsx('circle', { className: 'fa-bn-sun-halo', cx: 1112, cy: 70, r: 62 }),
    jsx('circle', { className: 'fa-bn-sun', cx: 1112, cy: 70, r: 32 }),
    jsx('path', { className: 'fa-bn-ridge', 'data-layer': 'far', d: BANNER_RIDGES.far }),
    jsx('path', { className: 'fa-bn-ridge', 'data-layer': 'main', d: BANNER_RIDGES.main }),
    jsx('g', { className: 'fa-bn-contours', clipPath: 'url(#fa-bn-main-clip)', children: RINGS.map((ring, i) =>
      jsx('path', { d: ring.d, 'data-index': ring.index ? '' : undefined }, i)) }),
    jsx('path', { className: 'fa-bn-crest', d: crest(BANNER_RIDGES.main) }),
    jsx('g', { className: 'fa-bn-clouds', children: BANNER_CLOUDS.map((d, i) => jsx('path', { d }, i)) }),
    jsx('path', { className: 'fa-bn-trail', d: BANNER_TRAIL }),
    ...BANNER_CAMPS.map((at, i) => jsx(Flag, { x: at.x, y: at.y, done: camps[i]?.done, label: camps[i]?.label }, `camp-${i}`)),
    jsx(Caduceus, { x: BANNER_SUMMIT.x, y: BANNER_SUMMIT.y, done: summitDone }, 'summit'),
    jsx('text', { className: 'fa-bn-label fa-bn-summit-label', x: BANNER_SUMMIT.x + 30, y: BANNER_SUMMIT.y - 18, children: 'Olympus' }),
    jsx('path', { className: 'fa-bn-ridge', 'data-layer': 'near', d: BANNER_RIDGES.near }),
    jsx('path', { className: 'fa-bn-crest', 'data-layer': 'near', d: crest(BANNER_RIDGES.near) }),
  ] })
}

/** The home banner: the plate, a scrim, the wordmark lockup and one promise. */
export function Banner({ eyebrow, promise, facts = [], camps = [], summitDone = false }) {
  return jsxs('header', { className: 'fa-bn hk-enter', children: [
    jsx(BannerArt, { camps, summitDone }, 'art'),
    jsx('span', { className: 'fa-bn-scrim', 'aria-hidden': 'true' }, 'scrim'),
    jsxs('div', { className: 'fa-bn-copy', children: [
      eyebrow ? jsx('span', { className: 'fa-sc fa-sc-blaze', children: eyebrow }, 'eyebrow') : null,
      jsxs('h1', { className: 'fa-bn-mark', children: [
        jsx('span', { children: 'Field' }, 'a'),
        jsx('span', { className: 'fa-bn-rule', 'aria-hidden': 'true' }, 'rule'),
        jsx('span', { children: 'Academy' }, 'b'),
      ] }, 'mark'),
      jsx('p', { className: 'fa-bn-promise', children: promise }, 'promise'),
      facts.length ? jsx('p', { className: 'fa-bn-facts', children: facts.map(f => jsx('span', { children: f }, f)) }, 'facts') : null,
    ] }, 'copy'),
  ] })
}

export const BANNER_CSS = `
.fa-bn{position:relative;overflow:hidden;isolation:isolate;min-height:260px;display:flex;align-items:center;border:1px solid var(--hk-stroke);border-radius:calc(var(--hk-radius) + 4px);background:var(--hk-bg)}
.fa-bn-art{position:absolute;inset:0;width:100%;height:100%;z-index:-2;display:block}
.fa-bn-sky-top{stop-color:var(--hk-bg)}
.fa-bn-sky-mid{stop-color:color-mix(in oklab,var(--fa-blaze) 16%,var(--hk-bg))}
.fa-bn-sky-low{stop-color:color-mix(in oklab,var(--fa-blaze) 34%,var(--hk-bg))}
.fa-bn-sun{fill:color-mix(in oklab,var(--fa-blaze) 58%,var(--hk-bg))}
.fa-bn-sun-halo{fill:color-mix(in oklab,var(--fa-blaze) 18%,transparent)}
.fa-bn-ridge[data-layer=far]{fill:color-mix(in oklab,var(--fa-blaze) 22%,color-mix(in srgb,var(--hk-ink) 10%,var(--hk-bg)));stroke:color-mix(in srgb,var(--fa-blaze) 55%,transparent);stroke-width:1}
.fa-bn-ridge[data-layer=main]{fill:color-mix(in oklab,var(--fa-blaze) 6%,color-mix(in srgb,var(--hk-ink) 7%,var(--hk-bg)))}
.fa-bn-ridge[data-layer=near]{fill:var(--hk-bg)}
.fa-bn-crest{fill:none;stroke:color-mix(in srgb,var(--hk-ink) 55%,transparent);stroke-width:1.4;stroke-linejoin:round}
.fa-bn-crest[data-layer=near]{stroke:color-mix(in srgb,var(--hk-ink) 30%,transparent)}
.fa-bn-contours path{fill:none;stroke:color-mix(in srgb,var(--hk-ink) 13%,transparent);stroke-width:1}
.fa-bn-contours path[data-index]{stroke:color-mix(in srgb,var(--fa-blaze) 45%,transparent);stroke-width:1.3}
.fa-bn-trail{fill:none;stroke:var(--fa-blaze);stroke-width:2.2;stroke-dasharray:7 6;stroke-linecap:round}
.fa-bn-camp{fill:var(--hk-bg);stroke:var(--fa-blaze);stroke-width:2}
.fa-bn-pole{stroke:var(--hk-ink);stroke-width:1.4}
.fa-bn-cloth{fill:var(--hk-bg);stroke:var(--fa-blaze);stroke-width:1.4;stroke-linejoin:round}
.fa-bn-flag[data-done] .fa-bn-cloth,.fa-bn-flag[data-done] .fa-bn-camp{fill:var(--fa-blaze)}
.fa-bn-flag[data-summit] .fa-bn-pole{stroke-width:1.8}
.fa-bn-clouds path{fill:color-mix(in srgb,var(--hk-bg) 78%,var(--hk-ink) 6%);stroke:color-mix(in srgb,var(--hk-ink) 22%,transparent);stroke-width:1;opacity:.92}
.fa-bn-staff{stroke:var(--hk-ink);stroke-width:2;stroke-linecap:round}
.fa-bn-orb{fill:var(--hk-bg);stroke:var(--fa-blaze);stroke-width:1.6}
.fa-bn-wing{fill:var(--hk-bg);stroke:var(--fa-blaze);stroke-width:1.4;stroke-linejoin:round}
.fa-bn-snake{fill:none;stroke:var(--fa-blaze);stroke-width:1.7;stroke-linecap:round}
.fa-bn-cad[data-done] .fa-bn-wing,.fa-bn-cad[data-done] .fa-bn-orb{fill:var(--fa-blaze)}
.fa-bn-summit-label{text-anchor:start}
.fa-bn-label{fill:var(--hk-ink);font-size:13px;font-weight:600;letter-spacing:.08em;font-variant-caps:all-small-caps;paint-order:stroke;stroke:var(--hk-bg);stroke-width:4px;stroke-linejoin:round}
.fa-bn-scrim{position:absolute;inset:0;z-index:-1;background:linear-gradient(90deg,var(--hk-bg) 0%,color-mix(in srgb,var(--hk-bg) 92%,transparent) 30%,color-mix(in srgb,var(--hk-bg) 35%,transparent) 44%,transparent 54%)}
.fa-bn-copy{display:grid;gap:9px;padding:28px 30px;max-width:480px;color:var(--hk-ink)}
.fa-bn-mark{display:flex;align-items:center;gap:12px;margin:0;font-size:30px;line-height:1.05;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.fa-bn-rule{display:block;width:22px;height:2px;background:var(--fa-blaze);flex:none}
.fa-bn-promise{font-size:14px;line-height:1.5;max-width:44ch}
.fa-bn-facts{display:flex;flex-wrap:wrap;gap:6px;font-size:var(--hk-fs-sm);font-weight:600}
.fa-bn-facts span{padding:1px 8px;border-radius:999px;border:1px solid var(--hk-stroke);background:color-mix(in srgb,var(--hk-bg) 82%,transparent)}
@container (max-width:640px){
  .fa-bn{flex-direction:column;align-items:stretch;min-height:0}
  .fa-bn-art{position:relative;inset:auto;height:150px;order:-1;border-bottom:1px solid var(--hk-stroke)}
  .fa-bn-scrim{display:none}
  .fa-bn-copy{padding:16px 18px 18px;max-width:none}
  .fa-bn-mark{font-size:24px;letter-spacing:.12em}
  .fa-bn-label{display:none}
}
@media (prefers-reduced-motion:no-preference){.fa-bn-trail{animation:fa-bn-walk 1.6s var(--hk-ease,ease) both}}
@keyframes fa-bn-walk{from{stroke-dashoffset:120;opacity:.2}to{stroke-dashoffset:0;opacity:1}}
`
