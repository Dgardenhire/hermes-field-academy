import { test } from 'node:test'
import assert from 'node:assert/strict'
import { cutWords, fieldProblems } from '../desktop/src/loop_a.js'

test('a description is shown as the skills index shows it: 60, or cut at the last whole word with three dots', () => {
  const admin = 'Use for the weekly admin routine our team runs after every Monday meeting: turning the notes into action items with owners and due dates.'
  assert.equal(admin.length, 137)
  assert.equal(cutWords(admin), 'Use for the weekly admin routine our team runs after...')
  assert.equal(cutWords('Use for the routine our office runs every month for tenants: the rent list.'), 'Use for the routine our office runs every month for...')
  assert.equal(cutWords('Use when asked for the Friday claims report, every week, for the office team, in full.'), 'Use when asked for the Friday claims report, every week...')
  assert.equal(cutWords('Use when asked for the Friday claims report.'), 'Use when asked for the Friday claims report.')
  assert.equal(cutWords('x'.repeat(60)).length, 60)
  assert.equal(cutWords('x'.repeat(61)), 'x'.repeat(57) + '...')
})

test('note fields: required, whole numbers, minimum length, optional', () => {
  const fields = [
    { id: 'steps', label: 'Steps', kind: 'lines', min: 3 },
    { id: 'rows', label: 'Rows', kind: 'int' },
    { id: 'why', label: 'Why', kind: 'textarea', required: false },
  ]
  assert.deepEqual(fieldProblems(fields, {}), ['Steps: this is needed.', 'Rows: this is needed.'])
  assert.deepEqual(fieldProblems(fields, { steps: 'ab', rows: 'six' }), ['Steps is too short.', 'Rows: a whole number.'])
  assert.deepEqual(fieldProblems(fields, { steps: 'read\nwrite', rows: '1,200' }), [])
  assert.deepEqual(fieldProblems([{ id: 'ok', label: 'OK', kind: 'bool' }], { ok: false }), [])
})
