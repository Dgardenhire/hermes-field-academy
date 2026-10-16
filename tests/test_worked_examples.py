"""Worked examples and fading support: a finished example, then one with gaps, then the learner alone."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402

M = "integrator.discovery"


class ShapeTests(AcademyCase):
    def test_every_mission_runs_read_example_gaps_try_explain_check(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            # A story-first mission shows the finished example before the short takeaway.
            first = ["example", "lesson"] if mission.get("story_first") else ["lesson", "example"]
            self.assertEqual([s["kind"] for s in mission["steps"]], first + ["complete", "lab", "explain", "gate"], mission_id)

    def test_the_support_fades_in_order(self):
        # Every mission opens with its story (full support), then the takeaway, then the half-done one,
        # then the learner alone.
        for mission_id, mission in self.curriculum.MISSIONS.items():
            if mission["level"] == "capstone" and not mission.get("story_first"):
                continue
            self.assertTrue(mission.get("story_first"), mission_id)
            kinds = [s["kind"] for s in mission["steps"]]
            self.assertEqual(kinds[:3], ["example", "lesson", "complete"], mission_id)
            support = [s.get("support") for s in mission["steps"] if s.get("support")]
            self.assertEqual(support[:2], ["full", "half"], mission_id)
            self.assertTrue(all(level == "none" for level in support[2:]), mission_id)

    def test_every_example_is_labelled_by_sub_goal(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            step = next(s for s in mission["steps"] if s["kind"] == "example")
            self.assertTrue(3 <= len(step["parts"]) <= 5, mission_id)
            for part in step["parts"]:
                self.assertTrue(part["label"] and part["text"], mission_id)

    def test_every_half_finished_example_has_two_to_four_gaps(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            step = next(s for s in mission["steps"] if s["kind"] == "complete")
            gaps = [p for p in step["parts"] if "gap" in p]
            self.assertTrue(2 <= len(gaps) <= 4, mission_id)

    def test_every_document_mission_shows_a_whole_finished_document(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            gate = next(s for s in mission["steps"] if s["kind"] == "gate")
            example = next(s for s in mission["steps"] if s["kind"] == "example")
            if gate["verify"] == "artifact":
                self.assertTrue(example["document"].startswith("#"), mission_id)

    def test_every_worked_document_passes_the_check_the_learner_faces(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            gate = next(s for s in mission["steps"] if s["kind"] == "gate")
            if gate["verify"] != "artifact":
                continue
            example = next(s for s in mission["steps"] if s["kind"] == "example")
            result = self.documents.analyze(example["document"], gate)
            self.assertEqual(result["missing"], [], mission_id)

    def test_every_half_finished_example_passes_once_its_gaps_hold_the_model_answers(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            gate = next(s for s in mission["steps"] if s["kind"] == "gate")
            if gate["verify"] != "artifact":
                continue
            complete = next(s for s in mission["steps"] if s["kind"] == "complete")
            text = "".join(p.get("text") or p["answer"] for p in complete["parts"])
            self.assertEqual(self.documents.analyze(text, gate)["missing"], [], mission_id)

    def test_the_example_is_not_a_free_pass_through_the_check(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            gate = next(s for s in mission["steps"] if s["kind"] == "gate")
            if gate["verify"] != "artifact":
                continue
            example = next(s for s in mission["steps"] if s["kind"] == "example")
            models = self.state._models(mission_id)
            ids = [m["id"] for m in self.documents.analyze(example["document"], gate, models)["missing"]]
            self.assertIn("copied", ids, mission_id)

    def test_the_passport_hides_the_model_answers_until_the_learner_has_tried(self):
        step = self.passport_step(M, "complete")
        for part in step["parts"]:
            self.assertNotIn("answer", part)

    def test_the_passport_carries_each_gaps_prompt_and_minimum(self):
        gaps = [p for p in self.passport_step(M, "complete")["parts"] if "gap" in p]
        for gap in gaps:
            self.assertTrue(gap["prompt"])
            self.assertGreaterEqual(gap["min_words"], 1)


class CompletionTests(AcademyCase):
    def answers(self):
        return {p["gap"]: p["answer"] for p in self.step(M, "complete")["parts"] if "gap" in p}

    def test_the_step_cannot_be_ticked_by_hand(self):
        with self.assertRaisesRegex(ValueError, "Fill in the gaps"):
            self.state.update_step(M, "complete", "done")

    def test_empty_gaps_are_sent_back_with_what_each_needs(self):
        reply = self.state.submit_completion(M, "complete", {})
        self.assertFalse(reply["ok"])
        self.assertEqual({p["id"] for p in reply["problems"]}, set(self.answers()))
        self.assertIsNone(reply["model"])
        self.assertEqual(self.passport_step(M, "complete")["status"], "ready")

    def test_a_gap_that_is_too_short_says_how_many_words_it_needs(self):
        answers = self.answers()
        answers["owner"] = "Marcus"
        reply = self.state.submit_completion(M, "complete", answers)
        owner = next(p for p in reply["problems"] if p["id"] == "owner")
        self.assertRegex(owner["what"], r"at least \d+ words. You have 1")

    def test_a_gap_that_needs_a_name_says_so(self):
        answers = self.answers()
        answers["owner"] = "the office manager who reviews the list before anything is sent out"
        reply = self.state.submit_completion(M, "complete", answers)
        self.assertIn("a person's name", next(p for p in reply["problems"] if p["id"] == "owner")["what"])

    def test_a_gap_that_needs_a_list_keeps_its_line_breaks(self):
        answers = self.answers()
        answers["out"] = "- Rescheduling a visit without a person\n- Reading patient records"
        reply = self.state.submit_completion(M, "complete", answers)
        self.assertTrue(reply["ok"], reply["problems"])

    def test_placeholder_text_in_a_gap_is_refused(self):
        answers = self.answers()
        answers["owner"] = "TODO write the owner here later today please thanks"
        reply = self.state.submit_completion(M, "complete", answers)
        self.assertIn("placeholder", next(p for p in reply["problems"] if p["id"] == "owner")["what"])

    def test_good_answers_show_the_model_answers_and_finish_the_step(self):
        reply = self.state.submit_completion(M, "complete", self.answers())
        self.assertTrue(reply["ok"])
        self.assertEqual(reply["model"], self.answers())
        self.assertEqual(self.passport_step(M, "complete")["status"], "done")

    def test_the_learners_answers_are_kept_and_the_model_comes_back_with_them(self):
        mine = {key: value + " and more words so it is mine" for key, value in self.answers().items()}
        mine["out"] = "- Rescheduling a visit without any person involved\n- Reading or changing medical records"
        self.state.submit_completion(M, "complete", mine)
        saved = self.passport_step(M, "complete")["saved"]
        self.assertTrue(saved["revealed"])
        self.assertEqual(saved["answers"]["out"], mine["out"])
        self.assertEqual(saved["model"], self.answers())

    def test_the_model_answers_stay_hidden_after_a_miss(self):
        self.state.submit_completion(M, "complete", {})
        self.assertFalse(self.passport_step(M, "complete")["saved"]["revealed"])
        self.assertIsNone(self.passport_step(M, "complete")["saved"]["model"])

    def test_after_two_misses_the_answers_can_be_shown_but_the_step_stays_open(self):
        self.state.submit_completion(M, "complete", {})
        second = self.state.submit_completion(M, "complete", {})
        self.assertTrue(second["can_show"])
        shown = self.state.submit_completion(M, "complete", {}, show_anyway=True)
        self.assertEqual(shown["model"], self.answers())
        self.assertFalse(shown["ok"])
        self.assertEqual(self.passport_step(M, "complete")["status"], "ready")

    def test_one_miss_does_not_unlock_the_answers(self):
        self.state.submit_completion(M, "complete", {})
        reply = self.state.submit_completion(M, "complete", {}, show_anyway=True)
        self.assertIsNone(reply["model"])

    def test_a_wrong_step_is_refused(self):
        with self.assertRaises(ValueError):
            self.state.submit_completion(M, "concept", {})
        with self.assertRaises(ValueError):
            self.state.submit_completion("nope", "complete", {})

    def test_the_step_counts_toward_the_mission(self):
        self.state.submit_completion(M, "complete", self.answers())
        mission = self.mission(M)
        self.assertEqual(mission["completed_steps"], 1)
        self.assertEqual(mission["total_steps"], 6)


class SupportBarTests(AcademyCase):
    """The page's three stages come from learn.js; the data they read comes from here."""

    def test_a_fresh_mission_starts_at_the_full_example(self):
        steps = self.mission(M)["steps"]
        self.assertEqual([s["status"] for s in steps], ["ready"] * 6)

    def test_the_example_is_tickable_like_the_lesson(self):
        self.state.update_step(M, "example", "done")
        self.assertEqual(self.passport_step(M, "example")["status"], "done")

    def test_each_step_says_how_long_it_takes(self):
        for step in self.mission(M)["steps"]:
            self.assertGreater(step["minutes"], 0, step["id"])

    def test_the_missions_time_is_the_sum_of_its_steps(self):
        for track in self.state.snapshot()["tracks"]:
            for mission in track["missions"]:
                self.assertEqual(mission["minutes"], sum(s["minutes"] for s in mission["steps"]), mission["id"])
                self.assertEqual(mission["minutes"], sum(mission["time"].values()), mission["id"])

    def test_the_time_estimates_are_honest_not_shorter_than_before(self):
        # 0.4.0 said 10 minutes for the first mission and gave one question and a check; 0.5.0 adds two steps.
        self.assertGreaterEqual(self.curriculum.MISSIONS["operator.runtime"]["minutes"], 20)


if __name__ == "__main__":
    unittest.main()
