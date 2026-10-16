# Curriculum voice guide

Every word a learner reads in Field Academy is held to the register of the two
people the missions route to. This file exists because an earlier pass wrote the
copy in a rhetorical register nobody teaches in, and it read as machine-written.

Sources for the register, both read directly:

- **Tonbi**, Hermes Agent Masterclass and Desktop App Masterclass. Transcripts of
  seven episodes are mined in `sources/tonbi/` (kept out of the repo; see
  Licensing below).
- **Tony Simons**, *The Whole Damn Thing* and the Hermes Agent Manual at
  `launch.tonysimons.dev`, which is written documentation rather than speech and
  is the closer model for lesson prose.

## What the sources actually sound like

Tonbi, mid-lesson, narrating a screen:

> "So I'm going to show you this skill here with my Hermes agent and I'm going to
> ask it research recent papers about recursive reasoning models. And you can see
> it automatically goes to a couple skills here. Skill one is this archive, which
> I showed you before and then paper summary, which is another skill to read some
> of these and then give me a summary here."

> "Because sometimes you may not, it might just create skills without you really
> realizing unless you're looking closely at all the tool calls."

> "So those skills just help with this kind of research, doing it faster and more
> efficiently, finding the proper information and making sure it doesn't fall
> into any kind of common problems or issues."

Tony Simons, in his manual:

> "A skill is a `SKILL.md` instruction document — a name, a description, and a
> step-by-step procedure — that teaches Hermes how to do a specific task (deploy
> to Kubernetes, open a GitHub PR, search GIFs). Skills live in
> `~/.hermes/skills/`, the primary directory and source of truth."

> "Skills are loaded on demand: Hermes reads every skill's short description for
> free and only loads the full content when a task actually calls for it."

> "Provider API keys are stored in your profile's `.env` file under `~/.hermes/`
> — not hardcoded into scripts or committed to repositories."

> "Job specifications are stored in `~/.hermes/jobs.json`, while durable run
> history, attempt logs, and telemetry are tracked in
> `~/.hermes/cron/executions.db`."

(The jobs file is `~/.hermes/cron/jobs.json` in the Hermes source, October 2026.)

## The rules that follow

1. **Name the concrete thing.** A skill name, a file path, a command, a UI
   surface, a repo. Both sources put a real artifact in nearly every paragraph.
   Tony names `~/.hermes/skills/`, `~/.hermes/cron/jobs.json`, `hermes doctor`,
   `hermes model`. Tonbi names "the archive skill", "paper summary", "the Hermes
   dashboard", "GitHub issues".
2. **You, present tense, active verb.** "You can see it goes to a couple skills."
   "Run the diagnostics to confirm the install is healthy." Not "the operator
   should verify."
3. **Give the reason in the same sentence, plainly.** Use *because*, *so*, *which
   is why*. "Because sometimes you may not realize unless you're looking closely
   at all the tool calls." A fact with no reason attached is a slogan.
4. **Concrete examples in parentheses**, the way Tony does: "(deploy to
   Kubernetes, open a GitHub PR, search GIFs)".
5. **Warnings state the observable symptom, not a principle.** "It will look fine
   for a week and then quietly deliver nothing" beats "silent failure is
   dangerous." Tonbi does this: "you may not realize unless you're looking
   closely at all the tool calls."
6. **Bracketed callouts for asides.** Tony uses `[NOTE]`, `[PRO TIP]`,
   `[SECURITY BOUNDARY]`. Use the same shape when a lesson needs a warning
   separated from the flow.

## Banned, with the reason

| Banned | Why | Seen in the old copy |
|---|---|---|
| The "X is not Y" hinge as a thesis | Neither source argues by negation. It is a rhetorical move, not a teaching one. | "The window is not the machine." "Capability is authority." "Governance is not a policy document." "An approval gate you have never tested is not a control, it is a hope." |
| Three parallel clauses as a flourish | It is a rhythm, not information. Both sources list things when there are really three things, and say so plainly. | "Chat is for thinking. Delegation is for a task. Kanban is for work that outlives the conversation." "Procedures belong in skills. Facts belong in memory." |
| A minted aphorism closing a lesson | Every lesson ended on one. It reads as written-for-effect, and it teaches nothing you can act on. | "that box is the incident you have not had yet" · "you wrote an installation note, not a runbook" · "the sentence you will read out loud in month two" · "Match the shape to the duration." |
| Invented abstractions | Nobody says these. They are consultant words standing in for a plain one. | "the coordination shape" · "the estate" · "the deciding property" · "the units that need drawing" · "acceptance is not a mood" |
| Nominalized deliverables | A deliverable is a thing you made, said the way you would say it. | "The vocabulary to ask 'which one owns this?'" · "A topology decision with a named owner." |
| Meta-commentary about the reader | "Most people get this wrong" is filler. | "Most people answer that question wrong the first time." · "Teams get this wrong by running…" |

## Kept vocabulary

Words that are Hermes' own, or the sources', and should stay: profile, gateway,
session, backend, skill, toolset, MCP server, cron, kanban, subagent, bot,
memory, workspace, provider, model, tool call, approval, runbook, scope,
handoff, artifact.

Words the sources never use and the copy should not invent: estate, topology,
coordination shape, least-privilege rule (say "the smallest permission that still
does the job"), authority boundary (say what the agent may reach), value model
(say what the old workflow cost).

## Licensing

The transcripts in `sources/` are other people's work. They are working notes for
voice mining and content checking. They are deliberately **not** in the plugin
repository and must not be redistributed with it. Missions link the source video
or article; they never quote it at length.
