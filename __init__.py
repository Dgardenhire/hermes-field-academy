"""Field Academy registration.

Two hooks, both gated on TWO axes. Session-id prefixes alone do not catch a
one-shot CLI run, so argv is checked as well: a `hermes -z` invocation gets a
bare `<YYYYMMDD>_<HHMMSS>_<hex>` id with no prefix, which passes a prefix
filter and lets a coaching offer land in captured stdout.

History worth keeping: an earlier version recorded background runs as learner
signals (14 of 23 rows came from scheduled jobs in 0.2) and the directive
leaked into a cron break reminder that shipped to Telegram carrying a
`::` marker in the message body. That old name is gone. The live directive is
DIRECTIVE below, and the desktop half registers the same string; a test asserts
the two halves agree, because a rename on one side alone is a silent no-op.
"""

import sys
from pathlib import Path

from . import schemas, state, tools
from .curriculum import mission_for_tool

# The transcript directive both halves must agree on. The desktop half
# registers this name; this half tells the model to emit it.
DIRECTIVE = "field-academy-practice"

# Flags that mean "answer once and exit, output goes to a script". A person is
# not reading the reply, so a coaching offer is pure noise in captured stdout.
# Long-running surfaces (gateway run, serve, the desktop backend) never carry
# these flags, so gating on argv leaves every interactive surface untouched.
AUTOMATION_FLAGS = ("-z", "--oneshot", "-Q")


def _is_automation_run() -> bool:
    return any(arg in AUTOMATION_FLAGS for arg in sys.argv[1:])


def _post_tool_call(tool_name, task_id="", **kwargs):
    """Offer a coaching moment, but only to a person sitting in a session.

    Scheduled runs and gateway-delivered messages share this hook. Recording
    them produced 14 of 23 signals from background jobs in 0.2, and the
    directive then leaked into a cron break reminder that shipped to Telegram
    with the raw marker in the message body.
    """
    if not state.is_learner_session(task_id) or _is_automation_run():
        return
    mission_id = mission_for_tool(tool_name)
    if mission_id:
        state.observe_tool(mission_id, tool_name, task_id)


# Surfaces where a person reads the reply in a Hermes window or terminal. Gateway
# session ids carry no prefix, so the turn's platform, which Hermes passes to
# pre_llm_call, is what keeps the offer out of messaging apps, webhooks and cron.
# An empty platform counts as interactive: older builds did not pass one.
INTERACTIVE_PLATFORMS = ("", "desktop", "tui", "cli", "local")


def _pre_llm_call(session_id="", platform="", **kwargs):
    if _is_automation_run() or str(platform or "").strip().lower() not in INTERACTIVE_PLATFORMS:
        return None
    mission = state.claim_spotlight(session_id)
    if not mission:
        return None
    return {
        "context": (
            "Field Academy has one optional practice to offer from the learner's recent work: "
            f"{mission['title']} ({mission['id']}). {mission['promise']} "
            "Finish what they asked for first. Offer it in one sentence, make it easy to decline, "
            "and never suggest that using a tool completed a step or proved anything. "
            f'If you do mention it, end with this on its own line: ::{DIRECTIVE}{{mission="{mission["id"]}"}}'
        )
    }


def _academy_command(raw_args):
    """Plain-text map for /academy in the terminal and messaging apps."""
    data = state.snapshot()
    lines = ["Field Academy: your paths"]
    for track in data["tracks"]:
        rung = next((item for item in track["levels"] if item["current"]), None)
        where = f"at {rung['name']}" if rung else "every mission passed"
        lines.append(
            f"- {track['name']}: {track['verified_missions']} of {len(track['missions'])} passed, {where}. "
            f"Field Record: {_certificate_words(track['certificate'])}"
        )
    due = data["reviews"]["due_count"]
    if due:
        lines.append(f"Review: {due} mission{'s' if due != 1 else ''} due. A session is three short questions.")
    nxt = data.get("next_up")
    if nxt:
        lines.append(f"Next: {nxt['title']} ({nxt['track_name']}, {nxt['level_name']}, about {nxt['minutes']} minutes)")
    try:
        from . import deployer

        lines.append(deployer.summary_line())
    except Exception:  # the path summary must never break the command
        pass
    lines.append("Open Field Academy in the Hermes app to do the steps.")
    return "\n".join(lines)


def _certificate_words(certificate):
    if certificate["status"] == "issued":
        return f"created, number {certificate['issued']['number']}"
    if certificate["status"] == "ready":
        return "ready to create"
    remaining = certificate["remaining"]
    return f"{remaining} mission{'s' if remaining != 1 else ''} to go"


def register(ctx):
    ctx.register_tool(name="field_academy_snapshot", toolset="field_academy", schema=schemas.FIELD_ACADEMY_SNAPSHOT, handler=tools.field_academy_snapshot)
    ctx.register_tool(name="field_academy_mission", toolset="field_academy", schema=schemas.FIELD_ACADEMY_MISSION, handler=tools.field_academy_mission)
    ctx.register_tool(name="field_academy_grade_explanation", toolset="field_academy", schema=schemas.FIELD_ACADEMY_GRADE_EXPLANATION, handler=tools.field_academy_grade_explanation)
    ctx.register_tool(name="field_academy_grade_review", toolset="field_academy", schema=schemas.FIELD_ACADEMY_GRADE_REVIEW, handler=tools.field_academy_grade_review)
    ctx.register_tool(name="field_academy_grade_deployer", toolset="field_academy", schema=schemas.FIELD_ACADEMY_GRADE_DEPLOYER, handler=tools.field_academy_grade_deployer)
    ctx.register_tool(name="field_academy_record_evidence", toolset="field_academy", schema=schemas.FIELD_ACADEMY_RECORD_EVIDENCE, handler=tools.field_academy_record_evidence)
    ctx.register_hook("post_tool_call", _post_tool_call)
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_command("academy", handler=_academy_command, description="Show your Field Academy paths, levels and Field Records")
    skills_dir = Path(__file__).parent / "skills"
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            ctx.register_skill(child.name, skill_md)
