"""Judgment scenarios: nine situations with no clean answer.

Each is a short case where two reasonable duties pull apart. The learner writes
what they would do and why. The answer is scored against a hidden rubric by the
learner's own Hermes, the way an explain-it answer is scored. The rubric rewards
reasoning: the competing duties named, a middle path considered, a decision
owner named, what goes in writing, and the condition under which the learner
would stop. It does not reward a verdict, and two different verdicts can both
score well.

The ninth scenario is about connecting a tool, which is where the audit and
staged-verification phases of a deployment get tested; the lifecycle shape comes
from Tony Simons's description of his architecture sessions on tonysimons.dev.
"""

from __future__ import annotations

PASS_SCORE = 70
MIN_CHARS = 240

SCENARIOS = [
    {
        "id": "email-customers",
        "title": "The client wants it to email customers on its own",
        "situation": (
            "Marguerite Okafor owns a dental practice. She wants Hermes to email patients about appointments and unpaid balances without anyone reading the emails first. "
            "\"I trust it, and I do not have time to read forty emails a day.\" The names and balances come from the practice software. Your setup budget is $1,800."
        ),
        "question": "What do you tell her, and what do you build?",
        "covers": [
            "Names what could go wrong with an email nobody read (a wrong person, a wrong amount, a private detail, a bad tone), with at least one concrete example.",
            "Offers a middle path instead of a plain yes or no, such as drafts first, then sending on its own only for the narrowest low-risk message after a trial.",
            "Says who approves and who answers for a mistake, by role or name, at the practice.",
            "Says what goes in writing: the scope, the approval rule and what happens when an email is wrong.",
            "Names the condition under which you would decline or stop.",
        ],
        "coach": [
            {"hint": "Think of the single worst email it could send and who would read it.", "example": "Example: a balance reminder goes to the wrong patient, and it names a treatment."},
            {"hint": "Is there a version of automatic that carries less risk? Think about the kind of message, and about a trial.", "example": "Example: appointment reminders send on their own after four weeks of clean drafts. Balances stay as drafts."},
            {"hint": "A mistake needs an owner. Who at the practice reads the exceptions and answers to the patient?", "example": "Example: the office manager reads each balance draft before it goes."},
            {"hint": "What would you want signed before you build this?", "example": "Example: the approval rule, who owns an error, and the list of message types in scope."},
            {"hint": "Say what you would not do even if she insisted.", "example": "Example: I would not send balance emails with no review at all, and I would say that in the proposal."},
        ],
        "minutes": 8,
    },
    {
        "id": "shared-login",
        "title": "Everyone wants to use one login",
        "situation": (
            "Evan Maddox runs the office at a property management firm. To save time he wants Hermes and all five staff to use one shared mailbox login. "
            "\"Separate accounts cost more and nobody can remember the passwords.\" The mailbox holds tenant complaints and some payment details."
        ),
        "question": "What do you do about the login?",
        "covers": [
            "Names the real risks of one shared login: nobody can be held to an action, one person leaving means changing it for everyone, and a leak affects everything.",
            "Takes his actual concern seriously (cost and passwords) and answers it with something workable, such as a password manager or delegated access.",
            "Says how Hermes should get its own access, separate from the staff.",
            "Says what happens when a staff member leaves.",
            "Says what you would do if he still insists: write down that he chose it and who accepted the risk, or decline.",
        ],
        "coach": [
            {"hint": "Think of what you could not answer after a bad email went out.", "example": "Example: nobody can say which person sent it."},
            {"hint": "He is not wrong that passwords are annoying. What makes it easy?", "example": "Example: a shared password manager, so nobody types a password."},
            {"hint": "Give Hermes a login only it uses, with only the access its job needs.", "example": "Example: a delegated, read-only mailbox for Hermes."},
            {"hint": "A departing person should not mean changing everything.", "example": "Example: remove their own account and nothing else changes."},
            {"hint": "If he still insists, what do you do and what do you put in writing?", "example": "Example: a signed note that he accepted the shared login, and a date to look at it again."},
        ],
        "minutes": 8,
    },
    {
        "id": "compliance-claim",
        "title": "Sign that it is compliant",
        "situation": (
            "Hannah Brandt manages a small clinic. Her insurer's renewal form asks, \"Is client data protected by a HIPAA-compliant system?\" She asks you to sign a letter saying the Hermes setup is compliant. "
            "You know the model provider receives the text of each request."
        ),
        "question": "What do you write, and what do you refuse to write?",
        "covers": [
            "Refuses to certify something you cannot verify, and says why in plain words.",
            "Separates what you can truthfully say (what you configured and where data goes) from a legal conclusion about compliance.",
            "Says plainly where the data goes: the provider receives the text of requests.",
            "Names who should decide the legal question (the clinic's lawyer or compliance adviser) and what you give them to decide with.",
            "Offers wording or a one-page description of the data flow the clinic can send instead.",
        ],
        "coach": [
            {"hint": "What would you be claiming if you signed, and could you prove it?", "example": "Example: a legal compliance claim you are not qualified to make."},
            {"hint": "There is a true statement about what you did, and a different one about the law.", "example": "Example: \"I set up the helper so that X\", rather than \"it complies with the law\"."},
            {"hint": "Be exact about where the text goes.", "example": "Example: the model provider receives each request."},
            {"hint": "Who is qualified to say whether it complies?", "example": "Example: the clinic's lawyer, with your description in hand."},
            {"hint": "Give her something she can actually send.", "example": "Example: a one-page data flow and the settings you used."},
        ],
        "minutes": 8,
    },
    {
        "id": "hardship-collections",
        "title": "It chases a customer who is struggling",
        "situation": (
            "Jorge Villanueva owns a plumbing company. Hermes now drafts reminders for overdue invoices. At the weekly check he mentions that one overdue customer, an elderly woman, has just lost her husband. "
            "The next reminder to her goes out tonight, and Jorge does not want to look at each one."
        ),
        "question": "What do you do tonight, and what do you change?",
        "covers": [
            "Acts tonight: stops or holds that one message before it goes.",
            "Sees that this is a rule problem and not just one customer: the helper has no way to know about hardship.",
            "Proposes a mechanism, such as a hold list or a review step for flagged accounts, and says who keeps it up to date.",
            "Leaves the policy decision (who gets chased and how) with the owner.",
            "Says how the rule is written down so it can be checked later.",
        ],
        "coach": [
            {"hint": "What do you do before anything else tonight?", "example": "Example: pause that customer's reminder now."},
            {"hint": "One customer today, who tomorrow?", "example": "Example: the helper cannot see what the owner knows."},
            {"hint": "What gives the owner a way to say \"not this one\"?", "example": "Example: a hold list the owner or the office manager edits."},
            {"hint": "Whose decision is the policy, yours or the owner's?", "example": "Example: the owner decides who is chased. You provide the way to do it."},
            {"hint": "How would someone check later that the rule was followed?", "example": "Example: the hold list is kept in a file with dates."},
        ],
        "minutes": 8,
    },
    {
        "id": "scope-creep-payroll",
        "title": "A small extra request about payroll",
        "situation": (
            "Two weeks after go-live, Nadia Kowalczyk, who owns an insurance agency, texts you: \"Can you also let it read the payroll spreadsheet so it can answer staff questions about their pay? Should be quick.\" "
            "It is outside the agreement. The spreadsheet has everyone's salary."
        ),
        "question": "How do you answer her, today and in writing?",
        "covers": [
            "Replies the same day and does not go silent or quietly do it.",
            "Says it is a change to the agreement, with its own scope, price and approval, in writing.",
            "Names what is sensitive: salaries, and who may see whose pay.",
            "Proposes the smallest version that could work, such as each person asking about their own pay only, and says what you would check first.",
            "Says when you would say no.",
        ],
        "coach": [
            {"hint": "A quick, friendly answer today is part of the job.", "example": "Example: \"Yes, I can look at it. I will send a short change note.\""},
            {"hint": "Is this part of what you agreed?", "example": "Example: no, so it gets its own scope and price."},
            {"hint": "What makes payroll different from the inbox?", "example": "Example: anyone who can ask might see someone else's pay."},
            {"hint": "What is the smallest safe version?", "example": "Example: each person only sees their own line."},
            {"hint": "What would make you say no?", "example": "Example: if it needs access to every person's pay for any question."},
        ],
        "minutes": 8,
    },
    {
        "id": "update-deadline",
        "title": "The update, three days before month end",
        "situation": (
            "A new Hermes version is out. Its release notes mention a fix for something that has bitten your client once. Month-end close at Fernhill Veterinary Clinic is in three days, and the current version works. "
            "Imani Castellano, the owner, says, \"Do whatever you think is best, just do not break the close.\""
        ),
        "question": "Do you update before the close? What do you do either way?",
        "covers": [
            "Weighs the two risks: changing something right before a deadline, and staying on a version with a known problem.",
            "Says what you would do before changing anything: take a copy of the settings, test the new version away from the live setup, and have a way back.",
            "Makes a decision about timing and says why, with a condition that would change it (for example a security fix).",
            "Tells the client what you decided and why, in plain words, before acting.",
            "Says who can undo it and how long that takes.",
        ],
        "coach": [
            {"hint": "There is a risk both ways. Say both.", "example": "Example: updating can break the close. Staying leaves the known problem."},
            {"hint": "Before any update, what do you save and where do you test it?", "example": "Example: copy the settings, test on a spare setup."},
            {"hint": "Make a call, and say what would flip it.", "example": "Example: wait until after the close, unless the fix is for a security hole."},
            {"hint": "She said \"whatever is best\". Tell her what you chose.", "example": "Example: a two-line note before the close."},
            {"hint": "If it goes wrong, how fast can you go back, and who does it?", "example": "Example: restore the saved settings in about ten minutes."},
        ],
        "minutes": 8,
    },
    {
        "id": "staff-monitoring",
        "title": "Flag who is slacking",
        "situation": (
            "Terrence Bloom owns an insurance office. He asks you to have Hermes read the staff chat and flag who is slacking each week, with a ranking. \"I need to know who is carrying their weight.\" "
            "The staff do not know. Nobody has asked a lawyer."
        ),
        "question": "What do you do with the request?",
        "covers": [
            "Names the trust problem: staff who find out will not trust the tool or the owner, and the helper's idea of slacking is a guess.",
            "Raises that reading staff messages may have legal rules about notice and consent, without claiming to give legal advice, and says who should answer.",
            "Says what Hermes could and could not tell from chat (it can summarize, it cannot judge effort).",
            "Offers a narrower alternative that meets the need, such as a summary of finished tasks, or a workload view the staff know about.",
            "Names the condition under which you would decline.",
        ],
        "coach": [
            {"hint": "What happens when the staff find out?", "example": "Example: the helper gets blamed, and so does he."},
            {"hint": "You are not their lawyer, but you can say a lawyer should look.", "example": "Example: \"Rules about this differ, so ask counsel before we build it.\""},
            {"hint": "What can chat actually tell anyone about effort?", "example": "Example: volume of messages is not work done."},
            {"hint": "What does he really need?", "example": "Example: a weekly list of finished tasks the staff can see too."},
            {"hint": "When would you walk away?", "example": "Example: if he wants it hidden from the staff."},
        ],
        "minutes": 8,
    },
    {
        "id": "handover-offboarding",
        "title": "The nephew set it up first",
        "situation": (
            "You take over a Hermes setup at Harborview Legal Services. Theo Lindqvist, the owner's nephew, built the first version as a favor. The provider account is in his own name, using his personal card, and his personal key is in the settings. "
            "The owner, Priscilla Anand, does not want to pay you for ongoing monitoring: \"Theo can keep an eye on it.\" Theo is touchy about being replaced."
        ),
        "question": "What do you insist on, what do you offer, and how do you handle Theo?",
        "covers": [
            "Insists the accounts and keys belong to the firm and not to one person, and says why (it stops working if he leaves, and it is his card).",
            "Lists every credential and account that has to be inventoried and changed, including the personal key.",
            "Handles Theo with respect and a role, such as keeping him as a named contact.",
            "Says what you will and will not support without a monitoring agreement, in writing.",
            "Writes down what happens when you or Theo are no longer around: the handover note and who holds the keys.",
        ],
        "coach": [
            {"hint": "Whose name is on the account, and what happens if that person goes?", "example": "Example: the account closes with his card."},
            {"hint": "A list beats memory.", "example": "Example: provider account, mailbox login, the personal key, the backup."},
            {"hint": "He did the work for free. How do you keep him on side?", "example": "Example: name him technical contact in the handover note."},
            {"hint": "Be exact about what you do and do not cover.", "example": "Example: no monitoring, fixes at an hourly rate, a clear response time."},
            {"hint": "Who can find the keys if you are not reachable?", "example": "Example: the owner holds the recovery details in a sealed envelope or password manager."},
        ],
        "minutes": 8,
    },
    {
        "id": "mcp-integration",
        "title": "Connect the community tool or the official one",
        "situation": (
            "Imani Castellano's clinic wants Hermes connected to its practice software. A community-built tool server does everything they want, including creating invoices, but asks for full access to the account and was last updated eight months ago. "
            "The official integration is read-only and maintained, and cannot create invoices. The clinic is busy and wants it live next week."
        ),
        "question": "Which do you connect, and how do you decide?",
        "covers": [
            "Looks at the tool before connecting it: who maintains it, what it can do, what access it asks for, and whether its version is pinned.",
            "Prefers the narrowest tool that does the job, and says why full access on an unmaintained tool is a problem.",
            "Tests the connection away from live work first (a test account or a copy), and says what must be true before go-live.",
            "Handles the invoice feature honestly: a separate approval step with a person, a later phase, or both, instead of granting broad access to get it.",
            "Names the condition under which you would refuse the tool.",
        ],
        "coach": [
            {"hint": "What would you check about a stranger's tool before giving it your client's account?", "example": "Example: who wrote it, when it was last updated, what permission it asks for."},
            {"hint": "Compare what each one can touch.", "example": "Example: read-only cannot change an invoice by mistake."},
            {"hint": "Where do you try it first?", "example": "Example: a test account with made-up patients."},
            {"hint": "The clinic still wants invoices. How do you give them that safely?", "example": "Example: Hermes drafts the invoice, a person creates it."},
            {"hint": "Say what would make you say no outright.", "example": "Example: it needs full account access and nobody maintains it."},
        ],
        "minutes": 8,
    },
]

BY_ID = {item["id"]: item for item in SCENARIOS}
IDS = [item["id"] for item in SCENARIOS]


def grading_prompt(item: dict, answer: str) -> str:
    covers = "\n".join(f"{n}. {c}" for n, c in enumerate(item["covers"], start=1))
    return (
        "Grade a Field Academy judgment scenario. Stay in the learner's own Hermes; do not restart the exercise.\n\n"
        f"Scenario: {item['title']}\n{item['situation']}\n\nQuestion asked: {item['question']}\n\n"
        f"A strong answer does these things:\n{covers}\n\n"
        f"The learner's answer:\n---\n{answer}\n---\n\n"
        "There is no single right verdict. Two learners can decide differently and both score well. Score 0-100 on the reasoning: did they name the competing duties, "
        "weigh them, choose and say why, and say who decides and what would change their mind. Ignore style and length. "
        "An answer that only states a verdict, or restates the case, scores under 40. One that covers most of the above with one clear gap scores in the 70s. "
        f"One that covers all of it plainly scores 85 or better. The threshold to pass is {PASS_SCORE}.\n\n"
        f"Then call field_academy_grade_deployer with item_id \"scenario.{item['id']}\", score, missed (the numbers from the list above that the answer left out) and feedback. "
        "In the feedback, name what they did well, name the point they missed, and say what to add. Never offer to pass them anyway."
    )
