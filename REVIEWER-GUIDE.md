# Reviewer guide

A tour for someone judging whether Field Academy is ready to recommend to the Hermes community. It takes about
10 minutes. Thank you for looking.

## What it is, in one paragraph

A free Hermes Desktop plugin, the School of Hermes, that teaches Hermes by having you do real work. A new learner
starts with **Start here**: one short practice in a test copy of Hermes, then the eleven **Foundations** missions
beside it. Each Foundations mission runs in a practice profile Field Academy makes (`academy-practice`), plants one
problem in it before the first chat, and checks the work by reading that profile's own files (memory, settings, chat
records, scheduled jobs, run history, logs). After Foundations, five trails climb a trail map of Mount Olympus:
Messenger (explain Hermes), Traveler (run it for yourself), Crossroads (connect a client's tools), Boundary Keeper
(who owns what, who approves, how it recovers), each with five missions over Beginner, Intermediate, Advanced and a
Capstone on your own problem, and Guide, nine parts for people who will deploy and run Hermes for a client. Five
practice and Teach missions sit in the trails' camps as extras. Every check reads something you made. A trail ends in
a Field Record, self-issued on the learner's own computer, not issued or endorsed by Nous Research. It is a community
project: Nous Research didn't make it and hasn't reviewed it.

## The 10-minute tour

Without installing anything, from the repository folder:

```bash
python3 harness/make_fixtures.py     # drives the real backend into each state, in a throwaway folder
python3 harness/shoot.py --list       # every screen
python3 harness/shoot.py map-fresh school-home school-crossroads school-guide
python3 harness/shoot.py f-lab f-check f-compare f-record
python3 harness/shoot.py mission mission-miss dp-lab-open certificate
```

PNGs land in `harness/shots/`. The harness stands in for the plugin SDK and needs network for its CDN imports. It
runs no `hermes` command and never touches `~/.hermes`.

1. **Home (1 minute).** `map-fresh` is what a stranger sees first: the Olympus banner, the trail map, and Start here
   with Foundations right below it. `school-home` is the same page mid-way, with one "You are here" on the trail the
   learner is working toward. At the foot of the page, **Settings** has the two switches: AI help, and the one-sentence
   practice offer Field Academy may add to the learner's own chats (off by default).
2. **A Foundations mission (3 minutes).** `f-lab` is the practice step, `f-check` the checks reading the practice
   profile, `f-compare` the chat and the files on one timeline, and `f-record` the entry that goes into the Field Record.
3. **A trail (2 minutes).** `school-crossroads`: four camps, five trail missions and one practice mission marked as
   extra; every count on the page says "of 5". `mission-miss` is a missed check: what was missing, one hint, then a
   worked example. [docs/paths.md](docs/paths.md) has a table per trail of what each check reads.
4. **The Guide trail (2 minutes).** `school-guide`, `dp-lab-open`: a disposable fake client folder with one hidden fault,
   graded on the repaired files.
5. **The Field Record (1 minute).** `certificate` and `f-record`: the proof behind each mission and the self-issued line.

To try it for real: [README.md](README.md#install) has the install steps, and [Uninstall](README.md#uninstall) the way
back out. Everything it stores is in its own data folder.

## Security, in one paragraph

Hermes copies the user's provider sign-in into every new profile, practice profiles included. Field Academy never
reads it, never writes an approval setting, and never aims a planted connector where the sign-in is: the "wide
connector" problem (mission 13 and the Teach mission) reaches `settings-copy/`, a made-up stand-in for the profile's
folder, and `practice_write.check_connector_reach` refuses any connector that would reach the real one. Read
`tests/test_no_credential_reach.py` and `docs/privacy.md`.

## What was checked before you got this

- Every lesson was compared with the Hermes docs in October 2026. Seven factual errors were fixed in 0.7.0
  (CHANGELOG.md lists them). After Hermes 0.22.0 changed the desktop layout and how scheduled jobs run, every
  lesson and check was compared again with the Hermes source on October 15, 2026, and 0.8.1 fixes what had
  drifted. Claims that could not be confirmed are listed in the README.
- Every check that reads Hermes was compared with Hermes's own source for the response shape it reads. Two would
  never have passed on a real install (the skill check and a paused scheduled job); both are fixed and tested.
- All tests pass: `cd tests && python3 -m unittest discover -s . -p 'test_*.py'`, and `node --test tests/*.test.mjs`
  after `python3 harness/make_fixtures.py`.

It runs in the author's own Hermes Desktop. Only the author has walked it; nobody else has finished a trail yet. Walked
live on Nov 11, 2026, on Hermes 0.23.1: Foundations mission 3 (Save a fact to memory and check it stuck) end to end,
with AI help on Claude and the practice chat on the OpenAI route, and its Field Record saved and checked with `shasum`.
In the connector mission, the practice chat was refused access outside its folder.

## Open questions we would value your view on

1. **The Guide trail's reviewer.** The learner chooses their reviewer and adds that person's key to their own list;
   the published reviewer list ships empty, and nobody has been named or recruited. Is a reviewer the learner
   chooses the right bar, or should the path end at "Guide, awaiting review" by design and leave the judgment to
   whoever hires the person?
2. **The self-issued wording.** Every Field Record, on screen and in its saved files, says "Self-issued with Field
   Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research." Is that clear enough, or
   should the wording change further?
3. **Self-scored questions.** The explain step and the Guide trail's scenarios are scored by the learner's own Hermes
   against a fixed rubric. Acceptable for a practice tool, or a reason to drop those scores from the Field Record?
4. **Credits.** The teaching links go to Tonbi, Kevin Simback's Hermes Atlas, the Hermes Bible and Tony Simons
   (see CREDITS.md). If anyone named would rather not be linked, it changes the same day.

## Where to send feedback

Open an issue on the repository, or reply wherever this reached you.
