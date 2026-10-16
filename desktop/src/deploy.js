// The Deployer path's reading logic for the page. Pure functions, no imports, so node tests can run them
// (tests/deploy.test.mjs).
//
// The page reads Hermes through the same read-only calls the mission checks use: the scheduler list and the
// chat list. It never writes, never starts a job and never runs anything. What it collects here is only
// times, and whether a run looks failed. The backend judges them (evidence.py). Hermes' lists come in shapes
// this plugin does not control, so nothing here assumes a field: a record is walked for anything that reads as
// a time, and the result says plainly when nothing did.

const str = value => (typeof value === 'string' ? value : '')
const arr = value => (Array.isArray(value) ? value : [])
const isObject = value => value && typeof value === 'object' && !Array.isArray(value)

const ISO = /\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?/
const FAILED = /\b(?:fail(?:ed|ure)?|error(?:ed)?|exception|timeout|timed out|denied|unauthori[sz]ed|forbidden|revoked|rate[- ]?limit(?:ed)?|429|401|403)\b/i
const STATUS_KEY = /^(?:status|state|result|outcome|last_status|exit|error|last_error)$/i
const TIME_KEY = /(?:time|_at|date|run|start|finish|end|created|last|ts|stamp)/i
const NOT_TIME_KEY = /(?:count|total|number|_id|^id$|attempt|size|bytes|duration|seconds|^ms$|retries|interval)/i
const EPOCH_LOW = 1500000000
const EPOCH_HIGH = 2500000000
const MAX_TIMES = 500

/** A time as `2026-10-03T09:00:00Z`, or '' when the value does not read as one. */
export function toIso(value) {
  let when = null
  if (typeof value === 'number' && Number.isFinite(value)) {
    let seconds = value
    if (seconds > EPOCH_HIGH * 100) seconds /= 1000
    if (seconds >= EPOCH_LOW && seconds <= EPOCH_HIGH) when = new Date(seconds * 1000)
  } else if (typeof value === 'string') {
    const match = value.match(ISO)
    if (match) {
      const text = match[0].replace(' ', 'T')
      const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(text)
      when = new Date(hasZone ? text : `${text}Z`)
    }
  }
  if (!when || Number.isNaN(when.getTime())) return ''
  return when.toISOString().replace(/\.\d{3}Z$/, 'Z')
}

function looksFailed(record) {
  for (const [key, value] of Object.entries(record)) {
    if (!STATUS_KEY.test(key)) continue
    if (typeof value === 'string' && value.trim() && FAILED.test(value)) return true
    if (/^(?:error|last_error)$/i.test(key) && value && typeof value !== 'boolean') return true
  }
  return false
}

/**
 * Every time in a record, split by whether the run looks failed. Walks nested lists and objects, so a
 * `runs` array or a `history` list is read the same way as a flat `last_run_at`.
 */
export function collectRunTimes(record) {
  const times = new Set()
  const failed = new Set()
  const walk = (value, key, bad, depth) => {
    if (depth > 6 || times.size + failed.size > MAX_TIMES) return
    if (Array.isArray(value)) {
      value.forEach(item => walk(item, key, bad, depth + 1))
      return
    }
    if (isObject(value)) {
      const here = bad || looksFailed(value)
      for (const [k, v] of Object.entries(value)) walk(v, k, here, depth + 1)
      return
    }
    if (typeof value !== 'string' && typeof value !== 'number') return
    // A number only counts under a key that names a time. A string counts anywhere, if it carries a date.
    if (typeof value === 'number' && (!TIME_KEY.test(key) || NOT_TIME_KEY.test(key))) return
    const iso = toIso(value)
    if (iso) (bad ? failed : times).add(iso)
  }
  walk(record, '', false, 0)
  return { times: [...times].sort(), failed: [...failed].sort() }
}

const nameOf = job => str(job && (job.name || job.title || job.id)).trim()

/** The scheduler entries that carry this name, ignoring case. */
export function findJobs(jobs, name) {
  const wanted = str(name).trim().toLowerCase()
  if (!wanted) return []
  return arr(jobs).filter(job => nameOf(job).toLowerCase() === wanted)
}

/** Chats Hermes started for the job: its title or id names the job. */
export function findSessions(sessions, name) {
  const wanted = str(name).trim().toLowerCase()
  if (!wanted) return []
  return arr(sessions).filter(item => `${str(item && item.title)} ${str(item && item.id)} ${str(item && item.source)}`.toLowerCase().includes(wanted))
}

/**
 * What the page read from Hermes for one job: the sample the backend adds to its own record, and a note for the
 * screen saying what was and was not found. `found` is true when any time was read.
 */
export function sampleFromHermes({ jobs, sessions }, name) {
  const matched = findJobs(jobs, name)
  const chats = findSessions(sessions, name)
  const merged = { times: new Set(), failed: new Set() }
  for (const job of matched) {
    const part = collectRunTimes(job)
    part.times.forEach(t => merged.times.add(t))
    part.failed.forEach(t => merged.failed.add(t))
  }
  for (const chat of chats) {
    const part = collectRunTimes({ created_at: chat.created_at, started_at: chat.started_at, updated_at: chat.updated_at, last_active: chat.last_active })
    part.times.forEach(t => merged.times.add(t))
  }
  const times = [...merged.times].sort()
  const failed = [...merged.failed].sort()
  let note
  if (!matched.length && !chats.length) note = `Hermes's scheduler list does not show a job named ${name}, and no chat carries that name.`
  else if (!times.length && !failed.length) note = 'Hermes lists the job but shows no run times for it.'
  else note = `Read ${times.length} run times and ${failed.length} failed runs from ${matched.length ? 'the scheduler list' : 'the chat list'}${matched.length && chats.length ? ' and the chat list' : ''}.`
  return {
    sample: { source: matched.length ? (chats.length ? 'desktop scheduler and chat lists' : 'desktop scheduler list') : 'desktop chat list', times, failed },
    found: times.length + failed.length > 0,
    jobFound: matched.length > 0,
    note,
  }
}

/** The Hermes version out of whatever the runtime check returned. '' when it shows none. */
export function versionFrom(runtime) {
  if (!isObject(runtime)) return ''
  for (const key of ['version', 'hermes_version', 'agent_version', 'app_version']) {
    const value = runtime[key]
    if (typeof value === 'string' && /\d+\.\d+/.test(value)) return value.trim().slice(0, 40)
  }
  return ''
}

/** Words for where a part of the path stands. State never rides on colour alone. */
export function stateWords(state) {
  return {
    verified: 'Passed',
    awaiting_review: 'Waiting for the reviewer',
    in_progress: 'Started',
    not_started: 'Not started',
  }[state] || 'Not started'
}

/** The address that opens a folder in the system's file manager, for the Open button. */
export function folderUrl(path) {
  const clean = str(path)
  if (!clean) return ''
  const slashed = clean.replace(/\\/g, '/')
  return `file://${slashed.startsWith('/') ? '' : '/'}${slashed.split('/').map(encodeURIComponent).join('/')}`
}

/** How the clock reads for a deployment that is running: whole days since it started. */
export function daysSince(iso, now = new Date()) {
  const start = new Date(iso)
  if (!iso || Number.isNaN(start.getTime())) return 0
  return Math.max(0, Math.floor((now.getTime() - start.getTime()) / 86400000))
}
