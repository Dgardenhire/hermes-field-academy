// Page logic for Foundations missions 7 to 11, with no imports, tested in tests/loop_b.test.mjs. The screens are in
// foundations_b.js. Each mission names its lab note's fields (lab.note_fields) and the panels its page shows
// (lab.panels); these functions turn those into form rules, words and the calls the page sends.

const str = v => (v === null || v === undefined ? '' : String(v))
const arr = v => (Array.isArray(v) ? v : [])

/** The note fields for one phase ('first' or 'transfer'). */
export function phaseFields(mission, transfer = false) {
  const want = transfer ? 'transfer' : 'first'
  return arr(mission?.lab?.note_fields).filter(f => (f.for || 'first') === want)
}

/** Which try form a mission's Practice step shows (0.9 persona test). Every mission gets its own, or none:
 *  'fields'  missions 7 to 10, from lab.try_fields;
 *  'a'       missions 1, 2, 4, 5 and 6, from lab.note_fields_a.try (foundations_a.js);
 *  'none'    a mission with field notes and no try fields (mission 11 has no warm-up try);
 *  'memory'  mission 3's guess and Memory number. */
export function tryFormKind(mission) {
  const lab = mission?.lab || {}
  if (arr(lab.try_fields).length) return 'fields'
  if (arr(lab.note_fields_a?.try).length) return 'a'
  if (arr(lab.note_fields).length) return 'none'
  return 'memory'
}

/** The try fields of a mission that declares them. */
export function tryFields(mission) {
  return arr(mission?.lab?.try_fields)
}

/** The try note's body: only its own fields, numbers as numbers. */
export function tryBody(fields, form) {
  const body = noteBody(fields, form)
  delete body.for
  return body
}

/** What's missing or wrong in a field-by-field note, in the words the page shows. Mirrors foundations_b.clean_note. */
export function noteFieldProblems(fields, form) {
  const out = []
  for (const f of arr(fields)) {
    const raw = form?.[f.id]
    const empty = raw === undefined || raw === null || (typeof raw === 'string' && !raw.trim())
    if (empty) {
      if (f.required) out.push(`${f.label}: this one is needed.`)
      continue
    }
    if (f.kind === 'choice') {
      if (!arr(f.choices).some(c => c.value === raw)) out.push(`${f.label}: pick one of the choices.`)
    } else if (f.kind === 'number') {
      if (!/^\d{1,6}$/.test(str(raw).trim())) out.push(`${f.label}: a whole number.`)
    } else {
      const text = f.kind === 'long' ? str(raw).trim() : str(raw).split(/\s+/).join(' ').trim()
      const max = Number(f.max || (f.kind === 'long' ? 4000 : 300))
      if (text.length > max) out.push(`${f.label}: at most ${max} characters.`)
      if (text.length < Number(f.min || 1)) out.push(`${f.label}: a little more, please.`)
    }
  }
  return out
}

/** The body the page saves for a note: only this phase's fields, numbers as numbers. */
export function noteBody(fields, form, transfer = false) {
  const body = { for: transfer ? 'transfer' : 'first' }
  for (const f of arr(fields)) {
    const raw = form?.[f.id]
    if (raw === undefined || raw === null || (typeof raw === 'string' && !raw.trim())) continue
    body[f.id] = f.kind === 'number' ? Number(str(raw).trim()) : raw
  }
  return body
}

const HIDDEN = '[hidden on screen]'
const SECRET_NAME = /(token|secret|passw(?:or)?d|passwd|^pwd$|api[_-]?key|apikey|access[_-]?key|authorization|^auth$|bearer|cookie|credential|signature|^sig$|private[_-]?key)/i

/** Settings text as the page may show it (mission 7, 0.9 persona test): a password or token inside an address, a secret query
 *  value, a secret-named JSON value, a bearer token and common key shapes are hidden. The text copied by the button is
 *  the full one, so a paste into Hermes still works; only the screen (a screen share, a recording) never shows it. */
export function screenSafe(text) {
  let out = str(text)
  // user:password@ or token@ in any address
  out = out.replace(/\b([a-z][a-z0-9+.-]*:\/\/)([^\s\/@"'<>]+)@/gi, (_, scheme) => `${scheme}${HIDDEN}@`)
  // ?token=... &api_key=... and other secret-named query values
  out = out.replace(/([?&;])([^=&#\s"']+)=([^&#\s"']*)/g, (m, sep, name, value) => (SECRET_NAME.test(name) && value ? `${sep}${name}=${HIDDEN}` : m))
  // "Authorization": "...", "GITHUB_TOKEN": "...", "api_key": "..."
  out = out.replace(/("([^"\\]*)"\s*:\s*)"((?:[^"\\]|\\.)*)"/g, (m, lead, name, value) => (SECRET_NAME.test(name) && value ? `${lead}"${HIDDEN}"` : m))
  out = out.replace(/\b(Bearer|Basic|Token)\s+[A-Za-z0-9._~+\/=-]{8,}/g, (_, word) => `${word} ${HIDDEN}`)
  out = out.replace(/\b(?:sk-[A-Za-z0-9_-]{16,}|(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,}|xox[abprs]-[A-Za-z0-9-]{10,}|hf_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|AKIA[0-9A-Z]{16})/g, HIDDEN)
  return out
}

/** Does the app's Scheduled jobs page work on the practice profile? It follows the live gateway's profile. */
export function scheduledLine(liveProfile, practice) {
  const live = str(liveProfile)
  if (!practice) return { state: 'idle', title: 'Scheduled jobs', text: '' }
  if (!live) {
    return { state: 'unknown', title: 'Field Academy couldn\'t read which profile Scheduled jobs works on',
      text: `Check it yourself: send a message in a practice chat, then open Scheduled jobs and look for jobs named academy-. Those belong to ${practice}.` }
  }
  if (live === practice) return { state: 'pass', title: `Scheduled jobs works on ${practice}`, text: 'New jobs you make there land in the practice profile.' }
  return { state: 'fail', title: `Scheduled jobs works on ${live}`, text: `Press Open practice chat and send a message there. Scheduled jobs then works on ${practice}. Check here again before you press New cron.` }
}

/** Words for mission 8's two-run notice. */
export function watchWords(w) {
  if (!w || !w.ready) return { tone: 'idle', title: 'Waiting for your job\'s name', text: 'Save your job\'s name below, and Field Academy watches its run history.' }
  if (!w.found) return { tone: 'warn', title: `No job called ${w.job} in academy-practice`, text: 'Check the name as it shows in Scheduled jobs.' }
  const late = w.late ? ` ${w.late} of them late.` : ''
  if (w.landed) {
    return { tone: 'good', title: 'Two scheduled runs have landed', text: `${w.runs} runs the schedule fired.${late}${w.still_on ? ' The job is still on: pause or delete it now, or it keeps costing you every hour, then put your sleep setting back.' : ' The job is stopped.'}` }
  }
  return { tone: 'info', title: `${w.runs} of 2 scheduled runs so far`, text: `Field Academy checks again each time you open this page. The wait doesn't count toward your record's hours.${late}` }
}

/** The cron.manage calls that make one job the way a planted problem needs it: add, then pause when it should start paused. */
export function jobCalls(job) {
  const add = { action: 'add', name: job.name, schedule: job.schedule, prompt: job.prompt }
  if (job.deliver) add.deliver = job.deliver
  return { add, pause: Boolean(job.pause) }
}

/** The job id a cron.manage add returned, from either shape the gateway sends. */
export function addedJobId(result) {
  const r = result && typeof result === 'object' && 'result' in result ? result.result : result
  return str(r?.job_id || r?.job?.job_id || r?.job?.id || r?.id)
}

/** What the panel says when a job meant to start paused can't be confirmed paused (audit B1). Plain words, no jargon. */
export function jobStopWords(kind, job, profile, why = '') {
  const where = profile ? ` in ${profile}` : ''
  if (kind === 'on') {
    return `${job} is on${where} and Field Academy couldn't pause it, so it stopped there. It runs every hour on your AI provider until you stop it. Open Scheduled jobs${where}, pause or delete ${job}, then press Try again.`
  }
  if (kind === 'removed') return `Hermes made ${job}, but Field Academy couldn't pause it, so it deleted it. Nothing from it runs. Press Try again.`
  if (kind === 'unread') {
    return `Field Academy couldn't read the job list to confirm ${job} is paused${why ? ` (${why})` : ''}, so it stopped there. Open Scheduled jobs${where}: if ${job} is there and on, pause or delete it. Then press Try again.`
  }
  return `Hermes didn't confirm it made ${job}${why ? ` (${why})` : ''}, so Field Academy stopped there. Open Scheduled jobs${where}: if ${job} is there and on, pause or delete it. Then press Try again.`
}

const quiet = async (p) => { try { return await p() } catch (e) { return null } }
const stillOn = (state, job) => arr(state?.still_on).some(s => s?.name === job)
const recorded = (state, job) => arr(state?.made).includes(job)

/** Pause each job the backend lists as still on by the id it read from the job list (or its name), then delete what
 * still won't pause. The backend's reading of the list after each round decides, never the call's reply. */
async function stopStillOn(state, call, report) {
  let now = state
  const tried = []
  for (const action of ['pause', 'remove']) {
    const on = arr(now?.still_on)
    if (!on.length) break
    for (const j of on) {
      await quiet(() => call({ action, name: str(j.id) || str(j.name) }))
      if (action === 'remove') tried.push(str(j.name))
    }
    now = await report()
  }
  return { state: now, removed: tried.filter(n => !stillOn(now, n)) }
}

/**
 * Make the jobs a planted problem needs, failing closed (audit B1). `todo` is what /jobs returned; `call(params)` sends
 * cron.manage to the practice profile; `report()` posts /jobs-made, which reads the job list and records what's there.
 * A job meant to start paused is paused by the id the add returned, then confirmed from the list; if the add gave no id
 * it recognises, or the list still shows it on, it's paused by the listed id, then deleted, and nothing after it is
 * made. Returns { ok, state, message }; an add that throws for a job meant to run is rethrown.
 */
export async function makeJobs(todo, { call, report, profile = '', errorText = e => str(e?.message || e) }) {
  let state = todo
  if (arr(state?.still_on).length) { // left on by an earlier try: settle those before making anything
    const done = await stopStillOn(state, call, report)
    state = done.state
    const left = arr(state?.still_on)[0]
    if (left) return { ok: false, state, message: jobStopWords('on', left.name, profile) }
    if (done.removed.length) return { ok: false, state, message: jobStopWords('removed', done.removed[0], profile) }
  }
  for (const job of arr(todo?.jobs)) {
    const calls = jobCalls(job)
    let out = null
    let failed = null
    try { out = await call(calls.add) } catch (e) { failed = e }
    if (!calls.pause) {
      if (failed) { await quiet(report); throw failed }
      continue
    }
    const id = failed ? '' : addedJobId(out)
    if (id) await quiet(() => call({ action: 'pause', name: id }))
    try {
      state = await report()
    } catch (e) {
      await quiet(() => call({ action: 'pause', name: id || job.name }))
      return { ok: false, state, message: jobStopWords('unread', job.name, profile, errorText(e)) }
    }
    const done = await stopStillOn(state, call, report)
    state = done.state
    if (stillOn(state, job.name)) return { ok: false, state, message: jobStopWords('on', job.name, profile) }
    if (done.removed.includes(job.name)) return { ok: false, state, message: jobStopWords('removed', job.name, profile) }
    if (!recorded(state, job.name)) {
      await quiet(() => call({ action: 'pause', name: job.name }))
      return { ok: false, state, message: jobStopWords('missing', job.name, profile, failed ? errorText(failed) : '') }
    }
  }
  state = await report()
  const left = arr(state?.still_on)[0]
  if (left) return { ok: false, state, message: jobStopWords('on', left.name, profile) }
  return { ok: true, state, message: '' }
}

/** A page reading of the app's snapshot list, for mission 9's check 2 (never enough on its own). */
export function rollbackSample(out) {
  const r = out && typeof out === 'object' && 'result' in out ? out.result : out
  const list = arr(r?.checkpoints).slice(0, 30).map(c => ({ message: str(c?.message).slice(0, 200), timestamp: str(c?.timestamp).slice(0, 40) }))
  return { source: 'rollback.list', enabled: Boolean(r?.enabled), checkpoints: list }
}

/** Mission 7's transfer example as the settings block the learner reads. */
export function exampleBlock(example) {
  if (!example) return ''
  return JSON.stringify({ mcpServers: { notes: example } }, null, 2)
}

/** Which panels a mission's page shows. */
export function panelsFor(mission) {
  return arr(mission?.lab?.panels)
}

/* The mission 9 grid's cells by the name a check fact gives them (foundations_checks_b.GRID_NAMES). */
const GRID_CELLS = {
  'Terminal, before': 'tb', 'Terminal, after': 'ta', 'File edits, before': 'fb', 'File edits, after': 'fa',
  'Connected tools, before': 'cb', 'Connected tools, after': 'ca',
}

/** A check fact's value in words. Facts saved before the grid spoke in labels read "you: no_connector; the profile:
 *  asks"; those are put in the words of the mission's own choices, so the page never shows a raw value. */
export function factWords(fact, mission) {
  const value = str(fact?.value)
  const cell = GRID_CELLS[str(fact?.label)]
  const old = cell ? value.match(/^you: (\S+); the profile: (\S+)$/) : null
  if (!old) return value
  const field = arr(mission?.lab?.note_fields).find(f => f.id === cell && f.kind === 'choice')
  const say = v => (arr(field?.choices).find(c => c.value === v)?.label || v.replace(/_/g, ' '))
  return `You: ${say(old[1])}. The profile: ${say(old[2])}.`
}
