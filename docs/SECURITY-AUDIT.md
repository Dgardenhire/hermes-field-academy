# Field Academy 0.9 security audit

Independent audit of Field Academy 0.9 (Foundations) against the hackathon security bar (ten items: secrets,
dependencies, static analysis, inputs, prompt injection, approvals and gates, catalog rules, privacy, fresh-machine
install, evidence). The auditor did not build the plugin.

- **Branch and base:** `foundations-0.9`, audited from `46dc1dc`. Fixes are the four `audit:` commits after it.
- **Date:** November 8, 2026.
- **Ground rules kept:** no `hermes` command was run, nothing was installed into `~/.hermes`, no `.env`, `auth.json`
  or Keychain item was read, no real profile was touched. Every attack ran against scratch Hermes roots the test
  suite builds.

## Verdict

Pass with one open item, Low and accepted (B2 below). Seven findings were fixed with tests that fail without each fix,
and B1, left open by the audit, was fixed after it the same way. The most serious, A1, could have deleted a learner's
own profile.

## Tools run

| Tool | Scope | Result |
|---|---|---|
| `gitleaks git . --redact` | 137 commits, about 6.5 MB | No leaks, before and after the fixes. A gitleaks pre-commit hook also passed on each `audit:` commit. |
| `gitleaks dir . --redact` | working tree, about 22 MB (screenshots included) | No leaks. |
| Dependencies | `git ls-files` | No `requirements*`, `pyproject`, `package.json` or lockfile. The Python code is standard library only (imports listed by grep), so `pip-audit` and `npm audit` have nothing to read. |
| OSV (`api.osv.dev/v1/querybatch`) | Every pinned third-party package: `@modelcontextprotocol/server-filesystem@2026.8.31` (the planted connector Hermes runs with `npx`), and the harness's CDN pins `react@19.2.7`, `react-dom@19.2.7`, `@tanstack/react-query@5.101.2`, `@vscode/codicons@0.0.45` | No known vulnerabilities for any of them. The npm registry confirms `2026.8.31` is a published version. osv-scanner isn't installed and isn't on PyPI, so the OSV API was queried directly. |
| `uvx bandit -r . -x ./tests` | 19.6k lines | 0 High. 13 Medium (after the fixes; 14 before), 46 Low. Each is explained under "Static analysis" below. |
| `uvx semgrep --metrics=off` with `p/python`, `p/security-audit`, `p/secrets`, `p/javascript` | 171 tracked files, 326 rules | 3 findings, none in code Hermes loads (see below). |
| Test suite | `python3 -m unittest discover -s tests` | 1,125 tests before (21 skipped). 1,145 after, all passing (21 skipped). The Node suite, `node --test tests/`, has 230 tests, all passing. After the B1 fix: 1,148 Python (23 skipped on the machine that ran it) and 238 Node, all passing. |
| Public package | `build.sh` from `nous-hermes-plugins/public/` run on the final head (`7fce134`) into a scratch folder | 268 files, this audit included. Every path in `.public-exclude` is gone (`.github`, `docs/brief-img`, `docs/concept-brief-nous.html`, `docs/make_brief.py`, `docs/catalog`, `docs/DEMO-NOTES.md`, `docs/STATUS.md`), and so is the list itself. No personal path (`/Users/…`, an email address) anywhere; the only home paths are test fixtures (`/home/ada`, `C:/Users/you`). The build's binary and credential-shape checks passed, and the package's own test suite passes (1,145 run, 25 skipped: the exclude-list tests skip once the list is applied). |

### Static analysis, explained

- **B608 (SQL built from strings), 12 left.** Every one builds a query from code constants: `?` placeholder lists
  (`field_record.py:302-307, 342`, `foundations_b.py:174`), the constant `OPEN` tuple (`foundations.py:117`), a
  fixed `kind` clause (`foundations.py:146`), or column names intersected with a fixed list (`hermes_read._rows`).
  Values always go through placeholders. The one that took a name from a database file, `evidence._scan_tables`,
  was fixed (A5).
- **B610 (`deployer.py:545`).** A false positive: a local function named `extra`, not Django.
- **B105 (hard-coded password), 19.** Rubric strings and fixture values, no credentials.
- **B311 (`random`), 9.** Seeded generators that vary planted values per learner. Nothing security-relevant is drawn
  from them; the practice plan token uses `secrets.token_hex`.
- **B603/B404/B607.** `harness/shoot.py` starts headless Chrome and `scripts/check_foundations.py` runs `git`, both
  with fixed argument lists and no shell. Neither is loaded by Hermes.
- **B101/B110.** Asserts in the harness, two deliberate `except: pass` around best-effort reads.
- **Semgrep.** `dangerous-subprocess-use-tainted-env-args` in `.github/platforms/hermes_run.py:51` (CI only, not in
  the public package) and `harness/shoot.py:194` (developer screenshots): fixed argument lists, no shell, not loaded
  by Hermes. `insecure-file-permissions` at `practice_write.py:177` is the planted lock: it only ever removes write
  bits or restores the owner's write bit.

## Findings

Severity is for the learner using the plugin as shipped. "Fixed" means fixed in this branch, with a test in
`tests/test_audit_090.py` that fails without the fix (each was run against the unfixed code and failed).

### A1. High: a folder at a practice name that Field Academy didn't make could be deleted, written or read. Fixed.

- **Where:** `practice.py:553` `prepare_remove` and `practice_write.py` `guard`, as of `46dc1dc`.
- **Scenario:** Field Academy records `academy-practice`. The learner deletes it in Settings, Profiles and later makes
  a real profile with that name, or renames a real profile to it. The record still says `ready`, the path matches, so
  **Delete** on the mission page snapshots the real profile's memory and config into Field Academy's folder and asks
  the app to delete it. The same profile could be written into (`guard` checked only the name, the path, the backend
  and that nobody had chatted) and read by the memory view and the checks. A second path: a name planned but never
  recorded (Hermes's reply lost, or the folder refused as "there before this plan" or a Hermes Bots profile) could
  still be sent to the app's delete, whatever was at that name.
- **Fix:** `confirm` keeps the folder's identity on disk (`folder_id`: device and inode). `is_ours` checks it before
  every write (`guard`), the delete, the memory view, the working-folder check, the job list, the checks and Compare,
  and the page's status read; a record from before has to carry its plan token in SOUL.md. A folder that isn't ours
  is refused, and the record is let go so nothing tries again. A planned name is deleted only when the folder there
  is the one Field Academy asked for (made after the plan, the planned SOUL.md, not a Hermes Bots profile).
- **Tests:** `A1ProfileIdentity`, six tests, including a renamed profile carrying a copied SOUL.md.
- **Commit:** `c4d7682` (the checks and Compare part is in `481b304`).

### A2. Medium: the scrubber missed common secret shapes. Fixed.

- **Where:** `scrub.py:36` (as of `46dc1dc`).
- **Scenario:** a practice chat, memory line, log or job holds a Hugging Face token (`hf_` plus 34), a Discord bot
  token (three dotted parts, none 40 long), a Slack webhook address (24-character secret, slashes stop the catch-all),
  Firecrawl or Tavily keys, a password inside an address (`https://user:pass@host`), a Basic login header, or JSON
  such as `{"api_key": "…"}` (the closing quote after the name stopped the key=value rule). Each survived into kept
  excerpts and the Field Record.
- **Fix:** patterns for each (`scrub.py:36-45`). Token counts such as `max_tokens: 4000` are untouched.
- **Tests:** `A2Scrubber`, five tests. **Commit:** `481b304`.

### A3. Medium: check facts and plant facts reached the database and the Field Record unscrubbed. Fixed.

- **Where:** `foundations_checks.py:29` `outcome`, `foundations.py` `_compare`, `hermes_read.py` `cron_jobs`,
  `field_record.py` `build` (as of `46dc1dc`).
- **Scenario:** only excerpts were scrubbed. A check's facts, title and detail quote what Hermes holds: a job's
  delivery place (which can be a webhook address with its secret), an always-allow entry, a model name. They were
  stored in `f_checks`, copied into record entries ("caught", "missed") and written into `record.json` and `record.md`.
- **Fix:** `outcome` scrubs titles, details, facts and missing lines; Compare scrubs plant facts; `cron_jobs` scrubs
  `deliver`, `workdir`, `model` and `provider`; `field_record.build` scrubs every string in the body except
  fingerprints and times (`_scrubbed`, `field_record.py:322`). An excerpt kept before the scrubber knew its shape
  is withheld instead of written (`field_record.py:217`), so `write_folder`'s fingerprint check never meets it.
- **Tests:** `A3FactsAndRecord`, four tests. **Commit:** `481b304`.

### A4. Low: an excerpt could close its code fence and write lines into `record.md`. Fixed.

- **Where:** `field_record.py:657` (as of `46dc1dc`).
- **Scenario:** text read from a practice profile (a memory line, a tool result, a planted order) containing three
  backticks ends the fence. Lines after it render as part of the record, for example a forged
  "Caught: … *(Field Academy read it.)*" line or a remote image that pings a server when a stranger opens `record.md`
  in a viewer. `record.json` and the fingerprints were not affected.
- **Fix:** the fence is one backtick longer than the longest backtick run in the excerpt (`field_record.py:681`).
- **Test:** `A4Markdown`. **Commit:** `481b304`.

### A5. Low: a table name read from a database file was put into SQL unquoted. Fixed.

- **Where:** `evidence.py:290`, the Guide's run-history scan.
- **Scenario:** the connection is read-only and `query_only`, so nothing could be written, but a table name with a
  double quote broke the query and the table was skipped silently.
- **Fix:** the name is quoted with doubled quotes. **Test:** `A5RunHistoryScan`. **Commit:** `481b304`.

### A6. Medium (claims): the record folder's README overstated what the MANIFEST proves. Fixed.

- **Where:** `field_record.py:757` (README.txt in every saved record) and `README.md:105`, as of `46dc1dc`.
- **Scenario:** README.txt said the checks "prove the files haven't changed since the record was saved". They
  don't: `MANIFEST.sha256` sits beside the files and the record number is a hash of `record.json`, so whoever edits
  a file can rewrite both and every check passes. They prove the files match each other, which catches accidental
  damage. `SECURITY.md` already said the number "isn't proof on its own"; the stranger-facing text didn't.
- **Fix:** both now say the checks show the files match each other, not that the folder is the one saved, and tell
  a reader to compare a record number sent earlier by another route. What they don't prove (that Hermes made the
  files, that the work was honest) stays.
- **Test:** `A6RecordReadme`. **Commit:** `481b304`.

### A7. Low: a linked SOUL.md or profile.yaml was followed, and sign-in token files were hashed. Fixed.

- **Where:** `practice.py:300` `_same_text`, `catalog_profile`, and `NEVER_HASHED` at `practice.py:166`.
- **Scenario:** a SOUL.md that is a link to a file with the planned text passed `confirm`; a linked profile.yaml
  was read through. The fingerprint hashed every file except `.env` and `auth.json`, so files Hermes keeps sign-in
  tokens in (`mcp-tokens/`, `pairing/`, `platforms/`, `.env.*`) were hashed, against the documented rule that no
  hash of a key is kept. A SHA-256 of a random token can't be reversed; the rule was still broken.
- **Fix:** a linked SOUL.md never matches; a linked profile.yaml counts as a Hermes Bots profile and is left alone;
  those token files are listed by size and time only.
- **Tests:** `A7LinksAndTokenFiles`, two tests. **Commit:** `20ace97`.

### A8. Medium (disclosure): what planted problems do, and the keys written, weren't fully disclosed. Fixed.

> Later change (Nov 10): the `_plant_always_allow` and `_plant_approvals_off` plants named below were removed. Field
> Academy no longer writes `approvals.*` or `command_allowlist`; mission 9 plants a connector at default trust instead.

- **Where:** `README.md`, `SECURITY.md`, `docs/privacy.md` as of `46dc1dc`; the behaviour is in `plants_a.py:322`
  `_plant_extra_connector`, `plants_b.py` `_setup_connectors`, `_plant_twin`, `_plant_always_allow` (`:394`),
  `_plant_approvals_off` (`:422`), `_plant_broken_connector` (`:449`) and `_plant_job_blocked` (`:483`).
- **Scenario:** the docs said "no network calls … no shell commands, no background processes". True of Field
  Academy itself, but its planted connectors make Hermes run `npx -y @modelcontextprotocol/server-filesystem@2026.8.31`
  when a practice chat opens, which downloads a package from npm and keeps a program running. Mission 9 plants
  `approvals.mode: off` or a recursive delete in `command_allowlist`, and the terminal tool can reach the whole
  computer while the problem stands. Mission 10 leaves an hourly job on, and a job the learner repairs runs on the
  provider every hour and delivers where it points. `docs/privacy.md` also left out half the config keys
  `practice_write.WRITABLE_KEYS` allows (approvals, checkpoints, the model keys, connector fields).
- **Fix:** a new section, "What the planted problems do while they stand", in `docs/privacy.md`, a summary in
  `README.md`, and two notes in `SECURITY.md`. The key list now matches the code. **Commit:** `bc9e13d`.
- **Not changed, by design:** the plants themselves. They are the lesson, and each one is confined to the practice
  profile: the connector's only folder argument is inside the practice profile, the pinned package has no OSV
  advisories, and mission 7 also switches off Hermes's own `file` and `terminal` toolsets.

### Left open by the audit

**B1. Low: a practice job meant to start paused could stay on. Fixed after the audit.** `desktop/src/foundations_b.js:112`
paused a job only when the add call returned an id it recognised (`addedJobId`); if Hermes answered in another shape,
the pause was skipped without a word, and `practice.jobs_made` recorded the job as made whatever its `enabled` state.
The job then ran hourly on the learner's provider.

- **Fix (fails closed):** `practice.jobs_to_make` reads the practice profile's job list and returns `still_on`, each
  job meant to start paused that the list shows on, with the id the list gives it. `jobs_made` no longer records such
  a job, and it stays off the add list, so a retry never makes a second job by the same name. On the page, `makeJobs`
  (`desktop/src/loop_b.js`) pauses by the id the add returned, then asks the backend to read the list. A job still on
  is paused by its listed id (or its name, which Hermes's `cron.manage` also accepts), then deleted if it still won't
  pause, and nothing after it is made. What the learner sees is plain: the job was deleted and nothing from it runs,
  or the job is on and they should pause or delete it in Scheduled jobs. If the list can't be read, the page pauses
  by id or name anyway and says it couldn't confirm. The panel runs on its own once per visit, so a job that won't
  pause can't be made and deleted over and over.
- **Tests:** `tests/test_audit_090.py` `B1PlannedPausedJob` (three, each fails on the unfixed `practice.py`) and eight
  `B1:` tests in `tests/loop_b.test.mjs` against a stand-in Hermes: no id in the reply, a pause that doesn't take, a
  pause and delete that both fail, a job the list never shows, an unreadable list, a job left on by an earlier try,
  and an add that throws.
- **Bundle:** rebuilt with `hermes-ui-kit` at its committed HEAD (`e3fccf9`), taken with `git archive` into a scratch
  folder beside a copy of the plugin, so the bundle's path comments read `../hermes-ui-kit/src/…` and carry no
  `/Users` path. The same kit reproduced the previous bundle byte for byte from the previous source first, and
  `build.mjs --check` passes on the new one.

**B2. Low, accepted: the backend trusts a `confirm: true` it can't tell from a click.** Any caller of the plugin's
backend routes can send it. After A1 that can only ever delete a practice profile Field Academy made and recorded,
and the delete itself goes through the app's own `deleteProfile`. Accepted as designed.

## The bar, item by item

1. **Secrets.** gitleaks clean over history and tree. Test secrets are built at run time. The plugin holds no
   credentials and asks for none (`requires_env` is empty). The scrubber was widened (A2) and now covers every
   field that can quote a practice profile (A3).
2. **Dependencies.** None: Python standard library only, and the desktop file imports only `@hermes/plugin-sdk`,
   `react` and `react/jsx-runtime` (counted in the built `desktop/plugin.js`). The one package a learner's machine
   runs because of Field Academy, the planted filesystem connector, is pinned to an exact version with no advisories.
3. **Static analysis.** bandit and semgrep run with uvx; no High; every Medium explained above.
4. **Inputs.** Practice names are matched against `^academy-practice(?:-b)?(?:-[2-9]|-[1-9][0-9])?$` and resolved
   inside `profiles/`, refusing links (`practice_home`). Every write goes through `guard`, a fixed file list or
   pattern (`WORK_FILE`, `SKILL_FILE`, `_FOLDER_FILE` with `..` refused), link checks on every folder on the way,
   and `mkstemp` plus `os.replace` in the same folder. Readers refuse `..`, links and `.env`/`auth.json` by name,
   cap sizes and walk counts, and open SQLite read-only with `query_only`. Record folders are written only under
   Field Academy's own data folder with fixed names. No `shell=True` anywhere; no fetcher, so no SSRF surface.
   Cleanup: the only delete is the app's `deleteProfile` on a verified practice profile (A1); Field Academy itself
   removes nothing outside its data folder, and before a delete it only clears the lock it set on its own file.
5. **Prompt injection.** Checks are deterministic code reading files; no model output decides a check. Practice
   content reaches the learner only as escaped React text and fenced Markdown (A4). The grading prompt carries the
   learner's answer marked as untrusted, and a grade can only fill a pending answer's level; that self-grading is
   disclosed. A practice chat's model can't call Field Academy's tools unless the learner enables the plugin in that
   profile, and its data folder is per profile. Mission 7's planted injection (an order telling Hermes to move files)
   is confined by the folder-scoped connector with the file and terminal toolsets off.
6. **Approvals and gates.** Deleting needs `confirm` and, after A1, a verified folder. Writes stop at the first chat
   and while the profile's backend runs. Checks that can't read never pass. Gates fail closed: an unreadable chat
   store refuses writes, an unreadable profile.yaml counts as a Hermes Bots profile.
7. **Catalog rules.** Desktop surface uses only the SDK; no compiled binaries (build check passed); the six tools,
   two hooks, one command and the skills registered in `__init__.py` match `plugin.yaml`; `requires_hermes:
   ">=0.22.0"`. Disclosures now match the reads, writes and gateway calls (A8).
8. **Privacy.** No telemetry, no network calls by Field Academy. Demo data is made up (Ada Lovelace, Harbor Bakery,
   Loretta Abernathy is labelled as invented). What leaves the computer is listed and now includes what Hermes does
   because of a planted connector.
9. **Fresh-machine install.** Not done here: the rules for this audit forbid running Hermes or installing into
   `~/.hermes`. `docs/LIVE-TEST.md` is the checklist for a clean macOS install; the plugin's own README says no live
   run has been done yet. This item stays open for the live test.
10. **Evidence.** This file.

## Second review

An independent second review of everything after the first audit: `git log dfbfdbc..HEAD`, which is one commit,
`6388ddf` (the persona test fixes: a try form per mission, test-out, the record a stranger reads, the re-check panel,
the warnings on missions 2, 7 and 9). The reviewer did not build those changes. Same ground rules as the first audit:
no `hermes` command, nothing installed into `~/.hermes`, no `.env`, `auth.json` or Keychain read, no real profile
touched. Fixes are the four `audit:` commits after `6388ddf` (`5edf101`, `bea9fc5`, `a3a12a8`, `486b76c`).

### Verdict

Pass. Five findings, all fixed, each with a test in `tests/test_audit_090.py` that was run against the unfixed code
and failed. The most serious, C1, let a test-out go into the record as "Tested out" when the first run's own result
said a check had missed.

### Tools run

| Tool | Scope | Result |
|---|---|---|
| `gitleaks git . --redact` and `gitleaks dir . --redact` | 149 commits (6.8 MB) and the working tree (22 MB) | No leaks. The gitleaks pre-commit hook passed on each `audit:` commit. |
| `uvx pip-audit` | No dependency manifest is tracked. Every import outside the standard library was listed from the code: `fastapi` (the Hermes dashboard's own, in `dashboard/`), `plugins` (Hermes's own, in `store.py`), `yaml` (tests only), `hermes_cli` (CI only) | Field Academy installs nothing. `pip-audit` on an empty requirements list: no known vulnerabilities. |
| `uvx bandit -r . -x ./tests` | 29k lines | 0 High, 13 Medium, 46 Low: the same counts and the same lines as the first audit (12 B608 built from code constants, the B610 false positive). Nothing new from `6388ddf`. |
| `uvx semgrep --metrics=off` with `p/python`, `p/security-audit`, `p/secrets`, `p/javascript` | 172 files | The same 3 findings as the first audit, none in code Hermes loads. |
| Test suite | `python3 -m unittest discover -s tests`, `node --test tests/` | Before: 1,182 Python run, 1 failing (C5), 21 skipped; 250 Node passing. After: 1,190 Python run, all passing, 21 skipped; 250 Node, all passing. |
| Public package | `build.sh` from `nous-hermes-plugins/public/` on `486b76c`, with the repo's `.public-exclude`, into a scratch folder | 272 files. Every excluded path is gone (`.github`, `docs/brief-img`, `docs/concept-brief-nous.html`, `docs/make_brief.py`, `docs/catalog`, `docs/DEMO-NOTES.md`, `docs/STATUS.md`) and so is the list. No `/Users/…` path and no email address except test fixtures (`example.com`, `example.invalid`). No executable or bytecode; the only binary files are PNG and JPEG screenshots. The build's own binary and credential-shape checks passed. Its test suite: 1,190 Python run, all passing, 25 skipped; 250 Node, all passing once `harness/make_fixtures.py` writes the git-ignored `harness/fixtures.json` that `tests/trail_map.test.mjs` reads (without it, that one file stops with "no such file"). |

### Findings

#### C1. High (honesty of the record): a test-out could be "Tested out" with a check missed. Fixed.

- **Where:** `foundations.py` `_test_out_state`, as of `6388ddf`.
- **Scenario:** a test-out passed when every check in the learner's standard passed on the first run. The standard is
  not every check. Missions 2, 4, 5 and 7 to 10 don't map the hidden planted-problem check (`plant_fixed`) into their
  standard; missions 1, 2, 3, 7 and 10 each have a visible check the standard doesn't map (`trips`,
  `models_counted`, `notes_kept`, `folder_outcome`, `round_one`); and at Advanced the learner chooses which course
  checks to keep. So a first run whose own result read "Not there yet" (the planted problem left in place, or the seed
  notes lost) unlocked the Record step, and the entry said "every check passed on the first run". An Advanced
  test-out that dropped the explanation check went in with no explanation graded.
- **Fix:** a test-out passes only when every live check of the first run passed, the hidden one included, and, when
  the course's standard grades an explanation, its first grade passed. record.md now says the hidden check was
  included, and mentions the explanation only when one was graded.
- **Tests:** `C1TestOutNeedsEveryCheck`, two. **Commit:** `5edf101`.
- **Can a learner forge a pass otherwise?** No route found. The test-out mark is written only by `start`, before the
  freeze, and never by `save_entry`; checks run only after the freeze; a live result comes only from Field Academy's
  own readers (the page's `sample` is kept as `page_sample` and never counts); the first run can't be re-run; the
  explanation's level can only come from the agent tool, once per answer, and the first grade is the one that counts.
  The explanation is self-graded by the learner's own Hermes, which the record says.

#### C2. Medium (privacy): a withheld excerpt's facts still went into the record. Fixed.

- **Where:** `field_record.py` `_entry`, as of `6388ddf`.
- **Scenario:** `6388ddf` added "What the check found: …" under each excerpt, from the check's facts. When the holder
  withheld an excerpt, its facts were still written into `record.json` and `record.md`, and a fact can quote the
  same line the holder chose to keep private.
- **Fix:** a withheld excerpt keeps no facts. Kept facts are scrubbed again in `_entry` (`clean_facts`), as excerpts
  are.
- **Tests:** `C2WithheldFacts`, two. **Commit:** `bea9fc5`.

#### C3. Medium (record integrity): values quoted in record.md could change its structure. Fixed.

- **Where:** `field_record.py` `record_markdown`, `ask_holder`, `_facts_words` and `_cell`, as of `6388ddf`.
- **Scenario:** A4 fenced the excerpts, but the new captions put fact labels and values, check text, plant titles
  and file names straight into record.md lines, and so did the holder's own lines. A newline or Markdown in any of
  them (a job's delivery place, a skill's file name, a line Hermes wrote) could start a forged heading, a table row,
  a "Caught: … *(Field Academy read it.)*" line, a link, raw HTML or a remote image that pings a server when a
  stranger opens the record.
- **Fix:** every such value is written as one line with Markdown's control characters escaped (`_md`), table cells
  included; a file name is an inline code span whose backtick run is longer than any inside it (`_code`).
  `record.json` keeps the values as they were.
- **Tests:** `C3RecordMarkdownStructure`, two: values carrying backticks, newlines, `#`, `|`, `[ ]`, `>` and `<img>`
  never leave their line. **Commit:** `bea9fc5`.

#### C4. Medium: mission 7's settings text could be read from a real profile and copied in full. Fixed.

- **Where:** `foundations_b.py` `connector_text`, `ops` and `watch`, and `foundations_a.py` `_planted`, as of `6388ddf`
  (the readers date from `fcef123`; `6388ddf` added the copy button's full-text copy beside the masked view).
- **Scenario:** A1 put `require_ours` in front of every reader it found, but not these. If the practice profile was
  deleted in Settings and a real profile was made again under its name, mission 7's panel read that profile's
  `mcp_servers` in full, tokens included. The screen masked them; the copy button put the real secrets on the
  clipboard. The unfixed code returned a test token planted in such a profile.
- **Fix:** each of the four refuses a folder that isn't the one Field Academy made, and lets the record go.
- **Tests:** `C4ConnectorTextIdentity`, two. **Commit:** `a3a12a8`.
- **What the copy button copies now:** the practice profile's own `mcp_servers`, which hold the connectors Field
  Academy planted and anything the learner added there. Practice profiles are made with `profiles.create` without
  cloning the learner's config (`practice.plan`); that Hermes copies no connector settings into a new profile is
  taken from its request shape, not seen live (no Hermes was run).

#### C5. Low: the branch's own release guard failed. Fixed.

- **Where:** `tests/persona_fixes.test.mjs`, added in `6388ddf`.
- **Scenario:** a fixture path under a macOS home folder (`/Users/` and a name) tripped `test_release`'s personal-path guard, so the Python suite
  failed on the branch head, and the same check guards what ships.
- **Fix:** the fixture uses `/home/ada/…`, as the other fixtures do. **Commit:** `486b76c`.

### Reviewed and left as they are

- **Try forms.** `clean_try` keeps only the fields the mission declares (`lab.try_fields`), each checked by kind,
  required ones required, length-capped; anything else in the body is dropped, so the memory mission's guess and
  token count can't land in another mission's record. Mission 11, which has no try, refuses a try note outright. The whole body is capped at 16,000 characters, and every string is scrubbed when
  the record is built.
- **On-screen masking (`screenSafe`).** It hides passwords in addresses, secret-named query and JSON values, bearer
  and basic tokens, and the common key shapes. It is a screen-share guard, not a scrubber: a secret under a name it
  doesn't know (`SERVICE_KEY`, say) or passed as a command argument (`--token x`) would still show. Low, accepted: the
  text is the practice profile's own, and after C4 it can't be anyone else's.
- **record.md content.** The verdict line is counted from the body and says who graded the explanations and that no
  one outside reviewed it; "N of M missions passed" counts only missions whose every standard check passed. Times are
  UTC throughout. "Ask the holder" builds its questions from the entry and now escapes what it quotes (C3).
- **The re-check panel** runs the after-fix phase, which the backend still gates on the gap note; the first result
  stays on the record.
- **Warnings on missions 2, 7 and 9** match what the plants do: the connector reaches one folder inside the practice
  profile (2 and 7, with Hermes's file and terminal tools off in 7), and mission 9's setting lets a terminal command
  run without asking, with the terminal reaching the whole computer. One teaching note, not a security one: mission 2
  has a single possible plant, the extra connector, so its warning names the problem the learner is meant to find.
  That is Damon's call. **Since changed (Nov 8, approved by Damon):** mission 2 draws one of two plants, the
  connector or a pack of skills for other work (`unused_skills`). The connector is in the settings in both, off when
  it isn't the plant, so the warning is true either way and names neither (`tests/test_cost_second_problem.py`).
- **B2** (the backend can't tell `confirm: true` from a click) stays accepted, as before.

## November 8, 2026: the Explain it level can now come from a backend model call

**What changed.** Before, a level reached `f_checks` one way: the learner's own Hermes, in a chat, called the agent tool
`field_academy_grade_explanation`. 0.9 premium adds **Score my answer** (`POST /ai/grade/{mission_id}/{step_id}`,
`grading.py`). The page sends only the answer. The backend keeps it as an `explain_answer` entry, builds the grading
text from `rubric_prompt` (minus the paragraph telling a chat agent to call the tool), and asks the learner's model on
Field Academy's own `field_academy_grader` task through `ctx.llm.complete_structured`. The level comes from that reply
and is recorded through the same `foundations.grade_rubric`, source `hermes_grader`, with `"via": "inline"` in
`facts_json`.

**Why the page still can't grade itself.**
- The route reads only `answer` from the body. A level, quote or `passed` the page sends is ignored
  (`tests/test_ai_grading.py`, `GradeRoute.test_the_route_takes_only_the_answer`).
- The reply is checked by code before use: a whole number from 1 to 4 (schema checked in `ai.check_schema` even when
  Hermes has no `jsonschema`), non-empty text fields, one repair try, then a plain failure that records nothing.
- The quote is kept only when it appears word for word in the answer.
- One answer, one level: an answer whose hash already has a level is refused before any call, a lock per attempt stops
  a double press, and `grade_rubric` still refuses a second level per answer.
- The answer reaches the model fenced by `learning.untrusted_answer` and scrubbed (`ai.clean`: `scrub.scrub` plus a
  bare `name:password@` pass) inside the helper, not at call sites.
- No AI module writes `f_checks` or `f_evidence` itself (`tests/test_ai_boundaries.py`); `grade_rubric` takes a `via`
  of `chat` or `inline` and refuses anything else.

**Accepted.** A learner who controls their own model can still steer their own level, as they always could through
their own chat. The record says who graded ("your Hermes graded it") and does not claim more. Two route tests that
asserted "no route contains grade" (`test_foundations_api.py`, `test_security_085.py`) now assert that this is the only
one. Unverified until the QA lane runs S1: that the call works from the page routes inside a real Hermes, and that no
chat appears in Sessions.

## November 9, 2026: two `ai.py` fixes from the security queue, and the new read-only replay

**Fail-open task fallback, fixed.** `ai.call` used to retry on the main model, with no task, whenever a
`PluginLlmTrustError` message contained "task". That also matched Hermes's refusal to route through a built-in task
without `allow_task_override`. It now falls back only on Hermes's explicit "a plugin may only pass a task key it
registered itself" refusal (`agent/plugin_llm.py` `_check_task`) or a `TypeError` for an unexpected `task` keyword (an
older Hermes). Every other trust refusal (built-in task, provider or model override, an allowlist miss) returns the
NOT_ALLOWED words with one call made (`tests/test_ai_helper.py`, `test_every_other_trust_refusal_is_not_allowed_...`).

**Redaction gap, fixed.** The bare `name:password@host` pass missed passwords holding `:` `/` `@` or quotes. `ai.clean`
now works token by token: in any whitespace-delimited token shaped `user:password@host` (a scheme in front allowed),
everything between the first `:` after the user and the LAST `@` followed by a host is removed, before and after
`scrub.scrub`. One test per character. Times, labels and plain email addresses pass unchanged; a label glued to an
address with no space (`to:bob@example.com`) loses its name part, the safe side.

**Replay your run (`recorder.py`) reads, never writes.** It reads the practice profile's `state.db` through
`hermes_read` (read-only connection) and the attempt's own frozen `f_evidence` and `f_checks` rows. Every text is
scrubbed and clipped. Before Compare `GET /replay/{id}` returns no events at all, so neither the files lane nor the
memory row's staged line can give the snag away; the nudge's own input stays the chat lane with tool rows by title and
time only. A `messages` table missing an expected column is reported as `schema_changed`, never a crash.
