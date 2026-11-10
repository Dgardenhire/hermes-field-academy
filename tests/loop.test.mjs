// The Foundations mission loop's page logic: the twelve steps, the forms, the Compare words and the lesson
// Markdown. Run by tests/test_loop_js.py, or: node --test tests/loop.test.mjs

import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  STEPS, brierWords, currentStep, freezeMissing, gapWords, gridRow, guessKeyTerm, hostSupport, inlineSpans, labNoteProblems,
  latest, mdBlocks, memoryMath, percent, plantWords, practiceReady, practiceRows, predictionProblems, recallProblems,
  selfScoreProblems, shortHash, statusWord, stepStates, timerWords, tokensFromChars, homeAction, isPracticeProfile,
  calibrationTable, recordProblems, toggleWithhold, hoursWords, checkedByWords, hiddenWords,
} from '../desktop/src/loop.js'

const IDS = ['s1', 's2', 's3', 's4']
const entry = (kind, body) => ({ kind, body, created_at: '2026-10-21T10:00:00+00:00' })
const frozen = {
  attempt: { id: 1, status: 'lab', frozen_at: '2026-10-21T10:05:00+00:00', profile: 'academy-practice' },
  lab: { profiles: ['a', 'b'] },
  entries: [entry('recall', {}), entry('claim', {}), entry('standard', {}), entry('prediction', {})],
  runs: {},
}
const listing = [
  { name: 'academy-practice', which: 'a', status: 'ready', set_up: true },
  { name: 'academy-practice-b', which: 'b', status: 'ready', set_up: false },
]
const status = (view, list) => Object.fromEntries(stepStates(view, list).map(s => [s.id, s.status]))

test('there are twelve steps, practice before the idea', () => {
  assert.equal(STEPS.length, 12)
  const ids = STEPS.map(s => s.id)
  assert.ok(ids.indexOf('setup') < ids.indexOf('idea'))
  assert.deepEqual(ids.slice(-4), ['check', 'compare', 'fix', 'record'])
})

test('a fresh attempt opens at recall with everything after it locked', () => {
  const s = status({ attempt: { id: 1, status: 'open' }, entries: [], lab: { profiles: ['a'] } }, [])
  assert.equal(s.recall, 'open')
  assert.equal(s.claim, 'locked')
  assert.equal(s.record, 'locked')
  assert.equal(currentStep(stepStates({ entries: [] }, [])), 'recall')
})

test('steps open in order and practice needs every profile with the main one set up', () => {
  let s = status(frozen, [])
  assert.equal(s.predict, 'done')
  assert.equal(s.setup, 'open')
  assert.equal(s.lab, 'locked', 'the lab waits for the practice profile')
  assert.equal(practiceReady(frozen, [listing[0]]), false, 'the second profile is still needed')
  s = status(frozen, listing)
  assert.equal(s.setup, 'done')
  assert.equal(s.lab, 'open')
  assert.equal(currentStep(stepStates(frozen, listing)), 'idea')
  assert.equal(practiceReady({ ...frozen, attempt: { ...frozen.attempt, frozen_at: '' } }, listing), false)
})

test('the transfer note does not count as the first lab note, and checks gate on the self-score', () => {
  const v = { ...frozen, entries: [...frozen.entries, entry('lab_note', { fact: 'x', for: 'transfer' })] }
  assert.equal(status(v, listing).lab, 'open')
  const w = { ...frozen, entries: [...frozen.entries, entry('lab_note', { fact: 'x' }), entry('self_score', {})] }
  assert.equal(status(w, listing).check, 'open')
  const x = { ...w, runs: { first: {} }, entries: [...w.entries, entry('gap_note', {})] }
  assert.equal(status(x, listing).fix, 'open')
  assert.equal(status({ ...x, runs: { first: {}, after_fix: {}, transfer: {} } }, listing).record, 'open')
  assert.equal(status({ ...x, attempt: { ...x.attempt, status: 'done' }, runs: { first: {}, after_fix: {}, transfer: {} } }, listing).record, 'done')
})

test('latest picks the newest matching entry, and the freeze names what is missing', () => {
  const v = { entries: [entry('lab_note', { fact: 'a' }), entry('lab_note', { fact: 'b', for: 'transfer' }), entry('lab_note', { fact: 'c' })] }
  assert.equal(latest(v, 'lab_note').fact, 'c')
  assert.equal(latest(v, 'lab_note', b => b.for === 'transfer').fact, 'b')
  assert.equal(latest(v, 'gap_note'), null)
  assert.deepEqual(freezeMissing({ entries: [entry('recall', {})] }), ['your claim', 'the checks', 'your guess'])
})

test('forms say what is missing before anything is sent', () => {
  assert.equal(recallProblems(['x', ' '], ['a', 'b']).length, 1)
  assert.deepEqual(recallProblems(['x', 'y'], ['a', 'b']), [])
  const good = { checks: Object.fromEntries(IDS.map(id => [id, { expect_pass: true, confidence: 70 }])), where_wrong: 'The new chat check.' }
  assert.deepEqual(predictionProblems(good, IDS), [])
  const bad = { checks: { s1: { expect_pass: true, confidence: 40 } }, where_wrong: '' }
  const problems = predictionProblems(bad, IDS)
  assert.ok(problems.some(p => p.includes('50 to 100')))
  assert.ok(problems.some(p => p.includes('check 2')))
  assert.ok(problems.some(p => p.includes('slip')))
  assert.deepEqual(selfScoreProblems({ checks: { s1: { pass: true } } }, ['s1', 's2']), ['Score yourself on check 2.'])
  assert.deepEqual(labNoteProblems({ fact: 'Harbor Bakery uses QuickBooks', key_term: 'QuickBooks' }), [])
  assert.equal(labNoteProblems({ fact: 'short', key_term: '' }).length, 2)
  const t = labNoteProblems({ fact: 'Ada prefers short answers', key_term: 'short' }, true)
  assert.ok(t.some(p => p.includes('one-off')) && t.some(p => p.includes('saved')) && t.some(p => p.includes('why')))
  assert.deepEqual(labNoteProblems({ fact: 'Ada prefers short answers', key_term: 'short', one_off: 'printer quote at noon', one_off_saved: false, one_off_why: 'It matters for one afternoon only.' }, true), [])
  assert.ok(labNoteProblems({ fact: 'Harbor Bakery uses QuickBooks', key_term: 'x', removed_ok: 'a' }).length === 1)
})

test('a key word is guessed from the fact', () => {
  assert.equal(guessKeyTerm('Harbor Bakery uses QuickBooks Online'), 'QuickBooks')
  assert.equal(guessKeyTerm('reports are due by noon on fridays'), 'reports')
  assert.equal(guessKeyTerm(''), '')
})

test('the Work it out numbers use the learner own Memory line', () => {
  assert.deepEqual(memoryMath(260), { tokens: 260, full: 800, room: 540, notes: 12 })
  assert.equal(memoryMath(780).notes, 0)
  assert.equal(memoryMath(900).room, 0)
  assert.equal(memoryMath(''), null)
  assert.equal(memoryMath('x'), null)
  assert.equal(tokensFromChars(2200), 800)
})

test('Compare rows and the gap read in plain words', () => {
  const row = gridRow({ id: 's1', text: 'In the file', expect_pass: true, confidence: 80, self_pass: true, passed: false, passed_after_fix: true })
  assert.equal(row.guess, 'Pass, 80% sure')
  assert.equal(row.check, 'Fail')
  assert.equal(row.after, 'Pass')
  assert.equal(row.off, true)
  assert.equal(gridRow({ id: 's3', proves_by: 'rubric', passed: true, level: 3 }).check, 'Pass, level 3 of 4')
  assert.equal(gridRow({ id: 's2' }).check, 'Not yet')
  assert.equal(gapWords(2), 'You gave yourself 2 more checks than the checks did.')
  assert.equal(gapWords(-1), 'You gave yourself 1 fewer check than the checks did.')
  assert.equal(gapWords(0), 'You scored yourself the same as the checks did.')
  assert.equal(percent(0.75), '75%')
  assert.equal(percent(null), '—')
  assert.match(brierWords(0.04), /sharp/)
  assert.match(brierWords(0.4), /worse/)
  assert.equal(plantWords('memory_full').title, 'Memory was nearly full')
  assert.equal(shortHash('a'.repeat(64)).length, 12)
  assert.equal(timerWords(165), '2:45')
  assert.equal(timerWords(-3), '0:00')
})

test('host features are detected, never assumed', () => {
  assert.deepEqual(hostSupport({ newChat() {}, request() {} }), { newChat: true, deleteProfile: false, requestProfile: false, request: true })
  assert.deepEqual(hostSupport(null), { newChat: false, deleteProfile: false, requestProfile: false, request: false })
  const rows = practiceRows([{ name: 'academy-practice', which: 'a', status: 'removed' }, { name: 'academy-practice-2', which: 'a', status: 'ready' }], ['a', 'b'])
  assert.equal(rows[0].profile.name, 'academy-practice-2')
  assert.equal(rows[1].profile, null)
  assert.equal(statusWord({ status: 'in_use' }), 'In use')
  assert.equal(statusWord(null), 'Not made yet')
})

test('lesson Markdown becomes headings, lists, quotes and tables, with no HTML', () => {
  const blocks = mdBlocks([
    '## What is going on', '', 'Two files.', 'Short on purpose.', '', '### Sub', '- **MEMORY.md** notes', '- `USER.md` you',
    '', '1. One', '2. Two', '   more', '', '> A quote', '>', '> Second', '', '| Level | What |', '|---|---|', '| 1 | Weak |', '', '<b>x</b>',
  ].join('\n'))
  assert.deepEqual(blocks.map(b => b.kind), ['h2', 'p', 'h3', 'ul', 'ol', 'quote', 'table', 'p'])
  assert.equal(blocks[1].text, 'Two files. Short on purpose.')
  assert.deepEqual(blocks[4].items, ['One', 'Two more'])
  assert.deepEqual(blocks[5].items, ['A quote', 'Second'])
  assert.deepEqual(blocks[6].head, ['Level', 'What'])
  assert.deepEqual(blocks[6].rows, [['1', 'Weak']])
  assert.equal(blocks[7].text, '<b>x</b>', 'HTML stays text')
  const spans = inlineSpans('As of Hermes 0.22.4, a **save** shows `29%` here and as of Hermes 0.22 too.')
  assert.deepEqual(spans.map(s => s.kind), ['asof', 'text', 'strong', 'text', 'code', 'text', 'asof', 'text'])
  assert.equal(spans[0].text, 'As of Hermes 0.22.4')
  assert.deepEqual(inlineSpans('a **b'), [{ kind: 'text', text: 'a **b' }])
})

// A span tree as a short string: **strong**, _em_, `code`, [asof], so a test reads like the text.
const flat = spans => spans.map(s => s.kind === 'strong' ? `**${flat(s.children)}**` : s.kind === 'em' ? `_${flat(s.children)}_`
  : s.kind === 'code' ? `\`${s.text}\`` : s.kind === 'asof' ? `[${s.text}]` : s.text).join('')

test('code spans render inside bold and italic, and a star inside code is just a star', () => {
  const bold = inlineSpans('**Fit the `files` connector to the job,** then save it.')
  assert.equal(bold[0].kind, 'strong')
  assert.deepEqual(bold[0].children, [{ kind: 'text', text: 'Fit the ' }, { kind: 'code', text: 'files' }, { kind: 'text', text: ' connector to the job,' }])
  assert.equal(bold[0].text, 'Fit the files connector to the job,')
  assert.ok(!JSON.stringify(bold).includes('`'), 'no backtick is left in the text')
  const em = inlineSpans('*Type `/rollback` yourself: Field Academy does not.*')
  assert.equal(em.length, 1)
  assert.equal(em[0].kind, 'em')
  assert.deepEqual(em[0].children.map(c => c.kind), ['text', 'code', 'text'])
  assert.equal(em[0].children[1].text, '/rollback')
  assert.equal(flat(inlineSpans('**a *b `c`* d** and `x*y*z` and *e*')), '**a _b `c`_ d** and `x*y*z` and _e_')
  assert.equal(flat(inlineSpans('**As of Hermes 0.22.4** `1`')), '**[As of Hermes 0.22.4]** `1`')
  for (const plain of ['2 * 3 * 4', 'a **b', 'a *b', '* not a list here', 'files `*.md`']) {
    assert.ok(!inlineSpans(plain).some(s => s.kind === 'strong' || s.kind === 'em'), plain)
  }
  assert.equal(flat(inlineSpans('files `*.md`')), 'files `*.md`')
})

test('the hidden checks line is the same plain words for every mission', () => {
  assert.equal(hiddenWords({ count: 1, passed: 0 }), "1 check you can't see: 0 of 1 met. Something in the practice profile still needs fixing.")
  assert.equal(hiddenWords({ count: 2, passed: 2 }), "2 checks you can't see: 2 of 2 met.")
  assert.equal(hiddenWords({ count: 0, passed: 0 }), '')
  assert.ok(!hiddenWords({ count: 1, passed: 0 }).includes('fact'))
})

test('the page never calls its backend while a practice profile is active, and only the page itself goes back home', () => {
  for (const name of ['academy-practice', 'academy-practice-b', 'academy-practice-2', 'academy-practice-b-12']) assert.ok(isPracticeProfile(name), name)
  for (const name of ['default', 'work', 'academy-practice-x', 'my-academy-practice', '']) assert.equal(isPracticeProfile(name), false, name)
  const home = { profile: 'default', connectionId: null }
  assert.equal(homeAction('default', home, true, false), 'call')
  assert.equal(homeAction('academy-practice', home, true, true), 'repin')
  assert.equal(homeAction('academy-practice', home, true, false), 'wait', 'a background poll never moves the profile')
  assert.equal(homeAction('academy-practice', home, false, true), 'wait', 'no ensureAgent on this desktop')
  assert.equal(homeAction('academy-practice', null, true, true), 'wait', 'no known home')
  assert.equal(homeAction('academy-practice-b', { profile: 'academy-practice' }, true, true), 'wait')
})

test('the calibration table keeps empty rows empty and has no average', () => {
  const rows = calibrationTable([
    { mission: 'f.loop', title: 'Loop', in_record: true, checks: 4, predicted: 4, self_scored: 3, passed_first: 2 },
    { mission: 'f.cost', title: 'Cost', in_record: false, checks: null, predicted: null, self_scored: null, passed_first: null },
  ])
  assert.deepEqual(rows[0], { id: 'f.loop', title: 'Loop', empty: false, checks: '4', predicted: '4', selfScored: '3', passed: '2' })
  assert.deepEqual(rows[1], { id: 'f.cost', title: 'Cost', empty: true, checks: '', predicted: '', selfScored: '', passed: '' })
  assert.equal(rows.length, 2)
  assert.deepEqual(calibrationTable(null), [])
})

test('the record form asks for a name and the limits in your own words', () => {
  assert.deepEqual(recordProblems({}), ['Type the name you want on your Field Record.', 'Write two or three lines on what this record doesn\'t show, in your own words.'])
  assert.deepEqual(recordProblems({ holder: 'Ada', limits: 'It shows practice work on my laptop only.' }), [])
  assert.deepEqual(recordProblems({ holder: 'Ada', limits: 'It shows practice work on my laptop only.', caseText: 'word '.repeat(301) }), ['Keep the case under 300 words.'])
})

test('withholding an excerpt adds or removes it once', () => {
  assert.deepEqual(toggleWithhold([3, 1], 2, true), [1, 2, 3])
  assert.deepEqual(toggleWithhold([1, 2], 2, true), [1, 2])
  assert.deepEqual(toggleWithhold([1, 2], 1, false), [2])
  assert.deepEqual(toggleWithhold(null, 5, true), [5])
})

test('hours and the checked-by tag read plainly', () => {
  assert.equal(hoursWords({ active_minutes: 0 }), 'Less than a minute of active time')
  assert.equal(hoursWords({ active_minutes: 1 }), '1 minute of active time')
  assert.equal(hoursWords({ active_minutes: 54, hours: 0.9 }), '54 minutes of active time')
  assert.equal(hoursWords({ active_minutes: 200, hours: 3.3 }), '3.3 hours of active time')
  assert.equal(checkedByWords('your Hermes graded it'), 'Your Hermes graded it')
  assert.equal(checkedByWords(undefined), '')
})
