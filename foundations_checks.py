"""Live checks for Foundations: each reader reads the practice profile (hermes_read) and judges one thing.

A reader takes a context (the practice home, the learner's lab note, what was planted) and returns an outcome:
``passed``, ``title``, ``detail``, ``facts``, ``missing`` (each ``{id, what}``), ``evidence`` (``(kind, rel_path, text,
source_sha256)`` tuples; the text is scrubbed before it is kept) and ``readable``. A reader that can't read never
passes. Message text is read only to compare; only the matched excerpt is kept.

Every reader id here must have a fixture test in tests/test_foundations_checks.py (scripts/check_foundations.py
checks that).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import hermes_read, matching, plants, scrub

EXCERPT = 300


def clock_words(stamp) -> str:
    """A Unix time as "October 3, 2026, 10:42:05 UTC", the way the record states times. Empty when it can't be read."""
    from datetime import datetime, timezone

    try:
        moment = datetime.fromtimestamp(float(stamp), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return ""
    return f"{moment.strftime('%B')} {moment.day}, {moment.year}, {moment.strftime('%H:%M:%S')} UTC"


def make_evidence(kind, rel_path, text, source_sha256=""):
    """The one way evidence is made: the text is scrubbed and cut to EXCERPT characters here, before anything keeps
    or hashes it. foundations.py stores only evidence that is already in this form."""
    return (str(kind)[:40], str(rel_path)[:200], scrub.clip(text, EXCERPT), str(source_sha256 or "")[:64])


def clean_facts(facts) -> list:
    """Facts as kept and shown: every label and value scrubbed. A fact can quote what Hermes holds (a job's delivery
    place, an always-allow entry, a model name), so it gets the same scrubber as an excerpt."""
    out = []
    for fact in facts or []:
        if isinstance(fact, dict):
            out.append({k: scrub.scrub(v) if isinstance(v, str) else v for k, v in fact.items()})
        else:
            out.append(fact)
    return out


def outcome(passed, title, detail, facts=None, missing=None, evidence=None, readable=True):
    missing = [{k: scrub.scrub(v) if isinstance(v, str) else v for k, v in m.items()} if isinstance(m, dict) else m for m in (missing or [])]
    return {"passed": bool(passed), "title": scrub.scrub(title), "detail": scrub.scrub(detail), "facts": clean_facts(facts), "missing": missing,
            "evidence": [make_evidence(*item) for item in (evidence or [])], "readable": readable}


def cannot_read(what: str):
    return outcome(False, "Field Academy could not read this from the practice profile", what,
                   missing=[{"id": "unreadable", "what": what}], readable=False)


def _note(ctx) -> dict:
    return ctx.get("note") or {}


def _need_fact(ctx):
    note = _note(ctx)
    if not str(note.get("fact", "")).strip():
        return cannot_read("Write down the fact you asked Hermes to save, so Field Academy knows what to look for.")
    return None


def _excerpt_around(text: str, term: str, width: int = 300) -> str:
    low = text.lower()
    at = low.find(str(term or "").lower())
    if at < 0:
        return scrub.clip(text, width)
    start = max(0, at - width // 3)
    if start:
        # Start at a word, never inside one, and say that something came before.
        space = text.find(" ", start, at + 1)
        start = space + 1 if 0 <= space < at else start
        return scrub.clip("…" + text[start:], width)
    return scrub.clip(text, width)


# ------------------------------------------------------------------ memory --


def _memory_hit(ctx, files=("memory", "user")):
    mem = hermes_read.memory(ctx["home"])
    if not mem.get("readable"):
        return mem, None, None
    fact = _note(ctx).get("fact", "")
    for which in files:
        line = matching.holds(mem[which]["entries"], fact)
        if line:
            return mem, which, line
    return mem, None, None


def _fill_words(part) -> str:
    """"479 of 2,200 characters, 5 lines", with "1 line" for one (0.9 persona test)."""
    n = len(part["entries"])
    return f"{part['chars']:,} of {part['limit']:,} characters, {n} {'line' if n == 1 else 'lines'}"


def memory_line_matching(ctx):
    """The fact is in MEMORY.md or USER.md of the practice profile, as one line under 300 characters."""
    problem = _need_fact(ctx)
    if problem:
        return problem
    mem, which, line = _memory_hit(ctx)
    if not mem.get("readable"):
        return cannot_read(mem.get("why", "The memory files could not be read."))
    facts = [{"label": "MEMORY.md", "value": _fill_words(mem["memory"])}, {"label": "USER.md", "value": _fill_words(mem["user"])}]
    if not line:
        near, _ = matching.best_line(mem["memory"]["entries"] + mem["user"]["entries"], _note(ctx).get("fact", ""), max_len=10_000)
        what = "No line in the practice profile's memory files holds your fact."
        if near and len(near) > matching.MAX_LINE:
            what = f"A line holds your fact, but it is {len(near)} characters. Memory lines should be short: under {matching.MAX_LINE}."
        return outcome(False, "Your fact isn't in memory", what, facts, [{"id": "no_line", "what": what}])
    rel = mem[which]["rel_path"]
    return outcome(True, f"Your fact is in {Path(rel).name}", f"Found in {rel}: one line of {len(line)} characters.", facts,
                   evidence=[("memory", rel, line, mem[which]["sha256"])])


def memory_user_line(ctx):
    """Transfer: the second fact, about the learner, is in USER.md specifically."""
    problem = _need_fact(ctx)
    if problem:
        return problem
    mem, which, line = _memory_hit(ctx, files=("user", "memory"))
    if not mem.get("readable"):
        return cannot_read(mem.get("why", "The memory files could not be read."))
    if which == "user":
        return outcome(True, "The fact about you is in USER.md", f"Found in USER.md: {len(line)} characters.",
                       evidence=[("memory", "memories/USER.md", line, mem["user"]["sha256"])])
    if which == "memory":
        what = "The fact is in MEMORY.md. A fact about you belongs in USER.md."
        return outcome(False, "Saved, but in the other file", what, missing=[{"id": "wrong_file", "what": what}],
                       evidence=[("memory", "memories/MEMORY.md", line, mem["memory"]["sha256"])])
    what = "No line in USER.md holds the fact about you."
    return outcome(False, "The fact about you isn't in memory", what, missing=[{"id": "no_line", "what": what}])


# ---------------------------------------------------------------- sessions --


def _save_time(ctx, mem, which):
    """When the fact was saved: the memory tool call that carried the key term, else the memory file's time."""
    term = _note(ctx).get("key_term") or ""
    found = hermes_read.messages(ctx["home"])
    best = None
    for row in found.get("messages", []) if found.get("readable") else []:
        calls = row.get("tool_calls") or ""
        if row.get("role") == "assistant" and calls and '"memory"' in calls and matching.mentions(calls, term):
            stamp = row.get("timestamp")
            if isinstance(stamp, (int, float)) and (best is None or stamp < best):
                best = float(stamp)
    if best is not None:
        return best, "the memory call"
    mtime = mem[which].get("mtime") if which else None
    return (float(mtime), "the memory file's time") if mtime else (None, "")


def sessions_used_before_said(ctx):
    """A chat started after the save used the fact (its key term) before the learner mentioned it."""
    problem = _need_fact(ctx)
    if problem:
        return problem
    term = str(_note(ctx).get("key_term", "")).strip()
    if not term:
        return cannot_read("Name the key word of your fact (for example the software's name), so Field Academy can look for it.")
    mem, which, line = _memory_hit(ctx)
    if not mem.get("readable"):
        return cannot_read(mem.get("why", "The memory files could not be read."))
    if not line:
        what = "No line in memory holds the fact, so a new chat had nothing to use."
        return outcome(False, "No new chat used the fact", what, missing=[{"id": "not_saved", "what": what}])
    saved_at, how = _save_time(ctx, mem, which)
    listed = hermes_read.sessions(ctx["home"])
    if not listed.get("readable"):
        return cannot_read(listed.get("why", "The chat records could not be read."))
    later = [s for s in listed["sessions"] if isinstance(s.get("started_at"), (int, float)) and saved_at is not None and s["started_at"] > saved_at]
    # Times, not only the order: a stranger reading the record sees the save came first (0.9 persona test).
    facts = [{"label": "Saved at", "value": f"{clock_words(saved_at)}, from {how}" if saved_at is not None else "not found"},
             {"label": "Chats started after the save", "value": str(len(later))}]
    for session in later:
        msgs = hermes_read.messages(ctx["home"], session["id"])
        rows = msgs.get("messages", []) if msgs.get("readable") else []
        first_said = next((i for i, m in enumerate(rows) if m.get("role") == "user" and matching.mentions(m.get("content"), term)), None)
        first_used = next((i for i, m in enumerate(rows) if m.get("role") == "assistant" and matching.mentions(m.get("content"), term)), None)
        if first_used is not None and (first_said is None or first_used < first_said):
            text = _excerpt_around(str(rows[first_used].get("content") or ""), term)
            facts.append({"label": "The chat that used it started", "value": clock_words(session["started_at"])})
            return outcome(True, "A new chat used the fact on its own",
                           "In a chat that started after the save, Hermes used it before you mentioned it.", facts,
                           evidence=[("session", "state.db", text, "")])
    if not later:
        what = "No chat started after the save. Start a new chat (/new) and ask for real work that needs the fact."
    else:
        what = "No new chat used the fact before you mentioned it. Ask for work that needs it, without naming it."
    return outcome(False, "No new chat used the fact", what, facts, [{"id": "not_used", "what": what}])


# --------------------------------------------------------- staged and plant --


def _pending_words(item) -> str:
    return hermes_read.pending_words(item)


def pending_cleared(ctx):
    """No memory save is left waiting for approval."""
    found = hermes_read.pending(ctx["home"])
    if not found.get("readable"):
        return cannot_read("The approval queue could not be read.")
    waiting = found.get("memory", [])
    if waiting:
        what = f"{len(waiting)} memory {'save is' if len(waiting) == 1 else 'saves are'} still waiting for approval."
        return outcome(False, "Saves are waiting", what, missing=[{"id": "waiting", "what": what}],
                       evidence=[("pending", w["rel_path"], _pending_words(w), "") for w in waiting[:2]])
    return outcome(True, "Nothing is waiting for approval", "The memory approval queue is empty.")


def plant_fixed(ctx):
    """Every planted problem is fixed, and the fact is in place after the fix."""
    problem = _need_fact(ctx)
    if problem:
        return problem
    planted = ctx.get("planted") or {}
    if not planted:
        return cannot_read("Field Academy has no record of what was set up in this practice profile.")
    missing, facts, evidence = [], [], []
    for kind, details in sorted(planted.items()):
        seen = plants.detect(kind, ctx["home"], details)
        result = plants.verify(kind, ctx["home"], details, _note(ctx).get("fact", ""), _note(ctx))
        facts.extend(seen.get("facts", []))
        evidence.extend((k, rel, text, "") for k, rel, text in seen.get("evidence", [])[:2])
        if not result["fixed"]:
            missing.append({"id": f"plant:{kind}", "what": result["why"]})
    if missing:
        return outcome(False, "Something in the setup still needs fixing", missing[0]["what"], facts, missing, evidence)
    return outcome(True, "The setup problem is fixed", "What stopped the save is gone, and the fact is in memory.", facts, evidence=evidence)


def memory_seed_kept(ctx):
    """The protected notes the page listed are still in memory (shortened is fine), or the learner said why one went."""
    seed = ctx.get("seed_notes") or {}
    if not seed.get("notes"):
        return cannot_read("Field Academy has no record of the notes it put in the practice profile's memory.")
    mem = hermes_read.memory(ctx["home"])
    if not mem.get("readable"):
        return cannot_read(mem.get("why", "The memory files could not be read."))
    entries = mem["memory"]["entries"] + mem["user"]["entries"]
    states = [plants.note_state(entries, text) for text in seed["notes"]]
    keys = plants.key_notes(ctx["home"], seed, _note(ctx))
    facts = [{"label": "Notes Field Academy set up", "value": str(len(seed["notes"]))},
             {"label": "Still there as written", "value": str(states.count("kept"))},
             {"label": "Shortened", "value": str(states.count("shortened"))},
             {"label": "Gone", "value": str(states.count("removed"))}]
    if keys["ok"]:
        detail = ("Every note already in memory is still there, including the two the page asked you to keep." if not keys["gone"] else
                  "A note the page listed is gone, and you said why that was right.")
        return outcome(True, "The notes already in memory are still there", detail, facts)
    what = (f"A note the page listed is gone from memory: \"{keys['gone'][0]}\". Put it back and cut something "
            "else, or say which note went and why losing it was right.")
    return outcome(False, "A listed note is gone", what, facts, [{"id": "note_gone", "what": what}],
                   evidence=[("removed_note", "memories/MEMORY.md", keys["gone"][0], mem["memory"]["sha256"])])


def memory_one_off_decision(ctx):
    """Transfer: the learner decided whether a one-off detail earns a memory line, and memory matches that call."""
    note = _note(ctx)
    detail = str(note.get("one_off") or "").strip()
    if not detail or not isinstance(note.get("one_off_saved"), bool):
        return cannot_read("Write the one-off detail and whether you saved it or left it out.")
    mem = hermes_read.memory(ctx["home"])
    if not mem.get("readable"):
        return cannot_read(mem.get("why", "The memory files could not be read."))
    line = matching.holds(mem["memory"]["entries"] + mem["user"]["entries"], detail)
    if note["one_off_saved"]:
        if line:
            return outcome(True, "You saved it, and it's there", "The one-off detail is a line in memory, as you said.",
                           evidence=[("memory", "memories", line, "")])
        what = "You said you saved the one-off detail, but no memory line holds it."
        return outcome(False, "It isn't in memory", what, missing=[{"id": "not_saved", "what": what}])
    if line:
        what = "You said you left the one-off detail out, but a memory line holds it. Remove it, or say you saved it."
        return outcome(False, "It's in memory after all", what, missing=[{"id": "saved_anyway", "what": what}],
                       evidence=[("memory", "memories", line, "")])
    return outcome(True, "You left it out, and it's out", "No memory line holds the one-off detail, as you decided.")


# ------------------------------------------------------------------- skills --


def skills_procedure_not_memory(ctx):
    """Transfer: the weekly steps went into a skill, and memory holds no long copy of them."""
    note = _note(ctx)
    term = str(note.get("procedure_term") or note.get("key_term") or "").strip()
    if not term:
        return cannot_read("Name the weekly task, so Field Academy can look for its skill.")
    found = hermes_read.skills(ctx["home"])
    if not found.get("readable"):
        return cannot_read("The skills folder could not be read.")
    skill = next((s for s in found["skills"] if matching.mentions(s["name"].replace("-", " "), term) or matching.mentions(s["description"], term)
                  or matching.mentions(s["name"], term)), None)
    mem = hermes_read.memory(ctx["home"])
    long_lines = []
    if mem.get("readable"):
        for line in mem["memory"]["entries"] + mem["user"]["entries"]:
            steps = len(re.findall(r"(?m)(?:^|\s)(?:\d+[.)]|step \d+|then )", line.lower()))
            if matching.mentions(line, term) and (len(line) > 200 or steps >= 3):
                long_lines.append(line)
    if skill and not long_lines:
        return outcome(True, "The steps are a skill", f"Found the skill {skill['name']}, and memory holds no copy of the steps.",
                       evidence=[("skill", skill["rel_path"], f"{skill['name']}: {skill['description']}", skill["sha256"])])
    missing = []
    if not skill:
        missing.append({"id": "no_skill", "what": f"No skill names or describes {term!r}. A procedure belongs in a skill."})
    if long_lines:
        missing.append({"id": "in_memory", "what": "Memory still holds the steps. Move them to a skill and keep at most a short pointer."})
    return outcome(False, "The steps aren't where they belong", missing[0]["what"], missing=missing,
                   evidence=[("memory", "memories", line, "") for line in long_lines[:1]])


READERS = {
    "memory.line_matching": memory_line_matching,
    "memory.user_line": memory_user_line,
    "sessions.used_before_said": sessions_used_before_said,
    "pending.cleared": pending_cleared,
    "memory.seed_kept": memory_seed_kept,
    "memory.one_off_decision": memory_one_off_decision,
    "plant.fixed": plant_fixed,
    "skills.procedure_not_memory": skills_procedure_not_memory,
}
from . import foundations_checks_b as _checks_b  # noqa: E402  missions 7 to 11
READERS.update(_checks_b.READERS)


def run(reader_id: str, ctx: dict) -> dict:
    reader = READERS.get(reader_id)
    if reader is None:
        return cannot_read(f"Unknown check {reader_id}.")
    try:
        return reader(ctx)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return cannot_read(f"The check stopped on an error: {exc.__class__.__name__}.")


# Missions 1, 2, 4, 5 and 6 (0.9 M6, part A) register their readers here.
from . import foundations_checks_a as _checks_a  # noqa: E402

READERS.update(_checks_a.READERS)

# The capability missions (helper agents, toolsets) register their readers here.
from . import foundations_checks_c as _checks_c  # noqa: E402

READERS.update(_checks_c.READERS)

# The teaching missions on the Guide trail register their readers here.
from . import foundations_checks_t as _checks_t  # noqa: E402

READERS.update(_checks_t.READERS)
