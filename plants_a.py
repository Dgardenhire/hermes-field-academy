"""Planted problems for Foundations missions 1, 2, 4, 5 and 6 (0.9 M6, part A): planter, detector, fix-verifier.

The same contract as plants.py, whose REGISTRY takes these in. Every write goes through practice_write.py, into a
recorded practice profile before its first chat. Names, numbers and the planted value vary with the learner's seed
(decisions from review 2), drawn from the attempt's own seed so a reset with the same attempt plants the same thing.

Each mission also needs things every learner gets, whatever was drawn: mission 1's warm-up notes and job sheets,
mission 2's job file, mission 5's hand-written skill, mission 6's notes file outside both profiles. Each planter
writes that **base** first (the same for every kind of the mission, written once) and returns it under ``base``, so
the checks and the page find it in whatever was planted.

Kinds, by mission (source: .planning/field-academy-v3/missions/0N-*.v2.md, build notes):

* mission 1 ``output_locked``: the output file already exists with last week's figures and is Locked (Mac), Read-only
  (Windows) or not writable (Linux). ``input_empty``: one of the three sheets is a header row and nothing else.
  ``rows_short``: the card asks for every one of N jobs and the sheets hold N - 2.
* mission 2 ``extra_connector``: the reference filesystem server, switched on and never used by the job.
  ``unused_skills``: a pack of twelve skills for another line of work, on, never opened by the job; the same connector
  is there too, switched off, so the page's warning about it is true whichever was drawn. (Two more variants are
  held, see the mission's ``lab.held``.)
* mission 4 ``soul_wrong_profile``: a second practice profile beside the first; editing its SOUL.md is the trap.
* mission 5 ``steps_in_memory``: a three-step procedure as one memory line. ``greedy_neighbor``: a second hand-made
  skill whose description matches almost any request.
* mission 6 ``cloned_memory``: a client fact in A's memory, then B made with ``clone_from: academy-practice`` (the
  narrow exception: the source is a practice profile Field Academy recorded). ``decoy_in_b``: the same kind of line
  written straight into B's memory.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

from . import hermes_read, hermes_read_a, matching, practice, practice_write

FS_SERVER_PACKAGE = "@modelcontextprotocol/server-filesystem@2026.8.31"  # the pin mission 7 uses; 14 tools
FOLDER = hermes_read_a.FOLDER


def _seed(row) -> str:
    """The attempt's seed, for draws every kind of a mission must agree on."""
    try:
        with practice._conn() as conn:
            found = conn.execute("SELECT seed FROM f_attempts WHERE id = ?", (int(row.get("attempt_id") or 0),)).fetchone()
        if found and found["seed"]:
            return str(found["seed"])
    except Exception:  # noqa: BLE001 - a missing attempt only changes which names are drawn
        pass
    return str((row.get("plan") or {}).get("token") or row.get("name"))


def _rng(row, what) -> random.Random:
    return random.Random(f"field-academy-foundations-a:{_seed(row)}:{what}")


def _base_done(home, rel) -> bool:
    return (Path(home) / rel).exists()


def _full(home, rel) -> str:
    return str((Path(home) / rel).resolve(strict=False))


def _partner(name_a: str = ""):
    """The second practice profile (``which: b``) Field Academy recorded and hasn't removed, or None."""
    with practice._conn() as conn:
        rows = [practice._row(conn, r["name"]) for r in conn.execute("SELECT name FROM f_practice WHERE status IN ('ready', 'planted')")]
    return next((r for r in rows if r and r["plan"].get("which") == "b" and Path(r.get("path", "")).is_dir()), None)


def _messages(home):
    found = hermes_read.messages(home)
    return found.get("messages", []) if found.get("readable") else []


# ===================================================================== mission 1 ==

DAYS = (("monday", "tuesday", "wednesday"), ("tuesday", "wednesday", "thursday"), ("wednesday", "thursday", "friday"))
CLIENTS = ("Alder St", "Birch Rd", "Cedar Ct", "Dunmore Ave", "Elm Row", "Fenwick Pl", "Grange Ln", "Hollow Way", "Iris Close")
PREFIXES = ("JB", "WO", "SV", "PL")
WARM = (
    ("delivery-note.md", "Delivery note. The boiler parts arrive on {d1}. The fitter booked for {d2} can start then."),
    ("staff-rota.md", "Rota change. Sam covers {d1} and {d2}; Ari covers {d3}. Nobody is off on {d4}."),
    ("supplier-call.md", "Supplier call. Prices hold until {d1}. Ask again before {d2}. New catalogue {d3}."),
    ("site-visit.md", "Site visit notes. The roof was checked; the gutter needs clearing before winter."),
)
MONTHS = ("March", "April", "May", "June", "September", "October")
M1_JOB = f"{FOLDER}/job"
M1_TRANSFER = f"{FOLDER}/job-2"


def _m1_base(ctx) -> dict:
    """Warm-up notes, the three job sheets and the transfer's price lists. Drawn from the seed, written once."""
    home, row = ctx["home"], ctx["row"]
    rng = _rng(row, "m1-base")
    write = not _base_done(home, f"{FOLDER}/warm-up/{WARM[0][0]}")
    month = rng.choice(MONTHS)
    warm = []
    for name, text in WARM:
        days = sorted(rng.sample(range(1, 29), 4))
        body = text.format(**{f"d{i + 1}": f"{d} {month}" for i, d in enumerate(days)}) + "\n"
        warm.append((name, body))
    days = rng.choice(DAYS)
    prefix = rng.choice(PREFIXES)
    numbers = rng.sample(range(101, 999), rng.randint(16, 21))
    sheets = {d: [] for d in days}
    for i, number in enumerate(numbers):
        sheets[days[i % 3]].append({"job": f"{prefix}-{number}", "client": rng.choice(CLIENTS), "hours": rng.randint(1, 6),
                                    "paid": "no" if rng.random() < 0.15 else "yes"})
    a, b = rng.sample(range(4, 9), 2)
    prices = {"bolts": (a, b), "washers": (b, a + 1), "hinges": (a + 2, b + 2)}
    if write:
        for name, body in warm:
            practice_write.write_work_file_a(home, row, f"{FOLDER}/warm-up/{name}", body)
        for day, rows in sheets.items():
            practice_write.write_work_file_a(home, row, f"{M1_JOB}/{day}.csv", _csv(rows))
        for n, which in ((0, "a"), (1, "b")):
            practice_write.write_work_file_a(home, row, f"{M1_TRANSFER}/supplier-{which}.csv",
                                             "item,price\n" + "".join(f"{k},{v[n]}\n" for k, v in prices.items()))
    return {"mission": "f.loop", "days": list(days), "prefix": prefix, "stated": len(numbers), "job_rel": M1_JOB,
            "job_path": _full(home, M1_JOB), "warm_path": _full(home, f"{FOLDER}/warm-up"), "transfer_rel": M1_TRANSFER,
            "transfer_path": _full(home, M1_TRANSFER), "output": f"{M1_JOB}/summary.md",
            "warm_dates": {name: len(re.findall(r"\d+ [A-Z][a-z]+", body)) for name, body in warm}}


def _csv(rows) -> str:
    return "job,client,hours,paid\n" + "".join(f"{r['job']},{r['client']},{r['hours']},{r['paid']}\n" for r in rows)


def card_m1(base) -> str:
    return (f"Read the three job sheets in {base['job_path']}. Write summary.md in that folder with one line for each of "
            f"the {base['stated']} jobs (job number, client, hours), then the total hours and any job marked unpaid.")


def card_m1_transfer(base) -> str:
    return (f"Read the two supplier price lists in {base['transfer_path']}. Write compare.md in that folder: each item, "
            "both prices, and which supplier is cheaper for it.")


def sheet_rows(home, base) -> dict:
    """The job sheets as they are now: {file name: [rows]}."""
    out = {}
    for day in base.get("days", []):
        found = hermes_read_a.work_file(home, f"{base['job_rel']}/{day}.csv")
        lines = found.get("text", "").splitlines()[1:] if found.get("exists") else []
        out[f"{day}.csv"] = [dict(zip(("job", "client", "hours", "paid"), line.split(","))) for line in lines if line.count(",") == 3]
    return out


def _plant_output_locked(ctx) -> dict:
    base = _m1_base(ctx)
    rng = _rng(ctx["row"], "m1-locked")
    stale = [f"{base['prefix']}-{n}" for n in rng.sample(range(10, 99), 5)]
    hours = rng.randint(30, 60)
    text = "# Weekly summary (last week)\n\n" + "".join(f"- {j}\n" for j in stale) + f"\nTotal hours: {hours}\n"
    practice_write.write_work_file_a(ctx["home"], ctx["row"], base["output"], text)
    practice_write.lock_work_file_a(ctx["home"], ctx["row"], base["output"])
    return {"base": base, "rel": base["output"], "stale_jobs": stale, "stale_hours": hours}


def _plant_input_empty(ctx) -> dict:
    base = _m1_base(ctx)
    sheets = sheet_rows(ctx["home"], base)
    name = _rng(ctx["row"], "m1-empty").choice(sorted(n for n, rows in sheets.items() if rows))
    practice_write.write_work_file_a(ctx["home"], ctx["row"], f"{base['job_rel']}/{name}", "job,client,hours,paid\n")
    return {"base": base, "empty": name}


def _plant_rows_short(ctx) -> dict:
    base = _m1_base(ctx)
    sheets = sheet_rows(ctx["home"], base)
    biggest = max(sorted(sheets), key=lambda n: len(sheets[n]))
    kept = sheets[biggest][:-2]
    practice_write.write_work_file_a(ctx["home"], ctx["row"], f"{base['job_rel']}/{biggest}", _csv(kept))
    return {"base": base, "short_file": biggest, "removed": [r["job"] for r in sheets[biggest][-2:]]}


def job_chat(home, folder_rel, folder_path, after=None, last=False):
    """The chat whose first message names the job folder (by full path, or by its folder name)."""
    listed = hermes_read.sessions(home)
    found = []
    for session in listed.get("sessions", []) if listed.get("readable") else []:
        if after is not None and (session.get("started_at") or 0) < after:
            continue
        rows = hermes_read.messages(home, session["id"]).get("messages", [])
        first = next((m for m in rows if m.get("role") == "user"), None)
        text = str((first or {}).get("content") or "")
        if folder_path and folder_path in text or folder_rel and folder_rel in text.replace("\\", "/"):
            found.append((session, rows))
    if not found:
        return None, []
    return found[-1] if last else found[0]


def _final_answer(rows) -> str:
    said = [m for m in rows if m.get("role") == "assistant" and str(m.get("content") or "").strip()]
    return str(said[-1].get("content") or "") if said else ""


def hermes_unlocked(rows, output_name="summary.md") -> bool:
    """Did Hermes clear the lock itself, with a terminal command aimed at the output file?"""
    for m in rows:
        calls = str(m.get("tool_calls") or "")
        if m.get("role") == "assistant" and "terminal" in calls and output_name in calls and re.search(r"chmod|chflags|attrib|icacls", calls):
            return True
    return False


def m1_output(home, planted: dict, chat_start) -> dict:
    """Is the output right now? Exists, writable, written after the job started, every real job and no other, the true
    total, and a plain line naming an empty input or a short count."""
    base = next((d["base"] for d in planted.values() if isinstance(d, dict) and d.get("base", {}).get("mission") == "f.loop"), None)
    if not base:
        return {"ok": False, "why": "Field Academy has no record of the job it set up."}
    out = hermes_read_a.work_file(home, base["output"])
    if not out.get("exists"):
        return {"ok": False, "why": "summary.md isn't in the job folder."}
    if out.get("locked"):
        return {"ok": False, "why": "summary.md is still locked, so nothing could have written it."}
    if chat_start and out["mtime"] < chat_start:
        return {"ok": False, "why": "summary.md is older than the job: it's a copy from before you sent the request."}
    text = out["text"]
    sheets = sheet_rows(home, base)
    present = [r for rows in sheets.values() for r in rows]
    ids = {r["job"] for r in present}
    named = set(re.findall(rf"\b{re.escape(base['prefix'])}-\d+\b", text))
    missing, extra = sorted(ids - named), sorted(named - ids)
    if missing:
        return {"ok": False, "why": f"summary.md leaves out {len(missing)} real {'job' if len(missing) == 1 else 'jobs'}, such as {missing[0]}."}
    if extra:
        return {"ok": False, "why": f"summary.md lists a job that isn't in the sheets: {extra[0]}."}
    total = sum(int(r["hours"]) for r in present if r["hours"].isdigit())
    if str(total) not in re.findall(r"\d+", text):
        return {"ok": False, "why": "summary.md doesn't give the true total hours."}
    empty = [name for name, rows in sheets.items() if not rows]
    for name in empty:
        if name.lower() not in text.lower() and Path(name).stem.lower() not in text.lower():
            return {"ok": False, "why": f"One sheet is empty, and summary.md doesn't say which."}
    if not empty and len(present) < base["stated"] and str(len(present)) not in re.findall(r"\d+", text):
        return {"ok": False, "why": "The sheets hold fewer jobs than the request asked for, and summary.md doesn't say how many there are."}
    return {"ok": True, "why": "summary.md is fresh, lists every real job and no other, and gives the true total."}


def _detect_output_locked(home, details) -> dict:
    base = details.get("base", {})
    out = hermes_read_a.work_file(home, details.get("rel", ""))
    _session, rows = job_chat(home, base.get("job_rel"), base.get("job_path"))
    failed = any(m.get("role") == "tool" and m.get("tool_name") in ("write_file", "patch") and re.search(r"denied|not permitted|read-only|error", str(m.get("content")), re.I) for m in rows)
    stale = out.get("exists") and any(j in out.get("text", "") for j in details.get("stale_jobs", []))
    return {"fired": bool(rows) and (failed or stale or hermes_unlocked(rows)),
            "facts": [{"label": "summary.md still last week's", "value": "yes" if stale else "no"},
                      {"label": "A save in the job failed", "value": "yes" if failed else "no"},
                      {"label": "Hermes cleared the lock itself", "value": "yes" if hermes_unlocked(rows) else "no"}],
            "evidence": [("work_file", details.get("rel", ""), out.get("text", ""))] if stale else []}


def _detect_input_empty(home, details) -> dict:
    _s, rows = job_chat(home, details.get("base", {}).get("job_rel"), details.get("base", {}).get("job_path"))
    answer = _final_answer(rows)
    admitted = bool(answer) and (details.get("empty", "") in answer or "empty" in answer.lower())
    return {"fired": bool(rows), "facts": [{"label": "Empty sheet", "value": details.get("empty", "")},
                                           {"label": "The answer said so", "value": "yes" if admitted else "no"}], "evidence": []}


def _detect_rows_short(home, details) -> dict:
    base = details.get("base", {})
    _s, rows = job_chat(home, base.get("job_rel"), base.get("job_path"))
    present = sum(len(r) for r in sheet_rows(home, base).values())
    return {"fired": bool(rows), "facts": [{"label": "Jobs the request asked for", "value": str(base.get("stated", ""))},
                                           {"label": "Jobs in the sheets", "value": str(present)}], "evidence": []}


def _verify_m1(home, details, fact, note=None) -> dict:
    base = details.get("base", {})
    session, _rows = job_chat(home, base.get("job_rel"), base.get("job_path"))
    result = m1_output(home, {"x": details}, (session or {}).get("started_at"))
    return {"fixed": result["ok"], "why": result["why"]}


# ===================================================================== mission 2 ==

M2_JOB = f"{FOLDER}/orders"
CONNECTOR_NAMES = ("academy-files", "academy-archive", "academy-shared-drive")


def _m2_base(ctx) -> dict:
    home, row = ctx["home"], ctx["row"]
    rng = _rng(row, "m2-base")
    amounts = [f"{rng.randint(800, 9900) / 100:.2f}" for _ in range(rng.randint(7, 12))]
    numbers = rng.sample(range(1000, 9999), len(amounts))
    if not _base_done(home, f"{M2_JOB}/orders.csv"):
        practice_write.write_work_file_a(home, row, f"{M2_JOB}/orders.csv", "order,amount\n" + "".join(f"A{n},{a}\n" for n, a in zip(numbers, amounts)))
    return _m2_info(home, amounts)


def _m2_info(home, amounts) -> dict:
    total = sum(round(float(a) * 100) for a in amounts) / 100
    return {"mission": "f.cost", "job_rel": M2_JOB, "job_path": _full(home, M2_JOB), "orders": len(amounts), "total": f"{total:.2f}",
            "output": f"{M2_JOB}/totals.md"}


def card_m2(base) -> str:
    return (f"Read {base['job_path']}/orders.csv. Write totals.md in that folder with the number of orders and the total "
            "of the amount column.")


def m2_output(home, base, chat_start) -> dict:
    out = hermes_read_a.work_file(home, base["output"])
    if not out.get("exists"):
        return {"ok": False, "why": "totals.md isn't in the orders folder."}
    if chat_start and out["mtime"] < chat_start:
        return {"ok": False, "why": "totals.md is older than the last job chat."}
    numbers = {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", out["text"])}
    total = base["total"]
    if not ({total, total.rstrip("0").rstrip("."), f"{float(total):,.2f}".replace(",", "")} & numbers):
        return {"ok": False, "why": "totals.md doesn't give the true total of the amount column."}
    if str(base["orders"]) not in numbers:
        return {"ok": False, "why": "totals.md doesn't give the number of orders."}
    return {"ok": True, "why": "totals.md gives the right number of orders and the right total."}


def _m2_connector(ctx, enabled: bool) -> str:
    """The archive connector every mission 2 learner finds in the Connectors tab: on when it is the planted extra, off
    when the other problem was drawn. Either way the page's warning about it stays true and tells nothing."""
    name = _rng(ctx["row"], "m2-connector").choice(CONNECTOR_NAMES)
    scope = _full(ctx["home"], f"{FOLDER}/archive")
    practice_write.write_work_file_a(ctx["home"], ctx["row"], f"{FOLDER}/archive/readme.txt", "Old exports. Nothing here is used.\n")
    practice_write.add_mcp_server_a(ctx["home"], ctx["row"], name, "npx", ["-y", FS_SERVER_PACKAGE, scope], enabled=enabled)
    return name


def _plant_extra_connector(ctx) -> dict:
    base = _m2_base(ctx)
    name = _m2_connector(ctx, enabled=True)
    return {"base": base, "connector": name, "package": FS_SERVER_PACKAGE}


# The second mission 2 problem: a pack of skills for some other line of work, installed once to try and left on. Every
# skill puts its name and description in the skills list on every trip (agent/prompt_builder.py build_skills_system_prompt,
# Hermes 0.23.0), and the orders job never opens one. The Capabilities Skills tab switches a skill off by adding it to
# the global ``skills.disabled`` list (hermes_cli/web_routers/skills.py toggle_skill, skills_config.save_disabled_skills
# with no platform), which the skills list leaves out for every platform. One pack per learner, drawn from the seed.
SKILL_PACKS = (
    ("social posts", (
        ("academy-caption-ideas", "Draft three short captions for a photo post."),
        ("academy-hashtag-picks", "Pick hashtags for a post from its topic and place."),
        ("academy-post-calendar", "Plan a month of social posts around key dates."),
        ("academy-reel-script", "Script a 30-second video: hook, three beats, sign-off."),
        ("academy-comment-replies", "Draft friendly replies to comments on a post."),
        ("academy-bio-rewrite", "Rewrite a profile bio to fit the character limit."),
        ("academy-story-prompts", "Suggest story ideas from this week's news."),
        ("academy-trend-check", "Check whether a trend suits the brand before using it."),
        ("academy-poll-ideas", "Suggest poll questions that get followers talking."),
        ("academy-collab-pitch", "Draft a short pitch to a local creator."),
        ("academy-alt-text", "Describe a photo in plain words for alt text."),
        ("academy-review-thanks", "Draft a thank-you reply to a customer review."),
    )),
    ("events", (
        ("academy-venue-shortlist", "Shortlist venues by size, access and travel time."),
        ("academy-guest-invites", "Draft invitations with the date, place and RSVP line."),
        ("academy-seating-plan", "Lay out tables so each group sits together."),
        ("academy-run-of-show", "Build a minute-by-minute plan for the day."),
        ("academy-speaker-brief", "Brief a speaker on the audience, timing and room."),
        ("academy-badge-names", "Prepare name badges from the RSVP replies."),
        ("academy-dietary-notes", "Collect guests' dietary needs for the caterer."),
        ("academy-signage-text", "Draft signs for doors, tables and the front desk."),
        ("academy-volunteer-roles", "Give helpers setup, door and cleanup roles."),
        ("academy-weather-backup", "Plan an indoor fallback for an outdoor event."),
        ("academy-feedback-form", "Draft a short feedback form for guests."),
        ("academy-thank-you-notes", "Draft thank-you notes to speakers and helpers."),
    )),
    ("hiring", (
        ("academy-job-ad", "Draft a job ad with duties, hours and how to apply."),
        ("academy-cv-screen", "Screen applications against the role's must-haves."),
        ("academy-interview-questions", "Suggest interview questions for a role."),
        ("academy-interview-slots", "Offer candidates times that suit the panel."),
        ("academy-reference-check", "Draft questions for a reference phone call."),
        ("academy-offer-letter", "Draft an offer letter from the agreed terms."),
        ("academy-rejection-note", "Draft a kind, short note to applicants not chosen."),
        ("academy-first-week", "Plan a new starter's first week, day by day."),
        ("academy-buddy-match", "Pair a new starter with a buddy on the team."),
        ("academy-role-profile", "Describe a role's purpose, duties and skills."),
        ("academy-probation-review", "Prepare notes for a three-month review."),
        ("academy-exit-interview", "Draft exit interview questions for a leaver."),
    )),
)


def _pack_skill(name: str, description: str) -> str:
    return (f"---\nname: {name}\ndescription: {description}\n---\n\n## When to Use\n\nWhen someone asks you to: "
            f"{description[0].lower()}{description[1:]}\n\n## Procedure\n\n1. Ask for anything you need that the request "
            "doesn't give.\n2. Make the draft.\n3. Show it and ask what to change.\n")


def _plant_unused_skills(ctx) -> dict:
    base = _m2_base(ctx)
    connector = _m2_connector(ctx, enabled=False)  # someone already switched it off: here it isn't the problem
    theme, pack = _rng(ctx["row"], "m2-skills").choice(SKILL_PACKS)
    for name, description in pack:
        practice_write.write_skill_a(ctx["home"], ctx["row"], f"skills/{name}/SKILL.md", _pack_skill(name, description))
    return {"base": base, "skills": [name for name, _ in pack], "theme": theme, "connector": connector}


def pack_still_on(home, details) -> dict:
    """Which of the planted skills are still in the skills list: present, and not on the global switched-off list."""
    off = hermes_read_a.disabled_skills(home)
    found = hermes_read.skills(home)
    if not off.get("readable") or not found.get("readable"):
        return {"readable": False, "on": []}
    present = {s["name"] for s in found.get("skills", [])}
    return {"readable": True, "on": [n for n in details.get("skills", []) if n in present and n not in off["disabled"]]}


def _detect_unused_skills(home, details) -> dict:
    names = set(details.get("skills", []))
    opened = 0
    for m in _messages(home):
        calls = str(m.get("tool_calls") or "")
        if m.get("role") == "assistant" and "skill_view" in calls and any(n in calls for n in names):
            opened += 1
    state = pack_still_on(home, details)
    return {"fired": bool(hermes_read.sessions(home).get("sessions")),
            "facts": [{"label": "Skills for other work still on", "value": f"{len(state['on'])} of {len(names)}" if state["readable"] else "couldn't read"},
                      {"label": "Times a chat opened one", "value": str(opened)}], "evidence": []}


def _verify_unused_skills(home, details, fact, note=None) -> dict:
    state = pack_still_on(home, details)
    if not state["readable"]:
        return {"fixed": False, "why": "Field Academy couldn't read the practice profile's skills and their switches."}
    if state["on"]:
        count = len(state["on"])
        return {"fixed": False, "why": f"{count} {'skill' if count == 1 else 'skills'} for work this profile never does "
                                       f"{'is' if count == 1 else 'are'} still on, and each one's line rides along on every trip."}
    return {"fixed": True, "why": "The skills the job never used are off."}


def _detect_extra_connector(home, details) -> dict:
    now = hermes_read_a.connectors(home).get("connectors", {}).get(details.get("connector", ""), None)
    used = any(m.get("role") == "assistant" and details.get("connector", "~") in str(m.get("tool_calls") or "") for m in _messages(home))
    return {"fired": bool(hermes_read.sessions(home).get("sessions")),
            "facts": [{"label": f"Connector {details.get('connector')}", "value": "gone" if now is None else ("on" if now["enabled"] else "off")},
                      {"label": "Any job used it", "value": "yes" if used else "no"}], "evidence": []}


def _verify_extra_connector(home, details, fact, note=None) -> dict:
    now = hermes_read_a.connectors(home)
    if not now.get("readable"):
        return {"fixed": False, "why": "Field Academy couldn't read the practice profile's connectors."}
    item = now["connectors"].get(details.get("connector", ""))
    if item is not None and item["enabled"]:
        return {"fixed": False, "why": "A connector the job never used is still switched on, and its tools ride along on every trip."}
    return {"fixed": True, "why": "The connector the job never used is off."}


# ===================================================================== mission 4 ==


def _plant_soul_wrong_profile(ctx) -> dict:
    partner = _partner()
    if partner is None:
        raise ValueError("This mission needs the second practice profile, academy-practice-b, made and recorded first.")
    found = hermes_read_a.soul(partner["path"])
    return {"base": {"mission": "f.new-chats"}, "decoy": partner["name"], "decoy_path": partner["path"],
            "decoy_soul_sha": found.get("sha256", "")}


def _detect_soul_wrong_profile(home, details) -> dict:
    path = details.get("decoy_path", "")
    found = hermes_read_a.soul(path) if path and Path(path).is_dir() else {"readable": False}
    changed = found.get("readable") and found.get("sha256") != details.get("decoy_soul_sha")
    return {"fired": bool(changed), "facts": [{"label": f"{details.get('decoy', 'The second profile')}'s SOUL.md changed", "value": "yes" if changed else "no"}],
            "evidence": []}


def _verify_soul_wrong_profile(home, details, fact, note=None) -> dict:
    rule = str((note or {}).get("rule_text") or "")
    found = hermes_read_a.soul(home)
    if not found.get("readable"):
        return {"fixed": False, "why": "Field Academy couldn't read academy-practice's SOUL.md."}
    if not rule or squash(rule) not in squash(found["text"]):
        return {"fixed": False, "why": "The rule isn't in academy-practice's SOUL.md, the profile the practice chats use."}
    return {"fixed": True, "why": "The rule is in academy-practice's SOUL.md."}


def squash(text) -> str:
    return " ".join(str(text or "").lower().split())


# ===================================================================== mission 5 ==

WEEKLY_ADMIN = """---
name: academy-weekly-admin
description: Use for the weekly admin routine our team runs after every Monday meeting: turning the notes into action items with owners and due dates.
---

## When to Use

After the Monday team meeting, when the meeting notes need turning into a list of action items.

## Procedure

1. Read the meeting notes from top to bottom once before writing anything.
2. Pull out every decision that needs someone to act on it.
3. Write each as one action item: what, who owns it, and the due date.
4. Group the items by owner, earliest due date first.
5. End with a line listing any decision that has no owner yet.

## Pitfalls

- An item with no named owner gets lost; list it at the end, never assign it yourself.
- "Next week" is not a due date. Use the date the notes give, or ask.
- Discussion points that weren't decided are not action items.

## Verification

- Every decision in the notes appears as an item or on the no-owner line.
- Every item has an owner and a date.
- No item was invented: each one points back to a line in the notes.
"""

REPORT_HELPER = """---
name: academy-report-helper
description: Use when asked for any report, summary or list.
---

## When to Use

Any request for a report, a summary or a list.

## Procedure

1. Ask what the report is for.
2. Gather what's needed.
3. Write it up with a heading, a short summary and the details.

## Pitfalls

- Reports without a summary line get skimmed.

## Verification

- It has a heading, a summary and the details.
"""

PROCEDURES = (
    "For the weekly {thing} summary: pull the export, drop rows under {days} days, total by {by}.",
    "For the monthly {thing} report: download the sheet, remove rows under {days} days, then sum by {by}.",
)
PROC_PARAMS = {"thing": ("vendor", "supplier", "invoice"), "days": ("30", "45", "60"), "by": ("vendor", "supplier", "client")}


def _m5_base(ctx) -> dict:
    rel = "skills/academy-weekly-admin/SKILL.md"
    if not _base_done(ctx["home"], rel):
        practice_write.write_skill_a(ctx["home"], ctx["row"], rel, WEEKLY_ADMIN)
    return {"mission": "f.skills", "weekly_admin": rel, "token": str((ctx["row"].get("plan") or {}).get("token") or ctx["row"]["name"])}


def _plant_steps_in_memory(ctx) -> dict:
    base = _m5_base(ctx)
    rng = _rng(ctx["row"], "m5-steps")
    line = rng.choice(PROCEDURES).format(**{k: rng.choice(v) for k, v in sorted(PROC_PARAMS.items())})
    entries = list(hermes_read.memory(ctx["home"])["memory"]["entries"]) + [line]
    practice_write.write_memory(ctx["home"], ctx["row"], "memory", entries)
    return {"base": base, "line": line}


def _plant_greedy_neighbor(ctx) -> dict:
    base = _m5_base(ctx)
    rel = "skills/academy-report-helper/SKILL.md"
    practice_write.write_skill_a(ctx["home"], ctx["row"], rel, REPORT_HELPER)
    return {"base": base, "rel": rel, "name": "academy-report-helper", "description": "Use when asked for any report, summary or list."}


def step_markers(line) -> int:
    return len(re.findall(r"(?:^|[\s:;,])(?:\d+[.)]|step \d+|then |first,? |next,? |finally,? )", str(line).lower())) + str(line).count(", then")


def procedure_lines(entries) -> list:
    """Memory lines that read like a procedure: three or more ordered steps, or three or more clauses after a colon."""
    out = []
    for line in entries:
        head, _, tail = str(line).partition(":")
        clauses = [c for c in re.split(r",|;| then ", tail) if c.strip()] if tail else []
        if step_markers(line) >= 3 or len(clauses) >= 3 and re.match(r"^\s*(for|to|when|every)\b", head.lower()):
            out.append(line)
    return out


def _detect_steps_in_memory(home, details) -> dict:
    entries = hermes_read.memory(home).get("memory", {}).get("entries", [])
    still = matching.holds(entries, details.get("line", ""), threshold=0.6)
    return {"fired": True, "facts": [{"label": "The steps line is still in MEMORY.md", "value": "yes" if still else "no"}],
            "evidence": [("memory", "memories/MEMORY.md", still)] if still else []}


def _verify_steps_in_memory(home, details, fact, note=None) -> dict:
    mem = hermes_read.memory(home)
    if not mem.get("readable"):
        return {"fixed": False, "why": "Field Academy couldn't read the memory files."}
    entries = mem["memory"]["entries"] + mem["user"]["entries"]
    if matching.holds(entries, details.get("line", ""), threshold=0.6):
        return {"fixed": False, "why": "Memory still holds a job's steps. Steps belong in a skill; take them out of memory."}
    if procedure_lines(entries):
        return {"fixed": False, "why": "A memory line still reads like a procedure, with three or more steps."}
    return {"fixed": True, "why": "No job's steps are left in memory."}


def neighbor_state(home, details) -> str:
    found = hermes_read.skills(home)
    item = next((s for s in found.get("skills", []) if s["name"] == details.get("name")), None)
    if item is None:
        return "removed"
    if "disabled" in str(item.get("description", "")).lower():
        return "disabled"
    return "narrowed" if matching.overlap(item.get("description", ""), details.get("description", "")) < 0.6 else "as planted"


def _detect_greedy_neighbor(home, details) -> dict:
    loaded = 0
    for m in _messages(home):
        if m.get("role") == "assistant" and "skill_view" in str(m.get("tool_calls") or "") and details.get("name", "~") in str(m.get("tool_calls")):
            loaded += 1
    return {"fired": loaded > 0, "facts": [{"label": "Times Hermes opened academy-report-helper", "value": str(loaded)},
                                           {"label": "academy-report-helper now", "value": neighbor_state(home, details)}], "evidence": []}


def _verify_greedy_neighbor(home, details, fact, note=None) -> dict:
    state = neighbor_state(home, details)
    if state == "as planted":
        return {"fixed": False, "why": "A skill that matches almost any request is still there as it was, and it can win over yours."}
    return {"fixed": True, "why": f"The catch-all skill is {state}."}


# ===================================================================== mission 6 ==

DECOYS = (
    ("Castellan Roofing", "invoices go out net {n}"),
    ("Marlow Dental", "recall letters go out on the first {weekday}"),
    ("Brightwater Tiles", "quotes expire after {n} days"),
    ("Okonkwo Joinery", "site photos are filed by street name"),
    ("Pellam Vets", "reminders go out {n} days before each booking"),
)
DECOY_PARAMS = {"n": ("10", "15", "21", "30"), "weekday": ("Monday", "Tuesday", "Thursday")}
HOLLIS = "Hollis report: due the 14th. Contact: Ruth Hollis.\n"


def decoy_for(seed: str) -> str:
    rng = random.Random(f"field-academy-foundations-a:{seed}:m6-decoy")
    client, rest = rng.choice(DECOYS)
    return f"Client {client}: " + rest.format(**{k: rng.choice(v) for k, v in sorted(DECOY_PARAMS.items())}) + "."


def _data_dir() -> Path:
    with practice._conn() as conn:
        return practice._data_dir(conn)


def hollis_path() -> Path:
    return _data_dir() / "practice-files" / "hollis-notes.txt"


def _m6_base(ctx) -> dict:
    partner = _partner()
    if partner is None:
        raise ValueError("This mission needs the second practice profile, academy-practice-b, made and recorded first.")
    practice_write.write_shared_file_a(_data_dir(), "hollis-notes.txt", HOLLIS)
    return {"mission": "f.profiles", "a": ctx["row"]["name"], "a_path": str(ctx["home"]), "b": partner["name"], "b_path": partner["path"],
            "hollis": str(hollis_path()), "decoy": decoy_for(_seed(ctx["row"])), "b_cloned": bool((partner["plan"].get("request") or {}).get("cloned_from"))}


def _plant_cloned_memory(ctx) -> dict:
    base = _m6_base(ctx)
    in_b = matching.holds(hermes_read.memory(base["b_path"]).get("memory", {}).get("entries", []), base["decoy"], threshold=0.8)
    if not in_b:
        # The page made B before A held the line (an old app, or a reply lost on the way): put the line where a clone
        # would have, and say so in the record.
        partner = _partner()
        entries = list(hermes_read.memory(base["b_path"])["memory"]["entries"]) + [base["decoy"]]
        practice_write.write_memory(base["b_path"], partner, "memory", entries)
    return {"base": base, "decoy": base["decoy"], "via_clone": bool(in_b) and base["b_cloned"]}


def _plant_decoy_in_b(ctx) -> dict:
    base = _m6_base(ctx)
    partner = _partner()
    entries = list(hermes_read.memory(base["b_path"])["memory"]["entries"]) + [base["decoy"]]
    practice_write.write_memory(base["b_path"], partner, "memory", entries)
    return {"base": base, "decoy": base["decoy"]}


def _decoy_in(path, decoy) -> str:
    mem = hermes_read.memory(path)
    if not mem.get("readable"):
        return ""
    return matching.holds(mem["memory"]["entries"] + mem["user"]["entries"], decoy, threshold=0.6) or ""


def _detect_m6(home, details) -> dict:
    b = details.get("base", {}).get("b_path", "")
    still = _decoy_in(b, details.get("decoy", "")) if b and Path(b).is_dir() else ""
    facts = [{"label": "The other client's line in academy-practice-b", "value": "still there" if still else "gone"}]
    if "via_clone" in details:
        facts.append({"label": "How it got there", "value": "academy-practice-b was cloned from academy-practice" if details["via_clone"]
                      else "written into academy-practice-b's memory"})
    return {"fired": True, "facts": facts, "evidence": [("memory", "memories/MEMORY.md (academy-practice-b)", still)] if still else []}


def _verify_m6(home, details, fact, note=None) -> dict:
    b = details.get("base", {}).get("b_path", "")
    if not b or not Path(b).is_dir():
        return {"fixed": False, "why": "Field Academy couldn't find academy-practice-b."}
    if _decoy_in(b, details.get("decoy", "")):
        return {"fixed": False, "why": "academy-practice-b's memory still holds a line about another client."}
    return {"fixed": True, "why": "academy-practice-b's memory holds nothing about the other client."}


# ========================================================== plan and removal hooks ==


def plan_extra(conn, which, attempt_id, root, request) -> dict:
    """Mission 6's cloned-memory plant: before B is planned, put the client line in A, and ask Hermes to make B as a
    clone of A. Only from a practice profile Field Academy recorded, unopened; never from a learner's profile."""
    if which != "b" or not attempt_id:
        return request
    attempt = conn.execute("SELECT * FROM f_attempts WHERE id = ?", (int(attempt_id),)).fetchone()
    if attempt is None or attempt["mission_id"] != "f.profiles" or "cloned_memory" not in json.loads(attempt["plants_json"] or "[]"):
        return request
    rows = [practice._row(conn, r["name"]) for r in conn.execute("SELECT name FROM f_practice WHERE status IN ('ready', 'planted')")]
    source = next((r for r in rows if r and r["plan"].get("which", "a") == "a" and practice.valid_name(r["name"])
                   and Path(r.get("path", "")).is_dir()), None)
    if source is None:
        return request  # no recorded A yet: B is made blank, and the planter writes the line into B instead
    decoy = decoy_for(str(attempt["seed"]))
    entries = list(hermes_read.memory(source["path"])["memory"]["entries"])
    if decoy not in entries:
        practice_write.write_memory(source["path"], source, "memory", entries + [decoy])
        conn.execute("UPDATE f_practice SET fingerprint_json = ? WHERE name = ?",
                     (json.dumps(practice.fingerprint(source["path"])), source["name"]))
    params = dict(request["params"])
    params["clone_from"] = source["name"]
    params.pop("no_skills", None)  # Hermes refuses no_skills with a clone (hermes_cli/profiles.py create_profile)
    return {**request, "params": params, "cloned_from": source["name"]}


def before_remove(row, home) -> None:
    """Clear a lock Field Academy set (mission 1), so Hermes can delete the folder."""
    planted = (row.get("plan") or {}).get("planted") or {}
    details = planted.get("output_locked")
    if isinstance(details, dict) and details.get("rel"):
        try:
            practice_write.unlock_work_file_a(home, row, details["rel"])
        except (OSError, practice_write.Refused):
            pass


def base_for(planted: dict, mission: str = "") -> dict:
    """The base every planter of a mission returned, from whatever was planted."""
    for details in (planted or {}).values():
        if isinstance(details, dict) and isinstance(details.get("base"), dict) and (not mission or details["base"].get("mission") == mission):
            return details["base"]
    return {}


REGISTRY = {
    "output_locked": {"plant": _plant_output_locked, "detect": _detect_output_locked, "verify": _verify_m1},
    "input_empty": {"plant": _plant_input_empty, "detect": _detect_input_empty, "verify": _verify_m1},
    "rows_short": {"plant": _plant_rows_short, "detect": _detect_rows_short, "verify": _verify_m1},
    "extra_connector": {"plant": _plant_extra_connector, "detect": _detect_extra_connector, "verify": _verify_extra_connector},
    "unused_skills": {"plant": _plant_unused_skills, "detect": _detect_unused_skills, "verify": _verify_unused_skills},
    "soul_wrong_profile": {"plant": _plant_soul_wrong_profile, "detect": _detect_soul_wrong_profile, "verify": _verify_soul_wrong_profile},
    "steps_in_memory": {"plant": _plant_steps_in_memory, "detect": _detect_steps_in_memory, "verify": _verify_steps_in_memory},
    "greedy_neighbor": {"plant": _plant_greedy_neighbor, "detect": _detect_greedy_neighbor, "verify": _verify_greedy_neighbor},
    "cloned_memory": {"plant": _plant_cloned_memory, "detect": _detect_m6, "verify": _verify_m6},
    "decoy_in_b": {"plant": _plant_decoy_in_b, "detect": _detect_m6, "verify": _verify_m6},
}
