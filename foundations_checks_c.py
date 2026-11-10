"""Live checks for the capability missions: helper agents (f.delegation) and toolsets (f.toolsets). Same contract as
foundations_checks.py: each reader takes the context (practice home, the learner's lab note, what was set up and
planted, the practice record) and returns an outcome. A reader that can't read never passes.

Every reader id here has a fixture test whose docstring is the id (tests/test_foundations_checks_c.py).
"""

from __future__ import annotations

import re

from . import foundations_checks as fc
from . import hermes_read, hermes_read_b, plants_c, yaml_keys
from .foundations_checks_a import _calls


def _note(ctx) -> dict:
    return ctx.get("note") or {}


def _setup(ctx) -> dict:
    return ctx.get("setup") or {}


def _planted_epoch(ctx):
    stamp = str((ctx.get("row") or {}).get("planted_at") or "")
    return hermes_read_b.iso_epoch(stamp) if stamp else None


def _sessions(home) -> list:
    found = hermes_read.sessions(home)
    return list(found["sessions"]) if found.get("readable") else []


def _rows(home, sid) -> list:
    return hermes_read.messages(home, sid).get("messages", [])


# ------------------------------------------------------------- delegation --


def _batches(ctx):
    """(session, call, result text) for every delegate_task call in a chat (not a helper) after setup."""
    since = _planted_epoch(ctx)
    out = []
    for session in _sessions(ctx["home"]):
        if session.get("source") == "subagent":
            continue
        if since is not None and isinstance(session.get("started_at"), (int, float)) and session["started_at"] < since:
            continue
        rows = _rows(ctx["home"], session["id"])
        results = [r for r in rows if r.get("role") == "tool" and r.get("tool_name") == "delegate_task"]
        for row in rows:
            if row.get("role") != "assistant":
                continue
            for call in _calls(row):
                if call["name"] == "delegate_task":
                    later = [r for r in results if (r.get("timestamp") or 0) >= (row.get("timestamp") or 0)]
                    out.append((session, call, str(later[0].get("content") or "") if later else ""))
    return out


def _task_count(call) -> int:
    tasks = call["args"].get("tasks")
    if isinstance(tasks, list):
        return len(tasks)
    return 1 if str(call["args"].get("goal") or "").strip() else 0


def delegation_batch(ctx):
    """One request handed every client to its own helper at once, and Hermes ran the batch."""
    clients = _setup(ctx).get("clients") or {}
    if not clients:
        return fc.cannot_read("Field Academy has no record of the client folders set up for this mission.")
    found = _batches(ctx)
    facts = [{"label": "Hand-offs to helpers in your chats", "value": str(len(found))},
             {"label": "Most helpers in one hand-off", "value": str(max((_task_count(c) for _, c, _ in found), default=0))}]
    if not found:
        what = "No hand-off to helpers in a practice chat yet. Ask Hermes to give each client folder to its own helper, all in one go."
        return fc.outcome(False, "No helpers yet", what, facts, [{"id": "no_delegation", "what": what}])
    good = [(s, c, r) for s, c, r in found if _task_count(c) >= len(clients) and plants_c.TOO_MANY not in r]
    if good:
        session, call, result = good[-1]
        return fc.outcome(True, "All the clients went to helpers in one hand-off",
                          f"Hermes handed {_task_count(call)} tasks to helpers in one call, and the call ran.", facts,
                          evidence=[("tool_result", "state.db", result[:300] or "delegate_task", "")])
    refused = [r for _, _, r in found if plants_c.TOO_MANY in r]
    if refused:
        what = ("Hermes tried a batch of helpers and was refused: " + refused[-1][refused[-1].find(plants_c.TOO_MANY):][:200]
                + " Find the setting that caps it, then ask again in a new chat.")
        return fc.outcome(False, "The batch was refused", what, facts, [{"id": "refused", "what": what}],
                          evidence=[("tool_result", "state.db", refused[-1][:300], "")])
    what = (f"Hermes used helpers, but never for all {len(clients)} clients in one hand-off. Ask for one helper per client, "
            "all at once.")
    return fc.outcome(False, "Not one hand-off for every client", what, facts, [{"id": "not_one_batch", "what": what}])


CLIENT_PATH = re.compile(r"clients[/\\]([A-Za-z0-9-]+)")


def _touched(home, sid) -> set:
    """The client folders a helper's own tool calls named."""
    out = set()
    for row in _rows(home, sid):
        if row.get("role") != "assistant":
            continue
        for call in _calls(row):
            text = " ".join(str(v) for v in call["args"].values() if isinstance(v, (str, int)))
            out.update(CLIENT_PATH.findall(text))
    return out


def delegation_helpers_ran(ctx):
    """Each client was worked by a helper of its own: a helper chat (source "subagent") whose tool calls stayed in that
    one client's folder."""
    clients = _setup(ctx).get("clients") or {}
    if not clients:
        return fc.cannot_read("Field Academy has no record of the client folders set up for this mission.")
    since = _planted_epoch(ctx)
    helpers = [s for s in plants_c.helper_sessions(ctx["home"])
               if since is None or not isinstance(s.get("started_at"), (int, float)) or s["started_at"] >= since]
    covered, crossed = set(), []
    for helper in helpers:
        touched = _touched(ctx["home"], helper["id"]) & set(clients)
        if len(touched) == 1:
            covered |= touched
        elif len(touched) > 1:
            crossed.append(helper)
    facts = [{"label": "Helper chats in the practice profile", "value": str(len(helpers))},
             {"label": "Clients worked by a helper of their own", "value": f"{len(covered)} of {len(clients)}"}]
    if not helpers:
        what = "No helper chats in the practice profile's records yet. Hermes records each helper as a chat of its own."
        return fc.outcome(False, "No helper chats yet", what, facts, [{"id": "no_helpers", "what": what}])
    missing_names = [clients[c]["name"] for c in clients if c not in covered]
    if missing_names:
        extra = " One helper worked in more than one client's folder." if crossed else ""
        what = f"No helper of its own worked {missing_names[0]}'s folder.{extra} Give each helper exactly one client folder."
        return fc.outcome(False, "Not every client had its own helper", what, facts, [{"id": "uncovered", "what": what}])
    return fc.outcome(True, "Each client had its own helper", "Field Academy read each helper's chat: each stayed in one client's folder.",
                      facts, evidence=[("session", "state.db", f"{len(helpers)} helper chats, source subagent", "")])


def delegation_summaries_right(ctx):
    """Every client folder has a summary.md with that client's own budget, no other client's, and the house rule's
    closing line, which the helpers only see if the request passed it on."""
    setup = _setup(ctx)
    clients, rule = setup.get("clients") or {}, setup.get("rule_line", "")
    if not clients or not rule:
        return fc.cannot_read("Field Academy has no record of the clients or the house rule set up for this mission.")
    budgets = {slug: c["budget"] for slug, c in clients.items()}
    missing, evidence, have = [], [], 0
    for slug, client in clients.items():
        text = hermes_read_b.folder_text(ctx["home"], f"clients/{slug}/summary.md", 32 * 1024)
        if text is None:
            missing.append({"id": "no_summary", "what": f"No clients/{slug}/summary.md yet for {client['name']}."})
            continue
        have += 1
        others = [b for s, b in budgets.items() if s != slug and b in text]
        if client["budget"] not in text:
            missing.append({"id": "wrong_figure", "what": f"{client['name']}'s summary doesn't give its budget, {client['budget']}."})
        elif others:
            missing.append({"id": "crossed", "what": f"{client['name']}'s summary quotes another client's budget, {others[0]}."})
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        if not lines or lines[-1].strip("*_ ") != rule:
            missing.append({"id": "rule_missing", "what": f"{client['name']}'s summary doesn't end with \"{rule}\". The rule is in "
                                                          "memory, and helpers start without memory: the request has to pass it on."})
        evidence.append(("practice_file", f"{hermes_read_b.FOLDER}/clients/{slug}/summary.md", text[:300], ""))
    facts = [{"label": "Summaries written", "value": f"{have} of {len(clients)}"}]
    if missing:
        order = {"no_summary": 0, "wrong_figure": 1, "crossed": 2, "rule_missing": 3}
        missing.sort(key=lambda m: order.get(m["id"], 9))
        return fc.outcome(False, "A summary is missing or wrong", missing[0]["what"], facts, missing, evidence[:1])
    return fc.outcome(True, "Every summary is right", "Each has its own client's budget, no other, and ends with the house rule.",
                      facts, evidence=evidence[:1])


INHERIT = re.compile(r"\b(main|same|inherit\w*|parent|default|empty|blank)\b", re.I)


def delegation_reading(ctx):
    """Transfer: the learner read someone else's helper settings and request and said what would really happen."""
    note = _note(ctx)
    if not str(note.get("t_runs") or "").strip() or not str(note.get("t_change") or "").strip():
        return fc.cannot_read("Answer how many helpers run, which model they use, whether they follow the rule, and what you'd change.")
    missing = []
    try:
        runs = int(str(note.get("t_runs")).strip())
    except ValueError:
        runs = None
    if runs != 0:
        missing.append({"id": "runs", "what": "Count again: four tasks against a cap of two. Hermes refuses the whole batch, so none run."})
    if not INHERIT.search(str(note.get("t_model") or "")):
        missing.append({"id": "model", "what": "An empty helper model doesn't mean no model. Say which one the helpers use."})
    if str(note.get("t_rule") or "").strip().lower() != "no":
        missing.append({"id": "rule", "what": "Helpers start without the profile's context files. Would they see a rule kept in AGENTS.md?"})
    facts = [{"label": "Helpers that run", "value": f"you said {runs if runs is not None else '?'}; it's 0"}]
    if missing:
        return fc.outcome(False, "The setup reads differently", missing[0]["what"], facts, missing)
    return fc.outcome(True, "You read the setup right", "None run, they'd use the main model, and they wouldn't see the rule.", facts)


# ---------------------------------------------------------------- toolsets --


# What a job like this one doesn't need: each of these reaches outside the practice folder or runs programs.
OUTSIDE = ("terminal", "code_execution", "browser", "web")
TERMINALISH = frozenset({"terminal", "process_manage", "execute_code"})
FILE_TOOLS = frozenset({"read_file", "write_file", "patch", "search_files"})
COMPOSITE = re.compile(r"^hermes(?:-|$)")


def toolset_settings(home) -> dict:
    """The toolsets a desktop chat gets: ``platform_toolsets.cli`` (what the Tools tab writes) minus
    ``agent.disabled_toolsets``. None for "on" means the list wasn't pinned, so Hermes's defaults apply."""
    found = hermes_read._read_text(home, "config.yaml")
    if found is None:
        return hermes_read.unreadable("No config.yaml in the practice profile.")
    tree = yaml_keys.parse(found[0])

    def names(path):
        value = yaml_keys.get(tree, path)
        if isinstance(value, str) and not isinstance(value, yaml_keys.Text):
            value = [value]
        return [str(v).strip() for v in value if isinstance(v, (str, int))] if isinstance(value, list) else None

    pinned = names("platform_toolsets.cli")
    disabled = names("agent.disabled_toolsets") or []
    on = None
    if pinned is not None and not any(COMPOSITE.match(n) for n in pinned):
        on = sorted(set(pinned) - set(disabled))
    return {"readable": True, "mtime": found[2], "pinned": pinned, "disabled": disabled, "on": on}


def toolsets_trimmed(ctx):
    """A desktop chat in the practice profile gets the file tools and none of terminal, code, browser or web."""
    found = toolset_settings(ctx["home"])
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The practice profile's settings could not be read."))
    on = found["on"]
    facts = [{"label": "Toolsets a desktop chat gets", "value": ", ".join(on) if on is not None else "every default toolset (nothing switched off in the Tools tab)"},
             {"label": "Also switched off in agent.disabled_toolsets", "value": ", ".join(found["disabled"]) or "none"}]
    if on is None:
        left = [t for t in OUTSIDE if t not in found["disabled"]]
        if not left:
            if "file" in found["disabled"]:
                what = "The file toolset is switched off, so Hermes can't read the notes or write the brief."
                return fc.outcome(False, "The job's own tools are off", what, facts, [{"id": "file_off", "what": what}])
            return fc.outcome(True, "Only what the job needs is on", "Terminal, code, browser and web are switched off.", facts,
                              evidence=[("setting", "config.yaml", "agent.disabled_toolsets: " + ", ".join(found["disabled"]), "")])
        what = (f"Every default toolset is still on, {left[0]} included. Open Capabilities, set Configuring: to the practice "
                "profile, and switch off in the Tools tab what the job doesn't need.")
        return fc.outcome(False, "Nothing switched off yet", what, facts, [{"id": "all_on", "what": what}])
    if "file" not in on:
        what = "The file toolset is off, so Hermes can't read the notes or write the brief."
        return fc.outcome(False, "The job's own tools are off", what, facts, [{"id": "file_off", "what": what}])
    extra = [t for t in OUTSIDE if t in on]
    if extra:
        what = f"{extra[0]} is still on, and this job never needs it."
        return fc.outcome(False, "A toolset the job doesn't need is on", what, facts, [{"id": "extra", "what": what}])
    return fc.outcome(True, "Only what the job needs is on", "File tools are on; terminal, code, browser and web are off.", facts,
                      evidence=[("setting", "config.yaml", "platform_toolsets.cli: " + ", ".join(found["pinned"] or []), "")])


PROBE = re.compile(r"\bdate\b", re.I)


def toolsets_probe_refused(ctx):
    """In a chat after the last settings change you asked Hermes to run `date` in the terminal, and it ran no
    terminal or code tool."""
    found = toolset_settings(ctx["home"])
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The practice profile's settings could not be read."))
    later = [s for s in _sessions(ctx["home"]) if s.get("source") != "subagent" and isinstance(s.get("started_at"), (int, float))
             and s["started_at"] > (found.get("mtime") or 0)]
    for session in reversed(later):
        rows = _rows(ctx["home"], session["id"])
        asked = any(r.get("role") == "user" and PROBE.search(str(r.get("content") or "")) and "terminal" in str(r.get("content") or "").lower() for r in rows)
        if not asked:
            continue
        ran = [r.get("tool_name") for r in rows if r.get("role") == "tool" and r.get("tool_name") in TERMINALISH]
        if ran:
            what = f"Hermes ran {ran[0]} when you asked for the terminal. Something that runs programs is still on."
            return fc.outcome(False, "Hermes still ran a program", what, [], [{"id": "ran", "what": what}])
        return fc.outcome(True, "Hermes couldn't run the command", "Your chat asked for the terminal and no terminal or code tool ran.",
                          [{"label": "Chats since the last settings change", "value": str(len(later))}],
                          evidence=[("session", "state.db", f"chat {str(session['id'])[:12]}: no terminal tool call", "")])
    what = "No chat since your last settings change asks Hermes to run `date` in the terminal. Open a new practice chat and ask."
    return fc.outcome(False, "Not tested yet", what, [{"label": "Chats since the last settings change", "value": str(len(later))}],
                      [{"id": "no_probe", "what": what}])


def toolsets_job_done(ctx):
    """brief.md in the practice folder names every meeting's decision, written with the file tools."""
    notes = _setup(ctx).get("notes") or {}
    if not notes:
        return fc.cannot_read("Field Academy has no record of the meeting notes set up for this mission.")
    text = hermes_read_b.folder_text(ctx["home"], "brief.md", 32 * 1024)
    if text is None:
        what = "No brief.md in the practice folder yet."
        return fc.outcome(False, "No brief yet", what, [], [{"id": "no_brief", "what": what}])
    low = text.lower()
    missed = [n["title"] for n in notes.values() if n["title"].lower() not in low]
    facts = [{"label": "Meetings the brief names", "value": f"{len(notes) - len(missed)} of {len(notes)}"}]
    if missed:
        what = f"The brief doesn't mention the {missed[0]} meeting."
        return fc.outcome(False, "A meeting is missing from the brief", what, facts, [{"id": "missed", "what": what}],
                          evidence=[("practice_file", f"{hermes_read_b.FOLDER}/brief.md", text[:300], "")])
    wrote = any(r.get("role") == "tool" and r.get("tool_name") in FILE_TOOLS for r in hermes_read.messages(ctx["home"]).get("messages", []))
    if not wrote:
        what = "The brief is there, but no chat shows Hermes's file tools writing it."
        return fc.outcome(False, "Not written by Hermes", what, facts, [{"id": "not_hermes", "what": what}])
    return fc.outcome(True, "The brief is written", "brief.md names every meeting, and the chat shows the file tools at work.", facts,
                      evidence=[("practice_file", f"{hermes_read_b.FOLDER}/brief.md", text[:300], "")])


def toolsets_reading(ctx):
    """Transfer: the learner read someone else's toolset settings and connector and said what a chat could really do."""
    note = _note(ctx)
    if not str(note.get("t_on") or "").strip() or not str(note.get("t_change") or "").strip():
        return fc.cannot_read("Say which toolsets a chat gets, whether it can run a command, whether it can change files in your home folder, and what you'd change.")
    named = {t for t in ("file", "web", "terminal", "browser", "code_execution", "memory") if re.search(rf"\b{t}\b", str(note.get("t_on")).lower())}
    missing = []
    if named != {"file", "web"}:
        missing.append({"id": "on", "what": "The Tools tab list has three; one of them is also switched off in agent.disabled_toolsets."})
    if str(note.get("t_run") or "").strip().lower() != "no":
        missing.append({"id": "run", "what": "With terminal off, can a chat still run a program?"})
    if str(note.get("t_home") or "").strip().lower() != "yes":
        missing.append({"id": "home", "what": "Look at the connector's folder: switching toolsets off doesn't touch a connector."})
    if missing:
        return fc.outcome(False, "The settings read differently", missing[0]["what"], [], missing)
    return fc.outcome(True, "You read the settings right", "File and web; no program; and the connector still reaches the whole home folder.", [])


READERS = {
    "delegation.batch": delegation_batch,
    "delegation.helpers_ran": delegation_helpers_ran,
    "delegation.summaries_right": delegation_summaries_right,
    "delegation.reading": delegation_reading,
    "toolsets.trimmed": toolsets_trimmed,
    "toolsets.probe_refused": toolsets_probe_refused,
    "toolsets.job_done": toolsets_job_done,
    "toolsets.reading": toolsets_reading,
}
