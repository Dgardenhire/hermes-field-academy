"""Load Foundations missions from ``content/foundations/<id>.py`` and their prose from ``content/foundations/md/``.

A mission file holds one ``MISSION`` dict (the content model in ENGINEERING-PLAN section 4). Long prose lives beside it
as Markdown: the idea (``idea``) and the worked expert run (``expert``). The expert run is written as one ``## Step``
heading per step, each with **Did:**, **Saw:**, **Noticed:** and **Ruled out:** lines.

``public()`` is what the page may see before Compare: no planted-problem kinds and no hidden checks, the same
discipline as curriculum._public stripping answers.
"""

from __future__ import annotations

import copy
import importlib.util
import re
from pathlib import Path

FOLDER = Path(__file__).resolve().parent / "content" / "foundations"
LEVELS = ("beginner", "intermediate", "advanced")
STEPS = ("recall", "claim", "standard", "predict", "idea", "expert", "lab", "evidence", "check", "compare", "fix_transfer", "record")
EXPERT_PARTS = (("did", "Did"), ("saw", "Saw"), ("noticed", "Noticed"), ("ruled_out", "Ruled out"))
_cache: dict = {}

# Seed notes may name parameters, ``{refund}``, filled per learner from ``lab.seed_params`` (decisions from review 2:
# names, numbers and planted values vary by seed, so two learners don't get identical notes).
_PLACE = re.compile(r"\{([a-z_]+)\}")


def placeholders(text) -> list:
    return list(dict.fromkeys(_PLACE.findall(str(text or ""))))


def fill(text, params) -> str:
    """``text`` with each ``{name}`` replaced from ``params``. A name with no value is left as written."""
    return _PLACE.sub(lambda m: str(params[m.group(1)]) if m.group(1) in params else m.group(0), str(text or ""))


def longest_fill(text, choices) -> str:
    """``text`` filled with the longest choice of each parameter, for length rules at build time."""
    return fill(text, {k: max((str(v) for v in vals), key=len) for k, vals in (choices or {}).items() if vals})


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def expert_steps(text: str) -> list:
    """One dict per ``## Step`` heading: title plus did, saw, noticed and ruled_out ("" when missing)."""
    steps = []
    current = None
    for line in (text or "").splitlines():
        heading = re.match(r"^##\s+(?:Step\s+\d+[:.]?\s*)?(.*)$", line)
        if heading and line.lower().startswith("## step"):
            current = {"title": heading.group(1).strip(), **{key: "" for key, _ in EXPERT_PARTS}}
            steps.append(current)
            continue
        if current is None:
            continue
        for key, label in EXPERT_PARTS:
            match = re.match(rf"^\s*[-*]?\s*\*\*{label}:\*\*\s*(.*)$", line, re.I)
            if match:
                current[key] = match.group(1).strip()
                break
    return steps


def load_file(path: Path) -> dict:
    name = f"fa_foundations_{re.sub(r'[^A-Za-z0-9_]', '_', path.stem)}_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    mission = copy.deepcopy(getattr(module, "MISSION"))
    folder = path.parent
    mission["_file"] = path.name
    mission["_idea_text"] = _read(folder / mission["idea"]) if mission.get("idea") else ""
    mission["_expert_text"] = _read(folder / mission["expert"]) if mission.get("expert") else ""
    mission["_expert_steps"] = expert_steps(mission["_expert_text"])
    mission["_try_text"] = _read(folder / mission["try"]) if mission.get("try") else ""
    mission["_record_example"] = _read(folder / mission["record_example"]) if mission.get("record_example") else ""
    return mission


def load_all(folder=None) -> dict:
    """Every mission in the folder, by id, in file-name order. Cached per folder."""
    folder = Path(folder) if folder is not None else FOLDER
    key = str(folder.resolve())
    if key in _cache:
        return _cache[key]
    out = {}
    if folder.is_dir():
        for path in sorted(folder.glob("*.py")):
            if path.name.startswith("_"):
                continue
            mission = load_file(path)
            out[mission["id"]] = mission
    _cache[key] = out
    return out


def clear_cache():
    _cache.clear()


def get(mission_id: str, folder=None) -> dict:
    missions = load_all(folder)
    if mission_id not in missions:
        raise ValueError(f"Unknown Foundations mission: {mission_id}")
    return missions[mission_id]


def check_ids(mission: dict, phase: str = "first") -> list:
    """The live checks run in a phase: ``first`` and ``after_fix`` use the main checks, ``transfer`` the transfer ones."""
    transfer = set((mission.get("transfer") or {}).get("live_checks") or [])
    return [c["id"] for c in mission.get("live_checks", []) if (c["id"] in transfer) == (phase == "transfer")]


def profiles_needed(mission: dict) -> list:
    """Practice profiles to set up for this mission's lab. Both, whenever wrong_profile could be drawn, so the second
    profile's existence never tells the learner which problem was planted."""
    if (mission.get("lab") or {}).get("profiles"):  # a mission may name its profiles (missions 4 and 6 always use two)
        return list(mission["lab"]["profiles"])
    return ["a", "b"] if "wrong_profile" in (mission.get("lab") or {}).get("plants", []) else ["a"]


def profiles_after_try(mission: dict) -> list:
    """Practice profiles made only once the try is done (mission 4's academy-practice-b), so the try can't land in
    the wrong square."""
    return list((mission.get("lab") or {}).get("profiles_after_try") or [])


def plants_after_try(mission: dict) -> list:
    """Planted problems that wait for those profiles. Hidden from the page like the rest."""
    return list((mission.get("lab") or {}).get("plants_after_try") or [])


def public(mission: dict) -> dict:
    """The mission as the page may show it before Compare."""
    out = {k: copy.deepcopy(v) for k, v in mission.items() if not k.startswith("_")}
    lab = out.get("lab") or {}
    lab.pop("plants", None)
    lab.pop("plants_at", None)
    lab.pop("seed_notes", None)  # the pool; the learner's own protected notes come with the attempt
    lab.pop("seed_draw", None)
    lab.pop("seed_params", None)
    lab.pop("plants_after_try", None)
    lab["profiles"] = profiles_needed(mission)
    out["live_checks"] = [{"id": c["id"], "visible": True} for c in mission.get("live_checks", []) if c.get("visible", True)]
    hidden = {c["id"] for c in mission.get("live_checks", []) if not c.get("visible", True)}
    for check in out.get("standard", []):
        if any(f"live:{h}" in str(check.get("proves_by", "")) for h in hidden):
            check["proves_by"] = "hidden"
    out["hidden_checks"] = sum(1 for c in mission.get("live_checks", []) if not c.get("visible", True))
    out["idea_text"] = mission.get("_idea_text", "")
    out["expert_steps"] = mission.get("_expert_steps", [])
    # "As of Hermes" facts show as dated notes; the source patterns stay with the build-time check.
    out["as_of"] = [{"fact": item.get("fact", ""), "since": item.get("since", "")} for item in mission.get("as_of") or []]
    out["try_text"] = mission.get("_try_text", "")
    out["record_example_text"] = mission.get("_record_example", "")
    out.pop("expert_slots", None)  # interview questions still to answer stay off the page
    return out
