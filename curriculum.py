"""Curriculum for Hermes Field Academy.

Four paths, nineteen missions. Each path climbs three levels (Beginner,
Intermediate, Advanced, the level names Nous uses on its Learning Path page),
finishes with a capstone on the learner's own problem, and ends with a
Field Record, the learner's own learning record for the path. Each mission has six steps, with the support fading as you go: a
lesson to read, a finished worked example to read, a half-finished one to
complete, a practice to try in your own Hermes, one question to answer in your
own words, and a check that passes only against real work on this computer.

The words for the worked examples, review questions, hints, placement checks and
capstones live in content/, one file per path (docs/content-format.md). This
file holds the structure and merges that content in.

Copy rules (docs/curriculum-voice.md): plain English, second person, present
tense. Headings name the thing and never end with a period. No "not X, but Y",
no lines about the product itself, no emoji.
"""

from __future__ import annotations

from copy import deepcopy

from . import content as _content

LEVELS = ("beginner", "intermediate", "advanced", "capstone")
LEVEL_NAMES = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced", "capstone": "Capstone"}

# Where a level's reading and practice can be skipped by a placement check. The
# question and the check on real work are never skipped.
SKIPPABLE_KINDS = ("lesson", "example", "complete", "lab")

# The "built on" list for each mission. Official docs first, then the people who
# teach Hermes. Every URL here returned 200 on 2026-10-02.
SOURCES = {
    "tonbi_terminal": {
        "name": "Hermes Agent Masterclass",
        "creator": "Tonbi, on Hermes Atlas",
        "url": "https://hermesatlas.com/masterclass/",
        "note": "Ten episodes with timestamped notes, from install to security.",
    },
    "tonbi_desktop": {
        "name": "Hermes Desktop App Masterclass",
        "creator": "Tonbi, on YouTube",
        "url": "https://www.youtube.com/playlist?list=PLJyLffobY7XU",
        "note": "The app itself: settings, connections, daily work.",
    },
    "tony": {
        "name": "The Whole Damn Thing",
        "creator": "Tony Simons, on X",
        "url": "https://x.com/tonysimons_/article/2079066422211117218",
        "note": "Twelve parts on how Hermes works and where it breaks.",
    },
    "official_desktop": {
        "name": "Desktop app",
        "creator": "Nous Research, Hermes docs",
        "url": "https://hermes-agent.nousresearch.com/docs/user-guide/desktop",
        "note": "What the app does and how it connects.",
    },
    "official_quickstart": {
        "name": "Quickstart",
        "creator": "Nous Research, Hermes docs",
        "url": "https://hermes-agent.nousresearch.com/docs/getting-started/quickstart",
        "note": "Install and your first working chat.",
    },
    "official_tools": {
        "name": "Tools reference",
        "creator": "Nous Research, Hermes docs",
        "url": "https://hermes-agent.nousresearch.com/docs/reference/tools-reference",
        "note": "Every tool, and where you can use it.",
    },
    "official_multi": {
        "name": "Connecting to more than one Hermes",
        "creator": "Nous Research, Hermes docs",
        "url": "https://hermes-agent.nousresearch.com/docs/user-guide/multi-connection-desktop",
        "note": "This computer, another computer, Hermes Cloud, and profiles.",
    },
    "official_kanban": {
        "name": "Kanban",
        "creator": "Nous Research, Hermes docs",
        "url": "https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban",
        "note": "Tasks that last longer than one chat.",
    },
    "official_teams": {
        "name": "Microsoft Teams",
        "creator": "Nous Research, Hermes docs",
        "url": "https://hermes-agent.nousresearch.com/docs/user-guide/messaging/teams",
        "note": "Setup, approvals and who may talk to Hermes.",
    },
}


def _nous(path, title):
    return {
        "course": "Hermes docs",
        "part": "Docs",
        "title": title,
        "creator": "Nous Research",
        "where": "Hermes docs",
        "credit": "Nous Research, Hermes docs",
        "kind": "docs",
        "url": f"https://hermes-agent.nousresearch.com/docs/{path}",
    }


def _atlas_episode(number, title):
    return {
        "course": "Hermes Agent Masterclass",
        "part": f"Episode {number}",
        "title": title,
        "creator": "Tonbi",
        "where": "Hermes Atlas",
        "credit": "Tonbi, on Hermes Atlas",
        "kind": "video",
        "url": f"https://hermesatlas.com/masterclass/#episode-{number}",
    }


def _atlas_guide(path, title):
    return {
        "course": "Hermes Atlas guides",
        "part": "Guide",
        "title": title,
        "creator": "Kevin Simback",
        "where": "Hermes Atlas",
        "credit": "Kevin Simback, on Hermes Atlas",
        "kind": "guide",
        "url": f"https://hermesatlas.com/{path}",
    }


def _bible(path, title):
    return {
        "course": "Hermes Bible",
        "part": "Docs mirror",
        "title": title,
        "creator": "iamlukethedev",
        "where": "the Hermes Bible",
        "credit": "iamlukethedev, on the Hermes Bible",
        "kind": "guide",
        "url": f"https://hermesbible.com/docs/{path}",
    }


def _youtube(part, title, video_id, course="Hermes Desktop App Masterclass"):
    return {
        "course": course,
        "part": part,
        "title": title,
        "creator": "Tonbi",
        "where": "YouTube",
        "credit": "Tonbi, on YouTube",
        "kind": "video",
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


def _tony(part, title):
    return {
        "course": "The Whole Damn Thing",
        "part": f"Part {part}",
        "title": title,
        "creator": "Tony Simons",
        "where": "X",
        "credit": "Tony Simons, on X",
        "kind": "article",
        "url": "https://x.com/tonysimons_/article/2079066422211117218",
    }


def _lab(part, title):
    return {
        "course": "Build a Hermes services business",
        "part": f"Lab {part}",
        "title": title,
        "creator": "Damon Gardenhire",
        "where": "School of Hermes",
        "credit": "School of Hermes, a concept by Damon Gardenhire",
        "kind": "course",
        "url": f"https://linchpin.studio/school-of-hermes/#lab-{part}",
    }


# Every link a mission shows, each credited to the person or group that made it.
# Tonbi's ten-part masterclass is linked through Hermes Atlas, where each episode
# has timestamped notes; his desktop series and quickstart live only on YouTube.
EPISODES = {
    # Official docs (Nous Research)
    "nous.desktop": _nous("user-guide/desktop", "Desktop app"),
    "nous.sessions": _nous("user-guide/sessions", "Sessions"),
    "nous.memory": _nous("user-guide/features/memory", "Memory"),
    "nous.skills": _nous("user-guide/features/skills", "Skills"),
    "nous.cron": _nous("user-guide/features/cron", "Scheduled jobs (cron)"),
    "nous.learning_path": _nous("getting-started/learning-path", "Learning path"),
    "nous.docker": _nous("user-guide/docker", "Running Hermes in Docker"),
    "nous.multi": _nous("user-guide/multi-connection-desktop", "Connecting to more than one Hermes"),
    "nous.mcp": _nous("user-guide/features/mcp", "MCP servers"),
    "nous.security": _nous("user-guide/security", "Security"),
    "nous.profiles": _nous("user-guide/profiles", "Profiles"),
    "nous.delegation": _nous("user-guide/features/delegation", "Subagents and delegation"),
    "nous.kanban": _nous("user-guide/features/kanban", "Kanban"),
    "nous.checkpoints": _nous("user-guide/checkpoints-and-rollback", "Checkpoints and rollback"),
    "nous.quickstart": _nous("getting-started/quickstart", "Quickstart"),
    # Tonbi's masterclass, through Hermes Atlas
    "t.1": _atlas_episode(1, "Installation, setup and basic commands"),
    "t.2": _atlas_episode(2, "VPS, Docker and messaging"),
    "t.3": _atlas_episode(3, "Memory, Honcho and Obsidian"),
    "t.4": _atlas_episode(4, "Skills that grow with the agent"),
    "t.5": _atlas_episode(5, "Providers, models and local inference"),
    "t.6": _atlas_episode(6, "Tools and MCP servers"),
    "t.7": _atlas_episode(7, "Cron and automation"),
    "t.8": _atlas_episode(8, "Subagents and delegation"),
    "t.9": _atlas_episode(9, "Profiles and Kanban"),
    "t.10": _atlas_episode(10, "Security"),
    # Tonbi on YouTube (not on Hermes Atlas)
    "t.quickstart": _youtube("Quickstart", "Zero to Working Agent in 10 Minutes", "BeWUUclCin0", "Hermes Agent Masterclass"),
    "d.1": _youtube("Part 1", "Installation, UI, Settings and Backends", "mnBQTECjvKc"),
    "d.2": _youtube("Part 2", "Working in the App", "O0VJ-anrL3Y"),
    "d.3": _youtube("Part 3", "Plugins, Kanban, Bot Mode and Pets", "O3tDjW3hHIA"),
    # Kevin Simback's guides on Hermes Atlas (author named in each page's metadata)
    "atlas.modes": _atlas_guide("guide/modes/#where-it-lives", "Where Hermes lives"),
    "atlas.memory": _atlas_guide("guide/memory/", "The Hermes Agent Memory Guidebook"),
    "atlas.desktop": _atlas_guide("guide/desktop/", "Hermes Desktop: the complete guide"),
    # The Hermes Bible, a searchable mirror of the docs by iamlukethedev
    "bible.desktop": _bible("user-guide/desktop", "Desktop app"),
    "bible.sessions": _bible("user-guide/sessions", "Sessions"),
    "bible.memory": _bible("user-guide/features/memory", "Memory"),
    "bible.skills": _bible("user-guide/features/skills", "Skills"),
    "bible.cron": _bible("guides/automate-with-cron", "Automate with cron"),
    "bible.docker": _bible("user-guide/docker", "Docker"),
    "bible.mcp": _bible("guides/use-mcp-with-hermes", "Use MCP with Hermes"),
    "bible.security": _bible("user-guide/security", "Security"),
    "bible.multi_profile": _bible("user-guide/multi-profile-gateways", "Multi-profile gateways"),
    "bible.delegation": _bible("user-guide/features/delegation", "Delegation"),
    "bible.kanban": _bible("user-guide/features/kanban", "Kanban"),
    "bible.checkpoints": _bible("user-guide/checkpoints-and-rollback", "Checkpoints and rollback"),
    "bible.learning_path": _bible("getting-started/learning-path", "Learning path"),
    # Tony Simons
    "tony.1": _tony(1, "How Hermes Agent actually processes work"),
    "tony.2": _tony(2, "The choices that compound"),
    "tony.3": _tony(3, "The learning system"),
    "tony.4": _tony(4, "Skills as executable SOPs"),
    "tony.5": _tony(5, "Tools and toolsets"),
    "tony.6": _tony(6, "Cron as infrastructure"),
    "tony.7": _tony(7, "Messaging gateways"),
    "tony.8": _tony(8, "Delegation and subagents"),
    "tony.9": _tony(9, "Browser and computer use"),
    "tony.10": _tony(10, "Kanban as coordination"),
    "tony.11": _tony(11, "The admin layer"),
    "tony.12": _tony(12, "What to skip, what breaks, how to stay sane"),
    # The services-business labs (School of Hermes)
    "lab.1": _lab(1, "Find the first client problem"),
    "lab.2": _lab(2, "Scope and price the engagement"),
    "lab.3": _lab(3, "Install for a client"),
    "lab.4": _lab(4, "Integrate the client's workflow"),
    "lab.5": _lab(5, "Test and obtain client acceptance"),
    "lab.6": _lab(6, "Train users and hand over"),
    "lab.7": _lab(7, "Package ongoing maintenance"),
    "lab.8": _lab(8, "Support, improve, and renew"),
}

# Each mission's "Learn more" list, official docs first. The commercial missions
# have no Tonbi episode because none of his walkthroughs cover selling or
# scoping client work; the services labs carry them.
WATCH = {
    "operator.runtime": ["nous.desktop", "t.1", "atlas.modes", "bible.desktop", "tony.1"],
    "operator.desktop": ["nous.sessions", "d.2", "atlas.desktop", "bible.sessions"],
    "operator.learning": ["nous.memory", "t.3", "t.4", "atlas.memory", "bible.memory", "bible.skills", "tony.3", "tony.4"],
    "operator.automation": ["nous.cron", "t.7", "bible.cron", "tony.6"],
    "integrator.discovery": ["nous.learning_path", "lab.1", "lab.2", "tony.2"],
    "integrator.deploy": ["nous.docker", "t.2", "atlas.modes", "bible.docker", "lab.3"],
    "integrator.connect": ["nous.mcp", "t.6", "bible.mcp", "bible.security", "lab.4"],
    "integrator.handoff": ["nous.checkpoints", "lab.5", "lab.6", "lab.7", "bible.checkpoints"],
    "architect.estate": ["nous.profiles", "t.9", "bible.multi_profile", "tony.11"],
    "architect.governance": ["nous.security", "t.10", "bible.security", "tony.12"],
    "architect.operations": ["nous.delegation", "t.8", "t.9", "bible.delegation", "bible.kanban", "tony.10"],
    "architect.reliability": ["nous.checkpoints", "t.2", "bible.checkpoints", "lab.8"],
    "ambassador.firsthand": ["nous.quickstart", "t.quickstart", "d.2", "tony.1"],
    "ambassador.story": ["nous.quickstart", "d.1", "atlas.modes", "bible.learning_path", "tony.1"],
    "ambassador.qualify": ["nous.learning_path", "lab.1", "lab.2", "tony.2"],
    "ambassador.handoff": ["nous.learning_path", "lab.6", "lab.8", "tony.12"],
}


def unwatched_missions():
    """Missions with nothing to read behind them. Empty is the healthy answer."""
    return [mission_id for mission_id, keys in WATCH.items() if not keys]


def lesson(step_id, title, body, source, *, deliverable=""):
    return {
        "id": step_id,
        "kind": "lesson",
        "title": title,
        "body": body,
        "source": source,
        "action": "read",
        "deliverable": deliverable,
    }


def lab(step_id, title, body, *, action="coach", route="", route_label="", prompt="", deliverable=""):
    return {
        "id": step_id,
        "kind": "lab",
        "title": title,
        "body": body,
        "action": action,
        "route": route,
        "route_label": route_label,
        "prompt": prompt,
        "deliverable": deliverable,
    }


def gate(step_id, title, body, *, verify, proof, check="", headings=(), deliverable=""):
    return {
        "id": step_id,
        "kind": "gate",
        "title": title,
        "body": body,
        "action": "verify",
        "verify": verify,
        "check": check,
        "proof": proof,
        "headings": [h.lower() for h in headings],
        "deliverable": deliverable,
    }


def mission(mission_id, title, promise, outcome, sources, steps, *, level, minutes, field_case=""):
    if level not in LEVELS:
        raise ValueError(f"Unknown level for {mission_id}: {level}")
    return {
        "id": mission_id,
        "title": title,
        "promise": promise,
        "outcome": outcome,
        "level": level,
        "level_name": LEVEL_NAMES[level],
        "minutes": minutes,
        "source_ids": sources,
        "field_case": field_case,
        "steps": steps,
    }


def _document_gate(title, headings, kind_of_document):
    return gate(
        "gate",
        title,
        (
            f"Write your {kind_of_document} as a text or Markdown file with the sections below, save it, "
            "and type where you saved it. It passes when every section is there and the document runs "
            "longer than a few lines."
        ),
        verify="artifact",
        check=kind_of_document,
        headings=headings,
        proof=(
            f"Your {kind_of_document}, saved on your computer, with all {len(headings)} sections. "
            "Its fingerprint goes on your Field Record."
        ),
    )


TRACKS = {
    "ambassador": {
        "name": "Messenger",
        "lore": (
            "Hermes's first job was carrying word between the gods and people. Here that job is yours: "
            "say what Hermes is, honestly, to someone who has never used it."
        ),
        "eyebrow": "For introductions",
        "promise": "Watch Hermes do a real job, explain it honestly, spot a real opportunity, and pass it to the person who will build it.",
        "proof": "A two-minute explanation, notes on a real opportunity, and a clean handoff to the builder.",
        "level_meanings": {
            "beginner": "You can explain Hermes in two minutes, limits included.",
            "intermediate": "You can tell real interest from a real opportunity.",
            "advanced": "You can pass an opportunity to the builder without losing anything.",
        },
        "missions": [
            mission(
                "ambassador.firsthand",
                "Watch Hermes do one real job",
                "You can explain Hermes honestly once you have watched it work. Give it one small job from your own week and see what happens.",
                "First-hand notes on one real job: what Hermes did, what it got wrong, and what you would tell a client.",
                ["tonbi_desktop", "official_quickstart"],
                [
                    lesson(
                        "concept",
                        "Watch it work before you explain it",
                        "Before you explain Hermes to anyone, give it one small real job from your own work and watch it. You describe the job in plain words, and Hermes works through the steps with the tools and accounts you allow. Watch each step, because Tonbi points out that Hermes can do things you won't notice unless you look closely at the tool calls. Write down what the job was, what Hermes did, what it got wrong or needed help with, and what you would honestly tell a client. Those notes are first-hand, so your two-minute explanation rests on something you saw.",
                        "tonbi_desktop",
                    ),
                    lab(
                        "firsthand",
                        "Give Hermes one real job",
                        (
                            "1. Pick one small job from your own work that takes you under an hour.\n"
                            "2. Send the practice chat and describe the job.\n"
                            "3. Watch each step Hermes takes.\n"
                            "4. Write your notes as a file with the four sections the check asks for."
                        ),
                        action="coach",
                        prompt="I want to watch you do one small real job from my own work before I explain you to anyone. I will describe the job next. Before you start, tell me what you can do with the tools and accounts I have allowed, and what I will need to do or paste in myself. As you work, say each step in plain words. When you finish, tell me honestly what you got wrong, what you weren't sure about, and where I had to help. Then help me write notes with four headings: The job, What Hermes did, What went wrong, What I would tell a client.",
                    ),
                    _document_gate(
                        "Check your first-hand notes",
                        ["The job", "What Hermes did", "What went wrong", "What I would tell a client"],
                        "first-hand notes",
                    ),
                ],
                level="beginner",
                minutes=30,
            ),
            mission(
                "ambassador.story",
                "Explain Hermes in two minutes",
                "Overselling loses technical buyers in the first sentence. Lead with what Hermes does and what it leaves out.",
                "A two-minute explanation that holds up with a skeptic and credits the people who built Hermes.",
                ["official_desktop", "tonbi_desktop", "tony"],
                [
                    lesson(
                        "concept",
                        "Say the limits first",
                        "A strong introduction covers four things: what Hermes does, where it runs, what it takes to look after, and what it won't do. The fourth one earns the meeting, because most vendors skip it. Say that Hermes is open source, that Nous Research maintains it, that the best teaching comes from named people in the community, and that someone has to own every setup.",
                        "official_desktop",
                    ),
                    lab(
                        "pitch",
                        "Explain it to a skeptic",
                        "Hermes plays an operations director who has heard four AI pitches this month.",
                        action="coach",
                        prompt="Act as a skeptical operations director who has heard four AI pitches this month. Ask me what Hermes is, where it runs, what it takes to look after, and what it won't do. Interrupt me if I use a word a business person wouldn't use, or claim something I can't show. After two minutes, tell me the one sentence that landed.",
                    ),
                    _document_gate(
                        "Check your two-minute explanation",
                        ["What it is", "Where it runs", "What it takes", "What it will not do", "Credit"],
                        "two-minute explanation",
                    ),
                ],
                level="beginner",
                minutes=30,
            ),
            mission(
                "ambassador.qualify",
                "Spot a real opportunity",
                "A real opportunity has a task that repeats, someone who owns it, someone who can approve spending, and a small first step.",
                "A clear yes, later or no on a prospect, with your reasons written down.",
                ["tony", "official_quickstart"],
                [
                    lesson(
                        "concept",
                        "Four signs of a real opportunity",
                        "A real opportunity has a task that repeats, a person who feels the pain of it, someone who can approve spending, and a first step small enough to sell. If one is missing, keep talking and hold off on a quote. Write your decision down with your reasons, so the person who builds it later knows what you knew.",
                        "tony",
                    ),
                    lab(
                        "roleplay",
                        "Practice with an eager prospect",
                        "Hermes plays a business owner who loves the idea of AI and has no clear task, owner or budget.",
                        action="coach",
                        prompt="Play a business owner who is excited about AI and has no clear problem. Sound promising. Let me run the conversation, and don't make it easy: stay vague about how often the work happens, who owns it, and the budget until I ask directly. At the end, tell me whether this is a yes, a later or a no, and quote the moment the answer became clear.",
                    ),
                    _document_gate(
                        "Check your opportunity notes",
                        ["Prospect", "Workflow", "Owner", "Systems", "Authority", "Decision", "Next step"],
                        "opportunity notes",
                    ),
                ],
                level="intermediate",
                minutes=30,
            ),
            mission(
                "ambassador.handoff",
                "Pass the opportunity to the builder",
                "Trust breaks when the builder hears something different from what you promised.",
                "A handoff note that keeps what's known apart from what was promised.",
                ["tony", "official_desktop"],
                [
                    lesson(
                        "concept",
                        "Keep what you know apart from what you promised",
                        "A handoff note has four sections: what we know, what we promised, what still needs checking, and who owns each next step. Keep the middle two apart. Mixed together, a casual promise turns into a requirement the builder never agreed to. Write the note while you still remember who said what, and send it before the joint call.",
                        "tony",
                    ),
                    lab(
                        "rehearse",
                        "Practice the joint call",
                        "Hermes plays both the client and the builder who takes over. You introduce them and stay on the call.",
                        action="coach",
                        prompt="Practice a handoff call with me. You play both the client and the builder who takes over. Make me say what we know, what we promised, what still needs checking, and who owns each next step, in front of both of you. Correct me if I retell the client's story wrong or answer a question that belongs to the builder.",
                    ),
                    _document_gate(
                        "Check your handoff note",
                        ["Known", "Promised", "Validate", "Owner", "Next step"],
                        "handoff note",
                    ),
                ],
                level="advanced",
                minutes=30,
            ),
        ],
    },
    "operator": {
        "name": "Traveler",
        "lore": (
            "Hermes looked after people on the road. You get Hermes running on your own computer and "
            "keep it running."
        ),
        "eyebrow": "For yourself",
        "promise": "Run Hermes on your own computer and keep one daily job working.",
        "proof": "Hermes is connected, your chats are saved, your skills are set up, and a job runs on a schedule.",
        "level_meanings": {
            "beginner": "You know where Hermes is running and what the app keeps when you close it.",
            "intermediate": "Hermes remembers how you work, so you stop repeating yourself.",
            "advanced": "Hermes does a job for you on a schedule, without you asking.",
        },
        "missions": [
            mission(
                "operator.runtime",
                "Find where Hermes is running",
                "Hermes runs on one particular computer, under one particular setup. Knowing which one tells you where to look when something doesn't happen.",
                "You can name the computer and the profile your chats run on.",
                ["official_desktop", "tonbi_terminal", "tonbi_desktop"],
                [
                    lesson(
                        "concept",
                        "Four parts that all get called Hermes",
                        "The app is the window you type in. A session is one conversation. A profile is one complete Hermes setup, with its own memory, skills, and passwords and service keys. The gateway is the background program that runs scheduled jobs and answers messages from your phone. Installed as a background service, it keeps going while the app is closed. On this computer the open app also runs your jobs when no gateway is running, and stops them when you quit it. When something you expected doesn't happen, check what runs the jobs first. The app can look fine while the gateway on another computer has stopped.",
                        "tonbi_desktop",
                    ),
                    lab(
                        "locate",
                        "Look up your connection",
                        "Open Gateways in Settings. Read which connection you're on: this computer, another computer (a remote gateway, or SSH, a secure remote connection), or Hermes Cloud. Note the profile name too.",
                        action="route",
                        route="/settings?tab=gateway",
                        route_label="Open Gateways",
                    ),
                    gate(
                        "gate",
                        "Check that Hermes is connected",
                        "Click Check my work. It passes when Hermes answers and this window has an open connection to it.",
                        verify="desktop",
                        check="runtime",
                        proof="Hermes answers, and this window is connected to it.",
                    ),
                ],
                level="beginner",
                minutes=10,
            ),
            mission(
                "operator.desktop",
                "Learn what the app keeps when you close it",
                "Some things keep running when you close them, and some are saved for later. Knowing which is which keeps you from losing work.",
                "You finish one small task in the app and know where each piece is saved.",
                ["official_desktop", "tonbi_desktop"],
                [
                    lesson(
                        "concept",
                        "What happens when you close something",
                        "Hiding a terminal or browser pane tucks it away, and whatever runs inside keeps running, so a long task carries on while you read something else. Closing its tab with the x stops it. Sessions are saved and come back after a restart. A project groups the sessions that work in the same folder. The command palette (Cmd-K) reaches every action in the app, including the ones with no button on screen.",
                        "tonbi_desktop",
                    ),
                    lab(
                        "workflow",
                        "Finish one small task in the app",
                        "Ask Hermes to walk you through a small real task: start a project, run one terminal command, preview a file, and keep what you made.",
                        action="coach",
                        prompt="Walk me through one small real task in the Hermes app, one step at a time: start a project, run one terminal command, preview a file, and save the result. After each step, tell me where that piece is saved and what happens to it if I close the window.",
                    ),
                    gate(
                        "gate",
                        "Check that your sessions are saved",
                        "Click Check my work. It passes when Hermes lists at least one saved session.",
                        verify="desktop",
                        check="workspace",
                        proof="Hermes lists at least one saved session.",
                    ),
                ],
                level="beginner",
                minutes=15,
            ),
            mission(
                "operator.learning",
                "Make Hermes remember how you work",
                "Hermes keeps facts, past chats and how-tos in three different places. Put each one in the right place and you stop repeating yourself.",
                "A fact you tell Hermes once comes back in a new chat.",
                ["official_tools", "tonbi_terminal", "tony"],
                [
                    lesson(
                        "concept",
                        "Where a fact goes, and where a how-to goes",
                        "Memory is a short list of facts about you that Hermes reads at the start of every chat, so keep it small. Your past chats are an archive Hermes can search when you ask what you decided last month. A skill is a saved set of steps that Hermes opens when your request matches it. Put facts in memory and step-by-step how-tos in a skill. A long how-to in memory gets read in every chat and costs you on each one.",
                        "tony",
                    ),
                    lab(
                        "memory",
                        "Save one fact and get it back",
                        "Pick a preference you're tired of repeating. Ask Hermes to remember it, start a new chat, and ask for it back.",
                        action="coach",
                        prompt="Help me save one fact about how I work so you remember it in every new chat. Go one step at a time. Then tell me where you saved it, and how that differs from my past chats and from a skill.",
                    ),
                    gate(
                        "gate",
                        "Check that skills and tools are set up",
                        "Click Check my work. It passes when Hermes lists at least one installed skill and one set of tools.",
                        verify="desktop",
                        check="knowledge",
                        proof="Hermes lists at least one installed skill and one set of tools.",
                    ),
                ],
                level="intermediate",
                minutes=15,
            ),
            mission(
                "operator.automation",
                "Put one job on a schedule",
                "A scheduled job runs a request on a timer, so a daily summary or check shows up without you asking.",
                "One scheduled job you can read, run and fix.",
                ["official_quickstart", "tonbi_terminal", "tony"],
                [
                    lesson(
                        "concept",
                        "A scheduled job starts with a blank page",
                        "When you chat, Hermes sees the whole conversation. A scheduled job sees none of it: no earlier messages, no open files, nothing you decided yesterday. Its request has to say where to work, what to read, what a good result looks like, where to send it, and what to do if something fails. Leave one out and the job can run for a week and deliver nothing useful.",
                        "tonbi_terminal",
                    ),
                    lab(
                        "open",
                        "Make a job you can watch",
                        "Open Scheduled jobs and make a harmless job, paused or set to run once, so you can watch it run before you rely on it.",
                        action="route",
                        route="/cron",
                        route_label="Open Scheduled jobs",
                    ),
                    gate(
                        "gate",
                        "Check that a job is scheduled",
                        "Click Check my work. It passes when Hermes lists at least one scheduled job.",
                        verify="desktop",
                        check="automation",
                        proof="Hermes lists at least one scheduled job.",
                    ),
                ],
                level="advanced",
                minutes=20,
            ),
        ],
    },
    "integrator": {
        "name": "Crossroads",
        "lore": (
            "Hermes was the god of crossroads, where roads meet. You connect Hermes to a client's "
            "tools."
        ),
        "eyebrow": "For clients",
        "promise": "Set Hermes up for a client, connect it to their tools, and hand it over.",
        "proof": "A written scope, a working connection, a tested approval step, and a handover guide.",
        "level_meanings": {
            "beginner": "You can turn a vague request into a first project with a price.",
            "intermediate": "You can choose where a client's Hermes runs and connect one of their tools safely.",
            "advanced": "You can hand over a setup the client's own staff can run.",
        },
        "missions": [
            mission(
                "integrator.discovery",
                "Turn a vague request into a first project",
                "Clients often ask for \"an AI agent.\" Find the one task that wastes someone's afternoon before you quote a price.",
                "A one-page scope for a first project, with what it leaves out written down.",
                ["tony", "official_quickstart"],
                [
                    lesson(
                        "concept",
                        "Six questions for the first meeting",
                        "Ask six questions: which work repeats, who owns the result, which systems it touches, what a good result looks like in numbers, what happens when it's wrong, and who signs off. Then write down what the project leaves out. That list is what you point to in month two, when the client asks for something you agreed to leave out. Last, put a price on the first project: a setup fee and a monthly fee for looking after it.",
                        "tony",
                    ),
                    lab(
                        "interview",
                        "Practice the first meeting",
                        "Hermes plays a contractor who wants \"an AI agent for the business\" and stays vague until you ask the right questions.",
                        action="coach",
                        prompt="Play a mid-size contractor who wants 'an AI agent for the business.' Stay vague unless I ask something specific: don't volunteer the task, the owner, the systems, the budget, or who signs off. I'm going to run the first meeting. When I stop, tell me which of the six things I never found out, and quote the question that came closest.",
                    ),
                    _document_gate(
                        "Check your scope document",
                        ["Client", "Workflow", "Owner", "Systems", "Acceptance", "Out of scope", "Price"],
                        "scope document",
                    ),
                ],
                level="beginner",
                minutes=45,
            ),
            mission(
                "integrator.deploy",
                "Choose where Hermes runs for a client",
                "Hermes can run on a laptop, a rented server or Hermes Cloud. The real difference is who fixes it when it stops.",
                "You can say where the client's Hermes runs, and who looks after it.",
                ["official_multi", "tonbi_terminal", "tony"],
                [
                    lesson(
                        "concept",
                        "Four questions for any setup",
                        "For each option, ask whose computer it is, whose passwords are stored on it, who installs the updates, and who gets the call when it stops at 2am. A laptop costs nothing extra and stops when someone closes the lid. A rented server costs money each month and needs someone to keep it updated. Hermes Cloud looks after the computer, and you still own the account and the bill.",
                        "official_multi",
                    ),
                    lab(
                        "gateways",
                        "Look at your own setup",
                        "Open Gateways and follow the route from this window to the computer that does the work.",
                        action="route",
                        route="/settings?tab=gateway",
                        route_label="Open Gateways",
                    ),
                    gate(
                        "gate",
                        "Check that the connection route works",
                        "Click Check my work. It passes when this window can name the Hermes setup it's connected to.",
                        verify="desktop",
                        check="routes",
                        proof="This window names the Hermes setup it's connected to.",
                    ),
                ],
                level="intermediate",
                minutes=20,
            ),
            mission(
                "integrator.connect",
                "Connect one client tool safely",
                "Each tool you connect gives Hermes something new it can do, and something new that can go wrong.",
                "One tool connected, with an approval step you've tested.",
                ["official_tools", "tonbi_terminal"],
                [
                    lesson(
                        "concept",
                        "Give the smallest permission that works",
                        "Once Hermes can send email, it can send the wrong email. Once it can read a shared drive, it can read everything on that drive. Before you connect anything, write down the smallest permission that still does the job, and who approves anything Hermes sends out. Hermes asks before it runs a risky command on the computer. A connected tool acts without asking unless its MCP server is marked trust: untrusted in config.yaml, which makes every tool that can change something ask first. So give a sending tool draft-only access, where a person presses send, and test Hermes's own approval prompt once each way.",
                        "tonbi_terminal",
                    ),
                    lab(
                        "approval",
                        "Test the approval step",
                        "Set Hermes's command approvals to manual for the test, then ask it to delete a scratch folder you made for the purpose. Turn the approval request down once, then approve it once.",
                        action="coach",
                        prompt="Help me test your approval prompt safely. Tell me how to set command approvals to manual for this test. Then I will make a scratch folder of copies, and you ask to delete it, which needs my approval. I turn it down once and approve it the second time. Tell me where each choice shows up afterward, and the smallest permission my real client tool needs, with draft-only sending where a person presses send.",
                    ),
                    gate(
                        "gate",
                        "Check your tool list",
                        "Click Check my work. It passes when Hermes lists the tools it can use. The result also counts your MCP servers, the add-ons that give Hermes new tools.",
                        verify="desktop",
                        check="connections",
                        proof="Hermes lists the tools it can use.",
                    ),
                ],
                level="intermediate",
                minutes=20,
            ),
            mission(
                "integrator.handoff",
                "Write the guide the client's staff will use",
                "A setup only one person understands stops working when that person moves on.",
                "A guide the client's own staff can follow without you.",
                ["official_desktop", "tony"],
                [
                    lesson(
                        "concept",
                        "Write for the person who takes over",
                        "The guide covers what runs where (the Topology section), who owns each part, which profiles exist, which tools are connected, where keys are kept (never the keys themselves), what each scheduled job does and when, how to restore from a backup, how to recover when it breaks, and what it leaves out on purpose. To test it, hand it to someone who has never seen the system. Watch them finish one routine task and one recovery using only the guide.",
                        "official_desktop",
                    ),
                    lab(
                        "acceptance",
                        "Practice the handover",
                        "Hermes plays the client's IT person on handover day, with only your guide to go on.",
                        action="coach",
                        prompt="Play the client's IT person on the day I hand over Hermes. You have my guide and you've never seen the system. Pick the main task and one failure, and try to finish both using only what the guide says. Stop the moment you can't follow it and tell me which line lost you.",
                    ),
                    _document_gate(
                        "Check your handover guide",
                        ["Topology", "Owners", "Profiles", "Integrations", "Secrets", "Cron", "Backups", "Recovery", "Limits"],
                        "handover guide",
                    ),
                ],
                level="advanced",
                minutes=60,
            ),
        ],
    },
    "architect": {
        "name": "Boundary Keeper",
        "lore": (
            "Stone pillars called herms marked where one property ended and the next began. You decide "
            "who owns what, who approves what, and how it recovers."
        ),
        "eyebrow": "For an organization",
        "promise": "Plan Hermes for a whole organization: who owns what, who approves what, and how it recovers.",
        "proof": "A map with owners, a written rule set, a working task board, and a recovery plan with real numbers.",
        "level_meanings": {
            "beginner": "You can map every part of an organization's Hermes setup and name its owner.",
            "intermediate": "You can decide who may approve what, and match each job to the right kind of agent.",
            "advanced": "You can show the setup recovers from a bad day and is worth what it costs.",
        },
        "missions": [
            mission(
                "architect.estate",
                "Map every part and name its owner",
                "Once a company runs more than a few agents, it gets hard to say who owns what. A map with names on it fixes that.",
                "Every agent, gateway, profile and shared service has a named owner.",
                ["official_multi", "tony"],
                [
                    lesson(
                        "concept",
                        "Draw the map before you add anything",
                        "Problems show up where things are shared: two teams on one profile, one gateway serving both payroll and a marketing test, a bot that can reach more than the person who asked for it. Draw the organization's setup: teams, gateways, profiles, bots, workspaces, models and data. Put a person's name on every part. Any part without a name is the first thing to fix.",
                        "official_multi",
                    ),
                    lab(
                        "inventory",
                        "List what you already have",
                        "Open Profiles and write down every profile on your own setup before you plan anything new. Each bot in the Bots tab is a profile too.",
                        action="route",
                        route="/profiles",
                        route_label="Open Profiles",
                    ),
                    gate(
                        "gate",
                        "Check what's registered",
                        "Click Check my work. It passes when Hermes lists at least one profile for this window.",
                        verify="desktop",
                        check="estate",
                        proof="Hermes lists at least one profile for this window.",
                    ),
                ],
                level="beginner",
                minutes=30,
            ),
            mission(
                "architect.governance",
                "Decide who can do what",
                "Someone will ask why Hermes was allowed to take an action. Write the answer down before they ask.",
                "A written list of who may ask, approve, run, inspect and recover.",
                ["tonbi_terminal", "tony"],
                [
                    lesson(
                        "concept",
                        "A document Hermes reads can give it orders",
                        "When Hermes reads a supplier's PDF, the words in that PDF reach a system that can act. One sentence hidden in a normal-looking document can redirect an outgoing message. The fix sits outside Hermes: limit what it can reach, make risky actions wait for a person, and keep a log every time. Your rules name who uses Hermes, who approves what, what data it may see, how long logs are kept, who reads them and when, who is told first when something goes wrong, and when access is reviewed.",
                        "tony",
                    ),
                    lab(
                        "threat",
                        "Practice spotting a hidden instruction",
                        "Hermes gives you a normal-looking business document with a hidden instruction inside, and asks how you'd respond.",
                        action="coach",
                        prompt="Give me one realistic business document, like an invoice or a supplier letter, that hides an instruction aimed at an AI agent. Make it look normal. Then ask me what the agent could reach, what the safe response is, what I should keep as a record, and which rule would have caught it. One scenario at a time.",
                    ),
                    _document_gate(
                        "Check your rules document",
                        ["Identities", "Approvals", "Data", "Retention", "Audit", "Incident", "Access review"],
                        "rules document",
                    ),
                ],
                level="intermediate",
                minutes=45,
            ),
            mission(
                "architect.operations",
                "Match each job to the right kind of agent",
                "A chat, a helper agent and a task board each suit work of a different length. Pick the one that fits.",
                "A small task running on the task board, with a review step.",
                ["tonbi_desktop", "tony", "official_kanban"],
                [
                    lesson(
                        "concept",
                        "Pick by how long the work lasts",
                        "A subagent is a helper Hermes starts for one task. It's quick, and it ends with that task. A bot is a named agent with its own profile and memory. A card on the Kanban board lasts through restarts and long weeks, and its description holds the definition of done and the review step. Give a two-week process a card on the board, where it can last two weeks.",
                        "official_kanban",
                    ),
                    lab(
                        "board",
                        "Put one real task on the board",
                        "Open Kanban and add one small, real task with a review step.",
                        action="route",
                        route="/kanban",
                        route_label="Open Kanban",
                    ),
                    gate(
                        "gate",
                        "Check your agent list",
                        "Click Check my work. It passes when Hermes lists at least one named agent.",
                        verify="desktop",
                        check="agents",
                        proof="Hermes lists at least one named agent.",
                    ),
                ],
                level="intermediate",
                minutes=30,
            ),
            mission(
                "architect.reliability",
                "Plan the recovery and measure the value",
                "Anyone can promise a system stays up. A recovery you've practiced and a before-and-after number hold up in a budget meeting.",
                "A recovery plan you've rehearsed, and a cost comparison with both sides measured.",
                ["tony", "official_multi", "official_kanban"],
                [
                    lesson(
                        "concept",
                        "Measure the old way too",
                        "A claim that Hermes saves time needs a number for the old way: who did the work, how long it took, how often it was wrong, and what fixing mistakes cost. Then measure the new way, including the time spent checking and fixing. The honest number is usually smaller than the pitch, and much harder to argue with. Then write the recovery side: the recovery time you promise in hours, what fails first, how you recover, and who updates Hermes and how you roll back.",
                        "tony",
                    ),
                    lab(
                        "tabletop",
                        "Practice a bad day",
                        "Hermes plays out a gateway failure in the middle of the client's most important job and asks what you do at each step.",
                        action="coach",
                        prompt="Run a practice emergency with me. The gateway fails in the middle of the job the business depends on most, at a bad moment. Ask me in order: what's affected, what I stop, whether I switch over or restore, how I check the data and the waiting work, who I tell, and what changes afterwards. Push back when I'm vague.",
                    ),
                    _document_gate(
                        "Check your recovery and value plan",
                        ["Service levels", "Failure", "Recovery", "Upgrades", "Baseline", "After", "Cost"],
                        "recovery and value plan",
                    ),
                ],
                level="advanced",
                minutes=60,
            ),
        ],
    },
}


def explain(step_id, title, question, covers, prompt, threshold=70):
    """A graded understanding step. Hermes scores the answer; 70 or more passes."""
    return {
        "id": step_id,
        "kind": "explain",
        "title": title,
        "body": question,
        "covers": covers,
        "prompt": prompt,
        "threshold": threshold,
        "action": "grade",
    }


# One question per mission, and what a strong answer covers. The learner sees
# the list only after writing an answer, and Hermes grades against the same list.
EXPLAIN = {
    "operator.runtime": {
        "title": "Explain where your work runs",
        "question": "Your scheduled morning report didn't go out, but the Hermes app on your screen was open all day, connected to another computer. Say which of the four parts you check first, which you check second, and why in that order.",
        "covers": [
            "that an open app window tells you nothing about whether scheduled work ran on the computer that runs the job",
            "that scheduled jobs need the gateway on that computer, a separate background program, to be running",
            "that the job belongs to one profile, with its own memory and passwords",
            "how you would actually confirm it instead of guessing",
        ],
    },
    "operator.desktop": {
        "title": "Explain what survives closing the app",
        "question": "You close every pane and then quit the app. Say what is still running, what comes back when you reopen it, and what is gone.",
        "covers": [
            "that hiding a pane leaves whatever runs inside it running",
            "that a session is saved and comes back after a restart",
            "that a project groups sessions that work in the same folder",
            "that anything that only ever lived in the window is gone",
        ],
    },
    "operator.learning": {
        "title": "Explain where a repeated how-to goes",
        "question": "You're tired of explaining the same five-step how-to over and over. Say where it belongs, and why the other two places are the wrong fit.",
        "covers": [
            "that a step-by-step how-to belongs in a skill",
            "that memory is a short list read in every chat, so a how-to there costs you in every chat and clashes with what you say next",
            "that past chats are an archive you search, and searching them changes nothing about how Hermes behaves",
            "that a skill opens when the request matches its description, or when you type its name as a command, so the description decides whether it opens on its own",
        ],
    },
    "operator.automation": {
        "title": "Explain what a scheduled request must say",
        "question": "A scheduled job runs at three in the morning with nobody watching. Name what its request has to say, and what goes wrong when each one is missing.",
        "covers": [
            "where to work, because there's no open conversation to borrow a folder from",
            "what to read",
            "what a good result looks like, clearly enough to tell when it fails",
            "where to send the result, or nobody sees it",
            "what to do when something fails, or a broken job fails quietly for a week",
        ],
    },
    "integrator.discovery": {
        "title": "Explain what you need from the first meeting",
        "question": "A client says they want an AI agent for the business. Name what you need to find out before you quote a price, and the one line of the scope that protects you two months later.",
        "covers": [
            "which work repeats often enough to be worth automating",
            "who owns the result, by name",
            "which systems the work touches",
            "what a good result looks like in a number, so everyone agrees when it's done",
            "what happens when it's wrong, since that decides how much checking the work needs",
            "who signs off, as distinct from who is enthusiastic",
            "that the list of what's left out is what you point to in month two",
        ],
    },
    "integrator.deploy": {
        "title": "Explain how you choose where it runs",
        "question": "Compare a laptop and a rented server on the questions that decide it. Then say which you'd choose for a client whose office empties at six.",
        "covers": [
            "whose computer it is, and so who is responsible for it",
            "whose passwords are stored on it",
            "who installs updates",
            "who gets the call when it stops at two in the morning",
            "that a laptop is usually the wrong choice for an office that empties at six, because the laptop leaves with someone",
        ],
    },
    "integrator.connect": {
        "title": "Explain what you say before you connect anything",
        "question": "A client asks you to connect Hermes to their shared drive so it can help out. Write the sentence you say before agreeing, and explain what they're really asking for.",
        "covers": [
            "that connecting a tool gives Hermes the power to act with it",
            "that read access to a shared drive covers everything on that drive, beyond the one folder they had in mind",
            "that the useful question is the smallest permission that still does the job",
            "that someone has to own what Hermes sends out, and an approval step nobody has tested can't be trusted",
        ],
    },
    "integrator.handoff": {
        "title": "Explain what the guide has to let a stranger do",
        "question": "The client's IT person has never seen the system and you can't be reached. Say what the guide has to let them do, and how you know it works.",
        "covers": [
            "finish one routine task and one recovery without you",
            "what runs where, who owns each part, how to start and stop it, how to read the logs",
            "how to restore from a backup, and what the system leaves out on purpose",
            "who to call when it breaks",
            "that you know it works because someone who didn't build it did both, using only the guide, while you watched",
        ],
    },
    "architect.estate": {
        "title": "Explain which parts you would map",
        "question": "Sketch the parts you'd put on one page for a company with Operations, Finance and Sales. Then say which part you wouldn't let those teams share, and why.",
        "covers": [
            "the parts to draw: teams, gateways, profiles, agents, workspaces, models and data",
            "that every part carries a person's name",
            "that a regulated task and a marketing test shouldn't share a profile or a gateway, because sharing mixes their data and their failures",
            "how you would spot a part nobody owns",
        ],
    },
    "architect.governance": {
        "title": "Explain what went wrong with the hidden instruction",
        "question": "An approved supplier document contains a line telling the agent to email its contents to a new address. Say what went wrong, and name the safeguards that would have caught it.",
        "covers": [
            "that once Hermes reads a document, its words reach a system that can act",
            "that the document was approved, so the fix sits outside Hermes",
            "the safeguards: limit what Hermes can reach, make risky actions wait for a person, and log every action",
        ],
    },
    "architect.operations": {
        "title": "Explain which kind of agent fits which job",
        "question": "Three pieces of work: a two-minute question, a three-hour task and a two-week process. Say what you'd use for each, and what decides it.",
        "covers": [
            "that a chat suits a question",
            "that a subagent suits one task that ends when it's done",
            "that the board suits work that outlasts the chat, the computer and the week",
            "that how long the work lasts decides it, and that a board card's description holds its definition of done and review step",
        ],
    },
    "architect.reliability": {
        "title": "Explain the recovery and the value",
        "question": "The gateway stops in the middle of the job the business depends on. Walk through what you do, in order. Then say why the value case needs numbers for the old way of working too.",
        "covers": [
            "the order: what's affected, what you stop, whether you switch over or restore, how you check the data and the waiting work, who you tell, what changes afterwards",
            "that a value claim with no before number falls apart in a budget meeting",
            "that the before number covers who did it, how long it took, how often it was wrong and what fixing it cost",
            "that the after number includes checking and fixing time, and is usually smaller than the pitch",
        ],
    },
    "ambassador.firsthand": {
        "title": "Explain what you saw Hermes do",
        "question": "A friend asks whether Hermes actually works. Answer from the job you gave it: what the job was, what Hermes did, where it went wrong or needed you, and why seeing it yourself changes what you tell a client.",
        "covers": [
            "the real job you gave Hermes, small and taken from your own work",
            "what Hermes actually did, step by step, with the tools and accounts you allowed",
            "one thing it got wrong or needed your help with, said plainly",
            "that first-hand notes keep your explanation honest, because you describe what you watched happen",
        ],
    },
    "ambassador.story": {
        "title": "Explain Hermes to a skeptic in four sentences",
        "question": "Say what Hermes is, where it runs, what it takes to look after, and what it won't do. Then say why the last sentence wins the meeting.",
        "covers": [
            "that it's an open source agent someone runs and owns, with no company hosting it for you by default",
            "where it runs, in plain words",
            "that a real setup needs an owner, upkeep and money",
            "a real limit, stated plainly",
            "that the limit earns the meeting, because most vendors skip it",
            "credit to Nous Research and to the people whose teaching this rests on",
        ],
    },
    "ambassador.qualify": {
        "title": "Explain how you decide it's real",
        "question": "An eager prospect loves AI and can't name a task. Name what would make it a real opportunity, and say what you do when most of it is missing.",
        "covers": [
            "a task that repeats often enough to matter",
            "an owner who feels the pain personally, as distinct from someone who likes the idea",
            "someone who can approve spending",
            "a first step small enough to sell",
            "that with most of these missing, you keep talking and hold off on a quote",
            "that the decision gets written down with the reasons, so the later handoff is honest",
        ],
    },
    "ambassador.handoff": {
        "title": "Explain how you hand off cleanly",
        "question": "On a call you said, \"we can probably automate that.\" Name the four parts of the handoff note, say which part that sentence goes in, and why it matters.",
        "covers": [
            "the four parts: what we know, what we promised, what still needs checking, and who owns each next step",
            "that the sentence is a promise, and it belongs apart from the known facts",
            "that mixing the two turns a casual remark into a requirement the builder never agreed to",
            "that the note goes out before the joint call, while you still remember who said what",
        ],
    },
}

_MISSION_INDEX = [(item["id"], item) for track in TRACKS.values() for item in track["missions"]]
for _mission_id, _mission in _MISSION_INDEX:
    _spec = EXPLAIN.get(_mission_id)
    if not _spec:
        continue
    _gate_index = next(
        (index for index, step in enumerate(_mission["steps"]) if step["kind"] == "gate"),
        len(_mission["steps"]),
    )
    _mission["steps"].insert(_gate_index, explain("explain", _spec["title"], _spec["question"], _spec["covers"], _spec.get("prompt", ""), _spec.get("threshold", 70)))

# ── Content merge ────────────────────────────────────────────────────────────
#
# The structure above is the 0.4 curriculum. What 0.5 adds sits in content/:
# a worked example and a half-finished one for every mission, stronger checks,
# coaching hints, review questions, the capstone and the placement check for
# every path. Merging it here keeps one place that decides step order.

CONTENT = _content.all_missions()
CAPSTONES = _content.capstones()
PLACEMENTS = _content.placements()

REVISIONS_VERSION = "0.5.0"
REVISIONS_DATE = "2026-10-03"


def _minutes(spec, kind, fallback):
    return int((spec.get("minutes") or {}).get(kind, fallback))


def _example_step(spec):
    worked = spec["worked"]
    step = {
        "id": "example",
        "kind": "example",
        "title": worked.get("title") or "See it done",
        "body": worked["intro"],
        "parts": deepcopy(worked.get("parts", [])),
        "document": worked.get("document", ""),
        "action": "read",
        "support": "full",
        "deliverable": "",
    }
    return step


def _complete_step(spec):
    done = spec["complete"]
    return {
        "id": "complete",
        "kind": "complete",
        "title": done.get("title") or "Your turn: finish it",
        "body": done["intro"],
        "parts": deepcopy(done["parts"]),
        "action": "fill",
        "support": "half",
        "deliverable": "",
    }


def _build_gate(spec):
    sections = deepcopy(spec.get("sections", []))
    verify = spec["verify"]
    return {
        "id": "gate",
        "kind": "gate",
        "title": spec["title"],
        "body": spec["body"],
        "action": "verify",
        "verify": verify,
        "check": spec.get("check", ""),
        "proof": spec["proof"],
        "headings": [rule["heading"] for rule in sections],
        "sections": sections,
        "cross": spec.get("cross", ""),
        "live": spec.get("live", ""),
        "inputs": deepcopy(spec.get("inputs", [])),
        "marker": spec.get("marker", ""),
        "fixes": deepcopy(spec.get("fixes", {})),
        "support": "none",
        "deliverable": "",
    }


def _capstone_mission(track_id, spec):
    steps = [
        lesson("concept", spec["lesson"]["title"], spec["lesson"]["body"], spec["lesson"]["source"]),
        lab("lab", spec["lab"]["title"], spec["lab"]["body"], action="coach", prompt=spec["lab"]["prompt"]),
        explain("explain", spec["explain"]["title"], spec["explain"]["question"], spec["explain"]["covers"], "", 70),
        gate("gate", spec["gate"]["title"], spec["gate"]["body"], verify="artifact", proof=spec["gate"]["proof"]),
    ]
    return mission(
        spec["id"], spec["title"], spec["promise"], spec["outcome"], spec["sources"], steps,
        level="capstone", minutes=0,
    )


def _apply_content():
    for track_id, spec in CAPSTONES.items():
        if track_id in TRACKS and not any(item["id"] == spec["id"] for item in TRACKS[track_id]["missions"]):
            TRACKS[track_id]["missions"].append(_capstone_mission(track_id, spec))
            TRACKS[track_id]["level_meanings"]["capstone"] = spec["level_meaning"]
            CONTENT[spec["id"]] = spec
            WATCH[spec["id"]] = list(spec.get("watch", []))
    for track in TRACKS.values():
        for item in track["missions"]:
            spec = CONTENT.get(item["id"])
            if not spec:
                continue
            steps = item["steps"]
            lab_step = next((s for s in steps if s["kind"] == "lab"), None)
            if lab_step is not None:
                lab_step.update({k: v for k, v in (spec.get("lab") or {}).items() if k in ("title", "body", "prompt", "route", "route_label", "action")})
                lab_step["support"] = "none"
            explain_step = next((s for s in steps if s["kind"] == "explain"), None)
            if explain_step is not None:
                coach = spec.get("coach") or (spec.get("explain") or {}).get("coach") or []
                explain_step["coach"] = deepcopy(coach)
                explain_step["support"] = "none"
            if spec.get("gate"):
                index = next(i for i, s in enumerate(steps) if s["kind"] == "gate")
                steps[index] = _build_gate(spec["gate"])
            if spec.get("worked") and spec.get("complete"):
                if spec.get("story_first"):
                    # The story teaches the idea; the lesson follows it as a short takeaway.
                    steps[0:0] = [_example_step(spec)]
                    steps[2:2] = [_complete_step(spec)]
                else:
                    steps[1:1] = [_example_step(spec), _complete_step(spec)]
            takeaway = spec.get("takeaway")
            if takeaway:
                lesson_step = next((s for s in steps if s["kind"] == "lesson"), None)
                if lesson_step is not None:
                    lesson_step["title"] = takeaway.get("title") or lesson_step["title"]
                    lesson_step["lines"] = list(takeaway.get("lines", []))
                    lesson_step["picture"] = takeaway.get("picture", "")
                    lesson_step["body"] = " ".join(takeaway.get("lines", [])) or lesson_step["body"]
            item["story_first"] = bool(spec.get("story_first"))
            minutes = spec.get("minutes") or {}
            for step in steps:
                step["minutes"] = int(minutes.get(step["kind"], 0))
            item["time"] = {k: int(v) for k, v in minutes.items()}
            if minutes:
                item["minutes"] = sum(int(v) for v in minutes.values())
            item["use"] = spec.get("use", "")
            item["use_plain"] = spec.get("use_plain", "")
            item["review"] = deepcopy(spec.get("review", []))


def _revisions():
    out = []
    for mission_id, spec in CONTENT.items():
        for entry in spec.get("revisions", []):
            out.append({
                "id": f"{mission_id}@{entry['version']}",
                "mission_id": mission_id,
                "version": int(entry["version"]),
                "kind": entry.get("kind", "content"),
                "released": entry.get("released", REVISIONS_VERSION),
                "date": entry.get("date", REVISIONS_DATE),
                "summary": entry["summary"],
            })
    for released, date, revisions in RELEASES:
        for mission_id, entries in revisions.items():
            base = max([r["version"] for r in out if r["mission_id"] == mission_id] or [1])
            for offset, (kind, summary) in enumerate(entries, start=1):
                out.append({
                    "id": f"{mission_id}@{base + offset}",
                    "mission_id": mission_id,
                    "version": base + offset,
                    "kind": kind,
                    "released": released,
                    "date": date,
                    "summary": summary,
                })
    out.sort(key=lambda r: (r["date"], r["mission_id"], r["version"]))
    return out


# What 0.7.0 changed, mission by mission, after checking every lesson against the Hermes docs.
# Each entry bumps that mission's version by one, so a learner who passed it sees the change.
RELEASE_VERSION = "0.7.0"
RELEASE_DATE = "2026-10-05"
RELEASE_REVISIONS = {
    "operator.runtime": [("content", "The lesson now says the gateway keeps running with the app closed when it is installed as a background service, and Gateways names the hosted option Hermes Cloud.")],
    "operator.desktop": [("content", "The lesson now says hiding a terminal or browser pane keeps it running, and closing its tab with the x stops it.")],
    "operator.learning": [("content", "The check now reads your skills fresh, so a skill you just made shows without restarting Hermes. The lesson notes that a skill also opens when you type its name.")],
    "operator.automation": [("check", "The check now finds paused jobs, and because Hermes shows only the first 100 characters of a job's request, you paste the whole request and it must begin the way Hermes shows it.")],
    "integrator.discovery": [("content", "The lesson now asks you to price the first project, which the check has always asked for.")],
    "integrator.deploy": [("content", "The hosted option is now called Hermes Cloud, the name Gateways uses.")],
    "integrator.connect": [("content", "The approval test now uses Hermes's own approval prompt for a risky command, because Hermes does not ask before a connected tool acts. Sending tools get draft-only access so a person presses send.")],
    "integrator.handoff": [("content", "The lesson now names every section the check reads: profiles, connected tools, where keys are kept and the scheduled jobs.")],
    "architect.governance": [("content", "The lesson now names every section of the rules document, and the examples point to Hermes's session history and logs.")],
    "architect.reliability": [("content", "The lesson now covers the recovery side the check reads: the recovery time you promise, and who updates Hermes and how you roll back.")],
}

# What 0.8.1 changed, after checking every lesson and check against the Hermes 0.22.0 source
# (October 15, 2026). The audit table is kept outside the repository.
RELEASE_081_VERSION = "0.8.1"
RELEASE_081_DATE = "2026-10-15"
RELEASE_081_REVISIONS = {
    "operator.runtime": [("content", "Hermes 0.22 changed two things this mission teaches. On this computer the open app now runs your scheduled jobs when no gateway is running, so quitting it stops them. And Gateways shows the computer, not the profile: the lesson now has you read the profile from the sidebar, and the connection shows as Connected in the status bar.")],
    "operator.desktop": [("content", "The app now keeps the text of a message you never sent. The lesson's examples now use a terminal closed with the x and a file attached to an unsent message, which are still gone after a restart.")],
    "integrator.deploy": [("content", "The fixes now name the labels Hermes shows: Connected in the status bar, Test and Reachable in Gateways, and the profile in the sidebar. A job missed while the laptop is shut runs once, late, when it wakes.")],
    "integrator.connect": [("content", "Marking an MCP server trust: untrusted in config.yaml now makes its tools that can change things ask first. The lesson says so, and the check now counts tools inside Hermes's toolsets.")],
    "architect.estate": [("content", "The Agents page shows only live helper agents now, so the lab opens Profiles, where every profile and bot is listed, and the check reads the profiles this window can reach.")],
    "architect.governance": [("content", "Hermes deletes ended sessions after 90 days by default and keeps only its newest log files, so the retention examples now raise sessions.retention_days and keep copies of the logs.")],
    "architect.operations": [("content", "Kanban ships switched off and its cards have no separate done or review fields. The lab now has you turn it on and write both in the card's description.")],
}

RELEASES = [
    (RELEASE_VERSION, RELEASE_DATE, RELEASE_REVISIONS),
    (RELEASE_081_VERSION, RELEASE_081_DATE, RELEASE_081_REVISIONS),
]


_apply_content()

# The versioned changelog. Each entry says which mission changed, the version it
# changed to, and what changed in plain words. A learner who passed a mission at
# an older version sees it under "What changed since you learned this" and can
# re-verify. Kinds: "check" (the proof asked for changed), "content" (the
# teaching changed), "added" (a new mission). To record a change, add a
# revision to that mission's entry in content/ and bump its version.
REVISIONS = _revisions()


def mission_version(mission_id):
    return max([r["version"] for r in REVISIONS if r["mission_id"] == mission_id] or [1])


def revisions_since(mission_id, passed_version):
    return [r for r in REVISIONS if r["mission_id"] == mission_id and r["version"] > int(passed_version)]


MISSIONS = {
    item["id"]: {**item, "track": track_id, "version": mission_version(item["id"])}
    for track_id, track in TRACKS.items()
    for item in track["missions"]
}
STEPS = {
    (mission_id, item["id"]): item
    for mission_id, current in MISSIONS.items()
    for item in current["steps"]
}

# Tool activity may suggest a mission. It never changes progress and never
# counts as evidence.
TOOL_SIGNALS = {
    "terminal": "operator.runtime",
    "shell": "operator.runtime",
    "session_search": "operator.learning",
    "memory": "operator.learning",
    "skill": "operator.learning",
    "cron": "operator.automation",
    "mcp": "integrator.connect",
    "browser": "integrator.connect",
    "delegate": "architect.operations",
    "kanban": "architect.operations",
    "subagent": "architect.operations",
}


def mission_for_tool(tool_name):
    normalized = (tool_name or "").lower()
    for fragment, mission_id in TOOL_SIGNALS.items():
        if fragment in normalized:
            return mission_id
    return None


def _public(item):
    current = deepcopy(item)
    # Review questions are delivered a session at a time, and the model answers
    # to a half-finished example are shown only after the learner has tried.
    current.pop("review", None)
    current["version"] = mission_version(current["id"])
    for step in current["steps"]:
        if step["kind"] == "complete":
            for part in step["parts"]:
                part.pop("answer", None)
    current["sources"] = [deepcopy(SOURCES[source_id]) for source_id in current.pop("source_ids")]
    watch = [deepcopy(EPISODES[key]) for key in WATCH.get(current["id"], [])]
    current["watch"] = watch
    gate_step = next((step for step in current["steps"] if step["kind"] == "gate"), None)
    current["proof"] = gate_step["proof"] if gate_step else ""
    for step in current["steps"]:
        if step["kind"] == "lesson":
            step["watch"] = watch
            break
    return current


def public_tracks():
    tracks = []
    for track_id, track in TRACKS.items():
        current = deepcopy(track)
        current["id"] = track_id
        current["missions"] = [_public(item) for item in track["missions"]]
        placement = PLACEMENTS.get(track_id)
        current["placement"] = (
            {
                "available": True,
                "title": placement["title"],
                "intro": placement["intro"],
                "questions": len(placement["questions"]),
                "minutes": int(placement.get("minutes", 5)),
            }
            if placement
            else {"available": False}
        )
        tracks.append(current)
    return tracks


def get_mission(mission_id):
    if mission_id not in MISSIONS:
        raise ValueError(f"Unknown mission: {mission_id}")
    return _public(MISSIONS[mission_id])


def index():
    """The compact shape handed to the agent: one line per mission."""
    lines = []
    for track_id, track in TRACKS.items():
        lines.append({"track": track_id, "name": track["name"], "promise": track["promise"]})
        for item in track["missions"]:
            lines[-1].setdefault("missions", []).append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "level": item["level_name"],
                    "promise": item["promise"],
                    "gate": item["steps"][-1]["title"],
                }
            )
    return lines
