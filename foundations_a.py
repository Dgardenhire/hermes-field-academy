"""Engine pieces for Foundations missions 1, 2, 4, 5 and 6 (0.9 M6, part A): their notes, their page data.

* ``validate``: a mission may declare ``lab.note_fields_a``, the fields of its try note and of its lab notes (first and
  transfer). foundations.save_entry asks here first; ``None`` means "not mine", and the memory mission's own rules run.
  The freeze rules are the same: these notes come after the lab opens.
* ``page``: what the mission page needs beyond the mission itself, read on this side so the page never sees a planted
  problem: request cards with the practice folder's full path, the paths to copy, the hello chats' first trips, the
  practice profile's skills as Hermes's index shows them, and the snapshot of skills taken when Your turn opens.
"""

from __future__ import annotations

import json
from pathlib import Path

PLANT_TITLES = {
    "output_locked": "The output file was an old, locked copy",
    "input_empty": "One input sheet was empty",
    "rows_short": "The sheets held fewer jobs than the request said",
    "extra_connector": "A connector the job never used was switched on",
    "unused_skills": "Skills for work this profile never does were switched on",
    "soul_wrong_profile": "A second practice profile sat beside the first",
    "steps_in_memory": "A job's steps were saved in memory",
    "greedy_neighbor": "A catch-all skill matched almost any request",
    "cloned_memory": "academy-practice-b was cloned from academy-practice",
    "decoy_in_b": "Another client's fact was saved in academy-practice-b",
}
KINDS = ("text", "textarea", "lines", "int", "bool", "choice")


def _fields(mission, which) -> list:
    return list(((mission.get("lab") or {}).get("note_fields_a") or {}).get(which) or [])


def _clean(field, value, mission):
    label = field.get("label", field["id"])
    kind = field.get("kind", "text")
    required = field.get("required", True)
    if value in (None, "") or (isinstance(value, list) and not value):
        if required:
            raise ValueError(f"{label}: this is needed.")
        return None
    if kind == "bool":
        if not isinstance(value, bool):
            raise ValueError(f"{label}: choose one.")
        return value
    if kind == "int":
        try:
            number = int(str(value).replace(",", "").strip())
        except ValueError:
            raise ValueError(f"{label}: a whole number.") from None
        if not field.get("min", 0) <= number <= field.get("max", 10_000_000):
            raise ValueError(f"{label}: between {field.get('min', 0)} and {field.get('max', 10_000_000)}.")
        return number
    if kind == "choice":
        ids = [c["id"] for c in field.get("choices") or (mission.get("lab") or {}).get(field.get("choices_from", ""), [])]
        if value not in ids:
            raise ValueError(f"{label}: pick one of the choices.")
        return value
    text = "\n".join(str(v) for v in value) if isinstance(value, list) else str(value)
    text = text.strip() if kind in ("textarea", "lines") else " ".join(text.split())
    if len(text) < field.get("min", 1):
        raise ValueError(f"{label} is too short.")
    if len(text) > field.get("max", 2000):
        raise ValueError(f"{label} is too long.")
    if kind == "lines":
        lines = [ln.strip(" -*\t") for ln in text.splitlines() if ln.strip(" -*\t")]
        if len(lines) < field.get("min_lines", 1):
            raise ValueError(f"{label}: one per line, at least {field.get('min_lines', 1)}.")
        return lines[:60]
    return text


def validate(conn, attempt, mission, kind, body):
    """The clean note for a mission that declares ``lab.note_fields_a``; None when the mission doesn't."""
    if kind not in ("lab_note", "try_note"):
        return None
    which = "try" if kind == "try_note" else ("transfer" if body.get("for") == "transfer" else "first")
    fields = _fields(mission, which)
    if not fields:
        return None
    if not attempt["frozen_at"]:
        raise ValueError("That comes after the lab opens.")
    out = {} if kind == "try_note" else {"for": which}
    for field in fields:
        value = _clean(field, body.get(field["id"]), mission)
        if value is not None:
            out[field["id"]] = value
    rules = {r["id"]: r for r in (mission.get("lab") or {}).get("rules_a") or []}
    if out.get("rule") in rules:
        out["rule_text"] = rules[out["rule"]]["text"]
    # The memory readers, reused by mission 4's transfer, look for ``fact`` and ``key_term``.
    if "fact" in out and not out.get("key_term"):
        out["key_term"] = ""
    return out


# ------------------------------------------------------------------- page data --


def _attempt(attempt_id) -> dict:
    from . import foundations

    with foundations._conn() as conn:
        return foundations._attempt(conn, attempt_id)


def _planted(attempt) -> tuple:
    from . import practice

    name = attempt.get("profile") or ""
    row = practice.record(name) if name else None
    if not row or row["status"] not in ("ready", "planted"):
        return None, {}
    practice.require_ours(row)  # second review, C4: nothing is read from a folder Field Academy didn't make
    return row, practice.planted(name)


def skills_snapshot(token: str) -> list:
    from . import store

    if not token:
        return []
    conn = store.connect()
    try:
        return json.loads(store.meta_get(conn, f"fa_a_skills:{token}", "[]") or "[]")
    except ValueError:
        return []
    finally:
        conn.close()


def _take_snapshot(token: str, home) -> list:
    """The skills present when Your turn opens, kept once: they can't satisfy the checks (the try's skill among them)."""
    from . import hermes_read, store

    if not token:
        raise ValueError("Set up practice first.")
    conn = store.connect()
    try:
        have = store.meta_get(conn, f"fa_a_skills:{token}", "")
        if have:
            return json.loads(have)
        names = sorted(s["name"] for s in hermes_read.skills(home).get("skills", []))
        store.meta_set(conn, f"fa_a_skills:{token}", json.dumps(names))
        conn.commit()
        return names
    finally:
        conn.close()


def _skills_view(home) -> list:
    """The practice profile's skills as Hermes's index shows them, and who made each (skills/.usage.json)."""
    from . import foundations_checks_a, hermes_read, hermes_read_a

    usage = hermes_read_a.skill_usage(home)
    out = []
    for s in hermes_read.skills(home).get("skills", []):
        made = (usage.get(s["name"]) or {}).get("created_by")
        out.append({"name": s["name"], "description": s["description"], "seen": foundations_checks_a.seen_line(s["description"]),
                    "chars": len(" ".join(str(s["description"]).split())), "cut": len(" ".join(str(s["description"]).split())) > 60,
                    "made_by": "Field Academy wrote it by hand" if s["name"].startswith("academy-") else
                    {"agent": "Hermes's background review saved it (a Self-improvement review)", "learn": "Hermes saved it when you asked in a chat",
                     "installed": "installed from the hub"}.get(made, "made outside a chat, or Hermes didn't say"),
                    "from_review": made == "agent"})
    return out


def _first_trips(home) -> list:
    from . import foundations_checks_a, hermes_read_a

    out = []
    for s in foundations_checks_a._single_word_chats(home):
        trip = hermes_read_a.first_trip(home, s)
        out.append({"title": s.get("title") or "", "started_at": s.get("started_at"), "tokens": trip.get("tokens"),
                    "how": trip.get("how") or trip.get("why", ""), "cost": s.get("estimated_cost_usd"), "cost_status": s.get("cost_status") or ""})
    return out


def _shown(path):
    from . import practice

    return practice.shown_path(path)


def page(attempt_id, what: str, body=None) -> dict:
    """Mission page data for an attempt, never a planted kind. ``what``: info, first_trips, skills, snapshot."""
    from . import foundations_content, plants_a

    attempt = _attempt(attempt_id)
    mission = foundations_content.get(attempt["mission_id"])
    row, planted = _planted(attempt)
    home = Path(row["path"]) if row else None
    if what == "info":
        out = {"mission": attempt["mission_id"], "ready": bool(row and row["status"] == "planted"), "paths": [], "cards": []}
        if attempt["mission_id"] == "f.loop":
            base = plants_a.base_for(planted, "f.loop")
            if base:
                out["paths"] = [{"label": "The warm-up folder", "path": base["warm_path"], "shown": _shown(base["warm_path"])}]
                out["cards"] = [{"label": "Your turn", "text": plants_a.card_m1(base)},
                                {"label": "Do it again, differently", "text": plants_a.card_m1_transfer(base)}]
                out["warm_prompt"] = f"Read the files in {base['warm_path']} and tell me which one mentions the most dates."
        elif attempt["mission_id"] == "f.cost":
            base = plants_a.base_for(planted, "f.cost")
            if base:
                out["cards"] = [{"label": "The job", "text": plants_a.card_m2(base)}]
                out["paths"] = [{"label": "The job's folder", "path": base["job_path"], "shown": _shown(base["job_path"])}]
        elif attempt["mission_id"] == "f.profiles":
            base = plants_a.base_for(planted, "f.profiles")
            if base:
                out["paths"] = [{"label": "The notes file", "path": base["hollis"], "shown": _shown(base["hollis"]), "file": True}]
                out["profiles"] = [{"which": "a", "name": base["a"], "button": "Open practice chat A"},
                                   {"which": "b", "name": base["b"], "button": "Open practice chat B"}]
        elif attempt["mission_id"] == "f.new-chats":
            out["rules"] = (mission.get("lab") or {}).get("rules_a", [])
        elif attempt["mission_id"] == "f.skills":
            out["lists"] = (mission.get("lab") or {}).get("try_lists_a", [])
            out["snapshot_taken"] = bool(skills_snapshot(plants_a.base_for(planted, "f.skills").get("token", "")))
        return out
    if home is None:
        raise ValueError("Set up practice first.")
    if what == "first_trips":
        return {"chats": _first_trips(home), "checked_by": "Field Academy read it"}
    if what == "skills":
        return {"skills": _skills_view(home), "checked_by": "Field Academy read it"}
    if what == "snapshot":
        token = plants_a.base_for(planted, "f.skills").get("token", "")
        return {"skills_before": _take_snapshot(token, home)}
    raise ValueError("Unknown page data.")
