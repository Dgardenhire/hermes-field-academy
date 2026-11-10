// The home page's preview box and its order. Run by tests/test_home_js.py, or: node --test tests/home.test.mjs

import { test } from 'node:test'
import assert from 'node:assert/strict'
import { PREVIEW_RUN, homePreview, replayRows, bracketAt, bracketWords } from '../desktop/src/desk_logic.js'

const live = { state: 'ready', events: [{ event_id: 'x', lane: 'chat', at: 5, title: 'Live' }], lanes: [], bracket: null }

test('the preview is never empty: loading, unreachable and not-ready all fall back to the bundled run', () => {
  for (const sample of [null, undefined, {}, 'x', { state: 'empty', words: 'not in this copy' }, { state: 'not_ready', events: [] }, { state: 'ready', events: [] }]) {
    assert.equal(homePreview(sample), PREVIEW_RUN)
  }
})

test('a ready live sample with moments in it wins over the bundled run', () => {
  assert.equal(homePreview(live), live)
})

test('the bundled run draws a strip with both lanes and a bracket where the chat and the files split', () => {
  const rows = replayRows(PREVIEW_RUN)
  assert.ok(rows.length >= 2)
  assert.ok(rows.some(r => r.chat.length) && rows.some(r => r.files.length))
  assert.ok(bracketAt(rows) >= 0)
  assert.match(bracketWords(PREVIEW_RUN), /deleted a note/)
})

test('the bundled run says it is a recorded sample, not a live run', () => {
  assert.equal(PREVIEW_RUN.state, 'ready')
  assert.equal(PREVIEW_RUN.sample, true)
})
