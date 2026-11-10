// 0.9 persona test: the page logic behind the persona-test fixes (docs/STATUS.md). Pure functions only, run with
//   node --test tests/persona_fixes.test.mjs

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  canReveal, canTestOut, earlierPracticeLeft, freezeMissing, mdBlocks, missionWords, plantPill, recallLead, revealBlocks,
  showsMemory, stepStates,
} from '../desktop/src/loop.js'
import { screenSafe, tryBody, tryFields, tryFormKind } from '../desktop/src/loop_b.js'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const MD = join(ROOT, 'content', 'foundations', 'md')

/* ------------------------------------------------------------ try forms -- */

test('every kind of mission gets its own try form, never mission 3\'s by default', () => {
  assert.equal(tryFormKind({ lab: { try_fields: [{ id: 'guess_asks' }], note_fields: [{ id: 'tb' }] } }), 'fields')
  assert.equal(tryFormKind({ lab: { note_fields_a: { try: [{ id: 'guess' }] } } }), 'a')
  assert.equal(tryFormKind({ lab: { note_fields: [{ id: 'job' }] } }), 'none', 'a field-note mission with no try fields has no try form')
  assert.equal(tryFormKind({ lab: {} }), 'memory')
  assert.equal(tryFormKind({}), 'memory')
})

test('a try note carries only its own fields, numbers as numbers', () => {
  const fields = [{ id: 'tools_total', kind: 'number' }, { id: 'guess_asks', kind: 'choice' }, { id: 'times_asked', kind: 'number' }]
  assert.deepEqual(tryBody(fields, { tools_total: '14', guess_asks: 'yes', times_asked: '', stray: 'x' }), { tools_total: 14, guess_asks: 'yes' })
  assert.deepEqual(tryFields({ lab: { try_fields: fields } }), fields)
  assert.deepEqual(tryFields({}), [])
})

test('Show memory file only where the mission says its work runs through memory', () => {
  assert.equal(showsMemory({ lab: { memory_view: true } }), true)
  assert.equal(showsMemory({ lab: {} }), false)
  assert.equal(showsMemory({}), false)
})

/* ------------------------------------------------------- check yourself -- */

test('every Check yourself answer is hidden behind its question, in every lesson', () => {
  const files = readdirSync(MD).filter(f => f.endsWith('.idea.md'))
  let lessons = 0
  for (const file of files) {
    const text = readFileSync(join(MD, file), 'utf8')
    if (!/^## Check yourself/m.test(text)) continue
    lessons++
    const blocks = revealBlocks(mdBlocks(text))
    const start = blocks.findIndex(b => b.kind === 'h2' && /^Check yourself/.test(b.text))
    const end = blocks.findIndex((b, i) => i > start && b.kind === 'h2')
    const section = blocks.slice(start + 1, end === -1 ? undefined : end)
    const qa = section.filter(b => b.kind === 'qa')
    assert.ok(qa.length >= 2, `${file}: ${qa.length} questions`)
    assert.equal(section.filter(b => b.kind === 'quote').length, 0, `${file}: an answer is still printed open`)
    for (const q of qa) {
      assert.match(q.question, /^\d+\.\s/, `${file}: ${q.question.slice(0, 40)}`)
      assert.ok(q.answer.length >= 1 && q.answer.every(a => a.trim()), file)
    }
  }
  assert.equal(lessons, files.filter(f => /^## Check yourself/m.test(readFileSync(join(MD, f), 'utf8'))).length)
  assert.ok(lessons >= 12)
})

test('quotes outside Check yourself stay quotes, and the answer opens only after one is written', () => {
  const text = '## The idea\n\n**A bold line**\n\n> A quote that stays a quote.\n\n## Check yourself\n\n**1. Why?**\n\n> Because.\n'
  const blocks = revealBlocks(mdBlocks(text))
  assert.equal(blocks.filter(b => b.kind === 'quote').length, 1)
  assert.deepEqual(blocks.filter(b => b.kind === 'qa'), [{ kind: 'qa', question: '1. Why?', answer: ['Because.'] }])
  assert.equal(canReveal(''), false)
  assert.equal(canReveal(' x '), false)
  assert.equal(canReveal('No idea, a guess'), true)
})

/* ---------------------------------------------------------- recall copy -- */

test('Recall speaks to someone who skipped the missions it reaches back to', () => {
  assert.equal(recallLead([{ mission: 'f.cost', order: 2, title: "See what a chat costs, and cut it", done: true }]), '')
  assert.equal(recallLead([]), '')
  const one = recallLead([{ mission: 'f.schedules', order: 8, title: 'Set up a job that runs on a schedule', done: false }])
  assert.match(one, /^You haven't done mission 8 \(Set up a job that runs on a schedule\) in Field Academy yet/)
  const two = recallLead([{ order: 1, title: 'Check whether Hermes really did what it says', done: false }, { order: 2, title: "See what a chat costs, and cut it", done: false }])
  assert.match(two, /mission 1 \(Check whether Hermes really did what it says\) or mission 2 \(See what a chat costs, and cut it\)/)
})

test('the replace sentence shows only when a practice profile from another try is still there', () => {
  assert.equal(earlierPracticeLeft([], { profile: '' }), false)
  assert.equal(earlierPracticeLeft([{ name: 'academy-practice', status: 'removed' }], { profile: '' }), false)
  assert.equal(earlierPracticeLeft([{ name: 'academy-practice', status: 'ready' }], { profile: '' }), true)
  assert.equal(earlierPracticeLeft([{ name: 'academy-practice', status: 'ready' }], { profile: 'academy-practice' }), false)
  assert.equal(earlierPracticeLeft([{ name: 'academy-practice', status: 'ready' }, { name: 'academy-practice-b', status: 'ready' }], { profile: 'academy-practice' }), true)
})

/* -------------------------------------------------------------- compare -- */

test('the planted problem pill uses the record\'s word: caught', () => {
  assert.equal(plantPill({ fired: true, caught: true }), 'You caught it')
  assert.equal(plantPill({ fired: true, caught: false }), 'You ran into it, not caught yet')
  assert.equal(plantPill({ fired: false, caught: false }), 'Not caught yet')
  assert.equal(plantPill({ fired: true }), 'You ran into it')
  assert.equal(plantPill({ fired: false }), "You didn't run into it")
})

/* ---------------------------------------------------- connector masking -- */

test('mission 7 never shows a password or token from a connector on screen', () => {
  // Made at run time, so no scanner takes a test value for a real one (test_security_085).
  const fakeToken = 'abcdefgh'.repeat(2)
  const text = JSON.stringify({ mcp_servers: {
    github: { url: 'https://user:pw@mcp.example.com:8443/sse?token=abc&mode=fast', headers: { Authorization: ['Bearer', fakeToken].join(' ') } },
    notes: { command: 'notes', env: { NOTES_API_KEY: 'k-123456', NOTES_HOME: '/tmp/notes' }, url: 'https://tok3n@notes.example.com/mcp' },
    files: { command: 'npx', args: ['-y', '@modelcontextprotocol/server-filesystem@2026.8.31', '/home/ada/.hermes/profiles/academy-practice/practice-folder'], trust: 'untrusted', tools: { include: [] } },
  } }, null, 2)
  const shown = screenSafe(text)
  for (const secret of ['user:pw', 'pw@', 'token=abc', fakeToken, 'k-123456', 'tok3n']) assert.ok(!shown.includes(secret), secret)
  assert.ok(shown.includes('mcp.example.com:8443/sse?token=[hidden on screen]&mode=fast'))
  assert.ok(shown.includes('"NOTES_HOME": "/tmp/notes"'), 'a setting that is not a secret stays')
  assert.ok(shown.includes('/home/ada/.hermes/profiles/academy-practice/practice-folder'), 'paths stay')
  assert.ok(shown.includes('"trust": "untrusted"'))
  assert.equal(screenSafe('{"files": {"command": "npx"}}'), '{"files": {"command": "npx"}}')
})

/* ------------------------------------------------------------- test-out -- */

const entry = (kind, body = {}) => ({ kind, body })
const frozenView = (extra = {}) => ({
  attempt: { id: 1, frozen_at: '2026-11-08T10:00:00+00:00', profile: 'academy-practice' },
  lab: { profiles: ['a'] },
  entries: [entry('claim', { text: 'c' }), entry('standard', { checks: [] }), entry('prediction', { checks: {} }), entry('lab_note', { fact: 'x' }), entry('self_score', { checks: {} })],
  runs: { first: { passed: true } },
  ...extra,
})
const ready = [{ name: 'academy-practice', which: 'a', status: 'ready', set_up: true }]

test('a test-out skips Recall and can reach the record once every check passed the first time', () => {
  const states = Object.fromEntries(stepStates(frozenView({ test_out: { on: true, passed: true } }), ready).map(s => [s.id, s.status]))
  assert.equal(states.recall, 'skipped')
  assert.equal(states.claim, 'done')
  assert.equal(states.record, 'open')
  const missed = Object.fromEntries(stepStates(frozenView({ test_out: { on: true, passed: false } }), ready).map(s => [s.id, s.status]))
  assert.equal(missed.record, 'locked', 'a miss goes through Compare and the fix like any mission')
  const usual = Object.fromEntries(stepStates(frozenView(), ready).map(s => [s.id, s.status]))
  assert.equal(usual.recall, 'open')
  assert.equal(usual.record, 'locked')
})

test('the freeze asks for no recall on a test-out', () => {
  const view = { entries: [entry('claim'), entry('standard'), entry('prediction')] }
  assert.deepEqual(freezeMissing(view), ['your recall'])
  assert.deepEqual(freezeMissing({ ...view, test_out: { on: true } }), [])
})

test('who can test out, and how the list words it', () => {
  assert.equal(canTestOut({ id: 'f.loop', attempts: [] }), true)
  assert.equal(canTestOut({ id: 'f.review', kind: 'review', attempts: [] }), false)
  assert.equal(canTestOut({ id: 'f.loop', attempts: [{ status: 'done' }] }), false)
  assert.equal(canTestOut({ id: 'f.loop', attempts: [{ status: 'lab', frozen_at: 'x' }] }), false)
  assert.equal(canTestOut({ id: 'f.loop', attempts: [{ status: 'open', frozen_at: '' }] }), true, 'a try not yet in practice can become a test-out')
  assert.equal(canTestOut({ id: 'f.loop', attempts: [{ status: 'open', frozen_at: '', test_out: true }] }), false)
  assert.equal(missionWords({ attempts: [{ status: 'done', tested_out: true }] }).word, 'Tested out')
  assert.equal(missionWords({ attempts: [{ status: 'done', tested_out: false, test_out: true }] }).word, 'In your record')
  assert.equal(missionWords({ attempts: [{ status: 'open', test_out: true, frozen_at: '' }] }).word, 'Testing out')
  assert.equal(missionWords({ attempts: [] }).word, 'Not started')
})
