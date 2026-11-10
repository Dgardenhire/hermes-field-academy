Hermes Desktop plugin

# Field Academy

Learn Hermes by doing real work and proving it. Field Academy sets up a practice profile, plants one problem in it,
and checks your work by reading Hermes itself. You keep a Field Record of what you prove.

- **Version:** 0.9.0
- **Needs:** Hermes 0.22.0 or later. Checked against Hermes 0.23.0.
- **License:** MIT, free
- **Source:** [GitHub](https://github.com/Dgardenhire/hermes-field-academy)

## Learn by doing

Field Academy is a plugin, an add-on for Hermes Desktop. It teaches Hermes by having you use it. Each mission ends
with you making something real in Hermes, and a check that looks at it.

It's for anyone who runs Hermes or wants to. You go at your own pace.

Field Academy is an independent plugin developed by Damon Gardenhire. It is not an official plugin for Hermes made by
Nous Research.

![The Field Academy home page: the mountain banner, then the Foundations card in three parts](shots/foundations-home.png)

*Home.* Foundations comes first, then the paths.

## Getting it running

You need Hermes Desktop with Hermes Agent 0.22.0 or later. You install Field Academy once, on the computer where
Hermes runs.

1. **Install it from Hermes Desktop.** Open [this install link](hermes://plugin/install?catalog=field-academy) and
   Hermes Desktop installs Field Academy for you. Or, in Hermes Desktop, click **Capabilities**, then **Plugins**,
   find Field Academy and click **Install**.
2. **Reload Hermes.** Restart it, or press <kbd>Ctrl</kbd>-<kbd>K</kbd> on Windows or Linux (<kbd>Cmd</kbd>-<kbd>K</kbd>
   on a Mac) and choose **Reload desktop plugins**.
3. **Click Field Academy** under Tools in the sidebar.
4. **Press Open Foundations** and start the first mission.

> **Prefer the terminal?** Run this line instead of the first step. On Windows, use PowerShell. It downloads Field
> Academy and switches it on.
>
> ```bash
> hermes plugins install Dgardenhire/hermes-field-academy --enable
> ```

> **To remove it.** Run `hermes plugins remove field-academy`. Your progress stays saved until you delete the
> field-academy folder. On Windows it's in `%LOCALAPPDATA%\hermes\plugin-data`, and on a Mac or Linux it's in
> `~/.hermes/plugin-data`. Practice profiles stay until you delete them.

## Foundations

Foundations is eleven missions on how Hermes really works. It's the Foundations card on the home page, under the paths. The first practice is the **Start here** card at the top of that page. Each mission
takes about an hour.

**Already use Hermes?** You can test out of a mission instead of taking it from the top. Open **Already use Hermes?
Test out of a mission** on the Foundations page and press **Test out** beside a mission. A test-out skips Recall, and
the lesson and the worked example are there only if you want them. Everything that proves the skill stays: your claim,
your guess, the practice profile with its planted problem, the job, your own score and the check. Pass every check on
the first run, your explanation included, and the mission goes into your Field Record marked **Tested out**, never as
completed. Miss one and you finish the mission the usual way, from where you are; the record says the try began as a
test-out. Mission 11 is the review itself, so it has no test-out.

If you start a mission without the ones before it, its Recall says so and asks for your best guess instead.

![The Foundations page: eleven missions in order, each with its time and expected cost](shots/foundations-path.png)

1. **Check whether Hermes really did what it says.** Tell from what Hermes actually did whether its "done" is true.
2. **See what a chat costs, and cut it.** See what makes a chat cost what it does, and cut the cost.
3. **Save a fact to memory and check it stuck.** Get one fact into memory and prove it stuck.
4. **Start a new chat at the right time.** Know exactly when a change to Hermes takes hold.
5. **Turn a repeat job into a skill.** Make a skill Hermes finds on its own.
6. **Keep two jobs apart in two profiles.** Keep two jobs apart in two profiles.
7. **Connect an outside tool safely.** Give an outside tool only the access a job needs.
8. **Set up a job that runs on a schedule.** Set up a scheduled job that runs right with nobody watching.
9. **Stop a mistake before it happens, or undo it.** Know whether a mistake is stopped before it happens or undone after.
10. **Find out why Hermes failed, and fix it.** Find why Hermes failed with its own logs, fix it, and show the fix holds.
11. **Foundations review.** Take a job through a profile you didn't set up, and find what's planted in it.

### The practice profile

Every mission runs in a practice profile, a separate Hermes profile with its own memory, settings and chats. Field
Academy asks Hermes to make it when you press the button on the mission page. It's called `academy-practice`. A
mission that needs two profiles also makes `academy-practice-b`, and a new try makes `academy-practice-2`.

Your own profile stays as it is. The checks read only the practice profile, never yours. The one thing that happens
in your own profile is grading: when you send your explanation, Field Academy opens one new chat there, in the profile
you're using, and your Hermes scores the answer with Field Academy's grading tool. That chat is all Foundations adds to
your profile, and it reads nothing else there.

Two names to keep apart: the **practice profile** is `academy-practice` itself (the page shows where it lives), and the
**practice folder** is the folder inside it where a mission's files sit, `academy-practice/practice-folder`.

**Open practice chat** opens a new chat in the practice profile. Every press opens a brand-new chat, which matters:
some missions are about what a new chat knows.

When you're done with a mission, press **Delete practice profiles** on its page, or delete them in Hermes under
**Settings**, **Profiles**.

### The planted problem

Before your first chat, Field Academy sets up one snag in the practice profile, the kind a real setup has. In the
memory mission, saves might be held for approval, or memory might be nearly full. In the scheduled-jobs mission, a
draft job might send its result to a place that doesn't exist.

The page tells you a snag is there. It doesn't tell you which one. Noticing it is part of the work, and your Field
Record says whether you caught it.

### Twelve steps

A row of steps at the top shows where you are. In a narrow window it shows dots, and the step's name is the heading
below.

1. **Recall.** Three minutes to write two things from memory, without looking back.
2. **Your claim.** The sentence you're about to prove.
3. **Your guess.** Say which checks you expect to pass. Once the practice starts, your recall, claim and guess
   are locked.
4. **Practice.** Field Academy makes the practice profile. A short try shows you the idea.
5. **The idea.** How this part of Hermes works. Facts carry a small tag with the Hermes version they were checked
   against.
6. **Watch it done.** Someone works the same kind of job: what they did, saw, noticed and ruled out at each step.
7. **Your turn.** The real job, in the practice profile.
8. **Score yourself.** Say how each check went before you see it.
9. **Check.** Field Academy reads the practice profile and shows what it found.
10. **Compare.** Your guess, your score and the real result, side by side.
11. **Fix and transfer.** Fix what missed, then use the idea on a different job.
12. **Record.** Add the mission to your Field Record.

![Your turn in the memory mission: the two notes the profile's owner can't lose, the steps, and the buttons](shots/foundations-lab.png)

*Your turn.* The box at the top lists notes that must survive. The buttons open a practice chat and show the
memory file.

### The check

When you press **Check my work**, Field Academy opens the practice profile's own files and reads them: the memory
files, settings, chat records, scheduled jobs, run history and logs. Each check shows what it found, with numbers
you can look up yourself, like "479 of 2,200 characters, 5 lines" for `MEMORY.md`.

![The check: each check with what Field Academy read, and the explain-it question below](shots/foundations-check.png)

One check stays hidden until you're done, so you can't aim at it. The page says how many hidden checks passed.

Then you explain the idea in your own words. Your own Hermes scores the answer in one new chat in your own profile,
not the practice one. The table above the box says what each level looks like.

**Missed a check?** The Check step says how to check again right there: fix the snag, write one line at Compare on
what surprised you, then press **Check my fix**. Your first result stays on the record beside the new one.

**Check yourself,** at the end of each lesson, asks you to write your answer before it shows its own. Your answer
stays on the page; nothing is saved or graded.

**Missions 2, 7 and 9** show a warning on the Practice and Your turn steps, before your first chat: what the practice
profile's connector does (missions 2 and 7), and that until you fix mission 9's planted setting, the terminal can reach
your whole computer.

![The scheduled-jobs mission in light mode: two scheduled runs have landed, and you score yourself first](shots/foundations-schedule.png)

*Score yourself.* In the scheduled-jobs mission, the page tells you when two scheduled runs have landed.

### Your Foundations Field Record

Open it from the Foundations page with **Open my Field Record**. It shows:

- Your claims, each with the checks behind it.
- **How your self-judgment moved:** your guess, your own score and the real result for each mission. There's no
  average on purpose; with about four checks a mission, one lucky check moves an average more than judgment does.
- Every excerpt Field Academy read, with the file it came from, the check it backs and a SHA-256 fingerprint. Tick
  **Keep this excerpt out** for anything you don't want someone else to see. A kept-out excerpt keeps only its
  fingerprint.
- Two things in your own words: what the record doesn't show, and, if you want, one real case.

![A Foundations Field Record: who issued it, the claims, and the table of guesses and results](shots/foundations-record.png)

**Save my Field Record** writes a folder in `~/.hermes/plugin-data/field-academy/field-records/`. It holds the
record, every excerpt you kept, a `README.txt` and a `MANIFEST.sha256` file. Anyone you give the folder to can type
`shasum -a 256 -c MANIFEST.sha256` inside it and see that the files match each other. That catches a damaged file; it
doesn't prove the folder is the one you saved, so send your record number by another route too.

`record.md` is written for a stranger with five minutes. It opens with a one-line verdict (missions passed and how,
planted problems caught and missed, who graded the explanations, whether anyone outside reviewed it). Each excerpt is
captioned with the check it backs and what that check found, every date has its time (UTC), a claim you kept in the
course's words is labelled as the course's, and each entry ends with two or three questions to ask you in an
interview.

## The mountain

The home page is a map of Mount Olympus. Each path is a trail up the mountain, named for one of Hermes's old jobs in the Greek myths. After Foundations, new learners start on Messenger.

- **Messenger:** For introductions. Watch Hermes do one real job, explain it honestly, and pass a good idea to someone who can build it.
- **Traveler:** For yourself. Run Hermes on your own computer and keep one daily job working.
- **Crossroads:** For clients. Set Hermes up for a client, connect it to their tools and hand it over.
- **Boundary Keeper:** For an organization. Plan Hermes for a whole team: who owns what, who approves what, and how it recovers.
- **Guide:** For people who set up and run Hermes for a client. Fix broken setups, write a proposal, connect a real service and get your work reviewed.

The first four paths have 20 missions in all.

- Click a trail, a waypoint or a flag to open it.
- **Review queue** lists missions due for a quick review.
- **What changed since you learned this** lists missions whose lesson or check changed after you passed them. A pass always stays a pass.

![The trail map: four trails, Messenger, Traveler, Crossroads and Boundary Keeper, each a dotted line across Beginner, Intermediate, Advanced and Capstone camps to a summit flag](manual/trail-map.jpg)

*Trail map.* Filled waypoints are passed, and the ringed one is where you are.

## Camp by camp

Every path climbs the same way, one camp at a time.

1. **Beginner.** The basics the rest of the path stands on.
2. **Intermediate.** Hermes starts doing more of the work for you.
3. **Advanced.** Hermes works without you there to ask.
4. **Capstone.** One mission on a problem of your own. You decide what success looks like before you start.
5. **The summit.** Pass every mission and you can create your Field Record for that path.

Each mission shows how long it takes and whether you've passed it. **Next** marks the one to do now.

![The Traveler path: a trail across four camps, the placement check, the camps listed in order with each mission's time and status, and the summit](manual/path.jpg)

*Traveler path.* Camp 1 passed, Camp 2 in progress, and the Field Record waiting at the summit.

## Inside a mission

Every mission has six steps. You mark each one done as you go.

1. **The story.** A short story about someone using Hermes, and what they did at each turn.
2. **The takeaway.** The main idea in a few lines.
3. **Your turn.** A half-finished example. You fill in the blanks, then see the model answers beside yours.
4. **Try it.** A button opens the right page in Hermes, or starts a new chat with the practice prompt already sent.
5. **Explain it.** Answer a question in your own words. Your own Hermes scores it out of 100, and 70 passes.
6. **Prove it.** Make something real in Hermes, such as a skill, a scheduled job, a chat or a document, or look up a fact Hermes reports. Then press **Check my work** and Field Academy looks at it.

![The mission Find where Hermes is running: six steps done, By the end, Why this matters to you, the story of Dana's Monday summary, and a diagram of the four parts called Hermes](manual/mission-top.jpg)

*A mission.* A story about a missing Monday email, then the four parts that all get called Hermes.

![Your turn: two blanks to fill about Marcus's Friday report, with the learner's answers beside the model answers](manual/mission-turn.jpg)

*Your turn.* Fill in the blanks first, then compare.

### Good to know

- Everything you need to pass is on the page. Extra guides and videos sit at the bottom under **Go deeper**.
- If Hermes runs on a different computer, you can paste a document into the page instead of saving it.
- Help fades as you climb. Later missions give you less of the example and more of the work.

## When a check misses

A miss tells you what's missing and gives you one hint. Miss again and you also get a worked example to follow. You can retry as many times as you like.

1. **Read What was missing.** Each line names one thing to fix, like a section that's too short.
2. **Fix the first item.**
3. **Press Check my work** again.

![Steps 5 and 6 of a Crossroads mission: an answer box with Send for scoring, then Check your scope document with a miss listing what was missing, one hint and a worked example](manual/mission-prove.jpg)

*A second miss.* What's missing, one hint and a worked example.

## Keeping it fresh

People forget what they don't use, so passed missions come back for short reviews. A review is three questions, about four minutes, scored by your own Hermes.

- **First review:** Two days after you pass a mission.
- **Answer well:** The next one waits longer: a week, then three weeks, then two months.
- **Answer poorly:** It comes back tomorrow. The mission stays passed.
- **Strength:** Each passed mission shows **Strong**, **Holding**, **Fading** or **Weak**. It slips the longer a review waits.

Press **Start a review** on the home page, or **Practice early**.

![The review queue: 2 missions due, Start a review and Practice early buttons, and three missions with strength bars, two Fading and one Strong](manual/review-queue.jpg)

*Review queue.* Two missions due now, each with its strength.

![Your review is scored: one answer at 88 marked Strong, one at 62 that comes back sooner, with what was missing and one hint](manual/review-scored.jpg)

*Scored.* A weak answer shows what it missed and comes back sooner.

## Skip ahead

Already use Hermes? Each path has a placement check: six questions, two for each level, about five minutes.

1. **Open the path** and press **Take the placement check**.
2. **Answer the six questions** and press **See my result**. Each answer shows whether it was right, and why.
3. **Get both questions on a level right** and you can skip that level's reading and practice.

> **What still counts.** You still answer the question and pass the check on every mission. Your Field Record notes which missions you skipped the reading on.

![Placement check result: You knew Beginner, with a Skip the reading on 2 missions button, and the first two questions marked right with explanations](manual/placement.jpg)

*Placement result.* Both Beginner questions right, so the Beginner reading can be skipped.

## Your Field Record

A Field Record is your own record of what you learned on a path. You create it at the summit once every mission is passed.

Every Field Record carries this line: "Self-issued with Field Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research."

1. **Open the path** once every mission is passed.
2. **Type your name** the way you want it on the record.
3. **Press Create your Field Record.**
4. **Press Save as a file** if you want a copy.

#### What's on it

- Your name and the date.
- What each mission's check found, and your scores.
- The name of each document you wrote, with a fingerprint that matches that exact file.
- Which missions you skipped the reading on.
- A record number.

#### What isn't

- Your written answers.
- Your chats.
- Where files sit on your computer.

### The record number

The record number is a short code made from everything on the record. It shows the record hasn't been changed by accident.

It catches mistakes, not cheating. Anyone can edit a record and make a new number, so the number isn't proof by itself.

Records made before version 0.8.3 were called certificates. Their record numbers still match, and the screen shows them with the new name.

## The Guide path

The Guide path asks one question: can you set up and run Hermes for a small client, like a one-person business or a three-person firm? Its four camps follow the order of a real setup.

1. **Audit.** Each lab gives you a practice folder laid out like a client's Hermes, with one problem hidden in it. Find it, fix it and write down what happened.

   - **The key in the open:** a secret key that leaked into a saved settings file.
   - **The runaway bill:** a job running every minute on an expensive AI model.
   - **Monday after the power cut:** a service that doesn't start again after a restart.

2. **Architect.** One more lab, a proposal for a made-up accounting firm, and nine hard cases with no clean answer.

3. **Build and integrate.** Connect one real service to your own Hermes, with only the access it needs, and let a scheduled job use it for at least three days.

4. **Staged verification.** Break something on purpose and show Hermes recovers. Then explain one lab the way you would to a client.

5. **The review.** A reviewer you choose, someone with the experience to judge it, scores your work and signs it. You paste their signed file into the page.

> **On Windows.** Two lab steps work a little differently on Windows, and the lab's help shows the Windows way. To lock a file so only you can read it, a Mac or Linux uses `chmod 600 .env`. On Windows, open PowerShell in the lab folder and type `icacls .env /inheritance:r /grant:r "${env:USERDOMAIN}\${env:USERNAME}:F"`. If another account is still listed after that, take it off too with `icacls .env /remove` and its name. To let a script run, a Mac or Linux uses `chmod +x`. Windows has no such setting, so the schedule line names the program that runs the script, such as `/bin/sh`. The checks and your Field Record are the same on every computer.

![The Guide path: a trail across Audit, Architect, Build and Verify, four camps listing the labs, the proposal, the nine scenarios, the real service, the drills and the walkthrough, and a summit card that needs a reviewer you choose](manual/guide-path.jpg)

*Guide path.* Nine parts in four camps, then a reviewer you choose.

![The lab The key in the open: a note from the client, the lab folder with Open the folder, what the client sees, and a box for your diagnosis](manual/guide-lab.jpg)

*A lab.* A client's note, a folder to fix with made-up keys, and a box for your write-up.

### Your Guide Field Record

When all nine parts pass and your reviewer's signed file is loaded, you can create your Guide Field Record. Until then, the path ends at **Guide, awaiting review**.

- Ask your reviewer for their public key, a code that lets Field Academy check their signature, and add it on the review page. Field Academy's own reviewer list is empty for now, so your record says you added the key yourself.
- The signature proves your reviewer signed your work. It doesn't mean anyone else vouches for them.
- The record shows the Hermes version you worked on. After a major Hermes update, it shows **Re-verify needed** and asks you to redo the four labs on new cases.

Each lab case is different, so copying someone else's fix won't pass on yours.

## Questions

### Do I have to copy and paste prompts?

No. When Field Academy needs Hermes to practice or score something, it opens a new chat and sends the prompt for you. On an older Hermes, it copies the prompt and you paste it.

### Who scores my answers?

Your own Hermes, with the same scoring guide every time. A 70 out of 100 passes.

### Does it send my information anywhere?

No. Field Academy has no server, no tracking and no account. Your progress is saved on the computer where Hermes runs, and your own Hermes scores your answers.

### Can someone fake a pass?

Yes, if they change their own saved data, or send Field Academy a made-up result for one of the four checks that read Hermes. Field Academy checks every document itself. It's a learning tool, and your record shows what passed on your own computer.

### Does Foundations touch my own Hermes profile?

No. Every mission runs in a practice profile Field Academy makes. It only writes to a practice profile before its
first chat, and only a few named settings, the two memory files and sample files. It never reads or writes your own
profiles, and never touches `.env` or `auth.json` anywhere.

### What does a Foundations mission cost?

A few short chats on your own model provider. Each mission says what it expects before you start. Mission 2 shows
you where to read the real figure.

### Do I lose a pass when a lesson changes?

No. The mission shows under **What changed since you learned this** with a **Re-verify** button. Your pass stays either way.

### Can I see my progress outside the app?

Yes. Type `/academy` to Hermes in your terminal, or in a messaging app connected to Hermes, and it shows the map as plain text.

### Will updating Field Academy erase my progress?

No. Your progress is saved apart from the plugin, and it carries over from earlier versions.

### How do I start over?

Delete the field-academy folder, and Field Academy starts fresh the next time you open it. On Windows it's in `%LOCALAPPDATA%\hermes\plugin-data`, and on a Mac or Linux it's in `~/.hermes/plugin-data`.

### Is Field Academy made by Nous Research?

Field Academy is an independent plugin developed by Damon Gardenhire. It is not an official plugin for Hermes made by Nous Research.

## Credits

Field Academy links to guides and videos made by people across the Hermes community, and every link names its author. None of them have reviewed or endorsed Field Academy.

- **Nous Research**, for the [Hermes docs](https://hermes-agent.nousresearch.com/docs/), the first stop in every Go deeper list.
- **Tonbi**, Tonbi's AI Garage, for the Hermes Agent Masterclass. [hermesatlas.com/masterclass](https://hermesatlas.com/masterclass/)
- **Kevin Simback**, Hermes Atlas, for its guides to Hermes. [hermesatlas.com](https://hermesatlas.com/)
- **Tony Simons**, for The Whole Damn Thing, on how Hermes works and where it breaks. [On X](https://x.com/tonysimons_/article/2079066422211117218)
- **School of Hermes**, a concept by Damon Gardenhire, for the client-work labs. [linchpin.studio/school-of-hermes](https://linchpin.studio/school-of-hermes/)

The way Field Academy teaches draws on published research about how people learn and remember.

## Keep exploring

- **Hermes Agent** from Nous Research. [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com)
- **The Hermes Bible**, by iamlukethedev. [hermesbible.com](https://www.hermesbible.com/)
- **Hermes Atlas**, by Kevin Simback. [hermesatlas.com](https://hermesatlas.com/)
