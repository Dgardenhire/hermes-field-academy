// The mission desk's pure logic (desktop/src/desk_logic.js): phases, the Compare line, the replay's rows and bracket,
// what the Field guide is waiting on, source chips and the grade quote. Run: node --test tests/desk.test.mjs
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  PHASES, bracketWords, checkHeadline, heldSentence, replayStatus, resumeWords, explainMerged, explainShown, fixChanges, heldCommands, huntStarted, runHeadline, scoreSentence, bracketAt, compareLine, fetchingWords, guideFetching, phaseBarWords, phaseRows, quoteParts, replayRows, sourceWords, usedRungs,
} from '../desktop/src/desk_logic.js'
import { STEPS, stepStates, currentStep, freezeMissing } from '../desktop/src/loop.js'

const real = JSON.parse(readFileSync(new URL('../harness/desk_real.json', import.meta.url), 'utf8'))

test('the four phases hold all twelve steps once, in order', () => {
  assert.deepEqual(PHASES.flatMap(p => p.steps), STEPS.map(s => s.id))
  assert.deepEqual(PHASES.map(p => p.title), ['Get ready', 'Learn', 'Do', 'See what happened'])
})

test('a locked phase shows one lock line, never a lock per step', () => {
  const states = STEPS.map((s, i) => ({ ...s, status: i < 3 ? 'done' : i === 3 ? 'open' : 'locked' }))
  const rows = phaseRows(states, 'setup')
  assert.equal(rows[3].locked, true)
  assert.equal(rows[3].lockLine, 'Opens after Did it work?')
  assert.equal(rows[0].lockLine, '')
  assert.equal(phaseBarWords(states, 'check'), 'See what happened: Check')
})

test('the Compare line counts what you said beside what Hermes shows, from the real run', () => {
  const line = compareLine(real.fixtures.attempt_at_compare.compare)
  assert.equal(line.said, 4)
  assert.equal(line.shows, 0)
  assert.equal(line.text, undefined, 'no score slogan is built any more')
  assert.equal(line.gap, 4)
  assert.match(line.note, /One check waits/)
  assert.equal(compareLine({ said: 4, shows: 1, of: 4 }).shows, 1)
})

test('the replay puts the save and the held file on one row, with the bracket on it', () => {
  const rows = replayRows(real.replay)
  const row = rows.find(r => r.bracket)
  assert.ok(row, 'a bracket row')
  assert.ok(row.chat.some(e => e.event_id === real.replay.bracket.from))
  assert.ok(row.files.some(e => e.event_id === real.replay.bracket.to))
  assert.ok(bracketAt(rows) > 0 && bracketAt(rows) < 1)
  assert.equal(replayRows({ events: [] }).length, 0)
  assert.equal(bracketAt([]), -1)
})

test('the guide looks again only while something is fetching', () => {
  assert.equal(guideFetching(real.guide_check_fetching), true)
  assert.equal(guideFetching(real.guide_check_ready), false)
  assert.equal(fetchingWords(100, 106.4), 'Fetching, 6 s')
  assert.equal(fetchingWords(undefined, 5), 'Fetching')
  assert.equal(usedRungs(real.guide_compare).nudge, true)
  assert.equal(usedRungs(real.guide_check_ready).nudge, false)
})

test('source chips say where a sentence came from in plain words', () => {
  assert.equal(sourceWords('m3'), 'Your chat')
  assert.equal(sourceWords('f-pending-1'), 'Your files')
  assert.equal(sourceWords('idea-11'), 'The idea')
  assert.equal(sourceWords('asof-6'), 'Hermes facts')
})

test('the grade quote is marked inside the learner\'s own answer, or not at all', () => {
  const parts = quoteParts(real.grade_ok.answer, real.grade_ok.quote)
  assert.equal(parts.filter(p => p.mark).map(p => p.text).join(''), real.grade_ok.quote)
  assert.equal(parts.map(p => p.text).join(''), real.grade_ok.answer)
  assert.deepEqual(quoteParts('abc', 'zzz'), [{ text: 'abc', mark: false }])
})

test('a First Flight skips Recall and the claim, opens on the guess, and needs only the guess to set up', () => {
  const view = real.first_flight_start
  const states = stepStates(view, [])
  assert.equal(states.find(s => s.id === 'recall').status, 'skipped')
  assert.equal(states.find(s => s.id === 'claim').status, 'skipped')
  assert.equal(currentStep(states), 'predict')
  assert.deepEqual(freezeMissing(view), ['your guess'])
})

test('the headline is a sentence about this run, built from its own data', () => {
  const first = real.fixtures.attempt_at_check.runs.first
  const h = runHeadline(real.replay, first.checks)
  assert.match(h.headline, /^Hermes said it saved your note at \d{1,2}:\d{2} [AP]M\. It didn't: the note is still waiting for your approval\.$/)
  assert.doesNotMatch(h.headline, /\b\d+ of \d+\b/)
  // Without the replay it falls back to the checks that missed, in their own words.
  assert.equal(runHeadline(null, first.checks).headline, first.checks.filter(c => !c.passed).slice(0, 2).map(c => c.title + '.').join(' '))
  assert.equal(checkHeadline(first), runHeadline(null, first.checks).headline)
  assert.match(scoreSentence(real.fixtures.attempt_at_compare.compare), /^You marked every check as passed before looking; none of them has passed yet\./)
  assert.match(bracketWords(real.replay), /the chat showed Saved to memory, but the note went to the approval queue \(pending\/memory\/\), not MEMORY\.md\./)
})

test('the sample run has a different hidden problem from the practice, and the hero says it once', () => {
  const sample = JSON.parse(readFileSync(new URL('../content/sample_run.json', import.meta.url), 'utf8'))
  assert.equal(sample.snag, 'memory_full', 'First Flight plants a held save; the sample must not show that answer')
  const h = runHeadline(sample, sample.checks, "the learner's")
  assert.match(h.headline, /^Hermes said it saved the learner's note at \d{1,2}:\d{2} [AP]M\. It did, but to make room it deleted a note the practice jobs rely on\.$/)
  assert.doesNotMatch(JSON.stringify(sample), /approv/i)
  assert.match(bracketWords(sample), /Hermes deleted a note from MEMORY\.md/)
  // The practice's own hero: one sentence, no second line repeating what the replay's meter shows.
  assert.equal(runHeadline(real.replay, real.fixtures.attempt_at_check.runs.first.checks).detail, '')
})

test('the fix approves the one held save by its id, read from the held file', () => {
  const held = real.replay.events.find(e => e.kind === 'file:pending')
  const cmds = heldCommands(held.path)
  assert.equal(cmds.length, 2)
  assert.equal(cmds[0], '/memory pending')
  assert.match(cmds[1], /^\/memory approve [0-9a-f]{8}$/)
  assert.deepEqual(heldCommands('memories/MEMORY.md'), [])
  assert.deepEqual(heldCommands('pending/memory/../../x.json'), [])
})

test('Check holds back where to look until a hint or a guess', () => {
  const fresh = { enabled: true, help: { hunt_helps: 0, used: [] } }
  assert.equal(huntStarted(fresh, {}), false)
  assert.equal(huntStarted({ ...fresh, help: { hunt_helps: 1, used: [{ kind: 'nudge', rung: 1 }] } }, {}), true)
  assert.equal(huntStarted(fresh, { answer: 'I think the save never reached the memory file.' }), true)
  assert.equal(huntStarted({ enabled: false }, {}), true, 'with AI help off there is no hint to ask for')
})

test('Why did this miss? leaves out the sentence that points at a time, which the hint already gave', () => {
  assert.deepEqual(explainShown(['No line holds your fact.', 'Look at the memory row at 03:53.']), ['No line holds your fact.'])
  assert.deepEqual(explainShown(['Look at the memory row at 03:53.']), ['Look at the memory row at 03:53.'])
})

test('Why did this miss? on Compare says each cause once across checks', () => {
  const same = 'Open the pending folder in the practice profile and read what is waiting there.'
  const out = explainMerged([{ sentences: ['Field Academy made saves wait for approval, so MEMORY.md never got your fact.', same] },
                             { sentences: ['Field Academy made saves wait for approval, so the fact never reached memory.', same] }])
  assert.equal(out.length, 2)
  const real = explainMerged([{ sentences: ['Field Academy made memory saves wait for approval, so your fact is still waiting.', 'Open the pending folder in the practice profile and read what is waiting there.'] },
                              { sentences: ['Field Academy made saves wait for approval, so your fact was held back from memory.', 'Look in the pending folder in the practice profile and read what is waiting there.'] }])
  assert.equal(real.length, 2, 'two checks, one cause: said once')
  assert.equal(real[0], 'Field Academy made memory saves wait for approval.', 'the cause only, no closing clause')
})

test('a passed fix lists what changed, before and after', () => {
  const ch = fixChanges(real.fixtures.attempt_after_fix.runs.first, real.fixtures.attempt_after_fix.runs.after_fix)
  assert.ok(ch.length >= 1)
  assert.ok(ch.every(c => c.title && c.now))
})

// Loop 3 (live gate, Nov 9): a held save is a plain sentence, the home card resumes, a failed replay offers Retry.
test('a held save reads as one plain sentence, from the evidence line or from Hermes\'s raw batch summary', () => {
  const want = 'Hermes is holding this note to add to memory, not saved yet: “Harbor Bakery uses QuickBooks Online; the other five clients use Xero.”'
  assert.equal(heldSentence('add Harbor Bakery uses QuickBooks Online; the other five clients use Xero.').sentence, want)
  assert.equal(heldSentence('apply 1 op(s) to memory: - add: Harbor Bakery uses QuickBooks Online; the other five clients use Xero.').sentence, want)
  assert.equal(heldSentence('apply 1 op(s) to memory:\n- add: Harbor Bakery uses QuickBooks Online; the other five clients use Xero').sentence, want)
  assert.match(heldSentence('remove Old note').sentence, /^Hermes is holding this note to remove from memory/)
  for (const t of ['add X', 'apply 1 op(s) to memory: - add: X', 'apply 2 op(s) to memory: - add: X - add: Y']) {
    assert.doesNotMatch(heldSentence(t).sentence, /op\(s\)|apply \d/)
  }
  assert.equal(heldSentence('').note, '')
})

test('the home card offers to resume a First Flight under way, and says where it stopped', () => {
  assert.equal(resumeWords({ attempts: [] }), null)
  assert.equal(resumeWords({ attempts: [{ status: 'done', stage: 'done' }] }), null)
  const r = resumeWords({ attempts: [{ status: 'active', stage: 'checked', frozen_at: '2026-11-09' }] })
  assert.equal(r.button, 'Continue the practice')
  assert.match(r.where, /fixing it/)
  assert.match(resumeWords({ attempts: [{ status: 'active', stage: 'guess' }] }).where, /guess/)
  assert.match(resumeWords({ attempts: [{ status: 'active' }] }).where, /step you reached/)
})

test('a failed run request on Compare is an error with words, never an endless loading line', () => {
  assert.equal(replayStatus({ data: { state: 'ready' } }).state, 'ready')
  assert.equal(replayStatus({ data: null, error: '' }).state, 'loading')
  const e = replayStatus({ data: null, error: 'Gateway ticket bootstrap failed' })
  assert.equal(e.state, 'error')
  assert.equal(e.title, 'Your run didn\'t load')
  assert.doesNotMatch(e.words, /gateway|bootstrap/i)
})

test('Compare wires Retry to the replay, and useReplay gives up after a wait', () => {
  const f = readFileSync(new URL('../desktop/src/foundations.js', import.meta.url), 'utf8')
  const d = readFileSync(new URL('../desktop/src/desk.js', import.meta.url), 'utf8')
  assert.match(f, /children: 'Retry'/)
  assert.match(f, /onClick: replay\.retry/)
  assert.match(d, /REPLAY_WAIT_MS = \d+/)
  assert.match(d, /retry: \(\) => setTries/)
  assert.doesNotMatch(f, /heldText = held \? String\(held\.text/)
})

test('fixChanges shows the file whose numbers changed, not the first one listed (Nov 11 live check)', () => {
  const facts = (mem, user) => [{ label: 'MEMORY.md', value: mem }, { label: 'USER.md', value: user }]
  const first = { checks: [{ id: 'in_file', passed: false, facts: facts('457 of 2,200 characters', '0 of 1,375 characters') }] }
  const after = { checks: [{ id: 'in_file', passed: true, title: 'Your fact is in USER.md', facts: facts('457 of 2,200 characters', '58 of 1,375 characters') }] }
  const [ch] = fixChanges(first, after)
  assert.equal(ch.was, 'USER.md: 0 of 1,375 characters')
  assert.equal(ch.now, 'USER.md: 58 of 1,375 characters')
})
