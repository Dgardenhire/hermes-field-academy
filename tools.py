"""Agent-side tool handlers."""

import json

from . import state


def _result(operation):
    try:
        return json.dumps(operation(), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:  # pragma: no cover - defensive
        return json.dumps({"error": f"Field Academy could not complete the operation: {exc}"})


def field_academy_snapshot(args, **kwargs):
    return _result(state.compact)


def field_academy_mission(args, **kwargs):
    def operation():
        mission_id = args.get("mission_id") or state.snapshot()["active_mission"]
        mission = state.mission_snapshot(mission_id)
        return {
            "id": mission["id"],
            "track": mission["track"],
            "title": mission["title"],
            "promise": mission["promise"],
            "outcome": mission["outcome"],
            "level": mission.get("level_name", ""),
            "minutes": mission.get("minutes", 0),
            "learner_goal": mission.get("goal", ""),
            "why_it_matters": mission.get("use_text", ""),
            "version": mission.get("version", 1),
            "proof": mission.get("proof", ""),
            "field_case": mission.get("field_case", ""),
            "watch": mission.get("watch", []),
            "steps": [
                {
                    "id": step["id"],
                    "kind": step["kind"],
                    "title": step["title"],
                    "body": step.get("body", ""),
                    "action": step.get("action", ""),
                    "route": step.get("route", ""),
                    "prompt": step.get("prompt", ""),
                    "verify": step.get("verify", ""),
                    "headings": step.get("headings", []),
                    "marker": step.get("marker", ""),
                    "support": step.get("support", ""),
                    "covers": step.get("covers", []),
                    "threshold": step.get("threshold", 70),
                    "deliverable": step.get("deliverable", ""),
                    "status": step["status"],
                    "explanation": step.get("explanation", {}),
                }
                for step in mission["steps"]
            ],
            "sources": mission["sources"],
        }

    return _result(operation)


def field_academy_grade_explanation(args, **kwargs):
    def operation():
        return state.grade_explanation(
            args.get("mission_id", ""),
            args.get("step_id", "explain"),
            args.get("score", 0),
            args.get("feedback", ""),
            args.get("missed") or [],
        )

    return _result(operation)


def field_academy_grade_review(args, **kwargs):
    def operation():
        return state.grade_review(args.get("session_id", ""), args.get("grades") or [])

    return _result(operation)


def field_academy_record_evidence(args, **kwargs):
    def operation():
        event_id = state.record_evidence(
            args.get("competency_id", ""),
            args.get("summary", ""),
            args.get("artifact", ""),
            kwargs.get("task_id", ""),
        )
        return {"ok": True, "event_id": event_id}

    return _result(operation)


def field_academy_grade_deployer(args, **kwargs):
    def operation():
        from . import deployer

        return deployer.grade_deployer(
            args.get("item_id", ""),
            args.get("score", 0),
            args.get("missed") or [],
            args.get("feedback", ""),
        )

    return _result(operation)
