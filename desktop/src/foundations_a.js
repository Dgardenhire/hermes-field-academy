// Field Academy Foundations, missions 1, 2, 4, 5 and 6 (0.9 M6, part A): their notes and their page pieces.
//
// Each of these missions declares its own note fields (lab.note_fields_a) and gets its page data from the backend
// (/foundations/a/<attempt>/<what>), read there so the page never learns what was planted. foundations.js hands its
// helpers in through createPartAViews(deps) and asks owns(missionId) before using the memory mission's own forms.

import { useEffect, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'
import { Button, Input, Textarea } from '@hermes/plugin-sdk'
import { Facts, Notice, Section } from 'hermes-ui-kit'
import { PLANTS } from './loop.js'
import { cutWords, fieldProblems } from './loop_a.js'

export const MISSIONS_A = ['f.loop', 'f.cost', 'f.new-chats', 'f.skills', 'f.profiles']

export const PLANTS_A = {
  output_locked: { title: 'The output file was an old, locked copy', what: 'summary.md already existed with last week\'s figures and was locked, so a save failed and "it exists" proved nothing.' },
  input_empty: { title: 'One input sheet was empty', what: 'One of the three sheets was a header row and nothing else. The right output names it instead of filling the gap.' },
  rows_short: { title: 'Fewer jobs than the request said', what: 'The card asked for every one of the jobs it counted, and the sheets held two fewer. The right output says how many there really are.' },
  extra_connector: { title: 'A connector the job never used was on', what: 'The reference filesystem connector was switched on. Its tool descriptions rode along on every trip, and the job never called one.' },
  unused_skills: { title: 'Skills for other work were on', what: 'Twelve skills for a kind of work this profile never does were installed and switched on. Each one\'s name and description rode along on every trip, and the job never opened one.' },
  soul_wrong_profile: { title: 'A second practice profile sat beside the first', what: 'academy-practice-b sat next to academy-practice in the profile row. Editing its SOUL.md changes nothing in academy-practice\'s chats.' },
  steps_in_memory: { title: 'A job\'s steps were saved in memory', what: 'A three-step procedure sat in MEMORY.md as one line. Steps belong in a skill; two copies drift apart.' },
  greedy_neighbor: { title: 'A catch-all skill matched almost anything', what: 'academy-report-helper said "Use when asked for any report, summary or list," so it could win over a skill with a weaker line.' },
  cloned_memory: { title: 'B was cloned from A', what: 'academy-practice-b was made with Clone from academy-practice, and A\'s client line came with it.' },
  decoy_in_b: { title: 'Another client\'s fact sat in B', what: 'A line about another client was saved in academy-practice-b\'s memory, as if by mistake.' },
}
Object.assign(PLANTS, PLANTS_A)

export function createPartAViews(deps) {
  const { Markdown, PathLine, Toggle, Problem, Problems, MemoryFile, openPracticeChat, post, ctxRest, copyText, useAction, latest } = deps
  const owns = id => MISSIONS_A.includes(id)

  function useData(path, deps2) {
    const [state, setState] = useState({ data: null, error: '' })
    const load = async () => {
      try {
        setState({ data: await ctxRest(path), error: '' })
      } catch (e) {
        setState({ data: null, error: String(e?.message || e) })
      }
    }
    useEffect(() => { load() }, deps2 || [path])
    return { ...state, load }
  }

  function useMissionPublic(id) {
    return useData(`/foundations/mission/${encodeURIComponent(id)}`, [id]).data
  }

  /** A request card with its full path filled in, and Copy. */
  function Card({ card }) {
    return jsxs('div', { className: 'fa-f-predict', children: [
      jsx('strong', { children: card.label }),
      jsx('pre', { className: 'fa-f-excerpt', children: card.text }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: () => copyText(card.text, 'Copied the request.'), children: 'Copy the request' }) }),
    ] })
  }

  function Field({ f, value, set, rules }) {
    const id = `fa-a-${f.id}`
    if (f.kind === 'bool') {
      return jsxs('div', { className: 'fa-f-row', children: [jsx('span', { children: f.label }),
        jsx(Toggle, { label: f.label, value, onChange: set, yes: 'Yes', no: 'No' })] })
    }
    if (f.kind === 'choice') {
      return jsxs('div', { className: 'fa-field', children: [jsx('label', { htmlFor: id, children: f.label }),
        jsx('div', { className: 'hk-stack', style: { gap: 6 }, children: (rules || []).map(r => jsxs('label', { className: 'fa-f-withhold', children: [
          jsx('input', { type: 'radio', name: id, checked: value === r.id, onChange: () => set(r.id) }),
          jsxs('span', { children: [jsx('strong', { children: `${r.label}. ` }), jsx('code', { className: 'fa-f-code', children: r.text })] }),
        ] }, r.id)) })] })
    }
    const big = f.kind === 'textarea' || f.kind === 'lines'
    return jsxs('div', { className: 'fa-field', children: [
      jsx('label', { htmlFor: id, children: f.label }),
      big ? jsx(Textarea, { id, rows: f.kind === 'lines' ? 5 : 3, value: Array.isArray(value) ? value.join('\n') : (value ?? ''), onChange: e => set(e.target.value) })
        : jsx(Input, { id, inputMode: f.kind === 'int' ? 'numeric' : undefined, value: value ?? '', onChange: e => set(f.kind === 'int' ? e.target.value.replace(/[^0-9,]/g, '') : e.target.value) }),
      f.id === 'better' && value ? jsx('span', { className: 'hk-small', children: `${String(value).length} characters. Hermes would show: ${cutWords(value)}` }) : null,
    ] })
  }

  /** The note form a mission declares, for the try, the lab or the transfer. */
  function NoteFieldsA({ view, save, action, transfer = false, which: whichIn, reloadAll }) {
    const mission = useMissionPublic(view.attempt.mission_id)
    const which = whichIn || (transfer ? 'transfer' : 'first')
    const kind = which === 'try' ? 'try_note' : 'lab_note'
    const saved = which === 'try' ? latest(view, 'try_note') : latest(view, 'lab_note', b => (b.for || 'first') === which)
    const [form, setForm] = useState(() => saved || {})
    const [shown, setShown] = useState([])
    const own = useAction(reloadAll)
    const act = action || own
    if (!mission) return null
    const fields = mission.lab?.note_fields_a?.[which] || []
    if (!fields.length) return null
    const send = () => {
      const problems = fieldProblems(fields, form)
      setShown(problems)
      if (problems.length) return
      const body = Object.fromEntries(fields.map(f => [f.id, f.kind === 'int' && form[f.id] !== undefined && form[f.id] !== '' ? Number(String(form[f.id]).replace(/,/g, '')) : form[f.id]]))
      if (which !== 'try') body.for = which
      const name = `a-${which}`
      if (save && which !== 'try') save(name, kind, body)
      else act.run(name, () => post(`/foundations/attempt/${view.attempt.id}/entry`, { kind, body }))
    }
    return jsxs('div', { className: 'hk-stack', children: [
      ...fields.map(f => jsx(Field, { f, value: form[f.id], rules: mission.lab?.rules_a, set: v => setForm(x => ({ ...x, [f.id]: v })) }, f.id)),
      jsx(Problems, { items: shown }),
      jsx(Problem, { text: act.error }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: which === 'try' ? 'secondary' : 'primary', loading: act.busy === `a-${which}`, onClick: send,
        children: saved ? 'Save again' : which === 'try' ? 'Save my numbers' : 'Save what I did' }) }),
    ] })
  }

  function Paths({ paths }) {
    return (paths || []).map(p => jsxs('div', { className: 'hk-stack', style: { gap: 4 }, children: [jsx('strong', { children: p.label }),
      jsx(PathLine, { path: p.path, shown: p.shown, label: p.label, folder: !p.file })] }, p.path))
  }

  function ProfileButtons({ info }) {
    if (!info?.profiles) return null
    return jsx('div', { className: 'hk-stack', children: info.profiles.map(p => jsxs('div', { className: 'fa-f-profile', children: [
      jsxs('div', { className: 'hk-stack', style: { gap: 2 }, children: [jsx('strong', { children: p.name }), jsx('span', { className: 'hk-small', children: p.which === 'a' ? 'Client A' : 'Client B' })] }),
      jsxs('div', { className: 'hk-stack', children: [jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: p.which === 'a' ? 'primary' : 'secondary', onClick: () => openPracticeChat(p.name), children: p.button }) }),
        jsx(MemoryFile, { name: p.name })] }),
    ] }, p.name)) })
  }

  function FirstTrips({ attemptId }) {
    const d = useData(`/foundations/a/${attemptId}/first_trips`, [attemptId])
    const chats = d.data?.chats || []
    return jsx(Section, { title: 'Your one-word chats', children: jsxs('div', { className: 'hk-stack', children: [
      chats.length ? jsx(Facts, { rows: chats.map((c, i) => ({ label: `Hello ${i + 1}${c.title ? `: ${c.title}` : ''}`,
        value: c.tokens != null ? `${c.tokens.toLocaleString()} tokens on its first trip${c.cost != null ? `, about $${Number(c.cost).toFixed(4)}` : ''}` : `Field Academy couldn't read this one: ${c.how}. Read Context Usage for that chat yourself.` })) })
        : jsx('p', { className: 'hk-small', style: { margin: 0 }, children: 'No one-word practice chat yet. Send hello in a new practice chat.' }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: d.load, children: 'Read them again' }) }),
      jsx('span', { className: 'fa-f-tag', children: 'Field Academy read it from the practice profile\'s chat records' }),
    ] }) })
  }

  function SkillsSeen({ attemptId }) {
    const d = useData(`/foundations/a/${attemptId}/skills`, [attemptId])
    const skills = d.data?.skills || []
    return jsx(Section, { title: 'Skills as Hermes sees them', count: skills.length, children: jsxs('div', { className: 'hk-stack', children: [
      ...skills.map(s => jsxs('div', { className: 'fa-f-predict', children: [
        jsx('strong', { children: s.name }),
        jsx('code', { className: 'fa-f-code', children: s.seen }),
        jsx('span', { className: 'hk-small', children: `${s.chars} characters${s.cut ? ', cut short' : ''}. ${s.made_by}.` }),
      ] }, s.name)),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: d.load, children: 'Read them again' }) }),
      jsx('span', { className: 'fa-f-tag', children: 'Field Academy read it' }),
    ] }) })
  }

  function Lists({ lists }) {
    return (lists || []).map(l => jsxs('div', { className: 'fa-f-predict', children: [jsx('strong', { children: l.label }), jsx('pre', { className: 'fa-f-excerpt', children: l.text }),
      jsx('div', { className: 'hk-actions', children: jsx(Button, { variant: 'secondary', onClick: () => copyText(l.text, 'Copied the list.'), children: 'Copy the list' }) })] }, l.label))
  }

  /** Under Try this first: what this mission's try needs, then its own numbers. */
  function TryPanel({ view, reloadAll }) {
    const info = useData(`/foundations/a/${view.attempt.id}/info`, [view.attempt.id, view.attempt.status]).data
    if (!info) return null
    return jsxs('div', { className: 'hk-stack', children: [
      info.warm_prompt ? jsx(Card, { card: { label: 'The warm-up question', text: info.warm_prompt } }) : null,
      info.mission === 'f.loop' ? jsx(Paths, { paths: info.paths }) : null,
      info.mission === 'f.cost' ? jsx(FirstTrips, { attemptId: view.attempt.id }) : null,
      info.mission === 'f.skills' ? jsx(Lists, { lists: info.lists }) : null,
      info.mission === 'f.skills' ? jsx(SkillsSeen, { attemptId: view.attempt.id }) : null,
      info.mission === 'f.profiles' ? jsx(Paths, { paths: info.paths }) : null,
      info.mission === 'f.profiles' ? jsx(ProfileButtons, { info }) : null,
      jsx(NoteFieldsA, { view, which: 'try', reloadAll }),
    ] })
  }

  /** On Your turn: the cards, paths and readings this mission needs. */
  function LabPanel({ view }) {
    const info = useData(`/foundations/a/${view.attempt.id}/info`, [view.attempt.id]).data
    const [snap, setSnap] = useState(null)
    useEffect(() => {
      if (view.attempt.mission_id !== 'f.skills') return
      ctxRest(`/foundations/a/${view.attempt.id}/snapshot`, { method: 'POST', body: {} }).then(setSnap).catch(() => setSnap(null))
    }, [view.attempt.id])
    if (!info) return null
    return jsxs('div', { className: 'hk-stack', children: [
      ...(info.cards || []).filter(c => c.label !== 'Do it again, differently').map(c => jsx(Card, { card: c }, c.label)),
      info.mission === 'f.cost' ? jsx(Paths, { paths: info.paths }) : null,
      info.mission === 'f.cost' ? jsx(FirstTrips, { attemptId: view.attempt.id }) : null,
      info.mission === 'f.profiles' ? jsx(ProfileButtons, { info }) : null,
      info.mission === 'f.skills' ? jsx(SkillsSeen, { attemptId: view.attempt.id }) : null,
      info.mission === 'f.skills' && snap?.skills_before?.length ? jsx(Notice, { tone: 'info', children: `Already here when Your turn opened, so they don't count for the checks: ${snap.skills_before.join(', ')}.` }) : null,
    ] })
  }

  /** Under Do it again: the second card, where the mission has one. */
  function TransferCard({ view }) {
    const info = useData(`/foundations/a/${view.attempt.id}/info`, [view.attempt.id]).data
    const card = (info?.cards || []).find(c => c.label === 'Do it again, differently')
    return card ? jsx(Card, { card }) : null
  }

  function NoteForm(props) {
    return jsxs('div', { className: 'hk-stack', children: [props.transfer ? jsx(TransferCard, { view: props.view }) : null, jsx(NoteFieldsA, props)] })
  }

  return { owns, TryPanel, LabPanel, NoteForm, NoteFieldsA }
}
