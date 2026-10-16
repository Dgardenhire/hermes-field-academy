# Reviewer guide

A tour for someone judging whether Field Academy is ready to recommend to the Hermes community. It takes about
10 minutes. Thank you for looking.

## What it is, in one paragraph

A free Hermes Desktop plugin that teaches Hermes by having you do real work on your own setup. Four learning
paths, named after Hermes's old jobs on Mount Olympus, climb Beginner, Intermediate and Advanced, the level names
from the Nous Learning Path, then end in a capstone on your own problem: Messenger (explain Hermes and spot where it
fits), Traveler (run Hermes on your own computer), Crossroads (connect Hermes to a client's tools) and Boundary
Keeper (who owns what, who approves, how it recovers). Twenty missions in all, and a new learner starts on
Messenger's hands-on first mission, Watch Hermes do one real job. A fifth path, Guide, is for people who will deploy
and run Hermes for a client. Every mission ends in a check that reads something you made. It is a community
project: Nous Research didn't make it and hasn't reviewed it. What a learner gets at the end of a path is a Field
Record, their own learning record, self-issued with the plugin on their own computer and not issued or endorsed by
Nous Research.

## The 10-minute tour

Without installing anything, from the repository folder:

```bash
python3 harness/make_fixtures.py     # drives the real backend into each state, in a throwaway folder
python3 harness/shoot.py --list       # every screen
python3 harness/shoot.py map mission mission-miss dp-lab-open certificate
```

PNGs land in `harness/shots/`. The harness stands in for the plugin SDK and needs network for its CDN imports. It
runs no `hermes` command and never touches `~/.hermes`.

1. **Home (1 minute).** `map-fresh` is what a stranger sees first: the Olympus banner with one flag per path and
   the caduceus at the summit, one question about what they want Hermes to do, and a Start card that points to
   Watch Hermes do one real job. `map` is the same page mid-way.
2. **One mission (3 minutes).** `mission` shows the six steps: the story, the takeaway, your turn (finish a
   half-done example), try it, explain it, prove it. Reading and video links sit at the end, closed, under Go
   deeper; everything needed to pass is on the page. Practice prompts and scoring requests open a new chat and send
   themselves. `mission-miss` is a missed check: what was missing, one hint, then a worked example.
3. **The checks (3 minutes).** [docs/paths.md](docs/paths.md) has a table per path of what each check reads. The
   strongest are the document checks and the Guide path's labs; the weakest are named there too.
4. **The Guide path (2 minutes).** `dp-path`, `dp-lab-open` and `dp-lab-miss`: a disposable fake client folder
   with one hidden fault, graded on the repaired files.
5. **The Field Record (1 minute).** `certificate` shows a learner's Field Record with the proof behind each
   mission and the self-issued line. It never holds answers, chats or full paths.

To try it for real: [README.md](README.md#install) has the install steps. Everything it stores is in its own data
folder; delete that folder to start over.

## What was checked before you got this

- Every lesson was compared with the Hermes docs in October 2026. Seven factual errors were fixed in 0.7.0
  (CHANGELOG.md lists them). After Hermes 0.22.0 changed the desktop layout and how scheduled jobs run, every
  lesson and check was compared again with the Hermes source on October 15, 2026, and 0.8.1 fixes what had
  drifted. Claims that could not be confirmed are listed in the README.
- Every check that reads Hermes was compared with Hermes's own source for the response shape it reads. Two would
  never have passed on a real install (the skill check and a paused scheduled job); both are fixed and tested.
- All tests pass: `python3 -m unittest discover -s tests` (Python and Node).

It has not run inside a live Hermes Desktop, and no learner outside the author has taken a path.

## Open questions we would value your view on

1. **The Guide path's reviewer.** The learner chooses their reviewer and adds that person's key to their own list;
   the published reviewer list ships empty, and nobody has been named or recruited. Is a reviewer the learner
   chooses the right bar, or should the path end at "Guide, awaiting review" by design and leave the judgment to
   whoever hires the person?
2. **The self-issued wording.** Every Field Record, on screen and in its saved files, says "Self-issued with Field
   Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research." Is that clear enough, or
   should the wording change further?
3. **Self-scored questions.** The explain step and the Guide path's scenarios are scored by the learner's own Hermes
   against a fixed rubric. Acceptable for a practice tool, or a reason to drop those scores from the Field Record?
4. **Credits.** The teaching links go to Tonbi, Kevin Simback's Hermes Atlas, the Hermes Bible and Tony Simons
   (see CREDITS.md). If anyone named would rather not be linked, it changes the same day.

## Where to send feedback

Open an issue on the repository, or reply wherever this reached you.
