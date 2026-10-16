"""Runs tests/learn.test.mjs and tests/prose.test.mjs with node. Skips, with the reason, when node isn't installed."""

import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class LearnJsTests(unittest.TestCase):
    def test_the_pages_learning_logic(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed, so the page's learning logic can't run here")
        result = subprocess.run([node, "--test", str(ROOT / "tests" / "learn.test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])

    def test_text_renders_as_paragraphs_and_lists(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed, so the page's text renderer can't run here")
        result = subprocess.run([node, "--test", str(ROOT / "tests" / "prose.test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])

    def test_the_pure_module_imports_nothing(self):
        for name in ("learn.js", "prose-text.js"):
            text = (ROOT / "desktop" / "src" / name).read_text(encoding="utf-8")
            self.assertEqual([line for line in text.splitlines() if line.startswith("import ")], [], name)


if __name__ == "__main__":
    unittest.main()
