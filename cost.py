"""What a practice cost, for the record cover: Hermes's own estimate for the practice chat, and Field Academy's own
calls in tokens.

* The practice chat: the sum of Hermes's own per-chat estimate (``sessions.estimated_cost_usd``, or the actual cost
  when ``cost_status`` says it is one) in the practice profile's ``state.db``, read through ``hermes_read.sessions``
  (read-only). A chat Hermes couldn't price (``cost_status`` unknown) adds tokens only. No dollar figure is ever made
  up here.
* Field Academy's guide and grading calls: tokens only, from the ledger ``ai.call`` keeps (``result.usage``).
* The practice profile is usually deleted at the end, so the last good reading is kept in the plugin's data folder
  (``cost/attempt-N.json``) and used when the profile is gone.
"""

from __future__ import annotations

import json

from . import ai, foundations, hermes_read, practice, runtime


def _snapshot_path(attempt_id):
    folder = runtime.data_dir() / "cost"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"attempt-{int(attempt_id)}.json"


def _read_practice(name: str):
    """The practice chats' cost as Hermes recorded it, per chat (``sessions``: ``estimated_cost_usd`` with its
    ``cost_status``). ``session_model_usage`` holds the same estimate per model, but ``hermes_read`` doesn't read its
    ``cost_status``, and an estimate of 0 there can mean "no price known"; the sessions row says which."""
    row = practice.record(name) if name else None
    if not row or not practice.is_ours(row):
        return None
    found = hermes_read.sessions(row["path"])
    if not found.get("readable"):
        return None
    usd, priced, included, tokens, models = 0.0, 0, 0, 0, []
    sessions = []
    for s in found.get("sessions", []):
        used = sum(int(s.get(k) or 0) for k in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "reasoning_tokens"))
        status = str(s.get("cost_status") or "").lower()
        if not status and not used:
            continue  # a chat with no model call in it yet: nothing to price
        sessions.append(s)
        tokens += used
        value = s.get("actual_cost_usd") if status == "actual" else s.get("estimated_cost_usd")
        if status in ("actual", "estimated") and isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
            usd += float(value)
            priced += 1
        elif status == "included":
            included += 1
            priced += 1
        model = str(s.get("model") or "")
        if model and model not in models:
            models.append(model)
    return {"rows": len(sessions), "estimated_rows": priced, "included_rows": included,
            "usd": round(usd, 4) if priced else None, "tokens": tokens, "models": models[:3],
            "complete": bool(sessions) and priced == len(sessions)}


def attempt_cost(attempt_id) -> dict:
    """``{practice: {...} | None, guide_tokens, line, guide_line}`` for one attempt."""
    with foundations._conn() as conn:
        attempt = foundations._attempt(conn, attempt_id)
    live = _read_practice(attempt.get("profile") or "")
    path = _snapshot_path(attempt_id)
    if live is not None and live["rows"]:
        path.write_text(json.dumps(live, sort_keys=True), encoding="utf-8")
        found, source = live, "live"
    else:
        try:
            found, source = json.loads(path.read_text(encoding="utf-8")), "kept"
        except (OSError, ValueError):
            found, source = None, "none"
    ours = ai.usage_totals(attempt_id)
    return {"practice": found, "practice_source": source, "guide_tokens": ours["total"], "guide_calls": ours["calls"],
            "line": practice_line(found), "guide_line": guide_line(ours)}


def practice_line(found) -> str:
    if not found or not found.get("rows"):
        return "This practice: Hermes hadn't recorded any usage yet."
    model = f" on {found['models'][0]}" if found.get("models") else ""
    if found.get("usd") is not None:
        if found["usd"] == 0 and found.get("included_rows"):
            return f"This practice: included in your plan{model}, by Hermes's own count."
        amount = f"${found['usd']:.2f}" if found["usd"] >= 0.01 else "under $0.01"
        part = "" if found.get("complete") else ", for the parts Hermes could price"
        return f"This practice: about {amount}, Hermes's own estimate{model}{part}."
    return f"This practice: {found['tokens']:,} tokens{model}. Hermes had no cost estimate for it."


def guide_line(ours: dict) -> str:
    if not ours.get("calls"):
        return "Field guide and grading: not used."
    return f"Field guide and grading: {ours['total']:,} tokens over {ours['calls']} call{'s' if ours['calls'] != 1 else ''}, on your own model."
