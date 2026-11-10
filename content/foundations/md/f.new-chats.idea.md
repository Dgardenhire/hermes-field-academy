## What's going on

When a chat starts, Hermes builds its instructions for the model:

- **`SOUL.md`**, who Hermes is and how it talks
- **memory notes**, `MEMORY.md` and `USER.md`
- **a project file**, such as `AGENTS.md`, if the chat starts in a folder that has one
- **the skills list** and **the tool descriptions**

Then it saves that copy with the chat and sends the same copy on every trip. It doesn't look at the files again. Come back to the chat tomorrow and it still uses the copy it started with.

The reason is mission 2's cache discount, which only holds while the start of the package stays exactly the same. Rereading your files mid-chat would break it.

There's one exception when you reopen an old chat. If its model or its working folder has changed since it started, Hermes rebuilds the copy from your current files.

### Where the rule has to go

`SOUL.md` lives in the profile's own home folder, never in the folder you're working in, so it follows you into every project in that profile. Edit the main profile's `SOUL.md` and a chat in another profile won't change at all.

A project file is different. It loads only when a chat starts in that folder. When `SOUL.md` and a project file disagree, both go to the model, and Hermes doesn't decide between them. The **Rules** line in the Context Usage panel shows when a project file is loaded.

### Chats that never end

Some chats are built to keep going:

- **Messaging apps.** On Telegram, Discord and the rest, one conversation is one chat. As of Hermes 0.22 it doesn't reset after a quiet spell or at midnight, and restarting your computer doesn't start a new one.
- **Bot Chats** in the app, one long chat per bot.
- **The app itself** reopens your last chat when it starts, by default.

So it's easy to live in one chat for weeks without meaning to. That chat never sees your edits, never rereads memory, and carries more conversation on every trip.

### When a long chat catches up

There's one moment a running chat rereads your files: compaction. When a chat gets full, Hermes summarizes the middle to make room, and it rebuilds the instructions from your current files, memory included. On most models that happens at about three quarters full. On models with very large windows (512,000 tokens or more), at half.

## Work it out

When would a chat that never ends pick up your edit? Use the fresh chat from the try.

Click the meter. The top of the Context Usage panel shows two numbers, such as **14K / 128K Tokens**: what this chat uses now, and the model's whole window. Under it, **11% Full** is the first number as a share of the second.

First, check your window. If the second number is under 512K, compaction comes at three quarters full. If it's 512K or more, it comes at half. Say yours reads 14K / 128K:

- compaction at three quarters: 128,000 × 0.75 = 96,000 tokens
- room before compaction: 96,000 − 14,000 = 82,000 tokens

On a 1M window the same 14K chat would compact at 500,000 tokens, with 486,000 to go.

Now, how fast does a chat fill? Your goldfish exchange added only a few hundred tokens. A work chat that reads files adds thousands per exchange. At 600 tokens an exchange, that's about 135 exchanges. At 3,000, about 27. A shop bot answering 20 customers a day catches up in a week, or a day, or a month, depending on what people ask.

Write your own version, with your own window and your own threshold. The answer swings between a day and a month, which is why a new chat is the dependable way to make a change take effect.

## Check yourself

Answer in the box, then show the answer.

**1. You edit `SOUL.md` at 10:00. At 11:00 you reopen a chat you started at 9:00, same model, same folder. Does it follow the edit?**

> No. It reuses the copy it started with. It would catch up at its next compaction, or you can start a new chat.

**2. You save a memory note on Monday. Your Telegram chat has been running since August. When does that chat see the note?**

> At its next compaction, whenever that comes. Send `/new` in Telegram and the next message starts fresh.

**3. You change `SOUL.md` in your main profile. A chat in your `work` profile starts afterward. Does it follow the change?**

> No. Each profile has its own `SOUL.md`. Edit the one in `work`.

## What people get wrong

- **"Restarting gives me a fresh chat."** Quitting the app, rebooting, restarting the messaging connection: none of them starts a new chat. The app reopens your last one, and a Telegram chat picks up where it left off.
- **"Going back to yesterday's chat picks up today's edit."** It sends the copy it started with. To see it, ask the old chat and a new chat the same question after an edit.
- **"One long chat is cheapest because it already knows everything."** Every trip carries the whole conversation, and compaction summaries lose detail. A fresh chat with good memory notes is usually cheaper and sharper.

## The judgment: when to start fresh

Start new chats on purpose, at natural breaks.

1. **After you change `SOUL.md`, memory or a project file.** Otherwise you're testing the old copy.
2. **When a job is finished, or the topic changes.** A new job doesn't need the last one's conversation.
3. **Before you close one out, keep what matters.** Ask Hermes to save anything worth keeping to memory first.

Keep going in the same chat when you're midway through a job and the conversation holds things you'd have to explain again.

When a change "doesn't work," check the setup before you blame the model:

- Did you edit the right profile's `SOUL.md`?
- Is a project file in the folder saying the opposite? Look at the **Rules** line.
- Did you test in a chat that started after the edit?

An old chat can only show you the old instructions, so a test there tells you nothing about the edit. And if a change has to be live by a certain day, start the new chat yourself; compaction keeps no schedule.

## Also good to know

- **New chats in the app.** `Cmd+N` on a Mac or `Ctrl+N` on Windows and Linux starts a new chat in the profile the app is using.
- **Going back to an old chat.** `/resume` in the app or a terminal. In a terminal, `hermes -c` continues your most recent chat and `hermes sessions list` shows them all.
- **Which files loaded.** In a terminal or a messaging app, `/context` lists each project file and whether it loaded.
- **A quick change for one chat.** `/personality` changes the tone for the current chat only, without touching `SOUL.md`.
- **The messaging reset.** `/new`, or its other name `/reset`, starts a fresh chat on Telegram and the other apps.
