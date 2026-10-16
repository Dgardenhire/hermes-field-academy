// The Deployer path's reading logic, with made-up Hermes records. Run through tests/test_deployer_ui.py.

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { collectRunTimes, daysSince, findJobs, findSessions, folderUrl, sampleFromHermes, stateWords, toIso, versionFrom } from '../desktop/src/deploy.js'

test('toIso reads ISO strings, epoch seconds and epoch milliseconds, and nothing else', () => {
  assert.equal(toIso('2026-10-03T09:00:00Z'), '2026-10-03T09:00:00Z')
  assert.equal(toIso('2026-10-03 09:00:00'), '2026-10-03T09:00:00Z')
  assert.equal(toIso('2026-10-03T09:00:00+02:00'), '2026-10-03T07:00:00Z')
  assert.equal(toIso(1790000000), '2026-09-21T14:13:20Z')
  assert.equal(toIso(1790000000000), '2026-09-21T14:13:20Z')
  for (const bad of ['', 'yesterday', null, undefined, 12, 4.5e9, {}, [], true, 'abc 2026']) assert.equal(toIso(bad), '', String(bad))
})

test('a flat last-run field and a nested history are read the same way', () => {
  assert.deepEqual(collectRunTimes({ name: 'job', last_run_at: '2026-10-03T09:00:00Z' }).times, ['2026-10-03T09:00:00Z'])
  const nested = collectRunTimes({ name: 'job', runs: [{ started_at: '2026-10-03T09:00:00Z', status: 'ok' }, { started_at: '2026-10-04T09:00:00Z', status: 'ok' }] })
  assert.equal(nested.times.length, 2)
  assert.equal(nested.failed.length, 0)
})

test('a failed run is kept apart from a good one', () => {
  const read = collectRunTimes({ history: [{ started_at: '2026-10-03T09:00:00Z', status: 'ok' }, { started_at: '2026-10-03T21:00:00Z', status: 'failed' }, { started_at: '2026-10-04T09:00:00Z', error: 'authorization error' }] })
  assert.deepEqual(read.times, ['2026-10-03T09:00:00Z'])
  assert.deepEqual(read.failed, ['2026-10-03T21:00:00Z', '2026-10-04T09:00:00Z'])
})

test('a number only counts under a key that names a time, so counts and ids are not read as dates', () => {
  const read = collectRunTimes({ run_count: 1790000000, id: 1790000001, last_run: 1790000002, attempts: 3 })
  assert.deepEqual(read.times, ['2026-09-21T14:13:22Z'])
})

test('it never throws on strange input and is bounded', () => {
  for (const odd of [null, undefined, 5, 'x', [], {}, [[[]]], { a: { b: { c: { d: { e: { f: { g: { h: '2026-10-03T09:00:00Z' } } } } } } } }]) {
    assert.doesNotThrow(() => collectRunTimes(odd))
  }
  const big = { runs: Array.from({ length: 5000 }, (_, i) => ({ started_at: new Date(1790000000000 + i * 60000).toISOString() })) }
  assert.ok(collectRunTimes(big).times.length <= 501)
  const cyclic = { name: 'x' }
  cyclic.self = { next: { next: { next: { next: { next: { next: { next: cyclic } } } } } } }
  assert.doesNotThrow(() => collectRunTimes(cyclic))
})

test('jobs and chats are found by name, ignoring case and nothing is assumed about the fields', () => {
  const jobs = [{ name: 'Deployer-Calendar' }, { title: 'other' }, { id: 'deployer-calendar' }, null, 7]
  assert.equal(findJobs(jobs, 'deployer-calendar').length, 2)
  assert.equal(findJobs(jobs, '').length, 0)
  assert.equal(findJobs(null, 'x').length, 0)
  assert.equal(findSessions([{ title: 'cron: deployer-calendar run' }, { title: 'Weekly notes' }], 'deployer-calendar').length, 1)
})

test('what was read comes with a note that says what was found and what was not', () => {
  const missing = sampleFromHermes({ jobs: [{ name: 'other' }], sessions: [] }, 'deployer-x')
  assert.equal(missing.found, false)
  assert.equal(missing.jobFound, false)
  assert.match(missing.note, /does not show a job named deployer-x/)
  const bare = sampleFromHermes({ jobs: [{ name: 'deployer-x', schedule: '0 9 * * *' }], sessions: [] }, 'deployer-x')
  assert.equal(bare.found, false)
  assert.equal(bare.jobFound, true)
  assert.match(bare.note, /shows no run times/)
  const ok = sampleFromHermes({ jobs: [{ name: 'deployer-x', runs: [{ started_at: '2026-10-03T09:00:00Z' }, { started_at: '2026-10-04T09:00:00Z', status: 'error' }] }], sessions: [] }, 'deployer-x')
  assert.equal(ok.found, true)
  assert.equal(ok.sample.times.length, 1)
  assert.equal(ok.sample.failed.length, 1)
  assert.match(ok.note, /Read 1 run times and 1 failed runs/)
  assert.equal(ok.sample.source, 'desktop scheduler list')
  const chat = sampleFromHermes({ jobs: [], sessions: [{ title: 'deployer-x', created_at: '2026-10-05T09:00:00Z' }] }, 'deployer-x')
  assert.equal(chat.found, true)
  assert.equal(chat.sample.source, 'desktop chat list')
})

test('the sample carries only times, never a prompt or a message', () => {
  const read = sampleFromHermes({ jobs: [{ name: 'deployer-x', prompt: 'Read my private notes and send the secret plan', last_run_at: '2026-10-03T09:00:00Z', token: 'abc' }], sessions: [] }, 'deployer-x')
  assert.equal(JSON.stringify(read.sample).includes('private'), false)
  assert.equal(JSON.stringify(read.sample).includes('abc'), false)
  assert.deepEqual(Object.keys(read.sample).sort(), ['failed', 'source', 'times'])
})

test('the version is read from a runtime answer only when it looks like one', () => {
  assert.equal(versionFrom({ version: '0.21.3' }), '0.21.3')
  assert.equal(versionFrom({ hermes_version: 'v1.2' }), 'v1.2')
  assert.equal(versionFrom({ version: 'latest' }), '')
  assert.equal(versionFrom(null), '')
  assert.equal(versionFrom({ home: '~/.hermes' }), '')
})

test('state words, folder addresses and days', () => {
  assert.equal(stateWords('verified'), 'Passed')
  assert.equal(stateWords('awaiting_review'), 'Waiting for the reviewer')
  assert.equal(stateWords('nonsense'), 'Not started')
  assert.equal(folderUrl('/Users/a b/field academy/labs'), 'file:///Users/a%20b/field%20academy/labs')
  assert.equal(folderUrl(''), '')
  assert.equal(daysSince('2026-10-01T09:00:00Z', new Date('2026-10-04T10:00:00Z')), 3)
  assert.equal(daysSince('', new Date()), 0)
})

test('the module imports nothing', async () => {
  const { readFileSync } = await import('node:fs')
  const text = readFileSync(new URL('../desktop/src/deploy.js', import.meta.url), 'utf8')
  assert.deepEqual(text.split('\n').filter(line => line.startsWith('import ')), [])
})
