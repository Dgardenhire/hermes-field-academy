"""0.9 design floors, checked in the page source: no HTML text under 12px, no small caps on reading text, the stepper
never crams titles into a narrow window, and the first screen names what a mission does that a prompt can't."""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "desktop" / "src"
# SVG text in the map, banner, profile picture and seal is drawn in a scaled viewBox, so its font-size is not pixels.
SVG_CLASSES = (".fa-bn-label", ".fa-profile-label", ".fa-seal-text", ".fa-pic-cap")


def css_rules():
    for path in sorted(SRC.glob("*.js")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith((".", "@container", "@media")) and "{" in line:
                yield path.name, line


class Floors(unittest.TestCase):
    def test_no_html_text_under_12px(self):
        small = []
        for name, rule in css_rules():
            if rule.startswith(SVG_CLASSES):
                continue
            for size in re.findall(r"font-size:\s*([\d.]+)px", rule):
                if float(size) < 12:
                    small.append(f"{name}: {rule[:90]}")
        self.assertEqual(small, [])

    def test_the_kit_s_smallest_size_is_raised_to_12px_inside_field_academy_only(self):
        text = (SRC / "foundations.js").read_text(encoding="utf-8")
        self.assertIn(".fa-root .hk{--hk-fs-xs:12px}", text)
        self.assertNotRegex(text, r"(?m)^\.hk\{--hk-fs-xs", "a bare .hk rule would change other plugins' pages")

    def test_reading_text_is_not_set_in_small_caps(self):
        caps = [f"{n}: {r[:80]}" for n, r in css_rules() if "all-small-caps" in r and not r.startswith(SVG_CLASSES)]
        self.assertEqual(caps, [])

    def test_code_never_shrinks_below_12px(self):
        self.assertIn("font-size:max(12px,.92em)", (SRC / "foundations.js").read_text(encoding="utf-8"))

    def test_a_narrow_pane_names_the_phase_and_step_in_words(self):
        """Loop 2: the 12-step stepper is gone; below 1,180 px the rail folds into a bar that says, in words, where you are."""
        text = (SRC / "desk.js").read_text(encoding="utf-8")
        self.assertIn("jsx('strong', { children: phaseBarWords(states, at) })", text)
        self.assertIn("@container (min-width:1180px)", text)


class FirstScreen(unittest.TestCase):
    def test_the_foundations_card_shows_the_plant_the_check_and_the_record(self):
        text = (SRC / "foundations.js").read_text(encoding="utf-8")
        card = text[text.index("function FoundationsCard"):text.index("function FoundationsPath")]
        for words in ("A problem is planted first", "The check reads Hermes itself", "The record opens anywhere",
                      "memories/MEMORY.md", "state.db", "MANIFEST.sha256", "Prove what you can do with Hermes"):
            self.assertIn(words, card)

    def test_the_start_here_card_comes_straight_after_the_banner_and_foundations_follows_the_paths(self):
        text = (SRC / "plugin.js").read_text(encoding="utf-8")
        banner = text.index("jsx(Banner, {")
        first = text.index("jsx(foundationsViews.FirstFlightCard")
        lead = text.index("up the mountain, each named for one of Hermes's old jobs")
        card = text.index("jsx(foundationsViews.FoundationsCard")
        trail = text.index("title: 'Trail map'")
        self.assertLess(banner, trail)
        self.assertLess(trail, first)
        self.assertLess(first, lead)
        self.assertLess(lead, card)

    def test_a_bare_step_number_is_not_shown_over_the_step(self):
        self.assertIn("!/^Step \\d+$/.test(String(eyebrow))", (SRC / "foundations.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
