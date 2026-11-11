"""The open cache against the real backend, and how the page uses it.

Hermes takes 2 to 3 seconds to start this plugin's backend before the page's first request answers. The page keeps a
small copy of the last answers the map was drawn from (desktop/src/opencache.js) and draws the map from it at once.
This builds real passports, Guide trails and Foundations lists (a fresh start, part-way, one certificate issued, and
the first and last Foundations states), then runs tests/open_cache.test.mjs over them with node: the kept copy must
draw the same map, fit the size cap, and never hold a credential.

Skips the node half, with the reason, when node isn't installed. No Hermes command runs.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "desktop" / "src"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_trail_map import _fixtures_module, node_env  # noqa: E402


def _states():
    fx = _fixtures_module()
    states = {}
    for name, recipe in (("fresh", fx.fresh), ("progress", fx.progress), ("issued", fx.issued)):
        built = fx.build(f"open_{name}", recipe)
        states[name] = {"passport": built["passport"], "deployer": built.get("deployer")}
    sys.path.insert(0, str(ROOT / "harness"))
    import foundations_fixtures

    def foundations_recipe(make):
        def run(state, curriculum, data_dir, store):
            kit = foundations_fixtures.Kit(state, store, data_dir)
            try:
                make(kit)
                return {"foundations": kit.out()}
            finally:
                kit.close()

        return run

    recipes = dict(foundations_fixtures.RECIPES)
    for name in ("f_fresh", "f_done"):
        built = fx.build(f"open_{name}", foundations_recipe(recipes[name]))
        states[name] = {"passport": built["passport"], "deployer": built.get("deployer"), "foundations": built["foundations"]["snapshot"]}
    return states


class OpenCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        cls.states = _states()

    def test_the_states_carry_what_the_map_reads(self):
        for name, state in self.states.items():
            self.assertEqual(len(state["passport"]["tracks"]), 4, name)
            self.assertIn("track", state["deployer"], name)
        self.assertTrue(self.states["f_done"]["foundations"]["missions"])

    def test_first_paint_from_the_kept_copy(self):
        if not self.node:
            self.skipTest("node is not installed, so the open cache's JavaScript can't run here")
        with tempfile.TemporaryDirectory(prefix="fa-open-") as tmp:
            path = Path(tmp) / "states.json"
            path.write_text(json.dumps(self.states))
            run = subprocess.run(
                [self.node, "--test", str(ROOT / "tests" / "open_cache.test.mjs")],
                env=node_env(self.node, FA_OPEN_STATES=str(path)),
                capture_output=True, text=True, timeout=120,
            )
        self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-2000:])
        self.assertRegex(run.stdout, r"(?m)^(?:#|ℹ) fail 0$")
        # Every real state was checked, not only the hand-made ones.
        for name in self.states:
            self.assertIn(f"{name}: the kept passport draws the same map", run.stdout)
        self.assertIn("f_done: the kept Foundations list", run.stdout)


class OpenCacheSourceTests(unittest.TestCase):
    """How the page uses the open cache."""

    @classmethod
    def setUpClass(cls):
        cls.plugin = (SRC / "plugin.js").read_text(encoding="utf-8")
        cls.found = (SRC / "foundations.js").read_text(encoding="utf-8")
        cls.cache = (SRC / "opencache.js").read_text(encoding="utf-8")
        cls.page = cls.plugin[cls.plugin.index("function Page()"):cls.plugin.index("/* -------------------------------------------------------------- chrome ----- */")]

    def test_the_cache_module_is_pure(self):
        self.assertNotRegex(self.cache, r"(?m)^import ", "opencache.js must stay importable by node with no app around it")
        self.assertNotIn("localStorage", self.cache, "the SDK's ctx.storage, never the browser's storage directly")
        self.assertNotIn("localStorage", self.plugin)

    def test_the_cache_lives_in_the_sdk_storage(self):
        self.assertIn("writeSnapshot(api?.storage, kind, out, scope)", self.plugin)
        self.assertIn("readSnapshot(api?.storage, kind, scope)", self.plugin)

    def test_the_map_answers_are_kept_and_nothing_else(self):
        self.assertIn("kept('passport', () => ctxRest('/passport'))", self.plugin)
        self.assertIn("kept('deployer', () => ctxRest('/deployer'))", self.plugin)
        self.assertIn("kept('foundations', () => takeEarly('/foundations'))", self.plugin)
        self.assertEqual(len(re.findall(r"\bkept\('", self.plugin)), 3)

    def test_the_page_draws_from_the_plan_and_holds_clicks_on_a_copy(self):
        self.assertIn("openPlan({", self.page)
        self.assertIn("onClickCapture: onPreviewEvent", self.page)
        self.assertIn("onKeyDownCapture: onPreviewEvent", self.page)
        self.assertIn("if (control.isConnected) control.click()", self.page)
        self.assertIn("if (!preview.current) return goNow(next)", self.page)
        # The skeleton stays for the very first open.
        self.assertIn("SkeletonPage, { label: 'Loading your trails'", self.page)

    def test_the_hermes_version_is_read_from_the_live_trail_only(self):
        self.assertIn("if (liveDeployer) syncVersion(liveDeployer)", self.page)
        self.assertNotIn("syncVersion(deployer)", self.page)

    def test_the_cards_requests_go_out_with_the_passport(self):
        self.assertIn("startEarly('/foundations')", self.page)
        self.assertIn("startEarly('/replay/sample')", self.page)
        self.assertIn("loadFoundations().then(", self.found)
        self.assertIn("loadSample().then(", self.found)
        self.assertIn("foundationsViews.useFoundations(true, { fromCopy: true })", self.plugin)

    def test_the_bundle_carries_it(self):
        bundle = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        for name in ("function openPlan", "function previewIntent", "function carriesSecret", "open-cache.", "onClickCapture: onPreviewEvent"):
            self.assertIn(name, bundle)


if __name__ == "__main__":
    unittest.main()
