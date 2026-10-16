// Field Academy's look: an expedition map. Paths are trails on a topographic map,
// missions are waypoints grouped into camps, the Field Record is the summit flag.
// Everything is inline SVG coloured from the app's theme variables; one accent, the
// trail blaze, is mixed from the theme's own warm tones. Motion is gentle and only
// marks progress: a newly walked stretch of trail draws itself once, and the marker
// eases to its new waypoint. Both stop under prefers-reduced-motion.

import { useCallback, useEffect, useRef, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'
import { useReducedMotion } from 'hermes-ui-kit'
import {
  bezelTicks, compassReading, contourPaths, layoutProfile, layoutRow, pathBetween,
} from './trail.js'

/* --------------------------------------------------------------- styles -- */

export const FIELD_CSS = `
.fa-page,.fa-chip,.fa-offer{
  --fa-blaze:color-mix(in oklab,var(--hk-warn-fill) 62%,var(--hk-bad-fill));
  --fa-blaze-ink:color-mix(in srgb,var(--fa-blaze) 70%,var(--hk-ink));
  --fa-paper:color-mix(in srgb,var(--fa-blaze) 3%,var(--hk-surface));
  --fa-contour:color-mix(in srgb,var(--hk-ink) 8%,transparent);
  --fa-contour-index:color-mix(in srgb,var(--fa-blaze) 20%,transparent);
  --fa-faint:color-mix(in srgb,var(--hk-ink) 30%,transparent);
  --fa-ground:color-mix(in srgb,var(--fa-blaze) 9%,var(--hk-surface));
  --fa-ground-far:color-mix(in srgb,var(--hk-ink) 4%,transparent);
  font-family:var(--dt-font-sans,inherit);
}
.fa-sc{font-variant-caps:all-small-caps;letter-spacing:.07em;font-weight:600;font-size:var(--hk-fs);line-height:1.2}
.fa-sc-blaze{color:var(--fa-blaze-ink)}
.fa-num{font-weight:200;font-variant-numeric:lining-nums tabular-nums;letter-spacing:-.03em;line-height:1}
.fa-num-xl{font-size:34px}
.fa-num-l{font-size:28px}
.fa-num-m{font-size:20px;font-weight:300}
.fa-num small{font-size:var(--hk-fs-sm);font-weight:500;letter-spacing:0;margin-left:3px}

/* where you are */
.fa-here{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:12px}
@container (max-width:720px){.fa-here{grid-template-columns:1fr}}
.fa-panel{background:var(--fa-paper);border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);padding:16px 18px;display:grid;gap:8px;min-width:0;position:relative;overflow:hidden}
.fa-where{grid-template-columns:auto minmax(0,1fr);column-gap:18px;align-items:center}
.fa-where-lines{display:grid;gap:5px;min-width:0}
.fa-next{border-left:3px solid var(--fa-blaze)}
.fa-next-meta{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:var(--hk-fs-sm)}
.fa-next-meta span{display:inline-flex;gap:5px;align-items:center}
.fa-next-meta .codicon{color:var(--fa-blaze-ink)}
.fa-bezel{display:block;flex:none;position:relative}
.fa-bezel svg{display:block}
.fa-bezel-mid{position:absolute;inset:0;display:grid;place-content:center;justify-items:center;gap:2px;text-align:center}
.fa-bezel-mid .fa-sc{font-size:var(--hk-fs-sm)}
.fa-tick{stroke:var(--fa-faint);stroke-width:2;stroke-linecap:round}
.fa-tick[data-lit]{stroke:var(--fa-blaze)}
.fa-bezel-track{fill:none;stroke:var(--hk-stroke);stroke-width:1}
.fa-bezel-arc{fill:none;stroke:var(--fa-blaze);stroke-width:2;stroke-linecap:round}

/* the map */
.fa-map{background:var(--fa-paper);border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);position:relative;overflow:hidden;--fa-label:268px}
.fa-contours{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.fa-contours path{fill:none;stroke:var(--fa-contour);stroke-width:1}
.fa-contours path[data-index]{stroke:var(--fa-contour-index);stroke-width:1.2}
.fa-map-grid{position:relative;display:grid;grid-template-columns:var(--fa-label) minmax(0,1fr)}
.fa-map-head{grid-column:2;position:relative;height:34px;border-bottom:1px dashed var(--hk-stroke)}
.fa-map-head span{position:absolute;top:12px;transform:translateX(-50%);white-space:nowrap;font-size:var(--hk-fs-sm)}
.fa-map-corner{grid-column:1;height:34px;border-bottom:1px dashed var(--hk-stroke);padding:12px 0 0 16px;font-size:var(--hk-fs-sm)}
.fa-trail-label{grid-column:1;display:grid;align-content:center;gap:3px;padding:8px 14px 8px 16px;border:0;border-right:1px dashed var(--hk-stroke);background:transparent;color:inherit;font:inherit;text-align:left;cursor:pointer;min-width:0;
  transition:background-color var(--hk-dur) var(--hk-ease)}
.fa-trail-label:hover{background:color-mix(in srgb,var(--hk-hover) 70%,transparent)}
.fa-trail-label[data-active]{background:var(--hk-active);box-shadow:inset 3px 0 0 var(--fa-blaze)}
.fa-trail-label:focus-visible{outline:2px solid var(--hk-accent);outline-offset:-2px}
.fa-trail-top{display:flex;align-items:baseline;gap:8px;min-width:0}
.fa-trail-name{font-size:var(--hk-fs-h2);font-weight:600;flex:1;min-width:0;line-height:1.25}
.fa-trail-promise{font-size:var(--hk-fs-sm);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.fa-trail-cert{font-size:var(--hk-fs-sm);display:inline-flex;gap:5px;align-items:center}
.fa-trail-cert .codicon{color:var(--fa-blaze-ink)}
.fa-map-svg{grid-column:2;display:block;overflow:visible}
@container (max-width:760px){.fa-map{--fa-label:170px}.fa-map .fa-trail-promise,.fa-map .fa-trail-cert{display:none}.fa-map-head span{font-size:11px;letter-spacing:.04em}}
.fa-map-foot{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:space-between;padding:10px 16px;border-top:1px dashed var(--hk-stroke);position:relative}

/* trail marks (SVG) */
.fa-band{fill:transparent;transition:fill var(--hk-dur) var(--hk-ease)}
.fa-band[data-active]{fill:color-mix(in srgb,var(--hk-accent) 6%,transparent)}
.fa-divider{stroke:var(--hk-stroke);stroke-width:1;stroke-dasharray:3 4}
.fa-trail-rest{fill:none;stroke:var(--fa-faint);stroke-width:1.6;stroke-dasharray:1.5 5;stroke-linecap:round}
.fa-trail-approach{fill:none;stroke:var(--fa-blaze);stroke-width:2;stroke-dasharray:5 4;stroke-linecap:round;opacity:.85}
.fa-trail-walked{fill:none;stroke:var(--fa-blaze);stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}
.fa-draw{stroke-dasharray:1;stroke-dashoffset:0;animation:fa-draw 1100ms var(--hk-ease) both}
@keyframes fa-draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
.fa-wp{cursor:pointer;outline:none}
.fa-wp-hit{fill:transparent}
.fa-wp-dot{fill:var(--hk-surface);stroke:var(--fa-faint);stroke-width:1.5;stroke-dasharray:2 2}
.fa-wp[data-status=started] .fa-wp-dot{stroke:var(--fa-blaze);stroke-dasharray:none}
.fa-wp-half{fill:var(--fa-blaze)}
.fa-wp[data-status=passed] .fa-wp-dot{fill:var(--fa-blaze);stroke:var(--fa-blaze);stroke-dasharray:none}
.fa-wp-check{fill:none;stroke:var(--hk-surface);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.fa-wp:hover .fa-wp-dot{stroke:var(--fa-blaze);stroke-width:2}
.fa-wp:focus-visible .fa-wp-hit{stroke:var(--hk-accent);stroke-width:2}
.fa-start{fill:var(--hk-surface);stroke:var(--fa-blaze-ink);stroke-width:1.5}
.fa-marker{transition:transform 1100ms cubic-bezier(.33,.7,.2,1)}
.fa-marker-halo{fill:color-mix(in srgb,var(--fa-blaze) 20%,transparent)}
.fa-marker-ring{fill:var(--hk-surface);stroke:var(--fa-blaze);stroke-width:2.6}
.fa-marker-core{fill:var(--hk-ink)}
.fa-flag{cursor:pointer;outline:none}
.fa-flag-pole{stroke:var(--hk-ink);stroke-width:1.5;stroke-linecap:round}
.fa-flag-cloth{fill:var(--hk-surface);stroke:var(--fa-faint);stroke-width:1.4;stroke-linejoin:round}
.fa-flag[data-status=ready] .fa-flag-cloth{fill:color-mix(in srgb,var(--fa-blaze) 45%,var(--hk-surface));stroke:var(--fa-blaze)}
.fa-flag[data-status=issued] .fa-flag-cloth{fill:var(--fa-blaze);stroke:var(--fa-blaze)}
.fa-flag-cairn{fill:var(--fa-ground);stroke:var(--fa-faint);stroke-width:1}
.fa-flag:focus-visible .fa-wp-hit,.fa-flag:hover .fa-flag-cloth{stroke:var(--hk-accent)}

/* legend */
.fa-legend{display:flex;flex-wrap:wrap;align-items:center;gap:6px 16px;font-size:var(--hk-fs-sm)}
.fa-legend span{display:inline-flex;align-items:center;gap:6px}
.fa-legend svg{display:block;overflow:visible}

/* path: elevation profile */
.fa-profile{background:var(--fa-paper);border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);position:relative;overflow:hidden}
.fa-profile svg{display:block}
.fa-ridge{fill:var(--fa-ground)}
.fa-ridge-far{fill:var(--fa-ground-far)}
.fa-ridge-line{fill:none;stroke:color-mix(in srgb,var(--fa-blaze) 35%,transparent);stroke-width:1}
.fa-profile-label{font-size:12px;fill:var(--hk-ink);font-variant-caps:all-small-caps;letter-spacing:.07em;font-weight:600}
.fa-profile-foot{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:space-between;padding:10px 16px;border-top:1px dashed var(--hk-stroke)}

/* path: camps */
.fa-camps{display:grid;grid-template-columns:56px minmax(0,1fr);column-gap:10px}
.fa-camp{display:contents}
.fa-camp-rail{grid-column:1;display:flex;flex-direction:column;align-items:center;gap:4px;padding-top:6px}
.fa-camp-rail .fa-num{color:var(--hk-ink)}
.fa-camp[data-status=passed] .fa-camp-rail .fa-num,.fa-camp[data-current] .fa-camp-rail .fa-num{color:var(--fa-blaze-ink)}
.fa-camp-line{flex:1;width:6px;min-height:14px;overflow:visible}
.fa-camp-line line{stroke:var(--fa-faint);stroke-width:1.6;stroke-dasharray:1.5 5;stroke-linecap:round;vector-effect:non-scaling-stroke}
.fa-camp-line[data-walked] line{stroke:var(--fa-blaze);stroke-width:2.6;stroke-dasharray:none}
.fa-camp-body{grid-column:2;display:grid;gap:6px;padding:4px 0 18px;min-width:0}
.fa-camp-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.fa-camp-head .hk-h2{flex:1;min-width:0}
.fa-camp-rows{display:grid;border-top:1px solid var(--hk-stroke)}
.fa-camp-rows .hk-rowbtn{border-bottom:1px solid var(--hk-stroke);border-radius:0;padding:9px 8px}
.fa-mark{display:block;flex:none;overflow:visible}
.fa-row-meta{display:block;font-size:var(--hk-fs-sm)}
.fa-here-tag{font-size:var(--hk-fs-sm);display:inline-flex;align-items:center;gap:5px;color:var(--fa-blaze-ink);font-weight:600}

/* mission: field notes */
.fa-note-head{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:end}
.fa-strip{display:grid;grid-template-columns:auto minmax(0,1fr);gap:16px;align-items:center;padding:12px 16px;background:var(--fa-paper);border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);position:relative;overflow:hidden}
.fa-strip-steps{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(var(--fa-n,4),minmax(0,1fr));gap:6px}
.fa-strip-step{display:grid;grid-template-columns:auto minmax(0,1fr);gap:2px 8px;align-items:baseline;width:100%;padding:6px 8px;border:0;border-radius:var(--hk-radius-sm);background:transparent;color:inherit;font:inherit;text-align:left;cursor:pointer;
  border-top:2px solid var(--hk-stroke);transition:background-color var(--hk-dur) var(--hk-ease),border-color var(--hk-dur) var(--hk-ease)}
.fa-strip-step:hover{background:var(--hk-hover)}
.fa-strip-step:focus-visible{outline:2px solid var(--hk-accent);outline-offset:1px}
.fa-strip-step[data-state=done]{border-top-color:var(--fa-blaze)}
.fa-strip-step[data-state=now]{border-top-color:var(--fa-blaze);background:color-mix(in srgb,var(--fa-blaze) 9%,transparent)}
.fa-strip-step .fa-num{grid-row:span 2}
.fa-strip-state{font-size:var(--hk-fs-sm)}
.fa-strip-step .fa-sc{font-size:12px;letter-spacing:.05em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@container (max-width:640px){.fa-strip{grid-template-columns:1fr}.fa-strip-steps{grid-template-columns:repeat(2,minmax(0,1fr))}}
.fa-compass{display:block;flex:none;overflow:visible}
.fa-compass-face{fill:var(--hk-surface);stroke:var(--hk-stroke-strong);stroke-width:1}
.fa-compass-arc{fill:none;stroke:var(--fa-faint);stroke-width:4;stroke-linecap:butt}
.fa-compass-arc[data-state=done]{stroke:var(--fa-blaze)}
.fa-compass-arc[data-state=now]{stroke:color-mix(in srgb,var(--fa-blaze) 45%,transparent)}
.fa-compass-tick{stroke:var(--hk-stroke-strong);stroke-width:1}
.fa-needle{transition:transform 900ms cubic-bezier(.33,.7,.2,1)}
.fa-needle-n{fill:var(--fa-blaze)}
.fa-needle-s{fill:var(--fa-faint)}
.fa-needle-hub{fill:var(--hk-surface);stroke:var(--hk-ink);stroke-width:1.2}
.fa-notes{list-style:none;margin:0;padding:0;display:grid}
.fa-note{display:grid;grid-template-columns:52px minmax(0,1fr);gap:12px;padding:18px 0 20px;border-top:1px solid var(--hk-stroke);scroll-margin-top:16px}
.fa-note:last-child{border-bottom:1px solid var(--hk-stroke)}
.fa-note-num{padding-top:2px;text-align:center}
.fa-note[data-done] .fa-note-num{color:var(--fa-blaze-ink)}
.fa-note-body{display:grid;gap:10px;min-width:0}
.fa-note-kind{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.fa-note-text{max-width:66ch;line-height:1.65}
.fa-done-tag{display:inline-flex;align-items:center;gap:4px;font-size:var(--hk-fs-sm);font-weight:600;color:var(--fa-blaze-ink)}
.fa-outcome{border-left:3px solid var(--fa-blaze);padding:2px 0 2px 12px;display:grid;gap:3px;max-width:70ch}

/* field record */
.fa-cert{position:relative;background:var(--fa-paper);border:1px solid var(--hk-stroke-strong);border-radius:2px;padding:7px}
.fa-cert-inner{position:relative;border:1px solid color-mix(in srgb,var(--fa-blaze) 55%,transparent);outline:1px solid color-mix(in srgb,var(--fa-blaze) 22%,transparent);outline-offset:-5px;padding:34px 40px 28px;display:grid;gap:14px;overflow:hidden}
.fa-cert-corner{position:absolute;width:30px;height:30px;color:var(--fa-blaze-ink);pointer-events:none}
.fa-cert-corner path{fill:none;stroke:currentColor;stroke-width:1.2}
.fa-cert-top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;position:relative}
.fa-cert-centre{display:grid;justify-items:center;text-align:center;gap:8px;position:relative;padding:4px 0 6px}
.fa-cert-name{font-size:34px;font-weight:300;letter-spacing:-.01em;line-height:1.15;margin:0;padding:0 24px 8px;border-bottom:1px solid color-mix(in srgb,var(--fa-blaze) 55%,transparent)}
.fa-cert-path{font-size:var(--hk-fs-h1);font-weight:600;line-height:1.25;margin:0}
.fa-cert-promise{max-width:56ch}
.fa-cert-foot{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;align-items:end;position:relative;border-top:1px dashed var(--hk-stroke);padding-top:14px}
@container (max-width:640px){.fa-cert-foot{grid-template-columns:1fr}.fa-cert-inner{padding:24px 18px}}
.fa-cert-number{font-family:var(--hk-mono);font-size:15px;letter-spacing:.06em}
.fa-cert-issuer{max-width:60ch}
.fa-seal{display:block;color:var(--fa-blaze-ink)}
.fa-seal-rim{fill:color-mix(in srgb,var(--fa-blaze) 13%,var(--hk-surface));stroke:var(--fa-blaze);stroke-width:1}
.fa-seal-ring{fill:none;stroke:var(--fa-blaze);stroke-width:1}
.fa-seal-text{font-size:9.5px;fill:var(--hk-ink);font-variant-caps:all-small-caps;letter-spacing:.16em;font-weight:600}
.fa-seal-mark{fill:none;stroke:var(--fa-blaze-ink);stroke-width:1.5;stroke-linejoin:round;stroke-linecap:round}
.fa-seal-flag{fill:var(--fa-blaze)}
.fa-cert .fa-contours{opacity:.7}

@media (prefers-reduced-motion:reduce){.fa-draw{animation:none !important}.fa-marker,.fa-needle{transition:none !important}}
`

/* --------------------------------------------------------------- motion -- */

/**
 * [ref, width] for an element. Measures once the moment the element attaches, then
 * follows it with a ResizeObserver, so the map draws on its first frame instead of
 * waiting for the observer's first report.
 */
function useWidth() {
  const [width, setWidth] = useState(0)
  const observer = useRef(null)
  const ref = useCallback(el => {
    if (observer.current) { observer.current.disconnect(); observer.current = null }
    if (!el) return
    const measure = w => setWidth(prev => (prev === w ? prev : w))
    measure(Math.round(el.getBoundingClientRect().width))
    if (typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(entries => {
      const box = entries[0] && entries[0].contentRect
      if (box) measure(Math.round(box.width))
    })
    ro.observe(el)
    observer.current = ro
  }, [])
  return [ref, width]
}

/** Marker positions each view has already shown, so a pass that happened elsewhere animates once on return. */
const seen = new Map()

/**
 * Where the marker should start and end on this mount. The first time a view sees a
 * path it simply shows the marker; when the marker has moved on since (a mission
 * passed), the newly walked stretch draws itself and the marker eases forward.
 */
function useTrailMotion(key, marker) {
  const reduced = useReducedMotion()
  const [from] = useState(() => {
    const prev = seen.get(key)
    return prev !== undefined && prev < marker && !reduced ? prev : marker
  })
  const [shown, setShown] = useState(from)
  useEffect(() => {
    seen.set(key, marker)
    if (shown === marker) return undefined
    const t = setTimeout(() => setShown(marker), 80)
    return () => clearTimeout(t)
  }, [key, marker])
  return { from, shown }
}

function openOnKey(open) {
  return e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      e.stopPropagation()
      open()
    }
  }
}

const STATUS_WORDS = { passed: 'passed', started: 'started', waiting: 'not started yet' }

/* ---------------------------------------------------------------- marks -- */

/** One waypoint, drawn at the origin; place it with a transform. */
function WaypointMark({ status, r = 5.5 }) {
  return [
    jsx('circle', { className: 'fa-wp-dot', r }, 'dot'),
    status === 'started' ? jsx('path', { className: 'fa-wp-half', d: `M0 ${-r} A${r} ${r} 0 0 0 0 ${r} Z` }, 'half') : null,
    status === 'passed' ? jsx('path', { className: 'fa-wp-check', d: `M${-r * 0.45} ${r * 0.02} L${-r * 0.1} ${r * 0.36} L${r * 0.5} ${-r * 0.32}` }, 'check') : null,
  ]
}

function Waypoint({ stop, onOpen }) {
  const w = stop.point
  return jsxs('g', {
    className: 'fa-wp', 'data-status': w.status, transform: `translate(${stop.x} ${stop.y})`,
    role: 'button', tabIndex: 0, 'aria-label': `${w.title}, ${STATUS_WORDS[w.status]}`,
    onClick: e => { e.stopPropagation(); onOpen(w.id) }, onKeyDown: openOnKey(() => onOpen(w.id)),
    children: [jsx('title', { children: w.title }), jsx('circle', { className: 'fa-wp-hit', r: 12 }), ...WaypointMark({ status: w.status })],
  })
}

/** The bright "you are here" marker. */
function Marker({ x, y }) {
  return jsxs('g', { className: 'fa-marker', style: { transform: `translate(${x}px, ${y}px)` }, 'aria-hidden': 'true', children: [
    jsx('circle', { className: 'fa-marker-halo', r: 14 }),
    jsx('circle', { className: 'fa-marker-ring', r: 8 }),
    jsx('circle', { className: 'fa-marker-core', r: 3 }),
  ] })
}

const FLAG_WORDS = { issued: 'Field Record created', ready: 'Field Record ready to create', in_progress: 'Field Record' }

function SummitFlag({ stop, status, onOpen, scale = 1 }) {
  const s = scale
  return jsxs('g', {
    className: 'fa-flag', 'data-status': status, transform: `translate(${stop.x} ${stop.y})`,
    role: 'button', tabIndex: 0, 'aria-label': FLAG_WORDS[status] || 'Field Record',
    onClick: e => { e.stopPropagation(); onOpen() }, onKeyDown: openOnKey(onOpen),
    children: [
      jsx('title', { children: FLAG_WORDS[status] || 'Field Record' }),
      jsx('circle', { className: 'fa-wp-hit', cy: -10 * s, r: 16 * s }),
      jsx('path', { className: 'fa-flag-cairn', d: `M${-8 * s} ${4 * s} L${-4 * s} ${-1 * s} L${4 * s} ${-1 * s} L${8 * s} ${4 * s} Z` }),
      jsx('line', { className: 'fa-flag-pole', x1: 0, y1: 0, x2: 0, y2: -26 * s }),
      jsx('path', { className: 'fa-flag-cloth', d: `M0 ${-26 * s} L${16 * s} ${-21 * s} L0 ${-15 * s} Z` }),
    ],
  })
}

/** A small status mark for HTML rows and the legend, the same shapes as on the map. */
export function TrailMark({ status, here = false, size = 16 }) {
  const c = size / 2
  return jsx('svg', { className: 'fa-mark', width: size, height: size, viewBox: `${-c} ${-c} ${size} ${size}`, 'aria-hidden': 'true', children: here
    ? [jsx('circle', { className: 'fa-marker-ring', r: c * 0.62, strokeWidth: 2 }, 'r'), jsx('circle', { className: 'fa-marker-core', r: c * 0.24 }, 'c')]
    : jsx('g', { className: 'fa-wp', 'data-status': status, children: WaypointMark({ status, r: c * 0.62 }) }) })
}

export function Legend() {
  return jsxs('div', { className: 'fa-legend', 'aria-label': 'What the marks mean', children: [
    jsxs('span', { children: [jsx(TrailMark, { here: true }), 'You are here'] }),
    jsxs('span', { children: [jsx(TrailMark, { status: 'passed' }), 'Passed'] }),
    jsxs('span', { children: [jsx(TrailMark, { status: 'started' }), 'Started'] }),
    jsxs('span', { children: [jsx(TrailMark, { status: 'waiting' }), 'Ahead'] }),
    jsxs('span', { children: [
      jsx('svg', { width: 14, height: 16, viewBox: '-3 -14 14 16', 'aria-hidden': 'true', children: jsxs('g', { className: 'fa-flag', 'data-status': 'issued', children: [
        jsx('line', { className: 'fa-flag-pole', x1: 0, y1: 1, x2: 0, y2: -13 }),
        jsx('path', { className: 'fa-flag-cloth', d: 'M0 -13 L9 -10 L0 -7 Z' }),
      ] }) }),
      'Field Record',
    ] }),
  ] })
}

/* ------------------------------------------------------------- contours -- */

export function Contours({ width, height, seed = 0 }) {
  if (!width || !height) return null
  return jsx('svg', { className: 'fa-contours', viewBox: `0 0 ${width} ${height}`, preserveAspectRatio: 'none', 'aria-hidden': 'true',
    children: contourPaths(width, height, seed).map((line, i) => jsx('path', { d: line.d, 'data-index': line.index ? '' : undefined }, i)) })
}

/* ------------------------------------------------------------ the map -- */

/**
 * The trail's three strokes. Walked: solid blaze up to the last stop behind you.
 * Approach: dashed blaze from there to the marker, the stretch you're on now.
 * Ahead: faint dots to the summit. A stretch walked since this view last looked
 * draws itself once.
 */
function trailLines(model, stops, segs, from) {
  const last = stops.length - 1
  const behind = m => (m <= 0 ? 0 : m >= last && model.summit.status === 'issued' ? last : m - 1)
  const was = behind(from)
  const now = behind(model.marker)
  return [
    jsx('path', { className: 'fa-trail-rest', d: pathBetween(stops, segs, model.marker, last) }, 'rest'),
    jsx('path', { className: 'fa-trail-approach', d: pathBetween(stops, segs, now, model.marker) }, 'approach'),
    jsx('path', { className: 'fa-trail-walked', d: pathBetween(stops, segs, 0, was) }, 'walked'),
    now > was ? jsx('path', { className: 'fa-trail-walked fa-draw', pathLength: 1, d: pathBetween(stops, segs, was, now) }, 'draw') : null,
  ]
}

const ROW = 138

function TrailRow({ model, layout, y, active, onOpenMission, onOpenTrack }) {
  const { stops, segs } = layout
  const motion = useTrailMotion(`map:${model.id}`, model.marker)
  const at = stops[Math.min(motion.shown, stops.length - 1)]
  return jsxs('g', { transform: `translate(0 ${y})`, children: [
    jsx('rect', { className: 'fa-band', 'data-active': active ? '' : undefined, x: 0, y: 0, width: layout.width, height: layout.height }),
    ...trailLines(model, stops, segs, motion.from),
    jsx('circle', { className: 'fa-start', cx: stops[0].x, cy: stops[0].y, r: 3.5 }),
    ...stops.filter(s => s.kind === 'waypoint').map(stop => jsx(Waypoint, { stop, onOpen: onOpenMission }, stop.point.id)),
    jsx(SummitFlag, { stop: stops[stops.length - 1], status: model.summit.status, onOpen: () => onOpenTrack(model.id) }),
    model.total ? jsx(Marker, { x: at.x, y: at.y }) : null,
  ] })
}

function trailCertWords(model) {
  if (model.summit.status === 'issued') return 'Field Record created'
  if (model.summit.status === 'ready') return 'Field Record ready to create'
  if (model.summit.words) return model.summit.words
  const unit = model.unit === 'parts' ? (model.summit.remaining === 1 ? 'part' : 'parts') : (model.summit.remaining === 1 ? 'mission' : 'missions')
  return `${model.summit.remaining} ${unit} to the Field Record`
}

/**
 * The topographic map: one trail per path, camps in columns, the Field Record as a
 * summit flag. Trail labels are the keyboard list (j/k, Enter opens the path);
 * waypoints and flags are buttons too.
 */
export function TrailMap({ models, list, onOpenTrack, onOpenMission, foot }) {
  const [ref, width] = useWidth()
  const camps = models[0] ? models[0].camps : []
  const height = models.length * ROW
  const layouts = width ? models.map((m, i) => layoutRow(m, width, ROW, i)) : []
  const columns = layouts[0] ? layouts[0].columns : null
  const [boxRef, box] = useWidth()
  return jsxs('div', { className: 'fa-map', ref: boxRef, children: [
    jsx(Contours, { width: box, height: height + 34 + 52, seed: models.length }),
    jsxs('div', { className: 'fa-map-grid', children: [
      jsx('div', { className: 'fa-map-corner fa-sc', children: 'Trail' }),
      jsx('div', { className: 'fa-map-head', ref, children: columns
        ? [
            ...camps.map((camp, i) => {
              const col = columns.camps[Math.min(i, columns.camps.length - 1)]
              return jsx('span', { className: 'fa-sc', style: { left: (col.x0 + col.x1) / 2 }, children: col.x1 - col.x0 < 150 ? (camp.short || camp.name) : `${camp.short || camp.name} camp` }, camp.id)
            }),
            jsx('span', { className: 'fa-sc', style: { left: 'auto', right: 8, transform: 'none' }, children: 'Summit' }, 'summit'),
          ]
        : null }),
      ...models.map((model, i) => jsxs('button', {
        type: 'button', className: 'fa-trail-label', style: { gridRow: i + 2, height: ROW },
        onClick: () => onOpenTrack(model.id), ...list.itemProps(i),
        children: [
          model.eyebrow ? jsx('span', { className: 'fa-sc fa-sc-blaze', children: model.eyebrow }) : null,
          jsxs('span', { className: 'fa-trail-top', children: [
            jsx('span', { className: 'fa-trail-name', children: model.name }),
            jsxs('span', { className: 'fa-num fa-num-m', children: [model.passed, jsx('small', { children: `of ${model.total}` })] }),
          ] }),
          model.promise ? jsx('span', { className: 'fa-trail-promise', title: model.promise, children: model.promise }) : null,
          jsx('span', { className: 'fa-trail-cert', children: trailCertWords(model) }),
        ],
      }, model.id)),
      width
        ? jsxs('svg', {
            className: 'fa-map-svg', width, height, viewBox: `0 0 ${width} ${height}`, style: { gridRow: `2 / span ${models.length}` },
            role: 'group', 'aria-label': 'Trail map of your paths',
            children: [
              ...(columns ? [...columns.camps.slice(1).map(c => c.x0), columns.camps[columns.camps.length - 1].x1 + 8]
                .map((x, i) => jsx('line', { className: 'fa-divider', x1: x, x2: x, y1: 0, y2: height }, `d${i}`)) : []),
              ...models.map((model, i) => jsx(TrailRow, {
                model, layout: layouts[i], y: i * ROW, active: list.index === i, onOpenMission, onOpenTrack,
              }, model.id)),
            ],
          })
        : jsx('div', { style: { gridColumn: 2, gridRow: `2 / span ${models.length}`, height } }),
    ] }),
    foot ? jsx('div', { className: 'fa-map-foot', children: foot }) : null,
  ] })
}

/* ------------------------------------------------------- where you are -- */

/** Progress as a bezel of ticks, one per mission, lit as each one passes. */
export function Bezel({ passed, total, size = 108, children }) {
  const c = size / 2
  return jsxs('span', { className: 'fa-bezel', style: { width: size, height: size }, role: 'img', 'aria-label': `${passed} of ${total} missions passed`, children: [
    jsxs('svg', { width: size, height: size, viewBox: `0 0 ${size} ${size}`, 'aria-hidden': 'true', children: [
      jsx('circle', { className: 'fa-bezel-track', cx: c, cy: c, r: c - Math.max(10, size * 0.12) }),
      total > 0 && passed > 0
        ? jsx('circle', { className: 'fa-bezel-arc', cx: c, cy: c, r: c - Math.max(10, size * 0.12), pathLength: 100,
            strokeDasharray: `${Math.min(100, (passed / total) * 100).toFixed(2)} 100`, transform: `rotate(-90 ${c} ${c})` })
        : null,
      ...(total >= 6 ? bezelTicks(passed, total, size) : []).map((t, i) => jsx('line', { className: 'fa-tick', 'data-lit': t.lit ? '' : undefined, x1: t.x1, y1: t.y1, x2: t.x2, y2: t.y2 }, i)),
    ] }),
    jsx('span', { className: 'fa-bezel-mid', 'aria-hidden': 'true', children }),
  ] })
}

/* --------------------------------------------------------- path profile -- */

export function ElevationProfile({ model, onOpenMission, onOpenSummit, children }) {
  const [ref, width] = useWidth()
  const height = 216
  const layout = width ? layoutProfile(model, width, height) : null
  const motion = useTrailMotion(`path:${model.id}`, model.marker)
  if (!layout) return jsx('div', { className: 'fa-profile', ref, style: { height: height + 44 } })
  const { stops, segs } = layout
  const at = stops[Math.min(motion.shown, stops.length - 1)]
  return jsxs('div', { className: 'fa-profile', ref, children: [
    jsxs('svg', { width, height, viewBox: `0 0 ${width} ${height}`, role: 'group', 'aria-label': `${model.name} trail, from the trailhead to the Field Record`, children: [
      jsx('path', { className: 'fa-ridge-far', d: layout.farRidge }),
      jsx('g', { className: 'fa-contours', children: contourPaths(width, height, 3).map((line, i) => jsx('path', { d: line.d, 'data-index': line.index ? '' : undefined }, i)) }),
      jsx('path', { className: 'fa-ridge', d: layout.ridge }),
      jsx('path', { className: 'fa-ridge-line', d: pathBetween(stops, segs, 0, stops.length - 1), transform: 'translate(0 7)' }),
      ...layout.columns.camps.slice(1).map((c, i) => jsx('line', { className: 'fa-divider', x1: c.x0, x2: c.x0, y1: 10, y2: height - 22 }, `d${i}`)),
      ...model.camps.map((camp, i) => {
        const col = layout.columns.camps[Math.min(i, layout.columns.camps.length - 1)]
        return jsx('text', { className: 'fa-profile-label', x: (col.x0 + col.x1) / 2, y: height - 9, textAnchor: 'middle', children: `Camp ${camp.number} · ${camp.short || camp.name}` }, camp.id)
      }),
      ...trailLines(model, stops, segs, motion.from),
      jsx('circle', { className: 'fa-start', cx: stops[0].x, cy: stops[0].y, r: 4 }),
      ...stops.filter(s => s.kind === 'waypoint').map(stop => jsx(Waypoint, { stop, onOpen: onOpenMission }, stop.point.id)),
      jsx(SummitFlag, { stop: stops[stops.length - 1], status: model.summit.status, onOpen: onOpenSummit, scale: 1.2 }),
      model.total ? jsx(Marker, { x: at.x, y: at.y }) : null,
    ] }),
    children ? jsx('div', { className: 'fa-profile-foot', children }) : null,
  ] })
}

/** The rail beside a camp: dashed ahead, solid blaze once the camp is passed. */
export function CampLine({ walked }) {
  return jsx('svg', { className: 'fa-camp-line', 'data-walked': walked ? '' : undefined, viewBox: '0 0 6 100', preserveAspectRatio: 'none', 'aria-hidden': 'true',
    children: jsx('line', { x1: 3, x2: 3, y1: 0, y2: 100 }) })
}

/* ------------------------------------------------------- mission compass -- */

const POINTS = ['N', 'E', 'S', 'W']

/** A compass with one quarter per step. The needle points at the step you're on. */
export function Compass({ steps, size = 76 }) {
  const reading = compassReading(steps)
  const c = size / 2
  const r = c - 4
  const n = Math.max(1, reading.total)
  const arc = i => {
    const gap = 0.12
    const a0 = (i / n) * Math.PI * 2 - Math.PI / 2 - Math.PI / n + gap
    const a1 = ((i + 1) / n) * Math.PI * 2 - Math.PI / 2 - Math.PI / n - gap
    return `M${(c + Math.cos(a0) * r).toFixed(1)} ${(c + Math.sin(a0) * r).toFixed(1)} A${r} ${r} 0 0 1 ${(c + Math.cos(a1) * r).toFixed(1)} ${(c + Math.sin(a1) * r).toFixed(1)}`
  }
  const label = reading.complete ? 'Every step done' : `On step ${reading.at + 1} of ${reading.total}`
  return jsxs('svg', { className: 'fa-compass', width: size, height: size, viewBox: `0 0 ${size} ${size}`, role: 'img', 'aria-label': label, children: [
    jsx('circle', { className: 'fa-compass-face', cx: c, cy: c, r: r - 6 }),
    ...(steps || []).map((s, i) => jsx('path', { className: 'fa-compass-arc', d: arc(i),
      'data-state': s.status === 'done' ? 'done' : i === reading.at ? 'now' : 'later' }, `a${i}`)),
    ...POINTS.map((_, i) => {
      const a = (i / 4) * Math.PI * 2 - Math.PI / 2
      return jsx('line', { className: 'fa-compass-tick', x1: c + Math.cos(a) * (r - 6), y1: c + Math.sin(a) * (r - 6), x2: c + Math.cos(a) * (r - 11), y2: c + Math.sin(a) * (r - 11) }, `t${i}`)
    }),
    jsxs('g', { className: 'fa-needle', style: { transform: `rotate(${reading.angle}deg)`, transformOrigin: `${c}px ${c}px` }, children: [
      jsx('path', { className: 'fa-needle-n', d: `M${c} ${c - r + 12} L${c + 5} ${c} L${c - 5} ${c} Z` }),
      jsx('path', { className: 'fa-needle-s', d: `M${c} ${c + r - 12} L${c + 5} ${c} L${c - 5} ${c} Z` }),
    ] }),
    jsx('circle', { className: 'fa-needle-hub', cx: c, cy: c, r: 3.2 }),
  ] })
}

/* -------------------------------------------------------- field record -- */

const CORNER = 'M1 29 L1 9 Q1 1 9 1 L29 1 M6 29 L6 12 Q6 6 12 6 L29 6 M1 1 L6 6'

export function CertCorners() {
  const at = [
    { top: 6, left: 6, rotate: 0 }, { top: 6, right: 6, rotate: 90 },
    { bottom: 6, right: 6, rotate: 180 }, { bottom: 6, left: 6, rotate: 270 },
  ]
  return at.map(({ rotate, ...pos }, i) => jsx('svg', { className: 'fa-cert-corner', viewBox: '0 0 30 30', style: { ...pos, transform: `rotate(${rotate}deg)` }, 'aria-hidden': 'true',
    children: jsx('path', { d: CORNER }) }, i))
}

/** The Field Academy mark: two plain rings, its name around the edge, a peak and a flag inside. A maker's mark, not a seal of approval. */
export function Seal({ size = 128, idSuffix = '' }) {
  const c = size / 2
  const textR = c - 21
  const id = `fa-seal-arc${idSuffix}`
  return jsxs('svg', { className: 'fa-seal', width: size, height: size, viewBox: `0 0 ${size} ${size}`, role: 'img', 'aria-label': 'Field Academy mark', children: [
    jsx('circle', { className: 'fa-seal-rim', cx: c, cy: c, r: c - 2 }),
    jsx('circle', { className: 'fa-seal-ring', cx: c, cy: c, r: c - 9 }),
    jsx('circle', { className: 'fa-seal-ring', cx: c, cy: c, r: c - 30 }),
    jsx('defs', { children: jsx('path', { id, d: `M${c - textR} ${c} A${textR} ${textR} 0 1 1 ${c + textR} ${c} A${textR} ${textR} 0 1 1 ${c - textR} ${c}` }) }),
    jsx('text', { className: 'fa-seal-text', children: jsx('textPath', { href: `#${id}`, startOffset: '0', textLength: (2 * Math.PI * textR - 6).toFixed(1), lengthAdjust: 'spacing', children: 'Field Academy · self-issued field record · ' }) }),
    jsx('path', { className: 'fa-seal-mark', d: `M${c - 20} ${c + 12} L${c - 7} ${c - 6} L${c - 1} ${c + 2} L${c + 7} ${c - 12} L${c + 20} ${c + 12} Z` }),
    jsx('line', { className: 'fa-seal-mark', x1: c + 7, y1: c - 12, x2: c + 7, y2: c - 22 }),
    jsx('path', { className: 'fa-seal-flag', d: `M${c + 7} ${c - 22} L${c + 15} ${c - 19.5} L${c + 7} ${c - 17} Z` }),
  ] })
}
