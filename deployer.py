"""The Deployer tier: state, checks, the review hook and the Guide Field Record.

This is the second kind of path in Field Academy. The four paths teach Hermes
through missions; this one asks whether someone can set up, deploy and manage
Hermes for a small client, and it asks by making them do the work: break-and-fix
labs on a disposable client machine, a proposal for a fictional firm, nine
judgment cases, a real deployment on their own Hermes, failure drills, and a
signed review by a reviewer the learner chooses.

It keeps its own tables (store.py) so nothing here can disturb a learner's
progress on the four paths, and it never writes anywhere but Field Academy's own
data folder. Everything it reads from Hermes it reads without changing anything
(evidence.py), and a test fails if that stops being true.

Module map: labs.py builds the lab folders, grade.py grades them, brief.py and
scenarios.py hold the proposal and the cases, evidence.py judges run history,
walkthrough.py builds the review packet and verifies the reviewer's signature,
deployer_content.py holds the words.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import brief as brief_mod
from . import deployer_content as C
from . import documents, evidence, grade, labs, learning, pathways, scenarios, store, walkthrough

PLUGIN_ROOT = Path(__file__).resolve().parent
PUBLISHED_REVIEWERS = PLUGIN_ROOT / "reviewers" / "trusted-reviewers.json"
MAX_FILE_BYTES = 5 * 1024 * 1024
PASS_SCORE = 70
LAB_ORDER = ("lab.leak", "lab.cost", "lab.reboot", "lab.vault")
DRILL_IDS = tuple(d["id"] for d in C.DRILLS)
SECRET_ANY = re.compile(r"FAKE-[A-Z]+-[A-Za-z0-9-]+|FAKE-KEY-DO-NOT-USE-[A-Za-z0-9-]+")


def new_seed() -> int:
    """A fresh lab seed. Tests replace this to get a known case."""
    return secrets.randbits(31)


# ------------------------------------------------------------------ plumbing --


def _conn():
    return store.connect()


def _now() -> str:
    return store.now()


def _clock() -> datetime:
    return store.clock()


def _clean(text, limit):
    return " ".join((text or "").split())[:limit]


def _data_dir(conn) -> Path:
    override = os.environ.get("FIELD_ACADEMY_DATA_DIR")
    if override:
        return Path(override)
    return Path(conn.execute("PRAGMA database_list").fetchone()[2]).parent


def _hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()


def _json(text, default):
    try:
        return json.loads(text) if text else default
    except ValueError:
        return default


def _item(conn, item_id):
    row = conn.execute("SELECT * FROM deployer_items WHERE item_id = ?", (item_id,)).fetchone()
    if not row:
        return {"item_id": item_id, "status": "open", "score": None, "detail": {}, "fingerprint": "", "passed_at": "", "exists": False}
    data = dict(row)
    data["detail"] = _json(data.pop("detail_json"), {})
    data["exists"] = True
    return data


def _save_item(conn, item_id, status=None, score=None, detail=None, fingerprint=None, passed=False):
    current = _item(conn, item_id)
    merged = {**current["detail"], **(detail or {})}
    conn.execute(
        """INSERT INTO deployer_items(item_id, status, score, detail_json, fingerprint, updated_at, passed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(item_id) DO UPDATE SET status = excluded.status, score = excluded.score, detail_json = excluded.detail_json,
             fingerprint = excluded.fingerprint, updated_at = excluded.updated_at, passed_at = excluded.passed_at""",
        (
            item_id,
            status or current["status"],
            score if score is not None else current["score"],
            json.dumps(merged, ensure_ascii=False),
            fingerprint if fingerprint is not None else current["fingerprint"],
            _now(),
            _now() if passed else current["passed_at"],
        ),
    )
    return merged


def _record_miss(conn, item_id, builder):
    row = conn.execute("SELECT misses FROM deployer_attempts WHERE item_id = ?", (item_id,)).fetchone()
    misses = (row["misses"] if row else 0) + 1
    feedback = builder(misses)
    conn.execute(
        """INSERT INTO deployer_attempts(item_id, misses, last_feedback_json, updated_at) VALUES (?, ?, ?, ?)
           ON CONFLICT(item_id) DO UPDATE SET misses = excluded.misses, last_feedback_json = excluded.last_feedback_json, updated_at = excluded.updated_at""",
        (item_id, misses, json.dumps(feedback), _now()),
    )
    return feedback


def _clear_misses(conn, item_id):
    conn.execute("DELETE FROM deployer_attempts WHERE item_id = ?", (item_id,))


def _last_feedback(conn, item_id):
    row = conn.execute("SELECT last_feedback_json FROM deployer_attempts WHERE item_id = ?", (item_id,)).fetchone()
    return _json(row["last_feedback_json"], None) if row else None


def _read_file(path):
    """Read a text file the learner named: bounded, UTF-8 only. Returns (text, sha256, size, problem)."""
    target = Path(str(path or "")).expanduser()
    if not target.is_file():
        return None, "", 0, {"id": "file", "what": f"Nothing is saved at {target}. Save the document as text or Markdown, then type where you saved it."}
    size = target.stat().st_size
    if size == 0:
        return None, "", 0, {"id": "file", "what": "That file is empty. Write the document, save it, and check again."}
    if size > MAX_FILE_BYTES:
        return None, "", size, {"id": "file", "what": f"That file is {size} bytes and the limit is {MAX_FILE_BYTES}. Type the location of the document itself."}
    raw = target.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, "", size, {"id": "file", "what": "That is not a text document. Save it as plain text or Markdown and type that location."}
    return text, hashlib.sha256(raw).hexdigest(), len(raw), None


def _failed_outcome(conn, item_id, title, missing, coach, facts=None, detail=""):
    feedback = _record_miss(conn, item_id, lambda n: learning.ladder(n, missing, coach))
    return {"passed": False, "title": title, "detail": detail or missing[0]["what"], "facts": facts or [], "missing": missing, "feedback": feedback}


def _section_coach(sections):
    coach = {}
    for rule in sections:
        coach[f"section:{rule['heading']}"] = {"hint": rule.get("hint", ""), "example": rule.get("example", "")}
    for key, value in learning.GENERIC_COACH.items():
        coach.setdefault(key, dict(value))
    return coach


# ---------------------------------------------------------------------- labs --


def _lab_row(conn, lab_id):
    seed = store.meta_get(conn, f"deployer:seed:{lab_id}", "")
    if not seed.isdigit():
        return None
    row = conn.execute("SELECT * FROM deployer_labs WHERE lab_id = ? AND seed = ?", (lab_id, int(seed))).fetchone()
    return dict(row) if row else None


def _passed_lab_row(conn, lab_id):
    row = conn.execute("SELECT * FROM deployer_labs WHERE lab_id = ? AND status = 'passed' ORDER BY passed_at DESC LIMIT 1", (lab_id,)).fetchone()
    return dict(row) if row else None


def _check_lab_id(lab_id):
    if lab_id not in LAB_ORDER:
        raise ValueError(f"Unknown lab: {lab_id}")


def open_lab(lab_id):
    """Build the lab folder, or hand back the one that exists. Never overwrites the learner's work."""
    _check_lab_id(lab_id)
    with _conn() as conn:
        row = _lab_row(conn, lab_id)
        seed = row["seed"] if row else new_seed()
        manifest = labs.build_lab(lab_id, seed, _data_dir(conn))
        if not row:
            conn.execute(
                "INSERT OR IGNORE INTO deployer_labs(lab_id, seed, folder, created_at) VALUES (?, ?, ?, ?)",
                (lab_id, seed, manifest["path"], _now()),
            )
            store.meta_set(conn, f"deployer:seed:{lab_id}", seed)
        return lab_view(conn, lab_id)


def new_variant(lab_id):
    """A new case for the same lab. An unfinished folder is deleted (only if it carries the lab marker); a passed one is kept for the reviewer."""
    _check_lab_id(lab_id)
    with _conn() as conn:
        row = _lab_row(conn, lab_id)
        if row and row["status"] != "passed":
            labs.reset_lab(lab_id, row["seed"], _data_dir(conn))
            conn.execute("DELETE FROM deployer_labs WHERE lab_id = ? AND seed = ?", (lab_id, row["seed"]))
            _clear_misses(conn, lab_id)
        store.meta_set(conn, f"deployer:seed:{lab_id}", "")
    return open_lab(lab_id)


def _concat_result(row):
    return _json(row.get("last_result_json", ""), None)


def lab_view(conn, lab_id):
    meta = {"lab_id": lab_id, "title": labs.TITLES[lab_id], "minutes": labs.MINUTES[lab_id]}
    row = _lab_row(conn, lab_id)
    passed_row = _passed_lab_row(conn, lab_id)
    out = {**meta, "opened": bool(row), "status": "not_started", "attempts": 0, "result": None, "feedback": None, "worked": None,
           "passed_at": passed_row["passed_at"] if passed_row else ""}
    if passed_row and not row:
        out["status"] = "verified"
    if not row:
        return out
    root = Path(row["folder"])
    spec = labs.spec_for(lab_id, row["seed"])
    out.update(labs.manifest(spec, root) if root.is_dir() else {"path": str(root), "files": [], "note": "", "symptoms": [], "hand_in": []})
    out["title"] = meta["title"]
    out["seed"] = row["seed"]
    out["attempts"] = row["attempts"]
    out["status"] = "verified" if row["status"] == "passed" else "in_progress"
    out["result"] = _concat_result(row)
    out["diagnosis"] = row["diagnosis"]
    out["changed"] = labs.changed_files(lab_id, row["seed"], root) if root.is_dir() else []
    feedback = _last_feedback(conn, lab_id)
    out["feedback"] = feedback
    if feedback and feedback.get("misses", 0) >= 2:
        out["worked"] = grade.WORKED[lab_id]
    out["folder_missing"] = not root.is_dir()
    return out


def check_lab(lab_id, diagnosis=""):
    """Grade the learner's folder and write-up. Reads files only."""
    _check_lab_id(lab_id)
    with _conn() as conn:
        row = _lab_row(conn, lab_id)
        if not row:
            raise ValueError("Open the lab first, so there is a folder to repair.")
        if row["status"] == "passed":
            return {"outcome": _concat_result(row) or {"passed": True, "title": "Already passed", "detail": "", "facts": [], "missing": []}, "lab": lab_view(conn, lab_id), "already_passed": True}
        root = Path(row["folder"])
        clean = SECRET_ANY.sub("[key removed]", " ".join((diagnosis or "").split()))[:4000]
        result = grade.grade_lab(lab_id, row["seed"], root, clean)
        unchanged = root.is_dir() and labs.tree_fingerprint(root) == labs.pristine_fingerprint(lab_id, row["seed"])
        if unchanged:
            result = {"passed": False, "title": "Nothing has changed yet", "detail": "The folder is exactly as it was built. Find the problem in the files and repair it, then check again.", "facts": [],
                      "missing": [{"id": "unchanged", "what": "The folder is exactly as it was built. Find the problem in the files and repair it, then check again."}]}
        attempts = row["attempts"] + 1
        fingerprint = labs.tree_fingerprint(root) if root.is_dir() else ""
        if result["passed"]:
            _clear_misses(conn, lab_id)
            conn.execute(
                """UPDATE deployer_labs SET status = 'passed', attempts = ?, diagnosis = ?, last_result_json = ?, tree_fingerprint = ?, changed_json = ?, passed_at = ?
                   WHERE lab_id = ? AND seed = ?""",
                (attempts, clean, json.dumps(result), fingerprint, json.dumps(labs.changed_files(lab_id, row["seed"], root)), _now(), lab_id, row["seed"]),
            )
        elif unchanged:
            # Checking an untouched folder is not an attempt at a repair, so it does not climb the
            # hint ladder towards the worked example. It gets the first hint every time.
            attempts = row["attempts"]
            result["feedback"] = learning.ladder(1, result["missing"], {"unchanged": {
                "hint": "Start with the client's note, then the logs folder. The evidence points at the file to open.",
                "example": "Example: the log names a key id, a job or a service. Search the files for it."}})
            conn.execute(
                "UPDATE deployer_labs SET last_result_json = ? WHERE lab_id = ? AND seed = ?",
                (json.dumps(result), lab_id, row["seed"]),
            )
        else:
            coach = {key: dict(value) for key, value in grade.COACH.items()}
            result["feedback"] = _record_miss(conn, lab_id, lambda n: learning.ladder(n, result["missing"], coach))
            conn.execute(
                "UPDATE deployer_labs SET attempts = ?, diagnosis = ?, last_result_json = ? WHERE lab_id = ? AND seed = ?",
                (attempts, clean, json.dumps(result), lab_id, row["seed"]),
            )
        view = lab_view(conn, lab_id)
    return {"outcome": result, "lab": view}


# --------------------------------------------------------------------- brief --

BRIEF_COACH = {
    "firm_named": {"hint": "Write the proposal to this firm. Use its name in the Scope.", "example": "Example: Scope: A helper for Wren and Castellan CPAs that drafts the Monday follow-ups."},
    "owner_named": {"hint": "Name the partner who decides, in the Scope or in Approvals.", "example": "Example: Delphine Wren decides what is in scope."},
    "price_parts": {"hint": "Write two labelled amounts: the setup price and the monthly running cost.", "example": "Example: Setup: $2,400. Running cost: $110 per month."},
    "price_over": {"hint": "Bring the setup price to the firm's budget or under it, and say what you cut.", "example": "Example: Setup $2,800 instead of $3,400, leaving out the second mailbox."},
    "price_low": {"hint": "A price far below the budget for this much work is a risk to the client too. Price what you can deliver.", "example": "Example: if the budget is $3,200, a setup near $2,400 to $3,200 is believable."},
    "monthly_over": {"hint": "Bring the monthly cost under the firm's ceiling. Choose a cheaper model or a less frequent job.", "example": "Example: $90 per month for the provider and the computer."},
    "criteria_count": {"hint": "Write at least three numbered lines, each a test someone else could run.", "example": "Example:\n1. The summary arrives by 8 am for four weeks.\n2. Nothing is sent without a partner reading it.\n3. A draft takes under 2 minutes to approve."},
    "criteria_measurable": {"hint": "Put a number or a time on at least two criteria.", "example": "Example: \"arrives by 8 am\" and \"under 2 minutes\" can both be counted."},
    "access_count": {"hint": "One line for each tool the helper reaches. The brief names the firm's tools.", "example": "Example:\n- Outlook email: read the shared inbox, create drafts\n- Shared drive: read the Clients folder\n- Accounting software: read invoices"},
    "access_tools": {"hint": "Use the names of the firm's tools from the brief.", "example": "Example: the firm's email, its accounting software and its shared drive, by name."},
    "access_broad": {"hint": "Replace the blanket word with the specific thing the helper needs to do.", "example": "Example: instead of \"admin on the accounting software\", write \"read invoices\"."},
    "access_permission": {"hint": "Say what the helper may do with each tool: read, list, draft.", "example": "Example: \"read the Clients folder\" says what it may do."},
    "unsafe_not_refused": {"hint": "Say in one plain sentence that you will not do it.", "example": "Example: \"I will not give the helper the shared login.\""},
    "unsafe_unnamed": {"hint": "Say which request you decline, in its own words.", "example": "Example: name the request, such as the shared login or the automatic emails."},
    "unsafe_no_alternative": {"hint": "Offer what the firm gets instead.", "example": "Example: \"Instead, drafts go to a partner to read and send.\""},
    "approvals_list": {"hint": "List at least two actions that need a person's yes, and use the word approve.", "example": "Example:\n- Marcia Alder approves any email before it goes\n- Priya Nand approves any new connection"},
    "build_weeks": {"hint": "Say how many weeks the whole build takes.", "example": "Example: Four weeks in all."},
    "build_late": {"hint": "Shorten the plan to fit the weeks the firm asked for, or cut scope and say so.", "example": "Example: move the second mailbox to a later phase."},
    "staged_weak": {"hint": "Say what you test on first (copies or samples) and what must be true before real client files are touched.", "example": "Example: five runs on copies of last month's files, read by a partner, before anything goes live."},
    "audit_list": {"hint": "List at least two things you will check before building.", "example": "Example:\n- Where the tax documents are kept and who can open them\n- Which logins are shared"},
}


def _brief_seed(conn):
    seed = store.meta_get(conn, "deployer:brief_seed", "")
    if not seed.isdigit():
        seed = str(new_seed())
        store.meta_set(conn, "deployer:brief_seed", seed)
    return int(seed)


def brief_view(conn):
    item = _item(conn, "brief")
    brief = brief_mod.brief_for(_brief_seed(conn))
    answer = conn.execute("SELECT * FROM deployer_answers WHERE item_id = 'brief'").fetchone()
    out = {
        "item_id": "brief", "title": C.ITEM_TITLES["brief"], "minutes": C.ITEM_MINUTES["brief"],
        "brief": brief["brief"], "constraints": brief["constraints"], "sections": brief["sections"], "firm": brief["firm"],
        "status": "verified" if item["status"] == "verified" else ("in_progress" if item["exists"] else "not_started"),
        "stage": item["detail"].get("stage", "writing"),
        "score": item["score"], "document": item["detail"].get("document", ""), "sha256": item["fingerprint"],
        "feedback": _last_feedback(conn, "brief"), "answer": None, "rubric": None,
    }
    if answer:
        out["answer"] = _answer_view(answer)
        if answer["score"] is not None:
            out["rubric"] = [r["point"] for r in brief_mod.RUBRIC]
    return out


def _answer_view(row):
    data = dict(row)
    data.pop("answer", None)
    raw = data.pop("ladder_json", "") or ""
    data["ladder"] = _json(raw, None)
    return data


def new_brief_case():
    """A new fictional firm, if the learner has not passed this one yet."""
    with _conn() as conn:
        item = _item(conn, "brief")
        if item["status"] == "verified":
            raise ValueError("You already passed this proposal. Its record stays as it is.")
        store.meta_set(conn, "deployer:brief_seed", new_seed())
        conn.execute("DELETE FROM deployer_items WHERE item_id = 'brief'")
        conn.execute("DELETE FROM deployer_answers WHERE item_id = 'brief'")
        _clear_misses(conn, "brief")
        return brief_view(conn)


def brief_submit(path):
    """Check the proposal document. A pass hands back the instruction for the learner's own Hermes to score the prose."""
    with _conn() as conn:
        if _item(conn, "brief")["status"] == "verified":
            raise ValueError("You already passed this proposal. Its record stays as it is.")
        brief = brief_mod.brief_for(_brief_seed(conn))
        text, digest, size, problem = _read_file(path)
        coach = _section_coach(brief_mod.SECTIONS)
        coach.update({k: v for k, v in BRIEF_COACH.items()})
        if problem:
            return _failed_outcome(conn, "brief", "No document to check", [problem], coach)
        result = brief_mod.check(text, brief)
        facts = [
            {"label": "File", "value": Path(str(path)).name},
            {"label": "Size", "value": f"{size} bytes, {len(text.split())} words"},
            {"label": "SHA-256", "value": digest[:16]},
        ]
        if result["missing"]:
            return _failed_outcome(conn, "brief", "Your proposal isn't ready yet", result["missing"], coach, facts)
        _clear_misses(conn, "brief")
        capped = text[:20000]
        conn.execute(
            """INSERT INTO deployer_answers(item_id, answer, score, feedback, attempts, ladder_json, created_at, graded_at)
               VALUES ('brief', ?, NULL, '', COALESCE((SELECT attempts + 1 FROM deployer_answers WHERE item_id = 'brief'), 1), '', ?, '')
               ON CONFLICT(item_id) DO UPDATE SET answer = excluded.answer, score = NULL, feedback = '', attempts = excluded.attempts, ladder_json = '', created_at = excluded.created_at, graded_at = ''""",
            (capped, _now()),
        )
        _save_item(conn, "brief", status="scoring", detail={"stage": "scoring", "document": Path(str(path)).name, "checks_met_at": _now()}, fingerprint=digest)
        return {
            "passed": False, "awaiting_score": True,
            "title": "The checks on the document are met",
            "detail": "Every section is there and every number fits. Now your own Hermes scores the parts a check cannot judge.",
            "facts": facts, "missing": [], "sha256": digest,
            "prompt": brief_mod.grading_prompt(brief, capped),
        }


# ----------------------------------------------------------------- scenarios --


def scenario_view(conn, scenario_id):
    item = scenarios.BY_ID[scenario_id]
    row = conn.execute("SELECT * FROM deployer_answers WHERE item_id = ?", (f"scenario.{scenario_id}",)).fetchone()
    out = {
        "id": scenario_id, "title": item["title"], "situation": item["situation"], "question": item["question"], "minutes": item["minutes"],
        "status": "not_started", "score": None, "feedback": None, "attempts": 0, "ladder": None, "covers": None,
    }
    if row:
        out.update({"score": row["score"], "attempts": row["attempts"], "feedback": row["feedback"], "ladder": _json(row["ladder_json"], None)})
        out["status"] = "verified" if row["score"] is not None and row["score"] >= PASS_SCORE else "in_progress"
        if row["graded_at"]:
            out["covers"] = item["covers"]
    return out


def scenario_submit(scenario_id, answer):
    if scenario_id not in scenarios.BY_ID:
        raise ValueError(f"Unknown scenario: {scenario_id}")
    clean = _clean(answer, 4000)
    if len(clean) < scenarios.MIN_CHARS:
        raise ValueError(f"That is too short to score. Write at least {scenarios.MIN_CHARS} characters, a few sentences that weigh the choice.")
    with _conn() as conn:
        conn.execute(
            """INSERT INTO deployer_answers(item_id, answer, score, feedback, attempts, ladder_json, created_at, graded_at)
               VALUES (?, ?, NULL, '', COALESCE((SELECT attempts + 1 FROM deployer_answers WHERE item_id = ?), 1), '', ?, '')
               ON CONFLICT(item_id) DO UPDATE SET answer = excluded.answer, score = NULL, feedback = '', attempts = excluded.attempts, ladder_json = '', created_at = excluded.created_at, graded_at = ''""",
            (f"scenario.{scenario_id}", clean, f"scenario.{scenario_id}", _now()),
        )
        return {"scenario_id": scenario_id, "prompt": scenarios.grading_prompt(scenarios.BY_ID[scenario_id], clean)}


def grade_deployer(item_id, score, missed=None, feedback=""):
    """Record the score the learner's own Hermes gave a scenario answer or the proposal's prose."""
    if item_id == "brief":
        rubric, coach_list = brief_mod.RUBRIC, brief_mod.RUBRIC
        covers = [r["point"] for r in rubric]
    elif item_id.startswith("scenario.") and item_id.split(".", 1)[1] in scenarios.BY_ID:
        spec = scenarios.BY_ID[item_id.split(".", 1)[1]]
        covers, coach_list = spec["covers"], spec["coach"]
    else:
        raise ValueError(f"Unknown item to grade: {item_id}")
    try:
        value = max(0, min(100, int(score)))
    except (TypeError, ValueError) as exc:
        raise ValueError("A score between 0 and 100 is required.") from exc
    passed = value >= PASS_SCORE
    note = _clean(feedback, 1500)
    indexes = sorted({int(n) for n in (missed or []) if str(n).isdigit() and 1 <= int(n) <= len(covers)})
    with _conn() as conn:
        row = conn.execute("SELECT * FROM deployer_answers WHERE item_id = ?", (item_id,)).fetchone()
        if not row:
            raise ValueError("Nothing has been submitted for this item yet.")
        if row["graded_at"]:
            raise ValueError("That answer already has a score. Send a new answer for a new score.")
        ladder = None
        if passed:
            _clear_misses(conn, item_id)
        else:
            missing = [{"id": f"point:{n}", "what": f"Missing point: {covers[n - 1]}"} for n in indexes] or [{"id": "feedback", "what": note or "The answer needs more of the points a strong answer covers."}]
            coach = {key: dict(value) for key, value in learning.GENERIC_COACH.items()}
            for number, entry in enumerate(coach_list, start=1):
                coach[f"point:{number}"] = {"hint": entry.get("hint", ""), "example": entry.get("example", "")}
            ladder = _record_miss(conn, item_id, lambda n: learning.ladder(n, missing, coach))
        conn.execute(
            "UPDATE deployer_answers SET score = ?, feedback = ?, graded_at = ?, ladder_json = ? WHERE item_id = ?",
            (value, note, _now(), json.dumps(ladder) if ladder else "", item_id),
        )
        if item_id == "brief":
            _save_item(conn, "brief", status="verified" if passed else "open", score=value, detail={"stage": "passed" if passed else "writing", "prose_score": value}, passed=passed)
    return {"passed": passed, "score": value, "threshold": PASS_SCORE, "feedback": note, "ladder": ladder}


# ---------------------------------------------------------------- deployment --


def _deploy_view(conn):
    item = _item(conn, "deploy")
    detail = item["detail"]
    samples = _samples(conn, "deploy")
    return {
        "item_id": "deploy", "title": C.DEPLOY["title"], "minutes": C.ITEM_MINUTES["deploy"],
        "intro": C.DEPLOY["intro"], "steps": C.DEPLOY["steps"], "reads": C.DEPLOY["reads"], "cannot_read": C.DEPLOY["cannot_read"],
        "record_sections": [s["heading"] for s in C.DEPLOY["record_sections"]],
        "status": item["status"] if item["status"] in ("verified", "awaiting_review") else ("in_progress" if detail.get("started_at") else "not_started"),
        "service": detail.get("service", ""), "job": detail.get("job", ""), "started_at": detail.get("started_at", ""),
        "record": detail.get("record"), "result": detail.get("result"), "fallback": _public_fallback(detail.get("fallback")),
        "checks": len(samples), "feedback": _last_feedback(conn, "deploy"), "accepted": bool(detail.get("accepted_by_reviewer")),
        "evidence_note": detail.get("evidence_note", "")
    }


def _public_fallback(fallback):
    if not fallback:
        return None
    return {k: fallback[k] for k in ("submitted_at", "sha256", "timestamps", "days") if k in fallback}


def _samples(conn, item_id):
    return [dict(r) for r in conn.execute("SELECT * FROM deployer_samples WHERE item_id = ? ORDER BY id", (item_id,))]


def _union(samples):
    times, failed = set(), set()
    for s in samples:
        times.update(_json(s["times_json"], []))
        failed.update(_json(s["failed_json"], []))
    return sorted(times), sorted(failed)


def deploy_start(service, job):
    service, job = _clean(service, 80), _clean(job, 80)
    if not service or not job:
        raise ValueError("Name the service you connected and the scheduled job that uses it.")
    if not job.lower().startswith("deployer-"):
        raise ValueError("Name the job so it starts with deployer-, so Field Academy can find it in Hermes's own records.")
    with _conn() as conn:
        existing = _item(conn, "deploy")
        if existing["detail"].get("started_at"):
            raise ValueError("The clock is already running. Its start time is part of the evidence, so it cannot be restarted.")
        _save_item(conn, "deploy", status="running", detail={"service": service, "job": job, "started_at": _now()})
        return _deploy_view(conn)


def _check_record(path, sections, item_id, extra=None):
    text, digest, size, problem = _read_file(path)
    if problem:
        return None, digest, [problem]
    step = {"sections": sections}
    analysis = documents.analyze(text, step, [])
    missing = list(analysis["missing"])
    if extra and not missing:
        missing += extra(analysis["sections"])
    return {"name": Path(str(path)).name, "sha256": digest, "bytes": size, "words": len(text.split())}, digest, missing


def _broad_access(sections):
    out = []
    for line in documents.list_items(sections.get("Access granted", "")):
        hit = brief_mod.BROAD.search(line)
        if hit and not brief_mod.NEGATION.search(line[: hit.start()]):
            out.append({"id": "access_broad", "what": f'The line "{line[:60]}" grants a blanket permission ("{hit.group(0)}"). List the specific thing the job reads.'})
            break
    return out


def deploy_record(path):
    with _conn() as conn:
        item = _item(conn, "deploy")
        if not item["detail"].get("started_at"):
            raise ValueError("Start the clock first, with the service's name and the job's name.")
        record, digest, missing = _check_record(path, C.DEPLOY["record_sections"], "deploy", _broad_access)
        coach = _section_coach(C.DEPLOY["record_sections"])
        coach["access_broad"] = {"hint": "List the specific thing the job reads, one permission per line.", "example": "Example: \"Read events on the Work calendar\" instead of \"full access\"."}
        if missing:
            return _failed_outcome(conn, "deploy", "Your access record isn't finished yet", missing, coach)
        _clear_misses(conn, "deploy")
        _save_item(conn, "deploy", detail={"record": {**record, "checked_at": _now()}}, fingerprint=digest)
        return {"passed": True, "title": "Your access record is complete", "detail": "It says what you granted, what you refused, when it expires, who owns it and what to do if it leaks. Now let the job run, and check the run history.",
                "facts": [{"label": "File", "value": record["name"]}, {"label": "SHA-256", "value": digest[:16]}], "missing": []}


def _valid_sample(sample, now):
    if not isinstance(sample, dict):
        return None
    times = [t for t in (sample.get("times") or [])[:500] if isinstance(t, str)]
    failed = [t for t in (sample.get("failed") or [])[:500] if isinstance(t, str)]
    return {"source": _clean(str(sample.get("source", "desktop")), 40), "times": [evidence.iso(t) for t in evidence.clean_times(times, now)], "failed": [evidence.iso(t) for t in evidence.clean_times(failed, now)]}


def _take_sample(conn, item_id, job, sample, home, read_home):
    now = _clock()
    taken = []
    clean = _valid_sample(sample, now)
    if clean and (clean["times"] or clean["failed"]):
        taken.append(clean)
    if read_home:
        found = evidence.collect(home if home is not None else _hermes_home(), job, now) if (home is not None or _hermes_home().exists()) else {"found": False}
        if found.get("found"):
            taken.append({"source": "hermes files", "times": found["times"], "failed": found["failed"]})
    for item in taken:
        conn.execute(
            "INSERT INTO deployer_samples(item_id, taken_at, source, times_json, failed_json) VALUES (?, ?, ?, ?, ?)",
            (item_id, _now(), item["source"], json.dumps(item["times"]), json.dumps(item["failed"])),
        )
    return taken


# Misses that only mean "not enough time has passed yet".
WAITING_MISSES = {"few_runs", "few_days", "short_span"}


def deploy_check(sample=None, home=None, read_home=True):
    """Read what Hermes recorded for the job and judge whether it ran over several days. Writes only to Field Academy's own table."""
    with _conn() as conn:
        item = _item(conn, "deploy")
        detail = item["detail"]
        if not detail.get("started_at"):
            raise ValueError("Start the clock first.")
        _take_sample(conn, "deploy", detail["job"], sample, home, read_home)
        times, failed = _union(_samples(conn, "deploy"))
        started = evidence.parse_ts(detail["started_at"])
        result = evidence.analyze_run_history(times, since=started, now=_clock(), failed=failed)
        coach = {
            "few_runs": {"hint": "Let the job run more. Each scheduled run adds one.", "example": "Example: a job that runs twice a day has 6 runs in 3 days."},
            "few_days": {"hint": "Wait. The check needs runs on three different days.", "example": "Example: Monday, Tuesday and Wednesday."},
            "short_span": {"hint": "Wait until at least 48 hours have passed between the first and last run.", "example": "Example: first run Monday 9 am, last run Wednesday 9 am."},
            "clustered": {"hint": "Make the job run on a normal schedule instead of being run by hand.", "example": "Example: 0 9 * * * runs once at 9 am each day."},
            "mostly_failed": {"hint": "Open the job in Hermes and read why it fails, then fix the credential or the request.", "example": "Example: a token that expired gives an authorization error."},
            "stopped": {"hint": "Check that Hermes is running and the job is switched on.", "example": "Example: the job was paused, so it stopped three days ago."},
            "unreadable": {"hint": "Add your own log excerpt below. Your reviewer will check it.", "example": ""},
        }
        record = detail.get("record")
        if not record:
            result["missing"].append({"id": "record_missing", "what": "Write the access record and check it first."})
            coach["record_missing"] = {"hint": "The access record says what you granted and refused.", "example": ""}
            result["passed"] = False
        sources = sorted({s["source"] for s in _samples(conn, "deploy")})
        note = f"Read from: {', '.join(sources) or 'nothing readable'}. {len(times)} run times, {len(failed)} failed."
        if result["passed"]:
            _clear_misses(conn, "deploy")
            _save_item(conn, "deploy", status="verified", detail={"result": {"passed": True, "facts": result["facts"], "checked_at": _now()}, "evidence_note": note}, passed=True)
        else:
            if not result.get("readable", True):
                _save_item(conn, "deploy", detail={"evidence_note": note})
                result["fallback"] = True
            else:
                # Only waiting is left (too few runs, days or hours so far): that is time, not a
                # mistake, so it gets the plain hint and does not climb toward the worked example.
                waiting_only = all(m.get("id") in WAITING_MISSES for m in result["missing"])
                if waiting_only:
                    result["feedback"] = learning.ladder(1, result["missing"], coach)
                else:
                    result["feedback"] = _record_miss(conn, "deploy", lambda n: learning.ladder(n, result["missing"], coach))
                _save_item(conn, "deploy", detail={"result": {"passed": False, "facts": result["facts"], "checked_at": _now()}, "evidence_note": note})
        return {"outcome": result, "deploy": _deploy_view(conn)}


def _fallback(conn, item_id, excerpt, notes, record_ok, extra_detail=None):
    clean_notes = _clean(notes, 1000)
    raw = (excerpt or "")
    if len(raw.strip()) < 80:
        raise ValueError("Paste the part of your log that shows the runs. It is too short to review.")
    summary = evidence.excerpt_summary(raw, _clock())
    if summary["count"] < 3:
        raise ValueError("The excerpt shows fewer than 3 timestamps. Paste lines that include the date and time of each run.")
    if not record_ok:
        raise ValueError("Complete the written record for this item first.")
    packet = {
        "submitted_at": _now(),
        "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "excerpt": evidence.redact(raw),
        "notes": clean_notes,
        "timestamps": summary["count"],
        "days": summary["days"],
        "first": summary["first"],
        "last": summary["last"],
    }
    _save_item(conn, item_id, status="awaiting_review", detail={"fallback": packet, "evidence_note": "Hermes run history could not be read. The reviewer checks your own excerpt."})
    return packet


def deploy_fallback(excerpt, notes=""):
    with _conn() as conn:
        item = _item(conn, "deploy")
        if not item["detail"].get("started_at"):
            raise ValueError("Start the clock first.")
        packet = _fallback(conn, "deploy", excerpt, notes, bool(item["detail"].get("record")))
        return {"ok": True, "fallback": _public_fallback(packet), "deploy": _deploy_view(conn)}


# -------------------------------------------------------------------- drills --


def _drill_def(drill_id):
    for d in C.DRILLS:
        if d["id"] == drill_id:
            return d
    raise ValueError(f"Unknown drill: {drill_id}")


def _drill_view(conn, drill):
    item = _item(conn, f"drill.{drill['id']}")
    detail = item["detail"]
    status = item["status"] if item["status"] in ("verified", "awaiting_review") else ("in_progress" if detail.get("started_at") else "not_started")
    return {
        "id": drill["id"], "title": drill["title"], "minutes": drill["minutes"], "intro": drill["intro"], "steps": drill["steps"], "risk": drill["risk"],
        "optional": bool(drill.get("optional")), "status": status,
        "started_at": detail.get("started_at", ""), "ended_at": detail.get("ended_at", ""),
        "note": detail.get("note"), "result": detail.get("result"), "fallback": _public_fallback(detail.get("fallback")),
        "feedback": _last_feedback(conn, f"drill.{drill['id']}"), "accepted": bool(detail.get("accepted_by_reviewer")),
        "evidence_note": detail.get("evidence_note", ""),
    }


def drill_start(drill_id):
    drill = _drill_def(drill_id)
    with _conn() as conn:
        if not _item(conn, "deploy")["detail"].get("job"):
            raise ValueError("Start your deployment first. A drill breaks the thing you deployed.")
        item = _item(conn, f"drill.{drill_id}")
        if item["status"] in ("verified", "awaiting_review"):
            raise ValueError("This drill is already done.")
        _save_item(conn, f"drill.{drill_id}", status="running", detail={"started_at": _now(), "ended_at": "", "result": None, "fallback": None})
        _clear_misses(conn, f"drill.{drill_id}")
        return _drill_view(conn, drill)


def drill_recover(drill_id):
    drill = _drill_def(drill_id)
    with _conn() as conn:
        item = _item(conn, f"drill.{drill_id}")
        if not item["detail"].get("started_at"):
            raise ValueError("Start the drill first.")
        _save_item(conn, f"drill.{drill_id}", detail={"ended_at": _now()})
        return _drill_view(conn, drill)


def drill_note(drill_id, path):
    drill = _drill_def(drill_id)
    with _conn() as conn:
        item = _item(conn, f"drill.{drill_id}")
        if not item["detail"].get("ended_at"):
            raise ValueError("Say you recovered first, then write the recovery note.")
        record, digest, missing = _check_record(path, C.DRILL_SECTIONS, f"drill.{drill_id}")
        coach = _section_coach(C.DRILL_SECTIONS)
        if missing:
            return _failed_outcome(conn, f"drill.{drill_id}", "Your recovery note isn't finished yet", missing, coach)
        _clear_misses(conn, f"drill.{drill_id}")
        _save_item(conn, f"drill.{drill_id}", detail={"note": {**record, "checked_at": _now()}}, fingerprint=digest)
        return {"passed": True, "title": "Your recovery note is complete", "detail": "Now check the evidence Hermes recorded.", "facts": [{"label": "File", "value": record["name"]}], "missing": [], "drill": _drill_view(conn, drill)}


def drill_check(drill_id, sample=None, home=None, read_home=True):
    drill = _drill_def(drill_id)
    with _conn() as conn:
        deploy = _item(conn, "deploy")["detail"]
        item = _item(conn, f"drill.{drill_id}")
        detail = item["detail"]
        if not detail.get("started_at"):
            raise ValueError("Start the drill first.")
        _take_sample(conn, "deploy", deploy["job"], sample, home, read_home)
        times, failed = _union(_samples(conn, "deploy"))
        ended = evidence.parse_ts(detail["ended_at"]) if detail.get("ended_at") else None
        result = evidence.analyze_recovery(times, started=evidence.parse_ts(detail["started_at"]), ended=ended, now=_clock(), failed=failed)
        coach = {
            "open": {"hint": "Press I recovered once the job works again.", "example": ""},
            "no_before": {"hint": "The check needs to see the job running normally before the drill. Let the deployment run for a few days first.", "example": ""},
            "too_quick": {"hint": "Leave it broken for longer.", "example": "Example: through one full scheduled run."},
            "no_gap": {"hint": "A run still worked while you say it was broken. Check that the drill really broke it, such as the token being revoked.", "example": ""},
            "too_short": {"hint": "Keep it broken through at least one scheduled run.", "example": "Example: a job that runs every 6 hours needs 6 hours."},
            "no_recovery": {"hint": "Wait for the next scheduled run after you fixed it, then check again.", "example": ""},
            "future": {"hint": "Press I recovered only after you fixed it.", "example": ""},
        }
        if not detail.get("note"):
            result["missing"].append({"id": "note_missing", "what": "Write and check the recovery note first."})
            coach["note_missing"] = {"hint": "The recovery note says what you did, how you knew and how you fixed it.", "example": ""}
            result["passed"] = False
        note = f"{len(times)} run times and {len(failed)} failed runs recorded across the deployment."
        sid = f"drill.{drill_id}"
        if result["passed"]:
            _clear_misses(conn, sid)
            _save_item(conn, sid, status="verified", detail={"result": {"passed": True, "facts": result["facts"], "checked_at": _now()}, "evidence_note": note}, passed=True)
        elif not result.get("readable", True):
            _save_item(conn, sid, detail={"evidence_note": note})
            result["fallback"] = True
        else:
            result["feedback"] = _record_miss(conn, sid, lambda n: learning.ladder(n, result["missing"], coach))
            _save_item(conn, sid, detail={"result": {"passed": False, "facts": result["facts"], "checked_at": _now()}, "evidence_note": note})
        return {"outcome": result, "drill": _drill_view(conn, drill)}


def drill_fallback(drill_id, excerpt, notes=""):
    drill = _drill_def(drill_id)
    with _conn() as conn:
        item = _item(conn, f"drill.{drill_id}")
        if not item["detail"].get("ended_at"):
            raise ValueError("Say you recovered first.")
        packet = _fallback(conn, f"drill.{drill_id}", excerpt, notes, bool(item["detail"].get("note")))
        return {"ok": True, "fallback": _public_fallback(packet), "drill": _drill_view(conn, drill)}


# ------------------------------------------------------------- walkthrough ---


def _lab_tokens(conn):
    tokens = set()
    for lab_id in LAB_ORDER:
        row = _passed_lab_row(conn, lab_id)
        if not row:
            continue
        spec = labs.spec_for(lab_id, row["seed"])
        tokens.add(spec["client"]["name"].lower())
        if lab_id == "lab.leak":
            tokens.update(i["key_id"].lower() for i in spec["leaked"])
            tokens.add(os.path.basename(spec["leak_file"]).lower() if spec["leak_file"] != "config.yaml" else "config.yaml")
        if lab_id == "lab.cost":
            tokens.add(spec["runaway_job"].lower())
        if lab_id == "lab.vault":
            tokens.update(a["profile"].lower() for a in spec["agents"])
        if lab_id == "lab.reboot":
            tokens.add("backup.sh")
    return tokens


def walkthrough_view(conn):
    item = _item(conn, "walkthrough")
    review = _item(conn, "review")
    return {
        "item_id": "walkthrough", "title": C.WALKTHROUGH["title"], "intro": C.WALKTHROUGH["intro"], "prompt": C.WALKTHROUGH["prompt"], "min_chars": C.WALKTHROUGH["min_chars"],
        "saved": item["exists"] and item["detail"].get("explanation") is not None,
        "explanation": item["detail"].get("explanation", ""), "media": item["detail"].get("media"), "saved_at": item["detail"].get("saved_at", ""),
        "feedback": _last_feedback(conn, "walkthrough"),
        "review": _review_view(conn, review),
    }


def walkthrough_save(text, media_path=""):
    clean = " ".join((text or "").split())
    clean = SECRET_ANY.sub("[key removed]", clean)[:6000]
    with _conn() as conn:
        missing = []
        if len(clean) < C.WALKTHROUGH["min_chars"]:
            missing.append({"id": "walk_short", "what": f"Your walkthrough is {len(clean)} characters. Write at least {C.WALKTHROUGH['min_chars']}, so it covers what looked wrong, the evidence, what you changed and what you would do differently."})
        elif not any(t in clean.lower() for t in _lab_tokens(conn)):
            missing.append({"id": "walk_specific", "what": "Your walkthrough does not name anything from your own labs, such as the file, the job, the key id or the client. Name the details only someone who did the lab would know."})
        elif not re.search(r"differently|next time|mistake|wrong|learned|surprised|slow", clean, re.I):
            missing.append({"id": "walk_reflect", "what": "Say one thing you would do differently next time."})
        media = None
        if media_path:
            target = Path(media_path).expanduser()
            if not target.is_file():
                missing.append({"id": "walk_media", "what": f"No file at {target}. Leave the recording out, or type the right location."})
            else:
                digest = hashlib.sha256()
                with target.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1 << 20), b""):
                        digest.update(chunk)
                media = {"name": target.name, "bytes": target.stat().st_size, "sha256": digest.hexdigest()}
        coach = {
            "walk_short": {"hint": "Write four short paragraphs: what looked wrong, the evidence, what you changed, what you would do differently.", "example": ""},
            "walk_specific": {"hint": "Use the real names from your lab.", "example": "Example: \"The nightly-report job ran every minute, which the log showed.\""},
            "walk_reflect": {"hint": "Say what you would do differently next time.", "example": "Example: \"I would have read the log before opening any file.\""},
            "walk_media": {"hint": "Type the full location of the recording, or leave it out.", "example": "Example: ~/Documents/walkthrough.mp4 on Mac and Linux, or C:\\Users\\you\\Documents\\walkthrough.mp4 on Windows"},
        }
        if missing:
            return _failed_outcome(conn, "walkthrough", "Your walkthrough isn't ready yet", missing, coach)
        _clear_misses(conn, "walkthrough")
        _save_item(conn, "walkthrough", status="saved", detail={"explanation": clean, "media": media, "saved_at": _now()})
        return {"passed": True, "title": "Your walkthrough is saved", "detail": "It goes into the review packet in your own words.", "facts": [], "missing": [], "walkthrough": walkthrough_view(conn)}


# --------------------------------------------------------------------- review --


def _item_state(conn, key):
    """verified, awaiting_review, in_progress or not_started for one waypoint of the path."""
    if key in LAB_ORDER:
        if _passed_lab_row(conn, key):
            return "verified"
        return "in_progress" if _lab_row(conn, key) else "not_started"
    if key == "brief":
        item = _item(conn, "brief")
        return "verified" if item["status"] == "verified" else ("in_progress" if item["exists"] else "not_started")
    if key == "scenarios":
        passed = sum(1 for sid in scenarios.IDS if scenario_view(conn, sid)["status"] == "verified")
        if passed == len(scenarios.IDS):
            return "verified"
        return "in_progress" if conn.execute("SELECT COUNT(*) AS n FROM deployer_answers WHERE item_id LIKE 'scenario.%'").fetchone()["n"] else "not_started"
    if key == "deploy":
        item = _item(conn, "deploy")
        if item["status"] == "verified" or (item["status"] == "awaiting_review" and item["detail"].get("accepted_by_reviewer")):
            return "verified"
        if item["status"] == "awaiting_review":
            return "awaiting_review"
        return "in_progress" if item["detail"].get("started_at") else "not_started"
    if key == "drills":
        states = [_drill_state(conn, d) for d in DRILL_IDS]
        done = sum(1 for s in states if s == "verified")
        if done >= C.DRILL_RULES["min_drills"]:
            return "verified"
        if any(s == "awaiting_review" for s in states) and done + sum(1 for s in states if s == "awaiting_review") >= C.DRILL_RULES["min_drills"]:
            return "awaiting_review"
        return "in_progress" if any(s != "not_started" for s in states) else "not_started"
    if key == "walkthrough":
        review = _item(conn, "review")
        if review["status"] == "signed":
            return "verified"
        if review["status"] in ("awaiting_review", "rejected", "stale"):
            return "awaiting_review"
        return "in_progress" if _item(conn, "walkthrough")["exists"] else "not_started"
    raise ValueError(key)


def _drill_state(conn, drill_id):
    item = _item(conn, f"drill.{drill_id}")
    if item["status"] == "verified" or (item["status"] == "awaiting_review" and item["detail"].get("accepted_by_reviewer")):
        return "verified"
    if item["status"] == "awaiting_review":
        return "awaiting_review"
    return "in_progress" if item["detail"].get("started_at") else "not_started"


KEYS = ("lab.leak", "lab.cost", "lab.reboot", "lab.vault", "brief", "scenarios", "deploy", "drills", "walkthrough")


def _readiness(conn):
    """What is left before a review packet can be built. Walkthrough itself comes last."""
    waiting = []
    for key in KEYS[:-1]:
        state = _item_state(conn, key)
        if state not in ("verified", "awaiting_review"):
            waiting.append(C.ITEM_TITLES[key])
    if not _item(conn, "walkthrough")["exists"]:
        waiting.append("The walkthrough in your own words")
    return waiting


def _packet_evidence(conn, learner):
    """Everything the reviewer sees. Built only from records, so it can be rebuilt and compared."""
    lab_rows = []
    for lab_id in LAB_ORDER:
        row = _passed_lab_row(conn, lab_id)
        lab_rows.append({
            "lab_id": lab_id, "title": labs.TITLES[lab_id], "seed": row["seed"], "attempts": row["attempts"], "passed_at": row["passed_at"],
            "tree_fingerprint": row["tree_fingerprint"], "changed": _json(row["changed_json"], []), "diagnosis": row["diagnosis"],
        })
    b = _item(conn, "brief")
    ans = conn.execute("SELECT * FROM deployer_answers WHERE item_id = 'brief'").fetchone()
    brief = brief_mod.brief_for(_brief_seed(conn))
    scen = []
    for sid in scenarios.IDS:
        row = conn.execute("SELECT * FROM deployer_answers WHERE item_id = ?", (f"scenario.{sid}",)).fetchone()
        scen.append({"id": sid, "title": scenarios.BY_ID[sid]["title"], "score": row["score"], "answer": row["answer"], "answer_sha256": hashlib.sha256(row["answer"].encode()).hexdigest()})
    d = _item(conn, "deploy")
    dd = d["detail"]
    deployment = {
        "service": dd.get("service", ""), "job": dd.get("job", ""), "started_at": dd.get("started_at", ""), "status": d["status"],
        "record": dd.get("record"), "evidence_note": dd.get("evidence_note", ""), "checks": len(_samples(conn, "deploy")),
        "sources": sorted({s["source"] for s in _samples(conn, "deploy")}),
    }
    drills, fallback = [], []
    if dd.get("fallback"):
        fallback.append({"item": "deploy", "sha256": dd["fallback"]["sha256"], "excerpt": dd["fallback"]["excerpt"], "timestamps": dd["fallback"]["timestamps"], "days": dd["fallback"]["days"], "notes": dd["fallback"].get("notes", "")})
    for drill in C.DRILLS:
        it = _item(conn, f"drill.{drill['id']}")
        if not it["detail"].get("started_at"):
            continue
        drills.append({"id": drill["id"], "title": drill["title"], "status": it["status"], "started_at": it["detail"].get("started_at"), "ended_at": it["detail"].get("ended_at"), "note": it["detail"].get("note"), "evidence_note": it["detail"].get("evidence_note", "")})
        if it["detail"].get("fallback"):
            f = it["detail"]["fallback"]
            fallback.append({"item": f"drill.{drill['id']}", "sha256": f["sha256"], "excerpt": f["excerpt"], "timestamps": f["timestamps"], "days": f["days"], "notes": f.get("notes", "")})
    w = _item(conn, "walkthrough")
    version = current_version(conn)
    return {
        "learner": learner,
        "hermes_version": {"value": version["value"], "source": version["source"]},
        "plugin_version": _plugin_version(),
        "labs": lab_rows,
        "brief": {"firm": brief["firm"], "document": b["detail"].get("document", ""), "sha256": b["fingerprint"], "score": b["score"], "text": ans["answer"] if ans else ""},
        "scenarios": scen,
        "deployment": deployment,
        "drills": drills,
        "fallback_evidence": fallback,
        "walkthrough": {"explanation": w["detail"].get("explanation", ""), "media": w["detail"].get("media"), "saved_at": w["detail"].get("saved_at", "")},
        "limits": C.HONEST_LIMITS,
        "rubric": [r["id"] for r in walkthrough.RUBRIC],
    }


def _plugin_version():
    manifest = PLUGIN_ROOT / "plugin.yaml"
    try:
        for line in manifest.read_text().splitlines():
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return ""


def _evidence_digest(body):
    return hashlib.sha256(walkthrough.canonical(body).encode("utf-8")).hexdigest()


def build_review_packet(learner):
    learner = _clean(learner, 80)
    if not learner:
        raise ValueError("Type your name, the way you want it on the packet.")
    with _conn() as conn:
        waiting = _readiness(conn)
        if waiting:
            raise ValueError("Finish these first: " + "; ".join(waiting) + ".")
        body = _packet_evidence(conn, learner)
        packet = walkthrough.build_packet(body, _now())
        folder = _data_dir(conn) / "deployer" / "review"
        sources = {lab_id: _passed_lab_row(conn, lab_id)["folder"] for lab_id in LAB_ORDER}
        paths = walkthrough.write_packet(folder, packet, sources)
        _save_item(conn, "review", status="awaiting_review", detail={"packet": packet, "paths": paths, "digest": _evidence_digest(body), "signoff": None, "result": None, "built_at": _now()}, fingerprint=packet["fingerprint"])
        return _review_view(conn, _item(conn, "review"))


def _review_view(conn, item=None):
    item = item or _item(conn, "review")
    waiting = _readiness(conn)
    trusted = trusted_reviewers(conn)
    base = {
        "status": "locked", "waiting": waiting, "rubric": walkthrough.RUBRIC, "floor": walkthrough.FLOOR,
        "reviewers": {
            "published": sorted(v["name"] for v in trusted.values() if v["list"] == "published"),
            "local": sorted(v["name"] for v in trusted.values() if v["list"] == "local"),
        },
    }
    if item["status"] in ("open",) or not item["exists"]:
        base["status"] = "ready" if not waiting else "locked"
        return base
    detail = item["detail"]
    status = item["status"]
    if status == "awaiting_review" and detail.get("digest"):
        try:
            if detail["digest"] != _evidence_digest(_packet_evidence(conn, detail["packet"]["learner"])):
                status = "stale"
        except (TypeError, KeyError):
            pass
    result = detail.get("result") or {}
    return {
        **base, "status": status, "fingerprint": item["fingerprint"], "paths": detail.get("paths"), "built_at": detail.get("built_at", ""),
        "learner": detail["packet"]["learner"], "needs_acceptance": result.get("needs_acceptance", []),
        "fallback_items": [f["item"] for f in detail["packet"].get("fallback_evidence", [])],
        "problems": result.get("problems", []), "reviewer": result.get("reviewer") or None, "list": result.get("list", ""),
        "scores": result.get("scores", {}), "comments": result.get("comments", ""), "signed_at": result.get("signed_at", ""),
        "key_fingerprint": result.get("key_fingerprint", ""),
    }


def trusted_reviewers(conn=None):
    local = (_data_dir(conn) / "deployer" / "reviewers.local.json") if conn else None
    return walkthrough.load_trusted(PUBLISHED_REVIEWERS, local)


def trust_local_reviewer(name, public_key):
    """Add a reviewer's public key to this computer's own list.

    The published list ships empty until reviewers are named. A learner who has a
    reviewer can add that reviewer's key here, and every Field Record signed with it
    says the key came from the learner's own list, so a reader knows to check it.
    """
    clean_name = _clean(name, 120).strip()
    key = str(public_key or "").strip().lower()
    if not clean_name:
        raise ValueError("Type the reviewer's name.")
    if not re.fullmatch(r"[0-9a-f]{64}", key):
        raise ValueError("A reviewer key is 64 characters, the digits 0 to 9 and the letters a to f. Copy it from the reviewer.")
    with _conn() as conn:
        path = _data_dir(conn) / "deployer" / "reviewers.local.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        except (OSError, ValueError):
            data = {}
        reviewers = [r for r in data.get("reviewers", []) if str(r.get("public_key", "")).lower() != key]
        reviewers.append({"name": clean_name, "public_key": key, "added_at": _now()})
        path.write_text(json.dumps({"about": "Reviewers you added on this computer. Field Records signed by these keys say so.", "reviewers": reviewers}, indent=2) + "\n", encoding="utf-8")
    return {"name": clean_name, "list": "local", "count": len(reviewers)}


def load_signoff(text):
    """Read a reviewer's signed sign-off and check it against the packet. Only a valid, approved sign-off from a trusted key counts."""
    try:
        signoff = json.loads(text) if isinstance(text, str) else text
    except ValueError as exc:
        raise ValueError("That is not valid JSON. Paste the whole signed file the reviewer sent.") from exc
    with _conn() as conn:
        item = _item(conn, "review")
        if not item["exists"] or not item["detail"].get("packet"):
            raise ValueError("Build the review packet first. The reviewer signs a specific packet.")
        packet = item["detail"]["packet"]
        current = _evidence_digest(_packet_evidence(conn, packet["learner"]))
        if current != item["detail"].get("digest"):
            _save_item(conn, "review", status="stale")
            raise ValueError("Your work changed after the packet was built. Build a new packet and ask the reviewer to sign that one.")
        result = walkthrough.verify_signoff(signoff, packet, trusted_reviewers(conn))
        if result["approved"]:
            _save_item(conn, "review", status="signed", detail={"signoff": signoff, "result": result}, passed=True)
            accepted = set(result["accepted_evidence"])
            for item_id in accepted:
                if item_id == "deploy" or item_id.startswith("drill."):
                    cur = _item(conn, item_id)
                    if cur["status"] == "awaiting_review":
                        _save_item(conn, item_id, detail={"accepted_by_reviewer": True, "accepted_at": _now()})
        else:
            _save_item(conn, "review", status="rejected" if result["valid"] else "awaiting_review", detail={"result": result})
        return _review_view(conn)


# ---------------------------------------------------------------- versions ---


def set_version(value, source="typed by you"):
    value = _clean(value, 40)
    if not evidence.parse_version(value):
        raise ValueError("That does not look like a version. Type it the way Hermes shows it, for example 0.12.3.")
    with _conn() as conn:
        store.meta_set(conn, "deployer:hermes_version", value)
        store.meta_set(conn, "deployer:hermes_version_source", _clean(source, 60))
        store.meta_set(conn, "deployer:hermes_version_seen", _now())
        return current_version(conn)


def current_version(conn):
    value = store.meta_get(conn, "deployer:hermes_version", "")
    source = store.meta_get(conn, "deployer:hermes_version_source", "")
    if not value:
        detected, how = evidence.detect_version()
        if detected:
            return {"value": detected, "source": f"read from the {how}", "machine_read": True, "seen_at": ""}
        return {"value": "", "source": "", "machine_read": False, "seen_at": ""}
    return {"value": value, "source": source, "machine_read": not source.startswith("typed"), "seen_at": store.meta_get(conn, "deployer:hermes_version_seen", "")}


def reverify_view(conn):
    row = conn.execute("SELECT * FROM certificates WHERE track_id = 'deployer'").fetchone()
    if not row:
        return None
    body = _json(row["body_json"], {})
    renewals = [dict(r) for r in conn.execute("SELECT * FROM deployer_renewals ORDER BY id")]
    baseline = renewals[-1]["hermes_version"] if renewals else (body.get("hermes_version") or {}).get("value", "")
    status = evidence.reverify_status(baseline, current_version(conn)["value"])
    status["earned_on"] = (body.get("hermes_version") or {}).get("value", "")
    status["renewed"] = [{"version": r["hermes_version"], "at": r["created_at"]} for r in renewals]
    status["open"] = store.meta_get(conn, "deployer:reverify_started", "") != ""
    return status


def start_reverify():
    """Re-verify means four new lab cases on the current Hermes. The proposal, the cases and the review are not repeated."""
    with _conn() as conn:
        status = reverify_view(conn)
        if not status or status["status"] != "reverify":
            raise ValueError("Nothing to re-verify. The Field Record is current.")
        store.meta_set(conn, "deployer:reverify_started", _now())
    for lab_id in LAB_ORDER:
        with _conn() as conn:
            row = _lab_row(conn, lab_id)
            if row:
                store.meta_set(conn, f"deployer:seed:{lab_id}", "")
        open_lab(lab_id)
    with _conn() as conn:
        return reverify_view(conn)


def finish_reverify():
    with _conn() as conn:
        started = store.meta_get(conn, "deployer:reverify_started", "")
        if not started:
            raise ValueError("Start the re-verify first.")
        fresh = []
        for lab_id in LAB_ORDER:
            row = _lab_row(conn, lab_id)
            if not row or row["status"] != "passed" or row["passed_at"] < started:
                raise ValueError(f"Pass the new case for {labs.TITLES[lab_id]} first.")
            fresh.append({"lab_id": lab_id, "seed": row["seed"], "tree_fingerprint": row["tree_fingerprint"], "passed_at": row["passed_at"]})
        version = current_version(conn)
        body = {"hermes_version": version["value"], "source": version["source"], "labs": fresh, "created_at": _now()}
        conn.execute("INSERT INTO deployer_renewals(hermes_version, version_source, created_at, body_json) VALUES (?, ?, ?, ?)", (version["value"], version["source"], _now(), json.dumps(body)))
        store.meta_set(conn, "deployer:reverify_started", "")
        return reverify_view(conn)


# -------------------------------------------------------------- field record --


def _certificate_status(conn):
    row = conn.execute("SELECT 1 FROM certificates WHERE track_id = 'deployer'").fetchone()
    if row:
        return "issued"
    states = [_item_state(conn, key) for key in KEYS]
    if all(s == "verified" for s in states):
        return "ready"
    if all(s in ("verified", "awaiting_review") for s in states) and _item(conn, "review")["exists"]:
        return "awaiting_review"
    if any(s != "not_started" for s in states):
        return "in_progress"
    return "not_started"


def issue_certificate(name):
    from . import state

    clean = _clean(name, 80)
    with _conn() as conn:
        existing = conn.execute("SELECT * FROM certificates WHERE track_id = 'deployer'").fetchone()
        if existing:
            return state._certificate_view(existing)
        status = _certificate_status(conn)
        if status == "awaiting_review":
            raise ValueError("Guide, awaiting review. The Field Record needs your reviewer's signed sign-off, and it has not been loaded yet.")
        if status != "ready":
            raise ValueError("Finish every part of the path first, including the review.")
        if not clean:
            raise ValueError("Type the name you want on your Field Record.")
        version = current_version(conn)
        if not version["value"]:
            raise ValueError("Tell Field Academy which Hermes version you are on, so the Field Record can show it.")
        review = _item(conn, "review")
        result = review["detail"]["result"]
        issued_at = _now()
        labs_body = []
        for lab_id in LAB_ORDER:
            row = _passed_lab_row(conn, lab_id)
            labs_body.append({"lab_id": lab_id, "title": labs.TITLES[lab_id], "seed": row["seed"], "attempts": row["attempts"], "passed_at": row["passed_at"], "tree_fingerprint": row["tree_fingerprint"]})
        b = _item(conn, "brief")
        d = _item(conn, "deploy")
        body = {
            "record": "Field Academy Guide Field Record",
            "record_format": pathways.RECORD_FORMAT,
            "path_id": "deployer",
            "path": "Guide",
            "path_promise": C.PROMISE,
            "name": clean,
            "issued_at": issued_at,
            "hermes_version": {"value": version["value"], "source": version["source"], "machine_read": version["machine_read"]},
            "labs": labs_body,
            "brief": {"firm": brief_mod.brief_for(_brief_seed(conn))["firm"], "document": b["detail"].get("document", ""), "fingerprint": b["fingerprint"], "score": b["score"]},
            "scenarios": [{"id": sid, "score": scenario_view(conn, sid)["score"]} for sid in scenarios.IDS],
            "deployment": {"service": d["detail"].get("service", ""), "status": "accepted by the reviewer" if d["status"] == "awaiting_review" else "read from Hermes", "checks": len(_samples(conn, "deploy"))},
            "drills": [{"id": i, "status": ("accepted by the reviewer" if _item(conn, f"drill.{i}")["status"] == "awaiting_review" else "read from Hermes")} for i in DRILL_IDS if _drill_state(conn, i) == "verified"],
            "review": {
                "reviewer": result["reviewer"]["name"], "role": result["reviewer"].get("role", ""), "key_fingerprint": result["key_fingerprint"], "list": result["list"],
                "packet_fingerprint": review["fingerprint"], "scores": result["scores"], "signed_at": result["signed_at"], "rubric_version": walkthrough.RUBRIC_VERSION,
            },
            "shows": C.WHAT_IT_SHOWS,
            "does_not_show": C.WHAT_IT_DOES_NOT,
            "lifecycle_credit": C.LIFECYCLE_CREDIT,
            "issuer": C.ISSUER,
            "disclaimer": pathways.DISCLAIMER,
            "plugin_version": _plugin_version(),
        }
        body["number"] = state.certificate_number(body)
        conn.execute(
            "INSERT OR IGNORE INTO certificates(track_id, name, number, issued_at, body_json) VALUES ('deployer', ?, ?, ?, ?)",
            (clean, body["number"], issued_at, state._canonical(body)),
        )
        return state._certificate_view(conn.execute("SELECT * FROM certificates WHERE track_id = 'deployer'").fetchone())


def certificate_markdown(certificate):
    from . import state

    body = certificate["body"]
    display = certificate.get("display") or state.record_display(body)
    review = body["review"]
    lines = [
        "# Field Record: Guide path", "",
        display["disclaimer"], "",
        f"Kept by **{body['name']}**, created on {state._human_date(body['issued_at'])}.", "",
        body["path_promise"], "",
        f"Record number: `{body['number']}`",
        f"Recorded on Hermes {body['hermes_version']['value']} ({body['hermes_version']['source']}). When the major version of Hermes changes, this record needs to be re-verified.", "",
        "## The review", "",
        f"Signed by {review['reviewer']}, a reviewer the holder chose, on {state._human_date(review['signed_at'])}, key `{review['key_fingerprint']}`, "
        + ("on Field Academy's published reviewer list." if review["list"] == "published" else "not on Field Academy's published reviewer list; the holder's own list."),
        f"Packet fingerprint `{review['packet_fingerprint'][:16]}`. Scores out of 3: " + ", ".join(f"{k} {v}" for k, v in review["scores"].items()) + ".", "",
        "## The proof behind it", "",
        "| Lab | Seed | Checks taken | Passed | Repaired folder fingerprint |", "|---|---|---|---|---|",
    ]
    for lab in body["labs"]:
        lines.append(f"| {lab['title']} | {lab['seed']} | {lab['attempts']} | {state._human_date(lab['passed_at'])} | `{lab['tree_fingerprint'][:16]}` |")
    lines += [
        "", f"Proposal for {body['brief']['firm']}: scored {body['brief']['score']} on the prose, fingerprint `{body['brief']['fingerprint'][:16]}`.",
        "Judgment scenarios: " + ", ".join(f"{s['id']} {s['score']}" for s in body["scenarios"]) + ".",
        f"Real deployment: {body['deployment']['service']}, {body['deployment']['status']}, {body['deployment']['checks']} checks.",
        "Failure drills: " + (", ".join(f"{d['id']} ({d['status']})" for d in body["drills"]) or "none"), "",
        "## What this record shows", "", *[f"- {line}" for line in display["shows"]], "",
        "## What it does not show", "", *[f"- {line}" for line in display["does_not_show"]], "",
        body["lifecycle_credit"], "", display["issuer"], "", display["disclaimer"], "",
        "The record number is the first 12 characters of a SHA-256 over this record's contents, as stored in the matching .json file. Change any line and the number stops matching.", "",
    ]
    note = state.legacy_note(display)
    if note:
        lines += [note, ""]
    return "\n".join(lines)


def save_certificate():
    from . import state

    with _conn() as conn:
        row = conn.execute("SELECT * FROM certificates WHERE track_id = 'deployer'").fetchone()
        if not row:
            raise ValueError("Create your Field Record first.")
        cert = state._certificate_view(row)
        folder = _data_dir(conn) / "field-records"
    folder.mkdir(parents=True, exist_ok=True)
    stem = "field-academy-deployer-field-record"
    (folder / f"{stem}.md").write_text(certificate_markdown(cert), encoding="utf-8")
    (folder / f"{stem}.json").write_text(json.dumps(cert["body"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"markdown": str(folder / f"{stem}.md"), "json": str(folder / f"{stem}.json"), "number": cert["number"]}


# ------------------------------------------------------------------ snapshot --

STATUS_FOR_MAP = {"verified": "verified", "awaiting_review": "in_progress", "in_progress": "in_progress", "not_started": "not_started"}


def snapshot():
    """The whole Deployer tier for the page: the path as a trail, and every part with its state."""
    from . import state

    with _conn() as conn:
        states = {key: _item_state(conn, key) for key in KEYS}
        cert_row = conn.execute("SELECT * FROM certificates WHERE track_id = 'deployer'").fetchone()
        cert_status = _certificate_status(conn)
        items = []
        for key in KEYS:
            detail = ""
            if key == "scenarios":
                detail = f"{sum(1 for sid in scenarios.IDS if scenario_view(conn, sid)['status'] == 'verified')} of {len(scenarios.IDS)} passed"
            if key == "drills":
                detail = f"{sum(1 for d in DRILL_IDS if _drill_state(conn, d) == 'verified')} of {C.DRILL_RULES['min_drills']} needed"
            items.append({"id": key, "title": C.ITEM_TITLES[key], "minutes": C.ITEM_MINUTES[key], "state": states[key], "detail": detail})
        phases = []
        current_found = False
        for number, phase in enumerate(C.PHASES, start=1):
            statuses = [states[k] for k in phase["items"]]
            passed = sum(1 for s in statuses if s == "verified")
            status = "passed" if passed == len(statuses) else ("started" if any(s != "not_started" for s in statuses) else "not_started")
            is_current = not current_found and status != "passed"
            current_found = current_found or is_current
            phases.append({"id": phase["id"], "short_name": phase["short"], "number": number, "name": phase["name"], "meaning": phase["meaning"], "missions": list(phase["items"]), "passed": passed, "total": len(statuses), "status": status, "current": is_current})
        by_phase = {item_key: p for p in C.PHASES for item_key in p["items"]}
        missions = []
        for item in items:
            phase = by_phase[item["id"]]
            missions.append({"id": item["id"], "title": item["title"], "status": STATUS_FOR_MAP[item["state"]], "level": phase["id"], "level_name": phase["name"], "minutes": item["minutes"], "total_steps": 1, "completed_steps": 1 if item["state"] == "verified" else 0, "version": 1, "use_text": "", "strength": None, "changed": False, "time": {}})
        here = next((m["id"] for m in missions if m["status"] != "verified"), "")
        remaining = sum(1 for m in missions if m["status"] != "verified")
        issued = state._certificate_view(cert_row) if cert_row else None
        track = {
            "id": "deployer", "name": C.TITLE, "eyebrow": C.EYEBROW, "lore": C.LORE, "promise": C.PROMISE, "unit": "parts", "missions": missions, "levels": phases, "here": here,
            "verified_missions": len(missions) - remaining, "placement": {"available": False},
            "certificate": {"status": "issued" if issued else ("ready" if cert_status == "ready" else "in_progress"), "remaining": remaining, "title": "Guide Field Record", "issued": issued,
                            "words": {"awaiting_review": "Guide, awaiting review", "issued": "Field Record created", "ready": "Field Record ready to create"}.get(cert_status, "")},
        }
        version = current_version(conn)
        return {
            "available": True,
            "track": track,
            "items": items,
            "labs": [lab_view(conn, lab_id) for lab_id in LAB_ORDER],
            "brief": brief_view(conn),
            "scenarios": [scenario_view(conn, sid) for sid in scenarios.IDS],
            "deploy": _deploy_view(conn),
            "drills": [_drill_view(conn, d) for d in C.DRILLS],
            "drill_note": C.DRILL_NOTE,
            "drills_needed": C.DRILL_RULES["min_drills"],
            "walkthrough": walkthrough_view(conn),
            "certificate": {
                "status": cert_status,
                "label": {"issued": "Guide Field Record created", "ready": "Guide, ready to create your Field Record", "awaiting_review": "Guide, awaiting review"}.get(cert_status, "Guide path in progress"),
                "issued": issued,
                "reverify": reverify_view(conn),
                "needs_version": not version["value"],
            },
            "hermes_version": version,
            "about": {
                "certifies": C.WHAT_IT_SHOWS, "shows": C.WHAT_IT_SHOWS, "does_not": C.WHAT_IT_DOES_NOT, "lifecycle_credit": C.LIFECYCLE_CREDIT, "issuer": C.ISSUER,
                "disclaimer": pathways.DISCLAIMER,
                "promise": C.PROMISE, "limits": C.HONEST_LIMITS,
            },
        }


def summary_line():
    """One line for /academy: where the Deployer path stands."""
    data = snapshot()
    done = sum(1 for i in data["items"] if i["state"] == "verified")
    status = data["certificate"]["label"]
    return f"Guide: {done} of {len(data['items'])} parts passed. {status}."
