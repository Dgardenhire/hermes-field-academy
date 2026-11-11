// Renders desktop/plugin.js in a Hermes-like frame, with a fake ctx backed by
// fixtures.json (real backend answers, from make_fixtures.py). URL parameters:
//
//   state   fresh | progress | ready | issued | reviews | misses | placement | offline | loading   (default fresh)
//   click   text of a button to click after load; repeat for a sequence,
//           e.g. click=Operator&click=Find where Hermes is running.
//           click=@autopick chooses the first option of every question.
//   check   pass | miss: the answer Check my work gets for a live check
//   review  open | submitted | graded: which review session /review/start returns
//   theme   dark | light                                 (default dark)
//   scroll  text of an element to scroll to the top before the screenshot

import { createRoot } from 'react-dom/client'
import { jsx } from 'react/jsx-runtime'

const params = new URLSearchParams(location.search)
const state = params.get('state') || 'fresh'
document.documentElement.dataset.theme = params.get('theme') === 'light' ? 'light' : 'dark'
// accent=red|green tries the page under a user's own accent color, as Hermes's Appearance settings allow.
const ACCENTS = { red: { dark: '#e5534b', light: '#c62f2f' }, green: { dark: '#3fb27f', light: '#17804f' } }
const accent = ACCENTS[params.get('accent')]
if (accent) {
  const value = accent[document.documentElement.dataset.theme]
  for (const name of ['--ui-accent', '--dt-primary']) document.documentElement.style.setProperty(name, value)
  document.documentElement.style.setProperty('--ui-row-active-background', `color-mix(in srgb, ${value} 14%, transparent)`)
}

const fixtures = await fetch('./fixtures.json').then(r => r.json())
// Loop 2 desk states (d_*): the real backend's attempt views and the Field guide, replay and grade answers from one
// real-model run (desk_real.json: claude -p --model sonnet standing in for Hermes's model, Lane A). See desk.js below.
const desk = state.startsWith('d_') ? await import('./desk_states.js').then(m => m.deskState(state, fixtures)) : null
const data = desk ? desk.data : fixtures.states[state] || fixtures.states.fresh
const pass = params.get('check') !== 'miss'
const reviewMode = params.get('review') || 'open'
window.__harness = {
  rpc: {
    'setup.runtime_check': { home: '~/.hermes' },
    'session.list': {
      sessions: pass
        ? [{ id: 's1', title: '[FA-DESKTOP] Walk me through one small task', created_at: '2026-10-02T10:00:00Z' }, { id: 's2', title: 'Weekly notes' }]
        : [{ id: 's2', title: 'Weekly notes' }],
    },
    'skills.manage': { skills: pass ? [{ name: 'academy-weekly-status' }, { name: 'github' }] : [{ name: 'github' }] },
    'cron.manage': {
      jobs: pass
        ? [{ name: 'academy-friday-summary', schedule: '0 8 * * 5', prompt: 'Work in the projects folder. Read the notes from this week. Write a summary of no more than ten bullet points. Send it to me in a message. If something fails, tell me which note could not be read.' }]
        : [{ name: 'morning-news' }],
    },
    // Shapes as Hermes 0.22 answers them (tui_gateway/methods_tools.py): tools.list groups by toolset,
    // agents.list lists background processes, mcp.catalog lists servers Hermes can add.
    'tools.list': { toolsets: [
      { name: 'terminal', description: 'Shell commands', tool_count: 2, enabled: true, tools: ['terminal', 'process'] },
      { name: 'browser', description: 'Web pages', tool_count: 2, enabled: true, tools: ['browser_navigate', 'browser_snapshot'] },
    ] },
    'agents.list': { processes: [] },
    'mcp.catalog': { servers: [{ name: 'github', description: 'GitHub', installed: true, enabled: true, requires: [], transport: 'stdio' }, { name: 'notion', description: 'Notion', installed: false, enabled: false, requires: [], transport: 'http' }] },
    'toolsets.list': { toolsets: [{ name: 'core' }] },
  },
}

const pause = ms => new Promise(resolve => setTimeout(resolve, ms))

function reviewSession() {
  if (reviewMode === 'graded') return data.review_graded
  if (reviewMode === 'submitted') return data.review_submitted
  return data.review_open
}

const aiSettings = { ai_help: true, practice_offer: false }

async function rest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  await pause(40)
  if (state === 'offline') throw new Error('404: {"detail":"Not Found"}')
  if (state === 'loading') return new Promise(() => {})
  if (desk) {
    const answer = await desk.rest(method, path, options.body || {})
    if (answer !== undefined) return answer
  }
  if (path === '/settings/ai') {
    for (const name of ['ai_help', 'practice_offer']) if (method === 'POST' && typeof options.body?.[name] === 'boolean') aiSettings[name] = options.body[name]
    return { ...aiSettings }
  }
  if (method === 'GET' && path === '/passport') return data.passport
  if (method === 'POST' && path.startsWith('/gate/')) {
    if (options.body?.outcome) {
      // The real backend adds the hint ladder to a miss; this stand-in builds a first-miss version of it.
      const outcome = { ...options.body.outcome }
      if (!outcome.passed && !outcome.feedback) {
        const missing = (outcome.missing || []).map(item => ({ id: item.id, what: item.what }))
        outcome.feedback = { level: 1, misses: 1, retry: true, missing, focus: missing[0]?.id || '', example: '',
          hint: 'Open Gateways in Settings and read the profile name exactly as it appears. Spelling counts.',
          headline: `${missing.length} thing${missing.length === 1 ? ' is' : 's are'} missing. Start with the first one, then check again.` }
      }
      return { outcome }
    }
    return { outcome: data.gate_outcome || { passed: false, title: 'No file at that path', detail: 'Nothing readable there.', facts: [] } }
  }
  if (method === 'POST' && path.startsWith('/complete/')) {
    const id = path.split('/')[2]
    return { ok: true, problems: [], attempts: 0, can_show: false, model: (data.models || {})[id] || {}, yours: options.body?.answers || {} }
  }
  if (method === 'POST' && path === '/review/start') return reviewSession()
  if (method === 'GET' && path.startsWith('/review/')) return reviewSession()
  if (method === 'POST' && /^\/review\/[^/]+\/submit$/.test(path)) return { session_id: 'x', prompt: 'Grade a Field Academy review.' }
  if (method === 'GET' && path.startsWith('/placement/')) return data.placement
  if (method === 'POST' && /^\/placement\/[a-z]+\/apply$/.test(path)) return data.placement_applied
  if (method === 'POST' && /^\/placement\/[a-z]+$/.test(path)) return data.placement_outcome
  // The Deployer tier: the snapshot is real backend output; a button press gets a real outcome the recipe captured.
  if (method === 'GET' && path === '/deployer') return data.deployer
  if (method === 'POST' && path.startsWith('/deployer/')) {
    const dp = data.deployer
    if (/^\/deployer\/lab\/[^/]+\/check$/.test(path)) {
      return { outcome: data.lab_outcome || { passed: false, title: 'Not fixed yet', detail: '1 thing is still missing.', facts: [], missing: [] }, lab: dp.labs[0] }
    }
    if (path === '/deployer/deploy/check') return { outcome: data.deploy_check_outcome, deploy: dp.deploy }
    if (path === '/deployer/brief/check') {
      return { passed: false, awaiting_score: true, title: 'The checks on the document are met', detail: 'Every section is there and every number fits. Now your own Hermes scores the parts a check cannot judge.', facts: [], missing: [], prompt: 'Grade a Field Academy client proposal.' }
    }
    return {}
  }
  // Foundations: every answer is the real backend's, captured at the fixture's state (foundations_fixtures.py).
  if (path === '/foundations' || path.startsWith('/foundations/')) {
    const fd = data.foundations
    if (!fd) throw new Error('404: {"detail":"Not Found"}')
    if (method === 'GET' && path === '/foundations') return fd.snapshot
    if (path.startsWith('/foundations/a/')) return (fd.part_a || {})[path.split('/').pop()] || {}
    if (method === 'GET' && path.startsWith('/foundations/mission/')) return fd.mission
    if (method === 'GET' && path === '/foundations/practice') return fd.practice
    if (method === 'GET' && /^\/foundations\/practice\/[^/]+\/memory$/.test(path)) return fd.memory
    if (method === 'GET' && /^\/foundations\/practice\/[^/]+\/folder$/.test(path)) return fd.folder || { state: 'no_chat' }
    // Missions 7 to 11 (harness/foundations_fixtures_b.py).
    if (/^\/foundations\/practice\/[^/]+\/connector-text$/.test(path)) return fd.connector_text || { ok: false, why: 'Not in this state.' }
    if (/^\/foundations\/practice\/[^/]+\/jobs(-made)?$/.test(path)) return fd.jobs || { jobs: [], made: [] }
    if (/^\/foundations\/practice\/[^/]+\/ops$/.test(path)) return fd.ops || {}
    if (/^\/foundations\/practice\/[^/]+\/baseline$/.test(path)) return fd.baseline || { ready: false }
    if (/^\/foundations\/attempt\/[^/]+\/watch$/.test(path)) return fd.watch || { ready: false }
    if (path === '/foundations/record' || path === '/foundations/record/preview') return fd.field_record
    if (path === '/foundations/record/issue') return fd.issued || {}
    if (path === '/foundations/record/save') return (fd.issued || {})
    if (path.endsWith('/record/preview') || (method === 'GET' && path.endsWith('/record'))) return fd.record
    if (method === 'POST' && path === '/foundations/practice/plan') return { name: 'academy-practice', request: { method: 'profiles.create', params: { name: 'academy-practice' } } }
    if (method === 'POST' && path.startsWith('/foundations/practice/')) return (fd.practice.practice || [])[0] || {}
    if (method === 'POST' && path.endsWith('/explain')) return { prompt: 'Grade a Field Academy Foundations answer.' }
    return fd.view
  }
  // Loop 2 routes in the older fixture states: the guide and the replay answer as the real backend does outside a hunt.
  if (method === 'GET' && path.startsWith('/guide/')) return { enabled: true, off_reason: null, off_words: '', step: '', ladder: { nudge: { state: 'not_started', text: '' }, where: { available: false, text: '' }, reveal: { available: false } }, explain: [], pins: [], starters: [], help: { words: '', used: [] }, do_it_with_me: null }
  if (method === 'GET' && path.startsWith('/replay/')) return { state: 'not_ready', words: 'Your replay opens on Compare, once the first check has run.', events: [], lanes: [], bracket: null }
  if (method === 'POST' && /^\/certificate\/[a-z]+\/save$/.test(path)) return fixtures.states.issued.saved
  if (method === 'POST' && /^\/certificate\/[a-z]+$/.test(path)) return fixtures.states.issued.certificate
  if (method === 'POST') return {}
  throw new Error('404: {"detail":"Not Found"}')
}

const contributions = []
const ctx = {
  rest,
  registerMany(list) { contributions.push(...list); return () => {} },
  storage: { get: (_k, fallback) => fallback, set: () => {} },
  os: { openExternal: url => console.log('open', url), writeClipboard: async () => {} },
}

const plugin = (await import('../desktop/plugin.js')).default
plugin.register(ctx)
const page = contributions.find(item => item.id === 'page')
createRoot(document.getElementById('app')).render(jsx(page.render, {}))

async function waitFor(fn, ms = 4000) {
  const start = performance.now()
  while (performance.now() - start < ms) {
    const found = fn()
    if (found) return found
    await pause(50)
  }
  return null
}

function clickable(text) {
  const nodes = [...document.querySelectorAll('button, summary')]
  return nodes.find(node => node.textContent.trim() === text) || nodes.find(node => node.getAttribute('aria-label') === text) || nodes.find(node => node.textContent.includes(text))
}

for (const text of params.getAll('click')) {
  if (text === '@autopick') {
    await waitFor(() => document.querySelector('fieldset input[type=radio]'))
    for (const group of document.querySelectorAll('fieldset')) group.querySelector('input[type=radio]')?.click()
    await pause(300)
    continue
  }
  const target = await waitFor(() => clickable(text))
  if (!target) {
    document.body.dataset.harnessError = `no button: ${text}`
    break
  }
  target.click()
  await pause(500)
}

const scrollTo = params.get('scroll')
if (scrollTo) {
  const target = await waitFor(() => [...document.querySelectorAll('h1, h2, h3, p, strong, legend, span')].find(n => n.textContent.includes(scrollTo)))
  if (target) {
    const root = document.querySelector('.hk-page') || document.querySelector('.fa-root')
    root.scrollTop = target.getBoundingClientRect().top - root.getBoundingClientRect().top + root.scrollTop - 24
  }
}
document.body.dataset.harnessDone = '1'

// audit=1: after the clicks, list every piece of visible text under 12px, and every run of body text drawn in a
// color fainter than the page's own ink (text-primary). Written into the page so `chrome --dump-dom` can read it.
if (params.get('audit')) {
  await pause(800)
  const rgba = value => (value.match(/[\d.]+/g) || []).map(Number)
  const lum = ([r, g, b]) => [r, g, b].map(c => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 })
    .reduce((sum, c, i) => sum + c * [0.2126, 0.7152, 0.0722][i], 0)
  const backdrop = node => {
    for (let n = node; n; n = n.parentElement) {
      const c = rgba(getComputedStyle(n).backgroundColor)
      if (c.length >= 3 && (c[3] === undefined || c[3] > 0.5)) return c
    }
    return rgba(getComputedStyle(document.body).backgroundColor)
  }
  const blend = (fg, bg) => { const a = fg[3] === undefined ? 1 : fg[3]; return [0, 1, 2].map(i => fg[i] * a + bg[i] * (1 - a)) }
  const opacity = node => { let o = 1; for (let n = node; n; n = n.parentElement) o *= Number(getComputedStyle(n).opacity); return o }
  const ink = rgba(getComputedStyle(document.documentElement).getPropertyValue('--ui-text-primary') ? (() => {
    const probe = document.createElement('span'); probe.style.color = 'var(--ui-text-primary)'; document.body.append(probe)
    const c = getComputedStyle(probe).color; probe.remove(); return c })() : 'rgb(0,0,0)')
  const small = [], faint = []
  const walker = document.createTreeWalker(document.querySelector('#app'), NodeFilter.SHOW_TEXT)
  const seen = new Set()
  for (let t = walker.nextNode(); t; t = walker.nextNode()) {
    const el = t.parentElement
    const text = t.textContent.replace(/\s+/g, ' ').trim()
    if (!el || !text || seen.has(el)) continue
    const box = el.getBoundingClientRect()
    if (!box.width || !box.height || getComputedStyle(el).visibility === 'hidden') continue
    seen.add(el)
    const style = getComputedStyle(el)
    const size = parseFloat(style.fontSize)
    const where = `${el.tagName.toLowerCase()}.${String(el.className).split(' ').slice(0, 2).join('.')}`
    if (size < 12 && !el.closest('svg')) small.push({ size, where, text: text.slice(0, 60) })
    const bg = backdrop(el)
    const fg = blend(rgba(style.color), bg)
    const o = opacity(el)
    const inkFg = blend(ink, bg)
    const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05) }
    const mine = ratio(fg, bg) * o, full = ratio(inkFg, bg)
    if (text.length >= 30 && mine < full * 0.8 && !el.closest('svg, input, textarea, button, code, pre')) faint.push({ where, contrast: +mine.toFixed(2), ink: +full.toFixed(2), text: text.slice(0, 70) })
  }
  const out = document.createElement('pre')
  out.id = 'harness-audit'
  out.textContent = JSON.stringify({ small, faint })
  document.body.append(out)
}

// deskcheck=a,b,c (Loop 2): the brief's "must be visible" lines as DOM checks, written into the page for
// `chrome --dump-dom` (harness/shoot_desk.py). Each check gives {ok, ...what it measured}.
if (params.get('deskcheck')) {
  await pause(900)
  const page = document.querySelector('.hk-page') || document.querySelector('#app')
  const shown = el => { if (!el) return false; const r = el.getBoundingClientRect(); const st = getComputedStyle(el); return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none' }
  const inView = el => { const r = el.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth }
  const buttons = [...document.querySelectorAll('#app button')].filter(shown)
  const btn = text => buttons.find(b => b.textContent.trim() === text)
  const texts = () => {
    const out = []
    const walker = document.createTreeWalker(document.querySelector('#app'), NodeFilter.SHOW_TEXT)
    for (let t = walker.nextNode(); t; t = walker.nextNode()) {
      const el = t.parentElement
      if (!el || !t.textContent.trim() || el.closest('svg, .hk-sr')) continue
      if (!shown(el)) continue
      out.push({ el, size: parseFloat(getComputedStyle(el).fontSize), text: t.textContent.trim().slice(0, 50) })
    }
    return out
  }
  const CHECKS = {
    ff_card: () => { const c = document.querySelector('.fa-ff'); const b = btn('Start the practice'); return { ok: Boolean(c && b && inView(b)), button_bottom: b ? Math.round(b.getBoundingClientRect().bottom) : null } },
    one_primary: () => { const p = buttons.filter(b => b.classList.contains('hb-btn') && b.dataset.variant === 'default'); return { ok: p.length === 1, primary: p.map(b => b.textContent.trim()) } },
    no_anyone: () => ({ ok: !/anyone can check/i.test(document.body.innerText) }),
    no_hscroll: () => ({ ok: page.scrollWidth <= page.clientWidth + 1 && document.documentElement.scrollWidth <= innerWidth + 1, scroll: page.scrollWidth, client: page.clientWidth }),
    min12: () => { const small = texts().filter(t => t.size < 12); return { ok: small.length === 0, small: small.slice(0, 5).map(t => `${t.size}px ${t.text}`) } },
    hero_largest: () => {
      const h = document.querySelector('[data-hero]')
      if (!h) return { ok: false, why: 'no hero line' }
      const size = parseFloat(getComputedStyle(h).fontSize)
      const max = Math.max(...texts().filter(t => !h.contains(t.el)).map(t => t.size))
      const wide = innerWidth >= 1280
      // Loop 2e: the headline is a plain sentence about the run, never a score slogan.
      const slogan = /\b\d+ of \d+\b|You said/.test(h.textContent)
      return { ok: size > max && (!wide || size >= 32) && inView(h) && !slogan, size, next_largest: max, text: h.textContent }
    },
    guide_visible: () => {
      const g = document.querySelector('.fa-guide')
      const tab = document.querySelector('.fa-guide-tab')
      if (innerWidth >= 1280) return { ok: shown(g) && g.getBoundingClientRect().right <= innerWidth && g.getBoundingClientRect().top < innerHeight, mode: 'column' }
      return { ok: shown(g) || shown(tab), mode: shown(g) ? 'column' : 'drawer tab' }
    },
    hunt_buttons: () => {
      const names = ['Give me a hint', 'Show me where to look', 'Show me the answer']
      const missing = names.filter(n => !btn(n))
      const drawer = innerWidth < 1280 && shown(document.querySelector('.fa-guide-tab'))
      return { ok: !missing.length || drawer, missing, mode: drawer ? 'drawer tab' : 'column' }
    },
    explain_button: () => ({ ok: Boolean(btn('Why did this miss?')) || Boolean(document.querySelector('.fa-explain')) }),
    // Before any hint or guess, Check doesn't say where to look: no Why did this miss?, no Go to Compare, no pointer
    // at the moment of the save, and no time stamp from the run in the main column.
    holds_back: () => {
      const main = document.querySelector('.fa-desk-work')?.textContent || ''
      const leaks = ['look again at the moment', '03:53', '3:53'].filter(w => main.includes(w))
      return { ok: !btn('Why did this miss?') && !btn('Go to Compare') && !leaks.length, leaks }  // Why did this miss? is on Compare now
    },
    nudge_text: () => { const s = [...document.querySelectorAll('.fa-guide-said')].filter(shown); return { ok: s.length > 0, text: s[0]?.textContent.slice(0, 160) } },
    explain_text: () => { const e = [...document.querySelectorAll('.fa-explain')].filter(shown); return { ok: e.length > 0, count: e.length } },
    grade: () => { const g = document.querySelector('.fa-grade-level'); return { ok: Boolean(g && /Level \d of 4/.test(g.textContent) && document.querySelector('.fa-grade mark')), level: g?.textContent } },
    said_once: () => {
      // The hero says what happened once: no callout under the strip and no second hero line repeating it.
      const call = document.querySelector('.fa-replay-call'), sub = document.querySelector('.fa-hero-sub[data-detail]')
      return { ok: !call && !sub, callout: Boolean(call), sub: sub ? sub.textContent : '' }
    },
    bracket: () => { const cards = document.querySelectorAll('.fa-ev[data-bracket]').length; return { ok: cards >= 2 && Boolean(document.querySelector('.fa-strip-bracket')), cards } },
    sample_tag: () => ({ ok: shown(document.querySelector('.fa-sample-tag')) && Boolean(btn('Start your own practice')) }),
    progress: () => { const n = document.querySelectorAll('.fa-progress li').length; return { ok: n >= 3, lines: n } },
    no_range: () => ({ ok: document.querySelectorAll('input[type=range]').length === 0 }),
    // The fix's commands sit in the main column (they work with AI help off), approve one save by id, never "all".
    diwm: () => { const main = document.querySelector('.fa-desk-work')?.textContent || ''; return { ok: /\/memory pending/.test(main) && /\/memory approve [0-9a-f]{8}/.test(main) && !/approve all/.test(document.body.textContent) } },
  }
  const out = {}
  for (const name of params.get('deskcheck').split(',').filter(Boolean)) {
    try { out[name] = CHECKS[name] ? CHECKS[name]() : { ok: false, why: 'unknown check' } } catch (e) { out[name] = { ok: false, why: String(e) } }
  }
  if (document.body.dataset.harnessError) out.harness = { ok: false, why: document.body.dataset.harnessError }
  const pre = document.createElement('pre')
  pre.id = 'harness-deskcheck'
  pre.hidden = true
  pre.textContent = JSON.stringify(out)
  document.body.append(pre)
}
