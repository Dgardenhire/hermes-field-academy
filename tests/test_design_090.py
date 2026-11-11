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

    def test_the_start_here_card_comes_straight_after_the_banner_and_foundations_sits_beside_it(self):
        # Rubric pass, Nov 11: the eleven Foundations missions sit next to Start here, not tenth on the page.
        text = (SRC / "plugin.js").read_text(encoding="utf-8")
        banner = text.index("jsx(Banner, {")
        first = text.index("jsx(foundationsViews.FirstFlightCard")
        lead = text.index("up the mountain, each named for one of Hermes's old jobs")
        card = text.index("jsx(foundationsViews.FoundationsCard")
        trail = text.index("title: 'Trail map'")
        self.assertLess(banner, trail)
        self.assertLess(trail, first)
        self.assertLess(first, card)
        self.assertLess(card, lead)
        self.assertEqual(text.count("jsx(foundationsViews.FoundationsCard"), 1)
        self.assertIn("compact: true }, 'foundations')", text[card:card + 200])

    def test_the_home_map_marks_one_you_are_here_not_one_per_trail(self):
        field = (SRC / "field.js").read_text(encoding="utf-8")
        page = (SRC / "plugin.js").read_text(encoding="utf-8")
        self.assertIn("marked: here === undefined || here === model.id", field)
        self.assertIn("model.total && marked ? jsx(Marker", field)
        self.assertEqual(page.count("here: mapHere"), 2)  # the four-trail map and the Guide panel share one marker
        self.assertIn("go, here: mapHere }, 'deployer')", page)

    def test_both_switches_have_a_control_on_the_page_and_in_hermes_settings(self):
        page = (SRC / "plugin.js").read_text(encoding="utf-8")
        panel = page[page.index("function SettingsPanel"):page.index("function PracticeOffer")]
        for name in ("'ai_help'", "'practice_offer'", "type: 'checkbox'", "'/settings/ai'", "method: 'POST'"):
            self.assertIn(name, page[page.index("const SWITCHES"):page.index("function PracticeOffer")])
        self.assertIn("useAiSettings()", panel)  # one shared copy of the switches for the panel and the home card
        store = page[page.index("function loadAiSettings"):page.index("function SettingsPanel")]
        self.assertIn("ctxRest('/settings/ai')", store)
        self.assertIn("setTimeout(() => loadAiSettings(attempt + 1), 3000)", store)  # Hermes may still be starting
        # Field Academy asks before it adds anything to a chat: the question sits at the top of the home page.
        card = page[page.index("function ChatSuggestCard"):page.index("// Delete my Field Academy data")]
        for words in ("Want mission suggestions while you chat?", "Yes, suggest missions", "Not now", "practice_offer_asked"):
            self.assertIn(words, card)
        # It runs across the page above the map and Start here, so it is the first thing under the banner.
        self.assertIn("    banner,\n    jsx(ChatSuggestCard, {}, 'suggest'),\n    jsxs('div', { className: 'fa-top'", page)
        self.assertIn("jsx(Section, { title: 'Settings', children: jsx(SettingsPanel, {}) }, 'settings')", page)
        self.assertIn("if (typeof ctx.registerSettingsPage === 'function')", page)
        settings_page = page[page.index("ctx.registerSettingsPage({"):]
        self.assertIn("jsx(SettingsPanel, {}", settings_page)
        self.assertIn("jsx(DataPanel, {}", settings_page)

    def test_a_missing_backend_never_shows_a_bare_not_found(self):
        page = (SRC / "plugin.js").read_text(encoding="utf-8")
        self.assertIn("/^(?:404:?\\s*)?not found\\.?$/i.test(text.trim()) ? NO_BACKEND : text", page)
        self.assertIn("query.data && (query.stale ||", page)

    def test_a_bare_step_number_is_not_shown_over_the_step(self):
        self.assertIn("!/^Step \\d+$/.test(String(eyebrow))", (SRC / "foundations.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


class LiveCheckNov11(unittest.TestCase):
    """Two things the Nov 11 live run found: fields whose borders could not be seen, and a fix step that left the
    second slash command for the learner to type past Hermes's command picker."""

    def test_fields_have_a_visible_border(self):
        page = (ROOT / "desktop" / "src" / "plugin.js").read_text()
        self.assertIn(".hk textarea{border-color:color-mix(in srgb,currentColor 45%,transparent)}", page)

    def test_the_fix_button_drafts_each_command_in_turn(self):
        desk = (ROOT / "desktop" / "src" / "desk.js").read_text()
        self.assertIn("commands[i]", desk)
        self.assertIn("setNext(more ? i + 1 : 0)", desk)


class RecordStaysShown(unittest.TestCase):
    """Nov 11 live check: adding to the record reloaded through attempt/start, which opened a fresh blank try."""

    def test_adding_keeps_the_finished_attempt_on_screen(self):
        src = (ROOT / "desktop" / "src" / "foundations.js").read_text()
        self.assertIn("if (out && out.added) setJustAdded(out.added); else return reloadAll()", src)
        self.assertIn("view.record || preview?.added || justAdded", src)
        self.assertIn("jsx(DeletePractice, { view, listing, reloadAll: null })", src)
