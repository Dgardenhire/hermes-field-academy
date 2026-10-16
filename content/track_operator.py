"""Operator path content. Format: docs/content-format.md.

operator.runtime is the model for a mission whose check reads the live app.
"""

MISSIONS = {
    "operator.runtime": {
        "minutes": {"lesson": 3, "example": 3, "complete": 4, "lab": 5, "explain": 5, "gate": 2},
        "use": (
            "You said you want Hermes to do this for you: {goal}. Work like that runs in the background, "
            "so you need to know which computer and which profile it lives on."
        ),
        "use_plain": (
            "Anything you ask Hermes to do in the background runs on one computer, under one profile. "
            "This mission shows you which."
        ),
        "lab": {
            "body": (
                "1. Open Gateways in Settings and read the connection marked Current.\n"
                "2. Read your profile name. With several profiles, the sidebar's profile rail shows "
                "it. With one, it is called default.\n"
                "3. Write both down for the check."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "Four parts that all get called Hermes",
            "lines": [
                "The app is the window you type in. On this computer it also runs Hermes, so quitting it stops background work unless a gateway runs on its own.",
                "A gateway is the background program. It runs scheduled jobs and answers your phone whether or not the app is open.",
                "Every job belongs to one profile, on one computer. Gateways in Settings shows you which computer.",
            ],
            "picture": "four-parts",
        },
        "worked": {
            "title": "What happened to Dana's Monday summary",
            "intro": (
                "Dana runs a bookkeeping office. Every Monday at 7, Hermes emails her a summary of the week's invoices. "
                "One Monday it never came. Her Hermes app had been open on her screen all weekend, connected to the "
                "office computer in the back room."
            ),
            "parts": [
                {
                    "label": "She ignored the open window",
                    "text": "The app being open told her nothing. The window is only where she types.",
                },
                {
                    "label": "She checked the gateway first",
                    "text": "Her jobs run through the gateway, the program in the background on the office computer. It had stopped when that computer restarted for an update.",
                },
                {
                    "label": "She found the profile",
                    "text": "In Settings, under Gateways, the connection marked Current was the office computer. The sidebar showed her profile: bookkeeping.",
                },
                {
                    "label": "She wrote it down",
                    "text": "Her note: Profile: bookkeeping. Connection: another computer, the office one. The summary needs the gateway on the office computer running.",
                },
            ],
        },
        "complete": {
            "title": "Your turn: Marcus's Friday report",
            "intro": (
                "Marcus runs a landscaping crew, and his Friday photo report didn't arrive. Fill in the two blanks "
                "the way Dana worked it out, then compare with our answers."
            ),
            "parts": [
                {"text": "Symptom: the Friday photo report didn't arrive, and the app was open all week.\nPart to check first: "},
                {
                    "gap": "first",
                    "prompt": "Which part runs scheduled jobs? Name it and say why you check it first.",
                    "answer": "The gateway, because it is the background program that runs scheduled jobs whether or not the window is open.",
                    "min_words": 6,
                },
                {
                    "text": (
                        "\nWhere to look: Gateways in Settings for the connection, and the sidebar for the profile. "
                        "His profile is crew and the connection is another computer over SSH.\nThe note: "
                    ),
                },
                {
                    "gap": "note",
                    "prompt": "Write the note in one or two sentences: the profile, the connection, and what has to be running.",
                    "answer": "Profile: crew. Connection: another computer. The crew profile's gateway has to be running on that computer.",
                    "min_words": 8,
                },
            ],
        },
        "coach": [
            {
                "hint": "Ask what an open window can show you. It shows the app on your screen. Does it show a program that runs on its own?",
                "example": "Example: Dana's window was open all weekend and the report still never came. The window and the job are separate things.",
            },
            {
                "hint": "Name the background program that runs scheduled jobs and answers your phone messages.",
                "example": "Example: Marcus checks the gateway first, because a stopped gateway starts no scheduled job while the app looks fine. When it starts again, it runs the missed job once, late, however many times it was missed.",
            },
            {
                "hint": "Think about which setup the job was created in. Memory, skills and passwords belong to one profile.",
                "example": "Example: a job made under the work profile can't use a skill that only exists under the home profile.",
            },
            {
                "hint": "Name one place you could look to be sure, rather than guessing. Gateways in Settings shows the connection, and the sidebar shows the profile.",
                "example": "Example: Dana opens Gateways, reads that the connection is the office computer and that her profile is bookkeeping, then looks at that profile's scheduled jobs.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "Hermes runs on a laptop that goes to sleep every night. The 6 a.m. job didn't run. "
                    "Say why, and what you would change."
                ),
                "points": [
                    {
                        "point": "that a sleeping computer runs nothing, so the gateway on it can't run the job",
                        "hint": "Think about what the laptop is doing at 6 a.m.",
                        "example": "Example: the gateway lives on that laptop. While the laptop sleeps, no scheduled job starts. When it wakes, the 6 a.m. job runs once, late.",
                    },
                    {
                        "point": "a change: move the job to a computer that stays on, or set the job for a time the laptop is awake",
                        "hint": "You can change where it runs or when it runs.",
                        "example": "Example: move the gateway to an office computer that never sleeps, or schedule the job for 9 a.m., when the laptop is open.",
                    },
                    {
                        "point": "how you would confirm it, by reading the connection in Gateways rather than guessing",
                        "hint": "Name the place in Settings that shows which computer Hermes runs on.",
                        "example": "Example: open Gateways in Settings and read which connection is marked Current.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "A coworker keeps two profiles, work and home. A job she set up under work isn't running. "
                    "Say what you check, in order."
                ),
                "points": [
                    {
                        "point": "that a job belongs to one profile, so you look at the work profile's jobs, because the home profile keeps its own list",
                        "hint": "Ask which profile the job was created under.",
                        "example": "Example: open the work profile and look for the job there. The home profile has its own list.",
                    },
                    {
                        "point": "that the gateway serving that profile has to be running",
                        "hint": "Which background program runs scheduled jobs?",
                        "example": "Example: check that the Gateway item in the status bar says Connected. A stopped gateway starts no job under that profile until it runs again.",
                    },
                    {
                        "point": "that each profile has its own memory, skills and passwords, so the job may be missing something the other profile has",
                        "hint": "Think about what a job needs that lives inside a profile.",
                        "example": "Example: the job needs a password that was saved under home, so it fails under work.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "A teammate says, \"Hermes is running, I can see the window.\" "
                    "Say what that tells you about tonight's scheduled report."
                ),
                "points": [
                    {
                        "point": "that the window shows the app, and says nothing about whether scheduled work will run",
                        "hint": "Separate what you can see from what runs on its own.",
                        "example": "Example: the app can be open on a screen while the background program behind it has stopped.",
                    },
                    {
                        "point": "that the report depends on the gateway, so you would check the gateway",
                        "hint": "Name the program that runs jobs while you are away from the screen.",
                        "example": "Example: before tonight, check that the Gateway item in the status bar says Connected.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check where your Hermes runs",
            "body": (
                "Type the profile name and the connection you wrote down, then click Check my work. "
                "It passes when your answers match what Hermes reports."
            ),
            "verify": "desktop",
            "check": "runtime",
            "inputs": [
                {"id": "profile", "label": "Profile name", "placeholder": "Copy it as the sidebar shows it, or type default"},
                {"id": "connection", "label": "Where that profile runs", "options": ["This computer", "Another computer", "Hermes Cloud"]},
            ],
            "proof": "Hermes answers, this window is connected, and the profile and connection you wrote down match what Hermes reports.",
            "fixes": {
                "not_connected": {
                    "hint": "Click Gateway in the status bar at the bottom of the window. If it doesn't say Connected, choose Reconnect gateway.",
                    "example": "Example: once the Gateway item says Connected, run the check again.",
                },
                "no_answer": {
                    "hint": "Hermes didn't answer the check. Choose Reconnect gateway from the Gateway item in the status bar, wait for it to say Connected, and try again.",
                    "example": "Example: a gateway that was asleep can take a few seconds to answer after you reconnect.",
                },
                "missing_profile": {
                    "hint": "Type your profile's name. With one profile it is called default, and with more, the sidebar's profile rail shows the one you are on. If you gave the default profile a display name, still type default.",
                    "example": "Example: Dana's sidebar showed bookkeeping, so she typed bookkeeping.",
                },
                "profile_mismatch": {
                    "hint": "Compare your answer with the profile the sidebar shows. Spelling counts, so copy it exactly.",
                    "example": "Example: if the sidebar shows work, typing Work or office won't match. Type work.",
                },
                "connection_mismatch": {
                    "hint": "Read the kind again in Gateways: Local is this computer, Remote gateway or SSH is another computer, and Hermes Cloud is Hermes Cloud.",
                    "example": "Example: a connection whose kind reads SSH is another computer, and a hosted one reads Hermes Cloud.",
                },
            },
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now asks for the profile name and the connection you read in Gateways, and compares "
                    "them with what Hermes reports. It used to pass whenever Hermes answered."
                ),
            }
        ],
    },
    "operator.desktop": {
        "minutes": {"lesson": 3, "example": 3, "complete": 4, "lab": 8, "explain": 5, "gate": 2},
        "use": (
            "You said you want Hermes to do this for you: {goal}. That work spreads across chats, panes and "
            "folders, so you need to know which pieces keep running, which are saved, and which disappear when you close the window."
        ),
        "use_plain": (
            "Your Hermes work spreads across chats, panes and projects. This mission shows you which pieces "
            "keep running, which are saved, and which disappear when you close the window."
        ),
        "lab": {
            "body": (
                "Send the practice chat below. It walks you through one small real task:\n"
                "1. Start a project.\n"
                "2. Run a terminal command.\n"
                "3. Preview a file.\n"
                "4. Keep what you made.\n"
                "\n"
                "Write down where each piece is saved."
            ),
            "prompt": (
                "[FA-DESKTOP] Walk me through one small real task in the Hermes app, one step at a time: start a project, "
                "run one terminal command, preview a file, and keep what I made. After each step, tell me where that piece "
                "is saved and what happens to it if I close the window."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "What happens when you close something",
            "lines": [
                "Hiding a pane tucks it away, and whatever runs inside it keeps running.",
                "Closing its tab with the x stops it, and anything that lived only in the window is gone.",
                "Sessions are saved and come back after a restart, grouped in a project when they share a folder.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "Where Elena's price list work ended up",
            "intro": (
                "Elena Okafor runs a dog grooming shop and wanted her price list in one tidy file. She did one small "
                "task in the app, then wrote down where each piece ended up."
            ),
            "parts": [
                {
                    "label": "She started a project in her Prices folder",
                    "text": "A project groups every session that works in the same folder, so her later chats about prices landed beside this one.",
                },
                {
                    "label": "She hid the terminal while it worked",
                    "text": "She ran a command that listed the folder's files, then hid the terminal pane to read the draft price list. The command kept running behind it.",
                },
                {
                    "label": "She closed a second terminal with the x",
                    "text": "That stopped it. The terminal lived only in the window, so it was gone, scrollback and all.",
                },
                {
                    "label": "She found her chat the next morning",
                    "text": "After a restart, her chat came back as a saved session under the Prices project. The price list was still a file in the folder.",
                },
            ],
        },
        "complete": {
            "title": "Your turn: Tomas's long export",
            "intro": (
                "Tomas Reyes runs a bike repair shop and has a long export running in a terminal pane. Fill in the "
                "three blanks about what closing the app does, then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "Task: Tomas starts a project in his Repairs folder and runs a long export in the terminal pane.\n"
                        "He hides the terminal pane. What happens to the export: "
                    )
                },
                {
                    "gap": "pane",
                    "prompt": "What happens to the export when he hides the pane, and why?",
                    "answer": "It keeps running, because hiding a pane hides the view and whatever runs inside carries on.",
                    "min_words": 8,
                },
                {"text": "\nHe quits the app and reopens it the next day. What comes back: "},
                {
                    "gap": "back",
                    "prompt": "Name what comes back, and where his chat sits.",
                    "answer": "His chat comes back as a saved session, and it sits in the Repairs project with the other sessions from that folder.",
                    "min_words": 10,
                },
                {"text": "\nThe second terminal he closed with the x before quitting: "},
                {
                    "gap": "gone",
                    "prompt": "What happens to something that only ever lived in the window?",
                    "answer": "It is gone, scrollback and all, because it only lived in the window and closing its tab released it.",
                    "min_words": 8,
                },
            ],
        },
        "coach": [
            {
                "hint": "Ask what hiding a pane changes about the view and what it changes about the task inside. Which one changes?",
                "example": "Example: Tomas hides the pane holding his long export. The export keeps running while he reads something else.",
            },
            {
                "hint": "Think about what you can open again tomorrow from your list of past chats, with no extra effort.",
                "example": "Example: after a restart, Elena opens the app and her price-list chat is there, ready to continue.",
            },
            {
                "hint": "Name the thing that gathers sessions working in the same folder, so they sit together.",
                "example": "Example: three chats about the Repairs folder sit together under one Repairs project.",
            },
            {
                "hint": "Ask where a thing lives. If it lives only in the window, what keeps it when the window closes?",
                "example": "Example: a terminal closed with the x keeps no copy of its scrollback, so it is gone after a restart.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "You hide the terminal pane while a long export runs, then open a preview of a different file. "
                    "Say what happens to the export."
                ),
                "points": [
                    {
                        "point": "that hiding a pane hides the view and leaves the work inside it running",
                        "hint": "Separate what you see on screen from what the task is doing.",
                        "example": "Example: a nightly backup started in a pane keeps going after you hide that pane.",
                    },
                    {
                        "point": "that you can keep reading or working on something else meanwhile",
                        "hint": "Ask what you gain when a hidden task carries on.",
                        "example": "Example: you read a client's file in the preview pane while the export finishes.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "On Monday you worked in three chats about the Garcia Roofing folder. Say how you find them "
                    "on Tuesday after a restart, and what ties them together."
                ),
                "points": [
                    {
                        "point": "that sessions are saved and come back after a restart",
                        "hint": "Think about what the app keeps when you quit.",
                        "example": "Example: the three chats are still in your list on Tuesday, ready to continue.",
                    },
                    {
                        "point": "that a project groups the sessions that work in the same folder",
                        "hint": "Name the thing that sits above a set of chats about one folder.",
                        "example": "Example: all three chats sit under a Garcia Roofing project because they share a folder.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "A coworker typed a note into the message box, attached a spreadsheet, and quit the app before "
                    "sending. Her note came back, and the attachment is gone. Say why, and what she should do next time."
                ),
                "points": [
                    {
                        "point": "that the app saves the text of an unsent message, while an attached file is held only in the window, so it is gone when the app closes",
                        "hint": "Ask which part the app keeps a copy of.",
                        "example": "Example: the typed note had a saved copy and came back, and the attachment existed only in the window.",
                    },
                    {
                        "point": "that she should send the message, or keep the file in the project folder, so something keeps it",
                        "hint": "Pick a place that survives a restart.",
                        "example": "Example: save the spreadsheet in the project folder and attach it again before sending.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your practice session",
            "body": (
                "Send the practice chat from the lab and let Hermes answer. Then click Check my work. It passes when "
                "Hermes lists a saved session that begins with the [FA-DESKTOP] practice message."
            ),
            "verify": "desktop",
            "check": "workspace",
            "marker": "[FA-DESKTOP]",
            "proof": "Hermes lists a saved session that carries the [FA-DESKTOP] marker from your practice chat.",
            "fixes": {
                "no_sessions": {
                    "hint": "Hermes lists no saved sessions yet. Send the practice chat from the lab, wait for the answer, and run the check again.",
                    "example": "Example: after you send the practice chat and Hermes replies, the session appears in your list.",
                },
                "no_marker": {
                    "hint": "Your sessions don't start with [FA-DESKTOP]. Send the lab's practice chat exactly as written, including that opening tag.",
                    "example": "Example: a chat that begins [FA-DESKTOP] Walk me through one small real task counts. A chat you typed from scratch doesn't.",
                },
            },
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now looks for the saved session from your practice chat, which begins with [FA-DESKTOP]. "
                    "It used to pass with any one saved session."
                ),
            }
        ],
    },
    "operator.learning": {
        "minutes": {"lesson": 3, "example": 4, "complete": 4, "lab": 10, "explain": 5, "gate": 2},
        "use": (
            "You said you want Hermes to do this for you: {goal}. That goes faster when Hermes already knows "
            "how you work, so you stop explaining the same things in every chat."
        ),
        "use_plain": (
            "Hermes can keep what you keep repeating: facts in memory, how-tos in a skill. This mission shows "
            "you which goes where, so you stop explaining the same things in every chat."
        ),
        "lab": {
            "title": "Save a fact and make a skill",
            "body": (
                "1. In one chat, save a fact you keep repeating.\n"
                "2. In the same chat, turn one how-to into a skill named academy- plus a short name, "
                "such as academy-weekly-status.\n"
                "3. Start a new chat and ask Hermes for the fact."
            ),
            "prompt": (
                "Help me do two things, one step at a time. First, save one fact about how I work to memory. Second, "
                "turn one how-to I keep explaining into a skill named academy-weekly-status, or another name that starts "
                "with academy-. Then tell me where each one is saved and when you will use it."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "Where a fact goes, and where a how-to goes",
            "lines": [
                "Memory is a short list of facts Hermes reads at the start of every chat, so keep it small.",
                "A skill is a saved set of steps that Hermes opens when your request matches it.",
                "Your past chats are an archive Hermes can search when you ask what you decided.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "How Hannah stopped repeating herself",
            "intro": (
                "Hannah Brooks is a wedding florist. She was tired of explaining two things to Hermes in every chat, "
                "so she sorted them into the right places."
            ),
            "parts": [
                {
                    "label": "She sorted the fact from the how-to",
                    "text": (
                        "She quotes in whole dollars with delivery included, which is one line and a fact. Her Friday stem "
                        "order takes five steps in a set order, which is a how-to."
                    ),
                },
                {
                    "label": "She put the fact in memory",
                    "text": "Hermes reads memory at the start of every chat, so she kept it to that one short line.",
                },
                {
                    "label": "She saved the steps as a skill",
                    "text": (
                        "She named it academy-stem-order and described it the way she talks: order stems for this weekend's "
                        "weddings. Hermes opens a skill when a request matches its description."
                    ),
                },
                {
                    "label": "She tested both in a new chat",
                    "text": "She asked for the weekend stem order and Hermes opened the skill. She asked for a quote and Hermes already knew her whole-dollar rule.",
                },
            ],
        },
        "complete": {
            "title": "Your turn: Mateo's three repeats",
            "intro": (
                "Chef Mateo Rossi runs a catering company and repeats three things to Hermes. Decide where each belongs: "
                "memory, a skill, or past chats. Then compare with our answers."
            ),
            "parts": [
                {"text": "Item 1: \"I never put shellfish on a menu.\"\nWhere it goes: "},
                {
                    "gap": "fact",
                    "prompt": "Where does this go, and why?",
                    "answer": "Memory, because it is one short fact that Hermes should know at the start of every chat.",
                    "min_words": 10,
                },
                {
                    "text": (
                        "\nItem 2: the six steps for turning a client's event notes into a menu proposal.\nWhere it goes: "
                    )
                },
                {
                    "gap": "howto",
                    "prompt": "Where does this go, and why?",
                    "answer": "A skill, because it is a step-by-step how-to that Hermes opens when a request matches it.",
                    "min_words": 10,
                },
                {"text": "\nItem 3: \"What did we decide in March about the venue deposit?\"\nWhere to look: "},
                {
                    "gap": "archive",
                    "prompt": "Where does Hermes find this, and why?",
                    "answer": "Past chats, because Hermes can search that archive when you ask what you decided earlier.",
                    "min_words": 8,
                },
            ],
        },
        "coach": [
            {
                "hint": "Ask whether the thing is one line or a list of steps in a set order. Which place holds steps?",
                "example": "Example: a six-step routine for writing a menu proposal is saved as a skill.",
            },
            {
                "hint": "Think about what Hermes reads each time you open a chat, and what a long entry there costs you every time.",
                "example": "Example: a twelve-step expense routine in memory is read in every chat, even a chat about the weather, and it can clash with what you say next.",
            },
            {
                "hint": "Ask what searching an archive changes about how Hermes behaves from now on.",
                "example": "Example: Hermes finds what you decided in March, and the search teaches it nothing new about your routine.",
            },
            {
                "hint": "Think about how Hermes decides to open a skill. What does it compare your request with?",
                "example": "Example: a skill described as a catering proposal opens when you ask for a proposal. A description like helpful notes never matches a request.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "A friend's memory is nearly full, and a twelve-step expense routine takes up most of it. Hermes "
                    "sometimes ignores her newest instruction. Say what you would change."
                ),
                "points": [
                    {
                        "point": "move the twelve-step routine out of memory and into a skill",
                        "hint": "Ask which kind of thing belongs in a skill.",
                        "example": "Example: save the expense routine as a skill that opens when she asks for an expense report.",
                    },
                    {
                        "point": "keep memory to short facts, because Hermes reads all of it in every chat",
                        "hint": "Think about what a long list costs on each chat.",
                        "example": "Example: keep a line such as she bills in whole dollars, and remove anything that reads like instructions.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "Last month you decided in a chat which supplier to drop. You never saved it anywhere, and Hermes "
                    "has no idea today. Say where the answer lives and how you ask."
                ),
                "points": [
                    {
                        "point": "that your past chats are an archive Hermes can search",
                        "hint": "Name the place that keeps old conversations.",
                        "example": "Example: the decision sits in last month's chat, which Hermes can search.",
                    },
                    {
                        "point": "that you ask what you decided, so Hermes searches the archive",
                        "hint": "Think about the question that sends Hermes to old chats.",
                        "example": "Example: ask, what did we decide last month about the supplier?",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "You saved a skill for invoice follow-ups, but Hermes never opens it when you type \"chase the "
                    "late payers.\" Say what you check first."
                ),
                "points": [
                    {
                        "point": "that a skill opens on its own only when its description matches the request",
                        "hint": "Ask what Hermes compares your words with.",
                        "example": "Example: the skill's description says billing reminders, so a request about late payers has no match.",
                    },
                    {
                        "point": "that you reword the description in the words you actually use, then test it in a new chat",
                        "hint": "Fix the description, then try the same request again.",
                        "example": "Example: add the phrase chase late payers to the description, open a new chat and ask again.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check that your skill is installed",
            "body": (
                "Click Check my work. It passes when Hermes lists an installed skill whose name starts with academy-, "
                "the one you made in the lab."
            ),
            "verify": "desktop",
            "check": "knowledge",
            "marker": "academy-",
            "proof": "Hermes lists an installed skill whose name starts with academy-, which you made from a how-to you repeat.",
            "fixes": {
                "no_skills": {
                    "hint": "Hermes lists no installed skills. Go back to the lab chat and ask Hermes to save your how-to as a skill, then run the check again.",
                    "example": "Example: after Hermes saves the steps as a skill, it shows in your skill list.",
                },
                "no_marked_skill": {
                    "hint": "Your skills don't have a name starting with academy-. Ask Hermes to save the how-to under that kind of name.",
                    "example": "Example: academy-weekly-status works. A skill named weekly-status doesn't match.",
                },
            },
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now looks for a skill you made, whose name starts with academy-. It used to pass "
                    "when Hermes listed at least one skill and one set of tools."
                ),
            }
        ],
    },
    "operator.automation": {
        "minutes": {"lesson": 3, "example": 4, "complete": 5, "lab": 12, "explain": 6, "gate": 3},
        "use": (
            "You said you want Hermes to do this for you: {goal}. Work you want without asking runs as a "
            "scheduled job, and a job needs everything spelled out because it starts with a blank page."
        ),
        "use_plain": (
            "Work you want without asking runs as a scheduled job. A job starts with a blank page, so this "
            "mission shows you everything its request has to say."
        ),
        "lab": {
            "body": (
                "1. In Scheduled jobs, make a job named academy-friday-recap.\n"
                "2. Pause it or run it once.\n"
                "\n"
                "Its request must say:\n"
                "- Where to work\n"
                "- What to read\n"
                "- What a good result is\n"
                "- Where to send it\n"
                "- What to do on failure"
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "A scheduled job starts with a blank page",
            "lines": [
                "A scheduled job sees none of your chat: no earlier messages, no open files, nothing from yesterday.",
                "Its request has to say where to work, what to read, and what a good result looks like.",
                "It also says where to send the result and what to do if something fails.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "How Gloria wrote her Monday rent job",
            "intro": (
                "Gloria Nguyen owns a twelve-unit apartment building and wanted a list of late rent every Monday "
                "morning. A job starts with a blank page, so she wrote its request one line at a time."
            ),
            "parts": [
                {
                    "label": "She said where to work",
                    "text": "Her request opened: work in the Rent folder on this computer. The job had no open conversation to borrow a folder from.",
                },
                {
                    "label": "She named the files to read",
                    "text": "Read rent-log.csv and every file in the Late notices folder. The job knew nothing she had decided last week.",
                },
                {
                    "label": "She said what a good result was",
                    "text": "Tenants more than five days late, with amounts, on one page. An empty rent-log.csv counts as a failure.",
                },
                {
                    "label": "She ended with delivery and failure",
                    "text": "Send the list to her usual chat. If anything fails, send one line saying what failed, so she hears about a broken job that same Monday.",
                },
            ],
        },
        "complete": {
            "title": "Your turn: Naomi's Sunday stock check",
            "intro": (
                "Naomi Fraser runs a food truck and wants a stock check every Sunday night. The first two lines of her "
                "request are written. Fill in the last three blanks, then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "Job name: truck-stock, every Sunday at 8 pm.\nWhere to work: the Inventory folder on the office computer.\n"
                        "What to read: stock.csv and the week's sales.csv.\nWhat a good result looks like: "
                    )
                },
                {
                    "gap": "result",
                    "prompt": "Describe a good result in a way you could check.",
                    "answer": "A list of every item with fewer than ten units left, sorted by how fast it sells, short enough for one screen.",
                    "min_words": 12,
                },
                {"text": "\nWhere to send it: "},
                {
                    "gap": "send",
                    "prompt": "Say where the result goes.",
                    "answer": "To Naomi in her usual chat, with the list written in the message itself.",
                    "min_words": 8,
                },
                {"text": "\nIf something fails: "},
                {
                    "gap": "fail",
                    "prompt": "Say what the job does when it breaks.",
                    "answer": "Send Naomi one line naming the file that failed to open, so a broken job gets noticed the same night.",
                    "min_words": 10,
                },
            ],
        },
        "coach": [
            {
                "hint": "Ask what a chat gives you for free that a job at three in the morning lacks. A folder you already have open is one.",
                "example": "Example: Naomi's request opens with: work in the Inventory folder on the office computer.",
            },
            {
                "hint": "Name the files, pages or messages the job needs, as exactly as you would for a new assistant on day one.",
                "example": "Example: read stock.csv and the week's sales.csv in that folder.",
            },
            {
                "hint": "Write the result so a stranger could answer yes or no to it. A number or a length helps.",
                "example": "Example: a list of items with fewer than ten units left, short enough for one screen.",
            },
            {
                "hint": "Name the place you will actually look. A result saved where nobody looks gets seen by nobody.",
                "example": "Example: send the list to Naomi in her usual chat.",
            },
            {
                "hint": "Decide what you want on a bad night, so the job tells you and stays out of silence.",
                "example": "Example: send one line naming the file that would not open.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "A job ran every morning for a month before you noticed it had delivered nothing useful. "
                    "Name two lines its request probably lacked."
                ),
                "points": [
                    {
                        "point": "what a good result looks like, clearly enough to tell when the job fails",
                        "hint": "Ask how the job could tell its own result is wrong.",
                        "example": "Example: a list of overdue invoices under one page, and an empty list counts as a failure.",
                    },
                    {
                        "point": "what to do on failure, so a broken job reports itself",
                        "hint": "Think about what you wanted to happen on a bad morning.",
                        "example": "Example: send one line saying which file could not be read.",
                    },
                    {
                        "point": "where to send the result, so someone sees it",
                        "hint": "Ask where the result went once the job finished.",
                        "example": "Example: send the summary to Dev in his usual chat.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "In chat you asked, \"Do the usual report from yesterday,\" and it worked. You schedule that exact "
                    "request and it produces nothing useful. Say why, and what you rewrite."
                ),
                "points": [
                    {
                        "point": "that a job sees none of your earlier conversation, so usual and yesterday mean nothing to it",
                        "hint": "Compare what a chat remembers with what a job starts with.",
                        "example": "Example: the job has no earlier messages, so it can't know which report you meant.",
                    },
                    {
                        "point": "to rewrite it naming the folder, the files, and what the report holds",
                        "hint": "Replace every vague word with a name.",
                        "example": "Example: work in the Sales folder, read last-week.csv, list the five biggest orders.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "You built a daily 7 a.m. check and want to trust it by Friday. Say how you test it before you "
                    "rely on it."
                ),
                "points": [
                    {
                        "point": "make it harmless, paused or set to run once, so a mistake costs nothing",
                        "hint": "Choose a setting that keeps the job from running every day while you test.",
                        "example": "Example: set the job to run once this afternoon.",
                    },
                    {
                        "point": "watch it run, read the result, and fill in any line the request was missing",
                        "hint": "Look at what came out, then fix what the request left unsaid.",
                        "example": "Example: the result had no failure line, so add one and run it once more.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your scheduled job",
            "body": (
                "Paste the job's whole request, as Hermes lists only its first 100 characters. It passes when "
                "an academy- job has a schedule and its request says where to work, what to read, a good result, "
                "where to send it and what to do on failure."
            ),
            "verify": "desktop",
            "check": "automation",
            "marker": "academy-",
            "proof": "Hermes lists a scheduled job whose request says where to work, what to read, what a good result is, where to send it, and what to do on failure.",
            "fixes": {
                "no_jobs": {
                    "hint": "Hermes lists no scheduled jobs. Open Scheduled jobs, make the job from the lab, and run the check again.",
                    "example": "Example: after you save the job, it appears in the Scheduled jobs list.",
                },
                "no_marked_job": {
                    "hint": "Your jobs don't have a name starting with academy-. Rename the job or make a new one with that kind of name.",
                    "example": "Example: academy-monday-rent works. A job named monday-rent doesn't match.",
                },
                "no_schedule": {
                    "hint": "The job has no schedule. Give it a time, even if you keep it paused, so it has something to run on.",
                    "example": "Example: every Sunday at 8 pm, left paused until you are ready.",
                },
                "paste_request": {
                    "hint": "Open the job in Scheduled jobs, copy its whole request, paste it into the box above the button, and check again.",
                    "example": "Example: the list shows \"Work in the Rent folder and read rent-roll.csv. List every unit...\", so copy the request from the job itself, all of it.",
                },
                "request_mismatch": {
                    "hint": "Paste the request exactly as the job holds it. The start has to match what Hermes shows for the job.",
                    "example": "Example: if you edited the job after copying, copy it again from the job.",
                },
                "prompt_thin": {
                    "hint": "The request is missing lines. Add where to work, what to read, what a good result is, where to send it, and what to do on failure.",
                    "example": "Example: work in the Sales folder, read last-week.csv, list the five biggest orders, send it to me in my chat, and if a file fails to open send me one line saying which.",
                },
            },
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now looks for a job you made, named academy-, with a schedule and a request that covers "
                    "the five things. It used to pass when Hermes listed at least one scheduled job."
                ),
            }
        ],
    },
}


CAPSTONE = {
    "id": "operator.capstone",
    "title": "Put Hermes to work on your own job",
    "promise": "Pick one real job from your own work, set Hermes up to do it, and write down whether it met the criteria you set first.",
    "outcome": "A written record of one real job running in your Hermes, judged against criteria you chose.",
    "level_meaning": "You run one job of your own in Hermes and judge it against criteria you set.",
    "sources": ["official_desktop", "official_quickstart", "tony"],
    "watch": ["nous.desktop", "nous.memory", "nous.cron", "t.7", "tony.6"],
    "lesson": {
        "title": "Choose one job and set the bar first",
        "body": (
            "Pick one job from your own week that comes around again. Before it runs, write down how you will judge "
            "Hermes on it: two or three numbered criteria, at least two with a number. Then use what you learned. "
            "Check where your Hermes runs, put the facts in memory, turn the how-to into a skill, and schedule the job. "
            "Your criteria let you say afterward whether it worked."
        ),
        "source": "tony",
    },
    "lab": {
        "title": "Run your job and keep notes",
        "body": (
            "1. Use the practice chat to plan your job with Hermes: the criteria, the facts for "
            "memory, the skill and the schedule.\n"
            "2. Run the job for real.\n"
            "3. Write down what you see against each criterion."
        ),
        "prompt": (
            "I want to put Hermes to work on one real job of my own. Ask me what the job is and how often it comes up. "
            "Help me write three numbered criteria, at least two with a number. Then go one step at a time: where my Hermes "
            "runs, which facts go in memory, which how-to becomes a skill, and what a scheduled job's request must say. "
            "Afterward, help me judge each criterion as met, partly met or not met."
        ),
    },
    "explain": {
        "title": "Explain what carries over to a new situation",
        "question": (
            "Pat Delgado's Hermes sends a Monday order report from a laptop. The office now wants the same report every "
            "Monday for a team of four, from a different computer. Say which of your ideas carry over, which you check "
            "again, and what changes because other people depend on it."
        ),
        "covers": [
            "that scheduled jobs run through a gateway, so the gateway on the new computer has to be running",
            "that memory, skills and passwords belong to a profile, so the new setup may lack what the job needs",
            "that the request has to stand alone on the new computer, naming where to work and what to read, because folders differ",
            "that a team needs a stated good result and a named place to send it, so everyone can tell when the job fails",
            "that you test the job once, paused or run once, before the team relies on it",
        ],
        "coach": [
            {
                "hint": "Think about which background program runs scheduled jobs, and where it lives now.",
                "example": "Example: the gateway on the old laptop stays behind, so the office computer needs its own gateway running.",
            },
            {
                "hint": "Ask which setup holds the memory, skills and passwords the job uses, and whether it exists on the new computer.",
                "example": "Example: the job needs a spreadsheet password saved in the old profile, so the new profile has to hold it too.",
            },
            {
                "hint": "Read the request as if the new computer knew nothing. Which folder and file names might differ there?",
                "example": "Example: the report folder sits at a different place on the office computer, so the request names the new folder.",
            },
            {
                "hint": "With four people, who decides whether the report is right, and where do they all look for it?",
                "example": "Example: a shared channel receives the report, and the failure line goes to the same channel.",
            },
            {
                "hint": "Choose a harmless first run that lets you read the result before the team depends on it.",
                "example": "Example: run it once on the new computer on a Friday, read the result, then switch on the schedule.",
            },
        ],
    },
    "use": (
        "You said you want Hermes to do this for you: {goal}. This is the mission where you do it for real, on your own job, "
        "and judge the result against criteria you set first."
    ),
    "use_plain": (
        "This mission is where you put one real job of your own into Hermes and judge the result against criteria "
        "you set before it ran."
    ),
    "minutes": {"lesson": 4, "example": 4, "complete": 8, "lab": 30, "explain": 6, "gate": 10},
    "story_first": True,
    "takeaway": {
        "title": "Choose one job and set the bar first",
        "lines": [
            "Pick one job from your own week that comes around again.",
            "Before it runs, write two or three numbered criteria, at least two with a number.",
            "Afterward, your criteria let you say plainly whether the job worked.",
        ],
        "picture": "",
    },
    "worked": {
        "title": "How Walter judged his monthly tuning list",
        "intro": (
            "Walter Pruitt tunes pianos for 140 customers and scanned his spreadsheet by hand every month to find who "
            "was due. He gave that job to Hermes and wrote this record after the first run."
        ),
        "parts": [
            {
                "label": "He picked one job that came around monthly",
                "text": "The tuning list took about two hours each month, and a single repeating job was small enough to judge.",
            },
            {
                "label": "He set the criteria before the run",
                "text": "Three numbered lines, each with a number or a time, such as ready by 7 am on the first. A criterion he could count could end up not met.",
            },
            {
                "label": "He used what the path taught",
                "text": "His pianos profile runs on the office computer. A memory fact, a skill named academy-tuning-list and a scheduled job did the work.",
            },
            {
                "label": "He judged each criterion honestly",
                "text": "The list arrived at 6:52 am and missed one customer in 20, so two were met. Reading took 14 minutes against his 10, so the third was not met, and he dated his next change.",
            },
        ],
        "document": (
            "# Own job: monthly tuning list for Pruitt Piano Tuning\n\n"
            "## Problem\n"
            "Walter Pruitt tunes pianos for 140 customers tracked in one spreadsheet. Every month he scans it by hand "
            "to find who is due, about two hours of work that gets skipped in busy weeks.\n\n"
            "## Criteria\n"
            "1. The list is ready by 7 am on the first of every month.\n"
            "2. It names every customer whose last tuning was over 11 months ago, with at most one miss in 20 checked.\n"
            "3. Walter needs under 10 minutes to read and send it.\n\n"
            "## What I did\n"
            "My profile, pianos, runs on the office computer, so its gateway has to be running there. I saved one fact "
            "to memory: a tuning is due 11 months after the last one. I turned the five steps for building the list into "
            "a skill named academy-tuning-list. The job tuning-list runs at 6 am on the first of each month. Its request "
            "names the Customers folder and customers.csv, defines a good result as one page, sends it to me in my chat, "
            "and says to send one line naming the file if anything fails.\n\n"
            "## Evidence\n"
            "1. The October list arrived at 6:52 am on the first. Met.\n"
            "2. It named 23 customers, and I found one missing in a check of 20. Met.\n"
            "3. Reading and sending took 14 minutes. Not met.\n\n"
            "## What did not work\n"
            "The first run read the Archive tab of the spreadsheet and listed customers who had moved away. I fixed it by "
            "naming the Active tab in the request. Reading still takes long because I double-check each address.\n\n"
            "## Next\n"
            "Within 14 days I will add each phone number beside the name and time the reading again against the "
            "10 minute goal.\n"
        ),
    },
    "complete": {
        "title": "Your turn: Lucy's Friday parent notes",
        "intro": (
            "Lucy Tran runs Tran Tutoring and wants a Friday progress note for each parent. Her record has blanks in "
            "the criteria, the evidence and the next step. Fill them, then compare with our answers."
        ),
        "parts": [
            {
                "text": (
                    "# Own job: Friday parent update for Tran Tutoring\n\n"
                    "## Problem\n"
                    "Lucy Tran runs a tutoring business with 30 students. Every Friday she writes a progress note to each "
                    "parent from her session notes, which takes about three hours.\n\n"
                    "## Criteria\n"
                )
            },
            {
                "gap": "criteria",
                "prompt": "Write three numbered criteria, at least two with a number.",
                "answer": (
                    "1. Every parent has a draft note by 4 pm each Friday.\n"
                    "2. At least 27 of 30 drafts need no edits from Lucy.\n"
                    "3. Lucy spends under 45 minutes a week on the notes."
                ),
                "min_words": 25,
                "needs": ["number", "list"],
            },
            {
                "text": (
                    "\n\n## What I did\n"
                    "My profile tutoring runs on this computer, so its gateway has to be running here. I saved the note "
                    "format as a fact in memory and the five writing steps as a skill named academy-parent-note. A job named "
                    "parent-notes runs every Friday at 2 pm, reads the Sessions folder, and sends the drafts to me in my chat, "
                    "with one line to me if a file will not open.\n\n"
                    "## Evidence\n"
                )
            },
            {
                "gap": "evidence",
                "prompt": "Write one numbered line per criterion, each ending met, partly met or not met.",
                "answer": (
                    "1. The drafts arrived at 3:40 pm on the first Friday. Met.\n"
                    "2. Twenty-four of 30 needed no edits. Partly met.\n"
                    "3. The notes took me 50 minutes. Not met."
                ),
                "min_words": 20,
                "needs": ["verdict"],
            },
            {
                "text": (
                    "\n\n## What did not work\n"
                    "The first drafts used the same opening line for every parent, so several read as copied.\n\n"
                    "## Next\n"
                )
            },
            {
                "gap": "next",
                "prompt": "Say the next change and when you will make it.",
                "answer": "Within 7 days I will add each student's latest goal to the skill and compare the edit count again.",
                "min_words": 12,
                "needs": ["time"],
            },
        ],
    },
    "gate": {
        "title": "Check your own job record",
        "body": (
            "Write a text or Markdown file with the six sections below, about your own real job. "
            "Number your criteria, then number one evidence line for each.\n"
            "1. Save it.\n"
            "2. Type where you saved it.\n"
            "3. Click Check my work."
        ),
        "verify": "artifact",
        "check": "own-job record",
        "cross": "criteria",
        "sections": [
            {
                "heading": "Problem", "min_words": 15, "needs": ["time"],
                "what": "the one job, who it is for, and how often it comes up",
                "fix": "Say how often the job comes up or how long it takes by hand.",
                "hint": "Name the job, the person it is for, how often it comes up and how long it takes by hand.",
                "example": "Example: Rosa Alvarez runs a bakery and every Thursday spends two hours retyping wholesale orders into her invoice program.",
            },
            {
                "heading": "Criteria", "min_words": 20, "needs": ["number"],
                "what": "three numbered criteria you set before running the job, at least two with a number",
                "fix": "Put a number or a time in at least one criterion: how many, by when, how long.",
                "hint": "Write three numbered lines. Turn each into something you can count or time, so a later check can say met or not met.",
                "example": "Example:\n1. All twelve orders are entered by noon each Thursday.\n2. No more than one order needs a correction.\n3. Rosa spends under 20 minutes on it.",
            },
            {
                "heading": "What I did", "min_words": 30, "needs": [],
                "what": "where your Hermes runs, what went into memory, your skill, and the job's request",
                "hint": "Say where your Hermes runs, what you saved to memory, which skill you made, and what the job's request says.",
                "example": "Example: My profile bakery runs on the shop computer. Memory holds my invoice format. A skill named academy-order-entry holds the six steps. The job runs Thursdays at 8 am and names the Orders folder.",
            },
            {
                "heading": "Evidence", "min_words": 15, "needs": ["verdict"],
                "what": "one numbered line per criterion, each ending met, partly met or not met",
                "fix": "End every line with met, partly met or not met.",
                "hint": "Write one numbered line per criterion, in the same order, saying what you saw and ending with your verdict.",
                "example": "Example:\n1. Eleven of twelve orders were in by 11:40 am. Partly met.\n2. Two orders needed fixes. Not met.\n3. It took me 15 minutes. Met.",
            },
            {
                "heading": "What did not work", "min_words": 15, "needs": [],
                "what": "something that failed or fell short, in plain words",
                "hint": "Name one thing that failed or fell short and what you saw. An honest note teaches you more than a clean one.",
                "example": "Example: Hermes read last month's order sheet, because my request named the folder and left out the file name.",
            },
            {
                "heading": "Next", "min_words": 12, "needs": ["time"],
                "what": "the next change and when you will make it",
                "fix": "Say when you will make the change, such as within 14 days.",
                "hint": "Pick one change that closes the biggest gap in your evidence, and give it a date.",
                "example": "Example: Within 7 days I will name the exact order file in the request and run the job again.",
            },
        ],
        "proof": (
            "Your own job record, saved on your computer, with criteria you set and a verdict against each one. "
            "Its fingerprint goes on your Field Record."
        ),
    },
    "review": [
        {
            "id": "r1",
            "question": (
                "A month after your job started working, you rename the profile it runs under, and the job stops "
                "delivering. Say what you check."
            ),
            "points": [
                {
                    "point": "that the job belongs to the profile and moved with it, so you look for it under the new name",
                    "hint": "Ask where the job went when the profile's name changed.",
                    "example": "Example: open the job list under the new profile name and find the job there.",
                },
                {
                    "point": "that the gateway serving that profile has to be running",
                    "hint": "Name the program that runs scheduled jobs.",
                    "example": "Example: check that the Gateway item in the status bar says Connected, and that the job shows its next run.",
                },
            ],
        },
        {
            "id": "r2",
            "question": (
                "Your criterion says, \"The weekly summary is good.\" A month later you can't say whether the job "
                "worked. Rewrite the criterion and say how you record the result."
            ),
            "points": [
                {
                    "point": "put a number or a time in the criterion, so you can count it",
                    "hint": "Ask what you could measure: how many, by when, how long.",
                    "example": "Example: the summary lists all open invoices over 30 days by 8 am Monday.",
                },
                {
                    "point": "write one evidence line per criterion ending met, partly met or not met",
                    "hint": "Think about the word that closes each line of your record.",
                    "example": "Example: 1. Arrived at 7:55 am. Met.",
                },
            ],
        },
        {
            "id": "r3",
            "question": (
                "A job you built for yourself will now serve your assistant, Marco Lee, too. Say what you add to "
                "the request and the record."
            ),
            "points": [
                {
                    "point": "a named place both of you look, so the result reaches Marco",
                    "hint": "Ask where the result lands for two people.",
                    "example": "Example: send the result to a shared chat that includes Marco.",
                },
                {
                    "point": "a failure line that reaches someone who can act, so a broken job gets noticed",
                    "hint": "Decide who hears first when the job fails.",
                    "example": "Example: if a file fails to open, send one line naming it to the shared chat.",
                },
            ],
        },
    ],
    "revisions": [
        {
            "version": 1,
            "kind": "added",
            "summary": (
                "New in 0.5.0: a final mission where you run one real job of your own and write down whether it met "
                "the criteria you set first."
            ),
        }
    ],
}


PLACEMENT = {
    "title": "Placement check",
    "intro": (
        "This is for people who already use Hermes. Six scenario questions, two for each level. Answer both questions "
        "for a level correctly and you skip that level's reading and practice. The checks on real work still apply "
        "to every mission."
    ),
    "minutes": 5,
    "questions": [
        {
            "id": "p1",
            "level": "beginner",
            "question": "Your 7 a.m. report didn't arrive, though the Hermes app on your desk was open all night, connected to the office computer. What do you check first?",
            "options": [
                "The app window, because it shows what Hermes did overnight",
                "The gateway, because that background program runs scheduled jobs",
                "Your memory list, because the report depends on a fact you saved there last month",
                "Your past chats, because the report may sit in an old session",
            ],
            "answer": 1,
            "why": (
                "The gateway on the office computer runs the jobs whether or not the window is open, and it can stop while the app looks fine. "
                "The window shows only the app. Memory and past chats hold facts and old conversations, and they run no jobs."
            ),
        },
        {
            "id": "p2",
            "level": "beginner",
            "question": "You quit the app and reopen it tomorrow. Which of these is still there?",
            "options": [
                "Your chat from earlier, saved as a session",
                "The scrollback of a terminal you closed with the x",
                "A file you attached to a message you never sent",
            ],
            "answer": 0,
            "why": (
                "Sessions are saved and come back after a restart, and so does the text of an unsent message. A terminal "
                "closed with the x and a file attached to an unsent message had no saved copy, so they are gone."
            ),
        },
        {
            "id": "p3",
            "level": "intermediate",
            "question": "You explain the same five-step routine for formatting a client report in almost every chat. Where does it belong?",
            "options": [
                "In memory, so Hermes reads it at the start of every chat",
                "In your past chats, which Hermes can search",
                "In the scheduled jobs list, so it runs by itself each morning before you start work",
                "In a skill, which Hermes opens when a request matches it",
            ],
            "answer": 3,
            "why": (
                "A step-by-step routine is a skill. Memory is read in every chat, so a long routine there costs you each time. "
                "Past chats are an archive, and a schedule runs a request on a timer."
            ),
        },
        {
            "id": "p4",
            "level": "intermediate",
            "question": "Last month you decided in a chat which supplier to drop and never saved it anywhere. Where can Hermes find that now?",
            "options": [
                "In past chats, which Hermes searches when you ask",
                "In memory, because every chat starts by reading it",
                "In a skill, because skills keep decisions for later",
                "In the job list, because decisions run on a timer",
            ],
            "answer": 0,
            "why": (
                "Your past chats are an archive Hermes can search when you ask what you decided. "
                "Memory holds short saved facts. A skill holds steps, and the job list holds timed requests."
            ),
        },
        {
            "id": "p5",
            "level": "advanced",
            "question": "You schedule the request \"Do the usual Friday recap.\" It worked in chat all week, but the job delivers nothing useful. What do you change?",
            "options": [
                "Run it later in the day, while the chat you tested in is still open on screen",
                "Rewrite it to name the folder, files, a good result, where to send it, and the failure step",
                "Add \"be thorough\" to the end of the request so the job tries harder at three in the morning",
                "Save the Friday recap routine to memory so that every chat and every job has it",
            ],
            "answer": 1,
            "why": (
                "A scheduled job sees none of your earlier chat, so the request has to say where to work, what to read, "
                "what a good result is, where to send it, and what to do on failure. The other changes leave those gaps open."
            ),
        },
        {
            "id": "p6",
            "level": "advanced",
            "question": "A 3 a.m. job runs without its input file, which is missing, and sends a report that looks normal. You find out a week later. Which line in its request would have told you sooner?",
            "options": [
                "Read every file in the folder before starting",
                "Work in the Reports folder on this computer, in the same place as last week",
                "If anything fails, send me one line saying what failed",
                "A good result is a one-page summary under 300 words, with the totals at the top",
            ],
            "answer": 2,
            "why": (
                "Hermes tells you when a run errors, but a run without its file can still look fine. The failure line "
                "tells the job what to do when something breaks, so you hear the same night. The other three lines "
                "say what to read, where to work and what a good result is."
            ),
        },
    ],
}
