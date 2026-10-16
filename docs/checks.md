# Audit of every check

Every mission ends with a check on real work. In 0.4.0 most checks passed when
something existed: any saved session, any installed skill, any scheduled job,
any file with the right headings and 240 characters. 0.5.0 replaces each one
with a check that needs a specific thing the learner made in that mission.

Three kinds of evidence are used:

- **A typed answer compared with what Hermes reports.** The learner reads a value
  in the app, writes it down, and the check compares.
- **A marker.** The practice makes something whose name or first line carries a
  mission-specific marker, so a skill, job or chat the learner already had can't
  pass the check.
- **A document whose every section holds real content.** Each section has a
  minimum length and, where the section asks for one, a name, a number, an amount
  of money, a time or a list. Placeholder text, repeated sections, a file that is
  mostly the worked example, and a file that already passed another mission all
  fail. The capstones also compare the criteria the learner wrote with the
  evidence they gave for each one.

## The table

| Mission | Old check (0.4.0) | New check (0.5.0) |
|---|---|---|
| `operator.runtime` | Hermes answers and the window is connected | The profile and the connection type the learner read in Gateways, compared with what Hermes reports |
| `operator.desktop` | At least one saved session | A saved session that starts with the marker `[FA-DESKTOP]`, which the practice prompt carries |
| `operator.learning` | At least one skill and one tool set | An installed skill whose name starts with `academy-` |
| `operator.automation` | At least one scheduled job | A job named `academy-...` that has a schedule and whose request covers four of the five points: where to work, what to read, what a good result is, where to send it, what to do on failure |
| `operator.capstone` | None (new) | A report with criteria the learner wrote and one piece of evidence per criterion, each with a verdict |
| `integrator.discovery` | Seven headings, 240 characters | Seven sections: a named client and owner, a time in Workflow, a number in Acceptance, two items in Out of scope, a price in dollars |
| `integrator.deploy` | This window names a connection route | A five-section setup note (a named person for whose computer and for the 2 am call, a time for updates) and the live connection route |
| `integrator.connect` | Hermes lists at least one tool | A six-section approval test record (a named approver, a time for each approval and refusal) and Hermes listing its tools |
| `integrator.handoff` | Nine headings, 240 characters | Nine sections with named owners, a list of separate steps for Recovery and Limits, and times for Cron and Backups |
| `integrator.capstone` | None (new) | A report checked against criteria the learner wrote |
| `architect.estate` | Hermes lists an agent or a route | A six-section map with a named person on every part, and Hermes listing at least one profile for this window |
| `architect.governance` | Seven headings, 240 characters | Seven sections: names, lists and times where each asks for one |
| `architect.operations` | Hermes lists at least one named agent | A five-section task card with a number in Done when and named people for the review and the owner |
| `architect.reliability` | Seven headings, 240 characters | Seven sections with numbers for service levels, baseline and after, a price for Cost, numbered recovery steps |
| `architect.capstone` | None (new) | A report checked against criteria the learner wrote |
| `ambassador.firsthand` | None (new) | Four sections: a time in The job, a list of steps in What Hermes did |
| `ambassador.story` | Five headings, 240 characters | Five sections: a number in What it takes, a named teacher in Credit |
| `ambassador.qualify` | Seven headings, 240 characters | Seven sections: Decision starts with yes, later or no; named people for Prospect, Owner and Authority |
| `ambassador.handoff` | Five headings, 240 characters | Five sections: separate lists for Known and Promised, a named owner, a time for Next step |
| `ambassador.capstone` | None (new) | A report checked against criteria the learner wrote |

## Checks that cannot be made strong, and why

These limits remain after the rewrite. Each is said on the screen where it
applies, and none is hidden.

- **`operator.runtime`.** The check compares the learner's answer with what Hermes
  reports. If this version of Hermes doesn't report the connection type, the
  check accepts the answer as written and says so in its result. The profile name
  is always compared.
- **`operator.desktop`.** The marker proves the practice chat exists and was
  started from the practice prompt. It can't prove the learner did the steps in
  it. The check reads the saved session list as text, and it could not be run against
  a live Hermes here, so a Hermes that titles chats without the first message would
  not show the marker. The page offers a typed chat name as a fallback. When Hermes
  shows a time for the chat, it must be newer than the mission's first step.
- **`operator.automation`.** Hermes's job list (`cron.manage` list, asked to include
  paused jobs) shows only the first 100 characters of a request, as `prompt_preview`.
  So the learner pastes the whole request, and it counts only if it begins the way
  Hermes shows that job's request. Past the first 100 characters the text is the
  learner's paste. The five points are found by plain word matching, which is
  generous, so a request can pass the points without being a good request.
- **`operator.learning`.** The check reads skill names fresh from Hermes's command
  catalog. It proves an `academy-` skill exists, not what is in it, and Hermes has no
  call that lists memory to a plugin, so the memory half of the lab is not checked.
- **`integrator.connect`.** Hermes asks for approval before a risky command, and
  before a write-capable tool only on an MCP server marked `trust: untrusted`;
  other connected tools act without asking. The test uses Hermes's own approval
  prompt on a scratch folder. Nothing in Field Academy can see whether that prompt appeared. The record is the learner's own account, held to a named
  approver and two times. That raises the bar. It doesn't turn the account into proof.
- **`architect.operations`.** Field Academy's page can call only its own
  backend, so it can't ask whether a card exists on the Kanban board, and the
  task card is the learner's own record.
- **Every document.** The checks find the parts a real document has. They can't
  judge whether the writing is good, and a name check sees a name-shaped word,
  not a real person. The result says so on every pass: the writing is the learner's to judge.
- **Every typed live check.** The desktop half posts its own result to the
  backend, so a modified plugin could post a pass. The Field Record states what was
  checked, and it records the fingerprint of every document.
