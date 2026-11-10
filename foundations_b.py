"""The mission loop's additions for Foundations missions 7 to 11, kept apart from foundations.py.

* Lab notes by field. A mission names its note's fields in ``lab.note_fields``; ``clean_note`` checks them. Mission 3's
  fact-and-key-word note stays in foundations.py.
* Practice setup per mission: ``lab.setup`` (plants.SETUPS) and ``lab.folder`` (chats work in the practice folder).
* Mission 10's second round: after the first check, Reset plants the other break (``lab.transfer_swap``).
* Mission 11's draw (``lab.pick == "review"``): one problem from what every chat carries and one from what Hermes may
  do unwatched, never one the learner already met at a Compare step, never two connector problems together, picked
  by the learner's seed. A group with nothing left gives back the kind met longest ago, and the record says so.
* Mission 11's Start snapshot: memory lines, skills and waiting saves, after the plants and before the first chat.
* Mission 8's two-run notice, and the waits that never count toward the record's hours.
* The connector settings text (mission 7) and the practice profile's logs folder and terminal commands (mission 10).
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

from . import foundations_checks_b, hermes_read_b, plants, plants_b, practice, scrub

KINDS = ("text", "long", "choice", "number")

# Mission 11's plant pool (missions/11-review.md, build notes). Kinds from missions 1 to 6 join when their planters
# are registered; only registered kinds are ever drawn.
# Missions 2, 5 and 6's ids from the part-A branch: extra_connector (M2's unused connector), steps_in_memory and
# greedy_neighbor (M5). M2's extra toolsets and M6's client fact have no standalone planter yet, so they aren't drawn.
REVIEW_A = ("write_approval", "memory_full", "extra_connector", "steps_in_memory", "greedy_neighbor")
REVIEW_B = ("twin_connector", "always_allow", "approvals_off", "broken_connector")
CONNECTOR_KINDS = frozenset({"twin_connector", "broken_connector", "extra_connector"})


# --------------------------------------------------------------- lab notes --


def _clean_fields(fields, body: dict, out: dict) -> dict:
    """Each field's value from ``body``, checked by its kind, added to ``out``; required ones must be there."""
    for field in fields:
        fid, label = field["id"], field.get("label", field["id"])
        raw = body.get(fid)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            if field.get("required"):
                raise ValueError(f"{label}: this one is needed.")
            continue
        kind = field.get("kind", "text")
        if kind == "choice":
            values = [c["value"] for c in field.get("choices") or []]
            if raw not in values:
                raise ValueError(f"{label}: pick one of the choices.")
            out[fid] = raw
        elif kind == "number":
            try:
                number = int(str(raw).strip())
            except ValueError:
                raise ValueError(f"{label}: a whole number.") from None
            if not 0 <= number <= 100000:
                raise ValueError(f"{label}: a whole number.")
            out[fid] = number
        else:
            text = str(raw).strip() if kind == "long" else " ".join(str(raw).split())
            limit = int(field.get("max", 4000 if kind == "long" else 300))
            if len(text) > limit:
                raise ValueError(f"{label}: at most {limit} characters.")
            if len(text) < int(field.get("min", 1)):
                raise ValueError(f"{label}: a little more, please.")
            out[fid] = text
    return out


def clean_note(mission: dict, body: dict) -> dict:
    """A lab note checked against the mission's ``lab.note_fields``. ``for`` is ``first`` or ``transfer``; only that
    phase's fields are kept, and its required ones must be there."""
    fields = (mission.get("lab") or {}).get("note_fields") or []
    phase = "transfer" if body.get("for") == "transfer" else "first"
    return _clean_fields([f for f in fields if f.get("for", "first") == phase], body, {"for": phase})


def clean_try(mission: dict, body: dict) -> dict:
    """The try note of a mission that declares ``lab.try_fields`` (0.9 persona test): what the learner counted and guessed in the
    Practice step, in that mission's own fields. Nothing else is kept."""
    return _clean_fields((mission.get("lab") or {}).get("try_fields") or [], body, {})


def try_lines(mission: dict, body) -> list:
    """The try note in words, one ``{label, value}`` per answered field, in the mission's own labels and choice
    labels, for the record entry and its preview. Every mission's try reads in its own terms (0.9 persona test)."""
    if not isinstance(body, dict) or not body:
        return []
    lab = mission.get("lab") or {}
    if lab.get("try_fields"):
        fields = lab["try_fields"]
    elif (lab.get("note_fields_a") or {}).get("try"):
        fields = [dict(f, choices=[{"value": c.get("id"), "label": c.get("label") or c.get("text")} for c in
                                   (f.get("choices") or lab.get(f.get("choices_from", ""), []))]) for f in lab["note_fields_a"]["try"]]
    elif lab.get("note_fields"):
        return []
    else:  # the memory mission's guess and Memory number
        out = [{"label": "Your guess: how much Hermes carries", "value": str(body.get("guess") or "")}] if body.get("guess") else []
        if body.get("memory_tokens") is not None:
            out.append({"label": "Your Memory line", "value": f"{body['memory_tokens']} tokens"})
        return out
    out = []
    for field in fields:
        if field["id"] not in body:
            continue
        value = body[field["id"]]
        if field.get("kind") in ("choice",):
            value = next((c.get("label") or c.get("value") for c in field.get("choices") or [] if c.get("value") == value), value)
        elif field.get("kind") == "bool" or isinstance(value, bool):
            value = "Yes" if value else "No"
        elif isinstance(value, list):
            value = "; ".join(str(v) for v in value)
        out.append({"label": str(field.get("label") or field["id"]), "value": str(value)})
    return out


# ------------------------------------------------------------------- draws --


def met_kinds(conn) -> list:
    """Planted kinds the learner has seen revealed at a Compare step (the first check ran), oldest first."""
    out = []
    for row in conn.execute("SELECT id, plants_json FROM f_attempts ORDER BY id"):
        ran = conn.execute("SELECT 1 FROM f_checks WHERE attempt_id = ? AND phase = 'first' AND source = 'practice_profile' LIMIT 1",
                           (row["id"],)).fetchone()
        if ran:
            out.extend(json.loads(row["plants_json"] or "[]"))
    return out


def review_pick(met, seed: str, registered=None) -> list:
    """Two kinds: one from each group, by the rule in missions/11-review.md."""
    registered = set(registered if registered is not None else plants.REGISTRY)
    rng = random.Random(f"field-academy-foundations-review:{seed}")

    def choose(group, exclude=()):
        live = [k for k in group if k in registered and k not in exclude]
        fresh = [k for k in live if k not in met]
        if fresh:
            return rng.choice(sorted(fresh))
        seen = [k for k in met if k in live]
        return seen[0] if seen else None

    second = choose(REVIEW_B)
    first = choose(REVIEW_A, exclude=CONNECTOR_KINDS if second in CONNECTOR_KINDS else ())
    return [k for k in (first, second) if k]


def draw(mission: dict, conn, seed: str):
    """The kinds an attempt plants, when the mission has its own rule. None means the usual draw."""
    if (mission.get("lab") or {}).get("pick") == "review":
        return review_pick(met_kinds(conn), seed)
    return None


def seen_before(conn, kinds) -> list:
    """Kinds in this draw the learner had already met: mission 11's record says "a kind seen before"."""
    met = met_kinds(conn)
    return [k for k in kinds if k in met]


def plant_kwargs(mission: dict, attempt: dict, first_ran: bool) -> dict:
    """What foundations.plant_lab passes to practice.plant_for_attempt for this mission."""
    lab = mission.get("lab") or {}
    out = {"setup": lab.get("setup"), "folder": bool(lab.get("folder"))}
    if lab.get("transfer_swap") and first_ran:
        drawn = json.loads(attempt.get("plants_json") or "[]")
        others = [k for k in lab.get("plants", []) if k not in drawn]
        if others:
            out["kinds"] = others[:1]
    return out


def after_plant(mission: dict, attempt: dict) -> None:
    """Mission 11: record the Start snapshot once the plants are in and before anyone chats."""
    if (mission.get("lab") or {}).get("pick") != "review" or not attempt.get("profile"):
        return
    row = practice.record(attempt["profile"])
    if row and row.get("path"):
        practice.set_extra(row["name"], "baseline", foundations_checks_b.baseline(Path(row["path"])))


def baseline_view(name: str) -> dict:
    """The Start snapshot as the page shows it, for the whole run."""
    row = practice.record(name) if practice.valid_name(name) else None
    if not row:
        raise ValueError(f"{name} isn't set up.")
    base = (row.get("plan") or {}).get("baseline")
    if not isinstance(base, dict):
        return {"name": name, "ready": False}
    return {"name": name, "ready": True, "memory": base.get("memory", []), "user": base.get("user", []),
            "skills": [s["name"] for s in base.get("skills", [])], "pending": [f"{p['kind']}: {p['summary']}" for p in base.get("pending", [])],
            "taken_at": row.get("planted_at", "")}


# ---------------------------------------------------------------- run-time --


def check_context(row) -> dict:
    """What the readers for missions 7 to 11 need beyond foundations.run_checks's usual context."""
    return {"setup": (row.get("plan") or {}).get("setup") or {}, "row": row}


def wait_windows(conn, attempt_ids) -> list:
    """Waits for scheduled runs (mission 8), kept by the two-run check as an epoch pair, as ISO stamps for
    field_record.active_seconds: time inside them is never counted as active."""
    from datetime import datetime, timezone

    if not attempt_ids:
        return []
    marks = ",".join("?" for _ in attempt_ids)
    out = []
    for row in conn.execute(f"SELECT facts_json FROM f_checks WHERE attempt_id IN ({marks}) AND source = 'practice_profile'", tuple(attempt_ids)):
        try:
            facts = json.loads(row["facts_json"] or "{}").get("facts") or []
        except ValueError:
            continue
        for fact in facts:
            match = re.fullmatch(r"(\d+)-(\d+)", str(fact.get("value", ""))) if fact.get("label") == "Waiting for runs" else None
            if match:
                a, b = (datetime.fromtimestamp(int(x), timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00") for x in match.groups())
                out.append((a, b))
    return out


def watch(attempt_id) -> dict:
    """Mission 8's notice: how many runs the schedule fired for the learner's job. Read on every page open."""
    from . import foundations

    view = foundations.attempt_view(attempt_id)
    profile = view["attempt"].get("profile")
    note = next((e["body"] for e in reversed(view["entries"]) if e["kind"] == "lab_note" and e["body"].get("for") != "transfer"), {})
    name = str(note.get("job_name") or "").strip()
    row = practice.record(profile) if profile else None
    if not row or not name:
        return {"ready": False, "runs": 0, "landed": False}
    practice.require_ours(row)
    home = Path(row["path"])
    job = next((j for j in hermes_read_b.jobs(home).get("jobs", []) if j.get("name") == name), None)
    if job is None:
        return {"ready": True, "job": name, "found": False, "runs": 0, "landed": False}
    fired = foundations_checks_b.scheduled_runs(hermes_read_b.runs(home, job.get("id")).get("executions", []))
    return {"ready": True, "job": name, "found": True, "runs": len(fired), "late": sum(1 for r in fired if r["late"]),
            "landed": len(fired) >= 2, "still_on": job.get("enabled") is not False,
            "last": fired[-1].get("claimed_at") if fired else None}


def connector_text(name: str) -> dict:
    """Mission 7's settings text for the practice profile, read fresh each time."""
    if not practice.valid_name(name):
        raise ValueError("Field Academy only reads its own practice profiles.")
    row = practice.record(name)
    if not row or row["status"] not in ("ready", "planted"):
        raise ValueError(f"{name} isn't set up.")
    practice.require_ours(row)  # second review, C4: the copy button copies this text in full
    server = ((row.get("plan") or {}).get("setup") or {}).get("server", "files")
    found = hermes_read_b.settings_text(Path(row["path"]), server, {"trust": "untrusted", "tools": {"include": []}})
    if not found.get("readable"):
        return {"ok": False, "why": found.get("why", ""), "server": server}
    return {"ok": True, "text": found["text"], "server": server, "servers": found["servers"], "package": plants_b.FS_PACKAGE,
            "folder": str(hermes_read_b.folder_path(row["path"])), "folder_shown": practice.shown_path(hermes_read_b.folder_path(row["path"]))}


def ops(name: str) -> dict:
    """Mission 10's practice-profile tools: the logs folder, and the terminal commands for the doctor and a backup.
    The app's Run doctor and Create backup act on the app's own selected profile, so the page offers them only where
    the app lets a plugin aim them at the practice profile."""
    if not practice.valid_name(name):
        raise ValueError("Field Academy only reads its own practice profiles.")
    row = practice.record(name)
    if not row or row["status"] not in ("ready", "planted"):
        raise ValueError(f"{name} isn't set up.")
    practice.require_ours(row)
    logs = Path(row["path"]) / "logs"
    backups = hermes_read_b.backups(Path(row["path"]))["items"]
    return {"logs": str(logs), "logs_shown": practice.shown_path(logs), "doctor": f"hermes -p {name} doctor",
            "backup": f"hermes -p {name} backup --quick --label before-fix",
            "backups": [{"kind": b["kind"], "name": b["name"], "mtime": b["mtime"]} for b in backups[-5:]]}


def record_extras(conn, attempt: dict, mission: dict) -> dict:
    """Mission 11's record additions: whether a planted kind was seen before, the Start snapshot's size, and the
    learner's how-I-found-it lines, shown as written."""
    if (mission.get("lab") or {}).get("pick") != "review":
        return {}
    kinds = json.loads(attempt.get("plants_json") or "[]")
    met_before = [k for k in kinds if k in _met_before(conn, attempt["id"])]
    notes = [json.loads(r["body_json"]) for r in conn.execute("SELECT body_json FROM f_entries WHERE attempt_id = ? AND kind = 'lab_note' ORDER BY id",
                                                              (attempt["id"],))]
    note = next((n for n in reversed(notes) if n.get("for") != "transfer"), {})
    return {"review": {"seen_before": met_before, "job": note.get("job", ""),
                       "how_found": [scrub.scrub(note.get(k, ""), 600) for k in ("found_1", "found_2") if note.get(k)],
                       "how_found_by": "yours, shown as written",
                       "accounts": {k: scrub.scrub(note.get(k, ""), 2000) for k in ("claims", "wrong", "edits") if note.get(k)}}}


def _met_before(conn, attempt_id) -> list:
    out = []
    for row in conn.execute("SELECT id, plants_json FROM f_attempts WHERE id < ? ORDER BY id", (int(attempt_id),)):
        ran = conn.execute("SELECT 1 FROM f_checks WHERE attempt_id = ? AND phase = 'first' AND source = 'practice_profile' LIMIT 1",
                           (row["id"],)).fetchone()
        if ran:
            out.extend(json.loads(row["plants_json"] or "[]"))
    return out
