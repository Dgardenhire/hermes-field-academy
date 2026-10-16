// 0.7.0: the shapes Hermes really sends (read from its source: tui_gateway/methods_tools.py and
// tools/cronjob_job_args.py), which two live checks had wrong. Run by tests/test_release.py, or:
//   node --test tests/release.test.mjs

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { CONNECTION_KEYS, flattenSkills, jobHasSchedule, jobRequestRead, pastedMatches, promptCues } from '../desktop/src/learn.js'

test('skills are read from the grouped shape skills.manage list returns', () => {
  assert.deepEqual(flattenSkills({ skills: { general: ['academy-stem-order', 'notes'], work: ['invoices'] } }), ['academy-stem-order', 'notes', 'invoices'])
  assert.deepEqual(flattenSkills({ skills: [{ name: 'academy-a' }, 'b'] }), ['academy-a', 'b'])
  assert.deepEqual(flattenSkills(['x', { id: 'y' }]), ['x', 'y'])
  assert.deepEqual(flattenSkills(null), [])
  assert.deepEqual(flattenSkills({ skills: {} }), [])
})

test('a job request cut to a 100-character preview is marked as cut', () => {
  const long = 'Work in the Rent folder and read rent-roll.csv. List every unit that is more than five days late, with the amount'
  const job = { name: 'academy-rent', schedule: '0 8 * * 1', prompt_preview: `${long.slice(0, 100)}...` }
  const read = jobRequestRead(job)
  assert.equal(read.cut, true)
  assert.equal(read.text, long.slice(0, 100).trimEnd())
  assert.deepEqual(jobRequestRead({ prompt_preview: 'Short request.' }), { text: 'Short request.', cut: false })
  assert.deepEqual(jobRequestRead({ prompt: 'Full request here.' }), { text: 'Full request here.', cut: false })
  assert.deepEqual(jobRequestRead({}), { text: '', cut: false })
})

test('a pasted request must begin the way Hermes shows the job, and is then read for the five points', () => {
  const full = 'Work in the Rent folder and read rent-roll.csv. List every unit more than five days late with the amount owed. '
    + 'A good result is one line per unit, sorted by amount. Send it to me in this chat. If the file will not open, send me one line saying so.'
  const shown = jobRequestRead({ prompt_preview: `${full.slice(0, 100)}...` }).text
  assert.equal(pastedMatches(full, shown), true)
  assert.equal(pastedMatches(`  ${full.replace('Rent folder', 'Rent  folder')}`, shown), true)
  assert.equal(pastedMatches('List every late unit. Work in the Rent folder.', shown), false)
  assert.equal(pastedMatches('', shown), false)
  assert.equal(pastedMatches('anything', ''), false)
  assert.ok(promptCues(full).filter(c => c.found).length >= 4)
})

test('a schedule of "?" means Hermes has none', () => {
  assert.equal(jobHasSchedule({ schedule: '?' }), false)
  assert.equal(jobHasSchedule({ schedule: 'every monday at 8' }), true)
})

test('Hermes Cloud is a connection a learner can name', () => {
  assert.equal(CONNECTION_KEYS['hermes cloud'], 'cloud')
})
