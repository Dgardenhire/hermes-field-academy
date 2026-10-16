# The five paths: who each is for, and what it proves

Four learning paths and the Guide path. The paths take their names from Hermes's old jobs on Mount Olympus, and
each path page says in one line why its name fits. They appear in this order, and a new learner starts on
Messenger. Saved progress keeps working because the internal ids did not change; each section gives its id.

Each path below says who it is for, the pain it addresses, why it has the shape it has, and what the plugin
actually checks. "Checks" means code that reads something the learner made. Where a check can only take the
learner's word, or a model's score, it says so.

## Messenger

Internal id `ambassador`. Hermes carried word between the gods and people; this path says what Hermes is,
honestly, to someone who has never used it.

**Use case.** Someone who introduces Hermes to businesses but will not build the setup: a consultant, a
connector, a community member.

**Pain it solves.** Overselling, and explaining a tool you have never watched work. A pitch that skips what Hermes
takes to look after loses the second meeting, and a handoff that mixes "what we know" with "what we promised" hands
the builder a commitment they never made.

**Why this shape.** Watch Hermes do one real job first, so the explanation rests on something the learner saw.
Then explain it in two minutes (limits included), qualify a real opportunity, hand it off cleanly, and finish with
a capstone with one real person. Messenger is listed first, and its first mission is the first next step for a new
learner.

**What it checks.** Document checks, including first-hand notes on the job the learner gave Hermes (The job, with a
time such as how long it takes by hand; What Hermes did, as a list of steps; What went wrong; What I would tell a client), a
named person in the Credit section, and separate Known and Promised lists. Whether the job, or the conversation,
happened as written is the learner's account.

## Traveler

Internal id `operator`. Hermes protected travelers; this path gets Hermes running on your own computer and keeps it
running.

**Use case.** One person running Hermes on their own computer who wants it to do one piece of their own work
every week without being asked.

**Pain it solves.** Hermes has four things that all get called "Hermes" (the app, a session, a profile, the
gateway), and a first scheduled job usually fails silently because the request leans on a chat the job never
sees. People conclude "it doesn't work" when nothing was running the jobs (the app closed and no gateway service
running) or the request was thin.

**Why this shape.** Five missions in the order the confusion bites: where it runs, what survives closing the
window, what goes in memory versus a skill, a job that stands on its own, then a capstone on the learner's own job
with criteria set before it runs.

**What it checks.**

| Mission | The check reads |
|---|---|
| Find where Hermes is running | The profile and connection the learner typed, compared with what this window reports |
| Learn what the app keeps | A saved chat that starts with the `[FA-DESKTOP]` practice message |
| Make Hermes remember how you work | An installed skill whose name starts with `academy-`, read fresh from Hermes. The memory fact is not checked: Hermes has no call that lists memory to a plugin |
| Put one job on a schedule | A job named `academy-...` with a schedule (paused counts) whose request covers four of the five points. Hermes lists only the first 100 characters of a request, so the learner pastes the whole request and it must begin the way Hermes shows it |
| Capstone | A record with six sections, numbered criteria, and an evidence line per criterion ending met, partly met or not met |

## Crossroads

Internal id `integrator`. Hermes was the god of crossroads, where roads meet; this path connects Hermes to a
client's tools.

**Use case.** Someone setting Hermes up for a small client: a contractor, a clinic, a three-person office.

**Pain it solves.** Client work fails at the edges: a vague "AI agent" request with no scope, a laptop that sleeps
at 2am, a tool connected with more access than the job needs, and a handover only the installer understands.

**Why this shape.** Discovery, where it runs, one connection, handover, then a capstone engagement on the
learner's own problem. Each produces a document a real client would keep.

**What it checks.** Every mission ends in a document check: each required section must hold its own real content
(minimum words, plus a number, a name, a time or a price where the section needs one), and copies of the worked
example, repeated sections and reused files fail. "Choose where Hermes runs" and "Connect one client tool" also
read the live app (a connection route; the tool list). The approval test is a record the learner writes about
Hermes's own approval prompt: the plugin cannot see the prompt appear, so that part is the learner's account,
held to times and names.

## Boundary Keeper

Internal id `architect`. Herms, stone pillars, marked where one property ended and the next began; this path
decides who owns what, who approves what, and how it recovers.

**Use case.** Someone planning Hermes for a whole organization: a school office, a firm, a church, an employer.

**Pain it solves.** Shared parts with no owner, documents that can carry hidden instructions to an agent, a
two-week process handed to a helper that ends with the task, and value claims nobody measured.

**Why this shape.** Map and own, govern, match the job to the right kind of agent, plan recovery and measure
value, then a capstone on an organization the learner knows.

**What it checks.** Document checks as above. "Map every part" also reads the profiles this window can reach. The task
card mission reads the learner's file only: Field Academy cannot read the Kanban board, and the screen says so.

## Guide

Internal id `deployer`. Hermes led travelers to where they were going; this path is for deploying and running
Hermes for a client. It ends in the Guide Field Record, which needs the signature of a reviewer the learner
chooses; without it a learner holds "Guide, awaiting review". Like every Field Record it is self-issued, and not
issued or endorsed by Nous Research.

**Use case.** Someone who will set up, deploy and look after Hermes for small clients as paid work.

**Pain it solves.** A quiz cannot tell whether someone can find a leaked key in a client's files, cap a runaway
job, refuse an unsafe request in a proposal, keep a real service running for days, or recover from a revoked
token. Clients pay for exactly those things.

**Why this shape.** It follows a deployment's order (audit, architect, build and integrate, staged
verification), the lifecycle Tony Simons describes. Four break-and-fix labs on disposable fake client folders, a
priced proposal, nine judgment scenarios, a real service run for at least three days, failure drills, then a
walkthrough and a signed review by a reviewer the learner chooses.

**What it checks.**

| Part | The check reads |
|---|---|
| Labs | The repaired files and the write-up, against criteria the learner cannot see, from a seed so a copied fix fails |
| Proposal | Numbers against the budget, a named owner, an access list with no blanket permission, a refusal with an alternative. The prose is scored by the learner's own Hermes |
| Scenarios | Reasoning, scored by the learner's own Hermes against a rubric |
| Real deployment | Hermes's own scheduler list, run history and logs, read only: at least five runs on three days over 48 hours |
| Drills | A gap and a recovered run in Hermes's records, or a pasted excerpt the reviewer checks |
| Review | An Ed25519 signature over the packet's fingerprint from a reviewer key. The published list ships empty, so today a learner adds the reviewer they chose to their own list and the Field Record says so |

## Shared parts

- **Mission steps.** The story, the takeaway, your turn, try it, explain it, prove it. Every mission opens
  story-first: a short story, then a three-line takeaway.
  Reading and video links sit at the end of each mission, closed, under Go deeper, and everything needed to
  pass is on the page.
- **Explain it.** Every mission has one question scored by the learner's own Hermes (70 passes). This is
  self-hosted scoring: the rubric is fixed, the model is the learner's. The scoring request opens a new chat and
  sends itself, as practice prompts do; the clipboard is used only on a Hermes too old to allow that. A pass is
  never taken back by a later answer.
- **Review queue.** Passed missions return after two days, a week, three weeks and two months.
- **Placement.** Six questions per path can skip a level's reading; every question and check still counts.
- **Field Record.** The learner's own learning record for a path, self-issued on their computer. Records each
  check's version, the question scores and each document's fingerprint. Its number
  detects an accidental edit; it is not a signature, so a determined person editing their own data can rebuild it.
