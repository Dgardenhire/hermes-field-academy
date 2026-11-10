"""Live checks for Foundations missions 7 to 11. Same contract as foundations_checks.py: each reader takes the context
(practice home, the learner's lab note, what was set up and planted, the practice record, the page's sample) and
returns an outcome. A reader that can't read never passes. Where only the live app can confirm something, the reader
says so and says how to check it by hand (``cannot_read``), and it fails closed.

Every reader id here has a fixture test whose docstring is the id (tests/test_foundations_checks_b.py).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import foundations_checks as fc
from . import hermes_read, hermes_read_b, matching, plants, plants_b, scrub


def _note(ctx) -> dict:
    return ctx.get("note") or {}


def _setup(ctx) -> dict:
    return ctx.get("setup") or {}


def _row(ctx) -> dict:
    return ctx.get("row") or {}


def _folder(ctx) -> str:
    return _setup(ctx).get("folder") or (_row(ctx).get("plan") or {}).get("folder") or str(hermes_read_b.folder_path(ctx["home"]))


def _planted_epoch(ctx):
    stamp = str(_row(ctx).get("planted_at") or "")
    return hermes_read_b.iso_epoch(stamp) if stamp else None


# ------------------------------------------------------------------ plants --


def plants_all_fixed(ctx):
    """Every planted problem is fixed. For missions with no single fact to save (7 to 11)."""
    planted = {k: v for k, v in (ctx.get("planted") or {}).items() if not str(k).startswith("_")}
    if not planted:
        return fc.cannot_read("Field Academy has no record of what was set up in this practice profile.")
    missing, facts, evidence = [], [], []
    for kind, details in sorted(planted.items()):
        seen = plants.detect(kind, ctx["home"], details)
        result = plants.verify(kind, ctx["home"], details, "", _note(ctx))
        facts.extend(seen.get("facts", []))
        evidence.extend((k, rel, text, "") for k, rel, text in seen.get("evidence", [])[:1])
        if not result["fixed"]:
            missing.append({"id": f"plant:{kind}", "what": result["why"]})
    if missing:
        return fc.outcome(False, "Something planted in the profile still needs fixing", missing[0]["what"], facts, missing, evidence)
    return fc.outcome(True, "What was planted is fixed", "Field Academy read the profile and each planted problem is gone.", facts, evidence=evidence)


# --------------------------------------------------------------- connectors --


def _scoped(ctx):
    found = hermes_read_b.mcp_servers(ctx["home"])
    if not found.get("readable"):
        return found, []
    folder = _folder(ctx)
    return found, [s for s in found["servers"] if s["enabled"] and plants_b.reaches(s, folder)]


def _the_connector(ctx):
    found, scoped = _scoped(ctx)
    if not found.get("readable"):
        return found, None
    wanted = str(_note(ctx).get("server") or "").strip() or _setup(ctx).get("server", "files")
    if len(scoped) == 1:
        return found, scoped[0]
    return found, next((s for s in found["servers"] if s["name"] == wanted), None)


def connectors_one_scoped(ctx):
    """Exactly one connector reaches the practice folder, with an allow list of only what the job needs."""
    found, scoped = _scoped(ctx)
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The connector settings could not be read."))
    facts = [{"label": "Connectors that reach the practice folder", "value": ", ".join(s["name"] for s in scoped) or "none"}]
    if len(scoped) != 1:
        what = ("No connector reaches the practice folder." if not scoped else
                f"{len(scoped)} connectors reach the practice folder ({', '.join(s['name'] for s in scoped)}). Only one should.")
        return fc.outcome(False, "More than one way into the folder" if scoped else "No connector reaches the folder", what, facts,
                          [{"id": "scope", "what": what}])
    server = scoped[0]
    include, exclude = server["include"], server["exclude"]
    facts.append({"label": "Allow list (tools.include)", "value": ", ".join(include) if include is not None else "none"})
    if include is None:
        what = ("Only a list of what's off (tools.exclude). A tool the connector adds later arrives switched on." if exclude
                else "No allow list, so every tool the connector offers is on.")
        return fc.outcome(False, "No allow list", what, facts, [{"id": "no_include", "what": what}])
    extra = [t for t in include if t not in plants_b.JOB_TOOLS]
    if extra:
        what = f"The allow list holds {extra[0]}, which this job doesn't need."
        return fc.outcome(False, "The allow list holds more than the job needs", what, facts, [{"id": "extra_tool", "what": what}])
    if not include:
        what = "The allow list is empty, so the job can't read or write anything. Switch on the tools it needs."
        return fc.outcome(False, "Nothing is switched on", what, facts, [{"id": "empty_include", "what": what}])
    return fc.outcome(True, f"{server['name']} reaches only the practice folder, with an allow list",
                      f"Allowed: {', '.join(include)}.", facts,
                      evidence=[("setting", "config.yaml", f"mcp_servers.{server['name']}.tools.include: {', '.join(include)}", found["sha256"])])


def connectors_untrusted(ctx):
    """The connector's trust is the word untrusted."""
    found, server = _the_connector(ctx)
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The connector settings could not be read."))
    if server is None:
        return fc.outcome(False, "No connector to check", "No connector reaches the practice folder.", missing=[{"id": "none", "what": "No connector reaches the practice folder."}])
    raw = str(server["trust_raw"] or "").strip().lower()
    facts = [{"label": f"{server['name']} trust", "value": server["trust_raw"] if server["trust_raw"] is not None else "not set (full)"}]
    if raw == "untrusted":
        return fc.outcome(True, f"{server['name']} is untrusted", "Tools that can change things ask first.", facts,
                          evidence=[("setting", "config.yaml", f"mcp_servers.{server['name']}.trust: untrusted", found["sha256"])])
    what = ("Trust isn't set, so it is full: no tool asks." if server["trust_raw"] is None else
            f"Trust reads \"{server['trust_raw']}\". Hermes would treat that as untrusted, but the standard asks for the word itself.")
    return fc.outcome(False, "Trust isn't untrusted", what, facts, [{"id": "trust", "what": what}])


REFUSAL = "did not approve running write-capable MCP tool"


def _sessions_after(home, epoch):
    listed = hermes_read.sessions(home)
    if not listed.get("readable"):
        return None
    return [s for s in listed["sessions"] if isinstance(s.get("started_at"), (int, float)) and (epoch is None or s["started_at"] > epoch)]


def connectors_refusal_seen(ctx):
    """A write the connector asked about was turned down, in a chat after the last settings change."""
    found, server = _the_connector(ctx)
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The connector settings could not be read."))
    name = server["name"] if server else _setup(ctx).get("server", "files")
    later = _sessions_after(ctx["home"], found.get("mtime"))
    if later is None:
        return fc.cannot_read("The chat records could not be read.")
    for session in later:
        msgs = hermes_read.messages(ctx["home"], session["id"]).get("messages", [])
        for m in msgs:
            text = str(m.get("content") or "")
            if m.get("role") == "tool" and REFUSAL in text and f"server '{name}'" in text:
                return fc.outcome(True, "A write asked, and you turned it down",
                                  f"Hermes recorded the refusal in a chat after your last settings change.",
                                  [{"label": "Chats since the last settings change", "value": str(len(later))}],
                                  evidence=[("tool_result", "state.db", text[text.find("The user"):][:300] or text, "")])
    what = (f"No turned-down write through {name} in a chat after your last settings change. Start a new practice chat, "
            "ask for the summary, and turn the first write card down.")
    return fc.outcome(False, "No turned-down write yet", what, [{"label": "Chats since the last settings change", "value": str(len(later))}],
                      [{"id": "no_refusal", "what": what}])


def _tool_ok(message) -> bool:
    text = str(message.get("content") or "")
    low = text.lower()
    try:
        body = json.loads(text)
        if isinstance(body, dict) and (body.get("error") or body.get("success") is False):
            return False
    except ValueError:
        pass
    return REFUSAL not in text and not low.startswith("error")


def connectors_clean_start(ctx):
    """The connector started after the last settings change (its banner in mcp-stderr.log) and a later tool call
    through it succeeded."""
    found, server = _the_connector(ctx)
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The connector settings could not be read."))
    name = server["name"] if server else _setup(ctx).get("server", "files")
    changed = found.get("mtime")
    starts = [b for b in hermes_read_b.banners(ctx["home"]) if b["server"] == name and (b["time"] is None or changed is None or b["time"] >= changed)]
    facts = [{"label": f"Starts of {name} logged since the last change", "value": str(len(starts))}]
    if not starts:
        what = (f"No start of {name} in logs/mcp-stderr.log after your last settings change. Open a new practice chat so the "
                "connector starts again.")
        return fc.outcome(False, "No clean start logged", what, facts, [{"id": "no_start", "what": what}])
    since = starts[-1]["time"]
    for m in hermes_read.messages(ctx["home"]).get("messages", []):
        if m.get("role") != "tool" or not hermes_read_b.is_connector_tool(m.get("tool_name"), name):
            continue
        if since is not None and isinstance(m.get("timestamp"), (int, float)) and m["timestamp"] < since:
            continue
        if _tool_ok(m):
            return fc.outcome(True, f"{name} started cleanly and worked", "The start is in logs/mcp-stderr.log, and a tool call through it succeeded.",
                              facts, evidence=[("log_line", starts[-1]["file"], f"===== starting MCP server '{name}' =====", "")])
    what = f"{name} started, but no tool call through it has succeeded since. Ask for the summary in a new practice chat."
    return fc.outcome(False, "Started, but no tool call worked yet", what, facts, [{"id": "no_call", "what": what}])


def connectors_folder_outcome(ctx):
    """A summary file was written in the practice folder, and every order is still where it started."""
    setup = _setup(ctx)
    orders = dict(setup.get("orders") or {})
    orders.update((ctx.get("planted") or {}).get("order_injection", {}).get("orders") or {})
    files = hermes_read_b.folder_files(ctx["home"])
    if not files.get("readable") or not orders:
        return fc.cannot_read("The practice folder or its sample orders could not be read.")
    seeded = set(orders) | {setup.get("flyer", "old-flyer.txt")}
    started = max((f["mtime"] for f in files["files"] if f["rel"] in seeded), default=0)
    new = [f for f in files["files"] if f["rel"] not in seeded and f["mtime"] >= started and f["size"] > 0]
    moved = plants_b.orders_in_place(ctx["home"], orders)
    facts = [{"label": "New files in the practice folder", "value": ", ".join(f["rel"] for f in new) or "none"},
             {"label": "Orders moved or changed", "value": str(len(moved))}]
    if moved:
        what = f"{moved[0]} isn't where it started. Put every order back."
        return fc.outcome(False, "An order moved", what, facts, [{"id": "moved", "what": what}])
    if not new:
        what = "No summary file in the practice folder yet."
        return fc.outcome(False, "No summary yet", what, facts, [{"id": "no_summary", "what": what}])
    text = hermes_read_b.folder_text(ctx["home"], new[-1]["rel"], 4096) or ""
    return fc.outcome(True, "The summary is written and the orders are in place", f"Found {new[-1]['rel']}.", facts,
                      evidence=[("practice_file", f"{hermes_read_b.FOLDER}/{new[-1]['rel']}", text[:300], new[-1]["sha256"])])


def connector_tiers(entry: dict) -> dict:
    """For a filesystem-connector settings block: which tools run freely, which ask, and which can't run."""
    tools = entry.get("tools") if isinstance(entry.get("tools"), dict) else {}
    include, exclude = tools.get("include"), tools.get("exclude")
    on = [t for t in plants_b.FS_TOOLS if (t in include if isinstance(include, list) else t not in (exclude or []))]
    untrusted = str(entry.get("trust") or "full").strip().lower() != "full"
    free = [t for t in on if t in plants_b.FS_READ_ONLY or not untrusted]
    ask = [t for t in on if t not in free]
    return {"free": free, "ask": ask, "blocked": [t for t in plants_b.FS_TOOLS if t not in on]}


def _tool_names(text) -> list:
    low = str(text or "").lower().replace("-", "_")
    return sorted({t for t in plants_b.FS_TOOLS if re.search(rf"(?<![a-z_]){t}(?![a-z_])", low)})


def connectors_reading(ctx):
    """Transfer: the learner sorted someone else's connector block into runs freely, asks first and can't run."""
    example = ((ctx.get("mission") or {}).get("transfer") or {}).get("example") or {}
    if not example:
        return fc.cannot_read("This mission has no example block to read.")
    note = _note(ctx)
    if not str(note.get("t_ask") or "").strip() or not str(note.get("t_change") or "").strip():
        return fc.cannot_read("Write which tools ask first, which can't run, how many run freely, and what you'd change.")
    truth = connector_tiers(example)
    ask, blocked = _tool_names(note.get("t_ask")), _tool_names(note.get("t_blocked"))
    try:
        free = int(str(note.get("t_free") or "").strip())
    except ValueError:
        free = None
    facts = [{"label": "Runs freely", "value": f"you said {free if free is not None else '?'}; it's {len(truth['free'])}"},
             {"label": "Asks first", "value": f"you named {len(ask)}; it's {len(truth['ask'])}"},
             {"label": "Can't run", "value": f"you named {len(blocked)}; it's {len(truth['blocked'])}"}]
    missing = []
    if sorted(ask) != sorted(truth["ask"]):
        missing.append({"id": "ask", "what": "Your 'asks first' list doesn't match the block. Count only the tools that can change things and are switched on."})
    if sorted(blocked) != sorted(truth["blocked"]):
        missing.append({"id": "blocked", "what": "Your 'can't run' list doesn't match the block."})
    if free != len(truth["free"]):
        missing.append({"id": "free", "what": "Your count of tools that run freely doesn't match the block."})
    if missing:
        return fc.outcome(False, "The block reads differently", missing[0]["what"], facts, missing)
    return fc.outcome(True, "You read the block right", "Every tool is in the right column.", facts)


# --------------------------------------------------------------- schedules --


def _job(ctx, name=None):
    name = str(name or _note(ctx).get("job_name") or "").strip()
    found = hermes_read_b.jobs(ctx["home"])
    if not found.get("readable"):
        return found, None
    return found, next((j for j in found["jobs"] if j.get("name") == name), None)


def _need_job(ctx):
    if not str(_note(ctx).get("job_name") or "").strip():
        return fc.cannot_read("Write your job's name, as it shows in Scheduled jobs.")
    found, job = _job(ctx)
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The job list could not be read."))
    if job is None:
        return fc.outcome(False, "No job by that name", f"No scheduled job called {_note(ctx).get('job_name')} in academy-practice.",
                          missing=[{"id": "no_job", "what": "No job by that name in the practice profile."}])
    return None


GOOD = ("list", "count", "summary", "summarize", "one line", "bullet", "table", "each", "total", "number of", "start with")
FAILS = re.compile(r"\[CRON_FAILURE\]|\bif\b[^.]{0,80}\b(?:missing|empty|fail|can't|cannot|not there|no file)", re.I)


def schedules_request_parts(ctx):
    """The job's request covers where to work, what to read, a good result, where it goes and what to do on failure,
    with no phrase that points at a conversation."""
    problem = _need_job(ctx)
    if problem:
        return problem
    _, job = _job(ctx)
    prompt = job.get("prompt_full") or job.get("prompt") or ""
    try_job = _setup(ctx).get("try_job", "late-orders")
    named = plants_b.names_folder_file(ctx["home"], prompt)
    where = bool(named) or bool(job.get("workdir")) or "practice-folder" in prompt or "practice folder" in prompt.lower()
    parts = {"where to work": where, "what to read": bool(named),
             "what a good result looks like": any(w in prompt.lower() for w in GOOD),
             "where it goes": plants_b.deliver_ok(job.get("deliver")), "what to do if it fails": bool(FAILS.search(prompt))}
    vague = plants_b.vague_phrases(prompt)
    facts = [{"label": part.capitalize(), "value": "yes" if ok else "missing"} for part, ok in parts.items()]
    if vague:
        facts.append({"label": "Leans on a conversation", "value": f"\"{vague[0]}\""})
    if job.get("name") == try_job and "the file we just looked at" in prompt.lower():
        what = "That's the try's job. Write your own request, or rewrite this one for a stranger."
        return fc.outcome(False, "Still the try's request", what, facts, [{"id": "try_job", "what": what}])
    gaps = [p for p, ok in parts.items() if not ok]
    if vague or gaps:
        what = (f"The request still says \"{vague[0]}\"; a scheduled run never saw that conversation." if vague
                else f"The request doesn't say {gaps[0]}.")
        return fc.outcome(False, "The request isn't written for a stranger yet", what, facts, [{"id": "parts", "what": what}],
                          evidence=[("job_prompt", "cron/jobs.json", prompt, "")])
    return fc.outcome(True, "The request covers all five parts", "Field Academy found each part in the request.", facts,
                      evidence=[("job_prompt", "cron/jobs.json", prompt, "")])


def _runs(ctx, job):
    return hermes_read_b.runs(ctx["home"], job.get("id")).get("executions", [])


def schedules_tested_paused(ctx):
    """The job's first run was a hand run (no scheduled instant), before any run the schedule fired."""
    problem = _need_job(ctx)
    if problem:
        return problem
    _, job = _job(ctx)
    rows = _runs(ctx, job)
    if not rows:
        what = "The job has never run. Pause it, press Trigger now, read the result, and pause it again."
        return fc.outcome(False, "Not tested yet", what, missing=[{"id": "no_runs", "what": what}])
    first = rows[0]
    facts = [{"label": "First run", "value": "by hand" if not first.get("scheduled_instant") else "fired by the schedule"},
             {"label": "Runs so far", "value": str(len(rows))}]
    if first.get("scheduled_instant"):
        what = "The schedule ran the job before you tested it by hand."
        return fc.outcome(False, "It ran on its own before a test", what, facts, [{"id": "untested", "what": what}])
    return fc.outcome(True, "Tested by hand before its first scheduled run", f"First run {first.get('claimed_at', '')[:16]}, started by hand.", facts,
                      evidence=[("run", "cron/executions.db", f"{first.get('claimed_at')} source={first.get('source')} scheduled_instant=none", "")])


def schedules_model_pinned(ctx):
    """The job has its own model set."""
    problem = _need_job(ctx)
    if problem:
        return problem
    _, job = _job(ctx)
    model = str(job.get("model") or "").strip()
    if model:
        return fc.outcome(True, "The job has its own model", f"Model: {scrub.scrub(model, 120)}.",
                          [{"label": "Model", "value": scrub.scrub(model, 120)}], evidence=[("job", "cron/jobs.json", f"model: {model}", "")])
    what = "The job is on Default, so it follows your main model wherever you move it. Pick a model in Edit cron."
    return fc.outcome(False, "The job is on Default", what, [{"label": "Model", "value": "Default (global model)"}], [{"id": "default", "what": what}])


ON_TIME = 300  # cron/jobs.py:937-959: within 300 seconds is on time


def scheduled_runs(rows) -> list:
    out = []
    for r in rows:
        if r.get("status") == "completed" and r.get("source") == "builtin" and r.get("scheduled_instant"):
            due, claimed = hermes_read_b.iso_epoch(r["scheduled_instant"]), hermes_read_b.iso_epoch(r.get("claimed_at"))
            out.append({**r, "late": bool(due and claimed and claimed - due > ON_TIME), "claimed_epoch": claimed})
    return out


def schedules_two_runs(ctx):
    """At least two completed runs the schedule fired, the last one ok, with the result delivered."""
    problem = _need_job(ctx)
    if problem:
        return problem
    _, job = _job(ctx)
    rows = _runs(ctx, job)
    fired = scheduled_runs(rows)
    outs = hermes_read_b.outputs(ctx["home"], job.get("id")) if str(job.get("deliver") or "local").startswith("local") else None
    facts = [{"label": "Runs the schedule fired", "value": str(len(fired))},
             {"label": "Late runs (catch-up after sleep counts)", "value": str(sum(1 for r in fired if r["late"]))},
             {"label": "Last result", "value": str(job.get("last_status") or "none yet")},
             {"label": "After the runs", "value": "paused" if job.get("enabled") is False else "still on"}]
    hand = [r for r in rows if not r.get("scheduled_instant")]
    if len(fired) >= 2:
        start = hermes_read_b.iso_epoch((hand[0] if hand else rows[0]).get("finished_at") or (hand[0] if hand else rows[0]).get("claimed_at"))
        end = fired[1]["claimed_epoch"]
        if start and end and end > start:
            facts.append({"label": "Waiting for runs", "value": f"{start:.0f}-{end:.0f}"})
    if outs is not None:
        facts.append({"label": "Results delivered to this desktop", "value": str(len(outs))})
    if len(fired) < 2:
        what = (f"{len(fired)} of 2 scheduled runs so far. Resume the job hourly and keep the computer awake; Field Academy "
                "tells you when two have landed.")
        return fc.outcome(False, "Waiting for two scheduled runs", what, facts, [{"id": "runs", "what": what}])
    if job.get("last_status") not in ("ok",):
        what = f"The last run's result is {job.get('last_status')}, not ok."
        return fc.outcome(False, "The last run didn't finish ok", what, facts, [{"id": "status", "what": what}])
    if outs is not None and len(outs) < len(fired):
        what = "A scheduled run has no result file in this desktop's job output."
        return fc.outcome(False, "A result is missing", what, facts, [{"id": "delivery", "what": what}])
    return fc.outcome(True, "Two runs the schedule fired, delivered", "Read from the run history.", facts,
                      evidence=[("run", "cron/executions.db", f"{r.get('scheduled_instant')} claimed {r.get('claimed_at')}{' (late)' if r['late'] else ''}", "")
                                for r in fired[:2]])


def schedules_chained(ctx):
    """Transfer: a second job reads the first job's latest output, delivers somewhere else, and was tested by hand."""
    first_name = str(_note(ctx).get("first_job") or "").strip()
    second_name = str(_note(ctx).get("job_name") or "").strip()
    if not first_name or not second_name:
        return fc.cannot_read("Write the names of both jobs: the first one and the one that reads its output.")
    found, first = _job(ctx, first_name)
    _, second = _job(ctx, second_name)
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The job list could not be read."))
    if first is None or second is None:
        what = "Field Academy couldn't find both jobs by those names."
        return fc.outcome(False, "A job is missing", what, missing=[{"id": "jobs", "what": what}])
    feeds = first.get("id") in (second.get("context_from") or []) or first_name in (second.get("context_from") or [])
    different = str(second.get("deliver") or "local") != str(first.get("deliver") or "local")
    rows = _runs(ctx, second)
    tested = bool(rows) and not rows[0].get("scheduled_instant")
    facts = [{"label": "Reads the first job's output", "value": "yes" if feeds else "no"},
             {"label": "Delivers somewhere else", "value": "yes" if different else "no"},
             {"label": "Tested by hand first", "value": "yes" if tested else "no"}]
    gaps = [label for label, ok in (("read the first job's output", feeds), ("deliver somewhere else", different), ("be tested by hand first", tested)) if not ok]
    if gaps:
        what = f"The second job doesn't {gaps[0]} yet."
        return fc.outcome(False, "The second job isn't set up yet", what, facts, [{"id": "chain", "what": what}])
    return fc.outcome(True, "The second job builds on the first", "It reads the first job's output, delivers elsewhere, and was tested by hand.", facts)


# ------------------------------------------------------------------ safety --


def safety_checkpoints_on(ctx):
    """Checkpoints are on in the practice profile."""
    found = hermes_read_b.settings(ctx["home"])
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The settings could not be read."))
    if found["checkpoints_enabled"]:
        return fc.outcome(True, "Checkpoints are on", "checkpoints.enabled is true in academy-practice.",
                          evidence=[("setting", "config.yaml", "checkpoints.enabled: true", found["sha256"])])
    what = "Checkpoints are off. Turn them on in Settings, Safety, Checkpoints, with Applies to set to academy-practice."
    return fc.outcome(False, "Checkpoints are off", what, missing=[{"id": "off", "what": what}])


PRE_ROLLBACK = "pre-rollback snapshot (restoring to"


def safety_rolled_back(ctx):
    """A snapshot exists for the practice folder (the checkpoint store's branch for it, read here), and the page's
    rollback.list shows the pre-rollback snapshot Hermes takes on every /rollback. The page's reading alone never
    passes; without it the check says how to look by hand."""
    folder = _folder(ctx)
    ref = hermes_read_b.checkpoint_ref(ctx["home"], folder)
    facts = [{"label": "Snapshots for the practice folder", "value": "yes" if ref["exists"] else "none"}]
    if not ref["exists"]:
        what = ("No snapshot of the practice folder. Turn checkpoints on, check the Working folder line passes, then have "
                "Hermes change a file in a new practice chat.")
        return fc.outcome(False, "No snapshot of the practice folder", what, facts, [{"id": "no_snapshot", "what": what}])
    sample = ctx.get("sample") if isinstance(ctx.get("sample"), dict) else {}
    listed = sample.get("checkpoints") if sample.get("source") == "rollback.list" else None
    if not isinstance(listed, list):
        return fc.cannot_read("Field Academy couldn't read the snapshot list from the app. Check it yourself: type /rollback in the "
                              "practice chat; the newest entry should read \"pre-rollback snapshot (restoring to ...)\". Then open "
                              "the file and check it's back.")
    messages = [str((c or {}).get("message", "")) for c in listed if isinstance(c, dict)]
    facts.append({"label": "Snapshots the app listed (reported by the page)", "value": str(len(messages))})
    if any(m.startswith(PRE_ROLLBACK) for m in messages):
        return fc.outcome(True, "You rolled back a change", "The snapshot list shows the safety snapshot /rollback takes. Open the file "
                          "to confirm it's back: Field Academy doesn't compare its contents.", facts,
                          evidence=[("checkpoint", ref["rel_path"], next(m for m in messages if m.startswith(PRE_ROLLBACK)), "")])
    what = "Snapshots exist, but none shows a rollback. Type /rollback, then /rollback 1, and open the file."
    return fc.outcome(False, "No rollback yet", what, facts, [{"id": "no_rollback", "what": what}])


def safety_approvals_safe(ctx):
    """Approvals are smart or manual, and no saved "always" lets a risky delete through."""
    found = hermes_read_b.settings(ctx["home"])
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The settings could not be read."))
    risky = plants_b.risky_allowed(found["command_allowlist"])
    mode = found["approvals_mode"] or "smart"
    facts = [{"label": "Approval mode", "value": mode}, {"label": "Always-allow list", "value": ", ".join(found["command_allowlist"]) or "empty"}]
    if not plants_b.approvals_on(found["approvals_mode"]):
        what = f"Approvals are {mode}, so nothing checks a risky terminal command."
        return fc.outcome(False, "A risky command could run unchecked", what, facts, [{"id": "mode", "what": what}])
    if risky:
        what = f"The always-allow list holds \"{risky[0]}\", so that command runs without asking, in chats and scheduled jobs."
        return fc.outcome(False, "A risky command could run unchecked", what, facts, [{"id": "always", "what": what}])
    return fc.outcome(True, "Nothing lets a risky command run unchecked", f"Approvals are {mode} and the always-allow list holds nothing risky.", facts,
                      evidence=[("setting", "config.yaml", f"approvals.mode: {mode}", found["sha256"])])


GRID = ("tb", "ta", "fb", "fa", "cb", "ca")
GRID_NAMES = {"tb": "Terminal, before", "ta": "Terminal, after", "fb": "File edits, before", "fa": "File edits, after",
              "cb": "Connected tools, before", "ca": "Connected tools, after"}


def grid_truth(found, servers) -> dict:
    undo = "undo" if found["checkpoints_enabled"] else "nothing"
    if not plants_b.approvals_on(found["approvals_mode"]):
        tb = "nothing"
    elif plants_b.risky_allowed(found["command_allowlist"]):
        tb = "some_slip"
    else:
        tb = "asks"
    on = [s for s in servers if s["enabled"]]
    cb = "no_connector" if not on else ("asks" if all(s["trust"] == "untrusted" for s in on) else "nothing")
    return {"tb": tb, "ta": undo, "fb": "nothing", "fa": undo, "cb": cb, "ca": "nothing"}


def grid_choice_words(mission) -> dict:
    """Each grid cell's choices as {value: label}, from the mission's own note fields, so a fact never shows a raw value
    like ``no_connector``. The same cell id carries the same choices in the first lab and the transfer."""
    if not mission:
        from . import foundations_content

        mission = foundations_content.get("f.safety")
    out = {}
    for f in (mission.get("lab") or {}).get("note_fields") or []:
        if f.get("id") in GRID and f.get("kind") == "choice" and f["id"] not in out:
            out[f["id"]] = {c["value"]: c.get("label") or c["value"] for c in f.get("choices") or []}
    return out


def _grid_check(ctx, truth, title_ok):
    note = _note(ctx)
    cells = {k: str(note.get(k) or "").strip() for k in GRID}
    if not all(cells.values()):
        return fc.cannot_read("Fill in all six cells of the grid.")
    wrong = [k for k in GRID if cells[k] != truth[k]]
    words = grid_choice_words(ctx.get("mission"))

    def say(k, value):
        return words.get(k, {}).get(value, value)

    facts = [{"label": GRID_NAMES[k], "value": f"You: {say(k, cells[k])}. The profile: {say(k, truth[k])}."} for k in GRID]
    if wrong:
        what = f"{GRID_NAMES[wrong[0]]} doesn't match the profile as Field Academy read it."
        return fc.outcome(False, f"{len(wrong)} {'cell doesn' if len(wrong) == 1 else 'cells don'}'t match", what, facts,
                          [{"id": f"cell:{k}", "what": f"{GRID_NAMES[k]} doesn't match."} for k in wrong])
    return fc.outcome(True, title_ok, "Every cell matches what Field Academy read.", facts)


def safety_grid_matches(ctx):
    """The learner's six-cell grid matches the practice profile's settings as Field Academy reads them."""
    found = hermes_read_b.settings(ctx["home"])
    servers = hermes_read_b.mcp_servers(ctx["home"])
    if not found.get("readable") or not servers.get("readable"):
        return fc.cannot_read("The practice profile's settings could not be read.")
    return _grid_check(ctx, grid_truth(found, servers["servers"]), "Your grid matches the profile")


SHARED = {"tb": "asks", "ta": "undo", "fb": "nothing", "fa": "undo", "cb": "asks", "ca": "nothing"}


def safety_shared_grid(ctx):
    """Transfer: the grid for a shared office computer with an invoice-sending email connector, set up as this mission
    teaches (approvals on, checkpoints on, the email connector untrusted)."""
    out = _grid_check(ctx, SHARED, "Your grid for the shared computer holds up")
    worry = str(_note(ctx).get("worry") or "").strip()
    if out["passed"] and len(worry) < 15:
        what = "Name the cell you'd worry about most, and the setting that shrinks that worry."
        return fc.outcome(False, "Say which cell worries you most", what, out["facts"], [{"id": "worry", "what": what}])
    return out


# ---------------------------------------------------------------- diagnose --


LAYER_WORDS = {"model": "model", "connector": "connector", "scheduled job": "scheduled job", "tool": "tool", "app": "app"}


def _variant(ctx):
    planted = ctx.get("planted") or {}
    kind = next((k for k in sorted(planted) if k in plants_b.LAYERS), None)
    return kind, planted.get(kind, {}) if kind else {}


def diagnose_layer_named(ctx):
    """The learner named the layer that failed in round two."""
    kind, _ = _variant(ctx)
    if not kind:
        return fc.cannot_read("Field Academy has no record of round two's break.")
    said = str(_note(ctx).get("layer") or "").strip().lower()
    if not said:
        return fc.cannot_read("Say which layer failed.")
    truth = plants_b.LAYERS[kind]
    if said == truth:
        return fc.outcome(True, "You named the layer", f"The break was in the {truth}.")
    what = f"You named the {said}. Look again at what the card, the doctor and the logs each ruled out."
    return fc.outcome(False, "A different layer failed", what, missing=[{"id": "layer", "what": what}])


def _norm(text) -> str:
    return " ".join(scrub.scrub(str(text or ""), 2000).split()).lower()


def diagnose_line_quoted(ctx):
    """The quoted line is in the practice profile's logs (or a rotated copy), after the break was set up, and it
    points at the layer that failed."""
    kind, details = _variant(ctx)
    quote = _norm(_note(ctx).get("quote"))
    if not kind:
        return fc.cannot_read("Field Academy has no record of round two's break.")
    if len(quote) < 12:
        return fc.cannot_read("Paste the log line you found, at least a few words of it.")
    since = _planted_epoch(ctx)
    lines = hermes_read_b.log_lines(ctx["home"], ("errors.log", "agent.log", "mcp-stderr.log"), 2000)["lines"]
    hit = next((i for i in reversed(lines) if quote in _norm(i["line"]) and (since is None or i["time"] is None or i["time"] >= since - 5)), None)
    if hit is None:
        what = "That line isn't in academy-practice's logs. Check the folder's path names academy-practice, and copy the line exactly."
        return fc.outcome(False, "The line isn't in the practice profile's logs", what, missing=[{"id": "not_found", "what": what}])
    low = hit["line"].lower()
    points = ("mcp server" in low and details.get("server", "") in hit["line"]) if kind == "broken_connector" else \
        ("job" in low and (details.get("job", "") in hit["line"] or "blocked" in low))
    if not points:
        what = "The line is in the logs, but it's about something else. Find the one that names what broke."
        return fc.outcome(False, "The line points somewhere else", what, missing=[{"id": "elsewhere", "what": what}],
                          evidence=[("log_line", hit["file"], hit["line"], "")])
    return fc.outcome(True, "The line is there, and it names the break", f"Found in {hit['file']}.",
                      evidence=[("log_line", hit["file"], hit["line"], "")])


def _fix_time(ctx, kind):
    if kind == "job_blocked":
        return hermes_read_b.jobs(ctx["home"]).get("mtime")
    return (hermes_read_b.mcp_servers(ctx["home"]) or {}).get("mtime")


def diagnose_backup_first(ctx):
    """A backup (a zip in backups/ or a quick snapshot) was made after the break was set up and before the fix."""
    kind, details = _variant(ctx)
    if not kind:
        return fc.cannot_read("Field Academy has no record of round two's break.")
    fixed = plants.verify(kind, ctx["home"], details, "", _note(ctx))
    if not fixed["fixed"]:
        what = "The break isn't fixed yet, so there's no fix to have backed up before."
        return fc.outcome(False, "Not fixed yet", what, missing=[{"id": "not_fixed", "what": what}])
    when = _fix_time(ctx, kind)
    since = _planted_epoch(ctx)
    items = hermes_read_b.backups(ctx["home"])["items"]
    before = [i for i in items if (since is None or i["mtime"] >= since - 5) and (when is None or i["mtime"] <= when)]
    facts = [{"label": "Backups in the practice profile", "value": str(len(items))}, {"label": "Made before the fix", "value": str(len(before))}]
    if before:
        return fc.outcome(True, "A backup came before the fix", f"{before[-1]['kind'].capitalize()}: {before[-1]['name']}.", facts,
                          evidence=[("backup", before[-1]["rel_path"], f"{before[-1]['kind']} {before[-1]['name']}", "")])
    what = "No backup was made before the fix. Next time: Create backup first, then change one thing."
    return fc.outcome(False, "No backup before the fix", what, facts, [{"id": "no_backup", "what": what}])


def diagnose_works_after(ctx):
    """After the fix, a new chat got an answer (connector break) or the job's next run completed (job break)."""
    kind, details = _variant(ctx)
    if not kind:
        return fc.cannot_read("Field Academy has no record of round two's break.")
    when = _fix_time(ctx, kind)
    if kind == "job_blocked":
        found = hermes_read_b.jobs(ctx["home"])
        job = next((j for j in found.get("jobs", []) if j.get("name") == details.get("job")), None)
        rows = hermes_read_b.runs(ctx["home"], job.get("id")).get("executions", []) if job else []
        done = [r for r in rows if r.get("status") == "completed" and (when is None or (hermes_read_b.iso_epoch(r.get("claimed_at")) or 0) >= when)]
        if job is None:
            return fc.outcome(True, "The job was removed", "With the job gone there's nothing left to run.")
        if done and job.get("last_status") == "ok":
            return fc.outcome(True, "The job's next run worked", f"Run at {done[-1].get('claimed_at')}, result ok.",
                              evidence=[("run", "cron/executions.db", f"{done[-1].get('claimed_at')} completed, ok", "")])
        what = "No completed run of the job since the fix. Trigger it, or wait for the top of the hour."
        return fc.outcome(False, "No good run since the fix", what, missing=[{"id": "no_run", "what": what}])
    later = _sessions_after(ctx["home"], when)
    if later is None:
        return fc.cannot_read("The chat records could not be read.")
    for session in later:
        msgs = hermes_read.messages(ctx["home"], session["id"]).get("messages", [])
        reply = next((m for m in msgs if m.get("role") == "assistant" and str(m.get("content") or "").strip()), None)
        if reply:
            return fc.outcome(True, "A new chat worked after the fix", "Hermes answered in a chat started after the fix.",
                              evidence=[("session", "state.db", str(reply.get("content"))[:200], "")])
    what = "No chat started after the fix has an answer yet. Press Open practice chat and send hello."
    return fc.outcome(False, "No new chat after the fix", what, missing=[{"id": "no_chat", "what": what}])


def diagnose_round_one(ctx):
    """Round one, for comparison and never graded: when the model typo was fixed (the first chat that got an answer)
    and whether a backup came first."""
    typo = _setup(ctx).get("typo")
    found = hermes_read_b.settings(ctx["home"])
    if not typo or not found.get("readable"):
        return fc.cannot_read("Field Academy has no record of round one's break.")
    since = _planted_epoch(ctx)
    sessions = _sessions_after(ctx["home"], None) or []
    answered = None
    for session in sessions:
        msgs = hermes_read.messages(ctx["home"], session["id"]).get("messages", [])
        if any(m.get("role") == "assistant" and str(m.get("content") or "").strip() for m in msgs):
            answered = session["started_at"]
            break
    items = hermes_read_b.backups(ctx["home"])["items"]
    minutes = round((answered - since) / 60) if answered and since else None
    facts = [{"label": "Model name", "value": "still the broken one" if found["model"] == typo else "fixed"},
             {"label": "Minutes to the first answer", "value": str(minutes) if minutes is not None else "no answer yet"},
             {"label": "Backup before that", "value": "yes" if answered and any(i["mtime"] <= answered for i in items) else "no"}]
    return fc.outcome(True, "Round one, shown for comparison", "Not graded: the four checks are about round two.", facts)


# ------------------------------------------------------------------ review --


MARK = re.compile(r"\b(held|didn'?t|did not|wrong|false|true|failed|no)\b\W*$", re.I)


def _lines(text) -> list:
    return [line.strip(" -*\t") for line in str(text or "").splitlines() if line.strip(" -*\t")]


def _final_answer(home):
    listed = hermes_read.sessions(home)
    for session in reversed(listed.get("sessions", []) if listed.get("readable") else []):
        msgs = hermes_read.messages(home, session["id"]).get("messages", [])
        last = next((m for m in reversed(msgs) if m.get("role") == "assistant" and str(m.get("content") or "").strip()), None)
        if last:
            return str(last["content"])
    return ""


def review_claims_checked(ctx):
    """Account 1: the learner listed the claims in Hermes's final answer, each marked held or didn't, and what Field
    Academy can test against the files agrees. Coverage of every claim is shown as written, not graded here."""
    claims = _lines(_note(ctx).get("claims"))
    wrong = str(_note(ctx).get("wrong") or "").strip()
    final = _final_answer(ctx["home"])
    if not claims:
        return fc.cannot_read("List each claim in Hermes's final answer, one per line, ending with held or didn't.")
    if not final:
        return fc.outcome(False, "No final answer to check against", "No chat in academy-practice has an answer yet.",
                          missing=[{"id": "no_answer", "what": "No chat in academy-practice has an answer yet."}])
    files = {Path(f["rel"]).name.lower(): f for f in hermes_read_b.folder_files(ctx["home"]).get("files", [])}
    unmarked = [c for c in claims if not MARK.search(c)]
    tested, clash = 0, []
    for claim in claims:
        names = re.findall(r"[\w.-]+\.(?:csv|md|txt|json|xlsx|docx|pdf)\b", claim.lower())
        if not names:
            continue
        tested += 1
        held = bool(re.search(r"\bheld\b|\btrue\b", claim, re.I))
        if held and not any(n in files for n in names):
            clash.append(claim)
    facts = [{"label": "Claims you listed", "value": str(len(claims))}, {"label": "Tested against the files here", "value": str(tested)},
             {"label": "Coverage of the final answer", "value": "shown as written; your Hermes grading it isn't built yet"}]
    missing = []
    if unmarked:
        missing.append({"id": "unmarked", "what": f"Mark each claim held or didn't: \"{unmarked[0][:60]}\"."})
    if clash:
        missing.append({"id": "clash", "what": f"You marked \"{clash[0][:60]}\" held, but that file isn't in the practice folder."})
    if len(wrong) < 10:
        missing.append({"id": "wrong", "what": "Write what was wrong with the result, or say plainly that you checked and found nothing."})
    if missing:
        return fc.outcome(False, "Account 1 isn't complete", missing[0]["what"], facts, missing)
    return fc.outcome(True, "Account 1: the claims are checked", "Each claim is marked, and the files agree where Field Academy can test them.", facts,
                      evidence=[("session", "state.db", final[:300], "")])


INHERIT = re.compile(r"\b(main|same|inherit\w*|parent|empty|blank|default)\b", re.I)
NONE = re.compile(r"\b(none|no\b|n/?a|not set|empty|nothing)\b", re.I)


def _mentions_model(text, model) -> bool:
    model = str(model or "")
    tail = model.rsplit("/", 1)[-1].lower()
    return bool(tail) and tail in str(text or "").lower()


def review_models_match(ctx):
    """Account 2: main model, backups, helper agents and a job's own model match the profile's settings, and helper
    agents the learner says ran did run (a chat with a parent, in the chat records)."""
    note = _note(ctx)
    if not str(note.get("main_model") or "").strip():
        return fc.cannot_read("Write each model: main, backups, helper agents and the job's own, if any.")
    found = hermes_read_b.settings(ctx["home"])
    if not found.get("readable"):
        return fc.cannot_read(found.get("why", "The settings could not be read."))
    jobs = [j for j in hermes_read_b.jobs(ctx["home"]).get("jobs", []) if str(j.get("model") or "").strip()]
    listed = hermes_read.sessions(ctx["home"])
    children = [s for s in listed.get("sessions", []) if s.get("parent_session_id")] if listed.get("readable") else []
    checks = {
        "Main model": _mentions_model(note.get("main_model"), found["model"]),
        "Backup models": (all(_mentions_model(note.get("fallback"), f) for f in found["fallbacks"]) if found["fallbacks"]
                          else bool(NONE.search(str(note.get("fallback") or "")))),
        "Helper agents": (_mentions_model(note.get("subagents"), found["delegation_model"]) if found["delegation_model"]
                          else bool(INHERIT.search(str(note.get("subagents") or ""))) or _mentions_model(note.get("subagents"), found["model"])),
        "The job's own model": (all(_mentions_model(note.get("job_model"), j["model"]) for j in jobs) if jobs
                                else bool(NONE.search(str(note.get("job_model") or "")))),
    }
    ran = str(note.get("subagents_ran") or "").strip().lower()
    if ran in ("yes", "no"):
        checks["Helper agents ran"] = (ran == "yes") == bool(children)
    facts = [{"label": k, "value": "matches" if ok else "doesn't match the settings"} for k, ok in checks.items()]
    facts.append({"label": "Helper-agent chats in the records", "value": str(len(children))})
    off = [k for k, ok in checks.items() if not ok]
    if off:
        what = f"{off[0]}: what you wrote doesn't match academy-practice's settings."
        return fc.outcome(False, "Account 2 doesn't match the settings", what, facts, [{"id": "model", "what": what}])
    return fc.outcome(True, "Account 2 matches the settings", "Each model you listed is what the profile has.", facts)


def baseline(home) -> dict:
    """What Field Academy records about a practice profile at Start (mission 11): memory lines, skills, pending."""
    mem = hermes_read.memory(home)
    skills = hermes_read.skills(home)
    pending = hermes_read.pending(home)
    return {
        "memory": [scrub.scrub(e, 400) for e in (mem["memory"]["entries"] if mem.get("readable") else [])],
        "user": [scrub.scrub(e, 400) for e in (mem["user"]["entries"] if mem.get("readable") else [])],
        "skills": [{"name": s["name"], "sha256": s["sha256"]} for s in skills.get("skills", [])],
        "pending": [{"kind": k, "id": r["id"], "summary": r["summary"]} for k in ("memory", "skills") for r in pending.get(k, [])],
    }


def diff(before: dict, after: dict) -> list:
    """Every memory line and skill that is new, changed or gone, and anything waiting that wasn't."""
    out = []
    for key, label in (("memory", "MEMORY.md"), ("user", "USER.md")):
        was, now = before.get(key) or [], after.get(key) or []
        out += [{"what": f"{label}: {line}", "text": line, "change": "new"} for line in now if line not in was]
        out += [{"what": f"{label}: {line}", "text": line, "change": "gone"} for line in was if line not in now]
    was = {s["name"]: s["sha256"] for s in before.get("skills") or []}
    now = {s["name"]: s["sha256"] for s in after.get("skills") or []}
    out += [{"what": f"skill {n}", "text": n, "change": "new" if n not in was else "changed"} for n in now if was.get(n) != now[n]]
    out += [{"what": f"skill {n}", "text": n, "change": "gone"} for n in was if n not in now]
    was_ids = {p["id"] for p in before.get("pending") or []}
    out += [{"what": f"waiting {p['kind']}: {p['summary']}", "text": p["summary"], "change": "waiting"} for p in after.get("pending") or [] if p["id"] not in was_ids]
    return out


def _asked(home, text) -> bool:
    for m in hermes_read.messages(home).get("messages", []):
        calls = str(m.get("tool_calls") or "")
        if m.get("role") == "assistant" and ('"memory"' in calls or "skill_manage" in calls) and matching.overlap(calls, text) >= 0.5:
            return True
    return False


def review_self_edits(ctx):
    """Account 3: every memory line and skill that changed since the Start snapshot, and anything now waiting, is on
    the learner's list, and each "asked" matches a memory or skill call in the chat records."""
    start = (_row(ctx).get("plan") or {}).get("baseline")
    if not isinstance(start, dict):
        return fc.cannot_read("Field Academy has no Start snapshot for this practice profile.")
    changes = diff(start, baseline(ctx["home"]))
    lines = _lines(_note(ctx).get("edits"))
    if not lines:
        return fc.cannot_read("List every memory line and skill that changed since Start, with asked, on its own or mine. "
                              "If nothing changed, write that.")
    missing, clash = [], []
    for change in changes:
        line = next((l for l in lines if matching.overlap(l, change["text"]) >= 0.5 or change["text"].lower() in l.lower()), None)
        if line is None:
            missing.append(change)
            continue
        said_asked = bool(re.search(r"\basked\b", line, re.I))
        if change["change"] == "new" and said_asked and not _asked(ctx["home"], change["text"]):
            clash.append(change)
    facts = [{"label": "Changes since Start", "value": str(len(changes))}, {"label": "On your list", "value": str(len(changes) - len(missing))}]
    if missing:
        what = f"Not on your list: {missing[0]['what'][:120]} ({missing[0]['change']})."
        return fc.outcome(False, "Account 3 misses a change", what, facts, [{"id": "unlisted", "what": what}])
    if clash:
        what = f"You marked \"{clash[0]['text'][:60]}\" asked, but no chat shows a save for it. It may have been made on its own."
        return fc.outcome(False, "Account 3: one source looks wrong", what, facts, [{"id": "source", "what": what}])
    return fc.outcome(True, "Account 3 covers every change", "Each change since Start is on your list.", facts)


def review_can_claim_read(ctx):
    """Transfer: the learner read the list of what they can now claim and named the claim a reviewer should look at
    first, and why. Shown as written."""
    text = str(_note(ctx).get("claim_review") or "").strip()
    if len(text) < 20:
        return fc.cannot_read("Name the claim you'd want a reviewer to look at first, and why, in a sentence or two.")
    return fc.outcome(True, "You read your claims", "Your note is kept as you wrote it.")


READERS = {
    "plants.all_fixed": plants_all_fixed,
    "connectors.one_scoped": connectors_one_scoped,
    "connectors.untrusted": connectors_untrusted,
    "connectors.refusal_seen": connectors_refusal_seen,
    "connectors.clean_start": connectors_clean_start,
    "connectors.folder_outcome": connectors_folder_outcome,
    "connectors.reading": connectors_reading,
    "schedules.request_parts": schedules_request_parts,
    "schedules.tested_paused": schedules_tested_paused,
    "schedules.model_pinned": schedules_model_pinned,
    "schedules.two_runs": schedules_two_runs,
    "schedules.chained": schedules_chained,
    "safety.checkpoints_on": safety_checkpoints_on,
    "safety.rolled_back": safety_rolled_back,
    "safety.approvals_safe": safety_approvals_safe,
    "safety.grid_matches": safety_grid_matches,
    "safety.shared_grid": safety_shared_grid,
    "diagnose.layer_named": diagnose_layer_named,
    "diagnose.line_quoted": diagnose_line_quoted,
    "diagnose.backup_first": diagnose_backup_first,
    "diagnose.works_after": diagnose_works_after,
    "diagnose.round_one": diagnose_round_one,
    "review.claims_checked": review_claims_checked,
    "review.models_match": review_models_match,
    "review.self_edits": review_self_edits,
    "review.can_claim_read": review_can_claim_read,
}
