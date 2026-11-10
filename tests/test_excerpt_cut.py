"""Record excerpts end at a word, never inside one (fix in 0.9 M6): scrub.clip and the readers that keep excerpts."""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_scrub import load  # noqa: E402

LINE = ("Working files live in the shared folder Ops/2026; drafts go in Ops/2026/Drafts until approved, and nothing "
        "leaves the folder before the owner has read it twice and signed the cover sheet in blue ink on Fridays.")


class Clip(unittest.TestCase):
    def setUp(self):
        self.scrub = load("scrub")
        self.checks = load("foundations_checks")

    def test_a_line_that_fits_is_kept_whole(self):
        self.assertEqual(self.scrub.clip("Shift plans use 24-hour times.", 300), "Shift plans use 24-hour times.")

    def test_a_long_line_ends_at_a_word_with_an_ellipsis(self):
        out = self.scrub.clip(LINE, 60)
        self.assertLessEqual(len(out), 60)
        self.assertTrue(out.endswith("…"))
        head = out[:-1]
        self.assertTrue(LINE.startswith(head))
        self.assertTrue(LINE[len(head)] == " ", f"cut inside a word: {out!r}")

    def test_one_long_word_is_cut_rather_than_dropped(self):
        out = self.scrub.clip("x." * 200, 50)
        self.assertEqual(len(out), 50)

    def test_secrets_are_removed_before_the_cut(self):
        key = "sk" + "-" + "a" * 30
        out = self.scrub.clip(f"the key is {key} and more words follow here", 40)
        self.assertNotIn("aaaa", out)

    def test_evidence_is_cut_at_a_word_and_passes_the_store_guard(self):
        kind, rel, text, _ = self.checks.make_evidence("memory", "memories/MEMORY.md", LINE * 3)
        self.assertLessEqual(len(text), self.checks.EXCERPT)
        self.assertEqual(self.scrub.scrub(text, self.checks.EXCERPT), text)
        body = text.rstrip("…")
        self.assertIn((LINE * 3)[len(body)], " ")

    def test_an_excerpt_around_a_term_starts_at_a_word(self):
        text = "word " * 200 + "QuickBooks Online is the software. " + "tail " * 200
        out = self.checks._excerpt_around(text, "QuickBooks")
        self.assertTrue(out.startswith("…word ") or out.startswith("…QuickBooks"), out[:20])
        self.assertIn("QuickBooks", out)
        self.assertLessEqual(len(out), 300)


if __name__ == "__main__":
    unittest.main()
