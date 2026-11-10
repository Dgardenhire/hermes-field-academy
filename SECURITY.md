# Security

## What this plugin is

Field Academy is a Hermes plugin with two halves:

- **Agent half** (`__init__.py`, `state.py`, `tools.py`, `schemas.py`,
  `curriculum.py`) — registers six tools, two hooks, one slash command, and one
  skill. It runs inside the gateway process, and only when `field-academy` is in
  `plugins.enabled` in `config.yaml`.
- **Desktop half** (`desktop/plugin.js`) — a single ESM file that registers a
  page, a sidebar row, a status-bar chip, a palette command, and a transcript
  directive. It runs in the desktop renderer with the app's authority, like every
  desktop plugin.

The desktop half is app-level and local to the machine running Desktop. The
agent half is per-profile and gated separately. Enabling one does not enable the
other.

## Reporting

Report a security problem privately through GitHub: open the repository's
**Security** tab and choose **Report a vulnerability**, or go straight to
https://github.com/Dgardenhire/hermes-field-academy/security/advisories/new.
Only the maintainer sees the report until a fix is out. For anything that is
safe to discuss in public, open an issue at
https://github.com/Dgardenhire/hermes-field-academy/issues.

## Boundaries this plugin holds itself to

**File reads are bounded.** An artifact gate reads a file the learner names. The
read is capped at 5 MiB (`MAX_ARTIFACT_BYTES` in `state.py`) and the bytes must
decode as UTF-8, so a binary cannot satisfy a heading check by accident and a
large file cannot be read into the gateway process.

**Links in a lab folder are never followed.** Symbolic links, Windows junctions
and other reparse points inside a lab are skipped when a lab is listed, graded,
fingerprinted or copied into the review packet (`plain_files` and `plain_file`
in `labs.py`). A link to a real `~/.hermes/.env` is never read and never copied.

**Model-authored input is validated.** The transcript directive's `mission`
attribute is untrusted model output. It is trimmed and matched against
`^[a-z0-9][a-z0-9._-]{0,63}$` before use; anything else renders nothing. It is
only ever used as a lookup key and as a fallback display string, which React
escapes.

**Hooks are gated on two axes.** `pre_llm_call` and `post_tool_call` both refuse
scheduled, webhook, and gateway-delivered sessions by id prefix, and refuse
one-shot CLI runs by argv (`-z`, `--oneshot`, `-Q`). Session prefixes alone do
not catch a one-shot run, which gets a bare timestamp id.

**What a check enforces, and what it takes from the page.** The state layer
refuses `status='done'` on any step a check owns, so the HTTP API cannot mark a
gate, a graded explanation or a fill-in step done by asking.

- A document gate closes only when the backend reads the saved file and checks it
  itself (`record_gate` and `verify_artifact` in `state.py`). A pass sent from
  the page for a document gate is refused.
- Four Operator gates read the learner's live Hermes, which only the page can do
  (`verify: "desktop"` in the curriculum). Their pass or miss is taken from the
  page as sent. The backend keeps only the plain parts and labels them on the
  Field Record as reported by the page. Someone who calls the backend directly
  can report a pass for these four. The same goes for the part of a document gate
  that reads Hermes (`live`).
- Written answers are scored by the learner's own Hermes through the agent tools.
  No page route writes a score. The learner runs that agent, so a score is only
  as honest as the learner and the model. The grading request marks the answer as
  untrusted text and tells the model to ignore instructions inside it.
- The Field Record is self-issued and kept on the learner's own computer. Its
  number shows the record hasn't been changed by accident. Anyone can edit a
  record and make a new number, so the number isn't proof on its own.
  The same goes for `MANIFEST.sha256` in a saved record folder: it shows the files
  match each other, not that the folder is the one saved. A reader who wants that
  compares the record number with one the holder sent earlier by another route.
- Everything kept from a practice profile is scrubbed: excerpts, check facts,
  titles and details, and every string in a record body (fingerprints and times
  excepted). An excerpt the current scrubber would change is withheld from a new
  record. Excerpts in `record.md` sit in a code fence longer than any backtick run
  inside them.

**No network calls of its own.** The plugin makes none itself. Its AI help asks the learner's own model through
Hermes's plugin model API (`ctx.llm.complete_structured`, tasks `field_academy_guide` and `field_academy_grader`), so
Hermes, not Field Academy, talks to the provider; every input passes the scrubber first, and the AI help switch turns
every call off. (A planted connector in missions 2 and 7 is a setting Hermes
acts on: Hermes downloads its pinned npm package with `npx` when a practice chat starts. See "Practice profiles".) It reads the local gateway over
JSON-RPC and its own backend namespace over the desktop bridge, and it opens a
URL in the OS browser only when the learner clicks a source card.

**Windows access lists, read through the system API.** On Windows a file's lock
is its access list, not mode bits. `fileaccess.py` reads and writes access lists
through `advapi32` and `kernel32` with `ctypes` from the standard library; it
runs no program (no `icacls` subprocess). It reads a file's owner and access list
to grade a Guide lab. It writes access lists in these places only:

- When the lab builder makes a lab's `client-machine` folder under Field
  Academy's own data folder, it creates the folder in one call with a protected
  access list (nothing taken from the folder above) that lets the computer's local
  **Users** group read and run it and everything made in it later (inherited),
  beside full control for you, SYSTEM and the administrators. That is the careless
  install the lab asks you to repair. It refuses to make the folder through a
  junction or a link.
- In that folder, each file a healthy setup keeps private (a key file, a profile's
  saved session, its memory) is locked to your account alone, one file at a time.
- `scripts/sign_review.py` creates the reviewer's secret key file locked to your
  account from the moment it exists.

Every key in a lab is made up. Never put a real key in a lab folder: other
accounts on the computer can read it until you lock it. On Linux and macOS the
same module uses `os.stat`, `os.mkdir` and `chmod`.

**No credentials.** The plugin asks for no keys and reads no environment
secrets. `requires_env` is empty.

**No telemetry.** Nothing is reported anywhere.

**No self-updater.** The plugin does not fetch or replace its own files. Updates
arrive through `hermes plugins update`, or through a reviewed SHA bump in the
Hermes plugin catalog.

## Practice profiles (Foundations, 0.9)

Foundations is the only part of Field Academy that writes outside its own data folder, and it writes into one
place: a practice profile it planned and recorded itself.

- **Names.** A practice profile is only ever `<root>/profiles/academy-practice[-b][-N]` (`practice.NAME` in
  `practice.py`). Anything else, a link in its place, or a `profiles` folder that is itself a link, is refused.
- **Writes** (`practice_write.py`): named `config.yaml` keys only, through `yaml_keys.set_values`, which changes just
  those lines; whole-file prefills of `memories/MEMORY.md` and `memories/USER.md`; and sample files inside the
  practice folder. Every write is refused when the profile isn't recorded at exactly that path, when a file or
  folder is a link, when the profile's backend is running (`gateway.pid`), or once anyone has sent a message in it.
  Writes go through a temporary file and `os.replace`. Never written: `.env`, `auth.json`, `mcp-tokens/`,
  `pairing/`, `platforms/`, any other file, any profile Field Academy didn't record, and the learner's own profiles.
- **Reads** (`hermes_read*.py`) are read-only and bounded: SQLite files open with `mode=ro` and `query_only` (`evidence._ro_connect`), text
  reads are capped, folder walks stop at a fixed count and never follow links, and only the `config.yaml` keys in
  `hermes_read.CONFIG_KEYS` are kept. Excerpts pass through `scrub.py`, which removes key-shaped text, before they
  are stored. `.env` and `auth.json` are never opened; a test watches every open during a full run of the readers.
- **Identity.** When a practice profile is recorded, its folder's identity on disk (device and inode) is kept. Every
  write, the delete, the memory view, the checks and the job list check the folder at that path is still the one
  recorded; a profile deleted and made again under the name, or another profile renamed to it, is refused and the
  record let go. A name that was planned but never recorded is deleted only when the folder there is the one Field
  Academy asked for: made after the plan, carrying the planned SOUL.md (not a link), and not a Hermes Bots profile.
- **Planted problems act like real settings** until the learner fixes them: a filesystem connector Hermes starts
  with `npx` (a pinned npm package, so Hermes downloads and runs it, scoped to a folder in the practice profile), an
  approval safeguard switched off in mission 9 (the terminal tool still reaches the whole computer), and hourly jobs.
  See `docs/privacy.md`, "What the planted problems do while they stand".
- **Gateway calls into a practice profile** go through `host.requestProfile` on that profile's local route:
  `cron.manage` (`add`, then `pause`, and `remove` for a job that won't pause) for the jobs a mission needs,
  `session.list` and `rollback.list`. Profiles are made with `profiles.create` and removed with the app's own
  `deleteProfile`, only after the learner confirms.

## Data

Progress lives in a SQLite database under the Hermes plugin data directory
(`$HERMES_HOME/plugin-data/field-academy/data.db`), never inside the installed
plugin folder, so an update cannot erase it. See `docs/privacy.md`.

## What a reviewer should check

- `hermes plugins validate .` — manifest, declared-vs-registered capabilities,
  built-in tool collisions, and the install-time security scan.
- `grep -rn "openExternal\|fetch(\|http" desktop/plugin.js` — the only outbound
  path is a user-clicked source link.
- `grep -n "MAX_ARTIFACT_BYTES" -A3 state.py` — the read bound.
- `python -m unittest discover -s tests` — the invariant suite.
