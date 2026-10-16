// Field Academy trail geometry. Pure functions, no imports, so node tests can run them
// against every passport the real backend produces (tests/trail_map.test.mjs).
//
// The page draws each path as a trail: a trailhead, one waypoint per mission grouped
// into camps (Beginner, Intermediate, Advanced), and a summit flag for the Field Record.
// Everything here is defensive about the passport's shape: a missing field once blanked
// a page in real Hermes, so a gap becomes a sensible default and never an exception.

/** The passport fields the map reads. The node test asserts the real backend sends each one. */
export const MAP_FIELDS = {
  passport: ['goal', 'reviews', 'changes', 'new_missions', 'honest', 'next_up'],
  track: ['id', 'name', 'eyebrow', 'promise', 'missions', 'levels', 'here', 'verified_missions', 'certificate', 'placement'],
  level: ['id', 'number', 'name', 'meaning', 'missions', 'passed', 'total', 'status', 'current'],
  mission: ['id', 'title', 'status', 'level', 'level_name', 'minutes', 'completed_steps', 'total_steps', 'version', 'use_text', 'strength', 'changed', 'time'],
  step: ['id', 'kind', 'title', 'status'],
  certificate: ['status', 'remaining'],
}

const str = (value, fallback = '') => (typeof value === 'string' && value.trim() ? value : fallback)
const num = (value, fallback = 0) => (typeof value === 'number' && Number.isFinite(value) ? value : fallback)
const obj = value => (value && typeof value === 'object' && !Array.isArray(value) ? value : {})
const arr = value => (Array.isArray(value) ? value : [])
const round = n => Math.round(n * 10) / 10

function waypointStatus(status) {
  if (status === 'verified') return 'passed'
  if (status === 'not_started' || !status) return 'waiting'
  return 'started'
}

/**
 * One track as a trail: camps in order, each with its waypoints, plus where the marker
 * stands. Stops are numbered 0 (trailhead), 1..n (waypoints), n+1 (summit).
 */
export function trailModel(track) {
  const t = obj(track)
  const missions = arr(t.missions).filter(m => m && typeof m === 'object' && str(m.id))
  const byId = new Map(missions.map(m => [m.id, m]))
  const placed = new Set()
  const camps = arr(t.levels).filter(l => l && typeof l === 'object').map((level, i) => {
    const ids = arr(level.missions).filter(id => byId.has(id) && !placed.has(id))
    ids.forEach(id => placed.add(id))
    return {
      id: str(level.id, `camp-${i + 1}`),
      number: num(level.number, i + 1),
      name: str(level.name, `Level ${i + 1}`),
      short: str(level.short_name),
      meaning: str(level.meaning),
      status: str(level.status, 'not_started'),
      current: level.current === true,
      ids,
    }
  })
  // A mission no level lists still goes on the trail: in the camp its own level names, else the last one.
  for (const m of missions) {
    if (placed.has(m.id)) continue
    let camp = camps.find(c => c.id === m.level)
    if (!camp) {
      if (!camps.length) camps.push({ id: 'camp-1', number: 1, name: str(m.level_name, 'Level 1'), meaning: '', status: 'not_started', current: false, ids: [] })
      camp = camps[camps.length - 1]
    }
    camp.ids.push(m.id)
    placed.add(m.id)
  }

  const here = str(t.here)
  const waypoints = []
  for (const [ci, camp] of camps.entries()) {
    camp.waypoints = camp.ids.map(id => {
      const m = byId.get(id)
      const status = waypointStatus(m.status)
      const point = {
        id,
        title: str(m.title, 'Untitled mission'),
        status,
        passed: status === 'passed',
        here: id === here,
        minutes: num(m.minutes, 0),
        camp: ci,
        index: waypoints.length,
      }
      waypoints.push(point)
      return point
    })
    camp.passed = camp.waypoints.filter(w => w.passed).length
    camp.total = camp.waypoints.length
    delete camp.ids
  }

  const passed = waypoints.filter(w => w.passed).length
  const hereIndex = waypoints.findIndex(w => w.here)
  const allPassed = waypoints.length > 0 && passed === waypoints.length
  const marker = hereIndex >= 0 ? hereIndex + 1 : allPassed ? waypoints.length + 1 : 0
  const cert = obj(t.certificate)
  const status = cert.status === 'issued' || cert.status === 'ready' ? cert.status : 'in_progress'
  return {
    id: str(t.id, 'path'),
    name: str(t.name, 'Path'),
    eyebrow: str(t.eyebrow),
    promise: str(t.promise),
    unit: str(t.unit, 'missions'),
    camps,
    waypoints,
    passed,
    total: waypoints.length,
    marker,
    currentCamp: camps.findIndex(c => c.current),
    summit: { status, remaining: num(cert.remaining, waypoints.length - passed), words: str(cert.words) },
  }
}

/** The whole passport at a glance: every path as a trail, and totals with each mission counted once. */
export function overview(passport) {
  const p = obj(passport)
  const tracks = arr(p.tracks).map(trailModel)
  const seen = new Map()
  for (const track of tracks) for (const w of track.waypoints) seen.set(w.id, seen.get(w.id) || w.passed)
  const goal = tracks.find(t => t.id === p.goal_track) || tracks.find(t => t.id === obj(p.next_up).track_id) || null
  return {
    tracks,
    total: seen.size,
    passed: [...seen.values()].filter(Boolean).length,
    certificates: tracks.filter(t => t.summit.status === 'issued').length,
    goal,
    camp: goal && goal.currentCamp >= 0 ? goal.camps[goal.currentCamp] : null,
  }
}

/* ------------------------------------------------------------------ curves -- */

/** Catmull-Rom through points, as cubic segments: segment i joins point i to point i+1. */
export function curveSegments(points) {
  const segs = []
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] || points[i]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = points[i + 2] || p2
    const c1x = p1.x + (p2.x - p0.x) / 6
    const c1y = p1.y + (p2.y - p0.y) / 6
    const c2x = p2.x - (p3.x - p1.x) / 6
    const c2y = p2.y - (p3.y - p1.y) / 6
    segs.push(`C${round(c1x)} ${round(c1y)} ${round(c2x)} ${round(c2y)} ${round(p2.x)} ${round(p2.y)}`)
  }
  return segs
}

/** The part of a curve from stop a to stop b, as a path. Empty when there is nothing to draw. */
export function pathBetween(points, segs, a, b) {
  const from = Math.max(0, Math.min(a, points.length - 1))
  const to = Math.max(0, Math.min(b, points.length - 1))
  if (to <= from) return ''
  return `M${round(points[from].x)} ${round(points[from].y)} ${segs.slice(from, to).join(' ')}`
}

/** A closed smooth loop through points. */
function closedLoop(points) {
  const n = points.length
  let d = `M${round(points[0].x)} ${round(points[0].y)}`
  for (let i = 0; i < n; i++) {
    const p0 = points[(i - 1 + n) % n]
    const p1 = points[i]
    const p2 = points[(i + 1) % n]
    const p3 = points[(i + 2) % n]
    d += ` C${round(p1.x + (p2.x - p0.x) / 6)} ${round(p1.y + (p2.y - p0.y) / 6)} ${round(p2.x - (p3.x - p1.x) / 6)} ${round(p2.y - (p3.y - p1.y) / 6)} ${round(p2.x)} ${round(p2.y)}`
  }
  return `${d} Z`
}

/* ----------------------------------------------------------------- layouts -- */

/** Where each camp sits across a strip `width` wide, shared by every row so the camps line up. */
export function campColumns(count, width) {
  const n = Math.max(1, count)
  const left = 30
  const summit = Math.max(left + 60, width - 34)
  const right = summit - 22
  const span = Math.max(1, right - left)
  return {
    camps: Array.from({ length: n }, (_, i) => ({ x0: left + (span * i) / n, x1: left + (span * (i + 1)) / n })),
    trailhead: 12,
    summit,
  }
}

function stopsFor(model, columns, yAt) {
  const stops = [{ kind: 'start', x: columns.trailhead, y: yAt(0, 0) }]
  model.camps.forEach((camp, ci) => {
    const col = columns.camps[Math.min(ci, columns.camps.length - 1)]
    const n = camp.waypoints.length
    camp.waypoints.forEach((w, k) => {
      const x = col.x0 + ((col.x1 - col.x0) * (k + 0.5)) / Math.max(1, n)
      stops.push({ kind: 'waypoint', x, y: yAt(stops.length, x), point: w })
    })
  })
  stops.push({ kind: 'summit', x: columns.summit, y: yAt(stops.length, columns.summit) })
  return stops
}

/**
 * One trail across a map row `width` by `height`. The trail meanders around the row's
 * middle; `seed` keeps each path's wander its own and the same on every render.
 */
export function layoutRow(model, width, height, seed = 0) {
  const w = Math.max(160, num(width, 600))
  const h = Math.max(48, num(height, 96))
  const columns = campColumns(model.camps.length, w)
  const mid = h / 2 + 4
  const swing = h * 0.2
  const stops = stopsFor(model, columns, i => mid + swing * Math.sin(i * 1.9 + seed * 1.3 + 0.6))
  stops[stops.length - 1].y = mid - swing * 0.35
  return { width: w, height: h, columns, stops, segs: curveSegments(stops) }
}

/**
 * One path as an elevation profile: the trail climbs from the trailhead at lower left
 * to the summit at upper right, camp by camp. Returns the ridge outline too.
 */
export function layoutProfile(model, width, height) {
  const w = Math.max(200, num(width, 700))
  const h = Math.max(100, num(height, 180))
  const columns = campColumns(model.camps.length, w)
  const base = h - 34
  const top = 52
  const last = model.waypoints.length + 1
  const stops = stopsFor(model, columns, (i, x) => {
    const t = Math.min(1, Math.max(0, (x - columns.trailhead) / (columns.summit - columns.trailhead)))
    return base - (base - top) * Math.pow(t, 1.35) + (i > 0 && i < last ? 6 * Math.sin(i * 2.3) : 0)
  })
  stops[stops.length - 1].y = top
  const segs = curveSegments(stops)
  const ridge = `${pathBetween(stops, segs, 0, stops.length - 1)} L${w} ${round(top + 6)} L${w} ${h} L0 ${h} L0 ${round(stops[0].y)} L${round(stops[0].x)} ${round(stops[0].y)} Z`
  const far = [{ x: 0, y: base - 14 }, { x: w * 0.22, y: base - 52 }, { x: w * 0.42, y: base - 30 }, { x: w * 0.66, y: top - 6 }, { x: w * 0.86, y: top + 26 }, { x: w, y: top + 8 }]
  const farRidge = `${pathBetween(far, curveSegments(far), 0, far.length - 1)} L${w} ${h} L0 ${h} Z`
  return { width: w, height: h, columns, stops, segs, ridge, farRidge, base, top }
}

/**
 * Topographic contour lines for a `width` by `height` area: rings around two peaks,
 * gently irregular, every fourth one heavier (an index contour). Same input, same map.
 */
export function contourPaths(width, height, seed = 0) {
  const w = Math.max(1, num(width, 600))
  const h = Math.max(1, num(height, 300))
  const peaks = [
    { x: w * 0.78, y: h * 0.22, rings: 9, step: Math.max(14, Math.min(w, h) * 0.075) },
    { x: w * 0.18, y: h * 0.92, rings: 7, step: Math.max(12, Math.min(w, h) * 0.07) },
  ]
  const lines = []
  peaks.forEach((peak, pi) => {
    for (let k = 1; k <= peak.rings; k++) {
      const radius = k * peak.step
      const points = []
      for (let s = 0; s < 36; s++) {
        const a = (s / 36) * Math.PI * 2
        const wobble = 1 + 0.09 * Math.sin(3 * a + seed + k * 0.45 + pi) + 0.05 * Math.sin(5 * a - k * 0.7 + seed * 2)
        points.push({ x: peak.x + Math.cos(a) * radius * 1.7 * wobble, y: peak.y + Math.sin(a) * radius * wobble })
      }
      lines.push({ d: closedLoop(points), index: k % 4 === 0 })
    }
  })
  return lines
}

/* ------------------------------------------------------------- instruments -- */

/** Tick marks for the progress bezel: one per mission, lit for each one passed. */
export function bezelTicks(passed, total, size) {
  const n = Math.max(0, Math.round(num(total, 0)))
  const c = size / 2
  const outer = c - 1
  const inner = c - Math.max(6, size * 0.08)
  return Array.from({ length: n }, (_, i) => {
    const a = (i / n) * Math.PI * 2 - Math.PI / 2
    return {
      x1: round(c + Math.cos(a) * inner), y1: round(c + Math.sin(a) * inner),
      x2: round(c + Math.cos(a) * outer), y2: round(c + Math.sin(a) * outer),
      lit: i < passed,
    }
  })
}

/** Where the mission compass points: at the first step not done, or north when all are done. */
export function compassReading(steps) {
  const list = arr(steps)
  const done = list.map(s => ['done', 'placed'].includes(obj(s).status))
  const at = done.indexOf(false)
  const count = Math.max(1, list.length)
  return {
    at,
    done: done.filter(Boolean).length,
    total: list.length,
    complete: list.length > 0 && at === -1,
    angle: at === -1 ? 0 : (at / count) * 360,
  }
}

/** A seal's saw-tooth rim: alternate outer and inner radii around a circle. */
export function sealRim(cx, cy, outer, inner, teeth = 40) {
  const points = []
  for (let i = 0; i < teeth * 2; i++) {
    const a = (i / (teeth * 2)) * Math.PI * 2
    const r = i % 2 ? inner : outer
    points.push(`${round(cx + Math.cos(a) * r)} ${round(cy + Math.sin(a) * r)}`)
  }
  return `M${points.join(' L')} Z`
}
