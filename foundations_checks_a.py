"""Live checks for Foundations missions 1, 2, 4, 5 and 6 (0.9 M6, part A).

Same contract as foundations_checks.py, which takes READERS in: a reader gets a context (the practice home, the
learner's note for the phase, what was planted) and returns an outcome. A reader that can't read never passes; it says
what Field Academy couldn't read and how the learner can check it themselves. Message text is read only to compare.
Each reader id has a fixture test in tests/test_foundations_part_a.py, whose class docstring is the id.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import hermes_read, hermes_read_a, matching, plants, plants_a
from .foundations_checks import _excerpt_around, cannot_read, outcome

STOP = frozenset("""a an the and or but of to in on for with at by from as is are was were be been it its this that these
those i me my we our you your he she they them their his her what which who whom when where why how all any each every
some no not only own same so than too very can will just do does did done have has had please use used using asked ask
about into over under again then there here would could should may might also get got make made""".split())


def _note(ctx) -> dict:
    return ctx.get("note") or {}


def _base(ctx, mission=""):
    return plants_a.base_for(ctx.get("planted") or {}, mission)


def _need_base(ctx, mission):
    base = _base(ctx, mission)
    return base, (None if base else cannot_read("Field Academy has no record of what it set up in the practice profile. Set up practice again."))


def stem(word: str) -> str:
    word = word.lower()
    for end in ("ing", "ed", "es", "s"):
        if word.endswith(end) and len(word) - len(end) >= 3:
            return word[: -len(end)]
    return word


def content_words(text) -> set:
    return {stem(w) for w in re.findall(r"[a-z][a-z'-]+", str(text or "").lower()) if w not in STOP and len(w) > 2}


def _lines(value) -> list:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [line.strip(" -*\t") for line in str(value or "").splitlines() if line.strip(" -*\t")]


def _sessions(home) -> list:
    found = hermes_read.sessions(home)
    return list(found["sessions"]) if found.get("readable") else []


def _rows(home, sid) -> list:
    return hermes_read.messages(home, sid).get("messages", [])


def _calls(row) -> list:
    """The tool calls on one assistant row: [{name, args}]."""
    try:
        raw = json.loads(row.get("tool_calls") or "[]")
    except ValueError:
        return []
    out = []
    for call in raw if isinstance(raw, list) else []:
        fn = call.get("function") if isinstance(call, dict) else None
        if isinstance(fn, dict):
            args = fn.get("arguments")
            try:
                args = json.loads(args) if isinstance(args, str) else (args or {})
            except ValueError:
                args = {}
            out.append({"name": str(fn.get("name") or ""), "args": args if isinstance(args, dict) else {}})
    return out


# =================================================================== mission 1 ==

VERBS = {
    "read_file": ("read", "open", "look", "view", "check"), "write_file": ("write", "wrote", "save", "creat", "made", "output"),
    "patch": ("edit", "patch", "change", "update", "fix"), "terminal": ("run", "ran", "command", "terminal", "shell", "list", "ls"),
    "search_files": ("search", "find", "list", "look for", "glob"), "web_search": ("web", "search"),
}


def _step_groups(rows) -> list:
    """One group per assistant row that asked for tools: the calls Hermes ran together in one trip."""
    return [calls for calls in (_calls(r) for r in rows if r.get("role") == "assistant") if calls]


def _line_matches(line, calls) -> bool:
    low = line.lower()
    for call in calls:
        verbs = VERBS.get(call["name"], (call["name"].split("_")[0],))
        target = " ".join(str(v) for v in call["args"].values() if isinstance(v, str))
        files = {Path(t).name.lower() for t in re.findall(r"[\w./\\-]+\.\w{2,4}", target)} | {Path(t).stem.lower() for t in re.findall(r"[\w./\\-]+\.\w{2,4}", target)}
        if any(v in low for v in verbs) or call["name"].lower() in low or any(f and f in low for f in files):
            return True
    return False


def loop_steps_match(ctx):
    """Check 1: the learner's step list beside the steps in Hermes's record, in order (calls in one trip in any order)."""
    base, problem = _need_base(ctx, "f.loop")
    if problem:
        return problem
    lines = _lines(_note(ctx).get("steps"))
    if not lines:
        return cannot_read("Write down what Hermes did, one step per line.")
    session, rows = plants_a.job_chat(ctx["home"], base["job_rel"], base["job_path"])
    if session is None:
        return cannot_read("Field Academy found no practice chat whose request names the job folder. Paste the request from the card.")
    groups = _step_groups(rows)
    at, matched = 0, 0
    for group in groups:
        while at < len(lines) and not _line_matches(lines[at], group):
            at += 1
        if at < len(lines):
            matched += 1
            at += 1
    facts = [{"label": "Steps in Hermes's record", "value": str(len(groups))}, {"label": "Steps you listed", "value": str(len(lines))},
             {"label": "Matched in order", "value": f"{matched} of {len(groups)}"}]
    if groups and matched == len(groups):
        return outcome(True, "Your steps match Hermes's record", "Every step Hermes took is in your list, in order.", facts)
    what = f"Your list matches {matched} of the {len(groups)} steps in Hermes's record, in order. Open each row and list it."
    return outcome(False, "Your steps don't match the record yet", what, facts, [{"id": "steps", "what": what}])


CLAIMY = re.compile(r"\b(?:read|wrote|written|saved|created|updated|counted|found|listed|checked|all|every|none|total|\d+)\b", re.I)


def claims_in(answer) -> list:
    parts = re.split(r"(?<=[.!?])\s+|\n+", str(answer or ""))
    return [p.strip(" -*") for p in parts if len(p.strip()) > 8 and CLAIMY.search(p)]


def loop_claims_listed(ctx):
    """Check 2: every claim in Hermes's final answer is on the learner's claim list (loose match)."""
    base, problem = _need_base(ctx, "f.loop")
    if problem:
        return problem
    mine = _lines(_note(ctx).get("claims"))
    if not mine:
        return cannot_read("Write every claim in Hermes's answer, one per line.")
    session, rows = plants_a.job_chat(ctx["home"], base["job_rel"], base["job_path"])
    if session is None:
        return cannot_read("Field Academy found no practice chat whose request names the job folder.")
    claims = claims_in(plants_a._final_answer(rows))
    if not claims:
        return cannot_read("Field Academy couldn't find claims in Hermes's final answer. Check that the job finished.")
    missed = [c for c in claims if not any(matching.overlap(c, m) >= 0.3 or set(re.findall(r"\d+", c)) & set(re.findall(r"\d+", m)) - {""}
                                           for m in mine)]
    facts = [{"label": "Claims in the answer", "value": str(len(claims))}, {"label": "Claims you caught", "value": str(len(claims) - len(missed))}]
    if not missed:
        return outcome(True, "You caught every claim", "Each claim in the final answer is on your list.", facts)
    what = f"Your list misses {len(missed)} {'claim' if len(missed) == 1 else 'claims'} in the answer."
    return outcome(False, "A claim is missing from your list", what, facts, [{"id": "claims", "what": what}],
                   evidence=[("answer", "state.db", missed[0], "")])


KEYS = {"output_locked": ("locked", "read-only", "read only", "old date", "stale", "old copy", "last week", "wasn't saved",
                          "not saved", "didn't save", "permission", "couldn't write", "could not write", "unlock"),
        "input_empty": ("empty", "no rows", "header only", "only a header", "blank"),
        "rows_short": ("only", "fewer", "short", "missing")}


def _names_problem(kind, details, wrong) -> bool:
    low = str(wrong or "").lower()
    if kind == "input_empty":
        return any(k in low for k in KEYS[kind]) and (details.get("empty", "").lower() in low or Path(details.get("empty", "x")).stem in low or "sheet" in low or "file" in low)
    if kind == "rows_short":
        return any(k in low for k in KEYS[kind]) and bool(re.search(r"\d", low))
    return any(k in low for k in KEYS[kind])


def loop_result_right(ctx):
    """Check 4 (hidden): the learner's list names what was wrong with the real result, a hidden problem has a false
    claim, and the output is right after the fix."""
    base, problem = _need_base(ctx, "f.loop")
    if problem:
        return problem
    planted = {k: v for k, v in (ctx.get("planted") or {}).items() if k in KEYS}
    note = _note(ctx)
    session, rows = plants_a.job_chat(ctx["home"], base["job_rel"], base["job_path"], last=True)
    answer = plants_a._final_answer(rows).lower()
    missing = []
    for kind, details in sorted(planted.items()):
        if not _names_problem(kind, details, note.get("wrong")):
            missing.append({"id": f"plant:{kind}", "what": "Your list of what's wrong with the real result doesn't name the problem in the files yet."})
            continue
        admitted = any(k in answer for k in KEYS[kind])
        if not admitted and not str(note.get("false_claims") or "").strip():
            missing.append({"id": f"false:{kind}", "what": "The answer hid a problem, and no claim is marked false."})
        if kind == "output_locked" and plants_a.hermes_unlocked(rows) and not re.search(r"unlock|lock|chmod|chflags|attrib", str(note.get("wrong", "")), re.I):
            missing.append({"id": "unlocked", "what": "Hermes changed a file's lock on its own, and your list doesn't say so."})
    result = plants_a.m1_output(ctx["home"], planted, (session or {}).get("started_at"))
    if not result["ok"]:
        missing.append({"id": "output", "what": result["why"]})
    if missing:
        return outcome(False, "The result isn't right yet", missing[0]["what"], missing=missing)
    return outcome(True, "The problem is named and the output is right", result["why"])


def loop_trips(ctx):
    """The warm-up's real number of trips (sessions.api_call_count), beside the learner's guess and count."""
    base, problem = _need_base(ctx, "f.loop")
    if problem:
        return problem
    session, rows = plants_a.job_chat(ctx["home"], f"{hermes_read_a.FOLDER}/warm-up", base["warm_path"])
    if session is None:
        return cannot_read("Field Academy found no warm-up chat whose message names the warm-up folder.")
    trips = session.get("api_call_count")
    tools = sum(len(g) for g in _step_groups(rows))
    if not isinstance(trips, int) or trips < 1:
        return cannot_read("Hermes didn't record how many trips the warm-up took. Open the warm-up chat and count the rows yourself.")
    return outcome(True, "The warm-up's real numbers", f"Hermes made {trips} {'trip' if trips == 1 else 'trips'} to the model and {tools} tool {'call' if tools == 1 else 'calls'}.",
                   [{"label": "Trips to the model", "value": str(trips)}, {"label": "Tool calls", "value": str(tools)}])


def loop_second_job(ctx):
    """Transfer: a plan written before reading, the second job run in a fresh chat, and a /steer noted."""
    base, problem = _need_base(ctx, "f.loop")
    if problem:
        return problem
    note = _note(ctx)
    if len(_lines(note.get("plan"))) < 2:
        return cannot_read("Write which claims you'll check and how, one per line, before you read the answer.")
    session, rows = plants_a.job_chat(ctx["home"], base["transfer_rel"], base["transfer_path"])
    if session is None:
        what = "No practice chat runs the second job yet. Press Open practice chat and paste the second card."
        return outcome(False, "The second job hasn't run", what, missing=[{"id": "no_chat", "what": what}])
    steered = hermes_read_a.steers(ctx["home"], session["id"])
    facts = [{"label": "Steering notes Hermes recorded", "value": str(steered) if steered else "none found (check the chat yourself)"}]
    return outcome(True, "The second job ran with your plan", "Your plan is written and the second job ran in a fresh chat.", facts)


# =================================================================== mission 2 ==


def _single_word_chats(home, after=None) -> list:
    out = []
    for s in _sessions(home):
        if after and (s.get("started_at") or 0) < after:
            continue
        said = [m for m in _rows(home, s["id"]) if m.get("role") == "user"]
        if len(said) == 1 and re.fullmatch(r"\W*\w+\W*", str(said[0].get("content") or "").strip()):
            out.append(s)
    return out


def _int(value):
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def cost_fixed_part_drop(ctx):
    """Check 3: the first trip of the "before" and "after" hello chats; the drop is real and the learner's share is
    within 5 points of it."""
    chats = _single_word_chats(ctx["home"])
    if len(chats) < 2:
        return cannot_read("Field Academy needs two practice chats that are only one word, a hello before your cut and one after.")
    before, after = hermes_read_a.first_trip(ctx["home"], chats[0]), hermes_read_a.first_trip(ctx["home"], chats[-1])
    if not before.get("readable") or not after.get("readable"):
        return cannot_read("A hello chat made more than one trip, so its fixed part can't be read on its own. Read the "
                           "Context Usage panel for that chat yourself, or send a fresh one-word hello.")
    b, a = before["tokens"], after["tokens"]
    drop = round((b - a) * 100 / b, 1) if b else 0.0
    mine = _int(_note(ctx).get("share"))
    facts = [{"label": "Fixed part before", "value": f"{b:,} tokens"}, {"label": "Fixed part after", "value": f"{a:,} tokens"},
             {"label": "Measured drop", "value": f"{drop:g}%"}, {"label": "Your share", "value": f"{mine}%" if mine is not None else "not given"}]
    costs = [s.get("estimated_cost_usd") for s in _sessions(ctx["home"]) if isinstance(s.get("estimated_cost_usd"), (int, float))]
    facts.append({"label": "What Hermes recorded these chats cost", "value": f"${sum(costs):.4f} (estimated)" if costs else "your provider didn't report prices"})
    if a >= b:
        what = "The fixed part didn't shrink between your first and last hello chats. Cut, then start a new chat before you measure."
        return outcome(False, "The fixed part didn't shrink", what, facts, [{"id": "no_drop", "what": what}])
    if mine is None or abs(mine - drop) > 5:
        what = f"The measured drop is {drop:g}%. Write the share you worked out; it should be within 5 points."
        return outcome(False, "Your share is off", what, facts, [{"id": "share", "what": what}])
    return outcome(True, "The fixed part shrank, and you measured it", f"From {b:,} to {a:,} tokens, {drop:g}% less.", facts)


def _tool_error(row) -> bool:
    if row.get("role") != "tool":
        return False
    text = str(row.get("content") or "")
    try:
        body = json.loads(text)
        return isinstance(body, dict) and (body.get("success") is False or bool(body.get("error")))
    except ValueError:
        return text.lower().startswith(("error", "tool error", "unknown tool"))


def cost_job_still_right(ctx):
    """Check 4: the latest run of the job finished with no tool error, and its output is right."""
    base, problem = _need_base(ctx, "f.cost")
    if problem:
        return problem
    session, rows = plants_a.job_chat(ctx["home"], base["job_rel"], base["job_path"], last=True)
    if session is None:
        return cannot_read("Field Academy found no practice chat whose request names the orders folder. Paste the request from the card.")
    errors = [r for r in rows if _tool_error(r)]
    if errors:
        what = "The last run of the job hit a tool error. Something it needs was switched off."
        return outcome(False, "The job broke", what, missing=[{"id": "tool_error", "what": what}],
                       evidence=[("tool_error", "state.db", str(errors[0].get("content") or ""), "")])
    result = plants_a.m2_output(ctx["home"], base, session.get("started_at"))
    if not result["ok"]:
        return outcome(False, "The job's result isn't right", result["why"], missing=[{"id": "output", "what": result["why"]}])
    return outcome(True, "The job still comes out right", result["why"], [{"label": "Tool errors", "value": "none"}])


def cost_decision(ctx):
    """Check 2 (with the rubric): the written decision names a tool the job used and something it cut."""
    base, problem = _need_base(ctx, "f.cost")
    if problem:
        return problem
    text = str(_note(ctx).get("decision") or "").lower()
    if len(text) < 20:
        return cannot_read("Write what you'll cut and why, before you change anything.")
    _s, rows = plants_a.job_chat(ctx["home"], base["job_rel"], base["job_path"])
    used = sorted({c["name"] for r in rows for c in _calls(r)})
    names_used = [n for n in used if n.lower() in text or any(v in text for v in VERBS.get(n, ())) or "file" in text and "file" in n]
    cut = re.search(r"\b(cut|off|remov|disabl|switch|drop|turn)", text) and re.search(r"connector|mcp|toolset|browser|server|agents\.md|project file|tool|skill", text)
    facts = [{"label": "Tools the job used", "value": ", ".join(used) or "none found"}]
    if names_used and cut:
        return outcome(True, "Your decision rests on what the job used", "It names a tool the job used and what you'll cut.", facts)
    what = ("Name a tool the job actually used, from its activity rows." if not names_used else "Name what you'll switch off.")
    return outcome(False, "Your decision needs the record behind it", what, facts, [{"id": "decision", "what": what}])


def cost_models_counted(ctx):
    """Count every model: the learner's main, side-job and helper-agent answers beside the profile's settings."""
    note = _note(ctx)
    if not all(str(note.get(k) or "").strip() for k in ("main", "auxiliary", "subagents")):
        return cannot_read("Write the model for Main model, Auxiliary models and Subagents, from Settings, Model.")
    found = hermes_read_a.models(ctx["home"])
    if not found.get("readable"):
        return cannot_read(found.get("why", "The practice profile's settings could not be read."))
    facts = [{"label": "Main model in the settings", "value": found["main"] or "not set in this profile's file (inherited)"},
             {"label": "Subagents in the settings", "value": found["subagents"] or "empty: uses the main model"},
             {"label": "Side jobs set to their own model", "value": str(sum(1 for v in found["auxiliary"].values() if v != "auto"))}]
    main = found["main"].lower()
    mine = str(note["main"]).lower()
    if main and not (main in mine or mine in main or main.split("/")[-1] in mine):
        what = f"The settings name a different main model: {found['main']}."
        return outcome(False, "Your main model doesn't match", what, facts, [{"id": "main", "what": what}])
    detail = "Your answers sit beside what the profile's settings say." + ("" if main else " Field Academy couldn't read the main model from the file; Settings, Model shows it.")
    return outcome(True, "You counted the models", detail, facts)


def cost_subagent_model(ctx):
    """Transfer: helper agents set to their own model in the practice profile, and the reasoning written."""
    found = hermes_read_a.models(ctx["home"])
    if not found.get("readable"):
        return cannot_read(found.get("why", "The practice profile's settings could not be read."))
    note = _note(ctx)
    words = len(re.findall(r"[.!?](\s|$)", str(note.get("sentences") or "")))
    one_model = bool(note.get("one_model"))
    if not found["subagents"] and not one_model:
        what = "Subagents still use the main model. Set a model under Settings, Model, Subagents, for academy-practice."
        return outcome(False, "No model is set for helper agents", what, missing=[{"id": "unset", "what": what}])
    if words < 2:
        what = "Write two or three sentences: what it saves and on which jobs, and what could get worse."
        return outcome(False, "Your reasoning is missing", what, missing=[{"id": "why", "what": what}])
    return outcome(True, "Helper agents have their own model" if found["subagents"] else "One model only, and your reasoning",
                   "The setting is in the practice profile and your reasoning is written.",
                   [{"label": "Subagents", "value": found["subagents"] or "your provider has one model"}])


def plant_fixed_a(ctx):
    """Every planted problem is fixed (missions 2, 4, 5, 6: no stated fact needed)."""
    planted = ctx.get("planted") or {}
    if not planted:
        return cannot_read("Field Academy has no record of what was set up in this practice profile.")
    missing, facts = [], []
    for kind, details in sorted(planted.items()):
        seen = plants.detect(kind, ctx["home"], details)
        result = plants.verify(kind, ctx["home"], details, "", _note(ctx))
        facts.extend(seen.get("facts", []))
        if not result["fixed"]:
            missing.append({"id": f"plant:{kind}", "what": result["why"]})
    if missing:
        return outcome(False, "Something in the setup still needs fixing", missing[0]["what"], facts, missing)
    return outcome(True, "The setup problem is fixed", "What was planted is found and put right.", facts)


# =================================================================== mission 4 ==

TRY_LINE = "over and out"


def marker_ok(rule: dict, reply: str) -> bool:
    text = str(reply or "").strip()
    kind, value = rule.get("marker"), str(rule.get("value") or "")
    if kind == "ends_with":
        last = [line for line in text.splitlines() if line.strip()]
        return bool(last) and squash_end(last[-1]).endswith(squash_end(value))
    if kind == "starts_with":
        return text.lower().lstrip("*_# ").startswith(value.lower())
    if kind == "no_char":
        return bool(text) and value not in text
    return False


def squash_end(text) -> str:
    return re.sub(r"[\s*_]+$", "", " ".join(str(text).lower().split()))


def _rule(ctx):
    note = _note(ctx)
    rules = {r["id"]: r for r in ((ctx.get("mission") or {}).get("lab") or {}).get("rules_a", [])}
    return rules.get(note.get("rule"))


def _edit_time(ctx):
    found = hermes_read_a.soul(ctx["home"])
    return found, (found.get("mtime") if found.get("readable") else None)


def soul_rule_present(ctx):
    """Check 1: the chosen rule is in the practice profile's SOUL.md, and the try's line is gone."""
    rule = _rule(ctx)
    if rule is None:
        return cannot_read("Pick the rule you added, so Field Academy knows what to look for.")
    found = hermes_read_a.soul(ctx["home"])
    if not found.get("readable"):
        return cannot_read(found.get("why", "SOUL.md could not be read."))
    text = plants_a.squash(found["text"])
    facts = [{"label": "SOUL.md last saved", "value": "read from the file's time"}]
    if TRY_LINE in text:
        what = "The try's line, \"Over and out\", is still in SOUL.md. Take it out first, so it can't stand in for your rule."
        return outcome(False, "The try's line is still there", what, facts, [{"id": "try_line", "what": what}])
    if plants_a.squash(rule["text"]) not in text:
        what = "Your rule isn't in academy-practice's SOUL.md. Right-click academy-practice's square and choose Edit SOUL.md."
        return outcome(False, "Your rule isn't in SOUL.md", what, facts, [{"id": "no_rule", "what": what}])
    line = next((ln for ln in found["text"].splitlines() if plants_a.squash(rule["text"]) in plants_a.squash(ln)), rule["text"])
    return outcome(True, "Your rule is in SOUL.md", "Found in academy-practice's SOUL.md.", facts, evidence=[("soul", "SOUL.md", line, found["sha256"])])


def _prompt_has(home, sid, rule_text):
    prompt = hermes_read_a.system_prompt_text(home, sid)
    return None if prompt is None else plants_a.squash(rule_text) in plants_a.squash(prompt)


def soul_before_chat(ctx):
    """Check 2: a chat started before the edit, used after it, kept the old instructions and the old behaviour."""
    rule = _rule(ctx)
    if rule is None:
        return cannot_read("Pick the rule you added, so Field Academy knows what to look for.")
    found, edit = _edit_time(ctx)
    if edit is None:
        return cannot_read("SOUL.md could not be read.")
    best = None
    for s in _sessions(ctx["home"]):
        if (s.get("started_at") or 0) >= edit:
            continue
        rows = _rows(ctx["home"], s["id"])
        if any(m.get("role") == "user" and (m.get("timestamp") or 0) > edit for m in rows):
            best = (s, rows)
    if best is None:
        what = "No chat started before your edit was used after it. Open a practice chat, ask something, then edit SOUL.md and ask again in that same chat."
        return outcome(False, "No chat from before the edit", what, missing=[{"id": "no_before", "what": what}])
    session, rows = best
    has = _prompt_has(ctx["home"], session["id"], rule["text"])
    facts = [{"label": "The chat read", "value": session.get("title") or "untitled chat"}]
    if has is None:
        return cannot_read("Field Academy couldn't read the instructions that chat started with.")
    if has:
        what = ("That chat's saved instructions include your rule, so Hermes rebuilt them: it was reopened on another model "
                "or from another folder. That's correct Hermes behaviour; open a chat, then edit, then ask there again.")
        return outcome(False, "That chat picked the rule up", what, facts, [{"id": "rebuilt", "what": what}])
    later = [m for m in rows if m.get("role") == "assistant" and (m.get("timestamp") or 0) > edit and str(m.get("content") or "").strip()]
    if not later:
        what = "That chat has no reply after your edit yet. Ask it one more question."
        return outcome(False, "No reply after the edit", what, facts, [{"id": "no_reply", "what": what}])
    if all(marker_ok(rule, m["content"]) for m in later):
        what = "That chat's replies after the edit follow the rule anyway. Ask it something longer, so the old behaviour shows."
        return outcome(False, "The old chat followed the rule", what, facts, [{"id": "followed", "what": what}])
    reply = next(m for m in later if not marker_ok(rule, m["content"]))
    return outcome(True, "The chat from before kept the old instructions", "Its saved instructions lack your rule, and it answered after the edit without it.",
                   facts, evidence=[("session", "state.db", str(reply["content"]), "")])


def soul_after_chat(ctx):
    """Check 3: the first chat started after the edit carries the rule and its first reply follows it."""
    rule = _rule(ctx)
    if rule is None:
        return cannot_read("Pick the rule you added, so Field Academy knows what to look for.")
    found, edit = _edit_time(ctx)
    if edit is None:
        return cannot_read("SOUL.md could not be read.")
    later = [s for s in _sessions(ctx["home"]) if (s.get("started_at") or 0) > edit]
    if not later:
        what = "No chat started after your edit. Press Open practice chat and ask the same question there."
        return outcome(False, "No chat from after the edit", what, missing=[{"id": "no_after", "what": what}])
    session = later[0]
    has = _prompt_has(ctx["home"], session["id"], rule["text"])
    if has is None:
        return cannot_read("Field Academy couldn't read the instructions that chat started with.")
    rows = _rows(ctx["home"], session["id"])
    first = next((m for m in rows if m.get("role") == "assistant" and str(m.get("content") or "").strip()), None)
    if not has:
        what = "The first chat after your edit started without the rule. Check which profile's SOUL.md you edited, and whether a project file says the opposite."
        return outcome(False, "The new chat didn't get the rule", what, missing=[{"id": "missing_rule", "what": what}])
    if first is None or not marker_ok(rule, first["content"]):
        what = "The new chat has the rule, but its first reply doesn't follow it. Check the Rules line for a project file that disagrees."
        return outcome(False, "The first reply ignored the rule", what, missing=[{"id": "ignored", "what": what}])
    return outcome(True, "The chat from after the edit follows the rule", "Its saved instructions include your rule, and its first reply follows it.",
                   evidence=[("session", "state.db", str(first["content"]), "")])


# =================================================================== mission 5 ==

PARTS = {
    "when": ("when", "use when", "trigger", "applies", "use it", "use this"),
    "procedure": ("procedure", "steps", "how", "process", "method", "instructions"),
    "pitfalls": ("pitfall", "gotcha", "watch out", "mistake", "avoid", "caution", "careful"),
    "verification": ("verif", "check", "confirm", "test", "done when", "validat"),
}
PART_WORDS = {"when": "when to use it", "procedure": "the steps", "pitfalls": "the pitfalls", "verification": "a way to check the result"}


def four_parts(text) -> dict:
    """Which of the four parts a SKILL.md has: a heading matching each, followed by a non-empty line."""
    lines = str(text or "").splitlines()
    found, unknown = {}, []
    for i, line in enumerate(lines):
        head = re.match(r"^\s*#{1,6}\s+(.*)$", line)
        if not head:
            continue
        title = head.group(1).strip().lower()
        body = next((ln for ln in lines[i + 1:] if ln.strip()), "")
        has_body = bool(body) and not re.match(r"^\s*#", body)
        part = next((p for p, keys in PARTS.items() if any(k in title for k in keys) and p not in found), None)
        if part:
            found[part] = has_body
        else:
            unknown.append(title)
    return {"parts": found, "unknown": unknown}


def skills_before(ctx) -> list:
    """Skill names present when the learner opened Your turn (snapshot kept by foundations_a), always excluded."""
    from . import foundations_a

    return foundations_a.skills_snapshot(_base(ctx, "f.skills").get("token", ""))


def _learner_skill(ctx):
    name = str(_note(ctx).get("skill_name") or "").strip()
    if not name:
        return None, cannot_read("Write the name of the skill you made, as Capabilities, Skills shows it.")
    if name.startswith("academy-"):
        return None, cannot_read("That's one of Field Academy's own skills. Name the skill you made for your own job.")
    found = hermes_read.skills(ctx["home"])
    if not found.get("readable"):
        return None, cannot_read("The skills folder could not be read.")
    skill = next((s for s in found["skills"] if s["name"] == name), None)
    if skill is None:
        what = f"No skill named {name} is in academy-practice. Check the name in Capabilities, Skills, with Configuring set to academy-practice."
        return None, outcome(False, "Field Academy can't find that skill", what, missing=[{"id": "no_skill", "what": what}])
    if name in set(skills_before(ctx)):
        what = f"{name} was there before Your turn started, so it's the try's skill. Make one for a job of your own."
        return None, outcome(False, "That skill came from the try", what, missing=[{"id": "try_skill", "what": what}])
    return skill, None


def skills_four_parts(ctx):
    """Check 1: the learner's SKILL.md has when to use it, the steps, the pitfalls and a check, each with content."""
    skill, problem = _learner_skill(ctx)
    if problem:
        return problem
    text = hermes_read_a.skill_text(ctx["home"], skill["rel_path"])
    if not text.get("readable"):
        return cannot_read(text.get("why", "The skill file could not be read."))
    got = four_parts(text["text"])
    missing = [p for p in PARTS if not got["parts"].get(p)]
    facts = [{"label": "Parts found", "value": f"{4 - len(missing)} of 4"}]
    if got["unknown"]:
        facts.append({"label": "Headings Field Academy didn't place", "value": ", ".join(got["unknown"][:4])})
    if not missing:
        return outcome(True, "The skill has all four parts", "Each part has a heading and content under it.", facts,
                       evidence=[("skill", skill["rel_path"], f"{skill['name']}: {skill['description']}", skill["sha256"])])
    what = f"The skill is missing {PART_WORDS[missing[0]]}" + (", or a heading Field Academy didn't recognise." if got["unknown"] else ".")
    return outcome(False, "A part is missing", what, facts, [{"id": f"part:{p}", "what": f"Add {PART_WORDS[p]}."} for p in missing])


_LAST_WORD = re.compile(r"\s\S*$")
_CLIP_TRAIL = re.compile(r"[\s.,;:\-\u2013\u2014(/]+$")


def seen_line(description: str) -> str:
    """The description as the skills index shows it, the way Hermes 0.22.6 and later clip it (agent/skill_utils.py,
    clip_skill_description, v0.23.0:857-865): up to 60 characters as written; a longer line is cut at the last whole word
    in its first 58 characters, trailing punctuation dropped, plus three dots. One long word with no space is cut at 57."""
    text = " ".join(str(description or "").strip().strip("'\"").split())
    if len(text) <= 60:
        return text
    head = text[:58]
    boundary = _LAST_WORD.search(head)
    if not boundary or boundary.start() == 0:
        return text[:57] + "..."
    return _CLIP_TRAIL.sub("", head[:boundary.start()]) + "..."


def _loads(rows, name) -> list:
    """Indexes of assistant rows that opened ``name`` with skill_view."""
    out = []
    for i, r in enumerate(rows):
        if r.get("role") == "assistant" and any(c["name"] == "skill_view" and str(c["args"].get("name", "")) == name for c in _calls(r)):
            out.append(i)
    return out


def _test_chat(ctx, skill):
    """The first chat started after the skill was saved where Hermes opened it before the learner named it."""
    usage = hermes_read_a.skill_usage(ctx["home"]).get(skill["name"], {})
    saved = skill.get("mtime") or 0
    for s in _sessions(ctx["home"]):
        rows = _rows(ctx["home"], s["id"])
        loads = _loads(rows, skill["name"])
        if not loads:
            continue
        named = next((i for i, m in enumerate(rows) if m.get("role") == "user" and (skill["name"] in str(m.get("content") or "") or f"/{skill['name']}" in str(m.get("content") or ""))), None)
        if named is not None and named < loads[0]:
            continue
        started = s.get("started_at") or 0
        # The background review can patch the skill after the test chat; a patch after the start doesn't count against it.
        if started > saved or usage.get("last_patched_at"):
            return s, rows
    return None, []


def skills_loaded_unnamed(ctx):
    """Check 3: a chat started after the skill was saved where Hermes opened it (skill_view) before it was named."""
    skill, problem = _learner_skill(ctx)
    if problem:
        return problem
    session, rows = _test_chat(ctx, skill)
    if session is None:
        what = "No new chat opened your skill on its own. Ask for the job in a fresh practice chat, in your normal words, without its name or slash command."
        return outcome(False, "Hermes hasn't loaded it on its own", what, missing=[{"id": "not_loaded", "what": what}])
    first = next((m for m in rows if m.get("role") == "user"), {})
    return outcome(True, "Hermes found and loaded your skill", f"In a new chat it opened {skill['name']} before you named it.",
                   [{"label": "Loaded skill", "value": skill["name"]}], evidence=[("session", "state.db", str(first.get("content") or ""), "")])


def skills_description_words(ctx):
    """Check 2 (with the rubric): the part of the description Hermes shows shares a word with how the learner asked."""
    skill, problem = _learner_skill(ctx)
    if problem:
        return problem
    seen = seen_line(skill["description"])
    session, rows = _test_chat(ctx, skill)
    asked = str(next((m for m in rows if m.get("role") == "user"), {}).get("content") or "") if session else str(_note(ctx).get("asked") or "")
    if not asked.strip():
        return cannot_read("Write how you asked for the job, word for word.")
    head = seen[:-3] if seen.endswith("...") else seen
    shared = sorted(content_words(head) & content_words(asked))
    facts = [{"label": "Hermes sees", "value": seen}, {"label": "Characters", "value": str(len(" ".join(skill["description"].split())))},
             {"label": "Words shared with how you asked", "value": ", ".join(shared) or "none"}]
    if shared:
        return outcome(True, "The description speaks your words", "The part Hermes sees shares words with how you asked.", facts)
    cut = len(" ".join(skill["description"].split())) > 60
    what = ("Hermes cuts the description short, and the words you'd say come after the cut." if cut and content_words(skill["description"]) & content_words(asked)
            else "The part Hermes sees shares no word with how you asked. Start it with the words you'd say.")
    return outcome(False, "The description misses your words", what, facts, [{"id": "words", "what": what}])


def skills_steps_out(ctx):
    """Check 4: none of the job's steps are left in memory; a planted steps line is gone."""
    mem = hermes_read.memory(ctx["home"])
    if not mem.get("readable"):
        return cannot_read(mem.get("why", "The memory files could not be read."))
    entries = mem["memory"]["entries"] + mem["user"]["entries"]
    found = plants_a.procedure_lines(entries)
    term = str(_note(ctx).get("job") or "").strip()
    if term:
        found += [e for e in entries if e not in found and matching.mentions(e, term) and plants_a.step_markers(e) >= 2]
    if found:
        what = "A memory line still holds a job's steps. Steps belong in a skill; take them out of memory."
        return outcome(False, "Steps are still in memory", what, missing=[{"id": "steps_in_memory", "what": what}],
                       evidence=[("memory", "memories/MEMORY.md", found[0], mem["memory"]["sha256"])])
    return outcome(True, "No steps are left in memory", "No memory line reads like a procedure.", [{"label": "Memory lines", "value": str(len(entries))}])


def skills_better_line(ctx):
    """Transfer: what survives the cut, said right, and a better line of 60 characters or fewer."""
    note = _note(ctx)
    original, survives, better = str(note.get("original") or ""), str(note.get("survives") or ""), str(note.get("better") or "").strip()
    if not better:
        return cannot_read("Write a better description, 60 characters or fewer.")
    facts = [{"label": "Your line", "value": f"{len(better)} characters"}]
    if len(better) > 60:
        what = f"Your line is {len(better)} characters. Hermes refuses a new line over 60 and cuts a long one short."
        return outcome(False, "Your line is too long", what, facts, [{"id": "long", "what": what}])
    if original.strip():
        seen = seen_line(original)
        facts.append({"label": "What Hermes sees of the original", "value": seen})
        if survives.strip() and matching.overlap(survives, seen) < 0.6:
            what = f"Hermes sees: \"{seen}\". Compare that with what you wrote survives."
            return outcome(False, "Recount the cut", what, facts, [{"id": "cut", "what": what}])
    return outcome(True, "Your line fits and starts with your words", "Field Academy counted the characters.", facts)


# =================================================================== mission 6 ==


def _mem_entries(path):
    mem = hermes_read.memory(path)
    return (mem["memory"]["entries"] + mem["user"]["entries"]) if mem.get("readable") else None


def profiles_own_facts(ctx):
    """Check 1: each practice profile holds its own fact, and not the other's (nor another client's line)."""
    base, problem = _need_base(ctx, "f.profiles")
    if problem:
        return problem
    note = _note(ctx)
    if not all(str(note.get(k) or "").strip() for k in ("fact_a", "fact_b")):
        return cannot_read("Write the fact you saved in each profile.")
    a, b = _mem_entries(base["a_path"]), _mem_entries(base["b_path"])
    if a is None or b is None:
        return cannot_read("Field Academy couldn't read both practice profiles' memory files. Press Show memory file for each.")
    hollis = lambda lines: [ln for ln in lines if "hollis" not in ln.lower()]  # noqa: E731 - the try's line is excluded
    a, b = hollis(a), hollis(b)
    problems = []
    if not matching.holds(a, note["fact_a"]):
        problems.append("academy-practice's memory doesn't hold its fact.")
    if not matching.holds(b, note["fact_b"]):
        problems.append("academy-practice-b's memory doesn't hold its fact.")
    if matching.holds(a, note["fact_b"]):
        problems.append("academy-practice's memory holds B's fact.")
    if matching.holds(b, note["fact_a"]) or matching.holds(b, base.get("decoy", ""), threshold=0.6):
        problems.append("academy-practice-b's memory holds a line about another client.")
    facts = [{"label": "Lines in academy-practice", "value": str(len(a))}, {"label": "Lines in academy-practice-b", "value": str(len(b))}]
    if problems:
        return outcome(False, "The two memories aren't apart yet", problems[0], facts, [{"id": f"mem{i}", "what": p} for i, p in enumerate(problems)])
    return outcome(True, "Each profile holds its own fact", "Each memory has its own fact and not the other's.", facts,
                   evidence=[("memory", "memories/MEMORY.md (academy-practice)", matching.holds(a, note["fact_a"]), ""),
                             ("memory", "memories/MEMORY.md (academy-practice-b)", matching.holds(b, note["fact_b"]), "")])


def _used(home, own, others, after):
    """("ok", the reply) when a chat after the saves used its own fact before it was said and no chat leaked another's;
    ("leak", None) when any did; ("none", None) otherwise."""
    found = None
    for s in _sessions(home):
        if after and (s.get("started_at") or 0) <= after:
            continue
        rows = _rows(home, s["id"])
        if any(m.get("role") == "assistant" and any(o and matching.mentions(m.get("content"), o) for o in others) for m in rows):
            return "leak", None
        said = next((i for i, m in enumerate(rows) if m.get("role") == "user" and matching.mentions(m.get("content"), own)), None)
        used = next((i for i, m in enumerate(rows) if m.get("role") == "assistant" and matching.mentions(m.get("content"), own)), None)
        if found is None and used is not None and (said is None or used < said):
            found = rows[used]
    return ("ok", found) if found is not None else ("none", None)


def _save_time(path, fact):
    mem = hermes_read.memory(path)
    for key in ("memory", "user"):
        if mem.get("readable") and matching.holds(mem[key]["entries"], fact):
            return mem[key]["mtime"]
    return None


def profiles_own_use(ctx):
    """Check 2 (with the rubric): a new chat in each profile, after both saves, used its own fact and never the other's."""
    base, problem = _need_base(ctx, "f.profiles")
    if problem:
        return problem
    note = _note(ctx)
    ka, kb = str(note.get("key_a") or "").strip(), str(note.get("key_b") or "").strip()
    if not ka or not kb:
        return cannot_read("Name the key word of each fact, so Field Academy can look for it.")
    after = max([t for t in (_save_time(base["a_path"], note.get("fact_a", "")), _save_time(base["b_path"], note.get("fact_b", ""))) if t] or [0])
    decoy_word = next(iter(sorted(content_words(base.get("decoy", "")) - {"client", "invoice", "day"})), "")
    a_state, a_row = _used(base["a_path"], ka, [kb], after)
    b_state, b_row = _used(base["b_path"], kb, [ka, decoy_word], after)
    facts = [{"label": "academy-practice", "value": {"ok": "used its own fact", "leak": "mentioned the other client", "none": "no new chat used its fact"}[a_state]},
             {"label": "academy-practice-b", "value": {"ok": "used its own fact", "leak": "mentioned the other client", "none": "no new chat used its fact"}[b_state]}]
    if a_state == "ok" and b_state == "ok":
        return outcome(True, "Each profile used its own fact", "A new chat in each, after both saves, used its fact in real work and never the other's.", facts,
                       evidence=[("session", "state.db (academy-practice)", _excerpt_around(str(a_row.get("content") or ""), ka), ""),
                                 ("session", "state.db (academy-practice-b)", _excerpt_around(str(b_row.get("content") or ""), kb), "")])
    what = ("A chat brought up the other client's details." if "leak" in (a_state, b_state)
            else "Ask each profile for real work that needs its fact, in a new chat, without naming the fact.")
    return outcome(False, "Not both profiles used their own fact", what, facts, [{"id": "use", "what": what}])


def profiles_plan_written(ctx):
    """Transfer: a profile plan on paper, each profile with what it holds and what it must never hold."""
    text = str(_note(ctx).get("plan") or "")
    holds = len(re.findall(r"\bholds?\b|\bfacts?\b|\bskills?\b|\bkeys?\b", text, re.I))
    never = len(re.findall(r"\bnever\b|\bmust not\b|\bkeep out\b", text, re.I))
    if len(text) < 80 or not holds or not never:
        what = "For each profile, write its name, what it holds and what it must never hold."
        return outcome(False, "The plan isn't complete", what, missing=[{"id": "plan", "what": what}])
    return outcome(True, "Your profile plan is written", "Each profile has what it holds and what it must never hold.")


READERS = {
    "loop.steps_match": loop_steps_match,
    "loop.claims_listed": loop_claims_listed,
    "loop.result_right": loop_result_right,
    "loop.trips": loop_trips,
    "loop.second_job": loop_second_job,
    "cost.fixed_part_drop": cost_fixed_part_drop,
    "cost.job_still_right": cost_job_still_right,
    "cost.decision": cost_decision,
    "cost.models_counted": cost_models_counted,
    "cost.subagent_model": cost_subagent_model,
    "plant.fixed_a": plant_fixed_a,
    "soul.rule_present": soul_rule_present,
    "soul.before_chat": soul_before_chat,
    "soul.after_chat": soul_after_chat,
    "skills.four_parts": skills_four_parts,
    "skills.description_words": skills_description_words,
    "skills.loaded_unnamed": skills_loaded_unnamed,
    "skills.steps_out": skills_steps_out,
    "skills.better_line": skills_better_line,
    "profiles.own_facts": profiles_own_facts,
    "profiles.own_use": profiles_own_use,
    "profiles.plan_written": profiles_plan_written,
}
