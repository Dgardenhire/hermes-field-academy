# Curriculum voice guide

Every word a learner reads in Field Academy is held to the register of the two
people the missions route to.

Sources for the register, both read directly:

- **Tonbi**, Hermes Agent Masterclass and Desktop App Masterclass (videos).
- **Tony Simons**, *The Whole Damn Thing* and the Hermes Agent Manual at
  `launch.tonysimons.dev`, which is written documentation rather than speech and
  is the closer model for lesson prose.

## What the sources sound like

These are summaries in our words, not quotes.

Tonbi narrates a screen while he works. In one episode he asks his agent to
research recent papers, then points to each skill the agent picks up on its own
and says what each one does. He warns that an agent can make skills without you
noticing unless you watch the tool calls, and he gives the reason the skills
help: the research goes faster and avoids common mistakes. (Tonbi, Hermes Agent
Masterclass.)

Tony Simons writes reference prose. He defines a skill as one instruction file
with a name, a description and a step-by-step procedure, gives a few real tasks
as examples in brackets, and names the folder where skills live. He explains
that Hermes reads only each skill's short description until a task needs the
rest. He says where provider keys belong (the profile's `.env` file under
`~/.hermes/`, never in scripts or repositories), and where job settings and run
history are kept (`jobs.json` and `cron/executions.db`). (Tony Simons, Hermes
Agent Manual.)

(The jobs file is `~/.hermes/cron/jobs.json` in the Hermes source, October 2026.)

## The rules that follow

1. **Name the concrete thing.** A skill name, a file path, a command, a UI
   surface, a repo. Both sources put a real artifact in nearly every paragraph.
   Tony names `~/.hermes/skills/`, `~/.hermes/cron/jobs.json`, `hermes doctor`,
   `hermes model`. Tonbi names the skills, the dashboard and the GitHub issues he
   is using.
2. **You, present tense, active verb.** "Open Scheduled jobs and check that the
   job is on." Not "the operator should verify."
3. **Give the reason in the same sentence, plainly.** Use *because*, *so*, *which
   is why*. "Watch the tool calls, because Hermes can save a skill without telling
   you." A fact with no reason attached is a slogan.
4. **Concrete examples in parentheses**, the way Tony does: "(open a pull
   request, read a calendar, send a summary)".
5. **Warnings state the observable symptom, not a principle.** "It will look fine
   for a week and then quietly deliver nothing" beats "silent failure is
   dangerous." Tonbi does this when he says where you would spot the problem: in
   the tool calls.
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

Tonbi's videos and Tony Simons's writing are their own work. This guide describes
their style in our words and doesn't reproduce it. Missions link the source video
or article; they never quote it at length.
