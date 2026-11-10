"""The record cover's cost line and help summary.

Hermes's own estimate for the practice chat, never an invented dollar; Field Academy's calls in tokens; the last
reading kept for when the practice profile is deleted; and the record entry carries "No hints used" or "Caught
after one nudge" without changing how its number or chain is made.
"""

from __future__ import annotations

import pathlib
import shutil
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
import test_ai_guide as tg  # noqa: E402
from test_ai_fakes import FakeLlm, RoutedLlm  # noqa: E402


class Cost(tg.GuideCase):
    def setUp(self):
        super().setUp()
        self.cost = self.mod("cost")

    def usage(self, rows):
        """One practice chat per row, priced the way Hermes records it: ``usd`` None means cost_status unknown."""
        con = hf.state_db(self.home())
        for n, (model, usd, tokens) in enumerate(rows):
            hf.add_session(con, started_at=hf.T0 + 500 + n, model=model, input_tokens=tokens, output_tokens=10,
                           estimated_cost_usd=usd or 0, cost_status="unknown" if usd is None else "estimated")
        con.close()

    def test_hermes_estimate_with_its_model(self):
        aid = self.missed()
        self.usage([("anthropic/claude-sonnet-4.6", 0.021, 4000), ("anthropic/claude-sonnet-4.6", 0.009, 2000)])
        out = self.cost.attempt_cost(aid)
        self.assertEqual(out["practice"]["usd"], 0.03)
        self.assertEqual(out["line"], "This practice: about $0.03, Hermes's own estimate on anthropic/claude-sonnet-4.6.")

    def test_no_estimate_means_tokens_only(self):
        aid = self.missed()
        self.usage([("local/model", None, 5000)])
        out = self.cost.attempt_cost(aid)
        self.assertIsNone(out["practice"]["usd"])
        self.assertNotIn("$", out["line"])
        self.assertIn("5,010 tokens", out["line"])

    def test_a_plan_that_includes_the_cost_says_so(self):
        aid = self.missed()
        con = hf.state_db(self.home())
        hf.add_session(con, started_at=hf.T0 + 600, model="openai/gpt-5", estimated_cost_usd=0, cost_status="included")
        con.close()
        self.assertIn("included in your plan", self.cost.attempt_cost(aid)["line"])

    def test_a_partly_priced_practice_says_so(self):
        aid = self.missed()
        self.usage([("a", 0.02, 100), ("b", None, 100)])
        self.assertIn("for the parts Hermes could price", self.cost.attempt_cost(aid)["line"])

    def test_the_last_reading_is_kept_after_the_profile_is_deleted(self):
        aid = self.missed()
        self.usage([("anthropic/claude-sonnet-4.6", 0.04, 4000)])
        self.cost.attempt_cost(aid)
        shutil.rmtree(self.home())
        out = self.cost.attempt_cost(aid)
        self.assertEqual((out["practice_source"], out["practice"]["usd"]), ("kept", 0.04))

    def test_guide_and_grading_in_tokens_per_attempt(self):
        aid = self.missed()
        self.assertEqual(self.cost.attempt_cost(aid)["guide_line"], "Field guide and grading: not used.")
        self.runtime.set_llm(RoutedLlm({"field_academy_nudge": [self.good_nudge(aid)], "field_academy_explain": [self.explain_reply()] * 6}))
        self.view(aid)
        out = self.cost.attempt_cost(aid)
        self.assertEqual(out["guide_tokens"], 160 * out["guide_calls"])
        self.assertIn("tokens over", out["guide_line"])
        self.assertNotIn("$", out["guide_line"])


class RecordCarriesHelp(tg.GuideCase):
    LIMITS = tg.tmm.MemoryMission.__dict__.get("LIMITS", "It shows one practice mission on my own laptop and nothing more.")

    def test_the_record_entry_reads_the_help_and_the_cost(self):
        fr = self.mod("field_record")
        self.mod("evidence").detect_version_detail = lambda: {"value": "0.23.0", "source": "git tag", "exact": True}
        aid = self.missed()
        self.runtime.set_llm(RoutedLlm({"field_academy_nudge": [self.good_nudge(aid)], "field_academy_explain": [self.explain_reply()] * 6}))
        self.view(aid)
        self.guide.use_help(aid, rung=1)
        with self.store.connect() as conn:
            conn.execute("INSERT INTO f_record(attempt_id, mission_id, body_json, hash, prev_hash, created_at) VALUES (?, ?, ?, ?, '', ?)",
                         (aid, tg.MID, '{"mission": "f.memory"}', "0" * 64, self.store.now()))
        body = fr.build("Ada", "One practice mission.")
        entry = body["entries"][0]
        self.assertEqual(entry["help"]["words"], "One hint used")
        self.assertIn("This practice:", entry["cost"]["practice"])
        self.assertIn("tokens", entry["cost"]["guide"])
        self.assertTrue(fr.record_number(body).startswith("FA-"))


if __name__ == "__main__":
    unittest.main()
