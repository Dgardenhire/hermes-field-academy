// Field Academy Foundations: the mission loop screens. Built into desktop/plugin.js with the rest of the page.
//
// One mission runs as twelve steps (loop.js holds the order and the rules). The page sends Hermes's own gateway calls
// for the practice profile (profiles.create, deleteProfile, a new chat in that profile) and the backend does the rest:
// it plans the exact request, records what Hermes made, sets up the notes and problems before the first chat, reads
// the profile to check the work, and keeps the record. The app's active profile never changes: every practice chat
// opens with host.newChat(profile), one button per practice profile. Screens share the page's helpers through
// createFoundationsViews(ui), which plugin.js calls once, so nothing here imports from plugin.js.

import { useEffect, useRef, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'
import { Button, Codicon, Input, Textarea, host } from '@hermes/plugin-sdk'
import { Back, Card, Details, Facts, Notice, PageHeader, Pill, Section } from 'hermes-ui-kit'
import { createPartAViews } from './foundations_a.js'
import {
  STEPS, currentStep, freezeMissing, gapWords, gridRow, hiddenWords, guessKeyTerm, hostSupport, inlineSpans, labNoteProblems,
  latest, mdBlocks, revealBlocks, canReveal, memoryMath, percent, plantWords, plantPill, practiceRoute, practiceRows, predictionProblems, recallProblems, selfScoreProblems,
  shortHash, statusWord, stepStates, timerWords, calibrationTable, recordProblems, toggleWithhold, hoursWords, checkedByWords, showsMemory, recallLead, earlierPracticeLeft, canTestOut, missionWords,
} from './loop.js'
import { createFoundationsPanelsB } from './foundations_b.js'
import { createDeskViews } from './desk.js'
import { checkHeadline, fixChanges, heldCommands, heldSentence, homePreview, huntStarted, replayStatus, resumeWords, runHeadline, scoreSentence } from './desk_logic.js'
import { factWords, tryFormKind } from './loop_b.js'

export const FOUNDATIONS_CSS = `
.fa-rp{display:grid;gap:4px;padding-top:10px;border-top:1px solid var(--hk-stroke)}
.fa-rp-ev{margin:2px 0 0;padding-left:18px;display:grid;gap:3px;font-size:var(--hk-fs-sm)}
.fa-rp-ev code{font-size:var(--hk-fs-sm)}
.fa-rt{border-collapse:collapse;width:100%;font-size:var(--hk-fs-sm)}
.fa-rt th,.fa-rt td{padding:6px 10px 6px 0;text-align:left;vertical-align:top;border-top:1px solid color-mix(in srgb,var(--hk-ink) 10%,transparent)}
.fa-rt thead th{font-weight:600;border-top:0}
.fa-rt td[data-reached]{color:var(--fa-blaze-ink,var(--hk-ink));font-weight:600}
.fa-f-card{display:grid;gap:14px}
.fa-f-beats{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.fa-f-beat{display:grid;gap:6px;align-content:start;padding:12px 14px;border-radius:var(--hk-radius-sm);background:var(--hk-sunken);border-top:2px solid var(--fa-blaze,var(--hk-accent))}
.fa-f-beat p{margin:0}
.fa-f-beat .codicon{color:var(--fa-blaze-ink,var(--hk-accent))}
.fa-f-files{display:flex;flex-wrap:wrap;gap:6px}
.fa-f-beat .fa-f-code{background:var(--hk-surface);border:1px solid var(--hk-stroke)}
@container (max-width:760px){.fa-f-beats{grid-template-columns:minmax(0,1fr)}}
.fa-root .hk{--hk-fs-xs:12px}
.fa-f-md{display:grid;gap:10px;max-width:72ch;line-height:1.55}
.fa-f-md>p{margin:0}
.fa-f-md h3{margin:10px 0 0;font-size:18px}
.fa-f-md h4{margin:6px 0 0;font-size:15px}
.fa-f-md ul,.fa-f-md ol{margin:0;padding-left:22px;display:grid;gap:4px}
.fa-f-md blockquote{margin:0;padding:6px 12px;border-left:3px solid var(--fa-blaze,var(--hk-accent));background:var(--hk-sunken);border-radius:0 var(--hk-radius-sm) var(--hk-radius-sm) 0;display:grid;gap:6px}
.fa-f-md blockquote p{margin:0}
.fa-f-md code,.fa-f-code{font-family:var(--hk-mono);font-size:max(12px,.92em);padding:1px 4px;border-radius:4px;background:var(--hk-sunken);overflow-wrap:anywhere}
.fa-f-asof{display:inline-flex;align-items:center;padding:0 7px;margin:0 1px;border-radius:999px;border:1px solid var(--hk-stroke);font-size:12px;font-weight:600;white-space:nowrap}
.fa-f-checks{margin:0;padding:0;list-style:none;display:grid;gap:8px}
.fa-f-checks>li{display:grid;grid-template-columns:2rem minmax(0,1fr);gap:4px 10px;align-items:baseline}
.fa-f-checks b{font-weight:300;font-size:20px;line-height:1;font-variant-numeric:tabular-nums;color:var(--fa-blaze-ink,var(--hk-ink))}
.fa-f-predict{display:grid;gap:8px;padding:10px 12px;border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);background:var(--hk-surface)}
.fa-f-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.fa-f-toggle{display:inline-flex;border:1px solid var(--hk-stroke);border-radius:var(--hk-radius-sm);overflow:hidden}
.fa-f-toggle button{padding:4px 12px;border:0;background:var(--hk-surface);color:inherit;font:inherit;cursor:pointer}
.fa-f-toggle button[aria-pressed=true]{background:color-mix(in srgb,var(--fa-blaze,var(--hk-accent)) 22%,var(--hk-surface));font-weight:600}
.fa-f-toggle button:focus-visible{outline:2px solid var(--hk-accent);outline-offset:-2px}
.fa-f-range{display:inline-flex;gap:8px;align-items:center}
.fa-f-range input{width:10rem}
.fa-f-path{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-family:var(--hk-mono);font-size:var(--hk-fs-sm);padding:7px 9px;border-radius:var(--hk-radius-sm);background:var(--hk-sunken);overflow-wrap:anywhere}
.fa-f-path span{flex:1 1 20rem;min-width:0}
.fa-f-profiles{display:grid;gap:8px}
.fa-f-profile{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 12px;align-items:center;padding:10px 12px;border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);background:var(--hk-surface)}
.fa-f-profile .hk-actions{justify-content:flex-end}
.fa-f-mem{display:grid;gap:6px}
.fa-f-mem ol{margin:0;padding-left:22px;display:grid;gap:4px;font-family:var(--hk-mono);font-size:var(--hk-fs-sm)}
.fa-f-steps{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(min(100%,19rem),1fr))}
.fa-f-step{display:grid;gap:6px;padding:12px 14px;border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);background:var(--hk-surface)}
.fa-f-step dl{display:grid;grid-template-columns:6.5rem minmax(0,1fr);gap:4px 10px;margin:0}
.fa-f-step dt{text-transform:uppercase;font-size:12px;letter-spacing:.06em;font-weight:600}
.fa-f-step dd{margin:0}
.fa-f-result{display:grid;gap:6px;padding:10px 12px;border-radius:var(--hk-radius);border:1px solid var(--hk-stroke);background:var(--hk-surface)}
.fa-f-result[data-pass]{border-left:3px solid var(--hk-good,#3fb950)}
.fa-f-result[data-fail]{border-left:3px solid var(--fa-blaze,var(--hk-warn))}
.fa-f-excerpt{margin:0;font-family:var(--hk-mono);font-size:var(--hk-fs-sm);white-space:pre-wrap;overflow-wrap:anywhere;padding:7px 9px;border-radius:var(--hk-radius-sm);background:var(--hk-sunken)}
.fa-f-grid{width:100%;border-collapse:collapse;font-size:var(--hk-fs-sm)}
.fa-f-grid th{text-align:left;padding:6px 8px 6px 0;border-bottom:1px solid var(--hk-stroke);text-transform:uppercase;font-size:12px;letter-spacing:.06em}
.fa-f-grid td{padding:8px 8px 8px 0;border-bottom:1px solid var(--hk-stroke);vertical-align:top}
.fa-f-grid tr[data-off] td:nth-child(3),.fa-f-grid tr[data-off] td:nth-child(4){font-weight:600}
.fa-f-plant{display:grid;gap:4px;padding:10px 12px;border-left:3px solid var(--fa-blaze,var(--hk-accent));background:var(--hk-sunken);border-radius:0 var(--hk-radius-sm) var(--hk-radius-sm) 0}
.fa-f-rubric{width:100%;border-collapse:collapse;font-size:var(--hk-fs-sm)}
.fa-f-rubric td{padding:6px 8px 6px 0;border-bottom:1px solid var(--hk-stroke);vertical-align:top}
.fa-f-rubric td:first-child{width:3rem;font-weight:300;font-size:18px}
.fa-f-rubric th{text-align:left;padding:6px 8px 6px 0;border-bottom:1px solid var(--hk-stroke);text-transform:uppercase;font-size:12px;letter-spacing:.06em}
.fa-f-timer{font-variant-numeric:tabular-nums;font-size:22px;font-weight:300}
.fa-f-evidence{display:grid;gap:8px;margin:0;padding:0;list-style:none}
.fa-f-evidence li{display:grid;gap:4px}
.fa-f-meta{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:var(--hk-fs-sm)}
.fa-f-withhold{display:inline-flex;gap:6px;align-items:center;font-size:var(--hk-fs-sm)}
.fa-f-cal{width:100%;border-collapse:collapse;font-size:var(--hk-fs-sm)}
.fa-f-cal th{text-align:left;padding:6px 10px 6px 0;border-bottom:1px solid var(--hk-stroke);text-transform:uppercase;font-size:12px;letter-spacing:.06em;vertical-align:bottom}
.fa-f-cal tbody th,.fa-f-grid tbody th{text-transform:none;letter-spacing:0;font-size:var(--hk-fs)}
.fa-f-cal td{padding:8px 10px 8px 0;border-bottom:1px solid var(--hk-stroke);vertical-align:top;font-variant-numeric:tabular-nums}
.fa-f-cal td.fa-f-num{font-size:18px;font-weight:300;width:7rem}
.fa-f-cal tbody th{text-align:left;padding:8px 10px 8px 0;border-bottom:1px solid var(--hk-stroke);font-variant-caps:normal;letter-spacing:0;font-weight:400;vertical-align:top}
.fa-f-cal tr[data-empty] td{color:var(--hk-ink-2,inherit)}
.fa-f-form{display:grid;gap:12px;max-width:72ch}
.fa-f-form label{display:grid;gap:4px;font-weight:600}
.fa-f-form label span{font-weight:400}
.fa-f-claims{margin:0;padding-left:22px;display:grid;gap:10px}
.fa-f-claims li{display:grid;gap:3px}
.fa-f-tag{font-size:var(--hk-fs-sm);font-style:italic}
.fa-f-qa{display:grid;gap:8px;padding:10px 12px;border:1px solid var(--hk-stroke);border-radius:var(--hk-radius);background:var(--hk-surface)}
.fa-f-qa label{display:block}
.fa-f-start{border-left:3px solid var(--fa-blaze,var(--hk-accent));padding-left:14px}
.fa-f-scroll{overflow-x:auto}
`

const NEW_PROFILE_TIMEOUT_MS = 120000 // Hermes seeds a new profile in a separate process; Cabinet uses the same wait

export function createFoundationsViews(ui) {
  const { Frame, Label, ctxRest, errorText, copyText, openFolder, sendInNewChat, plural, longDate } = ui
  // The map's first requests go out when the page opens and keep a copy for the next open (plugin.js, open fast).
  const loadFoundations = ui.loadFoundations || (() => ctxRest('/foundations'))
  const loadSample = ui.loadSample || (() => ctxRest('/replay/sample'))

  /* ------------------------------------------------------------- plumbing -- */

  const post = (path, body) => ctxRest(path, { method: 'POST', body: body || {} })
  const support = () => hostSupport(host)
  // Every gateway call aimed at a practice profile, through its local route when the app lists one (practiceRoute).
  const requestPractice = async (name, method, params) => {
    let routes = []
    try { routes = typeof host.profileRoutes === 'function' ? await host.profileRoutes() : [] } catch (e) { routes = [] }
    return host.requestProfile(practiceRoute(routes, name), method, params)
  }
  // Missions 7 to 11: the lab note built from each mission's fields, and the panels its page lists (lab.panels).
  const B = createFoundationsPanelsB(ui, { Markdown, PathLine, Problem, Problems, Next, post, support, requestPractice })
  // The Loop 2 desk: phase rail, Field guide column, Compare line and replay (desk.js).
  const D = createDeskViews({ ctxRest, post, errorText, copyText, openPracticeChat: name => openPracticeChat(name), draftInPractice: (name, text) => draftInPractice(name, text), Problem: props => Problem(props) })

  /** Run one action at a time, with its error shown under the button that started it. */
  function useAction(after) {
    const [busy, setBusy] = useState('')
    const [error, setError] = useState('')
    const run = async (name, call) => {
      if (busy) return null
      setBusy(name)
      setError('')
      try {
        const out = await call()
        if (after) await after(out)
        return out
      } catch (e) {
        setError(errorText(e))
        return null
      } finally {
        setBusy('')
      }
    }
    return { busy, error, setError, run }
  }

  function Problem({ text }) {
    return text ? jsx(Notice, { tone: 'warn', live: true, children: text }) : null
  }

  function Problems({ items }) {
    return items && items.length ? jsx(Notice, { tone: 'warn', live: true, children: items.length === 1 ? items[0]
      : jsx('ul', { className: 'fa-bullets', children: items.map(p => jsx('li', { children: p }, p)) }) }) : null
  }

  /** One line of lesson text: bold, italic, code and "As of Hermes" pills, with code allowed inside bold and italic. */
  function Inline({ text }) {
    return spansOut(inlineSpans(text))
  }

  function spansOut(spans) {
    return spans.map((span, i) => span.kind === 'strong' ? jsx('strong', { children: spansOut(span.children) }, i)
      : span.kind === 'em' ? jsx('em', { children: spansOut(span.children) }, i)
        : span.kind === 'code' ? jsx('code', { children: span.text }, i)
          : span.kind === 'asof' ? jsx('span', { className: 'fa-f-asof', title: 'Checked against the Hermes source when this lesson was built', children: span.text }, i)
            : span.text)
  }

  /** One "Check yourself" question: the learner writes an answer first, then the course's answer can be shown. The
   *  answer stays on this page only; nothing is saved or graded. */
  function Reveal({ question, answer, n }) {
    const [mine, setMine] = useState('')
    const [open, setOpen] = useState(false)
    const id = `fa-qa-${n}`
    return jsxs('div', { className: 'fa-f-qa', children: [
      jsx('label', { htmlFor: id, children: jsx('strong', { children: jsx(Inline, { text: question }) }) }),
      jsx(Textarea, { id, rows: 2, value: mine, placeholder: 'Your answer, before you look', onChange: e => setMine(e.target.value) }),
      open ? jsx('blockquote', { 'aria-live': 'polite', children: answer.map((t, j) => jsx('p', { children: jsx(Inline, { text: t }) }, j)) })
        : jsxs('div', { className: 'fa-f-row', children: [
          jsx(Button, { variant: 'secondary', disabled: !canReveal(mine), onClick: () => setOpen(true), children: 'Show the answer' }),
          canReveal(mine) ? null : jsx('span', { className: 'hk-small', children: 'Write yours first. It stays on this page.' }),
        ] }),
    ] })
  }

  /** Lesson Markdown, rendered from parsed blocks. No HTML is read from the text. */
  function Markdown({ text }) {
    const blocks = revealBlocks(mdBlocks(text))
    if (!blocks.length) return null
    return jsx('div', { className: 'fa-f-md', children: blocks.map((b, i) => {
      if (b.kind === 'qa') return jsx(Reveal, { question: b.question, answer: b.answer, n: i }, i)
      if (b.kind === 'h2') return jsx('h3', { children: jsx(Inline, { text: b.text }) }, i)
      if (b.kind === 'h3') return jsx('h4', { children: jsx(Inline, { text: b.text }) }, i)
      if (b.kind === 'ul' || b.kind === 'ol') return jsx(b.kind, { start: b.start, children: b.items.map((t, j) => jsx('li', { children: jsx(Inline, { text: t }) }, j)) }, i)
      if (b.kind === 'code') return jsx('pre', { className: 'fa-f-excerpt', children: b.text }, i)
      if (b.kind === 'quote') return jsx('blockquote', { children: b.items.map((t, j) => jsx('p', { children: jsx(Inline, { text: t }) }, j)) }, i)
      if (b.kind === 'table') {
        return jsx('table', { className: 'fa-table', children: [
          jsx('thead', { children: jsx('tr', { children: b.head.map((c, j) => jsx('th', { children: jsx(Inline, { text: c }) }, j)) }) }, 'h'),
          jsx('tbody', { children: b.rows.map((r, j) => jsx('tr', { children: r.map((c, k) => jsx('td', { children: jsx(Inline, { text: c }) }, k)) }, j)) }, 'b'),
        ] }, i)
      }
      return jsx('p', { children: jsx(Inline, { text: b.text }) }, i)
    }) })
  }

  function Toggle({ value, onChange, yes = 'Pass', no = 'Fail', label }) {
    return jsxs('span', { className: 'fa-f-toggle', role: 'group', 'aria-label': label, children: [
      jsx('button', { type: 'button', 'aria-pressed': value === true, onClick: () => onChange(true), children: yes }),
      jsx('button', { type: 'button', 'aria-pressed': value === false, onClick: () => onChange(false), children: no }),
    ] })
  }

  /** A path shown home-relative (shown), with Copy and Open using the real one. */
  function PathLine({ path, shown, label, folder = true }) {
    if (!path) return null
    return jsxs('div', { className: 'fa-f-path', 'aria-label': label, children: [
      jsx('span', { children: shown || path }),
      jsx(Button, { variant: 'secondary', onClick: () => copyText(path, 'Copied the path.'), children: 'Copy' }),
      folder ? jsx(Button, { variant: 'ghost', onClick: () => openFolder(path), children: 'Open folder' }) : null,
    ] })
  }

  /* --------------------------------------------------- the practice profile -- */

  /** Open a chat in a practice profile without switching the app's own profile. */
  function openPracticeChat(name) {
    if (!support().newChat) {
      host.notify({ kind: 'error', message: 'This Hermes app can\'t open a chat in another profile from here. Update Hermes Desktop.' })
      return
    }
    try {
      host.newChat(name)
    } catch (e) {
      host.notify({ kind: 'error', message: `Hermes couldn't open a chat in ${name}. Update Hermes Desktop, then try again.` })
    }
  }

  /** Open a practice chat and put text in its composer, not sent. Resolves false when this Hermes can't place a draft,
   *  so the caller copies the text instead. Never submits: the learner presses Enter. */
  async function draftInPractice(name, text) {
    if (!name || !text || !support().newChat) return false
    try { host.newChat(name) } catch (e) { return false }
    const composer = host.composer
    if (!composer || typeof composer.setDraft !== 'function') return false
    for (let tries = 0; tries < 24; tries++) {
      await new Promise(resolve => setTimeout(resolve, 125))
      try {
        const ok = await composer.setDraft(null, text)
        if (ok) return true
      } catch (e) { break }
    }
    return false
  }

  async function createOne(which, attemptId) {
    const planned = await post('/foundations/practice/plan', { which, attempt_id: attemptId })
    let result = null
    let failure = null
    try {
      const raw = await host.request(planned.request.method, planned.request.params, NEW_PROFILE_TIMEOUT_MS)
      result = raw && typeof raw === 'object' && 'result' in raw ? raw.result : raw
    } catch (e) {
      failure = e
    }
    if (failure && /already exists/i.test(String(failure?.message || failure))) throw failure
    try {
      // A reply can be lost while Hermes finishes making the profile: the backend records it only if it is new since
      // the plan and carries exactly the planned instructions.
      return await post('/foundations/practice/confirm', { name: planned.name, result: result && typeof result === 'object' ? result : null })
    } catch (e) {
      throw failure || e
    }
  }

  async function deleteOne(profile) {
    await post('/foundations/practice/remove', { name: profile.name, confirm: true })
    if (!support().deleteProfile) {
      throw new Error(`This Hermes app can't delete a profile from here. Delete ${profile.name} in Settings, Profiles, then press Check it's gone.`)
    }
    await host.deleteProfile(profile.name)
    return post('/foundations/practice/removed', { name: profile.name })
  }

  /* --------------------------------------------------------------- pieces -- */

  function StepFrame({ title, eyebrow, lead, children }) {
    return jsxs('div', { className: 'hk-stack', style: { gap: 14 }, children: [
      jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
        // A plain 'Step N' repeats the stepper above, so only a real label (the mission's level, a phase) shows.
        eyebrow && !/^Step \d+$/.test(String(eyebrow)) ? jsx(Label, { children: eyebrow }) : null,
        jsx('h2', { className: 'hk-h2', style: { margin: 0 }, children: title }),
        lead ? jsx('p', { className: 'hk-lead', style: { margin: 0 }, children: lead }) : null,
      ] }),
      children,
    ] })
  }

  function Next({ label = 'Next', onClick, busy, disabled }) {
    return jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: busy, disabled, onClick, children: label }) })
  }

  function StandardList({ checks }) {
    return jsx('ol', { className: 'fa-f-checks', children: checks.map((c, i) => jsxs('li', { children: [jsx('b', { children: i + 1 }), jsx('span', { children: c.text })] }, c.id)) })
  }

  /* -------------------------------------------------------------- 1 recall -- */

  function RecallStep({ mission, view, save, action, listing }) {
    const saved = latest(view, 'recall')
    const prompts = mission.recall?.prompts || []
    const seconds = mission.recall?.seconds || 180
    const [answers, setAnswers] = useState(() => saved?.answers || prompts.map(() => ''))
    const [left, setLeft] = useState(null)
    const started = useRef(0)
    useEffect(() => {
      if (left === null || left <= 0) return undefined
      const t = setTimeout(() => setLeft(Math.max(0, seconds - Math.round((Date.now() - started.current) / 1000))), 500)
      return () => clearTimeout(t)
    }, [left])
    const problems = recallProblems(answers, prompts)
    const [shown, setShown] = useState([])
    // Recall and the fresh-profile box speak to where the learner really is: earlier missions skipped, or no
    // practice profile left to replace (0.9 persona test).
    if (view.test_out?.on && !saved) {
      return jsx(StepFrame, { title: mission.labels?.recall || 'Recall', eyebrow: 'Step 1', children: [
        jsx(Notice, { tone: 'info', title: 'Skipped: you\'re testing out', children: 'A test-out skips Recall, and your record says so. Go on to your claim.' }, 'skip'),
      ] })
    }
    const skipped = recallLead(view.recall_from)
    const fresh = [mission.fresh_text, earlierPracticeLeft(listing, view.attempt) ? mission.fresh_replace : ''].filter(Boolean).join('\n\n')
    return jsx(StepFrame, { title: mission.labels?.recall || 'Recall', eyebrow: 'Step 1', lead: mission.recall?.lead, children: [
      skipped ? jsx(Notice, { tone: 'info', title: 'If you skipped ahead', children: skipped }, 'skipped') : null,
      fresh ? jsx(Notice, { tone: 'info', title: mission.labels?.fresh || 'A fresh practice profile', children: jsx(Markdown, { text: fresh }) }, 'fresh') : null,
      saved ? jsx(Notice, { tone: 'good', title: 'Saved', children: 'Your recall is kept with this attempt. It locks when you set up practice.' }, 'saved') : null,
      jsxs('div', { className: 'fa-f-row', children: [
        left === null
          ? jsx(Button, { variant: 'secondary', onClick: () => { started.current = Date.now(); setLeft(seconds) }, children: 'Start the three minutes' })
          : jsx('span', { className: 'fa-f-timer', role: 'timer', 'aria-live': 'off', children: left > 0 ? timerWords(left) : 'Time' }),
        jsx('span', { className: 'hk-small', children: 'No looking back. Write what comes to mind.' }),
      ] }, 'timer'),
      ...prompts.map((p, i) => jsxs('div', { className: 'fa-field', children: [
        jsx('label', { htmlFor: `fa-recall-${i}`, children: p }),
        jsx(Textarea, { id: `fa-recall-${i}`, rows: 3, value: answers[i] || '', onChange: e => setAnswers(answers.map((a, j) => (j === i ? e.target.value : a))) }),
      ] }, `p${i}`)),
      jsx(Problems, { items: shown }, 'problems'),
      jsx(Problem, { text: action.error }, 'error'),
      jsx(Next, { label: saved ? 'Save again' : 'Save my recall', busy: action.busy === 'recall', disabled: view.attempt.frozen_at,
        onClick: () => { setShown(problems); if (!problems.length) save('recall', 'recall', { answers, seconds: left === null ? 0 : seconds - left }) } }, 'go'),
    ] })
  }

  /* -------------------------------------------------------- 2 claim + std -- */

  function ClaimStep({ mission, view, act, action, reload }) {
    const level = view.attempt.level
    const course = mission.standard.map(c => ({ id: c.id, text: c.text }))
    const savedClaim = latest(view, 'claim')
    const savedStd = latest(view, 'standard')
    const [claim, setClaim] = useState(savedClaim?.text || mission.claim.text)
    const [checks, setChecks] = useState(savedStd?.checks || course)
    const editable = level !== 'beginner' && !view.attempt.frozen_at
    const keep = () => act('claim', async () => {
      await post(`/foundations/attempt/${view.attempt.id}/entry`, { kind: 'claim', body: { text: claim, author: claim === mission.claim.text ? 'course' : 'learner' } })
      await post(`/foundations/attempt/${view.attempt.id}/entry`, { kind: 'standard', body: { checks } })
    })
    return jsx(StepFrame, { title: mission.labels?.claim || 'Your claim', eyebrow: 'Step 2', children: [
      editable
        ? jsx(Textarea, { rows: 3, value: claim, onChange: e => setClaim(e.target.value), 'aria-label': 'Your claim' }, 'c')
        : jsx('blockquote', { className: 'fa-f-md', style: { margin: 0 }, children: jsx('div', { className: 'fa-f-md', children: jsx('p', { style: { margin: 0, padding: '6px 12px', borderLeft: '3px solid var(--fa-blaze)', background: 'var(--hk-sunken)' }, children: claim }) }) }, 'c'),
      jsx('h3', { className: 'hk-h3', style: { margin: 0 }, children: mission.labels?.standard || 'How you\'ll know' }, 'sh'),
      jsx('p', { style: { margin: 0 }, children: mission.standard_lead }, 'sl'),
      editable
        ? jsx('div', { className: 'hk-stack', children: checks.map((c, i) => jsx(Input, { value: c.text, 'aria-label': `Check ${i + 1}`,
          onChange: e => setChecks(checks.map(x => (x.id === c.id ? { ...x, text: e.target.value } : x))) }, c.id)) }, 'std')
        : jsx(StandardList, { checks }, 'std'),
      level === 'beginner' ? jsx('p', { className: 'hk-small', children: 'At Beginner the course writes these. From Intermediate you reword them, and at Advanced you write your own.' }, 'b') : null,
      view.standard_changes?.length ? jsx(Details, { label: `Changed after the start (${view.standard_changes.length})`, children: view.standard_changes.map(c => jsx('p', { children: `${longDate(c.created_at)}: ${c.why}` }, c.created_at)) }, 'changes') : null,
      jsx(Problem, { text: action.error }, 'error'),
      savedClaim && savedStd ? jsx(Notice, { tone: 'good', title: 'Saved', children: 'These lock when you set up practice. A change after that is recorded on your record with your reason.' }, 'saved')
        : jsx(Next, { label: 'Keep this claim and these checks', busy: action.busy === 'claim', onClick: keep }, 'go'),
    ] })
  }

  /* -------------------------------------------------------------- 3 guess -- */

  /** First Flight's guess: one question, one tap, then how sure you are. Kept as the attempt's prediction. */
  function FirstFlightGuess({ view, save, action }) {
    const ff = view.first_flight || {}
    const g = ff.guess || {}
    const saved = ff.guessed || latest(view, 'prediction')?.guess || null
    const [answer, setAnswer] = useState(saved?.answer || '')
    const [sure, setSure] = useState(saved?.confidence || '')
    const frozen = Boolean(view.attempt.frozen_at) || Boolean(saved)
    return jsxs('div', { className: 'fa-guess', children: [
      jsx('h3', { children: g.question || 'Where do you think Hermes will trip?' }, 'q'),
      jsx('div', { className: 'fa-choices', role: 'group', 'aria-label': 'Your guess', children: (g.answers || []).map(a => jsxs('button', { type: 'button', className: 'fa-choice', 'aria-pressed': answer === a.id, disabled: frozen,
        onClick: () => setAnswer(a.id), children: [jsx(Codicon, { name: answer === a.id ? 'pass-filled' : 'circle-large-outline', size: 16 }), a.label] }, a.id)) }, 'a'),
      jsxs('div', { className: 'fa-chips', role: 'group', 'aria-label': 'How sure you are', children: [
        jsx('strong', { children: 'How sure?' }, 'l'),
        ...(g.confidence || []).map(c => jsx('button', { type: 'button', className: 'fa-chip-btn', 'aria-pressed': sure === c.id, disabled: frozen, onClick: () => setSure(c.id), children: c.label }, c.id)),
      ] }, 'c'),
      jsx(Problem, { text: action.error }, 'e'),
      saved ? jsx(Notice, { tone: 'info', children: 'Locked. You\'ll see it beside your result.' }, 'locked')
        : jsx(Next, { label: 'Lock my guess', busy: action.busy === 'prediction', disabled: !answer || !sure, onClick: () => save('prediction', 'prediction', { guess: { answer, confidence: sure } }) }, 'go'),
    ] })
  }

  function PredictStep({ mission, view, save, action }) {
    if (view.first_flight?.on) return jsx(StepFrame, { title: 'Your guess', children: jsx(FirstFlightGuess, { view, save, action }) })
    const saved = latest(view, 'prediction')
    const ids = mission.standard.map(c => c.id)
    const [form, setForm] = useState(() => saved || { checks: Object.fromEntries(ids.map(id => [id, { expect_pass: undefined, confidence: 75 }])), where_wrong: '' })
    const [shown, setShown] = useState([])
    const set = (id, patch) => setForm({ ...form, checks: { ...form.checks, [id]: { ...form.checks[id], ...patch } } })
    const frozen = Boolean(view.attempt.frozen_at)
    return jsx(StepFrame, { title: mission.labels?.predict || 'Your guess', eyebrow: 'Step 3', lead: mission.predict?.lead, children: [
      ...mission.standard.map((c, i) => jsxs('div', { className: 'fa-f-predict', children: [
        jsx('span', { children: [jsx('strong', { children: `Check ${i + 1}. ` }, 'n'), c.text] }),
        jsxs('div', { className: 'fa-f-row', children: [
          jsx(Toggle, { label: `Check ${i + 1}: will it pass?`, value: form.checks[c.id]?.expect_pass, onChange: v => !frozen && set(c.id, { expect_pass: v }), yes: 'I\'ll pass', no: 'I\'ll miss' }),
          jsxs('span', { className: 'fa-chips', role: 'group', 'aria-label': `How sure, check ${i + 1}`, children: [
            jsx('span', { children: 'How sure?' }, 'l'),
            ...[[60, 'Not sure'], [75, 'Fairly sure'], [90, 'Sure']].map(([n, words]) => jsx('button', { type: 'button', className: 'fa-chip-btn', disabled: frozen,
              'aria-pressed': (form.checks[c.id]?.confidence ?? 75) === n, onClick: () => set(c.id, { confidence: n }), children: words }, n)),
          ] }),
        ] }),
      ] }, c.id)),
      jsxs('div', { className: 'fa-field', children: [
        jsx('label', { htmlFor: 'fa-where', children: 'Where do you think you\'ll slip?' }),
        jsx(Textarea, { id: 'fa-where', rows: 2, value: form.where_wrong, disabled: frozen, onChange: e => setForm({ ...form, where_wrong: e.target.value }) }),
      ] }, 'where'),
      mission.cost?.line ? jsx('p', { className: 'hk-small', children: mission.cost.line }, 'cost') : null,
      jsx(Problems, { items: shown }, 'p'),
      jsx(Problem, { text: action.error }, 'e'),
      frozen ? jsx(Notice, { tone: 'info', children: 'Locked when practice was set up. You\'ll see it beside your result.' }, 'locked')
        : jsx(Next, { label: saved ? 'Save my guess again' : 'Save my guess', busy: action.busy === 'prediction', onClick: () => {
          const problems = predictionProblems(form, ids)
          setShown(problems)
          if (!problems.length) save('prediction', 'prediction', form)
        } }, 'go'),
    ] })
  }

  /* --------------------------------------------------------- 4 practice + try -- */

  function MemoryFile({ name }) {
    const [data, setData] = useState(null)
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const load = async () => {
      setBusy(true)
      setError('')
      try {
        setData(await ctxRest(`/foundations/practice/${encodeURIComponent(name)}/memory`))
      } catch (e) {
        setError(errorText(e))
      } finally {
        setBusy(false)
      }
    }
    return jsxs('div', { className: 'fa-f-mem', children: [
      jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: busy, onClick: load, children: data ? 'Read it again' : 'Show memory file' }) }),
      jsx(Problem, { text: error }),
      data ? jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { className: 'hk-small', style: { margin: 0 }, children: `Read just now from ${data.name}, straight from the files on disk. Anything shaped like a key is hidden.` }),
        data.pending ? jsx(Notice, { tone: 'warn', children: `${plural(data.pending, 'save is', 'saves are')} waiting for approval and ${data.pending === 1 ? 'isn\'t' : 'aren\'t'} in the file yet. Type /memory pending in a practice chat to see ${data.pending === 1 ? 'it' : 'them'}.` }) : null,
        ...data.files.map(f => jsxs('div', { className: 'fa-f-mem', children: [
          jsxs('div', { className: 'fa-f-row', children: [jsx('strong', { children: f.file }), jsx('span', { className: 'hk-small', children: `${f.chars.toLocaleString()} of ${f.limit.toLocaleString()} characters, ${plural(f.entries.length, 'line', 'lines')}` })] }),
          f.entries.length ? jsx('ol', { children: f.entries.map((e, i) => jsx('li', { children: e }, i)) }) : jsx('p', { className: 'hk-small', style: { margin: 0 }, children: f.exists ? 'Empty.' : 'No file yet. Hermes makes it with the first save.' }),
          jsx(PathLine, { path: f.path, shown: f.path_shown, label: `${f.file} full path`, folder: false }),
        ] }, f.file)),
      ] }) : null,
    ] })
  }

  /** Did the first practice chat work in the practice folder? Read from the chat's own record. */
  function WorkingFolder({ name }) {
    const [data, setData] = useState(null)
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const load = async () => {
      setBusy(true)
      setError('')
      try {
        setData(await ctxRest(`/foundations/practice/${encodeURIComponent(name)}/folder`))
      } catch (e) {
        setError(errorText(e))
      } finally {
        setBusy(false)
      }
    }
    useEffect(() => { load() }, [name])
    const words = {
      pass: ['good', 'The practice chat works in the practice folder'],
      fail: ['warn', 'The practice chat works in another folder'],
      unknown: ['info', 'Hermes didn\'t record the chat\'s folder'],
      no_chat: ['idle', 'No practice chat yet'],
    }[data?.state] || ['idle', 'Working folder']
    return jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
      jsx(Notice, { tone: words[0] === 'idle' ? 'info' : words[0], title: words[1], action: jsx(Button, { variant: 'secondary', loading: busy, onClick: load, children: 'Check again' }),
        children: data?.state === 'no_chat' ? 'Open a practice chat, send one message, then check again.'
          : data?.state === 'pass' ? `It's in ${data.cwd}.`
            : data ? [data.cwd ? jsx('p', { style: { margin: 0 }, children: `It's in ${data.cwd}.` }, 'cwd') : null, data.fix ? jsx('p', { style: { margin: 0 }, children: data.fix }, 'fix') : null] : null }),
      jsx(Problem, { text: error }),
    ] })
  }

  function ProfileRow({ row, mainName, chat = true }) {
    const p = row.profile
    const name = p?.name || (row.which === 'b' ? 'academy-practice-b' : 'academy-practice')
    const usable = p && ['ready', 'in_use'].includes(p.status)
    return jsxs('div', { className: 'fa-f-profile', children: [
      jsxs('div', { className: 'hk-stack', style: { gap: 2 }, children: [
        jsxs('div', { className: 'fa-f-row', children: [jsx('strong', { children: name }), jsx(Pill, { tone: usable ? 'good' : 'idle', children: statusWord(p) })] }),
        jsx('span', { className: 'hk-small', children: row.which === 'a' ? 'This mission uses this profile.' : 'A second practice profile, kept for the course.' }),
      ] }),
      jsx('div', { className: 'hk-actions', children: usable && (chat || name !== mainName) ? jsx(Button, { variant: name === mainName ? 'primary' : 'secondary', onClick: () => openPracticeChat(name),
        children: name === mainName ? 'Open practice chat' : `Open a chat in ${name}` }) : null }),
    ] })
  }

  function SetupStep({ mission, view, listing, reloadAll }) {
    const action = useAction(reloadAll)
    const [confirming, setConfirming] = useState('')
    const rows = practiceRows(listing, view.lab.profiles)
    const live = listing.filter(p => ['ready', 'in_use', 'planned', 'removing'].includes(p.status))
    const mainRow = rows.find(r => r.which === 'a')?.profile
    const frozen = Boolean(view.attempt.frozen_at)
    const ready = stepStates(view, listing).find(s => s.id === 'setup').status === 'done'
    const later = view.lab.after_try?.needed || []
    const stale = live.some(p => p.set_up && p.name !== view.attempt.profile) || live.some(p => p.status === 'in_use' && !ready)
      || (!ready && live.some(p => later.includes(p.which)))
    const missing = freezeMissing(view)
    const has = support()
    // Progress lines while Hermes makes the practice profile (P13): each line starts when its part starts.
    const [progress, setProgress] = useState(null)
    const mark = key => setProgress(p => ({ ...(p || { at: Date.now() / 1000, marks: {} }), now: key, marks: { ...((p || {}).marks || {}), [key]: Date.now() / 1000 } }))
    const setUp = () => action.run('setup', async () => {
      setProgress({ at: Date.now() / 1000, now: 'make', marks: { make: Date.now() / 1000 } })
      if (!frozen) await post(`/foundations/attempt/${view.attempt.id}/lab/open`)
      const now = (await ctxRest('/foundations/practice')).practice || []
      for (const which of view.lab.profiles) {
        if (!now.some(p => p.which === which && ['ready', 'in_use'].includes(p.status))) await createOne(which, view.attempt.id)
      }
      mark('plant')
      await post('/foundations/practice/plant', { attempt_id: view.attempt.id })
      mark('ready')
    })
    const removeAll = then => action.run(then, async () => {
      for (const p of live) await deleteOne(p)
      if (then === 'reset') {
        for (const which of view.lab.profiles) await createOne(which, view.attempt.id)
        await post('/foundations/practice/plant', { attempt_id: view.attempt.id })
      }
      setConfirming('')
    })
    const request = mainRow?.request || null
    return jsx(StepFrame, { title: 'Practice', eyebrow: 'Step 4', lead: 'Field Academy makes a separate practice profile for this. Your own profiles are not changed.', children: [
      jsx(PracticeNote, { mission }, 'note'),
      !frozen && missing.length ? jsx(Notice, { tone: 'info', children: `Save ${missing.join(', ')} first. They lock when practice is set up.` }, 'missing') : null,
      !has.request ? jsx(Notice, { tone: 'warn', children: 'This Hermes app can\'t make a profile from here. Update Hermes Desktop.' }, 'old') : null,
      // Once practice is ready, the try below has the one Open practice chat button (0.9 persona test).
      action.busy === 'setup' ? null : jsx('div', { className: 'fa-f-profiles', children: rows.map(r => jsx(ProfileRow, { row: r, mainName: view.attempt.profile || 'academy-practice', chat: !ready }, r.which)) }, 'rows'),
      mainRow?.path ? jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [jsx('strong', { children: 'Where the practice profile lives' }), jsx(PathLine, { path: mainRow.path, shown: mainRow.path_shown, label: 'Practice profile full path' })] }, 'path') : null,
      jsx(Problem, { text: action.error }, 'err'),
      progress && (action.busy === 'setup' || !ready) ? jsx(SetupProgress, { progress, name: view.attempt.profile || 'academy-practice', busy: action.busy === 'setup' }, 'progress') : null,
      !ready ? jsxs('div', { className: 'hk-stack', children: [
        frozen ? null : jsx('p', { style: { margin: 0 }, children: view.first_flight?.on ? 'Your guess is saved as it is now.' : 'Setting up locks your recall, claim, checks and guess, so they can\'t change after you see how it goes.' }),
        stale ? jsx(Notice, { tone: 'warn', children: `A practice profile from an earlier mission or try is still there: ${live.map(p => p.name).join(', ')}. Delete it and start fresh?` }) : null,
        jsx('div', { className: 'hk-actions', children: stale
          ? (confirming === 'fresh'
            ? [jsx(Button, { key: 'yes', variant: 'destructive', loading: action.busy === 'reset', onClick: () => removeAll('reset'), children: 'Yes, delete it and start fresh' }),
              jsx(Button, { key: 'no', variant: 'ghost', onClick: () => setConfirming(''), children: 'Keep it for now' })]
            : jsx(Button, { onClick: () => setConfirming('fresh'), children: 'Start fresh' }))
          : jsx(Button, { loading: action.busy === 'setup', disabled: missing.length > 0 || !has.request, onClick: setUp, children: frozen ? 'Set up practice' : 'Lock my answers and set up practice' }) }),
        request ? jsx(Details, { label: 'The exact request Field Academy sends to Hermes', children: jsx('pre', { className: 'fa-pre', children: JSON.stringify(request, null, 2) }) }) : null,
      ] }, 'setup') : null,
      ready ? jsxs('div', { className: 'hk-stack', children: [
        mission.try_text ? jsx('h3', { className: 'hk-h3', style: { margin: 0 }, children: 'Try this first' }) : null,
        jsx(Markdown, { text: mission.try_text }),
        jsxs('div', { className: 'fa-f-row', children: [
          // The question goes into the practice chat's box, not sent: the learner presses Enter (P14).
          jsx(Button, { onClick: async () => {
            if (!mission.try_prompt) { openPracticeChat(view.attempt.profile); return }
            const placed = await draftInPractice(view.attempt.profile, mission.try_prompt)
            if (!placed) copyText(mission.try_prompt, 'Copied. Paste it in the practice chat and press Enter.')
          }, children: 'Open practice chat' }),
          mission.try_prompt ? jsx(Button, { variant: 'secondary', onClick: () => copyText(mission.try_prompt, 'Copied the question.'), children: 'Copy the question' }) : null,
        ] }),
        // The try asks for the practice folder's path, so it shows here too, with Copy (0.9 persona test).
        (mission.lab?.panels || []).includes('folder') ? jsx(B.FolderPanel, { name: view.attempt.profile }) : null,
        showsMemory(mission) ? jsx(MemoryFile, { name: view.attempt.profile }) : null,
        jsx(WorkingFolder, { name: view.attempt.profile }),
        jsx(TryNote, { mission, view, reloadAll }),
      ] }, 'try') : null,
      ready ? jsx(Details, { label: 'Reset or delete practice', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { style: { margin: 0 }, children: 'Reset deletes the practice profiles and makes fresh ones with the same setup. Delete removes them. Either way their chats and memory are gone, and your own profiles are never touched.' }),
        confirming ? jsxs('div', { className: 'fa-f-row', children: [
          jsx('span', { children: confirming === 'reset' ? 'Delete the practice profiles and make them again?' : 'Delete the practice profiles?' }),
          jsx(Button, { variant: 'destructive', loading: Boolean(action.busy), onClick: () => removeAll(confirming), children: confirming === 'reset' ? 'Yes, reset' : 'Yes, delete' }),
          jsx(Button, { variant: 'ghost', onClick: () => setConfirming(''), children: 'Keep them' }),
        ] }) : jsxs('div', { className: 'hk-actions', children: [
          jsx(Button, { variant: 'secondary', onClick: () => setConfirming('reset'), children: 'Reset practice' }),
          jsx(Button, { variant: 'ghost', onClick: () => setConfirming('delete'), children: 'Delete practice profiles' }),
        ] }),
        has.deleteProfile ? null : jsx('p', { className: 'hk-small', children: 'This Hermes app can\'t delete a profile from here. Delete them in Settings, Profiles, then come back.' }),
      ] }) }, 'manage') : null,
    ] })
  }

  function SetupProgress({ progress, name, busy }) {
    const [now, setNow] = useState(() => Date.now() / 1000)
    useEffect(() => {
      if (!busy) return undefined
      const t = setInterval(() => setNow(Date.now() / 1000), 500)
      return () => clearInterval(t)
    }, [busy])
    const lines = [['make', `Making ${name}`], ['plant', 'Writing the practice folder and planting one snag'], ['ready', 'Ready']]
    const order = lines.map(l => l[0])
    const reached = order.indexOf(progress.now)
    return jsx('ol', { className: 'fa-progress', 'aria-live': 'polite', 'aria-label': 'Setting up your practice Hermes', children: lines.map(([key, words], i) => {
      const state = i < reached || progress.now === 'ready' ? 'done' : i === reached ? 'now' : 'later'
      const started = progress.marks?.[key]
      const ended = progress.marks?.[order[i + 1]]
      const secs = started ? Math.max(0, Math.round((ended || now) - started)) : null
      return jsxs('li', { 'data-state': state, children: [
        state === 'done' ? jsx(Codicon, { name: 'pass-filled', size: 16 }) : state === 'now' ? jsx(Codicon, { name: 'loading', size: 16, className: 'codicon-modifier-spin' }) : jsx(Codicon, { name: 'circle-large-outline', size: 16 }),
        jsx('span', { children: words }),
        jsx('span', { children: secs === null || key === 'ready' ? '' : `${secs} s` }),
      ] }, key)
    }) })
  }

  /** The Practice step's own note, routed by tryFormKind so every mission asks its own questions (0.9 persona test). Before, a
   *  mission outside Part A fell back to mission 3's memory form and wrote its guess and token count into the record. */
  function TryNote({ mission, view, reloadAll }) {
    if (PA.owns(view.attempt.mission_id)) return jsx(PA.TryPanel, { view, reloadAll })
    const kind = tryFormKind(mission)
    if (kind === 'fields') return jsx(B.TryForm, { mission, view, reloadAll })
    if (kind !== 'memory') return null
    return jsx(MemoryTry, { view, reloadAll })
  }

  function MemoryTry({ view, reloadAll }) {
    const saved = latest(view, 'try_note')
    const [guess, setGuess] = useState(saved?.guess || '')
    const [tokens, setTokens] = useState(saved?.memory_tokens ?? '')
    const action = useAction(reloadAll)
    const math = memoryMath(tokens)
    return jsxs('div', { className: 'hk-stack', children: [
      jsxs('div', { className: 'fa-inputs', children: [
        jsxs('div', { className: 'fa-field', children: [jsx('label', { htmlFor: 'fa-guess', children: 'Your guess: how much does Hermes carry?' }),
          jsx(Input, { id: 'fa-guess', value: guess, placeholder: 'A paragraph, a page, ten pages', onChange: e => setGuess(e.target.value) })] }),
        jsxs('div', { className: 'fa-field', children: [jsx('label', { htmlFor: 'fa-tokens', children: 'Your Memory line, in tokens' }),
          jsx(Input, { id: 'fa-tokens', inputMode: 'numeric', value: String(tokens), placeholder: '260', onChange: e => setTokens(e.target.value.replace(/[^0-9]/g, '')) })] }),
      ] }),
      math ? jsx('p', { className: 'hk-small', style: { margin: 0 }, children: `Room left: ${math.full} − ${math.tokens} = ${math.room} tokens. That's about ${plural(math.notes, 'more one-line note', 'more one-line notes')}.` }) : null,
      jsx(Problem, { text: action.error }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: action.busy === 'try', disabled: !guess.trim(),
        onClick: () => action.run('try', () => post(`/foundations/attempt/${view.attempt.id}/entry`, { kind: 'try_note', body: { guess, memory_tokens: tokens } })),
        children: saved ? 'Save again' : 'Save my guess and number' }) }),
    ] })
  }

  /* ------------------------------------------------------- 5 idea, 6 expert -- */

  function IdeaStep({ mission, view, save, action }) {
    const read = view.entries.some(e => e.kind === 'read' && e.body.step === 'idea')
    return jsx(StepFrame, { title: 'The idea', eyebrow: 'Step 5', children: [
      jsx(Markdown, { text: mission.idea_text }, 'md'),
      jsx(Problem, { text: action.error }, 'e'),
      read ? jsx(Notice, { tone: 'good', children: 'Marked as read.' }, 'r') : jsx(Next, { label: 'I\'ve read it', busy: action.busy === 'idea', onClick: () => save('idea', 'read', { step: 'idea' }) }, 'go'),
    ] })
  }

  function ExpertStep({ mission, view, save, action }) {
    const read = view.entries.some(e => e.kind === 'read' && e.body.step === 'expert')
    return jsx(StepFrame, { title: 'Watch it done', eyebrow: 'Step 6', lead: mission.expert_lead, children: [
      mission.expert_note ? jsx('p', { className: 'hk-small', style: { margin: 0, fontStyle: 'italic' }, children: mission.expert_note }, 'note') : null,
      jsx('div', { className: 'fa-f-steps', children: mission.expert_steps.map((s, i) => jsxs('div', { className: 'fa-f-step', children: [
        jsx('strong', { children: `${i + 1}. ${s.title}` }),
        jsxs('dl', { children: [
          jsx('dt', { children: 'Did' }), jsx('dd', { children: jsx(Inline, { text: s.did }) }),
          jsx('dt', { children: 'Saw' }), jsx('dd', { children: jsx(Inline, { text: s.saw }) }),
          jsx('dt', { children: 'Noticed' }), jsx('dd', { children: jsx(Inline, { text: s.noticed }) }),
          jsx('dt', { children: 'Ruled out' }), jsx('dd', { children: jsx(Inline, { text: s.ruled_out }) }),
        ] }),
      ] }, i)) }, 'steps'),
      jsx(Problem, { text: action.error }, 'e'),
      read ? jsx(Notice, { tone: 'good', children: 'Marked as read.' }, 'r') : jsx(Next, { label: 'I\'ve read it', busy: action.busy === 'expert', onClick: () => save('expert', 'read', { step: 'expert' }) }, 'go'),
    ] })
  }

  // Missions 1, 2, 4, 5 and 6 bring their own notes and page pieces (foundations_a.js).
  const PA = createPartAViews({ Markdown, PathLine, Toggle, Problem, Problems, MemoryFile, openPracticeChat, post, ctxRest, copyText, useAction, latest })

  /* ------------------------------------------------------------ 7 your turn -- */

  function NoteForm({ view, save, action, transfer = false }) {
    if (PA.owns(view.attempt.mission_id)) return jsx(PA.NoteForm, { view, save, action, transfer })
    const saved = latest(view, 'lab_note', b => (transfer ? b.for === 'transfer' : b.for !== 'transfer'))
    const [form, setForm] = useState(() => saved || { fact: '', key_term: '', removed_ok: '', one_off: '', one_off_why: '' })
    const [shown, setShown] = useState([])
    const set = patch => setForm({ ...form, ...patch })
    return jsxs('div', { className: 'hk-stack', children: [
      jsxs('div', { className: 'fa-field', children: [
        jsx('label', { htmlFor: `fa-fact-${transfer}`, children: transfer ? 'The fact about you that you asked Hermes to save' : 'The fact you asked Hermes to save' }),
        jsx(Input, { id: `fa-fact-${transfer}`, value: form.fact, onChange: e => set({ fact: e.target.value, key_term: form.key_term || '' }),
          onBlur: () => { if (!form.key_term) set({ key_term: guessKeyTerm(form.fact) }) } }),
      ] }),
      jsxs('div', { className: 'fa-inputs', children: [
        jsxs('div', { className: 'fa-field', children: [jsx('label', { htmlFor: `fa-key-${transfer}`, children: 'Its key word' }),
          jsx(Input, { id: `fa-key-${transfer}`, value: form.key_term, onChange: e => set({ key_term: e.target.value }) }),
          jsx('span', { className: 'hk-small', children: 'The word a new chat would have to use, such as the software\'s name.' })] }),
      ] }),
      transfer ? jsxs('div', { className: 'hk-stack', children: [
        jsxs('div', { className: 'fa-field', children: [jsx('label', { htmlFor: 'fa-oneoff', children: 'The one-off detail you weighed up' }),
          jsx(Input, { id: 'fa-oneoff', value: form.one_off || '', placeholder: 'The printer quote came in at noon today', onChange: e => set({ one_off: e.target.value }) })] }),
        jsxs('div', { className: 'fa-f-row', children: [jsx('span', { children: 'Did it get a line?' }),
          jsx(Toggle, { label: 'Did the one-off detail get a line?', value: form.one_off_saved, onChange: v => set({ one_off_saved: v }), yes: 'I saved it', no: 'I left it out' })] }),
        jsxs('div', { className: 'fa-field', children: [jsx('label', { htmlFor: 'fa-oneoff-why', children: 'Why, in one sentence' }),
          jsx(Input, { id: 'fa-oneoff-why', value: form.one_off_why || '', onChange: e => set({ one_off_why: e.target.value }) })] }),
      ] }) : null,
      transfer ? null : jsxs('div', { className: 'fa-field', children: [
        jsx('label', { htmlFor: 'fa-removed', children: 'If Hermes cut a note to make room, which one, and why was that all right? (Optional)' }),
        jsx(Textarea, { id: 'fa-removed', rows: 2, value: form.removed_ok || '', onChange: e => set({ removed_ok: e.target.value }) }),
      ] }),
      jsx(Problems, { items: shown }),
      jsx(Problem, { text: action.error }),
      jsx(Next, { label: saved ? 'Save again' : 'Save what I did', busy: action.busy === `note-${transfer}`, onClick: () => {
        const problems = labNoteProblems(form, transfer)
        setShown(problems)
        if (problems.length) return
        const body = { fact: form.fact, key_term: form.key_term, for: transfer ? 'transfer' : 'first' }
        if (transfer) Object.assign(body, { one_off: form.one_off, one_off_saved: form.one_off_saved, one_off_why: form.one_off_why })
        if (!transfer && (form.removed_ok || '').trim()) body.removed_ok = form.removed_ok
        save(`note-${transfer}`, 'lab_note', body)
      } }),
    ] })
  }

  /** Mission 4: the second practice profile is made only now, after the try, so the try can't land in it. */
  function AfterTry({ view, listing, reloadAll }) {
    const run = useAction(reloadAll)
    const needed = view.lab.after_try?.needed || []
    const tried = latest(view, 'try_note') !== null
    const has = support()
    const go = () => run.run('after-try', async () => {
      const now = (await ctxRest('/foundations/practice')).practice || []
      for (const which of needed) {
        if (!now.some(p => p.which === which && ['ready', 'in_use'].includes(p.status))) await createOne(which, view.attempt.id)
      }
      await post(`/foundations/attempt/${view.attempt.id}/after-try`)
    })
    const rows = practiceRows(listing, needed)
    return jsx(StepFrame, { title: 'Your turn', eyebrow: 'Step 7', lead: 'One more practice profile first. Field Academy makes it now, after the try, so the try always lands in academy-practice.', children: [
      !tried ? jsx(Notice, { tone: 'info', children: 'Do the try in Practice and save its numbers first.' }, 'try') : null,
      jsx('p', { style: { margin: 0 }, children: 'Took the try\'s line back out of SOUL.md? Check 1 looks for it, so do that before you start.' }, 'line'),
      jsx('div', { className: 'fa-f-profiles', children: rows.map(r => jsx(ProfileRow, { row: r, mainName: view.attempt.profile || 'academy-practice' }, r.which)) }, 'rows'),
      !has.request ? jsx(Notice, { tone: 'warn', children: 'This Hermes app can\'t make a profile from here. Update Hermes Desktop.' }, 'old') : null,
      jsx(Problem, { text: run.error }, 'err'),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: run.busy === 'after-try', disabled: !tried || !has.request, onClick: go, children: 'Make the second practice profile' }) }, 'go'),
    ] })
  }

  /** What this mission's practice profile can do while its setup stands (mission.practice_note: missions 2, 7 and
   *  9), shown before the first chat on the Practice step and again on Your turn (0.9 persona test). */
  function PracticeNote({ mission }) {
    return mission.practice_note ? jsx(Notice, { tone: 'warn', title: 'Before your first practice chat', children: jsx(Markdown, { text: mission.practice_note }) }) : null
  }

  function LabStep({ mission, view, save, action, listing, reloadAll }) {
    if (view.lab.after_try && !view.lab.after_try.done) return jsx(AfterTry, { view, listing, reloadAll })
    return jsx(StepFrame, { title: 'Your turn', eyebrow: 'Step 7', children: [
      jsx(PracticeNote, { mission }, 'note'),
      view.protected_notes?.length ? jsx(Card, { tone: 'info', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx('strong', { children: 'Two notes this profile\'s owner can\'t lose' }),
        jsx('ul', { className: 'fa-bullets', children: view.protected_notes.map(n => jsx('li', { children: jsx('code', { className: 'fa-f-code', children: n }) }, n)) }),
      ] }) }, 'protected') : null,
      jsx(Markdown, { text: view.lab.body }, 'body'),
      jsxs('div', { className: 'fa-f-row', children: [
        jsx(Button, { onClick: () => openPracticeChat(view.attempt.profile), children: 'Open practice chat' }),
        jsx('span', { className: 'hk-small', children: 'Each press opens a brand-new chat in the practice profile. Your own profile stays as it is.' }),
      ] }, 'chat'),
      mission.lab?.panels ? jsx(B.LabPanels, { mission, view }, 'panels') : null,
      showsMemory(mission) ? jsx(MemoryFile, { name: view.attempt.profile }, 'mem') : null,
      jsx(WorkingFolder, { name: view.attempt.profile }, 'folder'),
      PA.owns(view.attempt.mission_id) ? jsx(PA.LabPanel, { view }, 'part-a') : null,
      jsx(Details, { label: 'What Field Academy checks', children: jsx(Markdown, { text: mission.lab?.checks_text }) }, 'checks'),
      mission.lab?.note_fields ? jsx(B.FieldNoteForm, { mission, view, save, action }, 'note') : jsx(NoteForm, { view, save, action }, 'note'),
    ] })
  }

  /* ------------------------------------------------------ 8 score yourself -- */

  function ScoreStep({ mission, view, save, action, goStep }) {
    const saved = latest(view, 'self_score')
    const ids = mission.standard.map(c => c.id)
    const [form, setForm] = useState(() => saved || { checks: {} })
    const [shown, setShown] = useState([])
    const closed = Boolean(view.runs?.first)
    const locked = closed || Boolean(saved)
    return jsx(StepFrame, { title: 'Did it work?', lead: locked ? '' : 'Say how you did on each check before you see any result.', children: [
      jsx('div', { className: 'fa-toggles', children: mission.standard.map((c, i) => jsxs('div', { className: 'fa-tog', children: [
        jsx('span', { children: [jsx('strong', { children: `${i + 1}. ` }, 'n'), c.text] }),
        jsxs('span', { className: 'fa-tog-pair', role: 'group', 'aria-label': `Check ${i + 1}: did you pass?`, children: [
          jsx('button', { type: 'button', 'aria-pressed': form.checks[c.id]?.pass === true, disabled: locked, onClick: () => setForm({ checks: { ...form.checks, [c.id]: { pass: true } } }), children: 'Passed' }),
          jsx('button', { type: 'button', 'aria-pressed': form.checks[c.id]?.pass === false, disabled: locked, onClick: () => setForm({ checks: { ...form.checks, [c.id]: { pass: false } } }), children: 'Missed' }),
        ] }),
      ] }, c.id)) }, 'toggles'),
      jsx(Problems, { items: shown }, 'p'),
      jsx(Problem, { text: action.error }, 'e'),
      locked ? jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
        jsx(Notice, { tone: 'info', children: closed ? 'Your answers are saved. The first check has run.' : 'Your answers are saved.' }),
        !closed && goStep ? jsx('div', { className: 'hk-actions', children: jsx(Button, { onClick: () => goStep('check'), children: 'Check my work' }) }) : null,
      ] }, 'locked')
        : jsx(Next, { label: 'Lock my score', busy: action.busy === 'self', onClick: () => {
          const problems = selfScoreProblems(form, ids)
          setShown(problems)
          if (!problems.length) save('self', 'self_score', form)
        } }, 'go'),
    ] })
  }

  /* --------------------------------------------------------------- 9 check -- */

  /** The record states times in UTC to the second; on screen they read as local times, like the rest of the page. */
  function localTimes(text) {
    return String(text ?? '').replace(/([A-Z][a-z]+ \d{1,2}, \d{4}), (\d{2}:\d{2}):\d{2} UTC/g, (all, day, hm) => {
      const when = new Date(`${day} ${hm} UTC`)
      return Number.isNaN(when.getTime()) ? all : when.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    })
  }

  /** A check run, the way Compare shows a run: one plain headline from the run itself, the checks that missed as rows
   *  with what Field Academy read, and the ones that passed folded into one line. */
  function Outcome({ run, mission, guide, attemptId, headline, hunted = true }) {
    if (!run) return null
    const hidden = run.hidden || { count: 0, passed: 0 }
    const checks = run.checks || []
    const missed = checks.filter(c => !c.passed)
    const passed = checks.filter(c => c.passed)
    const hiddenLeft = (hidden.count || 0) - (hidden.passed || 0)
    const when = run.at ? new Date(run.at) : null
    const clock = when && !Number.isNaN(when.getTime()) ? when.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : ''
    const line = headline || checkHeadline(run)
    // The headline already says each missed check's title, so its card leads with what Field Academy read instead.
    const said = c => !c.passed && line.includes(c.title)
    // A card the headline already covers shows only what was read (its facts), and with no facts it isn't shown: an
    // empty card holding only a button read as a bug (round 13; rounds 9 to 12: the cards restated the headline).
    const row = c => said(c) && !c.facts?.length ? null : jsxs('div', { className: 'fa-f-result', 'data-pass': c.passed ? '' : undefined, 'data-fail': c.passed ? undefined : '', children: [
      said(c) ? null : jsxs('div', { className: 'fa-f-row', children: [jsx(Codicon, { name: c.passed ? 'pass' : 'circle-large-outline', size: 16 }), jsx('strong', { children: c.title })] }),
      c.detail && c.detail !== c.title && !said(c) ? jsx('span', { children: c.detail }) : null,
      c.facts?.length ? jsx(Facts, { rows: c.facts.map(f => ({ label: f.label, value: localTimes(factWords(f, mission)) })) }) : null,
      c.checked_by && c.checked_by !== 'Field Academy read it' ? jsx('span', { className: 'hk-small', children: `Checked by: ${c.checked_by}` }) : null,
    ] }, c.id)
    return jsxs('div', { className: 'hk-stack', children: [
      jsxs('div', { className: 'fa-check-head', 'data-pass': run.passed ? '' : undefined, role: 'status', children: [
        jsx('p', { className: 'fa-check-line', children: line }),
        jsx('p', { children: `Field Academy read the practice profile's files${clock ? ` on ${clock}` : ''}.${hiddenLeft > 0 ? ` There is also a hidden check, and it hasn't passed.` : ''}` }),
      ] }),
      ...missed.map(row).filter(Boolean),
      passed.length ? (missed.length
        ? jsx(Details, { label: `Also checked and passed: ${passed.map(c => lowerFirstWord(c.title)).join('; ')}`, children: jsx('div', { className: 'hk-stack', children: passed.map(row) }) }, 'passed')
        : jsx('div', { className: 'hk-stack', children: passed.map(row) }, 'passed')) : null,
    ] })
  }

  function lowerFirstWord(t) {
    const s = String(t || '')
    return /^[A-Z][a-z]/.test(s) ? s.charAt(0).toLowerCase() + s.slice(1) : s
  }

  function Evidence({ items }) {
    if (!items || !items.length) return null
    return jsx(Details, { label: `The lines Field Academy read (${items.length})`, children: jsx('ul', { className: 'fa-f-evidence', children: items.map(e => jsxs('li', { children: [
      jsxs('div', { className: 'fa-f-meta', children: [jsx('span', { className: 'fa-f-code', children: e.rel_path }), jsx('span', { title: `SHA-256 ${e.sha256 || ''}`, children: 'As the check read it' })] }),
      jsx('pre', { className: 'fa-f-excerpt', children: e.excerpt }),
    ] }, e.id)) }) })
  }

  async function pageSample(profile) {
    if (!support().requestProfile || !profile) return null
    try {
      const out = await requestPractice(profile, 'session.list', {})
      const raw = out && typeof out === 'object' && 'result' in out ? out.result : out
      const list = Array.isArray(raw) ? raw : Array.isArray(raw?.sessions) ? raw.sessions : []
      return { source: 'session.list', sessions: list.length }
    } catch (e) {
      return null
    }
  }

  function ExplainPanel({ mission, view, reloadAll, gradeShown }) {
    const ex = view.explain || {}
    const [answer, setAnswer] = useState(ex.answer || gradeShown?.answer || '')
    const action = useAction(reloadAll)
    const send = (path, body) => action.run('explain', async () => {
      const out = await post(path, body)
      await sendInNewChat(out.prompt, 'A new chat is open in your own profile and the grading request is copied. Paste it and press Enter.')
      return out
    })
    const rubric = mission.explain?.rubric || {}
    const open = !ex.submitted || (ex.level && !ex.passed)
    return jsx(Section, { title: 'Explain it', children: jsxs('div', { className: 'hk-stack', children: [
      jsx('blockquote', { className: 'fa-f-md', style: { margin: 0 }, children: jsx('p', { style: { margin: 0, padding: '6px 12px', borderLeft: '3px solid var(--hk-accent)', background: 'var(--hk-sunken)' }, children: jsx(Inline, { text: mission.explain?.question || '' }) }) }),
      jsx(Details, { label: `What each level looks like. Level ${mission.explain?.pass_level || 3} passes.`, children: jsx('table', { className: 'fa-f-rubric', children: [
        jsx('thead', { children: jsxs('tr', { children: [jsx('th', { scope: 'col', children: 'Level' }), jsx('th', { scope: 'col', children: 'An answer at this level' })] }) }, 'h'),
        jsx('tbody', { children: [1, 2, 3, 4].map(n => jsxs('tr', { children: [jsx('td', { children: n }), jsx('td', { children: jsx(Inline, { text: rubric[n] || rubric[String(n)] || '' }) })] }, n)) }, 'b'),
      ] }) }),
      ex.level && !gradeShown ? jsx(Notice, { tone: ex.passed ? 'good' : 'warn', title: `Level ${ex.level} of 4${ex.passed ? '' : `. Level ${ex.pass_level} passes`}`, children: `${ex.feedback || ''}` }) : null,
      ex.waiting ? jsx(Notice, { tone: 'info', live: true, children: 'Waiting for your Hermes to give it a level in the chat that opened. This updates by itself.' }) : null,
      open ? jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
        jsx(Textarea, { id: 'fa-explain-answer', rows: 5, value: answer, onChange: e => setAnswer(e.target.value), 'aria-label': 'Your answer' }),
        jsx('span', { className: 'hk-small', children: `${answer.trim().length} characters. At least 120.` }),
      ] }) : null,
      open ? jsx(D.InlineGrade, { missionId: mission.id, attemptId: view.attempt.id, answer, initial: gradeShown }) : null,
      jsx(Problem, { text: action.error }),
      open || ex.waiting ? jsx(Details, { label: 'Score it in a chat instead', children: jsxs('div', { className: 'hk-actions', children: [
        open ? jsx(Button, { variant: 'secondary', loading: action.busy === 'explain', disabled: answer.trim().length < 120, onClick: () => send(`/foundations/attempt/${view.attempt.id}/explain`, { answer }), children: 'Open a grading chat' }) : null,
        ex.waiting ? jsx(Button, { variant: 'secondary', onClick: () => send(`/foundations/attempt/${view.attempt.id}/explain/resend`), children: 'Open the grading chat again' }) : null,
      ] }) }) : null,
    ] }) })
  }

  /** After a miss on the first check: the way to check again, right where the miss shows (0.9 persona test). The first result
   *  stays on the record; the re-check is the after-fix run, which needs the gap note from Compare first. */
  function RecheckPanel({ mission, view, reloadAll, goStep, hunted = true }) {
    const runner = useAction(reloadAll)
    const gap = latest(view, 'gap_note') !== null
    const after = view.runs?.after_fix
    const recheck = () => runner.run('after_fix', async () => {
      const sample = await B.sample(mission, view.attempt.profile)
      return post(`/foundations/attempt/${view.attempt.id}/check`, { phase: 'after_fix', ...(sample ? { sample } : {}) })
    })
    return jsx('section', { className: 'fa-next', 'aria-label': 'What to do next', children: jsxs('div', { className: 'hk-stack', children: [
      jsx('h3', { children: 'What to do next' }),
      // Before a hint, no sentence: the Field guide already says to look in the practice chat first (Nov 9 critics).
      gap || hunted ? jsx('p', { style: { margin: 0 }, children: gap
        ? 'Fix the problem in the practice chat, then check again here.'
        : 'When you think you know why, go to Compare to see your chat and Hermes\'s files side by side.' }) : null,
      jsx('div', { className: 'hk-actions', children: [
        jsx(Button, { key: 'chat', variant: 'secondary', onClick: () => openPracticeChat(view.attempt.profile), children: 'Open practice chat' }),
        gap ? jsx(Button, { key: 'run', loading: runner.busy === 'after_fix', onClick: recheck, children: 'Check my fix' })
          : goStep && hunted ? jsx(Button, { key: 'go', variant: 'secondary', onClick: () => goStep('compare'), children: 'Go to Compare' }) : null,
      ] }),
      jsx(Problem, { text: runner.error }),
      after ? jsx(Outcome, { run: after, mission }) : null,
      after && goStep ? jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: () => goStep('fix'), children: 'Go on to the transfer' }) }) : null,
    ] }) })
  }

  function CheckStep({ mission, view, reloadAll, goStep, guide, gradeShown }) {
    const action = useAction(reloadAll)
    const run = view.runs?.first
    return jsx(StepFrame, { title: run ? 'What Field Academy found' : 'Check', lead: run ? '' : 'Field Academy reads the practice profile\'s memory files, settings and chat records itself.', children: [
      run ? jsx(Outcome, { run, mission, guide, attemptId: view.attempt.id, hunted: huntStarted(guide?.view, view.explain) }, 'out') : jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: action.busy === 'check', onClick: () => action.run('check', async () => {
        const sample = (await B.sample(mission, view.attempt.profile)) || await pageSample(view.attempt.profile)
        return post(`/foundations/attempt/${view.attempt.id}/check`, { phase: 'first', ...(sample ? { sample } : {}) })
      }), children: 'Check my work' }) }, 'go'),
      jsx(Problem, { text: action.error }, 'e'),
      run && !run.passed ? jsx(RecheckPanel, { mission, view, reloadAll, goStep, hunted: huntStarted(guide?.view, view.explain) }, 'recheck') : null,
      run ? jsx(Evidence, { items: view.evidence }, 'ev') : null,
      run && mission.explain ? jsxs('details', { className: 'fa-explain-box', id: 'fa-explain-box', open: Boolean(gradeShown) || undefined, children: [
        jsx('summary', { children: 'Score my answer: explain it in your own words, and your model gives it a level' }),
        jsx(ExplainPanel, { mission, view, reloadAll, gradeShown }),
      ] }, 'explain') : null,
    ] })
  }

  /* -------------------------------------------------------------- 10 compare -- */

  /** The learner's guess from before the practice, in their own words or the First Flight answer they tapped. */
  function guessWords(view) {
    const p = latest(view, 'prediction')
    if (!p) return ''
    const ff = view.first_flight?.guess
    if (p.guess && ff) {
      const a = (ff.answers || []).find(x => x.id === p.guess.answer)
      const sure = { low: 'not sure', medium: 'fairly sure', high: 'sure' }[p.guess.confidence]
      return a ? `Before you started, you guessed “${a.label.replace(/[.\s]+$/, '')}”${sure ? `, and you were ${sure}` : ''}.` : ''
    }
    const w = String(p.where_wrong || '').trim()
    return w ? `Before you started, you guessed you might slip here: “${w}”` : ''
  }

  function CompareStep({ view, save, action, guide, sample, go, onReplayState }) {
    const replay = D.useReplay(view.attempt.id, 'compare', sample)
    const cmp = view.compare
    const savedGap = latest(view, 'gap_note')
    const [gap, setGap] = useState(savedGap?.text || '')
    if (!cmp) return jsx(StepFrame, { title: 'Compare', lead: 'Run the first check to see your score beside what Hermes did.' })
    const cal = cmp.calibration || {}
    const pins = guide?.view?.pins || []
    const head = runHeadline(replay.data, view.runs?.first?.checks)
    return jsxs('div', { className: 'hk-stack', style: { gap: 18 }, children: [
      jsx(D.CompareHero, { headline: head.headline, detail: head.detail, score: scoreSentence(cmp), guess: guessWords(view) }, 'hero'),
      replay.data ? jsx(D.Replay, { attemptId: view.attempt.id, pins, sample: sample || replay.data, onSample: go ? () => go({ name: 'sample' }) : null, onState: onReplayState }, 'replay')
        : replayStatus(replay).state === 'error'
          // A failed run request says so and offers Retry, never an endless loading line (Loop 3 live gate).
          ? jsx(Notice, { tone: 'warn', title: replayStatus(replay).title, action: jsx(Button, { variant: 'secondary', onClick: replay.retry, children: 'Retry' }), children: replayStatus(replay).words }, 'replay')
          : jsx('p', { children: replayStatus(replay).words }, 'replay'),
      jsx(Details, { label: 'See each check', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('div', { className: 'fa-f-scroll', children: jsx('table', { className: 'fa-f-grid', children: [
          jsx('thead', { children: jsx('tr', { children: ['Check', 'Your guess', 'Your score', 'Hermes shows'].map(h => jsx('th', { scope: 'col', children: h }, h)) }) }, 'h'),
          jsx('tbody', { children: cmp.grid.map((g, i) => {
            const r = gridRow(g)
            return jsxs('tr', { 'data-off': r.off ? '' : undefined, children: [
              jsx('td', { children: `${i + 1}. ${r.text}` }), jsx('td', { children: r.guess }), jsx('td', { children: r.mine }),
              jsx('td', { children: g.passed === null || g.passed === undefined ? 'Waits for Score my answer' : r.after ? `${r.check}, then ${r.after} after the fix` : r.check }),
            ] }, r.id)
          }) }, 'b'),
        ] }) }),
        jsx(Facts, { rows: [{ label: 'Guesses that matched', value: percent(cal.hit_rate) }] }),
      ] }) }, 'grid'),
      jsx(Details, { label: 'How we know', children: jsx('div', { className: 'hk-stack', children: cmp.plants.map(p => {
        const words = plantWords(p.kind)
        return jsxs('div', { className: 'fa-f-plant', children: [
          jsxs('div', { className: 'fa-f-row', children: [jsx('strong', { children: words.title }), jsx(Pill, { tone: p.caught ? 'good' : p.fired ? 'warn' : 'idle', children: plantPill(p) })] }),
          jsx('span', { children: words.what }),
          p.facts?.length ? jsx(Facts, { rows: p.facts.map(f => ({ label: f.label, value: f.value })) }) : null,
        ] }, p.kind)
      }) }) }, 'plants'),
      jsxs('div', { className: 'fa-field', children: [
        jsx('label', { htmlFor: 'fa-gap', children: 'In one line: what did Hermes do that you didn\'t expect?' }),
        jsx(Textarea, { id: 'fa-gap', rows: 3, value: gap, onChange: e => setGap(e.target.value) }),
      ] }, 'gap'),
      jsx(Problem, { text: action.error }, 'e'),
      jsx(Next, { label: savedGap ? 'Save my note again' : 'Save my note', busy: action.busy === 'gap', disabled: gap.trim().length < 10, onClick: () => save('gap', 'gap_note', { text: gap }) }, 'go'),
    ] })
  }

  /* ------------------------------------------------------ 11 fix + transfer -- */

  function FixStep({ mission, view, save, action, reloadAll }) {
    const runner = useAction(reloadAll)
    const savedFix = latest(view, 'fix_note')
    const [fix, setFix] = useState(savedFix?.text || '')
    const transferNote = latest(view, 'lab_note', b => b.for === 'transfer')
    const runPhase = phase => runner.run(phase, async () => {
      const sample = await B.sample(mission, view.attempt.profile)
      return post(`/foundations/attempt/${view.attempt.id}/check`, { phase, ...(sample ? { sample } : {}) })
    })
    const after = view.runs?.after_fix
    const changes = after?.passed ? fixChanges(view.runs?.first, after) : []
    // The real run: what Hermes is still holding, read from the replay (the files lane), so the step names the note.
    const replay = D.useReplay(view.attempt.id, 'compare')
    const held = ((replay.data && replay.data.state === 'ready' && replay.data.events) || []).find(e => e.kind === 'file:pending')
    // One plain sentence, never Hermes's raw "apply 1 op(s) to memory: ..." summary (Loop 3 live gate).
    const heldText = held ? heldSentence(held.text).sentence : ''
    const planted = (view.compare?.plants || []).find(p => p.fired) || (view.compare?.plants || [])[0]
    return jsx(StepFrame, { title: 'Fix it', children: [
      after?.passed ? jsxs('section', { className: 'fa-fixed', 'aria-label': 'What your fix changed', children: [
        jsx('p', { className: 'fa-check-line', children: 'Your fix worked.' }),
        ...changes.map(ch => jsxs('div', { className: 'fa-fixed-row', children: [
          jsxs('strong', { children: [jsx(Codicon, { name: 'pass', size: 16 }), ` ${ch.title}`] }),
          ch.was || ch.now ? jsxs('span', { children: [ch.was ? jsx('span', { className: 'fa-was', children: `Before: ${localTimes(ch.was)}` }) : null, ch.now ? jsx('span', { children: `Now: ${localTimes(ch.now)}` }) : null] }) : null,
        ] }, ch.id)),
      ] }, 'fixed') : jsxs('section', { className: 'fa-fixed', 'aria-label': 'What to fix', children: [
        // The action, not a third telling of Compare's headline (round 15).
        jsx('p', { className: 'fa-check-line', children: held ? 'Approve the one note Hermes is holding.' : planted ? `${plantWords(planted.kind).title}.` : 'Fix what the check found, in the practice chat.' }),
        held ? jsxs('div', { className: 'fa-replay-detail', children: [
          jsx('span', { className: 'hk-small', children: `In Hermes's files, ${held.path || 'the approval queue'}` }),
          jsx('p', { style: { margin: 0 }, children: heldText }),
        ] }) : null,
        held && heldCommands(held.path).length ? jsx('p', { style: { margin: 0 }, children: 'Type these two commands in the practice chat, then press Check my fix.' }) : jsx('p', { style: { margin: 0 }, children: 'Do the fix in the practice chat yourself, then press Check my fix.' }),
        held && heldCommands(held.path).length ? jsx(D.FixCommands, { commands: heldCommands(held.path), attemptId: view.attempt.id, practiceName: view.attempt.profile }) : null,
      ] }, 'tofix'),
      jsx(Section, { title: after?.passed ? 'Your notes on the fix' : 'Then check your fix', children: jsxs('div', { className: 'hk-stack', children: [
        jsxs('div', { className: 'fa-f-row', children: [
          jsx(Button, { variant: 'secondary', onClick: () => openPracticeChat(view.attempt.profile), children: 'Open practice chat' }),
          showsMemory(mission) ? jsx(MemoryFile, { name: view.attempt.profile }) : null,
        ] }),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { key: 'run', variant: after?.passed ? 'secondary' : undefined, loading: runner.busy === 'after_fix', onClick: () => runPhase('after_fix'), children: after?.passed ? 'Check my fix again' : 'Check my fix' }) }),
        // A note on the fix is for the record, not needed to check it, so it sits folded (round 11 and 12 critics).
        jsx(Details, { label: savedFix ? 'Your note on the fix' : 'Add a note on the fix for your record', children: jsxs('div', { className: 'hk-stack', children: [
          jsx(Textarea, { id: 'fa-fix', rows: 3, value: fix, onChange: e => setFix(e.target.value), 'aria-label': 'Your note on the fix' }),
          jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: action.busy === 'fix', disabled: fix.trim().length < 10, onClick: () => save('fix', 'fix_note', { text: fix }), children: savedFix ? 'Update the note' : 'Save the note' }) }),
        ] }) }),
        jsx(Problem, { text: runner.error || action.error }),
        after && !after.passed ? jsx(Outcome, { run: after, mission }) : null,
        after?.passed ? jsx(Details, { label: 'Every check, after your fix', children: jsx(Outcome, { run: after, mission }) }) : null,
      ] }) }, 'fix'),
      !view.runs?.after_fix?.passed ? null : jsx(Section, { title: 'Next: do the job once more, a little differently', children: jsxs('div', { className: 'hk-stack', children: [
        jsx(Markdown, { text: mission.transfer?.body }),
        mission.lab?.note_fields ? jsx(B.FieldNoteForm, { mission, view, save, action, transfer: true }) : jsx(NoteForm, { view, save, action, transfer: true }),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: runner.busy === 'transfer', disabled: !transferNote, onClick: () => runPhase('transfer'), children: 'Check the transfer' }) }),
        jsx(Outcome, { run: view.runs?.transfer, mission }),
      ] }) }, 'transfer'),
    ] })
  }

  /* -------------------------------------------------------------- 12 record -- */

  /** The last offer of a mission: delete its practice profile, with a one-line receipt. Only on a click and a yes. */
  function DeletePractice({ view, listing, reloadAll }) {
    const [sure, setSure] = useState(false)
    const [receipt, setReceipt] = useState('')
    const action = useAction()
    const live = (listing || []).filter(p => ['ready', 'in_use'].includes(p.status))
    if (receipt) return jsx('p', { role: 'status', style: { margin: 0 }, children: receipt })
    if (!live.length) return null
    const names = live.map(p => p.name).join(' and ')
    return jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
      sure ? jsxs('div', { className: 'fa-f-row', children: [
        jsx('span', { children: `Delete ${names}? Its chats and memory go with it.` }),
        jsx(Button, { variant: 'destructive', loading: action.busy === 'delete', onClick: () => action.run('delete', async () => {
          for (const p of live) await deleteOne(p)
          setReceipt(`Deleted ${names}. Your own profiles were not touched.`)
          if (reloadAll) await reloadAll()
        }), children: 'Yes, delete it' }),
        jsx(Button, { variant: 'ghost', onClick: () => setSure(false), children: 'Keep it' }),
      ] }) : jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: () => setSure(true), children: 'Delete the practice profile' }) }),
      jsx(Problem, { text: action.error }),
    ] })
  }

  function RecordStep({ mission, view, reloadAll, go, listing = [] }) {
    const [preview, setPreview] = useState(null)
    const [withhold, setWithhold] = useState([])
    const [sure, setSure] = useState(false)
    // Adding closes the attempt. A reload here would ask to start the mission again and land on a fresh, blank try,
    // hiding "In your record" (Nov 11 live check), so the add keeps this attempt on screen with the answer it returns.
    const [justAdded, setJustAdded] = useState(null)
    const action = useAction(out => { if (out && out.added) setJustAdded(out.added); else return reloadAll() })
    useEffect(() => {
      let live = true
      post(`/foundations/attempt/${view.attempt.id}/record/preview`, { withhold }).then(p => { if (live) setPreview(p) }).catch(e => { if (live) action.setError(errorText(e)) })
      return () => { live = false }
    }, [view.attempt.status, withhold.join(',')])
    const added = view.record || preview?.added || justAdded
    const entry = preview?.entry
    return jsx(StepFrame, { title: 'Record', eyebrow: 'Step 12', lead: 'This is the entry exactly as it would go into your Field Record. Read every excerpt first: you can keep any of them out.', children: [
      jsx(Problem, { text: action.error }, 'e'),
      entry ? jsxs('div', { className: 'hk-stack', children: [
        jsx(Facts, { rows: [
          { label: 'Claim', value: entry.claim },
          { label: 'Checks frozen', value: longDate(entry.standard_frozen_at) },
          { label: 'Your guess', value: `${entry.grid.filter(g => g.expect_pass === true).length} of ${entry.grid.length} to pass` },
          { label: 'First result', value: entry.result_first.of != null ? `${entry.result_first.passed} of ${entry.result_first.of}. ${entry.result_first.checked_by}` : 'Not run' },
          { label: 'After the fix', value: entry.result_after_fix.of != null ? `${entry.result_after_fix.passed} of ${entry.result_after_fix.of}. ${entry.result_after_fix.checked_by}` : 'Not run' },
          { label: 'Transfer', value: entry.transfer.of != null ? `${entry.transfer.passed} of ${entry.transfer.of}. ${entry.transfer.checked_by}` : 'Not run' },
          { label: 'Explain it', value: entry.explain.level ? `Level ${entry.explain.level} of 4. ${entry.explain.checked_by}` : 'No level yet' },
          entry.transfer.one_off ? { label: 'Save or skip', value: `${entry.transfer.one_off.saved ? 'Saved' : 'Left out'}: "${entry.transfer.one_off.detail}". ${entry.transfer.one_off.checked_by}. Why: ${entry.transfer.one_off.why} (${entry.transfer.one_off.why_checked_by})` } : null,
        ].filter(Boolean) }),
        // The try in this mission's own words (try_lines, 0.9 persona test), never another mission's form.
        entry.try_lines?.length ? jsx(Section, { title: 'The try, before the lesson', children: jsx(Facts, { rows: entry.try_lines.map(t => ({ label: t.label, value: t.value })) }) }) : null,
        entry.caught.length ? jsx(Facts, { rows: entry.caught.map(c => ({ label: 'Caught', value: c.title })) }) : null,
        entry.missed.length ? jsx(Facts, { rows: entry.missed.map(c => ({ label: 'Missed', value: c.title })) }) : null,
        entry.gap ? jsx(Facts, { rows: [{ label: 'Gap note', value: entry.gap }] }) : null,
        jsx(Section, { title: 'Excerpts', count: entry.evidence.length, children: jsx('ul', { className: 'fa-f-evidence', children: entry.evidence.map(e => jsxs('li', { children: [
          jsxs('div', { className: 'fa-f-meta', children: [jsx('span', { className: 'fa-f-code', children: e.file }), jsx('span', { title: `SHA-256 ${e.sha256 || ''}`, children: 'Fingerprinted' }), jsx('span', { children: e.checked_by }),
            added ? null : jsxs('label', { className: 'fa-f-withhold', children: [jsx('input', { type: 'checkbox', checked: withhold.includes(e.id),
              onChange: ev => setWithhold(ev.target.checked ? [...withhold, e.id] : withhold.filter(x => x !== e.id)) }), 'Keep this excerpt out']})] }),
          e.withheld ? jsx('p', { className: 'hk-small', style: { margin: 0 }, children: 'Kept out. The record keeps only its fingerprint.' }) : jsx('pre', { className: 'fa-f-excerpt', children: e.excerpt }),
        ] }, e.id)) }) }),
      ] }, 'entry') : jsx('p', { children: 'Loading the entry.' }, 'loading'),
      mission.record_example_text ? jsx(Details, { label: 'An example entry', children: jsx(Markdown, { text: mission.record_example_text }) }, 'example') : null,
      added ? jsx(Notice, { tone: 'good', title: 'In your record', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { style: { margin: 0 }, children: `Added ${longDate(added.created_at)}. It can't be changed; a correction would be added below it.` }),
        go ? jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: () => go({ name: 'f-record' }), children: 'See your Field Record' }) }) : null,
        // No reload once the entry is in: it would start the mission again (see justAdded above). The receipt says it.
        jsx(DeletePractice, { view, listing, reloadAll: null }),
      ] }) }, 'added')
        : preview && preview.ready ? jsxs('div', { className: 'hk-stack', children: [
          jsxs('label', { className: 'fa-f-withhold', children: [jsx('input', { type: 'checkbox', checked: sure, onChange: e => setSure(e.target.checked) }), 'I\'ve read the entry. Adding it can\'t be undone.'] }),
          jsx('div', { className: 'hk-actions', children: jsx(Button, { disabled: !sure, loading: action.busy === 'add', onClick: () => action.run('add', () => post(`/foundations/attempt/${view.attempt.id}/record`, { withhold, confirm: true })), children: 'Add to my record' }) }),
        ] }, 'add') : jsx(Notice, { tone: 'info', children: view.test_out?.on && view.test_out.passed !== false
          ? 'To test out, every check has to pass on the first run, your explanation included. Then the entry is ready.'
          : 'Run the check after your fix and the transfer check first.' }, 'wait'),
    ] })
  }

  /* --------------------------------------------------------- the mission -- */

  const STEP_VIEWS = {
    recall: RecallStep, claim: ClaimStep, predict: PredictStep, setup: SetupStep, idea: IdeaStep, expert: ExpertStep, lab: LabStep,
    evidence: ScoreStep, check: CheckStep, compare: CompareStep, fix: FixStep, record: RecordStep,
  }

  function useMission(missionId, testOut = false, firstFlight = false) {
    const [state, setState] = useState({ loading: true, error: '', mission: null, view: null, listing: [] })
    const asked = useRef(testOut)
    const load = async () => {
      try {
        const start = { mission_id: missionId, ...(asked.current ? { test_out: true } : {}) }
        asked.current = false  // asked once; a reload returns the same attempt, still marked
        const [mission, view, practice] = await Promise.all([
          ctxRest(`/foundations/mission/${encodeURIComponent(missionId)}`),
          firstFlight ? post('/first-flight/start', {}) : post('/foundations/attempt/start', start),
          ctxRest('/foundations/practice'),
        ])
        setState({ loading: false, error: '', mission, view, listing: practice.practice || [] })
      } catch (e) {
        setState(s => ({ ...s, loading: false, error: errorText(e) }))
      }
    }
    useEffect(() => { load() }, [missionId])
    // While the learner's Hermes is grading an answer, the level arrives through the agent tool: look again every 5 s.
    const waiting = Boolean(state.view?.explain?.waiting)
    useEffect(() => {
      if (!waiting) return undefined
      const t = setInterval(load, 5000)
      return () => clearInterval(t)
    }, [waiting])
    return { ...state, reload: load }
  }

  /** What a test-out means, at the top of every step of one (0.9 persona test). */
  function TestOutNotice({ state }) {
    if (state.passed === true) return jsx(Notice, { tone: 'good', title: 'You tested out', children: 'Every check passed on the first run. Add the mission to your record from the Record step; it goes in marked Tested out. Compare and the fix and transfer are there if you want them.' })
    if (state.passed === false) return jsx(Notice, { tone: 'info', title: 'This test-out became the full mission', children: 'A check missed on the first run, so finish the usual way: Compare, the fix and the transfer, then the record. Your record says the try began as a test-out.' })
    return jsx(Notice, { tone: 'info', title: 'Testing out', children: 'Recall is skipped, and the lesson and the worked example are optional. Pass every check on the first run, your explanation included, and the mission goes in your record marked Tested out.' })
  }

  function MissionLoop({ missionId, go, initialStep, testOut = false, firstFlight = false, harnessGrade = null }) {
    const m = useMission(missionId, testOut, firstFlight)
    const [stepId, setStepId] = useState(initialStep || '')
    const action = useAction(m.reload)
    // A mission placed in a trail's camp belongs to that trail: its page names the trail and goes back to it.
    const trail = m.mission?.trail?.id ? m.mission.trail : null
    const up = () => go(trail ? { name: 'path', id: trail.id } : { name: 'foundations' })
    const states = m.view && m.mission ? stepStates(m.view, m.listing) : []
    // After a missed first check the page stays on Check, where the hunt is, until the learner opens Compare.
    const hunting = Boolean(m.view?.runs?.first && !m.view.runs.first.passed && latest(m.view, 'gap_note') === null
      && !(m.view.entries || []).some(e => e.kind === 'help' && e.body?.kind === 'reveal'))
    const opening = states.length ? currentStep(states) : ''
    const at = !states.length ? '' : stepId && states.find(s => s.id === stepId && s.status !== 'locked') ? stepId : opening === 'compare' && hunting ? 'check' : opening
    const runsKey = m.view ? `${m.view.runs?.first?.at || ''}|${m.view.runs?.after_fix?.at || ''}|${(m.view.entries || []).length}` : ''
    const guide = D.useGuide(m.view?.attempt?.id, at, runsKey)
    const [replayState, setReplayState] = useState('')
    if (m.loading) return jsx(Frame, { up, children: jsx('p', { children: 'Loading the mission.' }) })
    if (!m.view || !m.mission) return jsx(Frame, { up, children: [jsx(Back, { label: 'Foundations', onClick: up }, 'b'), jsx(Problem, { text: m.error || 'This mission could not load.' }, 'e')] })
    const index = STEPS.findIndex(s => s.id === at)
    const save = (name, kind, body) => action.run(name, () => post(`/foundations/attempt/${m.view.attempt.id}/entry`, { kind, body }))
    const act = (name, call) => action.run(name, call)
    const View = STEP_VIEWS[at]
    // In a First Flight the lesson is there if wanted, but Next goes from Practice straight to the job.
    const skipLearn = m.view.first_flight?.on && at === 'setup'
    const next = skipLearn ? states.find(s => s.id === 'lab') : states[index + 1]
    const ff = m.view.first_flight?.on
    const missed = Boolean(m.view.runs?.first && !m.view.runs.first.passed)
    const level = m.view.attempt.level === 'beginner' ? 'Beginner' : m.view.attempt.level === 'intermediate' ? 'Intermediate' : 'Advanced'
    const turnOn = async () => { await post('/settings/ai', { ai_help: true }).catch(() => null); guide.reload() }
    const turnOff = async () => { await post('/settings/ai', { ai_help: false }).catch(() => null); guide.reload() }
    return jsx(Frame, { up, width: 'full', children: jsxs('div', { className: 'fa-desk', children: [
      jsxs('header', { className: 'fa-desk-head', children: [
        jsx(Back, { label: ff ? 'Home' : trail ? `${trail.name} trail` : 'Foundations', onClick: ff ? () => go({ name: 'map' }) : up, hint: false }),
        jsx(Label, { children: ff ? 'Your first practice' : `${trail ? `${trail.name} · ${trail.camp_name} camp` : `Foundations · ${level}`} · Try ${m.view.attempt.attempt_no}${m.view.test_out?.on ? ' · Test-out' : ''}` }),
        jsx('h1', { className: 'hk-h1', style: { margin: 0 }, children: m.mission.title }),
        jsx(D.PhaseBar, { states, at }),
      ] }, 'head'),
      jsx(D.PhaseRail, { states, at, onPick: setStepId }, 'rail'),
      jsxs('main', { className: 'fa-desk-work', children: [
        m.view.test_out?.on ? jsx(TestOutNotice, { state: m.view.test_out }, 'testout') : null,
        m.view.attempt.frozen_at && !['lab', 'compare'].includes(at) ? jsx(B.CheckNotices, { mission: m.mission, view: m.view }, 'notices') : null,
        jsx(View, { key: `${at}:${m.view.attempt.id}`, mission: m.mission, view: m.view, listing: m.listing, save, act, action, reload: m.reload, reloadAll: m.reload, go, goStep: setStepId, guide, gradeShown: harnessGrade, onReplayState: setReplayState }, `step-${at}`),
        next && next.status !== 'locked' && !['record', 'evidence', 'predict'].includes(at) && !(at === 'check' && missed) ? jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: () => setStepId(next.id), children: `Next: ${next.title}` }) }, 'next') : null,
      ] }, 'work'),
      jsx(D.FieldGuide, { guide, attemptId: m.view.attempt.id, step: at, missed, practiceName: m.view.attempt.profile, onOpenCompare: () => setStepId('compare'), onTurnOn: turnOn, onTurnOff: turnOff,
        noRun: ['empty', 'schema_changed'].includes(replayState), fixed: Boolean(m.view.runs?.after_fix?.passed),
        onScoreAnswer: m.view.runs?.first && m.mission.explain ? () => {
          const box = typeof document !== 'undefined' ? document.getElementById('fa-explain-box') : null
          if (box) box.open = true
          setTimeout(() => {
            const n = typeof document !== 'undefined' ? document.getElementById('fa-explain-answer') : null
            if (n) { n.scrollIntoView({ block: 'center' }); n.focus() }
          }, 50)
        } : null }, 'guide'),
    ] }) })
  }

  /* --------------------------------------------------------- the Field Record -- */

  /** One row per mission: what you expected beside what passed the first time. No average row, by design. */
  function CalibrationView({ rows, emptyText = 'Not tried yet' }) {
    const table = calibrationTable(rows)
    if (!table.length) return null
    return jsxs('div', { className: 'hk-stack', children: [
      jsx('div', { className: 'fa-f-scroll', children: jsxs('table', { className: 'fa-f-cal', children: [
        jsx('thead', { children: jsxs('tr', { children: [
          jsx('th', { scope: 'col', children: 'Mission' }), jsx('th', { scope: 'col', children: 'Checks' }),
          jsx('th', { scope: 'col', children: 'You expected to pass' }), jsx('th', { scope: 'col', children: 'You scored yourself' }),
          jsx('th', { scope: 'col', children: 'Passed the first time' }),
        ] }) }),
        jsx('tbody', { children: table.map(r => r.empty
          ? jsxs('tr', { 'data-empty': '', children: [jsx('th', { scope: 'row', style: { fontWeight: 400 }, children: r.title }), jsx('td', { colSpan: 4, children: emptyText })] }, r.id)
          : jsxs('tr', { children: [
            jsx('th', { scope: 'row', style: { fontWeight: 400 }, children: r.title }), jsx('td', { className: 'fa-f-num', children: r.checks }),
            jsx('td', { className: 'fa-f-num', children: r.predicted }), jsx('td', { className: 'fa-f-num', children: r.selfScored }),
            jsx('td', { className: 'fa-f-num', children: r.passed }),
          ] }, r.id)) }),
      ] }) }),
      jsx('span', { className: 'fa-f-tag', children: 'Field Academy read it' }),
    ] })
  }

  function useRecord() {
    const [state, setState] = useState({ loading: true, data: null, error: '' })
    const load = async (body) => {
      try {
        const data = body ? await post('/foundations/record/preview', body) : await ctxRest('/foundations/record')
        setState({ loading: false, data, error: '' })
      } catch (e) {
        setState(s => ({ ...s, loading: false, error: errorText(e) }))
      }
    }
    return { ...state, load }
  }

  function ExcerptList({ items, withhold, setWithhold, locked }) {
    return jsx('ul', { className: 'fa-f-evidence', children: items.map(x => {
      const before = x.withheld && !withhold.includes(x.id)
      return jsxs('li', { children: [
        jsxs('div', { className: 'fa-f-meta', children: [
          jsx('strong', { children: x.mission_title }), jsx('span', { className: 'fa-f-code', children: x.file }), jsx('span', { children: x.kind }),
          jsx('span', { children: `Read ${longDate(x.read_at)}` }),
          jsx('span', { title: `SHA-256 ${x.sha256 || ''}`, children: 'Fingerprinted' }), jsx('span', { className: 'fa-f-tag', children: 'Field Academy read it' }),
          locked || before ? null : jsxs('label', { className: 'fa-f-withhold', children: [jsx('input', { type: 'checkbox', checked: withhold.includes(x.id),
            onChange: e => setWithhold(toggleWithhold(withhold, x.id, e.target.checked)) }), 'Keep this excerpt out'] }),
        ] }),
        // What a stranger reads beside it in record.md: the check it backs, and what kind of line it is (0.9 persona test).
        x.backs?.label ? jsx('span', { className: 'hk-small', children: `${x.backs.label}${x.backs.n ? `: ${x.backs.text}` : `: ${x.backs.text}`} ${x.about || ''}` }) : null,
        x.withheld
          ? jsx('p', { className: 'hk-small', style: { margin: 0 }, children: before ? 'Kept out when you added this entry. The record keeps only its fingerprint.' : 'Kept out. The record keeps only its fingerprint and says it was withheld.' })
          : jsx('pre', { className: 'fa-f-excerpt', children: x.excerpt }),
      ] }, x.id)
    }) })
  }

  function SavedRecord({ item }) {
    return jsxs('div', { className: 'fa-f-result', 'data-pass': '', children: [
      jsxs('div', { className: 'fa-f-row', children: [jsx('strong', { className: 'fa-f-code', children: item.number }), jsx('span', { className: 'hk-small', children: `Saved ${longDate(item.issued_at)}` }),
        item.entries != null ? jsx('span', { className: 'hk-small', children: plural(item.entries, 'entry', 'entries') }) : null] }),
      item.folder_shown ? jsx(PathLine, { path: item.folder, shown: item.folder_shown, label: 'Record folder' }) : null,
    ] })
  }

  /** Your Foundations Field Record: preview everything, keep any excerpt out, then save the folder a stranger can check. */
  /** The record's cover: what was proved, how it was caught, what it cost, and that it is self-issued. Hashes sit
   *  behind Details. Neutral colors under any accent: nothing here is a warning. */
  /** The cover's headline, in plain words from the record itself: which mission is in it and whether it passed. */
  function recordLine(body) {
    const entries = body.entries || []
    const passed = new Set(((body.can_claim || {}).passed || []).map(x => x.title))
    if (!entries.length) return 'Nothing is in your record yet.'
    const e = entries[entries.length - 1]
    if (passed.has(e.mission_title)) return `You passed “${e.mission_title}”.`
    const fixed = e.result_after_fix && e.result_after_fix.of != null && e.result_after_fix.passed === e.result_after_fix.of
    const graded = e.explain && e.explain.level
    return `${fixed ? `You fixed the problem in “${e.mission_title}”.` : `“${e.mission_title}” is in your record.`} ${graded ? 'It isn\'t passed yet because your written answer needs more.' : 'It isn\'t passed yet.'}`
  }

  function RecordCover({ body, verdict }) {
    const scope = body.scope || {}
    const entries = body.entries || []
    const left = Math.max(0, (scope.missions_in_course || 0) - (scope.missions_in_record || 0))
    return jsxs('section', { className: 'fa-cover', 'aria-label': 'Record cover', children: [
      jsx('p', { className: 'fa-cover-line', children: recordLine(body) }),
      entries.length ? jsx(Facts, { rows: entries.flatMap(e => [
        { label: e.mission_title, value: [e.help?.words, e.mode === 'first_flight' || (e.skipped || []).includes('claim') ? 'Started from the 10-minute practice' : ''].filter(Boolean).join('. ') || 'In your record' },
      ].filter(Boolean)) }) : null,
      jsx('p', { children: `${body.disclaimer || ''} If an entry is changed after it is added, the saved record shows it.` }),
      jsx(Details, { label: 'Details', children: jsx(Facts, { rows: [
        ...entries.filter(e => e.cost?.practice).map(e => ({ label: 'What it cost', value: `${e.cost.practice} ${e.cost.guide || ''}`.trim() })),
        { label: 'Latest entry fingerprint', value: body.chain_head || '' }, { label: 'Format', value: `${body.record_format || ''}` },
      ] }) }),
    ] })
  }

  /** The record's trail map: per trail, each camp reached or how far along, and the summit. */
  function RecordTrails({ trails }) {
    const camps = trails.trails[0]?.camps || []
    const head = trails.trailhead
    return jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
      head?.total ? jsx('p', { style: { margin: 0 }, children: jsxs('span', { children: [jsx('strong', { children: 'Foundations, the trailhead: ' }), `${head.passed} of ${head.total} missions passed.`] }) }) : null,
      jsx('table', { className: 'fa-rt', children: [
        jsx('thead', { children: jsxs('tr', { children: [jsx('th', { children: 'Trail' }), ...camps.map(c => jsx('th', { children: `${c.name} camp` }, c.id)), jsx('th', { children: 'Summit' })] }) }, 'h'),
        jsx('tbody', { children: trails.trails.map(t => jsxs('tr', { children: [
          jsxs('th', { scope: 'row', children: [jsx('span', { className: 'fa-sc fa-sc-blaze', style: { display: 'block' }, children: t.eyebrow }), t.name] }),
          ...t.camps.map((c, i) => jsx('td', { 'data-reached': c.reached ? '' : undefined, children: `${c.name !== camps[i]?.name ? `${c.name}: ` : ''}${c.reached ? 'Reached' : c.total ? `${c.passed} of ${c.total}` : ''}` }, c.id)),
          jsx('td', { 'data-reached': t.summit ? '' : undefined, children: t.summit ? 'Reached' : 'Not yet' }),
        ] }, t.id)) }, 'b'),
      ] }),
      jsx('p', { className: 'hk-small', style: { margin: 0 }, children: trails.note }),
    ] })
  }

  /** The proof, mission by mission: where it sits on the trail map, how it passed, and each line of evidence. */
  function RecordPassed({ passed }) {
    const rows = passed.missions || []
    if (!rows.length) return jsx('p', { style: { margin: 0 }, children: 'None yet. A mission goes here once every check on it has passed.' })
    return jsxs('div', { className: 'hk-stack', style: { gap: 12 }, children: [
      jsx('p', { className: 'hk-small', style: { margin: 0 }, children: passed.note }),
      ...rows.map(m => jsxs('div', { className: 'fa-rp', children: [
        jsxs('div', { className: 'fa-f-row', children: [jsx('strong', { children: m.title }), jsx('span', { className: 'hk-small', children: m.where })] }),
        jsx('span', { className: 'hk-small', children: `Passed ${m.how}, ${m.checks} checks, ${longDate(m.date)}. Record entry ${m.entry}.` }),
        jsx('ul', { className: 'fa-rp-ev', children: m.evidence.map((ev, i) => jsxs('li', { children: [
          jsx('code', { children: ev.withheld ? 'withheld' : ev.file }),
          jsx('span', { children: ev.withheld ? ` read from ${ev.read_from}, kept out by you` : ` read from ${ev.read_from}: “${ev.excerpt}”` }),
          jsx('span', { className: 'hk-small', children: ` ${String(ev.sha256 || '').slice(0, 12)}` }),
        ] }, i)) }),
      ] }, m.mission)),
    ] })
  }

  function FieldRecordView({ go }) {
    const rec = useRecord()
    const [form, setForm] = useState({ holder: '', limits: '', caseText: '' })
    const [withhold, setWithhold] = useState([])
    const [sure, setSure] = useState(false)
    const [saved, setSaved] = useState(null)
    const action = useAction()
    const up = () => go({ name: 'foundations' })
    useEffect(() => { rec.load({ withhold }) }, [withhold.join(',')])
    const data = rec.data
    const body = data?.body
    const problems = recordProblems(form)
    const set = key => e => setForm(f => ({ ...f, [key]: e.target.value }))
    const save = () => action.run('save', async () => {
      const out = await post('/foundations/record/issue', { holder: form.holder, limits: form.limits, case: form.caseText, withhold, confirm: true })
      setSaved(out)
      setSure(false)
      await rec.load({ withhold })
      return out
    })
    const again = number => action.run(`again-${number}`, async () => {
      const out = await post('/foundations/record/save', { number })
      host.notify({ kind: 'success', message: 'Saved the files again.' })
      return out
    })
    const head = jsx(PageHeader, { back: jsx(Back, { label: 'Foundations', onClick: up }), eyebrow: jsx(Label, { children: 'Field Academy' }), title: 'Your Field Record',
      lead: 'Camps reached on each trail, and every mission you passed with the lines Field Academy read as evidence. It is saved on this computer, and you choose who sees it.' }, 'head')
    if (rec.loading) return jsx(Frame, { up, children: [head, jsx('p', { children: 'Loading your record.' }, 'l')] })
    if (!body) return jsx(Frame, { up, children: [head, jsx(Problem, { text: rec.error || 'Your record could not load.' }, 'e')] })
    const scope = body.scope || {}
    const issuedList = data.issued || []
    const items = data.excerpts || []
    const can = body.can_claim || { passed: [], not_yet: [] }
    const fl = body.first_and_last || {}
    if (!data.ready) {
      return jsx(Frame, { up, children: [head, jsx(Notice, { tone: 'info', title: 'Nothing in your record yet', children: 'Finish a mission and add it to your record at its last step. Then your Field Record can be saved here.' }, 'empty'),
        jsx(Section, { title: 'How your self-judgment moved', children: jsx(CalibrationView, { rows: body.calibration?.per_mission, emptyText: 'Not in your record yet' }) }, 'cal')] })
    }
    return jsx(Frame, { up, children: [
      head,
      jsx(Problem, { text: rec.error || action.error }, 'e'),
      saved ? jsx(Notice, { tone: 'good', title: 'Your Field Record is saved', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { style: { margin: 0 }, children: `Record number ${saved.number}. The folder holds the record, the excerpts, a fingerprint of every file and a README that tells a stranger how to check it.` }),
        jsx(PathLine, { path: saved.folder, shown: saved.folder_shown, label: 'Record folder' }),
        jsx(Facts, { rows: (saved.files || []).map(f => ({ label: f.startsWith('evidence/') ? 'Excerpt' : 'File', value: f })) }),
      ] }) }, 'saved') : null,
      jsx(RecordCover, { body, verdict: data.verdict }, 'cover'),
      body.trails?.trails?.length ? jsx(Section, { title: 'The trail map', children: jsx(RecordTrails, { trails: body.trails }) }, 'trails') : null,
      body.passed ? jsx(Section, { title: 'Missions passed, with evidence', count: (body.passed.missions || []).length, children: jsx(RecordPassed, { passed: body.passed }) }, 'passed') : null,
      jsx(Details, { label: 'Who, when, and every claim', children: jsxs('div', { className: 'hk-stack', children: [
      jsx(Section, { title: 'Who and when', children: jsx(Facts, { rows: [
        { label: 'Issued by', value: 'You. Nobody else issues it.' },
        { label: 'Hermes', value: `${scope.hermes?.line || ''} ${checkedByWords(scope.hermes?.checked_by)}.` },
        { label: 'Time', value: `${hoursWords(scope.hours)}. Gaps over 15 minutes, like waiting for a scheduled run, don't count. Field Academy counted it.` },
        { label: 'Missions', value: `${scope.missions_in_record} of ${scope.missions_in_course} in your record` },
        { label: 'Outside reviewer', value: 'None. The record says so: "Nobody outside has reviewed this record."' },
      ] }) }, 'scope'),
      jsx(Section, { title: 'Your claims', count: body.claims.length, children: jsx('ol', { className: 'fa-f-claims', children: body.claims.map(c => jsxs('li', { children: [
        jsx('strong', { children: c.mission_title }), jsx('span', { children: c.claim }),
        jsx('span', { className: 'hk-small', children: `${plural((c.standard || []).length, 'check', 'checks')}, frozen ${longDate(c.standard_frozen_at)}. ${c.changes.length ? `Changed ${plural(c.changes.length, 'time', 'times')} after that, with your reasons.` : 'No change after that.'}` }),
      ] }, c.n)) }) }, 'claims'),
      jsx(Section, { title: 'How your self-judgment moved', children: jsxs('div', { className: 'hk-stack', children: [
        jsx(CalibrationView, { rows: (body.calibration.per_mission || []).filter(r => r.in_record), emptyText: 'Not in your record yet' }),
        (body.calibration.per_mission || []).some(r => !r.in_record) ? jsx('p', { style: { margin: 0 }, children: `${plural((body.calibration.per_mission || []).filter(r => !r.in_record).length, 'mission', 'missions')} to go.` }) : null,
      ] }) }, 'cal'),
      ] }) }, 'details'),
      jsx(Section, { title: 'First and last', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { className: 'hk-small', style: { margin: 0 }, children: fl.note }),
        jsx(Facts, { rows: [fl.first, fl.last].filter(Boolean).map((s, i) => ({ label: i === 0 ? 'First' : 'Latest',
          value: `${s.mission_title}: ${s.found_wrong || 'Nothing written about what was wrong.'} Planted problems caught ${s.caught}, missed ${s.missed}.` })) }),
      ] }) }, 'fl'),
      jsx(Section, { title: 'What you can now claim', children: jsxs('div', { className: 'hk-stack', children: [
        can.passed.length ? jsx(Facts, { rows: can.passed.map(x => ({ label: x.title, value: `${x.claim}${x.after_fix ? ' Passed after a fix.' : x.tested_out ? ' Tested out.' : ''}` })) })
          : jsx('p', { style: { margin: 0 }, children: 'Nothing yet. A claim goes here once every check on it has passed.' }),
        can.not_yet.length ? jsx(Details, { label: `Not yet (${can.not_yet.length})`, children: jsx(Facts, { rows: can.not_yet.map(x => ({ label: x.title, value: x.why })) }) }) : null,
      ] }) }, 'can'),
      jsx(Details, { label: `The lines Field Academy read (${items.length}). Check them before you save.`, children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { className: 'hk-small', style: { margin: 0 }, children: 'These are the lines Field Academy read from your practice profiles. Secrets were already removed. Read each one: keep out anything you don\'t want a stranger to see. A kept-out excerpt shows as withheld, with only its fingerprint.' }),
        jsx(ExcerptList, { items, withhold, setWithhold, locked: false }),
      ] }) }, 'excerpts'),
      jsx(Section, { title: 'In your words', children: jsxs('div', { className: 'fa-f-form', children: [
        jsxs('label', { children: ['Your name on the record', jsx(Input, { value: form.holder, onChange: set('holder'), placeholder: 'Your name', 'aria-label': 'Your name on the record' })] }),
        jsxs('label', { children: ['What this record doesn\'t show', jsx('span', { className: 'hk-small', children: 'Two or three lines, in your own words. Not graded.' }),
          jsx(Textarea, { style: { minHeight: '5rem', width: '100%' }, value: form.limits, onChange: set('limits'), 'aria-label': 'What this record doesn\'t show',
            placeholder: 'It shows practice work on my own computer. Nobody else watched, and my own Hermes graded my answers.' })] }),
        jsxs('label', { children: ['A case for a stranger, if you want one', jsx('span', { className: 'hk-small', children: 'One job: what you asked, what Hermes got wrong or nearly got wrong, how you found out. Under 300 words. Leave it empty and the record says no case was written.' }),
          jsx(Textarea, { style: { minHeight: '8rem', width: '100%' }, value: form.caseText, onChange: set('caseText'), 'aria-label': 'A case for a stranger' })] }),
      ] }) }, 'form'),
      jsx(Section, { title: 'Save your record', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { style: { margin: 0 }, children: 'Field Academy saves a folder on this computer with the record, every excerpt you kept, a fingerprint of each file and a README for a stranger. Nothing is sent anywhere. You choose who sees it.' }),
        problems.length && (form.holder || form.limits || form.caseText || sure) ? jsx(Problems, { items: problems }) : null,
        jsxs('label', { className: 'fa-f-withhold', children: [jsx('input', { type: 'checkbox', checked: sure, onChange: e => setSure(e.target.checked) }), 'I\'ve read the record and every excerpt. Saving it can\'t be undone.'] }),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { disabled: !sure || problems.length > 0, loading: action.busy === 'save', onClick: save, children: 'Save my Field Record' }) }),
      ] }) }, 'save'),
      issuedList.length ? jsx(Section, { title: 'Records you saved', count: issuedList.length, children: jsx('div', { className: 'hk-stack', children: [
        jsx('p', { className: 'hk-small', style: { margin: 0 }, children: 'Save the files again writes a record\'s folder again from the record as it was saved, in the same place. Use it if a file in the folder was deleted or changed. The record and its number stay the same.' }, 'about'),
        ...issuedList.map(item => jsxs('div', { className: 'hk-stack', children: [
        jsx(SavedRecord, { item }),
        jsx('div', { className: 'hk-actions', children: [
          jsx(Button, { variant: 'secondary', loading: action.busy === `again-${item.number}`, onClick: () => again(item.number), children: 'Save the files again' }, 'a'),
          item.folder ? jsx(Button, { variant: 'secondary', onClick: () => openFolder(item.folder), children: 'Open the folder' }, 'o') : null,
        ] }),
      ] }, item.number))] }) }, 'issued') : null,
    ] })
  }

  /* ------------------------------------------------------- the path + card -- */

  /** The Foundations list. On the map (fromCopy) the last list kept for this Hermes shows at once while the live one
   *  loads; the map holds every click until its live answers are in, so nothing acts on the copy. */
  function useFoundations(wanted = true, { fromCopy = false } = {}) {
    const [state, setState] = useState(() => {
      const copy = wanted && fromCopy && ui.keptFoundations ? ui.keptFoundations() : null
      return copy ? { loading: false, data: copy, error: '' } : { loading: true, data: null, error: '' }
    })
    useEffect(() => {
      if (!wanted) return undefined
      let live = true
      loadFoundations().then(data => live && setState({ loading: false, data, error: '' })).catch(e => live && setState({ loading: false, data: null, error: errorText(e) }))
      return () => { live = false }
    }, [])
    return state
  }

  function missionStatus(m) {
    return missionWords(m)
  }

  /** The Foundations card, first under the banner: what a mission does that a prompt can't, shown with the real
   *  files it reads. Hidden on a backend from before 0.9. */
  function FoundationsCard({ go, foundations, compact = false }) {
    const own = useFoundations(!foundations)
    const f = foundations || own
    const missions = (f.data?.missions || []).filter(m => !m.trail)
    if (!missions.length) return null
    const done = missions.filter(m => (m.attempts || []).some(a => a.status === 'done')).length
    if (compact) {
      // Beside Start here on the home page: the eleven missions that come right after the first practice.
      const begun = missions.some(m => (m.attempts || []).length)
      return jsx(Card, { className: 'fa-f-next', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx(Label, { children: begun ? 'Foundations: where you left off' : 'Then: Foundations' }),
        jsx('h3', { className: 'hk-h2', style: { margin: 0 }, children: `${plural(missions.length, 'mission', 'missions')} on how Hermes really works` }),
        jsx('p', { style: { margin: 0 }, children: 'Each runs in a practice profile with one problem planted first. The check reads Hermes\'s own files, not your word.' }),
        jsxs('div', { className: 'hk-actions', children: [
          jsx(Button, { variant: begun ? 'default' : 'secondary', onClick: () => go({ name: 'foundations' }), children: 'Open Foundations' }),
          jsx('span', { className: 'hk-small', children: `${done} of ${missions.length} in your record` }),
        ] }),
      ] }) })
    }
    const beat = (icon, title, body, files) => jsxs('li', { className: 'fa-f-beat', children: [
      jsxs('div', { className: 'fa-f-row', children: [jsx(Codicon, { name: icon, size: 16 }), jsx('strong', { children: title })] }),
      jsx('p', { children: body }),
      jsx('div', { className: 'fa-f-files', children: files.map(name => jsx('code', { className: 'fa-f-code', children: name }, name)) }),
    ] })
    // The first-run practice above holds the page's Start here; this card is the eleven missions that follow it.
    const begun = missions.some(m => (m.attempts || []).length)
    return jsx(Section, { title: 'Foundations', count: missions.length, children: jsx(Card, { children: jsxs('div', { className: 'fa-f-card fa-f-start', children: [
      jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
        jsx(Label, { children: begun ? 'Where you left off' : 'The trailhead: Foundations' }),
        jsx('h2', { className: 'hk-h2', style: { margin: 0 }, children: 'Prove what you can do with Hermes' }),
        jsx('p', { style: { margin: 0 }, children: `${missions.length === 11 ? 'Eleven' : missions.length} missions on how Hermes really works. Each one runs in a practice profile Field Academy makes for you, so your own setup stays as it is.` }),
      ] }),
      jsxs('ol', { className: 'fa-f-beats', 'aria-label': 'What every mission does', children: [
        beat('bug', 'A problem is planted first',
          'Before your first chat, the practice profile gets a snag a real setup has: memory nearly full, saves held for approval, a job set to deliver nowhere.',
          ['memories/MEMORY.md', 'config.yaml']),
        beat('eye', 'The check reads Hermes itself',
          'When you press Check, Field Academy opens that profile\'s memory files, settings, chat records and run history. What you say about your work is never the check.',
          ['state.db', 'cron/jobs.json']),
        beat('verified', 'The record opens anywhere',
          'Each pass goes into your Field Record with the exact line it read. The record is tamper-evident and opens without Hermes.',
          ['record.md', 'MANIFEST.sha256']),
      ] }),
      jsxs('div', { className: 'hk-actions', children: [
        jsx(Button, { onClick: () => go({ name: 'foundations' }), children: 'Open Foundations' }),
        jsx('span', { className: 'hk-small', children: `${done} of ${plural(missions.length, 'mission', 'missions')} in your record` }),
      ] }),
    ] }) }) })
  }

  function useSample() {
    const [sample, setSample] = useState(null)
    useEffect(() => {
      let live = true
      loadSample().then(d => { if (live) setSample(d) }).catch(() => { if (live) setSample({ state: 'empty', words: '' }) })
      return () => { live = false }
    }, [])
    return sample
  }

  /** The home page's one card (P1, P2): a still of the replay's bracket, one line on what happens, two buttons. */
  function FirstFlightCard({ go, foundations, compact = false }) {
    const sample = useSample()
    const own = useFoundations(!foundations)
    const f = foundations || own
    // A First Flight already under way is offered back, with where it stopped (Loop 3 live gate).
    const resume = resumeWords((f.data?.missions || []).find(m => m.id === 'f.memory'))
    return jsxs('section', { className: compact ? 'fa-ff fa-ff-compact' : 'fa-ff', 'aria-label': 'First flight', children: [
      jsxs('div', { className: 'hk-stack fa-ff-copy', style: { gap: 12 }, children: [
        jsx(Label, { children: resume ? 'Where you left off' : 'Start here' }),
        jsx('h2', { children: resume ? resume.title : 'Practice one job in a test copy of Hermes, and see what it really did' }),
        jsx('p', { children: resume ? resume.where : 'Field Academy makes a practice copy of Hermes with one hidden problem. You ask it to save a note, say whether you think it worked, then see what Hermes actually did. It takes about 10 minutes.' }),
        jsxs('div', { className: 'fa-ff-actions', children: [
          jsx(Button, { onClick: () => go({ name: 'f-mission', id: 'f.memory', firstFlight: true }), children: resume ? resume.button : 'Start the practice' }),
          jsx(Button, { variant: 'secondary', onClick: () => go({ name: 'sample' }), children: 'Watch a sample run' }),
        ] }),
        jsx('p', { className: 'hk-small', children: 'It uses a separate practice profile and your own model.' }),
      ] }),
      jsxs('div', { className: 'hk-stack', style: { gap: 6 }, 'aria-label': 'A still from a sample run', children: [
        // Never an empty box: the live sample when it is ready, the bundled recorded run while it loads or when Hermes can't be reached.
        jsx(D.Replay, { sample: homePreview(sample), still: true }),
        jsx('span', { className: 'hk-small', children: 'At the end you see your practice chat beside the files Hermes wrote.' }),
      ] }),
    ] })
  }

  /** Watch a sample run (P3): the Compare line counts up and the time line slides to the bracket. No profile is made and
   *  no model is called; the sample is a recorded run, labelled as one. */
  function SampleRun({ go }) {
    const sample = useSample()
    const up = () => go({ name: 'map' })
    if (!sample) return jsx(Frame, { up, children: jsx('p', { children: 'Loading the sample run.' }) })
    if (sample.state !== 'ready') return jsx(Frame, { up, children: [jsx(Back, { label: 'Home', onClick: up }, 'b'), jsx(Notice, { tone: 'info', title: 'The sample run is not in this copy', children: 'Start the practice to see your own run instead.' }, 'n')] })
    const pins = sample.pins?.pins || []
    return jsx(Frame, { up, width: 'full', children: jsxs('div', { className: 'fa-desk', 'data-norail': '', children: [
      jsxs('header', { className: 'fa-desk-head', children: [
        jsx(Back, { label: 'Home', onClick: up, hint: false }),
        jsx(Label, { children: 'Sample run' }),
      ] }, 'head'),
      jsxs('main', { className: 'fa-desk-work', children: [
        jsx(D.CompareHero, { ...runHeadline(sample, sample.checks, 'the learner\'s'), score: scoreSentence(sample.compare, 'The learner in this sample'), sampleLabel: 'Sample run: a test practice profile, coached by Claude Sonnet. Not a live Hermes recording.' }, 'hero'),
        jsxs('div', { className: 'fa-ff-actions', children: [
          jsx(Button, { onClick: () => go({ name: 'f-mission', id: 'f.memory', firstFlight: true }), children: 'Start your own practice' }),
          jsx('span', { className: 'hk-small', style: { alignSelf: 'center' }, children: 'About 10 minutes.' }),
        ] }, 'go'),
        jsx(D.Replay, { sample, pins, play: true }, 'replay'),
      ] }, 'work'),
      jsx('aside', { className: 'fa-desk-guide', 'data-open': 'true', 'aria-label': 'Field guide', children: jsxs('div', { className: 'fa-guide', children: [
        jsxs('h2', { children: [jsx(Codicon, { name: 'compass', size: 16 }), 'Field guide'] }),
        jsxs('section', { className: 'fa-guide-sec', children: [
          jsx('h3', { children: 'Notes on the run' }),
          ...pins.map((p, i) => jsx(D.Said, { text: `${i + 1}. ${p.why}` }, p.event_id)),
          jsx('p', { className: 'hk-small', children: 'Written by the model from the sample run.' }),
        ] }),
      ] }) }, 'guide'),
    ] }) })
  }

  function FoundationsPath({ go }) {
    const f = useFoundations()
    const up = () => go({ name: 'map' })
    // Practice missions placed in a trail's camp are opened from that trail; Foundations lists its own.
    const missions = (f.data?.missions || []).filter(m => !m.trail)
    const table = f.data?.calibration_table || []
    const done = missions.filter(m => (m.attempts || []).some(a => a.status === 'done')).length
    const saved = (f.data?.record || []).length
    return jsx(Frame, { up, children: [
      jsx(PageHeader, { back: jsx(Back, { label: 'Trail map', onClick: up }), eyebrow: jsx(Label, { children: 'Missions' }), title: 'Foundations',
        lead: 'How Hermes really works, one idea at a time. Each mission runs in a practice profile, so your own Hermes stays as it is.' }, 'head'),
      f.loading ? jsx('p', { children: 'Loading.' }, 'l') : null,
      jsx(Problem, { text: f.error }, 'e'),
      missions.length ? jsx(Details, { label: 'Already use Hermes? Test out of a mission', children: jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
        jsx('p', { style: { margin: 0 }, children: 'A test-out skips Recall, and the lesson and the worked example are there only if you want them. Everything that proves the skill stays: your claim, your guess, a practice profile with a problem planted in it, the real job, your own score, and the check.' }),
        jsx('p', { style: { margin: 0 }, children: 'Pass every check on the first run, your explanation included, and the mission goes into your record marked Tested out. Miss one and you finish the mission the usual way, from where you are: Compare, the fix and the transfer. Your record says the try began as a test-out either way.' }),
        jsx('p', { className: 'hk-small', style: { margin: 0 }, children: 'Press Test out beside a mission to start. Mission 11 is the review itself, so it has no test-out.' }),
      ] }) }, 'testout') : null,
      jsx(Section, { title: 'Missions', count: missions.length, children: jsx('div', { className: 'hk-stack', children: missions.map(m => {
        const st = missionStatus(m)
        return jsx(Card, { children: jsxs('div', { className: 'fa-f-card', children: [
          jsxs('div', { className: 'fa-f-row', children: [jsx('strong', { className: 'hk-h3', children: Number.isInteger(m.order) ? `${m.order}. ${m.title}` : m.title }), jsx(Pill, { tone: st.tone, children: st.word })] }),
          jsx('span', { className: 'hk-small', children: jsx(Inline, { text: [m.minutes ? `About ${(m.minutes.read || 0) + (m.minutes.do || 0)} minutes. ` : '', m.cost?.line || ''].join('') }) }),
          jsxs('div', { className: 'hk-actions', children: [
            jsx(Button, { onClick: () => go({ name: 'f-mission', id: m.id }), children: st.button }, 'go'),
            canTestOut(m) ? jsx(Button, { variant: 'secondary', onClick: () => go({ name: 'f-mission', id: m.id, testOut: true }), children: 'Test out' }, 'out') : null,
          ] }),
        ] }) }, m.id)
      }) }) }, 'missions'),
      table.some(r => r.in_record) ? jsx(Section, { title: 'How well you judge your own work', children: jsx(CalibrationView, { rows: table }) }, 'cal') : null,
      done ? jsx(Section, { title: 'Your Field Record', children: jsx(Card, { children: jsxs('div', { className: 'fa-f-card', children: [
        jsx('p', { style: { margin: 0 }, children: `${plural(done, 'mission is', 'missions are')} in your record. Read it, keep out any excerpt you want private, and save a folder a stranger can check.` }),
        saved ? jsx('p', { className: 'hk-small', style: { margin: 0 }, children: `You saved ${plural(saved, 'record', 'records')} so far.` }) : null,
        jsx('div', { className: 'hk-actions', children: jsx(Button, { onClick: () => go({ name: 'f-record' }), children: 'Open my Field Record' }) }),
      ] }) }) }, 'record') : null,
    ] })
  }

  return { FoundationsCard, FoundationsPath, MissionLoop, FieldRecordView, CalibrationView, useFoundations, FirstFlightCard, SampleRun }
}
