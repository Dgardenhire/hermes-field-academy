## What's going on

Hermes's long-term memory is two small text files in the profile's `memories` folder:

- **`MEMORY.md`** holds Hermes's notes about your setup and how the work goes.
- **`USER.md`** holds notes about you: your role, your preferences, how you like answers.

Both are short on purpose. `MEMORY.md` holds at most 2,200 characters and `USER.md` 1,375. Together that's about a typed page. Hermes reads both files when a chat starts and puts them in the package it sends on every trip. Anything it said that isn't in the file came from the chat itself, or it was filling a gap.

### Three other things that feel like memory

- **Past chats.** Every chat is kept, and Hermes can search old ones when it needs something. Nothing from them loads on its own. As of Hermes 0.22.4, old chats stay until you choose to clear them.
- **Skills.** Saved step-by-step procedures. Mission 5 covers them.
- **Project files.** Instructions in the folder you're working in. Mission 4 covers them.

A simple rule sorts most cases. A fact goes in memory. A procedure goes in a skill. Anything long goes in a file.

### A save is a change to the file

Hermes saves a note by calling its memory tool. That's the only way. Saying "Got it, I'll remember" saves nothing. Here's the evidence you can collect, weakest first:

1. **Hermes's words.** "Saved."
2. **The row's title.** A row titled **Saved to memory**.
3. **What the row brought back.** Expand it. A real save shows how full memory is now, like `29% — 640/2,200 chars`.
4. **The file.** The line is there when you press **Show memory file**.
5. **A new chat.** Hermes uses the fact without being told.

The first two prove nothing on their own. A row titled **Saved to memory** isn't enough: as of Hermes 0.22.4, a save that's waiting for your approval still gets that title and a check mark, because the tool reported success. Expand it and it says the save was staged and isn't saved yet.

### Why the test needs a new chat

The chat where you saved the fact already has it in the conversation, so asking there proves nothing. And each chat reads memory once, when it starts. Saving a note changes the file right away, but no chat that's already open will see it. Mission 4 goes deeper.

### When memory is full

Hermes doesn't refuse. Its first try comes back over the limit, and then it makes room itself, cutting or shortening other notes in the same step, and saves yours. You get your fact. You may lose one you needed.

## Work it out

Use your own number from the Memory line.

Hermes estimates about 2.75 characters per token, so a full `MEMORY.md` is roughly 800 tokens. Your practice profile has no notes about you yet, so the Memory line is nearly all `MEMORY.md`. A one-line note of about 120 characters is roughly 45 tokens.

Say your Memory line showed 260 tokens. Room left: 800 − 260 = 540 tokens. That's about 12 more one-line notes. If your line showed 780, there's room for none, and your next save will cost an older note.

And remember mission 2: those tokens ride along on every trip of every chat. A job with eight trips sends your 260 tokens eight times.

Write your own version: your Memory tokens, the room left, and how many notes fit.

## Check yourself

Answer in the box, then show the answer.

**1. You save a fact in one chat. Another chat has been open since this morning. Does it know the fact?**

> No. It read memory when it started, before the save. A new chat will know it.

**2. The memory row says Saved to memory, with a check mark. Is the fact saved?**

> Not proven. A save waiting for approval looks the same. Expand the row, then look at the file itself.

**3. Where does each go: "Harbor Bakery uses QuickBooks Online," "every Friday, export the bank feed, reconcile, then email the owner," and a 40-page style guide?**

> Memory, a skill, and a file. The first is a fact. The second is a procedure. The third is far too long for a note.

## What people get wrong

- **"It said it saved it."** Small or weak models often write the confirmation without calling the tool. To see it, look for the memory row, expand it, and look at the file.
- **"It knows the fact in this chat, so memory works."** It knows because you just told it. The only fair test is a new chat where you don't mention it.
- **"Memory only holds what I asked it to save."** By default Hermes saves on its own. It saves preferences and corrections as it learns them, and a review that runs after a turn can add notes too. Read the file now and then to see what's there.

## The judgment: what earns a line

Memory is tiny, and you pay for every line on every trip. A line has to earn that.

1. **Save what most chats in this profile need.** A client's software, a deadline that never moves, a standing preference. Skip what one job needs once.
2. **Keep it short and specific.** "Harbor Bakery uses QuickBooks Online; other five clients use Xero" beats a paragraph about the clients.
3. **Skip what Hermes can look up.** If it's in a file Hermes can read, point to the file instead.
4. **Watch what a full memory cuts.** When Hermes makes room, read what it removed or shortened. If it dropped something you need, put it back and cut something else yourself.
5. **Turn on approvals for shared or client profiles.** With approvals on, nothing enters memory until you say yes.

One fact, one line, proven by the file and a new chat, is enough. You don't need to test it three ways.

Passwords, keys and account numbers go in Hermes's settings for keys, where they stay out of the package. Anything in memory is sent to the model on every trip of every chat.

## Also good to know

- **Where the files live.** For the practice profile, the mission page shows the full path under **Show memory file**, if you'd rather open it in a text editor yourself. For your main profile, `~/.hermes/memories/` on Mac and Linux, or `%LOCALAPPDATA%\hermes\memories\` on Windows. For a profile named `work`, `~/.hermes/profiles/work/memories/`.
- **Approvals.** Type `/memory approval on` in a chat to require approval, and `/memory pending` to see saves waiting for a yes.
- **The Memory Graph.** Type `/journey` in an app chat to see saved notes and skills over time.
- **Careful with Reset.** The app's Command Center shows the size of each memory file, with a button that deletes it. There's no undo.
