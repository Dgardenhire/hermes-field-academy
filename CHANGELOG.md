# Changelog

## 0.8.4 (2026-10-16)

Ready for the public catalog: links point where they will live, and examples read right on any computer.

- **School of Hermes has a new home.** Each client lab in the Guide path now opens its own lab at
  linchpin.studio/school-of-hermes (Lab 1 through Lab 8). School of Hermes is credited as a concept by Damon
  Gardenhire.
- **Examples for every computer.** Boxes that ask where you saved a file now show `~/Documents/...` instead of a
  Mac-only folder, and the hints add the Windows form, such as `C:\Users\you\Documents\scope.md`. How Field
  Academy reads the path you type is unchanged.
- **Guide labs work the Windows way on Windows.** On Windows a file's lock is its access list, so the lab
  that asks you to lock the keys file now checks that list, and the help shows the PowerShell line:
  `icacls .env /inheritance:r /grant:r "${env:USERDOMAIN}\${env:USERNAME}:F"`. Windows has no mark that makes a script
  runnable, so there the backup schedule has to name the program that runs the script (`/bin/sh`), the way
  Hermes runs a `.sh` script with bash. The reviewer's secret key is private on Windows too. Linux and macOS
  keep `chmod 600` and `chmod +x`. The checks, the grading and the records are the same on every computer, and
  the whole suite, a real Hermes install and a Guide lab now pass on Windows, Linux and macOS.
- **A manual in the repository.** docs/MANUAL.md and its screenshots come from the web manual, and the README
  opens with the Field Academy card and a link to it.
- **Fresh screenshots.** The home page shots in the README show Field Record wording.
- **Corrections.** SECURITY.md now counts all six tools and links issues to the hermes-field-academy
  repository. The catalog entry points to hermes-field-academy and its manual. Setup commands in the docs say
  `python3`.

## 0.8.3 (2026-10-16)

What you get at the end of a path is now a Field Record: your own learning record, built mission by mission and
written by Field Academy on your computer. Nothing on a screen or in a saved file suggests Nous Research issues,
reviews or endorses it.

- **One name everywhere.** The certificate is now the Field Record, on the map, the path screens, the record
  screens, `/academy`, the agent skill, the manifest and the docs. You create it by typing your name; nobody
  awards it.
- **The self-issued line.** Every Field Record, on screen, in the saved `.md` and in the saved `.json`, carries
  "Self-issued with Field Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research."
- **A maker's mark, not a seal.** The mark on the record has plain rings instead of a saw-tooth stamp edge, and
  reads "Field Academy · self-issued field record". The record says Kept by, Created and Record number in place of
  This certifies that, Issued and Verification number.
- **You choose your reviewer.** The Guide path says the reviewer is someone you choose. The lines calling the
  review a proposal for Nous Research are gone from the page, the record and the docs.
- **Old records still verify.** A record's number is a hash over its stored text, so records made by 0.8.2 and
  earlier keep their original wording and verify as before. New records carry `record_format: 2`. The screen and
  the saved `.md` show the new wording for both; an old record's `.json` stays byte for byte what its number covers.
- **Saved files** go to `field-records/` as `field-academy-<path>-field-record.md` and `.json`. Copies saved
  earlier stay in `certificates/`.
- The manifest tag `certification` is now `progress-tracking`. API routes, the database table and internal names
  are unchanged, so saved progress keeps working.

## 0.8.2 (2026-10-16)

Every page reads cleanly.

- Lessons, labs, hints, worked examples and model answers now show their paragraphs, bullet lists and numbered steps.
  Before, each came out as one paragraph, and examples written as lists showed raw dashes.
- All 17 labs are numbered steps, and every gate ends in three: save it, type where you saved it, click Check my work.
- Lists where the text was really a list: the certificate pass rule, the Deployer proposal's ten sections (numbered,
  since their order matters), how the proposal is checked, what a strong judgment answer does, and the reviewer's
  sign-off steps.
- Worked examples no longer start with "Example:" under a heading that already says so, and a review shows
  "Stronger · Strength: Strong · Next review: now".
- The path openers speak to you, and lines where the page described itself are gone or shorter.

## 0.8.1 (2026-10-15)

An accuracy pass. Hermes moved about 2,100 commits between October 6 and October 14, so every lesson, check and
doc was compared again with the Hermes 0.22.0 source. Seven missions changed their teaching, and a learner who
passed one sees it under "What changed since you learned this".

- **Where your work runs (Traveler).** Settings > Gateways shows the computer, not the profile, so the lab now
  reads the profile from the sidebar (or `default` with one profile). The connection reads Connected in the status
  bar's Gateway item, with Reconnect gateway; nothing in Hermes says "open". On this computer the open app now runs
  scheduled jobs when no gateway is running, so quitting it stops them. Missed runs collapse into one late run.
- **Closing things (Traveler).** The app keeps the text of a message you never sent. The examples now use a
  terminal closed with the x and a file attached to an unsent message, which are still gone.
- **Renamed profiles.** A renamed profile keeps its jobs, so the capstone review looks under the new name.
- **Crossroads.** Test in Gateways says Reachable. A job missed while a laptop is shut goes out late, once. An MCP
  server marked `trust: untrusted` asks before tools that can change things; other connected tools still act
  without asking.
- **Boundary Keeper.** The Agents page is now the live subagent tree, so the map lab opens Profiles, where every
  profile and bot is listed. One gateway serves every profile on a computer. Kanban ships switched off, and its
  cards keep done and review in the description. Hermes prunes ended sessions after 90 days and rotates its logs,
  so the retention examples raise `sessions.retention_days` and keep copies.
- **Messenger.** Hermes Cloud is hosted by Nous; Hermes is MIT licensed and maintained by Nous Research.
- **Checks.** The tool check counts tools inside Hermes's toolsets, and the MCP fact counts servers you added. The
  map check reads the profiles this window can reach (`agents.list` answers background processes, not agents).
- **The practice offer stays out of messaging apps.** Gateway session ids carry no prefix, so the offer now checks
  the platform Hermes passes for the turn.
- **Guide.** The Hermes version is read from Hermes's install stamp first (package metadata said 0.21.5 on a
  0.22.0 install). The restart drill stops whatever runs the jobs. A credential used by a script or terminal
  command also needs its name in `terminal.env_passthrough`.
- **Docs.** `hermes logs desktop` is the app and `gui` the backend; a newly enabled plugin's routes mount on first
  call; a page that fails shows "failed to render" with Retry. Field Academy sits under Tools in the sidebar.
- **Install scanner.** Two lines Hermes's scanner read as caution were reworded with the same meaning, and the
  scanner now returns safe.

## 0.8.0 (2026-10-05)

A redesign after a live walkthrough: the paths take their names from Hermes's old jobs, the course starts with
watching Hermes work, and every mission can open with a story instead of a lecture.

- **Paths renamed after Hermes's jobs, on Mount Olympus.** Messenger (explain Hermes and spot where it fits),
  Traveler (run Hermes on your own computer), Crossroads (connect Hermes to a client's tools), Boundary Keeper (who
  owns what, who approves, how it recovers) and Guide (deploy and run Hermes for a client). Each path page says in
  one line why the name fits. Saved progress keeps working: the paths' ids did not change.
- **Messenger comes first, and starts hands-on.** New mission, Watch Hermes do one real job: you give Hermes one
  small job from your own week and write first-hand notes on what it did and what it got wrong, before you explain
  it to anyone. A new learner's first next step is this mission. 20 missions in all.
- **New banner.** Olympus with a band of cloud on its shoulders, one flag per path, and the caduceus, the herald's
  staff, at the summit.
- **Story-first missions, all 20.** Every mission now opens with a short story about what happened to a named
  person, then a three-line takeaway. Find where Hermes is running adds a labelled picture of the four parts of
  Hermes. Steps carry plain names: the
  story, the takeaway, your turn, try it, explain it, prove it.
- **Reading and video links moved to the end** of each mission, closed, as Go deeper. Everything needed to pass is
  on the page.
- **No more copy and paste.** Practice prompts and scoring requests open a new chat and send themselves. The
  clipboard is used only on a Hermes too old to allow it. Scoring never lands in the middle of your own work.
- **Less to read before step one.** The time breakdown and the "how much help you get" panel are gone from the top
  of each mission.
- **Fixes.** The home page counts five paths everywhere. A learner with nothing passed no longer sees "What changed
  since you learned this". The Guide path's certificate is described as a proposal for Nous Research to consider,
  with no reviewers appointed.

## 0.7.0 (2026-10-05)

Ready for an outside reviewer: an end-to-end audit of every path, every check against Hermes's own source, every
lesson against the Hermes docs, and every screen in light, dark and narrow widths. Learners who passed a mission
whose lesson or check changed see it under "What changed since you learned this".

**Fixed: checks that could not pass on a real Hermes**

- **Make Hermes remember how you work.** The skill check read a list, and Hermes sends skills grouped by category,
  so it always reported "no skills". Hermes also caches that list once per process. The check now reads skills fresh
  through the command catalog and flattens the grouped list as a fallback.
- **Put one job on a schedule.** Paused jobs are left out of Hermes's list unless asked for, and the lesson says a
  paused job is fine, so a learner who followed it failed. The check now asks for paused jobs. Hermes lists only the
  first 100 characters of a job's request, so the five points could never be read: the learner now pastes the whole
  request, and it must begin the way Hermes shows that job. A schedule of "?" no longer counts as a schedule.
- **Remote and Hermes Cloud learners** could not hand in any document, because a typed path is read on the computer
  where Hermes runs. Every document check now takes a pasted document as well, saved in Field Academy's own folder
  and checked the same way.

**Fixed: flow**

- Answering an explain question again after passing reset the step and could un-pass the mission and drop a
  certificate's count. A pass now stays; practice happens in the review queue.
- When Hermes was busy, a submitted answer was saved but its scoring request was lost. It is now copied, and a
  waiting answer has a **Send for scoring again** button.
- Removed the three web routes that wrote scores (`/grade/...`, `/review/.../grade`, `/deployer/grade`). Nothing in
  the page used them, and they let a score be posted without Hermes. Scores arrive only through the agent tools.
- Deployer: checking an untouched lab folder, or a deployment that only needs more days, no longer climbs the hint
  ladder to the worked example. The reviewer step says plainly that the published reviewer list is empty and lets a
  learner add a reviewer's key to their own list (`POST /deployer/review/trust`), labelled on the certificate.
- "Due now" in the review queue now uses the same clock as the count above it. "Next review in about N days" rounds
  instead of truncating. Missions added before you started a path no longer show as "New".
- "Where you are" says "At the trailhead" until you start.
- `catalog-entry.yaml` had a misindented tool line that a strict YAML parser rejects.

**Fixed: content checked against the Hermes docs**

- The hosted option is **Hermes Cloud**, not "Nous Cloud", in every lesson, hint and choice list.
- The approval test taught that Hermes shows an approval request when a connected tool acts. It asks only before a
  risky command. The mission now tests Hermes's own approval prompt on a scratch folder and gives sending tools
  draft-only access so a person presses send.
- Hiding a terminal or browser pane keeps it running; closing its tab stops it. The lesson had them the same.
- A stopped gateway runs each missed job once, late, when it starts again (catch-up runs). Hints and the restart
  drill now say so.
- A skill also opens when you type its name. Memory has a size cap, so the "sixty lines" review question changed.
- Lessons for Turn a vague request, Write the handover guide, Decide who can do what and Plan the recovery now name
  every section their check reads.
- The rules examples no longer cite an "action log" Hermes does not have; they point to session history and logs.
- The Teams docs page is no longer cited for connecting tools or for governance.

**Added**

- A home banner: an engraved mountain range at dusk, inline SVG drawn only from the theme's colours, with a camp
  flag for each path that fills when its certificate is issued.
- `docs/paths.md`: each path's use case, the pain it solves, why it has its shape, and what every check reads.
- `REVIEWER-GUIDE.md`, a ten-minute tour and the open questions. README: screenshots, plain install steps, what is
  verified and what is not, privacy.
- Credits for the Nous Learning Path level names and for Orgo.
- Tests for every fix above (`tests/test_audit_070.py`, `tests/test_audit_070_deployer.py`, `tests/test_release.py`,
  `tests/release.test.mjs`).

## 0.6.0

The Deployer path: a fifth trail that certifies someone competent to set up, deploy and manage Hermes for small
clients, assessed by doing the work (docs/deployer-pedagogy.md).

**Added**

- **Lab builder** (`labs.py`). Four disposable "client machines", each a plain folder of fake files that imitates
  a Hermes home (settings, a `.env` with clearly marked fake keys, scheduled jobs, logs, a profile folder, a
  service file, a backup script, a pretend provider console) with one hidden fault. Built from a seed: the same
  seed builds the same folder byte for byte, a different seed changes the names, keys, numbers and which variant
  of the fault is hidden. Built only under the plugin's own data folder, refused if that folder looks like a Hermes
  home, and reset only when a marker file is present. The page has an Open the folder button.
- **Four fault-injection labs with scripted graders** (`grade.py`): a key leaked into a saved settings file
  (move it to `.env`, rotate it, record the leak); a job running every minute on an expensive model (find it in the
  logs, fix the schedule, add a cost cap that pauses jobs); a service that does not survive a reboot, with open
  file permissions and a backup that never ran; and one key shared by two helpers (a key each, the smallest scopes,
  a rotation note). Each has symptoms, log evidence, hidden criteria, and the 0.5.0 hint ladder, with a finished
  worked example on a different business after the second miss. Wrong fixes fail: the original folder, deleting
  the broken thing, rotating without revoking, a cap that only warns, a fix copied from another seed.
- **A client proposal** (`brief.py`): a fictional three-person accounting firm, a vague brief with a budget,
  constraints and one request that must be refused, varying by seed. Deterministic checks (a named owner, price
  and monthly cost against the budget, the build against the weeks asked for, an access list with no blanket
  permission, a refusal that names what it refuses and offers an alternative, a test before go-live) plus a
  six-point rubric the learner's own Hermes scores, through the new `field_academy_grade_deployer` tool.
- **Nine judgment scenarios** (`scenarios.py`), scored on reasoning against a hidden rubric. The ninth is about
  connecting a community tool server.
- **A real deployment and failure drills** (`evidence.py`). Run history is read from Hermes, read only: the
  scheduler list and chat list from the page, a run-history database and log files from the backend. Only
  timestamps and failure marks are kept. A deployment needs at least five runs on three days across 48 hours; a
  drill needs a gap and a recovered run. Where Hermes cannot be read the screen says so, and the part falls back
  to a log excerpt in the review packet that only the reviewer's acceptance can pass.
- **Expert review** (`walkthrough.py`, `ed25519.py`, `scripts/sign_review.py`). A review packet (all evidence,
  fingerprints, the learner's walkthrough, a rubric file) and a sign-off the plugin verifies by Ed25519 signature
  over the packet's fingerprint, against a published list of reviewer keys (`reviewers/trusted-reviewers.json`,
  shipped empty) or the learner's own local list, which the certificate labels. Without it: "Deployer, awaiting
  review".
- **The Deployer certificate**, recording the Hermes version it was earned on, the reviewer and key, the lab
  seeds and folder fingerprints, and what it does and does not certify. **Re-verify needed** shows when the
  Hermes version moves to a new series; re-verify repeats the four labs on new seeds and is recorded beside the
  certificate, never rewriting it.
- **Screens** in the expedition look: a fifth trail on the map, a path with four camps and a summit, and a screen
  for each part (`desktop/src/deployer.js`, `desktop/src/deploy.js`).
- Routes under `/deployer`; tables `deployer_labs`, `deployer_items`, `deployer_answers`, `deployer_attempts`,
  `deployer_samples`, `deployer_renewals`; docs/deployer-pedagogy.md, docs/reviewing.md.

**Changed**

- Database schema version 6. A 0.5.0 database is copied to `backups` first, and only tables are added.
- The four learning paths, their certificates and the passport are unchanged.
- `/academy` adds one line on the Deployer path.

**Not done**

- Nothing was tested against a live Hermes. The layout of Hermes's run history and logs is read generously.
- The published reviewer list is empty. Until a reviewer is added, only the learner's own list can sign.
- Hermes's release numbering is not verified, so "Re-verify needed" treats a new 0.x minor as a new series.

## 0.5.0 (unreleased)

Built on learning research (docs/pedagogy.md). Every mission now fades its support,
every check needs something you made, a miss gets real feedback, passed missions
come back for review, and each path ends on your own problem.

**Added**

- **Spaced review.** Two days after a mission passes it joins the Review queue on
  the home screen. A session is three questions from three different missions,
  scored by your own Hermes through the new `field_academy_grade_review` tool, the
  same way an explain-it answer is scored. Answers of 85 or more move a mission up
  (7, 21, 60, then 90 days), 70 to 84 repeat the gap, and a miss drops two rungs and
  returns tomorrow. Each mission keeps a strength and shows it as a word on the map.
  Practice early changes strength and never the schedule. Questions rotate through
  three per mission. No streaks, no daily goals. Tables `reviews`, `review_sessions`.
- **Stronger checks.** All 15 checks replaced. Live checks compare a typed answer
  with what Hermes reports or look for a skill, job or chat that carries a marker
  (`academy-`, `[FA-DESKTOP]`). Document checks read inside each section: minimum
  words, and a name, number, price, time or list where a section asks for one, with
  placeholder text, repeated sections, a copy of the example, and a file that
  already passed another mission all failing. Three document gates also read the
  live app. The audit, and the checks that still cannot be made strong, are in
  docs/checks.md.
- **Real feedback on a miss.** A miss says exactly what was missing, gives one
  hint, and on the second miss adds a worked example for the same item. Applies to
  document checks, live checks, explain-it answers (Hermes now reports which points
  were left out) and reviews. The last feedback survives a restart.
- **Worked examples and fading.** Every mission gains See one done (a finished
  example with labelled steps) and Finish one (a half-done example whose gaps you
  write before the model answer shows). A support bar shows the help fading: full
  example, half done, on your own. Each worked document passes the check the
  learner faces; a test enforces it. New step kinds `example` and `complete`.
- **Placement check.** Six scenario questions per path. Both right on a level
  skips that level's reading and practice, never its question or its check, and the
  certificate says so.
- **Capstone.** A fourth camp on every path: your own problem, criteria you write
  first, evidence for each, checked against each other. The explain question is a
  far-transfer case. Four new missions, so 19 in all.
- **What changed since you learned this.** A versioned changelog in the curriculum
  (`REVISIONS`). Missions whose lesson or check changed after you passed them are
  listed in plain words with a Re-verify button. A missed re-verify leaves the
  mission passed. The certificate records the check version of each mission.
- **Your goal.** A first-run question, "What do you want Hermes to do for you?",
  woven into every mission's "Why this matters to you", every practice prompt, and
  shown on the map. Skippable and changeable.
- **Honest time.** Every mission and step states its minutes. Estimates rose
  because they now include the example, the gaps and the question.
- `docs/pedagogy.md`, `docs/checks.md`, `docs/content-format.md`,
  `scripts/check_content.py`; routes for all of the above.

**Changed**

- Missions have six steps, not four, and paths have four camps. Totals read
  "19 missions".
- The certificate table has a Check column (version, and a note when reading was
  skipped by placement).
- `/academy` mentions how many reviews are due.

**Migration**

- The first open from an older database copies it whole to `backups/`, then only
  adds tables and columns (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ADD COLUMN`).
  Missions passed under 0.4.0 stay passed, are recorded at version 1 and show under
  What changed with a Re-verify offer, and enter the review queue three a day. An
  issued certificate stays valid.

## 0.4.0

The page opens on a map of paths, each path is a ladder of levels, and each path
ends with a certificate. Every word a learner reads was rewritten in plain English.

**Added**

- **Expedition look.** Each path is a trail on a topographic map drawn in inline SVG
  from the theme's own colours: missions are waypoints grouped into Beginner,
  Intermediate and Advanced camps, the certificate is a summit flag, and a bright
  marker shows where you stand. The map opens with "Where you are" (a bezel with one
  tick per mission) and a "Next best step" card; there are no streaks or timers.
  The path screen adds an elevation profile and numbered camps; a mission reads as a
  field note with a Read, Try it, Explain it, Check my work strip and a compass that
  points at your step; the certificate is a framed, engraved document with an SVG
  seal, its verification number and the line that Field Academy issues it. One
  accent, mixed with `color-mix` from theme variables, works in light and dark. A
  newly walked stretch of trail draws itself once and the marker eases forward,
  both off under reduced motion. Geometry lives in `desktop/src/trail.js` (pure,
  node-tested against every passport state); visuals in `desktop/src/field.js`.
- The plugin now starts enabled (`defaultEnabled: true`), like Factory.

- **Path map.** The sidebar opens on the four paths, each with a three-part level
  bar, where you are, how many missions passed, and how far the certificate is. A
  Start here / Up next card picks the next mission.
- **Level ladder.** Every mission sits on Beginner, Intermediate or Advanced (Nous's
  own level names). Each path says what each level means; the path screen marks
  You are here.
- **Certificate route and certificate.** Each path shows what to do, the proof each
  mission needs, and what you receive. Once every mission passes, you claim the
  certificate with your name. It carries pass dates, check results, question
  scores, and each document's file name and SHA-256, never answers or full paths.
  Its number is a hash of its contents (`verify_certificate`). Save as a file writes
  `.md` and `.json`. Routes: `GET/POST /certificate/{path}`, `POST /certificate/{path}/save`.
- **Credited links.** Reading lists start with the Nous docs, route Tonbi's
  masterclass through Hermes Atlas (`#episode-N`), and add Kevin Simback's Atlas
  guides and iamlukethedev's Hermes Bible. Every link carries a credit line.
- **Harness.** `harness/` renders every screen in headless Chrome without Hermes,
  from passports the real backend produced.
- `/academy` prints the map: each path's progress, level and certificate status.

**Changed**

- Mission titles name the thing ("Find where Hermes is running", "Spot a real
  opportunity"). Lessons lost the negation hinges and the lines about the product
  itself. Step labels are Read, Try it, Explain it, Check my work. No all-caps
  labels, no "This gate closes only by passing", no "You walk away with".
- Every word uses `--ui-text-primary`; the undefined `--ui-warning` is gone. All
  styles ship inline as `fa-` classes.

**Fixed**

- `field_academy_mission` raised `KeyError: 'track'` on every call, because the
  passport's missions don't carry their track.
- The in-chat offer called a hook after an early return.
- `scripts/check_voice.py` and `scripts/check_plugin_css.py` failed to start on
  Python 3.9.

## 0.3.1 (unreleased)

Hardening for catalog admission, a rewrite of the learner-facing copy, and a fix to
what the pane receives.

**Fixed**

- `claim_spotlight` advanced its watermark past rows it had not offered. A scan
  that found no mission for the learner's current level consumed the
  opportunities anyway, so switching level later surfaced nothing. The watermark
  now moves only when something was actually offered.
- The artifact gate read a named file with no bound: no size cap and
  `errors="replace"` on the decode, so a binary file could satisfy a heading
  check by accident and a large file could be read into the gateway process. The
  read is now capped at 5 MiB and must decode as UTF-8.
- The gate's size line reported characters as "words".
- Three arbitrary-value utility classes had no compiled rule in the shipped
  desktop stylesheet (`grid-cols-[7.5rem_1fr]`, `tracking-[0.1em]`,
  `tracking-[-0.02em]`). The step-detail grid was collapsing to one column and
  two letter-spacing values were silently dropped. They now ship with the plugin
  in its own stylesheet.
- `variant: 'primary'` was passed to `Button`, which has no such variant, so the
  lesson step's primary action rendered unstyled.
- The gate and explain actions swapped their label to "Checking…" / "Sending…"
  while working, reflowing the row. They use the Button's own `loading` state.
- The loading state was the literal string "Loading Field Academy…".

**Changed**

- **Breaking.** Public names are no longer inherited from the retired
  `hermes-growth-guide` plugin:
  - transcript directive `hermes-growth` → `field-academy-practice`
  - toolset `hermes_growth` → `field_academy`
  - tools `growth_*` → `field_academy_*`
- `defaultEnabled` is now `false`. The plugin adds a status-bar chip, a sidebar
  row, a transcript directive, and a `pre_llm_call` hook that writes into the
  user message, so it ships opt-in.
- The error, empty, and loading states use the app's `ErrorState`, `EmptyState`,
  and `Loader` instead of hand-rolled markup.
- Progress bars, level buttons, and the mission list carry accessible names and
  state (`role="progressbar"`, `aria-pressed`, `aria-current`).
- Directive attributes are validated against a bounded id pattern before use.

**Fixed (the pane received less than it read)**

- `state.snapshot()` did not carry per-step `status` or `explanation`, while the
  desktop half branches on both. No step ever rendered as done, a passed gate kept
  offering "Run the check", and a graded explanation never showed its score. The
  passport now carries them, and a test asserts the passport and the mission view
  agree.

**Changed (the copy)**

- Every learner-facing string was rewritten into the register of the people the
  missions route to. The old copy argued by negation ("The window is not the
  machine"), closed lessons on minted aphorisms ("that box is the incident you have
  not had one"), used three parallel clauses as a flourish, and invented
  abstractions nobody says ("the coordination shape", "the estate", "a topology
  decision"). The rules, with quotes from both sources, are in
  `docs/curriculum-voice.md`.
- New `scripts/check_voice.py` reports the patterns per mission and field. It runs
  clean.

**Added**

- `scripts/check_plugin_css.py` — fails when the pane uses a Tailwind class the
  app never compiled. Self-tests before it accuses anyone.
- `.github/workflows/ci.yml` — unit tests, ESM parse, identifier preflight, CSS
  guard, and the Nous `plugin-validate` composite action.
- Tests: both halves must agree on the directive name; the catalog entry must
  agree with `plugin.yaml`; artifact gates must refuse an empty, binary, or
  oversize file while still accepting a real document; an unmatched spotlight
  scan must consume nothing.
- `SECURITY.md`, `docs/privacy.md`, `docs/troubleshooting.md`, `docs/curriculum-voice.md`.
- `scripts/check_voice.py` (voice gate), `scripts/rewrite_voice.py` (the rewrite, re-runnable and idempotent).

## 0.3.0

Verified gates. Fifteen missions across four levels, each a lesson, a lab, and a
gate that closes only by passing a real check. Desktop gates read live gateway
state; artifact gates read a named file, require its sections, and record its
SHA-256. Explanation steps are graded against a server-built rubric and can only
be closed by the agent's write-back. Hooks gated on session prefix and on argv.

## 0.2.0

First desktop half: level ladder, mission list, status chip.

## 0.1.0

Agent half: mission state, evidence, the coach skill.
