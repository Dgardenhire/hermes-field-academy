## What's going on

When a job fires, Hermes starts a brand-new chat that nobody is in. Picture a temp worker who has read your staff file
but wasn't in the room for any conversation you've ever had. You hand them a sealed note, and you leave.

| A scheduled run gets | A scheduled run doesn't get |
|---|---|
| The profile's instructions, `SOUL.md` | Anything said in any chat, including the one you set it up from |
| Memory: `MEMORY.md` and `USER.md` | A project's `AGENTS.md`, unless the job has a working folder set |
| The job's own request, and any skills attached | A way to ask you a question |
| The tools allowed for scheduled jobs | Permission to run risky commands |

That's why "For Yusuf:" came through and the file didn't. His preference is in memory. "The file we just looked at"
points at a conversation the run never saw.

Nobody being there has three more effects:

- **It can't ask, and it can't get a yes.** The tool Hermes uses to ask you a question is taken away, and risky
  commands are refused. Mission 9 shows the one way around that refusal.
- **It uses whatever model is set when it fires:** the job's own model, then a model set for all scheduled jobs, then
  your main model at that moment. Leave a job on Default and it follows your main model wherever you move it.
- **Something has to be awake to start it.** A background program called the gateway checks for due jobs every 60
  seconds. As of Hermes 0.22.4 it keeps running after you quit the app. Nothing runs while the computer sleeps. When it
  wakes, a job that missed its time runs once, late. That late run still came from the schedule, not from you.

## Work it out

Use your own job and your own computer.

The Hourly setting fires at the top of every hour. Say your laptop lid closes at 10:30 at night and opens at 7:15 in
the morning. The slots from 11:00 through 7:00 all pass while it sleeps. That's nine slots.

How many runs happen? None overnight. Within a minute of waking, one catch-up run fires, late. Then the 8:00 run fires
on time. Nine missed slots become one late run. A daily report you want at 6:30 would arrive at about 7:15, every
day, and nothing tells you unless you look.

Write your own version: the hours your computer usually sleeps, when your job should fire, and when it would really
arrive.

## Check yourself

Answer in the box, then show the answer.

**1. In a chat you say "From now on, put totals in bold." The 6 a.m. job runs the next day. Are its totals bold?**

> Only if Hermes saved it to memory. What's said in a chat never reaches a scheduled run; what's in memory does.

**2. Your job is on Default. On Friday you switch your main model to a cheaper one to try it out. What runs
Saturday's job?**

> The cheaper one. A job on Default follows the main model at the moment it fires.

**3. You quit the app at 5 p.m. and leave the computer on. Does the 6 p.m. job run?**

> Yes, as of Hermes 0.22.4: the gateway keeps going after the app quits. Close the lid instead and nothing runs until
> it wakes.

## What people get wrong

- **"It worked when I pressed Trigger now, so it'll work at 3 a.m."** At 3 a.m. the computer may be asleep, the main
  model may have moved, and nobody is there to approve a risky step. Trigger now also switches a paused job back on,
  so a half-fixed job can fire at the top of the hour. Pause it again after every test.
- **"A run marked ok did the job."** Ok means it finished and delivered. A run that read the wrong file and reported a
  tidy wrong number is ok too. Read the first results against the source file yourself.
- **"A scheduled job starts from a blank page."** It reads your memory and `SOUL.md`. Don't repeat what memory holds.
  Anything memory doesn't hold, the request has to say.

## The judgment: when to trust a job

Treat a new job like a new hire on the night shift. It earns trust with a record of good nights.

1. **Write the request for a stranger.** Five parts: where to work, what to read, what a good result looks like,
   where it goes, and what to do if it fails. For the last part, tell it to start its reply with `[CRON_FAILURE]` on a
   line by itself when it can't do the work; Hermes then records the run as failed instead of ok. Then cross out every
   phrase that points at a conversation: "the file we talked about," "like before," "the usual."
2. **Pin the model** when the output matters: **Edit cron**, then pick a model in the **Model** field instead of
   "Default (global model)."
3. **Test it paused.** The app's new-job form has no paused option (as of Hermes 0.22.4), so press **Pause** right
   after you create it. Trigger it, read the output against the source, and pause it again.
4. **Decide where it lives.** A laptop that sleeps is fine for a job that can be late. A job that must land at 6:30
   belongs on a computer that stays awake, with the gateway installed so it starts on its own after a restart.
5. **Read the records.** Two on-time runs in **Run history**, with results you've checked, are worth more than any
   feeling that it's set up right.

A job doesn't need to run every few minutes to be useful. And it shouldn't send or delete anything for you until it has
a clean record.

## Also good to know

- **A job can have a working folder.** Then its file tools start there and the folder's `AGENTS.md` is read. The app's
  form doesn't set one; ask Hermes in a chat, or use `--workdir` in a terminal. It has to be the full path to a folder
  that exists.
- **A misspelled delivery place** stops the job before it calls the model. Its status reads `blocked_config`, and no
  tokens are spent.
- **In a terminal:** `hermes -p academy-practice cron list` shows each job's state and last result,
  `cron runs <job>` lists every attempt, and `cron doctor` checks every job and names what's wrong.
