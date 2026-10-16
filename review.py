"""Spaced review: the queue, a three-question session, and how results move the schedule.

Database-level functions that state.py calls. The rules (intervals, strength,
which missions to pick) are in learning.py and are pure; this file reads and
writes the ``reviews`` and ``review_sessions`` tables around them.

One row per passed mission. A mission comes due two days after it passes; a
session asks one question from each of up to three due missions, rotating among
the mission's three review questions. The learner's answers are scored by their
own Hermes, the same way an explanation is, through
``field_academy_grade_review``. Nothing here counts days of use or rewards a run
of them: a mission comes back when its schedule says so and not before.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta

from . import learning, store
from .curriculum import MISSIONS

MIN_ANSWER_CHARS = 40
SESSION_RESUME_HOURS = 24


def _clean(text, limit):
    return " ".join((text or "").split())[:limit]


def _has_bank(mission_id):
    return len(MISSIONS.get(mission_id, {}).get("review") or []) >= 1


def sync(conn, passes, now: datetime) -> int:
    """Give every passed mission a review row it doesn't have yet.

    ``passes`` is a list of {"mission_id", "passed_at", "score", "carried"}.
    A pass made under 0.5 comes due two days after it. A pass carried over from
    0.4.0 would otherwise all be overdue at once, so those are spread three a
    day, which is one session a day.
    """
    have = {row["mission_id"] for row in conn.execute("SELECT mission_id FROM reviews")}
    fresh = [p for p in passes if p["mission_id"] not in have and _has_bank(p["mission_id"])]
    carried = sorted((p for p in fresh if p.get("carried")), key=lambda p: (p.get("passed_at") or "", p["mission_id"]))
    made = 0
    for index, item in enumerate(carried):
        _insert(conn, item, now + timedelta(days=index // learning.SESSION_SIZE), now)
        made += 1
    for item in fresh:
        if item.get("carried"):
            continue
        passed = learning.parse(item.get("passed_at")) or now
        _insert(conn, item, learning.first_due(passed), now)
        made += 1
    return made


def _insert(conn, item, due: datetime, now: datetime) -> None:
    score = item.get("score")
    conn.execute(
        """INSERT OR IGNORE INTO reviews(mission_id, stage, interval_days, due_at, strength, created_at)
           VALUES (?, 0, ?, ?, ?, ?)""",
        (item["mission_id"], learning.INTERVALS[0], due.isoformat(), int(score) if score is not None else 70, now.isoformat()),
    )


def rows(conn) -> list[dict]:
    return [dict(row) for row in conn.execute("SELECT * FROM reviews ORDER BY mission_id")]


def _titled(row, now):
    mission = MISSIONS[row["mission_id"]]
    current = learning.current_strength(row["strength"], row["due_at"], row["interval_days"], now)
    return {
        "mission_id": row["mission_id"],
        "title": mission["title"],
        "track_id": mission["track"],
        "due_at": row["due_at"],
        "stage": row["stage"],
        "strength": current,
        "strength_word": learning.strength_word(current),
        "lapses": row["lapses"],
        "reps": row["reps"],
    }


def overview(conn, now: datetime) -> dict:
    """What the Review queue on the home screen shows."""
    all_rows = [r for r in rows(conn) if r["mission_id"] in MISSIONS]
    picked = learning.pick_session(all_rows, now, size=len(all_rows) or 1)
    due = [_titled(r, now) for r in picked]
    future = sorted((r for r in all_rows if (learning.parse(r["due_at"]) or now) > now), key=lambda r: r["due_at"])
    open_session = conn.execute(
        "SELECT * FROM review_sessions WHERE status IN ('open','submitted') ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    last_graded = conn.execute(
        "SELECT * FROM review_sessions WHERE status = 'graded' ORDER BY graded_at DESC LIMIT 1"
    ).fetchone()
    strength = {r["mission_id"]: _titled(r, now) for r in all_rows}
    size = min(learning.SESSION_SIZE, len(due))
    return {
        "now": now.isoformat(),
        "passed_missions": len(all_rows),
        "due_count": len(due),
        "due": due,
        "next_due_at": future[0]["due_at"] if future else "",
        "next_due_title": MISSIONS[future[0]["mission_id"]]["title"] if future else "",
        "session_size": learning.SESSION_SIZE,
        "minutes": max(0, size * learning.MINUTES_PER_QUESTION),
        "can_practice": len(all_rows) > 0,
        "strength": strength,
        "open_session": _session_view(open_session) if open_session else None,
        "last_session": _session_view(last_graded) if last_graded else None,
    }


# ---------------------------------------------------------------- session --


def _item_for(row, title, last):
    bank = MISSIONS[row["mission_id"]]["review"]
    ids = [entry["id"] for entry in bank]
    chosen = learning.next_variant(ids, last)
    entry = next(e for e in bank if e["id"] == chosen)
    return {
        "mission_id": row["mission_id"],
        "title": title,
        "item_id": entry["id"],
        "question": entry["question"],
        "early": bool(row.get("early")),
    }


def _session_view(row) -> dict:
    items = json.loads(row["items_json"])
    answers = json.loads(row["answers_json"] or "{}")
    results = json.loads(row["results_json"]) if row["results_json"] else None
    return {
        "id": row["id"],
        "status": row["status"],
        "practice": bool(row["practice"]),
        "created_at": row["created_at"],
        "submitted_at": row["submitted_at"],
        "graded_at": row["graded_at"],
        "items": items,
        "answers": answers,
        "results": results,
    }


def get_session(conn, session_id) -> dict:
    row = conn.execute("SELECT * FROM review_sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise ValueError("That review session does not exist.")
    return _session_view(row)


def start_session(conn, now: datetime, practice: bool = False) -> dict:
    """Open a session, or pick the unfinished one back up if it is under a day old."""
    existing = conn.execute(
        "SELECT * FROM review_sessions WHERE status IN ('open','submitted') ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if existing:
        started = learning.parse(existing["created_at"]) or now
        if now - started < timedelta(hours=SESSION_RESUME_HOURS):
            return _session_view(existing)
        conn.execute("UPDATE review_sessions SET status = 'abandoned' WHERE id = ?", (existing["id"],))
    all_rows = [r for r in rows(conn) if r["mission_id"] in MISSIONS]
    chosen = learning.pick_session(all_rows, now, practice=practice)
    if not chosen:
        raise ValueError(_nothing_due(conn, now))
    items = [_item_for(row, MISSIONS[row["mission_id"]]["title"], row.get("last_item")) for row in chosen]
    session_id = uuid.uuid4().hex[:12]
    conn.execute(
        "INSERT INTO review_sessions(id, created_at, practice, status, items_json) VALUES (?, ?, ?, 'open', ?)",
        (session_id, now.isoformat(), 1 if practice else 0, json.dumps(items)),
    )
    return get_session(conn, session_id)


def _nothing_due(conn, now):
    future = sorted((r for r in rows(conn)), key=lambda r: r["due_at"])
    future = [r for r in future if (learning.parse(r["due_at"]) or now) > now]
    if not future:
        return "Nothing to review yet. A mission comes up for review two days after you pass it."
    when = learning.parse(future[0]["due_at"])
    days = max(1, round((when - now).total_seconds() / 86400)) if when else 1
    return f"Nothing is due. {MISSIONS[future[0]['mission_id']]['title']} is next, in about {days} {'day' if days == 1 else 'days'}. You can practice early if you want to."


def submit(conn, session_id, answers: dict, now: datetime) -> dict:
    session = get_session(conn, session_id)
    if session["status"] == "graded":
        raise ValueError("That review is already scored.")
    if session["status"] == "abandoned":
        raise ValueError("That review expired. Start a new one.")
    clean = {}
    for item in session["items"]:
        text = _clean((answers or {}).get(item["mission_id"], ""), 3000)
        if len(text) < MIN_ANSWER_CHARS:
            raise ValueError(f"Write at least a sentence for: {item['title']}.")
        clean[item["mission_id"]] = text
    conn.execute(
        "UPDATE review_sessions SET status = 'submitted', answers_json = ?, submitted_at = ? WHERE id = ?",
        (json.dumps(clean), now.isoformat(), session_id),
    )
    return {"session_id": session_id, "prompt": grading_prompt(session, clean)}


def _entry(mission_id, item_id):
    return next(e for e in MISSIONS[mission_id]["review"] if e["id"] == item_id)


def grading_prompt(session, answers) -> str:
    blocks = []
    for number, item in enumerate(session["items"], start=1):
        entry = _entry(item["mission_id"], item["item_id"])
        points = "\n".join(f"  {i}. {p['point']}" for i, p in enumerate(entry["points"], start=1))
        blocks.append(
            f"Question {number} of {len(session['items'])}. Mission: {item['title']} ({item['mission_id']})\n"
            f"Question asked: {item['question']}\n"
            f"A strong answer covers:\n{points}\n"
            f"The learner's answer:\n---\n{answers[item['mission_id']]}\n---"
        )
    joined = "\n\n".join(blocks)
    return (
        "Grade a Field Academy review. Stay in the learner's own Hermes; do not restart any mission.\n\n"
        f"{joined}\n\n"
        "Score each answer 0-100 on substance only: did they use the idea on this case and hit the points above. "
        "Ignore style and length. An answer that restates the question or stays vague scores under 40. "
        f"The threshold to pass is {learning.PASS_SCORE}.\n\n"
        f'Then call field_academy_grade_review once, with session_id "{session["id"]}" and a grades list holding one entry '
        "per question: mission_id, score, missed (the numbers of the points they left out, empty if none) and feedback "
        "(two sentences: what they got right, then the specific point they missed). Never offer to pass anyone anyway, "
        "and never grade on effort."
    )


def grade(conn, session_id, grades: list, now: datetime) -> dict:
    session = get_session(conn, session_id)
    if session["status"] == "graded":
        raise ValueError("That review is already scored.")
    if session["status"] != "submitted":
        raise ValueError("Nothing has been submitted for this review yet.")
    by_mission = {str(g.get("mission_id")): g for g in grades or [] if isinstance(g, dict)}
    results = []
    for item in session["items"]:
        given = by_mission.get(item["mission_id"])
        if given is None:
            raise ValueError(f"Add a grade for {item['mission_id']}.")
        try:
            score = max(0, min(100, int(given.get("score"))))
        except (TypeError, ValueError) as exc:
            raise ValueError("Every grade needs a score between 0 and 100.") from exc
        entry = _entry(item["mission_id"], item["item_id"])
        points = entry["points"]
        missed = sorted({int(n) for n in (given.get("missed") or []) if str(n).isdigit() and 1 <= int(n) <= len(points)})
        row = dict(conn.execute("SELECT * FROM reviews WHERE mission_id = ?", (item["mission_id"],)).fetchone())
        early = bool(item.get("early"))
        step = learning.after_review(row["stage"], score, now, early=early)
        passed = score >= learning.PASS_SCORE
        misses = 0 if passed else (row["consecutive_misses"] or 0) + 1
        strength = learning.new_strength(row["strength"], score)
        if step["due_shift"]:
            due = (now + timedelta(days=step["interval_days"])).isoformat()
        else:
            due = row["due_at"]
        conn.execute(
            """UPDATE reviews SET stage = ?, interval_days = ?, due_at = ?, strength = ?, reps = reps + 1,
                 lapses = lapses + ?, consecutive_misses = ?, last_item = ?, last_score = ?, last_reviewed_at = ?
               WHERE mission_id = ?""",
            (
                step["stage"], step["interval_days"], due, strength,
                1 if step["outcome"] == "lapsed" else 0,
                row["consecutive_misses"] if early else misses,
                item["item_id"], score, now.isoformat(), item["mission_id"],
            ),
        )
        coach = {f"point:{i}": {"hint": p.get("hint", ""), "example": p.get("example", "")} for i, p in enumerate(points, start=1)}
        missing = [{"id": f"point:{i}", "what": f"Missing point: {points[i - 1]['point']}"} for i in missed]
        if not passed and not missing:
            note = _clean(given.get("feedback"), 600)
            missing = [{"id": "feedback", "what": note or "The answer needs more of the points a strong answer covers."}]
        ladder = learning.ladder(misses, missing, coach) if not passed else None
        results.append({
            "mission_id": item["mission_id"],
            "title": item["title"],
            "item_id": item["item_id"],
            "score": score,
            "passed": passed,
            "outcome": step["outcome"],
            "early": early,
            "stage": step["stage"],
            "interval_days": step["interval_days"],
            "next_due_at": due,
            "strength": strength,
            "strength_word": learning.strength_word(strength),
            "feedback": _clean(given.get("feedback"), 600),
            "ladder": ladder,
        })
    conn.execute(
        "UPDATE review_sessions SET status = 'graded', results_json = ?, graded_at = ? WHERE id = ?",
        (json.dumps(results), now.isoformat(), session_id),
    )
    return {"session_id": session_id, "results": results}
