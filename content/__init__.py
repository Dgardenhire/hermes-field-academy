"""Field Academy's teaching content, one file per path.

curriculum.py holds the structure of every mission. These files hold the words
that make the learning science work: a finished worked example and a half-done
one for each mission, the exact things a check looks for, hints for a miss,
review questions for spaced practice, the placement check, and the capstone.

The format is in docs/content-format.md. scripts/check_content.py validates it.
"""

from __future__ import annotations

from copy import deepcopy

from . import track_ambassador, track_architect, track_integrator, track_operator

TRACK_MODULES = {
    "operator": track_operator,
    "integrator": track_integrator,
    "architect": track_architect,
    "ambassador": track_ambassador,
}


def all_missions() -> dict:
    out: dict = {}
    for module in TRACK_MODULES.values():
        out.update(deepcopy(getattr(module, "MISSIONS", {})))
    return out


def capstones() -> dict:
    return {track: deepcopy(module.CAPSTONE) for track, module in TRACK_MODULES.items() if getattr(module, "CAPSTONE", None)}


def placements() -> dict:
    return {track: deepcopy(module.PLACEMENT) for track, module in TRACK_MODULES.items() if getattr(module, "PLACEMENT", None)}
