#!/usr/bin/env python3
"""Flag curriculum prose that drifts out of the teaching register.

The rules and the reasoning behind them are in docs/curriculum-voice.md. This
script is the mechanical half: it walks every learner-facing string and reports
the rhetorical patterns the sources never use, with the field it came from, so a
rewrite pass has a worklist instead of a feeling.

It checks patterns, not taste. A clean run means nothing here reads as written
for effect; it does not mean the copy is good.

Usage:  python scripts/check_voice.py [--json]
Exit 1 when anything is flagged.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Words the sources never use. Each is a stand-in for a plainer phrase.
JARGON = {
    "estate": "name the actual boxes: organisations, gateways, profiles, agents",
    "coordination shape": "say chat, delegation, or board",
    "deciding property": "name the property",
    "topology decision": "say where it runs",
    "value model": "say what the old workflow cost",
    "authority boundary": "say what the agent may reach",
    "least-privilege": "say the smallest permission that still does the job",
    "the seams": "name the boundary",
    "nominalization": "",
}

CHECKS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "negation hinge",
        "Neither source argues by negation. State what the thing is.",
        re.compile(r"\b(?:is|are|was|were) not (?:a|an|the) [a-z][^.]{0,60}[.,]"),
    ),
    (
        "not X, it is Y",
        "Same move, spelled out. Say Y.",
        re.compile(r"\bnot [^.]{0,50},\s*(?:it|that|they) (?:is|are)\b"),
    ),
    (
        "meta-commentary",
        "'Most people get this wrong' is filler.",
        re.compile(r"\b(?:most people|teams get this wrong|people get this wrong|nobody does this)\b", re.I),
    ),
    (
        "invented abstraction",
        "Name the concrete thing instead.",
        re.compile(r"\b(?:the estate|coordination shape|deciding property|topology decision|value model|authority boundary|least-privilege|the seams)\b", re.I),
    ),
    (
        "nominalized deliverable",
        "A deliverable is a thing you made, said plainly.",
        re.compile(r"^The (?:vocabulary|rule|ability|capacity|map|model|decision) (?:to|that|of|with)\b"),
    ),
]

# Three consecutive short sentences in the same shape is a rhythm, not information.
TRIAD = re.compile(r"^[A-Z][^.!?]{4,40}\.$")


def load_curriculum():
    import os
    import types
    from importlib import import_module

    os.environ["FIELD_ACADEMY_DATA_DIR"] = tempfile.mkdtemp(prefix="fa-voice-")
    # A bare package: the curriculum needs no storage, so the plugin's __init__
    # (which loads state and tools) is not run.
    package = types.ModuleType("fa_voice")
    package.__path__ = [str(ROOT)]
    sys.modules["fa_voice"] = package
    return import_module("fa_voice.curriculum")


def triads(body: str) -> list[str]:
    hits = []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    for i in range(len(sentences) - 2):
        window = sentences[i : i + 3]
        if all(TRIAD.match(s) for s in window):
            shapes = {len(s.split()) for s in window}
            if max(shapes) - min(shapes) <= 3:
                hits.append(" ".join(window))
    return hits


def walk(curriculum):
    """Yield (mission_id, field, text) for every learner-facing string."""
    for mission_id, mission in curriculum.MISSIONS.items():
        for field in ("title", "promise", "outcome", "field_case"):
            if isinstance(mission.get(field), str):
                yield mission_id, field, mission[field]
        for step in mission["steps"]:
            for field in ("title", "body", "deliverable", "prompt"):
                if isinstance(step.get(field), str):
                    yield mission_id, f"{step['id']}.{field}", step[field]
            for index, item in enumerate(step.get("covers") or []):
                yield mission_id, f"{step['id']}.covers[{index}]", item
            for index, item in enumerate(step.get("coach") or []):
                yield mission_id, f"{step['id']}.coach[{index}].hint", item.get("hint", "")
                yield mission_id, f"{step['id']}.coach[{index}].example", item.get("example", "")
            for index, part in enumerate(step.get("parts") or []):
                if part.get("text"):
                    yield mission_id, f"{step['id']}.parts[{index}]", part["text"]
                if part.get("answer"):
                    yield mission_id, f"{step['id']}.parts[{index}].answer", part["answer"]
            for rule in step.get("sections") or []:
                for key in ("what", "fix", "hint", "example"):
                    if rule.get(key):
                        yield mission_id, f"{step['id']}.{rule['heading']}.{key}", rule[key]
            for key, item in (step.get("fixes") or {}).items():
                yield mission_id, f"{step['id']}.fixes.{key}.hint", item.get("hint", "")
                yield mission_id, f"{step['id']}.fixes.{key}.example", item.get("example", "")
        for field in ("use", "use_plain"):
            if mission.get(field):
                yield mission_id, field, mission[field]
        for entry in mission.get("review") or []:
            yield mission_id, f"review.{entry['id']}.question", entry["question"]
            for index, point in enumerate(entry.get("points") or []):
                for key in ("point", "hint", "example"):
                    yield mission_id, f"review.{entry['id']}.points[{index}].{key}", point.get(key, "")
    for track_id, placement in curriculum.PLACEMENTS.items():
        yield f"{track_id}.placement", "intro", placement["intro"]
        for q in placement["questions"]:
            yield f"{track_id}.placement", f"{q['id']}.question", q["question"]
            yield f"{track_id}.placement", f"{q['id']}.why", q["why"]
            for index, option in enumerate(q["options"]):
                yield f"{track_id}.placement", f"{q['id']}.option[{index}]", option


def main(argv: list[str] | None = None) -> int:
    as_json = "--json" in (argv or sys.argv[1:])
    curriculum = load_curriculum()

    findings: list[dict[str, str]] = []
    for mission_id, field, text in walk(curriculum):
        for name, reason, pattern in CHECKS:
            match = pattern.search(text)
            if match:
                findings.append(
                    {
                        "mission": mission_id,
                        "field": field,
                        "check": name,
                        "reason": reason,
                        "match": match.group(0)[:90],
                    }
                )
        for hit in triads(text):
            findings.append(
                {
                    "mission": mission_id,
                    "field": field,
                    "check": "triad",
                    "reason": "Three parallel short sentences is a rhythm, not information.",
                    "match": hit[:90],
                }
            )
        for word, advice in JARGON.items():
            if advice and re.search(rf"\b{re.escape(word)}\b", text, re.I):
                findings.append(
                    {
                        "mission": mission_id,
                        "field": field,
                        "check": "jargon",
                        "reason": advice,
                        "match": word,
                    }
                )

    if as_json:
        print(json.dumps({"count": len(findings), "findings": findings}, indent=2))
    else:
        by_mission: dict[str, list[dict[str, str]]] = {}
        for finding in findings:
            by_mission.setdefault(finding["mission"], []).append(finding)
        for mission_id, items in by_mission.items():
            print(f"\n{mission_id}  ({len(items)})")
            for item in items:
                print(f"  [{item['check']}] {item['field']}: {item['match']!r}")
                print(f"      {item['reason']}")
        print(f"\n{len(findings)} finding(s) across {len(by_mission)} mission(s)")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
