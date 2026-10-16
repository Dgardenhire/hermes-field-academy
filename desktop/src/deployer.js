// Field Academy, the Deployer path screens. Built into desktop/plugin.js with the rest of the page.
//
// The path sits beside the four learning paths, in the same expedition look: four camps (Audit, Architect,
// Build and integrate, Staged verification), a waypoint for each part, and a summit that is the learner's own
// Field Record with the signature of a reviewer they chose. These screens share the page's helpers through `createDeployerViews(ui)`,
// which plugin.js calls once, so nothing here imports from plugin.js.
//
// What this half reads from Hermes it reads with the same read-only calls the mission checks use. It never
// writes, never starts a job and never runs a command. The backend judges what it reads.

import { useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'
import { Button, Codicon, Input, Textarea } from '@hermes/plugin-sdk'
import { Back, Card, Details, Facts, PageHeader, Pill, Ring, Section, useListKeys } from 'hermes-ui-kit'
import { CertCorners, Contours, ElevationProfile, Legend, Seal, TrailMark } from './field.js'
import { trailModel } from './trail.js'
import { stateWords } from './deploy.js'

export const DEPLOYER_CSS = `
.fa-dp-sections{margin:0;padding-left:22px;columns:2 14rem;column-gap:24px}
.fa-dp-sections>li{break-inside:avoid;padding:1px 0}
.fa-dp-note{white-space:pre-wrap;overflow-wrap:anywhere;padding:12px 14px;border-left:3px solid var(--fa-blaze);background:var(--hk-sunken);border-radius:0 var(--hk-radius-sm) var(--hk-radius-sm) 0;margin:0;font:inherit;line-height:1.55}
.fa-dp-path{font-family:var(--hk-mono);font-size:var(--hk-fs-sm);overflow-wrap:anywhere;padding:7px 9px;border-radius:var(--hk-radius-sm);background:var(--hk-sunken);margin:0}
.fa-dp-files{columns:2 16rem;column-gap:18px;margin:0;padding:0;list-style:none;font-family:var(--hk-mono);font-size:var(--hk-fs-sm)}
.fa-dp-files li{break-inside:avoid;padding:1px 0;overflow-wrap:anywhere}
.fa-dp-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,18rem),1fr));gap:12px}
.fa-dp-state{display:inline-flex;gap:6px;align-items:center;font-size:var(--hk-fs-sm)}
.fa-dp-phase-rows{display:grid;gap:4px}
.fa-dp-rubric{display:grid;gap:6px;margin:0;padding:0;list-style:none}
.fa-dp-rubric li{display:grid;grid-template-columns:2.2rem 1fr;gap:10px;align-items:baseline}
.fa-dp-rubric b{font-weight:300;font-size:20px;line-height:1;font-variant-numeric:lining-nums tabular-nums;color:var(--fa-blaze-ink,var(--hk-ink))}
`

const TITLE_FOR_PART = {
  lab: 'Break-and-fix lab',
  brief: 'Client proposal',
  scenarios: 'Judgment scenarios',
  deploy: 'Real deployment',
  drills: 'Failure drills',
  walkthrough: 'Walkthrough and review',
}

/** Where an item on the trail opens. */
/** The recovery note's headings, in order. The same list as DRILL_SECTIONS in deployer_content.py. */
const NOTE_SECTIONS = ['What I did', 'How I knew', 'How I fixed it', 'How to stop it surprising a client']

export function partFor(id) {
  if (String(id).startsWith('lab.')) return { name: 'deployer', part: 'lab', id }
  return { name: 'deployer', part: id, id: '' }
}

export function createDeployerViews(ui) {
  const { Prose, withoutExampleWord, Frame, Label, Result, Feedback, ctxRest, errorText, shortDate, longDate, plural, sendToHermes, refreshDeployer, openFolder, copyText, readHermes, scrollToId } = ui

  /* ------------------------------------------------------------ small parts -- */

  function Steps({ items }) {
    return jsx('ol', { className: 'fa-numbered', children: items.map(text => jsx('li', { children: jsx('span', { children: text }) }, text)) })
  }

  function Bullets({ items }) {
    return jsx('ul', { className: 'fa-bullets', children: items.map(text => jsx('li', { children: text }, text)) })
  }

  function PartFrame({ part, title, lead, go, children }) {
    const up = () => go({ name: 'path', id: 'deployer' })
    return jsx(Frame, { width: 'narrow', up, children: [
      jsx(PageHeader, {
        back: jsx(Back, { label: 'Guide path', onClick: up }),
        eyebrow: jsx(Label, { children: TITLE_FOR_PART[part] || 'Guide' }), title, lead,
      }, 'head'),
      ...children,
    ] })
  }

  function StateTag({ state }) {
    const tone = state === 'verified' ? 'good' : state === 'awaiting_review' ? 'warn' : 'idle'
    return jsx(Pill, { tone, icon: state === 'verified' ? 'check' : state === 'awaiting_review' ? 'eye' : undefined, children: stateWords(state) })
  }

  /** Run one call, show what it said, and refresh the path. */
  function useAction(onDone) {
    const [busy, setBusy] = useState('')
    const [result, setResult] = useState(null)
    const run = async (name, call) => {
      if (busy) return null
      setBusy(name)
      setResult(null)
      try {
        const payload = await call()
        await refreshDeployer()
        if (onDone) onDone(payload)
        return payload
      } catch (error) {
        setResult({ error: true, passed: false, title: errorText(error) })
        return null
      } finally {
        setBusy('')
      }
    }
    return { busy, result, setResult, run }
  }

  /** The evidence panel every Hermes-reading check shows: what was read, and the fallback when Hermes cannot be read. */
  function ReadNote({ note, unreadable }) {
    if (!note && !unreadable) return null
    return jsx(Card, { tone: unreadable ? 'warn' : 'info', children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
      jsx(Label, { plain: true, children: unreadable ? 'Hermes could not be read for this' : 'What Field Academy read from Hermes' }),
      note ? jsx('p', { children: note }) : null,
      unreadable
        ? jsx('p', { children: 'Field Academy will not take your word for it. Add your own log excerpt below. It goes into the review packet, and your reviewer decides whether to accept it.' })
        : null,
    ] }) })
  }

  /** The fallback: a log excerpt for the reviewer. It never passes on its own. */
  function FallbackBox({ label, existing, post }) {
    const action = useAction()
    const [excerpt, setExcerpt] = useState('')
    const [notes, setNotes] = useState('')
    if (existing) {
      return jsx(Card, { tone: 'warn', tint: true, children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
        jsx('strong', { children: 'Waiting for the reviewer' }),
        jsx('p', { children: `Your excerpt (${existing.timestamps} timestamps over ${plural(existing.days, 'day', 'days')}) is in the review packet. This part counts only if the reviewer accepts it.` }),
      ] }) })
    }
    return jsx(Card, { children: jsxs('div', { className: 'hk-stack', children: [
      jsx(Label, { children: 'A packet for the reviewer' }),
      jsx('p', { children: `${label} Paste the lines of your own log that show each run, with the date and time. Keys and tokens are removed before it is kept.` }),
      jsx(Textarea, { style: { minHeight: '7rem', width: '100%' }, value: excerpt, onChange: e => setExcerpt(e.target.value), 'aria-label': 'Log excerpt', placeholder: '2026-10-03T09:00:02Z cron deployer-calendar ran ok' }),
      jsx(Input, { value: notes, onChange: e => setNotes(e.target.value), placeholder: 'A note for the reviewer, if any', 'aria-label': 'Note for the reviewer' }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: action.busy === 'fallback', onClick: () => action.run('fallback', () => post(excerpt, notes)), children: 'Add it to the review packet' }) }),
      jsx(Result, { result: action.result }),
    ] }) })
  }

  /* ------------------------------------------------------------------- path -- */

  function CertificatePanel({ data, go }) {
    const cert = data.certificate
    const reverify = cert.reverify
    const tone = cert.status === 'issued' ? 'good' : cert.status === 'ready' || cert.status === 'awaiting_review' ? 'warn' : 'info'
    return jsx('div', { id: 'fa-dp-route', children: jsx(Card, { tone, tint: cert.status !== 'in_progress' && cert.status !== 'not_started', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
      jsx(Label, { children: 'Summit' }),
      jsx('h2', { className: 'hk-h2', children: cert.label }),
      cert.status === 'awaiting_review'
        ? jsx('p', { children: 'Every part is done. Your Guide Field Record still needs the reviewer you chose to read and sign your packet. Until then you hold Guide, awaiting review.' })
        : cert.status === 'issued'
          ? jsx('p', { children: 'Created with the signed sign-off of the reviewer you chose, on the Hermes version shown on the record.' })
          : jsx('p', { children: 'Your Guide Field Record needs all nine parts of this path, and the signature of a reviewer you choose on your packet. Without that signature the most you hold is Guide, awaiting review.' }),
      reverify && reverify.status === 'reverify'
        ? jsx(Pill, { tone: 'warn', icon: 'history', children: 'Re-verify needed' })
        : reverify && reverify.status === 'current'
          ? jsx(Pill, { tone: 'good', icon: 'check', children: 'Current for this Hermes' })
          : null,
      reverify ? jsx('p', { className: 'hk-small', children: reverify.words }) : null,
      jsxs('div', { className: 'hk-actions', children: [
        cert.status === 'issued' ? jsx(Button, { onClick: () => go({ name: 'deployer', part: 'certificate', id: '' }), children: 'View your Field Record' }) : null,
        cert.status === 'ready' || cert.status === 'awaiting_review' ? jsx(Button, { onClick: () => go({ name: 'deployer', part: 'walkthrough', id: '' }), children: cert.status === 'ready' ? 'Create your Field Record' : 'Open the review' }) : null,
      ] }),
    ] }) }) })
  }

  function AboutPanel({ about }) {
    return jsxs('div', { className: 'fa-dp-two', children: [
      jsx(Card, { children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx(Label, { children: 'What it shows' }),
        jsx(Bullets, { items: about.shows || about.certifies }),
      ] }) }),
      jsx(Card, { children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx(Label, { children: 'What it does not' }),
        jsx(Bullets, { items: about.does_not }),
        jsx('p', { className: 'hk-small', children: about.issuer }),
        about.disclaimer ? jsx('p', { className: 'hk-small', children: about.disclaimer }) : null,
      ] }) }),
    ] })
  }

  function VersionPanel({ data }) {
    const version = data.hermes_version || { value: '' }
    const [text, setText] = useState('')
    const action = useAction()
    if (version.value) {
      return jsx(Card, { children: jsxs('div', { className: 'hk-row', style: { flexWrap: 'wrap', gap: 12 }, children: [
        jsxs('div', { className: 'hk-grow hk-stack', style: { gap: 2 }, children: [
          jsx(Label, { plain: true, children: 'Hermes version on record' }),
          jsx('strong', { children: version.value }),
          jsx('span', { className: 'hk-small', children: version.machine_read ? `Read from Hermes (${version.source}).` : 'You typed this. Field Academy could not read it, and the Field Record says so.' }),
        ] }),
        jsx('p', { className: 'hk-small', style: { maxWidth: '24rem' }, children: 'The Field Record shows this version. When the major version of Hermes changes, it shows Re-verify needed and asks you to repeat the four labs on new cases.' }),
      ] }) })
    }
    return jsx(Card, { tone: 'warn', children: jsxs('div', { className: 'hk-stack', children: [
      jsx(Label, { children: 'Which Hermes version are you on' }),
      jsx('p', { children: 'Field Academy could not read the version from Hermes. Type it the way Hermes shows it, so the Field Record can show it.' }),
      jsxs('div', { className: 'hk-actions', children: [
        jsx('div', { style: { minWidth: '12rem' }, children: jsx(Input, { value: text, onChange: e => setText(e.target.value), placeholder: '0.21.3', 'aria-label': 'Hermes version' }) }),
        jsx(Button, { loading: action.busy === 'v', onClick: () => action.run('v', () => ctxRest('/deployer/version', { method: 'POST', body: { value: text, source: 'typed by you' } })), children: 'Save the version' }),
      ] }),
      jsx(Result, { result: action.result }),
    ] }) })
  }

  function EvidencePanel({ data }) {
    return jsx(Section, { title: 'What Field Academy can and cannot read', children: jsxs('div', { className: 'fa-dp-two', children: [
      jsx(Card, { children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx(Label, { children: 'It reads, without changing anything' }),
        jsx(Bullets, { items: data.deploy.reads }),
      ] }) }),
      jsx(Card, { children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx(Label, { children: 'It cannot read' }),
        jsx(Bullets, { items: data.deploy.cannot_read }),
        jsx('p', { className: 'hk-small', children: 'Where Hermes cannot be read, the screen says so and the part falls back to a packet your reviewer checks. Your word alone never passes.' }),
      ] }) }),
    ] }) })
  }

  function DeployerPath({ data, go }) {
    const track = data.track
    const model = trailModel(track)
    const itemById = Object.fromEntries(data.items.map(item => [item.id, item]))
    const rows = track.levels.flatMap(level => level.missions)
    const list = useListKeys({ count: rows.length, onOpen: i => rows[i] && go(partFor(rows[i])) })
    return jsx(Frame, { width: 'narrow', up: () => go({ name: 'map' }), onKey: list.keyProps.onKeyDown, children: [
      jsx(PageHeader, {
        back: jsx(Back, { label: 'Trail map', onClick: () => go({ name: 'map' }) }),
        eyebrow: jsx(Label, { children: track.eyebrow }), title: `${track.name} path`, lead: track.promise,
      }, 'head'),
      track.lore ? jsx('p', { className: 'fa-lore', children: track.lore }, 'lore') : null,
      jsx(AboutPanel, { about: data.about }, 'about'),
      jsx(ElevationProfile, {
        model,
        onOpenMission: id => go(partFor(id)),
        onOpenSummit: () => scrollToId('fa-dp-route'),
        children: [
          jsx('p', { children: `${track.verified_missions} of ${track.missions.length} parts passed. ${data.certificate.label}.` }, 'where'),
          jsx(Legend, {}, 'legend'),
        ],
      }, 'profile'),
      jsx(Section, { title: 'Camps on this trail', children: jsxs('div', { className: 'fa-camps', children: track.levels.map(level => {
        const missions = level.missions.map(id => itemById[id]).filter(Boolean)
        return jsxs('div', { className: 'fa-camp', 'data-status': level.status, 'data-current': level.current ? '' : undefined, children: [
          jsx('div', { className: 'fa-camp-rail', children: jsx('span', { className: 'fa-num fa-num-l', 'aria-hidden': 'true', children: level.number }) }),
          jsxs('div', { className: 'fa-camp-body', children: [
            jsxs('div', { className: 'fa-camp-head', children: [
              jsxs('div', { className: 'hk-grow', style: { display: 'grid', gap: 2 }, children: [
                jsx(Label, { children: `Camp ${level.number}` }),
                jsx('h3', { className: 'hk-h2', children: level.name }),
              ] }),
              level.status === 'passed' ? jsx(Pill, { tone: 'good', icon: 'check', children: 'Passed' }) : jsx('span', { className: 'hk-small', children: `${level.passed} of ${level.total} passed` }),
            ] }),
            jsx('p', { children: level.meaning }),
            jsx('div', { className: 'fa-camp-rows', children: missions.map(item => {
              const i = rows.indexOf(item.id)
              return jsxs('button', {
                type: 'button', className: 'hk-rowbtn', onClick: () => go(partFor(item.id)), ...list.itemProps(i),
                children: [
                  jsx(TrailMark, { status: item.state === 'verified' ? 'passed' : item.state === 'not_started' ? 'waiting' : 'started', here: item.id === track.here }),
                  jsxs('span', { className: 'hk-grow', children: [
                    jsx('span', { style: { display: 'block', fontWeight: 600 }, children: item.title }),
                    jsx('span', { className: 'fa-row-meta', children: `About ${item.minutes} minutes · ${stateWords(item.state)}${item.detail ? ` · ${item.detail}` : ''}` }),
                  ] }),
                  item.id === track.here ? jsx('span', { className: 'fa-here-tag', children: 'Next' }) : null,
                  jsx(Codicon, { name: 'chevron-right', size: 13 }),
                ],
              }, item.id)
            }) }),
          ] }),
        ] }, level.id)
      }) }) }, 'camps'),
      jsx(CertificatePanel, { data, go }, 'cert'),
      jsx(VersionPanel, { data }, 'version'),
      jsx(EvidencePanel, { data }, 'evidence'),
      jsx(Card, { children: jsx('p', { className: 'hk-small', children: data.about.lifecycle_credit }) }, 'credit'),
    ] })
  }

  /* -------------------------------------------------------------------- lab -- */

  function LabView({ lab, go }) {
    const [diagnosis, setDiagnosis] = useState(lab.diagnosis || '')
    const [confirm, setConfirm] = useState(false)
    const action = useAction()
    const passed = lab.status === 'verified'
    const open = () => action.run('open', () => ctxRest(`/deployer/lab/${lab.lab_id}/open`, { method: 'POST', body: {} }))
    const check = () => action.run('check', async () => {
      const payload = await ctxRest(`/deployer/lab/${lab.lab_id}/check`, { method: 'POST', body: { diagnosis } })
      action.setResult(payload.outcome)
      return payload
    })
    const fresh = () => action.run('new', async () => {
      setConfirm(false)
      setDiagnosis('')
      return ctxRest(`/deployer/lab/${lab.lab_id}/new`, { method: 'POST', body: {} })
    })
    const result = action.result || lab.result
    const feedback = result && !result.passed ? (result.feedback || lab.feedback) : null

    if (!lab.opened) {
      return jsx(PartFrame, { part: 'lab', title: lab.title, lead: `About ${lab.minutes} minutes. A client's machine, built as a folder of files, with one problem hidden in it.`, go, children: [
        jsx(Card, { key: 'how', children: jsxs('div', { className: 'hk-stack', children: [
          jsx(Label, { children: 'How a lab works' }),
          jsx(Steps, { items: [
            'Field Academy builds a folder of plain files that imitates a small client\'s Hermes setup: settings, a keys file, scheduled jobs, logs, a service file and a backup script.',
            'One problem is hidden in it. The client\'s note tells you the symptoms, and the logs hold the evidence.',
            'You open the folder, find the problem, and repair the files. Then you write down what happened in your own words.',
            'A script checks your files and your write-up against criteria you cannot see yet. A miss tells you what was missing and gives one hint.',
            'The case is built from a seed, so yours differs from anyone else\'s. A fix copied from someone else fails on yours.',
          ] }),
          jsx('p', { className: 'hk-small', children: 'Every key in a lab is made up and says so. The folder is only files. Nothing in it runs, Hermes never reads it, and nothing outside Field Academy\'s own data folder is touched.' }),
          jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: action.busy === 'open', onClick: open, children: 'Open the client\'s machine' }) }),
          jsx(Result, { result: action.result }),
        ] }) }),
      ] })
    }

    return jsx(PartFrame, { part: 'lab', title: lab.title, lead: `${lab.client}. About ${lab.minutes} minutes. ${passed ? 'Passed.' : `${plural(lab.attempts, 'check', 'checks')} so far.`}`, go, children: [
      passed
        ? jsx(Card, { key: 'passed', tone: 'good', tint: true, children: jsxs('div', { className: 'hk-stack', style: { gap: 3 }, children: [
            jsx('strong', { children: 'Passed' }),
            jsx('p', { children: `Passed ${shortDate(lab.passed_at)} after ${plural(lab.attempts, 'check', 'checks')}. The repaired folder stays where it is: it goes into your review packet.` }),
          ] }) })
        : null,
      jsx(Section, { key: 'note', title: 'The client\'s note', children: jsx('pre', { className: 'fa-dp-note', children: lab.note }) }),
      jsx(Section, { key: 'folder', title: 'The folder', children: jsx(Card, { children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { className: 'fa-dp-path', children: lab.path }),
        jsxs('div', { className: 'hk-actions', children: [
          jsx(Button, { onClick: () => openFolder(lab.path), children: 'Open the folder' }),
          jsx(Button, { variant: 'secondary', onClick: () => copyText(lab.path, 'Folder path copied.'), children: 'Copy the path' }),
        ] }),
        jsx('p', { className: 'hk-small', children: `It stands in for ${lab.fake_root} on the client's computer, so paths inside the files start there. Open it in your own editor and terminal.` }),
        jsx(Details, { label: `${lab.files.length} files in the folder`, children: jsx('ul', { className: 'fa-dp-files', children: lab.files.map(file => jsx('li', { children: file }, file)) }) }),
        lab.folder_missing ? jsx(Result, { result: { passed: false, title: 'The folder is gone', detail: 'It was moved or deleted. Press New case to build another.' } }) : null,
      ] }) }) }),
      jsx(Section, { key: 'symptoms', title: 'What the client sees', children: jsx(Bullets, { items: lab.symptoms }) }),
      passed ? null : jsx(Section, { key: 'work', title: 'Your repair and your write-up', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { children: 'Hand in:' }),
        jsx(Bullets, { items: lab.hand_in }),
        jsx(Textarea, { style: { minHeight: '8rem', width: '100%' }, value: diagnosis, onChange: e => setDiagnosis(e.target.value), 'aria-label': 'Your diagnosis',
          placeholder: 'What happened, how you found it, and what you changed. Name the file, the evidence in the logs and the fix.' }),
        jsxs('div', { className: 'hk-actions', children: [
          jsx(Button, { loading: action.busy === 'check', onClick: check, children: 'Check my repair' }),
          confirm
            ? jsxs('span', { className: 'hk-row', style: { gap: 8 }, children: [
                jsx('span', { className: 'hk-small', children: 'This deletes the folder and your edits.' }),
                jsx(Button, { variant: 'secondary', loading: action.busy === 'new', onClick: fresh, children: 'Yes, build a new case' }),
                jsx(Button, { variant: 'secondary', onClick: () => setConfirm(false), children: 'Keep this one' }),
              ] })
            : jsx(Button, { variant: 'secondary', onClick: () => setConfirm(true), children: 'New case' }),
        ] }),
        jsx(Result, { result: result ? { ...result, facts: [] } : null }),
        feedback ? jsx(Feedback, { feedback }) : null,
        lab.worked
          ? jsx(Card, { tone: 'info', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
              jsx(Label, { children: lab.worked.title }),
              jsx(Prose, { text: lab.worked.body }),
              jsx('p', { className: 'hk-small', children: 'It is a different business and a different fault. Use it as a model for the order of the steps, not for the answer.' }),
            ] }) })
          : null,
      ] }) }),
      lab.changed && lab.changed.length
        ? jsx(Section, { key: 'changed', title: 'Files you changed', children: jsx('ul', { className: 'fa-dp-files', children: lab.changed.map(c => jsx('li', { children: `${c.path} (${c.change})` }, c.path)) }) })
        : null,
    ] })
  }

  /* ------------------------------------------------------------------ brief -- */

  function ScoreCard({ score, threshold = 70, feedback }) {
    const passed = typeof score === 'number' && score >= threshold
    return jsx('div', { className: 'hk-row', style: { flexWrap: 'nowrap', gap: 12 }, children: [
      jsx(Ring, { key: 'r', value: (score || 0) / 100, size: 40, stroke: 4, tone: passed ? 'good' : 'warn', label: String(score), title: `${score} out of 100` }),
      jsx('div', { key: 'f', className: 'hk-grow', children: jsx(Result, { result: { passed, title: passed ? `Passed with ${score} out of 100` : `${score} out of 100. You need ${threshold} to pass`, detail: feedback || '' } }) }),
    ] })
  }

  function BriefView({ brief, go }) {
    const [path, setPath] = useState('')
    const action = useAction()
    const answer = brief.answer
    const waiting = brief.stage === 'scoring' && answer && typeof answer.score !== 'number'
    const check = () => action.run('check', async () => {
      const payload = await ctxRest('/deployer/brief/check', { method: 'POST', body: { path: path.trim() } })
      action.setResult(payload)
      if (payload.awaiting_score) await sendToHermes(payload.prompt)
      return payload
    })
    const fresh = () => action.run('new', () => ctxRest('/deployer/brief/new', { method: 'POST', body: {} }))
    const result = action.result
    const feedback = result && !result.passed ? result.feedback : (!waiting && brief.status !== 'verified' ? brief.feedback : null)
    return jsx(PartFrame, { part: 'brief', title: brief.title, lead: `About ${brief.minutes} minutes. Write the proposal you would send to ${brief.firm}.`, go, children: [
      brief.status === 'verified'
        ? jsx(Card, { key: 'ok', tone: 'good', tint: true, children: jsx('p', { children: `Passed. The checks on the document were met and your own Hermes scored the prose ${brief.score} out of 100. Document fingerprint ${String(brief.sha256).slice(0, 16)}.` }) })
        : null,
      jsx(Section, { key: 'brief', title: 'The brief', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('pre', { className: 'fa-dp-note', children: brief.brief }),
        jsx(Label, { plain: true, children: 'Constraints' }),
        jsx(Bullets, { items: brief.constraints }),
      ] }) }),
      jsx(Section, { key: 'task', title: 'What to write', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { children: 'One text or Markdown file with these sections, in this order. It follows a deployment: audit what is there, design the boundaries, build and connect, then test away from the client\'s real work before go-live.' }),
        jsx('ol', { className: 'fa-dp-sections', children: brief.sections.map(s => jsx('li', { children: s }, s)) }),
        jsx(Label, { plain: true, children: 'How it is checked' }),
        jsx('ol', { className: 'fa-bullets', children: [
          jsx('li', { children: 'A script checks the numbers, the names, the access list, and whether you refused the request you should refuse.' }, 'script'),
          jsx('li', { children: 'Your own Hermes scores the parts a script cannot judge, against a rubric you see afterwards.' }, 'hermes'),
        ] }),
      ] }) }),
      brief.status === 'verified' ? null : jsx(Section, { key: 'check', title: 'Check your proposal', children: jsxs('div', { className: 'hk-stack', children: [
        jsx(Input, { value: path, onChange: e => setPath(e.target.value), placeholder: '~/Documents/proposal.md', 'aria-label': 'Where you saved the proposal', onKeyDown: e => { if (e.key === 'Enter' && !e.nativeEvent?.isComposing) check() } }),
        jsxs('div', { className: 'hk-actions', children: [
          jsx(Button, { loading: action.busy === 'check', onClick: check, children: 'Check my proposal' }),
          jsx(Button, { variant: 'secondary', loading: action.busy === 'new', onClick: fresh, children: 'A different firm' }),
        ] }),
        jsx(Result, { result: result && result.awaiting_score ? { ...result, passed: true } : result }),
        feedback ? jsx(Feedback, { feedback }) : null,
        waiting ? jsx(Card, { tone: 'info', children: jsx('p', { children: 'Waiting for your Hermes to score the prose. Look at your chat: your Hermes was sent the document and the rubric. If nothing happened, copy the prompt from the notice and paste it into a chat.' }) }) : null,
        answer && typeof answer.score === 'number' && brief.status !== 'verified' ? jsx(ScoreCard, { score: answer.score, feedback: answer.feedback }) : null,
        answer && answer.ladder ? jsx(Feedback, { feedback: answer.ladder }) : null,
      ] }) }),
      brief.rubric
        ? jsx(Section, { key: 'rubric', title: 'What the prose was scored on', children: jsx(Details, { label: 'The six points', children: jsx('ol', { className: 'fa-numbered', children: brief.rubric.map(point => jsx('li', { children: jsx('span', { children: point }) }, point)) }) }) })
        : null,
    ] })
  }

  /* -------------------------------------------------------------- scenarios -- */

  function ScenarioList({ scenarios, go }) {
    const passed = scenarios.filter(s => s.status === 'verified').length
    return jsx(PartFrame, { part: 'scenarios', title: 'Nine cases with no clean answer', lead: `${passed} of ${scenarios.length} passed. About 8 minutes each.`, go, children: [
      jsx(Card, { key: 'how', children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
        jsx('p', { children: 'Each case sets two reasonable duties against each other. You write what you would do and why. Your own Hermes scores your reasoning against a rubric you see afterwards.' }),
        jsx(Prose, { text: 'Two people can decide differently and both score well. A strong answer:\n- Names the competing duties\n- Weighs them\n- Chooses one\n- Says who decides\n- Says what would change your mind' }),
      ] }) }),
      jsx(Section, { key: 'list', title: 'The cases', children: jsx('div', { className: 'fa-camp-rows', children: scenarios.map(item => jsxs('button', {
        type: 'button', className: 'hk-rowbtn', onClick: () => go({ name: 'deployer', part: 'scenario', id: item.id }),
        children: [
          jsx(TrailMark, { status: item.status === 'verified' ? 'passed' : item.status === 'not_started' ? 'waiting' : 'started' }),
          jsxs('span', { className: 'hk-grow', children: [
            jsx('span', { style: { display: 'block', fontWeight: 600 }, children: item.title }),
            jsx('span', { className: 'fa-row-meta', children: `${stateWords(item.status)}${typeof item.score === 'number' ? ` · ${item.score} out of 100` : ''}` }),
          ] }),
          jsx(Codicon, { name: 'chevron-right', size: 13 }),
        ],
      }, item.id)) }) }),
    ] })
  }

  function ScenarioView({ item, go }) {
    const [answer, setAnswer] = useState('')
    const action = useAction()
    const graded = typeof item.score === 'number'
    const passed = item.status === 'verified'
    const send = () => action.run('send', async () => {
      if (answer.trim().length < 240) throw new Error('Write at least a few sentences, 240 characters or more, that weigh the choice.')
      const payload = await ctxRest(`/deployer/scenario/${item.id}`, { method: 'POST', body: { answer } })
      await sendToHermes(payload.prompt)
      setAnswer('')
      return payload
    })
    const up = () => go({ name: 'deployer', part: 'scenarios', id: '' })
    return jsx(Frame, { width: 'narrow', up, children: [
      jsx(PageHeader, { back: jsx(Back, { label: 'All nine cases', onClick: up }), eyebrow: jsx(Label, { children: 'Judgment scenario' }), title: item.title, lead: item.situation }, 'head'),
      graded ? jsx(ScoreCard, { key: 'score', score: item.score, feedback: item.feedback }) : null,
      !passed && item.ladder ? jsx(Feedback, { key: 'ladder', feedback: item.ladder }) : null,
      passed ? null : jsx(Section, { key: 'write', title: item.question, children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { className: 'hk-small', children: 'Hermes scores your answer out of 100. 70 or more passes, and you can answer again as often as you like.' }),
        jsx(Textarea, { style: { minHeight: '10rem', width: '100%' }, value: answer, onChange: e => setAnswer(e.target.value), 'aria-label': 'Your answer', placeholder: graded ? 'Write a new answer. Start from the first thing that was missing.' : 'What would you do, and why? Name who decides and what would change your mind.' }),
        jsx(Result, { result: action.result }),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: action.busy === 'send', onClick: send, children: graded ? 'Send for a new score' : 'Send for scoring' }) }),
      ] }) }),
      item.covers
        ? jsx(Section, { key: 'covers', title: 'What a strong answer does', children: jsx('ol', { className: 'fa-numbered', children: item.covers.map(text => jsx('li', { children: jsx('span', { children: text }) }, text)) }) })
        : jsx('p', { key: 'hidden', className: 'hk-small', children: 'The rubric stays hidden until your first answer is scored.' }),
    ] })
  }

  /* ------------------------------------------------------------- deployment -- */

  function ClockForm({ deploy }) {
    const [service, setService] = useState('')
    const [job, setJob] = useState('deployer-')
    const action = useAction()
    return jsx(Card, { children: jsxs('div', { className: 'hk-stack', children: [
      jsx(Label, { children: 'Start the clock' }),
      jsx('p', { children: 'Press this when you connect the service and make the job. The start time is part of the evidence, so it cannot be restarted.' }),
      jsxs('div', { className: 'fa-inputs', children: [
        jsxs('div', { className: 'fa-field', children: [jsx('label', { htmlFor: 'fa-dp-service', children: 'The service you connected' }), jsx(Input, { id: 'fa-dp-service', value: service, onChange: e => setService(e.target.value), placeholder: 'Google Calendar, read only' })] }),
        jsxs('div', { className: 'fa-field', children: [jsx('label', { htmlFor: 'fa-dp-job', children: 'The scheduled job, starting with deployer-' }), jsx(Input, { id: 'fa-dp-job', value: job, onChange: e => setJob(e.target.value), placeholder: 'deployer-calendar-brief' })] }),
      ] }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: action.busy === 'start', onClick: () => action.run('start', () => ctxRest('/deployer/deploy/start', { method: 'POST', body: { service, job } })), children: 'Start the clock' }) }),
      jsx(Result, { result: action.result }),
    ] }) })
  }

  function DeployView({ deploy, go }) {
    const [path, setPath] = useState('')
    const [read, setRead] = useState(null)
    const record = useAction()
    const check = useAction()
    const started = Boolean(deploy.started_at)
    const days = started ? Math.max(0, Math.floor((Date.now() - new Date(deploy.started_at).getTime()) / 86400000)) : 0
    const doRecord = () => record.run('record', async () => {
      const payload = await ctxRest('/deployer/deploy/record', { method: 'POST', body: { path: path.trim() } })
      record.setResult(payload)
      return payload
    })
    const doCheck = () => check.run('check', async () => {
      const found = await readHermes(deploy.job)
      setRead(found)
      const payload = await ctxRest('/deployer/deploy/check', { method: 'POST', body: { sample: found.sample } })
      check.setResult(payload.outcome)
      return payload
    })
    const outcome = check.result || deploy.result
    const unreadable = Boolean(check.result && check.result.fallback)
    const feedback = check.result && !check.result.passed ? check.result.feedback : (deploy.status !== 'verified' ? deploy.feedback : null)
    return jsx(PartFrame, { part: 'deploy', title: deploy.title, lead: `About ${deploy.minutes} minutes of your time, spread over at least three days, plus the days it runs.`, go, children: [
      deploy.status === 'verified'
        ? jsx(Card, { key: 'ok', tone: 'good', tint: true, children: jsx('p', { children: 'Passed. Hermes\'s own records show the job ran on its schedule across several days.' }) })
        : deploy.status === 'awaiting_review'
          ? jsx(Card, { key: 'wait', tone: 'warn', tint: true, children: jsx('p', { children: deploy.accepted ? 'Accepted by the reviewer.' : 'Waiting for the reviewer. Hermes could not be read, so your excerpt in the packet is the only evidence.' }) })
          : null,
      jsx(Card, { key: 'intro', children: jsxs('div', { className: 'hk-stack', children: [jsx(Prose, { text: deploy.intro }), jsx(Steps, { items: deploy.steps })] }) }),
      jsx(Section, { key: 'reads', title: 'What the check looks at', children: jsxs('div', { className: 'fa-dp-two', children: [
        jsx(Card, { children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [jsx(Label, { children: 'It reads' }), jsx(Bullets, { items: deploy.reads })] }) }),
        jsx(Card, { children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [jsx(Label, { children: 'It cannot read' }), jsx(Bullets, { items: deploy.cannot_read })] }) }),
      ] }) }),
      started
        ? jsx(Card, { key: 'running', tone: 'info', children: jsxs('div', { className: 'hk-row', style: { flexWrap: 'wrap', gap: 14 }, children: [
            jsxs('div', { className: 'hk-grow hk-stack', style: { gap: 2 }, children: [
              jsx(Label, { plain: true, children: 'Running' }),
              jsx('strong', { children: `${deploy.service}, job ${deploy.job}` }),
              jsx('span', { className: 'hk-small', children: `Started ${longDate(deploy.started_at)}. Day ${days + 1}. ${plural(deploy.checks, 'check', 'checks')} so far.` }),
            ] }),
          ] }) })
        : jsx(ClockForm, { key: 'clock', deploy }),
      started && deploy.status !== 'verified'
        ? jsx(Section, { key: 'record', title: 'Your access record', children: jsxs('div', { className: 'hk-stack', children: [
            jsx('p', { children: 'A text or Markdown file with these sections:' }),
            jsx('div', { className: 'hk-row', style: { gap: 4 }, children: deploy.record_sections.map(s => jsx(Pill, { tone: 'idle', children: s }, s)) }),
            deploy.record ? jsx('p', { className: 'hk-small', children: `Checked: ${deploy.record.name}, fingerprint ${String(deploy.record.sha256).slice(0, 16)}.` }) : null,
            jsx(Input, { value: path, onChange: e => setPath(e.target.value), placeholder: '~/Documents/access-record.md', 'aria-label': 'Where you saved the access record' }),
            jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: record.busy === 'record', onClick: doRecord, children: deploy.record ? 'Check it again' : 'Check my access record' }) }),
            jsx(Result, { result: record.result }),
            record.result && !record.result.passed && record.result.feedback ? jsx(Feedback, { feedback: record.result.feedback }) : null,
          ] }) })
        : null,
      started && deploy.status !== 'verified'
        ? jsx(Section, { key: 'history', title: 'Check the run history', children: jsxs('div', { className: 'hk-stack', children: [
            jsx('p', { children: 'Check now and then, each day or two. Each check adds what Hermes shows to your record, so even if Hermes only shows the last run, the history builds up. The check needs at least five runs on three different days, at least 48 hours apart.' }),
            jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: check.busy === 'check', onClick: doCheck, children: 'Check what Hermes recorded' }) }),
            read && !unreadable ? jsx(ReadNote, { note: read.note, unreadable: false }) : null,
            unreadable ? null : jsx(Result, { result: outcome }),
            feedback ? jsx(Feedback, { feedback }) : null,
            unreadable ? jsx(ReadNote, { note: read && read.note, unreadable: true }) : null,
          ] }) })
        : null,
      started && deploy.status !== 'verified' && (unreadable || deploy.fallback)
        ? jsx(FallbackBox, { key: 'fallback', label: 'Hermes did not show enough run history.', existing: deploy.fallback, post: (excerpt, notes) => ctxRest('/deployer/deploy/fallback', { method: 'POST', body: { excerpt, notes } }) })
        : null,
    ] })
  }

  /* ----------------------------------------------------------------- drills -- */

  function DrillCard({ drill, deploy, drillNote }) {
    const [path, setPath] = useState('')
    const act = useAction()
    const base = `/deployer/drill/${drill.id}`
    const started = Boolean(drill.started_at)
    const ended = Boolean(drill.ended_at)
    const done = drill.status === 'verified' || drill.status === 'awaiting_review'
    const [read, setRead] = useState(null)
    const doCheck = () => act.run('check', async () => {
      const found = await readHermes(deploy.job)
      setRead(found)
      const payload = await ctxRest(`${base}/check`, { method: 'POST', body: { sample: found.sample } })
      act.setResult(payload.outcome)
      return payload
    })
    const outcome = act.result || drill.result
    const unreadable = Boolean(act.result && act.result.fallback)
    return jsx(Card, { children: jsxs('div', { className: 'hk-stack', children: [
      jsxs('div', { className: 'hk-row', style: { flexWrap: 'wrap', gap: 10 }, children: [
        jsxs('div', { className: 'hk-grow', style: { display: 'grid', gap: 2 }, children: [
          jsx('h3', { className: 'hk-h3', children: drill.title }),
          jsx('span', { className: 'hk-small', children: `About ${drill.minutes} minutes${drill.optional ? ' · optional' : ''}` }),
        ] }),
        jsx(StateTag, { state: drill.status === 'in_progress' || drill.status === 'running' ? 'in_progress' : drill.status }),
      ] }),
      jsx(Prose, { text: drill.intro }),
      jsx(Steps, { items: drill.steps }),
      jsx(Card, { tone: 'warn', children: jsx(Prose, { text: drill.risk }) }),
      !done
        ? jsxs('div', { className: 'hk-stack', children: [
            jsxs('div', { className: 'hk-actions', children: [
              !started ? jsx(Button, { loading: act.busy === 'start', onClick: () => act.run('start', () => ctxRest(`${base}/start`, { method: 'POST', body: {} })), children: 'Start the drill' }) : null,
              started && !ended ? jsx(Button, { loading: act.busy === 'recover', onClick: () => act.run('recover', () => ctxRest(`${base}/recover`, { method: 'POST', body: {} })), children: 'I recovered' }) : null,
            ] }),
            started ? jsx('p', { className: 'hk-small', children: `Started ${longDate(drill.started_at)}${ended ? `. Recovered ${longDate(drill.ended_at)}.` : '.'}` }) : null,
            ended
              ? jsxs('div', { className: 'hk-stack', children: [
                  jsx('p', { children: 'The recovery note: a text or Markdown file with these sections:' }),
                  jsx('div', { className: 'hk-row', style: { gap: 4 }, children: NOTE_SECTIONS.map(s => jsx(Pill, { tone: 'idle', children: s }, s)) }),
                  drill.note ? jsx('p', { className: 'hk-small', children: `Checked: ${drill.note.name}.` }) : null,
                  jsx(Input, { value: path, onChange: e => setPath(e.target.value), placeholder: '~/Documents/recovery-note.md', 'aria-label': 'Where you saved the recovery note' }),
                  jsxs('div', { className: 'hk-actions', children: [
                    jsx(Button, { variant: 'secondary', loading: act.busy === 'note', onClick: () => act.run('note', async () => { const p = await ctxRest(`${base}/note`, { method: 'POST', body: { path: path.trim() } }); act.setResult(p); return p }), children: 'Check my note' }),
                    jsx(Button, { loading: act.busy === 'check', onClick: doCheck, children: 'Check the evidence' }),
                  ] }),
                  read && !unreadable ? jsx(ReadNote, { note: read.note, unreadable: false }) : null,
                  unreadable ? null : jsx(Result, { result: outcome }),
                  (act.result && !act.result.passed && act.result.feedback) ? jsx(Feedback, { feedback: act.result.feedback }) : (drill.feedback ? jsx(Feedback, { feedback: drill.feedback }) : null),
                  unreadable ? jsx(ReadNote, { note: read && read.note, unreadable: true }) : null,
                  unreadable || drill.fallback ? jsx(FallbackBox, { label: 'Hermes did not show enough run history around the drill.', existing: drill.fallback, post: (excerpt, notes) => ctxRest(`${base}/fallback`, { method: 'POST', body: { excerpt, notes } }) }) : null,
                ] })
              : jsx(Result, { result: act.result }),
          ] })
        : jsx('p', { className: 'hk-small', children: drill.status === 'verified' ? 'Passed. The run history shows the gap and the recovery.' : (drill.accepted ? 'Accepted by the reviewer.' : 'Waiting for the reviewer.') }),
    ] }) })
  }

  function DrillsView({ drills, deploy, note, needed, go }) {
    const passed = drills.filter(d => d.status === 'verified').length
    return jsx(PartFrame, { part: 'drills', title: 'Break it on purpose and prove it recovers', lead: `${passed} of ${needed} needed. Pick any ${needed} of the ${drills.length}.`, go, children: [
      jsx(Card, { key: 'own', tone: 'warn', tint: true, children: jsx('p', { children: note }) }),
      !deploy.job
        ? jsx(Card, { key: 'need', tone: 'info', children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
            jsx('strong', { children: 'Start your deployment first' }),
            jsx('p', { children: 'A drill breaks the thing you deployed, and the proof is a gap and a recovered run in its history.' }),
            jsx('div', { className: 'hk-actions', children: jsx(Button, { onClick: () => go({ name: 'deployer', part: 'deploy', id: '' }), children: 'Open the real deployment' }) }),
          ] }) })
        : null,
      ...drills.map(drill => jsx(DrillCard, { drill, deploy }, drill.id)),
    ] })
  }

  /* ------------------------------------------------------------ walkthrough -- */

  /** Who can sign: the published list, and any reviewer the learner added on this computer. */
  function ReviewerList({ reviewers }) {
    const lists = reviewers || { published: [], local: [] }
    const [name, setName] = useState('')
    const [key, setKey] = useState('')
    const add = useAction(out => add.setResult({ passed: true, title: `${out.name} is on your own list`, detail: 'A sign-off signed with that key now counts, and your Field Record says the key came from your list.', facts: [] }))
    return jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
      jsx('strong', { children: 'Who can sign' }),
      jsx('p', { children: lists.published.length
        ? `Reviewers on Field Academy's published list: ${lists.published.join(', ')}.`
        : "You choose your reviewer: someone whose experience with Hermes and with clients you trust. Ask them for their public key and add it below. Field Academy's published reviewer list is empty for now. Your Field Record will say the key came from your own list, so anyone reading it knows to check who holds it." }),
      lists.local.length ? jsx('p', { children: `On your own list: ${lists.local.join(', ')}.` }) : null,
      jsx(Details, { label: 'Add a reviewer to your own list', children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
        jsx(Input, { value: name, onChange: e => setName(e.target.value), placeholder: "The reviewer's name", 'aria-label': "The reviewer's name" }, 'n'),
        jsx(Input, { value: key, onChange: e => setKey(e.target.value), placeholder: 'Their public key, 64 characters', 'aria-label': "The reviewer's public key", style: { fontFamily: 'var(--hk-mono)' } }, 'k'),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: add.busy === 'a', onClick: () => add.run('a', async () => {
          const out = await ctxRest('/deployer/review/trust', { method: 'POST', body: { name, public_key: key } })
          setKey('')
          return out
        }), children: 'Add to my list' }) }, 'a'),
        jsx(Result, { result: add.result }, 'r'),
      ] }) }),
    ] })
  }

  function ReviewPanel({ walk }) {
    const review = walk.review
    const [name, setName] = useState('')
    const [signoff, setSignoff] = useState('')
    const packet = useAction()
    const load = useAction()
    const waiting = review.waiting || []
    const status = review.status
    return jsx('div', { className: 'hk-stack', children: [
      status === 'locked' && waiting.length
        ? jsx(Card, { key: 'locked', tone: 'info', children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
            jsx('strong', { children: 'Not yet' }),
            jsx('p', { children: 'The packet is built when everything else on the path is done. Still to do:' }),
            jsx(Bullets, { items: waiting }),
          ] }) })
        : null,
      status === 'ready' || status === 'stale'
        ? jsx(Card, { key: 'build', children: jsxs('div', { className: 'hk-stack', children: [
            jsx(Label, { children: 'Build the review packet' }),
            jsx('p', { children: status === 'stale' ? 'Your work changed after the packet was built, so the reviewer\'s signature would no longer match it. Build a new one.' : 'The packet gathers all your evidence for the reviewer: your lab folders and diagnoses, the proposal, your nine answers, the run history and any excerpt, the drills, and your walkthrough. It carries a fingerprint, so the reviewer signs exactly this packet.' }),
            jsxs('div', { className: 'hk-actions', children: [
              jsx('div', { style: { minWidth: '14rem' }, children: jsx(Input, { value: name, onChange: e => setName(e.target.value), placeholder: 'Your name', 'aria-label': 'Your name for the packet' }) }),
              jsx(Button, { loading: packet.busy === 'p', onClick: () => packet.run('p', () => ctxRest('/deployer/review/packet', { method: 'POST', body: { name } })), children: 'Build the packet' }),
            ] }),
            jsx(Result, { result: packet.result }),
          ] }) })
        : null,
      review.paths && status !== 'locked' && status !== 'ready'
        ? jsx(Card, { key: 'paths', children: jsxs('div', { className: 'hk-stack', children: [
            jsx(Label, { children: 'The packet for your reviewer' }),
            jsx('p', { className: 'fa-dp-path', children: review.paths.folder }),
            jsx('p', { className: 'hk-small', children: `Fingerprint ${String(review.fingerprint).slice(0, 16)}. It holds packet.json, a readable packet.md, rubric.md, signoff-template.json and a copy of each repaired lab folder.` }),
            jsxs('div', { className: 'hk-actions', children: [
              jsx(Button, { onClick: () => openFolder(review.paths.folder), children: 'Open the packet folder' }),
              jsx(Button, { variant: 'secondary', onClick: () => copyText(review.paths.folder, 'Packet path copied.'), children: 'Copy the path' }),
            ] }),
            review.fallback_items && review.fallback_items.length
              ? jsx('p', { children: `The reviewer will be asked to accept evidence Field Academy could not read from Hermes: ${review.fallback_items.join(', ')}. Anything they do not accept stays unpassed.` })
              : null,
          ] }) })
        : null,
      status === 'awaiting_review' || status === 'rejected'
        ? jsx(Card, { key: 'signoff', children: jsxs('div', { className: 'hk-stack', children: [
            jsx(Label, { children: 'The reviewer\'s sign-off' }),
            jsx(Prose, { text: '1. Send the packet to a reviewer you choose, someone with the experience to judge it.\n2. They read it, score the six lines in rubric.md from 0 to 3, and sign it with their key (scripts/sign_review.py).\n3. They send back a signed JSON file.\n4. Paste its contents here.' }),
            jsx(ReviewerList, { reviewers: review.reviewers }),
            jsx(Textarea, { style: { minHeight: '8rem', width: '100%' }, value: signoff, onChange: e => setSignoff(e.target.value), 'aria-label': 'The signed sign-off', placeholder: '{ "signoff": "Field Academy Deployer review", ... }' }),
            jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: load.busy === 'l', onClick: () => load.run('l', () => ctxRest('/deployer/review/signoff', { method: 'POST', body: { signoff } })), children: 'Check the sign-off' }) }),
            jsx(Result, { result: load.result }),
            review.problems && review.problems.length
              ? jsx(Card, { tone: 'warn', tint: true, children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [jsx('strong', { children: 'What is wrong with it' }), jsx(Bullets, { items: review.problems })] }) })
              : null,
          ] }) })
        : null,
      status === 'signed'
        ? jsx(Card, { key: 'signed', tone: 'good', tint: true, children: jsxs('div', { className: 'hk-stack', style: { gap: 6 }, children: [
            jsx('strong', { children: `Signed by ${review.reviewer && review.reviewer.name}` }),
            jsx('p', { children: `${review.list === 'published' ? 'On Field Academy\'s published reviewer list.' : 'Not on the published reviewer list: your own list. Your Field Record says so.'} Key ${review.key_fingerprint}. Signed ${longDate(review.signed_at)}.` }),
            jsx('ul', { className: 'fa-dp-rubric', children: Object.entries(review.scores || {}).map(([id, score]) => jsxs('li', { children: [jsx('b', { children: score }), jsx('span', { children: (review.rubric.find(r => r.id === id) || {}).title || id })] }, id)) }),
            review.comments ? jsx('p', { className: 'fa-wrap', children: `“${review.comments}”` }) : null,
            review.needs_acceptance && review.needs_acceptance.length
              ? jsx('p', { children: `The reviewer did not accept: ${review.needs_acceptance.join(', ')}. Those parts stay unpassed until you redo them or the reviewer signs a new sign-off.` })
              : null,
          ] }) })
        : null,
      jsx(Details, { key: 'rubric', label: 'What the reviewer scores', children: jsx('div', { className: 'hk-stack', children: review.rubric.map(item => jsxs('div', { className: 'hk-stack', style: { gap: 2 }, children: [
        jsx('strong', { children: item.title }), jsx('p', { className: 'hk-small', children: item.look_for }),
      ] }, item.id)) }) }),
    ] })
  }

  function ClaimPanel({ data, go }) {
    const [name, setName] = useState('')
    const act = useAction(() => go({ name: 'deployer', part: 'certificate', id: '' }))
    const cert = data.certificate
    if (cert.status === 'issued') {
      return jsx(Card, { tone: 'good', tint: true, children: jsxs('div', { className: 'hk-actions', children: [jsx('strong', { children: 'Field Record created' }), jsx(Button, { onClick: () => go({ name: 'deployer', part: 'certificate', id: '' }), children: 'View your Field Record' })] }) })
    }
    if (cert.status === 'awaiting_review') {
      return jsx(Card, { tone: 'warn', tint: true, children: jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
        jsx('strong', { children: 'Guide, awaiting review' }),
        jsx('p', { children: 'You can create your Field Record once your reviewer\'s signed sign-off is loaded and every part of the path stands. You are not missing anything else.' }),
      ] }) })
    }
    if (cert.status !== 'ready') return null
    return jsx(Card, { tone: 'warn', tint: true, children: jsxs('div', { className: 'hk-stack', children: [
      jsx('h3', { className: 'hk-h2', children: 'Create your Field Record' }),
      data.certificate.needs_version ? jsx(VersionPanel, { data }) : null,
      jsx('p', { children: 'Every part passed and your reviewer signed. Type your name the way you want it on your record. Field Academy writes the record on your computer, and it stays yours.' }),
      jsxs('div', { className: 'hk-actions', children: [
        jsx('div', { style: { minWidth: '16rem', flex: 1 }, children: jsx(Input, { value: name, onChange: e => setName(e.target.value), placeholder: 'Your name', 'aria-label': 'Name on the Field Record' }) }),
        jsx(Button, { loading: act.busy === 'c', onClick: () => act.run('c', () => ctxRest('/deployer/certificate', { method: 'POST', body: { name } })), children: 'Create your Field Record' }),
      ] }),
      jsx(Result, { result: act.result }),
    ] }) })
  }

  function WalkthroughView({ walk, data, go }) {
    const [text, setText] = useState(walk.explanation || '')
    const [media, setMedia] = useState('')
    const act = useAction()
    const save = () => act.run('save', async () => {
      const payload = await ctxRest('/deployer/walkthrough', { method: 'POST', body: { text, media_path: media.trim() } })
      act.setResult(payload)
      return payload
    })
    return jsx(PartFrame, { part: 'walkthrough', title: walk.title, lead: 'A person reads your evidence and signs it. Without that signature you hold Guide, awaiting review.', go, children: [
      jsx(Card, { key: 'intro', children: jsx(Prose, { text: walk.intro }) }),
      jsx(Section, { key: 'walk', title: 'Your walkthrough', children: jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { children: walk.prompt }),
        jsx(Textarea, { style: { minHeight: '12rem', width: '100%' }, value: text, onChange: e => setText(e.target.value), 'aria-label': 'Your walkthrough', placeholder: 'The client\'s bill had jumped. I started by reading...' }),
        jsx('p', { className: 'hk-small', children: `${text.trim().length} characters${text.trim().length < walk.min_chars ? `, at least ${walk.min_chars} needed` : `, enough to save`}. Keys are removed before it is kept.` }),
        jsx(Input, { value: media, onChange: e => setMedia(e.target.value), placeholder: 'Optional: the location of a recording, such as ~/Documents/walkthrough.mp4', 'aria-label': 'Where a recording is saved' }),
        jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: act.busy === 'save', onClick: save, children: walk.saved ? 'Save it again' : 'Save my walkthrough' }) }),
        walk.saved ? jsx('p', { className: 'hk-small', children: `Saved ${longDate(walk.saved_at)}${walk.media ? `. Recording ${walk.media.name}, fingerprint ${String(walk.media.sha256).slice(0, 16)}, not copied.` : '.'} Saving it again after the packet is built makes the packet stale.` }) : null,
        jsx(Result, { result: act.result }),
        act.result && !act.result.passed && act.result.feedback ? jsx(Feedback, { feedback: act.result.feedback }) : (walk.feedback && !walk.saved ? jsx(Feedback, { feedback: walk.feedback }) : null),
      ] }) }),
      jsx(Section, { key: 'review', title: 'Your reviewer', children: jsx(ReviewPanel, { walk }) }),
      jsx(ClaimPanel, { key: 'claim', data, go }),
    ] })
  }

  /* ----------------------------------------------------------- field record -- */

  function DeployerCertificate({ data, go }) {
    const issued = data.certificate.issued
    const [saved, setSaved] = useState(null)
    const save = useAction(payload => setSaved(payload))
    const reverify = useAction()
    const up = () => go({ name: 'path', id: 'deployer' })
    if (!issued) {
      return jsx(Frame, { width: 'narrow', up, children: [
        jsx(Back, { label: 'Guide path', onClick: up }, 'back'),
        jsx('div', { className: 'fa-panel', key: 'none', children: jsxs('div', { className: 'hk-stack', style: { gap: 3 }, children: [
          jsx(Label, { children: 'Summit' }),
          jsx('h1', { className: 'hk-h1', children: data.certificate.label }),
          jsx('p', { children: 'There is no Field Record yet. It needs every part of the path and the signed sign-off of a reviewer you choose.' }),
        ] }) }),
      ] })
    }
    const body = issued.body
    const display = issued.display || { issuer: body.issuer, shows: body.shows, does_not_show: body.does_not_show, disclaimer: body.disclaimer || (data.about && data.about.disclaimer) || '' }
    const rv = data.certificate.reverify
    return jsx(Frame, { up, children: [
      jsx(Back, { label: 'Guide path', onClick: up }, 'back'),
      jsx('article', { key: 'cert', className: 'fa-cert hk-enter', 'aria-label': `Guide Field Record for ${body.name}, self-issued with Field Academy`, children: jsxs('div', { className: 'fa-cert-inner', children: [
        jsx(Contours, { width: 900, height: 600, seed: 11 }),
        jsx(CertCorners, {}),
        jsxs('div', { className: 'fa-cert-top', children: [
          jsxs('div', { style: { display: 'grid', gap: 3 }, children: [jsx(Label, { children: 'Field Record' }), jsx('span', { className: 'fa-sc', children: 'Self-issued record of work in labs' })] }),
          jsxs('div', { style: { display: 'grid', gap: 3, justifyItems: 'end', textAlign: 'right' }, children: [jsx(Label, { plain: true, children: 'Record number' }), jsx('span', { className: 'fa-cert-number', children: body.number })] }),
        ] }),
        jsxs('div', { className: 'fa-cert-centre', children: [
          jsx(Label, { plain: true, children: 'Kept by' }),
          jsx('p', { className: 'fa-cert-name', children: body.name }),
          jsx(Label, { plain: true, children: 'who completed every part of the' }),
          jsx('h1', { className: 'fa-cert-path', children: 'Guide path' }),
          jsx('p', { className: 'fa-cert-promise', children: body.path_promise }),
          jsx('p', { children: `Created ${longDate(body.issued_at)}, on the holder's own computer. Recorded on Hermes ${body.hermes_version.value}.` }),
        ] }),
        jsxs('div', { className: 'fa-cert-foot', children: [
          jsxs('div', { style: { display: 'grid', gap: 6 }, children: [
            jsx(Label, { children: 'Self-issued' }),
            jsx('p', { className: 'fa-cert-issuer', children: display.disclaimer }),
            jsx('p', { className: 'hk-small fa-cert-issuer', children: `Signed by ${body.review.reviewer}, a reviewer the holder chose. ${body.review.list === 'published' ? 'On Field Academy\'s published reviewer list.' : 'Not on the published reviewer list.'} Key ${body.review.key_fingerprint}.` }),
          ] }),
          jsx(Seal, { size: 124 }),
        ] }),
      ] }) }),
      jsxs('div', { key: 'actions', className: 'hk-actions', children: [
        jsx(Button, { loading: save.busy === 's', onClick: () => save.run('s', () => ctxRest('/deployer/certificate/save', { method: 'POST', body: {} })), children: 'Save as a file' }),
        jsx(Pill, { tone: issued.valid ? 'good' : 'bad', icon: issued.valid ? 'pass-filled' : 'error', children: issued.valid ? 'The record number matches its contents' : 'The record number does not match its contents' }),
        rv ? jsx(Pill, { tone: rv.status === 'reverify' ? 'warn' : rv.status === 'current' ? 'good' : 'idle', icon: rv.status === 'reverify' ? 'history' : 'check', children: rv.status === 'reverify' ? 'Re-verify needed' : rv.status === 'current' ? 'Current for this Hermes' : 'Version unknown' }) : null,
      ] }),
      rv ? jsx('p', { key: 'rv', children: rv.words }) : null,
      rv && rv.status === 'reverify'
        ? jsx(Card, { key: 'reverify', tone: 'warn', tint: true, children: jsxs('div', { className: 'hk-stack', children: [
            jsx('strong', { children: rv.open ? 'Re-verify is open' : 'Re-verify this Field Record' }),
            jsx('p', { children: 'Re-verify means the four labs again, on new cases, with the Hermes you are on now. The proposal, the nine cases and the review are not repeated, and your Field Record is not rewritten: a renewal is recorded beside it.' }),
            jsx('div', { className: 'hk-actions', children: rv.open
              ? jsx(Button, { loading: reverify.busy === 'f', onClick: () => reverify.run('f', () => ctxRest('/deployer/reverify/finish', { method: 'POST', body: {} })), children: 'Finish the re-verify' })
              : jsx(Button, { loading: reverify.busy === 's', onClick: () => reverify.run('s', () => ctxRest('/deployer/reverify/start', { method: 'POST', body: {} })), children: 'Start the re-verify' }) }),
            jsx(Result, { result: reverify.result }),
          ] }) })
        : null,
      saved ? jsx(Result, { key: 'saved', result: { passed: true, title: 'Saved', detail: 'A readable copy and a data copy are on your computer.', facts: [{ label: 'Readable copy', value: saved.markdown }, { label: 'Data copy', value: saved.json }] } }) : null,
      jsx(Section, { key: 'proof', title: 'The proof behind it', children: jsxs('div', { className: 'hk-stack', children: [
        jsx(Card, { flush: true, children: jsx('div', { style: { overflowX: 'auto', padding: '4px 14px 8px' }, children: jsxs('table', { className: 'fa-table', children: [
          jsx('thead', { children: jsxs('tr', { children: [jsx('th', { children: 'Lab' }), jsx('th', { children: 'Case' }), jsx('th', { children: 'Checks taken' }), jsx('th', { children: 'Passed' }), jsx('th', { children: 'Repaired folder' })] }) }),
          jsx('tbody', { children: body.labs.map(lab => jsxs('tr', { children: [
            jsx('td', { children: jsx('strong', { children: lab.title }) }), jsx('td', { children: `Seed ${lab.seed}` }), jsx('td', { children: lab.attempts }), jsx('td', { children: shortDate(lab.passed_at) }),
            jsx('td', { children: jsx('span', { className: 'hk-mono', children: String(lab.tree_fingerprint).slice(0, 16) }) }),
          ] }, lab.lab_id)) }),
        ] }) }) }),
        jsx(Facts, { rows: [
          { label: 'Proposal', value: `${body.brief.firm}, prose scored ${body.brief.score}` },
          { label: 'Judgment scenarios', value: body.scenarios.map(s => s.score).join(', ') },
          { label: 'Real deployment', value: `${body.deployment.service}, ${body.deployment.status}, ${plural(body.deployment.checks, 'check', 'checks')}` },
          { label: 'Failure drills', value: body.drills.map(d => `${d.id} (${d.status})`).join(', ') || 'none' },
          { label: 'Reviewer scores out of 3', value: Object.entries(body.review.scores).map(([k, v]) => `${k.replace(/_/g, ' ')} ${v}`).join(', ') },
        ] }),
      ] }) }),
      jsx(AboutPanel, { key: 'about', about: { shows: display.shows, does_not: display.does_not_show, issuer: display.issuer, disclaimer: display.disclaimer } }),
      jsx('p', { key: 'credit', className: 'hk-small', children: body.lifecycle_credit }),
    ] })
  }

  /* -------------------------------------------------------------- dispatcher -- */

  function DeployerPart({ view, data, go }) {
    const part = view.part
    if (part === 'lab') {
      const lab = data.labs.find(item => item.lab_id === view.id)
      return lab ? jsx(LabView, { lab, go }) : jsx(DeployerPath, { data, go })
    }
    if (part === 'brief') return jsx(BriefView, { brief: data.brief, go })
    if (part === 'scenarios') return jsx(ScenarioList, { scenarios: data.scenarios, go })
    if (part === 'scenario') {
      const item = data.scenarios.find(s => s.id === view.id)
      return item ? jsx(ScenarioView, { item, go }) : jsx(ScenarioList, { scenarios: data.scenarios, go })
    }
    if (part === 'deploy') return jsx(DeployView, { deploy: data.deploy, go })
    if (part === 'drills') return jsx(DrillsView, { drills: data.drills, deploy: data.deploy, note: data.drill_note, needed: data.drills_needed, go })
    if (part === 'walkthrough') return jsx(WalkthroughView, { walk: data.walkthrough, data, go })
    if (part === 'certificate') return jsx(DeployerCertificate, { data, go })
    return jsx(DeployerPath, { data, go })
  }

  return { DeployerPath, DeployerPart, DeployerCertificate }
}
