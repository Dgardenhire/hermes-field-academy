// The open cache: the map's first paint from a kept copy, and what is never kept.
//
//   FA_OPEN_STATES=/path/to/states.json node --test tests/open_cache.test.mjs
//
// tests/test_open_cache.py builds that file from the real backend (passports, Guide trails and Foundations lists from
// a fresh start to every certificate issued) and runs this. Without FA_OPEN_STATES it falls back to
// harness/fixtures.json, and without that it runs only the tests that need no backend data.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import {
  HOLD_SELECTOR, OPEN_CACHE_MAX_AGE_MS, OPEN_CACHE_MAX_CHARS, OPEN_CACHE_VERSION, carriesSecret, isSecretKey, openCacheKey, openPlan,
  openScope, packSnapshot, previewIntent, readSnapshot, slimFor, unpackSnapshot, writeSnapshot,
} from '../desktop/src/opencache.js'
import { MAP_FIELDS, overview, trailModel } from '../desktop/src/trail.js'
import { resumeWords } from '../desktop/src/desk_logic.js'

function loadStates() {
  if (process.env.FA_OPEN_STATES) return JSON.parse(readFileSync(process.env.FA_OPEN_STATES, 'utf8'))
  const url = new URL('../harness/fixtures.json', import.meta.url)
  if (!existsSync(url)) return {}
  const fixtures = JSON.parse(readFileSync(url, 'utf8'))
  return Object.fromEntries(Object.entries(fixtures.states).map(([name, s]) => [name, {
    passport: s.passport, deployer: s.deployer, foundations: s.foundations && s.foundations.snapshot,
  }]))
}

const STATES = loadStates()
const SCOPE = openScope('default', 'local')
const NOW = Date.UTC(2026, 10, 10, 12)

/** A PluginStorage like the SDK's: JSON in, JSON out, under one plugin's keys. */
function memoryStorage() {
  const map = new Map()
  return {
    map,
    get: (key, fallback) => (map.has(key) ? JSON.parse(map.get(key)) : fallback),
    set: (key, value) => map.set(key, JSON.stringify(value)),
    remove: key => map.delete(key),
  }
}

const tiny = {
  passport: { version: 1, goal_track: 'operator', tracks: [{ id: 'operator', name: 'Messenger', missions: [{ id: 'm1', title: 'One', status: 'verified', steps: [{ id: 's', kind: 'lesson', title: 'Read', status: 'done', body: 'long lesson' }], sources: ['x'], watch: ['y'] }], levels: [{ id: 'beginner', missions: ['m1'] }], certificate: { status: 'in_progress' } }], recent_evidence: [{ path: '/Users/you/notes.md' }] },
  deployer: { available: true, track: { id: 'deployer', name: 'Guide', missions: [], levels: [] }, certificate: { label: 'Awaiting review', status: 'in_progress' }, about: { disclaimer: 'Self-issued.' }, labs: [{ big: true }], hermes_version: { value: '0.23.0' } },
  foundations: { missions: [{ id: 'f.memory', order: 1, title: 'Memory', trail: '', attempts: [{ id: 3, status: 'open', stage: 'practice', profile: 'academy-practice' }] }], calibration_table: [{}], record: [{ folder: '/Users/you/record' }] },
}

/* ----------------------------------------------------------- first paint -- */

test('first paint: with a kept passport and Guide trail, the map draws at once from the copy', () => {
  const plan = openPlan({ live: {}, cached: { passport: tiny.passport, deployer: tiny.deployer }, view: 'map' })
  assert.equal(plan.state, 'ready')
  assert.equal(plan.preview, true)
  assert.equal(plan.passport, tiny.passport)
  assert.equal(plan.deployer, tiny.deployer)
})

test('first paint: the very first open, with nothing kept, still shows the skeleton', () => {
  assert.equal(openPlan({ live: {}, cached: {}, view: 'map' }).state, 'skeleton')
  assert.equal(openPlan({ live: {}, cached: { passport: null, deployer: null }, view: 'map' }).state, 'skeleton')
})

test('first paint: the map still waits for a Guide trail, live or kept, so its counts appear once', () => {
  const plan = openPlan({ live: {}, cached: { passport: tiny.passport }, view: 'map' })
  assert.equal(plan.state, 'skeleton')
  const settled = openPlan({ live: { deployerSettled: true }, cached: { passport: tiny.passport }, view: 'map' })
  assert.equal(settled.state, 'ready')
  assert.equal(settled.deployer, undefined, 'a backend with no Guide trail draws the map without one')
})

test('first paint: a page other than the map never draws from a copy', () => {
  for (const view of ['mission', 'path', 'foundations', 'f-mission', 'review', 'certificate']) {
    assert.equal(openPlan({ live: {}, cached: { passport: tiny.passport, deployer: tiny.deployer }, view }).state, 'skeleton', view)
  }
})

test('background refresh: the live answers replace the copy, and the map is live again', () => {
  const live = { passport: { ...tiny.passport, goal_track: 'traveler' }, deployer: { ...tiny.deployer }, deployerSettled: true }
  const plan = openPlan({ live, cached: { passport: tiny.passport, deployer: tiny.deployer }, view: 'map' })
  assert.equal(plan.state, 'ready')
  assert.equal(plan.preview, false)
  assert.equal(plan.passport, live.passport)
  assert.equal(plan.deployer, live.deployer)
})

test('background refresh: a live passport with the Guide trail still loading keeps the kept trail, still a preview', () => {
  const live = { passport: tiny.passport, deployerSettled: false }
  const plan = openPlan({ live, cached: { deployer: tiny.deployer }, view: 'map' })
  assert.deepEqual([plan.state, plan.preview, plan.deployer], ['ready', true, tiny.deployer])
  // Off the map, the page waits for the live trail as it always did.
  assert.equal(openPlan({ live, cached: { deployer: tiny.deployer }, view: 'path' }).state, 'skeleton')
})

test('background refresh: a Guide trail that failed (an older backend) is not stood in for by the copy', () => {
  const plan = openPlan({ live: { passport: tiny.passport, deployer: undefined, deployerSettled: true }, cached: { deployer: tiny.deployer }, view: 'map' })
  assert.deepEqual([plan.state, plan.preview, plan.deployer], ['ready', false, undefined])
})

test('on a practice profile nothing is live yet: what the page holds is shown as a copy', () => {
  const plan = openPlan({ live: { passport: tiny.passport, deployer: tiny.deployer, deployerSettled: true }, cached: {}, view: 'map', homeReady: false })
  assert.deepEqual([plan.state, plan.preview], ['ready', true])
  assert.equal(openPlan({ live: { passport: tiny.passport, deployerSettled: true }, cached: {}, view: 'mission', homeReady: false }).state, 'skeleton')
})

/* -------------------------------------------------------- storage round trip -- */

test('a kept answer round-trips through the SDK storage, under the plugin\'s own key', () => {
  const storage = memoryStorage()
  assert.equal(writeSnapshot(storage, 'passport', tiny.passport, SCOPE, NOW), true)
  assert.ok(storage.map.has(openCacheKey('passport')))
  const back = readSnapshot(storage, 'passport', SCOPE, NOW + 1000)
  assert.equal(back.goal_track, 'operator')
  assert.equal(back.tracks[0].missions[0].title, 'One')
})

test('a copy from another profile or connection, another version, or too long ago is not shown', () => {
  const storage = memoryStorage()
  writeSnapshot(storage, 'passport', tiny.passport, SCOPE, NOW)
  assert.equal(readSnapshot(storage, 'passport', openScope('work', 'local'), NOW), null)
  assert.equal(readSnapshot(storage, 'passport', openScope('default', 'remote-1'), NOW), null)
  assert.equal(readSnapshot(storage, 'passport', '', NOW), null)
  assert.equal(readSnapshot(storage, 'passport', SCOPE, NOW + OPEN_CACHE_MAX_AGE_MS + 1), null)
  assert.equal(readSnapshot(storage, 'passport', SCOPE, NOW - 10 * 60 * 1000), null, 'a copy from the future is not trusted')
  const record = storage.get(openCacheKey('passport'), null)
  assert.equal(unpackSnapshot('passport', { ...record, v: OPEN_CACHE_VERSION + 1 }, SCOPE, NOW), null)
  assert.equal(unpackSnapshot('passport', 'not a record', SCOPE, NOW), null)
})

test('no scope (no profile known yet) keeps nothing', () => {
  const storage = memoryStorage()
  assert.equal(openScope('', 'x'), '')
  assert.equal(writeSnapshot(storage, 'passport', tiny.passport, '', NOW), false)
  assert.equal(storage.map.size, 0)
})

test('storage that throws, or is missing, never breaks the page', () => {
  const broken = { get() { throw new Error('denied') }, set() { throw new Error('full') }, remove() { throw new Error('x') } }
  assert.equal(readSnapshot(broken, 'passport', SCOPE, NOW), null)
  assert.equal(writeSnapshot(broken, 'passport', tiny.passport, SCOPE, NOW), false)
  assert.equal(readSnapshot(null, 'passport', SCOPE, NOW), null)
  assert.equal(writeSnapshot(undefined, 'passport', tiny.passport, SCOPE, NOW), false)
})

/* ----------------------------------------------------------------- size cap -- */

test('size cap: an answer too big to keep is not kept, and the older copy goes with it', () => {
  const storage = memoryStorage()
  writeSnapshot(storage, 'passport', tiny.passport, SCOPE, NOW)
  const huge = { ...tiny.passport, school_line: 'x'.repeat(OPEN_CACHE_MAX_CHARS + 1) }
  assert.equal(packSnapshot('passport', huge, SCOPE, NOW), null)
  assert.equal(writeSnapshot(storage, 'passport', huge, SCOPE, NOW + 1), false)
  assert.equal(storage.map.has(openCacheKey('passport')), false, 'a copy older than the last answer is never shown')
})

test('size cap: only what the map reads is kept', () => {
  const p = slimFor('passport', tiny.passport)
  assert.equal('recent_evidence' in p, false)
  const m = p.tracks[0].missions[0]
  assert.deepEqual(Object.keys(m).sort(), ['id', 'status', 'title'], 'no lesson, steps, sources or watch list')
  const d = slimFor('deployer', tiny.deployer)
  assert.deepEqual(Object.keys(d).sort(), ['about', 'available', 'certificate', 'track'])
  const f = slimFor('foundations', tiny.foundations)
  assert.deepEqual(Object.keys(f), ['missions'])
  assert.deepEqual(f.missions[0].attempts, [{ id: 3, status: 'open', stage: 'practice' }])
  assert.equal(JSON.stringify(f).includes('/Users/you'), false, 'no saved-record folder is kept')
  assert.equal(JSON.stringify(p).includes('/Users/you'), false, 'no evidence path is kept')
})

test('an answer that is not the shape the map reads is not kept', () => {
  for (const kind of ['passport', 'deployer', 'foundations']) {
    for (const bad of [null, undefined, 'x', 3, [], {}]) {
      if (kind === 'deployer' && bad && typeof bad === 'object' && !Array.isArray(bad)) continue // {} is a backend with no trail
      assert.equal(slimFor(kind, bad), null, `${kind} ${JSON.stringify(bad)}`)
    }
  }
  assert.equal(slimFor('other', tiny.passport), null)
})

/* ---------------------------------------------------------------- no secrets -- */

test('no secrets: keys named like credentials are dropped wherever they sit', () => {
  for (const key of ['token', 'api_key', 'apiKey', 'API-KEY', 'password', 'client_secret', 'access_token', 'refresh_token', 'authorization', 'auth', 'cookie', 'credentials', 'private_key', 'bot_token']) {
    assert.ok(isSecretKey(key), key)
  }
  for (const key of ['author', 'authority', 'public_key', 'tokens_used', 'title', 'passed', 'secretary_name']) {
    assert.equal(isSecretKey(key), false, key)
  }
  const passport = { ...tiny.passport, api_key: 'abc', goal: { text: 'hi', token: 'abc' }, tracks: [{ ...tiny.passport.tracks[0], password: 'p' }] }
  const kept = slimFor('passport', passport)
  const text = JSON.stringify(kept)
  for (const word of ['api_key', '"token"', 'password']) assert.equal(text.includes(word), false, word)
  assert.equal(kept.goal.text, 'hi')
})

test('no secrets: an answer carrying anything shaped like a credential is not kept at all', () => {
  // Made when the test runs, so no scanner and no reader mistakes one for a real key (test_security_085).
  const body = 'abcdefghijklmnopqrstuvwxyz0123456789'
  const samples = [
    ['sk-', 'ant-api03-', body].join(''),
    ['sk-', 'proj-', body.slice(0, 24)].join(''),
    ['gh', 'p_', body].join(''),
    ['xo', 'xb-', '1234567890-abcdefghij'].join(''),
    ['AK', 'IA', 'ABCDEFGHIJKLMNOP'].join(''),
    ['AI', 'za', 'SyA1234567890', body.slice(0, 20)].join(''),
    ['-----BEGIN OPENSSH ', 'PRIVATE KEY-----'].join(''),
    ['Authorization: ', 'Bear', 'er ', body.slice(0, 16), '.', body.slice(16, 26)].join(''),
    ['ey', 'JhbGciOiJIUzI1NiJ9.', 'eyJzdWIiOiIxMjM0NTY3ODkwIn0.', body].join(''),
    ['123456789', ':', 'ABCdefGHIjklMNO', body.slice(0, 20)].join(''),
  ]
  const storage = memoryStorage()
  for (const secret of samples) {
    assert.ok(carriesSecret({ a: [{ b: `my goal is ${secret} ok` }] }), secret)
    const passport = { ...tiny.passport, goal: { text: `Use ${secret} for the bot`, asked: true } }
    assert.equal(slimFor('passport', passport), null, secret)
    writeSnapshot(storage, 'passport', tiny.passport, SCOPE, NOW)
    assert.equal(writeSnapshot(storage, 'passport', passport, SCOPE, NOW), false)
    assert.equal(storage.map.has(openCacheKey('passport')), false, 'the older copy is cleared too')
  }
  assert.equal(carriesSecret(tiny.passport), false)
})

test('no secrets: a copy that somehow holds one is refused on the way out', () => {
  const storage = memoryStorage()
  storage.set(openCacheKey('passport'), { v: OPEN_CACHE_VERSION, scope: SCOPE, at: NOW, data: { ...tiny.passport, goal: { text: ['gh', 'p_', 'abcdefghijklmnopqrstuvwxyz0123456789'].join('') } } })
  assert.equal(readSnapshot(storage, 'passport', SCOPE, NOW), null)
  storage.set(openCacheKey('passport'), { v: OPEN_CACHE_VERSION, scope: SCOPE, at: NOW, data: { ...tiny.passport, session_key: 'x' } })
  assert.equal('session_key' in readSnapshot(storage, 'passport', SCOPE, NOW), false)
})

/* ------------------------------------------------------- nothing acts on a copy -- */

function el(kind) {
  return { kind, closest(selector) { return selector.split(',').map(s => s.trim()).includes(kind) ? this : null } }
}

test('nothing acts on a copy: a click on a control is held for replay, typing and scrolling pass', () => {
  assert.ok(HOLD_SELECTOR.includes('button') && HOLD_SELECTOR.includes('[role="button"]'))
  assert.equal(previewIntent({ type: 'click', target: el('button') }), 'hold')
  assert.equal(previewIntent({ type: 'click', target: el('[role="button"]') }), 'hold')
  assert.equal(previewIntent({ type: 'click', target: el('a[href]') }), 'hold')
  assert.equal(previewIntent({ type: 'click', target: el('div') }), 'pass')
  assert.equal(previewIntent({ type: 'keydown', key: 'Enter', metaKey: true, target: el('textarea') }), 'block', 'a submit shortcut in a field')
  assert.equal(previewIntent({ type: 'keydown', key: 'Enter', ctrlKey: true, target: el('textarea') }), 'block')
  assert.equal(previewIntent({ type: 'keydown', key: 'Enter', target: el('textarea') }), 'pass', 'a new line in a field')
  assert.equal(previewIntent({ type: 'keydown', key: 'j', target: el('div') }), 'pass')
  assert.equal(previewIntent({ type: 'keydown', key: 'Enter', target: el('button') }), 'pass', 'the browser turns it into a click, which is held')
  assert.equal(previewIntent(null), 'pass')
})

/* ------------------------------------------------------ against the real backend -- */

const named = Object.entries(STATES)

for (const [name, state] of named) {
  if (state.passport) {
    test(`${name}: the kept passport draws the same map as the full one, and fits the cap`, () => {
      const slim = slimFor('passport', state.passport)
      assert.ok(slim, 'the real passport can be kept')
      assert.deepEqual(overview(slim), overview(state.passport))
      for (const key of MAP_FIELDS.passport) assert.deepEqual(slim[key], state.passport[key], key)
      for (const key of ['goal_track', 'school_line', 'camp_lines', 'summit_line', 'credential_note']) assert.deepEqual(slim[key], state.passport[key], key)
      state.passport.tracks.forEach((track, i) => {
        const kept = slim.tracks[i]
        for (const key of MAP_FIELDS.track.filter(k => k !== 'missions' && k !== 'certificate')) assert.deepEqual(kept[key], track[key], `${track.id}.${key}`)
        for (const key of [...MAP_FIELDS.certificate, 'words']) assert.deepEqual(kept.certificate[key], track.certificate[key], `${track.id} certificate.${key}`)
        track.missions.forEach((m, j) => {
          for (const key of MAP_FIELDS.mission) assert.deepEqual(kept.missions[j][key], m[key], `${m.id}.${key}`)
        })
        assert.deepEqual(trailModel(kept), trailModel(track))
      })
      const size = JSON.stringify(packSnapshot('passport', state.passport, SCOPE, NOW)).length
      assert.ok(size <= OPEN_CACHE_MAX_CHARS + 200, `${size} characters`)
      assert.ok(size < JSON.stringify(state.passport).length / 6, 'the lessons stay behind')
    })
  }
  if (state.deployer && state.deployer.track) {
    test(`${name}: the kept Guide trail draws the same trail`, () => {
      const slim = slimFor('deployer', state.deployer)
      assert.ok(slim)
      assert.deepEqual(trailModel(slim.track), trailModel(state.deployer.track))
      assert.equal(slim.track.name, state.deployer.track.name)
      assert.equal(slim.certificate.label, state.deployer.certificate.label)
      assert.equal(slim.certificate.status, state.deployer.certificate.status)
      assert.equal(slim.about.disclaimer, state.deployer.about.disclaimer)
      assert.equal('hermes_version' in slim, false)
      assert.ok(JSON.stringify(slim).length <= OPEN_CACHE_MAX_CHARS)
    })
  }
  if (state.foundations && Array.isArray(state.foundations.missions)) {
    test(`${name}: the kept Foundations list gives the cards the same counts and Start here`, () => {
      const slim = slimFor('foundations', state.foundations)
      assert.ok(slim)
      const pick = f => f.missions.map(m => [m.id, m.trail, (m.attempts || []).map(a => [a.status, a.stage])])
      assert.deepEqual(pick(slim), pick(state.foundations))
      const memory = f => resumeWords(f.missions.find(m => m.id === 'f.memory'))
      assert.deepEqual(memory(slim), memory(state.foundations))
      assert.ok(JSON.stringify(slim).length <= OPEN_CACHE_MAX_CHARS)
    })
  }
}
