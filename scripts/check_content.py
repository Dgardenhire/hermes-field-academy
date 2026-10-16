#!/usr/bin/env python3
"""Validate content/ against docs/content-format.md.

    python3 scripts/check_content.py            # every path
    python3 scripts/check_content.py operator   # one path
    python3 scripts/check_content.py --json

Checks that every mission has what the learning design needs (a worked example,
a half-finished one, coaching for every point, three review questions, a strong
gate), that each worked example passes the very check the learner faces, that the
half-finished example passes once its gaps hold the model answers, and that the
words follow docs/curriculum-voice.md. Exit 1 when anything is wrong.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

KINDS = ("lesson", "example", "complete", "lab", "explain", "gate")
DESKTOP_FIXES = {
    "runtime": {"not_connected", "no_answer", "missing_profile", "profile_mismatch", "connection_mismatch"},
    "workspace": {"no_sessions", "no_marker"},
    "knowledge": {"no_skills", "no_marked_skill"},
    "automation": {"no_jobs", "no_marked_job", "no_schedule", "prompt_thin"},
}
LIVE_CHECKS = {"routes", "connections", "estate"}
LEVELS = ("beginner", "intermediate", "advanced")

NEGATION = [
    re.compile(r"\bnot [^.;]{1,60}, but\b", re.I),
    re.compile(r"\b(?:is|are|was|were) not (?:a|an|the) [a-z][^.]{0,60}[.,]"),
    re.compile(r", not (?:a|an|the|just|only) ", re.I),
    re.compile(r"\bnot [^.]{0,50},\s*(?:it|that|they) (?:is|are)\b"),
    re.compile(r"\b(?:most people|teams get this wrong|people get this wrong|nobody does this)\b", re.I),
]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⭕]")


def load():
    import types
    from importlib import import_module

    os.environ["FIELD_ACADEMY_DATA_DIR"] = tempfile.mkdtemp(prefix="fa-content-")
    # A bare package: curriculum, documents and content need no storage, so the
    # plugin's __init__ (which loads state and tools) is not run.
    package = types.ModuleType("fa_content_check")
    package.__path__ = [str(ROOT)]
    sys.modules["fa_content_check"] = package

    return (
        import_module("fa_content_check.curriculum"),
        import_module("fa_content_check.documents"),
        import_module("fa_content_check.content"),
    )


def words(text):
    return len(str(text).split())


def composite(parts):
    return "".join(p["text"] if "text" in p else p["answer"] for p in parts)


def check_text(where, text, problems, limit=None):
    if not isinstance(text, str) or not text.strip():
        problems.append(f"{where}: empty")
        return
    if limit and words(text) > limit:
        problems.append(f"{where}: {words(text)} words, limit {limit}")
    for pattern in NEGATION:
        match = pattern.search(text)
        if match:
            problems.append(f"{where}: negation device or filler: {match.group(0)[:60]!r}")
    if EMOJI.search(text):
        problems.append(f"{where}: emoji")


def check_points(where, points, problems):
    if not points:
        problems.append(f"{where}: no points")
    for index, item in enumerate(points):
        for key, limit in (("point", 40), ("hint", 45), ("example", 60)):
            check_text(f"{where}[{index}].{key}", item.get(key), problems, limit)


def check_mission(mission_id, spec, step_covers, documents, problems):
    def bad(message):
        problems.append(f"{mission_id}: {message}")

    minutes = spec.get("minutes") or {}
    for kind in KINDS:
        if not isinstance(minutes.get(kind), int) or minutes[kind] <= 0:
            bad(f"minutes.{kind} must be a positive whole number")
    use = spec.get("use", "")
    if "{goal}" not in use:
        bad('use must contain "{goal}" once')
    if "{goal}" in spec.get("use_plain", "{goal}"):
        bad('use_plain must exist and must not contain "{goal}"')
    check_text(f"{mission_id}.use", use.replace("{goal}", "X"), problems, 50)
    check_text(f"{mission_id}.use_plain", spec.get("use_plain", ""), problems, 45)

    worked = spec.get("worked") or {}
    check_text(f"{mission_id}.worked.intro", worked.get("intro"), problems, 70)
    parts = worked.get("parts") or []
    if not 3 <= len(parts) <= 5:
        bad("worked.parts needs 3 to 5 labelled parts")
    for index, part in enumerate(parts):
        check_text(f"{mission_id}.worked.parts[{index}].label", part.get("label"), problems, 8)
        check_text(f"{mission_id}.worked.parts[{index}].text", part.get("text"), problems, 70)

    complete = spec.get("complete") or {}
    check_text(f"{mission_id}.complete.intro", complete.get("intro"), problems, 55)
    cparts = complete.get("parts") or []
    gaps = [p for p in cparts if "gap" in p]
    if not 2 <= len(gaps) <= 4:
        bad("complete.parts needs 2 to 4 gaps")
    if len({g.get("gap") for g in gaps}) != len(gaps):
        bad("complete gap ids must be unique")
    for gap in gaps:
        for key in ("gap", "prompt", "answer", "min_words"):
            if key not in gap:
                bad(f"complete gap {gap.get('gap')} missing {key}")
        if words(gap.get("answer", "")) < int(gap.get("min_words", 1)):
            bad(f"complete gap {gap.get('gap')}: the model answer is shorter than min_words")
        for kind in gap.get("needs", []):
            if kind not in documents.NEEDS:
                bad(f"complete gap {gap.get('gap')}: unknown need {kind}")
            elif not documents.has_need(kind, gap.get("answer", "")):
                bad(f"complete gap {gap.get('gap')}: the model answer fails its own need {kind}")
        check_text(f"{mission_id}.complete.{gap.get('gap')}.prompt", gap.get("prompt"), problems, 30)
        check_text(f"{mission_id}.complete.{gap.get('gap')}.answer", gap.get("answer"), problems, 60)

    coach = spec.get("coach") or (spec.get("explain") or {}).get("coach") or []
    if len(coach) != len(step_covers):
        bad(f"coach has {len(coach)} entries and the question has {len(step_covers)} points. They must match one for one")
    for index, item in enumerate(coach):
        check_text(f"{mission_id}.coach[{index}].hint", item.get("hint"), problems, 45)
        check_text(f"{mission_id}.coach[{index}].example", item.get("example"), problems, 60)

    review = spec.get("review") or []
    if [r.get("id") for r in review] != ["r1", "r2", "r3"]:
        bad("review needs exactly three questions with ids r1, r2, r3")
    for r in review:
        check_text(f"{mission_id}.review.{r.get('id')}.question", r.get("question"), problems, 60)
        if len(r.get("points") or []) < 2:
            bad(f"review {r.get('id')} needs at least 2 points")
        check_points(f"{mission_id}.review.{r.get('id')}.points", r.get("points") or [], problems)

    if not spec.get("revisions"):
        bad("revisions needs at least one entry")
    for entry in spec.get("revisions", []):
        check_text(f"{mission_id}.revisions.summary", entry.get("summary"), problems, 60)

    gate = spec.get("gate") or {}
    check_text(f"{mission_id}.gate.title", gate.get("title"), problems, 12)
    check_text(f"{mission_id}.gate.body", gate.get("body"), problems, 45)
    check_text(f"{mission_id}.gate.proof", gate.get("proof"), problems, 45)
    verify = gate.get("verify")
    if verify == "artifact":
        check_artifact_gate(mission_id, spec, gate, documents, problems)
    elif verify == "desktop":
        check = gate.get("check")
        if check not in DESKTOP_FIXES:
            bad(f"gate.check {check!r} is not one of {sorted(DESKTOP_FIXES)}")
        else:
            missing = DESKTOP_FIXES[check] - set(gate.get("fixes", {}))
            if missing:
                bad(f"gate.fixes is missing {sorted(missing)}")
        for key, item in (gate.get("fixes") or {}).items():
            check_text(f"{mission_id}.gate.fixes.{key}.hint", item.get("hint"), problems, 45)
            check_text(f"{mission_id}.gate.fixes.{key}.example", item.get("example"), problems, 60)
        if check in ("workspace", "knowledge", "automation") and not gate.get("marker"):
            bad("gate.marker is required for this check")
    else:
        bad(f"gate.verify must be artifact or desktop, got {verify!r}")


def check_artifact_gate(mission_id, spec, gate, documents, problems):
    def bad(message):
        problems.append(f"{mission_id}: {message}")

    sections = gate.get("sections") or []
    if len(sections) < 3:
        bad("an artifact gate needs at least 3 sections")
    for rule in sections:
        for key in ("heading", "min_words", "what", "hint", "example"):
            if key not in rule:
                bad(f"section {rule.get('heading')} missing {key}")
        for kind in rule.get("needs", []):
            if kind not in documents.NEEDS:
                bad(f"section {rule.get('heading')}: unknown need {kind}")
            elif "fix" not in rule:
                bad(f"section {rule.get('heading')}: a section that needs {kind} also needs a fix line")
        check_text(f"{mission_id}.section.{rule.get('heading')}.what", rule.get("what"), problems, 20)
        check_text(f"{mission_id}.section.{rule.get('heading')}.hint", rule.get("hint"), problems, 45)
        check_text(f"{mission_id}.section.{rule.get('heading')}.example", rule.get("example"), problems, 60)
    live = gate.get("live", "")
    if live and live not in LIVE_CHECKS:
        bad(f"gate.live {live!r} is not one of {sorted(LIVE_CHECKS)}")
    if live and "live_failed" not in gate.get("fixes", {}):
        bad("a gate with a live check needs fixes.live_failed")
    if gate.get("cross") not in (None, "", "criteria"):
        bad("gate.cross must be criteria or empty")
    step = {"sections": sections, "cross": gate.get("cross", "")}
    worked_doc = (spec.get("worked") or {}).get("document", "")
    if not worked_doc:
        bad("an artifact gate needs worked.document, a complete passing example")
        return
    if words(worked_doc) > 320:
        bad(f"worked.document is {words(worked_doc)} words, limit 320")
    result = documents.analyze(worked_doc, step)
    for miss in result["missing"]:
        bad(f"the worked example fails its own check: {miss['what']}")
    partial = composite((spec.get("complete") or {}).get("parts", []))
    result = documents.analyze(partial, step)
    for miss in result["missing"]:
        bad(f"the half-finished example fails once its gaps hold the model answers: {miss['what']}")
    if documents.copied_share(partial, [worked_doc]) > 0.4:
        bad("the half-finished example repeats the worked example too closely")
    for rule in sections:
        if rule["heading"].lower() not in worked_doc.lower():
            bad(f"worked.document has no {rule['heading']} heading")


def check_capstone(track_id, spec, documents, problems):
    def bad(message):
        problems.append(f"capstone {track_id}: {message}")

    for key in ("id", "title", "promise", "outcome", "level_meaning", "sources", "watch", "lesson", "lab", "explain", "gate", "worked", "complete", "use", "use_plain", "review", "minutes", "revisions"):
        if key not in spec:
            bad(f"missing {key}")
    if problems and any(p.startswith(f"capstone {track_id}: missing") for p in problems):
        return
    if spec["id"] != f"{track_id}.capstone":
        bad(f"id must be {track_id}.capstone")
    check_text(f"{track_id}.capstone.title", spec["title"], problems, 12)
    check_text(f"{track_id}.capstone.promise", spec["promise"], problems, 30)
    check_text(f"{track_id}.capstone.lesson", spec["lesson"].get("body"), problems, 90)
    check_text(f"{track_id}.capstone.lab", spec["lab"].get("body"), problems, 45)
    check_text(f"{track_id}.capstone.question", spec["explain"].get("question"), problems, 80)
    if not spec["gate"].get("cross") == "criteria":
        bad('gate.cross must be "criteria"')
    headings = [s["heading"] for s in spec["gate"].get("sections", [])]
    if "Criteria" not in headings or "Evidence" not in headings:
        bad("the gate needs sections named Criteria and Evidence")
    covers = spec["explain"].get("covers") or []
    flat = {k: v for k, v in spec.items()}
    flat["coach"] = spec["explain"].get("coach") or []
    flat["gate"] = spec["gate"]
    check_mission(spec["id"], flat, covers, documents, problems)


def check_placement(track_id, spec, problems):
    def bad(message):
        problems.append(f"placement {track_id}: {message}")

    for key in ("title", "intro", "questions"):
        if key not in spec:
            bad(f"missing {key}")
            return
    check_text(f"{track_id}.placement.intro", spec["intro"], problems, 60)
    questions = spec["questions"]
    ids = [q.get("id") for q in questions]
    if len(set(ids)) != len(ids):
        bad("question ids must be unique")
    for level in LEVELS:
        count = sum(1 for q in questions if q.get("level") == level)
        if count != 2:
            bad(f"level {level} needs exactly 2 questions, has {count}")
    for q in questions:
        if q.get("level") not in LEVELS:
            bad(f"{q.get('id')}: level must be one of {LEVELS}")
        options = q.get("options") or []
        if not 3 <= len(options) <= 4:
            bad(f"{q.get('id')}: needs 3 or 4 options")
        if not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < len(options):
            bad(f"{q.get('id')}: answer must be the index of the right option")
        check_text(f"{q.get('id')}.question", q.get("question"), problems, 60)
        check_text(f"{q.get('id')}.why", q.get("why"), problems, 60)
        for option in options:
            check_text(f"{q.get('id')}.option", option, problems, 30)
        lengths = [len(o) for o in options]
        if lengths and isinstance(q.get("answer"), int) and 0 <= q["answer"] < len(lengths):
            others = [n for i, n in enumerate(lengths) if i != q["answer"]]
            ratio = lengths[q["answer"]] / (sum(others) / len(others))
            if ratio > 1.3:
                bad(f"{q.get('id')}: the right option is {round(ratio, 2)} times as long as the others on average, which gives it away. Keep it within 1.3")
    longest = sum(
        1 for q in questions
        if isinstance(q.get("answer"), int) and q.get("options") and len(q["options"][q["answer"]]) == max(len(o) for o in q["options"])
    )
    if longest > 2:
        bad(f"the right option is the longest in {longest} of {len(questions)} questions. Make a wrong option the longest in at least four")


def validate(only=None):
    curriculum, documents, content = load()
    problems: list[str] = []
    track_ids = [only] if only else list(curriculum.TRACKS)
    for track_id in track_ids:
        track = curriculum.TRACKS[track_id]
        for item in track["missions"]:
            mission_id = item["id"]
            spec = curriculum.CONTENT.get(mission_id)
            if spec is None:
                problems.append(f"{mission_id}: no content")
                continue
            if mission_id.endswith(".capstone"):
                continue
            covers = next((s["covers"] for s in item["steps"] if s["kind"] == "explain"), [])
            check_mission(mission_id, spec, covers, documents, problems)
        capstone = curriculum.CAPSTONES.get(track_id)
        if capstone is None:
            problems.append(f"capstone {track_id}: none")
        else:
            check_capstone(track_id, capstone, documents, problems)
        placement = curriculum.PLACEMENTS.get(track_id)
        if placement is None:
            problems.append(f"placement {track_id}: none")
        else:
            check_placement(track_id, placement, problems)
    return problems


def main(argv=None):
    args = [a for a in (argv if argv is not None else sys.argv[1:])]
    as_json = "--json" in args
    names = [a for a in args if not a.startswith("--")]
    problems = validate(names[0] if names else None)
    if as_json:
        print(json.dumps({"count": len(problems), "problems": problems}, indent=2))
    else:
        for line in problems:
            print(line)
        print(f"\n{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
