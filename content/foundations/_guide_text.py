"""(Named with a leading underscore: foundations_content.load_all reads every other .py here as a mission.)

The Field guide's own words for missions 1 to 3: give-away lists, Show me where, fallbacks and starter questions.

Written by hand (AI lane, Nov 8, 2026). Nothing here goes to a model as an instruction about the answer.

* ``GIVEAWAYS``: per snag, the words a nudge or an Explain my miss line may not use before Compare, because each one
  names or points straight at that snag. A reply is checked against the lists of **every** snag the mission can plant,
  never just the one drawn, since the guide doesn't know which one it is before Compare. Matching is on whole words,
  case-insensitive, and also catches the snag's own id.
* ``WHERE``: rung 2, **Show me where**, per snag. Authored; it points at the place to look without naming the cause.
  The learner asks for it on purpose and it is recorded as help.
* ``NUDGE_FALLBACK``: rung 1 when the model can't be used or its reply gave the answer away. Per mission, so it can't
  depend on which snag was drawn; checked by a test against every snag list of its mission.
* ``EXPLAIN_FALLBACK_TAIL``: the second sentence of Explain my miss when the model can't be used.
* ``STARTERS``: three questions each for Check, Compare and Fix on missions 1 to 3 (27), shown before the learner asks
  anything. Starter questions for Check never name a snag either.
"""

from __future__ import annotations

GIVEAWAYS = {
    # Mission 1, f.loop: the weekly report job.
    "output_locked": ("locked", "lock", "read-only", "readonly", "permission", "permissions", "write-protected",
                      "last week", "stale", "old report", "output_locked"),
    "input_empty": ("empty", "blank", "no rows", "zero rows", "header only", "only the header", "input_empty"),
    "rows_short": ("short", "missing rows", "rows missing", "two rows", "fewer rows", "dropped rows", "cut off",
                   "rows_short"),
    # Mission 2, f.cost: what each trip carries.
    "extra_connector": ("connector", "connectors", "mcp", "server", "servers", "filesystem server", "extra_connector"),
    "unused_skills": ("skill", "skills", "skill pack", "skills list", "unused", "unused_skills"),
    # Mission 3, f.memory: the save that didn't land.
    "write_approval": ("approval", "approve", "approved", "approving", "pending", "staged", "stage", "held", "hold",
                       "waiting", "write_approval", "memory pending", "not yet saved"),
    "memory_full": ("full", "limit", "capacity", "2,200", "2200", "too long", "over the limit", "no room", "space",
                    "cut", "trimmed", "memory_full"),
}

MISSION_SNAGS = {
    "f.loop": ("output_locked", "input_empty", "rows_short"),
    "f.cost": ("extra_connector", "unused_skills"),
    "f.memory": ("write_approval", "memory_full"),
}

WHERE = {
    "output_locked": "Open the report file Hermes said it wrote and look at what is in it now, line by line. Then compare "
                     "its job numbers with this week's sheets.",
    "input_empty": "Open each of this week's job sheets, one at a time, and count the rows under the header line in each.",
    "rows_short": "Count the rows in the biggest job sheet, then count the jobs from that sheet in the report. Do the two "
                  "numbers match?",
    "extra_connector": "Open the practice profile's settings and read the list of tools Hermes loads at the start of every "
                       "chat. Ask of each one: does the orders job ever use it?",
    "unused_skills": "Open the Skills tab for the practice profile and read the names. Ask of each one: does the orders job "
                     "ever open it?",
    "write_approval": "Go back to the chat where you asked Hermes to remember the fact. Open the memory row and read every "
                      "line of it, not just its title.",
    "memory_full": "Open MEMORY.md in the practice profile and read it top to bottom. Is your fact there, word for word, "
                   "and what else is in the file?",
}

NUDGE_FALLBACK = {
    "f.loop": "Before you trust the summary, which file did Hermes read last in your chat, and have you opened that file "
              "yourself?",
    "f.cost": "Look at the first message of your practice chat. What did Hermes bring along on that trip that the orders "
              "job never used?",
    "f.memory": "Find the row in your practice chat where Hermes answered your request to remember the fact. Open it and "
                "read every line.",
}

# Ask during the hunt, when the answer would name the snag twice over: the course's words instead.
ASK_HUNT_FALLBACK = {
    "default": "That one is part of the hunt, so the guide won't say it yet. Press Give me a hint for a hint about where to look.",
    "f.memory": "That one is part of the hunt, so the guide won't say it yet. Open the memory row in your chat and read "
                "every line, or press Give me a hint.",
}

EXPLAIN_FALLBACK_TAIL = "Open the evidence beside this check and read the line it quotes, then look at that same file yourself."

STARTERS = {
    "f.loop": {
        "check": ("Which of my checks read the real files, and which only read Hermes's words?",
                  "What does it mean when a check I scored as a pass comes back not met?",
                  "How do I look at the report file myself, outside the chat?"),
        "compare": ("Why didn't Hermes's summary tell me the report was wrong?",
                    "Which line in my chat should I have doubted first?",
                    "How would I catch this in a real weekly report?"),
        "fix": ("What is the smallest change that fixes the report?",
                "How do I know my fix worked and isn't just a new summary?",
                "Should I ask Hermes to redo the job, or fix the file myself?"),
    },
    "f.cost": {
        "check": ("Where do I see what each trip to the model carries?",
                  "Why would a chat cost more when I didn't ask for anything new?",
                  "What did my before-and-after numbers just show?"),
        "compare": ("Why does something I never used still cost me on every trip?",
                    "Which number in my run shows the extra weight?",
                    "How would I spot this on my own Hermes?"),
        "fix": ("How do I turn something off without losing what I use?",
                "Why should I start a new chat after the fix?",
                "How do I check that the next trip got lighter?"),
    },
    "f.memory": {
        "check": ("What should I open first when a check misses?",
                  "Where does Hermes keep what it remembers, and how do I open it?",
                  "Why does a new chat matter for this check?"),
        "compare": ("Why did the chat look like the save worked?",
                    "Which line in the memory row should I have read?",
                    "What else can make a save look done when it isn't?"),
        "fix": ("What do the two fix commands actually do?",
                "How do I know the line really landed in MEMORY.md?",
                "Should I turn this setting off, or keep it on and check each save?"),
    },
}

# Where to look in your own Hermes to catch this snag yourself next time: the replay's note on the bracket says this (one
# thing the row and the headline don't), so the learner leaves with a habit, not a second telling. Fixed in code; the
# model rewords it in its own sentence and may name only these commands.
CATCH_IT = {
    "write_approval": ("Saved rows open collapsed; expand one and read its first word before trusting the title.", ()),
    "memory_full": ("Read the memory row's usage line; near 2,200, Hermes deletes notes to fit. Check MEMORY.md.", ()),
}

# Do it with me, mission 3's Fix step. Fixed in code: the model writes only the one line on why, and can't change these.
# "{id}" is the id of the one save Hermes is holding, read by code from the first check's pending/memory/<id>.json, so the
# learner approves that save and nothing else (never "approve all", which would also apply saves they haven't read).
DO_IT_WITH_ME = {
    "f.memory": ("/memory pending", "/memory approve {id}"),
}
DO_IT_WITH_ME_FALLBACK = {
    "f.memory": "The first command lists the save Hermes is holding; the second writes that one save into MEMORY.md, so a "
                "new chat can read it.",
}
