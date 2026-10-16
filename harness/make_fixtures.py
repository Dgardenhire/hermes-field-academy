#!/usr/bin/env python3
"""Build harness/fixtures.json from the real backend.

Each state is a real passport from state.snapshot(), produced by driving the
real state module in a throwaway data folder, so the screens render exactly
what the backend sends. Time is moved with store.clock so reviews come due
without waiting. No Hermes command runs; nothing under ~/.hermes is touched.

    python3 harness/make_fixtures.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANSWER = "Scheduled work runs through the gateway, a background program separate from the app window. " * 2
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=timezone.utc)

# Words a generated document draws on, so no two sections share their text.
LEXICON = (
    "harbor lantern orchard copper meadow signal anchor ribbon granite willow compass ember pebble thistle "
    "quarry beacon saddle fennel cobalt juniper sparrow timber vellum walnut yarrow zephyr bramble cedar delta "
    "falcon gravel hollow indigo kestrel lichen marble nettle onyx pewter quartz russet sorrel tundra umber "
    "violet wicker amber birch clover drift elm flint glade heron iris jasper knoll larch moss nutmeg oak "
    "plume quill reed sage tallow upland vale wren yew zinc alder basalt cinder dune eddy fjord grove haze"
).split()


def load(data_dir, name):
    os.environ["FIELD_ACADEMY_DATA_DIR"] = data_dir
    spec = importlib.util.spec_from_file_location(name, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    package = importlib.util.module_from_spec(spec)
    sys.modules[name] = package
    spec.loader.exec_module(package)
    return package.state, sys.modules[f"{name}.curriculum"], sys.modules[f"{name}.store"]


def set_time(store, when):
    store.clock = lambda: when


def _filler(seed, count):
    return " ".join(LEXICON[(seed * 7 + i * 3) % len(LEXICON)] + ("s" if (seed + i) % 5 == 0 else "") for i in range(count))


def section_body(rule, seed):
    """Text that satisfies a section's rule with words of its own."""
    parts = [f"For this part of our own case we noted {_filler(seed, max(8, int(rule.get('min_words', 8))))}."]
    needs = rule.get("needs", [])
    if "decision" in needs:
        parts[0] = "Yes, " + parts[0][0].lower() + parts[0][1:]
    if "name" in needs:
        parts.append("Marcus Bell reviews it.")
    if "number" in needs:
        parts.append("The count is 12.")
    if "money" in needs:
        parts.append("The price is $900 for setup.")
    if "time" in needs:
        parts.append("It runs every Friday and takes 30 minutes.")
    if "verdict" in needs:
        parts.append("Verdict: met.")
    body = " ".join(parts)
    if "list" in needs:
        body += f"\n- first item {_filler(seed + 3, 3)}\n- second item {_filler(seed + 5, 3)}\n- third item {_filler(seed + 9, 3)}"
    return body


def build_document(step):
    """A document that passes a gate's rules and isn't the worked example."""
    lines = ["# Notes", ""]
    for index, rule in enumerate(step["sections"]):
        heading = rule["heading"]
        if step.get("cross") == "criteria" and heading == "Criteria":
            body = (
                "1. The weekly summary arrives by 8 am every Monday.\n"
                "2. It lists every open order older than 7 days.\n"
                "3. I spend under 10 minutes reading it."
            )
        elif step.get("cross") == "criteria" and heading == "Evidence":
            body = (
                "1. The summary arrived at 7:52 am on 4 Mondays. Met.\n"
                "2. It listed 9 of the 11 open orders. Partly met.\n"
                "3. Reading took 6 minutes each week. Met."
            )
        else:
            body = section_body(rule, index + 1)
        lines += [f"## {heading}", body, ""]
    return "\n".join(lines)


def pass_mission(state, curriculum, data_dir, mission_id, score=86):
    mission = curriculum.MISSIONS[mission_id]
    with state._connection() as conn:
        placed = {r["step_id"] for r in conn.execute("SELECT step_id FROM mission_steps WHERE mission_id = ? AND status = 'placed'", (mission_id,))}
    for step in mission["steps"]:
        kind = step["kind"]
        if step["id"] in placed:
            continue
        if kind in ("lesson", "example", "lab"):
            state.update_step(mission_id, step["id"], "done")
        elif kind == "complete":
            answers = {part["gap"]: part["answer"] for part in step["parts"] if "gap" in part}
            state.submit_completion(mission_id, step["id"], answers)
        elif kind == "explain":
            state.submit_explanation(mission_id, step["id"], ANSWER)
            state.grade_explanation(mission_id, step["id"], score, "Named the gateway and the profile, and said how to confirm it.", [])
        elif step["verify"] == "artifact":
            target = Path(data_dir) / f"{mission_id.replace('.', '-')}-notes.md"
            target.write_text(build_document(step))
            live = {"passed": True, "title": "Hermes answered", "detail": "Hermes answered.", "facts": []} if step.get("live") else None
            outcome = state.verify_artifact(mission_id, step["id"], str(target), live=live)
            state.record_gate(mission_id, step["id"], outcome, artifact=str(target))
        else:
            state.record_gate(
                mission_id,
                step["id"],
                {"passed": True, "title": "Your answers match what Hermes reports", "detail": "Hermes answered.", "facts": []},
            )


def build(name, recipe):
    data_dir = tempfile.mkdtemp(prefix=f"fa-harness-{name}-")
    try:
        state, curriculum, store = load(data_dir, f"fa_harness_{name}")
        set_time(store, NOW)
        extra = recipe(state, curriculum, data_dir, store) or {}
        extra["models"] = {
            mission_id: {part["gap"]: part["answer"] for step in mission["steps"] if step["kind"] == "complete" for part in step["parts"] if "gap" in part}
            for mission_id, mission in curriculum.MISSIONS.items()
        }
        snapshot = json.loads(json.dumps(state.snapshot(), default=str))
        # The Deployer tier's own snapshot, from the real backend, for every state: a fresh one unless the recipe made its own.
        if "deployer" not in extra:
            import importlib

            extra["deployer"] = importlib.import_module(f"fa_harness_{name}.deployer").snapshot()
        # Paths from the throwaway folder would leak a temp path into screenshots, including the resolved form of it.
        shown = "~/.hermes/plugin-data/field-academy"
        text = json.dumps({"passport": snapshot, **extra}, default=str)
        text = text.replace(str(Path(data_dir).resolve()), shown).replace(data_dir, shown)
        return json.loads(text)
    finally:
        shutil.rmtree(data_dir, ignore_errors=True)
        os.environ.pop("FIELD_ACADEMY_DATA_DIR", None)


def fresh(state, curriculum, data_dir, store):
    return None


def progress(state, curriculum, data_dir, store):
    """Part-way: a goal, two missions passed five days ago and one yesterday, one reviewed, one changed since."""
    state.set_use_goal("Write my weekly status email from my project notes.")
    set_time(store, NOW - timedelta(days=5))
    pass_mission(state, curriculum, data_dir, "operator.runtime")
    pass_mission(state, curriculum, data_dir, "operator.desktop")
    set_time(store, NOW - timedelta(days=1))
    pass_mission(state, curriculum, data_dir, "ambassador.story")
    set_time(store, NOW - timedelta(hours=3))
    state.update_step("operator.learning", "concept", "done")
    state.update_step("operator.learning", "example", "done")
    set_time(store, NOW)
    # One mission passed under an older version of its check.
    with state._connection() as conn:
        conn.execute("UPDATE mission_versions SET passed_version = 1 WHERE mission_id = 'ambassador.story'")
    state.set_goal("operator")


def ready(state, curriculum, data_dir, store):
    state.set_use_goal("Help clients set up Hermes for their small offices.")
    for item in curriculum.TRACKS["ambassador"]["missions"]:
        pass_mission(state, curriculum, data_dir, item["id"])
    pass_mission(state, curriculum, data_dir, "operator.runtime")
    state.set_goal("ambassador")


def issued(state, curriculum, data_dir, store):
    ready(state, curriculum, data_dir, store)
    certificate = state.issue_certificate("ambassador", "Ada Lovelace")
    saved = state.save_certificate("ambassador")
    return {"certificate": certificate, "saved": saved}


def reviews(state, curriculum, data_dir, store):
    """Reviews due, one open session and one graded session, for the review screens."""
    progress(state, curriculum, data_dir, store)
    session = state.start_review()
    answers = {item["mission_id"]: "In my own words, scheduled work needs the gateway, which runs apart from the window." for item in session["items"]}
    state.submit_review(session["id"], answers)
    open_session = state.get_review_session(session["id"])
    grades = []
    for number, item in enumerate(session["items"]):
        score = [88, 62, 91][number % 3]
        grades.append({"mission_id": item["mission_id"], "score": score, "missed": [1, 2] if score < 70 else [], "feedback": "You named the gateway. You left out how you would confirm it."})
    graded = state.grade_review(session["id"], grades)
    set_time(store, NOW + timedelta(minutes=1))
    fresh_session = state.start_review(practice=True)
    return {"review_open": fresh_session, "review_submitted": open_session, "review_graded": {**state.get_review_session(session["id"]), "results": graded["results"]}}


def misses(state, curriculum, data_dir, store):
    """A document that missed twice, so the page shows the hint and the worked example."""
    state.set_use_goal("Write my weekly status email from my project notes.")
    mission_id = "integrator.discovery"
    for step in curriculum.MISSIONS[mission_id]["steps"]:
        if step["kind"] in ("lesson", "example", "lab"):
            state.update_step(mission_id, step["id"], "done")
        elif step["kind"] == "complete":
            answers = {part["gap"]: part["answer"] for part in step["parts"] if "gap" in part}
            state.submit_completion(mission_id, step["id"], answers)
    target = Path(data_dir) / "scope.md"
    target.write_text("# Scope\n\n## Client\nA company.\n\n## Workflow\nTheir work.\n\n## Owner\nThe office.\n")
    gate = next(s for s in curriculum.MISSIONS[mission_id]["steps"] if s["kind"] == "gate")
    outcome = None
    for _ in range(2):
        outcome = state.verify_artifact(mission_id, gate["id"], str(target))
        state.record_gate(mission_id, gate["id"], outcome, artifact=str(target))
    state.set_goal("integrator")
    return {"gate_outcome": outcome}


def placement(state, curriculum, data_dir, store):
    spec = curriculum.PLACEMENTS["operator"]
    answers = {q["id"]: q["answer"] if q["level"] == "beginner" else (q["answer"] + 1) % len(q["options"]) for q in spec["questions"]}
    questions = state.placement_questions("operator")
    outcome = state.submit_placement("operator", answers)
    state.set_goal("operator")
    return {"placement": questions, "placement_outcome": outcome, "placement_applied": {"levels": ["beginner"], "steps_skipped": 8}}


def main():
    recipes = (
        ("fresh", fresh), ("progress", progress), ("ready", ready), ("issued", issued),
        ("reviews", reviews), ("misses", misses), ("placement", placement),
    )
    states = {name: build(name, recipe) for name, recipe in recipes}
    sys.path.insert(0, str(ROOT / "harness"))
    import deployer_fixtures

    def deployer_recipe(make):
        def run(state, curriculum, data_dir, store):
            kit = deployer_fixtures.Kit(state, store, data_dir)
            extra = make(kit) or {}
            extra["deployer"] = kit.dep.snapshot()
            return extra

        return run

    for name, make in deployer_fixtures.RECIPES:
        states[name] = build(name, deployer_recipe(make))
    out = ROOT / "harness" / "fixtures.json"
    out.write_text(json.dumps({"states": states}, indent=1, ensure_ascii=False))
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
