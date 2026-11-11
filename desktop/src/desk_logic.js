// Field Academy 0.9 Loop 2: the mission desk's logic. Pure functions, no imports, so node tests can run them
// (tests/desk.test.mjs). What lives here: the four phases the twelve steps sit in, the Compare line, the replay's
// rows and bracket, readable clock times, and what the Field guide column is waiting on.

const arr = value => (Array.isArray(value) ? value : [])
const obj = value => (value && typeof value === 'object' && !Array.isArray(value) ? value : {})
const str = value => (typeof value === 'string' ? value : '')

/** The four phases, in order, and the steps each holds. Twelve steps stay; the page shows four groups. */
export const PHASES = [
  { id: 'before', title: 'Get ready', steps: ['recall', 'claim', 'predict', 'setup'], opens: '' },
  { id: 'learn', title: 'Learn', steps: ['idea', 'expert'], opens: 'Opens after your guess' },
  { id: 'do', title: 'Do', steps: ['lab', 'evidence'], opens: 'Opens after Practice' },
  { id: 'prove', title: 'See what happened', steps: ['check', 'compare', 'fix', 'record'], opens: 'Opens after Did it work?' },
]

/** The phases with their steps' states, which one holds the open step, and one lock line for a locked phase. */
export function phaseRows(states, at) {
  const byId = Object.fromEntries(arr(states).map(s => [s.id, s]))
  return PHASES.map(p => {
    const steps = p.steps.map(id => byId[id]).filter(Boolean)
    const locked = steps.length > 0 && steps.every(s => s.status === 'locked')
    const done = steps.length > 0 && steps.every(s => ['done', 'skipped'].includes(s.status))
    return { ...p, steps, locked, done, current: steps.some(s => s.id === at), lockLine: locked ? p.opens || 'Locked for now' : '' }
  })
}

/** The short line for the top phase bar on a narrow pane: "Prove: Check, 9 of 12". */
export function phaseBarWords(states, at) {
  const list = arr(states)
  const index = list.findIndex(s => s.id === at)
  if (index < 0) return ''
  const phase = PHASES.find(p => p.steps.includes(at))
  return `${phase ? phase.title : ''}: ${list[index].title}`
}

/** The Compare line: how many checks the learner gave themself beside how many Hermes's own files and chats show. */
export function compareLine(compare) {
  const c = obj(compare)
  const grid = arr(c.grid)
  const cal = obj(c.calibration)
  // A sample run carries the numbers alone: {said, shows, of}.
  const of = Number.isFinite(c.of) ? c.of : grid.length
  const said = Number.isFinite(c.said) ? c.said : Number.isFinite(cal.self_passes) ? cal.self_passes : grid.filter(g => g.self_pass === true).length
  const shows = Number.isFinite(c.shows) ? c.shows : Number.isFinite(cal.actual_passes) ? cal.actual_passes : grid.filter(g => g.passed === true).length
  const waiting = grid.filter(g => g.passed === null || g.passed === undefined).length
  return {
    said, shows, of, waiting,
    gap: said - shows,
    note: waiting ? `${waiting === 1 ? 'One check waits' : `${waiting} checks wait`} for Score my answer.` : '',
  }
}

/** A readable local clock time for an epoch number: "3:53 AM". Empty when it can't be read. */
export function clockWords(at) {
  const n = Number(at)
  if (!Number.isFinite(n) || n <= 0) return ''
  const when = new Date(n * 1000)
  if (Number.isNaN(when.getTime())) return ''
  return when.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

/** The replay drawn as rows on one time line: each row holds what happened at one moment, chat on the left and files
 *  on the right. Events within the same second share a row, so the save and the held file sit side by side. */
export function replayRows(replay) {
  const r = obj(replay)
  // A bare "(called memory)" message repeats the tool row under it, so the drawing leaves it out.
  const events = arr(r.events).filter(e => e && e.event_id && !(e.kind === 'assistant' && /^\(called /.test(str(e.text)))).slice().sort((a, b) => (Number(a.at) || 0) - (Number(b.at) || 0))
  const rows = []
  for (const e of events) {
    const at = Math.round(Number(e.at) || 0)
    let row = rows[rows.length - 1]
    if (!row || row.at !== at) {
      row = { at, clock: clockWords(at), chat: [], files: [] }
      rows.push(row)
    }
    ;(e.lane === 'files' ? row.files : row.chat).push(e)
  }
  const bracket = obj(r.bracket)
  for (const row of rows) {
    row.bracket = Boolean(bracket.from && bracket.to && row.chat.some(e => e.event_id === bracket.from) && row.files.some(e => e.event_id === bracket.to))
  }
  return rows
}

/** Where the replay's bracket sits, as a share of the strip (0 to 1), or -1 when there is none. */
export function bracketAt(rows) {
  const list = arr(rows)
  const i = list.findIndex(r => r.bracket)
  if (i < 0) return -1
  return list.length > 1 ? i / (list.length - 1) : 0
}

/** Is anything in a Field guide view still being fetched? Then the page looks again shortly. */
export function guideFetching(view) {
  const v = obj(view)
  const ladder = obj(v.ladder)
  if (obj(ladder.nudge).state === 'fetching') return true
  if (arr(v.explain).some(e => obj(e).state === 'fetching')) return true
  if (obj(obj(v.do_it_with_me).why).state === 'fetching') return true
  return false
}

/** Seconds since a fetch started, for "Fetching, 6 s". */
export function fetchingWords(startedAt, now) {
  const n = Number(startedAt)
  const t = Number(now)
  if (!Number.isFinite(n) || n <= 0 || !Number.isFinite(t)) return 'Fetching'
  return `Fetching, ${Math.max(0, Math.round(t - n))} s`
}

/** Which help rungs the learner has used, from the guide's help summary. */
export function usedRungs(view) {
  const used = arr(obj(obj(view).help).used)
  return {
    nudge: used.some(u => u.kind === 'nudge'),
    where: used.some(u => u.kind === 'where'),
    reveal: used.some(u => u.kind === 'reveal'),
    explain: used.some(u => u.kind === 'explain'),
  }
}

/** A grade's quote, split so the page can mark it inside the learner's own answer. */
export function quoteParts(answer, quote) {
  const a = str(answer)
  const q = str(quote)
  const i = q ? a.indexOf(q) : -1
  if (i < 0) return [{ text: a, mark: false }]
  return [{ text: a.slice(0, i), mark: false }, { text: q, mark: true }, { text: a.slice(i + q.length), mark: false }].filter(p => p.text)
}

/** A source chip's words: where a sentence of an answer came from, in plain words, not the id. */
export function sourceWords(id) {
  const s = str(id)
  if (/^m\d+$/.test(s) || /^c\d+$/.test(s)) return 'Your chat'
  if (/^f-/.test(s)) return 'Your files'
  if (/^idea-/.test(s)) return 'The idea'
  if (/^expert-/.test(s)) return 'Watch it done'
  if (/^asof-/.test(s)) return 'Hermes facts'
  if (/^entry-|^e\d+/.test(s)) return 'Your notes'
  return 'This lesson'
}

/* ------------------------------------------------------------- plain words -- */
// Loop 2e: every headline is a plain sentence about what happened in this run, built from the run's own data (the
// replay's events and the check results), never a score slogan ("You said N of M ...") and never a fixed tagline.

const lowerStart = t => (t ? t.charAt(0).toLowerCase() + t.slice(1) : '')
const sentence = t => { const s = str(t).trim(); return !s ? '' : /[.!?]$/.test(s) ? s : `${s}.` }

/** The headline for Compare and the sample run: what Hermes said beside what it did, from the replay and the checks. */
export function runHeadline(replay, checks, whose = 'your') {
  const r = obj(replay)
  const events = r.state === 'ready' ? arr(r.events) : []
  const from = events.find(e => e.event_id === obj(r.bracket).from)
  const tool = from || events.find(e => str(e.kind).startsWith('tool:memory'))
  const pending = events.find(e => e.kind === 'file:pending')
  const removed = events.find(e => e.kind === 'file:removed')
  const mem = events.find(e => e.kind === 'file:memory')
  const clock = tool ? clockWords(tool.at) : ''
  const list = arr(checks)
  const missed = list.filter(c => c && c.passed === false)
  const said = tool ? `Hermes said it saved ${whose} note${clock ? ` at ${clock}` : ''}.` : ''
  // One sentence, said once: the facts under it (the meter, the held file, the notes) are on the replay itself.
  if (tool && tool.staged && pending) {
    return { headline: `${said} It didn't: the note is still waiting for ${whose === 'your' ? 'your' : 'their'} approval.`, detail: '' }
  }
  if (tool && removed) {
    return { headline: `${said} It did, but to make room it deleted a note the practice jobs rely on.`, detail: '' }
  }
  if (tool && mem && obj(mem.meter).changed === false) {
    return { headline: `${said} It didn't: MEMORY.md never changed.`, detail: '' }
  }
  if (list.length && !missed.length) return { headline: 'Hermes did what you thought it did. Every check passed.', detail: '' }
  if (missed.length) {
    return { headline: missed.slice(0, 2).map(c => sentence(c.title)).join(' '), detail: '' }
  }
  return { headline: '', detail: '' }
}

/** How the learner's own score compared, as a plain sentence (no "N of M" slogan). */
export function scoreSentence(compare, who = 'You') {
  const c = obj(compare)
  const grid = arr(c.grid)
  const of = Number.isFinite(c.of) ? c.of : grid.length
  const said = Number.isFinite(c.said) ? c.said : grid.filter(g => g.self_pass === true).length
  const shows = Number.isFinite(c.shows) ? c.shows : grid.filter(g => g.passed === true).length
  if (!of) return ''
  const marked = said === of ? 'every check' : said === 0 ? 'no check' : `${said} ${said === 1 ? 'check' : 'checks'}`
  const held = shows === 0 ? 'none of them has passed yet' : shows >= said ? 'they all passed' : `only ${shows} ${shows === 1 ? 'has' : 'have'} passed`
  // The written answer's score lives on its own step; saying here that it "still needs a score" repeated it (round 7/8).
  const waitText = ''
  return said === 0 ? `${who} didn't mark any check as passed.${waitText}` : `${who} marked ${marked} as passed before looking; ${held}.${waitText}`
}

/** The Check step's headline: the missed checks in plain words, or that every check passed. */
export function checkHeadline(run) {
  const checks = arr(obj(run).checks)
  const missed = checks.filter(c => c && c.passed === false)
  if (!checks.length) return ''
  if (!missed.length) return 'Every check passed.'
  return missed.slice(0, 2).map(c => sentence(c.title)).join(' ')
}

/** What the bracket on the replay's strip joins, for its label (read by screen readers and on hover). */
export function bracketWords(replay) {
  const r = obj(replay)
  const events = arr(r.events)
  const b = obj(r.bracket)
  const from = events.find(e => e.event_id === b.from)
  const to = events.find(e => e.event_id === b.to)
  if (!from || !to) return ''
  if (to.kind === 'file:removed') return `${clockWords(from.at)}: the chat showed ${from.title || 'a save'}, and the same moment Hermes deleted a note from MEMORY.md.`
  const folder = str(to.path).includes('/') ? `${str(to.path).split('/').slice(0, -1).join('/')}/` : str(to.path)
  return `${clockWords(from.at)}: the chat showed ${from.title || 'a save'}, but the note went to ${folder ? `the approval queue (${folder})` : 'the approval queue'}, not MEMORY.md.`
}

/** After a fix: each check that missed the first time and passes now, with the fact that changed. */
export function fixChanges(first, after) {
  const before = Object.fromEntries(arr(obj(first).checks).map(c => [c.id, c]))
  return arr(obj(after).checks).filter(c => c && c.passed && before[c.id] && before[c.id].passed === false).map(c => {
    // The fact that changed, not the first one listed: a save that landed in USER.md showed MEMORY.md's unchanged
    // numbers as its before and after (Nov 11 live check).
    const wasAll = arr(before[c.id].facts)
    const nowAll = arr(c.facts)
    const changed = wasAll.find(w => { const n = nowAll.find(f => f.label === w.label); return n && n.value !== w.value })
    const was = changed || wasAll[0]
    const now = nowAll.find(f => was && f.label === was.label) || nowAll[0]
    return { id: c.id, title: c.title, was: was ? `${was.label}: ${was.value}` : '', now: was && now ? `${now.label}: ${now.value}` : str(c.detail) }
  })
}

/** The two fix commands for a held save, from the held file's own name (pending/memory/<id>.json): list what is held,
 *  then approve that one save by its id. Never "approve all". Empty when the path isn't a held memory save. */
export function heldCommands(path) {
  const m = /(?:^|\/)pending\/memory\/([0-9a-f]{8})\.json$/.exec(str(path))
  return m ? ['/memory pending', `/memory approve ${m[1]}`] : []
}

/** The learner has started looking for the cause: asked the Field guide for a hint (any rung, or a question while
 *  hunting) or written their own guess at it (Score my answer). Until then Check holds back where to look. */
export function huntStarted(guideView, explain) {
  // With AI help off or no model there are no hints to ask for, so nothing is held back.
  if (!guideView || guideView.enabled === false) return true
  const help = obj(obj(guideView).help)
  const r = usedRungs(guideView)
  const e = obj(explain)
  return Boolean(r.nudge || r.where || r.reveal || r.explain || (help.hunt_helps || 0) > 0 || str(e.answer).trim() || e.submitted || e.level)
}

/** Why did this miss?, as shown: a sentence that points at a moment in the chat (it names a time) is the hint's job,
 *  and the hint already said it, so it is left out (round 12: the 03:53 pointer showed three times). Keeps at least one. */
export function explainShown(sentences) {
  const all = arr(sentences).map(str).filter(Boolean)
  const kept = all.filter(t => !/\b\d{1,2}:\d{2}\b/.test(t))
  return kept.length ? kept : all.slice(0, 1)
}

/** Why did this miss? on Compare: every missed check's sentences, each cause said once. After Compare the checks
 *  usually miss for one cause and come back as near-paraphrases, so a check whose first sentence shares half its words
 *  with one already shown is left out whole; any other repeated sentence is left out too. */
export function explainMerged(items) {
  const words = t => new Set(str(t).toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(w => w.length > 2))
  const close = (a, b) => { const x = words(a), y = words(b); const both = [...x].filter(w => y.has(w)).length; return both * 2 >= Math.min(x.size, y.size) }
  const out = []
  const firsts = []
  // The cause, without a closing "so ..." clause that restates the headline (Nov 9 critics).
  const causeOnly = t => { const m = /^(.{12,}?), so\b.*$/i.exec(t); return m ? `${m[1]}.` : t }
  for (const i of arr(items)) {
    const ss = arr(obj(i).sentences).map(str).filter(Boolean).map((t, n) => (n === 0 ? causeOnly(t) : t))
    if (!ss.length || firsts.some(f => close(f, ss[0]))) continue
    firsts.push(ss[0])
    for (const t of ss) if (!out.some(o => close(o, t))) out.push(t)
  }
  return out
}

/* ---------------------------------------------------------------- Loop 3 -- */

const HELD_VERB = { add: 'add to memory', patch: 'change a note in memory', replace: 'change a note in memory', remove: 'remove from memory' }

/** A held save as one plain sentence, never Hermes's raw summary ("apply 1 op(s) to memory: - add: ..."). Reads the
 *  evidence line ("add Harbor Bakery uses ...") or, from an older run, the raw summary itself (Loop 3 live gate). */
export function heldSentence(text) {
  let t = str(text).trim()
  const batch = /^apply \d+ op\(s\) to [a-z ]+:\s*/i
  if (batch.test(t)) {
    const ops = t.replace(batch, '').split(/\n|\s+(?=-\s*(?:add|patch|remove|replace)\b)/i).map(s => s.trim()).filter(Boolean)
    const found = ops.map(o => /^-\s*(add|patch|remove|replace)[^:]*:\s*(.*)$/i.exec(o))
    const verbs = new Set(found.map(m => m && m[1].toLowerCase()))
    t = found.length && found.every(Boolean) && verbs.size === 1
      ? `${found[0][1].toLowerCase()} ${found.map(m => m[2].trim().replace(/[.;]+$/, '')).join('; ')}`
      : t.replace(batch, '').replace(/^-\s*/, '')
  }
  const m = /^(add|patch|remove|replace)\s+([\s\S]*)$/i.exec(t)
  const verb = m ? m[1].toLowerCase() : 'add'
  const note = (m ? m[2] : t).trim()
  if (!note) return { note: '', sentence: 'Hermes is holding a save. Nothing is in memory until you approve it.' }
  const quoted = /[.!?]$/.test(note) ? note : `${note}.`
  return { note, sentence: `Hermes is holding this note to ${HELD_VERB[verb]}, not saved yet: “${quoted}”` }
}

/** The home card's line for a First Flight already under way (Loop 3), by how far the attempt got. */
export function resumeWords(mission) {
  const attempts = arr(obj(mission).attempts)
  const last = obj(attempts[attempts.length - 1])
  if (!attempts.length || last.status === 'done') return null
  const where = {
    guess: 'You were making your guess before the practice.',
    practice: 'Your practice copy is set up. Next is the job in the practice chat.',
    checked: 'You checked your work. Next is finding out why and fixing it.',
    fixed: 'You checked your fix. Next is saving it to your record.',
  }[str(last.stage)] || 'Pick up at the step you reached.'
  return { title: 'Your practice is waiting', where, button: 'Continue the practice' }
}

/** What Compare shows for the run: the replay, a loading line, or a plain error with Retry (Loop 3 live gate). */
export function replayStatus(replay) {
  const r = obj(replay)
  if (r.data) return { state: 'ready' }
  if (r.error) return { state: 'error', title: 'Your run didn\'t load', words: 'Field Academy asked Hermes for your run, and it didn\'t come back. Your checks and answers are saved.' }
  return { state: 'loading', words: 'Loading your run.' }
}

/** The recorded run the home page shows when the live sample can't be had (still loading, a Hermes backend that is
 *  unreachable or older, or the file missing). It is a trimmed copy of content/sample_run.json, bundled with the page,
 *  so the preview box is never empty. */
export const PREVIEW_RUN = {
  state: 'ready',
  sample: true,
  fallback: true,
  lanes: [{ id: 'chat', label: 'In your chat' }, { id: 'files', label: 'In Hermes\'s files' }],
  bracket: {
    from: 'm5',
    to: 'f-removed-1',
    words: 'The chat showed Saved to memory, but to make room Hermes deleted a note the practice jobs rely on.',
  },
  events: [
    { event_id: 'm1', lane: 'chat', at: 1792400011, kind: 'user', title: 'You asked', text: 'Save to memory: Harbor Bakery uses QuickBooks Online; the other five use Xero' },
    { event_id: 'm5', lane: 'chat', at: 1792400015, kind: 'tool:memory', title: 'Saved to memory', text: 'Saved. Memory is 97% — 2,140/2,200 chars.', staged: false, failed: false },
    { event_id: 'f-removed-1', lane: 'files', at: 1792400015, kind: 'file:removed', title: 'A note was deleted', text: 'Refunds over 250 dollars need the owner\'s yes before they are sent.', path: 'memories/MEMORY.md' },
    { event_id: 'm6', lane: 'chat', at: 1792400016, kind: 'assistant', title: 'Hermes answered', text: 'Memory was full, so I cleared some older notes and saved it. Saved to memory.' },
  ],
  started_at: 1792400011,
  ended_at: 1792400016,
}

/** What the home page's preview draws: the live sample when it came back ready with moments in it, otherwise the
 *  bundled run. Never nothing. */
export function homePreview(sample) {
  const s = obj(sample)
  return s.state === 'ready' && arr(s.events).length ? s : PREVIEW_RUN
}
