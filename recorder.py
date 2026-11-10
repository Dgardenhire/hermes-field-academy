"""Replay your run: the learner's practice chat and what the first check read in Hermes's files, on one time line.

``replay(attempt_id, step)`` is the payload ``GET /replay/{attempt_id}`` returns; ``timeline(attempt_id, reveal)`` is
the event list the Field guide reads (nudge, Ask, pins). Two lanes:

* **In your chat** comes from the practice profile's ``state.db`` (``hermes_read.messages``, read-only), every message
  since the attempt's ``frozen_at``. A tool row carries the title the app shows for it ("Saved to memory" for a memory
  row, from Hermes Desktop's ``apps/desktop/src/i18n/en.ts``) and, once revealed, the tool's own result line.
* **In Hermes's files** comes from the FROZEN evidence of the first check run: the ``f_evidence`` rows it kept (a held
  save in ``pending/``) and the ``MEMORY.md`` fill it read (``f_checks.facts_json``). So the replay shows what the
  check read, never a later state of the folder.

The snag is found from the tool result's ``staged`` flag (Hermes's ``tools/memory_tool.py:99`` returns
``{"success": true, "staged": true, "pending_id": ..., "message": "Staged for approval (memory.write_approval is on).
Not yet saved — review with /memory pending."}``), never from the row's title, which says "Saved to memory"
either way. The bracket joins that chat row to the held save in the files lane.

Before Compare the route answers ``state: "not_ready"`` with no events: the files lane and the staged line would
give the snag away during the hunt. ``timeline(..., reveal=False)`` (the nudge's input) is the chat lane only, with
tool rows by title and time and no result text, the same plant-free shape the nudge has always had.

Everything here reads; nothing writes to a practice profile. Every text is scrubbed and clipped.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from . import foundations, hermes_read, practice, scrub

_log = logging.getLogger("hermes.plugins.field_academy")

LANES = [{"id": "chat", "label": "In your chat"}, {"id": "files", "label": "In Hermes's files"}]
EXPECTED_COLUMNS = ("id", "session_id", "role", "content", "tool_name", "timestamp")
MAX_EVENTS = 80
TEXT = 240
BRACKET_WORDS = ("The chat showed Saved to memory, but the note is waiting for your approval and is not in "
                 "MEMORY.md.")
ROOM_WORDS = ("The chat showed Saved to memory, but to make room Hermes deleted a note the practice jobs rely on.")
WORDS = {
    "empty": "Your replay fills in once you chat in your practice Hermes. Until then, watch a sample run.",
    "schema_changed": "Hermes changed how it stores chats. Your checks still work.",
    "not_ready": "Your replay opens on Compare, once the first check has run.",
    "unreadable": "Field Academy can't read your practice chat right now. Your checks still work.",
}
# The title Hermes Desktop gives a finished tool row (apps/desktop/src/i18n/en.ts, the tool "done" strings). Memory is
# the one the course depends on; other tools get a plain fallback.
TOOL_TITLES = {"memory": "Saved to memory", "skill_manage": "Saved a skill", "skills_list": "Listed skills",
               "read_file": "Read a file", "write_file": "Wrote a file", "terminal": "Ran a command"}
SAMPLE = Path(__file__).resolve().parent / "content" / "sample_run.json"


# ---------------------------------------------------------------- helpers --


def _epoch(stamp) -> float:
    if isinstance(stamp, (int, float)) and not isinstance(stamp, bool):
        return float(stamp)
    try:
        return datetime.fromisoformat(str(stamp)).timestamp()
    except (TypeError, ValueError):
        return 0.0


def _clip(value, limit=TEXT) -> str:
    return scrub.clip(" ".join(str(value or "").split()), limit)


def _tool_failed(content) -> bool:
    """Hermes's own result said the write failed (``"success": false``, e.g. memory over its limit)."""
    raw = str(content or "").strip()
    try:
        data = json.loads(raw) if raw.startswith("{") else None
    except ValueError:
        return False
    return isinstance(data, dict) and data.get("success") is False


def _tool_result(content):
    """``(text, staged)`` from a tool row's content: the result's own line (``message``, else ``usage``, else
    ``error``) and whether Hermes said it staged the write. Content that isn't JSON is shown as written."""
    raw = str(content or "").strip()
    try:
        data = json.loads(raw) if raw.startswith("{") else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return _clip(raw), False
    staged = data.get("staged") is True
    line = data.get("message") or data.get("error") or ""
    if not line and data.get("usage"):
        line = f"Saved. Memory is {data['usage']}." if data.get("success") else str(data["usage"])
    return _clip(line or raw), staged


def _tool_title(name: str) -> str:
    """The app's title, which does not change for a staged save: that is the snag."""
    return TOOL_TITLES.get(name, f"Used {name}" if name else "Used a tool")


# ------------------------------------------------------------- chat lane --


def _columns_ok(home) -> bool:
    conn = hermes_read._db(home, "state.db")
    if conn is None:
        return True  # no state.db at all is the empty state, not a schema change
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "messages" not in tables:
            return False
        have = set(hermes_read._columns(conn, "messages"))
        return all(c in have for c in EXPECTED_COLUMNS)
    except Exception:  # noqa: BLE001 - a table we can't even list is a changed store
        return False
    finally:
        conn.close()


def _chat_lane(attempt, reveal: bool) -> dict:
    """``{"state", "events"}`` for the chat lane. ``state`` is ``ready``, ``empty``, ``schema_changed`` or
    ``unreadable``."""
    name = attempt.get("profile") or ""
    row = practice.record(name) if name else None
    if not row or not practice.is_ours(row):
        return {"state": "empty", "events": []}
    home = row["path"]
    if not _columns_ok(home):
        return {"state": "schema_changed", "events": []}
    found = hermes_read.messages(home, limit=600)
    if not found.get("readable"):
        why = str(found.get("why") or "")
        return {"state": "empty" if "No chat records" in why else "unreadable", "events": []}
    since = _epoch(attempt.get("frozen_at")) - 5
    out, sessions_seen = [], set()
    for m in found["messages"]:
        try:
            at = float(m.get("timestamp") or 0)
        except (TypeError, ValueError):
            at = 0.0
        if since > 0 and at and at < since:
            continue
        session = str(m.get("session_id") or "")
        if session and session not in sessions_seen:
            sessions_seen.add(session)
            if len(sessions_seen) > 1:
                out.append({"event_id": f"c{m.get('id')}", "lane": "chat", "at": at, "kind": "chat:new",
                            "title": "A new chat started", "text": ""})
        role = str(m.get("role") or "")
        event = {"event_id": f"m{m.get('id')}", "lane": "chat", "at": at}
        if role == "tool":
            tool = scrub.scrub(m.get("tool_name") or "tool", 40)
            text, staged = _tool_result(m.get("content"))
            event.update(kind=f"tool:{tool}", title=_tool_title(tool), text=text if reveal else "")
            if reveal:
                event["staged"] = staged
                event["failed"] = _tool_failed(m.get("content"))
        elif role == "assistant" and not str(m.get("content") or "").strip() and m.get("tool_calls"):
            names = list(dict.fromkeys(re.findall(r'"name"\s*:\s*"([\w.-]+)"', str(m.get("tool_calls")))))
            event.update(kind="assistant", title="Hermes called " + (", ".join(names) or "a tool"),
                         text=f"(called {', '.join(names) or 'a tool'})")
        elif role == "user":
            event.update(kind="user", title="You asked", text=_clip(m.get("content")))
        else:
            event.update(kind=role or "assistant", title="Hermes answered", text=_clip(m.get("content")))
        out.append(event)
    out = out[-MAX_EVENTS:]
    return {"state": "ready" if out else "empty", "events": out}


# ------------------------------------------------------------ files lane --


def first_run_evidence(conn, attempt_id) -> list:
    """The ``f_evidence`` rows the first check run kept: those read from its first row's time up to (not including) the
    next run's. A later run's reads never show in the replay."""
    rows = [dict(r) for r in conn.execute("SELECT * FROM f_checks WHERE attempt_id = ? AND source = 'practice_profile' ORDER BY id",
                                          (int(attempt_id),))]
    first = [r for r in rows if r["phase"] == "first"]
    if not first:
        return []
    start = min(r["created_at"] for r in first)
    later = [r["created_at"] for r in rows if r["phase"] != "first" and r["created_at"] > max(x["created_at"] for x in first)]
    stop = min(later) if later else None
    out = []
    for r in conn.execute("SELECT * FROM f_evidence WHERE attempt_id = ? ORDER BY id", (int(attempt_id),)):
        if r["read_at"] < start or (stop is not None and r["read_at"] >= stop):
            continue
        out.append(dict(r))
    return out


def _meter(value: str):
    """``{"used", "limit"}`` from a fill line such as "479 of 2,200 characters, 5 lines"."""
    m = re.match(r"\s*([\d,]+) of ([\d,]+) characters", str(value or ""))
    if not m:
        return None
    return {"used": int(m.group(1).replace(",", "")), "limit": int(m.group(2).replace(",", ""))}


def _pending_created_at(home, rel_path: str, excerpt: str):
    """The held save's own ``created_at``, read from its record while it is still there and still the same save."""
    if not home or not rel_path.startswith("pending/"):
        return None
    path = hermes_read.safe_path(home, rel_path)
    if path is None or not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or hermes_read.pending_words(record)[:40] != str(excerpt or "")[:40]:
        return None
    stamp = record.get("created_at")
    return float(stamp) if isinstance(stamp, (int, float)) and not isinstance(stamp, bool) else None


def _files_lane(conn, attempt, chat_events) -> list:
    checks = [dict(r) for r in conn.execute(
        "SELECT * FROM f_checks WHERE attempt_id = ? AND phase = 'first' AND source = 'practice_profile' ORDER BY id", (int(attempt["id"]),))]
    if not checks:
        return []
    read_at = _epoch(max(r["created_at"] for r in checks))
    row = practice.record(attempt["profile"]) if attempt.get("profile") else None
    home = row["path"] if row and practice.is_ours(row) else None
    staged_rows = [e for e in chat_events if e.get("staged")]
    out = []
    n = 0
    made_room = _made_room(chat_events)
    removed = 0
    for ev in first_run_evidence(conn, attempt["id"]):
        if ev["kind"] == "removed_note":
            if any(o["kind"] == "file:removed" and o["text"] == _clip(ev["excerpt"]) for o in out):
                continue  # the check reads it once per run, but a re-read keeps a second row
            # A note the page listed is gone (memory_full): Hermes deleted it to fit the new save. Placed at the save
            # that followed the refused one, since that is when Hermes made room; else at the first check.
            removed += 1
            out.append({"event_id": f"f-removed-{removed}", "lane": "files", "at": made_room["at"] if made_room else read_at,
                        "kind": "file:removed", "title": "A note was deleted", "text": _clip(ev["excerpt"]),
                        "path": ev["rel_path"], "at_source": "the save that made room" if made_room else "the first check",
                        "read_at": read_at})
            continue
        if ev["kind"] != "pending":
            continue  # tool results are the chat lane's; memory lines show in the meter below
        n += 1
        at = _pending_created_at(home, ev["rel_path"], ev["excerpt"])
        at_source = "the held save's own record"
        if at is None and staged_rows:
            at, at_source = staged_rows[min(n, len(staged_rows)) - 1]["at"], "the chat row that staged it"
        if at is None:
            at, at_source = read_at, "the first check"
        out.append({"event_id": f"f-pending-{n}", "lane": "files", "at": at, "kind": "file:pending",
                    "title": "Held for your approval", "text": _clip(ev["excerpt"]), "path": ev["rel_path"],
                    "at_source": at_source, "read_at": read_at})
    memory_row = next((r for r in checks if r["check_id"] == "memory_line"), None)
    if memory_row is not None:
        facts = json.loads(memory_row["facts_json"] or "{}")
        fill = next((f.get("value") for f in facts.get("facts") or [] if isinstance(f, dict) and f.get("label") == "MEMORY.md"), "")
        meter = _meter(fill)
        if meter is not None:
            seeds = practice.seed_notes(attempt["profile"]).get("notes") if attempt.get("profile") else None
            seed_chars = len(hermes_read.DELIM.join(seeds)) if seeds else None
            changed = bool(memory_row["passed"]) if seed_chars is None else meter["used"] != seed_chars
            at = out[0]["at"] if out else (staged_rows[0]["at"] if staged_rows else read_at)
            out.append({"event_id": "f-memory", "lane": "files", "at": at, "kind": "file:memory",
                        "title": "MEMORY.md changed" if changed else "MEMORY.md unchanged",
                        "text": f"{meter['used']:,} of {meter['limit']:,} characters, as the check read it.",
                        "path": "memories/MEMORY.md", "meter": {**meter, "changed": changed}, "read_at": read_at})
    return out


# ------------------------------------------------------------------- api --


def _compare_reached(entries, checks, step: str) -> bool:
    first = [r for r in checks if r["phase"] == "first" and r["source"] == "practice_profile"]
    return bool(first) and (step in ("compare", "fix", "record") or any(e["kind"] == "gap_note" for e in entries))


def timeline(attempt_id, reveal: bool = False) -> dict:
    """``{"state", "events"}``. With ``reveal`` False (before Compare): the chat lane only, tool rows with no result
    text and no ``staged`` flag. With ``reveal`` True: both lanes, sorted by time, chat before files at a tie."""
    with foundations._conn() as conn:
        attempt = foundations._attempt(conn, attempt_id)
        chat = _chat_lane(attempt, reveal)
        files = _files_lane(conn, attempt, chat["events"]) if reveal and chat["state"] in ("ready", "empty") else []
    events = chat["events"] + files
    events.sort(key=lambda e: (e.get("at") or 0, 0 if e["lane"] == "chat" else 1))
    return {"state": chat["state"], "events": events}


def _made_room(chat_events):
    """The memory save that worked right after one Hermes said failed: where it made room. ``None`` without one."""
    refused = False
    for e in chat_events:
        if e.get("kind") != "tool:memory":
            continue
        if e.get("failed"):
            refused = True
        elif refused:
            return e
    return None


def bracket(events):
    """The amber bracket, joining the chat row that looked fine to the file that shows otherwise. A staged save: the
    first row Hermes marked ``staged`` and the first held save. Memory full: the save that made room and the note it
    deleted. ``None`` when the run has neither."""
    src = next((e for e in events if e.get("lane") == "chat" and e.get("staged") is True), None)
    dst = next((e for e in events if e.get("kind") == "file:pending"), None)
    if src is not None and dst is not None:
        return {"from": src["event_id"], "to": dst["event_id"], "words": BRACKET_WORDS}
    src = _made_room([e for e in events if e.get("lane") == "chat"])
    dst = next((e for e in events if e.get("kind") == "file:removed"), None)
    if src is not None and dst is not None:
        return {"from": src["event_id"], "to": dst["event_id"], "words": ROOM_WORDS}
    return None


def replay(attempt_id, step: str = "") -> dict:
    """The ``GET /replay/{attempt_id}`` payload (shape in docs/ai-calls.md)."""
    with foundations._conn() as conn:
        attempt = foundations._attempt(conn, attempt_id)
        entries = foundations._entries(conn, attempt_id)
        checks = foundations._checks(conn, attempt_id)
    base = {"attempt_id": int(attempt["id"]), "mission_id": attempt["mission_id"], "lanes": LANES, "bracket": None,
            "snag_found_from": "staged_flag", "events": [], "started_at": None, "ended_at": None, "words": ""}
    if not _compare_reached(entries, checks, str(step or "")):
        return {**base, "state": "not_ready", "words": WORDS["not_ready"]}
    found = timeline(attempt_id, reveal=True)
    if found["state"] in ("schema_changed", "unreadable"):
        return {**base, "state": found["state"] if found["state"] == "schema_changed" else "unreadable",
                "words": WORDS[found["state"]], "events": [e for e in found["events"] if e["lane"] == "files"]}
    if not any(e["lane"] == "chat" for e in found["events"]):
        return {**base, "state": "empty", "words": WORDS["empty"]}
    events = found["events"]
    times = [e["at"] for e in events if e.get("at")]
    joined = bracket(events)
    found_from = "removed_note" if joined and joined["words"] == ROOM_WORDS else "staged_flag"
    return {**base, "state": "ready", "events": events, "bracket": joined, "snag_found_from": found_from,
            "started_at": min(times) if times else None, "ended_at": max(times) if times else None}


def sample() -> dict:
    """The committed sample run (``content/sample_run.json``), labelled as a sample. A live recording replaces it."""
    try:
        return json.loads(SAMPLE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"state": "empty", "words": "The sample run isn't in this copy of Field Academy.", "label": "", "events": [],
                "lanes": LANES, "bracket": None}


def mount(router, guard) -> None:
    @router.get("/replay/sample")
    async def replay_sample():
        return sample()

    @router.get("/replay/{attempt_id}")
    async def replay_get(attempt_id: int, step: str = ""):
        return guard(replay, attempt_id, step)


__all__ = ["timeline", "replay", "bracket", "sample", "mount", "first_run_evidence", "LANES", "WORDS"]
