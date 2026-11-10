## What's going on

Think of each profile as a house on one street. Every house has its own filing cabinet, its own diary, its own key ring and its own calendar. The street, with everything lying on it, is shared.

A **profile** is a complete, separate Hermes with its own folder. Almost everything Hermes keeps for itself lives in that folder:

- its memory notes
- its chat history
- its settings, including which model it uses
- its keys for outside services
- its instructions (`SOUL.md`)
- its skills
- its scheduled jobs
- its messaging connections, like a Telegram bot

Your main profile is the Hermes folder itself: `~/.hermes` on Mac and Linux, `%LOCALAPPDATA%\hermes` on Windows. Every other profile sits inside it, under `profiles`.

Hermes in `academy-practice-b` reads only its own house's cabinet, and the Hollis fact sits in the other one. Your files are out on the street. Hermes in any profile can open anything your computer account can open, so a profile keeps Hermes's own records apart and leaves your files where everyone can reach them.

### Copies carry memory with them

The app's **New profile** dialog has a **Clone from** choice, described as copying "config, skills, and SOUL.md." It also copies both memory files. (As of Hermes 0.22.) Hermes treats memory as part of who the agent is, so it travels. Chats and scheduled jobs start empty.

That's right for a twin of the same job. For a different client, it hands the new house a cabinet full of the old client's facts.

### Know which house you're in

- **The button you pressed.** In this course every practice chat starts from **Open practice chat A** or **B**, and the button names the profile.
- **`/profile`.** Type it on its own in a chat that has at least one message, and a short note names the profile that chat is talking to. Add nothing after it: `/profile` with a name changes where your next new chat opens.
- **Settings pages** show an **Applies to** row once you have two profiles. It picks which profile your edits change.
- **Capabilities** has its own picker at the top, labeled **Configuring:**.

In everyday use, the colored squares at the foot of the sidebar switch the whole app between profiles. Leave them alone during this course: Field Academy's page lives in your own profile and disappears while the app is switched to a practice one.

### Reading a profile's memory

Both work without leaving Field Academy:

- **Ask.** Open a new chat in that profile and send `Quote your memory notes exactly, line by line.` Hermes reads its memory at the start of every chat, so a fresh chat can quote it.
- **Look.** Press **Show memory file** beside the profile's chat button. Field Academy shows that profile's `MEMORY.md`, read-only.

### One writer per house

Never run two copies of Hermes against one profile at once. Both save memory, and each reads the other's saves when its next chat starts, until the profile holds a blend of two jobs nobody chose.

## Work it out

A fact can reach another profile's work three ways. Fill in this table from your own try.

| Route | Does `academy-practice-b` have its own? | Did the Hollis fact get through? |
|---|---|---|
| Memory notes | Yes, its own cabinet | Your answer to step 2 |
| Past chats | Yes, its own diary | It has no Hollis chats to search |
| Files on your computer | No, shared street | Your answer to step 3 |

In your run, the profile closed two of three routes. Now work out the case people actually get burned by: you make a new profile with **Clone from**, and the profile you copy already holds a client's fact. How many of the three routes are open to the new one?

> Two. Its memory file starts life as a copy of the old profile's, client fact included, and the files are still on the shared street. Only past chats stay closed.

Now a number from your own run. Press **Show memory file** for A, then for B (or ask a new chat in each to quote its notes), and count the lines. Your try added one line to A and none to B. Write both counts down; you'll need B's in Your turn.

## Check yourself

Answer in the box, then show the answer.

**1. You make a profile for a new client, cloned from your main profile. What does it know on day one?**

> Everything in your main profile's memory notes, plus its settings, instructions and skills. No chats, no scheduled jobs.

**2. Hermes in your `bakery` profile can't remember a supplier you mentioned yesterday. What do you check first?**

> Which profile you were in yesterday: the cheapest check, and often the answer. Then whether the save really happened.

**3. Two clients' files sit in the same Documents folder. Does giving each client a profile stop one client's Hermes from reading the other's files?**

> No. Profiles separate Hermes's own records. Any profile can open any file your account can.

## What people get wrong

- **"A profile is like a chat folder."** It's a whole separate Hermes, with its own memory, keys, skills and schedule. To see it, open your Hermes folder's `profiles` folder and look inside one.
- **"Clone from only copies settings."** The dialog doesn't mention memory, and memory comes along. To see it, ask a new chat in a cloned profile to quote its memory notes: lines from the profile it was copied from are there.
- **"A profile per client keeps their files apart."** It keeps memory, chats, keys and schedules apart. Your try showed B reading a file that belonged to A's client.

## The judgment: when a job gets its own home

1. **Split when facts must never cross.** Different clients, work and family, a board seat and a day job. If one side's details showing up in the other would embarrass you or break a promise, they get separate profiles.
2. **Split when the keys differ.** A client's own email account or drive belongs only in that client's profile.
3. **Split when the tools differ a lot.** Unused tools cost money on every trip (mission 2).
4. **Don't split one person's related work.** Each profile has its own memory, so you'll repeat yourself, and copies of the same skill drift apart.
5. **Start blank for a new client.** Use **Clone from** only to make a twin of the same job, and read the twin's memory before you trust it.
6. **Look before you act.** Before you save a fact, ask for work or change a setting, check which profile you're in.

A profile per client or role is the right size; a single task gets a chat. Give a client's facts their own profile from day one rather than parking them in your main one "for now." For files, give each client its own folder. A real wall around files takes a sandbox, which is a different tool.

## Also good to know

- **From a terminal.** `hermes profile create bakery` makes a blank profile; `hermes profile list` shows them all; `hermes -p bakery chat` starts a chat in one. In a terminal chat, the prompt shows the profile's name, and `/profile` there also shows its folder.
- **New profiles can talk to a model straight away.** A profile made in the app starts with a copy of your model keys. Keys you add to it later stay in it.
- **Command-line tools share your logins.** Tools Hermes runs, like `git`, use your normal account's logins in every profile unless you change `terminal.home_mode`.
- **Sharing a setup.** Right-click a profile square and choose **Export profile…** to save it as one file. API keys are left out.
- **The memory map.** `/journey` opens a map of what a profile has learned over time. It's handy for spotting odd notes, though a cloned file's notes may all show the clone's date.
