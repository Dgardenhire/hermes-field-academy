# Why the Guide path assesses the way it does

The four learning paths (Messenger, Traveler, Crossroads and Boundary Keeper) ask whether someone understands
Hermes. The Guide path (internal id `deployer`, called the Deployer path before 0.8.0) asks a harder question: can
this person set up, deploy and manage Hermes for a small client (a solopreneur, a three-person firm), the kind of
work Tony Simons and Orgo offer? A multiple-choice test cannot answer that. This file says what the path does
instead, which assessment practice each part rests on, and which claims could not be verified.

Nobody has tested this path on learners. The design follows published assessment practice. Every number that is
Field Academy's own choice is marked as one.

## What is verified and what is not

Citations marked **checked** were looked up on 2026-10-04 against the publisher, PubMed or the author's own
site, and the title, journal, year and pages matched. Citations marked **from memory** were not looked up, and a
reader should check them before relying on them. A claim marked **not verified** has no source behind it here.

## The five kinds of evidence, and where each comes from

### 1. A performance, not a recall question

The path makes learners do the job: repair a client's files, write a proposal, run a service. That is performance
assessment, which Wiggins (1990) calls authentic assessment: examining performance on worthy tasks directly.
Miller's pyramid (1990) separates knowing, knowing how, showing how and doing, and argues that assessment should
climb it. Labs and the proposal are "shows how". The real deployment and the drills are the closest this plugin
can get to "does", because they happen on the learner's own Hermes.

- Wiggins, G. (1990). The case for authentic assessment. *Practical Assessment, Research & Evaluation*, 2(1). **checked**
  (an earlier draft of this file cited it as 2(2); the volume's issue is 1).
- Miller, G. E. (1990). The assessment of clinical skills/competence/performance. *Academic Medicine*, 65(9 Suppl), S63-S67. **checked**

### 2. Break-and-fix labs with a hidden fault

Each lab is a client machine with one fault injected and symptoms the client can see, which the learner must trace
to a cause through logs. Fault injection is a standard way to test whether a system, or a person, copes with
failure; chaos engineering is the same idea applied to running services. Field Academy borrows the shape: a
steady state (the client's setup works), a fault, evidence, and a check that the steady state is back.

- Basiri, A., et al. (2016). Chaos engineering. *IEEE Software*, 33(3), 35-41. **checked**
- Hsueh, M.-C., Tsai, T. K., & Iyer, R. K. (1997). Fault injection techniques and tools. *IEEE Computer*, 30(4), 75-82. **from memory**

The graders are scripted, like the stations of a structured clinical examination, where the marking is decided in
advance and the examiner's mood does not enter into it. A script is also what makes a lab fair across seeds.

- Harden, R. M., Stevenson, M., Downie, W. W., & Wilson, G. M. (1975). Assessment of clinical competence using objective structured examination. *BMJ*, 1, 447-451. **checked**

Three design choices follow from that, and all are Field Academy's own:

- **Seeded variants.** The names, keys, numbers and which variant of the fault appears all come from a seed, so one
  learner's repair does not pass another's lab. A test proves a repair made for one seed fails on another.
- **Hidden criteria.** The checks are shown only as misses, one at a time, through the same hint ladder the
  missions use (what was missing, one hint, then a worked example). A learner who cannot see the answer sheet must
  find the fault. **Not verified:** that hiding criteria improves learning. It protects the assessment's validity;
  it is not claimed to help learning.
- **No free pass.** The original broken folder always fails. Deleting the broken thing (a key, a job) fails,
  because the grader checks that what worked still works. A fix that looks right and is wrong, such as moving a key
  to a safe file without switching the leaked one off, fails with its own message.

What the labs look like is an approximation. **Not verified:** that the file layout in a lab matches a real Hermes
home. The files imitate one (settings, a keys file, scheduled jobs, logs, a profile folder) and are labelled as
imitation. The secrets-handling the labs teach follows the Twelve-Factor App's rule to keep credentials out of
code and settings files that are saved to a repository and put them in the environment, and the least-privilege
principle in Saltzer and Schroeder.

- Wiggins' and Harden's sources above, plus: The Twelve-Factor App, factor III, Config: <https://12factor.net/config> **checked**
- Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proceedings of the IEEE*, 63(9), 1278-1308. **checked** (the least-privilege principle is in it)
- National Institute of Standards and Technology, SP 800-57 (key management), for the idea of a rotation interval and revoking first. **from memory**

The credential-isolation lab (one key per helper, scopes limited to the job, no key in a settings file, a rotation
note with a named owner) is Field Academy's own exercise built on those ideas.

### 3. A written proposal, scored by rubric and by script

The proposal is a work product with hidden criteria. Where a criterion is checkable (a named owner, a price that
fits the budget, an access list with no blanket permission, a refusal of the unsafe request that says what it
refuses and offers something instead) a script checks it. Where it is not (is the scope honest, could the client
run the handover) the learner's own Hermes scores it against a fixed rubric, the same way an explain-it answer is
scored. Rubrics can be reliable when criteria are explicit and scorers are trained, and are weaker as a guide to
validity on their own.

- Jonsson, A., & Svingby, G. (2007). The use of scoring rubrics: Reliability, validity and educational consequences. *Educational Research Review*, 2(2), 130-144. **checked**

**Not verified:** how closely a language model's score tracks an expert's on this rubric. The path does not rely on
it: the model's score is one of three gates, and the expert review reads the same text. The model that scores is
the learner's own, so the score proves the answer was sent to a model and scored, and the human review is what
checks that the scoring was sensible.

The price check requires a setup price between 40 and 100 percent of the budget. The 40 percent floor is Field
Academy's own choice, made so that a price far below what the work can be delivered for is not rewarded. A
reasonable person could pick another floor.

### 4. Judgment scenarios

Nine cases have no clean answer. They are situational judgment items, which present a work situation and ask
what the person would do. Meta-analysis finds such tests predict job performance usefully (a validity coefficient
near .34 across about 10,000 people in the 2001 review), and that they overlap with general cognitive ability.

- McDaniel, M. A., Morgeson, F. P., Finnegan, E. B., Campion, M. A., & Braverman, E. P. (2001). Use of situational judgment tests to predict job performance: A clarification of the literature. *Journal of Applied Psychology*, 86(4), 730-740. **checked**

Standard situational judgment tests ask the learner to pick or rank responses. Field Academy asks for a written
answer instead, because the skill being assessed is explaining a decision to a client, and a ranking cannot show
that. **Not verified:** that a written, rubric-scored answer predicts anything. It is a design choice. The rubric
rewards the reasoning (the competing duties named, a middle path considered, a decision owner named, what goes in
writing, the condition for walking away) and never a verdict, and two different verdicts can both pass.

The ninth case, about connecting a tool, covers the audit and staged-verification parts of the lifecycle below.

### 5. A person reads it and signs it

Scripts check files. They cannot judge whether a learner reasons well, whether their evidence is plausibly their
own, or whether they could stand in front of a client. So the Guide Field Record needs a reviewer the learner
chooses, someone with the experience to judge it, to read a packet of all the evidence, score six rubric lines from
0 to 3, and sign. Without the signature the learner holds "Guide, awaiting review". Nobody at Nous Research or on
the Hermes team appoints or approves reviewers, and the published reviewer list ships empty.

This follows the argument that a score is only as good as the argument that supports using it: for a record that
says someone is competent, the argument needs a human who can be named and who answered for the judgment.

- Kane, M. T. (2013). Validating the interpretations and uses of test scores. *Journal of Educational Measurement*, 50(1), 1-73. **from memory**
- American Educational Research Association, American Psychological Association, & National Council on Measurement in Education (2014). *Standards for Educational and Psychological Testing*. **from memory**

The sign-off is a JSON file signed with the reviewer's Ed25519 key, so the plugin can verify that it was made by
a key it trusts, over this exact packet, with the scores shown. The signature code is the reference algorithm in
RFC 8032 and is tested against that RFC's vectors. See docs/reviewing.md for what that does and does not prove.

## Evidence that something ran over time

A real deployment and a failure drill are the parts of the path that happen on the learner's own setup, over days.
Field Academy cannot watch them, so it reads what Hermes itself recorded afterwards and judges the times:

- **Run history.** At least five runs, on at least three different days, with at least 48 hours between the first
  and last, after the learner started the clock, with no run in the future, not all in the same minute, and not
  mostly failed. The numbers are Field Academy's own choices.
- **A drill.** At least two runs before it, so the check can learn how often the job normally runs; a gap while it
  was broken (no run, or a failed run) that is long enough for a scheduled run to have been missed; and a run
  after recovery. A drill shorter than the job's usual gap cannot show a gap, and says so.
- **Where Hermes cannot be read**, the screen says so and the part becomes a packet the reviewer checks. A
  learner's own account never passes alone. This matters because self-attestation is the weakest evidence there
  is, and Field Academy does not pretend otherwise.

**Not verified:** the layout of Hermes's run history and logs. The reader looks for a run-history database under
`cron/` and for log lines that name the job, opens them read-only (and, for the database, immutable, so no journal
or lock file is created beside it), and keeps only timestamps and whether a run looks failed. The database layout it
assumes was taken from Tony Simons's manual as quoted in docs/curriculum-voice.md, which says run history lives in
`cron/executions.db`. The Hermes source confirms that file and its `executions` table (cron/executions.py, checked
2026-10-15). It could not be run against a live Hermes while this was written. Hermes writes that database in WAL
mode, and an immutable read skips the newest, not yet checkpointed runs, so a run can show up late. The desktop half also
reads the scheduler list and the chat list with the same read-only calls the mission checks use. It cannot read
the Kanban board (a plugin page reaches only its own backend), and says so on the screen.

Each check adds what Hermes shows to a growing record, so if Hermes shows only the last run, checking on different
days still builds a history. That is also a weak point: the times the page reads are posted to the backend by the
page, so a modified plugin could post made-up times. The reviewer, and the consistency checks in the rubric's
evidence-integrity line, are the answer to that, and the limit is stated in the Field Record.

## The order of the path

The four camps, and the order of the proposal's sections, follow the lifecycle Tony Simons describes for his
one-to-one Hermes architecture sessions: audit what exists, design the boundaries, build and integrate, then test
in isolation before production (his own names for the phases, as read from a summary of his site, are Deconstruct,
Architect, Build and Integrate, and Staged Verification). Field Academy used the shape and wrote its own words.
Tony Simons has not reviewed this path and does not endorse it. His site offers no certification, and nothing here
says it does.

- tonysimons.dev, read through a summarising fetch, so the details of his process are secondhand here. **not verified**

## Expiry

The Guide Field Record shows the Hermes version it was made on and shows "Re-verify needed" when that version moves to
a new series. Comparing the series is Field Academy's own rule: the major number when it is 1 or more, and the minor
number while the major is 0, because that is the usual reading of a 0.x version. Hermes reports its version from
the install stamp at the top of its checkout (0.22.0 on 2026-10-15), and its package metadata can lag behind (it read
0.21.5 on the same install), so Field Academy reads the stamp first. **Not verified:** how Hermes numbers its
releases. If it treats 0.x minors as compatible, the rule will ask for a re-verify more often than it
should, and the rule is one constant in `evidence.py`. A patch release never expires a Field Record.

Re-verify means the four labs again, on new seeds, on the current Hermes. It does not repeat the proposal, the nine
cases or the review, which is a judgment call: those test skills a Hermes release is less likely to change. The
Field Record is never rewritten; a renewal is recorded beside it.

Other credentials expire and renew on a schedule (cloud and networking certifications commonly do). **Not verified:**
the specific periods any of them use, so none is cited.

## What the Guide Field Record shows

Competence shown in labs and on the learner's own setup, with the signature of a reviewer the learner chose. It
does not show years of client work, and it does not predict how someone will do with a real client. It is the
learner's own record, self-issued with Field Academy, and not issued or endorsed by Nous Research. The record says
all of this on its face.
