// Field Academy, desktop half. SOURCE: desktop/plugin.js is built from this file plus the shared
// hermes-ui-kit by `node ../hermes-ui-kit/scripts/build.mjs .` (esbuild). Edit here, then build.
// The built file imports only '@hermes/plugin-sdk', 'react' and 'react/jsx-runtime'.

import { useEffect, useRef, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'
import {
  Button,
  Codicon,
  Input,
  TRANSCRIPT_DIRECTIVE_AREA,
  Textarea,
  host,
  queryClient,
} from '@hermes/plugin-sdk'
import {
  Back, BadgeIcon, Card, Details, Facts, KeyHint, NotConnected, Page as KitPage, PageHeader, Pill, Ring,
  Section, SkeletonPage, StaleNotice, isTyping, modKey, registerPage, submitOnModEnter, useFocusOnMount, useJustChanged,
  useKeys, useListKeys, usePolled,
} from 'hermes-ui-kit'
import { Bezel, CampLine, CertCorners, Compass, Contours, ElevationProfile, FIELD_CSS, Legend, Seal, TrailMap, TrailMark } from './field.js'
import { compassReading, overview, trailModel } from './trail.js'
import { DEPLOYER_CSS, createDeployerViews, partFor } from './deployer.js'
import { BANNER_CSS, Banner } from './banner.js'
import { PROSE_CSS, Prose, withoutExampleWord } from './prose.js'
import { folderUrl, sampleFromHermes, versionFrom } from './deploy.js'
import {
  CONNECTION_KEYS, blob, classifyConnection, dueWords, flattenSkills, jobHasSchedule, jobRequest, jobRequestRead, minutesWords, norm, pastedMatches, promptCues,
  recordTime, startsWithMarker, strengthWord,
} from './learn.js'

const ROUTE = '/academy'
const QUERY_KEY = ['field-academy', 'passport']

/** The transcript directive this half renders. The agent half names the same
 *  string in DIRECTIVE; a test asserts the two agree, because a rename on one
 *  side alone is a silent no-op. */
const DIRECTIVE = 'field-academy-practice'

/** Directive attributes are untrusted model output. Bound them before use: a
 *  hallucinated value should render nothing, never a wall of text. */
const MISSION_ID_RE = /^[a-z0-9][a-z0-9._-]{0,63}$/i

/** Field Academy's own styles, on top of the kit, prefixed fa-. The app compiles its own
 *  stylesheet at build time and never scans a runtime plugin, so a utility class invented in
 *  this file could render unstyled with no error. Every word uses the text color: state
 *  shows through fills, icons and position, never by dimming text. Installed once at
 *  register (kit injector, removed on dispose), so the page, the status chip and the
 *  in-chat offer all have it. */
const CSS = `
.fa-paths{grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr))}
.fa-links{display:grid;gap:6px}
.fa-link{display:flex;align-items:flex-start;gap:10px;width:100%;text-align:left;padding:8px 10px;border-radius:var(--hk-radius);border:1px solid var(--hk-stroke);background:var(--hk-surface);color:inherit;font:inherit;cursor:pointer;transition:border-color 140ms ease,background-color 140ms ease}
.fa-link:hover{border-color:var(--fa-blaze,var(--hk-accent));background:var(--hk-hover)}
.fa-link:focus-visible{outline:2px solid var(--hk-accent);outline-offset:1px}
.fa-link .codicon:first-child{color:var(--fa-blaze-ink,var(--hk-accent));margin-top:2px}
.fa-link-title{display:block;font-weight:600}
.fa-link-credit{display:block;font-size:var(--hk-fs-sm)}
.fa-numbered{counter-reset:fa;list-style:none;margin:0;padding:0;display:grid;gap:8px}
.fa-numbered>li{counter-increment:fa;display:grid;grid-template-columns:24px 1fr;gap:10px;align-items:baseline}
.fa-numbered>li::before{content:counter(fa);font-size:18px;font-weight:200;line-height:1;font-variant-numeric:lining-nums tabular-nums;color:var(--fa-blaze-ink,var(--hk-ink));text-align:right}
.fa-bullets{margin:0;padding-left:18px;display:grid;gap:3px}
.fa-takeaway{margin:0;padding:0;list-style:none;display:grid;gap:8px}
.fa-takeaway li{position:relative;padding-left:18px;font-size:15px;line-height:1.5}
.fa-takeaway li::before{content:'';position:absolute;left:0;top:.62em;width:8px;height:2px;background:var(--fa-blaze)}
.fa-pic{margin:0;max-width:640px}
.fa-pic svg{width:100%;height:auto;display:block}
.fa-pic-box rect{fill:color-mix(in srgb,var(--hk-ink) 5%,var(--hk-bg));stroke:var(--hk-stroke);stroke-width:1.2}
.fa-pic-box[data-tone=blaze] rect{fill:color-mix(in oklab,var(--fa-blaze) 14%,var(--hk-bg));stroke:var(--fa-blaze)}
.fa-pic-frame rect{fill:none;stroke:color-mix(in srgb,var(--hk-ink) 30%,transparent);stroke-width:1.2;stroke-dasharray:5 5}
.fa-pic-title{fill:var(--hk-ink);font-size:15px;font-weight:700}
.fa-pic-line{fill:var(--hk-ink);font-size:12.5px;opacity:.85}
.fa-pic-cap{fill:var(--hk-ink);font-size:12px;font-weight:700;letter-spacing:.1em;font-variant-caps:all-small-caps;opacity:.75}
.fa-pic-link{stroke:var(--fa-blaze);stroke-width:1.6;fill:none;stroke-dasharray:4 4}
.fa-lore{margin:-4px 0 0;max-width:62ch;font-size:13.5px;line-height:1.55;font-style:italic;color:var(--hk-ink);opacity:.9}
.fa-deeper{padding-top:8px;border-top:1px solid var(--hk-stroke)}
.fa-table{width:100%;border-collapse:collapse;font-size:var(--hk-fs-sm);line-height:1.45}
.fa-table th{text-align:left;font-weight:600;padding:8px 8px 6px 0;border-bottom:1px solid var(--hk-stroke);font-variant-caps:all-small-caps;letter-spacing:.06em;font-size:var(--hk-fs)}
.fa-table td{padding:8px 8px 8px 0;border-bottom:1px solid var(--hk-stroke);vertical-align:top;overflow-wrap:break-word}
.fa-table tr:last-child td{border-bottom:0}
.fa-pre{font-family:var(--hk-mono);font-size:var(--hk-fs-sm);padding:7px 9px;border-radius:var(--hk-radius-sm);background:var(--hk-sunken);overflow-x:auto;margin:0}
.fa-chip{display:inline-flex;align-items:center;gap:6px;padding:0 6px;font-size:12px;color:var(--ui-text-primary);background:none;border:0;cursor:pointer}
.fa-chip:focus-visible{outline:2px solid var(--ui-accent);outline-offset:1px}
.fa-offer{margin:10px 0;max-width:560px}
.fa-doc{font-family:var(--hk-mono);font-size:var(--hk-fs-sm);white-space:pre-wrap;overflow-wrap:anywhere;padding:10px 12px;border-radius:var(--hk-radius-sm);background:var(--hk-sunken);margin:0;line-height:1.5}
.fa-select{width:100%;min-height:32px;padding:4px 8px;border-radius:var(--hk-radius-sm);border:1px solid var(--hk-stroke);background:var(--hk-surface);color:inherit;font:inherit}
.fa-select:focus-visible{outline:2px solid var(--hk-accent);outline-offset:1px}
.fa-field{display:grid;gap:4px}
.fa-field>label{font-weight:600}
.fa-inputs{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,15rem),1fr));gap:10px}
.fa-parts{display:grid;gap:10px;margin:0;padding:0;list-style:none}
.fa-part{display:grid;grid-template-columns:minmax(0,9.5rem) minmax(0,1fr);gap:4px 14px;align-items:baseline}
@container (max-width:560px){.fa-part{grid-template-columns:1fr}}
.fa-partial{display:grid;gap:8px}
.fa-gap{display:grid;gap:6px;padding:10px 12px;border:1px dashed var(--fa-faint);border-radius:var(--hk-radius);background:color-mix(in srgb,var(--fa-blaze) 4%,var(--hk-surface))}
.fa-gap[data-problem]{border-style:solid;border-color:var(--fa-blaze)}
.fa-gap>label{font-weight:600}
.fa-compare{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr));gap:10px}
.fa-compare>div{display:grid;gap:4px;padding:8px 10px;border-radius:var(--hk-radius-sm);background:var(--hk-sunken)}
.fa-support{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.fa-stage{display:grid;gap:6px;padding:10px 12px;border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);background:var(--hk-surface);min-width:0}
.fa-stage[data-state=now]{border-color:var(--fa-blaze);box-shadow:inset 3px 0 0 var(--fa-blaze)}
.fa-stage-bar{display:flex;gap:3px}
.fa-stage-bar i{display:block;flex:1;height:6px;border-radius:2px;border:1px solid var(--fa-faint)}
.fa-stage-bar i[data-fill]{background:var(--fa-blaze);border-color:var(--fa-blaze)}
.fa-stage[data-state=done] .fa-stage-bar i[data-fill]{background:var(--hk-ink);border-color:var(--hk-ink)}
.fa-stage-state{font-size:var(--hk-fs-sm)}
.fa-meter{height:6px;border-radius:3px;background:var(--hk-stroke);overflow:hidden}
.fa-meter>span{display:block;height:100%;background:var(--fa-blaze)}
.fa-rev{display:grid;grid-template-columns:minmax(0,1fr) 7.5rem 7rem;gap:6px 12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--hk-stroke)}
.fa-rev:last-child{border-bottom:0}
@container (max-width:620px){.fa-rev{grid-template-columns:minmax(0,1fr) 6.5rem}.fa-rev>.fa-rev-due{display:none}}
.fa-hint{display:grid;gap:4px;padding:8px 10px;border-left:3px solid var(--fa-blaze);background:var(--hk-sunken);border-radius:0 var(--hk-radius-sm) var(--hk-radius-sm) 0}
.fa-wrap{white-space:pre-wrap;overflow-wrap:anywhere}
.fa-choices{display:grid;gap:6px;margin:0;padding:0;border:0}
.fa-choice{display:flex;gap:10px;align-items:flex-start;padding:8px 10px;border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);background:var(--hk-surface);cursor:pointer}
.fa-choice:hover{border-color:var(--fa-blaze)}
.fa-choice[data-picked]{border-color:var(--fa-blaze);background:color-mix(in srgb,var(--fa-blaze) 8%,var(--hk-surface))}
.fa-choice input{margin-top:3px}
.fa-q{display:grid;gap:8px;padding:14px 16px;border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);background:var(--fa-paper)}
.fa-goal{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 10px}
.fa-use{border-left:3px solid var(--fa-blaze);padding:2px 0 2px 12px;display:grid;gap:3px}
.fa-placed{display:inline-flex;gap:5px;align-items:center;font-size:var(--hk-fs-sm)}
`

/* ---------------------------------------------------------------- gateway -- */

/** host.request resolves the JSON-RPC result, but older builds may hand back
 *  the envelope. Unwrap either. */
async function rpc(method, params = {}) {
  const raw = await host.request(method, params)
  return raw && typeof raw === 'object' && 'result' in raw ? raw.result : raw
}

/** Pull a countable list out of a response whose shape we do not control. */
function listOf(response, keys) {
  if (Array.isArray(response)) return response
  if (!response || typeof response !== 'object') return []
  for (const key of keys) {
    const value = response[key]
    if (Array.isArray(value)) return value
  }
  for (const value of Object.values(response)) {
    if (Array.isArray(value)) return value
  }
  return []
}

function firstText(...values) {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

/** The extra fields a live check asks for when the mission's gate lists none. */
const INPUTS_BY_CHECK = {
  automation: [
    { id: 'request', label: "The job's whole request, copied from Scheduled jobs (Hermes's list shows only its first 100 characters)", placeholder: 'Paste the request here', multiline: true },
  ],
  workspace: [
    { id: 'title', label: "Only if the marker doesn't show: the exact name of your practice chat", placeholder: 'Leave empty unless the check asks', optional: true },
  ],
}

function miss(id, what) {
  return { id, what }
}

/**
 * Every installed skill's name, read fresh. `commands.catalog` scans the skill folders on each
 * call (every skill is also a slash command), so a skill made a minute ago shows. `skills.manage`
 * list is cached once per Hermes process and grouped by category ({skills: {general: [...]}}), so
 * it is the fallback, flattened.
 */
async function skillNames() {
  const names = new Set()
  try {
    const catalog = await rpc('commands.catalog')
    const skills = catalog && typeof catalog.skills === 'object' && catalog.skills ? catalog.skills : {}
    for (const key of Object.keys(skills)) names.add(key.replace(/^\//, ''))
  } catch (error) {
    // older builds: fall through to the cached list
  }
  try {
    const listed = await rpc('skills.manage', { action: 'list' })
    for (const name of flattenSkills(listed)) names.add(name)
  } catch (error) {
    if (!names.size) throw error
  }
  return [...names].filter(Boolean)
}

/**
 * Checks that read the running installation through the live gateway, so a pass means the
 * thing exists on this computer right now. Each takes (step, inputs) and returns
 * { passed, title, detail, facts, missing }. The backend records the result and builds the
 * hint ladder from the miss ids; the step carries the learner's typed answers and the marker.
 *
 * A check is only as strong as what Hermes reports. Where a list doesn't show a field the
 * check would like to read, the result says so in its facts instead of passing silently.
 */
const CHECKS = {
  async runtime(step, inputs = {}) {
    const gateway = host.state.gateway.get()
    const profile = host.state.profile.get() || 'default'
    const missing = []
    let facts = []
    let answered = true
    try {
      const runtime = await rpc('setup.runtime_check')
      facts = [
        { label: 'Hermes home', value: firstText(runtime?.home, runtime?.hermes_home) || 'answered' },
        { label: 'Profile', value: profile },
      ]
    } catch (error) {
      answered = false
      missing.push(miss('no_answer', `This window couldn't reach Hermes (${String(error?.message || error)}).`))
    }
    if (answered && gateway !== 'open') {
      missing.push(miss('not_connected', "Hermes answered, but this window isn't Connected, so nothing you send will run."))
    }
    const typedProfile = norm(inputs.profile)
    if (answered && gateway === 'open') {
      if (!typedProfile) {
        missing.push(miss('missing_profile', 'Type your profile name. With one profile it is called default.'))
      } else if (typedProfile !== norm(profile)) {
        missing.push(miss('profile_mismatch', `You typed "${String(inputs.profile).trim()}". Hermes reports a different profile for this window.`))
      }
      const routes = typeof host.profileRoutes === 'function' ? await host.profileRoutes() : []
      const mine = routes.find(route => norm(route?.profile || 'default') === norm(profile)) || routes[0]
      const actual = classifyConnection(mine)
      const said = CONNECTION_KEYS[norm(inputs.connection)] || ''
      if (actual && said && actual !== said) {
        missing.push(miss('connection_mismatch', `You said "${inputs.connection}". Hermes reports this connection as something else.`))
      }
      if (!actual) facts.push({ label: 'Connection type', value: 'Hermes did not report it, so your answer was taken as written' })
      else facts.push({ label: 'Connection', value: actual === 'local' ? 'This computer' : actual === 'remote' ? 'Another computer' : 'Hermes Cloud' })
    }
    const passed = missing.length === 0
    return {
      passed,
      title: passed ? 'Your answers match what Hermes reports' : "That doesn't match yet",
      detail: passed
        ? 'Hermes answered, this window is connected, and the profile and connection you wrote down match.'
        : missing[0].what,
      facts: [{ label: 'Connection state', value: String(gateway) }, ...facts],
      missing,
    }
  },

  async workspace(step, inputs = {}) {
    const marker = norm(step.marker || '[FA-DESKTOP]')
    const sessions = listOf(await rpc('session.list'), ['sessions'])
    const tagged = sessions.filter(session => blob(session).includes(marker))
    const typed = norm(inputs.title)
    const since = Date.parse(step.since || '') || 0
    const named = typed.length >= 6
      ? sessions.filter(session => {
        const when = recordTime(session)
        return blob(session).includes(typed) && (when === null || !since || when >= since)
      })
      : []
    const passed = tagged.length > 0 || named.length > 0
    const missing = []
    if (!passed && sessions.length === 0) missing.push(miss('no_sessions', 'Hermes lists no saved sessions yet.'))
    if (!passed && sessions.length > 0) missing.push(miss('no_marker', `None of your ${plural(sessions.length, 'saved session', 'saved sessions')} carries ${step.marker || '[FA-DESKTOP]'}.`))
    return {
      passed,
      title: passed ? 'Your practice chat is saved' : "Your practice chat isn't there yet",
      detail: passed
        ? tagged.length
          ? `Hermes lists a saved session that starts with ${step.marker || '[FA-DESKTOP]'}, so the practice you started is kept.`
          : 'Hermes lists a session with the name you typed, started after you began this mission.'
        : missing[0].what,
      facts: [
        { label: 'Saved sessions', value: String(sessions.length) },
        { label: 'With the marker', value: String(tagged.length) },
        ...(named.length && !tagged.length ? [{ label: 'Matched by', value: 'the name you typed' }] : []),
      ],
      missing,
    }
  },

  async knowledge(step) {
    const marker = step.marker || 'academy-'
    const names = await skillNames()
    const skills = names
    const marked = names.filter(name => name && startsWithMarker(name, marker))
    const passed = marked.length > 0
    const missing = []
    if (!passed && skills.length === 0) missing.push(miss('no_skills', 'Hermes lists no skills yet.'))
    if (!passed && skills.length > 0) missing.push(miss('no_marked_skill', `None of your ${plural(skills.length, 'skill', 'skills')} has a name that starts with ${marker}.`))
    return {
      passed,
      title: passed ? 'Your skill is installed' : "Your skill isn't there yet",
      detail: passed
        ? `Hermes lists a skill you made, ${marked[0]}. It carries the ${marker} marker, so it is the one from this mission.`
        : missing[0].what,
      facts: [
        { label: 'Skills', value: String(skills.length) },
        { label: `Names starting ${marker}`, value: marked.join(', ') || 'none' },
      ],
      missing,
    }
  },

  async automation(step, inputs = {}) {
    const marker = step.marker || 'academy-'
    // Paused jobs are left out of the list unless asked for, and the lesson says a paused job is fine.
    const jobs = listOf(await rpc('cron.manage', { action: 'list', include_disabled: true }), ['jobs'])
    const pasted = String(inputs.request || '').trim()
    const marked = jobs.filter(job => startsWithMarker(firstText(job?.name, job?.title, job?.id), marker))
    const missing = []
    const facts = [
      { label: 'Jobs', value: String(jobs.length) },
      { label: `Names starting ${marker}`, value: marked.map(job => firstText(job?.name, job?.title, job?.id)).join(', ') || 'none' },
    ]
    if (jobs.length === 0) {
      missing.push(miss('no_jobs', 'Hermes lists no scheduled jobs yet.'))
    } else if (marked.length === 0) {
      missing.push(miss('no_marked_job', `None of your ${plural(jobs.length, 'job', 'jobs')} has a name that starts with ${marker}.`))
    } else {
      // Judge the best-built job, so a learner with a rough draft and a good one passes on the good one.
      // Hermes's list shows only the first 100 characters of a request. When it is cut short, the
      // learner pastes the whole request and it must begin with what Hermes shows for that job,
      // so the five points are read from the job's own text and never from words typed here alone.
      const reads = marked.map(job => {
        const shown = jobRequestRead(job)
        let request = shown.text
        let matched = !shown.cut
        if (shown.cut) {
          matched = pastedMatches(pasted, shown.text)
          request = matched ? pasted : ''
        }
        const cues = request ? promptCues(request) : null
        return { job, request, shown, matched, cues, schedule: jobHasSchedule(job), found: cues ? cues.filter(c => c.found).length : 0 }
      })
      const best = reads.slice().sort((a, b) => (b.schedule - a.schedule) || (b.matched - a.matched) || (b.found - a.found))[0]
      if (!best.schedule) missing.push(miss('no_schedule', 'The job has no schedule. Set when it runs, even if you leave it paused.'))
      if (best.shown.cut && !best.matched) {
        facts.push({ label: 'Hermes shows', value: `the first 100 characters of the request, "${best.shown.text.slice(0, 60)}..."` })
        missing.push(pasted
          ? miss('request_mismatch', "The request you pasted doesn't begin the way Hermes shows this job's request. Copy it from the job itself.")
          : miss('paste_request', "Hermes shows only the start of the job's request. Paste the whole request below so the check can read all five points."))
      } else if (best.request) {
        const left = best.cues.filter(c => !c.found).map(c => c.label)
        facts.push({ label: 'Request says', value: `${best.found} of ${best.cues.length} points` })
        if (best.found < 4 || best.request.length < 120) {
          missing.push(miss('prompt_thin', `The request doesn't say ${left.length ? left.join(', ') : 'enough'} yet. It needs at least four of the five points and more than a line.`))
        }
      } else {
        facts.push({ label: 'Request text', value: 'Hermes did not show it, so the five points were not read' })
      }
    }
    const passed = missing.length === 0
    return {
      passed,
      title: passed ? 'Your job is scheduled' : "Your job isn't ready yet",
      detail: passed
        ? 'Hermes lists a job you made, with a schedule and a request that says what it must.'
        : missing[0].what,
      facts,
      missing,
    }
  },

  /* The three checks below read the live app as one half of a document gate. */

  async routes() {
    const routes = typeof host.profileRoutes === 'function' ? await host.profileRoutes() : []
    const passed = routes.length > 0
    return {
      passed,
      title: passed ? 'The connection route works' : 'No connection route yet',
      detail: passed
        ? 'This window can name the Hermes setup it talks to. That route is what you write down for a client.'
        : 'This window has no connection route. Add a connection in Gateways, then check again.',
      facts: routes.slice(0, 6).map(route => ({
        label: route.profile || 'default',
        value: firstText(route.mode, route.connectionId, route.url) || 'connected',
      })),
    }
  },

  async connections() {
    // tools.list answers { toolsets: [{ name, tool_count, tools: [...] }] }; older builds answered a flat tool list.
    const rows = listOf(await rpc('tools.list'), ['toolsets', 'tools'])
    const grouped = rows.some(row => row && (Array.isArray(row.tools) || typeof row.tool_count === 'number'))
    const toolCount = grouped
      ? rows.reduce((sum, row) => sum + (Array.isArray(row?.tools) ? row.tools.length : Number(row?.tool_count) || 0), 0)
      : rows.length
    // mcp.catalog lists the MCP servers Hermes can add; `installed` marks the ones this profile has.
    let servers = []
    try {
      servers = listOf(await rpc('mcp.catalog'), ['servers'])
    } catch (error) {
      servers = []
    }
    const installed = servers.filter(server => server && server.installed === true)
    const passed = toolCount > 0
    return {
      passed,
      title: passed ? 'Hermes lists its tools' : 'No tools listed',
      detail: passed
        ? 'You can see every tool Hermes can use. That list is what you show a client who asks what it can reach.'
        : 'Hermes lists no tools, so there is nothing to review yet. Check that Hermes is connected, then check again.',
      facts: [
        ...(grouped ? [{ label: 'Toolsets', value: String(rows.length) }] : []),
        { label: 'Tools', value: String(toolCount) },
        { label: 'MCP servers added', value: String(installed.length) },
      ],
    }
  },

  async estate() {
    // One route per profile this window can reach. Hermes's agents.list answers background processes, not
    // agents, and a bot is a profile, so the routes are the honest list of what is set up.
    const routes = typeof host.profileRoutes === 'function' ? await host.profileRoutes() : []
    const names = [...new Set(routes.map(route => firstText(route?.profile) || 'default'))]
    const passed = routes.length > 0
    return {
      passed,
      title: passed ? 'Hermes lists what is set up' : 'Nothing listed yet',
      detail: passed
        ? 'Your profiles are listed, so every part of your map can get a name and an owner.'
        : 'This window lists no profile yet. Check that Hermes is connected, then check again.',
      facts: [
        { label: 'Profiles', value: String(names.length) },
        { label: 'Names', value: names.slice(0, 6).join(', ') || 'none' },
      ],
    }
  },
}

async function runDesktopCheck(step, inputs = {}) {
  const runner = CHECKS[step.check]
  if (!runner) {
    return { passed: false, title: "This check isn't available", detail: 'This version of Hermes has no way to run it.', facts: [], missing: [miss('no_answer', 'This version of Hermes has no way to run this check.')] }
  }
  try {
    return await runner(step, inputs)
  } catch (error) {
    return { passed: false, title: "The check couldn't run", detail: String(error?.message || error), facts: [], missing: [miss('no_answer', String(error?.message || error))] }
  }
}

/* ------------------------------------------------------------------- data -- */

/** Set once in register(). ctx.rest is scoped to /api/plugins/field-academy and
 *  carries the backend's auth; a raw fetch comes back 401. */
let api = null

/** An in-chat offer names a mission. The page may not be mounted when the click
 *  happens, so the request parks here and the page drains it on mount. */
let pendingMission = null
const missionListeners = new Set()

function requestMission(missionId) {
  pendingMission = missionId
  missionListeners.forEach(fn => fn(missionId))
  host.navigate(ROUTE)
}

/** Where the page opens. Always the map, unless an in-chat offer asked for a
 *  specific mission. */
function readView() {
  if (pendingMission) {
    const id = pendingMission
    pendingMission = null
    return { name: 'mission', id }
  }
  return { name: 'map' }
}

function ctxRest(path, options) {
  if (!api) return Promise.reject(new Error('Field Academy is still starting.'))
  return api.rest(path, options || {})
}

/** The passport: polled lightly, kept on screen while it refreshes or if a refresh fails. */
function usePassport() {
  return usePolled({
    key: QUERY_KEY,
    fn: () => ctxRest('/passport'),
    staleTime: 5000,
    options: { refetchOnWindowFocus: true },
  })
}

function refresh() {
  return queryClient.invalidateQueries({ queryKey: QUERY_KEY })
}

/* ------------------------------------------------------------ the Deployer path -- */

const DEPLOYER_KEY = ['field-academy', 'deployer']

/** The Deployer tier's own data, polled lightly like the passport. A backend from before 0.6.0 answers 404, and the page then simply has no Deployer trail. */
function useDeployer() {
  return usePolled({
    key: DEPLOYER_KEY,
    fn: () => ctxRest('/deployer'),
    staleTime: 5000,
    options: { refetchOnWindowFocus: true },
  })
}

function refreshDeployer() {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: DEPLOYER_KEY }),
    queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  ])
}

async function copyText(text, message) {
  if (api?.os?.writeClipboard) await api.os.writeClipboard(text)
  host.notify({ kind: 'success', message: message || 'Copied.' })
}

/** Open a folder in the system's file manager when the app can, and always copy the path, so the button never fails silently. */
async function openFolder(path) {
  if (api?.os?.writeClipboard) await api.os.writeClipboard(path)
  if (api?.os?.openPath) {
    try {
      await api.os.openPath(path)
      return
    } catch (error) {
      // fall through to the address form
    }
  }
  if (api?.os?.openExternal) {
    try {
      await api.os.openExternal(folderUrl(path))
      host.notify({ kind: 'info', message: 'Opening the folder. The path is also copied.' })
      return
    } catch (error) {
      // fall through to the notice
    }
  }
  host.notify({ kind: 'info', message: 'The path is copied. Paste it into your file manager or terminal.' })
}

/**
 * What Hermes shows for one job, read with the same read-only calls the mission checks use: the scheduler list and
 * the chat list. Nothing is written or started. A call that fails is reported in the note, never hidden.
 */
async function readHermes(jobName) {
  let jobs = []
  let sessions = []
  const problems = []
  try {
    jobs = listOf(await rpc('cron.manage', { action: 'list' }), ['jobs'])
  } catch (error) {
    problems.push(`the scheduler list (${String(error?.message || error)})`)
  }
  try {
    sessions = listOf(await rpc('session.list'), ['sessions'])
  } catch (error) {
    problems.push(`the chat list (${String(error?.message || error)})`)
  }
  const found = sampleFromHermes({ jobs, sessions }, jobName)
  if (problems.length) found.note = `${found.note} Could not read ${problems.join(' or ')}.`
  return found
}

let versionTried = false

/** Read the Hermes version once, if Hermes shows it, so the Field Record can show it. A version the page cannot read stays for the learner to type. */
async function syncVersion(deployer) {
  if (versionTried || !deployer || (deployer.hermes_version && deployer.hermes_version.machine_read)) return
  versionTried = true
  try {
    const found = versionFrom(await rpc('setup.runtime_check'))
    if (found) {
      await ctxRest('/deployer/version', { method: 'POST', body: { value: found, source: 'read from Hermes' } })
      await refreshDeployer()
    }
  } catch (error) {
    // The learner can type it instead.
  }
}

function openLink(url) {
  if (api?.os?.openExternal) api.os.openExternal(url)
}

function errorText(error) {
  const raw = String(error?.message || error || '')
  const match = raw.match(/"detail"\s*:\s*"([^"]+)"/)
  return match ? match[1] : raw
}

function shortDate(iso) {
  if (!iso) return ''
  const when = new Date(iso)
  if (Number.isNaN(when.getTime())) return ''
  return when.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function longDate(iso) {
  if (!iso) return ''
  const when = new Date(iso)
  if (Number.isNaN(when.getTime())) return ''
  return when.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
}

function lowerFirst(text) {
  return text ? text.charAt(0).toLowerCase() + text.slice(1) : ''
}

function plural(count, one, many) {
  return `${count} ${count === 1 ? one : many}`
}

function findMission(data, missionId) {
  for (const track of data?.tracks || []) {
    const mission = track.missions.find(item => item.id === missionId)
    if (mission) return { track, mission }
  }
  return { track: null, mission: null }
}

/* ------------------------------------------------------------------ atoms -- */

/** Passport mission status in the trail's words: passed, started, or waiting further up the trail. */
function markStatus(status) {
  if (status === 'verified') return 'passed'
  if (status === 'not_started' || !status) return 'waiting'
  return 'started'
}

function statusWords(mission) {
  if (mission.status === 'verified') {
    const when = mission.passed_at ? `Passed ${shortDate(mission.passed_at)}` : 'Passed'
    return typeof mission.strength === 'number' ? `${when} · ${strengthWord(mission.strength)}` : when
  }
  if (mission.status === 'not_started') return 'Not started'
  return `Started · ${mission.completed_steps} of ${mission.total_steps} steps`
}

/** The line every Field Record carries. The backend sends the same words (pathways.DISCLAIMER); this is the fallback. */
const RECORD_DISCLAIMER = 'Self-issued with Field Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research.'

function certificateWords(certificate) {
  if (certificate.status === 'issued') return `Field Record created ${shortDate(certificate.issued?.issued_at)}`
  if (certificate.status === 'ready') return 'Field Record ready to create'
  return `Field Record: ${plural(certificate.remaining, 'mission', 'missions')} to go`
}

function CertificatePill({ certificate }) {
  const tone = certificate.status === 'issued' ? 'good' : certificate.status === 'ready' ? 'warn' : 'idle'
  return jsx(Pill, { tone, icon: certificate.status === 'issued' ? 'pass-filled' : 'mortar-board', children: certificateWords(certificate) })
}

/** Progress toward a path's Field Record: the bezel, one tick per mission. */
function CertificateBezel({ track, size = 64 }) {
  const total = (track.missions || []).length
  return jsx(Bezel, { passed: track.verified_missions || 0, total, size, children: [
    jsx('span', { className: 'fa-num fa-num-m', children: track.verified_missions || 0 }, 'n'),
    jsx('span', { className: 'fa-sc', style: { fontSize: 11 }, children: `of ${total}` }, 'of'),
  ] })
}

const LINK_ICON = { video: 'play-circle', docs: 'book', guide: 'compass', article: 'note', course: 'mortar-board' }

function LinkButton({ link }) {
  return jsxs('button', { type: 'button', className: 'fa-link', onClick: () => openLink(link.url), children: [
    jsx(Codicon, { name: LINK_ICON[link.kind] || 'link-external', size: 14 }),
    jsxs('span', { className: 'hk-grow', children: [
      jsx('span', { className: 'fa-link-title', children: link.part && link.kind === 'video' ? `${link.title} (${link.part})` : link.title }),
      jsx('span', { className: 'fa-link-credit', children: link.credit }),
    ] }),
    jsx(Codicon, { name: 'link-external', size: 12 }),
  ] })
}

/** The first four links show; the rest fold away so a lesson stays one screen. */
function LinkList({ links }) {
  if (!links || !links.length) return null
  const shown = links.slice(0, 4)
  const more = links.slice(4)
  return jsxs('div', { className: 'hk-stack', children: [
    jsx('div', { className: 'fa-links', children: shown.map(link => jsx(LinkButton, { link }, `${link.url}-${link.title}`)) }),
    more.length
      ? jsx(Details, { label: `${more.length} more to read or watch`, children:
          jsx('div', { className: 'fa-links', children: more.map(link => jsx(LinkButton, { link }, `${link.url}-${link.title}`)) }) })
      : null,
  ] })
}

function Result({ result }) {
  if (!result) return null
  const tone = result.error ? 'bad' : result.passed ? 'good' : 'warn'
  return jsx(Card, { tone, tint: true, className: result.passed ? 'hk-enter hk-pulse' : 'hk-enter', role: 'status', 'aria-live': 'polite', children: [
    jsxs('div', { className: 'hk-row', key: 'h', children: [
      jsx(Codicon, { name: result.error ? 'error' : result.passed ? 'pass-filled' : 'warning', size: 15, style: { color: 'var(--hk-tone)' } }),
      jsx('strong', { children: result.title }),
    ] }),
    result.detail ? jsx(Prose, { text: result.detail }, 'd') : null,
    result.facts && result.facts.length ? jsx(Facts, { rows: result.facts.map(f => ({ label: f.label, value: String(f.value) })) }, 'f') : null,
  ] })
}

/** "Missing point: x" sits under the label "What was missing", so the prefix is dropped there. */
function missingWords(what) {
  const text = String(what || '').replace(/^Missing point:\s*/, '')
  return text ? text[0].toUpperCase() + text.slice(1) : text
}

/** What to do after a miss: exactly what was missing, one hint, and on the second miss a worked example. */
function Feedback({ feedback }) {
  if (!feedback || !(feedback.missing || []).length) return null
  const first = feedback.misses <= 1
  return jsx(Card, { tone: 'warn', tint: true, className: 'hk-enter', role: 'status', 'aria-live': 'polite', children: jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
    jsxs('div', { className: 'hk-row', children: [jsx(Codicon, { name: 'lightbulb', size: 15, style: { color: 'var(--hk-tone)' } }), jsx('strong', { children: feedback.headline })] }),
    jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
      jsx(Label, { plain: true, children: 'What was missing' }),
      jsx('ul', { className: 'fa-bullets', children: feedback.missing.slice(0, 4).map(item => jsx('li', { children: missingWords(item.what) }, `${item.id}-${item.what}`)) }),
      feedback.missing.length > 4 ? jsx('p', { className: 'hk-small', children: `${feedback.missing.length - 4} more after these. Fix the first one and check again.` }) : null,
    ] }),
    feedback.hint ? jsxs('div', { className: 'fa-hint', children: [jsx(Label, { plain: true, children: 'One hint' }), jsx(Prose, { text: feedback.hint })] }) : null,
    feedback.example ? jsxs('div', { className: 'fa-hint', children: [jsx(Label, { plain: true, children: 'A worked example' }), jsx(Prose, { text: withoutExampleWord(feedback.example) })] }) : null,
    jsx('p', { className: 'hk-small', children: first
      ? 'Fix the first item, then try again. You can retry as many times as you like.'
      : 'Use the example as a model for the first item, then try again. Another miss shows the same help.' }),
  ] }) })
}

/** A small-caps label in the trail colour. */
function Label({ children, plain = false }) {
  return jsx('span', { className: plain ? 'fa-sc' : 'fa-sc fa-sc-blaze', children })
}

/* --------------------------------------------------------------- frame -- */

/** The page frame: kit tokens, Esc goes up a level (or leaves a text field first). */
function Frame({ children, up, width = 'wide', onKey }) {
  const root = useRef(null)
  useFocusOnMount(root)
  const keys = useKeys({ Escape: e => { if (isTyping(e)) { e.target.blur(); return } if (up) up() } })
  return jsx(KitPage, { rootRef: root, width, className: 'fa-page', label: 'Field Academy', onKeyDown: e => { if (onKey) onKey(e); keys(e) }, children })
}

/** Scroll one of this page's own sections into view, gently unless motion is reduced. */
function scrollToId(id) {
  const target = typeof document !== 'undefined' ? document.getElementById(id) : null
  if (!target) return
  const reduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  target.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' })
}

const deployerViews = createDeployerViews({
  Prose, withoutExampleWord, Frame, Label, Result, Feedback, ctxRest, errorText, shortDate, longDate, plural, sendToHermes, refreshDeployer, openFolder, copyText, readHermes, scrollToId,
})

/* -------------------------------------------------------------------- map -- */

/** The learner's own goal: asked once, shown on the map, changed any time. */
function GoalCard({ data }) {
  const goal = data.goal || { text: '', asked: false }
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(goal.text || '')
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')

  const save = async skipped => {
    if (busy) return
    if (!skipped && text.trim().length < 8) {
      setProblem('Write a few words about what you want Hermes to do for you.')
      return
    }
    setBusy(true)
    setProblem('')
    try {
      await ctxRest('/use', { method: 'POST', body: skipped ? { skipped: true } : { text: text.trim() } })
      await refresh()
      setEditing(false)
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy(false)
    }
  }

  if (goal.asked && !editing) {
    return jsxs('div', { className: 'fa-goal', children: [
      jsx(Label, { children: 'Your goal' }),
      goal.text
        ? jsx('span', { children: `“${goal.text}”` })
        : jsx('span', { children: 'You skipped this question. Missions use general examples.' }),
      jsx('button', { type: 'button', className: 'hk-link', onClick: () => { setText(goal.text || ''); setEditing(true) }, children: goal.text ? 'Change it' : 'Add a goal' }),
    ] })
  }
  return jsx(Card, { tone: 'info', tint: !goal.asked, className: 'hk-enter', children: jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
    jsx(Label, { children: goal.asked ? 'Your goal' : 'Before you start' }),
    jsx('h2', { className: 'hk-h2', children: 'What do you want Hermes to do for you?' }),
    jsx('p', { children: 'One or two sentences about your own work. Your answer becomes the example in every practice prompt and mission. You can change it any time, or skip it.' }),
    jsx(Textarea, {
      style: { minHeight: '4.5rem', width: '100%' },
      value: text,
      onChange: event => setText(event.target.value),
      placeholder: 'For example: write my weekly status email from my project notes.',
      'aria-label': 'What you want Hermes to do for you',
      ...submitOnModEnter(() => save(false)),
    }),
    problem ? jsx(Result, { result: { passed: false, title: problem } }) : null,
    jsxs('div', { className: 'hk-actions', children: [
      jsx(Button, { loading: busy, onClick: () => save(false), children: 'Save my goal' }),
      goal.asked
        ? jsx(Button, { variant: 'secondary', onClick: () => setEditing(false), children: 'Cancel' })
        : jsx(Button, { variant: 'secondary', onClick: () => save(true), children: 'Skip for now' }),
    ] }),
  ] }) })
}

function WherePanel({ info, data }) {
  const { goal, camp } = info
  const started = info.passed > 0 || info.tracks.some(track => track.waypoints.some(w => w.status !== 'waiting'))
  const where = !goal || !started
    ? 'At the trailhead'
    : camp
      ? `${goal.name} path, ${camp.name} camp`
      : goal.summit.status === 'issued' ? `${goal.name} path, at the summit` : `${goal.name} path, below the summit`
  const honest = data.honest || { passed: 0, holding: 0 }
  return jsxs('div', { className: 'fa-panel fa-where hk-enter', children: [
    jsx(Bezel, { passed: info.passed, total: info.total, children: [
      jsx('span', { className: 'fa-num fa-num-xl', children: info.passed }, 'n'),
      jsx('span', { className: 'fa-sc', children: `of ${info.total}` }, 'of'),
    ] }),
    jsxs('div', { className: 'fa-where-lines', children: [
      jsx(Label, { children: 'Where you are' }),
      jsx('h2', { className: 'hk-h1', children: where }),
      jsx('p', { children: `${info.passed} of ${plural(info.total, 'mission', 'missions')} passed${
        info.certificates ? `, and ${plural(info.certificates, 'Field Record', 'Field Records')} in your collection` : ''}.` }),
      honest.passed
        ? jsx('p', { children: `${honest.holding} of ${honest.passed} passed ${honest.passed === 1 ? 'mission' : 'missions'} still ${honest.holding === 1 ? 'holds' : 'hold'} up when Hermes reviews you.` })
        : null,
      jsx('p', { className: 'hk-small', children: 'Go at your own pace. Your progress stays saved on this computer.' }),
    ] }),
  ] })
}

function NextStep({ next, info, go }) {
  if (!next) {
    return jsxs('div', { className: 'fa-panel fa-next hk-enter', children: [
      jsx(Label, { children: 'Next best step' }),
      jsx('h2', { className: 'hk-h2', children: 'Every mission passed' }),
      jsx('p', { children: 'Create a Field Record for each path you finished. Each one waits at the summit of its trail.' }),
    ] })
  }
  const started = info.tracks.some(track => track.waypoints.some(w => w.status !== 'waiting'))
  return jsxs('div', { className: 'fa-panel fa-next hk-enter', children: [
    jsx(Label, { children: started ? 'Next best step' : 'Start here' }),
    jsx('h2', { className: 'hk-h2', children: next.title }),
    jsxs('div', { className: 'fa-next-meta', children: [
      jsxs('span', { children: [jsx(Codicon, { name: 'location', size: 13 }), `${next.track_name} path`] }),
      jsxs('span', { children: [jsx(Codicon, { name: 'milestone', size: 13 }), `${next.level_name} camp`] }),
      jsxs('span', { children: [jsx(Codicon, { name: 'watch', size: 13 }), minutesWords(next.minutes)] }),
    ] }),
    jsx('p', { children: next.reason }),
    next.use_text ? jsx('div', { className: 'fa-use', children: [jsx(Label, { plain: true, children: 'Why this matters to you' }, 'l'), jsx('p', { children: next.use_text }, 'p')] }) : null,
    jsx('div', { className: 'hk-actions', children: jsx(Button, { onClick: () => go({ name: 'mission', id: next.mission_id }), children: started ? 'Continue' : 'Start' }) }),
  ] })
}

/** Review queue: missions you passed that are due to come back, three questions at a time. */
function ReviewQueue({ data, go }) {
  const reviews = data.reviews || { due: [], due_count: 0, strength: {}, passed_missions: 0 }
  const rows = Object.values(reviews.strength || {}).sort((a, b) => String(a.due_at).localeCompare(String(b.due_at)))

  if (!reviews.passed_missions) {
    return jsx(Section, { title: 'Review queue', children: jsxs('div', { className: 'fa-panel', children: [
      jsx('p', { children: 'A mission comes back for review two days after you pass it, then after a week, three weeks and two months. A review is three short questions about missions you passed earlier, scored by your own Hermes. Pass your first mission to start the queue.' }),
    ] }) }, 'review')
  }

  const start = practice => go({ name: 'review', practice })
  const due = reviews.due_count
  // "Due now" must agree with the count above it, so read time from the clock that counted.
  const reviewNow = reviews.now && !Number.isNaN(new Date(reviews.now).getTime()) ? new Date(reviews.now) : new Date()
  return jsx(Section, { title: 'Review queue', count: due, children: jsxs('div', { className: 'fa-panel', children: [
    jsxs('div', { className: 'hk-row', style: { flexWrap: 'wrap', gap: 14, alignItems: 'center' }, children: [
      jsxs('div', { className: 'hk-grow hk-stack', style: { gap: 3 }, children: [
        jsx('strong', { children: due ? `${plural(due, 'mission', 'missions')} due for review` : 'Nothing is due' }),
        jsx('p', { className: 'hk-small', children: due
          ? `A session is three questions, ${minutesWords(reviews.minutes).toLowerCase()}. Hermes scores your answers the way it scores a question in a mission, and weak answers come back sooner.`
          : reviews.next_due_at
            ? `${reviews.next_due_title} comes up ${dueWords(reviews.next_due_at, reviewNow).replace('Due ', '')}. You can practice early, which changes your strength but not your schedule.`
            : 'Nothing is scheduled.' }),
      ] }),
      jsxs('div', { className: 'hk-actions', children: [
        due ? jsx(Button, { onClick: () => start(false), children: 'Start a review' }) : null,
        reviews.can_practice ? jsx(Button, { variant: due ? 'secondary' : 'default', onClick: () => start(true), children: 'Practice early' }) : null,
      ] }),
    ] }),
    reviews.open_session && reviews.open_session.status !== 'graded'
      ? jsx('p', { className: 'hk-small', children: reviews.open_session.status === 'submitted'
          ? 'You have a review waiting for its score. Open a review to see it.'
          : 'You have a review in progress. Start a review to pick it back up.' })
      : null,
    jsx('div', { children: rows.map(row => {
      const found = typeof row.strength === 'number'
      return jsxs('div', { className: 'fa-rev', children: [
        jsx('button', { type: 'button', className: 'hk-link', style: { textAlign: 'left' }, onClick: () => go({ name: 'mission', id: row.mission_id }), children: row.title }),
        jsxs('div', { className: 'hk-stack', style: { gap: 3 }, children: [
          jsx('div', { className: 'fa-meter', role: 'img', 'aria-label': `${row.strength_word}, ${found ? row.strength : 0} out of 100`, children: jsx('span', { style: { width: `${found ? Math.max(4, row.strength) : 0}%` } }) }),
          jsx('span', { className: 'hk-small', children: row.strength_word }),
        ] }),
        jsx('span', { className: 'hk-small fa-rev-due', children: dueWords(row.due_at, reviewNow) }),
      ] }, row.mission_id)
    }) }),
  ] }) }, 'review')
}

/** What changed since you learned this: missions whose content moved on after you passed them. */
function ChangesPanel({ data, go }) {
  const changes = data.changes || []
  const fresh = data.new_missions || []
  const passed = (data.honest || {}).passed
  const [busy, setBusy] = useState('')
  const [problem, setProblem] = useState('')

  if (!changes.length && !fresh.length) {
    if (!passed) return null
    return jsx(Section, { title: 'What changed since you learned this', children: jsx('div', { className: 'fa-panel', children:
      jsx('p', { children: 'Nothing has changed in the missions you passed. When a lesson or a check is updated, it shows up here with a way to re-verify.' }) }) }, 'changes')
  }

  const reverify = async change => {
    setBusy(change.mission_id)
    setProblem('')
    try {
      await ctxRest(`/mission/${change.mission_id}/reverify`, { method: 'POST', body: {} })
      await refresh()
      go({ name: 'mission', id: change.mission_id, focus: 'gate' })
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy('')
    }
  }
  const acknowledge = async change => {
    setBusy(change.mission_id)
    setProblem('')
    try {
      await ctxRest(`/mission/${change.mission_id}/acknowledge`, { method: 'POST', body: {} })
      await refresh()
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy('')
    }
  }

  const title = changes.length ? 'What changed since you learned this' : 'New on paths you started'
  return jsx(Section, { title, count: changes.length + fresh.length, children: jsxs('div', { className: 'hk-stack', children: [
    changes.length ? jsx('p', { className: 'hk-small', children: 'Your passes stay passed. When a check changed after you passed a mission, you can run the new one to re-verify. If it misses, the mission stays passed.' }) : null,
    problem ? jsx(Result, { result: { passed: false, title: problem } }) : null,
    ...changes.map(change => jsx(Card, { children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
      jsxs('div', { className: 'hk-row', style: { flexWrap: 'wrap', gap: 10 }, children: [
        jsxs('div', { className: 'hk-grow', children: [
          jsx('strong', { children: change.title }),
          jsx('div', { className: 'hk-small', children: `${change.track_name} path · ${change.level_name} · you passed version ${change.passed_version}, now version ${change.version}${change.carried_over ? ' · passed before version 0.5' : ''}` }),
        ] }),
        jsx(Pill, { tone: change.needs === 'check' ? 'warn' : 'info', children: change.needs === 'check' ? 'The check changed' : 'The lesson changed' }),
      ] }),
      jsx('ul', { className: 'fa-bullets', children: change.revisions.map(r => jsx('li', { children: r.summary }, r.summary)) }),
      jsxs('div', { className: 'hk-actions', children: [
        change.needs === 'check'
          ? jsx(Button, { loading: busy === change.mission_id, onClick: () => reverify(change), children: 'Re-verify' })
          : jsx(Button, { loading: busy === change.mission_id, onClick: () => acknowledge(change), children: "I've read the changes" }),
        jsx(Button, { variant: 'secondary', onClick: () => go({ name: 'mission', id: change.mission_id }), children: 'Open the mission' }),
      ] }),
    ] }) }, change.mission_id)),
    ...fresh.map(item => jsx(Card, { tone: 'info', children: jsxs('div', { className: 'hk-row', style: { flexWrap: 'wrap', gap: 10 }, children: [
      jsxs('div', { className: 'hk-grow hk-stack', style: { gap: 2 }, children: [
        jsx('strong', { children: `New: ${item.title}` }),
        jsx('div', { className: 'hk-small', children: `${item.track_name} path · ${item.level_name}` }),
        jsx('p', { children: item.summary }),
      ] }),
      jsx(Button, { variant: 'secondary', onClick: () => go({ name: 'mission', id: item.mission_id }), children: 'Open it' }),
    ] }) }, item.mission_id)),
  ] }) }, 'changes')
}

const MAP_SHAPE = [{ title: true, lines: 2, button: true, dot: true }, { title: true, lines: 6 }]

function DeployerTrailPanel({ deployer, list, offset, go }) {
  const model = trailModel(deployer.track)
  const mine = { index: list.index - offset, itemProps: i => list.itemProps(i + offset) }
  return jsx(Section, { title: `${deployer.track.name} path`, children: jsxs('div', { className: 'hk-stack', children: [
    jsx(Prose, { text: 'Set up, deploy and run Hermes for a small client. You do the real work:\n- Repair four broken client setups\n- Write a proposal\n- Answer nine hard cases\n- Run a real service for several days, then break it and recover it' }),
    jsx('p', { className: 'hk-small', children: 'The Guide Field Record needs a reviewer you choose to read and sign your evidence. Until someone signs, the path ends at Guide, awaiting review.' }),
    jsx(TrailMap, {
      models: [model], list: mine,
      onOpenTrack: () => go({ name: 'path', id: 'deployer' }),
      onOpenMission: id => go(partFor(id)),
      foot: [jsx('span', { className: 'hk-small', key: 'tip' }, deployer.certificate.label)],
    }),
    jsx('p', { className: 'hk-small', children: 'It records competence shown in labs and on your own setup. It is not years of client work.' }),
    jsx('p', { className: 'hk-small', children: deployer.about?.disclaimer || '' }),
  ] }) }, 'deployer')
}

/** The banner's camp flags: one per path, in map order, filled once its Field Record is created. */
function bannerCamps(info, deployer) {
  const camps = info.tracks.map(track => ({ label: track.name, done: track.summit.status === 'issued' }))
  if (deployer && deployer.track) camps.push({ label: deployer.track.name, done: deployer.certificate?.status === 'issued' })
  return camps.slice(0, 5)
}

/** The banner's facts line, counted from the passport so it can never drift from the map. */
function bannerFacts(info, deployer) {
  const paths = info.tracks.length + (deployer && deployer.track ? 1 : 0)
  return [plural(info.total, 'mission', 'missions'), plural(paths, 'path', 'paths'), 'Checks on real work', 'Stays on your computer']
}

function MapView({ data, go, deployer }) {
  const info = overview(data)
  const camps = bannerCamps(info, deployer)
  const models = info.tracks
  const extra = deployer && deployer.track ? 1 : 0
  const list = useListKeys({
    count: models.length + extra,
    onOpen: i => (models[i] ? go({ name: 'path', id: models[i].id }) : extra && go({ name: 'path', id: 'deployer' })),
  })
  return jsx(Frame, { onKey: list.keyProps.onKeyDown, children: [
    jsx(Banner, {
      eyebrow: 'A field guide to Hermes',
      promise: 'Learn Hermes by doing real work on your own setup, one camp at a time, and keep a Field Record of everything you prove',
      facts: bannerFacts(info, deployer),
      camps,
      summitDone: camps.length > 0 && camps.every(camp => camp.done),
    }, 'head'),
    jsx('p', { className: 'hk-lead', children: `${plural(models.length + extra, 'path', 'paths')} up the mountain, each named for one of Hermes's old jobs. Every path climbs from Beginner to Advanced, then a capstone on your own problem, and ends at the summit with a Field Record of the work you did.` }, 'lead'),
    jsx(GoalCard, { data }, 'goal'),
    jsxs('div', { className: 'fa-here', children: [
      jsx(WherePanel, { info, data }, 'where'),
      jsx(NextStep, { next: data.next_up, info, go }, 'next'),
    ] }, 'here'),
    jsx(ReviewQueue, { data, go }, 'review'),
    jsx(ChangesPanel, { data, go }, 'changes'),
    jsx(Section, { title: 'Trail map', count: models.length + extra, actions: jsx(KeyHint, { keys: ['J', 'K'], label: 'to move between trails, Enter to open' }),
      children: jsx(TrailMap, {
        models, list,
        onOpenTrack: id => go({ name: 'path', id }),
        onOpenMission: id => go({ name: 'mission', id }),
        foot: [jsx(Legend, {}, 'legend'), jsx('span', { className: 'hk-small', children: 'Click a trail, a waypoint or a flag to open it.' }, 'tip')],
      }) }, 'map'),
    extra ? jsx(DeployerTrailPanel, { deployer, list, offset: models.length, go }, 'deployer') : null,
    jsxs(Section, { title: 'How the trail works', children: [
      jsxs('ol', { className: 'fa-numbered', children: [
        jsx('li', { children: jsx('span', { children: 'Pick a trail and open its first mission. Each mission shows how long it takes before you start.' }) }),
        jsx('li', { children: jsx('span', { children: 'Read a short lesson, then see a finished example, then fill the gaps in a half-finished one. The help fades, and then you do it on your own.' }) }),
        jsx('li', { children: jsx('span', { children: 'Try it in your own Hermes, answer one question in your own words, and click Check my work. Each check reads something you made.' }) }),
        jsx('li', { children: jsx('span', { children: 'When you miss, you see exactly what was missing, then a hint, then a worked example. You can retry as often as you like.' }) }),
        jsx('li', { children: jsx('span', { children: 'Pass every mission and the capstone on a trail to reach its summit and create your Field Record for that path. Already know a level? Take the placement check on the path.' }) }),
      ] }),
      jsx('p', { className: 'hk-small', children: data.credential_note }),
    ] }, 'how'),
  ] })
}

/* ------------------------------------------------------------------- path -- */

function Camp({ rung, track, go, rows, list }) {
  const missions = rung.missions.map(id => track.missions.find(m => m.id === id)).filter(Boolean)
  return jsxs('div', { className: 'fa-camp', 'data-status': rung.status, 'data-current': rung.current ? '' : undefined, children: [
    jsxs('div', { className: 'fa-camp-rail', children: [
      jsx('span', { className: 'fa-num fa-num-l', 'aria-hidden': 'true', children: rung.number }),
      jsx(CampLine, { walked: rung.status === 'passed' }),
    ] }),
    jsxs('div', { className: 'fa-camp-body', children: [
      jsxs('div', { className: 'fa-camp-head', children: [
        jsxs('div', { className: 'hk-grow', style: { display: 'grid', gap: 2 }, children: [
          jsx(Label, { children: `Camp ${rung.number}` }),
          jsx('h3', { className: 'hk-h2', children: rung.name }),
        ] }),
        rung.current
          ? jsxs('span', { className: 'fa-here-tag', children: [jsx(TrailMark, { here: true, size: 14 }), 'You are here'] })
          : rung.status === 'passed'
            ? jsx(Pill, { tone: 'good', icon: 'check', children: 'Passed' })
            : jsx('span', { className: 'hk-small', children: `${rung.passed} of ${rung.total} passed` }),
      ] }),
      jsx('p', { children: rung.meaning }),
      jsx('div', { className: 'fa-camp-rows', children: missions.map(mission => {
        const i = rows.indexOf(mission.id)
        const here = mission.id === track.here
        return jsxs('button', {
          type: 'button',
          className: 'hk-rowbtn',
          onClick: () => go({ name: 'mission', id: mission.id }),
          ...list.itemProps(i),
          children: [
            jsx(TrailMark, { status: markStatus(mission.status), here }),
            jsxs('span', { className: 'hk-grow', children: [
              jsx('span', { style: { display: 'block', fontWeight: 600 }, children: mission.title }),
              jsx('span', { className: 'fa-row-meta', children: `${minutesWords(mission.minutes)} · ${statusWords(mission)}` }),
            ] }),
            here ? jsx('span', { className: 'fa-here-tag', children: 'Next' }) : null,
            jsx(Codicon, { name: 'chevron-right', size: 13 }),
          ],
        }, mission.id)
      }) }),
    ] }),
  ] })
}

function SummitRow({ track }) {
  const status = track.certificate.status
  return jsxs('div', { className: 'fa-camp', 'data-status': status === 'issued' ? 'passed' : undefined, children: [
    jsx('div', { className: 'fa-camp-rail', children: jsx('svg', { width: 26, height: 30, viewBox: '-9 -28 26 32', 'aria-hidden': 'true', children:
      jsxs('g', { className: 'fa-flag', 'data-status': status, children: [
        jsx('path', { className: 'fa-flag-cairn', d: 'M-8 4 L-4 -1 L4 -1 L8 4 Z' }),
        jsx('line', { className: 'fa-flag-pole', x1: 0, y1: 0, x2: 0, y2: -26 }),
        jsx('path', { className: 'fa-flag-cloth', d: 'M0 -26 L16 -21 L0 -15 Z' }),
      ] }) }) }),
    jsxs('div', { className: 'fa-camp-body', children: [
      jsxs('div', { className: 'fa-camp-head', children: [
        jsxs('div', { className: 'hk-grow', style: { display: 'grid', gap: 2 }, children: [
          jsx(Label, { children: 'Summit' }),
          jsx('h3', { className: 'hk-h2', children: track.certificate.title || 'Your Field Record' }),
        ] }),
        jsx(CertificatePill, { certificate: track.certificate }),
      ] }),
      jsx('div', { children: jsx('button', { type: 'button', className: 'hk-link', onClick: () => scrollToId(`fa-route-${track.id}`), children: 'See the route to your Field Record' }) }),
    ] }),
  ] })
}

function CertificateRoute({ track, go }) {
  const route = track.certificate
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')

  const claim = async () => {
    if (!name.trim()) {
      setProblem('Type the name you want on your Field Record.')
      return
    }
    setBusy(true)
    setProblem('')
    try {
      await ctxRest(`/certificate/${track.id}`, { method: 'POST', body: { name: name.trim() } })
      await refresh()
      go({ name: 'certificate', id: track.id })
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy(false)
    }
  }

  return jsx(Section, { id: `fa-route-${track.id}`, title: 'Your route to the Field Record', actions: jsx(CertificatePill, { certificate: route }), children: jsxs('div', { className: 'hk-stack', style: { gap: 10 }, children: [
    jsx('div', { className: 'fa-panel', children: jsxs('div', { className: 'hk-row', style: { flexWrap: 'nowrap', gap: 16 }, children: [
      jsx(CertificateBezel, { track, size: 72 }),
      jsxs('div', { className: 'hk-grow hk-stack', style: { gap: 3 }, children: [
        jsx(Label, { children: 'Summit' }),
        jsx('strong', { children: route.status === 'issued' ? 'Field Record created' : route.status === 'ready' ? 'Every mission passed' : `${plural(route.remaining, 'mission', 'missions')} to go` }),
        jsx('p', { className: 'hk-small', children: `${track.verified_missions} of ${track.missions.length} missions on this trail passed.` }),
      ] }),
      route.status === 'issued'
        ? jsx(Button, { onClick: () => go({ name: 'certificate', id: track.id }), children: 'View your Field Record' })
        : route.status !== 'ready' && track.here
          ? jsx(Button, { onClick: () => go({ name: 'mission', id: track.here }), children: 'Go to your next mission' })
          : null,
    ] }) }),
    route.status === 'ready'
      ? jsxs(Card, { tone: 'warn', tint: true, className: 'hk-enter', children: [
          jsx('h3', { className: 'hk-h2', children: 'Create your Field Record' }, 'h'),
          jsx('p', { children: 'Every mission on this path passed. Type your name the way you want it on your record. Field Academy writes the record on your computer, and it stays yours.' }, 'p'),
          jsxs('div', { className: 'hk-actions', key: 'a', children: [
            jsx('div', { style: { minWidth: '16rem', flex: 1 }, children: jsx(Input, { value: name, onChange: event => setName(event.target.value), placeholder: 'Your name', 'aria-label': 'Name on the Field Record',
              onKeyDown: e => { if (e.key === 'Enter' && !e.nativeEvent?.isComposing) claim() } }) }),
            jsx(Button, { loading: busy, onClick: claim, children: 'Create your Field Record' }),
          ] }),
          problem ? jsx(Result, { result: { passed: false, title: problem } }, 'r') : null,
        ] })
      : null,
    jsxs(Card, { children: [
      jsx('h3', { className: 'hk-h3', children: 'What to do' }, 'h'),
      jsx('ol', { className: 'fa-numbered', children: route.steps.map(step =>
        jsx('li', { children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [jsx('strong', { children: step.title }), jsx(Prose, { text: step.detail })] }) }, step.title)
      ) }, 'l'),
    ] }),
    jsxs(Card, { children: [
      jsx('h3', { className: 'hk-h3', children: 'The proof each mission needs' }, 'h'),
      jsx('p', { className: 'hk-small', children: `Every mission also needs ${lowerFirst(route.proof[0]?.explain || '')}` }, 'p'),
      jsx('div', { className: 'hk-stack', children: route.proof.map(row =>
        jsxs('div', { className: 'hk-row', style: { flexWrap: 'nowrap', alignItems: 'flex-start' }, children: [
          jsx('span', { style: { paddingTop: 2 }, children: jsx(TrailMark, { status: row.passed ? 'passed' : 'waiting' }) }),
          jsxs('div', { className: 'hk-grow', children: [
            jsx('p', { children: jsx('strong', { children: `${row.level_name}: ${row.title}` }) }),
            jsx('p', { className: 'hk-small', children: row.passed ? `${row.check} Passed ${shortDate(row.passed_at)}.` : row.check }),
          ] }),
        ] }, row.mission_id)
      ) }, 'l'),
    ] }),
    jsxs(Card, { children: [
      jsx('h3', { className: 'hk-h3', children: 'What you receive' }, 'h'),
      jsx('ul', { className: 'fa-bullets', children: route.receive.map(line => jsx('li', { children: line }, line)) }, 'l'),
      jsx('p', { className: 'hk-small', children: `${route.shows} ${route.issuer}` }, 'p'),
      jsx('p', { className: 'hk-small', children: route.disclaimer }, 'd'),
    ] }),
  ] }) })
}

/** The placement check: a short test that lets you skip the reading on levels you already know. */
function PlacementPanel({ track, go }) {
  const placement = track.placement || { available: false }
  if (!placement.available) return null
  const taken = placement.taken
  const levels = taken?.results?.levels || {}
  const known = Object.keys(levels).filter(level => levels[level].known)
  const applied = taken?.applied
  return jsx(Section, { title: 'Placement check', children: jsx('div', { className: 'fa-panel', children: jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
    jsx(Prose, { text: placement.intro }),
    taken
      ? jsx('p', { className: 'hk-small', children: known.length
          ? `You took it ${shortDate(taken.taken_at)} and knew ${known.length === 1 ? 'one level' : `${known.length} levels`}. ${applied ? `The reading and practice on ${applied.levels.join(', ')} missions are skipped. Each question and each check still counts.` : 'You have not applied it yet.'}`
          : `You took it ${shortDate(taken.taken_at)}. No level was known yet, so every mission starts with its lesson.` })
      : jsx('p', { className: 'hk-small', children: `${placement.questions} questions, about ${placement.minutes} minutes.` }),
    jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: taken ? 'secondary' : 'default', onClick: () => go({ name: 'placement', id: track.id }), children: taken ? 'Open the placement check' : 'Take the placement check' }) }),
  ] }) }) }, 'placement')
}

function PathView({ track, go }) {
  const model = trailModel(track)
  const rung = track.levels.find(item => item.current)
  const rows = track.levels.flatMap(level => level.missions.filter(id => track.missions.some(m => m.id === id)))
  const list = useListKeys({ count: rows.length, onOpen: i => rows[i] && go({ name: 'mission', id: rows[i] }) })
  return jsx(Frame, { width: 'narrow', up: () => go({ name: 'map' }), onKey: list.keyProps.onKeyDown, children: [
    jsx(PageHeader, {
      back: jsx(Back, { label: 'Trail map', onClick: () => go({ name: 'map' }) }),
      eyebrow: jsx(Label, { children: track.eyebrow }), title: `${track.name} path`, lead: track.promise,
    }, 'head'),
    track.lore ? jsx('p', { className: 'fa-lore', children: track.lore }, 'lore') : null,
    jsx(ElevationProfile, {
      model,
      onOpenMission: id => go({ name: 'mission', id }),
      onOpenSummit: () => scrollToId(`fa-route-${track.id}`),
      children: [
        jsx('p', { children: rung
          ? `You're at Camp ${rung.number}, ${rung.name}. ${track.verified_missions} of ${track.missions.length} missions passed.`
          : 'Every mission on this path passed. The summit is yours.' }, 'where'),
        jsx(Legend, {}, 'legend'),
      ],
    }, 'profile'),
    jsx(PlacementPanel, { track, go }, 'placement'),
    jsx(Section, { title: 'Camps on this trail', actions: jsx(KeyHint, { keys: ['J', 'K'], label: 'to move, Enter to open' }), children:
      jsxs('div', { className: 'fa-camps', children: [
        ...track.levels.map(item => jsx(Camp, { rung: item, track, go, rows, list }, item.id)),
        jsx(SummitRow, { track }, 'summit'),
      ] }) }, 'levels'),
    jsx(CertificateRoute, { track, go }, 'route'),
  ] })
}

/* --------------------------------------------------------------- mission -- */

const KIND = {
  lesson: { label: 'Read', short: 'Read', icon: 'book' },
  example: { label: 'See it done', short: 'See it', icon: 'eye' },
  complete: { label: 'Your turn', short: 'Finish', icon: 'edit' },
  lab: { label: 'Try it', short: 'Try it', icon: 'beaker' },
  explain: { label: 'Explain it', short: 'Explain', icon: 'comment-discussion' },
  gate: { label: 'Prove it', short: 'Prove it', icon: 'verified-filled' },
}

/** A story-first mission opens with what happened to someone, and the lesson follows as its takeaway. */
const STORY_KIND = {
  example: { label: 'The story', short: 'Story', icon: 'eye' },
  lesson: { label: 'The takeaway', short: 'Idea', icon: 'lightbulb' },
}

function kindOf(mission, step) {
  return (mission.story_first && STORY_KIND[step.kind]) || KIND[step.kind] || KIND.lesson
}

async function setStep(mission, step, status, onChanged) {
  await ctxRest(`/mission/${mission.id}/step/${step.id}`, { method: 'POST', body: { status } })
  await refresh()
  onChanged()
}

/**
 * Opens a fresh chat and sends `text` in it, the way a learner would by typing it. The composer for a
 * new chat mounts a moment after the route changes, so this waits for it. If this Hermes has no
 * composer for plugins, the text goes on the clipboard and the learner pastes it.
 */
async function sendInNewChat(text, fallbackMessage) {
  host.newChat()
  const composer = host.composer
  if (composer?.submit) {
    for (let tries = 0; tries < 24; tries++) {
      await new Promise(resolve => setTimeout(resolve, 125))
      try {
        if (composer.submit('new', text)) return true
      } catch { break }
    }
  }
  if (api?.os?.writeClipboard) await api.os.writeClipboard(text)
  host.notify({ kind: 'info', message: fallbackMessage })
  return false
}

async function startPracticeChat(prompt) {
  await sendInNewChat(prompt, 'A new chat is open and the practice prompt is copied. Paste it and press Enter.')
}

function LessonStep({ mission, step, onChanged }) {
  const done = step.status === 'done'
  return jsxs('div', { className: 'hk-stack', children: [
    step.picture ? jsx(Picture, { id: step.picture }) : null,
    step.lines?.length
      ? jsx('ul', { className: 'fa-takeaway', children: step.lines.map(line => jsx('li', { children: line }, line)) })
      : null,
    jsx('div', { className: 'hk-actions', children: jsx(Button, {
      variant: done ? 'secondary' : 'default',
      onClick: () => setStep(mission, step, done ? 'ready' : 'done', onChanged),
      children: done ? 'Mark as not done' : 'Got it',
    }) }),
  ] })
}

/** Optional reading and video for a mission, out of the way at the end. Passing never needs them. */
function GoDeeper({ mission }) {
  const links = mission.watch || []
  if (!links.length) return null
  return jsx('div', { className: 'fa-deeper', children: jsx(Details, { label: `Go deeper: ${plural(links.length, 'guide or video', 'guides and videos')} from the Hermes community`, children:
    jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
      jsx('p', { className: 'hk-small', children: 'Optional. Everything you need to pass is on this page.' }),
      jsx(LinkList, { links }),
    ] }) }) })
}

/** Small labelled diagrams for a takeaway. Inline SVG, drawn in the page's own ink. */
function Picture({ id }) {
  if (id === 'four-parts') return jsx(FourParts, {})
  return null
}

function FourParts() {
  const box = (x, y, w, h, title, line, tone) => jsxs('g', { className: 'fa-pic-box', 'data-tone': tone || undefined, children: [
    jsx('rect', { x, y, width: w, height: h, rx: 8 }),
    jsx('text', { className: 'fa-pic-title', x: x + 14, y: y + 24, children: title }),
    jsx('text', { className: 'fa-pic-line', x: x + 14, y: y + 44, children: line }),
  ] })
  return jsxs('figure', { className: 'fa-pic', children: [
    jsxs('svg', { viewBox: '0 0 640 236', role: 'img', 'aria-label': 'The app and its sessions sit on top. Below, one computer holds a profile, and inside the profile the gateway runs scheduled jobs and answers your phone, even with the app closed.', children: [
      box(16, 14, 290, 60, 'The app', 'The window you type in. Close it any time.'),
      box(334, 14, 290, 60, 'A session', 'One conversation. Saved, comes back later.'),
      jsxs('g', { className: 'fa-pic-frame', children: [
        jsx('rect', { x: 16, y: 96, width: 608, height: 126, rx: 10 }),
        jsx('text', { className: 'fa-pic-cap', x: 30, y: 116, children: 'One computer' }),
      ] }),
      box(32, 128, 270, 80, 'A profile', 'Its own memory, skills and keys.'),
      box(330, 128, 278, 80, 'The gateway', 'Runs jobs, answers your phone.', 'blaze'),
      jsx('text', { className: 'fa-pic-line', x: 344, y: 196, children: 'Keeps going when the app is closed.' }),
      jsx('path', { className: 'fa-pic-link', d: 'M302 168 L330 168' }),
      jsx('path', { className: 'fa-pic-link', d: 'M160 74 L160 128' }),
    ] }),
  ] })
}

/** A finished worked example, read in full. The first rung of fading support. */
function ExampleStep({ mission, step, onChanged }) {
  const done = step.status === 'done'
  const gate = (mission.steps || []).find(item => item.kind === 'gate')
  return jsxs('div', { className: 'hk-stack', children: [
    jsx('ol', { className: 'fa-parts', children: (step.parts || []).map(part => jsxs('li', { className: 'fa-part', children: [
      jsx('span', { className: 'fa-sc fa-sc-blaze', children: part.label }),
      jsx('span', { children: part.text }),
    ] }, part.label)) }),
    step.document
      ? jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
          jsx(Label, { plain: true, children: `A finished ${gate?.check || 'document'}` }),
          jsx('pre', { className: 'fa-doc', children: step.document }),
        ] })
      : null,
    jsx('div', { className: 'hk-actions', children: jsx(Button, {
      variant: done ? 'secondary' : 'default',
      onClick: () => setStep(mission, step, done ? 'ready' : 'done', onChanged),
      children: done ? 'Mark as not done' : 'Got it',
    }) }),
  ] })
}

/** A half-finished example with gaps. The learner writes first and sees the model answer second. */
function CompleteStep({ mission, step, onChanged }) {
  const saved = step.saved || { answers: {}, revealed: false, model: null }
  const [answers, setAnswers] = useState(saved.answers || {})
  const [busy, setBusy] = useState(false)
  const [reply, setReply] = useState(null)
  const [problem, setProblem] = useState('')
  const model = reply?.model || (saved.revealed ? saved.model : null)
  const problems = reply && !reply.ok ? reply.problems || [] : []
  const byGap = Object.fromEntries(problems.map(item => [item.id, item.what]))
  const done = step.status === 'done'

  const send = async showAnyway => {
    if (busy) return
    setBusy(true)
    setProblem('')
    try {
      const payload = await ctxRest(`/complete/${mission.id}/${step.id}`, { method: 'POST', body: { answers, show_anyway: showAnyway } })
      setReply(payload)
      if (payload.ok) {
        await refresh()
        onChanged()
      }
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy(false)
    }
  }

  return jsxs('div', { className: 'hk-stack', children: [
    jsx('div', { className: 'fa-partial', children: (step.parts || []).map((part, index) => part.gap
      ? jsxs('div', { className: 'fa-gap', 'data-problem': byGap[part.gap] ? '' : undefined, children: [
          jsx('label', { htmlFor: `fa-gap-${mission.id}-${part.gap}`, children: part.prompt }),
          jsx(Textarea, {
            id: `fa-gap-${mission.id}-${part.gap}`,
            style: { minHeight: '4.5rem', width: '100%' },
            value: answers[part.gap] || '',
            onChange: event => setAnswers({ ...answers, [part.gap]: event.target.value }),
            placeholder: 'Write your own answer here.',
            'aria-label': part.prompt,
          }),
          byGap[part.gap] ? jsx('p', { role: 'status', children: byGap[part.gap] }) : null,
        ] }, part.gap)
      : /(^|\n)#{1,3} /.test(part.text)
        ? jsx('pre', { className: 'fa-doc', children: part.text.replace(/^\n+|\n+$/g, '') }, `t${index}`)
        // The gap's own question follows, so a trailing "Where it goes:" cue line would say it twice.
        : jsx(Prose, { text: part.text.replace(/\n?[^\n:]{1,40}:\s*$/, '') }, `t${index}`)) }),
    problem ? jsx(Result, { result: { passed: false, title: problem } }) : null,
    problems.length
      ? jsx(Result, { result: { passed: false, title: 'A few gaps need more', detail: 'Add to the gaps marked above, then compare again.' } })
      : null,
    jsxs('div', { className: 'hk-actions', children: [
      jsx(Button, { loading: busy, onClick: () => send(false), children: model ? 'Compare again' : 'Compare with the model answers' }),
      reply && !reply.ok && reply.can_show && !model
        ? jsx(Button, { variant: 'secondary', onClick: () => send(true), children: 'Show the answers anyway' })
        : null,
      done ? jsx('span', { className: 'hk-small', children: 'Done' }) : null,
    ] }),
    model
      ? jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
          jsx(Label, { children: 'Your answers beside the model answers' }),
          ...(step.parts || []).filter(part => part.gap).map(part => jsxs('div', { className: 'fa-compare', children: [
            jsxs('div', { children: [jsx(Label, { plain: true, children: 'Yours' }), jsx('p', { className: 'fa-wrap', children: (answers[part.gap] || saved.answers?.[part.gap] || '').trim() || 'Left empty' })] }),
            jsxs('div', { children: [jsx(Label, { plain: true, children: 'Model answer' }), jsx(Prose, { text: model[part.gap] })] }),
          ] }, part.gap)),
          jsx('p', { className: 'hk-small', children: 'Yours can differ and still be right. Look for what the model answer includes that yours leaves out.' }),
        ] })
      : null,
  ] })
}

function LabStep({ mission, step, onChanged }) {
  const done = step.status === 'done'
  return jsxs('div', { className: 'hk-actions', children: [
    step.action === 'route' ? jsx(Button, { onClick: () => host.navigate(step.route), children: step.route_label || 'Open it in Hermes' }) : null,
    step.action === 'coach' ? jsx(Button, { onClick: () => startPracticeChat(step.prompt), children: 'Start a practice chat' }) : null,
    jsx(Button, {
      variant: 'secondary',
      onClick: () => setStep(mission, step, done ? 'ready' : 'done', onChanged),
      children: done ? 'Mark as not done' : 'I did this',
    }),
  ] })
}

/** Hand text to the learner's own Hermes. Falls back to the clipboard when no
 *  chat is open or the agent is mid-turn, so the answer is never lost. */
/** Scoring happens in its own fresh chat, so it never lands in the middle of the learner's real work. */
async function sendToHermes(text) {
  if (!text) return false
  return sendInNewChat(text, 'Your answer is saved and copied. Paste it into the new chat to get your score.')
}

function ExplainStep({ mission, step, onChanged }) {
  const saved = step.explanation || {}
  const graded = typeof saved.score === 'number'
  const threshold = step.threshold || 70
  const passed = graded && saved.score >= threshold
  const waiting = !graded && Boolean(saved.answer)
  const [answer, setAnswer] = useState('')
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')

  // A submitted answer waits for Hermes to score it. If the request never reached a chat, or the
  // learner closed that chat, this rebuilds the scoring request from the saved answer.
  const resend = async () => {
    if (busy) return
    setBusy(true)
    setProblem('')
    try {
      const payload = await ctxRest(`/explain/${mission.id}/${step.id}/resend`, { method: 'POST', body: {} })
      await sendToHermes(payload?.prompt || '')
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy(false)
    }
  }

  if (passed) {
    return jsxs('div', { className: 'hk-stack', children: [
      jsxs('div', { className: 'hk-row', style: { flexWrap: 'nowrap', gap: 12 }, children: [
        jsx(Ring, { value: saved.score / 100, size: 40, stroke: 4, tone: 'good', label: String(saved.score), title: `${saved.score} out of 100` }),
        jsx('div', { className: 'hk-grow', children: jsx(Result, { result: { passed: true, title: `Passed with ${saved.score} out of 100`, detail: saved.feedback || '' } }) }),
      ] }),
      jsx('p', { className: 'hk-small', children: 'Your pass stays. This question comes back in your Review queue, and your answers there change its strength, never the pass.' }),
    ] })
  }

  const submit = async () => {
    if (busy) return
    if (answer.trim().length < 120) {
      setProblem('Write at least two or three sentences, so there is enough to score.')
      return
    }
    setBusy(true)
    setProblem('')
    try {
      const payload = await ctxRest(`/explain/${mission.id}/${step.id}`, {
        method: 'POST',
        body: { answer, session_id: host.state.focusedSessionId?.get?.() || '' },
      })
      await sendToHermes(payload?.prompt || '')
      setAnswer('')
      await refresh()
      onChanged()
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy(false)
    }
  }

  return jsxs('div', { className: 'hk-stack', children: [
    graded
      ? jsxs('div', { className: 'hk-stack', children: [
          jsxs('div', { className: 'hk-row', style: { flexWrap: 'nowrap', gap: 12 }, children: [
            jsx(Ring, { value: saved.score / 100, size: 40, stroke: 4, tone: passed ? 'good' : 'warn', label: String(saved.score), title: `${saved.score} out of 100` }),
            jsx('div', { className: 'hk-grow', children: jsx(Result, { result: {
              passed,
              title: passed ? `Passed with ${saved.score} out of 100` : `${saved.score} out of 100. You need ${threshold} to pass`,
              detail: saved.feedback || '',
            } }) }),
          ] }),
          !passed ? jsx(Feedback, { feedback: saved.ladder }) : null,
        ] })
      : null,
    waiting
      ? jsx(Card, { tone: 'info', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
          jsx('strong', { children: 'Your answer is waiting for its score' }),
          jsx('p', { children: 'Hermes scores it in a chat and the score shows here. If the chat never got the request, send it again.' }),
          jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: busy, onClick: resend, children: 'Send for scoring again' }) }),
        ] }) })
      : null,
    jsx('p', { className: 'hk-small', children: `Hermes scores your answer out of 100. ${threshold} or more passes, and you can try as many times as you like.` }),
    jsx(Textarea, {
      style: { minHeight: '7rem', width: '100%' },
      value: answer,
      onChange: event => setAnswer(event.target.value),
      placeholder: graded && !passed ? 'Write a new answer. Start from the first thing that was missing.' : graded ? 'Write a new answer to try again.' : 'Answer in your own words.',
      'aria-label': 'Your answer',
      ...submitOnModEnter(submit),
    }),
    problem ? jsx(Result, { result: { passed: false, title: problem } }) : null,
    jsxs('div', { className: 'hk-actions', children: [
      jsx(Button, { loading: busy, onClick: submit, children: graded ? 'Send for a new score' : 'Send for scoring' }),
      jsx(KeyHint, { keys: [modKey(), '↵'], label: 'to send' }),
    ] }),
    jsx(Details, { label: 'What a strong answer covers', children: [
      jsx('p', { className: 'hk-small', children: 'Open this after you write yours.' }, 'p'),
      jsx('ul', { className: 'fa-bullets', children: (step.covers || []).map(item => jsx('li', { children: item }, item)) }, 'l'),
    ] }),
  ] })
}

function GateStep({ mission, step, onChanged }) {
  const [result, setResult] = useState(null)
  const [path, setPath] = useState('')
  const [pasting, setPasting] = useState(false)
  const [pasted, setPasted] = useState('')
  const [values, setValues] = useState({})
  const [busy, setBusy] = useState(false)
  const isDocument = step.verify === 'artifact'
  const done = step.status === 'done'
  const inputs = step.inputs && step.inputs.length ? step.inputs : INPUTS_BY_CHECK[step.check] || []
  const live = { ...step, since: mission.started_at }
  const showRecheck = mission.reverify || mission.changed

  const record = async extra => {
    try {
      const payload = await ctxRest(`/gate/${mission.id}/${step.id}`, {
        method: 'POST',
        body: { session_id: host.state.focusedSessionId?.get?.() || '', ...extra },
      })
      setResult(payload.outcome)
      if (payload.outcome?.passed) {
        await refresh()
        onChanged()
      } else {
        await refresh()
      }
    } catch (error) {
      setResult({ error: true, passed: false, title: "The result couldn't be saved", detail: errorText(error), facts: [] })
    }
  }

  const run = async () => {
    if (busy) return
    setBusy(true)
    try {
      if (isDocument) {
        if (pasting ? !pasted.trim() : !path.trim()) {
          setResult(pasting
            ? { passed: false, title: 'Paste the whole document first', detail: 'Copy everything in the file, headings included, and paste it in the box.', facts: [] }
            : { passed: false, title: 'Type where you saved the file first', detail: 'For example ~/Documents/scope.md on Mac and Linux, or C:\\Users\\you\\Documents\\scope.md on Windows', facts: [] })
          return
        }
        const liveOutcome = step.live ? await runDesktopCheck({ check: step.live }, {}) : null
        await record({ ...(pasting ? { text: pasted } : { path: path.trim() }), ...(liveOutcome ? { live: liveOutcome } : {}) })
        return
      }
      const outcome = await runDesktopCheck(live, values)
      await record({ outcome })
    } finally {
      setBusy(false)
    }
  }

  const feedback = result ? (result.passed ? null : result.feedback) : (!done ? step.feedback : null)
  return jsxs('div', { className: 'hk-stack', children: [
    showRecheck
      ? jsx(Card, { tone: 'info', children: jsxs('div', { className: 'hk-stack', style: { gap: 3 }, children: [
          jsx('strong', { children: 'This check changed since you passed' }),
          jsx('p', { children: 'Run it again to re-verify this mission. Your pass stays whatever it finds.' }),
        ] }) })
      : null,
    isDocument
      ? jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
          jsx(Label, { plain: true, children: 'Sections it needs' }),
          jsx('div', { className: 'hk-row', style: { gap: 4 }, children: (step.headings || []).map(heading =>
            jsx(Pill, { tone: 'idle', children: heading.charAt(0).toUpperCase() + heading.slice(1) }, heading)
          ) }),
          step.live ? jsx('p', { className: 'hk-small', children: 'This check also reads Hermes: it looks at what this window is connected to.' }) : null,
          pasting
            ? jsx(Textarea, {
                value: pasted,
                onChange: event => setPasted(event.target.value),
                placeholder: '# Your document\n\n## First heading\nWhat goes under it...',
                'aria-label': 'Your document, pasted',
                style: { minHeight: '10rem', width: '100%', fontFamily: 'var(--hk-mono)' },
                ...submitOnModEnter(run),
              })
            : jsx(Input, {
                value: path,
                onChange: event => setPath(event.target.value),
                placeholder: '~/Documents/my-document.md',
                'aria-label': 'Where you saved the file',
                onKeyDown: e => { if (e.key === 'Enter' && !e.nativeEvent?.isComposing) run() },
              }),
          jsx('button', { type: 'button', className: 'hk-link', style: { justifySelf: 'start' }, onClick: () => setPasting(!pasting), children: pasting
            ? 'Type where the file is saved instead'
            : 'Hermes runs on another computer? Paste the document instead' }),
        ] })
      : inputs.length
        ? jsx('div', { className: 'fa-inputs', children: inputs.map(input => jsxs('div', { className: 'fa-field', style: input.multiline ? { gridColumn: '1 / -1' } : undefined, children: [
            jsx('label', { htmlFor: `fa-in-${mission.id}-${input.id}`, children: input.label }),
            input.options
              ? jsxs('select', {
                  id: `fa-in-${mission.id}-${input.id}`, className: 'fa-select', value: values[input.id] || '',
                  onChange: event => setValues({ ...values, [input.id]: event.target.value }),
                  children: [jsx('option', { value: '', children: 'Choose one' }, 'none'), ...input.options.map(option => jsx('option', { value: option, children: option }, option))],
                })
              : input.multiline
                ? jsx(Textarea, {
                    id: `fa-in-${mission.id}-${input.id}`, value: values[input.id] || '', placeholder: input.placeholder || '',
                    style: { minHeight: '6rem', width: '100%' },
                    onChange: event => setValues({ ...values, [input.id]: event.target.value }),
                    ...submitOnModEnter(run),
                  })
              : jsx(Input, {
                  id: `fa-in-${mission.id}-${input.id}`, value: values[input.id] || '', placeholder: input.placeholder || '',
                  onChange: event => setValues({ ...values, [input.id]: event.target.value }),
                  onKeyDown: e => { if (e.key === 'Enter' && !e.nativeEvent?.isComposing) run() },
                }),
          ] }, input.id)) })
        : null,
    jsxs('div', { className: 'hk-actions', children: [
      jsx(Button, { loading: busy, onClick: run, children: done ? 'Check again' : 'Check my work' }),
      busy ? jsx('span', { className: 'hk-small', role: 'status', children: 'Reading your Hermes' }) : null,
    ] }),
    jsx(Result, { result: feedback && result && (feedback.missing || []).length ? { ...result, detail: '' } : result }),
    feedback ? jsx(Feedback, { feedback }) : null,
  ] })
}

function stepAnchor(mission, index) {
  return `fa-step-${mission.id}-${index}`
}

/** One step as a field note: a large numeral in the margin, the kind in small caps, then the work. */
function StepNote({ mission, step, index, onChanged }) {
  const meta = kindOf(mission, step)
  const done = step.status === 'done'
  const placed = step.status === 'placed'
  const justDone = useJustChanged(done)
  return jsxs('li', { className: 'fa-note', id: stepAnchor(mission, index), 'data-done': done || placed ? '' : undefined, children: [
    jsx('div', { className: 'fa-note-num', 'aria-hidden': 'true', children: jsx('span', { className: 'fa-num fa-num-l', children: index + 1 }) }),
    jsxs('div', { className: 'fa-note-body', children: [
      jsxs('div', { className: 'fa-note-kind', children: [
        jsxs('span', { className: 'fa-sc fa-sc-blaze', style: { display: 'inline-flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }, children: [
          jsx(Codicon, { name: meta.icon, size: 13 }),
          `Step ${index + 1} · ${meta.label}`,
          step.minutes ? ` · ${minutesWords(step.minutes)}` : '',
        ] }),
        done ? jsxs('span', { className: `fa-done-tag ${justDone ? 'hk-enter' : ''}`, children: [jsx(Codicon, { name: 'check', size: 13 }), 'Done'] }) : null,
        placed ? jsxs('span', { className: 'fa-placed', children: [jsx(Codicon, { name: 'arrow-right', size: 13 }), 'Skipped by placement'] }) : null,
      ] }),
      jsx('h3', { className: 'hk-h2', children: step.title }),
      step.body && !step.lines?.length ? jsx(Prose, { text: step.body, className: 'fa-note-text' }) : null,
      step.kind === 'lesson' ? jsx(LessonStep, { mission, step, onChanged }) : null,
      step.kind === 'example' ? jsx(ExampleStep, { mission, step, onChanged }) : null,
      step.kind === 'complete' ? jsx(CompleteStep, { mission, step, onChanged }) : null,
      step.kind === 'lab' ? jsx(LabStep, { mission, step, onChanged }) : null,
      step.kind === 'explain' ? jsx(ExplainStep, { mission, step, onChanged }) : null,
      step.kind === 'gate' ? jsx(GateStep, { mission, step, onChanged }) : null,
    ] }),
  ] })
}

/** The steps in a row beside the compass. Each one jumps to its note. */
function StepStrip({ mission }) {
  const steps = mission.steps || []
  const reading = compassReading(steps)
  const verified = mission.status === 'verified'
  return jsxs('div', { className: 'fa-strip hk-enter', children: [
    jsx(Compass, { steps }),
    jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
      jsxs('div', { className: 'hk-row', style: { gap: 12 }, children: [
        jsxs('span', { className: 'fa-num fa-num-m', children: [reading.done, jsx('small', { children: `of ${plural(reading.total, 'step', 'steps')} done` })] }),
        jsx('span', { className: 'hk-small', children: verified ? statusWords(mission) : `${minutesWords(mission.minutes)} in all` }),
      ] }),
      jsx('ol', { className: 'fa-strip-steps', style: { '--fa-n': Math.max(1, steps.length) }, children: steps.map((step, i) => {
        const state = ['done', 'placed'].includes(step.status) ? 'done' : i === reading.at ? 'now' : 'later'
        const meta = kindOf(mission, step)
        return jsx('li', { children: jsxs('button', {
          type: 'button', className: 'fa-strip-step', 'data-state': state, onClick: () => scrollToId(stepAnchor(mission, i)),
          'aria-label': `Step ${i + 1}, ${meta.label}: ${state === 'done' ? 'done' : state === 'now' ? 'you are here' : 'later'}`,
          children: [
            jsx('span', { className: 'fa-num fa-num-m', children: i + 1 }),
            jsx('span', { className: 'fa-sc', children: meta.short || meta.label }),
            jsx('span', { className: 'fa-strip-state', children: state === 'done' ? 'Done' : state === 'now' ? 'You are here' : 'Later' }),
          ],
        }) }, step.id)
      }) }),
    ] }),
  ] })
}

function ChangeNote({ change, onChanged, goGate }) {
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const acknowledge = async () => {
    setBusy(true)
    setProblem('')
    try {
      await ctxRest(`/mission/${change.mission_id}/acknowledge`, { method: 'POST', body: {} })
      await refresh()
      onChanged()
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy(false)
    }
  }
  return jsx(Card, { tone: 'info', className: 'hk-enter', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
    jsx('strong', { children: `This mission changed after you passed it (version ${change.passed_version}, now ${change.version})` }),
    jsx('ul', { className: 'fa-bullets', children: change.revisions.map(r => jsx('li', { children: r.summary }, r.summary)) }),
    problem ? jsx(Result, { result: { passed: false, title: problem } }) : null,
    jsx('div', { className: 'hk-actions', children: change.needs === 'check'
      ? jsx(Button, { onClick: goGate, children: 'Go to the check and re-verify' })
      : jsx(Button, { loading: busy, onClick: acknowledge, children: "I've read the changes" }) }),
  ] }) })
}

function PassedBanner({ mission, track, go }) {
  if (mission.status !== 'verified') return null
  const next = track.missions.find(m => m.id === track.here)
  const ready = track.certificate.status === 'ready'
  const due = mission.review_due_at ? dueWords(mission.review_due_at) : ''
  return jsx(Card, { tone: 'good', tint: true, className: 'hk-enter', children: jsxs('div', { className: 'hk-banner', children: [
    jsx(BadgeIcon, { name: 'pass-filled', tone: 'good' }),
    jsxs('div', { className: 'hk-grow hk-stack', style: { gap: 2 }, children: [
      jsx('strong', { children: `Passed ${shortDate(mission.passed_at)}` }),
      jsx('p', { children: next ? `Next waypoint: ${next.title} · ${next.level_name} · ${minutesWords(next.minutes)}`
        : ready ? 'Every mission on this path passed. Your Field Record is ready to create at the summit.' : 'Every mission on this path passed.' }),
      due ? jsx('p', { className: 'hk-small', children: `This mission comes back for a short review. ${due}.` }) : null,
    ] }),
    next
      ? jsx(Button, { onClick: () => go({ name: 'mission', id: next.id }), children: 'Start' })
      : jsx(Button, { onClick: () => go({ name: 'path', id: track.id }), children: ready ? 'Create your Field Record' : 'See your path' }),
  ] }) })
}

function MissionView({ mission, track, go, onChanged, changes = [], focus }) {
  const gateIndex = (mission.steps || []).findIndex(step => step.kind === 'gate')
  const goGate = () => scrollToId(stepAnchor(mission, gateIndex))
  useEffect(() => {
    if (focus !== 'gate' || gateIndex < 0) return undefined
    const timer = setTimeout(goGate, 350)
    return () => clearTimeout(timer)
  }, [mission.id, focus])
  const change = changes.find(item => item.mission_id === mission.id)
  return jsx(Frame, { width: 'narrow', up: () => go({ name: 'path', id: track.id }), children: [
    jsx(PageHeader, {
      back: jsx(Back, { label: `${track.name} path`, onClick: () => go({ name: 'path', id: track.id }) }),
      eyebrow: jsx(Label, { children: `Field note · ${track.name} path · ${mission.level_name} camp` }),
      title: mission.title, lead: mission.promise,
    }, 'head'),
    jsx(StepStrip, { mission }, 'strip'),
    jsxs('div', { className: 'fa-outcome', children: [
      jsx(Label, { plain: true, children: 'By the end' }),
      jsx('p', { children: mission.outcome }),
    ] }, 'outcome'),
    mission.use_text
      ? jsxs('div', { className: 'fa-use', children: [jsx(Label, { plain: true, children: 'Why this matters to you' }, 'l'), jsx('p', { children: mission.use_text }, 'p')] }, 'use')
      : null,
    change ? jsx(ChangeNote, { change, onChanged, goGate }, 'change') : null,
    jsx(PassedBanner, { mission, track, go }, 'passed'),
    jsx('ol', { className: 'fa-notes', children: mission.steps.map((step, index) =>
      jsx(StepNote, { mission, step, index, onChanged }, step.id)
    ) }, 'steps'),
    jsx(GoDeeper, { mission }, 'deeper'),
  ] })
}

/* ---------------------------------------------------------- field record -- */

function CertificateView({ track, go }) {
  const issued = track.certificate.issued
  const [saved, setSaved] = useState(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const up = () => go({ name: 'path', id: track.id })

  if (!issued) {
    return jsx(Frame, { width: 'narrow', up, children: [
      jsx(Back, { label: `${track.name} path`, onClick: up }, 'back'),
      jsx('div', { className: 'fa-panel', key: 'none', children: jsxs('div', { className: 'hk-row', style: { flexWrap: 'nowrap', gap: 16 }, children: [
        jsx(CertificateBezel, { track, size: 72 }),
        jsxs('div', { className: 'hk-stack', style: { gap: 3 }, children: [
          jsx(Label, { children: 'Summit' }),
          jsx('h1', { className: 'hk-h1', children: 'No Field Record yet' }),
          jsx('p', { children: `Pass every mission on the ${track.name} path to create it.` }),
        ] }),
      ] }) }),
    ] })
  }
  const body = issued.body
  const display = issued.display || { issuer: body.issuer, shows: body.shows, disclaimer: body.disclaimer || RECORD_DISCLAIMER }

  const save = async () => {
    setBusy(true)
    setProblem('')
    try {
      setSaved(await ctxRest(`/certificate/${track.id}/save`, { method: 'POST', body: {} }))
    } catch (error) {
      setProblem(errorText(error))
    } finally {
      setBusy(false)
    }
  }

  return jsx(Frame, { up, children: [
    jsx(Back, { label: `${track.name} path`, onClick: up }, 'back'),
    jsx('article', { className: 'fa-cert hk-enter', 'aria-label': `Field Record for ${body.name}, self-issued with Field Academy`, children: jsxs('div', { className: 'fa-cert-inner', children: [
      jsx(Contours, { width: 900, height: 600, seed: 7 }),
      jsx(CertCorners, {}),
      jsxs('div', { className: 'fa-cert-top', children: [
        jsxs('div', { style: { display: 'grid', gap: 3 }, children: [
          jsx(Label, { children: 'Field Record' }),
          jsx('span', { className: 'fa-sc', children: 'Self-issued learning record' }),
        ] }),
        jsxs('div', { style: { display: 'grid', gap: 3, justifyItems: 'end', textAlign: 'right' }, children: [
          jsx(Label, { plain: true, children: 'Record number' }),
          jsx('span', { className: 'fa-cert-number', children: body.number }),
        ] }),
      ] }),
      jsxs('div', { className: 'fa-cert-centre', children: [
        jsx(Label, { plain: true, children: 'Kept by' }),
        jsx('p', { className: 'fa-cert-name', children: body.name }),
        jsx(Label, { plain: true, children: 'who passed every mission on the' }),
        jsx('h1', { className: 'fa-cert-path', children: `${body.path} path` }),
        jsx('p', { className: 'fa-cert-promise', children: body.path_promise }),
        jsx('p', { children: `Created ${longDate(body.issued_at)}, on the holder's own computer` }),
      ] }),
      jsxs('div', { className: 'fa-cert-foot', children: [
        jsxs('div', { style: { display: 'grid', gap: 6 }, children: [
          jsx(Label, { children: 'Self-issued' }),
          jsx('p', { className: 'fa-cert-issuer', children: display.disclaimer }),
          jsx('p', { className: 'hk-small fa-cert-issuer', children: `${display.issuer} ${display.shows}` }),
        ] }),
        jsx(Seal, { size: 124 }),
      ] }),
    ] }) }, 'cert'),
    jsxs('div', { className: 'hk-actions', key: 'save', children: [
      jsx(Button, { loading: busy, onClick: save, children: 'Save as a file' }),
      jsx(Pill, { tone: issued.valid ? 'good' : 'bad', icon: issued.valid ? 'pass-filled' : 'error',
        children: issued.valid ? 'The record number matches its contents' : "The record number doesn't match its contents" }),
    ] }),
    saved
      ? jsx(Result, { result: { passed: true, title: 'Saved', detail: 'A readable copy and a data copy are on your computer.', facts: [
          { label: 'Readable copy', value: saved.markdown },
          { label: 'Data copy', value: saved.json },
        ] } }, 'saved')
      : null,
    problem ? jsx(Result, { result: { passed: false, title: problem } }, 'problem') : null,
    jsx(Section, { title: 'The proof behind it', children: jsx(Card, { flush: true, children: jsx('div', { style: { overflowX: 'auto', padding: '4px 14px 8px' }, children: jsxs('table', { className: 'fa-table', children: [
      jsx('thead', { children: jsxs('tr', { children: [
        jsx('th', { children: 'Camp' }), jsx('th', { children: 'Mission' }), jsx('th', { children: 'Passed' }),
        jsx('th', { children: 'What the check found' }), jsx('th', { children: 'Check' }), jsx('th', { children: 'Question' }), jsx('th', { children: 'Document' }),
      ] }) }),
      jsx('tbody', { children: body.missions.map(item => jsxs('tr', { children: [
        jsx('td', { children: item.level }),
        jsx('td', { children: jsx('strong', { children: item.title }) }),
        jsx('td', { children: shortDate(item.passed_at) }),
        jsx('td', { children: item.check_result || item.check }),
        jsx('td', { children: item.check_version ? `Version ${item.check_version}${item.reading_skipped ? ', reading skipped by placement' : ''}` : '' }),
        jsx('td', { children: item.question_score == null ? '' : `${item.question_score} of 100` }),
        jsx('td', { children: item.document
          ? jsxs('span', { children: [item.document, jsx('br', {}), jsx('span', { className: 'hk-mono', children: `SHA-256 ${String(item.fingerprint || '').slice(0, 16)}` })] })
          : '' }),
      ] }, item.mission_id)) }),
    ] }) }) }) }, 'proof'),
  ] })
}

/* ----------------------------------------------------------------- review -- */

const OUTCOME_WORDS = {
  advanced: 'Stronger',
  held: 'Unchanged',
  lapsed: 'Comes back sooner',
  practiced: 'Practice counted',
}

function ReviewResults({ session, go }) {
  const results = session.results || []
  const strong = results.filter(item => item.passed).length
  return jsx(Frame, { width: 'narrow', up: () => go({ name: 'map' }), children: [
    jsx(PageHeader, {
      back: jsx(Back, { label: 'Trail map', onClick: () => go({ name: 'map' }) }),
      eyebrow: jsx(Label, { children: 'Review' }),
      title: 'Your review is scored',
      lead: `${strong} of ${plural(results.length, 'answer', 'answers')} scored 70 or more. A miss comes back tomorrow, and an answer you hold comes back after a longer wait.`,
    }, 'head'),
    ...results.map(item => jsx(Card, { children: jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
      jsxs('div', { className: 'hk-row', style: { flexWrap: 'nowrap', gap: 12 }, children: [
        jsx(Ring, { value: item.score / 100, size: 40, stroke: 4, tone: item.passed ? 'good' : 'warn', label: String(item.score), title: `${item.score} out of 100` }),
        jsxs('div', { className: 'hk-grow hk-stack', style: { gap: 2 }, children: [
          jsx('strong', { children: item.title }),
          jsx('span', { className: 'hk-small', children: [OUTCOME_WORDS[item.outcome], `Strength: ${item.strength_word}`, item.early ? 'Your review schedule stays as it was' : `Next review: ${dueWords(item.next_due_at).replace('Due ', '').toLowerCase()}`].filter(Boolean).join(' · ') }),
        ] }),
      ] }),
      item.feedback ? jsx(Prose, { text: item.feedback }) : null,
      item.ladder ? jsx(Feedback, { feedback: item.ladder }) : null,
      jsx('div', { children: jsx('button', { type: 'button', className: 'hk-link', onClick: () => go({ name: 'mission', id: item.mission_id }), children: 'Open the mission' }) }),
    ] }) }, item.mission_id)),
    jsx('div', { className: 'hk-actions', children: jsx(Button, { onClick: () => go({ name: 'map' }), children: 'Back to the map' }) }, 'done'),
  ] })
}

function ReviewView({ practice, go }) {
  const [session, setSession] = useState(null)
  const [error, setError] = useState('')
  const [answers, setAnswers] = useState({})
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')

  useEffect(() => {
    let live = true
    ctxRest('/review/start', { method: 'POST', body: { practice: Boolean(practice) } })
      .then(next => { if (live) setSession(next) })
      .catch(err => { if (live) setError(errorText(err)) })
    return () => { live = false }
  }, [])

  useEffect(() => {
    if (!session || session.status !== 'submitted') return undefined
    const timer = setInterval(async () => {
      try {
        const next = await ctxRest(`/review/${session.id}`)
        if (next.status === 'graded') {
          setSession(next)
          refresh()
        }
      } catch (err) {
        // The next tick tries again.
      }
    }, 3000)
    return () => clearInterval(timer)
  }, [session?.id, session?.status])

  const send = async text => {
    if (busy) return
    setBusy(true)
    setProblem('')
    try {
      const payload = await ctxRest(`/review/${session.id}/submit`, { method: 'POST', body: { answers: text } })
      await sendToHermes(payload.prompt)
      setSession(await ctxRest(`/review/${session.id}`))
    } catch (err) {
      setProblem(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  const up = () => go({ name: 'map' })
  if (error) {
    return jsx(Frame, { width: 'narrow', up, children: [
      jsx(Back, { label: 'Trail map', onClick: up }, 'back'),
      jsx(Card, { key: 'none', children: jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
        jsx('h1', { className: 'hk-h2', children: 'Nothing to review right now' }),
        jsx('p', { children: error }),
        jsxs('div', { className: 'hk-actions', children: [
          !practice ? jsx(Button, { onClick: () => go({ name: 'review', practice: true }), children: 'Practice early' }) : null,
          jsx(Button, { variant: 'secondary', onClick: up, children: 'Back to the map' }),
        ] }),
      ] }) }),
    ] })
  }
  if (!session) return jsx(Frame, { width: 'narrow', children: jsx(SkeletonPage, { label: 'Getting your review', cards: [{ title: true, lines: 4 }] }) })
  if (session.status === 'graded') return jsx(ReviewResults, { session, go })

  const submitted = session.status === 'submitted'
  const ready = session.items.every(item => (answers[item.mission_id] || '').trim().length >= 40)
  return jsx(Frame, { width: 'narrow', up, children: [
    jsx(PageHeader, {
      back: jsx(Back, { label: 'Trail map', onClick: up }),
      eyebrow: jsx(Label, { children: session.practice ? 'Practice review' : 'Review' }),
      title: `${plural(session.items.length, 'question', 'questions')} from missions you passed`,
      lead: session.practice
        ? 'This is early practice. Your answers change your strength, and your review schedule stays as it is.'
        : 'Answer from memory, in your own words, before you look anything up. A sentence or two each is enough. Hermes scores them the way it scores a mission question.',
    }, 'head'),
    ...session.items.map((item, index) => jsxs('div', { className: 'fa-q', children: [
      jsx(Label, { children: `Question ${index + 1} · ${item.title}` }),
      jsx(Prose, { text: item.question }),
      jsx(Textarea, {
        style: { minHeight: '6rem', width: '100%' },
        value: submitted ? (session.answers[item.mission_id] || '') : (answers[item.mission_id] || ''),
        readOnly: submitted,
        onChange: event => setAnswers({ ...answers, [item.mission_id]: event.target.value }),
        placeholder: 'Write what you remember.',
        'aria-label': `Your answer to question ${index + 1}`,
      }),
    ] }, item.mission_id)),
    problem ? jsx(Result, { result: { passed: false, title: problem } }, 'problem') : null,
    submitted
      ? jsx(Card, { tone: 'info', className: 'hk-enter', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
          jsx('strong', { children: 'Waiting for Hermes to score your answers' }),
          jsx('p', { children: 'Your answers went to your own Hermes, and the scores show here once it records them. If nothing happens after a minute, send the instruction again.' }),
          jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: busy, onClick: () => send(session.answers), children: 'Send it again' }) }),
        ] }) }, 'wait')
      : jsxs('div', { className: 'hk-actions', children: [
          jsx(Button, { loading: busy, disabled: !ready, onClick: () => send(answers), children: 'Send for scoring' }),
          ready ? null : jsx('span', { className: 'hk-small', children: 'Write at least a sentence for each question.' }),
        ] }, 'send'),
  ] })
}

/* --------------------------------------------------------------- placement -- */

const LEVEL_LABEL = { beginner: 'Beginner camp', intermediate: 'Intermediate camp', advanced: 'Advanced camp' }

function PlacementView({ trackId, track, go }) {
  const [spec, setSpec] = useState(null)
  const [error, setError] = useState('')
  const [picks, setPicks] = useState({})
  const [outcome, setOutcome] = useState(null)
  const [applied, setApplied] = useState(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState('')
  const up = () => go({ name: 'path', id: trackId })

  useEffect(() => {
    let live = true
    ctxRest(`/placement/${trackId}`).then(next => { if (live) setSpec(next) }).catch(err => { if (live) setError(errorText(err)) })
    return () => { live = false }
  }, [trackId])

  if (error) return jsx(Frame, { width: 'narrow', up, children: [jsx(Back, { label: `${track?.name || 'Path'} path`, onClick: up }, 'back'), jsx(Result, { result: { passed: false, title: error } }, 'err')] })
  if (!spec) return jsx(Frame, { width: 'narrow', children: jsx(SkeletonPage, { label: 'Getting the placement check', cards: [{ title: true, lines: 5 }] }) })

  const answered = spec.questions.every(q => picks[q.id] !== undefined)
  const submit = async () => {
    if (busy) return
    setBusy(true)
    setProblem('')
    try {
      setOutcome(await ctxRest(`/placement/${trackId}`, { method: 'POST', body: { answers: picks } }))
      await refresh()
    } catch (err) {
      setProblem(errorText(err))
    } finally {
      setBusy(false)
    }
  }
  const apply = async () => {
    setBusy(true)
    setProblem('')
    try {
      setApplied(await ctxRest(`/placement/${trackId}/apply`, { method: 'POST', body: {} }))
      await refresh()
    } catch (err) {
      setProblem(errorText(err))
    } finally {
      setBusy(false)
    }
  }
  const results = outcome?.results
  const known = outcome?.known_levels || []

  return jsx(Frame, { width: 'narrow', up, children: [
    jsx(PageHeader, {
      back: jsx(Back, { label: `${track?.name || 'Path'} path`, onClick: up }),
      eyebrow: jsx(Label, { children: 'Placement check' }),
      title: spec.title,
      lead: spec.intro,
    }, 'head'),
    ...(results
      ? [
          jsx(Card, { tone: known.length ? 'good' : 'info', tint: true, className: 'hk-enter', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
            jsx('strong', { children: known.length ? `You knew ${known.map(level => LEVEL_LABEL[level].replace(' camp', '')).join(' and ')}` : 'No level is clear yet' }),
            jsx('p', { children: known.length
              ? `Both questions right on a level skips that level's reading and practice. ${outcome.offer.keeps}`
              : 'Start each mission with its lesson. You can take the check again later.' }),
            known.length && !applied
              ? jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: busy, onClick: apply, children: `Skip the reading on ${plural(outcome.offer.missions.length, 'mission', 'missions')}` }) })
              : null,
            applied ? jsx(Result, { result: { passed: true, title: `Skipped the reading and practice on ${plural(applied.steps_skipped, 'step', 'steps')}`, detail: 'Each question and each check still counts, and your Field Record says the reading was skipped.' } }) : null,
          ] }) }, 'outcome'),
          ...spec.questions.map((q, index) => {
            const found = results.questions.find(item => item.id === q.id)
            return jsx('div', { className: 'fa-q', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
              jsx(Label, { children: `Question ${index + 1} · ${LEVEL_LABEL[q.level]} · ${found?.right ? 'Right' : 'Not this time'}` }),
              jsx(Prose, { text: q.question }),
              jsx('p', { children: `Your answer: ${q.options[found?.chosen] ?? 'none'}` }),
              jsx(Prose, { text: found?.why }),
            ] }) }, q.id)
          }),
          jsxs('div', { className: 'hk-actions', children: [
            jsx(Button, { variant: 'secondary', onClick: () => { setOutcome(null); setPicks({}); setApplied(null) }, children: 'Take it again' }),
            jsx(Button, { onClick: up, children: `Back to the ${track?.name || ''} path` }),
          ] }, 'after'),
        ]
      : [
          ...spec.questions.map((q, index) => jsxs('fieldset', { className: 'fa-q', children: [
            jsx('legend', { children: jsx(Label, { children: `Question ${index + 1} · ${LEVEL_LABEL[q.level]}` }) }),
            jsx(Prose, { text: q.question }),
            jsx('div', { className: 'fa-choices', children: q.options.map((option, i) =>
              jsxs('label', { className: 'fa-choice', 'data-picked': picks[q.id] === i ? '' : undefined, children: [
                jsx('input', { type: 'radio', name: `fa-${q.id}`, checked: picks[q.id] === i, onChange: () => setPicks({ ...picks, [q.id]: i }) }),
                jsx('span', { children: option }),
              ] }, option)) }),
          ] }, q.id)),
          problem ? jsx(Result, { result: { passed: false, title: problem } }, 'problem') : null,
          jsxs('div', { className: 'hk-actions', children: [
            jsx(Button, { loading: busy, disabled: !answered, onClick: submit, children: 'See my result' }),
            answered ? null : jsx('span', { className: 'hk-small', children: 'Choose one option for every question.' }),
          ] }, 'send'),
        ]),
  ] })
}

/* ------------------------------------------------------------------- page -- */

function Offline({ error, onRetry }) {
  return jsx(Frame, { width: 'narrow', children: jsx(NotConnected, {
    name: 'Field Academy', error, onRetry,
    steps: jsxs('div', { className: 'hk-stack', children: [
      jsx('p', { children: "The part of Field Academy that saves your progress isn't running." }),
      jsx('p', { children: 'In Hermes, open Capabilities, then Plugins, and turn on Field Academy. Then quit Hermes and open it again.' }),
      jsx('p', { children: 'Or run this once in a terminal, then restart Hermes:' }),
      jsx('pre', { className: 'fa-pre', children: 'hermes plugins enable field-academy' }),
    ] }),
    otherwise: "Your progress can't load right now. Try again in a minute.",
  }) })
}

/** The Deployer path needs the 0.6.0 backend. An older one answers 404, so say what to do instead of showing a blank page. */
function DeployerUnavailable({ loading, error, go }) {
  return jsx(Frame, { width: 'narrow', up: () => go({ name: 'map' }), children: [
    jsx(PageHeader, { back: jsx(Back, { label: 'Trail map', onClick: () => go({ name: 'map' }) }), eyebrow: jsx(Label, { children: 'For clients, in practice' }), title: 'Deployer path', lead: loading ? 'Loading.' : 'The part of Field Academy that saves your progress does not know this path yet.' }, 'head'),
    loading ? null : jsx(Card, { key: 'why', tone: 'warn', children: jsxs('div', { className: 'hk-stack', children: [
      jsx('p', { children: 'The Deployer path needs Field Academy 0.6.0 or newer running inside Hermes. Quit Hermes and open it again to load it.' }),
      error ? jsx('p', { className: 'hk-small', children: errorText(error) }) : null,
    ] }) }),
  ] })
}

function Page() {
  const query = usePassport()
  const deployerQuery = useDeployer()
  const deployer = deployerQuery.data && deployerQuery.data.track ? deployerQuery.data : null
  const [view, setView] = useState(() => readView())

  useEffect(() => {
    if (deployer) syncVersion(deployer)
  }, [Boolean(deployer)])

  const go = next => setView(next)

  // An in-chat offer can ask for a mission while the page is already open.
  useEffect(() => {
    const apply = id => {
      pendingMission = null
      setView({ name: 'mission', id })
    }
    missionListeners.add(apply)
    return () => missionListeners.delete(apply)
  }, [])

  let body = null
  if (query.loading) {
    body = jsx(Frame, { children: jsx(SkeletonPage, { label: 'Loading your paths', cards: MAP_SHAPE }) })
  } else if (query.error && !query.data) {
    body = jsx(Offline, { error: query.error, onRetry: () => query.refetch() })
  } else {
    const data = query.data || {}
    const track = (data.tracks || []).find(item => item.id === view.id)
    if (view.name === 'path' && view.id === 'deployer') {
      body = deployer
        ? jsx(deployerViews.DeployerPath, { data: deployer, go })
        : jsx(DeployerUnavailable, { loading: deployerQuery.loading, error: deployerQuery.error, go })
    } else if (view.name === 'deployer') {
      body = deployer
        ? jsx(deployerViews.DeployerPart, { view, data: deployer, go })
        : jsx(DeployerUnavailable, { loading: deployerQuery.loading, error: deployerQuery.error, go })
    } else if (view.name === 'path' && track) {
      body = jsx(PathView, { track, go })
    } else if (view.name === 'certificate' && track) {
      body = jsx(CertificateView, { track, go })
    } else if (view.name === 'mission') {
      const found = findMission(data, view.id)
      body = found.mission
        ? jsx(MissionView, { mission: found.mission, track: found.track, go, onChanged: () => query.refetch(), changes: data.changes || [], focus: view.focus })
        : jsx(MapView, { data, go, deployer })
    } else if (view.name === 'review') {
      body = jsx(ReviewView, { practice: view.practice, go })
    } else if (view.name === 'placement' && track) {
      body = jsx(PlacementView, { trackId: track.id, track, go })
    } else {
      body = jsx(MapView, { data, go, deployer })
    }
  }

  return jsxs('div', { className: 'fa-root', style: { height: '100%', minHeight: 0, display: 'grid', gridTemplateRows: 'auto 1fr' }, children: [
    query.stale ? jsx('div', { className: 'hk', style: { padding: '8px 24px 0' }, children: jsx(StaleNotice, { error: query.error, updatedAt: query.updatedAt, onRetry: query.refetch }) }) : jsx('span', {}),
    jsx('div', { style: { minHeight: 0 }, children: body }, `${view.name}:${view.id || ''}`),
  ] })
}

/* -------------------------------------------------------------- chrome ----- */

function StatusChip() {
  const query = usePassport()
  const track = query.data?.tracks?.find(t => t.id === query.data?.goal_track)
  const due = query.data?.reviews?.due_count || 0
  const label = (track ? `Field Academy · ${track.name} ${track.verified_missions} of ${track.missions.length}` : 'Field Academy') + (due ? ` · ${plural(due, 'review', 'reviews')} due` : '')
  return jsxs('button', { type: 'button', className: 'hk fa-chip', onClick: () => host.navigate(ROUTE), children: [
    track ? jsx(Ring, { value: track.missions.length ? track.verified_missions / track.missions.length : 0, size: 14, stroke: 2, tone: 'info' }) : null,
    label,
  ] })
}

function PracticeOffer({ attrs }) {
  const raw = typeof attrs?.mission === 'string' ? attrs.mission.trim() : ''
  const query = usePassport()
  if (!MISSION_ID_RE.test(raw)) return null
  const { mission } = findMission(query.data, raw)
  if (!mission) return null
  return jsx('div', { className: 'hk fa-offer', children: jsxs(Card, { tone: 'info', children: [
    jsx('p', { className: 'hk-eyebrow', children: 'Try this next' }, 'e'),
    jsx('p', { className: 'hk-h3', children: mission.title }, 't'),
    jsx('p', { children: mission.promise }, 'p'),
    jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: () => requestMission(raw), children: 'Open this mission' }) }, 'a'),
  ] }) })
}

export default {
  id: 'field-academy',
  name: 'Field Academy',
  description: 'Learn Hermes along four paths, Beginner to Advanced, then a capstone on your own problem, with checks on real work, spaced review and a Field Record you keep for each path.',
  defaultEnabled: true,
  register(ctx) {
    api = ctx
    registerPage(ctx, {
      id: 'field-academy', route: ROUTE, label: 'Field Academy', codicon: 'mortar-board', css: CSS + FIELD_CSS + BANNER_CSS + DEPLOYER_CSS + PROSE_CSS,
      render: () => jsx(Page, {}),
      status: { side: 'right', order: 118, render: () => jsx(StatusChip, {}) },
      palette: [{
        id: 'field-academy.open',
        label: 'Field Academy',
        detail: 'Learn Hermes step by step and build your own Field Record',
        keywords: ['learn', 'field record', 'training', 'hermes', 'academy', 'path'],
        run: () => host.navigate(ROUTE),
      }],
      keybinds: [{ id: 'field-academy.open', label: 'Field Academy: open your paths', run: () => host.navigate(ROUTE) }],
      extra: [
        { id: 'practice', area: TRANSCRIPT_DIRECTIVE_AREA, data: { name: DIRECTIVE, render: ({ attrs }) => jsx(PracticeOffer, { attrs }) } },
      ],
    })
  },
}
