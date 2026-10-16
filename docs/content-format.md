# Content format

Everything a learner reads that is not structure lives in `content/`, one file per
path: `track_operator.py`, `track_integrator.py`, `track_architect.py`,
`track_ambassador.py`. Each exports three names.

- `MISSIONS`: a dict from mission id to the mission's content (below).
- `CAPSTONE`: the path's final mission, on the learner's own problem.
- `PLACEMENT`: the path's placement check.

`curriculum.py` merges these into the mission structure. Run
`python3 scripts/check_content.py <path>` after every edit. It checks the
shape, runs each worked example through the same check the learner faces, and
applies the voice rules. Run `python3 scripts/check_voice.py` and
`python3 -m unittest discover -s tests` before you finish.

## The six steps and how support fades

Every mission runs: Read the idea (the lesson, kept in `curriculum.py`), Read a
finished one (`worked`), Finish a half-done one (`complete`), Try it in your own
Hermes (the lab), Explain it (one question, scored by Hermes), Check my work (the
gate). Support fades across them: a full example, then an example with gaps, then
the learner alone. Worked-example research says this order helps a beginner and
wastes time for an expert, which is why the placement check exists.

## A mission's content

```python
"operator.runtime": {
    "minutes": {"lesson": 3, "example": 3, "complete": 4, "lab": 5, "explain": 5, "gate": 2},
    "use": "You said you want Hermes to do this for you: {goal}. <one sentence tying it to this mission>",
    "use_plain": "<the same sentence for a learner who skipped the goal question; no {goal}>",
    "lab": {"body": "...", "prompt": "..."},      # optional: only the fields you change
    "worked": {...},
    "complete": {...},
    "coach": [{"hint": "...", "example": "..."}],  # one per point in the explain question, same order
    "review": [{"id": "r1", ...}, {"id": "r2", ...}, {"id": "r3", ...}],
    "gate": {...},
    "revisions": [{"version": 2, "kind": "check", "summary": "..."}],
}
```

`minutes` are honest working minutes for a first-timer, summed into the mission's
"time this will take". Do not round them down to look friendly.

`use` is shown on the mission as "Why this matters to you". `{goal}` is replaced by
the learner's own answer to "What do you want Hermes to do for you?", in quotes.
Write the sentence so it reads right after a quoted goal.

### worked: a finished example, read

```python
"worked": {
    "intro": "Who the example is about and what they had to do.",
    "parts": [{"label": "Name the symptom", "text": "..."}, ...],   # 3 to 5, labelled by sub-goal
    "document": "...",                                              # artifact gates only
}
```

Label the parts by the sub-goal each one meets (Atkinson and others call this
subgoal labelling). Use a fictional person or business with a real-sounding
name, in a case different from every case in the lesson and the question.

For a gate that reads a document, `document` is the full finished document in
Markdown, and **it must pass the gate's own rules**. The validator runs it.

### complete: a half-finished example, with gaps

```python
"complete": {
    "intro": "...",
    "parts": [
        {"text": "Text the learner reads, in Markdown."},
        {"gap": "owner", "prompt": "The question the gap answers.",
         "answer": "The model answer.", "min_words": 8, "needs": ["name"]},
        {"text": "..."},
    ],
}
```

Two to four gaps. Put the gaps where the learner has to think, not where they copy.
`min_words` and `needs` are checked before the model answer is shown, so the learner
tries before they see the answer. For a document gate, the text with each gap
replaced by its model answer **must pass the gate's rules** and must not repeat the
worked example more than 40 percent.

### coach: help when the explain question is missed

One entry per point in the mission's explain question (`EXPLAIN[...]["covers"]` in
`curriculum.py`), in the same order. `hint` is a nudge that does not give the
answer away. `example` is a worked-example hint in a different case from the
mission's own: a short, concrete sample of an acceptable answer to that point.
After a first miss the learner sees what they missed and one hint. After a second
miss they also see the example (see docs/pedagogy.md on hint ladders).

### review: three questions for spaced review

Exactly three, ids `r1` `r2` `r3`. Each is a short scenario that asks the learner
to use the idea on a case they have not seen, so it tests understanding and not
recall of the lesson's words. Each has two to four points a good answer covers,
and each point carries a `hint` and an `example` like coach entries do. The three
should not reuse a scenario. One question is chosen each time a mission comes up for
review, rotating, so the learner can't memorise one answer.

### gate: the check on real work

Every gate asks for a specific thing the learner made during the mission. There
are two kinds.

**Document gate** (`"verify": "artifact"`). The learner saves a text or Markdown
file and types where it is.

```python
"gate": {
    "title": "Check your scope document",
    "body": "What to write, in two sentences, ending with 'click Check my work'.",
    "verify": "artifact",
    "check": "scope document",
    "live": "",            # optional: "routes", "connections" or "estate" also reads the live app
    "cross": "",           # "criteria" for a capstone (see below)
    "sections": [
        {"heading": "Owner", "min_words": 6, "needs": ["name"],
         "what": "who owns the result, by name",
         "fix": "Name a person, not a team.",
         "hint": "...", "example": "..."},
    ],
    "proof": "What the check proves, one sentence. It appears on the Field Record.",
    "fixes": {"live_failed": {"hint": "...", "example": "..."}},   # only when `live` is set
}
```

`needs` draws from: `number`, `money`, `time`, `name`, `list`, `verdict`,
`decision` (the section must start with yes, later or no). Each is a plain, checkable
property of the text. Pick `needs` that match what a real document has: a price has a
dollar figure, an owner has a name, acceptance has a number. `min_words` sets a floor
per section; 6 to 14 is typical. `fix` is the sentence appended to "this section has
no <need>". Sections appear to the learner as headings in the order you list them,
and the check matches each as a line that starts with the heading.

A document passes only when every section has its minimum, no placeholder text
(`TODO`, `[...]`, `____`), no two identical sections, enough different words, and is
not mostly the worked example or the half-finished one (a five-word-run overlap over 50
percent fails).

**Desktop gate** (`"verify": "desktop"`). The renderer reads the live app. These are
the four checks the renderer implements. You choose the title, body, proof, the
inputs, the marker and the fix text. Do not invent other checks or ids.

| check | where the evidence is | marker | miss ids to write fixes for |
|---|---|---|---|
| `runtime` | the profile and connection the learner typed, compared with what Hermes reports | none | `not_connected`, `no_answer`, `missing_profile`, `profile_mismatch`, `connection_mismatch` |
| `workspace` | a saved session whose record carries the marker; the lab's practice prompt must start with it | `[FA-DESKTOP]` | `no_sessions`, `no_marker` |
| `knowledge` | an installed skill whose name starts with the marker | `academy-` | `no_skills`, `no_marked_skill` |
| `automation` | a scheduled job whose name starts with the marker, that has a schedule, and whose request names where to work, what to read, what a good result is, where to send it and what to do on failure | `academy-` | `no_jobs`, `no_marked_job`, `no_schedule`, `prompt_thin` |

When a lab has to make the marked thing, change the lab's `body` and `prompt` so
the learner makes it with that name. Keep inside facts already in the lesson text
and the explain points. Do not invent Hermes menus, commands or features.

**Capstone gates** use `"cross": "criteria"` with sections including `Criteria`
(three or more numbered criteria, two or more with a number) and `Evidence` (one
numbered line per criterion, each ending met, partly met or not met). The check
compares them.

### revisions

Each mission lists what changed in 0.5.0 in plain words, a sentence or two. A
learner who passed the old version sees this under "What changed since you learned
this". Say what the check asks now, and what it used to ask.

## The capstone

```python
CAPSTONE = {
    "id": "operator.capstone",
    "title": "...", "promise": "...", "outcome": "...",
    "level_meaning": "What the Capstone camp means on this path, one sentence.",
    "sources": ["official_desktop"],            # ids from SOURCES in curriculum.py
    "watch": ["nous.desktop", "t.1"],           # ids from EPISODES in curriculum.py
    "lesson":  {"title": "...", "body": "...", "source": "tony"},
    "lab":     {"title": "...", "body": "...", "prompt": "..."},
    "explain": {"title": "...", "question": "...", "covers": [...], "coach": [...]},
    "worked": {...}, "complete": {...},
    "gate": {... "cross": "criteria", sections include Criteria and Evidence ...},
    "use": "... {goal} ...", "use_plain": "...",
    "minutes": {...}, "review": [...], "revisions": [{"version": 1, "kind": "added", "summary": "..."}],
}
```

The capstone is transfer: the learner applies the path's ideas to **their own
problem**, which they state, and the document is checked against criteria they set.
The explain question must put the learner in a situation unlike any earlier
mission (far transfer, in Barnett and Ceci's terms), and ask which ideas carry over
and which need changing.

## The placement check

```python
PLACEMENT = {
    "title": "Placement check",
    "intro": "Who this is for and what it does. Say plainly that the checks on real work still apply.",
    "minutes": 5,
    "questions": [
        {"id": "p1", "level": "beginner", "question": "...", "options": ["...", "...", "..."],
         "answer": 1, "why": "Why that option is right and what the others miss."},
    ],
}
```

Exactly two questions per level (beginner, intermediate, advanced), six in all. A
level counts as known when both are right. Scenario questions, three or four
options, the right option in different positions, and never visibly longer than
the others. `why` is the feedback: it explains the right answer and what each
tempting wrong answer misses, in plain words.

## Voice

Plain English for a non-technical owner. Second person, present tense, active
verb. No emoji. A heading names the thing and never ends with a period. State what
a thing is. Do not argue by negation ("not X, but Y", "X is not Y", ", not the").
No three short parallel sentences as a flourish. No consultant words (estate,
topology, least-privilege). Name concrete things: a profile name, a setting, a
person. Credit other people's work by name where you teach from it. Kept
vocabulary: profile, gateway, session, skill, toolset, MCP server, cron, kanban,
subagent, memory, approval, runbook, scope, handoff. See docs/curriculum-voice.md.

Limits the validator enforces: part text 70 words, hint 45, example 60, question
60, gate and lab body 45, `use` 50.
