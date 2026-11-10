"""The Foundations Field Record, record format 3 (ENGINEERING-PLAN section 5, DESIGN "The new Field Record").

A Foundations record is built from the entries the learner added mission by mission (``f_record``, append-only and
chained by hash). Issuing it freezes one body in ``f_issued`` and writes a folder a stranger can check::

    field-records/foundations-<date>/
        record.md         the record, to read
        record.json       the stored body, byte for byte what the record number covers
        evidence/         the scrubbed excerpts, one file each, named in record.json
        MANIFEST.sha256   a SHA-256 for every other file, in ``shasum -a 256 -c`` format
        README.txt        how a stranger checks the folder, and what the checks do and don't prove

Rules this file keeps (decisions from review 2 and missions/11-review.md):

* Every line says who checked it: "Field Academy read it", "your Hermes graded it", or "you wrote it".
* Calibration is a table, one row per mission, predicted passes beside checked passes. No average, no Brier score, no
  "guesses high" label as a headline: with about four checks a mission one lucky check moves any average more than
  judgment does. Missions not in the record are empty rows, never filled in.
* "What you can now claim" is built from passed claims, in each mission's own wording; missions not passed are listed
  under "Not yet" with the check that missed.
* Hours count active time only: gaps over 15 minutes, which include waits for a scheduled run, are left out.
* The Hermes version says where it was read from. Field Academy never runs Hermes to find it.
* The learner previews every excerpt and can withhold any of them. A withheld excerpt keeps only its fingerprint and
  says so. Nothing outside reviewed the record unless a reviewer is named; with none, it says so.

Paths and the Guide keep their own records (format 1 and 2, ``state.certificate_markdown`` and
``deployer.certificate_markdown``); nothing here reads or writes the ``certificates`` table.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

from . import foundations, foundations_checks, foundations_content, pathways, school, scrub, store

RECORD_FORMAT = pathways.FOUNDATIONS_RECORD_FORMAT
RECORD = "Field Academy Field Record"
KIND = "foundations"

READ_BY_FA = foundations.READ_BY_FA  # "Field Academy read it"
GRADED_BY_HERMES = foundations.GRADED_BY_HERMES  # "your Hermes graded it"
WRITTEN_BY_YOU = "you wrote it"
COUNTED_BY_FA = "Field Academy counted it"
COURSE_WROTE = "the course wrote it"  # a claim the learner kept as the course wrote it (0.9 persona test)

IDLE_SECONDS = 15 * 60

ISSUER = "self"
ISSUER_LINE = "Issued by its holder with Field Academy, a community plugin for Hermes Agent. Nobody else issued it."
NOT_OFFICIAL = ("This is not an official certificate. Field Academy is an independent plugin by Damon Gardenhire, "
                "not an official Hermes course from Nous Research.")
DISCLAIMER = pathways.DISCLAIMER
SHOWS = ("Work done in practice profiles on the holder's own computer: what the holder predicted before each mission, "
         "what Field Academy read from the practice profile, what the holder's own Hermes graded, and which planted "
         "problems were caught or missed.")
DOES_NOT_SHOW = ("That anyone outside checked the work, that the holder has used Hermes on real work for months, or "
                 "anything about a Hermes version other than the one named here. The fingerprints show the files match "
                 "each other; they don't show this folder is the one the holder saved, and they don't prove Hermes "
                 "produced them.")
HOURS_RULE = ("Counted from the times work was saved and checked. Gaps over 15 minutes, including waits for a scheduled "
              "run, are left out.")
CALIBRATION_NOTE = ("One row per mission: the checks the holder predicted would pass beside the checks that did, the "
                    "first time. No average and no verdict: with about four checks a mission, one lucky or unlucky check "
                    "moves any average more than judgment does. Read down the rows and see whether the guesses got "
                    "closer.")
# The tags as a stranger reads them in record.md. The body keeps the words the learner saw on the page.
TAG_WORDS = {READ_BY_FA: "Field Academy read it", GRADED_BY_HERMES: "the holder's Hermes graded it", WRITTEN_BY_YOU: "the holder wrote it",
             COUNTED_BY_FA: "Field Academy counted it", "yours, not graded": "the holder wrote it, not graded",
             "not graded yet": "the holder wrote it, not graded",
             COURSE_WROTE: "Field Academy's course wrote it, and the holder kept it"}

# What each kind of excerpt is, for its caption in record.md (0.9 persona test). A kind not listed gets the general line.
KIND_WORDS = {
    "memory": "A line in the practice profile's memory file, as it sits there.",
    "pending": "A save Hermes was holding for approval, not yet in the memory file.",
    "session": "A line Hermes wrote in a practice chat, from the chat record (state.db).",
    "answer": "What Hermes answered in a practice chat.",
    "tool_result": "What a tool sent back inside a practice chat.",
    "tool_error": "An error a tool sent back inside a practice chat.",
    "setting": "A setting in the practice profile's config.yaml.",
    "run": "A scheduled run's output, from the run history.",
    "log_line": "A line from the practice profile's logs.",
    "skill": "Part of a skill file in the practice profile.",
    "job_prompt": "A scheduled job's request, from the job list.",
    "job": "A scheduled job, from the job list.",
    "soul": "A line from the practice profile's SOUL.md.",
    "removed_note": "A note that was in memory before the work and is gone after it.",
    "practice_file": "A file in the practice folder.",
    "checkpoint": "The undo snapshot store's record for the practice folder.",
    "backup": "A backup of the practice profile.",
}
KIND_DEFAULT = "An excerpt Field Academy read from the practice profile."
REVIEWER_NONE = "Nobody outside has reviewed this record."
NO_CASE = "No case was written for this record."
LIMITS_MIN, LIMITS_MAX = 20, 800
CASE_MAX_WORDS = 300

# Where a Hermes version was read from, in plain words.
SOURCE_WORDS = {
    "git tag": "the release tag of the Hermes code installed on this computer",
    "install stamp tag": "the release tag in Hermes's install stamp",
    "install stamp": "Hermes's install stamp",
}


# ------------------------------------------------------------------ pieces --


def _canonical(body) -> str:
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_number(body) -> str:
    """FA-XXXX-XXXX-XXXX: the first 12 hex characters of a SHA-256 over the body without its number. The same rule as
    every other Field Record (``state.certificate_number``)."""
    unsigned = {key: value for key, value in body.items() if key != "number"}
    digest = hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest()[:12].upper()
    return f"FA-{digest[0:4]}-{digest[4:8]}-{digest[8:12]}"


def verify(body) -> bool:
    return isinstance(body, dict) and body.get("number") == record_number(body)


def _parse(stamp):
    try:
        return datetime.fromisoformat(str(stamp))
    except (TypeError, ValueError):
        return None


def active_seconds(stamps, idle: int = IDLE_SECONDS, waits=()) -> int:
    """Seconds of active work in a list of ISO time stamps: the sum of the gaps between one stamp and the next, leaving
    out every gap longer than ``idle`` and every gap that overlaps a wait (``(start, end)`` stamps, such as the time
    between setting up a scheduled job and its run). Stamps from different attempts merge into one timeline, so two
    missions worked side by side aren't counted twice."""
    moments = sorted(m for m in (_parse(s) for s in stamps or []) if m is not None)
    windows = [(a, b) for a, b in ((_parse(x), _parse(y)) for x, y in waits or ()) if a is not None and b is not None]
    total = 0.0
    for before, after in zip(moments, moments[1:]):
        gap = (after - before).total_seconds()
        if gap <= 0 or gap > idle:
            continue
        if any(before < end and after > start for start, end in windows):
            continue
        total += gap
    return int(total)


def version_line(hermes: dict) -> str:
    value, source = str(hermes.get("version") or ""), str(hermes.get("read_from") or "")
    if not value:
        return "Field Academy couldn't find the Hermes version on this computer."
    where = SOURCE_WORDS.get(source) or (f"the {source}" if source.startswith("package ") else source) or "an unknown place"
    exact = "" if hermes.get("exact", True) else " This is the lowest it can be; Hermes may be newer."
    return f"Hermes {value}, read from {where}.{exact}"


def _hermes() -> dict:
    from . import evidence

    try:
        found = evidence.detect_version_detail()
    except Exception:  # noqa: BLE001 - a version we can't read is reported as missing, never guessed
        found = {"value": "", "source": "", "exact": False}
    out = {"version": str(found.get("value") or ""), "read_from": str(found.get("source") or ""), "exact": bool(found.get("exact")),
           "checked_by": READ_BY_FA}
    out["line"] = version_line(out)
    return out


def _all_passed(values) -> bool:
    return bool(values) and all(v is True for v in values)


def calibration_rows(missions, grids) -> list:
    """One row per mission, in course order. ``grids`` maps a mission id to its first-attempt grid (rows with
    ``expect_pass``, ``self_pass`` and ``passed``); a mission with no grid is an empty row."""
    rows = []
    for mission in missions:
        grid = grids.get(mission["id"])
        row = {"mission": mission["id"], "title": mission.get("title", ""), "order": mission.get("order"), "in_record": grid is not None,
               "checks": None, "predicted": None, "self_scored": None, "passed_first": None}
        if grid is not None:
            row.update(checks=len(grid), predicted=sum(1 for g in grid if g.get("expect_pass") is True),
                       self_scored=sum(1 for g in grid if g.get("self_pass") is True),
                       passed_first=sum(1 for g in grid if g.get("passed") is True))
        rows.append(row)
    return rows


def _missions() -> list:
    missions = list(foundations_content.load_all(foundations.CONTENT_DIR).values())
    return sorted(missions, key=lambda m: (m.get("order") if isinstance(m.get("order"), int) else 999, m["id"]))


# ------------------------------------------------------------------ entries --


def _rows(conn) -> list:
    return [dict(r) for r in conn.execute("SELECT * FROM f_record ORDER BY id")]


def verify_chain(conn) -> dict:
    """Recompute every record entry's hash and link, corrections included."""
    prev = ""
    count = 0
    for row in _rows(conn):
        digest = hashlib.sha256(f"{prev}|{row['mission_id']}|{row['body_json']}|{row['created_at']}".encode("utf-8")).hexdigest()
        if row["prev_hash"] != prev or row["hash"] != digest:
            return {"intact": False, "head": prev, "entries": count, "broken_at": row["id"]}
        prev = row["hash"]
        count += 1
    return {"intact": True, "head": prev, "entries": count}


def _slug(text) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")[:40] or "excerpt"


def _yes_no(value) -> str:
    return "pass" if value is True else "fail" if value is False else "not run"


def _claim_tag(author) -> str:
    return COURSE_WROTE if author == "course" else WRITTEN_BY_YOU


def backs(mission, standard, check_id) -> dict:
    """Which check an excerpt backs: ``{"n", "text"}`` for a check in the frozen standard (through the mission's
    ``proves_by``), ``{"n": None, "text": "the transfer task"}`` for a transfer check, else a general line."""
    mission = mission or {}
    transfer = set((mission.get("transfer") or {}).get("live_checks") or [])
    proves = {c.get("id"): str(c.get("proves_by") or "") for c in mission.get("standard") or []}
    for i, check in enumerate(standard or [], start=1):
        if re.search(rf"live:{re.escape(str(check_id))}(?![\w.-])", proves.get(check.get("id"), "")):
            return {"n": i, "label": f"Backs check {i}", "text": str(check.get("text") or "")}
    if check_id in transfer:
        return {"n": None, "label": "Backs the transfer task", "text": "the same idea, used on a second job."}
    return {"n": None, "label": "Backs a check Field Academy ran", "text": "on the practice profile."}


def _mission_map() -> dict:
    return foundations_content.load_all(foundations.CONTENT_DIR)


def _entry(n, row, body, withhold) -> dict:
    grid = body.get("grid") or []
    mission = _mission_map().get(body.get("mission", row["mission_id"])) or {}
    standard = body.get("standard") or []
    prediction = body.get("prediction") or {}
    names = {}
    evidence = []
    seen = set()
    for item in body.get("evidence") or []:
        # A check that ran twice read the same line twice: the record keeps one copy of each excerpt per entry.
        if item.get("sha256") in seen:
            continue
        seen.add(item.get("sha256"))
        withheld = bool(item.get("withheld")) or item.get("id") in withhold
        if not withheld and scrub.scrub(str(item.get("excerpt", "")), foundations_checks.EXCERPT) != str(item.get("excerpt", "")):
            withheld = True  # kept before the scrubber knew a shape it now removes: only its fingerprint goes in the record
        out = {"id": item.get("id"), "check": item.get("check", ""), "kind": item.get("kind", ""), "file": item.get("file", ""),
               "sha256": item.get("sha256", ""), "read_at": item.get("read_at", ""), "checked_by": READ_BY_FA,
               "withheld": withheld, "excerpt": "" if withheld else str(item.get("excerpt", "")), "excerpt_file": None,
               "backs": backs(mission, standard, item.get("check", "")), "phase": item.get("phase", ""),
               # A withheld excerpt keeps no facts either: a fact can quote the same line (second review, C2).
               "facts": [] if withheld else foundations_checks.clean_facts([f for f in item.get("facts") or [] if isinstance(f, dict)][:4])}
        if not withheld:
            stem = f"{n:02d}-{_slug(out['kind'])}"
            names[stem] = names.get(stem, 0) + 1
            out["excerpt_file"] = f"evidence/{stem}{'' if names[stem] == 1 else '-' + str(names[stem])}.txt"
        evidence.append(out)

    def note(key):
        return {"text": str(body.get(key) or ""), "checked_by": WRITTEN_BY_YOU}

    return {
        "n": n, "entry_hash": row["hash"], "prev_hash": row["prev_hash"], "added_at": row["created_at"],
        "mission": body.get("mission", row["mission_id"]), "mission_title": body.get("mission_title", ""),
        "level": body.get("level", ""), "attempt_no": body.get("attempt_no"),
        "claim": {"text": body.get("claim", ""), "author": body.get("claim_author", ""), "checked_by": _claim_tag(body.get("claim_author", ""))},
        "mode": body.get("mode") or "full", "tested_out": body.get("tested_out") is True, "skipped": list(body.get("skipped") or []),
        "where_wrong": {"text": str(prediction.get("where_wrong") or ""), "checked_by": WRITTEN_BY_YOU},
        "checks": [{"id": g.get("id"), "text": g.get("text", ""), "expect_pass": g.get("expect_pass"), "confidence": g.get("confidence"),
                    "self_pass": g.get("self_pass"), "passed": g.get("passed"), "passed_after_fix": g.get("passed_after_fix"),
                    "level": g.get("level"), "checked_by": g.get("checked_by", READ_BY_FA)} for g in grid],
        "result_first": body.get("result_first") or {}, "result_after_fix": body.get("result_after_fix") or {},
        "transfer": body.get("transfer") or {}, "explain": body.get("explain") or {},
        "caught": body.get("caught") or [], "missed": body.get("missed") or [],
        "gap": note("gap"), "diagnosis": note("diagnosis"), "fix": note("fix"),
        "evidence": evidence, "corrections": [],
        **_help_and_cost(row),
        **({"first_flight": dict(body["first_flight"])} if isinstance(body.get("first_flight"), dict) else {}),
    }


def _help_and_cost(row) -> dict:
    """0.9 premium, AI lane: how the snag was found (from the attempt's ``help`` entries) and what the practice cost
    (Hermes's own estimate, and Field Academy's calls in tokens). Read at build time; neither changes how the record
    number or the chain is made. A failure here leaves both out rather than stopping the record."""
    try:
        from . import cost, guide

        helped = guide.help_summary(int(row["attempt_id"]))
        spent = cost.attempt_cost(int(row["attempt_id"]))
    except Exception:
        return {}
    return {"help": {"words": helped["words"], "key": helped["key"], "hunt_helps": helped["hunt_helps"], "checked_by": COUNTED_BY_FA},
            "cost": {"practice": spent["line"], "guide": spent["guide_line"], "practice_usd": (spent["practice"] or {}).get("usd"),
                     "guide_tokens": spent["guide_tokens"], "checked_by": COUNTED_BY_FA}}


def _passed(entry) -> str:
    """"tested_out" for a test-out that passed every check the first time, "first" when every check passed the first
    time, "after_fix" when the rest passed after the fix, else ""."""
    checks = entry["checks"]
    if entry.get("tested_out") and _all_passed([c["passed"] for c in checks]):
        return "tested_out"
    if _all_passed([c["passed"] for c in checks]):
        return "first"
    if checks and all(c["passed"] is True or c["passed_after_fix"] is True for c in checks):
        return "after_fix"
    return ""


def _can_claim(missions, entries) -> dict:
    passed, not_yet = [], []
    for mission in missions:
        mine = [e for e in entries if e["mission"] == mission["id"]]
        won = [(e, _passed(e)) for e in mine if _passed(e)]
        if won:
            entry, how = next(((e, h) for e, h in won if h == "first"), next(((e, h) for e, h in won if h == "tested_out"), won[0]))
            passed.append({"mission": mission["id"], "title": mission.get("title", ""), "claim": entry["claim"]["text"], "date": entry["added_at"],
                           "after_fix": how == "after_fix", "tested_out": how == "tested_out", "entry": entry["n"], "checked_by": READ_BY_FA})
            continue
        if mine:
            last = mine[-1]
            miss = next((c for c in last["checks"] if c["passed"] is False and c["passed_after_fix"] is not True), None)
            unrun = next((c for c in last["checks"] if c["passed"] is None and c["passed_after_fix"] is None), None)
            why = f"Missed: {miss['text']}" if miss else f"Not checked yet: {unrun['text']}" if unrun else "Not every check ran."
            not_yet.append({"mission": mission["id"], "title": mission.get("title", ""), "why": why,
                            "entry": last["n"], "checked_by": READ_BY_FA})
        else:
            not_yet.append({"mission": mission["id"], "title": mission.get("title", ""), "why": "Not in the record yet.", "entry": None,
                            "checked_by": READ_BY_FA})
    return {"passed": passed, "not_yet": not_yet}


TRAILS_NOTE = ("The trail map: five trails from the Foundations trailhead, each climbing Beginner, Intermediate, Advanced "
               "and Capstone camp to its summit at Olympus. A camp is reached when every mission in it has passed; a "
               "trail's summit is its own Field Record, created.")


def _trails() -> list:
    """Camps reached per trail and summits, read from the paths' progress. Empty when it can't be read: the record
    never fails on it."""
    try:
        from . import deployer, state

        tracks = list(state.snapshot().get("tracks") or [])
        try:
            guide = deployer.snapshot()
            if guide.get("available") and guide.get("track"):
                tracks.append(guide["track"])
        except Exception:  # noqa: BLE001
            pass
        return school.trails(tracks)
    except Exception:  # noqa: BLE001
        return []


PASSED_NOTE = ("Each mission below passed every check. Field Academy read each line of evidence from the practice profile "
               "itself; the file is in this folder's evidence/ folder and its SHA-256 is in MANIFEST.sha256.")


def _passed_list(missions, entries) -> dict:
    """The proof, mission by mission: where it sits on the trail map, how it passed, and every line of evidence."""
    can = _can_claim(missions, entries)
    by_n = {e["n"]: e for e in entries}
    rows = []
    for p in can["passed"]:
        entry = by_n.get(p["entry"])
        if not entry:
            continue
        where = school.trail_of(p["mission"])
        rows.append({
            "mission": p["mission"], "title": p["title"],
            "where": f"{where['name']} trail, {where['camp_name']} camp" if where else "Foundations, the trailhead",
            "how": "tested out" if p["tested_out"] else "after a fix" if p["after_fix"] else "first time",
            "date": p["date"], "entry": p["entry"], "claim": p["claim"],
            "checks": f"{sum(1 for c in entry['checks'] if c['passed'] or c['passed_after_fix'])} of {len(entry['checks'])}",
            "evidence": [{"file": ev["excerpt_file"] or "", "withheld": ev["withheld"], "kind": ev["kind"], "read_from": ev["file"],
                          "sha256": ev["sha256"], "excerpt": "" if ev["withheld"] else ev["excerpt"][:160]} for ev in entry["evidence"]],
            "checked_by": READ_BY_FA,
        })
    return {"missions": rows, "note": PASSED_NOTE}


def _side(entry) -> dict:
    first = entry["result_first"]
    return {"n": entry["n"], "mission": entry["mission"], "mission_title": entry["mission_title"], "added_at": entry["added_at"],
            "found_wrong": entry["gap"]["text"], "found_wrong_by": WRITTEN_BY_YOU,
            "caught": len(entry["caught"]), "missed": len(entry["missed"]),
            "first_result": {"passed": first.get("passed"), "of": first.get("of")}, "checked_by": READ_BY_FA}


def _first_and_last(entries) -> dict:
    if not entries:
        return {"first": None, "last": None, "note": "Nothing is in the record yet."}
    if len(entries) == 1:
        return {"first": _side(entries[0]), "last": None,
                "note": "Only one mission is in the record, so first and last are the same work. Add more to see the change."}
    return {"first": _side(entries[0]), "last": _side(entries[-1]),
            "note": "What you found wrong with the real result in your first entry, beside your latest."}


def _activity(conn, attempt_ids) -> list:
    if not attempt_ids:
        return []
    marks = ",".join("?" for _ in attempt_ids)
    ids = tuple(attempt_ids)
    stamps = []
    for sql in (f"SELECT started_at AS t FROM f_attempts WHERE id IN ({marks})",
                f"SELECT frozen_at AS t FROM f_attempts WHERE id IN ({marks}) AND frozen_at != ''",
                f"SELECT created_at AS t FROM f_entries WHERE attempt_id IN ({marks})",
                f"SELECT created_at AS t FROM f_checks WHERE attempt_id IN ({marks})",
                f"SELECT read_at AS t FROM f_evidence WHERE attempt_id IN ({marks})",
                f"SELECT created_at AS t FROM f_record WHERE attempt_id IN ({marks})"):
        stamps += [r["t"] for r in conn.execute(sql, ids)]
    return stamps


# Fields that hold fingerprints, record numbers or file names Field Academy made. Everything else in a record body is
# text that could quote a practice profile or the learner, so build() scrubs it (scrub.scrub would take a 64-character
# fingerprint for a key).
_NOT_SCRUBBED = frozenset({"sha256", "entry_hash", "prev_hash", "hash", "head", "chain_head", "number", "excerpt",
                           "excerpt_file", "read_at", "added_at", "created_at", "issued_at", "issued", "first_work",
                           "last_entry", "frozen_at", "standard_frozen_at", "date"})


def _scrubbed(value, key=""):
    """Every string in a record body scrubbed, except fingerprints, times and the excerpts (scrubbed and fingerprinted
    when they were read, and withheld by _entry if today's scrubber would change them)."""
    if isinstance(value, dict):
        return {k: _scrubbed(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrubbed(v, key) for v in value]
    if isinstance(value, str) and key not in _NOT_SCRUBBED:
        return scrub.scrub(value)
    return value


def _clean(value, limit) -> str:
    return scrub.scrub(re.sub(r"[ \t]+", " ", str(value or "")).strip(), limit)


def build(holder="", limits="", case="", withhold=(), issued_at=None) -> dict:
    """The record body as it would be issued now, without its number. Pure apart from reading the database."""
    withhold = {int(x) for x in withhold or [] if str(x).lstrip("-").isdigit()}
    missions = _missions()
    with foundations._conn() as conn:
        rows = _rows(conn)
        chain = verify_chain(conn)
        main = [r for r in rows if not r["corrects_id"]]
        bodies = [json.loads(r["body_json"]) for r in main]
        # Withholding an excerpt withholds every copy of the same text (the same check can read the same line twice).
        shas = {ev.get("sha256") for b in bodies for ev in b.get("evidence") or [] if ev.get("id") in withhold or ev.get("withheld")}
        withhold = withhold | {ev.get("id") for b in bodies for ev in b.get("evidence") or [] if ev.get("sha256") in shas}
        entries = []
        by_id = {}
        for n, (row, stored) in enumerate(zip(main, bodies), start=1):
            entry = _entry(n, row, stored, withhold)
            entries.append(entry)
            by_id[row["id"]] = entry
        for row in rows:
            if row["corrects_id"] and row["corrects_id"] in by_id:
                body = json.loads(row["body_json"])
                by_id[row["corrects_id"]]["corrections"].append({"text": str(body.get("correction", "")), "added_at": row["created_at"],
                                                                 "hash": row["hash"], "checked_by": WRITTEN_BY_YOU})
        attempt_ids = sorted({int(r["attempt_id"]) for r in main})
        stamps = _activity(conn, attempt_ids)
        started = [r["started_at"] for r in conn.execute(
            f"SELECT started_at FROM f_attempts WHERE id IN ({','.join('?' for _ in attempt_ids)})", tuple(attempt_ids))] if attempt_ids else []
        from . import foundations_b

        waits = foundations_b.wait_windows(conn, attempt_ids)
    seconds = active_seconds(stamps, waits=waits)
    issued_at = issued_at or store.now()
    first_grids = {}
    for entry in entries:
        first_grids.setdefault(entry["mission"], entry["checks"])
    can_claim = _can_claim(missions, entries)
    body = {
        "record": RECORD,
        "record_format": RECORD_FORMAT,
        "kind": KIND,
        "scope": {
            "holder": {"name": _clean(holder, 80), "checked_by": WRITTEN_BY_YOU},
            "issuer": ISSUER,
            "issuer_line": ISSUER_LINE,
            "not_official": NOT_OFFICIAL,
            "dates": {"first_work": min(started) if started else "", "last_entry": main[-1]["created_at"] if main else "", "issued": issued_at},
            "hermes": _hermes(),
            "hours": {"active_minutes": seconds // 60, "hours": round(seconds / 3600, 1), "rule": HOURS_RULE, "checked_by": COUNTED_BY_FA},
            "missions_in_record": len({e["mission"] for e in entries}),
            "missions_in_course": len(missions),
        },
        "claims": [{"n": e["n"], "mission": e["mission"], "mission_title": e["mission_title"], "claim": e["claim"]["text"],
                    "author": e["claim"]["author"], "checked_by": _claim_tag(e["claim"]["author"]), "standard": stored.get("standard") or [],
                    "standard_frozen_at": stored.get("standard_frozen_at", ""), "changes": stored.get("standard_changes") or []}
                   for e, stored in zip(entries, bodies)],
        "entries": entries,
        "calibration": {"per_mission": calibration_rows(missions, first_grids), "note": CALIBRATION_NOTE, "checked_by": READ_BY_FA},
        "first_and_last": _first_and_last(entries),
        "can_claim": _can_claim(missions, entries),
        "passed": _passed_list(missions, entries),
        "trails": {"trails": _trails(), "note": TRAILS_NOTE, "checked_by": COUNTED_BY_FA,
                   "trailhead": {"passed": sum(1 for p in can_claim["passed"] if p["mission"] not in school.PLACEMENTS),
                                 "total": sum(1 for m in missions if m["id"] not in school.PLACEMENTS)}},
        "case": {"text": _clean(case, 2400), "checked_by": WRITTEN_BY_YOU, "note": "" if str(case or "").strip() else NO_CASE},
        "limits": {"text": _clean(limits, LIMITS_MAX), "checked_by": "yours, not graded"},
        "reviewer": None,
        "reviewer_note": REVIEWER_NONE,
        "chain": {"head": chain["head"], "entries": chain["entries"], "intact": chain["intact"], "checked_by": READ_BY_FA},
        "chain_head": chain["head"],
        "shows": SHOWS,
        "does_not_show": DOES_NOT_SHOW,
        "disclaimer": DISCLAIMER,
        "plugin_version": _plugin_version(),
        "issued_at": issued_at,
    }
    return _scrubbed(body)


def _plugin_version() -> str:
    from . import state

    return state._plugin_version()


def excerpts(body) -> list:
    """Every excerpt in a body, flat, for the preview screen."""
    return [{"id": ev["id"], "entry": e["n"], "mission_title": e["mission_title"], "check": ev["check"], "kind": ev["kind"], "file": ev["file"],
             "sha256": ev["sha256"], "read_at": ev["read_at"], "excerpt": ev["excerpt"], "withheld": ev["withheld"], "excerpt_file": ev["excerpt_file"],
             "backs": ev.get("backs") or {}, "about": KIND_WORDS.get(ev["kind"], KIND_DEFAULT)}
            for e in body.get("entries", []) for ev in e.get("evidence", [])]


def _problems(holder, limits, case) -> list:
    out = []
    if not str(holder or "").strip():
        out.append("Type the name you want on your Field Record.")
    if len(str(limits or "").strip()) < LIMITS_MIN:
        out.append("Write two or three lines on what this record doesn't show, in your own words.")
    if len(str(limits or "")) > LIMITS_MAX:
        out.append(f"Keep what the record doesn't show under {LIMITS_MAX} characters.")
    if len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.-]*", str(case or ""))) > CASE_MAX_WORDS:
        out.append(f"Keep the case under {CASE_MAX_WORDS} words.")
    return out


# ------------------------------------------------------------------ issuing --


def preview(holder="", limits="", case="", withhold=()) -> dict:
    """The record exactly as Save would issue it, apart from the time and the number, with every excerpt listed."""
    body = build(holder, limits, case, withhold)
    return {"ready": bool(body["entries"]), "problems": _problems(holder, limits, case), "body": body, "excerpts": excerpts(body),
            "verdict": verdict_line(body), "issued": issued()}


def _row_view(row) -> dict:
    body = json.loads(row["body_json"])
    folder = row["folder"] or ""
    return {"number": row["number"], "issued_at": row["issued_at"], "folder": folder, "folder_shown": _shown(folder),
            "valid": verify(body), "entries": len(body.get("entries", []))}


def _shown(folder) -> str:
    from . import practice

    return practice.shown_path(folder) if folder else ""


def issued() -> list:
    with foundations._conn() as conn:
        return [_row_view(r) for r in conn.execute("SELECT * FROM f_issued ORDER BY id")]


def _records_dir() -> Path:
    from . import state

    return state.data_dir() / "field-records"


def _new_folder(issued_at) -> Path:
    base = _records_dir()
    day = str(issued_at)[:10]
    for n in range(1, 1000):
        folder = base / (f"foundations-{day}" if n == 1 else f"foundations-{day}-{n}")
        if not folder.exists():
            return folder
    raise ValueError("Too many records saved today. Move some out of field-records first.")


def issue(holder, limits, case="", withhold=(), confirmed: bool = False) -> dict:
    """Issue the record and save its folder. Final: the issued body can't be changed; a later record is a new one."""
    if not confirmed:
        raise ValueError("Saving your Field Record can't be undone, so it needs your confirmation.")
    problems = _problems(holder, limits, case)
    if problems:
        raise ValueError(problems[0])
    body = build(holder, limits, case, withhold)
    if not body["entries"]:
        raise ValueError("Add a mission to your record first. A Field Record needs at least one entry.")
    if not body["chain"]["intact"]:
        raise ValueError("Your record entries don't match their fingerprints any more, so Field Academy won't issue a record from them.")
    body["number"] = record_number(body)
    stored = _canonical(body)
    folder = _new_folder(body["issued_at"])
    files = write_folder(folder, stored)
    with foundations._conn() as conn:
        conn.execute("INSERT INTO f_issued(number, issued_at, body_json, folder) VALUES (?, ?, ?, ?)",
                     (body["number"], body["issued_at"], stored, str(folder)))
    return {"number": body["number"], "folder": str(folder), "folder_shown": _shown(folder), "files": files, "issued": issued()}


def save_again(number: str) -> dict:
    """Write an issued record's folder again from the stored body, in the folder it was first saved to."""
    with foundations._conn() as conn:
        row = conn.execute("SELECT * FROM f_issued WHERE number = ? ORDER BY id DESC LIMIT 1", (str(number),)).fetchone()
    if row is None:
        raise ValueError("No Field Record with that number.")
    folder = Path(row["folder"]) if row["folder"] else _new_folder(row["issued_at"])
    files = write_folder(folder, row["body_json"])
    return {"number": row["number"], "folder": str(folder), "folder_shown": _shown(folder), "files": files}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, path)


def write_folder(folder, stored: str) -> list:
    """Write the five parts of a record folder from the stored body. Bytes are written as is, with ``\\n`` line ends on
    every system, so the fingerprints are the same everywhere."""
    folder = Path(folder)
    body = json.loads(stored)
    written = {}
    for e in body.get("entries", []):
        for ev in e.get("evidence", []):
            if ev.get("excerpt_file") and not ev.get("withheld"):
                text = scrub.scrub(ev.get("excerpt", ""), foundations_checks.EXCERPT)
                if hashlib.sha256(text.encode("utf-8")).hexdigest() != ev.get("sha256"):
                    raise ValueError("An excerpt doesn't match its fingerprint, so the record folder wasn't written.")
                written[ev["excerpt_file"]] = text
    written["record.json"] = stored
    written["record.md"] = record_markdown(body)
    written["README.txt"] = readme_text(body)
    for rel, text in written.items():
        _write(folder / rel, text)
    manifest = "".join(f"{hashlib.sha256(written[rel].encode('utf-8')).hexdigest()}  {rel}\n" for rel in sorted(written))
    _write(folder / "MANIFEST.sha256", manifest)
    return sorted(written) + ["MANIFEST.sha256"]


def check_folder(folder) -> dict:
    """What a stranger's checks would say: each file in MANIFEST.sha256 against its fingerprint, and the record number."""
    folder = Path(folder)
    results = []
    try:
        lines = (folder / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"ok": False, "files": [], "number_ok": False, "why": "MANIFEST.sha256 is missing."}
    for line in lines:
        digest, _, rel = line.partition("  ")
        try:
            ok = hashlib.sha256((folder / rel).read_bytes()).hexdigest() == digest
        except OSError:
            ok = False
        results.append({"file": rel, "ok": ok})
    try:
        number_ok = verify(json.loads((folder / "record.json").read_text(encoding="utf-8")))
    except (OSError, ValueError):
        number_ok = False
    return {"ok": all(r["ok"] for r in results) and number_ok and bool(results), "files": results, "number_ok": number_ok}


# --------------------------------------------------------------- rendering --


def _date(stamp) -> str:
    moment = _parse(stamp)
    return f"{moment.strftime('%B')} {moment.day}, {moment.year}" if moment else (str(stamp or "") or "not recorded")


def _when(stamp) -> str:
    """A date with its time, in UTC, as every stamp is kept: "October 3, 2026, 10:42 UTC". The record's claims are
    about order (saved, then a new chat), and only times show order (0.9 persona test)."""
    moment = _parse(stamp)
    if not moment:
        return str(stamp or "") or "not recorded"
    if moment.tzinfo is not None:
        from datetime import timezone

        moment = moment.astimezone(timezone.utc)
    return f"{moment.strftime('%B')} {moment.day}, {moment.year}, {moment.strftime('%H:%M')} UTC"


def _words(who) -> str:
    return "; ".join(TAG_WORDS.get(part, part) for part in str(who or "").split("; ") if part)


def _tag(who) -> str:
    words = _words(who)
    return f" *({words[:1].upper()}{words[1:]}.)*" if words else ""


# Second review, C3: text that can quote a practice profile or a learner (check text, facts, plant titles, file names)
# goes into record.md as one line with Markdown's control characters escaped, so it can't start a heading, a list, a
# table row, a link or a remote image, or close a code span.
_MD_SPECIAL = re.compile(r"([\\`*_\[\]<>|~!#])")


def _md(value) -> str:
    """One line of plain Markdown text: every run of whitespace (newlines included) made a space, control characters
    escaped."""
    return _MD_SPECIAL.sub(r"\\\1", " ".join(str(value if value is not None else "").split()))


def _code(value) -> str:
    """An inline code span on one line, its backtick run longer than any inside the value."""
    flat = " ".join(str(value if value is not None else "").split())
    fence = "`" * (max((len(r) for r in re.findall(r"`+", flat)), default=0) + 1)
    pad = " " if flat.startswith("`") or flat.endswith("`") else ""
    return f"{fence}{pad}{flat}{pad}{fence}"


def _cell(value) -> str:
    return _md(value)


def _plural(n, one, many) -> str:
    return f"{n} {one if n == 1 else many}"


def _count(result) -> str:
    if not result or result.get("of") is None:
        return "not run"
    return f"{result.get('passed')} of {result.get('of')}"


def _n(count, one, many) -> str:
    return f"{count} {one if count == 1 else many}"


def verdict_line(body) -> str:
    """One line a stranger can read first: what passed and how, the planted problems caught and missed, who graded the
    explanations, and whether anyone outside reviewed it. Counted from the body, so it never says more than it holds."""
    entries = body.get("entries") or []
    passed = (body.get("can_claim") or {}).get("passed") or []
    of = (body.get("scope") or {}).get("missions_in_course") or len({e.get("mission") for e in entries})
    how = [(sum(1 for i in passed if not i.get("after_fix") and not i.get("tested_out")), "the first time"),
           (sum(1 for i in passed if i.get("after_fix")), "after a fix"),
           (sum(1 for i in passed if i.get("tested_out")), "by testing out")]
    ways = [f"{count} {words}" for count, words in how if count]
    head = f"{len(passed)} of {_n(of, 'mission', 'missions')} passed" + (f" ({', '.join(ways)})" if ways else "")
    caught = sum(len(e.get("caught") or []) for e in entries)
    missed = sum(len(e.get("missed") or []) for e in entries)
    graded = any((e.get("explain") or {}).get("level") for e in entries)
    reviewer = body.get("reviewer")
    return " ".join([
        f"{head}.",
        f"{_n(caught, 'planted problem', 'planted problems')} caught, {missed} missed.",
        "Explanations graded by the holder's own Hermes." if graded else "No explanation graded.",
        f"Reviewed by {reviewer.get('name', '')}." if reviewer else "No outside review.",
    ])


def ask_holder(entry) -> list:
    """Two or three questions for an interview, built from what this entry holds, so a reader can test the record
    against the person (README.txt's advice, made concrete)."""
    checks = entry.get("checks") or []
    out = []
    if entry.get("tested_out"):
        out.append("You tested out of this mission. Walk me through the job as you did it: what did you open to check "
                   "your own work before you pressed Check?")
    fixed = next(((i, c) for i, c in enumerate(checks, start=1) if c.get("passed") is False and c.get("passed_after_fix") is True), None)
    if fixed:
        out.append(f"Check {fixed[0]} missed on the first run and passed after your fix (\"{_md(fixed[1].get('text', ''))}\"). "
                   "What did you change, and how did you know it held?")
    for plant in (entry.get("caught") or [])[:1]:
        out.append(f"The practice profile had a planted problem: {_md(plant.get('title', plant.get('kind', '')))}. How did you "
                   "find it, and where would you look first on a real setup?")
    for plant in (entry.get("missed") or [])[:1]:
        out.append(f"You missed a planted problem: {_md(plant.get('title', plant.get('kind', '')))}. What would you check "
                   "differently now?")
    predicted = sum(1 for c in checks if c.get("expect_pass") is True)
    first = sum(1 for c in checks if c.get("passed") is True)
    if checks and predicted != first:
        out.append(f"You predicted {predicted} of {len(checks)} checks would pass, and {first} did the first time. Where "
                   "was your guess off, and why?")
    if len(out) < 2 and any(not ev.get("withheld") for ev in entry.get("evidence") or []):
        out.append("Pick one excerpt below and open the file it came from. What would it say if the check had failed?")
    return out[:3]


def _facts_words(facts) -> str:
    return "; ".join(f"{_md(f.get('label', ''))}: {_md(f.get('value', ''))}" for f in facts or [] if f.get("label"))


def trails_markdown(trails) -> list:
    """The trail map in record.md: per trail, each camp reached or not, and the summit."""
    if not isinstance(trails, dict) or not trails.get("trails"):
        return []
    head = trails.get("trailhead") or {}
    lines = ["## The trail map", "", trails.get("note", TRAILS_NOTE), ""]
    if head.get("total"):
        lines += [f"**Foundations, the trailhead:** {head.get('passed', 0)} of {head['total']} missions passed.", ""]
    lines += ["| Trail | Camps | Summit |", "|---|---|---|"]
    for t in trails["trails"]:
        camps = ", ".join(c["name"] + (" reached" if c["reached"] else f" {c['passed']} of {c['total']}") for c in t["camps"])
        lines.append(f"| {_cell(t['name'])}{(' (' + _cell(t['eyebrow'].lower()) + ')') if t.get('eyebrow') else ''} | {_cell(camps)} | {'reached' if t['summit'] else 'not yet'} |")
    lines.append("")
    for t in trails["trails"]:
        done = [m for m in t.get("passed") or [] if not m.get("practice")]
        if done:
            lines.append(f"- {_md(t['name'])}, path missions passed: " + "; ".join(f"{_md(m['title'])} ({m['camp']} camp)" for m in done))
    return lines + ["", f"Counted from the paths' progress. A path mission's check reads a document you made; a practice "
                        f"mission's evidence is listed below.{_tag(COUNTED_BY_FA)}", ""]


def passed_markdown(passed) -> list:
    """The missions passed, each with where it sits, how it passed and its evidence files."""
    if not isinstance(passed, dict):
        return []
    lines = ["## Missions passed, with evidence", "", passed.get("note", PASSED_NOTE), ""]
    if not passed.get("missions"):
        return lines + ["None yet.", ""]
    for m in passed["missions"]:
        lines += [f"### {_md(m['title'])}", "", f"{m['where']}. Passed {m['how']}, {m['checks']} checks, {_date(m['date'])}. "
                  f"Record entry {m['entry']}.{_tag(READ_BY_FA)}", "", f"**Claim:** {_md(m['claim'])}", ""]
        for ev in m["evidence"]:
            if ev["withheld"]:
                lines.append(f"- {_md(ev['read_from'])}: withheld by the holder, fingerprint `{ev['sha256'][:16]}`")
            else:
                lines.append(f"- `{ev['file']}`, read from {_md(ev['read_from'])}: \"{_md(ev['excerpt'])}\" (`{ev['sha256'][:16]}`)")
        lines.append("")
    return lines


def record_markdown(body) -> str:
    scope = body.get("scope") or {}
    hermes = scope.get("hermes") or {}
    hours = scope.get("hours") or {}
    dates = scope.get("dates") or {}
    lines = [
        "# Field Record: Foundations",
        "",
        body.get("disclaimer", DISCLAIMER),
        "",
        f"Record number: `{body.get('number', 'made when the record is saved')}`",
        "",
        f"**Verdict:** {verdict_line(body)}{_tag(COUNTED_BY_FA)}",
        "",
        "## Scope",
        "",
        f"- **Holder:** {_md(scope.get('holder', {}).get('name', ''))}{_tag(WRITTEN_BY_YOU)}",
        f"- **Issued by:** {scope.get('issuer_line', ISSUER_LINE)}",
        f"- **Official?** {scope.get('not_official', NOT_OFFICIAL)}",
        f"- **Dates:** first work {_when(dates.get('first_work'))}, last entry {_when(dates.get('last_entry'))}, saved {_when(dates.get('issued'))}",
        f"- **Hermes:** {version_line(hermes)}{_tag(READ_BY_FA)}",
        f"- **Active time:** {hours.get('hours', 0)} hours ({hours.get('active_minutes', 0)} minutes). {hours.get('rule', HOURS_RULE)}{_tag(COUNTED_BY_FA)}",
        f"- **Missions in the record:** {scope.get('missions_in_record', 0)} of {scope.get('missions_in_course', 0)}",
        f"- **Outside reviewer:** {body.get('reviewer_note', REVIEWER_NONE) if not body.get('reviewer') else body['reviewer'].get('name', '')}",
        "",
        "Every line says who checked it: *Field Academy read it* (Field Academy read the practice profile's files itself), "
        "*the holder's Hermes graded it* (the holder's own Hermes graded it, so it is self-graded), *the holder wrote it* "
        "(the holder's own words), or *Field Academy's course wrote it, and the holder kept it* (a claim in the course's "
        "words). Times are UTC.",
        "",
    ]
    lines += trails_markdown(body.get("trails"))
    lines += passed_markdown(body.get("passed"))
    lines += [
        "## Claims",
        "",
    ]
    for claim in body.get("claims", []):
        lines += [f"### {claim['n']}. {claim['mission_title']}", "", f"**Claim:** {_md(claim['claim'])}{_tag(_claim_tag(claim.get('author')))}", "",
                  f"**Standard, frozen {_when(claim.get('standard_frozen_at'))}:**", ""]
        lines += [f"{i}. {_md(c.get('text', ''))}" for i, c in enumerate(claim.get("standard", []), start=1)] or ["No standard was saved."]
        lines.append("")
        if claim.get("changes"):
            lines += ["**Changed after the freeze:**", ""]
            lines += [f"- {_when(c.get('created_at'))}: {_md(c.get('reason') or c.get('why') or c.get('text') or '')}{_tag(WRITTEN_BY_YOU)}" for c in claim["changes"]]
        else:
            lines.append("No change after the freeze.")
        lines.append("")
    lines += ["## Entries", ""]
    for e in body.get("entries", []):
        level = str(e.get("level") or "").capitalize()
        test_out = e.get("mode") == "test_out"
        lines += [f"### Entry {e['n']}: {e['mission_title']}", "",
                  f"Try {e.get('attempt_no')}, {level}{', a test-out' if test_out else ''}. Added {_when(e.get('added_at'))}.", "",
                  "| Check | Predicted | Self-scored | First result | After the fix | Checked by |",
                  "|---|---|---|---|---|---|"]
        for c in e.get("checks", []):
            expected = "pass" if c.get("expect_pass") is True else "fail" if c.get("expect_pass") is False else ""
            if expected and c.get("confidence") is not None:
                expected += f" ({c['confidence']}% sure)"
            first = _yes_no(c.get("passed")) + (f", level {c['level']} of 4" if c.get("level") else "")
            lines.append(f"| {_cell(c.get('text'))} | {expected} | {_yes_no(c.get('self_pass')) if c.get('self_pass') is not None else ''} | "
                         f"{first} | {_yes_no(c.get('passed_after_fix'))} | {_cell(_words(c.get('checked_by')))} |")
        lines.append("")
        if test_out and e.get("tested_out"):
            graded = " and the explanation's first grade passed" if (e.get("explain") or {}).get("level") else ""
            lines.append(f"- **Tested out:** every check passed on the first run (the hidden planted-problem check "
                         f"included){graded}, so the holder skipped the recall, the fix and "
                         f"the transfer. The lesson was optional.{_tag(READ_BY_FA)}")
        if isinstance(e.get("first_flight"), dict):
            lines.append(f"- **{_md(e['first_flight'].get('words', 'Began as a first flight'))}.** Recall and the claim "
                         f"were skipped; the course's standard stood.{_tag(READ_BY_FA)}")
        elif test_out and not e.get("tested_out"):
            lines.append(f"- **This try began as a test-out.** A check missed on the first run, so the holder finished the "
                         f"mission the usual way, with the fix and the transfer. Recall was skipped.{_tag(READ_BY_FA)}")
        if e["where_wrong"]["text"]:
            lines.append(f"- **Where the holder expected to slip:** {_md(e['where_wrong']['text'])}{_tag(WRITTEN_BY_YOU)}")
        lines.append(f"- **Live checks, first run:** {_count(e.get('result_first'))}{_tag(READ_BY_FA)}")
        lines.append(f"- **Live checks after the fix:** {_count(e.get('result_after_fix'))}{_tag(READ_BY_FA)}")
        lines.append(f"- **Transfer checks:** {_count(e.get('transfer'))}{_tag(READ_BY_FA)}")
        one_off = (e.get("transfer") or {}).get("one_off")
        if one_off:
            lines.append(f"- **Save or skip:** {'saved' if one_off.get('saved') else 'left out'}: \"{_md(one_off.get('detail', ''))}\"{_tag(READ_BY_FA)} "
                         f"Why: {_md(one_off.get('why', ''))}{_tag(one_off.get('why_checked_by', WRITTEN_BY_YOU))}")
        explain = e.get("explain") or {}
        if explain.get("level"):
            lines.append(f"- **Explain it:** level {explain['level']} of 4, pass at {explain.get('pass_level', 3)}{_tag(GRADED_BY_HERMES)}")
        else:
            lines.append("- **Explain it:** not graded")
        for plant in e.get("caught", []):
            lines.append(f"- **Caught:** {_md(plant.get('title', plant.get('kind', '')))}{_tag(READ_BY_FA)}")
        for plant in e.get("missed", []):
            lines.append(f"- **Missed:** {_md(plant.get('title', plant.get('kind', '')))}{_tag(READ_BY_FA)}")
        for key, label in (("gap", "What the holder found wrong"), ("diagnosis", "Why"), ("fix", "The fix")):
            if e[key]["text"]:
                lines.append(f"- **{label}:** {_md(e[key]['text'])}{_tag(WRITTEN_BY_YOU)}")
        lines += ["", "**Evidence:** each excerpt says which check it backs and what the check found when it read it.", ""]
        for ev in e.get("evidence", []):
            where = f"`{ev['excerpt_file']}`" if ev.get("excerpt_file") else "withheld by the holder; only its fingerprint is kept"
            back = ev.get("backs") or {"label": "Backs a check Field Academy ran", "text": "on the practice profile."}
            text = _md(back.get("text") or "")
            found = _facts_words(ev.get("facts"))
            # A withheld excerpt keeps its whole fingerprint here, since that is all of it the record holds.
            sha = str(ev.get("sha256", ""))
            print_sha = f"SHA-256 `{sha}`." if ev.get("withheld") else f"SHA-256 `{sha[:12]}` (in full in record.json)."
            lines.append(f"- **{back.get('label', 'Backs')}:** {text}{'' if text.endswith('.') else '.'} "
                         f"{KIND_WORDS.get(ev.get('kind', ''), KIND_DEFAULT)} From {_code(ev.get('file', ''))}, read {_when(ev.get('read_at'))}."
                         f"{f' What the check found: {found}.' if found else ''} {print_sha} {where}{_tag(READ_BY_FA)}")
            if ev.get("excerpt") and not ev.get("withheld"):
                # The fence is longer than any run of backticks in the excerpt, so text read from a practice profile
                # can't close it and write its own lines into the record.
                fence = "`" * max(3, max((len(run) for run in re.findall(r"`+", str(ev["excerpt"]))), default=0) + 1)
                lines += ["", "  " + fence, *("  " + x for x in str(ev["excerpt"]).splitlines() or [""]), "  " + fence, ""]
        if not e.get("evidence"):
            lines.append("- No excerpt was kept.")
        questions = ask_holder(e)
        if questions:
            lines += ["", "**Ask the holder:**", ""] + [f"- {q}" for q in questions]
        prev = e.get("prev_hash")
        lines += ["", f"Entry fingerprint `{str(e.get('entry_hash', ''))[:12]}`, which follows "
                  f"{f'`{prev[:12]}`' if prev else 'nothing (the first entry)'}. The full fingerprints are in record.json.", ""]
        for c in e.get("corrections", []):
            lines += [f"**Correction, {_when(c.get('added_at'))}:** {_md(c.get('text', ''))}{_tag(WRITTEN_BY_YOU)}", ""]
    cal = body.get("calibration") or {}
    lines += ["## How the holder's self-judgment moved", "", cal.get("note", CALIBRATION_NOTE), "",
              "| Mission | Checks | Predicted to pass | Self-scored as passed | Passed the first time |", "|---|---|---|---|---|"]
    for row in cal.get("per_mission", []):
        if row.get("in_record"):
            lines.append(f"| {_cell(row['title'])} | {row['checks']} | {row['predicted']} | {row['self_scored']} | {row['passed_first']} |")
        else:
            lines.append(f"| {_cell(row['title'])} | not in the record | | | |")
    lines += ["", _tag(READ_BY_FA).strip(), ""]
    fl = body.get("first_and_last") or {}
    lines += ["## First and last", "", fl.get("note", ""), ""]
    for label, side in (("First", fl.get("first")), ("Latest", fl.get("last"))):
        if side:
            lines.append(f"- **{label}, {side['mission_title']} ({_when(side['added_at'])}):** what the holder found wrong: "
                         f"{_md(side['found_wrong']) or 'nothing written'}{_tag(WRITTEN_BY_YOU)} Planted problems caught {side['caught']}, "
                         f"missed {side['missed']}; live checks on the first run {_count(side['first_result'])}{_tag(READ_BY_FA)}")
    lines += ["", "## What the holder can now claim", ""]
    can = body.get("can_claim") or {}
    for item in can.get("passed", []):
        after = " Passed after a fix." if item.get("after_fix") else " Tested out." if item.get("tested_out") else ""
        lines.append(f"- {_md(item['claim'])} ({item['title']}, {_date(item['date'])}, entry {item['entry']}).{after}{_tag(READ_BY_FA)}")
    if not can.get("passed"):
        lines.append("- Nothing yet. A claim goes here once every check on it has passed.")
    lines += ["", "**Not yet:**", ""]
    lines += [f"- {item['title']}: {item['why']}" for item in can.get("not_yet", [])] or ["- Nothing."]
    lines += ["", "Each claim is only as strong as the evidence under it.", "",
              "## A case for a stranger", "", (body.get("case") or {}).get("text") or NO_CASE, "",
              "## What this record doesn't show, in the holder's words", "", (body.get("limits") or {}).get("text", ""), "",
              "## Outside reviewer", "", body.get("reviewer_note", REVIEWER_NONE) if not body.get("reviewer") else
              f"{body['reviewer'].get('name', '')}: {body['reviewer'].get('saw', '')}", "",
              "## What this record shows", "", body.get("shows", SHOWS), "", f"**What it doesn't show:** {body.get('does_not_show', DOES_NOT_SHOW)}", "",
              f"Chain head `{str(body.get('chain_head', ''))[:12]}`, over {_plural((body.get('chain') or {}).get('entries', 0), 'entry', 'entries')}, corrections included. "
              "Each entry's fingerprint covers the one before it, so a removed or edited entry shows.", "",
              "README.txt in this folder says how to check the files.", "",
              body.get("disclaimer", DISCLAIMER), ""]
    return "\n".join(lines)


def readme_text(body) -> str:
    holder = (body.get("scope") or {}).get("holder", {}).get("name", "")
    number = body.get("number", "")
    return f"""FIELD ACADEMY FIELD RECORD: HOW TO CHECK IT

This folder holds a Field Record for {holder}, saved {_date(body.get('issued_at'))}.
Record number: {number}

WHAT'S IN THIS FOLDER

  record.md         The record, to read. Any text viewer opens it.
  record.json       The same record as data. The record number is made from it.
  evidence/         Short excerpts Field Academy read from practice profiles on the
                    holder's computer. Secrets were removed before they were saved.
  MANIFEST.sha256   A fingerprint (SHA-256) of every other file in this folder.
  README.txt        This file.

WHO MADE IT

The holder made this record with Field Academy, a free plugin for Hermes Agent by
Damon Gardenhire. It is not an official certificate. Nous Research didn't issue,
review or endorse it.

CHECK THAT NO FILE CHANGED

On a Mac or Linux, open a terminal in this folder and run:

    shasum -a 256 -c MANIFEST.sha256

On Linux, sha256sum -c MANIFEST.sha256 does the same. Every line should end in OK.

On Windows, open PowerShell in this folder and run:

    Get-FileHash -Algorithm SHA256 record.json

Compare the hash with the record.json line in MANIFEST.sha256 (case doesn't matter).
Do the same for each file you want to check.

CHECK THE RECORD NUMBER

The number is the first 12 characters of a SHA-256 over record.json without its
"number" line, written with sorted keys and no spaces. With Python 3, in this folder:

    python3 -c "import json,hashlib;b=json.load(open('record.json',encoding='utf-8'));n=b.pop('number');d=hashlib.sha256(json.dumps(b,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:12].upper();print(n,'FA-'+d[:4]+'-'+d[4:8]+'-'+d[8:])"

The two numbers it prints should match.

CHECK AN EXCERPT

Each excerpt in record.json has a sha256 and an excerpt_file. The file in evidence/
with that name has the same fingerprint, and MANIFEST.sha256 lists it too.
An excerpt the holder chose to keep private says "withheld". Its fingerprint stays in
the record, but its text isn't in this folder.

WHAT THESE CHECKS PROVE, AND WHAT THEY DON'T

They show the files match each other: each file matches its line in MANIFEST.sha256,
and the record number matches record.json. That catches a file damaged or changed by
accident.

They don't show the folder is the one the holder saved. Anyone who edits a file can
write a new MANIFEST.sha256 and work out a new number, and the checks pass again. To
know you have the folder as saved, compare the record number with one the holder gave
you earlier by another route (for example in an email sent when the record was saved).

They don't prove Hermes produced them. The holder's computer made every file, and
anyone with Field Academy's source could make a folder like this one.

Each line in record.md says who checked it:
  "Field Academy read it"          Field Academy read the practice profile's files
                                   itself.
  "the holder's Hermes graded it"  The holder's own Hermes graded it. That is
                                   self-grading, so weigh it that way.
  "the holder wrote it"            The holder's own words.

Nobody outside reviewed this record unless the record names them.

The strongest check is to ask the holder to walk you through one entry and show you
the practice profile it came from.
"""
