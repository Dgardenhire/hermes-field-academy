"""Exercise the INSTALLED Field Academy against a real Hermes on a CI runner.

Run inside Hermes's own runtime (.github/platforms/hermes_run.py) with HERMES_HOME pointing at a
scratch folder the plugin was installed into. It:

1. lets Hermes's own plugin manager discover and load the installed plugin, and checks its six
   tools, two hooks and /academy command are registered with Hermes;
2. starts a mission and records progress through the backend Hermes loaded, calling the plugin's
   tools through Hermes's tool registry where a tool exists;
3. passes every mission on the shortest path, creates the path's Field Record, checks it is
   format 2, verifies it, saves it as .md and .json, reads the JSON back and verifies that too,
   and checks an edited copy fails;
4. checks Field Academy's database and saved files are inside the scratch HERMES_HOME.

No FIELD_ACADEMY_DATA_DIR override: the plugin uses Hermes's own plugin storage, as it does for
a real learner. Exits non-zero on the first failure. No model is called.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import platform
import sys
import tempfile
from pathlib import Path

PLUGIN = "field-academy"
TOOLS = ("field_academy_snapshot", "field_academy_mission", "field_academy_grade_explanation",
         "field_academy_grade_review", "field_academy_grade_deployer", "field_academy_record_evidence")


def say(*parts):
    print("[field-academy]", *parts, flush=True)


def check(cond, what):
    if not cond:
        say("FAIL:", what)
        raise SystemExit(1)
    say("ok:", what)


def main() -> int:
    os.environ.pop("FIELD_ACADEMY_DATA_DIR", None)
    home = Path(os.environ["HERMES_HOME"]).resolve()
    say("platform", platform.platform(), "python", sys.version.split()[0])
    say("HERMES_HOME", home)

    from hermes_cli import plugins as hp
    from tools.registry import registry

    hp.discover_plugins(force=True)
    manager = hp.get_plugin_manager()
    loaded = next((lp for key, lp in manager._plugins.items() if PLUGIN in (key, getattr(lp.manifest, "name", None))), None)
    check(loaded is not None, "Hermes discovered the installed plugin")
    check(loaded.enabled and not loaded.error, f"Hermes loaded it enabled with no error (error={loaded.error!r})")
    plugin_dir = Path(loaded.module.__file__).resolve().parent
    check(str(plugin_dir).startswith(str(home)), f"the loaded copy is the one installed under HERMES_HOME ({plugin_dir})")
    check(sorted(loaded.tools_registered) == sorted(TOOLS), f"Hermes registered the six tools ({loaded.tools_registered})")
    check(sorted(set(loaded.hooks_registered)) == ["post_tool_call", "pre_llm_call"], f"Hermes registered both hooks ({loaded.hooks_registered})")
    check(hp.get_plugin_command_handler("academy") is not None, "Hermes registered /academy")
    pkg = loaded.module.__name__
    state = importlib.import_module(f"{pkg}.state")
    curriculum = importlib.import_module(f"{pkg}.curriculum")
    importlib.import_module(f"{pkg}.dashboard.plugin_api")
    say("ok: the dashboard routes module imports in Hermes's runtime")

    def tool(name, args):
        entry = registry.get_entry(name)
        check(entry is not None, f"{name} is in Hermes's tool registry")
        out = json.loads(entry.handler(args, task_id="ci"))
        check("error" not in out, f"{name} answered ({str(out.get('error', ''))[:200]})")
        return out

    snap = tool("field_academy_snapshot", {})
    say("snapshot keys:", sorted(snap)[:12])
    db = Path(state.data_dir()).resolve()
    check(str(db).startswith(str(home)), f"Field Academy's database is under the scratch home ({db})")

    # The shortest path, so a whole path can be passed and a Field Record created.
    track_id = min(curriculum.TRACKS, key=lambda t: len(curriculum.TRACKS[t]["missions"]))
    missions = [m["id"] for m in curriculum.TRACKS[track_id]["missions"]]
    say("path", track_id, "missions", missions)

    # Start a mission and record progress by hand, on another path, so the record path below runs the whole way.
    other = next(t for t in curriculum.TRACKS if t != track_id)
    first = curriculum.TRACKS[other]["missions"][0]["id"]
    started = state.start_mission(first)
    check(started["id"] == first, f"started mission {first}")
    mission = tool("field_academy_mission", {"mission_id": first})
    check(mission["id"] == first, "the mission tool returns the started mission")
    lesson = next(s for s in curriculum.MISSIONS[first]["steps"] if s["kind"] in ("lesson", "example", "lab"))
    after = state.update_step(first, lesson["id"], "done", "read it on a CI runner")
    status = next(s["status"] for s in after["steps"] if s["id"] == lesson["id"])
    check(status == "done", f"progress recorded on {first}/{lesson['id']} (status={status})")
    explain = next((s for s in curriculum.MISSIONS[first]["steps"] if s["kind"] == "explain"), None)
    if explain:
        state.submit_explanation(first, explain["id"], "Scheduled work runs through the gateway, a background program separate from the app window. " * 2)
        graded = tool("field_academy_grade_explanation", {"mission_id": first, "step_id": explain["id"], "score": 90,
                                                            "feedback": "Named the gateway.", "missed": []})
        check(graded.get("passed") is True, f"the explanation graded through Hermes's tool registry passed ({graded})")
    evidence = tool("field_academy_record_evidence", {"competency_id": first, "summary": "Ran it on a CI runner."})
    check(evidence.get("ok") is True, "evidence recorded through the tool")

    spec = importlib.util.spec_from_file_location("fa_ci_fixtures", plugin_dir / "harness" / "make_fixtures.py")
    fx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fx)
    work = tempfile.mkdtemp(prefix="fa-ci-docs-")
    for mission_id in missions:
        fx.pass_mission(state, curriculum, work, mission_id, 90)
        say("passed", mission_id, "status", state.mission_snapshot(mission_id).get("status"))
    track = next(t for t in state.snapshot()["tracks"] if t["id"] == track_id)
    say("path status:", track["certificate"]["status"], "passed", track["verified_missions"], "of", len(track["missions"]))
    check(track["certificate"]["status"] == "ready", "the Field Record is ready to create")

    record = state.issue_certificate(track_id, "Ada Lovelace")
    body = record["body"]
    check(body.get("record_format") == 2 and state.record_format(body) == 2, "the new Field Record is format 2")
    check(body.get("record") == "Field Academy Field Record", "it is a Field Record, not a certificate")
    check(record["valid"] and state.verify_certificate(body), f"it verifies (number {record['number']})")
    saved = state.save_certificate(track_id)
    md, js = Path(saved["markdown"]), Path(saved["json"])
    check(md.is_file() and js.is_file(), f"saved as {md.name} and {js.name}")
    check(str(js.resolve()).startswith(str(home)), f"the saved files are under the scratch home ({js.parent})")
    raw = js.read_bytes()
    stored = json.loads(raw.decode("utf-8"))
    check(state.verify_certificate(stored), "the saved JSON verifies when read back")
    check(stored["number"] == record["number"], "the saved number matches")
    edited = dict(stored, name="Mallory")
    check(not state.verify_certificate(edited), "an edited copy does not verify")
    text = md.read_text(encoding="utf-8")
    check(record["number"] in text and "Field Record" in text, "the .md carries the number and the name Field Record")

    out = hp.get_plugin_command_handler("academy")("")
    out = hp.resolve_plugin_command_result(out) if hasattr(hp, "resolve_plugin_command_result") else out
    say("/academy says:\n" + str(out))
    check("created, number " + record["number"] in str(out), "/academy shows the created Field Record")
    final = tool("field_academy_snapshot", {})
    say("final compact snapshot:", json.dumps(final)[:600])

    say("ALL CHECKS PASSED on", platform.system())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
