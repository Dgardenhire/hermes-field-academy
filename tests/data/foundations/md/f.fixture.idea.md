# Four places Hermes keeps what it knows

When people say Hermes remembers something, they can mean four different things. Each one is stored in a different
place and reached a different way, and most memory trouble comes from mixing them up.

**Memory notes.** Two small text files in the profile's `memories` folder: `MEMORY.md` holds Hermes's own notes about
your setup and how you work, and `USER.md` holds facts about you. For the main profile the folder is
`~/.hermes/memories/`; for a profile named `work` it is `~/.hermes/profiles/work/memories/`. Both files are small on
purpose. `MEMORY.md` holds 2,200 characters, about a dozen short lines, and `USER.md` holds 1,375. Hermes reads both at
the start of every chat and puts them in its instructions.

**Past chats.** Every conversation is saved, and Hermes can search old ones when it needs to. Nothing from them is
loaded on its own. As of Hermes 0.22.4 old chats are kept until you choose to clear them.

**Skills.** Step-by-step procedures saved as files. Hermes sees a skill's name and short description, and reads the
whole thing only when it decides it needs it.

**Project files.** Files such as `AGENTS.md` in the folder you are working in, read at the start of a chat there.

A simple rule sorts most cases. A fact goes in memory: invoices go out on the first of the month. A procedure goes in
a skill: how to build the monthly invoice. Anything long goes in a file.

## A reply that says Saved proves nothing on its own

Hermes may answer "Got it, I'll remember." A fact is saved only when Hermes used its memory tool. You can see that in
two places: the tool shows in the activity while Hermes works, and the line appears in the memory file. Small models
are the most likely to say they saved something when the tool never ran.

## Why a new fact does not show up right away

Hermes reads the memory files once, when a chat starts, and keeps that copy for the whole chat. A fact saved in the
middle of a chat goes into the file at once, yet that same chat keeps working from its old copy. The next new chat
reads it. So the fair test of memory is a new chat: type `/new`, or start one from the app.

This catches people out on Telegram and other messaging apps, where one conversation can run for weeks. Starting a new
chat now and then is how new memories get read in.

## Three ways a save can fail quietly

Memory can be full, and then Hermes gets an error instead of saving. Saves can be set to wait for approval, and then
they sit in a queue that `/memory pending` shows. And each profile has its own memory, so a fact saved in one profile
is missing from another.

## More on how memory works

or weak models often write the confirmation without calling the tool. To see it, look for the memory row, expand it, and look at the file. - **"It knows the fact in this chat, so memory works."** It knows because you just told it. The only fair test is a new chat where you don't mention it. - **"Memory only holds what I asked it to save."** By default Hermes saves on its own. It saves preferences and corrections as it learns them, and a review that runs after a turn can add notes too. Read the file now and then to see what's there. ## The judgment: what earns a line Memory is tiny, and you pay for every line on every trip. A line has to earn that. 1. **Save what most chats in this profile need.** A client's software, a deadline that never moves, a standing preference. Skip what one job needs once. 2. **Keep it short and specific.** "Harbor Bakery uses QuickBooks Online; other five clients use Xero" beats a paragraph about the clients. 3. **Skip what Hermes can look up.** If it's in a file Hermes can read, point to the file instead. 4. **Watch what a full memory cuts.** When Hermes makes room, read what it removed or shortened. If it dropped something you need, put it back and cut something else yourself. 5. **Turn on approvals for shared or client profiles.** With approvals on, nothing enters memory until you say yes. One fact, one line, proven by the file and a new chat, is enough. You don't need to test it three ways. Passwords, keys and account numbers go in Hermes's settings for keys, where they stay out of the package. Anything in memory is sent to the model on every trip of every chat. ## Also good to know - **Where the files live.** For the practice profile, the mission page shows the full path under **Show memory file**, if you'd rather open it in a text editor yourself. For your main profile, `~/.hermes/memories/` on Mac and Linux, or `%LOCALAPPDATA%\hermes\memories\` on Windows. For a profile named `work`, `~/.hermes/profiles/work/memories/`. - **Approvals.** Type `/memory approval on` in a chat to require approval, and `/memory pending` to see saves waiting for a yes. - **The Memory Graph.** Type `/journey` in an app chat to see saved notes and skills over time. - **Careful with Reset.** The app's Command Center shows the size of each memory file, with a button that deletes it. There's no undo.
