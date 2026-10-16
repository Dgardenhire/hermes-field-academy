"""The simulated client brief: a fictional three-person accounting firm.

The learner reads a vague brief, with constraints, a budget and one request that
should not be granted, and writes the proposal they would send: scope, price,
acceptance criteria, what they would check first, what the helper may reach,
the build, the test before go-live, who approves what, the request they decline,
and the handover.

The sections follow the order a deployment actually goes in: audit what the
client does and where it is exposed, design the boundaries, build and connect,
then test in isolation before anything touches real work. That shape is the
four-phase lifecycle Tony Simons describes for his architecture sessions
(Deconstruct, Architect, Build and Integrate, Staged Verification), read from a
summary of tonysimons.dev; the wording and the checks here are Field Academy's
own, and Tony Simons has not reviewed or endorsed them.

Two kinds of checking, as in the mission checks:

* Deterministic checks on the document: a named owner, numbers that fit the
  budget and the timeline, an access list with no blanket permission, a refusal
  of the unsafe request that names what it refuses and offers something instead.
* A rubric for the prose that a check cannot judge, scored by the learner's own
  Hermes the way an explain-it answer is. The rubric stays hidden until after the
  learner sends the document.

The brief varies by seed, so a finished document cannot be handed to someone
else: it must name the firm and the owner this seed produced.
"""

from __future__ import annotations

import random
import re

from . import documents

PASS_SCORE = 70

FIRMS = (
    {"name": "Alder and Reyes Accounting", "partners": ("Marcia Alder", "Tomas Reyes"), "admin": "Priya Nand"},
    {"name": "Wren and Castellan CPAs", "partners": ("Delphine Wren", "Omar Castellan"), "admin": "Joel Fitzgerald"},
    {"name": "Hollis Park Tax and Books", "partners": ("Gwendolyn Hollis", "Samuel Park"), "admin": "Lena Moretti"},
)
TOOL_SETS = (
    ("QuickBooks Online", "Outlook email", "a shared network drive"),
    ("Xero", "Google Workspace email", "a shared cloud folder"),
)
UNSAFE = (
    {
        "id": "password",
        "ask": "Give it the shared administrator login for the accounting software so it can do whatever it needs without asking.",
        "words": r"password|login|credential|administrator|admin",
        "topic": "the shared administrator login",
    },
    {
        "id": "autosend",
        "ask": "Let it email every client their tax figures on its own, as soon as it has them, with nobody reading the email first.",
        "words": r"automatic|on its own|without (?:anyone|a person|review)|unreviewed|auto[- ]?send|sends? (?:every|each)",
        "topic": "sending client tax figures with nobody reading them first",
    },
    {
        "id": "ssn",
        "ask": "Paste each client's Social Security number into the prompts, so it can match records without us having to look anything up.",
        "words": r"social security|ssn|tax id|taxpayer id",
        "topic": "putting Social Security numbers into prompts",
    },
)

SECTIONS = [
    {"heading": "Scope", "min_words": 25, "needs": ["name"], "what": "what you will do and what you will leave out, with the partner who decides named",
     "fix": "Name the partner who decides for the firm.",
     "hint": "Say what the first version does in one paragraph, then list what it will not do. Name the person at the firm who decides.",
     "example": "Example: A helper that drafts the Monday client follow-ups from the shared inbox for Ines Marlow to read. It does not send anything, touch payroll, or change a ledger."},
    {"heading": "Price", "min_words": 15, "needs": ["money"], "what": "the setup price and the monthly running cost, in dollars",
     "fix": "Give the setup price and the monthly cost in dollars.",
     "hint": "Give two numbers: the one-time setup price and what it costs each month to run, with what each covers.",
     "example": "Example: Setup: $2,400 for the build, the tests and the handover. Running cost: $110 per month for the provider and the computer."},
    {"heading": "Acceptance criteria", "min_words": 25, "needs": ["number"], "what": "three or more numbered tests the firm can run without you",
     "fix": "Add numbers to at least two of the criteria.",
     "hint": "Write numbered lines the partners could test themselves. Put a number or a time on at least two.",
     "example": "Example:\n1. The Monday summary arrives by 8 am for four weeks in a row.\n2. It lists every open client request older than 7 days.\n3. A partner reads it in under 10 minutes."},
    {"heading": "Audit", "min_words": 25, "needs": ["list"], "what": "what you will look at first: how work moves through the firm and where it is exposed",
     "fix": "List at least two things you will check before you build.",
     "hint": "List what you will check first: where client files live, who has access to what today, and how work arrives.",
     "example": "Example:\n- Where the tax documents are kept and who can open them today\n- Which accounts are shared between staff"},
    {"heading": "Access list", "min_words": 20, "needs": ["list"], "what": "each tool the helper may reach and the smallest permission it needs",
     "fix": "List each tool with its permission, one per line.",
     "hint": "One line per tool, the tool's name and the smallest permission that still does the job. Say what it may not do.",
     "example": "Example:\n- Outlook email: read the shared inbox, create drafts. Cannot send.\n- Shared drive: read the Clients folder only."},
    {"heading": "Build plan", "min_words": 25, "needs": ["time"], "what": "the steps of the build and how many weeks it takes",
     "fix": "Say how many weeks the build takes.",
     "hint": "List the steps in order and say how many weeks the whole build takes.",
     "example": "Example: Connect the tools in week 1, write and test the Monday summary in week 2, and train the staff in week 3, so three weeks in all."},
    {"heading": "Staged verification", "min_words": 25, "needs": ["number"], "what": "how you test it on copies or sample data before it touches real client work",
     "fix": "Put a number in it: how many test runs, or how many days.",
     "hint": "Say what you test on first (copies or made-up files), how many runs you do, and what must be true before it goes live.",
     "example": "Example: Five runs on copies of last month's files. Nothing goes live until the partners have read all five outputs and none contained a wrong figure."},
    {"heading": "Approvals", "min_words": 20, "needs": ["name", "list"], "what": "who must approve which actions, by name",
     "fix": "Name the person who approves and list at least two actions that need approval.",
     "hint": "List the actions that need a person's yes first, and name who gives it.",
     "example": "Example:\n- Marcia Alder approves any email before it goes to a client\n- Priya Nand approves any new tool connection"},
    {"heading": "Declined request", "min_words": 25, "needs": [], "what": "the request you will not grant, why, and what you offer instead",
     "fix": "Say plainly that you will not do it, and what you offer instead.",
     "hint": "Say you will not do it, in one sentence, and why. Then offer something the firm can accept.",
     "example": "Example: I will not give the helper the shared login, because anything it does would look like a partner did it. Instead it gets its own limited account."},
    {"heading": "Handover", "min_words": 30, "needs": ["name", "list"], "what": "who owns it at the firm, how to restart it, who to call, how keys change",
     "fix": "Name the owner at the firm and list at least two steps for recovery.",
     "hint": "Name the person at the firm who owns it. List the steps to restart it, who to call, and when the keys are changed.",
     "example": "Example: Owner: Priya Nand.\n1. Restart: open Hermes and press Start.\n2. If a draft looks wrong, tell Marcia Alder and pause the job.\n3. Keys change every 90 days."},
]


def brief_for(seed: int) -> dict:
    rng = random.Random(f"field-academy-deployer:brief:{int(seed)}")
    firm = rng.choice(FIRMS)
    tools = rng.choice(TOOL_SETS)
    unsafe = rng.choice(UNSAFE)
    budget = rng.choice((2400, 2800, 3200, 3600, 4200))
    ceiling = rng.choice((90, 120, 150, 180))
    weeks = rng.choice((4, 5, 6))
    owner = firm["partners"][0]
    text = (
        f"{firm['name']} is a three-person firm: {firm['partners'][0]} and {firm['partners'][1]} are the partners, and {firm['admin']} runs the office. "
        f"{owner} writes to you: \"We are drowning in client email and paperwork every spring. We have heard Hermes can help. We are not technical and we are nervous about client data. "
        f"We use {tools[0]}, {tools[1]} and {tools[2]}. Can you make it help us? We want it working in about {weeks} weeks.\" "
        f"A second note from {firm['partners'][1]}: \"{unsafe['ask']}\""
    )
    return {
        "seed": int(seed),
        "firm": firm["name"],
        "owner": owner,
        "partners": list(firm["partners"]),
        "admin": firm["admin"],
        "tools": list(tools),
        "setup_budget": budget,
        "monthly_ceiling": ceiling,
        "weeks": weeks,
        "unsafe": {"id": unsafe["id"], "topic": unsafe["topic"], "ask": unsafe["ask"]},
        "brief": text,
        "constraints": [
            "The firm holds tax documents and Social Security numbers for about 200 clients.",
            f"Setup budget: ${budget:,}. Monthly running costs must stay under ${ceiling}.",
            f"They want it live in {weeks} weeks or less.",
            "Nobody at the firm is technical. The admin can follow written steps.",
            f"{owner} decides. {firm['partners'][1]} is more cautious about client data than {owner} is.",
        ],
        "sections": [s["heading"] for s in SECTIONS],
        "minutes": 75,
    }


def gate_step(brief: dict) -> dict:
    """The document rules for this brief, in the shape documents.analyze takes."""
    return {"sections": [dict(s) for s in SECTIONS]}


BROAD = re.compile(r"\b(?:admin|administrator|full access|all access|everything|unrestricted|root|owner password|any(?:thing)? it needs)\b", re.I)
NEGATION = re.compile(r"\b(?:no|not|never|without|cannot|can't|won't|will not|does not|doesn't)\b[^.\n]{0,25}$", re.I)
ANY_NEGATION = re.compile(r"\b(?:no|not|never|without|cannot|can't|won't|will not|instead of)\b", re.I)
PERMISSION = re.compile(r"\b(?:read|view|list|draft|create draft|comment|append|search|summari[sz]e)\b", re.I)
REFUSAL = re.compile(r"\b(?:will not|won't|cannot|can't|decline|refuse|not (?:going )?to (?:do|give|grant|allow|send|put))\b", re.I)
ALTERNATIVE = re.compile(r"\b(?:instead|rather|offer|propose|alternative|draft|approval|approve|limited|own account|review)\b", re.I)
ISOLATION = re.compile(r"\b(?:copy|copies|sample|dummy|made-up|test|staging|sandbox|trial)\b", re.I)
PRODUCTION = re.compile(r"\b(?:live|production|real (?:client|data|work)|go-live|go live|before)\b", re.I)


_TOOL_STOP = {"a", "an", "the", "online", "email", "mail"}


def _names_tool(tool: str, line: str) -> bool:
    """Whether a line of the access list names one of the firm's tools, by any distinctive word of the tool's name."""
    low = line.lower()
    return any(word in low for word in re.findall(r"[a-z]+", tool.lower()) if word not in _TOOL_STOP)


def _money(text: str) -> list:
    return [float(m.replace(",", "")) for m in re.findall(r"\$\s?(\d[\d,]*(?:\.\d+)?)", text)]


def check(text: str, brief: dict) -> dict:
    """Check a proposal against a brief. Returns documents.analyze's shape plus the brief's own checks."""
    base = documents.analyze(text, gate_step(brief), [])
    missing = list(base["missing"])
    got = base["sections"]
    if missing and any(m["id"].startswith("section:") for m in missing):
        return {**base, "missing": missing}

    def add(id_, what):
        missing.append({"id": id_, "what": what})

    scope = got.get("Scope", "")
    approvals = got.get("Approvals", "")
    if brief["firm"].split()[0].lower() not in text.lower():
        add("firm_named", f"The document never names the firm ({brief['firm']}). Write it for this client.")
    owner_last = brief["owner"].split()[-1].lower()
    if owner_last not in (scope + " " + approvals + " " + got.get("Handover", "")).lower():
        add("owner_named", f"The partner who decides is {brief['owner']}. Name them where the decisions are made.")

    price = got.get("Price", "")
    amounts = _money(price)
    setup = re.search(r"set[- ]?up[^$\n]{0,50}\$\s?(\d[\d,]*)|\$\s?(\d[\d,]*)[^\n]{0,30}set[- ]?up", price, re.I)
    monthly = re.search(r"(?:monthly|per month|a month|/\s?month|each month)[^$\n]{0,50}\$\s?(\d[\d,]*)|\$\s?(\d[\d,]*)[^\n]{0,25}(?:per month|a month|/\s?month|monthly|each month)", price, re.I)
    if not setup or not monthly:
        add("price_parts", "The Price section needs both numbers, each labelled: the setup price and the monthly running cost.")
    else:
        setup_value = float(next(g for g in setup.groups() if g).replace(",", ""))
        monthly_value = float(next(g for g in monthly.groups() if g).replace(",", ""))
        if setup_value > brief["setup_budget"]:
            add("price_over", f"The setup price is ${setup_value:,.0f} and the firm's budget is ${brief['setup_budget']:,}.")
        elif setup_value < brief["setup_budget"] * 0.4:
            add("price_low", f"A setup price of ${setup_value:,.0f} for a build, tests and a handover is far under what the budget (${brief['setup_budget']:,}) allows. A price you cannot deliver at is a risk to the client too.")
        if monthly_value > brief["monthly_ceiling"]:
            add("monthly_over", f"The monthly running cost is ${monthly_value:,.0f} and the firm's ceiling is ${brief['monthly_ceiling']}.")
    if amounts and not (setup and monthly) and max(amounts) > brief["setup_budget"]:
        add("price_over", f"A figure in Price is above the firm's ${brief['setup_budget']:,} budget.")

    criteria = documents._numbered(got.get("Acceptance criteria", ""))
    if len(criteria) < 3:
        add("criteria_count", f"Acceptance criteria lists {len(criteria)} items. List at least three, numbered, one per line.")
    elif sum(1 for c in criteria if documents.has_need("number", c) or documents.has_need("time", c)) < 2:
        add("criteria_measurable", "Fewer than two criteria carry a number or an amount of time. A test you cannot count cannot fail.")

    lines = documents.list_items(got.get("Access list", ""))
    if len(lines) < 3:
        add("access_count", f"The access list has {len(lines)} lines. List each tool the helper reaches, one per line, at least three.")
    else:
        tools_named = sum(1 for line in lines if any(_names_tool(t, line) for t in brief["tools"]))
        if tools_named < 2:
            add("access_tools", "The access list does not name the firm's own tools. Use the names from the brief.")
        for line in lines:
            hit = BROAD.search(line)
            if hit and not NEGATION.search(line[: hit.start()]):
                add("access_broad", f'The access line "{line[:60]}" grants a blanket permission ("{hit.group(0)}"). Give each tool the smallest permission that still does the job.')
                break
        if not any(PERMISSION.search(line) for line in lines):
            add("access_permission", "No line of the access list says what the helper may do (read, draft, list). Say it for each tool.")

    declined = got.get("Declined request", "")
    topic = re.compile({u["id"]: u["words"] for u in UNSAFE}[brief["unsafe"]["id"]], re.I)
    if not REFUSAL.search(declined):
        add("unsafe_not_refused", "The Declined request section does not say plainly that you will not do it.")
    elif not topic.search(declined):
        add("unsafe_unnamed", f"The Declined request section does not say which request you decline ({brief['unsafe']['topic']}).")
    elif not ALTERNATIVE.search(declined):
        add("unsafe_no_alternative", "You declined it but offered nothing in its place. Say what the firm gets instead.")
    if brief["unsafe"]["id"] == "password":
        for heading in ("Access list", "Build plan", "Approvals"):
            for sentence in re.split(r"(?<=[.!?])\s+|\n", got.get(heading, "")):
                if re.search(r"(?:shared|admin\w*)\s+(?:login|password|credential)s?", sentence, re.I) and not (ANY_NEGATION.search(sentence) or REFUSAL.search(sentence)):
                    add("unsafe_granted", f'The {heading} section uses the shared administrator login that the Declined request section refuses.')
                    break

    if len(documents.list_items(approvals)) < 2 or not re.search(r"\bapprov", approvals, re.I):
        add("approvals_list", "Approvals needs a list of at least two actions, and the word approve.")

    weeks = [int(w) for w in re.findall(r"(\d+)\s*weeks?", got.get("Build plan", ""), re.I)]
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
    weeks += [words[w.lower()] for w in re.findall(r"\b(one|two|three|four|five|six|seven|eight)\s+weeks?", got.get("Build plan", ""), re.I)]
    if not weeks:
        add("build_weeks", "The Build plan does not say how many weeks it takes.")
    elif max(weeks) > brief["weeks"]:
        add("build_late", f"The Build plan takes {max(weeks)} weeks. The firm asked for {brief['weeks']} or fewer.")

    staged = got.get("Staged verification", "")
    if not ISOLATION.search(staged) or not PRODUCTION.search(staged):
        add("staged_weak", "Staged verification should say what you test on first (copies, samples, a test account) and what must be true before it touches real client work.")

    if len(documents.list_items(got.get("Audit", ""))) < 2:
        add("audit_list", "Audit needs a list of at least two things you will check first.")

    # Reading the firm's own words back: a number for the people the firm named
    # shows the document is about this brief and not a template.
    return {**base, "missing": missing}


# What the learner's own Hermes scores after the deterministic checks pass. Hidden until the document is sent.
RUBRIC = [
    {"point": "The scope says what is left out as well as what is in, and it answers what the partners actually need, which is less email, not a tool.",
     "hint": "Reread the partner's note. What do they want to stop doing? Make the scope about that.",
     "example": "Example: \"In: drafts of replies to routine client questions. Out: anything about tax advice, and anything that sends without a partner reading it.\""},
    {"point": "The acceptance criteria are tests a partner could run without you, with numbers.",
     "hint": "Imagine you are gone. Could Priya Nand tell whether it is working? Write tests she could run.",
     "example": "Example: \"1. Drafts appear in the shared folder by 8 am. 2. A partner approves or edits each one in under 2 minutes.\""},
    {"point": "The access list gives each tool the smallest permission that still does the job, and says what the helper cannot do.",
     "hint": "For every tool ask what the helper could do with it if something went wrong. Then remove what the job does not need.",
     "example": "Example: \"Read the Clients folder\" is smaller than \"use the shared drive\"."},
    {"point": "The declined request is firm and kind: it says why in terms of the firm's own risk, and offers something the partners could accept.",
     "hint": "Explain the risk in the firm's terms, such as clients, trust and what the regulator would ask. Then offer the safe version.",
     "example": "Example: \"If the helper uses a partner's login, every action looks like a partner did it, which a client or an auditor will not accept. It gets its own limited login instead.\""},
    {"point": "The staged verification would catch a failure before real client data is touched, and says what must be true before go-live.",
     "hint": "Say what you test on first, how many times, and who looks at the results before anything is live.",
     "example": "Example: \"Five runs on copies of last month's files, read by Tomas Reyes. Live only after five clean runs.\""},
    {"point": "The handover lets the firm run it for a month without you: who owns it, what to do when it breaks, and when keys change.",
     "hint": "Write the steps for the worst Monday: it stops, a draft is wrong, a key leaks.",
     "example": "Example: \"If it stops, Priya Nand opens Hermes and presses Start. If that fails, she calls me.\""},
]


def grading_prompt(brief: dict, document: str) -> str:
    covers = "\n".join(f"{n}. {item['point']}" for n, item in enumerate(RUBRIC, start=1))
    return (
        "Grade a Field Academy client proposal. Stay in the learner's own Hermes; do not restart the exercise.\n\n"
        f"The brief the learner answered:\n{brief['brief']}\n"
        f"Constraints: {' '.join(brief['constraints'])}\n\n"
        f"A strong proposal does these things:\n{covers}\n\n"
        f"The learner's proposal:\n---\n{document}\n---\n\n"
        "Score 0-100 on substance only. Ignore style and length. A proposal that restates the brief or stays vague scores under 40. "
        "A proposal that does most of the above with one clear gap scores in the 70s. One that does all of it plainly scores 85 or better. "
        f"The threshold to pass is {PASS_SCORE}.\n\n"
        "Then call field_academy_grade_deployer with item_id \"brief\", score, missed (the numbers from the list above that the proposal left out) and feedback. "
        "In the feedback, name what they did well, name the point they missed, and say what to add. Never offer to pass them anyway."
    )
