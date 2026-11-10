"""Run the whole test suite inside an installed Hermes's runtime (CI only).

    python .github/platforms/hermes_run.py .github/platforms/run_suite.py

The tests are stdlib only and give every test its own FIELD_ACADEMY_DATA_DIR; this run checks they also
pass with Hermes's interpreter and packages, the way the plugin runs for a learner.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"
os.chdir(ROOT)
sys.path.insert(0, str(TESTS))
suite = unittest.defaultTestLoader.discover(str(TESTS), pattern="test_*.py", top_level_dir=str(TESTS))
result = unittest.TextTestRunner(verbosity=1).run(suite)
print(f"ran {result.testsRun}, failures {len(result.failures)}, errors {len(result.errors)}, skipped {len(result.skipped)}")
for test, reason in result.skipped:
    print(f"skipped: {test.id()}: {reason}")
raise SystemExit(0 if result.wasSuccessful() else 1)
