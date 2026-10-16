// Prose: plain strings become paragraphs and real lists, so steps in a lesson read as steps.
//
//   node --test tests/prose.test.mjs

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { proseBlocks, withoutExampleWord } from '../desktop/src/prose-text.js'

test('one sentence is one paragraph', () => {
  assert.deepEqual(proseBlocks('Open Gateways in Settings.'), [{ kind: 'p', items: ['Open Gateways in Settings.'] }])
})

test('a lead line then numbered steps is a paragraph and an ordered list', () => {
  const blocks = proseBlocks('Do this:\n1. Open Gateways.\n2. Read the connection.\n3. Write it down.')
  assert.equal(blocks.length, 2)
  assert.deepEqual(blocks[0], { kind: 'p', items: ['Do this:'] })
  assert.deepEqual(blocks[1], { kind: 'ol', items: ['Open Gateways.', 'Read the connection.', 'Write it down.'] })
})

test('dash lines are a bulleted list and a blank line starts a new paragraph', () => {
  const blocks = proseBlocks('- one\n- two\n\nAfter the list.')
  assert.deepEqual(blocks, [{ kind: 'ul', items: ['one', 'two'] }, { kind: 'p', items: ['After the list.'] }])
})

test('single line breaks inside a paragraph are kept', () => {
  assert.deepEqual(proseBlocks('From: Dana\nTo: you'), [{ kind: 'p', items: ['From: Dana\nTo: you'] }])
})

test('a list right after a paragraph line needs no blank line', () => {
  assert.deepEqual(proseBlocks('Example:\n- Read the 22 appointments.\n- Wrote one text each.').map(b => b.kind), ['p', 'ul'])
})

test('empty or missing text gives no blocks', () => {
  assert.deepEqual(proseBlocks(''), [])
  assert.deepEqual(proseBlocks(undefined), [])
})

test('the word Example is dropped under a label that already says it', () => {
  assert.equal(withoutExampleWord('Example: Lakeside Dental.'), 'Lakeside Dental.')
  assert.equal(withoutExampleWord('Example:\n1. One\n2. Two'), '1. One\n2. Two')
  assert.equal(withoutExampleWord('Examples matter.'), 'Examples matter.')
})
