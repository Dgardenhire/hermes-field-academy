"""The Field guide column's backend: Find out why (Give me a hint, Show me where to look, Show me the answer), Why did this miss?,
replay pins, Do it with me, Ask, starter questions, the help entries and the off states.

Rules this file keeps (plan row 6, the AI lane brief, the security rails):

* **Before Compare, the model never sees the planted problem.** Every context here is built by code from the
  learner's practice-chat events and the visible check results; nothing reads ``f_attempts.plants_json`` or
  ``practice.planted`` into a model input until the learner is on Compare. Tool rows go in as their tool name and
  time only, never their output text, so a tool result can't hand the model the answer either.
* **Give-away words.** A nudge or an Explain my miss line before Compare is checked against the give-away list of every
  snag the mission can plant (``_guide_text.GIVEAWAYS``). A hit gets the one repair try ``ai.call`` allows; a second
  hit falls back to the course's own words, labelled as the course's.
* **Prefetch.** Reading the guide on Check right after a missed first check starts the nudge and Explain my miss calls
  on a background thread and caches the results in the plugin's data folder, so **Give me a hint** answers from the cache.
  Nothing starts while the page says the practice profile is the active one (``active=practice``).
* **Help is recorded.** Every help the learner uses is an append-only ``help`` entry in the attempt's hash chain. The
  record reads "No hints used" or "One hint used" from them (``help_summary``).
* **The model acts on nothing.** Do it with me's commands are fixed in code and only drafted by the page. Pins on an
  event that isn't in the timeline are dropped. Ask's sentences that cite a source that wasn't given are dropped.
* **Off states.** Off in test-out and when AI help is off; the view says which, so the page can say why.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime
from importlib import import_module

from . import ai, foundations, foundations_content, hermes_read, practice, runtime, scrub, store
from .content.foundations import _guide_text as text

_log = logging.getLogger("hermes.plugins.field_academy")

STEPS_WITH_STARTERS = ("check", "compare", "fix")
HELP_KINDS = {1: "nudge", 2: "where", 3: "reveal"}
ACTIONS = ("explain", "do_it_with_me", "ask", "pins")
MAX_EVENTS = 60
EVENT_TEXT = 160

OFF_WORDS = {
    "switch": "AI help is off. Turn it on to get hints and explanations. Checks work either way.",
    "test_out": "The Field guide is off while you test out, so the result is all yours.",
    "first_flight_locked": "The Field guide opens after you answer Did it work?",
}
FIRST_FLIGHT = "first_flight"

_cache_lock = threading.Lock()
_inflight: set = set()


# ---------------------------------------------------------------- helpers --


def _mission_snags(mission_id: str) -> tuple:
    return text.MISSION_SNAGS.get(mission_id, ())


def giveaways_in(reply_text: str, mission_id: str) -> list:
    """Every give-away word of every snag this mission can plant that appears in ``reply_text`` (whole words, any case,
    plain plural and past forms)."""
    found = []
    low = str(reply_text or "").lower()
    for snag in _mission_snags(mission_id):
        for word in text.GIVEAWAYS.get(snag, ()):
            if re.search(r"(?<![\w])" + re.escape(word.lower()) + r"(?:s|es|ed|d|ing)?(?![\w])", low):
                found.append(word)
    return found


def _clock(at) -> str:
    """``HH:MM`` in local time, from an epoch number or an ISO string; ``""`` when it can't be read."""
    try:
        if isinstance(at, (int, float)) or re.fullmatch(r"\d+(?:\.\d+)?", str(at or "")):
            return datetime.fromtimestamp(float(at)).strftime("%H:%M")
        return datetime.fromisoformat(str(at)).astimezone().strftime("%H:%M")
    except (TypeError, ValueError, OSError, OverflowError):
        return ""


def _epoch(stamp) -> float:
    try:
        return datetime.fromisoformat(str(stamp)).timestamp()
    except (TypeError, ValueError):
        return 0.0


def _attempt_and_mission(attempt_id):
    with foundations._conn() as conn:
        attempt = foundations._attempt(conn, attempt_id)
        entries = foundations._entries(conn, attempt_id)
        checks = foundations._checks(conn, attempt_id)
        test_out = foundations._is_test_out(conn, attempt_id)
    return attempt, foundations._mission(attempt["mission_id"]), entries, checks, test_out


def _first_run(checks) -> list:
    return [r for r in checks if r["phase"] == "first" and r["source"] == "practice_profile"]


def _latest_phase(checks):
    for phase in ("after_fix", "first"):
        rows = [r for r in checks if r["phase"] == phase and r["source"] == "practice_profile"]
        if rows:
            return phase, rows
    return None, []


def _visible_results(mission, rows) -> list:
    """The visible checks of one run, as the page shows them: id, label, passed, the facts read, what's missing."""
    specs = {c["id"]: c for c in mission.get("live_checks", [])}
    latest = {}
    for r in rows:
        latest[r["check_id"]] = r
    out = []
    for check_id, r in latest.items():
        if not specs.get(check_id, {}).get("visible", True):
            continue
        facts = json.loads(r["facts_json"] or "{}")
        out.append({"id": check_id, "passed": bool(r["passed"]), "title": facts.get("title", ""), "detail": facts.get("detail", ""),
                    "facts": facts.get("facts", []), "missing": facts.get("missing", [])})
    return out


def _compare_reached(entries, checks, step: str) -> bool:
    """Compare is open: the first check ran and the learner is on Compare or past it (the gap note is Compare's work)."""
    if not _first_run(checks):
        return False
    return step in ("compare", "fix") or any(e["kind"] == "gap_note" for e in entries)


# ----------------------------------------------------------------- events --


def events(attempt, reveal: bool = False) -> list:
    """The run as ``[{event_id, at, lane, kind, title, text, ...}]``: ``recorder.timeline`` when it is in this checkout,
    else Field Academy's own read of the practice profile's ``state.db`` (read-only, scrubbed).

    ``reveal`` False (before Compare): the chat lane only, tool rows by title and time with no result text. ``reveal``
    True (Compare on): both lanes, the tool rows' own result lines and ``staged`` flags, and the frozen files lane."""
    try:
        recorder = import_module(f"{__package__}.recorder")
    except ImportError:
        recorder = None
    if recorder is not None and hasattr(recorder, "timeline"):
        try:
            found = recorder.timeline(attempt["id"], reveal=bool(reveal))
            if isinstance(found, dict):
                found = found.get("events", [])
            return [e for e in found if isinstance(e, dict) and e.get("event_id")]
        except Exception:
            _log.exception("field-academy: the replay timeline could not be read; using the chat alone")
    return _chat_events(attempt)


def _chat_events(attempt) -> list:
    name = attempt.get("profile") or ""
    row = practice.record(name) if name else None
    if not row or not practice.is_ours(row):
        return []
    found = hermes_read.messages(row["path"], limit=400)
    if not found.get("readable"):
        return []
    since = _epoch(attempt.get("frozen_at")) - 5
    out = []
    for m in found["messages"]:
        try:
            at = float(m.get("timestamp") or 0)
        except (TypeError, ValueError):
            at = 0.0
        if since > 0 and at and at < since:
            continue
        role = str(m.get("role") or "")
        if role == "tool":
            kind, body = f"tool:{scrub.scrub(m.get('tool_name') or 'tool', 40)}", ""
        elif role == "assistant" and not str(m.get("content") or "").strip() and m.get("tool_calls"):
            names = re.findall(r'"name"\s*:\s*"([\w.-]+)"', str(m.get("tool_calls")))
            kind, body = "assistant", f"(called {', '.join(dict.fromkeys(names)) or 'a tool'})"
        else:
            kind, body = role, scrub.clip(" ".join(str(m.get("content") or "").split()), EVENT_TEXT)
        out.append({"event_id": f"m{m.get('id')}", "at": at, "lane": "chat", "kind": kind, "text": body})
    return out[-MAX_EVENTS:]


HIDDEN_RESULT = "(what it returned isn't listed here; the row in the chat shows it)"


def _event_body(e) -> str:
    """An event's text for a hunt-time model input. A tool row has no result text before Compare; it says so, with the
    row's title as the app shows it, so the model never reads the missing text as "the tool returned nothing"
    (Loop 2's first real run: "At 03:53, the memory step came back blank")."""
    body = scrub.clip(str(e.get("text") or ""), EVENT_TEXT)
    if str(e.get("kind", "")).startswith("tool:") and not body:
        title = scrub.clip(str(e.get("title") or ""), 60)
        return (f"row titled \"{title}\" " if title else "") + HIDDEN_RESULT
    return body


def _events_for_model(found) -> str:
    lines = []
    for e in found[-MAX_EVENTS:]:
        clock = _clock(e.get("at"))
        lane = "chat" if e.get("lane", "chat") == "chat" else "files"
        lines.append(f"{e['event_id']} | {clock or '--:--'} | {lane} | {e.get('kind', '')} | {_event_body(e)}")
    return "\n".join(lines) if lines else "(no chat events yet)"


def _results_for_model(results) -> str:
    lines = []
    for r in results:
        facts = "; ".join(f"{f.get('label', '')}: {f.get('value', '')}" if isinstance(f, dict) else str(f) for f in (r.get("facts") or [])[:6])
        lines.append(f"- {r['title'] or r['id']}: {'met' if r['passed'] else 'not met'}. {facts}")
    return "\n".join(lines) if lines else "(no results)"


def _events_for_pins(found) -> str:
    """The revealed run for the pins call: every field the screen draws, so a pin can only say what the run shows."""
    lines = []
    for e in found[-MAX_EVENTS:]:
        parts = [e["event_id"], _clock(e.get("at")) or "--:--", "chat" if e.get("lane", "chat") == "chat" else "files",
                 str(e.get("kind", "")), scrub.clip(str(e.get("title") or ""), 60), scrub.clip(str(e.get("text") or ""), EVENT_TEXT)]
        if "staged" in e:
            parts.append("staged: yes" if e["staged"] else "staged: no")
        if e.get("path"):
            parts.append(f"path: {e['path']}")
        if isinstance(e.get("meter"), dict):
            m = e["meter"]
            parts.append(f"fill: {m.get('used')} of {m.get('limit')} characters, {'changed' if m.get('changed') else 'unchanged'}")
        lines.append(" | ".join(parts))
    return "\n".join(lines) if lines else "(no events)"


def word_count(sentence: str) -> int:
    return len(str(sentence or "").split())


def first_sentence(text: str) -> str:
    """Up to the first sentence end outside a quotation: 'The reply says "Saved. Memory is 97%" and...' is one sentence."""
    flat = " ".join(str(text or "").split())
    for m in re.finditer(r"[.!?][\"\u201d']?(?=\s)", flat):
        head = flat[:m.end()]
        if head.count('"') % 2 == 0 and head.count("\u201c") <= head.count("\u201d"):
            return head
    return flat


# ------------------------------------------------------------------ cache --


def _cache_path(attempt_id):
    folder = runtime.data_dir() / "guide-cache"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"attempt-{int(attempt_id)}.json"


def _cache_read(attempt_id) -> dict:
    try:
        return json.loads(_cache_path(attempt_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _cache_put(attempt_id, key, value) -> None:
    with _cache_lock:
        data = _cache_read(attempt_id)
        data[key] = value
        _cache_path(attempt_id).write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _cache_update(attempt_id, key, fn) -> None:
    """Read, change and write one cache key under the lock (parallel Explain calls each write their own item)."""
    with _cache_lock:
        data = _cache_read(attempt_id)
        data[key] = fn(data.get(key))
        _cache_path(attempt_id).write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _now() -> float:
    import time

    return round(time.time(), 1)


def _run_key(rows) -> str:
    return max((r["created_at"] for r in rows), default="")


# ------------------------------------------------------------------ nudge --

NUDGE_SCHEMA = {"type": "object", "required": ["question", "event_id"], "additionalProperties": False,
                "properties": {"question": {"type": "string", "maxLength": 220}, "event_id": {"type": "string", "maxLength": 40}}}

NUDGE_INSTRUCTIONS = (
    "You are the Field guide in Field Academy, a course where a learner did a job in a practice copy of Hermes and a "
    "check just found something isn't right. Don't tell them what is wrong. Ask one short question (25 words or fewer) "
    "that sends them to one moment in their own practice chat to look closer. Name the time of that moment the way it "
    "is written in the list (like 10:41) and what happened then, then tell them what to open and what to read there. "
    "When the moment is a tool row, send them to what the row says came back, and ask whether it says their fact was "
    "really kept; never ask whether it matches what they asked for, because what was sent always matches. Plain words a 13-year-old could read. A tool row in the list shows only its "
    "title and time, not what it returned, so never say what a tool returned, or that it returned nothing.\n\n"
    "Never use these words or any form of them: {banned}.\n\n"
    "Reply with only a JSON object: question (your question) and event_id (the id of the moment you picked, copied from "
    "the list)."
)


def _nudge_inputs(attempt, mission, results, found) -> list:
    return [f"Mission: {mission['title']}\nThe job: {scrub.clip(mission.get('_try_text') or '', 600)}",
            "What the check found (the parts the learner can see):\n" + _results_for_model(results),
            "The learner's practice chat, oldest first (id | time | lane | kind | text):\n" + _events_for_model(found)]


def nudge_context(attempt_id) -> list:
    """The model inputs for a nudge, exactly as sent. Tests read this to prove no plant reaches the model."""
    attempt, mission, _, checks, _ = _attempt_and_mission(attempt_id)
    return _nudge_inputs(attempt, mission, _visible_results(mission, _first_run(checks)), events(attempt))


def _fallback_nudge(mission_id) -> dict:
    return {"state": "ready", "text": text.NUDGE_FALLBACK.get(mission_id, text.NUDGE_FALLBACK["f.memory"]), "source": "course",
            "model": "", "ms": 0, "event_id": ""}


def _make_nudge(attempt, mission, results, found) -> dict:
    mission_id = mission["id"]
    if not found:
        return _fallback_nudge(mission_id)
    ids = {e["event_id"]: e for e in found}
    banned = sorted({w for s in _mission_snags(mission_id) for w in text.GIVEAWAYS.get(s, ()) if "_" not in w})

    def checked(reply):
        event = ids.get(reply.get("event_id", ""))
        if event is None:
            raise ValueError("event_id is not one of the listed ids")
        clock = _clock(event.get("at"))
        if clock and clock not in reply["question"]:
            raise ValueError(f"the question doesn't name the time {clock}")
        hits = giveaways_in(reply["question"], mission_id)
        if hits:
            raise ValueError("it used a word that gives the answer away")

    try:
        out = ai.call(runtime.TASK_GUIDE, instructions=NUDGE_INSTRUCTIONS.format(banned=", ".join(banned)),
                      inputs=_nudge_inputs(attempt, mission, results, found), schema=NUDGE_SCHEMA, schema_name="field_academy_nudge",
                      purpose="nudge", max_tokens=200, validate=checked, attempt_id=attempt["id"])
    except ai.AiFailure as failure:
        if failure.kind == "bad_json":
            return {**_fallback_nudge(mission_id), "fallback_reason": "bad_json"}
        return {"state": failure.kind, "text": "", "message": failure.message, "next_step": failure.next_step,
                "fallback_text": _fallback_nudge(mission_id)["text"], "model": "", "ms": 0}
    reply = out["parsed"]
    return {"state": "ready", "text": reply["question"].strip(), "source": "model", "model": out["model"], "ms": out["ms"],
            "event_id": reply["event_id"], "tokens": out["tokens"]}


# ---------------------------------------------------------------- explain --

EXPLAIN_SCHEMA = {"type": "object", "required": ["sentences"], "additionalProperties": False,
                  "properties": {"sentences": {"type": "array", "minItems": 2, "maxItems": 2,
                                               "items": {"type": "string", "maxLength": 400}}}}
EXPLAIN_WORDS = 20

EXPLAIN_ONE_BEFORE = ("what Hermes needs for this check to pass, as a rule about how Hermes works (for example, a new chat "
                      "can only use a fact that is a line in its memory files). Don't say what the check found: the "
                      "page's headline already says it.")
# After Compare the snag is revealed, so Explain may name the cause (Damon's call, Nov 9: Why did this miss? lives on
# Compare, where it can say why; before Compare it could only restate the headline).
EXPLAIN_ONE_AFTER = ("the cause only, as a fact about what Field Academy changed (given). For example: Field Academy "
                     "turned on approval for memory saves. Stop there: no 'so ...' clause about what happened to the fact, "
                     "because the page's headline already says it. The page's headline already says what Hermes "
                     "claimed and what really happened, so don't just repeat it.")

EXPLAIN_INSTRUCTIONS = (
    "You are the Field guide in Field Academy. A check read the learner's practice copy of Hermes and found something "
    "not met. Using only the facts given, write exactly two short plain sentences a 13-year-old could read, each one 15 "
    "words or fewer. Sentence one: {one} Never say the fact is nowhere, or not written anywhere. Sentence two: where to look next and what to read there, naming one of the places listed "
    "under Places to look, written the way it is written there. Send them nowhere else, and don't guess at causes the "
    "facts don't show.{banned}\n\n"
    "Reply with only a JSON object: sentences (a list of the two sentences)."
)


def explain_places(mission, found, before_compare: bool) -> list:
    """Where a learner can look for this mission's snag, in their own chat and files, as ``[{name, match}]``. The second
    Explain sentence must name one. Mission 3: the memory row in the chat (by its time), MEMORY.md, and after Compare
    the pending folder. Built by code from the run; never from the plant before Compare."""
    if mission["id"] != "f.memory":
        return []
    out = []
    row = next((e for e in found if str(e.get("kind", "")).startswith("tool:memory")), None)
    if row is not None:
        clock = _clock(row.get("at"))
        out.append({"name": f"what the memory row in your chat at {clock} says came back" if clock else "what the memory row in your chat says came back",
                    "match": [m for m in (clock, "memory row") if m]})
    # MEMORY.md is where the fact is missing, so it is a place to look only when the chat has no memory row (Loop 2
    # critics: sending the learner back to the file the check already read adds nothing).
    if row is None:
        out.append({"name": "MEMORY.md in the practice profile", "match": ["MEMORY.md"]})
    if not before_compare:
        out.append({"name": "the pending folder in the practice profile", "match": ["pending"]})
    return out


def _explain_facts(result) -> list:
    """The facts an explanation may use. A zero-line ``USER.md`` reading is left out of every check but the one about
    USER.md: it is true and a dead end, and the model sent learners there (Loop 1)."""
    keep = []
    for f in (result.get("facts") or [])[:8]:
        if isinstance(f, dict) and f.get("label") == "USER.md" and result["id"] != "user_line" and str(f.get("value", "")).startswith("0 of"):
            continue
        keep.append(f)
    return keep


def explain_problems(sentences, result, mission_id, places, before_compare) -> list:
    """Every rule a pair of Explain sentences breaks (an empty list passes)."""
    problems = []
    if len(sentences) != 2 or any(not s.strip() for s in sentences):
        return ["it needs exactly two sentences"]
    for n, sentence in enumerate(sentences, 1):
        if word_count(sentence) > EXPLAIN_WORDS:
            problems.append(f"sentence {n} has {word_count(sentence)} words; the most is {EXPLAIN_WORDS}")
    if places and not any(m.lower() in sentences[1].lower() for p in places for m in p["match"]):
        problems.append("sentence 2 must name one of the places to look")
    if result["id"] != "user_line" and "user.md" in " ".join(sentences).lower():
        problems.append("USER.md is not the place to look for this check")
    if before_compare and giveaways_in(" ".join(sentences), mission_id):
        problems.append("it used a word that gives the answer away")
    return problems


def _explain_one(mission, result, before_compare: bool, attempt_id=None, places=(), snag: str = "") -> dict:
    banned = ""
    if before_compare:
        words = sorted({w for s in _mission_snags(mission["id"]) for w in text.GIVEAWAYS.get(s, ()) if "_" not in w})
        if words:
            banned = " Never use these words or any form of them: " + ", ".join(words) + "."
    places = list(places or [])

    def checked(reply):
        problems = explain_problems(reply["sentences"], result, mission["id"], places, before_compare)
        if problems:
            raise ValueError("; ".join(problems))

    facts = "; ".join(f"{f.get('label', '')}: {f.get('value', '')}" if isinstance(f, dict) else str(f) for f in _explain_facts(result))
    missing = "; ".join(str(m.get("what", "")) for m in result.get("missing") or [] if isinstance(m, dict))
    inputs = [f"The check: {result['title'] or result['id']}\nWhat it found: {result.get('detail', '')}\nThe facts it read: {facts or '(none)'}\n"
              f"What is still missing: {missing or '(not stated)'}"]
    if snag and not before_compare:
        inputs.append(f"What Field Academy planted, now shown to the learner (this is the cause to name): {snag}")
    if places:
        inputs.append("Places to look (sentence two names one of these):\n" + "\n".join(f"- {p['name']}" for p in places))
    tail = f"Look closely at {places[0]['name']}." if places else text.EXPLAIN_FALLBACK_TAIL
    fallback = [scrub.clip(result.get("detail") or missing or "This check isn't met yet.", 240), tail]
    try:
        out = ai.call(runtime.TASK_GUIDE, instructions=EXPLAIN_INSTRUCTIONS.format(
                          banned=banned, one=EXPLAIN_ONE_BEFORE if before_compare else EXPLAIN_ONE_AFTER), inputs=inputs, schema=EXPLAIN_SCHEMA,
                      schema_name="field_academy_explain", purpose="explain", max_tokens=260, validate=checked,
                      attempt_id=attempt_id)
    except ai.AiFailure as failure:
        base = {"check_id": result["id"], "sentences": fallback, "source": "course", "state": "ready"}
        return base if failure.kind == "bad_json" else {**base, "state": failure.kind, "message": failure.message,
                                                         "next_step": failure.next_step}
    return {"check_id": result["id"], "sentences": [s.strip() for s in out["parsed"]["sentences"]], "source": "model",
            "model": out["model"], "ms": out["ms"], "state": "ready"}


def _make_explain(mission, results, before_compare, attempt_id=None, places=(), on_item=None, snag: str = "") -> list:
    """Explain my miss for every failed visible check, all at once on their own threads (Loop 1 ran them one after
    another: 12.7 s plus 17.4 s). ``on_item`` gets each finished item as it lands."""
    failed = [r for r in results if not r["passed"]]
    found: dict = {}

    def one(r):
        try:
            item = _explain_one(mission, r, before_compare, attempt_id, places, snag)
        except ai.AiOff:
            return
        except Exception:  # one check's failure never sinks the others
            _log.exception("field-academy: explain for %s failed", r["id"])
            item = {"check_id": r["id"], "state": "provider_error", "sentences": [], "source": ""}
        found[r["id"]] = item
        if on_item is not None:
            on_item(item)

    workers = [threading.Thread(target=one, args=(r,), name=f"field-academy-explain-{r['id']}", daemon=True) for r in failed]
    for w in workers:
        w.start()
    for w in workers:
        w.join(ai.DEFAULT_TIMEOUT + 10)
    return [found[r["id"]] for r in failed if r["id"] in found]


# --------------------------------------------------------------- prefetch --


def _settled(entry, key) -> bool:
    """A cached result for this run that is done (not still fetching)."""
    return bool(entry) and entry.get("run") == key and entry.get("state") != "fetching"


def _explain_key(phase, rows, after: bool) -> str:
    """Explain is fetched once per run, and again after Compare (when it may name the cause)."""
    return f"{phase}:{_run_key(rows)}:{'after' if after else 'before'}"


def _prefetch(attempt_id, after: bool = False, explain_too: bool = True) -> None:
    """The nudge first, then every Explain my miss call at once, each on its own thread. A ``fetching`` marker with
    ``started_at`` goes into the cache before each call, so the page can say "fetching, 6 s"."""
    aid = int(attempt_id)
    try:
        attempt, mission, entries, checks, _ = _attempt_and_mission(aid)
        rows = _first_run(checks)
        key = _run_key(rows)
        results = _visible_results(mission, rows)
        cache = _cache_read(aid)
        found = events(attempt)  # plant-free: the hunt is still on for the nudge
        workers = []
        if not _settled(cache.get("nudge"), key):
            started = _now()
            _cache_put(aid, "nudge", {"state": "fetching", "text": "", "started_at": started, "run": key})

            def nudge():
                try:
                    made = _make_nudge(attempt, mission, results, found)
                except ai.AiOff:
                    made = {"state": "not_started", "text": ""}
                _cache_put(aid, "nudge", {**made, "run": key, "started_at": started, "ready_at": _now()})

            workers.append(threading.Thread(target=nudge, name="field-academy-nudge", daemon=True))
        phase, latest = _latest_phase(checks)
        before = not after and not _compare_reached(entries, checks, "check")
        latest_key = _explain_key(phase, latest, not before)
        # Why did this miss? shows only on Compare, so Explain is fetched only once Compare is reached: a paid call
        # per missed check that nothing shows is waste on the learner's account (Nov 9).
        if not before and explain_too and not _settled(cache.get("explain"), latest_key):
            latest_results = _visible_results(mission, latest)
            places = explain_places(mission, found if before else events(attempt, reveal=True), before)
            started = _now()
            _cache_put(aid, "explain", {"run": latest_key, "state": "fetching", "started_at": started,
                                        "items": [{"check_id": r["id"], "state": "fetching", "started_at": started, "sentences": []}
                                                  for r in latest_results if not r["passed"]]})

            def land(item):
                item = {**item, "started_at": started, "ready_at": _now()}
                _cache_update(aid, "explain", lambda cur: {**(cur or {}), "items": [
                    item if i["check_id"] == item["check_id"] else i for i in (cur or {}).get("items", [])]})

            def explain():
                plants = json.loads(attempt["plants_json"] or "[]")
                snag = ", ".join(foundations.PLANT_TITLES.get(x, x) for x in plants)
                _make_explain(mission, latest_results, before, aid, places, on_item=land, snag=snag)
                _cache_update(aid, "explain", lambda cur: {**(cur or {}), "state": "ready", "ready_at": _now()})

            workers.append(threading.Thread(target=explain, name="field-academy-explain", daemon=True))
        for w in workers:
            w.start()
        for w in workers:
            w.join(ai.DEFAULT_TIMEOUT + 15)
    except ai.AiOff:
        pass
    except Exception:
        _log.exception("field-academy: guide prefetch failed")
    finally:
        with _cache_lock:
            _inflight.discard(aid)


def start_prefetch(attempt_id, after: bool = False, explain_too: bool = True) -> bool:
    """Start the nudge and Explain my miss calls on a background thread. False when one is already running."""
    with _cache_lock:
        if int(attempt_id) in _inflight:
            return False
        _inflight.add(int(attempt_id))
    threading.Thread(target=_prefetch, args=(int(attempt_id), after, explain_too), name="field-academy-guide-prefetch", daemon=True).start()
    return True


def _running(key) -> bool:
    with _cache_lock:
        return key in _inflight


def wait_prefetch(attempt_id, seconds: float = 65.0, what=None) -> None:
    """Block until a running prefetch for this attempt finishes (tests, and a press before the cache is ready).
    ``what="why"`` waits for Do it with me's line instead."""
    import time

    key = int(attempt_id) if what is None else (int(attempt_id), what)
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not _running(key):
            return
        time.sleep(0.02)


def _prefetch_why(attempt_id) -> None:
    aid = int(attempt_id)
    try:
        attempt, mission, _, checks, _ = _attempt_and_mission(aid)
        key = _run_key(_first_run(checks))
        if _settled(_cache_read(aid).get("why"), key):
            return
        started = _now()
        _cache_put(aid, "why", {"state": "fetching", "text": "", "started_at": started, "run": key})
        try:
            why = _make_why(attempt, mission, checks)
        except ai.AiOff:
            why = {"state": "not_started", "text": ""}
        _cache_put(aid, "why", {**why, "run": key, "started_at": started, "ready_at": _now()})
    except Exception:
        _log.exception("field-academy: Do it with me prefetch failed")
    finally:
        with _cache_lock:
            _inflight.discard((aid, "why"))


def start_why(attempt_id) -> bool:
    """Start Do it with me's one line when Compare opens, so it is ready on Fix."""
    key = (int(attempt_id), "why")
    with _cache_lock:
        if key in _inflight:
            return False
        _inflight.add(key)
    threading.Thread(target=_prefetch_why, args=(int(attempt_id),), name="field-academy-why", daemon=True).start()
    return True


def _shown_state(entry: dict) -> dict:
    """What the page sees of a cached item: ``fetching`` carries ``started_at`` so it can count the seconds."""
    out = {k: v for k, v in (entry or {}).items() if k not in ("run", "ready_at")}
    if out.get("state") != "fetching":
        out.pop("started_at", None)
    return out


# ------------------------------------------------------------------- help --


def _help_entries(entries) -> list:
    return [e for e in entries if e["kind"] == "help"]


def help_summary(attempt_id) -> dict:
    """How the snag was found, from the help entries made before Compare: on your own, after one nudge, or with help."""
    with foundations._conn() as conn:
        entries = foundations._entries(conn, attempt_id)
    gap_at = next((e["id"] for e in entries if e["kind"] == "gap_note"), None)
    before = [e for e in _help_entries(entries) if gap_at is None or e["id"] < gap_at]
    hunt = [e["body"] for e in before if e["body"].get("kind") in HELP_KINDS.values()
            or (e["body"].get("kind") == "ask" and e["body"].get("hunt"))]
    rungs = [b.get("rung") for b in hunt]
    if not hunt:
        words, key = "No hints used", "own"
    elif rungs == [1]:
        words, key = "One hint used", "one_nudge"
    elif 3 in rungs:
        words, key = "The guide showed the answer", "shown"
    else:
        words, key = f"{len(hunt)} {'hint' if len(hunt) == 1 else 'hints'} used", "hints"
    return {"key": key, "words": words, "hunt_helps": len(hunt), "all_helps": len(_help_entries(entries)),
            "used": [{"kind": e["body"].get("kind"), "rung": e["body"].get("rung"), "step": e["body"].get("step"),
                      "at": e["created_at"]} for e in _help_entries(entries)]}


def _record_help(attempt_id, body) -> dict:
    with foundations._conn() as conn:
        attempt = foundations._attempt(conn, attempt_id)
        body = {**body, "mission": attempt["mission_id"], "at": store.now()}
        entry = foundations._append(conn, attempt_id, "help", body)
    return {**entry, "body": body}


# ------------------------------------------------------------------- view --


def is_first_flight(entries) -> bool:
    return any(e["kind"] == FIRST_FLIGHT for e in entries)


def _off_reason(test_out: bool, entries=(), checks=()) -> str:
    """Why the guide is closed, or ``""``. First Flight keeps it closed until the self-score is locked, so the score is
    the learner's own; then it opens like any other try."""
    if test_out:
        return "test_out"
    if not ai.ai_help_on():
        return "switch"
    if is_first_flight(entries) and not any(e["kind"] == "self_score" for e in entries):
        return "first_flight_locked"
    return ""


def guide_view(attempt_id, step: str = "", active: str = "own") -> dict:
    """What the Field guide column shows for one attempt and step. Starts the prefetch after a missed first check, and
    Do it with me's line when Compare opens. Anything still on its way reads ``{"state": "fetching", "started_at"}``."""
    step = str(step or "")
    attempt, mission, entries, checks, test_out = _attempt_and_mission(attempt_id)
    mission_id = mission["id"]
    reason = _off_reason(test_out, entries, checks)
    starters = list(text.STARTERS.get(mission_id, {}).get(step, ())) if step in STEPS_WITH_STARTERS else []
    base = {"enabled": not reason, "off_reason": reason or None, "off_words": OFF_WORDS.get(reason, ""), "step": step,
            "mission_id": mission_id, "starters": starters, "help": help_summary(attempt_id)}
    empty = {"ladder": {"nudge": {"state": "not_started", "text": ""}, "where": {"available": False, "text": ""},
                        "reveal": {"available": False}},
             "explain": [], "pins": [], "do_it_with_me": None}
    if reason:
        return {**base, **empty}
    first = _first_run(checks)
    missed = bool(first) and not all(bool(r["passed"]) for r in first)
    used = {(e["body"].get("kind")) for e in _help_entries(entries)}
    cache = _cache_read(attempt_id)
    hunting = missed and mission_id in text.MISSION_SNAGS
    view = dict(empty)
    fetch_here = step in ("check", "fix", "compare") and active != "practice"  # the hunt on Check, Explain on Compare
    if missed:
        key = _run_key(first)
        nudge = cache.get("nudge") or {}
        stale = nudge.get("state") == "fetching" and not _running(int(attempt_id))
        if nudge.get("run") != key or stale:
            if not fetch_here:
                nudge = {"state": "not_started", "text": ""}
            else:
                start_prefetch(attempt_id, _compare_reached(entries, checks, step))
                nudge = _cache_read(attempt_id).get("nudge") or {}
                if nudge.get("run") != key:
                    nudge = {"state": "fetching", "text": "", "started_at": _now()}
        shown = _shown_state(nudge)
        if "nudge" not in used:
            shown["text"] = ""  # ready, but its words show only once the learner presses Give me a hint (and it is recorded)
        plants = json.loads(attempt["plants_json"] or "[]")
        where_text = text.WHERE.get(plants[0], "") if plants else ""
        view["ladder"] = {"nudge": shown if hunting else {"state": "not_started", "text": ""},
                          "where": {"available": hunting and bool(where_text), "text": where_text if "where" in used else ""},
                          "reveal": {"available": True, "opens": "compare"}}
        explain = _cache_read(attempt_id).get("explain") or {}
        items = [_shown_state(i) for i in explain.get("items", [])]
        if "explain" not in used:
            items = [{k: v for k, v in i.items() if k in ("check_id", "state", "started_at")} | {"sentences": []} for i in items]
        view["explain"] = items
        phase, latest = _latest_phase(checks)
        after = _compare_reached(entries, checks, step)
        if after and explain.get("run") != _explain_key(phase, latest, True):
            items = []  # the before-Compare wording isn't shown on Compare; the after-Compare one is fetching
        view["explain"] = items
        if fetch_here and explain.get("run") != _explain_key(phase, latest, after):
            start_prefetch(attempt_id, after)  # none yet, a newer run (after the fix), or Compare just opened
    if _compare_reached(entries, checks, step):
        view["pins"] = (cache.get("pins") or {}).get("pins", [])
    if mission_id in text.DO_IT_WITH_ME and first and held_save_id(attempt_id):
        why = cache.get("why") or {}
        opened = missed and _compare_reached(entries, checks, step) and active != "practice"
        if opened and not _settled(why, _run_key(first)) and not _running((int(attempt_id), "why")):
            start_why(attempt_id)  # Compare is open: fetch the line now, so Fix shows it at once
            why = _cache_read(attempt_id).get("why") or {"state": "fetching", "started_at": _now()}
        if step == "fix":
            shown_why = _shown_state(why)
            view["do_it_with_me"] = {"commands": fix_commands(mission_id, attempt_id),
                                     "why": {"state": shown_why.get("state", "not_started"), "text": shown_why.get("text", ""),
                                             "source": shown_why.get("source", ""),
                                             **({"started_at": shown_why["started_at"]} if "started_at" in shown_why else {})},
                                     "sends": False}
    return {**base, **view}


def use_help(attempt_id, rung=None, action=None, step: str = "") -> dict:
    """The learner pressed a rung or a helper. Returns the recorded entry and what to show."""
    attempt, mission, entries, checks, test_out = _attempt_and_mission(attempt_id)
    reason = _off_reason(test_out, entries, checks)
    if reason:
        raise ValueError(OFF_WORDS[reason])
    first = _first_run(checks)
    if rung is not None:
        if isinstance(rung, bool) or rung not in HELP_KINDS:
            raise ValueError("A hint is rung 1, 2 or 3.")
        if not first or all(bool(r["passed"]) for r in first):
            raise ValueError("The hints open after a check finds something.")
        if rung == 1:
            wait_prefetch(attempt_id)
            nudge = _cache_read(attempt_id).get("nudge") or {}
            if nudge.get("run") != _run_key(first):
                _prefetch_now(attempt_id)
                nudge = _cache_read(attempt_id).get("nudge") or {}
            shown = _shown_state(nudge)
            if shown.get("state") != "ready":
                shown = {**shown, "text": shown.get("fallback_text") or text.NUDGE_FALLBACK.get(mission["id"], ""), "source": "course"}
        elif rung == 2:
            plants = json.loads(attempt["plants_json"] or "[]")
            shown = {"text": text.WHERE.get(plants[0], "") if plants else "", "source": "course"}
        else:
            shown = {"opens": "compare"}
        entry = _record_help(attempt_id, {"kind": HELP_KINDS[rung], "rung": rung, "step": step or "check",
                                          "source": shown.get("source", "")})
        return {"entry": entry, "shown": shown, "help": help_summary(attempt_id)}
    if action not in ACTIONS:
        raise ValueError("Unknown help.")
    if action == "explain":
        after = _compare_reached(entries, checks, step)
        if not after:
            raise ValueError("Why did this miss? opens on Compare.")
        phase, latest = _latest_phase(checks)
        wait_prefetch(attempt_id)
        cached = _cache_read(attempt_id).get("explain") or {}
        items = cached.get("items") if cached.get("run") == _explain_key(phase, latest, after) else None
        if items is None:
            _prefetch_now(attempt_id, after)
            items = (_cache_read(attempt_id).get("explain") or {}).get("items", [])
        items = [_shown_state(i) for i in items]
        entry = _record_help(attempt_id, {"kind": "explain", "step": step or "check", "checks": [i["check_id"] for i in items]})
        return {"entry": entry, "shown": {"explain": items}, "help": help_summary(attempt_id)}
    if action == "do_it_with_me":
        if mission["id"] not in text.DO_IT_WITH_ME:
            raise ValueError("Do it with me is on mission 3's Fix step.")
        if not held_save_id(attempt_id):
            raise ValueError("Do it with me walks through approving a save Hermes is holding, and this run has none.")
        key = _run_key(_first_run(checks))
        wait_prefetch(attempt_id, 65.0, what="why")  # started when Compare opened; usually ready by now
        why = _cache_read(attempt_id).get("why") or {}
        if not _settled(why, key) or why.get("source") != "model":  # the course's words: pressing again asks again
            why = {**_make_why(attempt, mission, checks), "run": key}
            _cache_put(attempt_id, "why", why)
        why = _shown_state(why)
        entry = _record_help(attempt_id, {"kind": "do_it_with_me", "step": "fix"})
        return {"entry": entry, "shown": {"commands": fix_commands(mission["id"], attempt_id), "why": why, "sends": False},
                "help": help_summary(attempt_id)}
    raise ValueError("Use the ask or pins route for that.")


def _prefetch_now(attempt_id, after: bool = False) -> None:
    with _cache_lock:
        _inflight.add(int(attempt_id))
    _prefetch(attempt_id, after)


# ---------------------------------------------------------- do it with me --

_HELD_PATH = re.compile(r"^pending/memory/([0-9a-f]{8})\.json$")  # Hermes names a held save uuid4().hex[:8]


def held_save_id(attempt_id) -> str:
    """The id of the save Hermes was holding when the first check ran, read from that run's evidence (the file name under
    pending/memory/). Empty when the first run found no held save."""
    rec = _recorder()
    if rec is None:
        return ""
    with foundations._conn() as conn:
        for ev in rec.first_run_evidence(conn, attempt_id):
            found = _HELD_PATH.match(str(ev.get("rel_path") or ""))
            if ev.get("kind") == "pending" and found:
                return found.group(1)
    return ""


def fix_commands(mission_id: str, attempt_id) -> list:
    """The two commands, with the held save's id filled in by code. Without an id, only the list command: the learner
    reads the id there (the why line says so); a command with a blank in it would be copied as is."""
    held = held_save_id(attempt_id)
    out = []
    for c in text.DO_IT_WITH_ME[mission_id]:
        if "{id}" in c:
            if not held:
                continue
            c = c.replace("{id}", held)
        out.append(c)
    return out


WHY_SCHEMA = {"type": "object", "required": ["why"], "additionalProperties": False,
              "properties": {"why": {"type": "string", "maxLength": 200}}}


def _make_why(attempt, mission, checks) -> dict:
    """One model line on why the two fixed commands fix it, from the check's facts. After Compare, so the snag may be
    named. The line can't add a command: any other slash command in it sends it back once, then to the course's words."""
    commands = fix_commands(mission["id"], attempt["id"])
    allowed = set(commands) | (set() if len(commands) > 1 else {"/memory approve"})
    results = _visible_results(mission, _first_run(checks))
    plants = json.loads(attempt["plants_json"] or "[]")
    title = foundations.PLANT_TITLES.get(plants[0], plants[0]) if plants else ""

    def checked(reply):
        if re.search(r"approve\s+all", reply["why"], re.I):
            raise ValueError("it told the learner to approve every held save")
        for found in re.findall(r"(?<![\w])/[a-z][\w-]*(?: [a-z][\w-]*)*", reply["why"]):
            if not any(found.startswith(c) or c.startswith(found) for c in allowed):
                raise ValueError("it named a command that isn't one of the two")

    inputs = [f"What Field Academy planted: {title}", "What the check read:\n" + _results_for_model(results),
              "The commands the learner will type, in order: " + " then ".join(commands)
              + ("" if len(commands) > 1 else ". Then /memory approve with the id the list shows."),
              "The approve command applies only the one held save, by its id; other held saves stay held."]
    try:
        out = ai.call(runtime.TASK_GUIDE, instructions=(
            "In one plain sentence of 30 words or fewer, a 13-year-old could read, say what each of these commands "
            "does. The page already says what went wrong, so don't say it again. Don't suggest any other command. Reply with only a JSON object: "
            "why."), inputs=inputs, schema=WHY_SCHEMA, schema_name="field_academy_why", purpose="do_it_with_me",
            max_tokens=120, validate=checked, attempt_id=attempt["id"])
    except ai.AiOff:
        raise
    except ai.AiFailure as failure:
        return {"state": "ready" if failure.kind == "bad_json" else failure.kind,
                "text": text.DO_IT_WITH_ME_FALLBACK[mission["id"]], "source": "course"}
    return {"state": "ready", "text": out["parsed"]["why"].strip(), "source": "model", "model": out["model"], "ms": out["ms"]}


# ------------------------------------------------------------------- pins --

PIN_WORDS = 20
PINS_SCHEMA = {"type": "object", "required": ["pins"], "additionalProperties": False,
               "properties": {"pins": {"type": "array", "maxItems": 6, "items": {
                   "type": "object", "required": ["event_id", "why"], "additionalProperties": False,
                   "properties": {"event_id": {"type": "string", "maxLength": 40}, "why": {"type": "string", "maxLength": 400}}}}}}
TOO_LONG = ("Your model's replay notes ran too long to show.",
            "Press Try again for shorter notes. The replay itself is all there.")
NO_PINS = ("Your model's replay notes didn't point at anything in your run.",
           "Press Try again. The replay itself is all there.")

PINS_INSTRUCTIONS = (
    "You are the Field guide in Field Academy. The learner did a job in a practice copy of Hermes, scored their own "
    "work, then a check read what Hermes really did. Pick up to three moments in this run where what the learner "
    "believed and what Hermes really did split.{bracket} For each pin give the event id copied from the list and why it "
    "matters: one plain sentence of 20 words or fewer that a 13-year-old could read. The page already says, in one "
    "sentence above the replay, what Hermes claimed and what really happened (it is in the inputs), so no note may say "
    "that again in any words: if the sentence says a note is waiting for approval, no pin says it waits, is held or "
    "needs approving; if it says a note was deleted, no pin says it was deleted or removed. Each note says "
    "what this one moment shows that the sentence doesn't: the exact words to read in it, the file it points at, or what "
    "it led to later. No two notes may make the same point. Say only what the run and the check facts show, and never "
    "anything a check fact contradicts. Reply with only a JSON object: pins, a list of {{event_id, why}}."
)


def _recorder():
    try:
        return import_module(f"{__package__}.recorder")
    except ImportError:
        return None


def _all_results(mission, rows) -> list:
    """Every check of a run with what it read, hidden ones included: after Compare the learner has seen them all."""
    specs = {c["id"]: c for c in mission.get("live_checks", [])}
    latest = {}
    for r in rows:
        latest[r["check_id"]] = r
    out = []
    for check_id, r in latest.items():
        facts = json.loads(r["facts_json"] or "{}")
        out.append({"id": check_id, "passed": bool(r["passed"]), "title": facts.get("title", ""), "facts": facts.get("facts", []),
                    "visible": specs.get(check_id, {}).get("visible", True)})
    return out


def pins_context(attempt_id) -> dict:
    """``{"inputs", "events", "bracket"}`` for the pins call: the revealed snag, every check fact of the first run, the
    learner's guess, the bracket and the revealed run (both lanes, the staged line, the frozen pending/ evidence)."""
    attempt, mission, entries, checks, _ = _attempt_and_mission(attempt_id)
    found = events(attempt, reveal=True)
    rec = _recorder()
    joined = rec.bracket(found) if rec is not None else None
    plants = json.loads(attempt["plants_json"] or "[]")
    guess = (next((e["body"] for e in reversed(entries) if e["kind"] == "prediction"), {}) or {}).get("where_wrong", "")
    results = _all_results(mission, _first_run(checks))
    lines = []
    for r in results:
        facts = "; ".join(f"{f.get('label', '')}: {f.get('value', '')}" for f in r["facts"][:6] if isinstance(f, dict))
        lines.append(f"- {r['title'] or r['id']}: {'met' if r['passed'] else 'NOT met'}." + (f" {facts}" if facts else ""))
    inputs = [f"What Field Academy planted (the learner has seen it now): "
              f"{', '.join(foundations.PLANT_TITLES.get(p, p) for p in plants) or '(none)'}",
              "What the first check found:\n" + ("\n".join(lines) or "(no results)"),
              "Where the learner guessed they'd slip: " + (scrub.clip(guess, 300) or "(no guess written)")]
    if joined:
        inputs.append("The sentence the page already shows above the replay (don't repeat it): " + joined["words"])
        ids = {e["event_id"]: e for e in found}
        a, b = ids.get(joined["from"], {}), ids.get(joined["to"], {})
        inputs.append(f"The bracket: chat event {joined['from']} ({a.get('title', '')}: {scrub.clip(str(a.get('text') or ''), 160)}) "
                      f"and files event {joined['to']} ({b.get('title', '')}, {b.get('path', '')}). {joined['words']}")
    inputs.append("The run, oldest first (id | time | lane | kind | title | text | more):\n" + _events_for_pins(found))
    return {"inputs": inputs, "events": found, "bracket": joined}


def usable_pins(raw, ids, limit: int = 3):
    """``(pins, counts)``. A pin on an unknown event is dropped; a pin over 20 words is cut to its first sentence when
    that fits, else dropped. The rest are kept, up to three, one per event."""
    kept, counts, seen = [], {"unknown": 0, "too_long": 0, "trimmed": 0}, set()
    for p in raw or []:
        event_id = str(p.get("event_id") or "")
        if event_id not in ids:
            counts["unknown"] += 1
            continue
        why = " ".join(str(p.get("why") or "").split())
        if word_count(why) > PIN_WORDS:
            short = first_sentence(why)
            if not short or word_count(short) > PIN_WORDS or word_count(short) < 6:
                counts["too_long"] += 1
                continue
            why, counts["trimmed"] = short, counts["trimmed"] + 1
        if not why or event_id in seen:
            continue
        seen.add(event_id)
        kept.append({"event_id": event_id, "why": why, "source": "model", "kept": None})
    return kept[:limit], counts


def make_pins(attempt_id, step: str = "compare") -> dict:
    """Up to three replay pins, after Compare only. At least one is asked for on the bracket. A long pin is trimmed or
    dropped, never the whole call; one more try runs when nothing usable came back or the bracket got no pin."""
    attempt, mission, entries, checks, test_out = _attempt_and_mission(attempt_id)
    if _off_reason(test_out, entries, checks):
        raise ValueError(OFF_WORDS[_off_reason(test_out, entries, checks)])
    if not _compare_reached(entries, checks, step):
        raise ValueError("Replay notes open on Compare.")
    ctx = pins_context(attempt_id)
    ids = {e["event_id"] for e in ctx["events"]}
    joined = ctx["bracket"]
    on_bracket = {joined["from"], joined["to"]} if joined else set()
    # The bracket pin goes on the chat row that looked fine: the files card beside it already shows where the note went,
    # so a pin there only restates the headline (round 7 and 8 critics). The row's own words are what to learn to read.
    # Its note says the one thing neither the row nor the headline says: where to look in Hermes to catch this yourself
    # next time (text.CATCH_IT, fixed in code per snag). Any other slash command in that note sends it back.
    plants = json.loads(attempt["plants_json"] or "[]")
    catch, catch_cmds = text.CATCH_IT.get(plants[0], ("", ())) if plants else ("", ())
    bracket_line = (f" You must put one pin on event {joined['from']}, the chat row that looked fine. Don't repeat what the row "
                    "or the headline says; say only where to look in Hermes to catch this yourself next time: "
                    f"{catch} Don't pin {joined['to']}; its card already shows the file." if joined and catch else
                    f" Put one pin on event {joined['from']}, the chat row that looked fine. Don't pin {joined['to']}."
                    if joined else "")

    def catch_ok(p):
        if not joined or p.get("event_id") != joined["from"]:
            return True
        found = re.findall(r"(?<![\w])/[a-z][\w-]*(?: [a-z][\w-]*)?", str(p.get("why") or ""))
        return all(any(f.startswith(c) or c.startswith(f) for c in catch_cmds) for f in found)
    meter_ids = {e["event_id"] for e in ctx["events"] if e.get("kind") == "file:memory"}
    if meter_ids:
        bracket_line += f" Don't pin {', '.join(sorted(meter_ids))}; its card already shows how full MEMORY.md is."
    tries, note = [], ""
    for _ in range(2):
        try:
            out = ai.call(runtime.TASK_GUIDE, instructions=PINS_INSTRUCTIONS.format(bracket=bracket_line) + note,
                          inputs=ctx["inputs"], schema=PINS_SCHEMA, schema_name="field_academy_pins", purpose="pins",
                          max_tokens=400, attempt_id=attempt["id"])
        except ai.AiFailure as failure:
            if tries:
                break  # keep what the first try gave
            result = {"state": failure.kind, "pins": [], "message": failure.message, "next_step": failure.next_step}
            _cache_put(attempt_id, "pins", result)
            return result
        # A pin on the bracket's files card is dropped: the card already says where the note went.
        raw = out["parsed"]["pins"]
        # No note on a files card that already says it: the bracket's file, or the MEMORY.md meter (its title and
        # fill are the fact; a note there only restated them, round 11).
        kept_raw = [p for p in raw if (not joined or p.get("event_id") != joined["to"]) and p.get("event_id") not in meter_ids
                    and catch_ok(p)]
        pins, counts = usable_pins(kept_raw, ids)
        counts["on_card"] = len(raw) - len(kept_raw)  # on a files card, or a bracket note with a command not its own
        hit = any(p["event_id"] in on_bracket for p in pins)
        tries.append({"pins": pins, "counts": counts, "bracket_pinned": hit, "out": out})
        if pins and (hit or not joined):
            break
        problems = []
        if counts["too_long"]:
            problems.append(f"{counts['too_long']} pin(s) ran over 20 words")
        if counts["unknown"]:
            problems.append(f"{counts['unknown']} pin(s) named an id that is not in the list")
        if joined and not hit:
            problems.append(f"no pin was on {joined['from']} or {joined['to']}")
        note = "\n\nYour last reply could not be used as it was: " + "; ".join(problems or ["no pin fit"]) + \
               ". Each why is one sentence of 20 words or fewer."
    pick = next((t for t in tries if t["pins"] and t["bracket_pinned"]), None) or next((t for t in tries if t["pins"]), None)
    if pick is None:
        long_drop = any(t["counts"]["too_long"] for t in tries)
        message, next_step = TOO_LONG if long_drop else NO_PINS
        result = {"state": "too_long" if long_drop else "no_pins", "pins": [], "message": message, "next_step": next_step,
                  "tries": len(tries)}
        _cache_put(attempt_id, "pins", result)
        return result
    out = pick["out"]
    result = {"state": "ready", "pins": pick["pins"], "model": out["model"], "ms": sum(t["out"]["ms"] for t in tries),
              "dropped": pick["counts"]["unknown"] + pick["counts"]["too_long"] + pick["counts"].get("on_card", 0), "trimmed": pick["counts"]["trimmed"],
              "bracket": joined, "bracket_pinned": pick["bracket_pinned"], "tries": len(tries)}
    _cache_put(attempt_id, "pins", result)
    return result


def update_pins(attempt_id, keep=(), dismiss=(), add=()) -> dict:
    """The learner keeps, dismisses or adds pins. Recorded as a help entry; kept and added pins go to the record."""
    attempt, mission, entries, checks, _ = _attempt_and_mission(attempt_id)
    ids = {e["event_id"] for e in events(attempt, reveal=True)}
    cache = _cache_read(attempt_id).get("pins") or {"pins": []}
    pins = list(cache.get("pins", []))
    for pin in pins:
        if pin["event_id"] in set(keep):
            pin["kept"] = True
        if pin["event_id"] in set(dismiss):
            pin["kept"] = False
    for item in add or []:
        if not isinstance(item, dict) or item.get("event_id") not in ids:
            continue
        pins.append({"event_id": item["event_id"], "why": scrub.clip(" ".join(str(item.get("why") or "").split()), 160),
                     "source": "you", "kept": True})
    _cache_put(attempt_id, "pins", {**cache, "pins": pins})
    kept = [p for p in pins if p.get("kept")]
    _record_help(attempt_id, {"kind": "pins", "step": "compare", "kept": [{"event_id": p["event_id"], "why": p["why"], "source": p["source"]} for p in kept]})
    return {"pins": kept}


# -------------------------------------------------------------------- ask --

ASK_SCHEMA = {"type": "object", "required": ["sentences", "not_in_sources"], "additionalProperties": False,
              "properties": {"sentences": {"type": "array", "maxItems": 4, "items": {
                  "type": "object", "required": ["text", "source_ids"], "additionalProperties": False,
                  "properties": {"text": {"type": "string", "maxLength": 300},
                                 "source_ids": {"type": "array", "maxItems": 4, "items": {"type": "string", "maxLength": 40}}}}},
                  "not_in_sources": {"type": "boolean"}}}


def ask_sources(attempt_id, step: str = "") -> list:
    """What Ask may cite, as ``[{id, kind, text}]``. Lesson paragraphs the learner has opened; the "as of Hermes" facts;
    from Check onward, the learner's own entries and chat events. Never the planted problem."""
    attempt, mission, entries, checks, _ = _attempt_and_mission(attempt_id)
    reads = {e["body"].get("step") for e in entries if e["kind"] == "read"}
    scored = any(e["kind"] == "self_score" for e in entries)
    out = []
    if "idea" in reads or scored:
        for n, para in enumerate(p for p in re.split(r"\n\s*\n", mission.get("_idea_text") or "") if p.strip()):
            out.append({"id": f"idea-{n + 1}", "kind": "lesson", "text": scrub.clip(" ".join(para.split()), 600)})
    if "expert" in reads or scored:
        for n, s in enumerate(mission.get("_expert_steps") or []):
            out.append({"id": f"expert-{n + 1}", "kind": "lesson",
                        "text": scrub.clip(f"{s.get('title', '')}: {s.get('did', '')} {s.get('saw', '')} {s.get('noticed', '')}", 600)})
    for n, fact in enumerate(mission.get("as_of") or []):
        out.append({"id": f"asof-{n + 1}", "kind": "as_of", "text": f"As of Hermes {fact.get('since', '')}: {fact.get('fact', '')}"})
    if _first_run(checks):
        for e in entries:
            if e["kind"] in ("claim", "prediction", "lab_note", "gap_note", "diagnosis", "fix_note"):
                body = e["body"].get("text") or e["body"].get("where_wrong") or e["body"].get("fact") or ""
                if body:
                    out.append({"id": f"you-{e['id']}", "kind": "yours", "text": scrub.clip(str(body), 400)})
        for ev in events(attempt, reveal=_compare_reached(entries, checks, step)):
            out.append({"id": ev["event_id"], "kind": "chat" if ev.get("lane", "chat") == "chat" else "files", "text": f"{_clock(ev.get('at'))} {ev.get('kind', '')} {_event_body(ev)}".strip()})
    return out


ASK_INSTRUCTIONS = (
    "Answer the learner's question using only the numbered sources. Write up to four short plain sentences, each "
    "with the ids of the sources it uses. If the sources don't answer it, return no sentences and not_in_sources "
    "true. Reply with only a JSON object: sentences (a list of {text, source_ids}) and not_in_sources."
)


def _ask_call(attempt, q, sources, instructions):
    return ai.call(runtime.TASK_GUIDE, instructions=instructions,
                   inputs=["Sources:\n" + "\n".join(f"[{s['id']}] {s['text']}" for s in sources), "The learner's question:\n" + q],
                   schema=ASK_SCHEMA, schema_name="field_academy_ask", purpose="ask", max_tokens=500, attempt_id=attempt["id"])


def _ask_kept(parsed, ids) -> list:
    kept = []
    for s in parsed["sentences"]:
        cited = [i for i in s["source_ids"] if i in ids]
        if not cited or len(cited) != len(s["source_ids"]):
            continue
        kept.append({"text": s["text"].strip(), "source_ids": cited})
    return kept


def ask(attempt_id, question: str, step: str = "") -> dict:
    """Ask, from cited sources. During the hunt (first check ran, Compare not yet open) the answer passes the nudge's
    give-away filter: a hit asks once more with the words banned, a second hit shows the course's words instead. Either
    way the question is a hunt help in the record, so "No hints used" stays true."""
    attempt, mission, entries, checks, test_out = _attempt_and_mission(attempt_id)
    if _off_reason(test_out, entries, checks):
        raise ValueError(OFF_WORDS[_off_reason(test_out, entries, checks)])
    q = " ".join(str(question or "").split())
    if not 3 <= len(q) <= 500:
        raise ValueError("Ask a question of 3 to 500 characters.")
    sources = ask_sources(attempt_id, step)
    ids = {s["id"] for s in sources}
    hunting = bool(_first_run(checks)) and not _compare_reached(entries, checks, step)
    held_back, tries = False, 0
    try:
        out = _ask_call(attempt, q, sources, ASK_INSTRUCTIONS)
        tries = 1
        kept = _ask_kept(out["parsed"], ids)
        if hunting and giveaways_in(" ".join(k["text"] for k in kept), mission["id"]):
            banned = sorted({w for sn in _mission_snags(mission["id"]) for w in text.GIVEAWAYS.get(sn, ()) if "_" not in w})
            out = _ask_call(attempt, q, sources, ASK_INSTRUCTIONS + (
                " The learner is still hunting for what went wrong, so don't tell them. Point them at where to look in "
                "their own chat instead. Never use these words or any form of them: " + ", ".join(banned) + "."))
            tries = 2
            kept = _ask_kept(out["parsed"], ids)
            if giveaways_in(" ".join(k["text"] for k in kept), mission["id"]):
                kept, held_back = [], True
    except ai.AiFailure as failure:
        if hunting:
            _record_help(attempt_id, {"kind": "ask", "step": step, "covered": False, "hunt": True, "failed": failure.kind})
        return {**failure.payload(), "sentences": [], "not_in_sources": False, "draft_for_practice_chat": ""}
    if held_back:
        words = text.ASK_HUNT_FALLBACK.get(mission["id"], text.ASK_HUNT_FALLBACK["default"])
        _record_help(attempt_id, {"kind": "ask", "step": step, "covered": True, "hunt": True, "held_back": True})
        return {"state": "ok", "sentences": [{"text": words, "source_ids": [], "source": "course"}], "not_in_sources": False,
                "held_back": True, "draft_for_practice_chat": "", "sends": False, "model": out["model"], "ms": out["ms"],
                "tries": tries, "help": help_summary(attempt_id)}
    not_covered = out["parsed"]["not_in_sources"] or not kept
    _record_help(attempt_id, {"kind": "ask", "step": step, "covered": not not_covered, "hunt": hunting})
    return {"state": "ok", "sentences": [] if not_covered else kept, "not_in_sources": not_covered,
            "draft_for_practice_chat": scrub.scrub(q, 500) if not_covered else "", "sends": False,
            "model": out["model"], "ms": out["ms"], "held_back": False, "tries": tries, "help": help_summary(attempt_id)}


# ----------------------------------------------------------------- routes --


def mount(router, guard) -> None:
    import asyncio

    @router.get("/guide/{attempt_id}")
    async def guide_get(attempt_id: int, step: str = "", active: str = "own"):
        return guard(guide_view, attempt_id, step, active)

    @router.post("/guide/{attempt_id}/help")
    async def guide_help(attempt_id: int, body: dict):
        body = body or {}
        return await asyncio.to_thread(guard, use_help, attempt_id, body.get("rung"), body.get("action"), str(body.get("step", "")))

    @router.post("/guide/{attempt_id}/ask")
    async def guide_ask(attempt_id: int, body: dict):
        body = body or {}
        return await asyncio.to_thread(guard, ask, attempt_id, str(body.get("question", "")), str(body.get("step", "")))

    @router.post("/guide/{attempt_id}/pins")
    async def guide_pins(attempt_id: int, body: dict):
        body = body or {}
        if body.get("make"):
            return await asyncio.to_thread(guard, make_pins, attempt_id, str(body.get("step", "compare")))
        lists = {k: body.get(k) if isinstance(body.get(k), list) else [] for k in ("keep", "dismiss", "add")}
        return await asyncio.to_thread(guard, update_pins, attempt_id, lists["keep"], lists["dismiss"], lists["add"])
