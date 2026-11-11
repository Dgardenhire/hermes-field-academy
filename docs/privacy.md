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
copied. Reading Hermes is read only: the plugin opens Hermes's run-history database read-only and never writes to it, reads
log files up to a size limit, and keeps only the times of lines that name your job.

### Foundations practice profiles (0.9)

Foundations missions run in practice profiles Field Academy makes for you, named `academy-practice` and
`academy-practice-b` (with a number added for a new try), through Hermes's own `profiles.create`. Hermes copies your
current provider sign-in into a new profile by default so practice chats work; Field Academy never reads, hashes or
copies those files (the folder fingerprint lists `.env`, `auth.json`, `.env.*` and anything under `mcp-tokens/`,
`pairing/` and `platforms/` by size and time only). It never reads or writes any profile it did not make and record,
including your own: when it records a practice profile it keeps the folder's identity on disk, and before every
write, read and delete it checks the folder there is still that one. A profile deleted and made again under the
practice name, or another profile renamed to it, is left alone and Field Academy lets go of its record.

Field Academy writes only into a practice profile it recorded, and only before anyone has chatted in it and while
its backend isn't running:

- `config.yaml`, named keys only (the list is in `practice_write.py`): `terminal.cwd`, always set to the practice
  profile's own folder or its practice folder; `memory.write_approval` and `skills.write_approval`;
  `checkpoints.enabled`; `model.default`,
  `cron.model` and `delegation.model`; connector entries under `mcp_servers.<name>` (`command`, `args`, `enabled`,
  `trust`, `tools.include`, `tools.exclude`); `agent.disabled_toolsets` and `fallback_providers`. Never an
  `approvals.*` key and never `command_allowlist`: Field Academy cannot switch approvals off, loosen them or
  pre-approve a command, and tests refuse any attempt;
- `memories/MEMORY.md` and `memories/USER.md`: a few seed notes, and for one planted problem enough notes to fill
  memory close to its limit;
- sample files (orders, notes, a CSV) in the profile's practice folder, at most two folders deep.

Through Hermes's gateway, aimed at the practice profile only, the page asks Hermes to make and pause the scheduled
jobs a mission needs (`cron.manage`), lists its chats (`session.list`) and undo snapshots (`rollback.list`), opens a
new chat there, and on a Hermes that offers them starts that profile's doctor and backup.

It reads, read-only, from the practice profile only: the two memory files, staged saves under `pending/`, named
`config.yaml` keys, skill names, descriptions and use counts, chat records and usage in `state.db`, `cron/jobs.json`
and the run history, `agent.log`, `errors.log`, `gateway.log` and `mcp-stderr.log`, and the undo snapshot folder.
Everything is compared on your computer. Only short excerpts with key-shaped text removed are kept, and you can
withhold any of them from your Field Record. It deletes a practice profile only after you confirm, through the
app's own delete, and never a profile it did not make. Your app's active profile never changes.

**`session_id` is an identifier only.** It is stored so an opportunity can be
offered once per session. The plugin never reads a session's transcript, and it
does not store one.

**`answer` is whatever the learner typed.** It is their text, written to answer a
question the plugin asked, and it is what gets graded. It is the most sensitive
column in the database and it stays on the machine.

**`artifact` is a file path the learner typed.** The gate stores the path, the
byte count, and the SHA-256. It does not copy the document.

### What the planted problems do while they stand

A planted problem is a real setting in the practice profile, so it acts like one until you fix it. None of them
touches your own profiles. Read this before a mission, not after:

- **Connectors (missions 2 and 7).** The practice profile gets a filesystem connector,
  `npx -y @modelcontextprotocol/server-filesystem@2026.8.31` aimed at a folder inside the practice profile. When a
  practice chat starts, Hermes runs it: `npx` downloads that pinned package from the npm registry (a network call
  Hermes makes, not Field Academy) and keeps it running as a background program while the chat is open. It can reach
  only the folder it is given. Mission 10 points a connector at a program inside the practice folder that isn't
  there, so Hermes fails to start it; don't put a program at that path to "fix" it.
- **A wide connector (mission 13 and the Teach mission).** A filesystem connector called `notes` reaches
  `settings-copy/` in the practice profile: made-up copies of `config.yaml`, `SOUL.md` and the memory file, and no
  sign-in. It stands in for the profile's own folder, where Hermes keeps the sign-in it copied in, so the lesson holds
  without putting your keys in a practice chat's reach. Field Academy refuses to aim any connector at a profile's own
  folder, above it, or at any sign-in file (`.env`, `auth.json`, `mcp-tokens/`, `pairing/`, `platforms/`).
- **Safety (mission 9, the Foundations review and the Teach mission).** One connector is added to the practice
  profile and left at Hermes's default trust, so nothing asks before it acts. It works inside a folder in the practice
  profile. Mark it untrusted or switch it off in Settings. Field Academy does not touch approvals: you read the mode
  and the Command Allowlist box yourself, change them yourself if they need it, and answer Hermes's own approval card
  for the delete in the tidying job. Never point a practice chat at files you care about.
- **Scheduled jobs (missions 8, 10 and 11).** Jobs are made through Hermes's own `cron.manage`, most of them paused.
  Mission 10's job is left on with a misspelled delivery place, so Hermes blocks each hourly run before it starts.
  A job you repair runs every hour on your provider and delivers where you point it: use `local` unless you mean to
  send a message. Pause or delete practice jobs when a mission ends; deleting the practice profile removes them.
- **Practice chats** use your own model provider, like any chat; each mission states its expected cost.

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
  practice, at most once per opportunity, only while
  **Suggest missions while I chat** is on (off until you say yes to the question at the top of the home page), only in an interactive session (the
  desktop app, the terminal UI or the CLI, never a messaging app, webhook or
  scheduled job). The
  context is appended to the **user message**, never the system prompt, and the
  session's stored transcript keeps the learner's own text.
- `post_tool_call` records which tool was used, mapped to a mission, once per
  mission per session.
- `field_academy_snapshot`, `field_academy_mission`, `field_academy_grade_explanation`,
  `field_academy_grade_review`, `field_academy_grade_deployer` and `field_academy_record_evidence` read and write the tables above.

## Deleting it

In Field Academy, open **Your data** (at the foot of the home page, or in Hermes under Settings, Plugins, Field
Academy). **Delete my progress** removes everything in the data folder except your saved Field Records and the two
tables that list them (`certificates`, `f_issued`). **Delete everything** removes those too. Each asks for a yes
first, deletes any practice profile still set up, keeps the two switches, and compacts the database so deleted rows
don't stay in the file. Records you saved outside the data folder are never touched.

If the plugin is already removed, delete the folder by hand:

```bash
rm -rf "$HERMES_HOME/plugin-data/field-academy"
```

With `HERMES_HOME` unset that is `~/.hermes/plugin-data/field-academy`. Removing
the plugin does not remove the data; deleting that directory does.
