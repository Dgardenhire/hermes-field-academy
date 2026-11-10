## What's going on

A helper agent is a second Hermes that your Hermes starts for one task, then reads back from. Hermes does it with a
tool called `delegate_task`. You can ask for one helper, or for a batch: a list of tasks, each to its own helper, all
running at the same time. Three client summaries that would take one chat three long turns take three helpers one
turn.

Think of it as hiring temps for an afternoon. Each temp is quick and capable, and each one arrives knowing nothing
about your office. They don't read the notes pinned up in the back room. They know what's written on the sheet you hand
them, and nothing more.

That sheet is the task. When Hermes starts a helper it writes a goal and, if it chooses, some context: a few lines of
background. The helper starts fresh from those words. It doesn't see your chat. It doesn't load the profile's memory
notes, and it doesn't load context files such as `AGENTS.md` in the folder you're working in. (As of Hermes 0.23.)

In your try, the house rule lived in memory. Your Hermes read it at the start of the chat, so it knew the rule. The
helpers didn't, and nothing in the request told Hermes to pass it on.

### Where helpers show up

Each helper is saved as a chat of its own in the profile's chat records, marked as a helper (`subagent`) and linked to
the chat that started it. (As of Hermes 0.23.) Its own tool calls are there: every file it read and every file it wrote.
That's how Field Academy checks which folder each helper worked in, and it's how you can check too. The parent chat
only shows the summary each helper sent back, and a summary is the helper's own account of what it did.

### The two settings that change what happens

Both live under `delegation` in the profile's `config.yaml`:

- **`max_concurrent_children`** caps how many helpers run at once. Hermes ships it at 10. (As of Hermes 0.23.) A batch
  bigger than the cap isn't trimmed or queued. It's refused whole, with a tool result that starts "Too many tasks:"
  and says the cap. (As of Hermes 0.23.) Hermes may then quietly split the job into smaller calls or do it itself, and
  the reply won't always mention the refusal.
- **`model`** picks the model helpers run on. Left empty, they use the main model. (As of Hermes 0.23.) Set it to a
  cheaper model to save money on simple tasks. Set it to a name the provider doesn't know, and every helper fails on
  its first call.

`delegation.provider` sits beside `model`. Empty means the main provider and its keys. Change the model without
changing
the provider and the new name has to be one your main provider serves.

### What a good task carries

1. **The exact place.** A full folder or file path, never "the client folder." A helper can't ask you which one.
2. **Every rule that applies.** House style, a closing line, a word limit, what to leave alone. If it's in memory or
   `AGENTS.md`, copy it into the task.
3. **What done looks like.** The file to write and where, and what it must contain.
4. **What to leave alone.** "Read only this folder" stops a helper wandering next door.

The list is short because the job is narrow. A helper is good at one task with clear edges.

## Work it out

You ran three helpers in your try. Fill in this table from it.

| | Your main chat | Each helper |
|---|---|---|
| Saw the profile's memory | Yes | Your answer from the try |
| Saw your earlier messages | Yes | No |
| Knew the client folder | From your request | Only if the task named it |

Now the case people get burned by. You ask for helpers on five clients, the cap is set to 4, and Hermes reports
"Done, all five summaries written." How many helpers ran at once, and how would you find out?

> None ran as a batch: five is over the cap of four, so that call was refused. Hermes then did the work some other way.
> To know which way, open the profile's chat records and count the helper chats linked to your request, then look for
> a tool result that starts "Too many tasks:".

## Check yourself

Answer in the box, then show the answer.

**1. You keep a client's style guide in `AGENTS.md` in the project folder. You ask for three helpers to write
drafts. Do the drafts follow the guide?**

> Not unless the request copies the guide into each task. Helpers don't load context files like `AGENTS.md`.

**2. Your helpers keep failing on their first call, and plain chats work fine. What do you check first?**

> `delegation.model` in the profile's config. A name your provider doesn't serve fails every helper while the main
> model works.

**3. Hermes says all four helpers finished. How do you know each one read the right folder?**

> Open each helper's own chat in the records and look at the files its tools read. The summary a helper sends back is
> its own account, not proof.

## What people get wrong

- **"The helpers know what my Hermes knows."** They start with the task text and nothing else: no memory, no context
  files, no chat. Your try showed it.
- **"A big batch just runs slower."** Over the cap, it doesn't run at all as a batch. The refusal sits in a tool result
  you may never see unless you look.
- **"Done means done right."** The parent reports what the helpers said. One helper reading the wrong folder looks the
  same in that report as one that read the right one.

## The judgment: when to hand work to helpers

1. **Split when the parts don't depend on each other.** One summary per client, one check per file, one draft per
   region. If part two needs part one's answer, run them in order in one chat.
2. **Keep it in one chat when the parts are small.** A helper costs about a short chat of its own. Three helpers for
   three one-line answers costs more than asking once.
3. **Write each task for a stranger.** Read it as if you'd never seen the job. If you'd need to ask a question, the
   helper would too, and it can't.
4. **Check what the helpers did.** The report is their own account. Open their chats or their output files. The five minutes it takes is the price
   of trusting the batch.
5. **Use a cheaper helper model on purpose.** Summaries and lookups often run fine on a smaller model. Test one helper
   before you change `delegation.model` for all of them.

## Also good to know

- **Helpers can't use every tool.** They can't ask you a question mid-task, and they can't start helpers of their own
  unless the settings allow it.
- **Each helper gets its own budget.** A helper has its own limit on steps, set by `delegation.max_iterations`, apart
  from the main chat's.
- **The cost shows per chat.** Each helper's tokens are counted on its own chat in the records, so a batch's cost is the
  parent plus every helper.
