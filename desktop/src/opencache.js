// Field Academy's open cache. Pure functions, no imports, so node tests can run them (tests/open_cache.test.mjs).
//
// Hermes starts the plugin backend and shakes hands with the gateway before the page's first request can answer,
// which a learner sees as 2 to 3 seconds of skeleton on every open. The page keeps a small copy of the last answers
// the map was drawn from (the passport, the Guide trail and the Foundations list) in the desktop SDK's own storage
// (ctx.storage), draws the map from that copy at once, and swaps in the fresh answers when they arrive. The very
// first open still shows the skeleton.
//
// What is kept: only what the map reads. Lessons and steps, sources and watch lists, recent evidence, the Field
// Record's body and every saved-record path are dropped. A key named like a credential is dropped, and an answer carrying
// anything shaped like a credential is never kept at all. Each copy is capped in size, tied to the profile and
// connection it came from, and stamped with a version so an older copy is ignored.
//
// While the map shows a copy, nothing on it acts on that copy: a click on a button or link is held and replayed on
// the same control once the fresh answer has redrawn it (the control's fresh handler runs, with fresh data), and
// navigation waits the same way. A control the fresh answer removed simply does nothing.

export const OPEN_CACHE_VERSION = 1
export const OPEN_CACHE_KINDS = ['passport', 'deployer', 'foundations']
/** Per kept answer, in characters of JSON. What the map reads of the passport runs about 30 KB on the full curriculum. */
export const OPEN_CACHE_MAX_CHARS = 64 * 1024
/** A copy older than this is not shown: after a month away the learner sees the skeleton, then the truth. */
export const OPEN_CACHE_MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000

const obj = value => (value && typeof value === 'object' && !Array.isArray(value) ? value : {})
const arr = value => (Array.isArray(value) ? value : [])
const isObj = value => Boolean(value) && typeof value === 'object' && !Array.isArray(value)

/** Storage key for one kind, under the plugin's own namespace (the SDK prefixes hermes.plugin.field-academy.). */
export function openCacheKey(kind) {
  return `open-cache.${kind}`
}

/** Which Hermes the copy belongs to: the profile and the connection the page talked to. */
export function openScope(profile, connectionId) {
  const p = typeof profile === 'string' ? profile.trim() : ''
  if (!p) return ''
  const c = connectionId === null || connectionId === undefined ? '' : String(connectionId)
  return `${c}|${p}`
}

/* ------------------------------------------------------------ secrets -- */

const SECRET_KEY = /^(?:.*[_-])?(?:token|secret|password|passwd|passphrase|api[_-]?key|apikey|access[_-]?key|private[_-]?key|auth|authorization|cookie|credentials?|session[_-]?key|client[_-]?secret|bearer)$/i

const SECRET_VALUE = [
  /\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{16,}/, // OpenAI and Anthropic style keys
  /\bgh[pousr]_[A-Za-z0-9]{20,}/, // GitHub tokens
  /\bgithub_pat_[A-Za-z0-9_]{20,}/,
  /\bxox[abprs]-[A-Za-z0-9-]{10,}/, // Slack tokens
  /\bAKIA[0-9A-Z]{16}\b/, // AWS access key ids
  /\bAIza[0-9A-Za-z_-]{30,}/, // Google API keys
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
  /\bBearer\s+[A-Za-z0-9._~+/=-]{16,}/i,
  /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}/, // JWTs
  /\b\d{8,10}:[A-Za-z0-9_-]{30,}/, // Telegram bot tokens
]

/** True when a key reads like a credential's name. */
export function isSecretKey(key) {
  return SECRET_KEY.test(String(key))
}

/** True when any string anywhere in the value is shaped like a credential. */
export function carriesSecret(value, depth = 0) {
  if (depth > 40) return true // refuse what we can't walk
  if (typeof value === 'string') return SECRET_VALUE.some(re => re.test(value))
  if (Array.isArray(value)) return value.some(item => carriesSecret(item, depth + 1))
  if (isObj(value)) return Object.entries(value).some(([k, v]) => carriesSecret(k, depth + 1) || carriesSecret(v, depth + 1))
  return false
}

/** A deep copy without any key named like a credential. */
export function withoutSecretKeys(value, depth = 0) {
  if (depth > 40) return null
  if (Array.isArray(value)) return value.map(item => withoutSecretKeys(item, depth + 1))
  if (!isObj(value)) return value
  const out = {}
  for (const [k, v] of Object.entries(value)) {
    if (isSecretKey(k)) continue
    out[k] = withoutSecretKeys(v, depth + 1)
  }
  return out
}

/* -------------------------------------------------- what the map reads -- */

/** The mission fields the map draws (trail.js MAP_FIELDS.mission), plus the ones that say where a mission sits. */
const MISSION_KEEP = ['id', 'title', 'status', 'level', 'level_name', 'minutes', 'completed_steps', 'total_steps', 'version', 'use_text', 'strength', 'strength_word', 'changed', 'time', 'placed', 'trail', 'camp']
/** What the map's summit flag reads of a path's Field Record. */
const CERTIFICATE_KEEP = ['status', 'remaining', 'words', 'label', 'title']

function pick(value, keys) {
  if (!isObj(value)) return value
  const out = {}
  for (const key of keys) if (key in value) out[key] = value[key]
  return out
}

/** One mission as the map reads it: no lesson, no steps, no sources. */
function slimMission(mission) {
  return pick(mission, MISSION_KEEP)
}

function slimTrack(track) {
  if (!isObj(track)) return track
  const out = { ...track }
  if (Array.isArray(track.missions)) out.missions = track.missions.map(slimMission)
  if (Array.isArray(track.placed)) out.placed = track.placed.map(slimMission)
  if (isObj(track.certificate)) out.certificate = pick(track.certificate, CERTIFICATE_KEEP)
  return out
}

function slimPassport(passport) {
  if (!isObj(passport) || !Array.isArray(passport.tracks)) return null
  const { recent_evidence, ...rest } = passport
  return { ...rest, tracks: passport.tracks.map(slimTrack) }
}

function slimDeployer(deployer) {
  if (!isObj(deployer)) return null
  const out = { available: deployer.available }
  if (isObj(deployer.track)) out.track = slimTrack(deployer.track)
  const cert = obj(deployer.certificate)
  out.certificate = { label: cert.label, status: cert.status }
  out.about = { disclaimer: obj(deployer.about).disclaimer }
  return out
}

function slimFoundations(foundations) {
  if (!isObj(foundations) || !Array.isArray(foundations.missions)) return null
  return {
    missions: foundations.missions.map(m => {
      if (!isObj(m)) return m
      return {
        id: m.id, order: m.order, title: m.title, kind: m.kind, level: m.level, minutes: m.minutes, trail: m.trail, camp: m.camp,
        attempts: arr(m.attempts).map(a => (isObj(a) ? { id: a.id, status: a.status, stage: a.stage } : a)),
      }
    }),
  }
}

const SLIM = { passport: slimPassport, deployer: slimDeployer, foundations: slimFoundations }

/** What would be kept of one answer, or null when nothing should be. */
export function slimFor(kind, data) {
  const slim = SLIM[kind]
  if (!slim) return null
  let out = null
  try { out = slim(data) } catch (error) { return null }
  if (!out) return null
  out = withoutSecretKeys(out)
  if (carriesSecret(out)) return null
  return out
}

/* ------------------------------------------------------------ storage -- */

/** The record to store for one answer, or null when this answer must not be kept (too big, a credential in it, no scope). */
export function packSnapshot(kind, data, scope, now = Date.now()) {
  if (!scope) return null
  const slim = slimFor(kind, data)
  if (!slim) return null
  let text = ''
  try { text = JSON.stringify(slim) } catch (error) { return null }
  if (text.length > OPEN_CACHE_MAX_CHARS) return null
  return { v: OPEN_CACHE_VERSION, scope, at: now, data: slim }
}

/** The kept answer, if this record is ours, current, for this scope and not too old. */
export function unpackSnapshot(kind, record, scope, now = Date.now()) {
  if (!isObj(record) || !scope) return null
  if (record.v !== OPEN_CACHE_VERSION || record.scope !== scope) return null
  const at = Number(record.at)
  if (!Number.isFinite(at) || at > now + 60000 || now - at > OPEN_CACHE_MAX_AGE_MS) return null
  // Re-check on the way out too: a copy written by an older build must not bring back something we no longer keep.
  return slimFor(kind, record.data)
}

/** Read one kept answer through a PluginStorage (get(key, fallback)). Never throws. */
export function readSnapshot(storage, kind, scope, now = Date.now()) {
  try {
    if (!storage || typeof storage.get !== 'function') return null
    return unpackSnapshot(kind, storage.get(openCacheKey(kind), null), scope, now)
  } catch (error) {
    return null
  }
}

/**
 * Keep one fresh answer. An answer that must not be kept also clears the old copy, so a copy is never older than the
 * last answer the page was given. Returns true when a copy was written. Never throws.
 */
export function writeSnapshot(storage, kind, data, scope, now = Date.now()) {
  try {
    if (!storage || typeof storage.set !== 'function') return false
    const record = packSnapshot(kind, data, scope, now)
    if (!record) {
      if (typeof storage.remove === 'function') storage.remove(openCacheKey(kind))
      return false
    }
    storage.set(openCacheKey(kind), record)
    return true
  } catch (error) {
    return false
  }
}

/* ---------------------------------------------------------- first paint -- */

/**
 * What the page draws on first paint, from the live answers (`live`, undefined until they come) and the kept copies
 * (`cached`). Returns { state: 'skeleton' | 'ready', passport, deployer, preview }.
 *
 * The rules the page had stay: it waits for the Guide trail as well as the passport, so the map's counts appear once,
 * and a page other than the map (a mission an in-chat offer opened, say) waits for live answers. What is new: on the
 * map, a kept copy stands in for an answer that hasn't come yet, and `preview` says some of the screen is a copy.
 * While the app is on a practice profile (homeReady false) nothing is live yet; what the page already held from the
 * home profile counts as a copy too.
 */
export function openPlan({ live = {}, cached = {}, view = 'map', homeReady = true } = {}) {
  const map = view === 'map'
  const present = value => value !== undefined && value !== null

  let passport = homeReady ? live.passport : undefined
  let passportCopy = false
  if (!present(passport) && map) {
    passport = present(live.passport) ? live.passport : cached.passport
    passportCopy = present(passport)
  }

  const deployerSettled = homeReady && Boolean(live.deployerSettled)
  let deployer = deployerSettled ? live.deployer : undefined
  let deployerCopy = false
  if (!deployerSettled && map) {
    const copy = present(live.deployer) ? live.deployer : cached.deployer
    if (present(copy)) {
      deployer = copy
      deployerCopy = true
    }
  }

  if (!present(passport) || (!deployerSettled && !deployerCopy)) return { state: 'skeleton', passport: undefined, deployer: undefined, preview: false }
  return { state: 'ready', passport, deployer, preview: passportCopy || deployerCopy }
}

/**
 * While the map shows a kept copy, what to do with one event on it:
 *   'hold'  a click on a button or link: stop it now and replay it on the same control once the live answer is drawn.
 *   'block' Enter with a modifier in a text field (a submit shortcut): stop it; the learner presses it again.
 *   'pass'  anything else (scrolling, typing, J and K, Tab).
 * `event` needs type, key, metaKey/ctrlKey and a target with closest() (a DOM event does).
 */
export const HOLD_SELECTOR = 'button, a[href], [role="button"], [role="link"], [role="menuitem"], [role="tab"], input[type="submit"], input[type="button"]'

export function previewIntent(event) {
  const e = event || {}
  const target = e.target && typeof e.target.closest === 'function' ? e.target : null
  if (e.type === 'click') return target && target.closest(HOLD_SELECTOR) ? 'hold' : 'pass'
  if (e.type === 'keydown' && (e.key === 'Enter' || e.key === ' ')) {
    const field = target && target.closest('textarea, input, [contenteditable="true"], select')
    if (field) return e.key === 'Enter' && (e.metaKey || e.ctrlKey) ? 'block' : 'pass'
    // Enter or Space on a focused control: the browser turns it into a click, which is held. Enter on the page
    // itself (the J/K list opening a trail) goes through navigation, which waits on its own.
    return 'pass'
  }
  return 'pass'
}
