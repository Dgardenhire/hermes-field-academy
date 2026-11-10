// Field Academy Foundations: the mission loop's logic for the page. Pure functions, no imports, so node tests can
// run them (tests/loop.test.mjs). What lives here: which of the twelve steps is open and what must be saved before
// the next, the checks a form must pass before it is sent, the numbers shown at Compare, and the light Markdown the
// lesson text is written in. The backend judges everything again; this only keeps the page honest and quick.

const arr = value => (Array.isArray(value) ? value : [])
const obj = value => (value && typeof value === 'object' && !Array.isArray(value) ? value : {})
const str = value => (typeof value === 'string' ? value : '')

/* ------------------------------------------------------------------ steps -- */

/** The twelve steps, in the order the page shows them. Practice comes before the idea: the try is the problem the
 *  lesson then explains (TEACHING-STANDARD test 2). */
export const STEPS = [
  { id: 'recall', title: 'Recall', line: 'Three minutes, from memory' },
  { id: 'claim', title: 'Your claim', line: 'What you will prove' },
  { id: 'predict', title: 'Your guess', line: 'Before you start' },
  { id: 'setup', title: 'Practice', line: 'Set up and try it' },
  { id: 'idea', title: 'The idea', line: 'How it works' },
  { id: 'expert', title: 'Watch it done', line: 'An expert run' },
  { id: 'lab', title: 'Your turn', line: 'Do the work' },
  { id: 'evidence', title: 'Did it work?', line: 'Before any result' },
  { id: 'check', title: 'Check', line: 'Field Academy reads it' },
  { id: 'compare', title: 'Compare', line: 'Your guess beside the result' },
  { id: 'fix', title: 'Fix it', line: 'Then once more' },
  { id: 'record', title: 'Record', line: 'Add it to your record' },
]

/** The latest entry of a kind (optionally matching a test), or null. */
export function latest(view, kind, test) {
  const found = arr(obj(view).entries).filter(e => e && e.kind === kind && (!test || test(obj(e.body))))
  return found.length ? obj(found[found.length - 1].body) : null
}

/** Is the practice set up for this attempt: every needed profile recorded, and the main one set up? */
export function practiceReady(view, listing) {
  const attempt = obj(obj(view).attempt)
  const needed = arr(obj(obj(view).lab).profiles)
  const live = arr(listing).filter(p => ['ready', 'in_use'].includes(p.status))
  const main = live.find(p => p.which === 'a' && p.name === attempt.profile)
  return Boolean(attempt.frozen_at && main && main.set_up && needed.every(w => live.some(p => p.which === w)))
}

/** Each step's status (done, open or locked) from what the attempt has saved. */
export function stepStates(view, listing) {
  const v = obj(view)
  const runs = obj(v.runs)
  const has = kind => latest(v, kind) !== null
  const read = step => arr(v.entries).some(e => e && e.kind === 'read' && obj(e.body).step === step)
  const ready = practiceReady(v, listing)
  const firstNote = latest(v, 'lab_note', b => b.for !== 'transfer') !== null
  // A test-out (0.9 persona test) skips Recall, and can go to the record once every check passed the first time.
  const testOut = obj(v.test_out).on === true
  const testedOut = testOut && obj(v.test_out).passed === true
  // A First Flight (0.9 Loop 2) skips Recall and the claim; the course's checks stand and the record says so.
  const firstFlight = obj(v.first_flight).on === true
  const done = {
    recall: has('recall') || testOut || firstFlight,
    claim: (has('claim') && has('standard')) || firstFlight,
    predict: has('prediction'),
    setup: ready,
    idea: read('idea'),
    expert: read('expert'),
    lab: firstNote,
    evidence: has('self_score'),
    check: Boolean(runs.first),
    compare: has('gap_note'),
    fix: Boolean(runs.after_fix) && Boolean(runs.transfer),
    record: obj(v.attempt).status === 'done',
  }
  const gate = {
    recall: true,
    claim: done.recall,
    predict: done.claim,
    setup: done.predict,
    idea: done.predict,
    expert: done.predict,
    lab: done.setup,
    evidence: done.lab,
    check: done.evidence,
    compare: done.check,
    fix: done.compare,
    record: done.fix || (testedOut && done.check),
  }
  const skipped = id => (id === 'recall' && (testOut || firstFlight) && !has('recall')) || (id === 'claim' && firstFlight && !has('claim'))
  return STEPS.map(s => ({ ...s, status: skipped(s.id) ? 'skipped' : done[s.id] ? 'done' : gate[s.id] ? 'open' : 'locked' }))
}

/** Where the page opens: the first open step that isn't done, else the last done one. */
export function currentStep(states) {
  const list = arr(states)
  // The first open step after the furthest one done, so a learner past Check isn't sent back to an optional lesson.
  let furthest = -1
  list.forEach((s, i) => { if (s.status === 'done') furthest = i })
  const ahead = list.find((s, i) => i > furthest && s.status === 'open')
  if (ahead) return ahead.id
  const open = list.find(s => s.status === 'open')
  if (open) return open.id
  const done = list.filter(s => s.status === 'done')
  return done.length ? done[done.length - 1].id : 'recall'
}

/** Does this mission's page offer Show memory file? Only missions whose work runs through memory say so
 *  (lab.memory_view, 0.9 persona test): missions 3, 4, 5, 8 and 11. Mission 6 shows each profile's memory beside its button. */
export function showsMemory(mission) {
  return obj(obj(mission).lab).memory_view === true
}

/** Recall's lead for someone who hasn't done the missions it reaches back to (0.9 persona test). Empty when they have, so the
 *  mission's own lead stands. */
export function recallLead(fromList) {
  const missed = arr(fromList).filter(m => m && m.done === false)
  if (!missed.length) return ''
  const names = missed.map(m => (Number.isInteger(m.order) ? `mission ${m.order} (${str(m.title)})` : str(m.title)))
  const list = names.length === 1 ? names[0] : `${names.slice(0, -1).join(', ')} or ${names[names.length - 1]}`
  return `You haven't done ${list} in Field Academy yet, so these may be new to you. Answer from your own use of Hermes, or write your best guess. A guess before the lesson helps it stick too.`
}

/** Is a practice profile from another attempt still here? Then the mission's fresh_replace text applies. */
export function earlierPracticeLeft(listing, attempt) {
  const mine = str(obj(attempt).profile)
  return arr(listing).some(p => p && ['ready', 'in_use', 'planned', 'removing'].includes(p.status) && (!mine || p.name !== mine))
}

/** The four things frozen when practice is set up, and which are still missing. */
export function freezeMissing(view) {
  const names = { recall: 'your recall', claim: 'your claim', standard: 'the checks', prediction: 'your guess' }
  const testOut = obj(obj(view).test_out).on === true
  const firstFlight = obj(obj(view).first_flight).on === true
  return Object.keys(names).filter(k => latest(view, k) === null && !(k === 'recall' && (testOut || firstFlight)) && !(k === 'claim' && firstFlight)).map(k => names[k])
}

/** Can this mission be tested out of from the Foundations list? Not the review, not one already in practice or in the
 *  record, and not one already being tested out. */
export function canTestOut(mission) {
  const m = obj(mission)
  if (m.kind === 'review' || m.id === 'f.review') return false
  const attempts = arr(m.attempts)
  if (attempts.some(a => a && a.status === 'done')) return false
  const last = attempts[attempts.length - 1]
  return !last || !(['open', 'lab'].includes(last.status) && (last.frozen_at || last.test_out))
}

/** A mission's status on the Foundations list. A test-out that passed reads Tested out, never In your record alone. */
export function missionWords(mission) {
  const attempts = arr(obj(mission).attempts)
  const last = attempts[attempts.length - 1]
  if (!last) return { word: 'Not started', tone: 'idle', button: 'Start' }
  if (last.status === 'done') return last.tested_out ? { word: 'Tested out', tone: 'good', button: 'Open' } : { word: 'In your record', tone: 'good', button: 'Open' }
  if (last.test_out) return { word: last.frozen_at ? 'Testing out, in practice' : 'Testing out', tone: 'info', button: 'Continue' }
  return { word: last.frozen_at ? 'In practice' : 'Started', tone: 'info', button: 'Continue' }
}

/* ------------------------------------------------------------------ forms -- */

export function recallProblems(answers, prompts) {
  const list = arr(answers)
  const empty = arr(prompts).map((_, i) => i).filter(i => !str(list[i]).trim())
  return empty.length ? [`Write something for ${empty.length === 1 ? 'the last prompt' : 'every prompt'}, even a guess.`] : []
}

/** A prediction per check: pass or fail, and a confidence from 50 to 100. */
export function predictionProblems(form, ids) {
  const f = obj(form)
  const checks = obj(f.checks)
  const out = []
  for (const id of arr(ids)) {
    const c = obj(checks[id])
    if (typeof c.expect_pass !== 'boolean') out.push(`Say pass or fail for check ${id.replace(/^s/, '')}.`)
    const n = Number(c.confidence)
    if (!Number.isInteger(n) || n < 50 || n > 100) out.push(`Confidence for check ${id.replace(/^s/, '')} is from 50 to 100.`)
  }
  if (str(f.where_wrong).trim().length < 10) out.push('Say where you think you will slip, in a few words.')
  return out
}

export function selfScoreProblems(form, ids) {
  const checks = obj(obj(form).checks)
  return arr(ids).filter(id => typeof obj(checks[id]).pass !== 'boolean').map(id => `Score yourself on check ${id.replace(/^s/, '')}.`)
}

export function labNoteProblems(form, transfer = false) {
  const f = obj(form)
  const out = []
  const fact = str(f.fact).trim()
  if (fact.length < 8) out.push(transfer ? 'Write the fact about you that you asked Hermes to save.' : 'Write the fact you asked Hermes to save.')
  if (fact.length > 300) out.push('Keep the fact to one line, under 300 characters.')
  if (!str(f.key_term).trim()) out.push('Name the key word of the fact, the one a new chat would have to use.')
  if (transfer) {
    if (str(f.one_off).trim().length < 4) out.push('Write the one-off detail you weighed up.')
    if (typeof f.one_off_saved !== 'boolean') out.push('Say whether you saved the one-off detail or left it out.')
    if (str(f.one_off_why).trim().length < 10) out.push('Say in one sentence why it does or doesn\'t earn a line.')
  }
  const why = str(f.removed_ok).trim()
  if (why && why.length < 10) out.push('If you say a note was cut, say which one and why that was all right.')
  return out
}

const STOP = new Set('a an and are as at be but by for from has have i in into is it its me my of on or our so that the their them they this to was we were when which who will with you your uses use used save saved memory remember please every each always never'.split(' '))

/** A reasonable key word for a fact: a capitalized name if there is one, else the longest word. */
export function guessKeyTerm(fact) {
  const words = str(fact).match(/[A-Za-z0-9][A-Za-z0-9'+-]*/g) || []
  const named = words.slice(1).filter(w => /^[A-Z0-9]/.test(w) && !STOP.has(w.toLowerCase()) && w.length >= 3)
  if (named.length) return named.sort((a, b) => b.length - a.length)[0]
  const plain = words.filter(w => !STOP.has(w.toLowerCase()) && w.length >= 4)
  return plain.sort((a, b) => b.length - a.length)[0] || ''
}

/* ---------------------------------------------------------------- numbers -- */

/** "Work it out" with the learner's own Memory number: a full MEMORY.md is about 800 tokens; a one-line note about 45. */
export function memoryMath(tokens, full = 800, perNote = 45) {
  const n = Number(tokens)
  if (!Number.isFinite(n) || n < 0 || String(tokens).trim() === '') return null
  const room = Math.max(0, Math.round(full - n))
  return { tokens: Math.round(n), full, room, notes: Math.floor(room / perNote) }
}

export function tokensFromChars(chars, perToken = 2.75) {
  const n = Number(chars)
  return Number.isFinite(n) && n > 0 ? Math.round(n / perToken) : 0
}

export function passWord(value) {
  return value === true ? 'Pass' : value === false ? 'Fail' : 'Not yet'
}

/** The Compare row for one check, in words. */
export function gridRow(row) {
  const r = obj(row)
  const guess = typeof r.expect_pass === 'boolean' ? `${passWord(r.expect_pass)}, ${r.confidence}% sure` : 'No guess'
  const mine = typeof r.self_pass === 'boolean' ? passWord(r.self_pass) : 'Not scored'
  let check = passWord(r.passed)
  if (r.proves_by === 'rubric' && r.level) check = `${passWord(r.passed)}, level ${r.level} of 4`
  const after = typeof r.passed_after_fix === 'boolean' && r.passed_after_fix !== r.passed ? passWord(r.passed_after_fix) : ''
  const off = typeof r.self_pass === 'boolean' && typeof r.passed === 'boolean' && r.self_pass !== r.passed
  return { id: r.id, text: str(r.text), guess, mine, check, after, off }
}

/** The line under a check result about the checks the learner can't see. Said the same way for every mission. */
export function hiddenWords(hidden) {
  const h = obj(hidden)
  const count = Number(h.count) || 0
  if (!count) return ''
  const passed = Number(h.passed) || 0
  const many = count === 1 ? 'check you can\'t see' : 'checks you can\'t see'
  return `${count} ${many}: ${passed} of ${count} met.${passed < count ? ' Something in the practice profile still needs fixing.' : ''}`
}

/** What the signed gap (self-scored passes minus checked passes) says. */
export function gapWords(gap) {
  const n = Number(gap)
  if (!Number.isFinite(n) || n === 0) return 'You scored yourself the same as the checks did.'
  const many = Math.abs(n) === 1 ? 'check' : 'checks'
  return n > 0 ? `You gave yourself ${n} more ${many} than the checks did.` : `You gave yourself ${-n} fewer ${many} than the checks did.`
}

export function percent(value) {
  return typeof value === 'number' && Number.isFinite(value) ? `${Math.round(value * 100)}%` : '—'
}

/** Brier score in words: 0 is perfect, 0.25 is what a coin toss scores. */
export function brierWords(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'Not enough results yet'
  const n = value.toFixed(2)
  if (value <= 0.1) return `${n}, sharp`
  if (value <= 0.25) return `${n}, better than a coin toss`
  return `${n}, worse than a coin toss`
}

export const PLANTS = {
  write_approval: {
    title: 'Saves waited for your approval',
    what: 'Memory approvals were on in academy-practice. A save from a chat was staged, and the app still showed Saved to memory with a check. Expanding the row said it was staged and not saved yet.',
  },
  memory_full: {
    title: 'Memory was nearly full',
    what: "MEMORY.md was filled close to its limit. Hermes's first save came back over the limit, then it made room by cutting or shortening other notes. The risk was losing a note the practice jobs rely on.",
  },
  wrong_profile: {
    title: 'A second profile looked the same',
    what: 'academy-practice-b had the same notes as academy-practice, so a chat there answered the same way. Work saved there never reached academy-practice.',
  },
}

/** The pill beside a planted problem at Compare, in the record's own terms: caught means its check passed. */
export function plantPill(plant) {
  const p = obj(plant)
  if (p.caught === true) return 'You caught it'
  if (p.caught === false) return p.fired ? 'You ran into it, not caught yet' : 'Not caught yet'
  return p.fired ? 'You ran into it' : 'You didn\'t run into it'
}

export function plantWords(kind) {
  return PLANTS[kind] || { title: 'Something in the setup', what: '' }
}

export function shortHash(sha) {
  return str(sha).slice(0, 12)
}

export function timerWords(seconds) {
  const s = Math.max(0, Math.round(Number(seconds) || 0))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

/* ---------------------------------------------------------- the Field Record -- */

/** The calibration table, one row per mission in course order. A mission not in the record is an empty row, never
 *  filled in. There is no average row: with about four checks a mission, one lucky check moves any average. */
export function calibrationTable(rows) {
  const n = value => (typeof value === 'number' && Number.isFinite(value) ? String(value) : '')
  return arr(rows).map(r => {
    const row = obj(r)
    const empty = !row.in_record
    return {
      id: str(row.mission), title: str(row.title), empty,
      checks: empty ? '' : n(row.checks), predicted: empty ? '' : n(row.predicted),
      selfScored: empty ? '' : n(row.self_scored), passed: empty ? '' : n(row.passed_first),
    }
  })
}

const WORD = /[A-Za-z0-9][A-Za-z0-9'’.-]*/g

/** What stops the record from being saved, in the order the form shows the fields. The backend checks again. */
export function recordProblems(form) {
  const f = obj(form)
  const out = []
  if (!str(f.holder).trim()) out.push('Type the name you want on your Field Record.')
  if (str(f.limits).trim().length < 20) out.push('Write two or three lines on what this record doesn\'t show, in your own words.')
  if (str(f.limits).length > 800) out.push('Keep what the record doesn\'t show under 800 characters.')
  if ((str(f.caseText).match(WORD) || []).length > 300) out.push('Keep the case under 300 words.')
  return out
}

/** Add or remove an excerpt from the withheld list, keeping it sorted and free of repeats. */
export function toggleWithhold(list, id, keepOut) {
  const ids = new Set(arr(list).filter(x => Number.isInteger(x)))
  if (keepOut) ids.add(id)
  else ids.delete(id)
  return [...ids].sort((a, b) => a - b)
}

/** Active hours, as the record states them. */
export function hoursWords(hours) {
  const h = obj(hours)
  const minutes = Number(h.active_minutes)
  if (!Number.isFinite(minutes) || minutes <= 0) return 'Less than a minute of active time'
  if (minutes < 60) return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} of active time`
  return `${Number(h.hours).toFixed(1)} hours of active time`
}

/** "Field Academy read it" and the other tags, with a capital, as the page shows them beside a line. */
export function checkedByWords(tag) {
  const s = str(tag)
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

/* ---------------------------------------------------------------- the host -- */

/** What this Hermes Desktop can do for a practice profile. Older desktops lack some of these. */
export function hostSupport(host) {
  const h = obj(host)
  return {
    newChat: typeof h.newChat === 'function',
    deleteProfile: typeof h.deleteProfile === 'function',
    requestProfile: typeof h.requestProfile === 'function',
    request: typeof h.request === 'function',
  }
}

/** Where a host.requestProfile call for a practice profile goes. Hermes 0.22 and 0.23 accept a bare profile name only
 *  while this computer is the app's sole connection; with a second connection added (another computer, a cloud agent)
 *  a bare name throws "requires a route descriptor from host.profileRoutes()" (apps/desktop/src/sdk/profile-request.ts).
 *  Practice profiles are always made on this computer, so the local route serving that profile is the one; with none
 *  found, the bare name keeps the old behaviour. */
export function practiceRoute(routes, name) {
  const want = String(name || '').trim().toLowerCase()
  const route = arr(routes).find(r => r && r.mode === 'local' && typeof r.connectionId === 'string' && r.connectionId.trim()
    && String(r.targetProfile || '').trim().toLowerCase() === want && String(r.profile || '').trim())
  return route ? { connectionId: route.connectionId, mode: route.mode, profile: route.profile, targetProfile: route.targetProfile } : name
}

/** The practice profiles this attempt needs, in order, each with what the page knows about it. */
export function practiceRows(listing, needed) {
  const live = arr(listing).filter(p => !['removed'].includes(p.status))
  return arr(needed).map(which => {
    const found = live.filter(p => p.which === which)
    return { which, profile: found.length ? found[found.length - 1] : null }
  })
}

/** A pill word for a practice profile's status. */
export function statusWord(profile) {
  const s = obj(profile).status
  return { planned: 'Planned', ready: 'Ready', in_use: 'In use', removing: 'Removing', removed: 'Removed' }[s] || 'Not made yet'
}

/* -------------------------------------------------------------- Markdown -- */
//
// Lesson text uses a small slice of Markdown: ## and ### headings, paragraphs, "- " and "1. " lists, "> " quotes
// (a lone ">" separates quoted paragraphs), and | tables. Inline: **bold**, `code`, and "As of Hermes 0.22.4" notes,
// which render as a pill. No HTML is ever read from the text.

export function mdBlocks(text) {
  const lines = str(text).replace(/\r\n/g, '\n').split('\n')
  const out = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    const t = line.trim()
    if (!t) { i++; continue }
    if (t.startsWith('```')) {
      // A fenced block (a settings example, a log line), kept exactly, less the fence's own indent.
      const pad = line.length - line.trimStart().length
      const body = []
      i++
      while (i < lines.length && !lines[i].trim().startsWith('```')) { body.push(lines[i].slice(Math.min(pad, lines[i].length - lines[i].trimStart().length))); i++ }
      i++
      out.push({ kind: 'code', text: body.join('\n') })
      continue
    }
    const head = t.match(/^(#{1,4})\s+(.*)$/)
    if (head) { out.push({ kind: head[1].length <= 2 ? 'h2' : 'h3', text: head[2].trim() }); i++; continue }
    if (t.startsWith('|')) {
      const rows = []
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        const cells = lines[i].trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim())
        if (!cells.every(c => /^:?-{2,}:?$/.test(c))) rows.push(cells)
        i++
      }
      out.push({ kind: 'table', head: rows[0] || [], rows: rows.slice(1) })
      continue
    }
    if (t.startsWith('>')) {
      const paras = [[]]
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        const inner = lines[i].trim().replace(/^>\s?/, '')
        if (!inner.trim()) paras.push([])
        else paras[paras.length - 1].push(inner.trim())
        i++
      }
      out.push({ kind: 'quote', items: paras.filter(p => p.length).map(p => p.join(' ')) })
      continue
    }
    const listKind = /^- /.test(t) ? 'ul' : /^\d+\.\s/.test(t) ? 'ol' : ''
    if (listKind) {
      const items = []
      while (i < lines.length) {
        const l = lines[i].trim()
        const isItem = listKind === 'ul' ? /^- /.test(l) : /^\d+\.\s/.test(l)
        if (isItem) items.push(l.replace(listKind === 'ul' ? /^- / : /^\d+\.\s+/, ''))
        else if (l.startsWith('```')) break
        else if (l && items.length && /^\s+\S/.test(lines[i])) items[items.length - 1] += ' ' + l
        else break
        i++
      }
      const start = listKind === 'ol' ? Number((t.match(/^(\d+)\./) || [])[1] || 1) : 1
      out.push(start > 1 ? { kind: listKind, items, start } : { kind: listKind, items })
      continue
    }
    const para = []
    while (i < lines.length && lines[i].trim() && !/^(#{1,4}\s|>|\||- |\d+\.\s)/.test(lines[i].trim())) {
      para.push(lines[i].trim())
      i++
    }
    out.push({ kind: 'p', text: para.join(' ') })
  }
  return out
}

/** Under a "Check yourself" heading, each bold question followed by its quoted answer becomes one `qa` block
 *  ({ question, answer: [paragraphs] }), so the page can keep the answer hidden until the learner has written one
 *  (0.9 persona test: the answers used to print right under each question, spending the retrieval practice). Everything else,
 *  and every other section, is left as it was. */
export function revealBlocks(blocks) {
  const list = arr(blocks)
  const out = []
  let inside = false
  for (let i = 0; i < list.length; i++) {
    const b = list[i]
    if (b.kind === 'h2') inside = /^check yourself\b/i.test(str(b.text).trim())
    const next = list[i + 1]
    const bold = b.kind === 'p' && /^\*\*[\s\S]+\*\*$/.test(str(b.text).trim()) && !/\*\*[\s\S]*\*\*[\s\S]*\*\*/.test(str(b.text).trim().slice(2, -2))
    if (inside && bold && next && next.kind === 'quote') {
      out.push({ kind: 'qa', question: str(b.text).trim().slice(2, -2).trim(), answer: arr(next.items) })
      i++
      continue
    }
    out.push(b)
  }
  return out
}

/** Can the answer be shown yet? Only once the learner has written something of their own. */
export function canReveal(answer) {
  return str(answer).trim().length >= 2
}

/** Inline pieces of one line: text, code, asof, and strong or em around their own pieces. Code spans are read first
 *  and kept whole, so a code span inside bold or italic renders as code and a star inside a code span is just a star.
 *  A strong or em span carries `children` (its pieces) and `text` (its words, without markers). Unclosed markers stay
 *  as text. */
export function inlineSpans(text) {
  const s = str(text)
  const codes = []
  // Code spans become placeholders that hold no star, so emphasis can never start or end inside one.
  const masked = s.replace(/`([^`]+)`/g, (_, code) => `\uE000${codes.push(code) - 1}\uE001`)
  return emphasis(masked, codes)
}

const PLACEHOLDER = /\uE000(\d+)\uE001/g

function unmask(text, codes) {
  return text.replace(PLACEHOLDER, (_, i) => codes[Number(i)])
}

function plainSpans(text, codes) {
  const out = []
  const re = /\uE000(\d+)\uE001|\b([Aa]s of Hermes \d+\.\d+(?:\.\d+)?)/g
  let last = 0
  let m
  while ((m = re.exec(text))) {
    if (m.index > last) out.push({ kind: 'text', text: text.slice(last, m.index) })
    out.push(m[1] !== undefined ? { kind: 'code', text: codes[Number(m[1])] } : { kind: 'asof', text: m[2] })
    last = re.lastIndex
  }
  if (last < text.length) out.push({ kind: 'text', text: text.slice(last) })
  return out
}

function emphasis(text, codes) {
  const out = []
  // **strong**, or *em* whose first and last characters are neither a space nor a star.
  const re = /\*\*(.+?)\*\*|\*(?![\s*])([^*]*?[^\s*])\*/g
  let last = 0
  let m
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(...plainSpans(text.slice(last, m.index), codes))
    const inner = m[1] !== undefined ? m[1] : m[2]
    const children = emphasis(inner, codes)
    out.push({ kind: m[1] !== undefined ? 'strong' : 'em', text: unmask(inner, codes).replace(/\*/g, ''), children })
    last = re.lastIndex
  }
  if (last < text.length) out.push(...plainSpans(text.slice(last), codes))
  return out
}

/* ------------------------------------------------------- the home profile -- */
//
// host.newChat(profile) moves the app's active gateway profile to the practice profile (Hermes 0.22.4,
// store/profile.ts newSessionInProfile -> ensureGatewayProfile), and a plugin's REST calls follow the active profile
// (api/plugins.ts pluginRest -> profileScoped). A practice profile has no Field Academy backend, so the page must not
// call it there. These decide what the page does about it; plugin.js does it.

const PRACTICE_PROFILE = /^academy-practice(?:-b)?(?:-[0-9]{1,2})?$/

export function isPracticeProfile(name) {
  return PRACTICE_PROFILE.test(str(name).trim().toLowerCase())
}

/** What to do before a backend call: 'call' (fine as is), 'repin' (go back to the home profile first; only from the
 *  page itself, never from a background poll) or 'wait' (no way back from here: say so). */
export function homeAction(active, home, canEnsure, fromPage) {
  if (!isPracticeProfile(active)) return 'call'
  if (fromPage && home && !isPracticeProfile(obj(home).profile) && canEnsure) return 'repin'
  return 'wait'
}
