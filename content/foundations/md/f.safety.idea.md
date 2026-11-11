## What's going on

Whether anything catches a mistake depends on which of three doors the action goes through:

- **terminal commands**, like `rm` or `mv`
- **file edits** through its own file tools, the "write file" and "patch" rows you saw in the activity
- **connected tools** from mission 7, like email or a project board

Protection can come at two moments: **before** (something checks or asks) and **after** (something can undo). Three
doors, two moments, six cells:

| | Before | After |
|---|---|---|
| **Terminal commands** | Approvals check risky patterns, like a recursive delete, and may ask you | Checkpoints, if on, snapshot the folder before `rm`, `mv`, `sed -i`, `>` and similar |
| **File edits** | Nothing asks. A short built-in list blocks a few protected places, like your SSH keys | Checkpoints, if on |
| **Connected tools** | Nothing asks, unless the connector is marked untrusted | Nothing. A sent email stays sent |

Your try went through the middle door with checkpoints off, as every profile starts. Both its cells were empty.

The practice profile has one connector, left at Hermes's default, full trust. Nothing asks before it acts. Mark it
untrusted in **Settings**, or switch it off. Your grid describes the profile as you leave it.

Two things in the table move with your settings:

- **The terminal's "before" cell** is the only one Hermes fills for you, in **Settings → Safety → Approvals**, which
  you change yourself. Answer the card for your delete with **Deny** once, then **Allow this session**. **Always
  allow…** empties the cell for good: it saves that pattern, and every chat and scheduled job in the profile then runs
  it without asking.
- **Both "after" cells** stay empty until you turn checkpoints on. The bottom-right cell never fills, whatever you set.

### Checkpoints

A checkpoint is a snapshot of a folder that Hermes takes just before it changes files there. Turn them on in **Settings
→ Safety → Checkpoints**, with **Applies to** set to `academy-practice`.

Once they're on, in a chat:

- `/rollback` lists the snapshots
- `/rollback diff 1` shows what changed since snapshot 1
- `/rollback 1` puts the files back and undoes your last chat turn; changes you made by hand since are kept

`/rollback` lists snapshots for the folder its chat is working in. The mission page's **Working folder** line tests
that: a pass means your practice chats work in the practice folder.

A fail means the app sends chats to a folder you once picked. Copy the practice folder's location from the mission page,
choose it with the practice chat's folder picker, and press **Open practice chat** again; the line checks the new chat.

Hermes skips the very top of your home folder, the top of the drive, folders with more than 50,000 files, and any file
over 10 MB.

## Work it out

How far back can you go? Hermes takes at most one snapshot per folder per turn (one message from you and everything
Hermes does in reply) and keeps the newest 20 for each folder.

Use your own number: the last long session you had with Hermes on real work in one folder, or your longest practice chat
if that's all you have. Count your messages there that ended with a file changed: that's *N*.

- If *N* is 20 or less, every one of those turns could be undone, with checkpoints on.
- If *N* is more than 20, the first *N* − 20 turns are past reach: an afternoon of 32 file-changing turns leaves the
  first 12.

Second limit: look in that folder for any file over 10 MB, like a big export or a video. No snapshot holds it, so
`/rollback` brings back everything around it but not the file.

Write down your *N*, what it leaves out of reach, and the name of any file over 10 MB you'd want back.

## Check yourself

Answer in the box, then show the answer.

**1. Last month you answered "Always allow" to a recursive delete. Tonight a scheduled job tries `rm -r
old-reports`. What happens?**

> It runs. An "always" entry holds everywhere in that profile, even in scheduled jobs, which otherwise refuse risky
> commands.

**2. Checkpoints are on. Hermes deletes an old draft in your project folder with a plain `rm`. Did anything ask first?
Can you get the file back?**

> Usually nothing asked: a single-file delete isn't on the risky-pattern list. But `rm` triggers a snapshot, so
> `/rollback` brings it back.

**3. Checkpoints are on. Hermes posts the wrong message to your team chat through a connector. Can `/rollback` take
it back?**

> No. Checkpoints cover files on this computer; a post, an email, a payment or a cloud-drive delete doesn't come back.
> The only protection is before: an untrusted connector that asks first.

## What people get wrong

- **"Hermes asks before it changes my files."** Approvals watch terminal commands that match a risky pattern. File-tool
  edits never ask, as the try's activity row showed.
- **"`/rollback` undoes whatever Hermes did."** Only file changes in a folder it snapshotted. Sent messages, files over
  10 MB, the top of your home folder and anything before checkpoints were on are all outside it.
- **"I answered 'Always' once, for that one time."** "Always" is saved in the profile and reaches every later chat and
  scheduled job there. "Allow this session" is the one-time answer.

## The judgment: where to put your protection

1. **Fill in the grid before you trust a profile.** Open **Settings → Safety → Approvals** for it and read the **Command
   Allowlist** box, where every "Always" answer is kept. An entry you don't remember adding goes first.
2. **Turn on checkpoints** in every profile that edits files, and work inside a project folder.
3. **Answer approval cards with "Allow this session."** Save "Always" for a command you'd let run at 3 a.m. with nobody
   watching, because that's where it ends up.
4. **Guard the sends before they happen.** For anything nothing can undo (email, posts, payments, cloud deletes),
   mark the connector untrusted so its write tools ask first.
5. **Test each cell you filled.** Make a change, `/rollback` it, then open the file yourself: Hermes saying it's
   restored proves nothing until the file agrees.

Where you keep things you can't afford to lose, the grid has limits no setting fixes; a container, below, is the
stronger wall.

## Also good to know

- **Approval modes.** **Smart**, the default, has a helper model let low-risk commands through, refuse clearly dangerous
  ones, and ask you about the rest. **Manual** asks every time. **Off** asks nothing; it's the same as YOLO mode.
- **YOLO is saved with the chat.** Reopen that chat next week and YOLO is back, so check the status bar before you carry
  on an old chat.
- **Deny rules** are patterns you write, like `"rm -r*"`, quoted, that always block, even under YOLO. A short built-in
  list, the hard floor, blocks things like wiping the whole drive under every setting. Both catch honest mistakes; a
  renamed program or a command wrapped in a script can slip past a pattern.
- **The real wall is a container.** A container keeps the terminal's commands away from the rest of your computer.
  Checkpoints don't work there, and the risky-pattern checks are skipped, but your deny rules still hold.
- **Removing an always-allow entry.** In the **Command Allowlist** box, delete the pattern you want gone (they're
  separated by commas) and click outside the box; the app saves it. As of Hermes 0.22.4 the next command checked goes by
  the new list; older versions needed a restart, and the docs still say so. In a terminal, `hermes config edit` opens
  the same list as `command_allowlist`.
- **The approval card waits 300 seconds.** If nobody answers, the command doesn't run.
- **Restore checkpoint** on a message in the app rewinds the chat to that message and runs it again. It doesn't say it
  restores files, so use `/rollback` for those, and open the file to check.
