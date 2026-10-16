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

Open an issue at https://github.com/Dgardenhire/hermes-field-academy/issues, or email
the maintainer if the report should not be public first.

## Boundaries this plugin holds itself to

**File reads are bounded.** An artifact gate reads a file the learner names. The
read is capped at 5 MiB (`MAX_ARTIFACT_BYTES` in `state.py`) and the bytes must
decode as UTF-8, so a binary cannot satisfy a heading check by accident and a
large file cannot be read into the gateway process.

**Model-authored input is validated.** The transcript directive's `mission`
attribute is untrusted model output. It is trimmed and matched against
`^[a-z0-9][a-z0-9._-]{0,63}$` before use; anything else renders nothing. It is
only ever used as a lookup key and as a fallback display string, which React
escapes.

**Hooks are gated on two axes.** `pre_llm_call` and `post_tool_call` both refuse
scheduled, webhook, and gateway-delivered sessions by id prefix, and refuse
one-shot CLI runs by argv (`-z`, `--oneshot`, `-Q`). Session prefixes alone do
not catch a one-shot run, which gets a bare timestamp id.

**Gates cannot be talked around.** The state layer refuses `status='done'` on any
step a check owns, so the HTTP API cannot close a gate, a graded explanation, or
an artifact step without the check passing.

**No network calls.** The plugin makes none. It reads the local gateway over
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
