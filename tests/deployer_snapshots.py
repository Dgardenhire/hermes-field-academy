"""Write the Deployer snapshots tests/deployer_trail.test.mjs reads, from the real backend.

    python3 tests/deployer_snapshots.py OUT.json

The same two states tests/test_deployer_ui.py builds (a fresh start, then every lab passed), made in a throwaway data
folder with HOME and HERMES_HOME fenced off (DeployerCase). The node test runs this itself when FA_DEPLOYER isn't set,
so `node --test tests/deployer_trail.test.mjs` works on its own.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from deployer_support import DeployerCase  # noqa: E402


class _Snapshots(DeployerCase):
    def runTest(self):  # unittest needs a test method to build the case
        pass


def main(out: str) -> int:
    case = _Snapshots()
    case.setUp()
    try:
        states = {"fresh": case.deployer.snapshot()}
        case.pass_labs()
        states["labs"] = case.deployer.snapshot()
        pathlib.Path(out).write_text(json.dumps(states, default=str), encoding="utf-8")
    finally:
        case.tearDown()
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: deployer_snapshots.py OUT.json")
    sys.exit(main(sys.argv[1]))
