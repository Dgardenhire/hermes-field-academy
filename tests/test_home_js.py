"""Home page: runs tests/home.test.mjs, and checks the built bundle. Paths are the page (no Start tab), the first-run
practice is a marked Start here entry at its top, and the preview box can never render empty."""

import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "desktop" / "src"


class HomeTests(unittest.TestCase):
    def test_the_preview_logic(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed, so the home page's logic can't run here")
        result = subprocess.run([node, "--test", str(ROOT / "tests" / "home.test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])

    def test_no_start_tab_and_paths_come_first(self):
        text = (SRC / "plugin.js").read_text(encoding="utf-8")
        body = text[text.index("function MapView"):text.index("/* ------------------------------------------------------------------- path --")]
        self.assertNotIn("fa-tabs", body)
        self.assertNotIn("['start', 'Start']", body)
        ff, trail, foundations = body.index("FirstFlightCard"), body.index("title: 'Trail map'"), body.index("FoundationsCard")
        self.assertLess(trail, ff, "the trail map comes first, with the Start here card beside it")
        self.assertIn("fa-top-start", body)
        self.assertLess(ff, foundations, "the Foundations card is below")
        self.assertNotIn("Stays on your computer", text)

    def test_start_here_is_marked_once_on_the_home_page(self):
        found = (SRC / "foundations.js").read_text(encoding="utf-8")
        card = found[found.index("function FirstFlightCard"):found.index("function SampleRun")]
        self.assertIn("'Start here'", card)
        fcard = found[found.index("function FoundationsCard"):found.index("function useSample")]
        self.assertNotIn("'Start here'", fcard)

    def test_the_preview_cannot_be_an_empty_box(self):
        found = (SRC / "foundations.js").read_text(encoding="utf-8")
        card = found[found.index("function FirstFlightCard"):found.index("function SampleRun")]
        self.assertIn("homePreview(sample)", card)
        self.assertNotIn("jsx('div', { className: 'fa-strip' })", card)

    def test_the_bundle_matches_the_source(self):
        built = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        self.assertIn("PREVIEW_RUN", built)
        self.assertNotIn("fa-tabs", built)
        self.assertEqual(len(re.findall(r"homePreview\(", built)), 2)  # the definition and the one use


if __name__ == "__main__":
    unittest.main()
