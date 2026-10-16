"""The trail map against the real backend.

Builds passports from the real state module (a fresh start, part-way, one path ready,
one certificate issued, and every mission on every path passed with every certificate
issued), then runs tests/trail_map.test.mjs over them with node: every path, level and
mission must land on the map with no missing field and no NaN in the drawing. A field
missing from the passport once crashed pages in real Hermes.

Skips, with the reason, when node isn't installed. No Hermes command runs.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _fixtures_module():
    spec = importlib.util.spec_from_file_location("fa_make_fixtures", ROOT / "harness" / "make_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def everything(state, curriculum, data_dir, store=None):
    fx = _fixtures_module()
    for track_id, track in curriculum.TRACKS.items():
        for item in track["missions"]:
            fx.pass_mission(state, curriculum, data_dir, item["id"])
    for track_id in curriculum.TRACKS:
        state.issue_certificate(track_id, "Ada Lovelace")
    return None


def node_env(node, **extra):
    """A bare environment for node: its own folder on PATH, plus what Windows needs to start any process.

    Windows processes need SYSTEMROOT (and node's test runner spawns a child node per file); without it the child
    never comes up and the run hangs instead of failing.
    """
    env = {"PATH": os.pathsep.join([str(Path(node).parent), "/usr/bin", "/bin"]), **extra}
    if os.name == "nt":
        for key in ("SYSTEMROOT", "SystemRoot", "WINDIR", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "PATHEXT", "COMSPEC"):
            if os.environ.get(key):
                env[key] = os.environ[key]
    return env


class TrailMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        fx = _fixtures_module()
        recipes = (("fresh", fx.fresh), ("progress", fx.progress), ("ready", fx.ready), ("issued", fx.issued), ("everything", everything))
        cls.passports = {name: fx.build(f"trail_{name}", recipe)["passport"] for name, recipe in recipes}

    def test_every_state_has_four_paths(self):
        for name, passport in self.passports.items():
            self.assertEqual(len(passport["tracks"]), 4, name)
        done = self.passports["everything"]
        self.assertTrue(all(t["certificate"]["status"] == "issued" for t in done["tracks"]))

    def test_the_node_environment_can_start_node_here(self):
        if not self.node:
            self.skipTest("node is not installed")
        run = subprocess.run([self.node, "-e", "console.log(process.platform)"], env=node_env(self.node),
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        if os.name == "nt":
            self.assertIn("SYSTEMROOT", {k.upper() for k in node_env(self.node)})

    def test_the_map_draws_every_path_level_and_mission(self):
        if not self.node:
            self.skipTest("node is not installed, so the map's JavaScript can't run here")
        with tempfile.TemporaryDirectory(prefix="fa-trail-") as tmp:
            path = Path(tmp) / "passports.json"
            path.write_text(json.dumps(self.passports))
            run = subprocess.run(
                [self.node, "--test", str(ROOT / "tests" / "trail_map.test.mjs")],
                env=node_env(self.node, FA_PASSPORTS=str(path)),
                capture_output=True, text=True, timeout=120,
            )
        self.assertEqual(run.returncode, 0, run.stdout[-4000:] + run.stderr[-2000:])
        self.assertRegex(run.stdout, r"(?m)^(?:#|ℹ) fail 0$")


class TrailMapSourceTests(unittest.TestCase):
    """How the desktop half uses the trail module."""

    @classmethod
    def setUpClass(cls):
        src = ROOT / "desktop" / "src"
        cls.plugin = (src / "plugin.js").read_text(encoding="utf-8")
        cls.field = (src / "field.js").read_text(encoding="utf-8")
        cls.trail = (src / "trail.js").read_text(encoding="utf-8")

    def test_the_map_reads_its_data_through_the_trail_model(self):
        self.assertIn("overview(data)", self.plugin)
        self.assertIn("trailModel(track)", self.plugin)

    def test_trail_geometry_is_pure(self):
        self.assertNotRegex(self.trail, r"^import ", "trail.js must stay importable by node with no app around it")

    def test_one_accent_mixed_from_theme_variables(self):
        for name, text in (("plugin.js", self.plugin), ("field.js", self.field), ("trail.js", self.trail)):
            self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", text), f"hex color in {name}")
            self.assertNotIn("rgb(", text, name)
        self.assertIn("--fa-blaze:color-mix(", self.field)

    def test_motion_is_gated_behind_reduced_motion(self):
        self.assertIn("@media (prefers-reduced-motion:reduce)", self.field)
        self.assertIn("useReducedMotion()", self.field)
        for animated in (".fa-draw", ".fa-marker", ".fa-needle"):
            self.assertRegex(self.field, r"prefers-reduced-motion:reduce\)\{[^\n]*" + re.escape(animated), animated)

    def test_the_field_record_says_self_issued_and_carries_a_mark_and_number(self):
        self.assertIn("'Self-issued'", self.plugin)
        self.assertIn("display.disclaimer", self.plugin)
        self.assertIn("display.issuer", self.plugin)
        self.assertIn("body.number", self.plugin)
        self.assertIn("jsx(Seal,", self.plugin)

    def test_no_streaks_or_timers(self):
        for text in (self.plugin, self.field):
            self.assertIsNone(re.search(r"\bstreak|\bdays? in a row|countdown", text, re.I))

    def test_the_plugin_starts_enabled(self):
        self.assertIn("defaultEnabled: true,", self.plugin)
        bundle = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        self.assertIn("defaultEnabled: true", bundle)


if __name__ == "__main__":
    unittest.main()
