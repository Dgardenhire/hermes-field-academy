// Loop 2 desk states for the harness (state=d_*). Each starts from a real fixture state (fixtures.json, the real
// backend after the real steps) and swaps in one real-model run of the memory mission with the snag planted:
// desk_real.json holds the backend's own route answers from that run (made by the AI lane's run_real_loop2.py, with
// `claude -p --model sonnet` standing in for Hermes's model). The AI failure states use the committed contract
// fixtures in tests/data/ai_contract/. Nothing here calls a model.
//
// The answers change as the harness clicks: pressing Nudge me makes the next GET /guide carry the nudge, as the real
// backend does after a help entry is written.

const clone = value => JSON.parse(JSON.stringify(value))
const pause = ms => new Promise(resolve => setTimeout(resolve, ms))
const never = () => new Promise(() => {})

async function load(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`harness: ${path} is missing`)
  return r.json()
}

const contract = name => load(`../tests/data/ai_contract/${name}.json`).then(j => j.response)

// state -> what it is built from. base: a fixtures.json state; view: an attempt view; guide: GET /guide answers by step.
const SPECS = {
  d_home: { base: 'f_fresh' },
  d_ff_guess: { base: 'f_fresh', view: 'first_flight_start', guide: { any: 'first_flight_guide_locked' } },
  d_ff_setup: { base: 'f_fresh', view: 'first_flight_start', guessed: true, guide: { any: 'first_flight_guide_locked' }, hangPlant: true },
  d_score: { base: 'f_checked', view: 'attempt_at_check', noRun: true, guide: { any: 'guide_check_ready' } },
  d_check: { base: 'f_checked', view: 'attempt_at_check', guide: { check: 'guide_check_ready' } },
  d_check_fetching: { base: 'f_checked', view: 'attempt_at_check', guide: { check: 'guide_check_fetching' } },
  d_compare: { base: 'f_checked', view: 'attempt_at_compare', guide: { compare: 'guide_compare' }, replay: 'replay' },
  d_fix: { base: 'f_checked', view: 'attempt_at_fix', guide: { fix: 'guide_fix', compare: 'guide_compare' }, replay: 'replay' },
  d_fix_passed: { base: 'f_checked', view: 'attempt_after_fix', guide: { fix: 'guide_fix', compare: 'guide_compare' }, replay: 'replay' },
  d_record: { base: 'f_saved', record: true },
  d_grade: { base: 'f_checked', view: 'attempt_at_check', guide: { check: 'guide_check_ready' }, answer: true },
  d_grade_wait: { base: 'f_checked', view: 'attempt_at_check', guide: { check: 'guide_check_ready' }, hangGrade: true, answer: true },
  d_replay_empty: { base: 'f_checked', view: 'attempt_at_compare', guide: { compare: 'guide_compare' }, replay: 'replay_empty' },
  d_replay_schema: { base: 'f_checked', view: 'attempt_at_compare', guide: { compare: 'guide_compare' }, replay: 'replay_schema_changed' },
  d_ai_no_model: { base: 'f_checked', view: 'attempt_at_check', guide: { check: '@guide-check-no_model' } },
  d_ai_timeout: { base: 'f_checked', view: 'attempt_at_check', guide: { check: '@guide-check-timeout' } },
  d_ai_bad_json: { base: 'f_checked', view: 'attempt_at_check', guide: { check: '@guide-check-bad_json-course-words' } },
  d_ai_provider: { base: 'f_checked', view: 'attempt_at_check', guide: { check: '@guide-check-provider_error' } },
  d_ai_off: { base: 'f_checked', view: 'attempt_at_check', guide: { any: '@guide-off-switch' } },
  d_testout_off: { base: 'f_checked', view: 'attempt_at_check', guide: { any: '@guide-off-test-out' } },
  // Loop 3 (live gate): the run request fails once, as the gateway did on Nov 9, then Retry gets it.
  d_compare_fail: { base: 'f_checked', view: 'attempt_at_compare', guide: { compare: 'guide_compare' }, replay: 'replay', replayFails: 1 },
  // Loop 3: a First Flight under way, checked but not fixed, so the home card offers to resume it.
  d_home_resume: { base: 'f_fresh', resume: 'checked' },
  // Loop 3: a held save as Hermes 0.23 stages it, shown from an older run whose evidence kept the raw summary.
  d_fix_raw: { base: 'f_checked', view: 'attempt_at_fix', guide: { fix: 'guide_fix', compare: 'guide_compare' }, replay: 'replay', rawHeld: true },
}

export async function deskState(name, fixtures) {
  const spec = SPECS[name] || SPECS.d_home
  const real = await load('./desk_real.json')
  const sample = await load('../content/sample_run.json').catch(() => null)
  const data = clone(fixtures.states[spec.base] || fixtures.states.f_fresh)
  const fd = data.foundations
  const pick = key => (key.startsWith('@') ? contract(key.slice(1)) : Promise.resolve(clone(real[key] || real.fixtures?.[key])))
  if (spec.view) {
    const view = await pick(spec.view)
    if (spec.noRun) {
      view.runs = {}
      view.evidence = []
      delete view.compare
    }
    if (spec.answer && view.explain) view.explain.answer = real.grade_ok.answer
    if (spec.guessed) {
      view.entries = [...(view.entries || []), { kind: 'prediction', body: { guess: { answer: 'save', confidence: 'medium' }, checks: {} }, created_at: view.attempt.started_at }]
      if (view.first_flight) view.first_flight.guessed = { answer: 'save', confidence: 'medium' }
    }
    fd.view = view
  }
  if (spec.record) {
    // The same First Flight, finished: after the fix, the transfer and Add to my record (real backend, same run).
    fd.field_record = clone(real.fixtures.field_record)
    fd.snapshot = clone(real.fixtures.foundations)
    fd.view = clone(real.fixtures.attempt_done)
  }
  const guides = {}
  for (const [step, key] of Object.entries(spec.guide || {})) guides[step] = await pick(key)
  // The real run pressed Why did this miss? on Compare before it read the Compare guide; the page opens with the
  // button, so its words show only after the press (the help handler below puts them back).
  if (guides.compare && guides.compare.help) {
    guides.compare.explain = (guides.compare.explain || []).map(i => ({ ...i, sentences: [] }))
    guides.compare.help = { ...guides.compare.help, used: (guides.compare.help.used || []).filter(u => !(u.kind === 'explain' && u.step === 'compare')) }
  }
  const replay = spec.replay ? clone(real[spec.replay]) : clone(real.replay_before_compare || { state: 'not_ready' })
  // No chat means no run to pin: the empty and changed-schema replays carry no notes, as the real backend would.
  if (spec.replay && spec.replay !== 'replay') {
    for (const g of Object.values(guides)) {
      g.pins = []
      g.help = { key: 'own', words: 'No hints used', hunt_helps: 0, all_helps: 0, used: [] }
    }
  }
  const grade = clone(real.grade_ok)
  if (spec.rawHeld) {
    for (const e of replay.events || []) {
      if (e.kind === 'file:pending') e.text = 'apply 1 op(s) to memory: - add: Harbor Bakery uses QuickBooks Online; the other five clients use Xero.'
    }
  }
  if (spec.resume) {
    fd.snapshot = clone(real.fixtures.foundations)
    for (const m of fd.snapshot.missions || []) {
      if (m.id === 'f.memory') m.attempts = [{ ...m.attempts[0], status: 'lab', finished_at: null, stage: spec.resume }]
    }
  }
  let replayFails = spec.replayFails || 0

  // After a help press the real backend writes a help entry; the next GET /guide shows what was used.
  const helped = (step, patch) => {
    const g = guides[step] || guides.any
    if (g) patch(g)
  }

  const settings = { ai_help: true, practice_offer: false }
  async function rest(method, path, body) {
    if (method === 'GET' && path === '/replay/sample') return sample || { state: 'empty', words: '' }
    if (method === 'GET' && path.startsWith('/replay/')) {
      if (replayFails > 0) { replayFails -= 1; await pause(80); throw new Error('Gateway ticket bootstrap failed') }
      return replay
    }
    if (path === '/settings/ai') {
      for (const name of ['ai_help', 'practice_offer']) if (method === 'POST' && typeof body[name] === 'boolean') settings[name] = body[name]
      return { ...settings }
    }
    if (method === 'GET' && path === '/first-flight') return real.first_flight_info
    if (method === 'POST' && path === '/first-flight/start') return fd.view || clone(real.first_flight_start)
    if (method === 'GET' && path.startsWith('/guide/')) {
      const step = new URLSearchParams(path.split('?')[1] || '').get('step') || ''
      const g = guides[step] || guides.any
      if (g) return clone({ ...g, step })
      return { enabled: false, off_reason: 'not_here', off_words: 'The guide opens on the Check step.', step, ladder: {}, explain: [], pins: [], starters: [], help: {} }
    }
    if (method === 'POST' && /^\/guide\/[^/]+\/help$/.test(path)) {
      await pause(120)
      if (body.rung === 1) {
        helped('check', g => { g.ladder.nudge.text = real.help_nudge.shown.text; g.help = real.help_nudge.help })
        return clone(real.help_nudge)
      }
      if (body.rung === 2) {
        helped('check', g => { g.ladder.where.text = real.help_where.shown.text; g.help = real.help_where.help })
        return clone(real.help_where)
      }
      if (body.rung === 3) return { shown: { opens: 'compare' }, help: real.help_where.help }
      if (body.action === 'explain') {
        // Explain my miss is not a hunt hint, so the help summary doesn't move (the real run's summary at this
        // point also counted an earlier nudge, Ask and Show me where).
        helped(body.step === 'compare' ? 'compare' : 'check', g => { g.explain = clone(real.help_explain.shown.explain); g.help.used = [...(g.help.used || []), { kind: 'explain', rung: null, step: body.step || 'check' }] })
        return clone(real.help_explain)
      }
      if (body.action === 'do_it_with_me') return clone(real.help_do_it_with_me)
      return {}
    }
    if (method === 'POST' && /^\/guide\/[^/]+\/ask$/.test(path)) {
      await pause(120)
      if (/slack/i.test(String(body.question || ''))) return clone(real.ask_not_covered)
      return clone(body.step === 'check' ? real.ask_hunt : real.ask_covered)
    }
    if (method === 'POST' && /^\/guide\/[^/]+\/pins$/.test(path)) return clone(real.pins_make)
    if (method === 'POST' && path.startsWith('/ai/grade/')) return spec.hangGrade ? never() : (await pause(150), grade)
    if (method === 'POST' && path === '/foundations/practice/plant' && spec.hangPlant) return never()
    return undefined
  }

  return { data, rest }
}
