## What's going on

A **token** is a chunk of text, about three quarters of a word. Models charge by the token, both for what they read and what they write.

The model behind Hermes remembers nothing from one moment to the next. Every time Hermes asks it something, Hermes sends a whole package: everything the model needs to know to answer. In the last mission you saw that one message from you can mean several trips around the loop. **Every trip resends the package.**

The package has two parts:

**The part that's the same every trip.** It goes first, before anything you've said:

- **Instructions:** Hermes's own guidance, plus your profile's `SOUL.md`. The panel calls this **System prompt**.
- **Tool descriptions:** a description of every tool that's switched on, so the model knows what it can call. The panel line is **Tool definitions**.
- **Connectors:** each connected service adds its own tools. Hermes calls these MCP servers, and so does the panel's **MCP** line. This course calls them connectors.
- **The skills list:** the name and a short description of each installed skill. The panel line is **Skills**.
- **Memory:** your `MEMORY.md` and `USER.md` notes.
- **Project file:** an `AGENTS.md` or similar file, if the chat is working in a folder that has one. The panel shows it as **Rules**.

**The conversation.** Everything said and done in this chat so far, growing with every trip.

Your hello was tiny. The total you wrote down is mostly the first part. That's the cost of having Hermes set up the way it is, and you pay it on every trip, in every chat.

### There's a discount, with a catch

Most model providers remember the start of a package they've just seen and charge much less for it the next time, often a small fraction of the full price. That's called the cache. Because the fixed part always comes first, it usually gets the discount after the first trip.

The catch: the discount only works while the start stays exactly the same. Change anything in the fixed part and the next trip pays full price again. Switching tools on or off counts, and so does switching models.

## Work it out

Use your own number from the hello.

Say your fixed part was 15,000 tokens. A small job that takes eight trips around the loop sends that block eight times: 120,000 tokens before a word of the conversation. With the cache, most of those trips are discounted. Without it, a chat whose start keeps changing pays the full 120,000.

Now say a quarter of the fixed part is descriptions of tools this job never touches. That's 30,000 tokens on that one job, and the same again on every job after it, sent so the model can know about tools it won't use.

Write down your own version: your fixed part, multiplied by eight trips.

## Check yourself

Answer in the box, then show the answer.

**1. You connect a service with 14 tools and never use any of them. Does it cost you anything?**

> Yes. Its tool descriptions ride in the fixed part on every trip of every chat in that profile, whether the model uses them or not.

**2. You switch a toolset off in the middle of a long chat. Will that chat get cheaper right away?**

> Not reliably. The running chat was built with the old set of tools. Changes to tools reach a chat when it starts, or when Hermes compacts a long one. Changing what goes first also breaks the cache discount for the next trip. Make the change, then start a new chat.

**3. Your chats this week add up to well under your bill. Where did the rest go?**

> Look at the other models Hermes runs: the side jobs that name chats, summarize full ones, review turns and judge risky commands, plus any helper agents. Each uses your main model unless you set another, and each trip is billed. **Settings → Model** shows them all for a profile.

## What people get wrong

- **"Tools I don't use are free."** Their descriptions are sent every trip. Unused tools cost money in every chat.
- **"Hermes only sends my message."** It sends the whole package, every trip. Your message is often the smallest part.
- **"A cheaper model always saves money."** Switching models in the middle of a long chat makes the next message reread the whole conversation at full price, because the cache belongs to the old model. As of Hermes 0.22, Hermes asks you to confirm a switch once a chat passes 100,000 tokens. Change models when you start a new chat.

## The judgment: what to cut

Cutting blind is how people break their own setup. Cut from what the record shows.

1. **Look at what the job actually used.** In the chat where you ran the job, look at the activity rows: every tool Hermes called is listed. That's what this job needs.
2. **Find the big pieces.** In the Context Usage panel, see which line is largest. It's usually **Tool definitions** or **MCP**.
3. **Cut what this job never touches.** Usual candidates: - toolsets for things the profile isn't for, like a web browser in a bookkeeping profile - connectors added once for a test and forgotten - skills installed for a kind of work this profile doesn't do - a long project file (`AGENTS.md`) in the working folder, if the **Rules** line is big and the job doesn't need most of what it says. You trim it by hand: open the file in a plain text editor (Notepad on Windows, TextEdit on Mac, any plain editor on Linux), delete the block the job doesn't need, and save.
4. **Keep what the job used, even if the name sounds unimportant.** If the job reads and writes files, the file tools stay.
5. **Remember the profile's other jobs.** Keep anything the profile needs on any day of the week. If two jobs need very different tools, they belong in two profiles. That comes in mission 6.

**Where the switches are.** Open **Capabilities** in the sidebar and pick a tab. Just under the tabs, a row labeled **Configuring:** has a profile picker; choose `academy-practice`. The app stays in your own profile. Then:

- **Skills** tab: each skill has a switch.
- **Tools** tab: each toolset has a switch.
- **Connectors** tab: each connector has a switch to turn it off.

Then press **Open practice chat** for a new chat and measure again.

**Count every model, including the ones working out of sight.** Hermes also runs side jobs on a model: naming the chat, summarizing a chat that's full, a review that may save notes, and judging whether a risky-looking command is safe. Helper agents are another. Each one uses your main model unless you set another, and every trip they make is billed. When the bill is higher than your chats explain, look there next.

## Also good to know

- **Long chats get compacted.** When a chat nears the edge of its window, Hermes summarizes the middle to make room. More on that in mission 4.
- **Dollars over time.** In a terminal, `hermes insights` shows tokens and estimated cost across days.
- **Helper agents at work.** While they're running, a **Subagents** box appears above the message box with how many are working.
- **Measuring without a chat.** In a terminal, `hermes prompt-size` measures the fixed part and breaks it down, without calling a model.
