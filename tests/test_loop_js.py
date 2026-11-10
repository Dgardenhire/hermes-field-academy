"""Runs tests/loop.test.mjs with node (the Foundations mission loop's page logic). Skips, with the reason, when node
isn't installed. Also checks the pure module imports nothing, and that the built bundle carries the Foundations
screens and never switches the app's profile itself."""

import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class LoopJsTests(unittest.TestCase):
    def test_the_mission_loop_logic(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed, so the mission loop's logic can't run here")
        result = subprocess.run([node, "--test", str(ROOT / "tests" / "loop.test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])

    def test_the_pure_module_imports_nothing(self):
        text = (ROOT / "desktop" / "src" / "loop.js").read_text(encoding="utf-8")
        self.assertEqual([line for line in text.splitlines() if line.startswith("import ")], [])

    def test_the_bundle_carries_foundations_and_never_switches_the_profile(self):
        built = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        self.assertIn("createFoundationsViews", built)
        self.assertIn("Open practice chat", built)
        for banned in ("setActiveProfile", "selectProfile(", "switchProfile"):
            self.assertNotIn(banned, built)
        self.assertNotRegex(built, r"/Users/|/private/var/|C:\\\\Users\\\\(?!you)")
        source = (ROOT / "desktop" / "src" / "foundations.js").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"host\.newChat\(\)", source), [], "practice chats always name their profile")


class Hermes023JsTests(unittest.TestCase):
    """Runs tests/hermes_023.test.mjs: practice-profile calls use the local route, and the palette gets detail()."""

    def test_the_page_meets_hermes_0_23(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed, so the page's Hermes 0.23 checks can't run here")
        result = subprocess.run([node, "--test", str(ROOT / "tests" / "hermes_023.test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])


class DeskJsTests(unittest.TestCase):
    """Runs tests/desk.test.mjs: the Loop 2 mission desk's logic, against the real-model run the harness renders."""

    def test_the_desk_logic(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed, so the desk's logic can't run here")
        result = subprocess.run([node, "--test", str(ROOT / "tests" / "desk.test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])

    def test_the_desk_logic_imports_nothing(self):
        text = (ROOT / "desktop" / "src" / "desk_logic.js").read_text(encoding="utf-8")
        self.assertEqual([line for line in text.splitlines() if line.startswith("import ")], [])

    def test_the_twelve_step_stepper_is_gone_and_the_desk_is_in(self):
        built = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        for needed in ("Field guide", "Start the practice", "Watch a sample run", "Give me a hint", "Show me where to look", "Show me the answer",
                       "Why did this miss?", "Score my answer", "Replay your run", "Turn off AI help"):
            self.assertIn(needed, built)
        source = (ROOT / "desktop" / "src" / "foundations.js").read_text(encoding="utf-8")
        self.assertNotIn("LoopStepper", source)
        self.assertNotIn("type: 'range'", source)
        for gone in ("Anyone can check", "GRADING_WHERE"):
            self.assertNotIn(gone, built)

    def test_no_slogan_lines_come_back(self):
        """Loop 2e (Damon, Nov 8: score slogans and clever fragments are gibberish to a stranger). None of these may be
        in the page, its source, the README, the catalog card or the lessons: headlines are plain sentences built from
        the run."""
        banned = [r"You said \d+ of \d+", r"You said \$\{", r"Hermes shows \d+ of \d+", r"Hermes shows \$\{", r"The checks said \d+ of \d+",
                  r"Find your first snag", r"Your chat says saved\. The file says held", r"Make it remember, and prove it",
                  r"Caught with \d+ hints?", r"Caught after one nudge", r"Caught on your own", r"So far: ", r"Not there yet\.",
                  r"Hunt for it", r"Show me what it was", r"Nudge me"]
        places = [ROOT / "desktop" / "plugin.js", ROOT / "README.md", ROOT / "docs" / "catalog" / "field-academy.yaml",
                  ROOT / "guide.py", ROOT / "recorder.py"]
        places += sorted((ROOT / "desktop" / "src").glob("*.js")) + sorted((ROOT / "content" / "foundations").glob("*.py"))
        for path in places:
            text = path.read_text(encoding="utf-8")
            for pattern in banned:
                self.assertIsNone(re.search(pattern, text), f"{path.name} brings back {pattern!r}")
