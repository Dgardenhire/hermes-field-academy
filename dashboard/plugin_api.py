"""Desktop API for Field Academy.

Mounted at /api/plugins/field-academy. The desktop half (desktop/plugin.js)
runs checks that need the live gateway and posts the result here; checks that
need a file run on this side, because the path lives on the backend's disk.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException


def _load_package():
    """Load the parent plugin as a package; dashboard APIs are imported as loose files."""
    package_name = "field_academy_dashboard_package"
    package = sys.modules.get(package_name)
    if package is None:
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            package_name,
            root / "__init__.py",
            submodule_search_locations=[str(root)],
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load Field Academy package")
        package = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = package
        spec.loader.exec_module(package)
    return package_name


package_name = _load_package()
state = sys.modules[f"{package_name}.state"]
diagnostics = sys.modules.get(f"{package_name}.diagnostics")
if diagnostics is None:
    from importlib import import_module

    diagnostics = import_module(f"{package_name}.diagnostics")

deployer = sys.modules.get(f"{package_name}.deployer")
if deployer is None:
    from importlib import import_module

    deployer = import_module(f"{package_name}.deployer")

practice = sys.modules.get(f"{package_name}.practice")
if practice is None:
    from importlib import import_module

    practice = import_module(f"{package_name}.practice")

foundations = sys.modules.get(f"{package_name}.foundations")
if foundations is None:
    from importlib import import_module

    foundations = import_module(f"{package_name}.foundations")

field_record = sys.modules.get(f"{package_name}.field_record")
if field_record is None:
    from importlib import import_module

    field_record = import_module(f"{package_name}.field_record")

router = APIRouter()


def _mount(module_name):
    """Add one lane's routes (the AI lane's ``routes_ai``, the Replay lane's ``routes_replay``) to this router.

    Each module defines ``mount(router)`` and registers its routes under this same prefix. A module that isn't in
    this checkout is skipped, and one that fails to load is logged and skipped, so the rest of the page still works.
    Owned by the AI lane; tell the Field Academy product owner before changing this or the two lines below it."""
    import logging
    from importlib import import_module

    try:
        module = import_module(f"{package_name}.{module_name}")
    except ModuleNotFoundError as exc:
        if exc.name == f"{package_name}.{module_name}":
            return
        logging.getLogger("hermes.plugins.field_academy").exception("field-academy: %s did not load", module_name)
        return
    except Exception:
        logging.getLogger("hermes.plugins.field_academy").exception("field-academy: %s did not load", module_name)
        return
    try:
        module.mount(router)
    except Exception:
        logging.getLogger("hermes.plugins.field_academy").exception("field-academy: %s routes did not mount", module_name)


_mount("routes_ai")
_mount("routes_replay")


def _guard(call, *args, **kwargs):
    """Run a Deployer operation and turn a plain refusal into a 400 with its message."""
    try:
        return call(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/passport")
async def passport():
    return state.snapshot()


@router.get("/summary")
async def summary():
    """The compact shape, for the status bar and the agent."""
    return state.compact()


@router.post("/goal")
async def goal(body: dict):
    try:
        return state.set_goal(body.get("track_id", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orientation")
async def orientation(body: dict):
    try:
        return state.set_orientation(body.get("track_id", ""), body.get("context", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mission/{mission_id}")
async def mission(mission_id: str):
    try:
        return state.mission_snapshot(mission_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/mission/{mission_id}/start")
async def mission_start(mission_id: str):
    try:
        return state.start_mission(mission_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/mission/{mission_id}/step/{step_id}")
async def mission_step(mission_id: str, step_id: str, body: dict):
    try:
        return state.update_step(mission_id, step_id, body.get("status", "done"), body.get("note", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/gate/{mission_id}/{step_id}")
async def gate(mission_id: str, step_id: str, body: dict):
    """Close a gate.

    ``path`` given  -> this side reads, checks and hashes the file (artifact gate).
    A gate that also reads the live app sends the page's reading as ``live``.
    ``outcome`` given -> taken only for a step the page checks itself (verify
    "desktop"); state.record_gate keeps its plain parts and labels it as
    reported by the page. A sent outcome for any other gate is refused.
    """
    try:
        if isinstance(body.get("text"), str) and body["text"].strip() and not body.get("path"):
            # A pasted document, for a Hermes that runs on another computer: saved in Field
            # Academy's own folder, then checked exactly like a typed path.
            body = {**body, "path": state.save_pasted_document(mission_id, step_id, body["text"])}
        if body.get("path"):
            outcome = state.record_gate(
                mission_id,
                step_id,
                None,
                session_id=body.get("session_id", ""),
                artifact=str(body.get("path", "")),
                live=body.get("live") if isinstance(body.get("live"), dict) else None,
            )
        elif isinstance(body.get("outcome"), dict):
            outcome = state.record_gate(mission_id, step_id, body["outcome"], session_id=body.get("session_id", ""))
        else:
            raise ValueError("A gate needs either a file path or a check outcome.")
        return {"outcome": outcome, "mission": state.mission_snapshot(mission_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/explain/{mission_id}/{step_id}")
async def explain_submit(mission_id: str, step_id: str, body: dict):
    """Store the learner's answer and hand back the grading instruction."""
    try:
        return state.submit_explanation(
            mission_id, step_id, body.get("answer", ""), body.get("session_id", "")
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/explain/{mission_id}/{step_id}/resend")
async def explain_resend(mission_id: str, step_id: str):
    """Rebuild the scoring request for the answer already saved."""
    try:
        return state.resend_explanation(mission_id, step_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Scores are recorded only by the agent tools (field_academy_grade_explanation and
# field_academy_grade_deployer). There is no HTTP route that writes a score, so the
# page cannot post one for itself.


@router.post("/use")
async def use_goal(body: dict):
    """The first-run answer to "What do you want Hermes to do for you?", or a skip."""
    try:
        return state.set_use_goal(body.get("text", ""), bool(body.get("skipped")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/complete/{mission_id}/{step_id}")
async def complete(mission_id: str, step_id: str, body: dict):
    """Check the gaps in a half-finished example, then show the model answers."""
    try:
        return state.submit_completion(mission_id, step_id, body.get("answers") or {}, bool(body.get("show_anyway")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reviews")
async def reviews():
    return state.review_overview()


@router.post("/review/start")
async def review_start(body: Optional[dict] = None):
    try:
        return state.start_review(bool((body or {}).get("practice")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/review/{session_id}")
async def review_session(session_id: str):
    try:
        return state.get_review_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/review/{session_id}/submit")
async def review_submit(session_id: str, body: dict):
    """Store the answers and hand back the grading instruction for the learner's own Hermes."""
    try:
        return state.submit_review(session_id, body.get("answers") or {})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/placement/{track_id}")
async def placement(track_id: str):
    try:
        return state.placement_questions(track_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/placement/{track_id}")
async def placement_submit(track_id: str, body: dict):
    try:
        return state.submit_placement(track_id, body.get("answers") or {})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/placement/{track_id}/apply")
async def placement_apply(track_id: str):
    try:
        return state.apply_placement(track_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/changes")
async def changes():
    return state.changes()


@router.post("/mission/{mission_id}/reverify")
async def mission_reverify(mission_id: str):
    try:
        return state.reverify(mission_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/mission/{mission_id}/acknowledge")
async def mission_acknowledge(mission_id: str):
    try:
        return state.acknowledge_changes(mission_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/check/{check_id}")
async def check(check_id: str, body: Optional[dict] = None):
    body = body or {}
    try:
        return diagnostics.run(
            check_id,
            mission_id=body.get("mission_id", ""),
            step_id=body.get("step_id", ""),
            path=body.get("path", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/evidence")
async def evidence(body: dict):
    try:
        event_id = state.record_evidence(
            body.get("mission_id", body.get("competency_id", "")),
            body.get("summary", ""),
            body.get("artifact", ""),
            body.get("session_id", ""),
            body.get("step_id", ""),
        )
        return {"ok": True, "event_id": event_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/certificate/{track_id}")
async def certificate(track_id: str):
    try:
        found = state.get_certificate(track_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not found:
        raise HTTPException(status_code=404, detail="No Field Record on this path yet.")
    return found


@router.post("/certificate/{track_id}")
async def certificate_claim(track_id: str, body: dict):
    """Write the path's Field Record. Refused until every mission on the path has passed. The route keeps its 0.8.2 name."""
    try:
        return state.issue_certificate(track_id, body.get("name", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/certificate/{track_id}/save")
async def certificate_save(track_id: str):
    try:
        return state.save_certificate(track_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/repair")
async def repair():
    """Delete rows left behind by a version whose ids no longer exist."""
    return state.purge_orphans()


# ── The Deployer tier ────────────────────────────────────────────────────────
#
# Every route here either reads Field Academy's own data, writes inside Field
# Academy's own data folder, or reads Hermes without changing it. None runs a
# program. The checks that read Hermes take what the desktop half read as
# ``sample`` and add what the backend can read from Hermes's own files.


@router.get("/deployer")
async def deployer_snapshot():
    return deployer.snapshot()


@router.post("/deployer/lab/{lab_id}/open")
async def deployer_lab_open(lab_id: str):
    return _guard(deployer.open_lab, lab_id)


@router.post("/deployer/lab/{lab_id}/new")
async def deployer_lab_new(lab_id: str):
    return _guard(deployer.new_variant, lab_id)


@router.post("/deployer/lab/{lab_id}/check")
async def deployer_lab_check(lab_id: str, body: Optional[dict] = None):
    return _guard(deployer.check_lab, lab_id, (body or {}).get("diagnosis", ""))


@router.post("/deployer/brief/check")
async def deployer_brief_check(body: dict):
    return _guard(deployer.brief_submit, body.get("path", ""))


@router.post("/deployer/brief/new")
async def deployer_brief_new():
    return _guard(deployer.new_brief_case)


@router.post("/deployer/scenario/{scenario_id}")
async def deployer_scenario(scenario_id: str, body: dict):
    return _guard(deployer.scenario_submit, scenario_id, body.get("answer", ""))


@router.post("/deployer/deploy/start")
async def deployer_deploy_start(body: dict):
    return _guard(deployer.deploy_start, body.get("service", ""), body.get("job", ""))


@router.post("/deployer/deploy/record")
async def deployer_deploy_record(body: dict):
    return _guard(deployer.deploy_record, body.get("path", ""))


@router.post("/deployer/deploy/check")
async def deployer_deploy_check(body: Optional[dict] = None):
    return _guard(deployer.deploy_check, (body or {}).get("sample"))


@router.post("/deployer/deploy/fallback")
async def deployer_deploy_fallback(body: dict):
    return _guard(deployer.deploy_fallback, body.get("excerpt", ""), body.get("notes", ""))


@router.post("/deployer/drill/{drill_id}/start")
async def deployer_drill_start(drill_id: str):
    return _guard(deployer.drill_start, drill_id)


@router.post("/deployer/drill/{drill_id}/recover")
async def deployer_drill_recover(drill_id: str):
    return _guard(deployer.drill_recover, drill_id)


@router.post("/deployer/drill/{drill_id}/note")
async def deployer_drill_note(drill_id: str, body: dict):
    return _guard(deployer.drill_note, drill_id, body.get("path", ""))


@router.post("/deployer/drill/{drill_id}/check")
async def deployer_drill_check(drill_id: str, body: Optional[dict] = None):
    return _guard(deployer.drill_check, drill_id, (body or {}).get("sample"))


@router.post("/deployer/drill/{drill_id}/fallback")
async def deployer_drill_fallback(drill_id: str, body: dict):
    return _guard(deployer.drill_fallback, drill_id, body.get("excerpt", ""), body.get("notes", ""))


@router.post("/deployer/walkthrough")
async def deployer_walkthrough(body: dict):
    return _guard(deployer.walkthrough_save, body.get("text", ""), body.get("media_path", ""))


@router.post("/deployer/review/packet")
async def deployer_review_packet(body: dict):
    return _guard(deployer.build_review_packet, body.get("name", ""))


@router.post("/deployer/review/signoff")
async def deployer_review_signoff(body: dict):
    return _guard(deployer.load_signoff, body.get("signoff", ""))


@router.post("/deployer/review/trust")
async def deployer_review_trust(body: dict):
    """Add a reviewer's key to this computer's own list. Field Records signed with it say so."""
    return _guard(deployer.trust_local_reviewer, body.get("name", ""), body.get("public_key", ""))


@router.post("/deployer/version")
async def deployer_version(body: dict):
    return _guard(deployer.set_version, body.get("value", ""), body.get("source", "typed by you"))


@router.post("/deployer/certificate")
async def deployer_certificate(body: dict):
    return _guard(deployer.issue_certificate, body.get("name", ""))


@router.post("/deployer/certificate/save")
async def deployer_certificate_save():
    return _guard(deployer.save_certificate)


@router.post("/deployer/reverify/start")
async def deployer_reverify_start():
    return _guard(deployer.start_reverify)


@router.post("/deployer/reverify/finish")
async def deployer_reverify_finish():
    return _guard(deployer.finish_reverify)


# -- Foundations: the practice profile ------------------------------------------
# The page sends profiles.create and deleteProfile itself, through Hermes's own gateway. This side plans the exact
# request, records what Hermes made, plants problems before the first chat, and confirms a deletion.


@router.get("/foundations/practice")
async def foundations_practice():
    return {"practice": practice.listing()}


@router.post("/foundations/practice/plan")
async def foundations_practice_plan(body: Optional[dict] = None):
    body = body or {}
    return _guard(practice.plan, body.get("which", "a"), body.get("attempt_id"))


@router.post("/foundations/practice/confirm")
async def foundations_practice_confirm(body: dict):
    result = body.get("result") if isinstance(body.get("result"), dict) else None
    return _guard(practice.confirm, str(body.get("name", "")), result)


@router.post("/foundations/practice/plant")
async def foundations_practice_plant(body: dict):
    return _guard(foundations.plant_lab, body.get("attempt_id", 0))


@router.post("/foundations/attempt/{attempt_id}/after-try")
async def foundations_after_try(attempt_id: int):
    return _guard(foundations.plant_after_try, attempt_id)


@router.get("/foundations/practice/{name}/memory")
async def foundations_practice_memory(name: str):
    return _guard(practice.memory_files, name)


@router.get("/foundations/practice/{name}/folder")
async def foundations_practice_folder(name: str):
    return _guard(practice.working_folder, name)


@router.post("/foundations/practice/remove")
async def foundations_practice_remove(body: dict):
    return _guard(practice.prepare_remove, str(body.get("name", "")), body.get("confirm") is True)


@router.post("/foundations/practice/removed")
async def foundations_practice_removed(body: dict):
    return _guard(practice.removed, str(body.get("name", "")))


# Missions 1, 2, 4, 5 and 6 (0.9 M6, part A): page data read on this side, never a planted problem.
def _foundations_a():
    from importlib import import_module

    return import_module(f"{package_name}.foundations_a")


@router.get("/foundations/a/{attempt_id}/{what}")
async def foundations_a_page(attempt_id: str, what: str):
    return _guard(_foundations_a().page, attempt_id, what)


@router.post("/foundations/a/{attempt_id}/{what}")
async def foundations_a_page_post(attempt_id: str, what: str, body: Optional[dict] = None):
    return _guard(_foundations_a().page, attempt_id, what, body or {})


# -- Foundations: the mission loop ----------------------------------------------
# No route here records a level or a score: those arrive only through the agent tool field_academy_grade_explanation.


@router.get("/foundations")
async def foundations_snapshot():
    return foundations.snapshot()


@router.get("/foundations/mission/{mission_id}")
async def foundations_mission(mission_id: str):
    return _guard(foundations.mission_view, mission_id)


@router.post("/foundations/attempt/start")
async def foundations_attempt_start(body: dict):
    return _guard(foundations.start, str(body.get("mission_id", "")), str(body.get("level", "")), body.get("test_out") is True)


@router.get("/foundations/attempt/{attempt_id}")
async def foundations_attempt(attempt_id: str):
    return _guard(foundations.attempt_view, attempt_id)


@router.post("/foundations/attempt/{attempt_id}/entry")
async def foundations_attempt_entry(attempt_id: str, body: dict):
    return _guard(foundations.save_entry, attempt_id, str(body.get("kind", "")), body.get("body") if isinstance(body.get("body"), dict) else {})


@router.post("/foundations/attempt/{attempt_id}/lab/open")
async def foundations_attempt_lab_open(attempt_id: str):
    return _guard(foundations.open_lab, attempt_id)


@router.post("/foundations/attempt/{attempt_id}/check")
async def foundations_attempt_check(attempt_id: str, body: Optional[dict] = None):
    body = body or {}
    sample = body.get("sample") if isinstance(body.get("sample"), dict) else None
    return _guard(foundations.run_checks, attempt_id, str(body.get("phase", "first")), sample)


@router.post("/foundations/attempt/{attempt_id}/explain")
async def foundations_attempt_explain(attempt_id: str, body: dict):
    return _guard(foundations.submit_explanation, attempt_id, str(body.get("answer", "")), str(body.get("session_id", "")))


@router.post("/foundations/attempt/{attempt_id}/explain/resend")
async def foundations_attempt_explain_resend(attempt_id: str):
    return _guard(foundations.resend_explanation, attempt_id)


@router.get("/foundations/attempt/{attempt_id}/record")
async def foundations_attempt_record(attempt_id: str):
    return _guard(foundations.record_preview, attempt_id)


@router.post("/foundations/attempt/{attempt_id}/record/preview")
async def foundations_attempt_record_preview(attempt_id: str, body: Optional[dict] = None):
    body = body or {}
    withhold = body.get("withhold") if isinstance(body.get("withhold"), list) else []
    return _guard(foundations.record_preview, attempt_id, withhold)


@router.post("/foundations/attempt/{attempt_id}/record")
async def foundations_attempt_record_add(attempt_id: str, body: Optional[dict] = None):
    body = body or {}
    withhold = body.get("withhold") if isinstance(body.get("withhold"), list) else []
    return _guard(foundations.add_to_record, attempt_id, withhold, body.get("confirm") is True)


@router.post("/foundations/record/correction")
async def foundations_record_correction(body: dict):
    return _guard(foundations.add_correction, str(body.get("entry_hash", "")), str(body.get("text", "")), body.get("confirm") is True)


# -- Foundations: the Field Record (format 3) -------------------------------------
# Preview lists every excerpt; the learner can withhold any. Issue saves the record folder on this computer, once.


def _record_args(body):
    body = body or {}
    withhold = body.get("withhold") if isinstance(body.get("withhold"), list) else []
    return str(body.get("holder", "")), str(body.get("limits", "")), str(body.get("case", "")), withhold


@router.get("/foundations/record")
async def foundations_record():
    return _guard(field_record.preview)


@router.post("/foundations/record/preview")
async def foundations_record_preview(body: Optional[dict] = None):
    return _guard(field_record.preview, *_record_args(body))


@router.post("/foundations/record/issue")
async def foundations_record_issue(body: Optional[dict] = None):
    return _guard(field_record.issue, *_record_args(body), confirmed=(body or {}).get("confirm") is True)


@router.post("/foundations/record/save")
async def foundations_record_save(body: dict):
    return _guard(field_record.save_again, str(body.get("number", "")))


# -- Foundations missions 7 to 11 -------------------------------------------------
# Read-only views the mission pages need: the connector settings text (7), the jobs the page asks Hermes to make and
# its report back (8, 10), the two-run notice (8), the practice profile's logs folder and terminal commands (10), and
# the Start snapshot (11). None records a check result.


def _foundations_b():
    module = sys.modules.get(f"{package_name}.foundations_b")
    if module is None:
        from importlib import import_module

        module = import_module(f"{package_name}.foundations_b")
    return module


@router.get("/foundations/practice/{name}/connector-text")
async def foundations_practice_connector_text(name: str):
    return _guard(_foundations_b().connector_text, name)


@router.get("/foundations/practice/{name}/jobs")
async def foundations_practice_jobs(name: str):
    return _guard(practice.jobs_to_make, name)


@router.post("/foundations/practice/{name}/jobs-made")
async def foundations_practice_jobs_made(name: str):
    return _guard(practice.jobs_made, name)


@router.get("/foundations/practice/{name}/ops")
async def foundations_practice_ops(name: str):
    return _guard(_foundations_b().ops, name)


@router.get("/foundations/practice/{name}/baseline")
async def foundations_practice_baseline(name: str):
    return _guard(_foundations_b().baseline_view, name)


@router.get("/foundations/attempt/{attempt_id}/watch")
async def foundations_attempt_watch(attempt_id: str):
    return _guard(_foundations_b().watch, attempt_id)
