"""Integrator path content. Format: docs/content-format.md.

integrator.discovery is the model for a mission whose check reads a document.
"""

MISSIONS = {
    "integrator.discovery": {
        "minutes": {"lesson": 4, "example": 5, "complete": 8, "lab": 12, "explain": 6, "gate": 10},
        "use": (
            "You said you want Hermes to do this for you: {goal}. Before you build it, a one-page scope tells you "
            "what the first version covers and what it leaves out."
        ),
        "use_plain": (
            "Every Hermes project starts with a scope: the one task, who owns it, how you will know it worked, "
            "and what it leaves out. This mission gives you a way to write one."
        ),
        "story_first": True,
        "takeaway": {
            "title": "Six questions for the first meeting",
            "lines": [
                "Ask which work repeats, who owns the result, and which systems it touches.",
                "Ask what a good result looks like in numbers, what happens when it's wrong, and who signs off.",
                "Write down what the project leaves out, then price it as a setup fee plus a monthly fee.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "How Priya turned \"an AI agent\" into one Friday job",
            "intro": (
                "The owner of Harbor Roofing asked Priya Raman, his office manager, for \"an AI agent.\" Before anyone "
                "talked price, she asked which work came back every week."
            ),
            "parts": [
                {
                    "label": "She found the task that repeats",
                    "text": "Friday quote follow-ups took the office three hours a week and got skipped whenever a crew ran late.",
                },
                {
                    "label": "She put her own name on it",
                    "text": "Priya reads every email before it goes out, so she owns the result.",
                },
                {
                    "label": "She counted what done means",
                    "text": "Every quote older than seven days gets a follow-up by Friday at 5 pm, and 95 percent need no edits from her.",
                },
                {
                    "label": "She wrote down what it leaves out",
                    "text": "Nothing goes out without her approval, and the quotes and prices stay as they are. Then came the price: $2,400 to set up and $350 a month.",
                },
            ],
            "document": (
                "# Scope: Harbor Roofing\n\n"
                "## Client\n"
                "Harbor Roofing, a family business in Wilmington with eleven employees that repairs and replaces residential roofs.\n\n"
                "## Workflow\n"
                "Every Friday afternoon the office writes quote follow-up emails to each customer who has not answered in seven days. "
                "It takes about three hours a week and gets skipped when a crew runs late.\n\n"
                "## Owner\n"
                "Priya Raman, the office manager, owns the follow-up list and reads every email before it goes out.\n\n"
                "## Systems\n"
                "The customer list in a shared spreadsheet, the company Gmail account, and the quote folder on the office computer.\n\n"
                "## Acceptance\n"
                "Every open quote older than seven days gets a follow-up by Friday at 5 pm, at least 95 percent need no edits from Priya, "
                "and the weekly time drops from three hours to under one.\n\n"
                "## Out of scope\n"
                "- Sending anything without Priya's approval\n"
                "- Changing quotes or prices\n"
                "- Reading customer payment details\n\n"
                "## Price\n"
                "$2,400 for setup and two rounds of changes, then $350 per month for upkeep and a monthly review.\n"
            ),
        },
        "complete": {
            "title": "Your turn: Lakeside Dental's scope",
            "intro": (
                "Here is a scope for Lakeside Dental that stops halfway. Fill in the three blanks, then compare "
                "with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "# Scope: Lakeside Dental\n\n"
                        "## Client\nLakeside Dental, a four-chair practice in Tulsa run by Dr. Ana Ruiz.\n\n"
                        "## Workflow\nEvery morning the front desk calls patients to confirm the next day's visits, which takes about "
                        "ninety minutes and is the first thing dropped on a busy day.\n\n"
                        "## Owner\n"
                    )
                },
                {
                    "gap": "owner",
                    "prompt": "Who owns the result? Name one person and say what they do with it.",
                    "answer": "Marcus Bell, the office manager, who reviews the confirmation list before any message goes out.",
                    "min_words": 8,
                    "needs": ["name"],
                },
                {
                    "text": (
                        "\n\n## Systems\nThe appointment calendar, the patient phone list, and the practice's text message account.\n\n"
                        "## Acceptance\n"
                    )
                },
                {
                    "gap": "acceptance",
                    "prompt": "What does a good result look like? Use at least one number.",
                    "answer": "Every patient with a visit tomorrow gets a confirmation by 3 pm, and the front desk spends under twenty minutes on it.",
                    "min_words": 10,
                    "needs": ["number"],
                },
                {"text": "\n\n## Out of scope\n"},
                {
                    "gap": "out",
                    "prompt": "List two things the project leaves out, one per line, starting each line with a dash.",
                    "answer": "- Rescheduling a visit without a person\n- Reading or changing patient medical records",
                    "min_words": 10,
                    "needs": ["list"],
                },
                {
                    "text": "\n\n## Price\n$1,800 for setup and one round of changes, then $250 per month for upkeep.\n"
                },
            ],
        },
        "coach": [
            {
                "hint": "Ask which task comes back every week and wastes someone's afternoon. A client who says \"everything\" has not picked one yet.",
                "example": "Example: a dental office confirms tomorrow's visits by phone every morning. That one task repeats and can be counted.",
            },
            {
                "hint": "Ask who would be upset if this task were done wrong. That person owns the result.",
                "example": "Example: the office manager, Marcus Bell, owns the confirmation list and signs off on it.",
            },
            {
                "hint": "List the places the task touches: a shared spreadsheet, an email account, a calendar. Each one needs an owner and a permission.",
                "example": "Example: the appointment calendar, the patient phone list and the text message account.",
            },
            {
                "hint": "Turn \"works well\" into something you can count: how many, by when, how much time saved.",
                "example": "Example: every patient with a visit tomorrow is confirmed by 3 pm, with under twenty minutes of staff time.",
            },
            {
                "hint": "Ask what the harm is if the result is wrong. A wrong text message to a patient costs more than a late report, so it needs a person to check it first.",
                "example": "Example: a person reads each confirmation before it sends, because a wrong time would cause a missed visit.",
            },
            {
                "hint": "Separate the person who likes the idea from the person who can sign the approval. You need both in the conversation.",
                "example": "Example: the owner of the practice signs the agreement. The office manager only uses the result.",
            },
            {
                "hint": "Write two things the project leaves out, and write them before the client asks for them.",
                "example": "Example: the scope leaves out rescheduling visits and anything that touches medical records.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "A bakery owner says, \"We want AI for orders.\" Name the first four things you ask "
                    "before you quote a price, and why each one matters."
                ),
                "points": [
                    {
                        "point": "which work repeats, and how often, so you pick one task worth automating",
                        "hint": "Ask what someone does again and again.",
                        "example": "Example: the owner retypes the same twelve wholesale orders into the invoice system every Thursday.",
                    },
                    {
                        "point": "who owns the result, by name",
                        "hint": "Ask who is unhappy when it goes wrong.",
                        "example": "Example: Rosa Alvarez, who runs wholesale, owns the order list.",
                    },
                    {
                        "point": "what a good result looks like in a number",
                        "hint": "Ask how many orders, by what time, with how many mistakes.",
                        "example": "Example: all twelve orders entered by noon with no more than one correction.",
                    },
                    {
                        "point": "which systems the work touches, because each one needs a permission",
                        "hint": "Ask where the orders arrive and where they end up.",
                        "example": "Example: orders arrive by email and go into the invoice software.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "Three weeks into the project the client asks you to add invoicing. "
                    "Say what you point to, and what you offer."
                ),
                "points": [
                    {
                        "point": "the out-of-scope list in the signed scope, which is where invoicing was left out",
                        "hint": "Name the part of the scope that already covers this request.",
                        "example": "Example: \"Invoicing is on the out-of-scope list we agreed on the first day.\"",
                    },
                    {
                        "point": "a separate project with its own scope and price, so the first one stays finished",
                        "hint": "Offer a next step that keeps the first project's price and finish line.",
                        "example": "Example: \"I can scope invoicing as a second project and send you a price this week.\"",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "Two people are keen on the project: the owner's nephew, who \"handles the tech,\" and the "
                    "owner, who signs the checks. Who do you need to hear from before you quote, and why?"
                ),
                "points": [
                    {
                        "point": "the person who can approve spending, because enthusiasm without that authority can't sign",
                        "hint": "Ask who can say yes to the price.",
                        "example": "Example: the owner signs the agreement, so the owner is on the call before you quote.",
                    },
                    {
                        "point": "the person who owns the result, because that person can say whether the task is done well",
                        "hint": "Ask who feels the pain of the task.",
                        "example": "Example: the office manager who does the task now owns the result and checks the output.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your scope document",
            "body": (
                "Write your scope as a text or Markdown file with the seven sections below and real "
                "content in each.\n"
                "1. Save it.\n"
                "2. Type where you saved it.\n"
                "3. Click Check my work."
            ),
            "verify": "artifact",
            "check": "scope document",
            "sections": [
                {
                    "heading": "Client", "min_words": 6, "needs": ["name"],
                    "what": "who the client is and what they do",
                    "fix": "Name the business.",
                    "hint": "Name the business and say what it does in one sentence.",
                    "example": "Example: Lakeside Dental, a four-chair practice in Tulsa run by Dr. Ana Ruiz.",
                },
                {
                    "heading": "Workflow", "min_words": 12, "needs": ["time"],
                    "what": "the one task that repeats, and how often",
                    "fix": "Say how often the task happens or how long it takes.",
                    "hint": "Describe one task, say how often it happens, and say how long it takes now.",
                    "example": "Example: Every morning the front desk calls patients to confirm tomorrow's visits, about ninety minutes of work.",
                },
                {
                    "heading": "Owner", "min_words": 6, "needs": ["name"],
                    "what": "who owns the result, by name",
                    "fix": "Name a person, not a team.",
                    "hint": "Write one person's name and say what they do with the result.",
                    "example": "Example: Marcus Bell, the office manager, reviews the list before any message goes out.",
                },
                {
                    "heading": "Systems", "min_words": 6, "needs": [],
                    "what": "which systems the task touches",
                    "hint": "List where the work starts and where it ends up: calendar, spreadsheet, email account, folder.",
                    "example": "Example: The appointment calendar, the patient phone list, and the practice's text message account.",
                },
                {
                    "heading": "Acceptance", "min_words": 10, "needs": ["number"],
                    "what": "what a good result looks like, in a number",
                    "fix": "Put a number on it: how many, by when, how much time.",
                    "hint": "Turn \"works well\" into a count, a deadline and a time saved.",
                    "example": "Example: Every patient with a visit tomorrow is confirmed by 3 pm, with under twenty minutes of staff time.",
                },
                {
                    "heading": "Out of scope", "min_words": 12, "needs": ["list"],
                    "what": "at least two things the project leaves out",
                    "fix": "List at least two items, one per line, each starting with a dash.",
                    "hint": "Write the requests you expect to hear in month two and decide now that they are left out.",
                    "example": "Example:\n- Rescheduling a visit without a person\n- Reading or changing medical records",
                },
                {
                    "heading": "Price", "min_words": 8, "needs": ["money"],
                    "what": "what you will charge and for what",
                    "fix": "Put the price in dollars.",
                    "hint": "Write the setup price and the monthly price, each with what it covers.",
                    "example": "Example: $1,800 for setup and one round of changes, then $250 per month for upkeep.",
                },
            ],
            "proof": (
                "Your scope document, saved on your computer, with all 7 sections filled in with real content. "
                "Its fingerprint goes on your Field Record."
            ),
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now reads inside each section. It needs a named client and owner, a number in "
                    "Acceptance, two items in Out of scope and a price in dollars. It used to look only for the headings."
                ),
            }
        ],
    },
    "integrator.deploy": {
        "minutes": {"lesson": 4, "example": 4, "complete": 6, "lab": 8, "explain": 6, "gate": 8},
        "use": (
            "You said you want Hermes to do this for you: {goal}. Where Hermes runs decides whether that work happens "
            "overnight, so you write down who owns the computer and who answers when it stops."
        ),
        "use_plain": (
            "Where Hermes runs decides who fixes it when it stops. This mission has you write down the four answers "
            "for your own setup."
        ),
        "lab": {
            "body": (
                "1. Open Gateways and follow the route from this window to the computer that does the "
                "work.\n"
                "2. Write a setup note about your own setup, with the five headings the check lists."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "Four questions for any setup",
            "lines": [
                "Ask whose computer it is, whose passwords it stores, who updates it, and who gets the 2am call.",
                "A laptop costs nothing extra, and it stops when someone closes the lid.",
                "A rented server costs money each month. Hermes Cloud looks after the computer, and you own the bill.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "Where Greta's appointment reminders run",
            "intro": (
                "Greta Lindqvist manages the front office at Tidewater Veterinary Clinic. Before the clinic switched on "
                "appointment reminders, she answered four questions about the computer Hermes would run on."
            ),
            "parts": [
                {
                    "label": "She read the connection",
                    "text": "Gateways in Settings showed another computer: the back-office desktop, reached over SSH.",
                },
                {
                    "label": "She named whose computer it was",
                    "text": "The clinic owns the desktop, and Greta answers for it.",
                },
                {
                    "label": "She listed what it stores",
                    "text": "The email login for the reminders and the model provider's key sit on that desktop. She left the passwords themselves out of her note.",
                },
                {
                    "label": "She named who keeps it running",
                    "text": "Samir Haddad, the IT contractor, installs updates on the first Monday of each month and takes the call if reminders stop at 2am.",
                },
            ],
            "document": (
                "# Setup note: Tidewater Veterinary Clinic\n\n"
                "## Connection\n"
                "Hermes runs on another computer: the back-office desktop at the clinic, which this window reaches over SSH. "
                "The profile is called frontdesk.\n\n"
                "## Whose computer\n"
                "The clinic owns the desktop, and Greta Lindqvist, the practice manager, answers for it. It stays in the "
                "locked back office and never leaves the building.\n\n"
                "## Passwords\n"
                "The desktop stores the email login Hermes uses for appointment reminders and the key for the model provider. "
                "Both sit under the frontdesk profile, and only Greta and Samir Haddad can sign in to that computer.\n\n"
                "## Updates\n"
                "Samir Haddad installs Hermes updates on the first Monday of every month, after the clinic closes at 6 pm, "
                "and writes the date in the shared log.\n\n"
                "## At 2am\n"
                "If reminders stop overnight, the call goes to Samir Haddad on his mobile, with Greta as the backup. He checks "
                "first that the desktop is on and that the Gateway item in this window's status bar says Connected.\n"
            ),
        },
        "complete": {
            "title": "Your turn: Hannah's setup note",
            "intro": (
                "Hannah Boyd prepares taxes for twenty households from one laptop. Here is her setup note with three "
                "blanks. Fill them in, then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "# Setup note: Hannah Boyd Tax Preparation\n\n"
                        "## Connection\n"
                        "Hermes runs on this computer, Hannah's work laptop, so the gateway only works while the laptop is open "
                        "and awake. The profile is called taxes.\n\n"
                        "## Whose computer\n"
                    )
                },
                {
                    "gap": "owner",
                    "prompt": "Whose computer is it, and who answers for it? Name one person.",
                    "answer": "Hannah Boyd owns the laptop and answers for it. She carries it home every night and to client meetings.",
                    "min_words": 8,
                    "needs": ["name"],
                },
                {
                    "text": (
                        "\n\n## Passwords\n"
                        "The laptop stores the email login Hermes uses for client reminders, and Hannah's own sign-in protects "
                        "the whole computer.\n\n"
                        "## Updates\n"
                    )
                },
                {
                    "gap": "updates",
                    "prompt": "Who installs updates, and how often? Give a time or a rhythm.",
                    "answer": "Hannah installs Hermes updates herself on the first Friday of every month, before the evening reminders go out.",
                    "min_words": 10,
                    "needs": ["time"],
                },
                {"text": "\n\n## At 2am\n"},
                {
                    "gap": "call",
                    "prompt": "Who gets the call when it stops at 2am, and what do they check first? Name a person.",
                    "answer": (
                        "Nobody is called overnight. At 8 am Hannah opens the lid and finds out, and the first thing she "
                        "checks is whether the laptop went to sleep."
                    ),
                    "min_words": 12,
                    "needs": ["name"],
                },
            ],
        },
        "coach": [
            {
                "hint": "Ask who answers if the computer breaks or goes missing. The person who owns it is the one who gets asked.",
                "example": "Example: a freelance bookkeeper owns her laptop outright, so every question about it ends with her.",
            },
            {
                "hint": "Think about what Hermes logs in to, and where those logins sit while it runs. Whoever can use that computer can reach them.",
                "example": "Example: a bakery's desktop holds the login for its order inbox, so anyone who uses the desktop can reach the inbox.",
            },
            {
                "hint": "Ask who runs the update and how often. An update nobody owns waits until something breaks.",
                "example": "Example: a contractor installs updates on the first Monday of each month and logs the date, so the owner can see the last one.",
            },
            {
                "hint": "Name a person, and say what that person checks first. At 2am a role has no phone, and a person does.",
                "example": "Example: the contractor's mobile goes in the note, and his first move is to check that the computer is on.",
            },
            {
                "hint": "Picture who carries the computer at six and where it sleeps. A computer that travels takes the gateway with it.",
                "example": "Example: a nurse takes her laptop home each evening, so the 7 am summary waits until she opens it the next day.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "A solo accountant runs Hermes on her laptop and wants a summary at 6 a.m. She travels two days a week. "
                    "Say what you tell her, and what you offer."
                ),
                "points": [
                    {
                        "point": "that the summary only goes out while the laptop is open and awake, and the laptop travels with her",
                        "hint": "Ask where the laptop is at 6 a.m. on a travel day.",
                        "example": "Example: on a Tuesday flight the laptop is closed in a bag, so the summary misses its time and goes out late, once, when she opens the laptop.",
                    },
                    {
                        "point": "a change: a computer that stays on at her office, or Hermes Cloud",
                        "hint": "Offer a place Hermes can run whether or not she is there.",
                        "example": "Example: an office desktop that stays on, or Hermes Cloud, where the computer is looked after for her.",
                    },
                    {
                        "point": "that she still owns the account and the passwords, whichever you pick",
                        "hint": "Ask what stays with her even when someone else looks after the computer.",
                        "example": "Example: with Hermes Cloud she still owns the account and the bill.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "A client's nephew offers to host Hermes on a server he rents, free of charge. "
                    "Say which of the four questions you ask first, and why."
                ),
                "points": [
                    {
                        "point": "whose computer it is: the nephew's, so he decides what happens to it",
                        "hint": "Ask who could switch it off or look inside.",
                        "example": "Example: if the nephew stops paying the rent, the client's reminders stop with it.",
                    },
                    {
                        "point": "whose passwords are stored on it, because the client's email login would sit on the nephew's server",
                        "hint": "Ask what Hermes needs to log in to and where those logins would live.",
                        "example": "Example: the client's mailbox login ends up on a server only the nephew controls.",
                    },
                    {
                        "point": "who installs updates and who takes the 2am call, since a favor has no schedule",
                        "hint": "Ask who picks up when it stops at night.",
                        "example": "Example: the nephew has a day job, so a stop at 2am waits until his lunch break.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "Hermes Cloud looks after the computer for a client. The client says that means you can stop worrying "
                    "about the setup. What do you still write down?"
                ),
                "points": [
                    {
                        "point": "that the client still owns the account and the bill, so a named person holds both",
                        "hint": "Name what stays with the client when Nous looks after the computer.",
                        "example": "Example: Priya Shah holds the Nous account and pays the monthly bill.",
                    },
                    {
                        "point": "which logins are stored there and who can reach them",
                        "hint": "Ask what Hermes logs in to, even on a computer someone else looks after.",
                        "example": "Example: the email login for reminders, and the two staff members who can open the account.",
                    },
                    {
                        "point": "who gets the call when it stops, since looking after the computer leaves that question open",
                        "hint": "Ask who the client rings first when reminders stop.",
                        "example": "Example: the office manager rings you first, then decides whether to contact Nous.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your setup note",
            "body": (
                "Write a setup note about your own setup as a text or Markdown file with the five "
                "headings below.\n"
                "1. Save it.\n"
                "2. Type where you saved it.\n"
                "3. Click Check my work.\n"
                "\n"
                "This window also has to name its connection."
            ),
            "verify": "artifact",
            "check": "setup note",
            "live": "routes",
            "sections": [
                {
                    "heading": "Connection", "min_words": 10, "needs": [],
                    "what": "where Hermes runs (this computer, another computer or Hermes Cloud) and which profile",
                    "hint": "Open Gateways, read the connection marked Current, and write where it runs. Then read the profile name from the sidebar, or write default if you have only one.",
                    "example": "Example: Hermes runs on this computer, a work laptop, under a profile called taxes.",
                },
                {
                    "heading": "Whose computer", "min_words": 8, "needs": ["name"],
                    "what": "whose computer it is, by name",
                    "fix": "Name a person who answers for the computer.",
                    "hint": "Write one person's name and say what they do with the computer.",
                    "example": "Example: Hannah Boyd owns the laptop and carries it home every night.",
                },
                {
                    "heading": "Passwords", "min_words": 12, "needs": [],
                    "what": "which logins are stored there and who can reach them",
                    "hint": "Describe the logins and keys stored on that computer and who can sign in to it. Leave the passwords themselves out.",
                    "example": "Example: The laptop stores the email login for reminders and the model provider key. Only the owner and her assistant can sign in.",
                },
                {
                    "heading": "Updates", "min_words": 10, "needs": ["time"],
                    "what": "who installs updates, and how often",
                    "fix": "Say how often updates are installed, or on which day.",
                    "hint": "Name who installs updates and say how often, so a late update shows.",
                    "example": "Example: Alan Cho installs updates on the first Sunday of every month and writes the date in a shared log.",
                },
                {
                    "heading": "At 2am", "min_words": 12, "needs": ["name"],
                    "what": "who gets the call when it stops, by name, and what they check first",
                    "fix": "Name a person, and say what they check first.",
                    "hint": "Write a person who picks up and the first thing they check.",
                    "example": "Example: Alan Cho gets the call on his mobile and checks first that the desktop is on.",
                },
            ],
            "proof": (
                "Your setup note, saved on your computer, with all 5 sections filled in, and this window names the "
                "Hermes setup it is connected to. The note's fingerprint goes on your Field Record."
            ),
            "fixes": {
                "live_failed": {
                    "hint": "Click Gateway in the status bar and choose Reconnect gateway, or click Test on your connection in Gateways. The check needs this window to name the setup it is connected to.",
                    "example": "Example: once the Gateway item says Connected, or Test says Reachable, the check can read it.",
                },
            },
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now reads a setup note with five sections, and this window still has to name its connection. "
                    "Whose computer and At 2am need a name, and Updates needs a time. It used to pass whenever this window "
                    "could name a connection route."
                ),
            }
        ],
    },
    "integrator.connect": {
        "minutes": {"lesson": 4, "example": 4, "complete": 6, "lab": 12, "explain": 6, "gate": 8},
        "use": (
            "You said you want Hermes to do this for you: {goal}. Each tool that work needs gives Hermes a new power, "
            "so you write down the smallest permission and who approves what it sends."
        ),
        "use_plain": (
            "Each tool you connect gives Hermes a new power. This mission has you test the approval step once and write "
            "down what happened."
        ),
        "lab": {
            "body": (
                "Hermes asks before a risky command, not before a connected tool acts.\n"
                "1. Set command approvals to manual (approvals.mode in config.yaml).\n"
                "2. Make a scratch folder of copies.\n"
                "3. Ask Hermes to delete it. Turn it down once, then approve it.\n"
                "4. Note each choice."
            ),
            "prompt": (
                "Help me test your approval prompt safely. Tell me how to set command approvals to manual for this test. "
                "I will make a scratch folder of copies, and you ask to delete it, which needs my approval. I turn it down "
                "once and approve it the second time. Tell me where each choice shows up afterward. Then tell me the smallest "
                "permission my real client tool needs, with draft-only sending so a person presses send."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "Give the smallest permission that works",
            "lines": [
                "Before you connect a tool, write down the smallest permission that still does the job.",
                "Hermes asks before a risky command, and a connected tool acts without asking unless you mark its server untrusted, so give a sending tool draft-only access.",
                "Name who approves what Hermes sends, and test Hermes's approval prompt once each way.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "How Lucia tested the approval step at Alder Physio",
            "intro": (
                "Lucia Ferreira connected the booking calendar for Alder Physio, a four-therapist clinic. Once Hermes "
                "could book visits, it could also book the wrong ones."
            ),
            "parts": [
                {
                    "label": "She wrote the permission first",
                    "text": "A connected tool acts without asking by default, so she switched on reading and draft bookings only. Changing or deleting a booking stays out of reach.",
                },
                {
                    "label": "She named who confirms",
                    "text": "Dana Whitfield, the practice manager, confirms every draft booking before a patient sees it.",
                },
                {
                    "label": "She tested the prompt both ways",
                    "text": "She set command approvals to manual and asked Hermes to delete a scratch folder. She turned it down at 10:15 am and approved it at 10:22 am.",
                },
                {
                    "label": "She noted where to find it",
                    "text": "Both choices appear in that Hermes session, so Dana can check them herself.",
                },
            ],
            "document": (
                "# Approval test: Alder Physio\n\n"
                "## Tool connected\n"
                "The booking calendar for Alder Physio, connected through an MCP server, so Hermes can book follow-up visits for patients.\n\n"
                "## Smallest permission\n"
                "Hermes reads the calendar and adds draft bookings that Dana confirms. Changing or deleting an existing booking "
                "stays out of its reach, because only the read and draft tools are switched on for that server.\n\n"
                "## Approver\n"
                "Dana Whitfield, the practice manager, confirms every draft booking before a patient sees it.\n\n"
                "## Approved once\n"
                "With command approvals set to manual, at 10:22 am I asked Hermes again to delete my scratch folder of copied "
                "bookings. The approval request appeared, I approved it, and the folder was deleted.\n\n"
                "## Turned down once\n"
                "At 10:15 am I asked Hermes to delete the same scratch folder and turned down the approval request. The folder stayed.\n\n"
                "## Where it was logged\n"
                "Both choices appear in the Hermes session where I ran the test, the refusal at 10:15 am and the approval at "
                "10:22 am, so Dana can find them.\n"
            ),
        },
        "complete": {
            "title": "Your turn: Marcus's approval test",
            "intro": (
                "Marcus Oyelaran connects the customer list for Sunrise Pet Boarding. Here is his approval test record with "
                "three blanks. Fill them in, then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "# Approval test: Sunrise Pet Boarding\n\n"
                        "## Tool connected\n"
                        "The customer list spreadsheet for Sunrise Pet Boarding, so Hermes can draft pickup reminders for owners.\n\n"
                        "## Smallest permission\n"
                    )
                },
                {
                    "gap": "permission",
                    "prompt": "Write the smallest permission that still does the job, and one thing that stays out of reach.",
                    "answer": (
                        "Hermes reads one sheet, the pickup list, and drafts reminders. Editing the sheet and sending to anyone "
                        "outside the list stays out of its reach."
                    ),
                    "min_words": 12,
                },
                {"text": "\n\n## Approver\n"},
                {
                    "gap": "approver",
                    "prompt": "Who approves what Hermes sends out? Name one person and say what they do.",
                    "answer": "Tess Calloway, the owner, approves every reminder before it goes out.",
                    "min_words": 8,
                    "needs": ["name"],
                },
                {"text": "\n\n## Approved once\n"},
                {
                    "gap": "approved",
                    "prompt": "Describe the approval you made: when, what appeared, and what happened.",
                    "answer": (
                        "At 2:31 pm, with command approvals on manual, I asked Hermes to delete my scratch folder. The approval "
                        "request appeared, I approved it, and the folder was deleted."
                    ),
                    "min_words": 14,
                    "needs": ["time"],
                },
                {
                    "text": (
                        "\n\n## Turned down once\n"
                        "At 2:40 pm I asked again on a fresh scratch folder and turned down the approval request. The folder stayed.\n\n"
                        "## Where it was logged\n"
                        "Both choices appear in the session where I ran the test, so the owner can find them there.\n"
                    )
                },
            ],
        },
        "coach": [
            {
                "hint": "Ask what Hermes can do after the connection that it could not do before.",
                "example": "Example: once Hermes is connected to a payroll tool, it can change a pay rate. Before, it could only talk about one.",
            },
            {
                "hint": "Think about everything that sits in a drive beyond the folder the client pictured when they asked.",
                "example": "Example: access to an accounting drive also covers old tax returns and payroll files next to the invoices folder.",
            },
            {
                "hint": "Turn the client's request into a question about the least access that still gets the job done.",
                "example": "Example: read one folder named Invoices, with no way to edit or delete a file.",
            },
            {
                "hint": "Ask who reads each thing Hermes wants to send, and whether anyone has watched that step work.",
                "example": "Example: the office manager approves each outgoing email, and she turned down one test email to see the step stop it.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "A church office wants Hermes to read the members spreadsheet and send the weekly newsletter. "
                    "Name what you write down before you connect it."
                ),
                "points": [
                    {
                        "point": "the smallest permission that still does the job: read one sheet and draft the newsletter",
                        "hint": "Ask what Hermes needs to touch, and what it can leave alone.",
                        "example": "Example: read the members sheet, draft the newsletter, and change nothing in the sheet.",
                    },
                    {
                        "point": "who approves the newsletter before it goes out, by name",
                        "hint": "Ask who reads it before hundreds of members do.",
                        "example": "Example: Pastor Elena Torres reads each newsletter and approves it.",
                    },
                    {
                        "point": "that you trigger the approval once and watch it work before real members are on the list",
                        "hint": "Ask how you would know the step works.",
                        "example": "Example: send a test newsletter to the pastor's own address and approve it.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "During your approval test the request appears and you approve it, but you never turn one down. "
                    "The client says that is enough. What do you say?"
                ),
                "points": [
                    {
                        "point": "that turning one down shows the step can stop something, and approving alone cannot show that",
                        "hint": "Ask what a refusal proves that an approval cannot.",
                        "example": "Example: if a turned-down request still sends, the step protects nobody.",
                    },
                    {
                        "point": "that you check where both choices were logged, so someone can find them later",
                        "hint": "Ask where a reader would look afterward.",
                        "example": "Example: both entries appear in the test session with their times.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "A client says, \"Connect it now and we'll choose an approver next month.\" "
                    "What do you answer, and why?"
                ),
                "points": [
                    {
                        "point": "that someone has to own what Hermes sends out before it connects, so you need the name now",
                        "hint": "Ask who answers if a wrong message goes out next week.",
                        "example": "Example: the owner, Jun Park, signs as approver before the tool is connected.",
                    },
                    {
                        "point": "that an approval step nobody has tested can't be trusted, so you run the test first",
                        "hint": "Ask what you know about the step on day one.",
                        "example": "Example: approve one test request and turn down another before anything real is connected.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your approval test",
            "body": (
                "Write your approval test as a text or Markdown file with the six headings below, "
                "about the test you ran.\n"
                "1. Save it.\n"
                "2. Type where you saved it.\n"
                "3. Click Check my work.\n"
                "\n"
                "Hermes also has to list its tools."
            ),
            "verify": "artifact",
            "check": "approval test record",
            "live": "connections",
            "sections": [
                {
                    "heading": "Tool connected", "min_words": 10, "needs": [],
                    "what": "which tool you connected and what Hermes does with it",
                    "hint": "Name the tool and say what you want Hermes to do there.",
                    "example": "Example: The customer list spreadsheet for Sunrise Pet Boarding, so Hermes can draft pickup reminders.",
                },
                {
                    "heading": "Smallest permission", "min_words": 14, "needs": [],
                    "what": "the least access that still does the job, and what stays out of reach",
                    "hint": "Write what Hermes may do and what it may leave alone, before you connect.",
                    "example": "Example: Hermes reads one sheet and drafts reminders. Editing the sheet or sending outside the list stays out of reach.",
                },
                {
                    "heading": "Approver", "min_words": 8, "needs": ["name"],
                    "what": "who approves what Hermes sends, by name",
                    "fix": "Name the person who approves what Hermes sends.",
                    "hint": "Write one person's name and what they do when a request appears.",
                    "example": "Example: Tess Calloway, the owner, approves every reminder before it goes out.",
                },
                {
                    "heading": "Approved once", "min_words": 14, "needs": ["time"],
                    "what": "the request you approved, with the time",
                    "fix": "Add the time you approved it, such as 2:31 pm.",
                    "hint": "Say when you made the request, what appeared, and what happened after you approved.",
                    "example": "Example: At 2:31 pm I asked Hermes to delete my scratch folder, the approval request appeared, and after I approved it the folder was deleted.",
                },
                {
                    "heading": "Turned down once", "min_words": 10, "needs": ["time"],
                    "what": "the request you turned down, with the time",
                    "fix": "Add the time you turned it down.",
                    "hint": "Say when you turned it down and what happened to the request.",
                    "example": "Example: At 2:40 pm I turned down a second request to delete a scratch folder, and the folder stayed.",
                },
                {
                    "heading": "Where it was logged", "min_words": 10, "needs": [],
                    "what": "where each choice shows up afterward",
                    "hint": "Use what Hermes told you in the lab about where each choice was logged.",
                    "example": "Example: Both choices appear in the session where I ran the test, so the owner can find them there.",
                },
            ],
            "proof": (
                "Your approval test record, saved on your computer, with all 6 sections filled in, and Hermes lists the "
                "tools it can use. The record's fingerprint goes on your Field Record."
            ),
            "fixes": {
                "live_failed": {
                    "hint": "Hermes did not list its tools. Choose Reconnect gateway from the Gateway item in the status bar, wait for it to say Connected, and run the check again.",
                    "example": "Example: a gateway that was asleep can take a few seconds to answer after you reconnect.",
                },
            },
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now reads your approval test record, with a named approver and a time for each choice, and "
                    "Hermes still has to list its tools. It used to pass whenever Hermes listed at least one tool."
                ),
            }
        ],
    },
    "integrator.handoff": {
        "minutes": {"lesson": 4, "example": 5, "complete": 10, "lab": 15, "explain": 6, "gate": 20},
        "use": (
            "You said you want Hermes to do this for you: {goal}. When that work runs without you, the next person "
            "needs a guide, so you write one a stranger can follow."
        ),
        "use_plain": (
            "A setup only one person understands stops working when that person leaves. This mission has you write the "
            "guide the next person follows."
        ),
        "lab": {
            "body": (
                "1. Write your handover guide.\n"
                "2. Have Hermes play the client's IT person, with only your guide to go on.\n"
                "3. Fix the line where Hermes gets lost.\n"
                "4. Keep the final version for the check."
            ),
            "prompt": (
                "Play the client's IT person on the day I hand over Hermes. I'll paste my handover guide below this message. "
                "You've never seen the system. Pick the main task and one failure, and try to finish both using only what "
                "the guide says. Stop the moment you can't follow it and tell me which line lost you."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "Write for the person who takes over",
            "lines": [
                "The guide says what runs where, who owns each part, which profiles exist, and what each scheduled job does.",
                "It says where the keys are kept, never the keys themselves, and how to restore and recover.",
                "Test it on someone new to the system: one routine task and one recovery, using only the guide.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "How Omar took over Pinecrest from Jun's guide",
            "intro": (
                "Jun Park set up Hermes for Pinecrest Property Management, then moved to another project. Omar Haddad, "
                "the IT contractor, had never seen the system and had only Jun's guide to go on."
            ),
            "parts": [
                {
                    "label": "Jun listed what runs where",
                    "text": "One line per part: the app on the leasing desk computer, the gateway and scheduled jobs on the office desktop.",
                },
                {
                    "label": "He put a name on every part",
                    "text": "Marisol Vega owns the rent reminders, and Omar owns the desktop and its updates.",
                },
                {
                    "label": "He left the passwords out",
                    "text": "The guide says the logins live in the leasing profile on the office desktop, and it holds none of them.",
                },
                {
                    "label": "He watched Omar use it",
                    "text": "Using only the guide, Omar found the Monday rent reminder job and walked through restoring the Friday backup.",
                },
            ],
            "document": (
                "# Handover guide: Pinecrest Property Management\n\n"
                "## Topology\n"
                "- Hermes app: the leasing desk computer\n"
                "- Gateway and scheduled jobs: the office desktop, which stays on\n\n"
                "## Owners\n"
                "Marisol Vega, the office manager, owns the weekly rent reminders. Omar Haddad, the IT contractor, owns the "
                "desktop and its updates.\n\n"
                "## Profiles\n"
                "One profile, called leasing, holds the memory, skills and saved logins for the rent reminders.\n\n"
                "## Integrations\n"
                "Hermes reads the tenant spreadsheet and drafts emails in the office mailbox. It reads one spreadsheet only and "
                "sends nothing without Marisol's approval.\n\n"
                "## Secrets\n"
                "Logins live in the leasing profile on the office desktop, and the sign-in list for that profile sits in the "
                "office safe. This guide holds none of them.\n\n"
                "## Cron\n"
                "The rent reminder job runs every Monday at 8 am. The month-end summary runs at 5 pm on the last day of each month.\n\n"
                "## Backups\n"
                "Omar makes a backup of the leasing profile every Friday at 6 pm and keeps the last four copies on an external drive.\n\n"
                "## Recovery\n"
                "1. If the reminders stop, Marisol calls Omar on his mobile before 9 am.\n"
                "2. Omar checks that the desktop is on and the gateway is running.\n"
                "3. If the desktop has failed, Omar restores the latest Friday backup on the spare computer and reconnects the app.\n\n"
                "## Limits\n"
                "- Hermes sends no message without Marisol's approval\n"
                "- Hermes reads one spreadsheet and touches no payment records\n"
            ),
        },
        "complete": {
            "title": "Your turn: Tobias's guide for Larkspur Florist",
            "intro": (
                "Tobias Reinholt is handing over the setup at Larkspur Florist to Joy Adeyemi, the shop manager. Fill in "
                "three blanks in his guide, then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "# Handover guide: Larkspur Florist\n\n"
                        "## Topology\n"
                        "- Hermes app: the front counter computer\n"
                        "- Gateway and reminder jobs: the back room computer, which stays on all day\n\n"
                        "## Owners\n"
                    )
                },
                {
                    "gap": "owners",
                    "prompt": "Name who owns each part. Use a real person's name for each one.",
                    "answer": (
                        "Joy Adeyemi, the shop manager, owns the delivery reminders. Femi Adeyemi, her cousin, owns the back "
                        "room computer and its updates."
                    ),
                    "min_words": 12,
                    "needs": ["name"],
                },
                {
                    "text": (
                        "\n\n## Profiles\n"
                        "One profile, called florist, holds the memory, skills and saved logins for the delivery reminders.\n\n"
                        "## Integrations\n"
                        "Hermes reads the order sheet and drafts text messages to customers. Joy approves each message before "
                        "it is sent, and Hermes reaches nothing else.\n\n"
                        "## Secrets\n"
                        "Logins live in the florist profile on the back room computer, and the sign-in list is in Joy's locked "
                        "drawer. This guide holds none of them.\n\n"
                        "## Cron\n"
                        "The delivery reminder job runs every evening at 7 pm, and the weekly stock list runs on Monday at 8 am.\n\n"
                        "## Backups\n"
                    )
                },
                {
                    "gap": "backups",
                    "prompt": "Who makes the backup, how often, and how many copies do they keep?",
                    "answer": "Femi makes a backup of the florist profile every Sunday at 9 pm and keeps the last three copies.",
                    "min_words": 12,
                    "needs": ["time"],
                },
                {"text": "\n\n## Recovery\n"},
                {
                    "gap": "recovery",
                    "prompt": "Write three recovery steps, one numbered line each, with a person named in each.",
                    "answer": (
                        "1. If reminders stop, Joy calls Femi.\n"
                        "2. Femi checks that the back room computer is on and the gateway is running.\n"
                        "3. If the computer has failed, Femi restores the Sunday backup on a spare."
                    ),
                    "min_words": 20,
                    "needs": ["list"],
                },
                {
                    "text": (
                        "\n\n## Limits\n"
                        "- Hermes sends nothing to a customer until Joy approves it\n"
                        "- Hermes never reads card payment details\n"
                    )
                },
            ],
        },
        "coach": [
            {
                "hint": "Ask what a stranger must manage alone: pick one everyday task and one failure.",
                "example": "Example: restart a stopped reminder job, and restore last Sunday's backup on a spare computer.",
            },
            {
                "hint": "List what the reader must know before touching anything: the parts, who owns each, how to switch it on and off, and where to read what happened.",
                "example": "Example: the guide names the desktop, its owner, the steps to stop and start the gateway, and where the logs are read.",
            },
            {
                "hint": "Think about the day the computer dies, and the day a client asks for something it was never meant to do.",
                "example": "Example: steps to restore Sunday's backup, and a short list of things Hermes never touches, such as payroll.",
            },
            {
                "hint": "Name a person and a way to reach them, for each kind of failure.",
                "example": "Example: the IT helper's mobile for a stopped job, and the director for anything that touched a customer.",
            },
            {
                "hint": "Ask who should try the guide, and what you do while they try.",
                "example": "Example: the office assistant, who never saw the setup, restarts a job and restores a backup while you stay silent and write down where she gets stuck.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "The client's IT person follows your guide and stops at Recovery: step two says to restore the backup "
                    "but never says where it is. What do you conclude, and what do you do?"
                ),
                "points": [
                    {
                        "point": "that the guide has a gap, and the line that lost them is where to fix it",
                        "hint": "Ask whose problem it is when a reader gets stuck.",
                        "example": "Example: the gap is the guide's. The reader did nothing wrong by stopping.",
                    },
                    {
                        "point": "to add where the backups live and who holds the drive",
                        "hint": "Write the missing fact into the step itself.",
                        "example": "Example: step two now reads: restore the latest copy from the external drive in the office safe.",
                    },
                    {
                        "point": "to run it again with a different person, because a fix you wrote yourself is still untested",
                        "hint": "Ask who tests the new line.",
                        "example": "Example: the office assistant repeats the recovery from the updated guide.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": "A client wants the email password written into the guide so the IT person can log in. What do you say?",
                "points": [
                    {
                        "point": "that Secrets says where logins live and holds none of them",
                        "hint": "Ask what a printed guide can safely say about a login.",
                        "example": "Example: the logins live in the florist profile, and the sign-in list is in the manager's locked drawer.",
                    },
                    {
                        "point": "that a guide gets emailed, printed and left on desks, so anything in it travels",
                        "hint": "Think about where copies of the guide end up.",
                        "example": "Example: a copy sits in a contractor's inbox long after the project ends.",
                    },
                    {
                        "point": "that the owner grants the IT person access directly, so the guide only points to where to ask",
                        "hint": "Name who hands out access.",
                        "example": "Example: the shop manager gives the IT person the sign-in list in person.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": "The client's office manager says, \"I read your guide and it's clear.\" Do you sign off, and why?",
                "points": [
                    {
                        "point": "that a clear read proves little, so someone who never saw the system has to do the work with it",
                        "hint": "Ask what reading shows and what doing shows.",
                        "example": "Example: the assistant follows the guide to restart a job and can't find the logs.",
                    },
                    {
                        "point": "one routine task and one recovery, using only the guide, while you watch and note where they stall",
                        "hint": "Name the two things the test has to include.",
                        "example": "Example: restart the stopped reminder job, then restore a backup on a spare computer.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your handover guide",
            "body": (
                "Write your handover guide as a text or Markdown file with the nine headings below and "
                "real content in each. Keep every secret out of it.\n"
                "1. Save it.\n"
                "2. Type where you saved it.\n"
                "3. Click Check my work."
            ),
            "verify": "artifact",
            "check": "handover guide",
            "sections": [
                {
                    "heading": "Topology", "min_words": 12, "needs": ["list"],
                    "what": "what runs where, one part per line",
                    "fix": "List at least two parts, one per line, each starting with a dash.",
                    "hint": "Write one line per part and say which computer it runs on.",
                    "example": "Example:\n- Hermes app: the front desk laptop\n- Gateway and scheduled jobs: the office desktop, which stays on",
                },
                {
                    "heading": "Owners", "min_words": 14, "needs": ["name"],
                    "what": "who owns each part, by name",
                    "fix": "Name a person for each part, not a team.",
                    "hint": "Beside each part, write the person who answers for it.",
                    "example": "Example: Keisha Brandt, the director, owns the weekly progress emails. Alan Cho, the IT helper, owns the desktop and its updates.",
                },
                {
                    "heading": "Profiles", "min_words": 10, "needs": [],
                    "what": "which profiles exist and what each one holds",
                    "hint": "Name each profile and say what memory, skills and logins sit under it.",
                    "example": "Example: Two profiles: tutoring for the progress emails and admin for payroll reminders, each with its own memory and logins.",
                },
                {
                    "heading": "Integrations", "min_words": 14, "needs": [],
                    "what": "which tools Hermes touches, with the permission on each",
                    "hint": "List each connected tool, what Hermes may do with it, and who approves what it sends.",
                    "example": "Example: Hermes reads the student roster sheet and drafts emails in the shared inbox. Keisha approves every email before it goes out.",
                },
                {
                    "heading": "Secrets", "min_words": 14, "needs": [],
                    "what": "where logins live, and nothing that grants access",
                    "hint": "Say which profile and which place hold the logins. Leave every password, key and code out.",
                    "example": "Example: Logins live in the tutoring profile on the office desktop, and the sign-in list is in the director's locked drawer. This guide holds none of them.",
                },
                {
                    "heading": "Cron", "min_words": 12, "needs": ["time"],
                    "what": "each scheduled job and when it runs",
                    "fix": "Say when each job runs, such as every Thursday at 4 pm.",
                    "hint": "List each scheduled job with its day and time.",
                    "example": "Example: The progress email job runs every Thursday at 4 pm. The attendance summary runs at 8 am each school day.",
                },
                {
                    "heading": "Backups", "min_words": 12, "needs": ["time"],
                    "what": "who backs up what, how often, and where the copies are",
                    "fix": "Say how often the backup is made, such as every Sunday at 9 pm.",
                    "hint": "Name who makes the backup, how often, and where the copies are kept.",
                    "example": "Example: Alan backs up the tutoring profile every Sunday at 9 pm and keeps the last three copies on an external drive.",
                },
                {
                    "heading": "Recovery", "min_words": 20, "needs": ["list"],
                    "what": "the steps to take when it stops, one numbered line per step",
                    "fix": "Write the steps as separate numbered lines, 1. then 2. then 3.",
                    "hint": "Number each step on its own line and say who does it.",
                    "example": "Example:\n1. If emails stop, Keisha calls Alan.\n2. Alan checks that the desktop is on.\n3. If it has failed, Alan restores the Sunday backup.",
                },
                {
                    "heading": "Limits", "min_words": 10, "needs": ["list"],
                    "what": "at least two things Hermes was set up never to do",
                    "fix": "List at least two limits, one per line, each starting with a dash.",
                    "hint": "Write the requests you expect later and decide now that they stay out.",
                    "example": "Example:\n- Nothing goes to parents without Keisha's approval\n- Hermes never reads payment records",
                },
            ],
            "proof": (
                "Your handover guide, saved on your computer, with all 9 sections filled in with real content. "
                "Its fingerprint goes on your Field Record."
            ),
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now reads inside each of the nine sections: named owners, a time for each job and backup, "
                    "separate numbered recovery steps, and a list in Topology and Limits. It used to look for the nine "
                    "headings and a file over 240 characters."
                ),
            }
        ],
    },
}


CAPSTONE = {
    "id": "integrator.capstone",
    "title": "Run a small engagement on your own problem",
    "promise": (
        "Take one real task of your own from first meeting to handover, then report against criteria you wrote "
        "before you started."
    ),
    "outcome": "A report on your own engagement: the criteria you set, the evidence for each, and what you do next.",
    "level_meaning": "You can run one small engagement on a problem of your own and say, with evidence, whether it worked.",
    "sources": ["tony", "official_multi", "official_tools", "official_desktop"],
    "watch": ["nous.learning_path", "lab.2", "lab.4", "lab.6", "nous.checkpoints"],
    "lesson": {
        "title": "Write the criteria before you build",
        "body": (
            "Pick one task of your own that repeats, and run it through a small engagement: scope it, set Hermes up, "
            "connect one tool with the smallest permission, and write the handover note. Before you start, write three or "
            "more numbered criteria, at least two with a number. When you finish, write one line of evidence for each "
            "criterion, ending met, partly met or not met. A criterion you can't count can't fail."
        ),
        "source": "tony",
    },
    "lab": {
        "title": "Run it on your own task",
        "body": (
            "1. Write your criteria before you begin.\n"
            "2. Work with Hermes to scope your task, set it up and connect one tool. Keep notes as you "
            "go.\n"
            "3. Write your report with the six headings the check lists."
        ),
        "prompt": (
            "I want to run a small engagement on a real task of my own. Ask me the six scope questions one at a time: which "
            "work repeats, who owns the result, which systems it touches, what a good result looks like in numbers, what "
            "happens when it's wrong, and who signs off. Then help me write three numbered criteria with at least two "
            "numbers in them. When I report back, challenge any line I mark met without evidence."
        ),
    },
    "explain": {
        "title": "Explain what carries over",
        "question": (
            "A volunteer food pantry asks you to set up Hermes to sort sign-ups from 200 volunteers. It has no budget, no "
            "office computer, and a coordinator who changes every three months. Say which parts of your process carry "
            "over, and which parts you change."
        ),
        "covers": [
            "that you still scope one task with a named owner, even when the work is free and the owner is a volunteer",
            "that the success criteria still carry numbers, so everyone agrees when the sign-up work is done",
            "that where it runs changes: a volunteer's laptop leaves with the volunteer, so you ask whose computer it is and who answers when it stops",
            "that the permission stays small and the approval step gets tested, because the sign-ups hold volunteers' personal details",
            "that the handover guide matters more, because the coordinator changes every three months and a newcomer has to run it from the guide alone",
        ],
        "coach": [
            {
                "hint": "Ask what you would write at the top of the scope when nobody is paying. The task and the owner still need names.",
                "example": "Example: a choir wants Hermes to track who has returned sheet music. The task is one list, and Kenji Mori, the librarian, owns it.",
            },
            {
                "hint": "Think about how the pantry would know the sign-up work is done. A feeling won't settle a disagreement.",
                "example": "Example: every new sign-up has a row by Sunday night, and the coordinator corrects fewer than 5 rows in 100.",
            },
            {
                "hint": "Ask who owns the computer, who is the person behind it, and what happens when that person goes away.",
                "example": "Example: a school PTA runs Hermes on the treasurer's laptop, and the laptop goes with the treasurer when the term ends.",
            },
            {
                "hint": "Ask what Hermes would touch and who would read what it sends. Free work still carries people's details.",
                "example": "Example: Hermes reads the sign-up sheet only, and the coordinator approves each reminder text before it goes out.",
            },
            {
                "hint": "Picture a newcomer on their first day with only the guide. What does that person need to finish alone?",
                "example": "Example: a new coordinator restarts a stopped job and restores a backup, using only the guide, in the first week.",
            },
        ],
    },
    "use": (
        "You said you want Hermes to do this for you: {goal}. This mission has you run that task through a small "
        "engagement and report honestly on whether it worked."
    ),
    "use_plain": (
        "This mission has you take one real task of your own through scope, setup, one connection and handover, then "
        "report on whether it worked."
    ),
    "minutes": {"lesson": 4, "example": 5, "complete": 8, "lab": 45, "explain": 8, "gate": 25},
    "story_first": True,
    "takeaway": {
        "title": "Write the criteria before you build",
        "lines": [
            "Run one repeating task of your own through scope, setup, one connection and a handover note.",
            "Before you start, write three or more numbered criteria, with a number in at least two.",
            "When you finish, give each criterion one line of evidence ending met, partly met or not met.",
        ],
        "picture": "",
    },
    "worked": {
        "title": "How Rosalind graded her own Sunday chore",
        "intro": (
            "Rosalind Achebe, a wedding photographer, spent about four hours every Sunday copying inquiry emails into a "
            "spreadsheet and drafting first replies. She ran one small engagement on that chore."
        ),
        "parts": [
            {
                "label": "She wrote the criteria first",
                "text": "Before building anything she wrote four numbered criteria. Three carried a number, such as 9 of 10 drafts needing no edits.",
            },
            {
                "label": "She ran it end to end",
                "text": "She scoped the task, set Hermes up on the studio laptop, connected her inquiry mailbox, and handed the note to her brother Kofi.",
            },
            {
                "label": "She marked each criterion with evidence",
                "text": "Eight of ten drafts needed no edits, so that line ended partly met. Sunday work took 55 minutes, which was met.",
            },
            {
                "label": "She named what failed",
                "text": "Hermes skipped two inquiries that came in as photos of handwritten notes, and her report says so.",
            },
        ],
        "document": (
            "# Engagement report: Achebe Photography\n\n"
            "## Problem\n"
            "Rosalind Achebe, a wedding photographer, spends about 4 hours every week copying new inquiry emails into a "
            "spreadsheet and drafting first replies. Late replies lose bookings.\n\n"
            "## Criteria\n"
            "1. Every inquiry from the past week has a spreadsheet row by Sunday at 6 pm\n"
            "2. At least 9 of 10 draft replies need no edits from Rosalind\n"
            "3. Sunday time on inquiries drops from four hours to under one\n"
            "4. Hermes sends nothing without Rosalind's approval\n\n"
            "## What I did\n"
            "I scoped one task, wrote the criteria above, and set Hermes up on the studio laptop under a profile called "
            "inquiries. I connected one tool, her inquiry mailbox, with read access to a single label, and tested the "
            "approval step by approving one draft and turning one down. Her brother Kofi Achebe took the handover note and "
            "restored the Friday backup from it.\n\n"
            "## Evidence\n"
            "1. Twelve of twelve inquiries had a row by 5:40 pm on the first Sunday, met\n"
            "2. Eight of ten drafts needed no edits, partly met\n"
            "3. Sunday work took 55 minutes, met\n"
            "4. The approval step stopped two test drafts and nothing went out unapproved, met\n\n"
            "## What did not work\n"
            "Hermes skipped the two inquiries that arrived as photos of handwritten notes, so I typed those rows myself. "
            "The drafts also sounded stiff until Rosalind added three of her own sentences to the profile's memory.\n\n"
            "## Next\n"
            "Yes, keep it running for a month. Kofi reviews the Sunday list for four weeks, and Rosalind then decides "
            "whether to add her assistant's mailbox.\n"
        ),
    },
    "complete": {
        "title": "Your turn: Kwame's engagement report",
        "intro": (
            "Kwame Asante runs a landscape lighting company, and this is his engagement report with three blanks. "
            "Fill them in, then compare with our answers."
        ),
        "parts": [
            {
                "text": (
                    "# Engagement report: Asante Landscape Lighting\n\n"
                    "## Problem\n"
                    "Crew leaders text Kwame Asante photos of finished jobs, and every Friday he spends about three hours "
                    "turning them into completion emails for customers. Late emails delay payment.\n\n"
                    "## Criteria\n"
                )
            },
            {
                "gap": "criteria",
                "prompt": "Write three numbered criteria for this engagement. Put a number in at least two of them.",
                "answer": (
                    "1. Every job finished this week has a completion email drafted by Friday at 3 pm\n"
                    "2. At least 8 of 10 drafts need no edits from Kwame\n"
                    "3. Kwame's Friday email time drops from three hours to under one hour"
                ),
                "min_words": 18,
                "needs": ["list"],
            },
            {
                "text": (
                    "\n\n## What I did\n"
                    "I wrote down the one task and the criteria, then ran Hermes on the shop computer under a profile called "
                    "jobs. The one connection was the shared photo folder, read-only, and I approved one email and turned "
                    "one down to test the approval step. Priya Nair, the office assistant, took the handover note and "
                    "restarted a stopped job from it.\n\n"
                    "## Evidence\n"
                )
            },
            {
                "gap": "evidence",
                "prompt": "Write one numbered evidence line per criterion, each ending met, partly met or not met.",
                "answer": (
                    "1. Seven of seven finished jobs had a draft by 2:40 pm, met\n"
                    "2. Six of ten drafts needed no edits, partly met\n"
                    "3. Friday email time fell to 50 minutes, met"
                ),
                "min_words": 18,
                "needs": ["list", "verdict"],
            },
            {
                "text": (
                    "\n\n## What did not work\n"
                    "Hermes drafted emails for jobs that were still open, because crew leaders post photos early. I added a "
                    "rule to the profile's memory to wait for the word done in the text.\n\n"
                    "## Next\n"
                )
            },
            {
                "gap": "next",
                "prompt": "Start with yes, later or no, then say what you do next and why.",
                "answer": "Later. Run it for four more Fridays and fix the open-jobs problem first, then decide whether to add the second crew's photo folder.",
                "min_words": 10,
                "needs": ["decision"],
            },
        ],
    },
    "review": [
        {
            "id": "r1",
            "question": (
                "Two weeks into an engagement you see that your second criterion, \"the drafts are good,\" can't come "
                "out met or not met. What do you change, and why?"
            ),
            "points": [
                {
                    "point": "rewrite it as something you can count, such as how many drafts need no edits",
                    "hint": "Ask what you could count to show a draft is good.",
                    "example": "Example: at least 9 of 10 replies need no edits from the owner.",
                },
                {
                    "point": "that you fix it now and say so in the report, because a criterion written after the work can flatter the result",
                    "hint": "Ask what changes when criteria are written after the results are in.",
                    "example": "Example: the report notes the rewrite date and keeps the old wording beside it.",
                },
            ],
        },
        {
            "id": "r2",
            "question": (
                "Your evidence line says \"met,\" but the only proof is that the owner said the new routine felt "
                "faster. What is missing?"
            ),
            "points": [
                {
                    "point": "a count or a time you measured, which a criterion with a number calls for",
                    "hint": "Ask what number the criterion names, and whether you have it.",
                    "example": "Example: the criterion says under one hour, so the line needs the minutes the work took.",
                },
                {
                    "point": "to mark the line partly met until the number exists, since a feeling can't settle a verdict",
                    "hint": "Choose the honest verdict while the measurement is missing.",
                    "example": "Example: partly met, with the owner's comment noted and a plan to time next Friday.",
                },
            ],
        },
        {
            "id": "r3",
            "question": "Your report shows two criteria met and one not met. What goes in Next, and why?",
            "points": [
                {
                    "point": "a decision starting with yes, later or no, so the reader knows whether the work goes on",
                    "hint": "Ask what the reader has to decide after your report.",
                    "example": "Example: Later. Fix the missed criterion first, then decide.",
                },
                {
                    "point": "the missed criterion named, with the first thing you change about it",
                    "hint": "Point at the one line that came out not met.",
                    "example": "Example: the drafts still need edits, so the first change is adding the owner's own phrases to memory.",
                },
            ],
        },
    ],
    "gate": {
        "title": "Check your engagement report",
        "body": (
            "Write your report as a text or Markdown file with the six headings below, about your own "
            "task. Number your criteria and write one numbered evidence line for each.\n"
            "1. Save it.\n"
            "2. Type where you saved it.\n"
            "3. Click Check my work."
        ),
        "verify": "artifact",
        "check": "engagement report",
        "cross": "criteria",
        "sections": [
            {
                "heading": "Problem", "min_words": 15, "needs": ["time"],
                "what": "your task, who it belongs to, and what it costs now",
                "fix": "Say how often the task happens or how long it takes now.",
                "hint": "Describe the task, say whose it is, and say how often it comes and how long it takes today.",
                "example": "Example: Maya Chen, a dog trainer, spends two hours every Monday writing session notes for clients.",
            },
            {
                "heading": "Criteria", "min_words": 20, "needs": ["list"],
                "what": "three or more numbered criteria, at least two with a number",
                "fix": "List at least three, one per line, each starting with a number.",
                "hint": "Write what you will see when it works, with counts and times, before you look at any results.",
                "example": "Example:\n1. Every client has notes by Tuesday at noon\n2. At least 8 of 10 notes need no edits\n3. Monday time drops from two hours to 40 minutes",
            },
            {
                "heading": "What I did", "min_words": 25, "needs": ["name"],
                "what": "how you scoped it, set it up, connected one tool and handed it over",
                "fix": "Name the person who approved the approval test or took the handover.",
                "hint": "Cover scope, setup, the one connection with its permission, the approval test, and who took the handover.",
                "example": "Example: I scoped one task, ran Hermes on the studio laptop, connected the notes folder read-only, and Maya's assistant, Lena Voss, took the handover note.",
            },
            {
                "heading": "Evidence", "min_words": 15, "needs": ["list", "verdict"],
                "what": "one numbered line per criterion, each ending with a verdict",
                "fix": "Write one numbered line per criterion, ending met, partly met or not met.",
                "hint": "Match each line to the criterion with the same number, and give a count or a time before the verdict.",
                "example": "Example:\n1. Eleven of eleven clients had notes by Tuesday at 10 am, met\n2. Six of ten notes needed no edits, partly met\n3. Monday work took 35 minutes, met",
            },
            {
                "heading": "What did not work", "min_words": 15, "needs": [],
                "what": "what failed or surprised you, and what you changed",
                "hint": "Say one thing that went wrong and what you did about it.",
                "example": "Example: Hermes missed notes dictated in a noisy yard, so I added a rule that Maya rereads those three clients' notes herself.",
            },
            {
                "heading": "Next", "min_words": 12, "needs": ["decision"],
                "what": "a decision to continue, wait or stop, with the reason",
                "fix": "Start with yes, later or no, then say why.",
                "hint": "Start with the decision, then say what you do next and who does it.",
                "example": "Example: Yes, keep it running through the spring season, and Lena reviews the weekly notes until the next check.",
            },
        ],
        "proof": (
            "Your engagement report, saved on your computer, with all 6 sections, three or more criteria, and one "
            "numbered evidence line for each. Its fingerprint goes on your Field Record."
        ),
    },
    "revisions": [
        {
            "version": 1,
            "kind": "added",
            "summary": (
                "New in 0.5.0: a final mission where you run a small engagement on your own task, write your criteria "
                "first, and report evidence against each one."
            ),
        }
    ],
}


PLACEMENT = {
    "title": "Placement check",
    "intro": (
        "Six scenario questions show where on the Integrator path to start. Get both questions at a level right and "
        "that level's reading and practice can be skipped. The checks on your own work still apply to every mission."
    ),
    "minutes": 5,
    "questions": [
        {
            "id": "p1",
            "level": "beginner",
            "question": (
                "A law office manager tells you, \"We need an AI agent for the firm.\" You haven't quoted a price yet. "
                "What do you do first?"
            ),
            "options": [
                "Quote a monthly price based on the number of staff and the size of the office",
                "Ask which one task repeats every week and who owns its result",
                "Install Hermes on the office computer and see what it does",
                "Ask which AI model the firm would like to use for its documents",
            ],
            "answer": 1,
            "why": (
                "One repeating task with a named owner is what you can scope and price. A price from staff numbers guesses "
                "at the work, installing first skips the scoping, and the choice of model comes long after the task is known."
            ),
        },
        {
            "id": "p2",
            "level": "beginner",
            "question": (
                "Three weeks after the client signs, they ask you to add invoicing, which the scope never mentioned. "
                "What do you do first?"
            ),
            "options": [
                "Add it quietly, since it looks like a small change, and mention it at the next review",
                "Say it can't be done, and close out the whole project with a note to the owner",
                "Raise the monthly price to cover the extra work it brings, starting next month",
                "Point to the out-of-scope list and offer invoicing as a second project",
            ],
            "answer": 3,
            "why": (
                "The out-of-scope list is where invoicing was left out, so you point to it and offer a second project. "
                "Adding it quietly erases the finish line, closing the project loses a good client, and a higher price "
                "never settles what the first project covers."
            ),
        },
        {
            "id": "p3",
            "level": "intermediate",
            "question": (
                "A client wants Hermes on the office manager's laptop so a report goes out at 7 each morning. She takes "
                "the laptop home every night. What do you tell them?"
            ),
            "options": [
                "Run it on a computer that stays on at the office, or in Hermes Cloud",
                "A laptop works fine because Hermes runs in the background even when the lid is closed",
                "Move it to a rented server, since a server never stops and needs no care",
                "Ask her to leave the lid open and the laptop plugged in overnight",
            ],
            "answer": 0,
            "why": (
                "A laptop that travels takes the gateway with it. A closed lid stops the work, a rented server still needs "
                "someone to install updates and take the 2am call, and an open lid overnight depends on one person's habit."
            ),
        },
        {
            "id": "p4",
            "level": "intermediate",
            "question": (
                "A client asks you to connect Hermes to their shared drive \"so it can find things.\" "
                "What do you do before you connect it?"
            ),
            "options": [
                "Connect it with full read access so it finds everything, and review the log afterward",
                "Ask the client to choose a strong password for the connection and store it",
                "Write the smallest permission, name the approver, and test the approval",
                "Wait until all of the client's staff have been trained on how to use Hermes",
            ],
            "answer": 2,
            "why": (
                "Connecting a tool gives Hermes the power to act with it, and read access to a drive covers everything on "
                "it. A full connection reviewed afterward is too late, a password says nothing about scope, and training "
                "leaves the permission unset."
            ),
        },
        {
            "id": "p5",
            "level": "advanced",
            "question": (
                "You finish a handover guide and leave the client's site tomorrow. Which test shows the guide is ready?"
            ),
            "options": [
                "You read it through twice, fix every typo you find, and send it to the owner",
                "A stranger does one routine task and one recovery using only the guide",
                "The owner reads it over on the call and says it looks very thorough to them",
                "It covers every setting that Hermes has, in the order the menus show them",
            ],
            "answer": 1,
            "why": (
                "A stranger doing the work with only the guide shows where it fails. Rereading it yourself misses gaps "
                "you can fill from memory, an owner's approval of the look shows nothing about the steps, and covering every "
                "setting hides the few steps that matter."
            ),
        },
        {
            "id": "p6",
            "level": "advanced",
            "question": (
                "The client's IT person follows your guide and stalls at Recovery step two, which says \"restore the "
                "backup\" and nothing about where it is. What does that tell you?"
            ),
            "options": [
                "The IT person needs more training before they take it over",
                "The guide is fine, since that step already names the task",
                "The client should hire a more experienced IT contractor",
                "The guide has a gap, so add where the backup lives and retest it",
            ],
            "answer": 3,
            "why": (
                "The line that lost the reader is the line to fix, and a different person has to test the fix. Blaming "
                "training or the contractor leaves the gap in place, and a step that names a task without the facts "
                "to do it fails the guide's purpose."
            ),
        },
    ],
}
