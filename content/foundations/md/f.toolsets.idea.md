## What's going on

Hermes does things through tools: read a file, write a file, run a command, search the web, drive a browser. Tools come
in groups called **toolsets**. The `file` toolset holds the four file tools (read, write, patch, search). The
`terminal` toolset holds the terminal and process tools. (As of Hermes 0.23.) Others cover the web, a browser, running
code, images, memory, scheduled jobs and more.

A new profile has nearly all of them on. That's convenient on your own computer, and it's why your try went the way it
did: you asked for a terminal command in a profile whose only job was notes, and Hermes ran it. Hermes uses whatever is
switched on. It doesn't ask what the job is first.

Think of a toolset as a key on a ring. Handing someone the whole ring to water the plants works, until it doesn't.
Giving Hermes only the keys a job needs does two things: a mistake or a bad instruction in a file can't reach the tools
that aren't there, and every chat costs a little less, because each tool's description is sent to the model on every
trip (mission 2).

### Where the switches are

In the app, **Capabilities** has a **Tools** tab. (As of Hermes 0.23.) Set **Configuring:** at the top to the profile
you mean, then switch toolsets on or off. The tab saves the list of what's on in the profile's `config.yaml` as
`platform_toolsets.cli`. (As of Hermes 0.23.) The list is per profile, like everything else in it.

There's a second place: `agent.disabled_toolsets` in the same file. Anything named there is taken off whatever the
Tools tab list says, and the app's chats honour it. (As of Hermes 0.23.) Mission 7 used it to switch off the file and
terminal toolsets so a connector was the only way to the files. A chat gets the Tools tab list minus that one.

### Two other ways a tool comes back

Switching a toolset off removes Hermes's own tools. It doesn't remove:

- **Connectors.** A connector brings its own tools. A filesystem connector pointed at a wide folder can read and change
  everything under it, whatever the `file` toolset says. You met connectors in mission 7: the folder in its settings is
  the whole of its reach.
- **Plugins.** A plugin can add a toolset of its own, and it goes on the same list as the built-in ones. (As of Hermes
  0.23.) Check what each installed plugin adds before you trust a short list.

So the question to answer is "what can a chat in this profile actually do?" You answer it
from three places: the Tools tab, the connectors, and the plugins.

### Test the switch

A switch on a screen is a claim. The proof is a request that should fail, failing. Ask for the thing you took away, in a
new chat after your last change, and see that no tool ran. The chat records keep every tool call, so the proof stays.

## Work it out

Fill in this table from your try and your fix.

| | Before | After |
|---|---|---|
| Toolsets the Tools tab shows on | Your count from the try | Your count now |
| `date` in the terminal | Ran | Your result |
| The job's file tools | On | On |

Now the case people miss. You switch off terminal, code execution, browser and web. A connector called `drive` points
at your whole Documents folder at full trust. Can a chat still delete a file in Documents?

> Yes. The connector's own tools can, and switching toolsets off never touches a connector. Point it at one folder,
> give it an allow list, or make it untrusted (mission 7).

## Check yourself

Answer in the box, then show the answer.

**1. Where does the Tools tab save your choices?**

> In the profile's `config.yaml`, as the list `platform_toolsets.cli`.

**2. The Tools tab shows terminal on, and `agent.disabled_toolsets` names terminal. Can a chat run a command?**

> No. A chat gets the Tools tab list minus anything in `agent.disabled_toolsets`.

**3. You've trimmed the toolsets. What one test tells you it worked?**

> Ask, in a new chat, for something you took away, and see that no tool ran.

## What people get wrong

- **"Fewer tools makes Hermes worse."** Fewer tools the job doesn't use makes it cheaper and safer, and the job doesn't
  notice. Your brief came out the same.
- **"Terminal off means nothing can touch my files."** The file toolset and any connector still can. Decide what the
  job needs to touch, and give it that.
- **"I switched it off, so it's off."** Two lists decide, and plugins and connectors add their own. Test it.

## The judgment: what a job gets

1. **Start from the job.** List what it does, then switch on what those actions need. Not the other way round.
2. **Programs and the web are the big keys.** Terminal, code execution, browser and web reach outside the folder you're
   working in. A job that only reads and writes files needs none of them.
3. **Give risky jobs their own profile.** A client's profile can be trimmed hard while your own keeps everything
   (mission 6).
4. **Check the other doors.** Every connector's folder, every plugin's toolsets.
5. **Test after every change.** One refused request in a new chat.

## Also good to know

- **The list is per profile.** Trimming `academy-practice` changes nothing in your own profile.
- **Changes take hold in a new chat.** A chat keeps the tools it started with (mission 4).
- **From a terminal.** `hermes tools` opens the same choices outside the app, and writes the same list.
