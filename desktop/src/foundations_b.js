// Field Academy Foundations, missions 7 to 11: the lab note form built from each mission's note fields, and the
// panels a mission's page shows (lab.panels). Built into desktop/plugin.js with the rest of the page.
//
// Everything aimed at the practice profile goes through Hermes's own gateway with host.requestProfile (on the
// profile's local route, kit.requestPractice): the jobs a
// planted problem needs (cron.manage add, then pause), and the snapshot list for mission 9 (rollback.list). The page
// never writes a Hermes file and never switches the app's profile. What only the live app can confirm is labelled,
// and falls back to telling the learner how to check by hand.

import { useEffect, useRef, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'
import { Button, Input, Textarea, host } from '@hermes/plugin-sdk'
import { Card, Details, Facts, Notice, Section } from 'hermes-ui-kit'
import { exampleBlock, makeJobs, noteBody, noteFieldProblems, panelsFor, phaseFields, rollbackSample, scheduledLine, screenSafe, tryBody, tryFields, watchWords } from './loop_b.js'

export function createFoundationsPanelsB(ui, kit) {
  const { ctxRest, copyText, longDate, plural } = ui
  const { Markdown, PathLine, Problem, Problems, Next, post, support, requestPractice } = kit
  const enc = encodeURIComponent

  function useLoad(path, deps = []) {
    const [data, setData] = useState(null)
    const [error, setError] = useState('')
    const load = async () => {
      if (!path) return
      try { setData(await ctxRest(path)); setError('') } catch (e) { setError(ui.errorText(e)) }
    }
    useEffect(() => { load() }, deps)
    return { data, error, load }
  }

  /* ------------------------------------------------------------- the note -- */

  function Choice({ field, value, onChange }) {
    return jsx('div', { className: 'fa-f-toggle', role: 'group', 'aria-label': field.label, children: (field.choices || []).map(c =>
      jsx('button', { type: 'button', 'aria-pressed': value === c.value, onClick: () => onChange(c.value), children: c.label || c.value }, c.value)) })
  }

  function FieldNoteForm({ mission, view, save, action, transfer = false }) {
    const fields = phaseFields(mission, transfer)
    const saved = (view.entries || []).filter(e => e.kind === 'lab_note' && (transfer ? e.body.for === 'transfer' : e.body.for !== 'transfer')).map(e => e.body).pop()
    const [form, setForm] = useState(() => ({ ...(saved || {}) }))
    const [shown, setShown] = useState([])
    const set = (id, value) => setForm({ ...form, [id]: value })
    const example = transfer ? mission.transfer?.example : null
    return jsxs('div', { className: 'fa-f-form', children: [
      example ? jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [
        jsx('strong', { children: 'The settings block to read' }),
        jsx('pre', { className: 'fa-f-excerpt', children: exampleBlock(example) }),
      ] }) : null,
      ...fields.map(f => {
        const id = `fa-b-${transfer ? 't' : 'f'}-${f.id}`
        const input = f.kind === 'choice' ? jsx(Choice, { field: f, value: form[f.id], onChange: v => set(f.id, v) })
          : f.kind === 'long' ? jsx(Textarea, { id, rows: 3, value: form[f.id] ?? '', onChange: e => set(f.id, e.target.value) })
            : jsx(Input, { id, type: f.kind === 'number' ? 'number' : 'text', value: form[f.id] ?? '', placeholder: f.placeholder || '', onChange: e => set(f.id, e.target.value) })
        return jsxs('div', { className: 'fa-field', children: [
          jsx('label', { htmlFor: f.kind === 'choice' ? undefined : id, children: `${f.label}${f.required ? '' : ' (optional)'}` }), input,
        ] }, f.id)
      }),
      jsx(Problems, { items: shown }),
      jsx(Problem, { text: action.error }),
      jsx(Next, { label: saved ? 'Save again' : 'Save what I did', busy: action.busy === `note-${transfer}`, onClick: () => {
        const problems = noteFieldProblems(fields, form)
        setShown(problems)
        if (!problems.length) save(`note-${transfer}`, 'lab_note', noteBody(fields, form, transfer))
      } }),
    ] })
  }

  /** The try's own note on missions 7 to 10 (0.9 persona test): what this mission's try asks you to count and guess, in its own
   *  fields (lab.try_fields), saved with the attempt and shown in the record entry in the same words. */
  function TryForm({ mission, view, reloadAll }) {
    const fields = tryFields(mission)
    const saved = (view.entries || []).filter(e => e.kind === 'try_note').map(e => e.body).pop()
    const [form, setForm] = useState(() => ({ ...(saved || {}) }))
    const [shown, setShown] = useState([])
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState('')
    if (!fields.length) return null
    const set = (id, value) => setForm({ ...form, [id]: value })
    const send = async () => {
      const problems = noteFieldProblems(fields, form)
      setShown(problems)
      if (problems.length || busy) return
      setBusy(true)
      setError('')
      try {
        await post(`/foundations/attempt/${view.attempt.id}/entry`, { kind: 'try_note', body: tryBody(fields, form) })
        if (reloadAll) await reloadAll()
      } catch (e) {
        setError(ui.errorText(e))
      } finally {
        setBusy(false)
      }
    }
    return jsxs('div', { className: 'fa-f-form', children: [
      jsx('strong', { children: 'Your guesses, and what you saw' }),
      ...fields.map(f => {
        const id = `fa-try-${f.id}`
        const input = f.kind === 'choice' ? jsx(Choice, { field: f, value: form[f.id], onChange: v => set(f.id, v) })
          : f.kind === 'long' ? jsx(Textarea, { id, rows: 3, value: form[f.id] ?? '', onChange: e => set(f.id, e.target.value) })
            : jsx(Input, { id, type: f.kind === 'number' ? 'number' : 'text', value: form[f.id] ?? '', placeholder: f.placeholder || '', onChange: e => set(f.id, e.target.value) })
        return jsxs('div', { className: 'fa-field', children: [
          jsx('label', { htmlFor: f.kind === 'choice' ? undefined : id, children: `${f.label}${f.required ? '' : ' (after you try it)'}` }), input,
        ] }, f.id)
      }),
      jsx(Problems, { items: shown }),
      jsx(Problem, { text: error }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', loading: busy, onClick: send, children: saved ? 'Save again' : 'Save my guesses' }) }),
    ] })
  }

  /* ------------------------------------------------------------- panels -- */

  function FolderPanel({ name }) {
    const { data } = useLoad(`/foundations/practice/${enc(name)}/folder`, [name])
    if (!data?.expected) return null
    return jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [jsx('strong', { children: 'The practice folder' }),
      jsx(PathLine, { path: data.expected, shown: data.expected_shown, label: 'Practice folder full path' })] })
  }

  function ConnectorTextPanel({ name }) {
    const { data, error, load } = useLoad(`/foundations/practice/${enc(name)}/connector-text`, [name])
    return jsx(Section, { title: 'The connector settings text', children: jsxs('div', { className: 'hk-stack', children: [
      jsx('p', { style: { margin: 0 }, children: 'Read fresh from the practice profile: every connector it has, unchanged, with trust and an empty allow list added to files. In Capabilities, Connectors, open files, then Advanced. Click in the settings box, press Ctrl+A (Cmd+A on a Mac), paste, and press Save.' }),
      data?.ok ? jsx('pre', { className: 'fa-f-excerpt', 'aria-label': 'Settings text', children: screenSafe(data.text) }) : null,
      data?.ok && screenSafe(data.text) !== data.text ? jsx('span', { className: 'hk-small', children: 'Passwords and tokens in these settings are hidden on screen. The copy button copies the full text, so the paste still works.' }) : null,
      data && !data.ok ? jsx(Notice, { tone: 'warn', title: 'Field Academy couldn\'t build the full text', children: `${data.why} In the files entry, add "trust": "untrusted" and "tools": { "include": [] }, then Save.` }) : null,
      jsx(Problem, { text: error }),
      jsxs('div', { className: 'hk-actions', children: [
        data?.ok ? jsx(Button, { onClick: () => copyText(data.text, 'Copied the settings text.'), children: 'Copy the settings text' }) : null,
        jsx(Button, { variant: 'secondary', onClick: load, children: 'Refresh' }),
      ] }),
      data?.package ? jsx('span', { className: 'hk-small', children: `Connector version pinned for this mission: ${data.package}.` }) : null,
    ] }) })
  }

  /** Mission 8 and 10: the jobs a planted problem needs, made by Hermes itself through cron.manage. A job meant to
   * start paused must read paused in the job list before anything else is made; if it can't be, it's deleted, or the
   * learner is told to stop it (makeJobs in loop_b.js, audit B1). */
  function JobsPanel({ name }) {
    const { data, load } = useLoad(`/foundations/practice/${enc(name)}/jobs`, [name])
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState('')
    const tried = useRef(false)
    const pending = data ? (data.jobs?.length || 0) + (data.still_on?.length || 0) : 0
    const make = async () => {
      if (!pending || busy) return
      if (!support().requestProfile) {
        setError('This Hermes app can\'t make a job in another profile from a plugin. Update Hermes Desktop, then come back.')
        return
      }
      setBusy(true)
      setError('')
      try {
        const out = await makeJobs(data, {
          call: params => requestPractice(name, 'cron.manage', params),
          report: () => post(`/foundations/practice/${enc(name)}/jobs-made`),
          profile: name, errorText: ui.errorText,
        })
        if (!out.ok) setError(out.message)
      } catch (e) {
        setError(`Hermes didn't make the practice job: ${ui.errorText(e)}`)
      } finally {
        setBusy(false)
        await load()
      }
    }
    useEffect(() => { if (pending && !tried.current) { tried.current = true; make() } }, [pending])
    if (!data) return null
    if (!pending) return data.made?.length ? jsx('span', { className: 'hk-small', children: `Practice ${plural(data.made.length, 'job is', 'jobs are')} set up in ${name}.` }) : null
    return jsxs('div', { className: 'hk-stack', children: [
      jsx(Notice, { tone: 'info', title: 'Setting up the practice job', children: 'Field Academy asks Hermes to make it in the practice profile, the same way Scheduled jobs would.' }),
      jsx(Problem, { text: error }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { loading: busy, onClick: make, children: 'Try again' }) }),
    ] })
  }

  function ScheduledPanel({ name }) {
    const read = () => { try { return host.state?.profile?.get?.() || '' } catch (e) { return '' } }
    const [live, setLive] = useState(read)
    const line = scheduledLine(live, name)
    return jsx(Notice, { tone: { pass: 'good', fail: 'warn', unknown: 'info' }[line.state] || 'info', title: line.title,
      action: jsx(Button, { variant: 'secondary', onClick: () => setLive(read()), children: 'Check again' }), children: line.text })
  }

  function WatchPanel({ attemptId }) {
    const { data, load } = useLoad(attemptId ? `/foundations/attempt/${attemptId}/watch` : '', [attemptId])
    useEffect(() => { const t = setInterval(load, 60000); return () => clearInterval(t) }, [attemptId])
    const words = watchWords(data)
    return jsx(Notice, { tone: words.tone, title: words.title, live: true, children: data?.last ? `${words.text} Last run ${longDate(data.last)}.` : words.text })
  }

  function OpsPanel({ name }) {
    const { data, load } = useLoad(`/foundations/practice/${enc(name)}/ops`, [name])
    if (!data) return null
    const direct = typeof host.runDoctor === 'function' && typeof host.runBackup === 'function'
    const run = async (what) => {
      try {
        await (what === 'doctor' ? host.runDoctor({ profile: name }) : host.runBackup({ profile: name }))
        host.notify({ kind: 'success', message: what === 'doctor' ? 'The doctor is running on the practice profile.' : 'Backup started in the practice profile.' })
        await load()
      } catch (e) { host.notify({ kind: 'error', message: ui.errorText(e) }) }
    }
    return jsx(Section, { title: 'The practice profile\'s tools', children: jsxs('div', { className: 'hk-stack', children: [
      jsx('strong', { children: 'Its logs folder' }),
      jsx(PathLine, { path: data.logs, shown: data.logs_shown, label: 'Practice profile logs folder' }),
      direct ? jsxs('div', { className: 'hk-actions', children: [
        jsx(Button, { onClick: () => run('doctor'), children: 'Run doctor on the practice profile' }),
        jsx(Button, { variant: 'secondary', onClick: () => run('backup'), children: 'Create backup' }),
      ] }) : jsxs('div', { className: 'hk-stack', children: [
        jsx('p', { style: { margin: 0 }, children: 'This Hermes app runs the doctor and backups only on the profile it has selected, so use a terminal for the practice profile. Copy a command, paste it in a terminal, press Enter.' }),
        jsx('strong', { children: 'The doctor, for the practice profile' }),
        jsx(PathLine, { path: data.doctor, label: 'The doctor command for the practice profile', folder: false }),
        jsx('strong', { children: 'A backup of the practice profile' }),
        jsx(PathLine, { path: data.backup, label: 'The backup command for the practice profile', folder: false }),
      ] }),
      data.backups?.length ? jsx(Facts, { rows: data.backups.map(b => ({ label: b.kind, value: `${b.name}, ${longDate(new Date(b.mtime * 1000).toISOString())}` })) }) : null,
    ] }) })
  }

  function BaselinePanel({ name }) {
    const { data } = useLoad(`/foundations/practice/${enc(name)}/baseline`, [name])
    if (!data?.ready) return null
    const list = (title, items) => jsxs('div', { className: 'fa-f-mem', children: [jsx('strong', { children: `${title} (${items.length})` }),
      items.length ? jsx('ol', { children: items.map((t, i) => jsx('li', { children: t }, i)) }) : jsx('span', { className: 'hk-small', children: 'Empty.' })] })
    return jsx(Card, { children: jsxs('div', { className: 'hk-stack', children: [
      jsx('strong', { children: `What Field Academy recorded at Start, ${longDate(data.taken_at)}` }),
      list('MEMORY.md', data.memory), list('USER.md', data.user), list('Skills', data.skills), list('Waiting for approval', data.pending),
    ] }) })
  }

  function CanClaimPanel() {
    const { data } = useLoad('/foundations/record', [])
    const claims = data?.body?.can_claim
    if (!claims) return null
    return jsx(Details, { label: 'What you can now claim, from your record', children: jsxs('div', { className: 'hk-stack', children: [
      jsx('ol', { className: 'fa-f-claims', children: claims.passed.map(c => jsxs('li', { children: [jsx('strong', { children: c.claim }),
        jsx('span', { className: 'fa-f-tag', children: `${c.title}, ${longDate(c.date)}${c.after_fix ? ', after a fix' : ''}. Field Academy read it.` })] }, c.mission)) }),
      claims.not_yet.length ? jsxs('div', { children: [jsx('strong', { children: 'Not yet' }),
        jsx('ul', { className: 'fa-bullets', children: claims.not_yet.map(c => jsx('li', { children: `${c.title}: ${c.why}` }, c.mission)) })] }) : null,
    ] }) })
  }

  /** The panels a mission's lab step shows, in the order the mission lists them. */
  function LabPanels({ mission, view }) {
    const name = view.attempt.profile
    if (!name) return null
    const map = {
      folder: () => jsx(FolderPanel, { name }), connector_text: () => jsx(ConnectorTextPanel, { name }), jobs: () => jsx(JobsPanel, { name }),
      scheduled_page: () => jsx(ScheduledPanel, { name }), watch: () => jsx(WatchPanel, { attemptId: view.attempt.id }), ops: () => jsx(OpsPanel, { name }),
      baseline: () => jsx(BaselinePanel, { name }), can_claim: () => jsx(CanClaimPanel, {}),
    }
    return jsxs('div', { className: 'hk-stack', children: panelsFor(mission).filter(p => map[p]).map(p => jsx('div', { children: map[p]() }, p)) })
  }

  /** Mission 8's notice, shown again where the learner lands when they come back. */
  function CheckNotices({ mission, view }) {
    return panelsFor(mission).includes('watch') ? jsx(WatchPanel, { attemptId: view.attempt.id }) : null
  }

  /** What the page reads from the live app for a check: mission 9's snapshot list. Labelled; never a pass alone. */
  async function sample(mission, profile) {
    if (!panelsFor(mission).includes('rollback_sample') || !support().requestProfile || !profile) return null
    try {
      const listed = await requestPractice(profile, 'session.list', {})
      const raw = listed && typeof listed === 'object' && 'result' in listed ? listed.result : listed
      const sessions = Array.isArray(raw) ? raw : Array.isArray(raw?.sessions) ? raw.sessions : []
      const id = sessions.map(s => s?.id || s?.session_id).find(Boolean)
      if (!id) return null
      return rollbackSample(await requestPractice(profile, 'rollback.list', { session_id: id }))
    } catch (e) {
      return null
    }
  }

  return { FieldNoteForm, TryForm, FolderPanel, LabPanels, CheckNotices, sample }
}
