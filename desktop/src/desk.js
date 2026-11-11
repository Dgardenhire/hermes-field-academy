// Field Academy 0.9 Loop 2: the mission desk. The phase rail, the Field guide column, the Compare line with the
// replay of the run under it, the First Flight card on the home page and the sample run. Built into desktop/plugin.js
// with the rest of the page; screens share the page's helpers through createDeskViews(ui), which foundations.js calls
// once, so nothing here imports from plugin.js.
//
// Rules this file keeps: nothing a model wrote is ever sent, approved, deleted or written from here. Do it with me's
// commands are fixed in the backend and only drafted or copied; the learner presses Enter. Model text is shown as text,
// never as markup.

import { useEffect, useRef, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'
import { Button, Codicon, Input, host } from '@hermes/plugin-sdk'
import { Notice, Spinner } from 'hermes-ui-kit'
import { bracketWords, heldSentence, explainMerged, explainShown, runHeadline, scoreSentence, sourceWords, bracketAt, clockWords, compareLine, fetchingWords, guideFetching, phaseBarWords, phaseRows, quoteParts, replayRows, usedRungs } from './desk_logic.js'

export const DESK_CSS = `
.fa-root .hk-keys kbd{font-size:12px}
.fa-desk{display:grid;gap:16px;grid-template-columns:minmax(0,1fr);align-items:start;padding:16px 20px 40px;width:100%;max-width:1500px;margin:0 auto}
.fa-desk-head{display:grid;gap:6px}
.fa-desk-rail{display:none}
.fa-desk-bar{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:var(--hk-fs)}
.fa-desk-bar strong{font-weight:600}
.fa-desk-bar ol{display:flex;gap:4px;margin:0;padding:0;list-style:none}
.fa-desk-bar li{width:44px;height:4px;border-radius:2px;background:var(--hk-stroke)}
.fa-desk-bar li[data-state=done]{background:var(--hk-good-fill)}
.fa-desk-bar li[data-state=now]{background:var(--hk-accent)}
.fa-desk-work{display:grid;gap:14px;min-width:0}
.fa-desk-guide{min-width:0}
@container (min-width:860px){
  .fa-desk{grid-template-columns:minmax(0,1fr) 300px}
  .fa-desk-head{grid-column:1/-1}
  .fa-desk-guide{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto}
}
@container (min-width:1180px){
  .fa-desk{grid-template-columns:200px minmax(0,1fr) 320px}
  .fa-desk[data-norail]{grid-template-columns:minmax(0,1fr) 320px}
  .fa-desk-rail{display:grid;position:sticky;top:12px}
  .fa-desk-bar{display:none}
}
@container (max-width:859px){
  .fa-desk{min-height:calc(100vh - 64px);grid-template-rows:auto 1fr auto}
  .fa-desk-guide{position:sticky;bottom:0;z-index:2;margin:0 -20px -40px;align-self:end}
}
.fa-rail{display:grid;gap:14px;margin:0;padding:0;list-style:none}
.fa-rail h3{margin:0 0 4px;font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase}
.fa-rail ol{margin:0;padding:0;list-style:none;display:grid;gap:2px}
.fa-rail button{display:flex;gap:8px;align-items:center;width:100%;text-align:left;font:inherit;color:inherit;background:none;border:0;border-radius:2px;padding:4px 8px;cursor:pointer}
.fa-rail button:hover{background:var(--hk-hover)}
.fa-rail button[aria-current=step]{background:var(--hk-active);font-weight:600}
.fa-rail button:focus-visible{outline:2px solid var(--hk-accent);outline-offset:-2px}
.fa-rail [data-status=done] .codicon{color:var(--hk-good)}
.fa-rail-lock{display:flex;gap:6px;align-items:center;padding:2px 8px;font-size:var(--hk-fs-sm)}
.fa-rail-step-locked{display:flex;gap:8px;align-items:center;padding:4px 8px}
.fa-guide{display:grid;gap:12px;padding:14px;border:1px solid var(--hk-stroke);border-radius:2px;background:var(--hk-surface)}
.fa-guide h2{margin:0;font-size:15px;font-weight:600;display:flex;gap:8px;align-items:center}
.fa-guide h3{margin:0;font-size:13px;font-weight:600}
.fa-guide-sec{display:grid;gap:8px;padding-top:10px;border-top:1px solid var(--hk-stroke)}
.fa-guide-buttons{display:grid;gap:6px}
.fa-guide-buttons button{justify-content:flex-start}
.fa-guide-said{display:grid;gap:4px;padding:8px 10px;border-radius:2px;background:var(--hk-sunken);border-left:3px solid var(--hk-accent)}
.fa-guide-said p{margin:0}
.fa-guide-from{font-size:var(--hk-fs-sm)}
.fa-guide-wait{display:flex;gap:8px;align-items:center;font-size:var(--hk-fs-sm);font-variant-numeric:tabular-nums}
.fa-guide-chips{display:flex;flex-wrap:wrap;gap:6px}
.fa-guide-chip{font:inherit;font-size:var(--hk-fs-sm);color:inherit;background:var(--hk-sunken);border:1px solid var(--hk-stroke);border-radius:2px;padding:3px 8px;cursor:pointer;text-align:left}
.fa-guide-chip:hover{border-color:var(--hk-accent)}
.fa-guide-src{display:inline-flex;font-size:12px;font-weight:600;padding:0 5px;margin-left:4px;border:1px solid var(--hk-stroke);border-radius:2px}
.fa-guide-cmd{display:grid;gap:4px;margin:0;padding:0;list-style:none}
.fa-guide-cmd code{display:block;font-family:var(--hk-mono);font-size:var(--hk-fs-sm);padding:6px 8px;border-radius:2px;background:var(--hk-sunken)}
.fa-guide-foot{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;justify-content:space-between;font-size:var(--hk-fs-sm);padding-top:8px;border-top:1px solid var(--hk-stroke)}
.fa-guide-tab{display:none}
@container (max-width:859px){
  .fa-guide{border-radius:2px 2px 0 0;max-height:60vh;overflow:auto;box-shadow:0 -6px 18px color-mix(in srgb,var(--hk-ink) 14%,transparent)}
  .fa-guide-tab{display:flex;justify-content:space-between;align-items:center;gap:10px;width:100%;background:var(--hk-surface);border:1px solid var(--hk-stroke);border-bottom:0;border-radius:2px 2px 0 0;padding:6px 20px}
  .fa-guide-tab-toggle{display:flex;gap:8px;align-items:center;flex:1;font:inherit;font-weight:600;color:inherit;background:none;border:0;padding:4px 0;cursor:pointer;text-align:left}
  .fa-desk-guide[data-open=false] .fa-guide{display:none}
  .fa-guide>h2{display:none}
}
.fa-hero{display:grid;gap:6px}
.fa-hero-line{margin:0;font-size:38px;line-height:1.15;font-weight:600;letter-spacing:-.005em;max-width:30ch}
@container (max-width:859px){.fa-hero-line{font-size:30px}}
@container (max-width:600px){.fa-hero-line{font-size:26px}}
.fa-hero-sub{font-size:15px;margin:0}
.fa-check-head{display:grid;gap:4px;padding:4px 0 8px}
.fa-check-line{margin:0;font-size:32px;line-height:1.1;font-weight:600}
.fa-check-head[data-pass] .fa-check-line{color:var(--hk-good)}
.fa-check-line{max-width:32ch}
.fa-next{display:grid;gap:8px;padding:12px 14px;border-radius:2px;border:1px solid var(--hk-stroke);border-left:3px solid var(--hk-accent);background:var(--hk-surface)}
.fa-next h3{margin:0;font-size:15px;font-weight:600}
.fa-explain-box{border:1px solid var(--hk-stroke);border-radius:2px;background:var(--hk-surface);padding:0 14px}
.fa-explain-box>summary{cursor:pointer;padding:12px 0;font-weight:600}
.fa-explain-box[open]{padding-bottom:14px}
.fa-fixed{display:grid;gap:8px}
.fa-fixed .fa-check-line{font-size:30px}
.fa-fixed-row{display:grid;gap:4px;padding:10px 12px;border-radius:2px;border:1px solid var(--hk-stroke);border-left:3px solid var(--hk-good-fill);background:var(--hk-surface)}
.fa-fixed-row>span{display:flex;flex-wrap:wrap;gap:4px 16px}
.fa-was{text-decoration:line-through;text-decoration-color:var(--hk-idle-fill)}
.fa-sample-tag{display:inline-flex;gap:6px;align-items:center;justify-self:start;font-size:var(--hk-fs-sm);font-weight:600;padding:2px 8px;border-radius:2px;border:1px solid var(--hk-stroke);background:var(--hk-sunken)}
.fa-replay{display:grid;gap:10px}
.fa-replay-head{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline}
.fa-replay-head h3{margin:0;font-size:15px;font-weight:600}
.fa-strip{position:relative;height:64px;border-radius:2px;background:var(--hk-sunken);border:1px solid var(--hk-stroke)}
.fa-strip-lane{position:absolute;left:12px;right:12px;height:1px;background:var(--hk-stroke)}
.fa-strip-lane[data-lane=chat]{top:20px}
.fa-strip-lane[data-lane=files]{top:44px}
.fa-strip-dot{position:absolute;width:12px;height:12px;margin:-6px 0 0 -6px;border-radius:50%;border:2px solid var(--hk-surface);background:var(--hk-idle-fill);padding:0;cursor:pointer}
.fa-strip-dot[data-lane=chat]{top:20px}
.fa-strip-dot[data-lane=files]{top:44px}
.fa-strip-dot[data-bracket]{background:var(--hk-warn-fill)}
.fa-strip-dot:focus-visible{outline:2px solid var(--hk-accent);outline-offset:2px}
.fa-strip-bracket{position:absolute;top:14px;height:36px;width:0;border-left:3px solid var(--hk-warn-fill)}
.fa-strip-label{position:absolute;left:8px;font-size:12px;font-weight:600;line-height:1;padding:0 4px;background:var(--hk-sunken)}
.fa-strip-label[data-lane=chat]{top:14px}
.fa-strip-label[data-lane=files]{top:38px}
.fa-replay-detail{display:grid;gap:6px;padding:10px 12px;border-radius:2px;border:1px solid var(--hk-accent);background:var(--hk-surface)}
.fa-replay-detail code{font-family:var(--hk-mono);font-size:12px;overflow-wrap:anywhere}
.fa-replay-excerpt{margin:0;font-family:var(--hk-mono);font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere;padding:7px 9px;border-radius:2px;background:var(--hk-sunken)}
.fa-replay-excerpt mark{background:color-mix(in srgb,var(--hk-warn-fill) 30%,transparent);color:inherit}
.fa-strip-head{position:absolute;top:4px;bottom:4px;width:2px;margin-left:-1px;background:var(--hk-accent);transition:left 600ms var(--hk-ease)}
.fa-replay-grid{display:grid;grid-template-columns:4.5rem minmax(0,1fr) minmax(0,1fr);gap:0 12px}
.fa-replay-grid>.fa-replay-lanes{display:contents}
.fa-replay-lane-title{font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;padding-bottom:6px;border-bottom:1px solid var(--hk-stroke)}
.fa-replay-row{display:contents}
.fa-replay-time{font-size:var(--hk-fs-sm);font-variant-numeric:tabular-nums;padding:10px 0}
.fa-replay-cell{display:grid;gap:6px;align-content:start;padding:8px 0;border-bottom:1px solid var(--hk-stroke);min-width:0}
.fa-ev{display:grid;gap:3px;padding:8px 10px;border-radius:2px;border:1px solid var(--hk-stroke);background:var(--hk-surface);min-width:0}
.fa-ev strong{font-weight:600}
.fa-ev p{margin:0;overflow-wrap:anywhere}
.fa-ev-note{display:inline-flex;gap:6px;align-items:center;font-size:var(--hk-fs-sm);font-weight:600}
.fa-ev:not([data-bracket])>p{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.fa-replay-row .fa-ev:not([data-bracket]){padding:6px 10px}
.fa-ev code{font-family:var(--hk-mono);font-size:12px;overflow-wrap:anywhere}
.fa-ev[data-bracket]{border:2px solid var(--hk-warn-fill);background:color-mix(in srgb,var(--hk-warn-fill) 10%,var(--hk-surface))}
.fa-ev[data-picked]{outline:2px solid var(--hk-accent);outline-offset:1px}
.fa-ev-deep{font-family:var(--hk-mono);font-size:12px;padding:4px 6px;border-radius:2px;background:var(--hk-sunken)}
.fa-ev-pin{display:grid;gap:4px;padding:6px 8px;border-radius:2px;border-left:3px solid var(--hk-accent);background:var(--hk-sunken)}
.fa-ev-pin p{margin:0}
.fa-meter{display:grid;gap:3px}
.fa-meter-bar{height:6px;border-radius:2px;background:var(--hk-sunken);overflow:hidden}
.fa-meter-bar span{display:block;height:100%;background:var(--hk-idle-fill)}
.fa-bracket-words{grid-column:2/-1;display:flex;gap:8px;align-items:center;padding:6px 10px;margin:4px 0 2px;border-radius:2px;background:color-mix(in srgb,var(--hk-warn-fill) 16%,transparent);font-weight:600}
@container (max-width:600px){
  .fa-replay-grid{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
  .fa-replay-time{grid-column:1/-1;padding:8px 0 0}
  .fa-replay-lanes>.fa-replay-spacer{display:none}
  .fa-bracket-words{grid-column:1/-1}
}
.fa-ff{display:grid;gap:18px;grid-template-columns:minmax(0,1fr);padding:20px;border:1px solid var(--hk-stroke);border-radius:2px;background:var(--hk-surface)}
@container (min-width:860px){.fa-ff{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);align-items:center}}
.fa-ff h2{margin:0;font-size:28px;line-height:1.15;font-weight:600}
.fa-ff-copy>p{margin:0;font-size:15px;max-width:52ch}
.fa-ff-still{pointer-events:none}
.fa-still-cards{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:10px}
.fa-ff-still .fa-ev{padding:6px 8px}
.fa-top{display:grid;gap:16px;grid-template-columns:minmax(0,1fr);align-items:start}
@container (min-width:1000px){.fa-top{grid-template-columns:minmax(0,1fr) 340px}}
.fa-top-map,.fa-top-start{min-width:0}
.fa-top-start{display:grid;gap:12px;align-content:start}
.fa-switch{display:flex;gap:10px;align-items:flex-start;cursor:pointer;max-width:70ch}
.fa-switch input{margin-top:3px;width:16px;height:16px;flex:none;accent-color:var(--fa-blaze,currentColor)}
.fa-top-map{container-type:inline-size}
@container (max-width:700px){.fa-map-head span{font-size:12px;letter-spacing:0}}
@container (max-width:520px){.fa-map-head span{font-size:0}.fa-map-head span::first-letter{font-size:12px}}
.fa-ff-compact{grid-template-columns:minmax(0,1fr)!important;gap:14px;padding:16px}
.fa-ff-compact h2{font-size:20px}
.fa-ff-compact .fa-ff-copy>p{font-size:14px}
.fa-ff-actions{display:flex;flex-wrap:wrap;gap:8px}
.fa-guess{display:grid;gap:14px}
.fa-guess{max-width:720px}
.fa-guess h3{margin:0;font-size:26px;line-height:1.2;font-weight:600}
.fa-choices{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(min(100%,15rem),1fr))}
.fa-choice{display:flex;gap:10px;align-items:center;text-align:left;font:inherit;font-size:15px;color:inherit;padding:16px 16px;border-radius:2px;border:1px solid var(--hk-stroke);background:var(--hk-surface);cursor:pointer}
.fa-choice:hover{border-color:var(--hk-accent)}
.fa-choice[aria-pressed=true]{border:2px solid var(--hk-accent);background:var(--hk-active);font-weight:600;padding:15px 15px}
.fa-choice:focus-visible{outline:2px solid var(--hk-accent);outline-offset:2px}
.fa-choice:disabled{cursor:default}
.fa-chips{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.fa-chip-btn{font:inherit;color:inherit;padding:5px 12px;border-radius:2px;border:1px solid var(--hk-stroke);background:var(--hk-surface);cursor:pointer}
.fa-chip-btn[aria-pressed=true]{border-color:var(--hk-accent);background:var(--hk-active);font-weight:600}
.fa-chip-btn:focus-visible{outline:2px solid var(--hk-accent);outline-offset:2px}
.fa-toggles{display:grid;gap:8px}
.fa-tog{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center;padding:8px 12px;border-radius:2px;border:1px solid var(--hk-stroke);background:var(--hk-surface)}
.fa-tog-pair{display:inline-flex;border:1px solid var(--hk-stroke);border-radius:2px;overflow:hidden}
.fa-tog-pair button{font:inherit;color:inherit;padding:4px 12px;border:0;background:var(--hk-surface);cursor:pointer;min-width:5.5rem}
.fa-tog-pair button+button{border-left:1px solid var(--hk-stroke)}
.fa-tog-pair button[aria-pressed=true]{background:var(--hk-accent);color:var(--dt-primary-foreground,var(--hk-surface));font-weight:600}
.fa-tog-pair button:disabled{cursor:default}
.fa-tog-pair button:focus-visible{outline:2px solid var(--hk-accent);outline-offset:-2px}
.fa-progress{display:grid;gap:6px;margin:0;padding:0;list-style:none}
.fa-progress li{display:grid;grid-template-columns:20px minmax(0,1fr) auto;gap:8px;align-items:center}
.fa-progress [data-state=done] .codicon{color:var(--hk-good)}
.fa-progress span:last-child{font-variant-numeric:tabular-nums;font-size:var(--hk-fs-sm)}
.fa-grade{display:grid;gap:10px;padding:12px 14px;border-radius:2px;border:1px solid var(--hk-stroke);background:var(--hk-surface)}
.fa-grade-level{font-size:22px;font-weight:600}
.fa-grade dl{display:grid;grid-template-columns:7rem minmax(0,1fr);gap:6px 12px;margin:0}
.fa-grade dt{font-weight:600}
.fa-grade dd{margin:0}
.fa-grade blockquote{margin:0;padding:8px 10px;border-radius:2px;background:var(--hk-sunken)}
.fa-grade mark{background:color-mix(in srgb,var(--hk-warn-fill) 34%,transparent);color:inherit;padding:0 2px;border-radius:2px}
.fa-explain{display:grid;gap:4px;padding:8px 10px;border-radius:2px;border-left:3px solid var(--hk-accent);background:var(--hk-sunken)}
.fa-explain p{margin:0}
.fa-result-split{display:grid;gap:10px}
@container (min-width:1000px){.fa-result-split{grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:start}}
.fa-cover{display:grid;gap:10px;padding:16px 18px;border-radius:2px;border:1px solid var(--hk-stroke);border-left:4px solid var(--hk-accent);background:var(--hk-surface)}
.fa-cover-line{font-size:32px;line-height:1.15;font-weight:600;margin:0}
`

export function createDeskViews(ui) {
  const { ctxRest, post, errorText, copyText, openPracticeChat, draftInPractice, Problem } = ui

  /* ------------------------------------------------------------- the rail -- */

  function PhaseRail({ states, at, onPick }) {
    const rows = phaseRows(states, at)
    return jsx('nav', { className: 'fa-desk-rail', 'aria-label': 'Mission steps', children: jsx('ol', { className: 'fa-rail', children: rows.map(p => jsxs('li', { children: [
      jsx('h3', { children: p.title }, 'h'),
      p.locked ? jsxs('div', { className: 'fa-rail-lock', children: [jsx(Codicon, { name: 'lock', size: 12 }), p.lockLine] }, 'lock')
        : jsx('ol', { children: p.steps.filter(s => s.status !== 'skipped').map(s => jsx('li', { 'data-status': s.status, children: s.status === 'locked'
          ? jsxs('span', { className: 'fa-rail-step-locked', children: [jsx(Codicon, { name: 'circle-small', size: 14 }), s.title] })
          : jsxs('button', { type: 'button', 'aria-current': s.id === at ? 'step' : undefined, onClick: () => onPick(s.id), children: [
            jsx(Codicon, { name: s.status === 'done' ? 'pass-filled' : s.status === 'skipped' ? 'dash' : s.id === at ? 'circle-filled' : 'circle-large-outline', size: 14 }),
            p.id === 'learn' && s.status === 'open' ? `${s.title} (optional)` : s.title,
          ] }) }, s.id)) }, 'steps'),
    ] }, p.id)) }) })
  }

  function PhaseBar({ states, at }) {
    return jsxs('div', { className: 'fa-desk-bar', children: [
      jsx('strong', { children: phaseBarWords(states, at) }),
      jsx('ol', { 'aria-hidden': 'true', children: phaseRows(states, at).map(p => jsx('li', { 'data-state': p.current ? 'now' : p.done ? 'done' : 'later' }, p.id)) }),
    ] })
  }

  /* ------------------------------------------------------ the guide data -- */

  /** The Field guide view for one attempt and step, looked at again every 1.5 s while anything is still fetching. */
  function useGuide(attemptId, step, runsKey) {
    const [state, setState] = useState({ view: null, error: '' })
    const [now, setNow] = useState(() => Date.now() / 1000)
    const load = async () => {
      if (!attemptId) return null
      try {
        const view = await ctxRest(`/guide/${attemptId}?step=${encodeURIComponent(step || '')}&active=own`)
        setState({ view, error: '' })
        return view
      } catch (e) {
        setState(s => ({ ...s, error: errorText(e) }))
        return null
      }
    }
    useEffect(() => { load() }, [attemptId, step, runsKey])
    const fetching = guideFetching(state.view)
    useEffect(() => {
      if (!fetching) return undefined
      const t = setInterval(() => { setNow(Date.now() / 1000); load() }, 1500)
      return () => clearInterval(t)
    }, [fetching, attemptId, step])
    return { ...state, now, reload: load, setView: view => setState(s => ({ ...s, view })) }
  }

  function Fetching({ startedAt, now, what }) {
    return jsxs('div', { className: 'fa-guide-wait', role: 'status', children: [jsx(Spinner, {}), `${what}. ${fetchingWords(startedAt, now)}`] })
  }

  function Said({ text, from }) {
    if (!text) return null
    return jsxs('div', { className: 'fa-guide-said', children: [jsx('p', { children: text }), from ? jsx('span', { className: 'fa-guide-from', children: from }) : null] })
  }

  function failureOf(part) {
    const p = part || {}
    return ['no_model', 'timeout', 'bad_json', 'provider_error', 'too_long'].includes(p.state) ? p : null
  }

  function Failure({ part, onRetry }) {
    const f = failureOf(part)
    if (!f) return null
    return jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
      jsx(Notice, { tone: f.state === 'bad_json' ? 'info' : 'warn', title: f.message || 'Your model didn\'t answer.', children: f.next_step || '' }),
      jsxs('div', { className: 'hk-actions', children: [
        f.state === 'no_model' ? jsx(Button, { onClick: () => { try { host.navigate('/settings?tab=config:model') } catch (e) { /* older Hermes */ } }, children: 'Open model settings' }, 'models') : null,
        onRetry ? jsx(Button, { variant: 'secondary', onClick: onRetry, children: 'Try again' }, 'retry') : null,
      ] }),
    ] })
  }

  /* ------------------------------------------------------ Field guide column -- */

  /** The Field guide column. What it holds depends on the step: the hunt ladder after a missed check, notes on the
   *  replay at Compare, Do it with me at Fix, and Ask on every step it is open on. */
  function FieldGuide({ guide, attemptId, step, missed, onOpenCompare, practiceName, onTurnOn, onTurnOff, onScoreAnswer, noRun = false, fixed = false }) {
    const [open, setOpen] = useState(false)
    const [shown, setShown] = useState({})
    const [busy, setBusy] = useState('')
    const [error, setError] = useState('')
    const v = guide.view
    const help = async (body, key) => {
      setBusy(key); setError('')
      try {
        const out = await post(`/guide/${attemptId}/help`, { ...body, step })
        setShown(s => ({ ...s, [key]: out?.shown || {} }))
        await guide.reload()
        return out
      } catch (e) {
        setError(errorText(e))
        return null
      } finally { setBusy('') }
    }
    const used = usedRungs(v)
    const nudge = v?.ladder?.nudge || {}
    const nudgeText = nudge.text || shown.nudge?.text || ''
    const whereText = v?.ladder?.where?.text || shown.where?.text || ''
    const body = []
    if (!v) {
      body.push(guide.error ? jsx('p', { children: 'The Field guide couldn\'t load just now. Your checks still work.' }, 'e') : jsx('p', { children: 'Opening your guide.' }, 'l'))
    } else if (!v.enabled) {
      body.push(jsx('p', { children: v.off_words || 'The guide is off for this step.' }, 'off'))
      if (v.off_reason === 'switch' && onTurnOn) body.push(jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: onTurnOn, children: 'Turn on AI help' }) }, 'on'))
    } else {
      if (step === 'check' && missed) {
        body.push(jsxs('section', { className: 'fa-guide-sec', 'aria-label': 'Find out why', children: [
          jsx('h3', { children: 'Find out why' }),
          jsx('p', { children: 'Try to find the cause in your practice chat first.' }),
          jsxs('div', { className: 'fa-guide-buttons', children: [
            jsx(Button, { variant: used.nudge ? 'secondary' : undefined, loading: busy === 'nudge', onClick: () => help({ rung: 1 }, 'nudge'), children: 'Give me a hint' }, 'n'),
            jsx(Button, { variant: 'secondary', loading: busy === 'where', onClick: () => help({ rung: 2 }, 'where'), children: 'Show me where to look' }, 'w'),
            jsx(Button, { variant: 'secondary', loading: busy === 'reveal', onClick: async () => { const out = await help({ rung: 3 }, 'reveal'); if (out && onOpenCompare) onOpenCompare() }, children: 'Show me the answer' }, 'r'),
          ] }),
          nudge.state === 'fetching' && (used.nudge || busy === 'nudge') ? jsx(Fetching, { startedAt: nudge.started_at, now: guide.now, what: 'Your model is reading your chat' }) : null,
          failureOf(nudge) ? jsx(Failure, { part: nudge, onRetry: () => help({ rung: 1, regenerate: true }, 'nudge') }) : null,
          used.nudge && nudgeText ? jsx(Said, { text: nudgeText, from: nudge.source === 'model' ? 'Hint, written by your model from your own chat' : 'Hint, from the course' }) : null,
          used.where && whereText ? jsx(Said, { text: whereText, from: 'Where to look, from the course' }) : null,
        ] }, 'hunt'))
      }
      if (step === 'check' && !missed) {
        body.push(jsx('p', { children: v.ladder?.nudge?.state === 'not_started' ? 'Run the check. If one misses, the guide helps you hunt for why.' : 'Every check met. Ask about anything in this mission.' }, 'idle'))
      }
      if (step === 'compare') body.push(jsx(WhyMissed, { v, attemptId, guide }, 'why'))
      if (step === 'compare') body.push(jsx(PinsPanel, { v, attemptId, guide, noRun }, 'pins'))
      if (step === 'fix' && fixed) body.push(jsx('section', { className: 'fa-guide-sec', children: jsx('p', { children: 'Your fix worked. Next, do the job once more, a little differently, in the main column.' }) }, 'fixed'))
      else if (step === 'fix' && v.do_it_with_me) body.push(jsx(DoItWithMe, { d: v.do_it_with_me, guide }, 'diwm'))
      body.push(jsx(AskPanel, { v, attemptId, step, guide, practiceName }, 'ask'))
    }
    if (error) body.push(jsx(Problem, { text: error }, 'err'))
    const words = v?.help?.words
    return jsxs('aside', { className: 'fa-desk-guide', 'data-open': open ? 'true' : 'false', 'aria-label': 'Field guide', children: [
      jsxs('div', { className: 'fa-guide-tab', children: [
        jsxs('button', { type: 'button', className: 'fa-guide-tab-toggle', 'aria-expanded': open, onClick: () => setOpen(!open), children: [
          jsx(Codicon, { name: 'compass', size: 16 }),
          `Field guide${v && v.enabled === false ? '' : step === 'check' && missed ? ': find out why' : step === 'compare' ? ': notes on your run' : step === 'fix' && v?.do_it_with_me && !fixed ? ': the fix, step by step' : ''}`,
          jsx(Codicon, { name: open ? 'chevron-down' : 'chevron-up', size: 16 }),
        ] }),
        v && v.enabled !== false && step === 'check' && missed && !open && !used.nudge
          ? jsx(Button, { onClick: async () => { setOpen(true); await help({ rung: 1 }, 'nudge') }, children: 'Give me a hint' }) : null,
      ] }),
      jsxs('div', { className: 'fa-guide', children: [
        jsxs('h2', { children: [jsx(Codicon, { name: 'compass', size: 16 }), 'Field guide'] }),
        ...body,
        v && v.enabled !== false ? jsxs('div', { className: 'fa-guide-foot', children: [
          words ? jsx('p', { children: `${words} so far.` }, 'w') : null,
          onTurnOff ? jsx(Button, { variant: 'ghost', onClick: onTurnOff, children: 'Turn off AI help' }, 'off') : null,
        ] }, 'foot') : null,
      ] }),
    ] })
  }

  function PinsPanel({ v, attemptId, guide, noRun = false }) {
    const [busy, setBusy] = useState(false)
    const [made, setMade] = useState(null)
    const pins = v.pins?.length ? v.pins : made?.pins || []
    const make = async () => {
      setBusy(true)
      try { setMade(await post(`/guide/${attemptId}/pins`, { make: true, step: 'compare' })); await guide.reload() } catch (e) { setMade({ state: 'provider_error', message: errorText(e) }) } finally { setBusy(false) }
    }
    const mark = async (id, keep) => {
      await post(`/guide/${attemptId}/pins`, keep ? { keep: [id] } : { dismiss: [id] }).catch(() => null)
      await guide.reload()
    }
    return jsxs('section', { className: 'fa-guide-sec', 'aria-label': 'Notes on your run', children: [
      jsx('h3', { children: 'Notes on your run' }),
      pins.length ? jsx('ol', { className: 'hk-stack', style: { gap: 8, margin: 0, padding: 0, listStyle: 'none' }, children: pins.filter(p => p.kept !== false).map((p, i) => jsxs('li', { className: 'fa-guide-said', children: [
        jsx('p', { children: [jsx('strong', { children: `${i + 1}. ` }, 'n'), p.why] }),
        jsxs('div', { className: 'fa-chips', children: [
          p.kept ? jsx('span', { className: 'fa-guide-from', children: 'Kept in your record' }) : jsx(Button, { variant: 'secondary', onClick: () => mark(p.event_id, true), children: 'Keep' }),
          jsx(Button, { variant: 'ghost', onClick: () => mark(p.event_id, false), children: 'Dismiss' }),
        ] }),
      ] }, p.event_id)) }) : null,
      !pins.length && noRun ? jsx('p', { children: 'Notes come once there is a chat to replay.' }) : null,
      !pins.length && !noRun && !failureOf(made) ? jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx('p', { children: 'Your model can point out the moments in your run that explain the result.' }),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: busy, onClick: make, children: 'Point out the key moments' }) }),
      ] }) : null,
      failureOf(made) ? jsx(Failure, { part: made, onRetry: make }) : null,
      pins.length ? jsx('span', { className: 'fa-guide-from', children: 'Written by your model from your own run.' }) : null,
    ] })
  }

  /** Why the fix works: one line from the learner's model (or the course). The commands themselves sit in the Fix step's
   *  main column (FixCommands), so they are there with AI help off too. */
  function DoItWithMe({ d, guide }) {
    const why = d.why || {}
    return jsxs('section', { className: 'fa-guide-sec', 'aria-label': 'Why this fixes it', children: [
      jsx('h3', { children: 'Why this fixes it' }),
      why.state === 'fetching' ? jsx(Fetching, { startedAt: why.started_at, now: guide.now, what: 'Your model is writing why' }) : null,
      why.state === 'ready' && why.text ? jsx(Said, { text: why.text, from: why.source === 'model' ? 'From your model' : 'From the course' }) : null,
    ] })
  }

  /** The fix for a held save, in the main column: the two commands (the id read from the held file's name), a button
   *  that puts the first in the practice chat's box without sending, and a copy button. */
  function FixCommands({ commands, attemptId, practiceName }) {
    const [drafted, setDrafted] = useState('')
    // Which command the button drafts next. Each press puts one command in the practice chat's box, so the learner never
    // types a slash command by hand: Hermes's command picker opens on "/" and a typed one went wrong in a live run.
    const [next, setNext] = useState(0)
    const text = commands.join('\n')
    const ordinal = i => ['first', 'second', 'third', 'fourth'][i] || `next`
    return jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
      jsx('ol', { className: 'fa-guide-cmd', children: commands.map(c => jsx('li', { children: jsx('code', { children: c }) }, c)) }),
      jsxs('div', { className: 'fa-f-row', children: [
        jsx(Button, { variant: 'secondary', onClick: async () => {
          const i = Math.min(next, commands.length - 1)
          const ok = draftInPractice ? await draftInPractice(practiceName, commands[i] || '') : false
          const more = i + 1 < commands.length
          setDrafted(ok
            ? `The ${ordinal(i)} command is in the practice chat, not sent. Press Send there${more ? ', then come back and press this button for the next one.' : '.'}`
            : 'Copied. Paste them in the practice chat and press Send after each.')
          if (!ok) copyText(text, 'Copied the commands.')
          else setNext(more ? i + 1 : 0)
          if (i === 0) post(`/guide/${attemptId}/help`, { action: 'do_it_with_me', step: 'fix' }).catch(() => null)
        }, children: next > 0 && commands.length > 1 ? `Put the ${ordinal(next)} command in the practice chat` : 'Put it in the practice chat' }),
        jsx(Button, { variant: 'secondary', onClick: () => copyText(text, 'Copied the commands.'), children: 'Copy the commands' }),
      ] }),
      drafted ? jsx('p', { className: 'hk-small', role: 'status', style: { margin: 0 }, children: drafted }) : null,
    ] })
  }

  function AskPanel({ v, attemptId, step, guide, practiceName }) {
    const [q, setQ] = useState('')
    const [busy, setBusy] = useState(false)
    const [answer, setAnswer] = useState(null)
    const ask = async question => {
      const text = (question || q).trim()
      if (!text) return
      setQ(text); setBusy(true); setAnswer(null)
      try { setAnswer(await post(`/guide/${attemptId}/ask`, { question: text, step })); guide.reload() } catch (e) { setAnswer({ state: 'provider_error', message: errorText(e) }) } finally { setBusy(false) }
    }
    return jsxs('section', { className: 'fa-guide-sec', 'aria-label': 'Ask', children: [
      jsx('h3', { children: 'Ask' }),
      jsxs('form', { className: 'hk-stack', style: { gap: 6 }, onSubmit: e => { e.preventDefault(); ask() }, children: [
        jsx(Input, { value: q, onChange: e => setQ(e.target.value), placeholder: 'Ask about this mission', 'aria-label': 'Ask the field guide' }),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { type: 'submit', loading: busy, disabled: !q.trim(), children: 'Ask' }) }),
      ] }),
      !answer && (v.starters || []).length ? jsx('div', { className: 'fa-guide-chips', children: v.starters.map(s => jsx('button', { type: 'button', className: 'fa-guide-chip', onClick: () => ask(s), children: s }, s)) }) : null,
      answer && answer.state === 'ok' && answer.sentences?.length ? jsx('div', { className: 'fa-guide-said', children: answer.sentences.map((s, i) => jsxs('p', { children: [
        s.text, ...[...new Set((s.source_ids || []).map(sourceWords))].slice(0, 3).map(w => jsx('span', { className: 'fa-guide-src', title: 'Where this comes from', children: w }, w)),
      ] }, i)) }) : null,
      answer && answer.state === 'ok' && answer.not_in_sources ? jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx('p', { children: 'This lesson doesn\'t cover that.' }),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: async () => {
          const ok = draftInPractice ? await draftInPractice(practiceName, answer.draft_for_practice_chat || q) : false
          if (!ok) copyText(answer.draft_for_practice_chat || q, 'Copied the question. Paste it in the practice chat.')
        }, children: 'Ask it in the practice chat' }) }),
      ] }) : null,
      answer && answer.held_back ? jsx('p', { className: 'fa-guide-from', children: 'Part of the answer would give the snag away, so the guide kept to a hint.' }) : null,
      failureOf(answer) ? jsx(Failure, { part: answer, onRetry: () => ask() }) : null,
    ] })
  }

  /** Why did this miss?, on Compare: once the snag is revealed your model can name the cause for each check that
   *  missed (Nov 9: on Check it could only restate the headline). Its words show after the learner asks. */
  function WhyMissed({ v, attemptId, guide }) {
    const [busy, setBusy] = useState(false)
    const items = (v && v.explain) || []
    if (!items.length) return null
    const used = usedRungs(v).explain
    const ready = items.filter(i => i.sentences && i.sentences.length)
    const fetching = items.find(i => i.state === 'fetching')
    // The heading shows only over the answer: above the button it said the same words twice (round 15).
    return jsxs('section', { className: 'fa-guide-sec', 'aria-label': 'Why did this miss?', children: [
      used && ready.length ? jsx('h3', { children: 'Why did this miss?' }) : null,
      used && ready.length ? jsxs('div', { className: 'fa-explain', children: [
        ...explainMerged(ready).map((t, n) => jsx('p', { children: t }, n)),
        jsx('span', { className: 'fa-guide-from', children: ready.every(i => i.source === 'model') ? 'From your model' : 'From the course' }, 'f'),
      ] }) : jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: busy, onClick: async () => {
        setBusy(true)
        try { await post(`/guide/${attemptId}/help`, { action: 'explain', step: 'compare' }); await guide.reload() } finally { setBusy(false) }
      }, children: 'Why did this miss?' }) }),
      used && fetching ? jsx(Fetching, { startedAt: fetching.started_at, now: guide.now, what: 'Your model is reading the run' }) : null,
    ] })
  }

  /** Explain my miss, inside a failed check's card, beside its facts. Fetched when the check missed, so it shows at once. */
  function ExplainMiss({ guide, attemptId, checkId }) {
    const [busy, setBusy] = useState(false)
    const [asked, setAsked] = useState(false)
    const v = guide.view
    if (!v || !v.enabled) return null
    const item = (v.explain || []).find(e => e.check_id === checkId) || {}
    const used = usedRungs(v).explain
    const show = (asked || used) && item.sentences?.length
    // A model failure here is said once, in the guide column; the card keeps its button for a later try.
    if (failureOf(item) && !asked) return null
    return jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
      show ? jsxs('div', { className: 'fa-explain', children: [...explainShown(item.sentences).map((s, i) => jsx('p', { children: s }, i)), jsx('span', { className: 'fa-guide-from', children: item.source === 'model' ? 'Field guide, from your model' : 'Field guide, from the course' }, 'f')] })
        : jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: busy, onClick: async () => {
          setBusy(true)
          try { await post(`/guide/${attemptId}/help`, { action: 'explain', step: 'check' }); setAsked(true); await guide.reload() } finally { setBusy(false) }
        }, children: 'Why did this miss?' }) }),
      (asked || used) && item.state === 'fetching' ? jsx(Fetching, { startedAt: item.started_at, now: guide.now, what: 'Your model is reading the check' }) : null,
      failureOf(item) ? jsx(Notice, { tone: 'warn', children: item.message || 'Your model didn\'t answer. The Field guide says what to try.' }) : null,
    ] })
  }

  /* -------------------------------------------------------------- replay -- */

  /** The run for Compare and Fix. A failed or silent request ends as an error with retry(), never an endless
   *  "Loading your run." (Loop 3 live gate: the gateway failed and the page waited forever). */
  const REPLAY_WAIT_MS = 20000

  function useReplay(attemptId, step, sample) {
    const [state, setState] = useState({ data: sample || null, error: '' })
    const [tries, setTries] = useState(0)
    useEffect(() => {
      let live = true
      if (sample) { setState({ data: sample, error: '' }); return undefined }
      if (!attemptId) return undefined
      setState({ data: null, error: '' })
      const timer = setTimeout(() => { if (live) setState(s => (s.data ? s : { data: null, error: 'timeout' })) }, REPLAY_WAIT_MS)
      ctxRest(`/replay/${attemptId}?step=${encodeURIComponent(step || 'compare')}`)
        .then(data => { if (live) setState({ data, error: '' }) })
        .catch(e => { if (live) setState({ data: null, error: errorText(e) || 'error' }) })
        .finally(() => clearTimeout(timer))
      return () => { live = false; clearTimeout(timer) }
    }, [attemptId, step, sample || null, tries])
    return { ...state, retry: () => setTries(n => n + 1) }
  }

  function Meter({ m }) {
    const used = Number(m.used) || 0
    const limit = Number(m.limit) || 0
    return jsxs('div', { className: 'fa-meter', children: [
      jsx('div', { className: 'fa-meter-bar', role: 'img', 'aria-label': `${used} of ${limit} characters`, children: jsx('span', { style: { width: `${limit ? Math.min(100, (used / limit) * 100) : 0}%` } }) }),
      jsx('span', { className: 'hk-small', children: `${m.changed ? 'Changed' : 'Unchanged'}, ${used.toLocaleString('en-US')} of ${limit.toLocaleString('en-US')}` }),
    ] })
  }

  function EventCard({ e, bracket, picked, pin }) {
    return jsxs('div', { className: 'fa-ev', id: `fa-ev-${e.event_id}`, 'data-bracket': bracket ? '' : undefined, 'data-picked': picked ? '' : undefined, children: [
      jsx('strong', { children: e.title || e.kind }),
      e.kind === 'tool:memory' && e.text ? jsx('p', { className: 'fa-ev-deep', children: e.text })
        // A held save reads as one plain sentence, not Hermes's raw summary (Loop 3 live gate).
        : e.kind === 'file:pending' && e.text ? jsx('p', { children: heldSentence(e.text).sentence })
          : e.text && e.kind !== 'file:memory' && !/^\(called /.test(e.text) ? jsx('p', { children: e.text }) : null,
      // A held save's file name is a random id; the folder says what matters. Other paths show whole.
      e.path ? jsx('code', { title: e.path, children: /\/[0-9a-f]{6,}\.json$/.test(e.path) ? `${e.path.split('/').slice(0, -1).join('/')}/` : e.path }) : null,
      e.meter ? jsx(Meter, { m: e.meter }) : null,
      pin ? jsxs('span', { className: 'fa-ev-note', children: [jsx(Codicon, { name: 'compass', size: 14 }), `Note ${pin.n} in the Field guide`] }) : null,
    ] })
  }

  /** Replay your run: two lanes on one time line, the chat on the left and Hermes's files on the right, with the
   *  amber bracket where the chat says one thing and the files another. */
  function Replay({ attemptId, sample, pins = [], still = false, play = false, onSample, onState }) {
    const { data, error } = useReplay(attemptId, 'compare', sample)
    useEffect(() => { if (onState && data) onState(data.state) }, [data && data.state])
    const [picked, setPicked] = useState('')
    const [head, setHead] = useState(play ? 0 : -1)
    const rows = data && data.state === 'ready' ? replayRows(data) : []
    const target = bracketAt(rows)
    useEffect(() => {
      if (!play || target < 0) return undefined
      const reduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
      if (reduced) { setHead(target); return undefined }
      const t = setTimeout(() => setHead(target), 300)
      return () => clearTimeout(t)
    }, [play, target])
    if (error) return jsx(Problem, { text: error })
    if (!data) return jsx('p', { children: 'Loading the replay.' })
    if (data.state !== 'ready') {
      return jsxs('div', { className: 'fa-replay', children: [
        jsx('div', { className: 'fa-replay-head', children: jsx('h3', { children: 'Replay your run' }) }),
        jsx(Notice, { tone: 'info', title: data.state === 'empty' ? 'No chat to replay yet' : data.state === 'schema_changed' ? 'Hermes changed how it stores chats' : 'The replay opens at Compare',
          children: data.words || (data.state === 'schema_changed' ? 'Hermes changed how it stores chats. Your checks still work.' : '') }),
        data.state === 'empty' && onSample ? jsx('div', { className: 'hk-actions', children: jsx(Button, { onClick: onSample, children: 'See a sample run' }) }) : null,
      ] })
    }
    const pickedEvent = picked ? (data.events || []).find(e => e.event_id === picked) : null
    const shownPins = pins.filter(p => p.kept !== false)
    const pinFor = id => { const i = shownPins.findIndex(p => p.event_id === id); return i < 0 ? null : { ...shownPins[i], n: i + 1 } }
    const all = rows.flatMap(r => [...r.chat, ...r.files])
    const x = i => (rows.length > 1 ? 16 + (i / (rows.length - 1)) * 74 : 50)
    const words = bracketWords(data)
    return jsxs('div', { className: still ? 'fa-replay fa-ff-still' : 'fa-replay', children: [
      still ? null : jsxs('div', { className: 'fa-replay-head', children: [
        jsx('h3', { children: 'Replay your run' }),
        jsx('span', { className: 'hk-small', children: `${clockWords(data.started_at)} to ${clockWords(data.ended_at)}. ${all.length} moments, read from the practice profile.` }),
      ] }),
      jsxs('div', { className: 'fa-strip', role: 'group', 'aria-label': 'Time line of the run', children: [
        jsx('span', { className: 'fa-strip-lane', 'data-lane': 'chat' }),
        jsx('span', { className: 'fa-strip-lane', 'data-lane': 'files' }),
        target >= 0 ? jsx('span', { className: 'fa-strip-bracket', role: 'img', 'aria-label': words || 'The moment the chat and the files split', title: words || undefined, style: { left: `${x(rows.findIndex(r => r.bracket))}%` } }) : null,
        ...rows.flatMap((r, i) => [...r.chat.slice(0, 1), ...r.files.slice(0, 1)].map(e => jsx('button', { type: 'button', className: 'fa-strip-dot', 'data-lane': e.lane, 'data-bracket': r.bracket ? '' : undefined,
          style: { left: `${x(i)}%` }, 'aria-label': `${r.clock}: ${e.title || e.kind}`, tabIndex: still ? -1 : 0,
          onClick: () => { setPicked(e.event_id); const n = typeof document !== 'undefined' && document.getElementById(`fa-ev-${e.event_id}`); if (n && n.scrollIntoView) n.scrollIntoView({ block: 'nearest' }) } }, e.event_id))),
        head >= 0 ? jsx('span', { className: 'fa-strip-head', style: { left: `${x(Math.round(head * (rows.length - 1)))}%` } }) : null,
        jsx('span', { className: 'fa-strip-label', 'data-lane': 'chat', 'aria-hidden': 'true', children: 'Chat' }),
        jsx('span', { className: 'fa-strip-label', 'data-lane': 'files', 'aria-hidden': 'true', children: 'Files' }),
      ] }),
      !still && pickedEvent ? jsxs('div', { className: 'fa-replay-detail', role: 'region', 'aria-label': 'The moment you picked', children: [
        jsxs('div', { className: 'fa-replay-head', children: [jsx('h3', { children: pickedEvent.title || pickedEvent.kind }), jsx('span', { className: 'hk-small', children: `${clockWords(pickedEvent.at)}, ${pickedEvent.lane === 'files' ? 'in Hermes\'s files' : 'in your chat'}` })] }),
        pickedEvent.path ? jsx('code', { children: pickedEvent.path }) : null,
        pickedEvent.text ? jsx('pre', { className: 'fa-replay-excerpt', children: jsx('mark', { children: pickedEvent.text }) }) : null,
        pickedEvent.meter ? jsx(Meter, { m: pickedEvent.meter }) : null,
      ] }) : null,
      // The home still shows the question, not the answer: the chat's own claim beside a file still to be read.
      still ? jsxs('div', { className: 'fa-still-cards', 'aria-hidden': 'true', children: [
        jsxs('div', { className: 'fa-ev', 'data-bracket': '', children: [jsx('span', { className: 'fa-guide-from', children: 'What the chat shows' }), jsxs('strong', { style: { display: 'flex', gap: 6, alignItems: 'center' }, children: [jsx(Codicon, { name: 'pass', size: 14 }), 'Saved to memory'] })] }),
        jsxs('div', { className: 'fa-ev', 'data-bracket': '', children: [jsx('span', { className: 'fa-guide-from', children: 'What Hermes\'s files show' }), jsx('strong', { children: 'You find out after the job' })] }),
      ] }) : jsxs('div', { className: 'fa-replay-grid', children: [
        jsxs('div', { className: 'fa-replay-lanes', children: [
          jsx('span', { className: 'fa-replay-spacer' }),
          jsx('span', { className: 'fa-replay-lane-title', children: (data.lanes || []).find(l => l.id === 'chat')?.label || 'In your chat' }),
          jsx('span', { className: 'fa-replay-lane-title', children: (data.lanes || []).find(l => l.id === 'files')?.label || 'In Hermes\'s files' }),
        ] }),
        ...rows.map((r, i) => jsxs('div', { className: 'fa-replay-row', children: [
          jsx('span', { className: 'fa-replay-time', children: r.clock }),
          jsx('div', { className: 'fa-replay-cell', children: r.chat.map(e => jsx(EventCard, { e, bracket: r.bracket && e.event_id === data.bracket.from, picked: picked === e.event_id, pin: pinFor(e.event_id) }, e.event_id)) }),
          jsx('div', { className: 'fa-replay-cell', children: r.files.map(e => jsx(EventCard, { e, bracket: r.bracket && e.event_id === data.bracket.to, picked: picked === e.event_id, pin: pinFor(e.event_id) }, e.event_id)) }),
        ] }, `${r.at}-${i}`)),
      ] }),
    ] })
  }

  /* --------------------------------------------------------------- hero -- */

  /** Compare's headline: one plain sentence about what Hermes did in this run, built from the run (runHeadline), then
   *  how the learner's own score compared and their guess. No score slogan. */
  function CompareHero({ headline, detail, score, sampleLabel, guess = '' }) {
    return jsxs('div', { className: 'fa-hero', children: [
      sampleLabel ? jsxs('span', { className: 'fa-sample-tag', children: [jsx(Codicon, { name: 'play-circle', size: 14 }), sampleLabel] }) : null,
      jsx('h2', { className: 'fa-hero-line', 'data-hero': '', children: headline || 'Here is what Hermes did in your practice run.' }),
      detail ? jsx('p', { className: 'fa-hero-sub', 'data-detail': '', children: detail }) : null,
      score || guess ? jsx('p', { className: 'fa-hero-sub', children: [
        score ? jsx('span', { children: `${score} ` }, 's') : null,
        guess ? jsx('span', { children: guess }, 'g') : null,
      ] }) : null,
    ] })
  }

  /* ---------------------------------------------------------- the inline grade -- */

  /** Score my answer: the learner's own model reads the answer and gives a level, what's right, what's missing and
   *  what to add next, with one quote marked inside the answer. */
  function InlineGrade({ missionId, attemptId, answer, initial }) {
    const [out, setOut] = useState(initial || null)
    const [busy, setBusy] = useState(false)
    const [started, setStarted] = useState(0)
    const [now, setNow] = useState(0)
    useEffect(() => {
      if (!busy) return undefined
      const t = setInterval(() => setNow(Date.now() / 1000), 1000)
      return () => clearInterval(t)
    }, [busy])
    const run = async () => {
      setBusy(true); setStarted(Date.now() / 1000); setNow(Date.now() / 1000); setOut(null)
      try { setOut(await post(`/ai/grade/${encodeURIComponent(missionId)}/explain@${attemptId}`, { answer })) } catch (e) { setOut({ state: 'provider_error', message: errorText(e) }) } finally { setBusy(false) }
    }
    return jsxs('div', { className: 'hk-stack', style: { gap: 8 }, children: [
      jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: busy, disabled: busy || answer.trim().length < 120, onClick: run, children: out && out.state === 'ok' ? 'Score it again' : 'Score my answer' }) }),
      busy ? jsxs('div', { className: 'fa-guide-wait', role: 'status', children: [jsx(Spinner, {}), `Your model is reading your answer, about 15 seconds. ${fetchingWords(started, now)}`, jsx(Button, { variant: 'ghost', onClick: () => setBusy(false), children: 'Cancel' })] }) : null,
      out && out.state === 'ok' ? jsxs('div', { className: 'fa-grade', children: [
        jsxs('div', { className: 'fa-row', style: { display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap' }, children: [
          jsx('span', { className: 'fa-grade-level', children: out.level_words || `Level ${out.level} of 4` }),
          jsx('span', { children: out.passed ? 'That passes.' : `Level ${out.pass_level} passes.` }),
        ] }),
        jsxs('dl', { children: [
          jsx('dt', { children: 'Right' }), jsx('dd', { children: out.right }),
          jsx('dt', { children: 'Missing' }), jsx('dd', { children: out.missing }),
          jsx('dt', { children: 'Add next' }), jsx('dd', { children: out.add_next }),
        ] }),
        out.quote ? jsx('blockquote', { 'aria-label': 'Your answer, with the line your model picked out', children: quoteParts(out.answer || answer, out.quote).map((p, i) => p.mark ? jsx('mark', { children: p.text }, i) : jsx('span', { children: p.text }, i)) }) : null,
        jsx('span', { className: 'fa-guide-from', title: out.model || '', children: 'Scored by your model. The level is saved to your record.' }),
      ] }) : null,
      out && out.state === 'off' ? jsx(Notice, { tone: 'info', children: out.message || 'AI help is off, so Score my answer is off too.' }) : null,
      failureOf(out) ? jsx(Failure, { part: out, onRetry: run }) : null,
    ] })
  }

  return { PhaseRail, PhaseBar, useGuide, useReplay, FieldGuide, ExplainMiss, Replay, CompareHero, InlineGrade, Said, Failure, FixCommands }
}
