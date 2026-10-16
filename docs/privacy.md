# Privacy

Field Academy keeps a local record of the learner's own progress. It sends
nothing anywhere, and it holds no credentials.

## Where the data lives

A single SQLite database, resolved in this order:

1. `$FIELD_ACADEMY_DATA_DIR/data.db` when that variable is set (used by the test
   suite, which points it at a temp directory).
2. Otherwise `plugins.plugin_storage.plugin_db("field-academy")`, which is the
   Hermes plugin data directory — normally
   `$HERMES_HOME/plugin-data/field-academy/data.db`.

Two folders sit beside it: `pasted/` holds a document you pasted instead of typing
its location (for a Hermes on another computer), so it can be checked and
fingerprinted like any file, and `deployer/reviewers.local.json` holds any reviewer
key you added yourself.

Deliberately **outside** the installed plugin folder, so
`hermes plugins update` cannot erase it. Deleting progress is deleting that one
directory.

## What is stored

| Table | Columns | Why |
|---|---|---|
| `mission_steps` | `mission_id`, `step_id`, `status`, `note`, `updated_at` | which step is done, ready, or needs another try |
| `evidence` | `mission_id`, `step_id`, `kind`, `summary`, `artifact`, `sha256`, `bytes`, `session_id`, `created_at` | the proof a gate passed: the file's path, size, and hash, or the check's result line |
| `explanations` | `mission_id`, `step_id`, `answer`, `score`, `feedback`, `attempts`, `session_id`, `created_at`, `graded_at` | the learner's written answer, the agent's score, and the feedback |
| `opportunities` | `mission_id`, `tool_name`, `session_id`, `created_at` | which tool use made a mission worth offering in chat |
| `meta` | `key`, `value` | the chosen level, the active mission, the spotlight watermark, the schema version, your goal and re-verify requests |
| `attempts` | `mission_id`, `step_id`, `misses`, `last_feedback_json`, `updated_at` | how many times a step missed in a row and the feedback shown, so the hint ladder survives a restart |
| `reviews` | `mission_id`, `stage`, `interval_days`, `due_at`, `strength`, `reps`, `lapses`, `consecutive_misses`, `last_item`, `last_score`, `last_reviewed_at` | where each passed mission sits on the review schedule |
| `review_sessions` | `id`, `status`, `items_json`, `answers_json`, `results_json`, timestamps | the three questions of a review, your typed answers, and the scores Hermes gave |
| `completions` | `mission_id`, `step_id`, `answers_json`, `revealed` | what you wrote into the gaps of a half-done example |
| `placements` | `track_id`, `answers_json`, `results_json`, `applied_json` | your placement answers and which steps they skipped |
| `mission_versions` | `mission_id`, `passed_version`, `carried_over` | which version of a mission you passed, for What changed |

### The Guide path (0.6.0; its tables keep the internal id `deployer`)

| Table | What it holds |
|---|---|
| `deployer_labs` | each lab's seed, the folder it was built in, your attempts, your diagnosis with any key-shaped text removed, the last result, and the repaired folder's fingerprint |
| `deployer_items` | the proposal, the real deployment, the drills, the walkthrough and the review: status, score, fingerprint and a record of each |
| `deployer_answers` | your written answer to a scenario or the proposal, the score your own Hermes gave it, and the hint ladder |
| `deployer_attempts` | misses in a row and the last feedback, per part |
| `deployer_samples` | run times read from Hermes at each check, as timestamps and failure marks only. Never a prompt, a message or a secret. |
| `deployer_renewals` | a record each time you re-verify |

Labs are folders of files under `plugin-data/field-academy/labs/`, made of fake data. The review packet is a
folder under `plugin-data/field-academy/deployer/review/` with everything the reviewer reads, which includes your
written answers, your walkthrough, and any log excerpt you pasted (key-shaped text is removed first). It stays on
your computer until you send it to a reviewer. A recording you name for the walkthrough is fingerprinted and never
copied. Reading Hermes is read only: the plugin opens Hermes's run-history database read-only and immutable, reads
log files up to a size limit, and keeps only the times of lines that name your job.

**`session_id` is an identifier only.** It is stored so an opportunity can be
offered once per session. The plugin never reads a session's transcript, and it
does not store one.

**`answer` is whatever the learner typed.** It is their text, written to answer a
question the plugin asked, and it is what gets graded. It is the most sensitive
column in the database and it stays on the machine.

**`artifact` is a file path the learner typed.** The gate stores the path, the
byte count, and the SHA-256. It does not copy the document.

## What leaves the machine

Nothing, except the two things a person does on purpose:

- **Opening a source.** Clicking a link under a mission's Go deeper, or a
  lesson's linked part, hands the URL to the OS browser. That is a normal web request from the learner's
  browser, with whatever that site normally collects. The plugin sends nothing
  with it.
- **Grading.** An explanation is graded by the learner's own Hermes agent, in the
  learner's own session, on the learner's own provider account. The plugin builds
  the grading instruction server-side, opens a new chat and sends it there, the
  same way it sends a practice prompt; the model call is the chat's, under the
  chat's terms. Only on a Hermes too old to allow that does the instruction go to
  the clipboard for the learner to paste.

No analytics, no crash reporting, no update checks, no third-party endpoints.

## What the agent can see

Two hooks and six tools read the plugin's own database:

- `pre_llm_call` may add one sentence to the user message, offering a single
  practice, at most once per opportunity, only in an interactive session (the
  desktop app, the terminal UI or the CLI, never a messaging app, webhook or
  scheduled job). The
  context is appended to the **user message**, never the system prompt, and the
  session's stored transcript keeps the learner's own text.
- `post_tool_call` records which tool was used, mapped to a mission, once per
  mission per session.
- `field_academy_snapshot`, `field_academy_mission`, `field_academy_grade_explanation`,
  `field_academy_grade_review`, `field_academy_grade_deployer` and `field_academy_record_evidence` read and write the tables above.

## Deleting it

```bash
rm -rf "$HERMES_HOME/plugin-data/field-academy"
```

With `HERMES_HOME` unset that is `~/.hermes/plugin-data/field-academy`. Removing
the plugin does not remove the data; deleting that directory does.
