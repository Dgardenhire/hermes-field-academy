"""Ambassador Partner path content. Format: docs/content-format.md.

All three missions check a document. The people who teach Hermes are credited by
name: Nous Research maintains it, and the community teachers in EPISODES do the
best teaching. Nobody named here has endorsed Field Academy.
"""

MISSIONS = {
    "ambassador.firsthand": {
        "minutes": {"lesson": 2, "example": 3, "complete": 5, "lab": 15, "explain": 5, "gate": 8},
        "use": (
            "You said you want Hermes to do this for you: {goal}. Give Hermes one small piece of that job and "
            "watch what it does, so what you later tell people comes from what you saw."
        ),
        "use_plain": (
            "Before you explain Hermes to anyone, give it one small real job from your own work and watch it. "
            "Your notes on what it did and got wrong keep your explanation honest."
        ),
        "story_first": True,
        "takeaway": {
            "title": "Watch it work before you explain it",
            "lines": [
                "Give Hermes one small job from your own week and watch every step it takes.",
                "Write down what it did, what it got wrong, and where you had to help.",
                "Those notes are what you tell a client, because you saw it happen yourself.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "What happened when Priya tried it",
            "intro": (
                "Priya Raman runs Lantern Catering with four cooks. A client asked whether Hermes was worth it. "
                "She had never used it, so she gave it one real job first."
            ),
            "parts": [
                {
                    "label": "She picked a small real job",
                    "text": "Monday's prep list takes her about 40 minutes. She pasted five order emails into Hermes and asked for a prep list sorted by day.",
                },
                {
                    "label": "She watched what it did",
                    "text": "Hermes pulled out each dish and added up the portions. It told her it couldn't open her inbox, because she hadn't connected it.",
                },
                {
                    "label": "She caught the mistake",
                    "text": "One order showed up twice, inside a reply, and Hermes counted it twice. She saw the doubled salads because she read every line.",
                },
                {
                    "label": "She wrote down what she'd say",
                    "text": "Her note for the client: it saved about 30 minutes, and a person still reads the list before it reaches the kitchen.",
                },
            ],
            "document": (
                "# First-hand notes: Priya Raman\n\n"
                "## The job\n"
                "Every Monday Priya turns the week's catering orders into one prep list for her four cooks. By hand it "
                "takes about 40 minutes. She pasted five order emails into Hermes and asked for a prep list sorted by day.\n\n"
                "## What Hermes did\n"
                "- Read all five emails and pulled out each dish, the number of guests and the delivery day.\n"
                "- Grouped the dishes by day and added up the portions for each one.\n"
                "- Said it could not open her inbox, because she had not connected it, so she pasted the emails in.\n\n"
                "## What went wrong\n"
                "One client had replied to her own order email, so that order appeared twice. Hermes counted it twice "
                "and doubled Thursday's salads. Priya caught it because she read every line before printing.\n\n"
                "## What I would tell a client\n"
                "It took about 10 minutes, including my check, against 40 by hand. It reads messy emails well and can "
                "count the same order twice, so a person reads the list before it reaches the kitchen.\n"
            ),
        },
        "complete": {
            "title": "Finish Omar's notes",
            "intro": (
                "Omar Haddad manages twelve rental units and gave Hermes three tenant repair emails to answer. "
                "Fill in the three blanks from what happened, then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "# First-hand notes: Omar Haddad\n\n"
                        "## The job\n"
                        "Every week Omar answers tenant repair emails, about 45 minutes for a normal batch. He gave "
                        "Hermes three of this week's emails and asked for a draft reply to each, offering a visit "
                        "time from his Tuesday schedule.\n\n"
                        "## What Hermes did\n"
                    )
                },
                {
                    "gap": "did",
                    "prompt": "List what Hermes did, one step per line starting with a dash.",
                    "answer": (
                        "- Read the three emails Omar pasted in and named the repair in each one.\n"
                        "- Drafted a short reply to each tenant, offering a Tuesday visit.\n"
                        "- Said it could not see his calendar, so it used the free times he typed in."
                    ),
                    "min_words": 20,
                    "needs": ["list"],
                },
                {"text": "\n\n## What went wrong\n"},
                {
                    "gap": "wrong",
                    "prompt": "Name one thing Hermes got wrong or needed help with, and how Omar caught it.",
                    "answer": "Hermes offered two tenants the same 10 am slot. Omar caught it because he read every draft before sending, and he moved one visit to 1 pm.",
                    "min_words": 14,
                },
                {"text": "\n\n## What I would tell a client\n"},
                {
                    "gap": "client",
                    "prompt": "Write what Omar would honestly tell a client, limits included.",
                    "answer": "It turned 45 minutes of replies into about 15, counting my check. The drafts were good, and I still read each one before a tenant sees it, because it can double-book a visit.",
                    "min_words": 16,
                },
                {"text": "\n"},
            ],
        },
        "coach": [
            {
                "hint": "Name the actual job you handed over, from your own work, and say how big it was.",
                "example": "Example: I gave Hermes the list of next week's 22 dental appointments and asked for one reminder text each.",
            },
            {
                "hint": "Describe the steps you watched, in order, including anything Hermes said it could not reach.",
                "example": "Example: It read the appointments, wrote 22 texts with the time and the dentist's name, and said it could not send them because no texting tool was connected.",
            },
            {
                "hint": "Pick one real mistake, or one place you had to step in, and say how you noticed it.",
                "example": "Example: It wrote 9 am for a 9 pm appointment. I caught it because I compared each text with the schedule.",
            },
            {
                "hint": "Think about what you can say to a client now that you couldn't say before you watched it work.",
                "example": "Example: I tell a client it cut 30 minutes to 10, and that I caught one wrong time, because I watched it happen.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "A prospect saw a demo video where Hermes did a job perfectly, and asks if that is what it is "
                    "like. Say what you answer, and what you base it on."
                ),
                "points": [
                    {
                        "point": "what you saw when you gave Hermes a real job of your own",
                        "hint": "Answer from your own notes, with the job you gave it.",
                        "example": "Example: When I had it sort my supplier invoices, it got 18 of 20 right on the first pass.",
                    },
                    {
                        "point": "one thing it got wrong or needed help with, said plainly",
                        "hint": "Name the mistake or the help it needed.",
                        "example": "Example: It read one invoice date backwards, and I fixed it before filing.",
                    },
                    {
                        "point": "that a person checks the work before it reaches a customer",
                        "hint": "Say who reads the result, and why.",
                        "example": "Example: I read every result before it goes out, because it can get a step wrong.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "You asked Hermes to draft three emails to suppliers, and it spelled one supplier's name wrong. "
                    "Say what goes in your notes and what you tell a client."
                ),
                "points": [
                    {
                        "point": "the mistake under What went wrong, with how you caught it",
                        "hint": "Write the mistake down plainly, with how you noticed.",
                        "example": "Example: It wrote Harlan Feed as Harlen Feed. I caught it reading the draft before sending.",
                    },
                    {
                        "point": "that a client hears the mistake too, with what a person does about it",
                        "hint": "Say what you tell the client and who checks drafts.",
                        "example": "Example: The drafts save time, and someone reads each one before it is sent.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "During your job, Hermes said it couldn't open your calendar, so you typed the dates in yourself. "
                    "Say what that tells you and how you explain it to a client."
                ),
                "points": [
                    {
                        "point": "that Hermes works with the tools and accounts you allow, and the calendar wasn't one of them",
                        "hint": "Ask what Hermes could reach during the job.",
                        "example": "Example: Hermes only reaches the accounts I connect, and I hadn't connected my calendar.",
                    },
                    {
                        "point": "that connecting it is a setup step someone owns, or a person keeps pasting the details in",
                        "hint": "Say what a client would have to do about it.",
                        "example": "Example: Either the office manager connects the calendar once, or someone pastes the dates in each week.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your first-hand notes",
            "body": (
                "Write your notes as a text or Markdown file with the four sections below, about the "
                "real job you gave Hermes.\n"
                "1. Save it.\n"
                "2. Type where you saved it.\n"
                "3. Click Check my work."
            ),
            "verify": "artifact",
            "check": "first-hand notes",
            "sections": [
                {
                    "heading": "The job", "min_words": 14, "needs": ["time"],
                    "what": "the real job from your own work, and how long it takes by hand",
                    "fix": "Say how long the job takes you by hand, or how often it comes up.",
                    "hint": "Name one small job you actually do, what you gave Hermes to work from, and how long it takes you by hand.",
                    "example": "Example: Every Friday I write reminder texts for next week's 22 dental appointments, about 30 minutes by hand. I pasted the list into Hermes and asked for one text each.",
                },
                {
                    "heading": "What Hermes did", "min_words": 20, "needs": ["list"],
                    "what": "the steps Hermes actually took, one per line",
                    "fix": "List the steps, one per line starting with a dash, in the order Hermes took them.",
                    "hint": "Write what you watched, in order. Include anything Hermes said it could not reach or do.",
                    "example": "Example:\n- Read the 22 appointments I pasted in.\n- Wrote one reminder text for each, with the time and the dentist's name.\n- Said it could not send texts, because no texting tool was connected.",
                },
                {
                    "heading": "What went wrong", "min_words": 14, "needs": [],
                    "what": "one thing Hermes got wrong or needed help with, and how you caught it",
                    "hint": "Name one real mistake or one place you stepped in. If nothing went wrong, say what you checked to be sure.",
                    "example": "Example: Hermes wrote 9 am for a 9 pm appointment. I caught it because I compared each text with the schedule before sending.",
                },
                {
                    "heading": "What I would tell a client", "min_words": 16, "needs": [],
                    "what": "what you would honestly say to a client, limits included",
                    "hint": "Write the sentences you would say out loud: what it saved you, and what a person still has to check.",
                    "example": "Example: It cut 30 minutes of reminders to about 10. A person still reads every text before it goes out, because it can mix up morning and evening.",
                },
            ],
            "proof": (
                "Your first-hand notes on one real job you gave Hermes, saved on your computer, with all 4 sections "
                "written. Its fingerprint goes on your Field Record."
            ),
        },
        "revisions": [
            {
                "version": 1,
                "kind": "added",
                "released": "0.8.0",
                "date": "2026-10-05",
                "summary": (
                    "New in 0.8.0: before you explain Hermes to anyone, you give it one small real job from your own "
                    "work and write first-hand notes on what it did and what it got wrong."
                ),
            }
        ],
    },
    "ambassador.story": {
        "minutes": {"lesson": 3, "example": 4, "complete": 6, "lab": 8, "explain": 5, "gate": 10},
        "use": (
            "You said you want Hermes to do this for you: {goal}. Someone who shares that goal will believe "
            "your explanation when you state the limits first, so this mission has you write it down."
        ),
        "use_plain": (
            "Whoever you explain Hermes to hears four things in two minutes: what it does, where it runs, "
            "what it takes and what it won't do. This mission builds that explanation."
        ),
        "lab": {
            "body": (
                "1. Run the skeptic exercise in Hermes.\n"
                "2. Write your explanation as a file with the five sections the check asks for.\n"
                "3. Open it with the sentence that landed."
            ),
            "prompt": (
                "Act as a skeptical operations director who has heard four AI pitches this month. Ask me what "
                "Hermes is, where it runs, what it takes to look after, and what it won't do. Interrupt me if I "
                "use a word a business person wouldn't use, or claim something I can't show. After two minutes, "
                "tell me the one sentence that landed. Then help me turn what I said into five short sections: "
                "What it is, Where it runs, What it takes, What it will not do, and Credit. In Credit, make me "
                "name Nous Research and one community teacher."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "Say the limits first",
            "lines": [
                "Cover four things: what Hermes does, where it runs, what it takes, and what it won't do.",
                "The limit earns the meeting, because most vendors skip it.",
                "Credit Nous Research and the community teachers, and say that someone has to own every setup.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "What happened when Gloria explained it to Dale",
            "intro": (
                "Gloria Santos sells maintenance software. Dale Pruitt, who owns a fleet repair shop, told her AI "
                "vendors all promise the moon. She had two minutes at his counter."
            ),
            "parts": [
                {
                    "label": "She opened with a job he hated",
                    "text": "Chasing invoices 30 days late. Dale could picture it, so he kept listening.",
                },
                {
                    "label": "She named where it runs",
                    "text": "The desktop behind his counter. Hermes is open source, so he runs it himself and owns the setup.",
                },
                {
                    "label": "She gave him numbers",
                    "text": "One person for about 2 hours a week, plus about $50 a month for the AI service.",
                },
                {
                    "label": "She said the limit out loud",
                    "text": "Hermes can get a step wrong, so a person approves anything that reaches a customer. Dale sat up. No vendor had told him that.",
                },
                {
                    "label": "She gave credit",
                    "text": "She named Nous Research, who maintain Hermes, and promised to send Tonbi's masterclass.",
                },
            ],
            "document": (
                "# Explaining Hermes to Dale Pruitt\n\n"
                "## What it is\n"
                "Hermes is an open source AI agent. You describe a job in plain words, such as chasing invoices that "
                "are 30 days late, and it works through the steps using the tools and accounts you allow.\n\n"
                "## Where it runs\n"
                "On a computer you choose, such as the desktop behind your service counter. You own that computer "
                "and the setup, because Hermes is software you run yourself.\n\n"
                "## What it takes\n"
                "One person owns it. Plan on about 2 hours a week for that person to read what Hermes did and fix "
                "what went wrong, plus a monthly bill for the AI service behind it. Expect to start near $50 a month.\n\n"
                "## What it will not do\n"
                "Hermes can get a step wrong, so a person approves anything that reaches a customer. It also cannot "
                "repair a messy process. If your invoices live in three places, someone tidies that first.\n\n"
                "## Credit\n"
                "Nous Research maintains Hermes. Tonbi's Hermes Agent Masterclass is the clearest walkthrough of the "
                "app I have found, and I will send you the link.\n"
            ),
        },
        "complete": {
            "title": "Your turn: finish the explanation for Nadia",
            "intro": (
                "Nadia Petrov owns a tutoring center and has heard the pitch before. Fill in the three blanks in your "
                "own words, then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "# Explaining Hermes to Nadia Petrov\n\n"
                        "## What it is\n"
                        "Hermes is an open source AI agent that takes a job described in plain words, such as sending "
                        "lesson reminders to parents, and works through the steps with the tools you allow.\n\n"
                        "## Where it runs\n"
                        "On a computer you pick, like the laptop at the front desk of the center, or a rented server. "
                        "You run it yourself, so the setup is yours.\n\n"
                        "## What it takes\n"
                    )
                },
                {
                    "gap": "takes",
                    "prompt": "Who owns it, and what do they spend? Give hours and money.",
                    "answer": "A person who owns it and spends about 3 hours a week checking what it sent, plus a monthly bill for the AI service that you should price before you say yes.",
                    "min_words": 12,
                    "needs": ["number"],
                },
                {"text": "\n\n## What it will not do\n"},
                {
                    "gap": "limit",
                    "prompt": "Name one real limit and the reason, in plain words.",
                    "answer": "Hermes can write a wrong reminder, so Nadia or her office manager approves anything that goes to parents. It also cannot fix a messy parent list, so someone cleans the list first.",
                    "min_words": 14,
                },
                {"text": "\n\n## Credit\n"},
                {
                    "gap": "credit",
                    "prompt": "Credit the maintainers and one community teacher by name.",
                    "answer": "Nous Research maintains Hermes. For a walk through the app, Nadia can watch Tonbi's Desktop App Masterclass on YouTube.",
                    "min_words": 10,
                    "needs": ["name"],
                },
                {"text": "\n"},
            ],
        },
        "coach": [
            {
                "hint": "Say who owns the setup once Hermes is installed. A listener should know whose job it is to keep it running.",
                "example": "Example: Hermes is open source software. Nous Research maintains it, and the florist who installs it owns the setup and keeps it running.",
            },
            {
                "hint": "Name an actual place: a computer in the office, a rented server, or Hermes Cloud. A bare 'the cloud' leaves a business owner guessing.",
                "example": "Example: It runs on the office desktop behind the vet clinic's front desk, and the clinic owns that computer.",
            },
            {
                "hint": "Give the owner a job title and two numbers: hours a week to check the work, and dollars a month to run it.",
                "example": "Example: The clinic manager spends about 1 hour a week reading what Hermes did, and the AI service costs around $40 a month.",
            },
            {
                "hint": "Pick one thing Hermes can't do for this buyer and say it in a single sentence, with the reason.",
                "example": "Example: Hermes can get a step wrong, so the clinic manager approves every message before it goes to a pet owner.",
            },
            {
                "hint": "Think about why a skeptic keeps listening after a limit. What did you give them that a brochure leaves out?",
                "example": "Example: After the vet clinic owner hears what Hermes can't do, she asks which job to start with, because you told her the limits first.",
            },
            {
                "hint": "Name the group that maintains Hermes and one person whose teaching you would send a buyer to.",
                "example": "Example: Nous Research maintains Hermes, and Tony Simons' written manual explains how it works step by step.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "A restaurant owner interrupts your explanation: \"So who do I call when it breaks?\" "
                    "Say what you tell her, in plain words."
                ),
                "points": [
                    {
                        "point": "that Hermes is open source software, so someone in her business owns the setup",
                        "hint": "Say who looks after Hermes once it is running.",
                        "example": "Example: Hermes is software you run yourself, so your kitchen manager owns it and keeps it running.",
                    },
                    {
                        "point": "that Nous Research maintains Hermes and community teachers publish guides and videos she can use",
                        "hint": "Name where help comes from when the owner is stuck.",
                        "example": "Example: Nous Research keeps the docs, and Tonbi's masterclass walks through the app on video.",
                    },
                    {
                        "point": "that upkeep is a cost to price in before she says yes",
                        "hint": "Say what looking after it costs her in time and money.",
                        "example": "Example: Plan on about 2 hours a week from the kitchen manager and a monthly bill for the AI service.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "A colleague tells a client that Hermes is \"a robot employee that does everything.\" "
                    "Name two things you would correct, and what you would say instead."
                ),
                "points": [
                    {
                        "point": "that Hermes does named jobs with the tools and accounts you give it",
                        "hint": "Replace 'everything' with one job and the access it needs.",
                        "example": "Example: Hermes drafts the weekly order email from the shared spreadsheet you allow it to read.",
                    },
                    {
                        "point": "that someone has to own it and spend time on it every week",
                        "hint": "Name the person and the hours.",
                        "example": "Example: the shop manager reads each draft and fixes mistakes, about 1 hour a week.",
                    },
                    {
                        "point": "a plain limit, because a promise of everything loses the technical buyer",
                        "hint": "Say one thing Hermes can't do, with the reason.",
                        "example": "Example: Hermes can get a step wrong, so a person approves anything sent to a customer.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "A client says, \"I saw a video about Hermes. Is that your product?\" "
                    "Say what you answer, and who you credit."
                ),
                "points": [
                    {
                        "point": "that Hermes is open source and Nous Research maintains it",
                        "hint": "Say whose software it is.",
                        "example": "Example: Hermes is open source under the MIT license, and Nous Research builds and maintains it.",
                    },
                    {
                        "point": "a credit by name to the teacher whose work the client watched or the one you rely on",
                        "hint": "Name a person and where their teaching lives.",
                        "example": "Example: Tonbi's Hermes Agent Masterclass on Hermes Atlas is the video you likely saw.",
                    },
                    {
                        "point": "what you offer: help finding the right opportunity and a clean handoff to the person who builds it",
                        "hint": "Say your own part in one sentence.",
                        "example": "Example: I help you decide whether a task is worth automating and introduce you to someone who builds it.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your two-minute explanation",
            "body": (
                "Write your explanation as a text or Markdown file with the five sections below, about "
                "a real listener and in your own words.\n"
                "1. Save it.\n"
                "2. Type where you saved it.\n"
                "3. Click Check my work."
            ),
            "verify": "artifact",
            "check": "two-minute explanation",
            "sections": [
                {
                    "heading": "What it is", "min_words": 14, "needs": [],
                    "what": "what Hermes does, in one plain sentence about a real task",
                    "hint": "Say what Hermes does for one task your listener has. Use words a customer would use.",
                    "example": "Example: Hermes is an open source AI agent. You describe a job in plain words, such as writing the weekly order sheet for a florist, and it works through the steps with the accounts you allow.",
                },
                {
                    "heading": "Where it runs", "min_words": 10, "needs": [],
                    "what": "the real place it runs and who owns it",
                    "hint": "Name a real place: the office computer, a rented server, or Hermes Cloud. Say who owns it.",
                    "example": "Example: It runs on a computer the florist chooses, such as the one in the back office. She owns the setup.",
                },
                {
                    "heading": "What it takes", "min_words": 12, "needs": ["number"],
                    "what": "who looks after it, with hours or money",
                    "fix": "Put a number on it: hours a week to look after it, or dollars a month to run it.",
                    "hint": "Name the owner by role, then give hours a week and the monthly cost. Honest numbers earn trust.",
                    "example": "Example: The shop manager spends about 1 hour a week checking results, and the AI service costs around $30 a month.",
                },
                {
                    "heading": "What it will not do", "min_words": 14, "needs": [],
                    "what": "one real limit, with the reason",
                    "hint": "Pick one real limit and give the reason in the same sentence.",
                    "example": "Example: Hermes can misread a handwritten order, so the manager reads every order sheet before it goes to the wholesaler.",
                },
                {
                    "heading": "Credit", "min_words": 10, "needs": ["name"],
                    "what": "Nous Research and one community teacher, by name",
                    "fix": "Name Nous Research and at least one person whose teaching you would send a buyer to.",
                    "hint": "Name who maintains Hermes and one community teacher, with where to find their work.",
                    "example": "Example: Nous Research maintains Hermes. Tony Simons wrote a twelve part manual, and Kevin Simback's guides on Hermes Atlas explain where Hermes lives.",
                },
            ],
            "proof": (
                "Your two-minute explanation, saved on your computer, with all 5 sections written for a real "
                "listener and Nous Research credited by name. Its fingerprint goes on your Field Record."
            ),
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now reads inside each section: a number in What it takes and a named person in "
                    "Credit, with real sentences everywhere. It used to look for the five headings and a file "
                    "over 240 characters."
                ),
            }
        ],
    },
    "ambassador.qualify": {
        "minutes": {"lesson": 3, "example": 4, "complete": 7, "lab": 10, "explain": 5, "gate": 10},
        "use": (
            "You said you want Hermes to do this for you: {goal}. Plenty of people will say they want that too, "
            "so this mission gives you four signs that separate a real opportunity from polite interest."
        ),
        "use_plain": (
            "Many people say they are curious about AI and few have a job to give it. This mission gives you four "
            "signs that tell the two apart, and a note that records your decision."
        ),
        "lab": {
            "body": (
                "1. Run the roleplay in Hermes, or use a real prospect you know.\n"
                "2. Write your notes as a file with the seven sections the check asks for.\n"
                "3. Give the moment the answer became clear as your reason."
            ),
            "prompt": (
                "Play a business owner who is excited about AI and has no clear problem. Sound promising. Let me run "
                "the conversation, and don't make it easy: stay vague about how often the work happens, who owns it, "
                "and the budget until I ask directly. Once I ask directly, answer with specific names, numbers and a "
                "budget, and invent a business name. At the end, tell me whether this is a yes, a later or a no, and "
                "quote the moment the answer became clear. Then help me write notes with these headings: Prospect, "
                "Workflow, Owner, Systems, Authority, Decision, Next step. My Decision starts with yes, later or no."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "Four signs of a real opportunity",
            "lines": [
                "Look for a task that repeats and a person who feels the pain of it.",
                "Then find who can approve spending, and a first step small enough to sell.",
                "If one is missing, keep talking, hold off on a quote, and write your decision down with reasons.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "What happened when Caroline asked about Hermes",
            "intro": (
                "Caroline Whitfield owns a nine-person pest control company in Lubbock. At a chamber lunch she "
                "asked Joel Banks, a consultant, what Hermes could do. Joel asked four questions first."
            ),
            "parts": [
                {
                    "label": "He found a task that repeats",
                    "text": "The office writes about 40 renewal letters a month, around 3 hours of work. Joel could count it, so he could price it.",
                },
                {
                    "label": "He found who feels it",
                    "text": "Brenda Kowalski, the office manager, writes the letters and feels every delay.",
                },
                {
                    "label": "He found who signs",
                    "text": "Caroline said she can approve up to $3,000 on her own.",
                },
                {
                    "label": "He wrote yes, with reasons",
                    "text": "The renewal letters made a first step small enough to price. With all four signs there, he wrote yes and his reasons for the builder.",
                },
            ],
            "document": (
                "# Opportunity notes: Whitfield Pest Control\n\n"
                "## Prospect\n"
                "Caroline Whitfield owns Whitfield Pest Control, a nine-person company in Lubbock that treats homes "
                "and small offices. She met me at a chamber lunch and asked what Hermes could do for her.\n\n"
                "## Workflow\n"
                "Every month the office writes about 40 renewal letters for annual service contracts, copying "
                "details from the customer list. It takes about 3 hours and slips whenever a technician calls in sick.\n\n"
                "## Owner\n"
                "Brenda Kowalski, the office manager, writes the letters now and feels the delay every month. She "
                "would read each letter before it goes out.\n\n"
                "## Systems\n"
                "The customer list in a shared spreadsheet, the company Gmail account, and a folder of signed "
                "contracts on the office computer.\n\n"
                "## Authority\n"
                "Caroline Whitfield signs every purchase and told me she can approve up to $3,000 without asking anyone.\n\n"
                "## Decision\n"
                "Yes. The task repeats, Brenda feels it, Caroline signs, and the 40 renewal letters alone make a first "
                "step small enough to price. I hold the quote until the builder has seen the customer list.\n\n"
                "## Next step\n"
                "A call of 30 minutes with Caroline, Brenda and the builder, Marcus Hill, on Thursday at 2 pm. I send my "
                "handoff note to Marcus by Wednesday.\n"
            ),
        },
        "complete": {
            "title": "Your turn: finish the notes on Tomas's shop",
            "intro": (
                "Tomas Ferreira owns Ridgeline Auto Glass, and the answer here is later. Fill in the three blanks, "
                "then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "# Opportunity notes: Ridgeline Auto Glass\n\n"
                        "## Prospect\n"
                        "Tomas Ferreira owns Ridgeline Auto Glass, a shop with six technicians in Amarillo. He was "
                        "keen on AI after a talk at the Rotary Club.\n\n"
                        "## Workflow\n"
                        "Every afternoon the office re-keys insurance claim details into each insurer's web portal, "
                        "about 90 minutes of work that crowds out phone calls.\n\n"
                        "## Owner\n"
                        "Lucia Ramos, the office manager, does the re-keying and wants it gone.\n\n"
                        "## Systems\n"
                        "Each insurer's claims portal, the shop's scheduling software, and a shared inbox.\n\n"
                        "## Authority\n"
                    )
                },
                {
                    "gap": "authority",
                    "prompt": "Who approves spending, and how much can they approve alone? Name them.",
                    "answer": "Tomas Ferreira signs every purchase over $500 and said he would pay for anything that gives Lucia back an hour a day.",
                    "min_words": 12,
                    "needs": ["name"],
                },
                {"text": "\n\n## Decision\n"},
                {
                    "gap": "decision",
                    "prompt": "Start with yes, later or no. Give your reasons.",
                    "answer": "Later. The task and the people are real, but Tomas wants one assistant for the whole shop, so no first step is small enough to sell. I hold the quote until he picks the claims paperwork alone.",
                    "min_words": 16,
                    "needs": ["decision"],
                },
                {"text": "\n\n## Next step\n"},
                {
                    "gap": "next",
                    "prompt": "Say what happens next and when.",
                    "answer": "I call Tomas in 2 weeks for 15 minutes and ask whether he has picked one job to start with.",
                    "min_words": 10,
                    "needs": ["time"],
                },
                {"text": "\n"},
            ],
        },
        "coach": [
            {
                "hint": "Ask how often the work happens and how long it takes each time. A task that comes back every week can be counted.",
                "example": "Example: A landscaper's office writes 25 estimates a week, about 15 minutes each.",
            },
            {
                "hint": "Ask who does the task today and what they would give to stop. The person who likes the idea may never have done the work.",
                "example": "Example: Lisa Park, the dispatcher who re-types 40 work orders each night, owns the pain. The owner who read an article about AI owns the enthusiasm.",
            },
            {
                "hint": "Ask who signs. A person can be keen and still need someone else's yes.",
                "example": "Example: The practice manager loves the idea, and Dr. Elena Voss approves anything over $500.",
            },
            {
                "hint": "Shrink the job until you could price it in one sentence and finish it in a few weeks.",
                "example": "Example: One first job, sorting the shared inbox into three folders each morning, for $1,500 over 3 weeks.",
            },
            {
                "hint": "Say what you do instead of quoting: ask the next question and name the missing sign out loud.",
                "example": "Example: \"I can't price this yet. Who signs for spending, and which task do you want first?\"",
            },
            {
                "hint": "Say where the decision goes and what it holds, so the builder can read it cold months later.",
                "example": "Example: A note that says Later, with three reasons and the date to call back, saved where the builder can open it.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "A gym owner says, \"Everything we do is manual. Can AI handle it?\" "
                    "Name the four signs you look for, and say how you find each one."
                ),
                "points": [
                    {
                        "point": "a task that repeats, found by asking how often and how long",
                        "hint": "Ask for one task and its count.",
                        "example": "Example: Every Monday the front desk emails 60 members about class changes, about 2 hours.",
                    },
                    {
                        "point": "a person who feels the pain, found by asking who does the work today",
                        "hint": "Ask who would celebrate if it vanished.",
                        "example": "Example: The front desk lead, Tasha Greene, who writes every email by hand.",
                    },
                    {
                        "point": "someone who can approve spending, found by asking who signs",
                        "hint": "Ask who says yes to a bill.",
                        "example": "Example: The owner signs anything over $300.",
                    },
                    {
                        "point": "a first step small enough to sell, found by shrinking the job to one task",
                        "hint": "Ask which single task to start with.",
                        "example": "Example: Only the Monday class-change emails, nothing else yet.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "A prospect has a weekly task and a keen owner, but cannot say who approves spending, and the "
                    "budget meeting is a month away. Say your decision and what you write down."
                ),
                "points": [
                    {
                        "point": "a decision of later, because nobody who can say yes has joined the conversation",
                        "hint": "Count the signs that are present and the one that is missing.",
                        "example": "Example: Later. Three signs are present and the person who signs is missing.",
                    },
                    {
                        "point": "the reasons and the missing sign written beside the decision",
                        "hint": "Write what a builder would need to read cold.",
                        "example": "Example: The note says the weekly task and the owner are real, and the signer is unknown until the budget meeting.",
                    },
                    {
                        "point": "a next step that asks to meet the person who signs",
                        "hint": "Name the person you want to meet and when.",
                        "example": "Example: I ask the owner to introduce me to the board treasurer before the meeting.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "After 20 minutes a prospect says, \"Just send me a price.\" You still don't know who owns the "
                    "task or who approves spending. Say what you do."
                ),
                "points": [
                    {
                        "point": "hold off the quote, and say why a price without those answers is a guess",
                        "hint": "Say what a quote needs before it is honest.",
                        "example": "Example: \"I can give you a real price once I know the task and who signs.\"",
                    },
                    {
                        "point": "ask directly for the missing pieces: who does the task today, who signs",
                        "hint": "Ask two direct questions.",
                        "example": "Example: \"Who does this work now, and who approves the bill?\"",
                    },
                    {
                        "point": "write the decision as later, with the reasons, so the next conversation starts from facts",
                        "hint": "Say what goes into the note.",
                        "example": "Example: Later, because the owner and the signer are unknown, with a call set for next Tuesday.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your opportunity notes",
            "body": (
                "Write your notes on a real or practice prospect as a text or Markdown file with the "
                "seven sections below.\n"
                "1. Save it.\n"
                "2. Type where you saved it.\n"
                "3. Click Check my work."
            ),
            "verify": "artifact",
            "check": "opportunity notes",
            "sections": [
                {
                    "heading": "Prospect", "min_words": 10, "needs": ["name"],
                    "what": "who the prospect is and what the business does",
                    "fix": "Name the person and the business.",
                    "hint": "Name the person, the business, and what it does in one sentence.",
                    "example": "Example: Imelda Cruz owns Cruz Family Dental, a four-chair practice in Norman.",
                },
                {
                    "heading": "Workflow", "min_words": 12, "needs": ["time"],
                    "what": "the task that repeats, and how often or how long",
                    "fix": "Say how often the task happens or how long it takes.",
                    "hint": "Describe one task, how often it happens, and how long it takes now.",
                    "example": "Example: Every Friday the office calls 30 patients to confirm Monday visits, about 2 hours.",
                },
                {
                    "heading": "Owner", "min_words": 10, "needs": ["name"],
                    "what": "who feels the pain of the task, by name",
                    "fix": "Name the person who does the task today.",
                    "hint": "Name the person who does the task now and say what they would do with the result.",
                    "example": "Example: Tyrone Banks, the front desk lead, makes the calls and would review every list.",
                },
                {
                    "heading": "Systems", "min_words": 6, "needs": [],
                    "what": "where the work happens today",
                    "hint": "List where the work starts and where it ends up: calendar, spreadsheet, email, portal.",
                    "example": "Example: The appointment calendar, a patient phone list, and the office text message account.",
                },
                {
                    "heading": "Authority", "min_words": 10, "needs": ["name"],
                    "what": "who approves spending, by name, and how much",
                    "fix": "Name the person who signs.",
                    "hint": "Name the person who can say yes to a bill and say how much they can approve alone.",
                    "example": "Example: Imelda Cruz signs every purchase and said she can approve $2,000 herself.",
                },
                {
                    "heading": "Decision", "min_words": 14, "needs": ["decision"],
                    "what": "yes, later or no, with your reasons",
                    "fix": "Start the section with the word yes, later or no.",
                    "hint": "Start with yes, later or no, then say which of the four signs were present and which were missing.",
                    "example": "Example: Later. The task repeats and Tyrone feels it, but nobody has said who signs.",
                },
                {
                    "heading": "Next step", "min_words": 10, "needs": ["time"],
                    "what": "what happens next, and when",
                    "fix": "Say when it happens, for example in 2 weeks or at 3 pm.",
                    "hint": "Write the next action, who takes it, and when, such as a call in 2 weeks.",
                    "example": "Example: I call Imelda in 10 days to ask whether she has picked one job to start with.",
                },
            ],
            "proof": (
                "Your opportunity notes, saved on your computer, with all 7 sections filled in, a named owner and "
                "signer, and a decision with reasons. Its fingerprint goes on your Field Record."
            ),
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now reads inside each section: named people for the prospect, owner and signer, a "
                    "time in Workflow and Next step, and a Decision that starts with yes, later or no. It used to "
                    "look for the headings and a file over 240 characters."
                ),
            }
        ],
    },
    "ambassador.handoff": {
        "minutes": {"lesson": 3, "example": 4, "complete": 7, "lab": 10, "explain": 5, "gate": 10},
        "use": (
            "You said you want Hermes to do this for you: {goal}. If someone builds it for you, the note that "
            "reaches the builder has to say what is known and what was promised, and this mission has you write one."
        ),
        "use_plain": (
            "When you introduce a client to the person who will build the work, a short note keeps what you know "
            "apart from what you said. This mission has you write that note."
        ),
        "lab": {
            "body": (
                "1. Run the joint call in Hermes.\n"
                "2. Write the handoff note as a file with the five sections the check asks for.\n"
                "3. Keep Known and Promised as two separate lists."
            ),
            "prompt": (
                "Practice a handoff call with me. You play both the client and the builder who takes over. Invent "
                "names, a business and a task that repeats. Make me say what we know, what we promised, what still "
                "needs checking, and who owns each next step, in front of both of you. Correct me if I retell the "
                "client's story wrong or answer a question that belongs to the builder. Then help me write the "
                "note with these headings: Known, Promised, Validate, Owner, Next step. Known and Promised are "
                "separate bulleted lists, and Owner names the builder."
            ),
        },
        "story_first": True,
        "takeaway": {
            "title": "Keep what you know apart from what you promised",
            "lines": [
                "A handoff note says what we know, what we promised, what needs checking, and who owns each step.",
                "Keep the promises apart from the facts, or a casual remark becomes a requirement.",
                "Write the note while you remember who said what, and send it before the joint call.",
            ],
            "picture": "",
        },
        "worked": {
            "title": "What Naomi wrote before the joint call",
            "intro": (
                "Naomi Fischer introduced Rafael Delgado, who owns a plumbing company, to a builder, Priya Shah. "
                "The day before their call, while she still remembered who said what, she wrote a handoff note."
            ),
            "parts": [
                {
                    "label": "She listed what she knew",
                    "text": "Rafael has 14 employees. His dispatcher, Carla Mendez, spends about 70 minutes every evening texting technicians their jobs.",
                },
                {
                    "label": "She wrote down her own promise",
                    "text": "She had said, \"We can probably automate the evening texts.\" Rafael heard a yes, so the sentence went under Promised, apart from the facts.",
                },
                {
                    "label": "She listed what Priya had to check",
                    "text": "Three questions only Priya could answer, starting with whether the dispatch software lets Hermes read tomorrow's jobs.",
                },
                {
                    "label": "She gave each step an owner",
                    "text": "Priya owned the price, Naomi owned the note, and the note reached both of them by Tuesday at noon.",
                },
            ],
            "document": (
                "# Handoff note: Delgado Plumbing\n\n"
                "## Known\n"
                "- Rafael Delgado owns Delgado Plumbing, a company with 14 employees in Tucson.\n"
                "- Every evening his dispatcher, Carla Mendez, texts each technician the next day's jobs by hand, about 70 minutes of work.\n"
                "- Carla would read every text before it goes out.\n"
                "- The schedule lives in the dispatch software and a shared spreadsheet.\n\n"
                "## Promised\n"
                "- I said, \"We can probably automate the evening texts.\" Rafael heard that as a yes.\n"
                "- I told Rafael that Priya Shah, the builder, would call him this week.\n"
                "- I gave no price and no date.\n\n"
                "## Validate\n"
                "Whether the dispatch software lets Hermes read tomorrow's jobs, whether the texts can go out from "
                "Carla's number, and how many jobs a technician gets on the busiest day. Priya checks these before "
                "she quotes anything.\n\n"
                "## Owner\n"
                "Priya Shah owns what is possible and the price. Carla Mendez owns the evening texts today. I own "
                "this note and the introduction until the call ends.\n\n"
                "## Next step\n"
                "I send this note to Priya and Rafael by Tuesday at noon. The joint call is Wednesday at 10 am and "
                "runs 30 minutes. Priya opens it by restating what we know before she answers anything.\n"
            ),
        },
        "complete": {
            "title": "Your turn: finish Dennis's note",
            "intro": (
                "Dennis Whitlock is introducing Beatriz Okafor, who runs a tax practice, to a builder. Fill in "
                "the three gaps in his note, then compare with our answers."
            ),
            "parts": [
                {
                    "text": (
                        "# Handoff note: Okafor Tax Service\n\n"
                        "## Known\n"
                        "- Beatriz Okafor runs a six-person tax practice in Tulsa.\n"
                        "- Every January the office emails 300 clients a document checklist, about 8 hours of work.\n"
                        "- Office manager Joy Kimura builds the lists by hand.\n\n"
                        "## Promised\n"
                    )
                },
                {
                    "gap": "promised",
                    "prompt": "List two things you said that sound like commitments. Use bullet lines and quote your words.",
                    "answer": "- I said, \"We can probably have the checklist emails ready by January 15.\"\n- I told Beatriz that Sam Lindqvist, the builder, would call her this week.",
                    "min_words": 20,
                    "needs": ["list"],
                },
                {
                    "text": (
                        "\n\n## Validate\n"
                        "Whether the client list exports from the tax software, whether the emails can go from the "
                        "office address, and how many clients change from year to year.\n\n"
                        "## Owner\n"
                    )
                },
                {
                    "gap": "owner",
                    "prompt": "Who owns what? Name the builder, the person who does the task now, and you.",
                    "answer": "Sam Lindqvist, the builder, owns what is possible and the price. Joy Kimura owns the checklist today, and I own this note.",
                    "min_words": 14,
                    "needs": ["name"],
                },
                {"text": "\n\n## Next step\n"},
                {
                    "gap": "next",
                    "prompt": "Say when the note goes out and when the call happens.",
                    "answer": "I send this note to Sam and Beatriz by Monday at noon, and the joint call runs 30 minutes on Tuesday.",
                    "min_words": 12,
                    "needs": ["time"],
                },
                {"text": "\n"},
            ],
        },
        "coach": [
            {
                "hint": "Think of the four questions a builder asks: what is true, what was said, what is unchecked, and who moves next.",
                "example": "Example: A gutter cleaning company: what we know (route sizes), what we promised (a price by Friday), what needs checking (whether the app reads the route list), who owns each next step.",
            },
            {
                "hint": "Ask whether the sentence describes a fact about the client or something you said you could do.",
                "example": "Example: \"We can probably automate that\" records what you said, so it goes under Promised in your exact words.",
            },
            {
                "hint": "Picture the client quoting your sentence in week three, and the builder reading a note that never mentioned it.",
                "example": "Example: The client says, \"You told us it was automated,\" and the builder has to deliver something nobody scoped.",
            },
            {
                "hint": "Ask when your memory of who said what is sharpest, and who needs the note before the two of them sit down together.",
                "example": "Example: Send it the day before the joint call, while you still recall that the client suggested the Friday deadline.",
            },
        ],
        "review": [
            {
                "id": "r1",
                "question": (
                    "On the call you guessed, \"It will cost about $2,000.\" You have no quote from the builder. "
                    "Which section holds the price, and how do you word it?"
                ),
                "points": [
                    {
                        "point": "Promised, because you said it and the builder never agreed to it",
                        "hint": "Ask whose words the price is.",
                        "example": "Example: Promised, because the guess came from me and the builder has not seen the work.",
                    },
                    {
                        "point": "your exact words, labelled as your guess, with who heard it",
                        "hint": "Quote yourself and say it was a guess.",
                        "example": "Example: \"I said it would cost about $2,000. That was my guess.\"",
                    },
                    {
                        "point": "the builder owns the price and confirms or replaces it, which goes under Validate",
                        "hint": "Say who sets the real price.",
                        "example": "Example: Validate: the builder confirms the price after seeing the data.",
                    },
                ],
            },
            {
                "id": "r2",
                "question": (
                    "A client wants a weekly staff schedule built. Give two lines that belong under Known "
                    "and one that belongs under Validate."
                ),
                "points": [
                    {
                        "point": "a countable fact about the work, such as how many people and how often",
                        "hint": "Write something you could check by asking.",
                        "example": "Example: 12 staff, and the owner builds the schedule every Thursday.",
                    },
                    {
                        "point": "a named person and what they do, such as who builds the schedule today",
                        "hint": "Name the person doing the work.",
                        "example": "Example: Ines Ortega, the shift lead, builds it in a spreadsheet.",
                    },
                    {
                        "point": "a question only the builder can answer, such as whether the scheduling app allows access",
                        "hint": "Write a question about what is possible.",
                        "example": "Example: Whether the scheduling app lets Hermes read availability.",
                    },
                ],
            },
            {
                "id": "r3",
                "question": (
                    "You finish the note a day after the joint call because the week got busy. "
                    "What changes for the builder and the client?"
                ),
                "points": [
                    {
                        "point": "the builder joined the call without the facts and promises set apart, so a casual remark can harden into a requirement",
                        "hint": "Think about what the builder knew in the room.",
                        "example": "Example: The builder hears \"we can automate that\" and treats it as agreed scope.",
                    },
                    {
                        "point": "your memory of who said what has already faded",
                        "hint": "Think about how much you recall a day later.",
                        "example": "Example: A day later you no longer recall whether the client or you suggested the Friday deadline.",
                    },
                    {
                        "point": "the fix: send the note before the call next time, and if late, say so and correct it",
                        "hint": "Say what you do now and next time.",
                        "example": "Example: Send a corrected note today and put the next one on the calendar the day before the call.",
                    },
                ],
            },
        ],
        "gate": {
            "title": "Check your handoff note",
            "body": (
                "Write your handoff note on a real or practice opportunity as a text or Markdown file "
                "with the five sections below, keeping Known and Promised as two separate lists.\n"
                "1. Save it.\n"
                "2. Type where you saved it.\n"
                "3. Click Check my work."
            ),
            "verify": "artifact",
            "check": "handoff note",
            "sections": [
                {
                    "heading": "Known", "min_words": 14, "needs": ["list"],
                    "what": "facts you can check, one per line",
                    "fix": "List at least two facts, one per line, each starting with a dash.",
                    "hint": "Write facts you could check by asking: sizes, counts, names, who does the task now.",
                    "example": "Example:\n- Sunil Rao runs a four-bay tire shop in Edmond\n- Every Friday he orders stock by phone, about 90 minutes",
                },
                {
                    "heading": "Promised", "min_words": 10, "needs": ["list"],
                    "what": "what you said that sounds like a commitment, in your exact words",
                    "fix": "List at least two items, one per line, each starting with a dash.",
                    "hint": "Quote yourself. Include any price, date or call you offered, even a casual one.",
                    "example": "Example:\n- I said, \"We can probably have this by May\"\n- I told Sunil the builder would call him Monday",
                },
                {
                    "heading": "Validate", "min_words": 10, "needs": [],
                    "what": "what still needs checking before anyone commits",
                    "hint": "Write the questions only the builder can answer, such as access, limits and price.",
                    "example": "Example: Whether the supplier's ordering site lets Hermes sign in, and how many items an order holds.",
                },
                {
                    "heading": "Owner", "min_words": 10, "needs": ["name"],
                    "what": "who owns each next step, by name",
                    "fix": "Name a person for each step, not a team.",
                    "hint": "Name the builder, the person who does the task now, and yourself, with what each owns.",
                    "example": "Example: Leah Brandt, the builder, owns what is possible and the price. Sunil owns the ordering today.",
                },
                {
                    "heading": "Next step", "min_words": 10, "needs": ["time"],
                    "what": "when the note goes out and when the joint call happens",
                    "fix": "Say when, for example by 5 pm or in 2 days.",
                    "hint": "Say when the note goes out, when the joint call is, and how long it runs.",
                    "example": "Example: I send this to Leah and Sunil by Thursday at 5 pm. The call is Friday at 9 am for 30 minutes.",
                },
            ],
            "proof": (
                "Your handoff note, saved on your computer, with Known and Promised as separate lists, a named "
                "owner and a time for the next step. Its fingerprint goes on your Field Record."
            ),
        },
        "revisions": [
            {
                "version": 2,
                "kind": "check",
                "summary": (
                    "The check now needs Known and Promised as two separate lists, a named owner and a time for "
                    "the next step. It used to look for the five headings and a file over 240 characters."
                ),
            }
        ],
    },
}


CAPSTONE = {
    "id": "ambassador.capstone",
    "title": "Make one real introduction",
    "promise": (
        "Explain Hermes to one real person, pass their opportunity to a builder, then report against the "
        "criteria you wrote first."
    ),
    "outcome": "A report on one real introduction, measured against criteria you set before you started.",
    "level_meaning": "You made one real introduction and reported honestly against your own criteria.",
    "sources": ["official_desktop", "tony", "tonbi_desktop"],
    "watch": ["nous.learning_path", "d.1", "tony.12", "lab.6"],
    "lesson": {
        "title": "Set the criteria before the conversation",
        "body": (
            "Before you talk to anyone, write three numbered criteria for success, and put a number or a time "
            "in at least two of them. Then do the real thing: explain Hermes to one person you know, and pass one "
            "real opportunity to a builder. If no opportunity exists yet, practice the handoff with Hermes playing "
            "the builder. Afterward, give each criterion a line of evidence and a verdict: met, partly met or not met."
        ),
        "source": "tony",
    },
    "lab": {
        "title": "Make the introduction",
        "body": (
            "1. Pick one real person with a repeating task.\n"
            "2. Prepare in Hermes with the practice chat.\n"
            "3. Explain Hermes to them in two minutes.\n"
            "4. Pass the opportunity to a builder. No builder yet? Rehearse the handoff with Hermes as "
            "the builder."
        ),
        "prompt": (
            "I'm about to explain Hermes to a real person. I'll tell you who they are and the task I'd mention. "
            "Play that person and ask what they would ask. Then play a builder who receives my handoff note. "
            "Afterward, help me write what happened under these headings: Problem, Criteria, What I did, Evidence, "
            "What did not work, Next. Remind me to number the criteria and to put a number or time in two of them."
        ),
    },
    "explain": {
        "title": "Explain what carries over",
        "question": (
            "Your sister schedules volunteers for a church of 400 people and asks whether Hermes could do it. A "
            "board of five votes next month, no builder is in sight, and you won't be at the meeting. Say which "
            "ideas from this path carry over and what you change."
        ),
        "covers": [
            "that the limits-first explanation carries over: what Hermes does for scheduling, where it runs, what it takes, what it won't do, and credit to Nous Research",
            "that the four signs still decide it: a repeating task, an owner who feels it, someone who can approve spending, and a first step small enough to sell",
            "that a board holds the spending, so you find out who signs and what they need in writing",
            "that with no builder you write the note for the board and list what a builder must check, with no promise that it will work",
            "that you keep what you know apart from what you promised, because nobody else will catch the difference",
        ],
        "coach": [
            {
                "hint": "Run the four parts of your explanation against this listener. What does a volunteer coordinator need to hear first?",
                "example": "Example: For a farm co-op, say Hermes drafts the weekly pickup schedule, runs on the co-op's computer, needs a person for about 1 hour a week, and can misread a change. Credit Nous Research.",
            },
            {
                "hint": "Check each sign against the church. Which can you name, and which can you only guess?",
                "example": "Example: A youth sports league: weekly game schedule (repeats), the coordinator feels it, the treasurer signs, first step is one season's schedule.",
            },
            {
                "hint": "Ask who actually releases money in a group like this, and what they need to see before a vote.",
                "example": "Example: A club's treasurer needs a one-page summary with a price and a named owner before the board votes.",
            },
            {
                "hint": "With nobody to build it, your note has to work for readers who will not talk to you. What must it hold?",
                "example": "Example: A note that lists the known facts, the open questions a builder must check, and a call to find one.",
            },
            {
                "hint": "Think about who reads your note without you in the room. How do they tell your facts from your hopes?",
                "example": "Example: Known lists 40 volunteers and a weekly rota. Promised lists my sentence, \"I think Hermes could handle this.\"",
            },
        ],
    },
    "use": (
        "You said you want Hermes to do this for you: {goal}. Find one person who has a task like that, "
        "explain Hermes to them, and report what happens against criteria you set first."
    ),
    "use_plain": (
        "Pick one person you know with a repeating task, explain Hermes to them, and report what happens "
        "against criteria you set first."
    ),
    "minutes": {"lesson": 3, "example": 5, "complete": 8, "lab": 40, "explain": 6, "gate": 15},
    "story_first": True,
    "takeaway": {
        "title": "Set the criteria before the conversation",
        "lines": [
            "Before you talk to anyone, write three numbered criteria, with a number or a time in two.",
            "Then explain Hermes to one real person and pass one real opportunity to a builder.",
            "Afterward, give each criterion a line of evidence and a verdict: met, partly met or not met.",
        ],
        "picture": "",
    },
    "worked": {
        "title": "What happened when Marguerite explained Hermes to Kevin",
        "intro": (
            "Marguerite Ellison wanted to make one real introduction. Kevin Abara runs a print shop and retypes "
            "about 30 quotes a week. Before she spoke to him, she wrote her criteria."
        ),
        "parts": [
            {
                "label": "She wrote criteria she could fail",
                "text": "Two carried a number or a time: 15 minutes and 2 days. Written first, they couldn't bend to fit afterward.",
            },
            {
                "label": "She explained, then handed off",
                "text": "She spent 25 minutes with Kevin on Tuesday and sent her note to Anita Rao, the builder, two days later.",
            },
            {
                "label": "She gave each one a verdict",
                "text": "Kevin forgot the credit to Nous Research: partly met. Anita hadn't answered: not met. Both went in the report.",
            },
            {
                "label": "She said what went wrong",
                "text": "She ran short on the owner question and promised a call before asking Anita. Her next step had a date: Monday at 9 am.",
            },
        ],
        "document": (
            "# Introduction report: Marguerite Ellison\n\n"
            "## Problem\n"
            "I wanted to explain Hermes to Kevin Abara, who runs a six-person print shop, and pass his repeating "
            "quote task to a builder, Anita Rao. Kevin retypes about 30 customer quotes a week into an invoice spreadsheet.\n\n"
            "## Criteria\n"
            "1. Kevin can say back what Hermes does and one thing it will not do, after a 15 minute conversation.\n"
            "2. Kevin names the person who owns the quote task and the person who approves spending.\n"
            "3. My handoff note reaches Anita within 2 days of the conversation.\n"
            "4. Anita agrees a first step small enough to price.\n\n"
            "## What I did\n"
            "On Tuesday I spent 25 minutes with Kevin at the shop and explained Hermes with the five sections of "
            "my note. Two days later I sent Anita a handoff note with Known and Promised as separate lists and set a call for Friday.\n\n"
            "## Evidence\n"
            "1. Kevin said back that Hermes is open source, needs an owner and cannot fix messy quotes. He missed the credit to Nous Research. Partly met.\n"
            "2. Kevin named Siobhan Quinn, who types the quotes, and said he approves anything under $2,000. Met.\n"
            "3. I sent the note on Thursday, two days after we spoke. Met.\n"
            "4. Anita has not answered yet, so no first step is agreed. Not met.\n\n"
            "## What did not work\n"
            "I spent ten minutes on where Hermes runs because Kevin kept asking, and I ran short on the owner "
            "question. My note promised a call with Anita before I had asked her.\n\n"
            "## Next\n"
            "Anita and I speak on Monday at 9 am to agree one first step, and I ask Kevin to confirm who signs.\n"
        ),
    },
    "complete": {
        "title": "Your turn: finish Imani's report",
        "intro": (
            "Imani Brooks explained Hermes to her aunt, Odessa Greene, who runs a catering kitchen. Fill in the "
            "three gaps in her report, then compare with our answers."
        ),
        "parts": [
            {
                "text": (
                    "# Introduction report: Imani Brooks\n\n"
                    "## Problem\n"
                    "I explained Hermes to my aunt, Odessa Greene, who runs a catering kitchen in Wichita. Every "
                    "week she copies event orders from emails into a prep sheet, and I wanted to pass that task to a builder, Mateo Cruz.\n\n"
                    "## Criteria\n"
                ),
            },
            {
                "gap": "criteria",
                "prompt": "Write three numbered criteria you could fail. Put a number or a time in at least two.",
                "answer": "1. Odessa can say back what Hermes does and one limit after a 10 minute talk.\n2. Odessa names who approves spending before we finish.\n3. Mateo has my note within 3 days.",
                "min_words": 30,
                "needs": ["list", "number"],
            },
            {
                "text": (
                    "\n\n## What I did\n"
                    "On Sunday I talked with Odessa for 20 minutes at her kitchen table and used my five section "
                    "explanation. Then I wrote a handoff note and sent it to Mateo.\n\n"
                    "## Evidence\n"
                ),
            },
            {
                "gap": "evidence",
                "prompt": "One numbered line per criterion, each ending met, partly met or not met.",
                "answer": "1. She said back both, and missed the credit to Nous Research. Partly met.\n2. She named Rosa Delgado as the signer. Met.\n3. I sent the note on day 4. Not met.",
                "min_words": 30,
                "needs": ["list", "verdict"],
            },
            {
                "text": (
                    "\n\n## What did not work\n"
                    "I talked about prices before I asked who approves them. Odessa got interested in the wrong "
                    "thing, and I had to bring the conversation back.\n\n"
                    "## Next\n"
                ),
            },
            {
                "gap": "next",
                "prompt": "Say what you do next and when, with a time.",
                "answer": "Mateo and I speak on Tuesday at 10 am to agree one first step, and I ask Odessa to confirm Rosa signs.",
                "min_words": 12,
                "needs": ["time"],
            },
            {"text": "\n"},
        ],
    },
    "review": [
        {
            "id": "r1",
            "question": (
                "You wrote three criteria. Afterward one is met, one is partly met and one is not met. "
                "Say how you report it."
            ),
            "points": [
                {
                    "point": "a verdict on each criterion in plain words, including the one that is not met",
                    "hint": "Give each criterion its own line and its own word.",
                    "example": "Example: 1. Met. 2. Partly met. 3. Not met.",
                },
                {
                    "point": "one line of evidence for each verdict, from what actually happened",
                    "hint": "Say what you saw or heard.",
                    "example": "Example: She named the signer, so criterion 2 is met.",
                },
                {
                    "point": "what you would change, written in the Next section with a time",
                    "hint": "Name the fix and when you do it.",
                    "example": "Example: I send the note the day before the call, starting Monday.",
                },
            ],
        },
        {
            "id": "r2",
            "question": (
                "The person you explained Hermes to loved it, but has no task that repeats. "
                "What does your report say?"
            ),
            "points": [
                {
                    "point": "that the explanation criterion can be met while the opportunity criterion is not met",
                    "hint": "Score each criterion separately.",
                    "example": "Example: Explanation: met. Opportunity: not met, because no task repeats.",
                },
                {
                    "point": "the decision as later or no, with the missing signs named",
                    "hint": "Say which of the four signs are absent.",
                    "example": "Example: Later. No task, no named owner, and no one has said who signs.",
                },
                {
                    "point": "a next step that keeps the door open, with a time",
                    "hint": "Say when you follow up and what you ask.",
                    "example": "Example: I ask in 3 weeks whether a repeating task has appeared.",
                },
            ],
        },
        {
            "id": "r3",
            "question": (
                "You have no real opportunity to pass on yet. How do you still finish the second half of "
                "the mission?"
            ),
            "points": [
                {
                    "point": "practice the handoff with Hermes playing a client and a builder, and say in the report that it was practice",
                    "hint": "Say who plays whom and label it.",
                    "example": "Example: Practice handoff with Hermes as the client and builder.",
                },
                {
                    "point": "still write criteria before you start, so the practice can be judged",
                    "hint": "Decide what success means first.",
                    "example": "Example: My note reaches the practice builder within 1 day.",
                },
                {
                    "point": "report the practice honestly, including what did not work",
                    "hint": "Write one thing that went wrong.",
                    "example": "Example: I mixed my own promise into the Known list and fixed it afterward.",
                },
            ],
        },
    ],
    "gate": {
        "title": "Check your introduction report",
        "body": (
            "Write your report as a text or Markdown file with the six sections below, about your own "
            "real conversation and the criteria you wrote before it.\n"
            "1. Save it.\n"
            "2. Type where you saved it.\n"
            "3. Click Check my work."
        ),
        "verify": "artifact",
        "check": "introduction report",
        "cross": "criteria",
        "sections": [
            {
                "heading": "Problem", "min_words": 14, "needs": ["name"],
                "what": "who you explained Hermes to and the task they have, by name",
                "fix": "Name the person.",
                "hint": "Name the person, their business, and the one task that repeats.",
                "example": "Example: I explained Hermes to Joanne Pruett, who runs a bakery and retypes 25 wholesale orders a week.",
            },
            {
                "heading": "Criteria", "min_words": 20, "needs": [],
                "what": "three numbered criteria you wrote before you started, two with a number",
                "hint": "Number three lines. Put a count or a time in at least two, so each one can fail.",
                "example": "Example:\n1. She can say back what Hermes does after 10 minutes\n2. She names who signs\n3. My note reaches the builder in 2 days",
            },
            {
                "heading": "What I did", "min_words": 15, "needs": ["time"],
                "what": "what you did and how long it took",
                "fix": "Say how long it took, such as a call that ran 20 minutes.",
                "hint": "Say when and how long you spoke, and what you sent to the builder.",
                "example": "Example: On Saturday I talked with Joanne for 30 minutes and sent the builder a note on Monday.",
            },
            {
                "heading": "Evidence", "min_words": 20, "needs": [],
                "what": "one numbered line per criterion, each ending met, partly met or not met",
                "hint": "Match the numbers to your criteria. State what happened, then the verdict.",
                "example": "Example:\n1. She said back the limit but missed the credit. Partly met.\n2. She named her husband as the signer. Met.\n3. The note went out on day 3. Not met.",
            },
            {
                "heading": "What did not work", "min_words": 12, "needs": [],
                "what": "one thing that fell short and why",
                "hint": "Write the moment you wish you had handled differently, and why it went that way.",
                "example": "Example: I explained pricing too early, so Joanne asked about cost before she described the task.",
            },
            {
                "heading": "Next", "min_words": 8, "needs": ["time"],
                "what": "your next action and when it happens",
                "fix": "Say when, for example on Friday at 2 pm or in 3 days.",
                "hint": "Write the one next action, who takes it, and when.",
                "example": "Example: I call the builder on Friday at 2 pm to agree a first step.",
            },
        ],
        "proof": (
            "Your introduction report, saved on your computer, with your own numbered criteria and a verdict on "
            "each one. Its fingerprint goes on your Field Record."
        ),
    },
    "revisions": [
        {
            "version": 1,
            "kind": "added",
            "summary": (
                "New in 0.5.0: you explain Hermes to one real person, pass an opportunity to a builder, and report "
                "against criteria you wrote first."
            ),
        }
    ],
}


PLACEMENT = {
    "title": "Placement check",
    "intro": (
        "Six scenario questions, two each for beginner, intermediate and advanced, tell Field Academy where to "
        "start you on the Ambassador path. The checks on real work still apply: you write the documents either way."
    ),
    "minutes": 5,
    "questions": [
        {
            "id": "p1",
            "level": "beginner",
            "question": "A prospect asks, \"Does Hermes live in your cloud?\" What is the most honest first answer?",
            "options": [
                "Yes, we host everything for you and take care of all the upkeep.",
                "It is open source and runs on a computer you choose, so you own the setup.",
                "It depends on the plan you pick, so I would rather send you a brochure and a price list.",
            ],
            "answer": 1,
            "why": (
                "Hermes is open source software that runs on a computer you choose, or on Hermes Cloud, which Nous "
                "hosts. The first option promises hosting and upkeep you can't speak for. The third dodges the "
                "question, which costs the trust you need."
            ),
        },
        {
            "id": "p2",
            "level": "beginner",
            "question": "At the end of your two-minute explanation, whose work do you credit?",
            "options": [
                "Nous Research, who maintain Hermes, and the community teachers you learned from",
                "Nobody, because the explanation is your own work and your own words",
                "Only the person who installed Hermes for the client, since they did the hands-on work",
            ],
            "answer": 0,
            "why": (
                "Nous Research maintains Hermes, and named community teachers such as Tonbi and Tony Simons do the best "
                "teaching. Naming them shows a skeptic where the real material lives. The other options leave out the people who built it."
            ),
        },
        {
            "id": "p3",
            "level": "intermediate",
            "question": "A prospect has a weekly task and a keen owner. Only her boss approves spending, and you have not met him. What do you do?",
            "options": [
                "Send a quote now, since the task is clear and the owner is keen",
                "Write the prospect off and move on to someone with a signer",
                "Keep talking, ask to include the boss, and hold the quote",
            ],
            "answer": 2,
            "why": (
                "A real opportunity needs someone who can approve spending. Quoting now prices work nobody can buy. "
                "Writing her off ignores the task and owner you already found. Asking for the boss keeps the conversation moving."
            ),
        },
        {
            "id": "p4",
            "level": "intermediate",
            "question": "Which prospect is a real opportunity?",
            "options": [
                "A founder who says AI will change everything but names no task at all",
                "An office manager who retypes 40 orders nightly, and an owner who signs $2,000",
                "A board member who wants a demo to show at next month's meeting",
            ],
            "answer": 1,
            "why": (
                "The office manager shows a task that repeats and a person who feels it, and the owner signs for spending. "
                "The founder and the board member show interest and no task, so both stay at later."
            ),
        },
        {
            "id": "p5",
            "level": "advanced",
            "question": "On a call you said, \"We can probably have this running by March.\" Where does that sentence go in the handoff note?",
            "options": [
                "Under Known, so the builder can see the target date from the start",
                "Left out of the note, since the builder sets the dates",
                "Under Owner, next to your name, so the builder knows who said it",
                "Under Promised, in your exact words, for the builder to confirm",
            ],
            "answer": 3,
            "why": (
                "The sentence is something you said, so it belongs under Promised in your words. Under Known it reads as a "
                "fact, and leaving it out hides what the client heard. Owner holds names, and the builder confirms the date."
            ),
        },
        {
            "id": "p6",
            "level": "advanced",
            "question": "The joint call is Thursday. When does the builder get your note?",
            "options": [
                "After the call, once you know what was agreed by everyone",
                "At the start of the call, as you introduce everyone present",
                "Before the call, while you still remember who said what",
                "Only if the client asks to see it",
            ],
            "answer": 2,
            "why": (
                "Sent before the call, the note lets the builder arrive with facts and promises already apart. After the "
                "call your memory of who said what has faded, and a note at the start of the call comes too late to read."
            ),
        },
    ],
}
