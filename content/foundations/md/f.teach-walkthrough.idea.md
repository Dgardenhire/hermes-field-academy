## What's going on

A walkthrough is the set of steps someone follows to do a job with Hermes when you're not there. It has one reader, and
that reader can't ask you anything. Every word in it has to be true on their screen, in their profile, today.

Your try showed how easily that slips. The draft read fine. Followed word for word, it pointed at something the
profile doesn't have, or it said something that would leave them less safe. The colleague who wrote it wasn't careless.
They wrote from memory, and memory rounds things off: "the orders skill" instead of its real name, "the folder"
instead of which one.

Think of it as directions to your house for someone who's never been. "Turn left at the old garage" is fine for you.
For them, the garage closed in 2019.

### What every step needs

1. **Exact names, copied from the screen.** A skill's name is the one at the top of its `SKILL.md`, and it's the
   name the **Skills** tab shows. (As of Hermes 0.23.) If a step names a skill, copy that name. A near miss is a skill
   that doesn't exist.
2. **One action per step.** "Open a new chat and type this" is two things that can go wrong separately. Number them.
3. **Words they'll type, in full.** If they're meant to type something, put it in the walkthrough exactly, so they can
   copy it.
4. **No step that switches a safeguard off.** Approvals, toolsets, connectors: a walkthrough is the wrong place to loosen
   them. If permission cards come up, say what to do with one: read what Hermes wants to do, and say yes only if it
   matches the job.
5. **A last step that checks the result.** Where the output lands, by name, and what they look for. Without it, "done"
   means Hermes said so.

### Read it against the profile

Before you trust any walkthrough, yours or someone else's, hold it up against the profile it's for:

- Every skill it names: is it on the **Skills** tab, spelled exactly?
- Every file it names: does that file exist, in the folder it says?
- Every setting it mentions: is that what the settings say now?
- Every step that changes something: is that change one you'd want them to make alone?

### Follow it yourself

The test is to follow it once, word for word, in a new chat, as if you'd never seen the job. Type only what it says to
type. Look only where it says to look. When a step doesn't work as written, the step is wrong, even if you could make
it work. Fix the step and follow it again from the top.

## Work it out

Read the colleague's draft against what you found in the profile.

| Line in the draft | True in the profile? | What you'd write |
|---|---|---|
| The skill named in step 2 | Your answer | The exact name from the Skills tab |
| Where the result lands | Your answer | The file and folder, by name |
| What to do with a permission card | Your answer | Read it; yes only if it matches the job |

Now the common one. A walkthrough worked in March. In May, someone renamed the skill to make the list tidier. What
happens to the person following it, and what would have warned them?

> Hermes can't find the skill and either says so or tries to do the job some other way. A last step that checks the
> result tells them something went wrong, even if the error didn't.

## Check yourself

Answer in the box, then show the answer.

**1. Where do you get a skill's name for a walkthrough?**

> From the profile's **Skills** tab, which shows the name in its `SKILL.md`. Copy it; don't type it from memory.

**2. A draft says: "If Hermes keeps asking permission, switch approvals off." What do you do with that line?**

> Take it out, and say what to do with a permission card instead.

**3. How do you know a walkthrough works?**

> Follow it once yourself, word for word, in a new chat, and check the result the way its last step says.

## What people get wrong

- **"I know this job, so I can write it down."** Knowing it is why you skip steps. Copy names from the screen.
- **"Short is kind."** Short and vague isn't. "Use the usual skill" is three words nobody new can follow.
- **"It worked when I did it."** You did it with everything in your head. Follow it as if you didn't know.

## The judgment: what a good walkthrough leaves out

1. **Leave out what they can't see.** Your shortcuts, your other profiles, your terminal.
2. **Leave out every loosened safeguard.** Smooth by being less safe is the wrong trade.
3. **Leave out the why, mostly.** One line of reason helps; a paragraph buries the step.
4. **Keep the check.** It's the one step you can't leave out.
5. **Date it.** Write the day you last followed it at the top, so the next reader knows how fresh it is.

## Also good to know

- **Keep it next to the work.** A walkthrough in the practice folder is found by the person who needs it.
- **Update it when the profile changes.** Rename a skill, change a folder, and the walkthrough is wrong until you fix it.
