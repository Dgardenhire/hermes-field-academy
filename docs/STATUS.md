# Field Academy 0.9.0: status

Private. Left out of the public package (`.public-exclude`). Updated November 8, 2026 (mission 2's second planted problem).

## Where it stands

Branch `foundations-0.9`, version 0.9.0. Not pushed, not published, no catalog PR opened. Entered in the Nous
Research Hermes plugin hackathon (due Wednesday, November 11, 5 p.m. EST).

## Done on November 8

1. **Hermes 0.23.0 facts check.** All 62 "as of Hermes" facts match the Hermes source at tag `v0.23.0`
   (`scripts/check_foundations.py --hermes-ref v0.23.0`, new tonight) and at the installed checkout. A separate
   audit of every reader against the 0.23.0 source found and fixed:
   - skill descriptions are cut at the last whole word (0.22.6+), not at 57; lesson, page and checks now match
     Hermes's `clip_skill_description`;
   - a new or changed skill description over 60 is refused (0.22.6+); the lesson said only a new one was;
   - "missed" rows in 0.23.0's run history are not runs;
   - `room:<id>` is a real 0.23.0 delivery place;
   - connector tools are named `mcp__<server>__<tool>`; two mission 7 checks and one planted-problem detector looked
     for `mcp_<server>_` and could never fire (tests had the same wrong form);
   - `.hermes-dist` is skipped in the skill walk, as 0.23.0 does;
   - the command palette entry passed a string where Hermes calls `detail()`;
   - practice-profile calls now use the profile's local route, so a second connection doesn't block them.
   Platform: nothing in 0.9 needs plugin RPC (not in the v0.23.0 release) or `ctx.files` (0.22.6+), so
   `requires_hermes` stays `">=0.22.0"`.
2. **Version 0.9.0** in `plugin.yaml`, the changelog, the manual and the release test. The disclosure for practice
   profiles is in the README, `SECURITY.md`, `docs/privacy.md` and the draft catalog entry.
3. **README and manual** rewritten for 0.9 with new harness screenshots (`docs/shots/foundations-*.png`).
4. **Design pass** (subject-led-design steps 6 to 8) on the rendered mission pages, both themes, red and green
   accents, wide and narrow. Fixed: text under 12px (kit sizes, code, small caps), stepper titles colliding under
   about 900px, "Step N" labels repeating the stepper, a "Checked by" line repeated on every result card, mission
   list in file-name order instead of 1 to 11 (now numbered, since lessons say "mission 2"). Recorded in the design
   ledger; Damon's verdict pending.
5. **First screen:** the Foundations card sits right under the banner, in three parts with real file names: the
   planted problem, the check that reads Hermes, the record anyone can check.
6. `docs/LIVE-TEST.md` and `docs/DEMO-NOTES.md`.
7. **Public package:** `.public-exclude` lists `.github`, the Nous brief (`docs/brief-img`,
   `docs/concept-brief-nous.html`, `docs/make_brief.py`), `docs/catalog`, the demo notes and this page.
   `build.sh` (in `.planning/nous-hermes-plugins/public/`) now honors that list and fails if a listed path survives.

## Done on November 8, after the persona test

The persona test (`.planning/hackathon-2026-11/personas/field-academy.md` in claude-test) walked 0.9 as a careful
first-week user, an experienced developer and a hiring manager. Fixed, highest first:

1. **Bug: missions 7 to 11 showed mission 3's try form** and wrote "Guessed ...; Memory line was N tokens" into the
   record (`desktop/src/foundations.js` TryNote). Missions 7 to 10 now declare `lab.try_fields`, checked by
   `foundations_b.clean_try`; mission 11 has no try; a memory-shaped try note is refused outside the memory missions;
   the record entry carries `try_lines` in each mission's own labels. Router `tryFormKind` (loop_b.js); a test per
   mission (`tests/test_try_forms.py`). **Show memory file** only where `lab.memory_view` (missions 3, 4, 5, 8, 11).
2. **One Start here:** the Foundations card; the path card is quieter until a path starts; the banner counts
   Foundations missions; "How the trail works" says Foundations comes first.
3. **Check yourself** answers hidden until the learner writes one (`revealBlocks`, all ten lessons).
4. **Re-check route on the Check step** after a miss: gap note first, then **Check my fix** right there.
5. **Copy:** grading location said one way everywhere (`GRADING_WHERE`, MANUAL); mission 9's terminal warning on the
   Practice and Your turn steps (`practice_note`, also missions 2 and 7); mission 10's copy matches the page's
   commands; Recall and the fresh-profile box adapt when earlier missions weren't done (`recall_from`,
   `fresh_replace`); "practice profile" vs "practice folder"; "Your turn" ends with Save what I did; rubric labelled;
   "1 line"; Compare "Your score" and "You caught it"; mission 7's trap count.
6. **Mission 7 masks credentials on screen** (`screenSafe`): address user:password, secret query values,
   secret-named JSON values, bearer tokens and key shapes. Copy still copies the full text.
7. **Test out** (Kwame): `foundations.start(test_out=True)` marks the attempt in its hash chain; Recall skipped; the
   record needs every check passed first time (explanation included) and says **Tested out**; a miss becomes the
   usual mission and the record says it began as a test-out. `tests/test_test_out.py`.
8. **Field Record for a stranger:** verdict line, excerpt captions (the check it backs, what kind of line, what the
   check found), times on dates (UTC), no excerpt cut mid-word (held saves use their full content), course-written
   claims labelled as the course's, "not graded" instead of "not graded yet", short fingerprints in the text (full
   in record.json), "Ask the holder" questions per entry. README.txt unchanged in what it admits.
   `tests/test_record_reader.py`.

Security fixes all kept (identity checks, scrubbing, B1). Bundle rebuilt from hermes-ui-kit's committed HEAD
(`e3fccf9`) via `git archive` in a scratch folder; `build.mjs --check` passes. New harness renders `pt-*` in
`harness/shoot.py`, looked at in light and dark.

## Done on November 8, after the second review

1. **Mission 2 has two possible planted problems** (approved by Damon in chat, Nov 8). Before, only
   `extra_connector` could be drawn, so the warning shown before the first practice chat named the answer
   (`docs/SECURITY-AUDIT.md`, second review). New: `unused_skills`, twelve skills for another line of work (social
   posts, events or hiring, drawn from the seed), switched on, never opened by the job. The archive connector is in
   the settings in both runs, off when the skills are drawn, so the reworded warning is true either way and names
   neither. Its fix-verifier passes when every skill in the pack is on the global `skills.disabled` list (what the
   Capabilities **Skills** tab writes, per the source; per-platform lists don't count) or deleted. The lesson and Your
   turn add the **Skills** line and **Skills** tab; the try no longer lists **MCP** among the panel lines, since a line
   at zero isn't shown. `cost.decision` accepts a cut that names skills. The Compare step and the record title it.
   Tests: `tests/test_cost_second_problem.py` (19). Live-test item 9 added: the Skills tab switch hasn't been seen in
   a live app. Not added to mission 11's pool. Not yet carried back to the planning source
   (`.planning/field-academy-v3/missions/02-cost.v2.md` in claude-test).

## Tests

- Python: 1,209 tests, OK, 21 skipped (Windows-only access-list tests). Was 1,190 before mission 2's second
  planted problem, 1,148 after the B1 fix, 1,125 before the audit.
- Node: 250 tests, all pass. Was 238 after the B1 fix.
- The public package built by `build.sh` from the mission 2 commit, in a scratch folder: 273 files, no excluded path
  left (the Nous brief, its images and generator, `.github`, the catalog draft, the demo notes, this page), no
  `/Users/` path but one test fixture, no email address. Its suite: 1,209 run, OK, 25 skipped (the four exclude-list
  tests skip there because the list was applied and removed); Node 250, all pass after `harness/make_fixtures.py`.
- `scripts/check_foundations.py`: 11 missions, 0 problems; 62 as-of facts match at `v0.23.0`.
- gitleaks before each commit: no leaks.

## Open, in order

1. **Live test in Damon's Hermes on Tuesday** (`docs/LIVE-TEST.md`). Highest risk: making a practice profile from
   the page, calls to it without switching, and the practice chat's working folder.
2. **Held planted problems** (`agents_md_contradicts`, `agents_md_big`, `shared_agents_md`, `extra_toolsets`) stay
   held until the live test confirms a desktop chat reads `AGENTS.md` from its working folder.
3. **Publish:** rebuild the public package with `build.sh`, push, put the commit in `docs/catalog/field-academy.yaml`
   and `docs/catalog/PR.md`, re-run `hermes plugins validate` at the pinned commit, check every image URL.
4. **Web manual** at linchpin.studio still shows 0.8.5; regenerate it from `docs/MANUAL.md`.
5. **hermes-ui-kit** has an uncommitted fix in `src/register.js` (palette `detail` as a function) from another
   session. This build used the kit's committed HEAD; Field Academy passes a function itself, so it doesn't depend on
   that fix.
6. Ideas from the platform digest, not started: an automation blueprint for spaced review, `ctx.os.notify` when
   reviews are due.
