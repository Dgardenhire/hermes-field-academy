"""Runs tests/loop_b.test.mjs with node (page logic for Foundations missions 7 to 11). Skips, with the reason, when
node isn't installed. Also checks the pure module imports nothing, and that the bundle carries the mission 7 to 11
panels and never makes a scheduled job by writing files."""

import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class LoopBJsTests(unittest.TestCase):
    def test_the_page_logic(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed, so the page logic can't run here")
        result = subprocess.run([node, "--test", str(ROOT / "tests" / "loop_b.test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])

    def test_the_pure_module_imports_nothing(self):
        text = (ROOT / "desktop" / "src" / "loop_b.js").read_text(encoding="utf-8")
        self.assertEqual([line for line in text.splitlines() if line.startswith("import ")], [])

    def test_the_bundle_carries_the_panels_and_makes_jobs_through_hermes(self):
        built = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        for words in ("Two scheduled runs have landed", "Copy the settings text", "cron.manage", "rollback.list"):
            self.assertIn(words, built)
        source = (ROOT / "desktop" / "src" / "foundations_b.js").read_text(encoding="utf-8")
        self.assertNotIn("jobs.json", source)
        self.assertNotIn("host.newChat()", source)


if __name__ == "__main__":
    unittest.main()
