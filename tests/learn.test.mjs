// The page's learning logic: how time, support and strength are worded, and how the live checks
// read the lists Hermes returns. Run by tests/test_learn_js.py, or: node --test tests/learn.test.mjs

import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  CONNECTION_KEYS, classifyConnection, dueWords, jobHasSchedule, jobRequest, minutesWords, promptCues,
  recordTime, startsWithMarker, strengthWord, supportStages, timeLine,
} from '../desktop/src/learn.js'

const NOW = new Date('2026-10-03T12:00:00Z')

test('due dates are said in plain words', () => {
  assert.equal(dueWords('2026-10-02T00:00:00Z', NOW), 'Due now')
  assert.equal(dueWords('2026-10-04T10:00:00Z', NOW), 'Due tomorrow')
  assert.equal(dueWords('2026-10-08T12:00:00Z', NOW), 'Due in 5 days')
  assert.match(dueWords('2026-12-25T12:00:00Z', NOW), /^Due Dec 25$/)
  assert.equal(dueWords('', NOW), '')
  assert.equal(dueWords('not a date', NOW), '')
})

test('minutes are said as about N minutes, then hours', () => {
  assert.equal(minutesWords(1), 'About 1 minute')
  assert.equal(minutesWords(28), 'About 28 minutes')
  assert.equal(minutesWords(60), 'About 1 hour')
  assert.equal(minutesWords(122), 'About 2 hours 2 minutes')
  assert.equal(minutesWords('x'), 'About 0 minutes')
})

test('the time line lists every step that has minutes', () => {
  const steps = [{ kind: 'lesson', minutes: 3 }, { kind: 'example', minutes: 4 }, { kind: 'gate', minutes: 0 }]
  assert.equal(timeLine(steps, { lesson: 'read', example: 'example' }), 'read 3 min · example 4 min')
  assert.equal(timeLine(null), '')
})

test('strength is always a word', () => {
  assert.deepEqual([null, 92, 85, 78, 70, 55, 39].map(strengthWord), ['Not reviewed yet', 'Strong', 'Strong', 'Holding', 'Holding', 'Fading', 'Weak'])
})

const steps = statuses => ['lesson', 'example', 'complete', 'lab', 'explain', 'gate'].map((kind, i) => ({ kind, status: statuses[i] || 'ready' }))

test('support fades through three stages and says where you are', () => {
  const fresh = supportStages(steps([]))
  assert.deepEqual(fresh.map(s => s.state), ['now', 'later', 'later'])
  assert.deepEqual(fresh.map(s => s.label), ['Full example', 'Half done', 'On your own'])
  const half = supportStages(steps(['done', 'done']))
  assert.deepEqual(half.map(s => s.state), ['done', 'now', 'later'])
  const alone = supportStages(steps(['done', 'done', 'done', 'done']))
  assert.deepEqual(alone.map(s => s.state), ['done', 'done', 'now'])
  const all = supportStages(steps(['done', 'done', 'done', 'done', 'done', 'done']))
  assert.deepEqual(all.map(s => s.state), ['done', 'done', 'done'])
})

test('a step skipped by placement counts as done for the stage, never for the check', () => {
  const placed = supportStages(steps(['placed', 'placed', 'placed', 'placed']))
  assert.deepEqual(placed.map(s => s.state), ['done', 'done', 'now'])
})

test('support stages survive missing data', () => {
  assert.equal(supportStages(undefined).length, 3)
  assert.equal(supportStages([{}, null]).length, 3)
})

test('connections are classified from whatever Hermes reports', () => {
  assert.equal(classifyConnection({ profile: 'default', mode: 'local' }), 'local')
  assert.equal(classifyConnection({ mode: 'ssh', url: 'ssh://office-server' }), 'remote')
  assert.equal(classifyConnection({ url: 'https://gateway.example.com' }), 'remote')
  assert.equal(classifyConnection({ url: 'http://localhost:9119' }), 'local')
  assert.equal(classifyConnection({ mode: 'nous-cloud' }), 'cloud')
  assert.equal(classifyConnection({ mode: 'mystery' }), '')
  assert.equal(classifyConnection(null), '')
  assert.equal(classifyConnection({}), '')
})

test('the three answers on the page map to the three kinds', () => {
  assert.deepEqual(CONNECTION_KEYS, { 'this computer': 'local', 'another computer': 'remote', 'hermes cloud': 'cloud', 'nous cloud': 'cloud' })
})

test('a marker matches the start of a name, ignoring case and a leading slash', () => {
  assert.ok(startsWithMarker('academy-weekly-status', 'academy-'))
  assert.ok(startsWithMarker('Academy-Weekly', 'academy-'))
  assert.ok(startsWithMarker('/academy-friday', 'academy-'))
  assert.ok(!startsWithMarker('my-academy-skill', 'academy-'))
  assert.ok(!startsWithMarker('', 'academy-'))
  assert.ok(!startsWithMarker(undefined, 'academy-'))
})

test('a scheduled request is read for the five points it must say', () => {
  const good = 'Work in the projects folder. Read this week\'s notes. Write a summary of no more than ten bullets. Send it to me in a message. If anything fails, tell me which note could not be read.'
  const cues = promptCues(good)
  assert.equal(cues.length, 5)
  assert.ok(cues.every(c => c.found), JSON.stringify(cues.filter(c => !c.found)))
  const thin = promptCues('Summarize my week.')
  assert.ok(thin.filter(c => c.found).length < 4)
  assert.deepEqual(thin.map(c => c.id), ['where', 'read', 'result', 'send', 'fail'])
  assert.equal(promptCues(undefined).filter(c => c.found).length, 0)
})

test('the request text is found in whichever field Hermes keeps it', () => {
  assert.equal(jobRequest({ prompt: ' Do the thing. ' }), 'Do the thing.')
  assert.equal(jobRequest({ instructions: 'Read it.' }), 'Read it.')
  assert.equal(jobRequest({ name: 'x' }), '')
  assert.equal(jobRequest(null), '')
})

test('a schedule is found in whichever field Hermes keeps it', () => {
  assert.ok(jobHasSchedule({ schedule: '0 8 * * 5' }))
  assert.ok(jobHasSchedule({ cron: '0 8 * * *' }))
  assert.ok(jobHasSchedule({ next_run_at: '2026-10-10T08:00:00Z' }))
  assert.ok(!jobHasSchedule({ name: 'x', schedule: '' }))
  assert.ok(!jobHasSchedule({ every: null }))
  assert.ok(!jobHasSchedule(undefined))
})

test('a record time is read from seconds, milliseconds or text', () => {
  assert.equal(recordTime({ created_at: '2026-10-02T10:00:00Z' }), Date.parse('2026-10-02T10:00:00Z'))
  assert.equal(recordTime({ updated_at: 1790000000 }), 1790000000000)
  assert.equal(recordTime({ timestamp: 1790000000000 }), 1790000000000)
  assert.equal(recordTime({ name: 'x' }), null)
  assert.equal(recordTime({ created_at: 'nope' }), null)
})
