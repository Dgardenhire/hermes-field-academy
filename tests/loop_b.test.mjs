// Page logic for Foundations missions 7 to 11. Run by tests/test_loop_js.py's node run, or: node --test tests/loop_b.test.mjs

import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  addedJobId, exampleBlock, factWords, jobCalls, jobStopWords, makeJobs, noteBody, noteFieldProblems, panelsFor, phaseFields, rollbackSample, scheduledLine, watchWords,
} from '../desktop/src/loop_b.js'
import { mdBlocks } from '../desktop/src/loop.js'

const mission = {
  lab: {
    panels: ['folder', 'jobs'],
    note_fields: [
      { id: 'job_name', label: 'Job', kind: 'text', required: true, max: 10 },
      { id: 'layer', label: 'Layer', kind: 'choice', choices: [{ value: 'model' }, { value: 'connector' }], required: true },
      { id: 'minutes', label: 'Minutes', kind: 'number' },
      { id: 'why', label: 'Why', kind: 'long', for: 'transfer', required: true, min: 5 },
    ],
  },
}

test('fields split by phase and problems mirror the backend', () => {
  assert.deepEqual(phaseFields(mission).map(f => f.id), ['job_name', 'layer', 'minutes'])
  assert.deepEqual(phaseFields(mission, true).map(f => f.id), ['why'])
  assert.deepEqual(noteFieldProblems(phaseFields(mission), {}), ['Job: this one is needed.', 'Layer: this one is needed.'])
  assert.deepEqual(noteFieldProblems(phaseFields(mission), { job_name: 'a very long name', layer: 'app', minutes: 'ten' }),
    ['Job: at most 10 characters.', 'Layer: pick one of the choices.', 'Minutes: a whole number.'])
  assert.deepEqual(noteFieldProblems(phaseFields(mission), { job_name: 'late', layer: 'model', minutes: '12' }), [])
  assert.deepEqual(noteFieldProblems(phaseFields(mission, true), { why: 'no' }), ['Why: a little more, please.'])
})

test('the note body keeps this phase only, numbers as numbers', () => {
  assert.deepEqual(noteBody(phaseFields(mission), { job_name: 'late', layer: 'model', minutes: '12', why: 'x' }),
    { for: 'first', job_name: 'late', layer: 'model', minutes: 12 })
  assert.deepEqual(noteBody(phaseFields(mission, true), { why: 'because' }, true), { for: 'transfer', why: 'because' })
})

test('the Scheduled jobs line passes only on the practice profile', () => {
  assert.equal(scheduledLine('academy-practice', 'academy-practice').state, 'pass')
  assert.equal(scheduledLine('default', 'academy-practice').state, 'fail')
  assert.match(scheduledLine('default', 'academy-practice').text, /Open practice chat/)
  assert.equal(scheduledLine('', 'academy-practice').state, 'unknown')
})

test('the two-run notice and the cleanup reminder', () => {
  assert.equal(watchWords(null).tone, 'idle')
  assert.equal(watchWords({ ready: true, found: false, job: 'x' }).tone, 'warn')
  assert.match(watchWords({ ready: true, found: true, runs: 1, landed: false }).title, /1 of 2/)
  const done = watchWords({ ready: true, found: true, runs: 2, late: 1, landed: true, still_on: true })
  assert.equal(done.title, 'Two scheduled runs have landed')
  assert.match(done.text, /pause or delete it now/)
  assert.match(done.text, /1 of them late/)
})

test('jobs are made with add, then pause, and the id is read from either shape', () => {
  assert.deepEqual(jobCalls({ name: 'a', schedule: '0 * * * *', prompt: 'p', deliver: 'telgram', pause: true }),
    { add: { action: 'add', name: 'a', schedule: '0 * * * *', prompt: 'p', deliver: 'telgram' }, pause: true })
  assert.equal(addedJobId({ result: { job_id: 'j1' } }), 'j1')
  assert.equal(addedJobId({ job: { job_id: 'j2' } }), 'j2')
  assert.equal(addedJobId(null), '')
})

/** A stand-in for Hermes's cron.manage in the practice profile, and for the backend's /jobs-made (practice.jobs_made):
 * the backend reads the list, records a job unless it was meant paused and lists on, and reports that one as still_on. */
function fakeHermes({ plan, addReply = (job) => ({ result: { job_id: job.id } }), pauseWorks = true, removeWorks = true, lists = true, reportFails = false } = {}) {
  const list = []
  const made = new Set()
  const sent = []
  let n = 0
  const call = async (params) => {
    sent.push(params)
    const find = () => list.find(j => j.id === params.name) || list.find(j => j.name === params.name)
    if (params.action === 'add') {
      const job = { id: `job-${++n}`, name: params.name, enabled: true }
      if (lists) list.push(job)
      return addReply(job)
    }
    const job = find()
    if (!job) throw new Error(`Job with ID or name '${params.name}' not found.`)
    if (params.action === 'pause') { if (pauseWorks) job.enabled = false; return { result: { success: true } } }
    if (params.action === 'remove') {
      if (!removeWorks) throw new Error('remove failed')
      list.splice(list.indexOf(job), 1)
      return { result: { success: true } }
    }
    throw new Error('unknown')
  }
  const state = () => {
    const todo = plan.filter(j => !made.has(j.name))
    const still_on = todo.filter(j => j.pause && list.some(l => l.name === j.name && l.enabled !== false))
      .map(j => ({ name: j.name, id: list.find(l => l.name === j.name).id }))
    return { jobs: todo.filter(j => !still_on.some(s => s.name === j.name)), still_on, made: [...made].sort() }
  }
  const report = async () => {
    if (reportFails) throw new Error('the backend is down')
    for (const j of state().jobs) {
      const found = list.find(l => l.name === j.name)
      if (found && !(j.pause && found.enabled !== false)) made.add(j.name)
    }
    return state()
  }
  return { call, report, state, list, sent }
}

const PLAN = [
  { name: 'draft-orders', schedule: '0 * * * *', prompt: 'p', deliver: 'local', pause: true },
  { name: 'late-list', schedule: '0 * * * *', prompt: 'q', deliver: 'local', pause: false },
]

test('B1: a job meant paused is paused by the id the add returned, confirmed from the list, then the next is made', async () => {
  const h = fakeHermes({ plan: PLAN })
  const out = await makeJobs(h.state(), { ...h, profile: 'academy-practice' })
  assert.equal(out.ok, true)
  assert.deepEqual(h.sent.filter(c => c.action === 'pause'), [{ action: 'pause', name: 'job-1' }])
  assert.equal(h.list.find(j => j.name === 'draft-orders').enabled, false)
  assert.deepEqual(out.state.made, ['draft-orders', 'late-list'])
})

test('B1: an add reply with no id the page knows is paused by the id the job list gives', async () => {
  const h = fakeHermes({ plan: PLAN, addReply: () => ({ result: { ok: true, message: 'created' } }) })
  const out = await makeJobs(h.state(), { ...h, profile: 'academy-practice' })
  assert.equal(out.ok, true)
  assert.deepEqual(h.sent.filter(c => c.action === 'pause'), [{ action: 'pause', name: 'job-1' }])
  assert.equal(h.list.every(j => j.name !== 'draft-orders' || j.enabled === false), true)
})

test('B1: a job that won\'t pause is deleted, nothing after it is made, and the page says so', async () => {
  const h = fakeHermes({ plan: PLAN, addReply: () => ({}), pauseWorks: false })
  const out = await makeJobs(h.state(), { ...h, profile: 'academy-practice' })
  assert.equal(out.ok, false)
  assert.deepEqual(h.list, [])
  assert.deepEqual(h.sent.map(c => c.action), ['add', 'pause', 'remove'])
  assert.equal(out.message, jobStopWords('removed', 'draft-orders', 'academy-practice'))
  assert.match(out.message, /deleted it\. Nothing from it runs/)
})

test('B1: a job that won\'t pause or delete stops everything and tells the learner to stop it', async () => {
  const h = fakeHermes({ plan: PLAN, pauseWorks: false, removeWorks: false })
  const out = await makeJobs(h.state(), { ...h, profile: 'academy-practice' })
  assert.equal(out.ok, false)
  assert.equal(h.sent.filter(c => c.action === 'add').length, 1)
  assert.match(out.message, /draft-orders is on in academy-practice/)
  assert.match(out.message, /pause or delete draft-orders, then press Try again/)
  assert.deepEqual(out.state.still_on, [{ name: 'draft-orders', id: 'job-1' }])
})

test('B1: a job the list never shows is paused by name, and nothing after it is made', async () => {
  const h = fakeHermes({ plan: PLAN, addReply: () => ({}), lists: false })
  const out = await makeJobs(h.state(), { ...h, profile: 'academy-practice' })
  assert.equal(out.ok, false)
  assert.deepEqual(h.sent.map(c => [c.action, c.name]), [['add', 'draft-orders'], ['pause', 'draft-orders']])
  assert.match(out.message, /Hermes didn't confirm it made draft-orders/)
})

test('B1: when the job list can\'t be read the job is paused anyway and the page says it couldn\'t confirm', async () => {
  const h = fakeHermes({ plan: PLAN, reportFails: true })
  const out = await makeJobs(h.state(), { ...h, profile: 'academy-practice' })
  assert.equal(out.ok, false)
  assert.equal(h.list[0].enabled, false)
  assert.match(out.message, /couldn't read the job list to confirm draft-orders is paused \(the backend is down\)/)
})

test('B1: a job left on by an earlier try is paused by its listed id before anything is made', async () => {
  const left = fakeHermes({ plan: PLAN })
  left.list.push({ id: 'job-9', name: 'draft-orders', enabled: true })
  const before = left.state()
  assert.deepEqual(before.still_on, [{ name: 'draft-orders', id: 'job-9' }])
  assert.deepEqual(before.jobs.map(j => j.name), ['late-list'])
  const out = await makeJobs(before, { ...left, profile: 'p' })
  assert.equal(out.ok, true)
  assert.deepEqual(left.sent.map(c => [c.action, c.name]), [['pause', 'job-9'], ['add', 'late-list']])
})

test('B1: a job meant to run whose add fails is still reported as a failure', async () => {
  const h = fakeHermes({ plan: [PLAN[1]] })
  const call = async (params) => { if (params.action === 'add') throw new Error('gateway closed'); return h.call(params) }
  await assert.rejects(makeJobs(h.state(), { call, report: h.report }), /gateway closed/)
})

test('the rollback sample keeps messages only, and the example block reads as settings', () => {
  const s = rollbackSample({ result: { enabled: true, checkpoints: [{ hash: 'abc', message: 'pre-rollback snapshot (restoring to aa)', timestamp: 't' }] } })
  assert.deepEqual(s, { source: 'rollback.list', enabled: true, checkpoints: [{ message: 'pre-rollback snapshot (restoring to aa)', timestamp: 't' }] })
  assert.match(exampleBlock({ trust: 'untrusted' }), /"mcpServers"/)
  assert.deepEqual(panelsFor(mission), ['folder', 'jobs'])
})

test('lesson Markdown keeps a fenced block and an ordered list that resumes after it', () => {
  const blocks = mdBlocks('1. **Replace.** Paste it.\n\n   ```json\n   {\n     "a": 1\n   }\n   ```\n\n2. **Save.**\n3. Next.')
  assert.deepEqual(blocks.map(b => b.kind), ['ol', 'code', 'ol'])
  assert.equal(blocks[1].text, '{\n  "a": 1\n}')
  assert.equal(blocks[2].start, 2)
})

test('mission 9 grid facts show the choice words, never the raw value', () => {
  const door = [{ value: 'no_connector', label: 'No connector in this profile' }, { value: 'asks', label: 'It asks first (untrusted)' },
    { value: 'nothing', label: 'Nothing asks (full trust)' }]
  const undo = [{ value: 'undo', label: 'A snapshot can undo it' }, { value: 'nothing', label: 'Nothing undoes it' }]
  const safety = { lab: { note_fields: [
    { id: 'cb', label: 'Connected tools, before', kind: 'choice', choices: door },
    { id: 'cb_why', label: 'How you know', kind: 'text' },
    { id: 'ca', label: 'Connected tools, after', kind: 'choice', choices: undo },
  ] } }
  assert.equal(factWords({ label: 'Connected tools, before', value: 'you: no_connector; the profile: asks' }, safety),
    'You: No connector in this profile. The profile: It asks first (untrusted).')
  assert.equal(factWords({ label: 'Connected tools, after', value: 'you: nothing; the profile: undo' }, safety),
    'You: Nothing undoes it. The profile: A snapshot can undo it.')
  // A cell with no choices to read still never shows an underscore.
  assert.equal(factWords({ label: 'Terminal, before', value: 'you: some_slip; the profile: asks' }, safety), 'You: some slip. The profile: asks.')
  // Facts already in words, and facts from other checks, pass through unchanged.
  const words = 'You: No connector in this profile. The profile: No connector in this profile.'
  assert.equal(factWords({ label: 'Connected tools, before', value: words }, safety), words)
  assert.equal(factWords({ label: 'Approval mode', value: 'off' }, safety), 'off')
  assert.equal(factWords({ label: 'Connected tools, before', value: 'you: no_connector; the profile: asks' }, null),
    'You: no connector. The profile: asks.')
})
