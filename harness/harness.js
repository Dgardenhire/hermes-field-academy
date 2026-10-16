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

const fixtures = await fetch('./fixtures.json').then(r => r.json())
const data = fixtures.states[state] || fixtures.states.fresh
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

async function rest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  await pause(40)
  if (state === 'offline') throw new Error('404: {"detail":"Not Found"}')
  if (state === 'loading') return new Promise(() => {})
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
  return nodes.find(node => node.textContent.trim() === text) || nodes.find(node => node.textContent.includes(text))
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
