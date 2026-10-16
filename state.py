"""Durable mission progress, checks on real work, reviews and evidence for Field Academy.

Storage lives in store.py, the spaced-review queue in review.py, the learning
rules (intervals, hint ladder, placement marking) in learning.py, and the
document reader in documents.py. This file ties them to the curriculum: it
decides what a step's status means, records what a check found, and builds the
passport the page reads.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from . import documents, learning, pathways, review, store
from .curriculum import (
    MISSIONS,
    PLACEMENTS,
    REVISIONS,
    SKIPPABLE_KINDS,
    STEPS,
    TRACKS,
    get_mission,
    index,
    public_tracks,
    revisions_since,
)

PLUGIN_ID = store.PLUGIN_ID
VALID_CONTEXTS = {"personal", "team", "client", "enterprise"}
VALID_STEP_STATUS = {"ready", "done", "needs_attention"}
# A step that counts toward finishing a mission. "placed" is a step a placement
# check skipped: the reading and practice, never the question or the check.
COUNTED = ("done", "placed")

# Artifact gates read a file the learner names. The backend runs inside the
# gateway process, so the read is capped and must decode as UTF-8: an unbounded
# read is a way to take the agent down with one large file, and a binary read
# with errors="replace" can satisfy a heading check by accident.
MAX_ARTIFACT_BYTES = 5 * 1024 * 1024

GOAL_MIN_CHARS = 8
GOAL_MAX_CHARS = 240

_connection = store.connect
_now = store.now
_meta_get = store.meta_get
_meta_set = store.meta_set


def _clean(text, limit):
    return " ".join((text or "").split())[:limit]


def _clean_lines(text, limit):
    """Trim each line but keep the line breaks, because a list is made of them."""
    lines = [" ".join(line.split()) for line in (text or "").splitlines()]
    return "\n".join(lines).strip()[:limit]


# ── Orientation and the learner's own goal ───────────────────────────────────


def set_orientation(track_id, context):
    if track_id not in {"operator", "integrator", "architect", "ambassador"}:
        raise ValueError(f"Unknown path: {track_id}")
    if context not in VALID_CONTEXTS:
        raise ValueError(f"Unknown learning context: {context}")
    with _connection() as conn:
        _meta_set(conn, "goal_track", track_id)
        _meta_set(conn, "learning_context", context)
        _meta_set(conn, "oriented", "1")
    return snapshot()


def set_goal(track_id):
    fallback = "personal" if track_id == "operator" else "client"
    with _connection() as conn:
        current = _meta_get(conn, "learning_context", fallback)
    return set_orientation(track_id, current if current in VALID_CONTEXTS else fallback)


def set_use_goal(text="", skipped=False):
    """Save the answer to "What do you want Hermes to do for you?".

    The answer is woven into mission text and practice prompts so the work is
    about the learner's own use. Skipping is a real choice and is saved too, so
    the question isn't asked twice. Both can be changed later.
    """
    clean = _clean(text, GOAL_MAX_CHARS)
    if skipped and not clean:
        with _connection() as conn:
            _meta_set(conn, "use_goal", "")
            _meta_set(conn, "use_goal_skipped", "1")
        return snapshot()
    if len(clean) < GOAL_MIN_CHARS:
        raise ValueError("Write a few words about what you want Hermes to do for you.")
    with _connection() as conn:
        _meta_set(conn, "use_goal", clean)
        _meta_set(conn, "use_goal_skipped", "0")
        _meta_set(conn, "use_goal_at", _now())
    return snapshot()


def _goal(conn):
    text = _meta_get(conn, "use_goal", "")
    return {
        "text": text,
        "asked": bool(text) or _meta_get(conn, "use_goal_skipped", "0") == "1",
        "skipped": not text and _meta_get(conn, "use_goal_skipped", "0") == "1",
    }


def _quoted(goal_text):
    return "“" + goal_text.strip().rstrip(".!? ") + "”"


def _use_text(mission, goal_text):
    """The "Why this matters to you" line: the learner's own goal when there is one."""
    if goal_text and mission.get("use"):
        return mission["use"].replace("{goal}", _quoted(goal_text))
    return mission.get("use_plain", "")


def _weave(prompt, goal_text):
    """Tack the learner's goal onto a practice prompt so every example is theirs."""
    if not prompt or not goal_text:
        return prompt
    return f"{prompt} Use my own goal as the example whenever you need one: {_quoted(goal_text)}."


# ── Steps ────────────────────────────────────────────────────────────────────


def start_mission(mission_id):
    if mission_id not in MISSIONS:
        raise ValueError(f"Unknown mission: {mission_id}")
    with _connection() as conn:
        _meta_set(conn, "active_mission", mission_id)
        _meta_set(conn, "goal_track", MISSIONS[mission_id]["track"])
    return mission_snapshot(mission_id)


def update_step(mission_id, step_id, status="done", note=""):
    if (mission_id, step_id) not in STEPS:
        raise ValueError(f"Unknown mission step: {mission_id}/{step_id}")
    if status not in VALID_STEP_STATUS:
        raise ValueError(f"Unknown step status: {status}")
    step = STEPS[(mission_id, step_id)]
    if step["kind"] == "gate" and status == "done":
        raise ValueError("Click Check my work. This step is done when the check passes.")
    if step["kind"] == "explain" and status == "done":
        raise ValueError("Send your answer for scoring. This step is done when it scores 70 or more.")
    if step["kind"] == "complete" and status == "done":
        raise ValueError("Fill in the gaps and compare with the model answers. This step is done when you have.")
    with _connection() as conn:
        _upsert_step(conn, mission_id, step_id, status, _clean(note, 1200))
        _meta_set(conn, "active_mission", mission_id)
        _meta_set(conn, "goal_track", MISSIONS[mission_id]["track"])
    return mission_snapshot(mission_id)


def _upsert_step(conn, mission_id, step_id, status, note):
    conn.execute(
        """INSERT INTO mission_steps(mission_id, step_id, status, note, updated_at)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(mission_id, step_id) DO UPDATE SET
             status = excluded.status, note = excluded.note, updated_at = excluded.updated_at""",
        (mission_id, step_id, status, note, _now()),
    )


def _step_status(conn, mission_id, step_id):
    row = conn.execute(
        "SELECT status FROM mission_steps WHERE mission_id = ? AND step_id = ?", (mission_id, step_id)
    ).fetchone()
    return row["status"] if row else "ready"


def _is_verified(conn, mission_id):
    statuses = {
        row["step_id"]: row["status"]
        for row in conn.execute("SELECT step_id, status FROM mission_steps WHERE mission_id = ?", (mission_id,))
    }
    if not all(statuses.get(step["id"]) in COUNTED for step in MISSIONS[mission_id]["steps"]):
        return False
    return conn.execute(
        "SELECT 1 FROM evidence WHERE mission_id = ? AND kind != 'note' LIMIT 1", (mission_id,)
    ).fetchone() is not None


# ── Misses, and what to say about them ───────────────────────────────────────


def _misses(conn, mission_id, step_id):
    row = conn.execute(
        "SELECT misses FROM attempts WHERE mission_id = ? AND step_id = ?", (mission_id, step_id)
    ).fetchone()
    return int(row["misses"]) if row else 0


def _record_miss(conn, mission_id, step_id, feedback_builder):
    """Count one more miss, build the feedback for that count, and keep it for the page."""
    count = _misses(conn, mission_id, step_id) + 1
    feedback = feedback_builder(count)
    conn.execute(
        """INSERT INTO attempts(mission_id, step_id, misses, last_feedback_json, updated_at)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(mission_id, step_id) DO UPDATE SET
             misses = excluded.misses, last_feedback_json = excluded.last_feedback_json, updated_at = excluded.updated_at""",
        (mission_id, step_id, count, json.dumps(feedback), _now()),
    )
    return feedback


def _clear_misses(conn, mission_id, step_id):
    conn.execute("DELETE FROM attempts WHERE mission_id = ? AND step_id = ?", (mission_id, step_id))


def _last_feedback(conn, mission_id, step_id):
    row = conn.execute(
        "SELECT misses, last_feedback_json FROM attempts WHERE mission_id = ? AND step_id = ?", (mission_id, step_id)
    ).fetchone()
    if not row or not row["last_feedback_json"]:
        return None
    try:
        return json.loads(row["last_feedback_json"])
    except ValueError:
        return None


def gate_coach(step):
    """What to say for each way a check can miss: the mission's own words first, then the general ones."""
    coach = {key: dict(value) for key, value in learning.GENERIC_COACH.items()}
    for rule in step.get("sections") or []:
        coach[f"section:{rule['heading']}"] = {"hint": rule.get("hint", ""), "example": rule.get("example", "")}
    for key, value in (step.get("fixes") or {}).items():
        coach[key] = {"hint": value.get("hint", ""), "example": value.get("example", "")}
    return coach


def _safe_missing(items):
    out = []
    for item in (items or [])[:8]:
        if isinstance(item, dict) and item.get("id"):
            out.append({"id": _clean(str(item["id"]), 80), "what": _clean(str(item.get("what", "")), 400)})
    return out


# ── Gates ────────────────────────────────────────────────────────────────────


def _models(mission_id):
    """The worked and half-finished examples, so a document that is mostly one of them is caught."""
    models = []
    for step in MISSIONS[mission_id]["steps"]:
        if step["kind"] == "example" and step.get("document"):
            models.append(step["document"])
        if step["kind"] == "complete":
            models.append("".join(part.get("text") or part.get("answer", "") for part in step["parts"]))
    return models


def _file_problem(target, title, detail, facts):
    return {
        "passed": False,
        "title": title,
        "detail": detail,
        "facts": facts,
        "missing": [{"id": "file", "what": detail}],
    }


def verify_artifact(mission_id, step_id, path, live=None):
    """Read a real file and check each section for real content, then hash it.

    This is the only way an artifact gate closes. Each section needs its own
    words, its own number or name where the section asks for one, and no
    placeholder text. A document that is mostly the worked example fails. A
    fingerprint already used for another mission fails, so one file can't pass
    twice. The fingerprint of a pass goes on the Field Record.

    Bounded on purpose: the backend runs inside the gateway process, so an
    unbounded read is a way to take the agent down with a large file, and a
    binary read as text can accidentally satisfy a heading check.
    """
    if (mission_id, step_id) not in STEPS:
        raise ValueError(f"Unknown mission step: {mission_id}/{step_id}")
    step = STEPS[(mission_id, step_id)]
    if step.get("verify") != "artifact":
        raise ValueError("This step is not an artifact gate.")
    target = Path(str(path or "")).expanduser()
    if not target.is_file():
        return _file_problem(
            target,
            "No file at that path",
            f"Nothing is saved at {target}. Save the document, then type where you saved it.",
            [{"label": "Looked for", "value": str(target)}],
        )
    size = target.stat().st_size
    if size > MAX_ARTIFACT_BYTES:
        return _file_problem(
            target,
            "That file is too large to check",
            (
                f"The document is {size} bytes and the limit is {MAX_ARTIFACT_BYTES}. "
                "Type the location of the document itself, saved as a text or Markdown file."
            ),
            [{"label": "File", "value": str(target)}, {"label": "Size", "value": f"{size} bytes"}],
        )
    if size == 0:
        return _file_problem(
            target, "That file is empty", "Write the document, save it, and check again.", [{"label": "File", "value": str(target)}]
        )
    raw = target.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return _file_problem(
            target,
            "That isn't a text document",
            (
                "Field Academy reads plain text to find the sections. "
                "Save the document as a text or Markdown file and type that location."
            ),
            [{"label": "File", "value": str(target)}, {"label": "Size", "value": f"{len(raw)} bytes"}],
        )
    digest = hashlib.sha256(raw).hexdigest()
    analysis = documents.analyze(text, step, _models(mission_id))
    missing = list(analysis["missing"])
    with _connection() as conn:
        reused = conn.execute(
            "SELECT mission_id FROM evidence WHERE sha256 = ? AND mission_id != ? LIMIT 1", (digest, mission_id)
        ).fetchone()
    if reused:
        missing.append({
            "id": "reused",
            "what": f"This exact file already passed {MISSIONS.get(reused['mission_id'], {}).get('title', 'another mission')}. Each mission takes its own document.",
        })
    facts = [
        {"label": "File", "value": str(target)},
        {"label": "Size", "value": f"{len(raw)} bytes, {len(text.split())} words"},
        {"label": "SHA-256", "value": digest[:16]},
        {"label": "Sections with real content", "value": f"{analysis['total'] - sum(1 for m in missing if m['id'].startswith('section:'))} of {analysis['total']}"},
    ]
    if step.get("live"):
        if not isinstance(live, dict):
            missing.append({
                "id": "live_failed",
                "what": "The part of this check that reads Hermes didn't run. Open this mission in the Field Academy page and run the check there.",
            })
        else:
            facts.extend(
                {"label": f"Hermes: {fact.get('label', '')}", "value": str(fact.get("value", ""))}
                for fact in (live.get("facts") or [])[:4]
                if isinstance(fact, dict)
            )
            if not live.get("passed"):
                missing.append({"id": "live_failed", "what": _clean(live.get("detail") or live.get("title") or "Hermes didn't answer.", 300)})
    passed = not missing
    kind = step.get("check") or "document"
    if passed:
        return {
            "passed": True,
            "title": "Your document is complete",
            "detail": (
                f"All {analysis['total']} sections have real content, and its fingerprint is saved for your Field Record. "
                f"The check looks for the parts a {kind} needs. Read it through once more to judge the writing yourself."
            ),
            "facts": facts,
            "missing": [],
            "sha256": digest,
            "bytes": len(raw),
        }
    return {
        "passed": False,
        "title": "Your document isn't finished yet",
        "detail": missing[0]["what"],
        "facts": facts,
        "missing": missing,
    }


def save_pasted_document(mission_id, step_id, text):
    """Keep a pasted document as a file in Field Academy's own folder and return its path.

    For a learner whose Hermes runs on another computer: a path they type means a path on
    that machine, so they paste the document instead. The text is saved as a file under the
    plugin's data folder and then checked exactly like a typed path, so the same rules, the
    same fingerprint and the same Field Record line apply.
    """
    if (mission_id, step_id) not in STEPS or STEPS[(mission_id, step_id)].get("verify") != "artifact":
        raise ValueError("Only a document check takes a pasted document.")
    body = str(text or "")
    if not body.strip():
        raise ValueError("Paste the whole document first.")
    raw = body.encode("utf-8")
    if len(raw) > MAX_ARTIFACT_BYTES:
        raise ValueError("That document is too large to check. Paste the document itself, as plain text.")
    digest = hashlib.sha256(raw).hexdigest()
    folder = data_dir() / "pasted"
    folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", mission_id.lower()).strip("-")
    target = folder / f"{slug}-{digest[:10]}.md"
    target.write_bytes(raw)
    return str(target)


def _gate_feedback(conn, mission_id, step, outcome):
    """Attach the hint ladder to a failed outcome and keep it."""
    missing = _safe_missing(outcome.get("missing"))
    if not missing:
        missing = [{"id": "feedback", "what": _clean(outcome.get("detail", ""), 400) or "That check didn't pass."}]
    coach = gate_coach(step)
    return _record_miss(
        conn, mission_id, step["id"], lambda count: learning.ladder(count, missing, coach)
    )


def record_gate(mission_id, step_id, outcome, session_id="", artifact=""):
    """Store a gate result and flip the step. Evidence carries the hash.

    A miss gets the hint ladder: what was missing, one hint, and on the second
    miss a worked example. A step that already passed stays passed when a later
    check misses, so re-verifying a changed check never un-passes the mission.
    """
    if (mission_id, step_id) not in STEPS:
        raise ValueError(f"Unknown mission step: {mission_id}/{step_id}")
    step = STEPS[(mission_id, step_id)]
    passed = bool(outcome.get("passed"))
    with _connection() as conn:
        before = _step_status(conn, mission_id, step_id)
        if passed:
            conn.execute(
                """INSERT INTO evidence(mission_id, step_id, kind, summary, artifact, sha256, bytes, session_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    mission_id,
                    step_id,
                    "artifact" if artifact else "check",
                    _clean(outcome.get("title", ""), 400),
                    _clean(artifact, 1000),
                    str(outcome.get("sha256", ""))[:64],
                    int(outcome.get("bytes") or 0),
                    _clean(session_id, 120),
                    _now(),
                ),
            )
            _clear_misses(conn, mission_id, step_id)
            outcome["feedback"] = None
            _upsert_step(conn, mission_id, step_id, "done", _clean(outcome.get("detail", ""), 1200))
            _after_pass(conn, mission_id, via_gate=True)
        else:
            feedback = _gate_feedback(conn, mission_id, step, outcome)
            outcome["feedback"] = feedback
            note = _clean(f"{feedback['headline']} {feedback['missing'][0]['what'] if feedback['missing'] else ''}", 1200)
            _upsert_step(conn, mission_id, step_id, "done" if before == "done" else "needs_attention", note)
        _meta_set(conn, "active_mission", mission_id)
        _meta_set(conn, "goal_track", MISSIONS[mission_id]["track"])
        _meta_set(conn, "last_gate", step_id)
    return outcome


def combine_live(outcome, live):
    """Fold a live-app result into an outcome. Used when a gate reads both a file and Hermes."""
    return outcome


def record_evidence(mission_id, summary="", artifact="", session_id="", step_id=""):
    if mission_id not in MISSIONS:
        raise ValueError(f"Unknown mission: {mission_id}")
    clean_summary = _clean(summary, 1200)
    if not clean_summary:
        raise ValueError("Evidence needs a short description.")
    with _connection() as conn:
        cursor = conn.execute(
            """INSERT INTO evidence(mission_id, step_id, kind, summary, artifact, session_id, created_at)
               VALUES (?, ?, 'note', ?, ?, ?, ?)""",
            (mission_id, step_id, clean_summary, _clean(artifact, 1000), _clean(session_id, 120), _now()),
        )
    return cursor.lastrowid


def _after_pass(conn, mission_id, via_gate=False):
    """When a pass completes a mission: record the version passed and start its review schedule."""
    if not _is_verified(conn, mission_id):
        return
    version = MISSIONS[mission_id]["version"]
    row = conn.execute("SELECT * FROM mission_versions WHERE mission_id = ?", (mission_id,)).fetchone()
    if row is None or via_gate:
        conn.execute(
            """INSERT INTO mission_versions(mission_id, passed_version, updated_at, carried_over)
               VALUES (?, ?, ?, 0)
               ON CONFLICT(mission_id) DO UPDATE SET
                 passed_version = excluded.passed_version, updated_at = excluded.updated_at, carried_over = 0""",
            (mission_id, version, _now()),
        )
        conn.execute("DELETE FROM meta WHERE key = ?", (f"reverify:{mission_id}",))
    score_row = conn.execute(
        "SELECT score FROM explanations WHERE mission_id = ? AND step_id = 'explain'", (mission_id,)
    ).fetchone()
    review.sync(
        conn,
        [{
            "mission_id": mission_id,
            "passed_at": _now(),
            "score": score_row["score"] if score_row and score_row["score"] is not None else None,
            "carried": False,
        }],
        store.clock(),
    )


# ── Half-finished examples ───────────────────────────────────────────────────


def _complete_step(mission_id, step_id):
    step = STEPS.get((mission_id, step_id))
    if step is None or step["kind"] != "complete":
        raise ValueError("That is not a half-finished example.")
    return step


def submit_completion(mission_id, step_id, answers, show_anyway=False):
    """Check the learner's gap answers, and show the model answers once they have tried.

    Trying first matters: the learner writes an answer before seeing one. Each
    gap needs its minimum number of words and, where it asks, a number or a
    name. After two attempts that still fall short the model answers are shown
    anyway, but the step stays open, because reading the answer is not the same
    as producing one.
    """
    step = _complete_step(mission_id, step_id)
    gaps = [part for part in step["parts"] if "gap" in part]
    given = {str(k): _clean_lines(str(v), 800) for k, v in (answers or {}).items()}
    problems = []
    for gap in gaps:
        text = given.get(gap["gap"], "")
        floor = int(gap.get("min_words", 3))
        count = len(documents.words(text))
        if count < floor:
            problems.append({"id": gap["gap"], "what": f"Write at least {floor} words. You have {count}."})
            continue
        stub = documents.PLACEHOLDER.search(text)
        if stub:
            problems.append({"id": gap["gap"], "what": "Replace the placeholder with your own words."})
            continue
        for kind in gap.get("needs", []):
            if not documents.has_need(kind, text):
                problems.append({"id": gap["gap"], "what": f"This answer needs {documents.need_words(kind)}."})
                break
    with _connection() as conn:
        misses = _misses(conn, mission_id, step_id)
        if problems and not (show_anyway and misses >= 2):
            conn.execute(
                """INSERT INTO attempts(mission_id, step_id, misses, last_feedback_json, updated_at)
                   VALUES (?, ?, ?, '', ?)
                   ON CONFLICT(mission_id, step_id) DO UPDATE SET misses = excluded.misses, updated_at = excluded.updated_at""",
                (mission_id, step_id, misses + 1, _now()),
            )
            conn.execute(
                """INSERT INTO completions(mission_id, step_id, answers_json, revealed, updated_at)
                   VALUES (?, ?, ?, 0, ?)
                   ON CONFLICT(mission_id, step_id) DO UPDATE SET answers_json = excluded.answers_json, updated_at = excluded.updated_at""",
                (mission_id, step_id, json.dumps(given), _now()),
            )
            return {
                "ok": False,
                "problems": problems,
                "attempts": misses + 1,
                "can_show": misses + 1 >= 2,
                "model": None,
            }
        conn.execute(
            """INSERT INTO completions(mission_id, step_id, answers_json, revealed, updated_at)
               VALUES (?, ?, ?, 1, ?)
               ON CONFLICT(mission_id, step_id) DO UPDATE SET
                 answers_json = excluded.answers_json, revealed = 1, updated_at = excluded.updated_at""",
            (mission_id, step_id, json.dumps(given), _now()),
        )
        if not problems:
            _upsert_step(conn, mission_id, step_id, "done", "")
            _clear_misses(conn, mission_id, step_id)
        _meta_set(conn, "active_mission", mission_id)
    model = {gap["gap"]: gap["answer"] for gap in gaps}
    return {"ok": not problems, "problems": problems, "attempts": 0, "can_show": False, "model": model, "yours": given}


def _completion_view(conn, mission_id, step):
    row = conn.execute(
        "SELECT * FROM completions WHERE mission_id = ? AND step_id = ?", (mission_id, step["id"])
    ).fetchone()
    if not row:
        return {"answers": {}, "revealed": False, "model": None}
    revealed = bool(row["revealed"])
    model = {part["gap"]: part["answer"] for part in STEPS[(mission_id, step["id"])]["parts"] if "gap" in part} if revealed else None
    return {"answers": json.loads(row["answers_json"] or "{}"), "revealed": revealed, "model": model}


# ── Graded explanations ──────────────────────────────────────────────────────

EXPLAIN_MIN_CHARS = 120


def _explain_step(mission_id, step_id):
    step = STEPS.get((mission_id, step_id))
    if step is None or step["kind"] != "explain":
        raise ValueError("That is not an explanation step.")
    return step


def grading_prompt(mission_id, step_id, answer):
    """The exact instruction the learner's own Hermes grades against.

    Built here rather than in the interface so the wording cannot drift between
    what the learner reads and what they are measured on.
    """
    step = _explain_step(mission_id, step_id)
    mission = MISSIONS[mission_id]
    covers = "\n".join(f"{number}. {item}" for number, item in enumerate(step["covers"], start=1))
    return (
        f"Grade a Field Academy explanation. Stay in the learner's own Hermes; do not restart the mission.\n\n"
        f"Mission: {mission['title']} ({mission_id})\n"
        f"Question asked: {step['body']}\n\n"
        f"An answer that actually understands this covers:\n{covers}\n\n"
        f"The learner's answer:\n---\n{answer}\n---\n\n"
        "Score 0-100 on substance only: did they explain the idea in their own words and hit the points above. "
        "Ignore style, length, and phrasing. An answer that restates the question or stays vague scores under 40. "
        "A correct answer missing one required point scores in the 70s. An answer that covers all of it in plain "
        f"language scores 85 or better. The threshold to pass is {step['threshold']}.\n\n"
        "Then call field_academy_grade_explanation with mission_id, step_id, score, missed and feedback. missed is the "
        "list of numbers from the points above that the answer left out, empty when it covered them all. In the "
        "feedback, do three things in this order: name what they got right, name the specific point they missed, and "
        "say what they would have to add to pass. Two or three sentences. Never offer to pass them anyway, and never "
        "grade on effort."
    )


def submit_explanation(mission_id, step_id, answer, session_id=""):
    _explain_step(mission_id, step_id)
    clean = _clean(answer, 4000)
    if len(clean) < EXPLAIN_MIN_CHARS:
        raise ValueError("That is too short to grade. Write at least two or three sentences.")
    with _connection() as conn:
        existing = conn.execute(
            "SELECT attempts, score FROM explanations WHERE mission_id = ? AND step_id = ?", (mission_id, step_id)
        ).fetchone()
        threshold = int(_explain_step(mission_id, step_id)["threshold"])
        if existing and existing["score"] is not None and int(existing["score"]) >= threshold:
            # A pass is never taken back by a later answer. Practice belongs in the review queue.
            raise ValueError("You already passed this question, and your pass stays. It comes back in your Review queue for practice.")
        attempts = (existing["attempts"] + 1) if existing else 1
        conn.execute(
            """INSERT INTO explanations(mission_id, step_id, answer, score, feedback, attempts, session_id, created_at, graded_at)
               VALUES (?, ?, ?, NULL, '', ?, ?, ?, '')
               ON CONFLICT(mission_id, step_id) DO UPDATE SET
                 answer = excluded.answer, score = NULL, feedback = '', attempts = excluded.attempts,
                 created_at = excluded.created_at, graded_at = ''""",
            (mission_id, step_id, clean, attempts, _clean(session_id, 120), _now()),
        )
        conn.execute(
            """INSERT INTO mission_steps(mission_id, step_id, status, note, updated_at)
               VALUES (?, ?, 'ready', '', ?)
               ON CONFLICT(mission_id, step_id) DO UPDATE SET status = 'ready', note = '', updated_at = excluded.updated_at""",
            (mission_id, step_id, _now()),
        )
        _meta_set(conn, "active_mission", mission_id)
    return {
        "mission_id": mission_id,
        "step_id": step_id,
        "attempts": attempts,
        "prompt": grading_prompt(mission_id, step_id, clean),
    }


def resend_explanation(mission_id, step_id):
    """The scoring request for the answer already saved, for when the first one never reached a chat."""
    _explain_step(mission_id, step_id)
    with _connection() as conn:
        row = conn.execute(
            "SELECT answer, score FROM explanations WHERE mission_id = ? AND step_id = ?", (mission_id, step_id)
        ).fetchone()
    if row is None or not row["answer"]:
        raise ValueError("Nothing has been submitted for this step yet.")
    if row["score"] is not None:
        raise ValueError("This answer already has its score.")
    return {"mission_id": mission_id, "step_id": step_id, "prompt": grading_prompt(mission_id, step_id, row["answer"])}


def grade_explanation(mission_id, step_id, score, feedback="", missed=None):
    step = _explain_step(mission_id, step_id)
    try:
        value = max(0, min(100, int(score)))
    except (TypeError, ValueError) as exc:
        raise ValueError("A score between 0 and 100 is required.") from exc
    passed = value >= int(step["threshold"])
    clean_feedback = _clean(feedback, 1500)
    covers = step.get("covers") or []
    indexes = sorted({int(n) for n in (missed or []) if str(n).isdigit() and 1 <= int(n) <= len(covers)})
    with _connection() as conn:
        row = conn.execute(
            "SELECT answer FROM explanations WHERE mission_id = ? AND step_id = ?", (mission_id, step_id)
        ).fetchone()
        if row is None:
            raise ValueError("Nothing has been submitted for this step yet.")
        ladder = None
        if passed:
            _clear_misses(conn, mission_id, step_id)
        else:
            missing = [{"id": f"point:{n}", "what": f"Missing point: {covers[n - 1]}"} for n in indexes]
            if not missing:
                missing = [{"id": "feedback", "what": clean_feedback or "The answer needs more of the points a strong answer covers."}]
            coach = {key: dict(value) for key, value in learning.GENERIC_COACH.items()}
            for number, entry in enumerate(step.get("coach") or [], start=1):
                coach[f"point:{number}"] = {"hint": entry.get("hint", ""), "example": entry.get("example", "")}
            ladder = _record_miss(conn, mission_id, step_id, lambda count: learning.ladder(count, missing, coach))
        conn.execute(
            "UPDATE explanations SET score = ?, feedback = ?, graded_at = ?, ladder_json = ? WHERE mission_id = ? AND step_id = ?",
            (value, clean_feedback, _now(), json.dumps(ladder) if ladder else "", mission_id, step_id),
        )
        _upsert_step(conn, mission_id, step_id, "done" if passed else "needs_attention", clean_feedback)
        if passed:
            conn.execute(
                """INSERT INTO evidence(mission_id, step_id, kind, summary, artifact, session_id, created_at)
                   VALUES (?, ?, 'explanation', ?, '', '', ?)""",
                (mission_id, step_id, f"Explained in own words, scored {value}", _now()),
            )
            _after_pass(conn, mission_id)
        _meta_set(conn, "goal_track", MISSIONS[mission_id]["track"])
    return {
        "passed": passed,
        "score": value,
        "threshold": int(step["threshold"]),
        "feedback": clean_feedback,
        "ladder": ladder,
        "attempts": snapshot_explanation(mission_id, step_id).get("attempts", 1),
    }


def snapshot_explanation(mission_id, step_id):
    with _connection() as conn:
        row = conn.execute(
            "SELECT * FROM explanations WHERE mission_id = ? AND step_id = ?", (mission_id, step_id)
        ).fetchone()
    return _explanation_view(row)


def _explanation_view(row):
    if not row:
        return {}
    data = dict(row)
    raw = data.pop("ladder_json", "") or ""
    try:
        data["ladder"] = json.loads(raw) if raw else None
    except ValueError:
        data["ladder"] = None
    return data


# ── Spaced review ────────────────────────────────────────────────────────────


def review_overview():
    with _connection() as conn:
        _sync_reviews(conn)
        return review.overview(conn, store.clock())


def start_review(practice=False):
    with _connection() as conn:
        _sync_reviews(conn)
        return review.start_session(conn, store.clock(), bool(practice))


def get_review_session(session_id):
    with _connection() as conn:
        return review.get_session(conn, session_id)


def submit_review(session_id, answers):
    with _connection() as conn:
        return review.submit(conn, session_id, answers, store.clock())


def grade_review(session_id, grades):
    with _connection() as conn:
        return review.grade(conn, session_id, grades, store.clock())


def _sync_reviews(conn):
    passes = []
    versions = {row["mission_id"]: dict(row) for row in conn.execute("SELECT * FROM mission_versions")}
    for mission_id in MISSIONS:
        if not _is_verified(conn, mission_id):
            continue
        evidence = conn.execute(
            "SELECT MAX(created_at) AS at FROM evidence WHERE mission_id = ? AND step_id = 'gate'", (mission_id,)
        ).fetchone()
        score = conn.execute(
            "SELECT score FROM explanations WHERE mission_id = ? AND step_id = 'explain'", (mission_id,)
        ).fetchone()
        passes.append({
            "mission_id": mission_id,
            "passed_at": (evidence["at"] if evidence and evidence["at"] else _now()),
            "score": score["score"] if score and score["score"] is not None else None,
            "carried": bool(versions.get(mission_id, {}).get("carried_over")),
        })
        if mission_id not in versions:
            conn.execute(
                "INSERT OR IGNORE INTO mission_versions(mission_id, passed_version, updated_at, carried_over) VALUES (?, ?, ?, 0)",
                (mission_id, MISSIONS[mission_id]["version"], _now()),
            )
    review.sync(conn, passes, store.clock())


# ── Placement ────────────────────────────────────────────────────────────────


def placement_questions(track_id):
    """The placement check's questions, without the answers."""
    spec = PLACEMENTS.get(track_id)
    if not spec:
        raise ValueError(f"There is no placement check for {track_id}.")
    with _connection() as conn:
        row = conn.execute("SELECT * FROM placements WHERE track_id = ?", (track_id,)).fetchone()
    return {
        "track_id": track_id,
        "title": spec["title"],
        "intro": spec["intro"],
        "minutes": int(spec.get("minutes", 5)),
        "questions": [
            {"id": q["id"], "level": q["level"], "question": q["question"], "options": list(q["options"])}
            for q in spec["questions"]
        ],
        "taken": _placement_view(row),
    }


def _placement_view(row):
    if not row:
        return None
    return {
        "taken_at": row["taken_at"],
        "results": json.loads(row["results_json"]) if row["results_json"] else None,
        "applied": json.loads(row["applied_json"]) if row["applied_json"] else None,
    }


def submit_placement(track_id, answers):
    spec = PLACEMENTS.get(track_id)
    if not spec:
        raise ValueError(f"There is no placement check for {track_id}.")
    clean = {}
    for q in spec["questions"]:
        value = (answers or {}).get(q["id"])
        if value is None or str(value) == "":
            raise ValueError("Answer every question first.")
        try:
            clean[q["id"]] = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Choose one option for each question.") from exc
    results = learning.score_placement(spec["questions"], clean, ("beginner", "intermediate", "advanced"))
    known = [level for level, outcome in results["levels"].items() if outcome["known"]]
    with _connection() as conn:
        conn.execute(
            """INSERT INTO placements(track_id, taken_at, answers_json, results_json, applied_json)
               VALUES (?, ?, ?, ?, '')
               ON CONFLICT(track_id) DO UPDATE SET
                 taken_at = excluded.taken_at, answers_json = excluded.answers_json, results_json = excluded.results_json""",
            (track_id, _now(), json.dumps(clean), json.dumps(results)),
        )
    return {"results": results, "known_levels": known, "offer": _placement_offer(track_id, known)}


def _placement_offer(track_id, known):
    missions = [m for m in TRACKS[track_id]["missions"] if m["level"] in known]
    return {
        "levels": known,
        "missions": [{"id": m["id"], "title": m["title"], "level": m["level"]} for m in missions],
        "keeps": "The question and the check on real work still count on every mission. Only the reading and practice are skipped.",
    }


def apply_placement(track_id):
    """Skip the reading and practice on the levels the placement check showed you know. Never the check."""
    if track_id not in PLACEMENTS:
        raise ValueError(f"There is no placement check for {track_id}.")
    with _connection() as conn:
        row = conn.execute("SELECT * FROM placements WHERE track_id = ?", (track_id,)).fetchone()
        if not row or not row["results_json"]:
            raise ValueError("Take the placement check first.")
        results = json.loads(row["results_json"])
        known = [level for level, outcome in results["levels"].items() if outcome["known"]]
        placed = []
        for mission in TRACKS[track_id]["missions"]:
            if mission["level"] not in known:
                continue
            for step in mission["steps"]:
                if step["kind"] not in SKIPPABLE_KINDS:
                    continue
                if _step_status(conn, mission["id"], step["id"]) in ("done", "placed"):
                    continue
                _upsert_step(conn, mission["id"], step["id"], "placed", "Skipped by the placement check")
                placed.append(f"{mission['id']}/{step['id']}")
        conn.execute(
            "UPDATE placements SET applied_json = ? WHERE track_id = ?",
            (json.dumps({"levels": known, "steps": placed, "at": _now()}), track_id),
        )
    return {"levels": known, "steps_skipped": len(placed)}


# ── Versions: what changed since you learned this ────────────────────────────


def changes():
    with _connection() as conn:
        _sync_reviews(conn)
        return _changes(conn)


def _changes(conn):
    versions = {row["mission_id"]: dict(row) for row in conn.execute("SELECT * FROM mission_versions")}
    out = []
    for track_id, track in TRACKS.items():
        for item in track["missions"]:
            mission_id = item["id"]
            if not _is_verified(conn, mission_id):
                continue
            row = versions.get(mission_id)
            passed_version = int(row["passed_version"]) if row else MISSIONS[mission_id]["version"]
            since = revisions_since(mission_id, passed_version)
            if not since:
                continue
            needs_check = any(r["kind"] == "check" for r in since)
            out.append({
                "mission_id": mission_id,
                "title": item["title"],
                "track_id": track_id,
                "track_name": track["name"],
                "level_name": item["level_name"],
                "passed_version": passed_version,
                "version": MISSIONS[mission_id]["version"],
                "needs": "check" if needs_check else "read",
                "revisions": [{"kind": r["kind"], "summary": r["summary"], "released": r["released"], "date": r["date"]} for r in since],
                "carried_over": bool(row and row["carried_over"]),
                "reverify_requested": bool(_meta_get(conn, f"reverify:{mission_id}", "")),
            })
    return out


def _new_missions(conn, tracks):
    """Missions added after you started a path: shown beside the changes, as something new to try."""
    out = []
    for track in tracks:
        started = any(m["status"] != "not_started" for m in track["missions"])
        # The day you first touched this path. A mission added before then was already there
        # when you arrived, so it is not news to you.
        first = min((str(m.get("started_at") or "")[:10] for m in track["missions"] if m.get("started_at")), default="")
        for item in track["missions"]:
            added = [r for r in REVISIONS if r["mission_id"] == item["id"] and r["kind"] == "added"]
            if added and first and added[0]["date"] < first:
                continue
            if added and started and item["status"] == "not_started":
                out.append({
                    "mission_id": item["id"],
                    "title": item["title"],
                    "track_id": track["id"],
                    "track_name": track["name"],
                    "level_name": item["level_name"],
                    "summary": added[0]["summary"],
                })
    return out


def reverify(mission_id):
    """Ask to run a mission's current check again. Leaves the mission passed whatever the check finds."""
    if mission_id not in MISSIONS:
        raise ValueError(f"Unknown mission: {mission_id}")
    with _connection() as conn:
        if not _is_verified(conn, mission_id):
            raise ValueError("Pass the mission first. Re-verifying is for missions you already passed.")
        _meta_set(conn, f"reverify:{mission_id}", _now())
        _meta_set(conn, "active_mission", mission_id)
    return mission_snapshot(mission_id)


def acknowledge_changes(mission_id):
    """Mark changes to a mission's teaching as read. A change to the check itself needs the check to run again."""
    if mission_id not in MISSIONS:
        raise ValueError(f"Unknown mission: {mission_id}")
    with _connection() as conn:
        row = conn.execute("SELECT * FROM mission_versions WHERE mission_id = ?", (mission_id,)).fetchone()
        if not row:
            raise ValueError("Pass the mission first.")
        since = revisions_since(mission_id, int(row["passed_version"]))
        if any(r["kind"] == "check" for r in since):
            raise ValueError("The check itself changed. Run the check again to re-verify this mission.")
        conn.execute(
            "UPDATE mission_versions SET passed_version = ?, updated_at = ? WHERE mission_id = ?",
            (MISSIONS[mission_id]["version"], _now(), mission_id),
        )
    return changes()


# ── Opportunity signals (never progress) ─────────────────────────────────────

# Sessions that are not a person sitting at the app. Scheduled runs carry the
# cron prefixes. Gateway session ids carry no prefix, so pre_llm_call also
# checks the turn's platform (see INTERACTIVE_PLATFORMS in __init__.py).
NON_LEARNER_PREFIXES = ("cron:", "cron_", "webhook:", "gateway:")


def is_learner_session(session_id):
    value = str(session_id or "")
    if not value:
        return False
    return not value.startswith(NON_LEARNER_PREFIXES)


def observe_tool(mission_id, tool_name, session_id=""):
    """Record one coaching opportunity per mission per session."""
    if mission_id not in MISSIONS:
        return False
    if not is_learner_session(session_id):
        return False
    clean_session = str(session_id or "")[:120]
    with _connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM opportunities WHERE mission_id = ? AND session_id = ? LIMIT 1",
            (mission_id, clean_session),
        ).fetchone()
        if exists:
            return False
        conn.execute(
            "INSERT INTO opportunities(mission_id, tool_name, session_id, created_at) VALUES (?, ?, ?, ?)",
            (mission_id, str(tool_name or "")[:100], clean_session, _now()),
        )
    return True


def claim_spotlight(session_id=""):
    """Return at most one mission to mention, and only inside a learner session.

    The watermark advances ONLY when something was actually offered. Rows newer
    than the match are consumed with it (they were examined and belong to a
    track the learner is not on), but a scan that finds no match consumes
    nothing, so switching track later can still surface those opportunities.
    Advancing unconditionally is what silently ate the matching row whenever a
    newer row for another track landed first.
    """
    if not is_learner_session(session_id):
        return None
    data = snapshot()
    with _connection() as conn:
        last_id = int(_meta_get(conn, "spotlight:last_opportunity", "0"))
        rows = conn.execute("SELECT * FROM opportunities WHERE id > ? ORDER BY id DESC", (last_id,)).fetchall()
        if not rows:
            return None
        match = next(
            (row for row in rows if MISSIONS.get(row["mission_id"], {}).get("track") == data["goal_track"]),
            None,
        )
        if not match:
            return None
        _meta_set(conn, "spotlight:last_opportunity", str(rows[0]["id"]))
    current = get_mission(match["mission_id"])
    return {"id": current["id"], "title": current["title"], "promise": current["promise"]}


# ── Snapshot ─────────────────────────────────────────────────────────────────


def _progress(mission_id, progress_rows, evidence_rows):
    steps = MISSIONS[mission_id]["steps"]
    statuses = {row["step_id"]: row for row in progress_rows if row["mission_id"] == mission_id}
    done = sum(statuses.get(item["id"], {}).get("status") in COUNTED for item in steps)
    attention = sum(statuses.get(item["id"], {}).get("status") == "needs_attention" for item in steps)
    proofs = [row for row in evidence_rows if row["mission_id"] == mission_id]
    real_proofs = [row for row in proofs if row["kind"] != "note"]
    return {
        "completed_steps": done,
        "total_steps": len(steps),
        "progress_percent": round(100 * done / len(steps)),
        "needs_attention": attention,
        "evidence_count": len(proofs),
        "status": (
            "verified" if done == len(steps) and real_proofs
            else "complete" if done == len(steps)
            else "active" if done or attention
            else "not_started"
        ),
    }


def _next_mission(tracks, goal_track):
    chosen = next(track for track in tracks if track["id"] == goal_track)
    pending = next((item for item in chosen["missions"] if item["status"] != "verified"), None)
    return (pending or chosen["missions"][0])["id"]


def purge_orphans():
    """Drop rows written by older versions whose ids no longer exist.

    0.1 and 0.2 wrote evidence against competency ids (operator.setup,
    operator.skills) that no version of this curriculum ever contained. Those
    rows render as progress the learner never made, so they are deleted rather
    than migrated.
    """
    known = set(MISSIONS)
    with _connection() as conn:
        orphan_missions = [
            row["mission_id"]
            for row in conn.execute("SELECT DISTINCT mission_id FROM evidence").fetchall()
            if row["mission_id"] not in known
        ]
        for mission_id in orphan_missions:
            conn.execute("DELETE FROM evidence WHERE mission_id = ?", (mission_id,))
        orphan_steps = [
            (row["mission_id"], row["step_id"])
            for row in conn.execute("SELECT mission_id, step_id FROM mission_steps").fetchall()
            if (row["mission_id"], row["step_id"]) not in STEPS
        ]
        for mission_id, step_id in orphan_steps:
            conn.execute(
                "DELETE FROM mission_steps WHERE mission_id = ? AND step_id = ?", (mission_id, step_id)
            )
    return {"missions": len(orphan_missions), "steps": len(orphan_steps)}


def _decorate_steps(conn, item, goal_text, progress_by_step, explanations, attempts_by_step):
    for step in item["steps"]:
        saved = progress_by_step.get((item["id"], step["id"]))
        step["status"] = saved["status"] if saved else "ready"
        step["note"] = saved["note"] if saved else ""
        if step["kind"] == "lab":
            step["prompt"] = _weave(step.get("prompt", ""), goal_text)
        if step["kind"] == "explain":
            step["explanation"] = _explanation_view(explanations.get((item["id"], step["id"])))
        if step["kind"] == "complete":
            step["saved"] = _completion_view(conn, item["id"], step)
        if step["kind"] == "gate":
            found = attempts_by_step.get((item["id"], step["id"]))
            step["misses"] = int(found["misses"]) if found else 0
            try:
                step["feedback"] = json.loads(found["last_feedback_json"]) if found and found["last_feedback_json"] else None
            except ValueError:
                step["feedback"] = None


def snapshot():
    purge_needed = False
    with _connection() as conn:
        progress_rows = [dict(r) for r in conn.execute("SELECT * FROM mission_steps")]
        evidence_rows = [dict(r) for r in conn.execute("SELECT * FROM evidence ORDER BY created_at DESC")]
        purge_needed = any(row["mission_id"] not in MISSIONS for row in evidence_rows) or any(
            (row["mission_id"], row["step_id"]) not in STEPS for row in progress_rows
        )
    if purge_needed:
        purge_orphans()
    with _connection() as conn:
        progress_rows = [dict(r) for r in conn.execute("SELECT * FROM mission_steps")]
        evidence_rows = [dict(r) for r in conn.execute("SELECT * FROM evidence ORDER BY created_at DESC")]
        explanations = {(row["mission_id"], row["step_id"]): row for row in conn.execute("SELECT * FROM explanations")}
        attempts_by_step = {(row["mission_id"], row["step_id"]): row for row in conn.execute("SELECT * FROM attempts")}
        certificates = {
            row["track_id"]: _certificate_view(row)
            for row in conn.execute("SELECT * FROM certificates")
        }
        goal_track = _meta_get(conn, "goal_track", "ambassador")
        context = _meta_get(conn, "learning_context", "")
        active_mission = _meta_get(conn, "active_mission", "")
        oriented = _meta_get(conn, "oriented", "0") == "1"
        goal = _goal(conn)
        placements = {row["track_id"]: row for row in conn.execute("SELECT * FROM placements")}
        versions = {row["mission_id"]: dict(row) for row in conn.execute("SELECT * FROM mission_versions")}
        tracks = public_tracks()
        progress_by_step = {(row["mission_id"], row["step_id"]): row for row in progress_rows}
        for track in tracks:
            for item in track["missions"]:
                item.update(_progress(item["id"], progress_rows, evidence_rows))
                _decorate_steps(conn, item, goal["text"], progress_by_step, explanations, attempts_by_step)
                item["passed_at"] = _passed_at(item["id"], item["status"], evidence_rows)
                item["use_text"] = _use_text(MISSIONS[item["id"]], goal["text"])
                item["placed"] = any(step["status"] == "placed" for step in item["steps"])
                touched = [row["updated_at"] for row in progress_rows if row["mission_id"] == item["id"]]
                item["started_at"] = min(touched) if touched else ""
            total = sum(item["total_steps"] for item in track["missions"])
            done = sum(item["completed_steps"] for item in track["missions"])
            track["completed_steps"] = done
            track["total_steps"] = total
            track["progress_percent"] = round(100 * done / total) if total else 0
            track["verified_missions"] = sum(item["status"] == "verified" for item in track["missions"])
            track["minutes"] = sum(item["minutes"] for item in track["missions"] if item["status"] != "verified")
            track["placement"] = {**track["placement"], "taken": _placement_view(placements.get(track["id"]))}
        verified_ids = [item["id"] for track in tracks for item in track["missions"] if item["status"] == "verified"]
        if verified_ids:
            _sync_reviews(conn)
        reviews = review.overview(conn, store.clock())
        change_list = _changes(conn)
        new_list = _new_missions(conn, tracks)
        for track in tracks:
            for item in track["missions"]:
                found = reviews["strength"].get(item["id"])
                item["strength"] = found["strength"] if found else None
                item["strength_word"] = found["strength_word"] if found else learning.strength_word(None)
                item["review_due_at"] = found["due_at"] if found else ""
                row = versions.get(item["id"])
                item["passed_version"] = int(row["passed_version"]) if row else (item["version"] if item["status"] == "verified" else 0)
                item["changed"] = any(c["mission_id"] == item["id"] for c in change_list)
                item["reverify"] = bool(_meta_get(conn, f"reverify:{item['id']}", ""))
    pathways.decorate(tracks, certificates)
    if active_mission not in MISSIONS or MISSIONS[active_mission]["track"] != goal_track:
        active_mission = _next_mission(tracks, goal_track)
    holding = sum(1 for found in reviews["strength"].values() if (found["strength"] or 0) >= learning.PASS_SCORE)
    return {
        "version": 5,
        "oriented": oriented,
        "goal": goal,
        "goal_track": goal_track,
        "learning_context": context,
        "active_mission": active_mission,
        "next_up": pathways.next_up(tracks, goal_track, goal["text"]),
        "tracks": tracks,
        "recent_evidence": evidence_rows[:12],
        "credential_note": pathways.ABOUT,
        "record_disclaimer": pathways.DISCLAIMER,
        "reviews": reviews,
        "changes": change_list,
        "new_missions": new_list,
        "honest": {
            "steps_done": sum(item["completed_steps"] for track in tracks for item in track["missions"]),
            "passed": len(verified_ids),
            "holding": holding,
            "fading": max(0, len(reviews["strength"]) - holding),
        },
    }


def _passed_at(mission_id, status, evidence_rows):
    """When the mission's check last passed, or "" if the mission hasn't passed."""
    if status != "verified":
        return ""
    times = [row["created_at"] for row in evidence_rows if row["mission_id"] == mission_id and row["step_id"] == "gate"]
    return max(times) if times else ""


def mission_snapshot(mission_id):
    if mission_id not in MISSIONS:
        raise ValueError(f"Unknown mission: {mission_id}")
    data = snapshot()
    item = next(m for track in data["tracks"] for m in track["missions"] if m["id"] == mission_id)
    # The agent's mission tool reads item["track"]; the passport's missions don't
    # carry it (their track is the parent), so the tool raised KeyError on every call.
    item["track"] = MISSIONS[mission_id]["track"]
    with _connection() as conn:
        evidence = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM evidence WHERE mission_id = ? ORDER BY created_at DESC", (mission_id,)
            )
        ]
    item["evidence"] = evidence
    item["sources"] = [s for s in item.get("sources", [])]
    item["goal"] = data["goal"]["text"]
    return item


# ── Compact shapes for the agent ─────────────────────────────────────────────


def compact():
    """A few hundred tokens, not forty kilobytes.

    The full curriculum is the model's to read only one mission at a time. When
    the whole thing lands in context the model parrots it back, which reads as
    an instruction manual rather than a teacher.
    """
    data = snapshot()
    active = data["active_mission"]
    mission = MISSIONS[active]
    with _connection() as conn:
        rows = conn.execute(
            "SELECT step_id, status FROM mission_steps WHERE mission_id = ?", (active,)
        ).fetchall()
    statuses = {row["step_id"]: row["status"] for row in rows}
    tracks = []
    for track in data["tracks"]:
        tracks.append(
            {
                "id": track["id"],
                "name": track["name"],
                "progress": f"{track['completed_steps']}/{track['total_steps']}",
                "verified_missions": track["verified_missions"],
                "missions": [
                    {
                        "id": item["id"],
                        "title": item["title"],
                        "status": item["status"],
                        "progress": f"{item['completed_steps']}/{item['total_steps']}",
                    }
                    for item in track["missions"]
                ],
            }
        )
    return {
        "goal_track": data["goal_track"],
        "learning_context": data["learning_context"],
        "learner_goal": data["goal"]["text"],
        "reviews_due": data["reviews"]["due_count"],
        "active_mission": {
            "id": active,
            "title": mission["title"],
            "promise": mission["promise"],
            "track": mission["track"],
            "steps": [
                {
                    "id": step["id"],
                    "kind": step["kind"],
                    "title": step["title"],
                    "status": statuses.get(step["id"], "ready"),
                }
                for step in mission["steps"]
            ],
        },
        "tracks": tracks,
        "evidence_count": len(data["recent_evidence"]),
        "note": "Call field_academy_mission for the full text of the active mission before teaching it.",
    }


def open_missions():
    data = snapshot()
    return [
        {"id": item["id"], "title": item["title"], "track": track["id"], "promise": item["promise"]}
        for track in data["tracks"]
        for item in track["missions"]
        if item["status"] != "verified"
    ]


def export_json():
    return json.dumps(snapshot(), ensure_ascii=False, indent=2)


# ── Field Records ────────────────────────────────────────────────────────────
#
# A Field Record is the learner's own learning record for one path, written on
# their computer once every mission on the path has passed. Field Academy 0.8.2
# and earlier called it a certificate, and the code, the API routes and the
# database table still use that name. Its number is the start of a SHA-256 over
# the record's own stored contents, so editing any line of a saved copy makes the
# number stop matching (verify_certificate recomputes it). It holds no chat text
# and no file contents: mission titles, pass dates, check summaries, question
# scores, and the file name and fingerprint of each document the learner wrote.
# It also says which version of each check was passed, and whether a mission's
# reading and practice were skipped by a placement check.
#
# Record formats. The number covers every stored line, the wording included, so
# a stored body is never rewritten. Format 1 (no record_format key) is what 0.8.2
# and earlier wrote; format 2 adds record_format, record and disclaimer, and words
# the issuer line as self-issued. Both verify the same way. The screen and the
# saved .md show the current wording for every format (record_display); the .json
# is always the stored body, byte for byte what the number covers.


def _canonical(body):
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def certificate_number(body):
    """FA-XXXX-XXXX-XXXX from the record's contents, without its number."""
    unsigned = {key: value for key, value in body.items() if key != "number"}
    digest = hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest()[:12].upper()
    return f"FA-{digest[0:4]}-{digest[4:8]}-{digest[8:12]}"


def verify_certificate(body):
    """True when a record's number still matches its contents."""
    return isinstance(body, dict) and body.get("number") == certificate_number(body)


def _plugin_version():
    manifest = Path(__file__).resolve().parent / "plugin.yaml"
    try:
        for line in manifest.read_text().splitlines():
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return ""


def record_format(body):
    """1 for records made by 0.8.2 and earlier, otherwise the stored record_format."""
    try:
        return int(body.get("record_format", 1)) if isinstance(body, dict) else 1
    except (TypeError, ValueError):
        return 1


def record_display(body):
    """The wording the screen and the saved .md show for a record, whatever its format.

    Format 2 and later show their own stored lines. Format 1 records stored the old
    certificate wording; they show the current lines instead, and their .json keeps
    the original text, which is what their number covers.
    """
    fmt = record_format(body)
    if body.get("path_id") == "deployer":
        from . import deployer_content as C

        shows, does_not = C.WHAT_IT_SHOWS, C.WHAT_IT_DOES_NOT
        issuer = C.ISSUER
    else:
        shows, does_not, issuer = pathways.WHAT_IT_SHOWS, None, pathways.ISSUER
    if fmt >= 2:
        shows = body.get("shows", shows)
        does_not = body.get("does_not_show", does_not)
        issuer = body.get("issuer", issuer)
    return {
        "format": fmt,
        "issuer": issuer,
        "shows": shows,
        "does_not_show": does_not,
        "disclaimer": body.get("disclaimer") if fmt >= 2 and body.get("disclaimer") else pathways.DISCLAIMER,
        "legacy": fmt < 2,
    }


def _certificate_view(row):
    body = json.loads(row["body_json"])
    return {
        "track_id": row["track_id"],
        "name": row["name"],
        "number": row["number"],
        "issued_at": row["issued_at"],
        "body": body,
        "valid": verify_certificate(body),
        "display": record_display(body),
    }


def _mission_proof(conn, mission_id):
    """What a Field Record says about one mission. File names only, never full paths."""
    evidence = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM evidence WHERE mission_id = ? AND step_id = 'gate' ORDER BY created_at DESC",
            (mission_id,),
        )
    ]
    latest = evidence[0] if evidence else {}
    explanation = conn.execute(
        "SELECT score FROM explanations WHERE mission_id = ? AND step_id = 'explain'", (mission_id,)
    ).fetchone()
    version = conn.execute(
        "SELECT passed_version FROM mission_versions WHERE mission_id = ?", (mission_id,)
    ).fetchone()
    placed = conn.execute(
        "SELECT COUNT(*) AS n FROM mission_steps WHERE mission_id = ? AND status = 'placed'", (mission_id,)
    ).fetchone()
    mission = MISSIONS[mission_id]
    gate_step = next(step for step in mission["steps"] if step["kind"] == "gate")
    proof = {
        "mission_id": mission_id,
        "title": mission["title"],
        "level": mission["level_name"],
        "passed_at": latest.get("created_at", ""),
        "check": gate_step["proof"],
        "check_result": latest.get("summary", ""),
        "check_version": int(version["passed_version"]) if version else mission["version"],
        "question_score": explanation["score"] if explanation and explanation["score"] is not None else None,
        "reading_skipped": bool(placed and placed["n"]),
    }
    if latest.get("kind") == "artifact":
        proof["document"] = Path(latest.get("artifact", "")).name
        proof["fingerprint"] = latest.get("sha256", "")
        proof["bytes"] = latest.get("bytes", 0)
    return proof


def issue_certificate(track_id, name):
    """Write the path's Field Record, once, after every mission on it has passed."""
    if track_id not in TRACKS:
        raise ValueError(f"Unknown path: {track_id}")
    clean_name = _clean(name, 80)
    data = snapshot()
    track = next(item for item in data["tracks"] if item["id"] == track_id)
    existing = track["certificate"]["issued"]
    if existing:
        return existing
    remaining = track["certificate"]["remaining"]
    if remaining:
        noun = "mission" if remaining == 1 else "missions"
        raise ValueError(f"Pass every mission on this path first. You have {remaining} {noun} to go.")
    if not clean_name:
        raise ValueError("Type the name you want on your Field Record.")
    issued_at = _now()
    with _connection() as conn:
        body = {
            "record": "Field Academy Field Record",
            "record_format": pathways.RECORD_FORMAT,
            "path_id": track_id,
            "path": track["name"],
            "path_promise": track["promise"],
            "name": clean_name,
            "issued_at": issued_at,
            "missions": [
                _mission_proof(conn, item["id"])
                for item in sorted(track["missions"], key=lambda m: pathways.LEVELS.index(m["level"]))
            ],
            "issuer": pathways.ISSUER,
            "disclaimer": pathways.DISCLAIMER,
            "shows": pathways.WHAT_IT_SHOWS,
            "plugin_version": _plugin_version(),
        }
        body["number"] = certificate_number(body)
        conn.execute(
            "INSERT OR IGNORE INTO certificates(track_id, name, number, issued_at, body_json) VALUES (?, ?, ?, ?, ?)",
            (track_id, clean_name, body["number"], issued_at, _canonical(body)),
        )
        row = conn.execute("SELECT * FROM certificates WHERE track_id = ?", (track_id,)).fetchone()
    return _certificate_view(row)


def get_certificate(track_id):
    if track_id not in TRACKS:
        raise ValueError(f"Unknown path: {track_id}")
    with _connection() as conn:
        row = conn.execute("SELECT * FROM certificates WHERE track_id = ?", (track_id,)).fetchone()
    return _certificate_view(row) if row else None


def data_dir():
    """The folder that holds Field Academy's database, for saved files."""
    import os

    override = os.environ.get("FIELD_ACADEMY_DATA_DIR")
    if override:
        return Path(override)
    with _connection() as conn:
        row = conn.execute("PRAGMA database_list").fetchone()
    return Path(row[2]).parent


def _human_date(stamp):
    try:
        moment = datetime.fromisoformat(stamp)
    except (TypeError, ValueError):
        return stamp or ""
    return f"{moment.strftime('%B')} {moment.day}, {moment.year}"


def legacy_note(display):
    """The line a format 1 record carries in its .md, or "" for current records."""
    if not display["legacy"]:
        return ""
    return (
        "This record was made with Field Academy 0.8.2 or earlier, which called it a certificate. "
        "Its .json file keeps that original wording, because the record number covers it."
    )


def certificate_markdown(certificate):
    body = certificate["body"]
    display = certificate.get("display") or record_display(body)
    lines = [
        f"# Field Record: {body['path']} path",
        "",
        display["disclaimer"],
        "",
        f"Kept by **{body['name']}**, created on {_human_date(body['issued_at'])}.",
        "",
        f"{body['path_promise']}",
        "",
        f"Record number: `{body['number']}`",
        "",
        "## The proof behind it",
        "",
        "| Level | Mission | Passed | What the check found | Check version | Question score | Document |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in body["missions"]:
        document = ""
        if item.get("document"):
            document = f"{item['document']} (SHA-256 {item.get('fingerprint', '')[:16]}…)"
        score = "" if item.get("question_score") is None else f"{item['question_score']} of 100"
        version = item.get("check_version")
        marks = []
        if version:
            marks.append(f"v{version}")
        if item.get("reading_skipped"):
            marks.append("reading skipped by placement")
        lines.append(
            f"| {item['level']} | {item['title']} | {_human_date(item['passed_at'])} | "
            f"{item.get('check_result') or item['check']} | {', '.join(marks)} | {score} | {document} |"
        )
    lines += [
        "",
        "## What this record shows",
        "",
        display["shows"],
        "",
        display["issuer"],
        "",
        display["disclaimer"],
        "",
        "The record number is the first 12 characters of a SHA-256 over this record's "
        "contents, as stored in the matching .json file. Change any line and the number stops matching.",
        "",
    ]
    note = legacy_note(display)
    if note:
        lines += [note, ""]
    return "\n".join(lines)


def save_certificate(track_id):
    """Write the Field Record as .md and .json beside the database. Returns both paths.

    Files go to field-records/. Copies saved by 0.8.2 and earlier stay where they
    were, in certificates/, untouched.
    """
    certificate = get_certificate(track_id)
    if not certificate:
        raise ValueError("Create your Field Record first.")
    folder = data_dir() / "field-records"
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"field-academy-{track_id}-field-record"
    markdown = folder / f"{stem}.md"
    payload = folder / f"{stem}.json"
    markdown.write_text(certificate_markdown(certificate), encoding="utf-8")
    payload.write_text(json.dumps(certificate["body"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"markdown": str(markdown), "json": str(payload), "number": certificate["number"]}
