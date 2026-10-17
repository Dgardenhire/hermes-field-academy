"""Exercise a Guide-path lab end to end against the INSTALLED Field Academy and a real Hermes (CI only).

Two phases, so the step between them can lock the key files with the learner's own command in a real shell
(PowerShell's icacls on Windows, chmod on Linux and macOS):

    python .github/platforms/hermes_run.py .github/platforms/exercise_guide_lab.py prepare <state.json>
    (the workflow locks every file listed in state.json, as a learner types it)
    python .github/platforms/hermes_run.py .github/platforms/exercise_guide_lab.py grade <state.json>

prepare opens the reboot and vault labs through the backend Hermes loaded, repairs everything a learner repairs
except the locks (with the reference repairs in tests/lab_solutions.py), checks that the backend then reports exactly
the open key files, and writes the files to lock. grade checks both labs pass through the backend and that the
changed-files evidence records the lock as a permissions change. No model is called.
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import sys
from pathlib import Path

PLUGIN = "field-academy"
CHECKOUT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CHECKOUT / "tests"))


def say(*parts):
    print("[guide-lab]", *parts, flush=True)


def check(cond, what):
    if not cond:
        say("FAIL:", what)
        raise SystemExit(1)
    say("ok:", what)


def backend():
    from hermes_cli import plugins as hp

    hp.discover_plugins(force=True)
    manager = hp.get_plugin_manager()
    loaded = next((lp for key, lp in manager._plugins.items() if PLUGIN in (key, getattr(lp.manifest, "name", None))), None)
    check(loaded is not None and loaded.enabled and not loaded.error, "Hermes loaded the installed plugin")
    home = Path(os.environ["HERMES_HOME"]).resolve()
    check(str(Path(loaded.module.__file__).resolve()).startswith(str(home)), "the loaded copy is the installed one")
    pkg = loaded.module.__name__
    return {name: importlib.import_module(f"{pkg}.{name}") for name in ("deployer", "labs", "grade", "fileaccess")}


def prepare(state_path):
    m = backend()
    from lab_solutions import solve_reboot, solve_vault

    say("platform", platform.platform(), "Windows rules" if m["fileaccess"].ON_WINDOWS else "POSIX rules")
    state = {"labs": []}
    for lab_id, solver in (("lab.reboot", solve_reboot), ("lab.vault", solve_vault)):
        view = m["deployer"].open_lab(lab_id)
        root = Path(view["path"])
        spec = m["labs"].spec_for(lab_id, view["seed"])
        diagnosis = solver(spec, root, skip=("perms",))
        result = m["deployer"].check_lab(lab_id, diagnosis)["outcome"]
        ids = [x["id"] for x in result["missing"]]
        wanted = "perm_open" if lab_id == "lab.reboot" else "env_open"
        check(not result["passed"] and ids == [wanted], f"{lab_id} seed {view['seed']}: only the open key files are left ({ids})")
        say(result["missing"][0]["what"])
        if lab_id == "lab.reboot":
            files = list(spec["secret_files"])
            if m["fileaccess"].ON_WINDOWS:
                cron = (root / "crontab.txt").read_text(encoding="utf-8")
                check("/bin/sh /srv/hermes-client/scripts/backup.sh" in cron, "on Windows the repaired schedule line names the program that runs the script")
        else:
            files = [f"profiles/{a['profile']}/.env" for a in spec["agents"]]
        for rel in files:
            check(not m["fileaccess"].is_private(root / rel), f"{rel} starts readable by others ({m['fileaccess'].others(root / rel)})")
        state["labs"].append({"lab_id": lab_id, "root": str(root), "files": files, "diagnosis": diagnosis})
        coach = m["grade"].COACH[wanted]["example"]
        say("the coaching a learner sees:", coach)
        if m["fileaccess"].ON_WINDOWS:
            check("icacls" in coach and "${env:USERDOMAIN}\\${env:USERNAME}:F" in coach, "the Windows coaching shows the icacls line")
        else:
            check("chmod 600" in coach, "the coaching shows chmod 600")
    Path(state_path).write_text(json.dumps(state, indent=2), encoding="utf-8")
    say("files to lock written to", state_path)


def grade(state_path):
    m = backend()
    state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    for lab in state["labs"]:
        root = Path(lab["root"])
        for rel in lab["files"]:
            check(m["fileaccess"].is_private(root / rel), f"{rel} is private after the learner's command")
        result = m["deployer"].check_lab(lab["lab_id"], lab["diagnosis"])
        check(result["outcome"]["passed"], f"{lab['lab_id']} passes through the backend ({result['outcome'].get('missing')})")
        view = result["lab"]
        check(view["status"] == "verified", f"{lab['lab_id']} is verified")
        changed = {c["path"]: c["change"] for c in view["changed"]}
        if lab["lab_id"] == "lab.reboot":
            check(changed.get(".env") == "permissions", f"the evidence records the lock on .env as a permissions change ({changed.get('.env')})")
    say("GUIDE LABS PASSED on", platform.system())


if __name__ == "__main__":
    # Under hermes_run.py the arguments arrive after the script's own path, so read the last two.
    phase, state_path = sys.argv[-2], sys.argv[-1]
    if phase not in ("prepare", "grade"):
        raise SystemExit(f"usage: exercise_guide_lab.py prepare|grade <state.json> (got {sys.argv[1:]})")
    (prepare if phase == "prepare" else grade)(state_path)
