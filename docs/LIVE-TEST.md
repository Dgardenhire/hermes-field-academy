# Live test: Foundations in a real Hermes Desktop

The test suite and the harness drive the real backend through a stand-in for the plugin SDK. This list covers what
only a real Hermes Desktop can show. It is in risk order: the first items can block every mission, the last ones
affect one screen. Allow about two hours. Each item says what a pass looks like and what to write down if it fails.

**Before you start.** Hermes Desktop on 0.23.0 (Settings, About). Field Academy 0.9.0 installed from this branch and
desktop plugins reloaded. Note which profile the app is on (the profile pill); it should never change during this
test unless a step says so. Keep **Settings**, **Profiles** open in a second window to watch profiles appear.

## 1. Making and deleting a practice profile from the page

Highest risk: every mission starts here.

1. Field Academy, **Open Foundations**, mission 1, work through to **Practice**, press the button that makes the
   practice profile.
2. Pass: within two minutes the page says the profile is ready, and **Settings**, **Profiles** lists
   `academy-practice`. The profile pill still shows your own profile.
3. Mission 6 (**Keep two jobs apart in two profiles**): the page makes `academy-practice-b` too, after the try.
4. On a mission page, press **Delete practice profiles**, confirm. Pass: both are gone from Profiles; the pill is
   unchanged; the page offers to make them again.

If it fails: the exact message on the page, how long it waited, and whether the profile shows up in Profiles
anyway. A profile that appears after the page gave up is the "reply lost while Hermes finishes making the profile"
case the page is built to recover from: press the button again and note whether it picks the profile up.

## 2. Calls to the practice profile without switching

The page asks Hermes about the practice profile (`session.list`, `cron.manage`, `rollback.list`) on that profile's
own route, without switching the app to it.

1. In mission 1, after a practice chat, press **Check my work**. Pass: the check shows chats from the practice
   profile, and the profile pill never moved.
2. If you have a second connection set up (another computer, or Hermes Cloud), repeat with it connected. Before
   0.9 a bare profile name was refused in that setup ("requires a route descriptor from host.profileRoutes()").
   Pass: the same result as step 1.
3. Open the command palette (Cmd-K). Pass: it opens, and **Field Academy** shows its one-line description. (Before
   0.9 the entry's description could break the palette.)

If it fails: the error text from the page, and whether a second connection was set up.

## 3. The practice chat's working folder

1. Mission 1, **Your turn**: press **Open practice chat**. A new chat opens.
2. Pass: the chat is in `academy-practice` (the chat header or the pill for that chat), your own profile is still
   the app's profile when you return to Field Academy, and the page shows **The practice chat works in the practice
   folder** with a path ending in `profiles/academy-practice`.
3. In that chat, ask: `What folder are you working in? Answer with the full path only.` Pass: the answer is the
   folder the page names, ending in `profiles/academy-practice`.

If it fails: the folder the chat reports, and the folder the page expected. This item also decides the three held
plants that rely on `AGENTS.md` (see item 6).

## 4. Mission 7: the trust gate

1. Mission 7 (**Connect an outside tool safely**). Set the connector up as the mission asks, with `trust: untrusted`.
2. In a new practice chat, ask Hermes to write a file through the connector. Pass: Hermes stops and asks, naming
   the tool and `UNTRUSTED server`. Deny it.
3. Press **Check my work**. Pass: **A write asked, and you turned it down** passes, and so does the check that the
   connector started cleanly after your last settings change.

This is the first live run of these two checks with the connector tool names Hermes really uses
(`mcp__<server>__<tool>`); before 0.9 they could not pass. If they fail: the tool name in the chat's tool row (open
the row), and the check's message.

## 5. Mission 8: scheduled runs fire

Hermes's gateway must be running and the computer awake for at least two hours.

1. Mission 8 (**Set up a job that runs on a schedule**). Let the page make the planted draft job; pass: it appears under
   **Scheduled jobs** in the practice profile, paused.
2. Make your own hourly job as the mission asks, pause it, press **Trigger now**, read the result, then resume it.
3. Leave it for two top-of-the-hour runs. Pass: the page says **Two scheduled runs have landed**, and **Check my
   work** shows the first run as by hand and later runs as fired by the schedule.
4. If the computer slept through a slot, Hermes 0.23.0 books a "missed" row in run history. Pass: the page does
   not count it as a run.

When done: pause or delete the jobs in the practice profile so they stop costing anything.

If it fails: what **Show runs** lists for the job, with times, and the page's message.

## 6. AGENTS.md plants (held)

Three planted problems are held until a desktop practice chat is confirmed to read `AGENTS.md` from its working
folder: `agents_md_contradicts` (mission 4), `agents_md_big` (mission 2) and `shared_agents_md` (mission 6,
Advanced).

1. With item 3 passed, put a file `AGENTS.md` in that folder (`profiles/academy-practice`) with one line:
   `End every reply with the word: lighthouse.`
2. Open a new practice chat and say hello. Open the context panel (Context Usage).
3. Pass: the reply ends with "lighthouse", and the panel lists a **Rules** line. Then the three plants can be
   released in a later build.

Write down: whether the reply followed the line, and the **Rules** line's size in the panel.

## 7. Mission 10: a blocked job costs nothing

1. Mission 10 (**Find out why Hermes failed, and fix it**) plants an active hourly job with a misspelled delivery place.
2. After the next top of the hour, open the practice profile's `logs/errors.log` from the page.
3. Pass: a WARNING line with `BLOCKED by pre-dispatch config validation` for that job, and no model call for it in
   the chat records or usage.

## 8. Mission 5: what Hermes shows of a long description

1. Mission 5 (**Turn a repeat job into a skill**). The page shows each skill's description as Hermes's index shows
   it.
2. In a fresh practice chat, ask: `Quote each skill description exactly as you see it, character for character.`
3. Pass: for `academy-weekly-admin`, Hermes quotes `Use for the weekly admin routine our team runs after...`, the
   same as the page.
4. In the skill's **Edit** box, change its description to a line over 60 characters and save. Pass: Hermes refuses
   it and says how long it is (0.22.6 and later).

## 9. Mission 2: switching skills off in another profile

Mission 2 plants one of two problems. One is a pack of twelve skills for other work (`unused_skills`). Its check
reads the practice profile's `skills.disabled` list, which the source says the **Skills** tab writes. No live app
has shown that yet.

1. Start mission 2 until **Your turn** shows a **Skills** line in the Context Usage panel of a `hello` chat. (Start
   a new try if the other problem was drawn.)
2. Open **Capabilities**, **Skills**, choose `academy-practice` under **Configuring:**, and switch off the skills
   the job never opened.
3. Pass: `profiles/academy-practice/config.yaml` lists them under `skills:` / `disabled:`, your own profile's skills
   are unchanged, and in a new `hello` chat the **Skills** line is gone or much smaller.

If it fails: the `skills:` part of the practice profile's `config.yaml` after the switch, and the panel's lines.

## 10. The Field Record folder

1. After one mission is in the record, open **Open my Field Record**, keep one excerpt out, type a name and the two
   lines, tick the box and press **Save my Field Record**.
2. Press **Open folder**. In a terminal in that folder, run `shasum -a 256 -c MANIFEST.sha256`.
3. Pass: every line ends in `OK`, `record.md` reads cleanly, and the kept-out excerpt has no file in `evidence/`.

## After the test

Delete the practice profiles from the page. Note the Hermes version, the date, and each item's result with the
release notes (the maintainer keeps them in a status page that isn't part of the public package).
