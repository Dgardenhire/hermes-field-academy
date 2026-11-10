## What's going on

Hermes is a set of parts that hand work to each other: the app, the gateway (the background program that runs your
chats and schedules), the model provider, Hermes's own tools, your connectors, and the scheduled jobs. A failure lives
in one of them. Each diagnostic looks at some of those parts, in its own way.

- **The error card is the warning light.** It names the layer that failed, from the same classifier Hermes uses to
  decide whether to retry. It says where, and stops there.
- **The doctor is the inspection.** It checks that the setup is put together right: files in place, provider name
  real, key present, the provider reachable. It doesn't send your real request. Your model's name is only tested
  when a real message goes out, so for most providers a typo in the model name passes the doctor.
- **The logs are the flight recorder.** They hold what actually happened, minute by minute, every time.

| File | What's in it |
|---|---|
| `errors.log` | Warnings and errors only. Start here. |
| `agent.log` | Everything: model calls, tools, chats |
| `mcp-stderr.log` | Messages from connectors as they start |
| `gateway.log` | The background program and messaging apps |
| `desktop.log` | The app starting, and its backend crashing |

Every profile keeps its own logs folder. The mission page shows the practice profile's, with a button to open it. The
error card has an **Open logs** button too; before you read any log, check that the folder's path names
`academy-practice`. Your main profile's logs won't have a line for this failure.

So the order is: the card for where, the doctor for the setup, the logs for what happened. A clean doctor rules out a
broken setup and nothing more.

Now read one. On the mission page, find the practice profile's logs folder and press its open button, then open
`errors.log` inside it.

- **On Windows,** double-click it. If Windows asks which app to use, pick Notepad. Press Ctrl+End to jump to the
  bottom, where the newest lines are, or Ctrl+F to search for `ERROR`.
- **On a Mac,** it opens in Console or TextEdit; on Linux, any text editor works. Scroll to the bottom, where the
  newest lines are.
- **If `errors.log` is empty or missing the minute you want,** look in `errors.log.1`. Hermes starts a new file when the
  old one gets big.

Each line starts with the date and time on your own computer's clock, the same time your taskbar or menu bar shows, so
you can match it to the minute you sent `hello`. The time has a comma and three more digits on the end, the
thousandths of a second. Some lines carry a code in square brackets right after the level; that's the
chat the line belongs to.

Find the line at that minute. It's marked ERROR, and it names the failed call. Depending on the provider it says
"Non-retryable client error" or "API call failed," with the reply that came back.

## Work it out

Rule layers out with what you saw. Each piece of evidence clears something.

| What you saw | What it rules out |
|---|---|
| A card appeared in the chat | The app is working |
| The card named the provider or model | The gateway got your message and passed it on |
| The doctor found your key and reached the provider | A missing or rejected key |
| The log shows the provider answered with an error | The network; something answered |

What's left? The provider was reached, accepted the key, and refused the request. The request carries one thing the
doctor never checked: the model's name. Open **Settings → Model** with **Applies to** set to `academy-practice`, and
read the name closely. **Applies to** picks the profile you're editing without switching the app.

Write down your own table from your own card, doctor and log line. Then fix it the safe way:

1. **Back up.** Copy the backup command from the mission page, under **The practice profile's tools**, and run it in
   a terminal: `hermes -p academy-practice backup --quick --label before-fix`. It saves a backup of the practice
   profile in that profile's own `backups` folder.
2. **Change one thing.** Pick the right model name.
3. **Test in a new chat.** Press **Open practice chat** and send `hello`.

## Check yourself

Answer in the box, then show the answer.

**1. The doctor finishes with no problems listed. Can you stop looking?**

> No. The doctor checks that the setup is put together right. The logs tell you what happened when it ran.

**2. The card names the provider or model. You press Retry five times. What changes?**

> Nothing useful. The same request goes out with the same name. Some errors hide the Retry button for that reason.

**3. Your 6 a.m. job shows a finished run, but the report it delivered is empty. Which layer, and where's the
proof?**

> The scheduled job. Open the run from **Run history** and read what Hermes said. Then check `errors.log` around
> 6:00 for warnings about that job.

## What people get wrong

- **"Reinstalling fixes it."** Your settings live in your profile, apart from the program. Update or reinstall
  Hermes and the same broken setting is waiting for you.
- **"A finished run means the job worked."** If a job's working folder is renamed or deleted, the job doesn't stop.
  Hermes logs a warning, runs without the folder, and the run can still finish. The warning in `errors.log` is the
  proof.
- **"Sharing a debug report is safe because keys are hidden."** Keys and passwords are hidden. Client names, file
  names and pieces of your chats aren't. `hermes debug share` and the Command Center's **Debug share** both upload to
  public paste sites. Read it first with `hermes debug share --local`. The error card's **Send diagnostics** goes only
  to Nous Research staff, after asking you, and is deleted after 14 days.

## The judgment: how to work a failure

The first two minutes decide how long the rest takes.

1. **Write down what you were doing and when.** The minute matters, because the logs are sorted by time.
2. **Read the card's layer before pressing anything.** Press **Copy error details** and keep it.
3. **Run the doctor, and read what it doesn't cover.** A clean result narrows the search. It doesn't end it.
4. **Read `errors.log` at that minute,** in the right profile's folder. Then `agent.log` if you need the whole story,
   or `mcp-stderr.log` for a connector.
5. **Back up, change one thing, test in a new chat.** Change three things at once and you won't know which fixed it,
   or which broke something new.
6. **Know when it isn't yours.** If the provider is down, no setting fixes it. **Switch provider** on the card moves
   this one chat elsewhere while you wait.

If ten minutes pass and you still can't name the layer, stop changing things. Gather the card's details, the doctor's
output and the log lines from that minute, and ask for help. Deleting the profile's settings or chat history to "start
fresh" throws away the evidence along with the work, so the next person can't find the cause either.

## Also good to know

- **Filter the logs in a terminal:** `hermes -p academy-practice logs errors --since 1h`, or
  `logs --component cron --level WARNING`. `--since` takes `30m`, `1h`, `2d`.
- **A backup holds your keys.** Keep it private. **Export profile** in the app makes a shareable file with the keys
  left out.
- **A backup fallback can hide a broken model.** If a profile has backup providers set, a model name the provider
  doesn't know sends the chat to the backup instead. Chats work, on a different model than you think.
- **When the app's background program dies,** the app restarts it and shows "Hermes stopped working in the
  background." The reason is in `desktop.log`.
