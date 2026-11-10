"""Live checks for the teaching missions on the Guide trail: set Hermes up for someone (f.teach-profile), write them a
walkthrough (f.teach-walkthrough), and judge their work from their Field Record (f.teach-review). Same contract as
foundations_checks.py. A reader that can't read never passes.

Every reader id here has a fixture test whose docstring is the id (tests/test_foundations_checks_t.py).
"""

from __future__ import annotations

import re

from . import foundations_checks as fc
from . import hermes_read, hermes_read_a, hermes_read_b, plants_t
from .foundations_checks_a import _calls
from .foundations_checks_c import toolset_settings


def _note(ctx) -> dict:
    return ctx.get("note") or {}


def _setup(ctx) -> dict:
    return ctx.get("setup") or {}


def _person(ctx) -> dict:
    return _setup(ctx).get("person") or {}


def _sessions(home) -> list:
    found = hermes_read.sessions(home)
    return [s for s in found.get("sessions", []) if found.get("readable") and s.get("source") != "subagent"]


def _rows(home, sid) -> list:
    return hermes_read.messages(home, sid).get("messages", [])


def _has_all(text, words) -> bool:
    low = str(text or "").lower()
    return all(str(w).lower() in low for w in words)


# ------------------------------------------------------------------ profile --


def teach_soul_for_them(ctx):
    """The practice profile's SOUL.md says who Hermes works for, and keeps the person's one rule."""
    person = _person(ctx)
    if not person:
        return fc.cannot_read("Field Academy has no record of the person this profile is for.")
    found = hermes_read_a.soul(ctx["home"])
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "SOUL.md could not be read."))
    text = found.get("text", "")
    missing = []
    if person["first"].lower() not in text.lower():
        missing.append({"id": "who", "what": f"SOUL.md doesn't say who Hermes works for. Name {person['first']} and the work."})
    if not _has_all(text, person["never_words"]):
        missing.append({"id": "rule", "what": f"SOUL.md doesn't keep {person['first']}'s rule: \"{person['never']}\"."})
    facts = [{"label": "SOUL.md", "value": f"{len(text)} characters"}]
    if missing:
        return fc.outcome(False, "SOUL.md isn't written for them yet", missing[0]["what"], facts, missing,
                          evidence=[("soul", "SOUL.md", text[:300], found.get("sha256", ""))] if text else None)
    return fc.outcome(True, f"SOUL.md is written for {person['first']}", "It names them and keeps their rule.", facts,
                      evidence=[("soul", "SOUL.md", text[:300], found.get("sha256", ""))])


def teach_memory_for_them(ctx):
    """The one thing Hermes should always know about their work is a line in the profile's memory."""
    person = _person(ctx)
    if not person:
        return fc.cannot_read("Field Academy has no record of the person this profile is for.")
    found = hermes_read.memory(ctx["home"])
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The memory file could not be read."))
    lines = [e for e in found.get("memory", {}).get("entries", []) if _has_all(e, person["fact_words"])]
    facts = [{"label": "Memory lines", "value": str(len(found.get("memory", {}).get("entries", [])))}]
    if not lines:
        what = f"The memory file has no line saying \"{person['fact']}\". Ask Hermes to remember it, then check the file."
        return fc.outcome(False, "Their fact isn't in memory", what, facts, [{"id": "no_fact", "what": what}])
    return fc.outcome(True, "Their fact is in memory", "Field Academy found it in MEMORY.md.", facts,
                      evidence=[("memory", "memories/MEMORY.md", lines[0], "")])


def teach_safe_for_them(ctx):
    """Approvals are on and the terminal toolset is off: they asked for no programs, and Hermes still checks before
    a risky change."""
    settings = hermes_read_b.settings(ctx["home"])
    tools = toolset_settings(ctx["home"])
    if not settings.get("readable") or not tools.get("readable"):
        return fc.cannot_read("The practice profile's settings could not be read.")
    mode = settings.get("approvals_mode")
    on = tools.get("on")
    terminal_on = ("terminal" in on) if on is not None else "terminal" not in tools.get("disabled", [])
    facts = [{"label": "Approvals", "value": str(mode or "smart (default)")},
             {"label": "Terminal toolset", "value": "on" if terminal_on else "off"}]
    if mode == "off":
        what = "Approvals are off, so nothing checks with them before a risky command."
        return fc.outcome(False, "Approvals are off", what, facts, [{"id": "approvals", "what": what}])
    if terminal_on:
        what = "The terminal toolset is on, and they asked for Hermes not to run programs. Switch it off in the Tools tab."
        return fc.outcome(False, "Hermes can still run programs", what, facts, [{"id": "terminal", "what": what}])
    return fc.outcome(True, "Safe for them", "Approvals are on and the terminal toolset is off.", facts,
                      evidence=[("setting", "config.yaml", f"approvals.mode: {mode or 'smart'}", "")])


def teach_first_chat_knows(ctx):
    """A new chat, after your last change to SOUL.md and memory, answered as their Hermes without being told who
    they are: the reply names them or their work and the message didn't."""
    person = _person(ctx)
    if not person:
        return fc.cannot_read("Field Academy has no record of the person this profile is for.")
    soul = hermes_read_a.soul(ctx["home"])
    mem = hermes_read.memory(ctx["home"])
    since = max(soul.get("mtime") or 0, (mem.get("memory") or {}).get("mtime") or 0)
    later = [s for s in _sessions(ctx["home"]) if isinstance(s.get("started_at"), (int, float)) and s["started_at"] >= since]
    names = (person["first"].lower(), person["word"].lower())
    for session in reversed(later):
        rows = _rows(ctx["home"], session["id"])
        said = " ".join(str(r.get("content") or "") for r in rows if r.get("role") == "user").lower()
        reply = " ".join(str(r.get("content") or "") for r in rows if r.get("role") == "assistant").lower()
        if any(n in said for n in names) or not reply:
            continue
        if any(n in reply for n in names):
            return fc.outcome(True, "A new chat knew who it works for", "The reply named them or their work, and your message didn't.",
                              [{"label": "Chats since your last change", "value": str(len(later))}],
                              evidence=[("session", "state.db", reply[:300], "")])
    what = (f"No new chat since your last change answers as {person['first']}'s Hermes without being told. Open a new practice "
            "chat and ask: \"Who do you work for, and what should you never do?\"")
    return fc.outcome(False, "Not shown in a new chat yet", what, [{"label": "Chats since your last change", "value": str(len(later))}],
                      [{"id": "no_chat", "what": what}])


def teach_profile_reading(ctx):
    """Transfer: the learner read someone's half-done setup and said what it would do for the person."""
    note = _note(ctx)
    if not str(note.get("t_change") or "").strip():
        return fc.cannot_read("Answer each question and say what you'd change.")
    missing = []
    if str(note.get("t_knows") or "").strip().lower() != "no":
        missing.append({"id": "knows", "what": "The rule is in a chat, not SOUL.md or memory. Does a new chat start with it?"})
    if str(note.get("t_asks") or "").strip().lower() != "no":
        missing.append({"id": "asks", "what": "Approvals are off. Does anything check with them before a risky command?"})
    if missing:
        return fc.outcome(False, "The setup reads differently", missing[0]["what"], [], missing)
    return fc.outcome(True, "You read the setup right", "A new chat doesn't know the rule, and nothing asks first.", [])


# -------------------------------------------------------------- walkthrough --


def _walkthrough(ctx):
    files = hermes_read_b.folder_files(ctx["home"])
    entry = next((f for f in files.get("files", []) if f["rel"] == "walkthrough.md"), None)
    return entry, plants_t.walkthrough_text(ctx["home"])


SKILL_NAME = re.compile(r"\bacademy-[a-z0-9][a-z0-9-]*[a-z0-9]\b")


def walkthrough_names_real(ctx):
    """walkthrough.md names the skill the profile really has, and no skill it doesn't."""
    entry, text = _walkthrough(ctx)
    if entry is None:
        what = "No walkthrough.md in the practice folder yet."
        return fc.outcome(False, "No walkthrough yet", what, [], [{"id": "none", "what": what}])
    found = hermes_read.skills(ctx["home"])
    if not found.get("readable"):
        return fc.cannot_read("The practice profile's skills could not be read.")
    have = {s["name"] for s in found["skills"]}
    named = {n for n in SKILL_NAME.findall(text.lower()) if not n.startswith('academy-practice')}  # the profile's name isn't a skill
    real = _setup(ctx).get("skill", plants_t.SKILL)
    facts = [{"label": "Skills the walkthrough names", "value": ", ".join(sorted(named)) or "none"},
             {"label": "Skills the profile has", "value": ", ".join(sorted(have)) or "none"}]
    ghost = sorted(named - have)
    if ghost:
        what = f"The walkthrough names {ghost[0]}, which the profile doesn't have."
        return fc.outcome(False, "It names a skill that isn't there", what, facts, [{"id": "ghost", "what": what}])
    if real not in named:
        what = f"The walkthrough never names {real}, the skill that does the job. Give its exact name."
        return fc.outcome(False, "The real skill isn't named", what, facts, [{"id": "unnamed", "what": what}])
    return fc.outcome(True, "It names the real skill", f"{real} is named, exactly, and nothing that isn't there.", facts,
                      evidence=[("practice_file", f"{hermes_read_b.FOLDER}/walkthrough.md", text[:300], entry["sha256"])])


CHECK_VERB = re.compile(r"\b(check|open|look|count|compare|make sure)\b", re.I)


def walkthrough_has_check(ctx):
    """A step tells them where the result lands and how to check it."""
    entry, text = _walkthrough(ctx)
    if entry is None:
        return fc.cannot_read("Write walkthrough.md in the practice folder first.")
    output = _setup(ctx).get("output", plants_t.OUTPUT)
    lines = [ln for ln in text.splitlines() if output.lower() in ln.lower() and CHECK_VERB.search(ln)]
    if not lines:
        what = f"No step says to open {output} and check it. A walkthrough ends with how they know it worked."
        return fc.outcome(False, "No check step", what, [], [{"id": "no_check", "what": what}])
    return fc.outcome(True, "It ends with a check", "A step names the result file and how to check it.", [],
                      evidence=[("practice_file", f"{hermes_read_b.FOLDER}/walkthrough.md", lines[0][:300], entry["sha256"])])


def walkthrough_tested(ctx):
    """After the walkthrough was written, a chat followed it: the skill was used and the result file was written
    again."""
    entry, _ = _walkthrough(ctx)
    if entry is None:
        return fc.cannot_read("Write walkthrough.md in the practice folder first.")
    skill = _setup(ctx).get("skill", plants_t.SKILL)
    output = _setup(ctx).get("output", plants_t.OUTPUT)
    files = hermes_read_b.folder_files(ctx["home"])
    out = next((f for f in files.get("files", []) if f["rel"] == output), None)
    later = [s for s in _sessions(ctx["home"]) if isinstance(s.get("started_at"), (int, float)) and s["started_at"] >= entry["mtime"]]
    for session in later:
        rows = _rows(ctx["home"], session["id"])
        used = any(skill in str(r.get("content") or "") for r in rows if r.get("role") == "user") or any(
            skill in " ".join(str(v) for v in c["args"].values()) for r in rows if r.get("role") == "assistant" for c in _calls(r))
        if used and out and out["mtime"] >= session["started_at"]:
            return fc.outcome(True, "You followed it and it worked", f"A chat after the walkthrough used {skill} and wrote {output}.",
                              [{"label": "Chats since the walkthrough", "value": str(len(later))}],
                              evidence=[("practice_file", f"{hermes_read_b.FOLDER}/{output}", (hermes_read_b.folder_text(ctx["home"], output, 4096) or "")[:300], out["sha256"])])
    what = (f"No chat after you wrote the walkthrough follows it to the end. Open a new practice chat, do exactly what step 2 "
            f"says, and check {output} the way the last step says.")
    return fc.outcome(False, "Not tested yet", what, [{"label": "Chats since the walkthrough", "value": str(len(later))}],
                      [{"id": "untested", "what": what}])


def walkthrough_reading(ctx):
    """Transfer: the learner judged someone else's walkthrough line by line."""
    note = _note(ctx)
    if not str(note.get("t_change") or "").strip():
        return fc.cannot_read("Answer each question and say what you'd change.")
    missing = []
    if str(note.get("t_stranger") or "").strip().lower() != "no":
        missing.append({"id": "stranger", "what": "\"Use the usual skill\" names nothing. Could someone new follow it?"})
    if str(note.get("t_done") or "").strip().lower() != "no":
        missing.append({"id": "done", "what": "Does any step say how they'd know it worked?"})
    if missing:
        return fc.outcome(False, "The walkthrough reads differently", missing[0]["what"], [], missing)
    return fc.outcome(True, "You read the walkthrough right", "Nothing in it is named, and nothing says how to check.", [])


# ------------------------------------------------------------------ review --


def _review(ctx):
    files = hermes_read_b.folder_files(ctx["home"])
    entry = next((f for f in files.get("files", []) if f["rel"] == "review.md"), None)
    return entry, plants_t.review_text(ctx["home"])


def review_ran_check(ctx):
    """Hermes ran the fingerprint check on their record folder: a tool call naming MANIFEST.sha256."""
    since = hermes_read_b.iso_epoch(str((ctx.get("row") or {}).get("planted_at") or "")) or 0
    for session in _sessions(ctx["home"]):
        if not isinstance(session.get("started_at"), (int, float)) or session["started_at"] < since:
            continue
        for row in _rows(ctx["home"], session["id"]):
            if row.get("role") != "assistant":
                continue
            for call in _calls(row):
                text = " ".join(str(v) for v in call["args"].values())
                if "MANIFEST.sha256" in text or ("shasum" in text and plants_t.RECORD_DIR in text):
                    return fc.outcome(True, "The fingerprints were checked", "A chat ran the check on their record folder.", [],
                                      evidence=[("tool_call", "state.db", f"{call['name']}: {text[:240]}", "")])
    what = ("No chat has checked their record's fingerprints. In a practice chat, ask Hermes to run "
            "`shasum -a 256 -c MANIFEST.sha256` inside their-record and show you every line.")
    return fc.outcome(False, "Fingerprints not checked", what, [], [{"id": "not_run", "what": what}])


def review_judged(ctx):
    """review.md gives the record number and judges their claim against what the record shows."""
    setup = _setup(ctx)
    entry, text = _review(ctx)
    if entry is None:
        what = "No review.md in the practice folder yet."
        return fc.outcome(False, "No review yet", what, [], [{"id": "none", "what": what}])
    missing = []
    if setup.get("number") and setup["number"] not in text:
        missing.append({"id": "number", "what": "Your review doesn't give the record number, so nobody can tell which record you judged."})
    if not re.search(r"after (?:a|the) fix|1 of 4|first (?:time|try|run)", text, re.I):
        missing.append({"id": "result", "what": "Say how their mission passed: first time, or after a fix, and how many checks each time."})
    if missing:
        return fc.outcome(False, "The review doesn't judge the record yet", missing[0]["what"], [], missing,
                          evidence=[("practice_file", f"{hermes_read_b.FOLDER}/review.md", text[:300], entry["sha256"])])
    return fc.outcome(True, "The review judges the record", "It names the record and says how the work really passed.", [],
                      evidence=[("practice_file", f"{hermes_read_b.FOLDER}/review.md", text[:300], entry["sha256"])])


def review_question(ctx):
    """review.md ends with at least one question for them, by name: what you'd ask before you'd vouch for it."""
    setup = _setup(ctx)
    entry, text = _review(ctx)
    if entry is None:
        return fc.cannot_read("Write review.md in the practice folder first.")
    first = str(setup.get("holder", "")).split(" ")[0]
    asks = [ln for ln in text.splitlines() if ln.strip().endswith("?")]
    if not asks:
        what = "Your review asks them nothing. Add the question you'd want answered before you vouch for this record."
        return fc.outcome(False, "No question for them", what, [], [{"id": "no_question", "what": what}])
    if first and first.lower() not in text.lower():
        what = f"Your review never speaks to {first} by name. Write it to them."
        return fc.outcome(False, "Not written to them", what, [], [{"id": "no_name", "what": what}])
    return fc.outcome(True, "It asks them a question", asks[0].strip()[:200], [])


def review_reading(ctx):
    """Transfer: the learner said what a clean fingerprint check does and doesn't prove."""
    note = _note(ctx)
    if not str(note.get("t_change") or "").strip():
        return fc.cannot_read("Answer each question and say what you'd add.")
    missing = []
    if str(note.get("t_unchanged") or "").strip().lower() != "yes":
        missing.append({"id": "unchanged", "what": "Every line OK means every file is as it was saved. Is that what it proves?"})
    if str(note.get("t_true") or "").strip().lower() != "no":
        missing.append({"id": "true", "what": "A record can be saved exactly as written and still claim too much. Does OK prove the claims?"})
    if missing:
        return fc.outcome(False, "The check reads differently", missing[0]["what"], [], missing)
    return fc.outcome(True, "You read the check right", "It proves nothing changed after saving, and nothing about whether the claims are true.", [])


READERS = {
    "teach.soul_for_them": teach_soul_for_them,
    "teach.memory_for_them": teach_memory_for_them,
    "teach.safe_for_them": teach_safe_for_them,
    "teach.first_chat_knows": teach_first_chat_knows,
    "teach.profile_reading": teach_profile_reading,
    "walkthrough.names_real": walkthrough_names_real,
    "walkthrough.has_check": walkthrough_has_check,
    "walkthrough.tested": walkthrough_tested,
    "walkthrough.reading": walkthrough_reading,
    "review.ran_check": review_ran_check,
    "review.judged": review_judged,
    "review.question": review_question,
    "review.reading": review_reading,
}
