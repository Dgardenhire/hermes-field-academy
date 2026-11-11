"""Setups and planted problems for the teaching missions on the Guide trail: you help another person use Hermes.
Same rules as plants.py, plants_b.py and plants_c.py: writes go only through practice_write.py, into a recorded
practice profile nobody has chatted in yet; names vary by the learner's seed; details stay hidden until Compare.

Setups (``lab.setup``):

* ``teach_profile`` (f.teach-profile): a brief from the person you're setting Hermes up for, in the practice folder.
* ``teach_walkthrough`` (f.teach-walkthrough): the same kind of brief, a profile already set up for that person (SOUL.md,
  one memory line, one skill) and a colleague's draft walkthrough.
* ``teach_review`` (f.teach-review): a saved Field Record folder from another learner, under ``their-record/`` in the
  practice folder, built from a real record body (content/foundations/data/teach-record.json) with the holder's name
  set and the record number and fingerprints made again.

Kinds: ``approvals_off`` and ``wide_connector`` are reused for f.teach-profile; ``stale_skill_name`` and
``unsafe_tip`` (f.teach-walkthrough); ``edited_excerpt`` and ``overclaim`` (f.teach-review).
"""

from __future__ import annotations

import hashlib
import json
import re  # noqa: F401
from pathlib import Path

from . import hermes_read, hermes_read_b, practice_write

PEOPLE = (
    {"name": "Marisol Vega", "first": "Marisol", "work": "a bike repair shop", "word": "bike",
     "fact": "The shop closes at 5 pm on Saturdays", "fact_words": ["saturday", "5"],
     "never": "Never email a customer without asking Marisol first", "never_words": ["email", "ask"]},
    {"name": "Desmond Achebe", "first": "Desmond", "work": "a two-van removals firm", "word": "removals",
     "fact": "Quotes are valid for 14 days", "fact_words": ["14", "quote"],
     "never": "Never book a job for a Sunday", "never_words": ["sunday", "book"]},
    {"name": "Hana Kobayashi", "first": "Hana", "work": "a ceramics studio that runs evening classes", "word": "ceramics",
     "fact": "Classes are capped at 8 students", "fact_words": ["8", "student"],
     "never": "Never share a student's phone number", "never_words": ["phone", "share"]},
    {"name": "Rory Fitzgerald", "first": "Rory", "work": "a small accountancy practice", "word": "accountancy",
     "fact": "Tax deadlines go in the calendar a month early", "fact_words": ["month", "deadline"],
     "never": "Never send a client's figures by text message", "never_words": ["text", "figure"]},
)

TITLES = {
    "stale_skill_name": "The colleague's draft named a skill that doesn't exist",
    "unsafe_tip": "The colleague's draft told the person to answer every permission card with yes",
    "edited_excerpt": "An excerpt in their record was changed after it was saved",
    "overclaim": "Their own words claimed more than their record shows",
}


def _person(ctx) -> dict:
    return dict(ctx["rng"].choice(PEOPLE))


def _brief(person) -> str:
    return (f"From {person['name']}:\n\n"
            f"I run {person['work']}. I'd like Hermes to help with the paperwork, but I don't use the command line and I "
            f"don't want it running programs.\n\n"
            f"Something it should always know: {person['fact']}.\n"
            f"A rule it must keep: {person['never']}.\n")


def _setup_teach_profile(ctx) -> dict:
    home, row = ctx["home"], ctx["row"]
    folder = practice_write.ensure_practice_folder(home, row)
    person = _person(ctx)
    practice_write.write_practice_file(home, row, "brief.txt", _brief(person))
    return {"folder": folder, "person": person}


SKILL = "academy-weekly-orders"
OUTPUT = "orders-summary.md"


def skill_text(person) -> str:
    return (f"---\nname: {SKILL}\ndescription: Summarise this week's orders for {person['first']} into {OUTPUT}\n---\n\n"
            f"# Weekly orders\n\n## When to use it\nWhen {person['first']} asks for the weekly orders.\n\n"
            f"## Steps\n1. Read every file in orders/ in the practice folder.\n2. Write {OUTPUT} in the practice folder, one line per order.\n\n"
            f"## Pitfalls\nLeave the order files where they are.\n\n## Check\n{OUTPUT} has one line per file in orders/.\n")


DRAFT = """# Your Hermes, week by week

1. Open the Hermes app and click your profile, {profile}.
2. Start a new chat and type: run the {skill} skill.
3. Hermes writes {output} in your practice folder. Open it and check there's one line per order.
4. If Hermes asks permission before doing something, read what it wants to do. Say yes only if it matches the job.
"""


def _setup_teach_walkthrough(ctx) -> dict:
    home, row, rng = ctx["home"], ctx["row"], ctx["rng"]
    folder = practice_write.ensure_practice_folder(home, row)
    person = _person(ctx)
    practice_write.write_practice_file(home, row, "brief.txt", _brief(person))
    for n in range(1, 4):
        practice_write.write_practice_file(home, row, f"orders/order-{n}.txt",
                                           f"Order {n}\nItem: {rng.choice(('tyres', 'chain', 'brake pads', 'lights', 'saddle'))}\n")
    practice_write.write_memory(home, row, "memory", [f"{person['fact']}."])
    practice_write.write_skill_a(home, row, f"skills/{SKILL}/SKILL.md", skill_text(person))
    practice_write.write_practice_file(home, row, "draft-walkthrough.md",
                                       DRAFT.format(profile="academy-practice", skill=SKILL, output=OUTPUT))
    return {"folder": folder, "person": person, "skill": SKILL, "output": OUTPUT}


TEMPLATE = Path(__file__).resolve().parent / "content" / "foundations" / "data" / "teach-record.json"
HOLDERS = ("Jun Park", "Amara Osei", "Liesel Brandt", "Tomás Herrera", "Noor Haddad")
RECORD_DIR = "their-record"


def record_files(body: dict) -> dict:
    """Every file of a saved record folder, made the way field_record.write_folder makes them, as rel -> text."""
    from . import field_record

    body = dict(body)
    body.pop("number", None)
    body["number"] = field_record.record_number(body)
    files = {}
    for e in body.get("entries", []):
        for ev in e.get("evidence", []):
            if ev.get("excerpt_file") and not ev.get("withheld"):
                files[ev["excerpt_file"]] = ev.get("excerpt", "")
    stored = json.dumps(body, ensure_ascii=False, sort_keys=True, indent=1)
    files["record.json"] = stored
    files["record.md"] = field_record.record_markdown(body)
    files["README.txt"] = field_record.readme_text(body)
    files["MANIFEST.sha256"] = "".join(f"{hashlib.sha256(files[rel].encode('utf-8')).hexdigest()}  {rel}\n" for rel in sorted(files))
    return files


def write_record(home, row, files: dict) -> None:
    for rel, text in files.items():
        practice_write.write_practice_file(home, row, f"{RECORD_DIR}/{rel}", text)


def _setup_teach_review(ctx) -> dict:
    home, row, rng = ctx["home"], ctx["row"], ctx["rng"]
    folder = practice_write.ensure_practice_folder(home, row)
    body = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    holder = rng.choice(HOLDERS)
    body["scope"]["holder"]["name"] = holder
    body["limits"]["text"] = "It shows practice work on my own computer. Nobody else watched, and my own Hermes graded my answers."
    body["case"] = {"text": "", "checked_by": "you wrote it", "note": "No case was written for this record."}
    files = record_files(body)
    write_record(home, row, files)
    entry = body["entries"][0]
    return {"folder": folder, "holder": holder, "mission_title": entry["mission_title"],
            "first": entry["result_first"], "after_fix": entry["result_after_fix"],
            "files": sorted(files), "number": json.loads(files["record.json"])["number"]}


SETUPS = {"teach_profile": _setup_teach_profile, "teach_walkthrough": _setup_teach_walkthrough, "teach_review": _setup_teach_review}


# -------------------------------------------------------------- walkthrough --


def _draft_path(home) -> str:
    return "draft-walkthrough.md"


def _rewrite_draft(ctx, old, new) -> None:
    text = hermes_read_b.folder_text(ctx["home"], _draft_path(ctx["home"])) or ""
    practice_write.write_practice_file(ctx["home"], ctx["row"], _draft_path(ctx["home"]), text.replace(old, new))


STALE = "weekly-orders"


def _plant_stale_skill_name(ctx) -> dict:
    _rewrite_draft(ctx, f"run the {SKILL} skill", f"run the {STALE} skill")
    return {"stale": STALE, "real": SKILL}


def walkthrough_text(home) -> str:
    return hermes_read_b.folder_text(home, "walkthrough.md", 64 * 1024) or ""


def names_stale(text, stale=STALE) -> bool:
    """Does the text name the stale skill, the bare name and not the real ``academy-`` one?"""
    import re

    return bool(re.search(rf"(?<![\w-]){re.escape(stale)}(?![\w-])", text.lower()))


def _detect_stale_skill_name(home, details) -> dict:
    text = walkthrough_text(home)
    return {"fired": bool(text) and names_stale(text, details.get("stale", STALE)),
            "facts": [{"label": "Skill the draft named", "value": details.get("stale", STALE)},
                      {"label": "Skill the profile has", "value": details.get("real", SKILL)}],
            "evidence": [("practice_file", f"{hermes_read_b.FOLDER}/draft-walkthrough.md", f"run the {details.get('stale', STALE)} skill")]}


def _verify_stale_skill_name(home, details, fact="", note=None) -> dict:
    text = walkthrough_text(home)
    if not text:
        return {"fixed": False, "why": "There's no walkthrough.md in the practice folder yet."}
    if names_stale(text, details.get("stale", STALE)):
        return {"fixed": False, "why": f"The walkthrough still names a skill called {details.get('stale', STALE)}, which the profile doesn't have."}
    return {"fixed": True, "why": "The walkthrough names only skills the profile has."}


UNSAFE = "If Hermes asks permission too often, just say yes to every card without reading it."
UNSAFE_WORDS = ("yes to every", "yes to everything", "without reading", "always allow", "approve everything", "approve every")


def _plant_unsafe_tip(ctx) -> dict:
    _rewrite_draft(ctx, "Say yes only if it matches the job.\n", f"Say yes only if it matches the job.\n5. {UNSAFE}\n")
    return {"tip": UNSAFE}


def unsafe_lines(text) -> list:
    return [ln for ln in text.splitlines() if any(w in ln.lower() for w in UNSAFE_WORDS) and not any(
        neg in ln.lower() for neg in ("never", "don't", "do not", "leave approvals on", "keep approvals on"))]


def _detect_unsafe_tip(home, details) -> dict:
    text = walkthrough_text(home)
    left = unsafe_lines(text)
    return {"fired": bool(left), "facts": [{"label": "Steps that tell them to skip the safeguard", "value": str(len(left))}],
            "evidence": [("practice_file", f"{hermes_read_b.FOLDER}/draft-walkthrough.md", details.get("tip", UNSAFE))]}


def _verify_unsafe_tip(home, details, fact="", note=None) -> dict:
    text = walkthrough_text(home)
    if not text:
        return {"fixed": False, "why": "There's no walkthrough.md in the practice folder yet."}
    left = unsafe_lines(text)
    if left:
        return {"fixed": False, "why": f"The walkthrough still tells them to skip the safeguard: \"{left[0].strip()[:120]}\"."}
    return {"fixed": True, "why": "No step tells them to approve without reading."}


# ------------------------------------------------------------------ review --


def _read_record(home) -> dict:
    text = hermes_read_b.folder_text(home, f"{RECORD_DIR}/record.json", 512 * 1024)
    return json.loads(text) if text else {}


EDIT_FILE = "evidence/01-tool-result.txt"
EDIT_TEXT = "Saved to memory."


def _plant_edited_excerpt(ctx) -> dict:
    practice_write.write_practice_file(ctx["home"], ctx["row"], f"{RECORD_DIR}/{EDIT_FILE}", EDIT_TEXT)
    return {"file": EDIT_FILE, "was": "Staged for approval. Not yet saved.", "now": EDIT_TEXT}


def mismatched(home) -> list:
    from . import field_record

    root = hermes_read.safe_path(home, f"{hermes_read_b.FOLDER}/{RECORD_DIR}")
    if root is None or not root.is_dir():
        return []
    return [r["file"] for r in field_record.check_folder(root)["files"] if not r["ok"]]


def review_text(home) -> str:
    return hermes_read_b.folder_text(home, "review.md", 64 * 1024) or ""


def _detect_edited_excerpt(home, details) -> dict:
    bad = mismatched(home)
    return {"fired": bool(bad), "facts": [{"label": "Files that don't match their fingerprint", "value": ", ".join(bad) or "none"}],
            "evidence": [("practice_file", f"{hermes_read_b.FOLDER}/{RECORD_DIR}/{details.get('file', EDIT_FILE)}", details.get("now", EDIT_TEXT))]}


def _verify_edited_excerpt(home, details, fact="", note=None) -> dict:
    text = review_text(home).lower()
    name = Path(details.get("file", EDIT_FILE)).name.lower()
    if not text:
        return {"fixed": False, "why": "There's no review.md in the practice folder yet."}
    if name not in text:
        return {"fixed": False, "why": "Your review doesn't name the file that no longer matches its fingerprint."}
    return {"fixed": True, "why": f"Your review names {Path(details.get('file', EDIT_FILE)).name}, the file that was changed."}


OVERCLAIM = "I passed every check the first time, with no help."


def _plant_overclaim(ctx) -> dict:
    body = _read_record(ctx["home"])
    body["case"] = {"text": OVERCLAIM, "checked_by": "you wrote it", "note": ""}
    files = record_files(body)
    # An excerpt changed by another plant stays changed: only the files the case touches are written again.
    for rel in ("record.json", "record.md", "README.txt", "MANIFEST.sha256"):
        practice_write.write_practice_file(ctx["home"], ctx["row"], f"{RECORD_DIR}/{rel}", files[rel])
    return {"claim": OVERCLAIM}


OVERCLAIM_WORDS = ("first time", "first try", "after a fix", "after the fix", "overclaim", "not true", "isn't true", "wrong", "doesn't match",
                   "does not match", "contradict")


def _detect_overclaim(home, details) -> dict:
    body = _read_record(home)
    return {"fired": OVERCLAIM in json.dumps(body.get("case") or {}),
            "facts": [{"label": "Their case", "value": details.get("claim", OVERCLAIM)}],
            "evidence": [("practice_file", f"{hermes_read_b.FOLDER}/{RECORD_DIR}/record.md", details.get("claim", OVERCLAIM))]}


def _verify_overclaim(home, details, fact="", note=None) -> dict:
    text = review_text(home).lower()
    if not text:
        return {"fixed": False, "why": "There's no review.md in the practice folder yet."}
    if any(w in text for w in OVERCLAIM_WORDS) and ("case" in text or "claim" in text or "first" in text):
        return {"fixed": True, "why": "Your review says their own words claim more than the record shows."}
    return {"fixed": False, "why": "Your review doesn't say whether their own words match what the record shows."}


REGISTRY = {
    "stale_skill_name": {"plant": _plant_stale_skill_name, "detect": _detect_stale_skill_name, "verify": _verify_stale_skill_name},
    "unsafe_tip": {"plant": _plant_unsafe_tip, "detect": _detect_unsafe_tip, "verify": _verify_unsafe_tip},
    "edited_excerpt": {"plant": _plant_edited_excerpt, "detect": _detect_edited_excerpt, "verify": _verify_edited_excerpt},
    "overclaim": {"plant": _plant_overclaim, "detect": _detect_overclaim, "verify": _verify_overclaim},
}
