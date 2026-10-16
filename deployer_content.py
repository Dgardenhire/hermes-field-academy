"""Words for the Deployer path that are not labs, the brief or scenarios.

Learner-facing copy follows docs/curriculum-voice.md: plain English, second
person, headings that name the thing and never end in a period, and no claim
the path cannot back.
"""

from __future__ import annotations

TITLE = "Guide"
EYEBROW = "For clients, in practice"
LORE = (
    "Hermes was a guide: he led travelers all the way to where they were going. You take a client the "
    "whole way, from finding what is wrong to a service that runs and recovers."
)
PROMISE = (
    "Set up, deploy and manage Hermes for a small client: find what is wrong on their machine, decide what each helper may reach, "
    "run a real service for several days, break it on purpose and prove it recovers, then show an expert your work."
)

PHASES = [
    {
        "id": "audit",
        "name": "Audit",
        "short": "Audit",
        "meaning": "Look over a client's setup and find what is wrong, from the evidence in its files and logs.",
        "items": ["lab.leak", "lab.cost", "lab.reboot"],
    },
    {
        "id": "architect",
        "name": "Architect",
        "short": "Architect",
        "meaning": "Decide the boundaries: what each helper may reach, what you promise, what you refuse and why.",
        "items": ["lab.vault", "brief", "scenarios"],
    },
    {
        "id": "build",
        "name": "Build and integrate",
        "short": "Build",
        "meaning": "Connect one real service to your own Hermes with the smallest permission that does the job, and run it for several days.",
        "items": ["deploy"],
    },
    {
        "id": "verify",
        "name": "Staged verification",
        "short": "Verify",
        "meaning": "Break it on purpose, prove it recovers, then walk an expert through your work.",
        "items": ["drills", "walkthrough"],
    },
]

ITEM_TITLES = {
    "lab.leak": "The key in the open",
    "lab.cost": "The runaway bill",
    "lab.reboot": "Monday after the power cut",
    "lab.vault": "One key for everything",
    "brief": "A proposal for a three-person firm",
    "scenarios": "Nine judgment scenarios",
    "deploy": "Run one real service for several days",
    "drills": "Failure drills",
    "walkthrough": "Walkthrough and expert review",
}
ITEM_MINUTES = {"lab.leak": 40, "lab.cost": 35, "lab.reboot": 45, "lab.vault": 50, "brief": 75, "scenarios": 72, "deploy": 90, "drills": 90, "walkthrough": 45}

LIFECYCLE_CREDIT = (
    "The order of this path follows the lifecycle Tony Simons describes for his one-to-one Hermes architecture sessions at tonysimons.dev: "
    "audit what exists, design the boundaries, build and integrate, then test in isolation before production. "
    "Field Academy read it from a summary of his site. He has not reviewed this path and does not endorse it, and his site offers no certification."
)

# What a Guide Field Record shows. It used to be WHAT_IT_CERTIFIES; records made by
# 0.8.2 and earlier store the old lines, and their record number covers them.
WHAT_IT_SHOWS = [
    "That you repaired four broken client setups from their own files and logs, and the repairs passed checks you could not see in advance.",
    "That you wrote a proposal for a fictional client that held up to the checks on price, access and refusing an unsafe request.",
    "That you reasoned through nine cases with no clean answer.",
    "That you ran a real service on your own Hermes for several days, and broke it and recovered it, as far as Hermes's own records could show.",
    "That a reviewer you chose read all of it and signed it with their own key.",
]
WHAT_IT_CERTIFIES = WHAT_IT_SHOWS
WHAT_IT_DOES_NOT = [
    "It is competence shown in labs and on your own setup. It is not years of client work, and it does not promise how you will do with a real client.",
    "It is your own record. Field Academy, a free community plugin, wrote it on your computer. Nous Research and the Hermes team don't issue, review or endorse it.",
    "Where Field Academy could not read Hermes, the record says so, and only your reviewer's acceptance counted.",
    "Your reviewer is someone you chose. Their signature proves their key signed this packet. It does not mean anyone else vouches for them.",
]
ISSUER = (
    "Created by its holder with the Field Academy plugin, "
    "with the signed sign-off of a reviewer the holder chose."
)

DEPLOY = {
    "title": "Run one real service for several days",
    "intro": (
        "Connect one real service to your own Hermes, give it the smallest permission that still does the job, and let a scheduled job use it for at least three days. "
        "Field Academy checks that it ran by reading Hermes's own records. It never runs the job, never changes anything in your Hermes, and never touches the service."
    ),
    "steps": [
        "Pick one small service that is yours and that you can connect read-only: a calendar, a mail label, a code repository, a spreadsheet.",
        "Make the smallest credential the service allows: read only, limited to what the job needs, with an expiry date.",
        "Connect it to your Hermes in a profile of its own, and keep the credential in that profile's .env file. If the job reaches it from a script or a terminal command, also list its name under terminal.env_passthrough in that profile's config.yaml.",
        "Make a scheduled job whose name starts with deployer- that uses the service once or twice a day.",
        "Start the clock here, with the service's name and the job's name.",
        "Write the access record: what you granted, what you refused, when it expires, who owns it, and what to do if it leaks.",
        "Leave it running. Come back each day or two and check. Each check adds what Hermes shows to the record.",
    ],
    "record_sections": [
        {"heading": "Service", "min_words": 6, "needs": ["name"], "what": "which service and whose it is", "fix": "Name the service and the person who owns the account.", "hint": "Name the service and the person whose account it is.", "example": "Example: Google Calendar, Alice Moreno's work calendar."},
        {"heading": "Access granted", "min_words": 8, "needs": ["list"], "what": "each permission you granted, one per line", "fix": "List each permission on its own line.", "hint": "One line per permission, in the service's own words. Include what the job may read.", "example": "Example:\n- Read events on the Work calendar\n- Nothing else"},
        {"heading": "Access refused", "min_words": 8, "needs": ["list"], "what": "what you could have granted and did not", "fix": "List at least two permissions you refused.", "hint": "List what the service offered that the job does not need, and say you left it out.", "example": "Example:\n- Create or change events, not needed\n- Other calendars, not needed"},
        {"heading": "Expiry", "min_words": 5, "needs": ["time"], "what": "when the credential expires or gets changed", "fix": "Say when it expires or when you change it.", "hint": "Give a date or a number of days.", "example": "Example: The token expires in 90 days and I change it every 60."},
        {"heading": "Owner", "min_words": 5, "needs": ["name"], "what": "the person who can switch it off", "fix": "Name the person who can switch it off.", "hint": "Name who can revoke the credential, and where.", "example": "Example: Alice Moreno can revoke it in her account settings."},
        {"heading": "If it leaks", "min_words": 12, "needs": [], "what": "what you do first if the credential leaks", "fix": "Say you switch it off first.", "hint": "Say what you do in order, starting with switching it off.", "example": "Example: Revoke the token first, then make a new one, then put it in the profile's .env."},
    ],
    "reads": [
        "Hermes's scheduler list, for the job and when it last ran",
        "Hermes's run history file, when there is one, for the times of each run and whether it failed",
        "Hermes's log files, for lines that name your job. Only the time of each line is kept.",
    ],
    "cannot_read": [
        "Whether a Kanban card exists. Field Academy's page can call only its own backend, so it does not read the board.",
        "What the job actually did. It sees that a run happened and when, never what it said or touched.",
        "Anything on a remote or Cloud backend that is not on this computer.",
    ],
}

DRILLS = [
    {
        "id": "revoke",
        "title": "Revoke the token",
        "minutes": 30,
        "intro": "Switch off the credential your deployment uses, watch the scheduled run fail, then make a new one and put it back.",
        "steps": [
            "Press Start the drill here, so the time is written down.",
            "In the service's own settings, revoke the credential your job uses.",
            "Wait for at least one scheduled run. It should fail with an error about authorization.",
            "Make a new credential with the same smallest permission, and put it in the profile's .env file.",
            "Press I recovered here, then wait for the next scheduled run to work.",
            "Press Check the evidence, and write the recovery note.",
        ],
        "risk": "You are revoking your own credential on your own service. If the service is your client's, stop and use your own.",
    },
    {
        "id": "ratelimit",
        "title": "Trip a rate limit",
        "minutes": 30,
        "optional": True,
        "intro": "Make the job ask for more than its allowance, see the refusals, then fix the cause. This one is optional because it can cost money or upset a provider.",
        "steps": [
            "Use a test key or a free tier, never a paid production key.",
            "Press Start the drill here.",
            "Lower the limit on the key in the provider's console if it lets you, or shorten the job's schedule for a few runs.",
            "Watch for refusals or a failed run that mentions a limit.",
            "Put the limit and the schedule back, and press I recovered.",
            "Wait for a clean run, press Check the evidence, and write the recovery note.",
        ],
        "risk": "A schedule that runs every minute on an expensive model is how a bill grows. Keep the drill short, use a test key, and put the schedule back straight after.",
    },
    {
        "id": "restart",
        "title": "Restart Hermes",
        "minutes": 30,
        "intro": "Stop what runs your scheduled jobs and start it again, and see whether the job picks up where it left off.",
        "steps": [
            "Press Start the drill here.",
            "Stop what runs your jobs: quit the Hermes app, and stop the gateway service too if one is installed. Or restart the computer if your setup should survive that.",
            "Leave it off through at least one scheduled run, so the run is missed.",
            "Start Hermes again and press I recovered. Hermes runs a missed job once, late, as a catch-up, so expect one run soon after it starts.",
            "Wait for the next on-time run as well, press Check the evidence, and write the recovery note.",
        ],
        "risk": "Do not do this in the middle of anything you need running.",
    },
]
DRILL_NOTE = (
    "This drill is yours to run on your own setup. Nothing is run for you. Field Academy never revokes a credential, trips a limit or restarts anything. "
    "It only reads the times Hermes recorded, afterwards, and judges them."
)
DRILL_RULES = {"min_drills": 2}
DRILL_SECTIONS = [
    {"heading": "What I did", "min_words": 10, "needs": ["time"], "what": "what you did to break it and when", "fix": "Say when you did it.", "hint": "Say what you broke and when.", "example": "Example: At 2 pm on Tuesday I revoked the token in the service's settings."},
    {"heading": "How I knew", "min_words": 12, "needs": [], "what": "how you could tell it was broken", "fix": "Say what you saw.", "hint": "Say what you saw that told you: the error, the missed run.", "example": "Example: The 3 pm run failed with an authorization error."},
    {"heading": "How I fixed it", "min_words": 12, "needs": [], "what": "the steps you took to recover", "fix": "Say what you did.", "hint": "List the steps you took to recover, in order.", "example": "Example: I made a new token with read only access and put it in the profile's .env."},
    {"heading": "How to stop it surprising a client", "min_words": 12, "needs": [], "what": "how a client would find out sooner next time", "fix": "Say how a client would find out.", "hint": "Say what a client would see or be told, and how soon.", "example": "Example: The job tells the owner by message when a run fails."},
]

WALKTHROUGH = {
    "title": "Walkthrough and expert review",
    "intro": (
        "The last step is a person. You explain one of your labs as you would to a client's partner, Field Academy gathers everything into a review packet, "
        "and a reviewer you choose, someone with the experience to judge it, reads it, scores it against a rubric and signs it. Without that signature you hold Guide, awaiting review."
    ),
    "min_chars": 600,
    "prompt": (
        "Walk through one of your labs the way you would to a client's partner who is not technical. Say what looked wrong, what the evidence was, what you changed and why, "
        "what you would tell the client to do, and one thing you would do differently next time. Name the details of your own lab, such as the file, the job or the key id. "
        "Write it out. You can also record yourself and give the file's location; Field Academy records the file's fingerprint and does not copy it."
    ),
}

HONEST_LIMITS = (
    "Labs and the proposal were checked by scripts that read files, and by your own Hermes for the prose. Run history was read from Hermes where Hermes shows it. "
    "Nothing here was tested against a live Hermes while it was written, so the exact layout of Hermes's run history is read generously. "
    "Where it could not be read, the packet carries your own excerpt and only the reviewer's acceptance counts."
)
