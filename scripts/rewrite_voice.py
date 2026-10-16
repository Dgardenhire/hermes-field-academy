#!/usr/bin/env python3
"""Rewrite curriculum prose into the register the sources actually teach in.

Works on the AST, not on source text: each string literal in curriculum.py whose
VALUE matches an old string is replaced by its new value, located by position and
re-emitted with repr(). That survives line wrapping, quote style, and implicit
concatenation, and it fails loudly if any old string is not found.

Voice rules: docs/curriculum-voice.md. Read that before editing this map.

Usage:  python scripts/rewrite_voice.py [--check]
        --check   report which entries are already applied, change nothing
"""

import ast
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parents[1] / "curriculum.py"

# old -> new. One entry per string literal. Keys must match the file exactly.
MAP: dict[str, str] = {
    # ── operator.runtime ────────────────────────────────────────────────────
    "The window is not the machine. Your prompts land somewhere, and that somewhere has a name.":
        "Your prompts run on a machine that has a name. Here is how to find out which one, so you can tell what actually broke.",
    "Four names, four different things":
        "Desktop, session, profile, gateway",
    "Desktop is a window. A session is one conversation inside it. A profile is a home directory, a set of credentials, and a memory of its own. A gateway is the long-running process that keeps scheduled work and messaging alive after you close the window. When something silently does not happen, the question is almost always which of the four owns it. Most people answer that question wrong the first time, because the window stays open and looks healthy while the gateway behind it is dead.":
        "Four things get called Hermes and they are not the same thing. Desktop is the window you click in. A session is one conversation. A profile is a home directory with its own credentials and its own memory. The gateway is the process that keeps scheduled jobs and messaging running after you close the window. When something silently does not happen, the answer is almost always one of those four. Check the window last: it stays open and looks fine while the gateway behind it is dead.",
    "The vocabulary to ask 'which one owns this?'":
        "Four names, and which one to check first.",
    "that the window being open proves nothing, because the window is not the machine":
        "that an open window tells you nothing about whether scheduled work ran",
    "that a scheduled job needs a live gateway process, which is separate from the window":
        "that a scheduled job needs a live gateway process, which runs separately from the window",
    "that the job also belongs to a specific profile with its own home and credentials":
        "that the job also belongs to one profile, with its own home directory and credentials",
    "how you would actually confirm it, rather than guessing":
        "how you would actually confirm it instead of guessing",

    # ── operator.learning ───────────────────────────────────────────────────
    "Memory, session history, and skills solve three different problems, and mixing them up is why the agent forgets.":
        "Memory, session history, and skills each hold something different. Put a thing in the wrong one and the agent will forget it.",
    "Three kinds of remembering":
        "Where a fact goes, and where a procedure goes",
    "Memory is a short list injected into every conversation, so it stays small and holds standing facts about you. Session history is the archive you search when you need to find what was decided last month. A skill is a written procedure the agent loads when the description matches the job. The trap is putting a procedure in memory: it is the wrong shape, it costs tokens in every conversation forever, and it will fight with whatever you say next. Procedures belong in skills. Facts belong in memory. Everything else belongs in history.":
        "Memory is a short list of facts that gets added to every conversation you have, which is why it stays small. Session history is the archive you search when you want to find what you decided last month. A skill is a written procedure that Hermes loads when its description matches what you asked for. The mistake to avoid is putting a procedure in memory. It is the wrong shape, it costs you tokens in every conversation from then on, and it will argue with whatever you say next. So a procedure goes in a skill. A standing fact about how you work goes in memory. Anything you might want to look up later can stay in history, where you search for it.",
    "The rule that decides where a thing goes.":
        "A rule for deciding which of the three a thing belongs in.",

    # ── operator.automation ─────────────────────────────────────────────────
    "Write for a stranger with no context":
        "A scheduled job starts with nothing",
    "When you type in a session, the agent has the whole conversation. A scheduled job has none of it: no thread, no files you had open, no memory of yesterday's decision. So the prompt has to name the working directory, the inputs, what success looks like, where the result goes, and what to do when it fails. A job that cannot say those five things will appear to work for a week and then quietly deliver nothing.":
        "When you type in a session, the agent has the whole conversation in front of it. A scheduled job has none of that: no thread, no files you had open, no memory of what you decided yesterday. So the prompt has to say where to work, what to read, what a good result looks like, where to put it, and what to do when it fails. Miss one of those five and the job will look fine for a week, then quietly deliver nothing.",
    "A prompt template for unattended work.":
        "A prompt template you can reuse for unattended work.",

    # ── operator.desktop ────────────────────────────────────────────────────
    "Sessions, projects, artifacts, the terminal, and the command palette are one surface, and they persist differently.":
        "Panes, sessions, and projects behave differently when you close the window. Knowing which is which covers most of what surprises people about the app.",
    "What survives, and what does not":
        "What happens when you close something",
    "Closing a pane hides it; it does not stop it. Terminals and live tools stay alive when hidden, which is why a long build keeps going while you read something else. A session is durable and survives restarts. A project is a label that groups sessions pointing at the same working directory. The command palette is the fastest way to reach anything, including things with no visible button. Learn those four facts and the window stops feeling accidental.":
        "Closing a pane hides it. It does not stop it, which is why a long build keeps running while you go and read something else. A session is saved and comes back after a restart. A project is a label that groups sessions working in the same folder. The command palette reaches everything in the app, including the things that have no button on screen. Once you know those four, the window stops doing things you did not expect.",
    "A map of what persists where.":
        "A note on what persists where.",

    # ── integrator.discovery ────────────────────────────────────────────────
    "Nobody buys an agent. They buy one workflow that stopped wasting somebody's afternoon.":
        "A client asks for an AI agent. What they actually want is one workflow that stopped wasting somebody's afternoon. Find that workflow before you quote anything.",
    "Which work repeats? Who owns the result? Which systems does it touch? What does a good outcome look like, in numbers? What happens when it is wrong? Who signs? Ask those six and the scope writes itself. Skip them and you will quote an engagement you cannot deliver, on a workflow nobody owns, with an acceptance test nobody agreed to. The scope's most valuable line is the exclusion list, because that is the sentence you will read out loud in month two.":
        "Ask six questions and the scope writes itself: which work repeats, who owns the result, which systems it touches, what a good outcome looks like in numbers, what happens when it is wrong, and who signs. Skip them and you will quote an engagement you cannot deliver, on a workflow nobody owns, with an acceptance test nobody agreed to. Write the exclusion list first. It is the part you will read out loud in month two, when the client asks for the thing you deliberately left out.",
    "that the exclusion list is the line you read out loud in month two":
        "that the exclusion list is what you point at in month two, when they ask for the thing you left out",

    # ── integrator.deploy ───────────────────────────────────────────────────
    "Ask four questions of every topology: whose machine is it, whose secrets live on it, who applies updates, and what happens at 2am when it dies? A laptop is cheap and dies when the lid closes. A VPS costs money every month and needs someone to patch it. Cloud removes the machine and keeps the account. None of these is correct in the abstract; the wrong answer is choosing one without being able to say who answers those four questions.":
        "Ask four questions of every option. Whose machine is it. Whose secrets live on it. Who applies the updates. What happens at 2am when it dies. A laptop is cheap, and it dies when somebody closes the lid. A VPS costs money every month, and it needs somebody to patch it. Cloud takes the machine away and leaves you the account, the bill, and the uptime page. Any of the three can be right, and you cannot pick one until you can answer those four questions.",
    "A topology decision with a named owner.":
        "A written answer to the four questions, with a name against each.",

    # ── integrator.connect ──────────────────────────────────────────────────
    "Capability is authority":
        "What you connect, you are responsible for",
    "The moment Hermes can send email, it can send the wrong email. The moment it can read a shared drive, it can read everything on that drive. So the useful question is not 'can we connect this' but 'what is the smallest permission that still does the job, and who approves the outbound action?' Write the answer down before you connect anything. An approval gate you have never tested is not a control, it is a hope.":
        "The moment Hermes can send email, it can send the wrong email. The moment it can read a shared drive, it can read everything on that drive. So do not start with whether you can connect it. Start with the smallest permission that still does the job, and who approves the outbound action. Write that down before you connect anything, then trigger the approval gate once. An approval gate nobody has ever tripped is an assumption, and you will find out it does not work at the worst possible moment.",
    "A least-privilege rule you can state in one sentence.":
        "One sentence naming the smallest permission that still does the job.",
    "that connecting a capability is granting an authority, and the two are the same thing":
        "that connecting a capability grants an authority to act, and the two arrive together",

    # ── integrator.handoff ──────────────────────────────────────────────────
    "The runbook answers: what runs where, who owns each part, how to start and stop it, how to read the logs, how to restore from backup, what it deliberately does not do, and who to call when it breaks. The test is not whether it is complete. The test is whether someone who has never seen the system can complete one routine and one recovery with the document alone. If they cannot, you wrote an installation note, not a runbook.":
        "The runbook answers: what runs where, who owns each part, how to start and stop it, how to read the logs, how to restore from a backup, what it deliberately does not do, and who to call when it breaks. Judge it by one thing. Can somebody who has never seen the system finish one routine task and one recovery using the document alone? Watch them try it. If they get stuck, what you have is an installation note rather than a runbook.",

    # ── architect.estate ────────────────────────────────────────────────────
    "Draw the whole estate":
        "Draw every box and put a name on it",
    "Boundaries first, cleverness later":
        "Draw the boxes before you add anything",
    "Organisations fail at the seams: two teams sharing one profile, one gateway serving a regulated workflow and a marketing experiment, a bot with more tool access than the human who asked for it. Draw the picture before you add anything. The picture has organisations, gateways, profiles, bots, workspaces, models, and data, and every box needs a name and a person. If you cannot say who is accountable for a box, that box is the incident you have not had yet.":
        "Companies get into trouble at the boundaries. Two teams sharing one profile. One gateway serving a regulated workflow and a marketing experiment. A bot with more tool access than the person who asked for it. Draw the picture before you add anything to it. The picture has organisations, gateways, profiles, bots, workspaces, models, and data, and every box on it needs a name and a person. If you cannot say who is accountable for a box, write that down too. It is the first thing to fix.",
    "An estate diagram with owners on every box.":
        "A diagram of every box, with a person's name against each.",
    "Read the estate you already have":
        "Start with the install you already have",
    "Explain how you draw the estate":
        "Explain which boxes you would draw",
    "that an unowned box is the incident you have not had yet":
        "how you would spot a box with nobody accountable for it",
    "Prove the estate is visible":
        "Prove the boxes are visible",
    "A verified estate inventory.":
        "A verified list of what is actually registered.",

    # ── architect.governance ────────────────────────────────────────────────
    "Governance is not a policy document. It is the answer you give when someone asks why that action was allowed.":
        "Governance is the answer you give when somebody asks why that action was allowed. Write those answers down before anybody asks.",
    "Data is an instruction, not a document":
        "A document the agent reads is an instruction",
    "Once Hermes reads a supplier PDF, that PDF's contents are input to a system with tools. A sentence buried in an approved document can redirect an outbound message, and nothing about the document looked suspicious. This is not a model flaw you can patch away; it is a boundary problem. So the controls that matter are external: what the agent may reach, what requires a human, and what gets logged whether anyone asked or not.":
        "Once Hermes reads a supplier PDF, the contents of that PDF are input to a system that has tools. A sentence buried in an approved document can redirect an outbound message, and nothing about the document looked suspicious. You cannot patch this away, because the document was allowed through in the first place. So put the controls outside the model: what the agent may reach, what has to wait for a human, and what gets logged whether anybody asked or not.",
    "A documented authority boundary.":
        "A written note on what the agent may reach.",
    "that this is a boundary problem, not a model defect you can patch away":
        "that the document was allowed through, so the fix sits outside the model",

    # ── architect.operations ────────────────────────────────────────────────
    "Chat is for thinking. Delegation is for a task. Kanban is for work that outlives the conversation.":
        "A conversation, a subagent, and a kanban card last for very different lengths of time. Pick the one that matches the work.",
    "Pick the coordination shape":
        "Match the mechanism to how long the work lasts",
    "Delegating to a subagent is cheap and disappears when the turn ends. A bot is a named collaborator with its own profile and memory. Kanban is durable: the card survives the session, the machine, and the week, and it carries its own definition of done and its own review gate. Teams get this wrong by running a week-long process inside one chat and calling it orchestration. Match the shape to the duration.":
        "Delegating to a subagent is cheap, and the subagent disappears when the turn ends. A bot is a named collaborator with its own profile and its own memory. A kanban card is durable: it survives the session, the machine, and the week, and it carries its own definition of done and its own review gate. The usual mistake is running a two-week process inside one chat and calling it orchestration. Work that lasts two weeks needs to live somewhere that lasts two weeks.",
    "that the deciding property is durability, and that a board task carries its own definition of done and its own review gate":
        "that what decides it is how long the work lasts, and that a board task carries its own definition of done and its own review gate",

    # ── architect.reliability ───────────────────────────────────────────────
    "Value claims fail when they compare a new workflow against nothing. Measure the old one: who did it, how long it took, how often it was wrong, and what the correction cost. Then measure the new one including review and repair. The honest number is usually smaller than the pitch and much harder to argue with. Pair it with one recovery you have genuinely executed, and you have an architecture defence that survives a CFO.":
        "Value claims fall apart when they compare a new workflow against nothing. Measure the old one: who did it, how long it took, how often it was wrong, and what fixing the mistake cost. Then measure the new one, including the review and the repair. The honest number is usually smaller than the pitch, and much harder to argue with. Pair it with a recovery you have actually executed, and you can defend the whole thing in a budget meeting.",
    "A value model with a real baseline.":
        "The old workflow's numbers, next to the new workflow's.",
    "that value claims built against nothing are the ones a CFO takes apart":
        "that a value claim with no baseline is the one that gets taken apart in a budget meeting",

    # ── ambassador.story ────────────────────────────────────────────────────
    "Credibility is in the limits":
        "Name the limits before the ambitions",
    "The strongest introduction names what the product does, where it runs, what it needs to work, and what it will not do. That last part is the one that earns the meeting, because every other vendor skipped it. Say plainly that Hermes is open source, that it is maintained by Nous Research, that the teaching comes from named people in the community, and that a deployment is a system someone has to own. Ambition without a limit statement reads as a pitch.":
        "The strongest introduction covers four things: what the product does, where it runs, what it takes to operate, and what it will not do. The fourth one earns the meeting, because every other vendor skipped it. Say plainly that Hermes is open source, that Nous Research maintains it, that the teaching comes from named people in the community, and that a deployment is a system somebody has to own. Leave the limits out and it sounds like a pitch.",

    # ── ambassador.qualify ──────────────────────────────────────────────────
    "Curiosity is not a pipeline. One repeated workflow with a named owner and a buyer is.":
        "A repeated workflow, a named owner, and somebody who can approve spending. That is a pipeline.",
    "A real opportunity has a repeated workflow, an owner who feels the pain, an authority who can approve spending, and a first step small enough to sell. Missing any one of the four means it is a conversation, not a deal, and treating it as a deal is how a partner burns a quarter on a friendly prospect. Write the decision down with the evidence behind it. The record is also what makes the technical handoff honest later.":
        "A real opportunity has four parts: a workflow that repeats, an owner who feels the pain, somebody who can approve spending, and a first step small enough to sell. Miss any one of them and you have a conversation rather than a deal. Write the decision down with the evidence behind it, because that record is also what makes the later handoff honest.",
    "that missing most of these makes it a conversation to nurture, not a deal to chase, and that treating it as a deal burns a quarter":
        "that missing most of the four makes it a conversation to nurture rather than a deal to chase",

    # ── ambassador.handoff ──────────────────────────────────────────────────
    "A handoff has four sections: what we know, what we promised, what still needs validating, and who owns each next step. Collapsing the middle two is the classic failure, because a promise you made casually becomes a requirement the engineer never agreed to. Write it down while you still remember which sentence was which, and send it before the joint call rather than after.":
        "A handoff has four sections: what we know, what we promised, what still needs validating, and who owns each next step. Keep the middle two apart. Merge them and a promise you made casually turns into a requirement the engineer never agreed to. Write it down while you still remember which sentence was which, and send it before the joint call rather than after.",

    # ── caught by scripts/check_voice.py on the rewritten copy ──────────────
    # The first pass introduced these two. The checker earned its keep. They are
    # sub-sentences of larger literals, so they live in SUBSTR below, not here.
}

# In-place fixes for strings too long to key by value (model prompts). Applied to
# the raw source, so they must be unambiguous.
SUBSTR: dict[str, str] = {
    "what the authority boundary is": "what the agent may reach",
    "authority boundary": "what the agent may reach",
    "Four things get called Hermes and they are not the same thing.":
        "Four different things get called Hermes.",
    "Ask four questions of every option. Whose machine is it. Whose secrets live on it. Who applies the updates. What happens at 2am when it dies.":
        "Ask four questions of every option: whose machine it is, whose secrets live on it, who applies the updates, and what happens at 2am when it dies.",
    # A definitional sequence of four short sentences is still a rhythm. Fold it
    # into one sentence that lists the four, the way Tony lists what a skill is.
    "Four different things get called Hermes. Desktop is the window you click in. A session is one conversation. A profile is a home directory with its own credentials and its own memory.":
        "Four different things get called Hermes. Desktop is the window you click in, a session is one conversation, a profile is a home directory with its own credentials and its own memory, and the gateway is the process that keeps scheduled jobs and messaging running after you close the window.",
}


def literal_spans(source: str) -> list[tuple[int, int, str]]:
    """(start, end, value) for every string literal in the module."""
    lines = source.splitlines(keepends=True)
    starts: list[int] = []
    total = 0
    for line in lines:
        starts.append(total)
        total += len(line)

    spans: list[tuple[int, int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            end_lineno = node.end_lineno or node.lineno
            start = starts[node.lineno - 1] + node.col_offset
            end = starts[end_lineno - 1] + node.end_col_offset
            spans.append((start, end, node.value))
    return spans


def variants(text: str) -> list[str]:
    """The text, plus every form the needle pass could produce from it.

    An entry whose new value contains a needle is legitimately mutated by the
    later pass, so checking the raw value alone reports a false "missing" on the
    second run. Compare against the mutated forms too.
    """
    forms = [text]
    current = text
    # To a fixed point: one needle can expose the text another needle matches.
    for _ in range(len(SUBSTR) + 1):
        nxt = current
        for needle, replacement in SUBSTR.items():
            if needle in nxt:
                nxt = nxt.replace(needle, replacement)
        if nxt == current:
            break
        forms.append(nxt)
        current = nxt
    return forms


def main(argv: list[str] | None = None) -> int:
    check_only = "--check" in (argv or sys.argv[1:])
    source = SRC.read_text(encoding="utf-8")

    spans = literal_spans(source)
    present = {value for _, _, value in spans}
    # Idempotent: an entry is satisfied if the file already carries the old text,
    # the new text, or the new text as the needle pass would leave it.
    missing = sorted(
        old for old in MAP
        if not any(form in present for form in variants(old) + variants(MAP[old]))
    )

    if missing:
        print(f"FAIL: {len(missing)} entry(ies) matched neither old nor new text in {SRC.name}:", file=sys.stderr)
        for old in missing:
            print(f"  - {old[:100]}", file=sys.stderr)
        return 1

    if check_only:
        already = sorted(new for old, new in MAP.items() if new in present)
        pending = sum(source.count(needle) for needle in SUBSTR)
        print(f"{len(MAP)} entries; {len(already)} already applied; {pending} in-place fix(es) pending")
        return 0

    edits: list[tuple[int, int, str]] = []
    for start, end, value in spans:
        if value in MAP:
            edits.append((start, end, repr(MAP[value])))

    # Right to left, so earlier offsets stay valid.
    out = source
    for start, end, replacement in sorted(edits, key=lambda e: e[0], reverse=True):
        out = out[:start] + replacement + out[end:]

    # Validate the literal pass BEFORE any needle runs: a needle may legitimately
    # rewrite part of a value this pass just wrote, so checking afterwards would
    # report a false failure.
    new_values = {value for _, _, value in literal_spans(out)}
    unwritten = [
        new for new in MAP.values()
        if not any(form in new_values for form in variants(new))
    ]
    if unwritten:
        print(f"FAIL: {len(unwritten)} new string(s) missing after the literal pass", file=sys.stderr)
        for new in unwritten[:5]:
            print(f"  - {new[:100]}", file=sys.stderr)
        return 1

    # Needle fixes LAST, so an exact-value entry always wins over a substring
    # rule that would otherwise mangle it.
    substr_hits = 0
    for needle, replacement in SUBSTR.items():
        if needle in out:
            substr_hits += out.count(needle)
            out = out.replace(needle, replacement)

    # Prove it before writing: the module must still parse, and no needle survives.
    try:
        ast.parse(out)
    except SyntaxError as exc:
        print(f"FAIL: rewrite produced invalid Python: {exc}", file=sys.stderr)
        return 1
    leftover = [needle for needle in SUBSTR if needle in out]
    if leftover:
        print(f"FAIL: {len(leftover)} needle(s) survived the rewrite", file=sys.stderr)
        for needle in leftover:
            print(f"  - {needle[:100]}", file=sys.stderr)
        return 1

    SRC.write_text(out, encoding="utf-8")
    print(f"rewrote {len(edits)} string literal(s) in {SRC.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
