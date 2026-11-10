# Field Academy's model calls (for the QA and release lane)

Private. Left out of the public package (`.public-exclude`). Written by the AI lane on Nov 8, 2026 (Loop 2 shapes added
Nov 9), for the catalog
disclosure rewrite (`docs/catalog/field-academy.yaml` says "no network calls" today; that is no longer true once
these calls ship).

## The short version for the disclosure

Field Academy can ask **your own Hermes model** for short coaching and to score your written answers. It uses
Hermes's plugin model access (`ctx.llm`), on two tasks you can see and change in **Settings, Models, Auxiliary**:
**Field Academy guide** and **Field Academy grader**. The call goes to whichever provider you picked for that task
(by default, your main model). Field Academy sends no data anywhere else. Every input passes Field Academy's secret
scrubber first. Before Compare, nothing it sends names the planted problem. A model never sends, approves, deletes or
writes anything in a practice profile, and never decides whether a check passed; the only verdict a model gives is
the level of a written answer. Turn it all off with **AI help** in Field Academy's Settings; every check keeps
working without it. Tokens are counted from Hermes's own usage numbers; Field Academy never estimates dollars itself.

## Each call

| Feature | Task | What goes in | What comes out | Off switch |
|---|---|---|---|---|
| **Score my answer** (built) | `field_academy_grader` (no inheritance: main model, 60 s) | The mission's title and id, its Explain it question, its four levels and pass level, and the learner's answer fenced as untrusted text (`rubric_prompt` without its tool paragraph). Scrubbed. | `{level 1-4, right, missing, add_next, quote}`. Code checks the level, drops the quote unless it is word for word in the answer, and records the level through `grade_rubric` (`hermes_grader`, `via: inline`). | AI help off: the route answers `state: off` and the chat route stays. |
| **Nudge me** (built, backend) | `field_academy_guide` (inherits `approval`) | The learner's practice-chat events before Compare (`recorder.timeline(reveal=False)`: times, roles, tool rows by title and time with no result text, short scrubbed text) and the visible check results. Never the planted problem. | One question about a moment in the chat. Give-away words per snag are filtered; one regenerate, then the course's own text. Fetched first, the moment the guide is read after a missed check. | AI help off; test-out; First Flight before the score is locked. |
| **Explain my miss** (built, backend) | `field_academy_guide` | A failed visible check's label and the facts Field Academy read (a zero-line `USER.md` reading is left out except for the `USER.md` check), plus the places a learner can look, built by code from the run: the memory row in the chat (by its time), `MEMORY.md`, and after Compare the pending folder. | Two plain sentences, each 20 words or fewer; the second names one of the places; never `USER.md` for another check; before Compare no give-away words. One repair, then the course's words. All failed checks are fetched at once, on their own threads, alongside the nudge. The raw evidence always shows beside them. | AI help off; test-out; First Flight before the score is locked. |
| **Replay pins** (built, backend) | `field_academy_guide` | After Compare only: the revealed snag, every check of the first run with its facts (met or NOT met), the learner's guess, the bracket, and the revealed run from `recorder.timeline(reveal=True)`: both lanes, the memory row's own staged line, the frozen `pending/` evidence and the `MEMORY.md` fill. | Up to 3 `{event_id, why}`, one asked for on the bracket's chat row. That note says where to look in Hermes to catch this snag yourself next time, from `_guide_text.CATCH_IT` (fixed per snag), and must not repeat the row or the page's headline, which the call is given. A note on the bracket's files card or on the MEMORY.md meter card is dropped (each card already shows it), and so is a bracket note naming any slash command other than that snag's own (none for a held save: the row already prints `/memory pending`). A pin over 20 words is cut to its first sentence or dropped (never the whole call); pins on unknown events are dropped. One more try when nothing usable came back or the bracket got no pin. Nothing usable twice: `state: "too_long"` (or `"no_pins"`) with plain words, not `bad_json`. | AI help off. |
| **Do it with me** (built, backend) | `field_academy_guide` | Mission 3's planted problem's title, the first check's facts, the two fixed commands. | One line on what each command does (not what went wrong; the page already says that). Fetched when Compare opens (the first `GET /guide` at `step=compare`), so Fix shows it at once. The commands (`/memory pending`, then `/memory approve <id>` for the one save Hermes is holding, its id read by code from the first check's `pending/memory/<id>.json`) are fixed in code and only drafted, never sent. Never `approve all`: that would also apply saves the learner has not read. The page shows the two commands in the Fix step's main column, built from the held file's name, so they are there with AI help off; the guide column shows only the line on why. Offered only when the first run found a held save. | AI help off. |
| **Ask** (built, backend) | `field_academy_guide` | Lesson paragraphs with ids, "as of Hermes" facts, and from Check onward the learner's entries and the run's events (plant-free before Compare; both lanes after). | Sentences with source ids; uncited sentences are dropped. During the hunt (first check ran, Compare not open) the answer passes the nudge's give-away filter: one regenerate with the words banned, then the course's words (`held_back: true`). Every hunt question is a hunt help in the record. | AI help off; closed in First Flight before the score is locked. |

**Replay your run** makes no model call. `recorder.py` reads the practice chat from `state.db` (read-only) and the
FROZEN evidence of the first check run (`f_evidence`, the `memory_line` check's `MEMORY.md` fill), so it shows what the
check read. The snag comes from the tool result's `staged` flag (Hermes `tools/memory_tool.py:99`), never from the
row's title, which says "Saved to memory" either way.

## Route shapes changed or added in Loop 2

All under the plugin prefix; one fixture per state in `tests/data/ai_contract/` (42 files).

- `GET /guide/{attempt_id}?step=&active=`: anything still on its way reads `{"state": "fetching", "started_at": <epoch s>}`
  (the nudge, each Explain item, Do it with me's `why`). New `off_reason` `"first_flight_locked"` with
  `off_words` "Your guide opens after you score yourself, so the score stays yours." (`guide-first-flight-locked.json`).
  `do_it_with_me.why` may be `fetching` with `started_at` (`guide-fix-why-fetching.json`).
- `POST /guide/{attempt_id}/pins` `{make: true}`: adds `trimmed`, `bracket`, `bracket_pinned`, `tries`; new states
  `too_long` and `no_pins` with `message` and `next_step` (`pins-too-long.json`).
- `POST /guide/{attempt_id}/ask`: adds `held_back`, `tries` and `help` (the help summary after the question); a held-back
  answer is one sentence with `source: "course"` and no `source_ids` (`ask-hunt-held-back.json`).
- `GET /replay/{attempt_id}?step=` (new): `{state: "ready"|"empty"|"schema_changed"|"not_ready"|"unreadable", words,
  started_at, ended_at, lanes: [{id, label}], events: [{event_id, lane, at, kind, title, text, staged?, path?, meter?,
  at_source?, read_at?}], bracket: {from, to, words}|null, snag_found_from: "staged_flag", attempt_id, mission_id}`.
  `not_ready` before Compare (no events at all, so neither the files lane nor the staged line can give the snag away);
  Compare is open at `step=compare|fix|record` or once a gap note exists. Fixtures `replay-ready`, `replay-before-compare`,
  `replay-empty`, `replay-schema-changed`.
- `GET /replay/sample` (new): the same payload from `content/sample_run.json`, plus `label` (honest: a test practice
  profile coached by a named model through the guide's own prompts, not a live Hermes recording), `sample: true`,
  `recorded`, `snag`, `checks`, `compare: {said, shows, of}`, `pins` and `nudge` (`replay-sample.json`).
- `POST /first-flight/start` (new): the attempt, the same shape as `POST /foundations/attempt/start` (`attempt_view`),
  which now carries `first_flight: {on, words, skipped, snag, guess: {question, answers: [{id, label}] x4, confidence:
  [{id, label}] x3}, guessed, guide}` (null for any other try). The guess is saved as the existing `prediction` kind with
  body `{guess: {answer, confidence}}` (`first-flight-start.json`).
- `GET /first-flight` (new): the question and answer list before a try exists (`first-flight-info.json`).

## Where it is in the code

- `runtime.py`: the context shared with the page routes, the two task names, the data folder.
- `ai.py`: the one helper every call uses (`call`): scrub, the switch, one repair try, the four failure kinds, the token
  ledger `ai-usage.jsonl` in the plugin's data folder.
- `grading.py`, `routes_ai.py`: Score my answer and the Settings switches.
- `guide.py`, `content/foundations/_guide_text.py`: the Field guide (nudge, where, reveal, Explain my miss, Do it with
  me, pins, Ask), the help entries and the off states; the authored words and 27 starter questions.
- `cost.py`: the record's cost line, from Hermes's own per-chat estimate (`sessions.estimated_cost_usd` with its
  `cost_status`), tokens only when Hermes has no price.
- `recorder.py`: Replay your run (`GET /replay/{attempt_id}`, `GET /replay/sample`) and the event list the guide reads.
- `foundations.py` `first_flight_start`: the First Flight mark (always `write_approval`, Recall and the claim skipped,
  "Began as a first flight; snag chosen for first flight" in the record).
- Route shapes: one JSON per route and state in `tests/data/ai_contract/` (42 files), rebuilt and shape-checked by
  `tests/test_ai_contract.py`.
- `__init__.py` `_register_ai`: registers the two tasks; an older Hermes without `register_auxiliary_task` still loads.

## The in-chat practice offer

Separate from AI help: **practice_offer** in Settings controls the one-sentence offer the `pre_llm_call` hook can add
to a learner's own chat. On by default, as before. It stays silent until the learner picks a path, and with the switch
off the hook returns nothing and doesn't read the opportunity list.

## Not verified yet

Model calls from Field Academy's page routes inside a real Hermes (spike S1), the tasks appearing in Settings, Models,
and "no new chat in Sessions" are for the QA lane to confirm in a QA profile. Until then, every live claim above is
unverified. The Lane A bench (`docs/bench/`) used Field Academy's own prompt and checks with `claude -p` standing in
for Hermes.
