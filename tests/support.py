"""Shared setup for the behaviour tests. Stdlib only.

Each test gets its own data folder and its own copy of the package, so no test
can see another's progress. Time moves with ``set_time``, which replaces the
store's clock, so a review that comes due in two days is tested without waiting.
"""

from __future__ import annotations

import importlib.util
import itertools
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
START = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)
_counter = itertools.count(1)


def fixtures_module():
    spec = importlib.util.spec_from_file_location("fa_fixtures_for_tests", ROOT / "harness" / "make_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FX = fixtures_module()


class AcademyCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["FIELD_ACADEMY_DATA_DIR"] = self.tmp
        self.name = f"fa_case_{next(_counter)}"
        spec = importlib.util.spec_from_file_location(self.name, ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
        self.pkg = importlib.util.module_from_spec(spec)
        sys.modules[self.name] = self.pkg
        spec.loader.exec_module(self.pkg)
        self.state = self.pkg.state
        self.store = sys.modules[f"{self.name}.store"]
        self.curriculum = sys.modules[f"{self.name}.curriculum"]
        self.documents = sys.modules[f"{self.name}.documents"]
        self.learning = sys.modules[f"{self.name}.learning"]
        self.review = sys.modules[f"{self.name}.review"]
        self.set_time(START)

    def tearDown(self):
        for key in [k for k in sys.modules if k == self.name or k.startswith(self.name + ".")]:
            del sys.modules[key]
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("FIELD_ACADEMY_DATA_DIR", None)

    # -- time and progress ---------------------------------------------------

    def set_time(self, when):
        self.now = when
        self.store.clock = lambda: when

    def advance(self, **delta):
        self.set_time(self.now + timedelta(**delta))

    def pass_mission(self, mission_id, score=88):
        FX.pass_mission(self.state, self.curriculum, self.tmp, mission_id, score)

    def pass_track(self, track_id):
        for item in self.curriculum.TRACKS[track_id]["missions"]:
            self.pass_mission(item["id"])

    # -- lookups -------------------------------------------------------------

    def mission(self, mission_id):
        return self.state.mission_snapshot(mission_id)

    def step(self, mission_id, kind):
        return next(s for s in self.curriculum.MISSIONS[mission_id]["steps"] if s["kind"] == kind)

    def passport_step(self, mission_id, kind):
        return next(s for s in self.mission(mission_id)["steps"] if s["kind"] == kind)

    def track(self, track_id):
        return next(t for t in self.state.snapshot()["tracks"] if t["id"] == track_id)

    def document(self, mission_id):
        """A document that passes the mission's gate and is not the worked example."""
        return FX.build_document(self.step(mission_id, "gate"))

    def write(self, name, text):
        target = pathlib.Path(self.tmp) / name
        target.write_text(text, encoding="utf-8")
        return str(target)

    def rows(self, sql, *args):
        with self.state._connection() as conn:
            return [dict(row) for row in conn.execute(sql, args)]
