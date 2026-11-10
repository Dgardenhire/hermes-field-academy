"""Planted problems for Foundations missions: for each kind, a planter, a detector and a fix-verifier.

* The planter writes the problem into a recorded, unopened practice profile, only through practice_write.py.
* The detector reads the profile afterwards and says whether the learner ran into it (``fired``), with facts.
* The fix-verifier says whether it is fixed now: the learner's fact landed where it belongs, and the cause is gone.

Every practice profile for the memory mission starts with **seed notes** (missions/03-memory.v2.md, build notes): four
or five short setup notes in MEMORY.md, as if someone had used the profile for a few weeks. Two of them are "key"
notes the practice jobs rely on. ``seed_memory`` writes them before any planted problem.

Kinds for the memory mission:

* ``write_approval``: ``memory.write_approval: true``, so saves from the app are staged under ``pending/memory/``
  (tools/write_approval.py, Hermes 0.22.4) instead of written. The app still titles the row "Saved to memory" with a
  check, because the tool reported ``success: true, staged: true``. Detected from the pending folder and from staged
  results in the chat records, so approving the save later doesn't hide that it happened.
* ``memory_full``: MEMORY.md, seed notes included, prefilled to within a few dozen characters of its limit (2,200 by
  default). Hermes's first save comes back over the limit (tools/memory_tool_store.py:380-386) and Hermes then makes
  room itself, cutting or shortening other notes in one batch. The risk planted is losing a key note. Detected from
  the over-limit tool error and from which seed and filler notes were removed or shortened; fixed when the fact is in,
  memory is within its limit, and both key notes are still there (possibly shortened), or the learner wrote which key
  note went and why losing it was right.
* ``wrong_profile``: a second practice profile, ``academy-practice-b``, sits beside the main one, and the page shows an
  honest "Open practice chat" button for each (Field Academy never switches the app's profile). When this kind is
  drawn the second profile becomes a convincing twin: it gets the same seed notes, so a chat opened in the wrong one
  answers just like the right one. When it isn't drawn, the second profile stays empty. A fact saved in ``-b`` is not
  in ``academy-practice`` (decision Q1, Oct 21).

Details of what was planted stay on this side, in ``f_practice.plan_json``, and are shown only at Compare.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

from . import hermes_read, matching, practice_write

KINDS = ("write_approval", "memory_full", "wrong_profile")

# Notes a working setup might already hold. Used to fill MEMORY.md for the memory_full plant.
FILLER = (
    "Weekly status report goes out {weekday} at {hour} pm, to the team channel, as a short list.",
    "The shared drive keeps client folders under Clients/<year>/<client name>.",
    "Invoices are numbered {invoice_prefix}-<year>-<three digits>, starting at 001 each January.",
    "Meeting notes use the headings Decisions, Owners and Dates, in that order.",
    "Draft emails are kept under {email_words} words unless asked for more.",
    "The project tracker is a spreadsheet called {tracker}, one tab per client.",
    "Dates in documents are written as 21 Oct 2026, never as 10/21/26.",
    "Time zone for scheduling is US Central unless a client says otherwise.",
    "Contract renewals are reviewed {renewal_days} days before the end date.",
    "Expense receipts go in the Receipts folder, named by date and vendor.",
    "Quotes are valid for {quote_days} days and say so on the first line.",
    "The website is edited in the CMS; never change the live page directly.",
    "Backups of the accounts file are made on the first of each month.",
    "Client calls are booked in {slot} minute slots with {gap} minutes between them.",
    "Proposal drafts are saved as PDF before they are sent, never as an editable file.",
    "New client onboarding uses the checklist in Templates/Onboarding.",
    "The newsletter goes out on the second Tuesday, drafted the Friday before.",
    "Passwords are never written in notes; the password manager holds them.",
    "Code changes go through a pull request with one reviewer before merging.",
    "Support tickets older than {ticket_days} days are raised in the Monday meeting.",
    "Brand colors are navy and gold; logos come from the Brand folder only.",
    "Holiday schedule: office closed the last week of December.",
    "Vendor payments run on the {pay_day} and the last business day of the month.",
    "Social posts are drafted on Monday and scheduled for Wednesday.",
    "Reports cite the source and date of every number they use.",
    "The printer on the second floor is the one that handles card stock.",
    "Board packets go out {packet_days} days before each board meeting.",
    "Summaries start with the decision needed, then the background.",
    "File names use lowercase words joined by hyphens, with the date first.",
    "Phone messages are logged in the Calls sheet with the time and callback number.",
)
# Names and numbers in the filler, drawn per learner seed with the order of the notes (decisions from review 2: plant
# parameters vary per seed, so two learners don't get identical plants).
FILLER_PARAMS = {
    "weekday": ("Friday", "Thursday", "Monday"),
    "hour": ("3", "4", "5"),
    "invoice_prefix": ("INV", "IN", "BILL"),
    "email_words": ("100", "120", "150"),
    "tracker": ("Tracker 2026", "Client Board", "Work Tracker"),
    "renewal_days": ("30", "45", "60"),
    "quote_days": ("14", "21", "30"),
    "slot": ("30", "45"),
    "gap": ("10", "15"),
    "ticket_days": ("2", "3", "5"),
    "pay_day": ("1st", "15th", "20th"),
    "packet_days": ("five", "seven", "ten"),
}
# How much room is left free under the limit, also drawn per seed: between LOW and HIGH characters, each picked from
# its own range, so the planted value differs between learners.
FILL_LOW = (25, 45)
FILL_HIGH = (70, 110)


def margin(rng) -> tuple:
    return rng.randint(*FILL_LOW), rng.randint(*FILL_HIGH)


def filler_notes(rng) -> list:
    """The filler pool for one plant: shuffled, with its names and numbers filled in."""
    pool = list(FILLER)
    rng.shuffle(pool)
    values = {name: rng.choice(choices) for name, choices in sorted(FILLER_PARAMS.items())}
    return [re.sub(r"\{([a-z_]+)\}", lambda m: values.get(m.group(1), m.group(0)), note) for note in pool]


def _rng(seed: str, kind: str) -> random.Random:
    return random.Random(f"field-academy-foundations:{seed}:{kind}")


def _short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _entries(home) -> list:
    mem = hermes_read.memory(home)
    if not mem.get("readable"):
        return []
    return list(mem["memory"]["entries"]) + list(mem["user"]["entries"])


# ------------------------------------------------------------- seed notes --
#
# A seed note counts as kept while some memory line still holds it (token overlap, matching.holds), so a note Hermes
# shortened to make room is "shortened", not "removed". Only a note no line holds any more is removed.

SEED_OVERLAP = 0.6


def note_state(entries, note: str) -> str:
    """kept, shortened or removed."""
    if note in entries:
        return "kept"
    return "shortened" if matching.holds(entries, note, threshold=SEED_OVERLAP) else "removed"


def clean_seed(notes) -> dict:
    """Seed notes from a mission (``[{"text", "key"}]``) as ``{"notes": [...], "key": [...]}``. Refuses a separator."""
    out = {"notes": [], "key": []}
    for item in notes or []:
        text = str((item or {}).get("text", "")).strip() if isinstance(item, dict) else str(item or "").strip()
        if not text:
            continue
        if hermes_read.DELIM.strip() in text.split("\n") or len(text) > 240:
            raise ValueError("A seed note must be one short line.")
        out["notes"].append(text)
        if isinstance(item, dict) and item.get("key"):
            out["key"].append(text)
    return out


def seed_memory(home, row, seed: dict) -> dict:
    """Write the seed notes as the whole of MEMORY.md. Before any planted problem, before the first chat."""
    notes = list((seed or {}).get("notes") or [])
    if not notes:
        return {"notes": [], "key": []}
    practice_write.write_memory(home, row, "memory", notes)
    return {"notes": notes, "key": list(seed.get("key") or [])}


def key_notes(home, seed: dict, note=None) -> dict:
    """Are the key seed notes still in memory? ``explained`` when the learner wrote which one went and why that was right.

    The written answer counts when it names a key note that is gone (half its words or more) and gives a reason of at
    least eight words. ``ok`` is true when every key note is kept or shortened, or the loss is explained.
    """
    entries = _entries(home)
    key = list((seed or {}).get("key") or [])
    states = {text: note_state(entries, text) for text in key}
    gone = [text for text, state in states.items() if state == "removed"]
    why = str((note or {}).get("removed_ok") or "").strip()
    explained = bool(gone) and len(matching.tokens(why)) >= 8 and any(matching.overlap(why, text) >= 0.5 for text in gone)
    return {"states": states, "gone": gone, "explained": explained, "ok": not gone or explained}


# ---------------------------------------------------------------- planters --


def _plant_write_approval(ctx) -> dict:
    practice_write.set_config(ctx["home"], ctx["row"], {"memory.write_approval": True})
    return {"key": "memory.write_approval", "value": True}


def _plant_memory_full(ctx) -> dict:
    home = ctx["home"]
    limit = hermes_read.limits(home)["memory"]
    entries = list(hermes_read.memory(home)["memory"]["entries"])
    pool = filler_notes(ctx["rng"])
    added = []
    low, high = margin(ctx["rng"])
    for note in pool * 4:
        trial = hermes_read.DELIM.join(entries + [note])
        if len(trial) > limit - low:
            continue
        entries.append(note)
        added.append(note)
        if len(trial) >= limit - high:
            break
    chars = len(hermes_read.DELIM.join(entries))
    if chars < limit - high * 2:
        raise ValueError("Field Academy couldn't fill the practice memory close enough to its limit.")
    practice_write.write_memory(home, ctx["row"], "memory", entries)
    return {"limit": limit, "filled_to": chars, "free": limit - chars, "filler": added, "margin": [low, high],
            "seed": list((ctx.get("seed") or {}).get("notes") or []), "key": list((ctx.get("seed") or {}).get("key") or [])}


def _plant_wrong_profile(ctx) -> dict:
    partner = ctx.get("partner_row")
    if not partner or partner.get("status") not in ("ready", "planted") or not Path(partner.get("path", "")).is_dir():
        raise ValueError("This plant needs the second practice profile, academy-practice-b, made and recorded first.")
    seed = ctx.get("seed") or {}
    if seed.get("notes") and partner.get("status") == "ready":
        # The twin: the same seed notes, so a chat in the wrong profile answers like the right one.
        practice_write.write_memory(partner["path"], partner, "memory", seed["notes"])
    decoy = hermes_read.memory(partner["path"])
    return {"decoy": partner["name"], "decoy_path": partner["path"],
            "decoy_entries": [_short(e) for e in decoy["memory"]["entries"] + decoy["user"]["entries"]] if decoy.get("readable") else []}


# --------------------------------------------------------------- detectors --


def _tool_results(home) -> list:
    """The memory tool's results in the practice profile's chats, parsed. Unparseable results are skipped."""
    found = hermes_read.messages(home)
    out = []
    for row in found.get("messages", []) if found.get("readable") else []:
        if row.get("role") != "tool" or row.get("tool_name") != "memory":
            continue
        try:
            body = json.loads(row.get("content") or "")
        except ValueError:
            continue
        if isinstance(body, dict):
            out.append({"session_id": row.get("session_id"), "timestamp": row.get("timestamp"), "body": body})
    return out


def _staged_results(home) -> list:
    """Saves Hermes reported as staged (``success: true, staged: true``): the app titles these "Saved to memory"."""
    return [r for r in _tool_results(home) if r["body"].get("success") is True and r["body"].get("staged") is True]


def _detect_write_approval(home, details) -> dict:
    staged = hermes_read.pending(home).get("memory", [])
    said = _staged_results(home)
    key = hermes_read.config(home).get("values", {}).get("memory.write_approval")
    return {
        "fired": bool(staged) or bool(said),
        "facts": [{"label": "Saves waiting for approval", "value": str(len(staged))},
                  {"label": "Saves Hermes staged in a chat", "value": str(len(said))},
                  {"label": "memory.write_approval", "value": "on" if key is True else "off"}],
        "evidence": [("pending", s["rel_path"], hermes_read.pending_words(s)) for s in staged[:2]]
        + [("tool_result", "state.db", str(r["body"].get("message", ""))) for r in said[:1]],
    }


def _memory_errors(home) -> list:
    out = []
    for result in _tool_results(home):
        body = result["body"]
        error = str(body.get("error", "")) if body.get("success") is False else ""
        if "exceed the limit" in error or "would exceed" in error:
            out.append({"session_id": result["session_id"], "timestamp": result["timestamp"], "error": error})
    return out


def _cuts(home, details) -> dict:
    """Which of the notes Field Academy put in MEMORY.md were shortened or removed since."""
    entries = _entries(home)
    out = {"shortened": [], "removed": []}
    for note in list(details.get("seed") or []) + [n for n in details.get("filler") or [] if isinstance(n, str) and len(n) > 12]:
        state = note_state(entries, note)
        if state != "kept":
            out[state].append(note)
    return out


def _detect_memory_full(home, details) -> dict:
    errors = _memory_errors(home)
    mem = hermes_read.memory(home)
    used = mem["memory"]["chars"] if mem.get("readable") else 0
    cuts = _cuts(home, details)
    keys = key_notes(home, details)
    facts = [{"label": "Memory saves refused for space", "value": str(len(errors))},
             {"label": "MEMORY.md used", "value": f"{used:,} of {details.get('limit', 2200):,} characters"},
             {"label": "Notes Hermes cut to make room", "value": str(len(cuts["removed"]))},
             {"label": "Notes Hermes shortened", "value": str(len(cuts["shortened"]))}]
    if details.get("key"):
        kept = sum(1 for state in keys["states"].values() if state != "removed")
        facts.append({"label": "Notes the practice jobs rely on, still there", "value": f"{kept} of {len(keys['states'])}"})
    return {
        "fired": bool(errors) or bool(cuts["removed"]) or bool(cuts["shortened"]),
        "facts": facts,
        "evidence": [("tool_error", "state.db", e["error"]) for e in errors[:1]] + [("removed_note", "memories/MEMORY.md", n) for n in keys["gone"][:2]],
    }


def _detect_wrong_profile(home, details) -> dict:
    decoy = details.get("decoy_path", "")
    said = hermes_read.user_message_count(decoy) if decoy and Path(decoy).is_dir() else 0
    mem = hermes_read.memory(decoy) if decoy and Path(decoy).is_dir() else {"readable": False}
    new = []
    if mem.get("readable"):
        before = set(details.get("decoy_entries") or [])
        new = [e for e in mem["memory"]["entries"] + mem["user"]["entries"] if _short(e) not in before]
    return {
        "fired": bool(said) or bool(new),
        "facts": [{"label": f"Messages sent in {details.get('decoy', 'the second profile')}", "value": str(said or 0)},
                  {"label": f"New memory lines in {details.get('decoy', 'the second profile')}", "value": str(len(new))}],
        "evidence": [("memory", "memories (second profile)", e) for e in new[:2]],
    }


# ----------------------------------------------------------- fix-verifiers --


def _verify_write_approval(home, details, fact, note=None) -> dict:
    line = matching.holds(_entries(home), fact)
    key = hermes_read.config(home).get("values", {}).get("memory.write_approval")
    staged = hermes_read.pending(home).get("memory", [])
    cause_gone = key is not True or not staged
    if line and cause_gone:
        return {"fixed": True, "why": "The fact is in memory and no save is left waiting for approval."}
    if not line:
        return {"fixed": False, "why": "The fact is not in the practice profile's memory files yet."}
    return {"fixed": False, "why": "Saves are still being held for approval."}


def _verify_memory_full(home, details, fact, note=None) -> dict:
    mem = hermes_read.memory(home)
    line = matching.holds(_entries(home), fact)
    within = mem.get("readable") and mem["memory"]["chars"] <= mem["memory"]["limit"]
    if not line:
        return {"fixed": False, "why": "The fact is not in memory yet."}
    if not within:
        return {"fixed": False, "why": "Memory is over its limit."}
    keys = key_notes(home, details, note)
    if not keys["ok"]:
        return {"fixed": False, "why": f"To make room, Hermes cut a note the practice jobs rely on: \"{keys['gone'][0]}\". Put it back "
                                       "and cut something else, or write which note went and why losing it was right."}
    return {"fixed": True, "why": "Space was made, the fact is in memory, and the notes the jobs rely on are still there."
            if not keys["gone"] else "Space was made, the fact is in memory, and you said why the note that went could go."}


def _verify_wrong_profile(home, details, fact, note=None) -> dict:
    line = matching.holds(_entries(home), fact)
    if line:
        return {"fixed": True, "why": "The fact is in academy-practice, the profile the mission named."}
    return {"fixed": False, "why": "The fact is not in academy-practice's memory."}


REGISTRY = {
    "write_approval": {"plant": _plant_write_approval, "detect": _detect_write_approval, "verify": _verify_write_approval},
    "memory_full": {"plant": _plant_memory_full, "detect": _detect_memory_full, "verify": _verify_memory_full},
    "wrong_profile": {"plant": _plant_wrong_profile, "detect": _detect_wrong_profile, "verify": _verify_wrong_profile},
}
from . import plants_b as _plants_b  # noqa: E402  missions 7 to 11
REGISTRY.update(_plants_b.REGISTRY)
KINDS = KINDS + tuple(k for k in _plants_b.REGISTRY if k not in KINDS)
SETUPS = dict(_plants_b.SETUPS)  # a mission's setup step (lab.setup), run before its planted problems


def run_setup(name: str, home, row, seed: str) -> dict:
    """A mission's setup step: what every learner gets (sample files, a connector, settings). Hidden like a plant."""
    if name not in SETUPS:
        raise ValueError(f"Unknown practice setup: {name}")
    return SETUPS[name]({"home": Path(home), "row": row, "rng": _rng(seed, "setup:" + name), "seed": seed})


def plant_all(home, row, kinds, seed: str, partner_row=None, seed_notes=None, setup=None) -> dict:
    """Plant each kind in order, after the seed notes. Returns the hidden details, by kind."""
    unknown = [k for k in kinds if k not in REGISTRY]
    if unknown:
        raise ValueError(f"Unknown planted problem: {unknown[0]}")
    out = {}
    for kind in kinds:
        ctx = {"home": Path(home), "row": row, "rng": _rng(seed, kind), "partner_row": partner_row, "seed": seed_notes or {}, "setup": setup or {}}
        out[kind] = REGISTRY[kind]["plant"](ctx)
    return out


def detect(kind: str, home, details) -> dict:
    return REGISTRY[kind]["detect"](Path(home), details or {})


def verify(kind: str, home, details, fact, note=None) -> dict:
    return REGISTRY[kind]["verify"](Path(home), details or {}, fact, note)


# Missions 1, 2, 4, 5 and 6 (0.9 M6, part A) register their planted problems here.
from . import plants_a as _plants_a  # noqa: E402

REGISTRY.update(_plants_a.REGISTRY)
KINDS = KINDS + tuple(k for k in _plants_a.REGISTRY if k not in KINDS)

# The Intermediate core missions (School of Hermes, level 2): f.delegation and f.toolsets.
from . import plants_c as _plants_c  # noqa: E402

REGISTRY.update(_plants_c.REGISTRY)
KINDS = KINDS + tuple(k for k in _plants_c.REGISTRY if k not in KINDS)
SETUPS.update(_plants_c.SETUPS)

# The teaching missions on the Guide trail: f.teach-profile, f.teach-walkthrough and f.teach-review.
from . import plants_t as _plants_t  # noqa: E402

REGISTRY.update(_plants_t.REGISTRY)
KINDS = KINDS + tuple(k for k in _plants_t.REGISTRY if k not in KINDS)
SETUPS.update(_plants_t.SETUPS)
