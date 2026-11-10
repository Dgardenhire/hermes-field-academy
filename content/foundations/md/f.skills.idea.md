## What's going on

### Hermes writes skills on its own

You asked in step 3, but Hermes doesn't wait to be asked. Its standing instructions tell it to save a workflow as a skill when it works one out. And after about every ten trips to the model in a chat, it reviews the chat in the background and updates its skills, paying close attention to your corrections. `/refine` runs that review now. (Defaults as of Hermes 0.22.) So skills pile up. The question is whether each gets used.

### The description decides

Picture a cookbook where Hermes reads only the table of contents. That's the skills list you saw in mission 2's Context Usage panel, riding along on every trip: each skill's name and description, one line each. Hermes scans it before replying and opens any skill that fits. It doesn't see the steps until it opens one.

Each description gets 60 characters there. A longer one is cut at the last whole word that fits, and three dots go on the end. Hermes won't save a new line over 60, or an edit that changes the line, but skills from the hub and older skills can still run long.

A line that fits can still miss. Hermes names a job its own way: "volunteer sign-up sheets," "shift rosters." You ask who's "showing up this weekend." When the words don't overlap, Hermes may never open the skill.

When it opens one, the app shows a row: **Loaded skill**, then the name. Typing `/` and the skill's name skips the search: the recipe is pasted into your message, and no **Loaded skill** row appears.

### What's in a skill

A skill is one file, `SKILL.md`: a short header with its `name` and `description`, then the four parts Hermes's own guide recommends: **When to Use**, **Procedure** (the steps), **Pitfalls** (each mistake as a rule with its reason: "Leave out anyone marked maybe; they rarely show") and **Verification** (how to check the result). In the skill's **Edit** box, a heading is a line starting with two number signs and a space, like `## Pitfalls`; the wording is yours. Steps go here and facts go in memory, as mission 3 showed.

## Work it out

**Your try skill.** Count its description, spaces included; it's 60 or under. Underline every word in it you'd actually say. None underlined means step 5 was a coin toss.

**A hand-written skill.** Field Academy wrote `academy-weekly-admin` by hand, the way people write their own. Its description is 137 characters: "Use for the weekly admin routine our team runs after every Monday meeting: turning the notes into action items with owners and due dates." Hermes gets this:

> Use for the weekly admin routine our team runs after...

The cut lands after "after," at character 52. "every" would end at 58, too close to the edge, so it goes too. "Meeting" starts at character 67, "notes" at 88, "action items" at 99. Every word that says what it's for is gone. To see it, ask a fresh practice chat: `Quote each skill description exactly as you see it, character for character.`

## Check yourself

Answer in the box, then show the answer.

**1. You test a new skill by typing its slash command, and the result comes out perfect. What have you proven?**

> Only that the recipe works. You named it, so Hermes never had to find it. The fair test is a new chat where you ask the way you normally would.

**2. A skill reads "Use when compiling volunteer shift rosters." You ask, "Who's working the food drive on Saturday?" Will it load?**

> Probably not. No word overlaps. "Use when asked who's working a shift" would give it a fair chance.

## What people get wrong

- **"Hermes only learns what I tell it to save."** It saves skills on its own, mid-chat and in its background review. To see it, look through **Capabilities → Skills** for skills you never asked for.
- **"Good steps get used."** Hermes picks a skill by its one line before it reads a single step. Your try showed it: same skill, and whether it loaded depended on the words you used.

## The judgment: a line that gets found

Let Hermes write the steps. Write the description yourself, from evidence.

1. **Ask for the job first, the way you normally would,** then copy your words. If you say "the Friday numbers," so does the description, even when "weekly receivables" sounds tidier.
2. **Put the trigger first.** Start with "Use when asked for..." and get the job's name in early.
3. **Count before you save.** Hermes refuses a new or changed line over 60 and says how long it is. A long line you leave alone still saves, so a hub skill keeps its long line until you rewrite it.
4. **Read what Hermes saved.** A skill it wrote on its own is a draft until you've checked the steps and pitfalls.

One skill per job is plenty. If two could match the same request, Hermes may open the wrong one, so sharpen one description or merge them. A two-step chore doesn't need a skill. And take any copy of the steps out of memory: two copies of a procedure drift apart, and Hermes reads both.

## Also good to know

- **Who tidies up.** Hermes's curator puts away skills its own review wrote once nobody uses them: stale at 14 days, archived at 30. Archived means moved aside, never deleted. Skills you asked for in a chat, wrote yourself or installed from the hub are left alone. In a terminal, `hermes curator restore <name>` brings one back and `hermes curator pin <name>` protects it. (As of Hermes 0.22.)
- **Seeing saves before they land.** Type `/skills approval on` in a chat and Hermes stages every skill save instead of making it; `/skills pending` shows what's waiting. A staged skill doesn't exist yet, whatever the reply says.
- **Skills from the hub are scanned.** Each has a trust level: `builtin`, `official`, `trusted` or `community`. In a terminal, `hermes skills inspect <name>` shows what you'd get before installing. `--force` can override a warning, never a `dangerous` verdict.
- **Seeing it over time.** `/journey` in a chat opens a map of what Hermes has learned, skills and memories, with dates.
