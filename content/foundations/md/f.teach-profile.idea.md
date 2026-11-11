## What's going on

Setting Hermes up for someone else is a different job from using it yourself. You know what you meant last Tuesday.
They don't, and neither will the next chat. Everything their Hermes must know has to live somewhere a new chat reads,
because a new chat is all they'll ever see.

Your try showed the gap. You told Hermes the rule in a chat, it said it would keep it, and a fresh chat had never heard
of it. Nothing was broken. A chat holds what's said in it until it ends, and then it's gone. The person will start a
new chat every morning.

Think of it as setting up a desk for someone starting on Monday. You can't stand behind them all week. What they need
goes in the drawer, on the wall, in the notebook on the desk, where they'll find it without asking you.

### Three places that last

Hermes reads three things at the start of every chat in a profile, and each has a job:

- **SOUL.md** says who Hermes is and how it behaves: who it works for, the rules it keeps, how it speaks. In the app,
  right-click the profile's square and choose **Edit SOUL.md…**. (As of Hermes 0.23.) A rule that must hold every
  time belongs here, in the person's own words where you can.
- **Memory** holds facts: short lines Hermes reads at the start of each chat (mission 3). "The shop closes at 5 on
  Saturdays" is a fact. Ask Hermes to remember it, then read the memory file to see the line is really there.
- **The settings** decide what Hermes can do: approvals, toolsets, connectors. These aren't words Hermes reads. They're
  limits it can't talk its way past.

Put each thing in one place. A rule in SOUL.md and again in memory is two copies that will drift apart.

### What they asked you to keep away

People who are new to Hermes often say some version of "I don't want it doing things on its own." Take that
literally:

1. **Approvals on.** When Hermes wants to run something risky, it asks first (mission 9). Open **Settings → Safety →
   Approvals** and read the mode yourself. Smart or Manual is right; if you find Off, change it there yourself. Field
   Academy only reads this setting and never changes it.
2. **Programs off, if they asked.** In **Capabilities**, **Tools**, switch off what runs programs: terminal and code
   execution, and the browser and web unless the job needs them. The Tools tab saves the list in the profile's
   settings. (As of Hermes 0.23.)
3. **Connectors only where the job is.** A connector that reaches more than the job's folder gives back what you
   switched off (f.toolsets). A connector left at full trust acts without asking, because approvals watch terminal
   commands, not connector tools (mission 9); mark it untrusted, or switch it off.

### Prove it as them

The proof is a brand-new chat, opened the way they'll open it, asked something only their Hermes would know, with no
hints from you. "Who do you work for, and what should you never do?" If the answer names them and their rule, the
setup works without you. If it doesn't, nothing you said in earlier chats counts.

## Work it out

Sort each line of a brief into its place.

| From the brief | Where it goes |
|---|---|
| Their name and their work | SOUL.md |
| "Never email a customer without asking me" | SOUL.md |
| "The shop closes at 5 on Saturdays" | Memory |
| "I don't want it running programs" | Settings: the Tools tab |

Now the case that catches people. You did all four. A week later Hermes runs a cleanup command and a file is gone.
What do you check first?

> Approvals. If they were off, nothing asked before the command ran. Then the Tools tab, in case the terminal toolset
> came back on, then every connector's folder.

## Check yourself

Answer in the box, then show the answer.

**1. You typed someone's rule into a chat and Hermes agreed to keep it. Will tomorrow's chat keep it?**

> No. A new chat starts from SOUL.md, memory and the settings. What was said in an old chat isn't read.

**2. Where does "Never promise a delivery time" go, and where does "Orders close at 3" go?**

> The rule goes in SOUL.md; the fact goes in memory.

**3. How do you know the setup works without you?**

> Open a new chat, don't name them, and ask who it works for and what it should never do.

## What people get wrong

- **"I told it, so it knows."** Telling a chat lasts as long as the chat. Your try showed it.
- **"More instructions make it safer."** A long SOUL.md is hard for you to check and easy to contradict. Keep the
  rules that matter, in their words.
- **"It's their profile, so their settings are fine."** Check approvals and toolsets yourself. Someone may have changed
  them before you arrived.

## The judgment: what you set up, and what you leave to them

1. **Set up what must hold every time.** Who it works for, the rules, the facts, the limits.
2. **Leave what they'll learn by doing.** Skills grow from jobs they repeat (mission 5). Don't guess them in advance.
3. **Use their words for their rules.** They'll recognise them when Hermes quotes them back.
4. **Test it as a stranger.** The first chat after setup is the handover.
5. **Write down what you changed.** The next mission turns that into a walkthrough.

## Also good to know

- **A profile per person.** Their Hermes gets its own profile, so their memory and yours never mix (mission 6).
- **Changes take hold in a new chat.** A chat already open keeps the SOUL.md it started with (mission 4).
