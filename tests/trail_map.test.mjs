// The trail map's data and geometry, run against passports the real backend produced.
//
//   FA_PASSPORTS=/path/to/passports.json node --test tests/trail_map.test.mjs
//
// tests/test_trail_map.py builds that file from the real state module (every path, every
// level, every mission, from a fresh start to every certificate issued) and runs this.
// Without FA_PASSPORTS it falls back to harness/fixtures.json. A field missing from the
// passport once crashed pages in real Hermes, so every field the map reads is checked
// here, and every number the map draws must be finite.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  MAP_FIELDS, bezelTicks, compassReading, contourPaths, layoutProfile, layoutRow, overview, pathBetween, sealRim, trailModel,
} from '../desktop/src/trail.js'

function loadStates() {
  if (process.env.FA_PASSPORTS) return JSON.parse(readFileSync(process.env.FA_PASSPORTS, 'utf8'))
  const fixtures = JSON.parse(readFileSync(new URL('../harness/fixtures.json', import.meta.url), 'utf8'))
  return Object.fromEntries(Object.entries(fixtures.states).map(([name, s]) => [name, s.passport]))
}

const STATES = loadStates()
const WIDTHS = [160, 320, 560, 900, 1400]
const BAD = /NaN|undefined|Infinity|null/

function finite(n, where) {
  assert.ok(typeof n === 'number' && Number.isFinite(n), `${where}: ${n}`)
}

function cleanPath(d, where) {
  assert.equal(typeof d, 'string', where)
  assert.ok(!BAD.test(d), `${where}: ${d.slice(0, 120)}`)
}

function checkGeometry(model, layout, where) {
  assert.equal(layout.stops.length, model.total + 2, `${where}: trailhead + waypoints + summit`)
  assert.equal(layout.segs.length, layout.stops.length - 1, `${where}: one curve per gap`)
  layout.stops.forEach((s, i) => { finite(s.x, `${where} stop ${i} x`); finite(s.y, `${where} stop ${i} y`) })
  layout.segs.forEach((seg, i) => cleanPath(seg, `${where} segment ${i}`))
  for (let a = 0; a < layout.stops.length; a++) {
    for (let b = a; b < layout.stops.length; b++) cleanPath(pathBetween(layout.stops, layout.segs, a, b), `${where} ${a}-${b}`)
  }
  for (const col of layout.columns.camps) { finite(col.x0, `${where} camp x0`); finite(col.x1, `${where} camp x1`) }
  const waypoints = layout.stops.filter(s => s.kind === 'waypoint')
  assert.deepEqual(waypoints.map(s => s.point.id), model.waypoints.map(w => w.id), `${where}: waypoints in trail order`)
}

test('passports were found', () => {
  assert.ok(Object.keys(STATES).length >= 4, Object.keys(STATES).join(', '))
})

for (const [name, passport] of Object.entries(STATES)) {
  test(`${name}: the passport carries every field the map reads`, () => {
    assert.ok(Array.isArray(passport.tracks) && passport.tracks.length >= 4, 'four paths')
    for (const key of MAP_FIELDS.passport) assert.ok(key in passport, `the passport is missing ${key}`)
    for (const key of ['asked', 'text']) assert.ok(key in passport.goal, `goal is missing ${key}`)
    for (const key of ['due_count', 'due', 'strength', 'passed_missions', 'minutes']) assert.ok(key in passport.reviews, `reviews is missing ${key}`)
    for (const track of passport.tracks) {
      for (const key of MAP_FIELDS.track) assert.ok(key in track, `${track.id} is missing ${key}`)
      for (const key of MAP_FIELDS.certificate) assert.ok(key in track.certificate, `${track.id} certificate is missing ${key}`)
      assert.equal(track.levels.length, 4, `${track.id}: Beginner, Intermediate, Advanced, Capstone`)
      assert.deepEqual(track.levels.map(l => l.name), ['Beginner', 'Intermediate', 'Advanced', 'Capstone'])
      for (const level of track.levels) {
        for (const key of MAP_FIELDS.level) assert.ok(key in level, `${track.id}/${level.id} is missing ${key}`)
      }
      for (const mission of track.missions) {
        for (const key of MAP_FIELDS.mission) assert.ok(key in mission, `${mission.id} is missing ${key}`)
        assert.ok(Array.isArray(mission.steps) && mission.steps.length, `${mission.id} has steps`)
        for (const step of mission.steps) {
          for (const key of MAP_FIELDS.step) assert.ok(key in step, `${mission.id}/${step.id} is missing ${key}`)
        }
      }
    }
  })

  test(`${name}: every path, level and mission lands on the map`, () => {
    for (const track of passport.tracks) {
      const model = trailModel(track)
      assert.equal(model.id, track.id)
      assert.ok(model.name && model.eyebrow && model.promise, `${track.id} labels`)
      assert.deepEqual(model.camps.map(c => c.id), track.levels.map(l => l.id), `${track.id}: one camp per level`)
      for (const [i, camp] of model.camps.entries()) {
        const level = track.levels[i]
        assert.ok(camp.name, `${track.id}/${camp.id} name`)
        assert.deepEqual(camp.waypoints.map(w => w.id), level.missions, `${track.id}/${camp.id}: missions in level order`)
        assert.equal(camp.passed, level.passed, `${track.id}/${camp.id}: passed count agrees with the backend`)
        assert.equal(camp.total, level.total, `${track.id}/${camp.id}: total agrees with the backend`)
      }
      const ids = model.waypoints.map(w => w.id).sort()
      assert.deepEqual(ids, track.missions.map(m => m.id).sort(), `${track.id}: every mission exactly once`)
      for (const w of model.waypoints) {
        assert.ok(w.title && w.title !== 'Untitled mission', `${w.id} title`)
        assert.ok(['passed', 'started', 'waiting'].includes(w.status), `${w.id} status ${w.status}`)
        finite(w.minutes, `${w.id} minutes`)
      }
      assert.equal(model.passed, track.verified_missions, `${track.id}: passed missions`)
      assert.ok(model.marker >= 0 && model.marker <= model.total + 1, `${track.id}: marker ${model.marker}`)
      if (track.here) assert.equal(model.waypoints[model.marker - 1].id, track.here, `${track.id}: marker stands at here`)
      else if (model.passed === model.total) assert.equal(model.marker, model.total + 1, `${track.id}: marker at the summit`)
      assert.equal(model.summit.status, ['issued', 'ready'].includes(track.certificate.status) ? track.certificate.status : 'in_progress')

      for (const width of WIDTHS) {
        checkGeometry(model, layoutRow(model, width, 124, 2), `${track.id} row @${width}`)
        const profile = layoutProfile(model, width, 216)
        checkGeometry(model, profile, `${track.id} profile @${width}`)
        cleanPath(profile.ridge, `${track.id} ridge @${width}`)
        cleanPath(profile.farRidge, `${track.id} far ridge @${width}`)
      }
    }
  })

  test(`${name}: the overview counts each mission once`, () => {
    const info = overview(passport)
    const unique = new Set(passport.tracks.flatMap(t => t.missions.map(m => m.id)))
    assert.equal(info.total, unique.size)
    assert.ok(info.passed >= 0 && info.passed <= info.total)
    assert.equal(info.tracks.length, passport.tracks.length)
    if (passport.goal_track || passport.next_up) assert.ok(info.goal, 'a goal path to show under Where you are')
  })

  test(`${name}: the mission compass reads every mission`, () => {
    for (const track of passport.tracks) {
      for (const mission of track.missions) {
        const r = compassReading(mission.steps)
        assert.equal(r.total, mission.steps.length)
        finite(r.angle, `${mission.id} angle`)
        assert.ok(r.complete || (r.at >= 0 && r.at < r.total), `${mission.id} at ${r.at}`)
      }
    }
  })
}

test('a passport with gaps still draws, with defaults instead of crashes', () => {
  const odd = [
    undefined, null, {}, { id: 'x' },
    { id: 'thin', missions: [{ id: 'a' }, { id: 'b', status: 'verified' }, { title: 'no id' }], levels: [{ missions: ['a', 'ghost'] }] },
    { id: 'nolevels', missions: [{ id: 'a', level: 'beginner', level_name: 'Beginner' }], here: 'a', certificate: { status: 'ready' } },
    { id: 'strange', missions: 'oops', levels: [null, 4, { id: 'l', number: 'one', missions: null }], certificate: 'x' },
  ]
  for (const [i, track] of odd.entries()) {
    const model = trailModel(track)
    assert.ok(Array.isArray(model.camps) && Array.isArray(model.waypoints), `case ${i}`)
    for (const width of [0, NaN, 300]) {
      checkGeometry(model, layoutRow(model, width, undefined, i), `odd ${i} row`)
      checkGeometry(model, layoutProfile(model, width, undefined), `odd ${i} profile`)
    }
  }
  const thin = trailModel(odd[4])
  assert.deepEqual(thin.waypoints.map(w => w.id), ['a', 'b'], 'missions no level lists still land in a camp')
  assert.equal(thin.waypoints[0].title, 'Untitled mission')
  assert.equal(trailModel(odd[5]).marker, 1)
  const empty = overview({ tracks: 'nope' })
  assert.equal(empty.total, 0)
  assert.equal(empty.goal, null)
})

test('contours, bezel ticks and the seal rim are finite', () => {
  for (const [w, h] of [[0, 0], [300, 200], [1200, 700]]) {
    const lines = contourPaths(w, h, 3)
    assert.ok(lines.length > 4)
    lines.forEach((line, i) => cleanPath(line.d, `contour ${i} @${w}x${h}`))
  }
  const ticks = bezelTicks(3, 15, 108)
  assert.equal(ticks.length, 15)
  assert.equal(ticks.filter(t => t.lit).length, 3)
  ticks.forEach(t => [t.x1, t.y1, t.x2, t.y2].forEach(n => finite(n, 'tick')))
  cleanPath(sealRim(64, 64, 63, 59, 44), 'seal rim')
  assert.deepEqual(compassReading([]), { at: -1, done: 0, total: 0, complete: false, angle: 0 })
  assert.equal(compassReading([{ status: 'done' }, { status: 'ready' }, {}, {}]).angle, 90)
  assert.equal(compassReading([{ status: 'done' }, { status: 'done' }]).complete, true)
})
