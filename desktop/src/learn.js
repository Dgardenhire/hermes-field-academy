// Field Academy's learning logic for the page. Pure functions, no imports, so node tests can
// run them (tests/learn.test.mjs). Two kinds: how the page words time, support and strength,
// and how the live checks read what Hermes lists. Hermes' lists come in shapes this plugin
// does not control, so everything here reads a record as text and never assumes a field.

const str = value => (typeof value === 'string' ? value : '')
const arr = value => (Array.isArray(value) ? value : [])
const obj = value => (value && typeof value === 'object' && !Array.isArray(value) ? value : {})

export const norm = value => String(value == null ? '' : value).trim().toLowerCase()

/** A record as one lowercase string, so a marker is found wherever Hermes keeps it. */
export function blob(value) {
  try {
    return JSON.stringify(value).toLowerCase()
  } catch (error) {
    return ''
  }
}

/* ----------------------------------------------------------------- words -- */

/** "Due now", "Due tomorrow", "Due in 5 days", for a review's due date. */
export function dueWords(iso, now = new Date()) {
  const due = new Date(iso)
  if (!iso || Number.isNaN(due.getTime())) return ''
  const days = Math.ceil((due.getTime() - now.getTime()) / 86400000)
  if (days <= 0) return 'Due now'
  if (days === 1) return 'Due tomorrow'
  if (days < 14) return `Due in ${days} days`
  return `Due ${due.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
}

/** How much time a mission or a review will take, in words. */
export function minutesWords(minutes) {
  const n = Math.max(0, Math.round(Number(minutes) || 0))
  if (n < 60) return `About ${n} ${n === 1 ? 'minute' : 'minutes'}`
  const hours = Math.floor(n / 60)
  const rest = n % 60
  return `About ${hours} ${hours === 1 ? 'hour' : 'hours'}${rest ? ` ${rest} minutes` : ''}`
}

/** The time each step takes, as one line the mission shows under its title. */
export function timeLine(steps, labels) {
  return arr(steps)
    .filter(step => Number(obj(step).minutes) > 0)
    .map(step => `${(labels && labels[step.kind]) || step.kind} ${step.minutes} min`)
    .join(' · ')
}

/** Strength is shown as a word as well as a bar: state never rides on colour alone. */
export function strengthWord(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'Not reviewed yet'
  if (value >= 85) return 'Strong'
  if (value >= 70) return 'Holding'
  if (value >= 40) return 'Fading'
  return 'Weak'
}

/* --------------------------------------------------------------- support -- */

/**
 * The three stages of support a mission fades through, and which one the learner is at.
 * Full example, then an example with gaps, then on their own. A placed step counts as done.
 */
export function supportStages(steps) {
  const list = arr(steps).filter(step => step && typeof step === 'object')
  const done = step => ['done', 'placed'].includes(obj(step).status)
  const group = pick => list.filter(step => pick(step))
  const stages = [
    { id: 'full', label: 'Full example', help: 'You read a finished one.', steps: group(s => s.kind === 'example') },
    { id: 'half', label: 'Half done', help: 'You fill the gaps in one.', steps: group(s => s.kind === 'complete') },
    { id: 'none', label: 'On your own', help: 'You do it, and Hermes checks it.', steps: group(s => ['lab', 'explain', 'gate'].includes(s.kind)) },
  ]
  let found = false
  return stages.map(stage => {
    const complete = stage.steps.length > 0 && stage.steps.every(done)
    const state = complete ? 'done' : !found ? 'now' : 'later'
    if (!complete) found = true
    return { id: stage.id, label: stage.label, help: stage.help, state, count: stage.steps.length }
  })
}

/* -------------------------------------------------------- reading Hermes -- */

/** What kind of connection a route is: this computer, another computer, or Hermes Cloud. '' when it cannot tell. */
export function classifyConnection(route) {
  const text = blob(route)
  if (!text || text === '{}') return ''
  if (/cloud|nous/.test(text)) return 'cloud'
  if (/ssh|remote|tailscale|https?:\/\/(?!localhost|127\.)/.test(text)) return 'remote'
  if (/local|127\.0\.0\.1|localhost|this computer|stdio|embedded|desktop/.test(text)) return 'local'
  return ''
}

export const CONNECTION_KEYS = { 'this computer': 'local', 'another computer': 'remote', 'hermes cloud': 'cloud', 'nous cloud': 'cloud' }

/** Whether a name starts with a mission's marker, ignoring case and a leading slash or space. */
/** Skill names out of either shape Hermes sends: a list, or lists grouped by category
 *  ({skills: {general: ['a', 'b']}}, which is what skills.manage list returns). */
export function flattenSkills(response) {
  const raw = response && typeof response === 'object' && !Array.isArray(response) && 'skills' in response ? response.skills : response
  const items = Array.isArray(raw) ? raw : raw && typeof raw === 'object' ? Object.values(raw).flat() : []
  return items
    .map(skill => (typeof skill === 'string' ? skill : String(obj(skill).name || obj(skill).id || '')).trim())
    .filter(Boolean)
}

/** The request a scheduled job carries. Hermes's list shows only `prompt_preview`, the first
 *  100 characters with "..." added, so a preview is marked as cut short. */
export function jobRequestRead(job) {
  const full = jobRequest(job)
  if (full) return { text: full, cut: false }
  const preview = typeof obj(job).prompt_preview === 'string' ? obj(job).prompt_preview.trim() : ''
  if (!preview) return { text: '', cut: false }
  const cut = preview.endsWith('...')
  return { text: cut ? preview.slice(0, -3).trimEnd() : preview, cut }
}

/** Whether pasted text is the job's own request: it must begin with what Hermes shows. */
export function pastedMatches(pasted, shown) {
  const squash = s => String(s || '').toLowerCase().replace(/\s+/g, ' ').trim()
  const a = squash(pasted)
  const b = squash(shown)
  return Boolean(a && b && a.startsWith(b))
}

export function startsWithMarker(name, marker) {
  return norm(name).replace(/^[\s/]+/, '').startsWith(norm(marker))
}

/** The five things a scheduled job's request must say, and whether the text says each. */
export const CUES = [
  { id: 'where', label: 'where to work', pattern: /\b(?:folder|directory|path|workspace|project|repo|in ~|\/users\/|~\/)/i },
  { id: 'read', label: 'what to read', pattern: /\b(?:read|open|look at|scan|check|review|use the|pull|fetch|collect)\b/i },
  { id: 'result', label: 'what a good result looks like', pattern: /\b(?:result|summary|report|output|should (?:include|list|have|be)|format|bullet|no more than|at most|one page|looks like)\b/i },
  { id: 'send', label: 'where to send it', pattern: /\b(?:send|deliver|post|email|message|notify|save (?:it )?(?:to|in)|write (?:it )?(?:to|in)|telegram|slack|file)\b/i },
  { id: 'fail', label: 'what to do on failure', pattern: /\b(?:fail|failure|error|if (?:it|you|anything|something)|can't|cannot|unable|otherwise|retry|stop and|tell me)\b/i },
]

export function promptCues(text) {
  const body = str(text)
  return CUES.map(cue => ({ id: cue.id, label: cue.label, found: cue.pattern.test(body) }))
}

/** The request text of a scheduled job, whichever field Hermes keeps it in. '' when none is shown. */
export function jobRequest(job) {
  const record = obj(job)
  for (const key of ['prompt', 'request', 'instruction', 'instructions', 'task', 'message', 'text', 'command', 'description']) {
    if (typeof record[key] === 'string' && record[key].trim()) return record[key].trim()
  }
  return ''
}

/** Whether a scheduled job carries a schedule, whichever field Hermes keeps it in. */
export function jobHasSchedule(job) {
  const record = obj(job)
  return ['schedule', 'cron', 'cron_expression', 'expression', 'every', 'interval', 'next_run', 'next_run_at', 'run_at', 'at', 'when']
    .some(key => record[key] !== undefined && record[key] !== null && record[key] !== '' && record[key] !== '?' && record[key] !== false)
}

/** The first timestamp on a record, as milliseconds, or null. */
export function recordTime(record) {
  const r = obj(record)
  for (const key of ['started_at', 'created_at', 'updated_at', 'last_active', 'last_active_at', 'timestamp', 'time']) {
    const raw = r[key]
    if (raw === undefined || raw === null || raw === '') continue
    const ms = typeof raw === 'number' ? (raw < 1e11 ? raw * 1000 : raw) : Date.parse(String(raw))
    if (Number.isFinite(ms)) return ms
  }
  return null
}
