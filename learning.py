"""The learning rules: spacing, strength, feedback and placement.

Pure functions. No storage, no clock of their own, no Hermes. state.py owns the
database and passes ``now`` in, which is why every rule here can be tested with
a made-up date. docs/pedagogy.md says where each rule comes from and which of
the numbers are Field Academy's own choices.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Days between a pass and the first review, then between later reviews, as a
# learner answers well. Field Academy's choice; docs/pedagogy.md says why.
INTERVALS = (2, 7, 21, 60)
GRADUATED_DAYS = 90
LAPSE_DAYS = 1
PASS_SCORE = 70
STRONG_SCORE = 85
SESSION_SIZE = 3
MINUTES_PER_QUESTION = 2

# How far a miss pulls the stage back. A lapse is not a reset to zero: the
# learner knew it once, and the gap that follows the lapse is short.
LAPSE_DROP = 2


def parse(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        value = datetime.fromisoformat(stamp)
    except (TypeError, ValueError):
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def interval_for(stage: int) -> int:
    return INTERVALS[stage] if stage < len(INTERVALS) else GRADUATED_DAYS


def first_due(passed_at: datetime) -> datetime:
    return passed_at + timedelta(days=INTERVALS[0])


def after_review(stage: int, score: int, now: datetime, *, early: bool = False) -> dict:
    """Where an item goes after one review.

    85 or more up a rung, 70 to 84 the same rung again, under 70 a lapse that
    drops two rungs and returns tomorrow. Practice done before the item was due
    changes its strength but never moves the rung, because an early answer says
    little about whether the gap held.
    """
    if early:
        return {"stage": stage, "interval_days": interval_for(stage), "outcome": "practiced", "due_shift": False}
    if score >= STRONG_SCORE:
        new = stage + 1
        return {"stage": new, "interval_days": interval_for(new), "outcome": "advanced", "due_shift": True}
    if score >= PASS_SCORE:
        return {"stage": stage, "interval_days": interval_for(stage), "outcome": "held", "due_shift": True}
    new = max(0, stage - LAPSE_DROP)
    return {"stage": new, "interval_days": LAPSE_DAYS, "outcome": "lapsed", "due_shift": True}


def new_strength(previous: int | None, score: int) -> int:
    """Strength is a running mean that leans on the latest answer: 40 percent before, 60 percent now."""
    score = max(0, min(100, int(score)))
    if previous is None:
        return score
    return round(0.4 * previous + 0.6 * score)


def current_strength(strength: int | None, due_at: str | None, interval_days: float, now: datetime) -> int | None:
    """Strength today. It holds until the review is due, then halves for every three intervals overdue.

    A model of forgetting that is Field Academy's own simplification, with a
    slow decay on purpose: a review a few days late is a nudge, and a mission
    nobody reviewed for months should stop showing as strong.
    """
    if strength is None:
        return None
    due = parse(due_at)
    if due is None or now <= due:
        return int(strength)
    overdue_days = (now - due).total_seconds() / 86400
    return round(strength * 0.5 ** (overdue_days / (3 * max(float(interval_days), 1.0))))


def strength_word(value: int | None) -> str:
    if value is None:
        return "Not reviewed yet"
    if value >= 85:
        return "Strong"
    if value >= 70:
        return "Holding"
    if value >= 40:
        return "Fading"
    return "Weak"


def pick_session(rows: list[dict], now: datetime, size: int = SESSION_SIZE, practice: bool = False) -> list[dict]:
    """Choose up to ``size`` missions to review, one question each.

    Due missions first. Among them the weakest and the longest overdue go first:
    a lapse, then how far past due as a share of its own gap, then lowest
    strength. With ``practice`` the learner asked for more than is due, so the
    pool is every mission, lowest current strength first, and the answers count
    toward strength but never move a rung.
    """
    ready = []
    for row in rows:
        due = parse(row.get("due_at"))
        overdue = 0.0
        if due and now > due:
            overdue = (now - due).total_seconds() / 86400 / max(float(row.get("interval_days") or 1), 1.0)
        is_due = bool(due) and now >= due
        ready.append({**row, "_due": is_due, "_overdue": overdue,
                      "_now": current_strength(row.get("strength"), row.get("due_at"), row.get("interval_days") or 1, now)})
    if practice:
        # Due ones still lead; the rest fill by lowest strength.
        pool = sorted(ready, key=lambda r: (not r["_due"], r["_now"] if r["_now"] is not None else 100, r["mission_id"]))
    else:
        pool = sorted(
            (r for r in ready if r["_due"]),
            key=lambda r: (0 if (r.get("lapses") or 0) > 0 else 1, -r["_overdue"], r["_now"] if r["_now"] is not None else 100, r["mission_id"]),
        )
    return [{k: v for k, v in row.items() if not k.startswith("_")} | {"early": not row["_due"]} for row in pool[:size]]


def next_variant(variants: list[str], last: str | None) -> str:
    """Rotate through a mission's question variants so the same question never comes twice in a row."""
    if not variants:
        return ""
    if last in variants:
        return variants[(variants.index(last) + 1) % len(variants)]
    return variants[0]


# --------------------------------------------------------------- feedback --


def ladder(misses: int, missing: list[dict], coach: dict[str, dict] | None = None) -> dict:
    """What to say after a miss: exactly what was missing, then a hint, then a worked-example hint.

    First miss: what was missing, plus one hint for the first thing on the list.
    Second miss and after: the same, plus a worked example for that same thing.
    One focus at a time, because a long list of fixes is easy to read and hard to act on.
    ``coach`` maps a missing item's id to {"hint": ..., "example": ...}.
    """
    coach = coach or {}
    level = 1 if misses <= 1 else 2
    items = []
    for item in missing:
        spec = coach.get(item.get("id", ""), {})
        items.append({"id": item.get("id", ""), "what": item.get("what", ""), "hint": spec.get("hint", ""), "example": spec.get("example", "")})
    focus = items[0] if items else None
    result = {
        "level": level,
        "misses": misses,
        "missing": [{"id": i["id"], "what": i["what"]} for i in items],
        "hint": focus["hint"] if focus else "",
        "example": focus["example"] if focus and level >= 2 else "",
        "focus": focus["id"] if focus else "",
        "retry": True,
    }
    if not items:
        result["headline"] = "Not there yet. Read the result above, change one thing, and check again."
    elif level == 1:
        result["headline"] = f"{len(items)} {'thing is' if len(items) == 1 else 'things are'} missing. Start with the first one, then check again."
    else:
        result["headline"] = "Still missing. Here is a finished example of the first one, then check again."
    return result


# Coaching that applies to any document, whatever the mission. A mission's own
# hint for a section or a check always wins over these.
GENERIC_COACH = {
    "file": {
        "hint": "Save the document as a plain text or Markdown file, then type its full location.",
        "example": "Example: ~/Documents/harbor-scope.md on Mac and Linux, or C:\\Users\\you\\Documents\\harbor-scope.md on Windows",
    },
    "duplicate": {
        "hint": "Give each section its own answer. Read the question each heading asks and answer only that.",
        "example": "Example: Owner names a person and what they do with the result. Acceptance gives a number. The two never share a sentence.",
    },
    "repetition": {
        "hint": "Write each section in sentences of its own, with the details of your case.",
        "example": "Example: instead of repeating \"works well,\" write \"every quote older than seven days gets a follow-up by Friday.\"",
    },
    "copied": {
        "hint": "Replace the example's case with your own: your client, your names, your numbers.",
        "example": "Example: swap Harbor Roofing for your own client and write what that client's week looks like.",
    },
    "reused": {
        "hint": "Each mission takes its own document. Write this one for this mission.",
        "example": "Example: a scope document and a handover guide answer different questions, so each needs its own file.",
    },
    "live_failed": {
        "hint": "Part of this check reads Hermes itself. Open Gateways, make sure the connection shows as open, and check again.",
        "example": "Example: after you reconnect, the connection in Gateways shows as open, and the check can read it.",
    },
    "criteria_count": {
        "hint": "Write each criterion as its own numbered line, something you could test later.",
        "example": "Example:\n1. The weekly report arrives by 8 am on Monday.\n2. It lists every open order older than seven days.\n3. I spend under ten minutes reading it.",
    },
    "criteria_thin": {
        "hint": "Say what you would see when the criterion is met, in a full sentence.",
        "example": "Example: \"The report arrives by 8 am on Monday\" describes something you can see. \"Report on time\" leaves you guessing.",
    },
    "criteria_measurable": {
        "hint": "Add a number or an amount of time to at least two criteria.",
        "example": "Example: \"arrives by 8 am\" and \"under ten minutes to read\" can both be counted.",
    },
    "evidence_count": {
        "hint": "Write one numbered line of evidence for each criterion, in the same order.",
        "example": "Example: \"1. Met. The report arrived at 7:52 am on all four Mondays.\"",
    },
    "evidence_verdict": {
        "hint": "End each evidence line with met, partly met or not met.",
        "example": "Example: \"2. It listed 9 of the 11 open orders. Partly met.\"",
    },
    "feedback": {
        "hint": "Reread the points a strong answer covers and add the one you left out.",
        "example": "",
    },
}


# -------------------------------------------------------------- placement --


def score_placement(questions: list[dict], answers: dict[str, int], levels: tuple[str, ...]) -> dict:
    """Mark a placement check. A level counts as known only when every question on it is right.

    Two questions a level keeps it honest: one lucky guess is not enough, and an
    experienced learner who knows a level answers both.
    """
    per_level: dict[str, dict] = {level: {"right": 0, "total": 0} for level in levels}
    detail = []
    for q in questions:
        chosen = answers.get(q["id"])
        right = chosen is not None and int(chosen) == int(q["answer"])
        bucket = per_level.setdefault(q["level"], {"right": 0, "total": 0})
        bucket["total"] += 1
        bucket["right"] += 1 if right else 0
        detail.append({
            "id": q["id"],
            "level": q["level"],
            "right": right,
            "chosen": chosen,
            "answer": q["answer"],
            "why": q.get("why", ""),
        })
    results = {
        level: {**counts, "known": counts["total"] > 0 and counts["right"] == counts["total"]}
        for level, counts in per_level.items()
        if counts["total"]
    }
    return {"levels": results, "questions": detail}
