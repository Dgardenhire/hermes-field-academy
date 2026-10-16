"""Backend-side checks.

Anything about *this user's app* belongs in the renderer (desktop/plugin.js),
where host.state and host.request read the live gateway. The checks here only
touch the backend's own filesystem, so their results are labelled as such: on a
remote or Cloud backend these paths are that machine's, not the learner's.
"""

from __future__ import annotations

import os
from pathlib import Path

from . import state


def _home():
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()


def _result(check_id, passed, title, detail, facts=None):
    return {
        "check": check_id,
        "passed": bool(passed),
        "title": title,
        "detail": detail,
        "facts": facts or [],
    }


def backend_home(mission_id="", step_id=""):
    """Report where the backend actually is, without pretending it is the learner's machine."""
    home = _home()
    return _result(
        "backend_home",
        home.exists(),
        "Backend home located" if home.exists() else "Backend home not found",
        f"The backend running this session keeps its state at {home}. If you are on a remote or Cloud "
        "backend, this is that machine, not your laptop.",
        [{"label": "Backend home", "value": str(home)}],
    )


def verify_artifact(mission_id, step_id, path, live=None):
    return state.verify_artifact(mission_id, step_id, path, live=live)


def run(check_id, mission_id="", step_id="", path=""):
    if check_id == "artifact":
        return verify_artifact(mission_id, step_id, path)
    if check_id == "backend_home":
        return backend_home(mission_id, step_id)
    raise ValueError(f"Unknown backend check: {check_id}")
