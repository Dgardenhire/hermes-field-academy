"""The placement check: a short test that skips reading and practice, and never the check on real work."""

import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402


class PlacementCase(AcademyCase):
    def spec(self, track_id="operator"):
        return self.curriculum.PLACEMENTS[track_id]

    def answers(self, track_id="operator", known=("beginner", "intermediate", "advanced")):
        out = {}
        for q in self.spec(track_id)["questions"]:
            right = q["answer"]
            out[q["id"]] = right if q["level"] in known else (right + 1) % len(q["options"])
        return out


class QuestionTests(PlacementCase):
    def test_every_path_has_a_placement_check_with_six_questions(self):
        for track_id in self.curriculum.TRACKS:
            questions = self.spec(track_id)["questions"]
            self.assertEqual(len(questions), 6, track_id)
            for level in ("beginner", "intermediate", "advanced"):
                self.assertEqual(sum(1 for q in questions if q["level"] == level), 2, f"{track_id} {level}")

    def test_the_questions_are_served_without_the_answers(self):
        payload = self.state.placement_questions("operator")
        self.assertEqual(len(payload["questions"]), 6)
        for q in payload["questions"]:
            self.assertNotIn("answer", q)
            self.assertNotIn("why", q)
        self.assertNotIn('"answer"', json.dumps(self.state.snapshot()["tracks"]))

    def test_the_right_answer_is_not_always_in_the_same_place(self):
        for track_id in self.curriculum.TRACKS:
            positions = {q["answer"] for q in self.spec(track_id)["questions"]}
            self.assertGreaterEqual(len(positions), 3, track_id)

    def test_the_right_option_is_never_conspicuously_the_longest(self):
        for track_id in self.curriculum.TRACKS:
            for q in self.spec(track_id)["questions"]:
                lengths = [len(o) for o in q["options"]]
                right = lengths[q["answer"]]
                others = [n for i, n in enumerate(lengths) if i != q["answer"]]
                self.assertLessEqual(right, 1.3 * (sum(others) / len(others)), q["id"])

    def test_the_intro_says_the_checks_on_real_work_still_apply(self):
        for track_id in self.curriculum.TRACKS:
            self.assertIn("still apply", self.spec(track_id)["intro"].lower(), track_id)

    def test_an_unknown_path_is_refused(self):
        with self.assertRaises(ValueError):
            self.state.placement_questions("wizard")


class ScoringTests(PlacementCase):
    def test_every_question_must_be_answered(self):
        with self.assertRaisesRegex(ValueError, "Answer every question"):
            self.state.submit_placement("operator", {"p1": 0})

    def test_all_right_knows_every_level(self):
        outcome = self.state.submit_placement("operator", self.answers())
        self.assertEqual(outcome["known_levels"], ["beginner", "intermediate", "advanced"])

    def test_beginner_only(self):
        outcome = self.state.submit_placement("operator", self.answers(known=("beginner",)))
        self.assertEqual(outcome["known_levels"], ["beginner"])

    def test_the_result_explains_every_answer(self):
        outcome = self.state.submit_placement("operator", self.answers(known=("beginner",)))
        for q in outcome["results"]["questions"]:
            self.assertTrue(q["why"])

    def test_the_offer_says_the_question_and_the_check_still_count(self):
        outcome = self.state.submit_placement("operator", self.answers(known=("beginner",)))
        self.assertIn("still count", outcome["offer"]["keeps"])
        self.assertEqual({m["level"] for m in outcome["offer"]["missions"]}, {"beginner"})

    def test_the_result_is_saved_and_shown_on_the_path(self):
        self.state.submit_placement("operator", self.answers(known=("beginner",)))
        taken = self.track("operator")["placement"]["taken"]
        self.assertIsNotNone(taken)
        self.assertTrue(taken["results"]["levels"]["beginner"]["known"])
        self.assertIsNone(taken["applied"])

    def test_it_can_be_taken_again(self):
        self.state.submit_placement("operator", self.answers(known=()))
        self.state.submit_placement("operator", self.answers())
        self.assertEqual(len(self.rows("SELECT * FROM placements")), 1)
        self.assertEqual(len(self.state.placement_questions("operator")["taken"]["results"]["levels"]), 3)

    def test_nothing_changes_until_the_learner_applies_it(self):
        self.state.submit_placement("operator", self.answers())
        self.assertEqual(self.rows("SELECT * FROM mission_steps"), [])


class NoFreeSkipTests(PlacementCase):
    def place(self, known=("beginner",)):
        self.state.submit_placement("operator", self.answers(known=known))
        return self.state.apply_placement("operator")

    def test_applying_before_taking_the_check_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Take the placement check first"):
            self.state.apply_placement("operator")

    def test_only_reading_and_practice_are_skipped(self):
        self.place()
        for mission_id in ("operator.runtime", "operator.desktop"):
            statuses = {s["kind"]: s["status"] for s in self.mission(mission_id)["steps"]}
            for kind in ("lesson", "example", "complete", "lab"):
                self.assertEqual(statuses[kind], "placed", f"{mission_id} {kind}")
            self.assertEqual(statuses["explain"], "ready", mission_id)
            self.assertEqual(statuses["gate"], "ready", mission_id)

    def test_levels_that_were_not_known_are_untouched(self):
        self.place()
        statuses = {s["status"] for s in self.mission("operator.learning")["steps"]}
        self.assertEqual(statuses, {"ready"})

    def test_a_skipped_mission_is_not_passed(self):
        self.place()
        mission = next(m for m in self.track("operator")["missions"] if m["id"] == "operator.runtime")
        self.assertNotEqual(mission["status"], "verified")
        self.assertEqual(mission["completed_steps"], 4)

    def test_a_skipped_level_still_needs_its_question_and_its_check(self):
        self.place()
        self.state.submit_explanation("operator.runtime", "explain", "Scheduled jobs need the gateway, which runs apart from the app window. " * 3)
        self.state.grade_explanation("operator.runtime", "explain", 90, "Good.", [])
        self.assertNotEqual(self.mission("operator.runtime")["status"], "verified")
        self.state.record_gate("operator.runtime", "gate", {"passed": True, "title": "ok", "detail": "ok", "facts": []})
        self.assertEqual(self.mission("operator.runtime")["status"], "verified")

    def test_the_question_cannot_be_skipped_by_placement(self):
        self.place(known=("beginner", "intermediate", "advanced"))
        for mission in self.track("operator")["missions"]:
            if mission["level"] == "capstone":
                continue
            explain = next(s for s in mission["steps"] if s["kind"] == "explain")
            self.assertEqual(explain["status"], "ready", mission["id"])

    def test_the_capstone_is_never_skipped(self):
        self.place(known=("beginner", "intermediate", "advanced"))
        statuses = {s["status"] for s in self.mission("operator.capstone")["steps"]}
        self.assertEqual(statuses, {"ready"})

    def test_a_skipped_step_the_learner_already_did_stays_done(self):
        self.state.update_step("operator.runtime", "concept", "done")
        self.place()
        steps = {s["id"]: s["status"] for s in self.mission("operator.runtime")["steps"]}
        self.assertEqual(steps["concept"], "done")
        self.assertEqual(steps["example"], "placed")

    def test_applying_twice_changes_nothing_more(self):
        first = self.place()
        second = self.state.apply_placement("operator")
        self.assertEqual(first["steps_skipped"], 8)
        self.assertEqual(second["steps_skipped"], 0)

    def test_the_applied_levels_and_steps_are_recorded(self):
        self.place()
        applied = self.track("operator")["placement"]["taken"]["applied"]
        self.assertEqual(applied["levels"], ["beginner"])
        self.assertEqual(len(applied["steps"]), 8)

    def test_a_certificate_says_which_missions_had_their_reading_skipped(self):
        self.state.submit_placement("ambassador", self.answers("ambassador", known=("beginner",)))
        self.state.apply_placement("ambassador")
        for item in self.curriculum.TRACKS["ambassador"]["missions"]:
            self.pass_mission(item["id"])
        body = self.state.issue_certificate("ambassador", "Ada Lovelace")["body"]
        skipped = {m["mission_id"]: m["reading_skipped"] for m in body["missions"]}
        self.assertTrue(skipped["ambassador.story"])
        self.assertFalse(skipped["ambassador.qualify"])
        markdown = self.state.certificate_markdown(self.state.get_certificate("ambassador"))
        self.assertIn("reading skipped by placement", markdown)

    def test_a_skipped_step_shows_as_skipped_on_the_page_not_as_done(self):
        self.place()
        steps = self.mission("operator.runtime")["steps"]
        self.assertEqual(steps[0]["status"], "placed")
        self.assertTrue(self.mission("operator.runtime")["placed"])

    def test_placement_counts_toward_the_steps_done(self):
        self.place()
        mission = self.mission("operator.runtime")
        self.assertEqual((mission["completed_steps"], mission["total_steps"]), (4, 6))

    def test_nothing_can_be_placed_without_passing_the_check_itself(self):
        self.state.submit_placement("operator", self.answers(known=()))
        result = self.state.apply_placement("operator")
        self.assertEqual(result["steps_skipped"], 0)
        self.assertEqual(self.rows("SELECT * FROM mission_steps"), [])


if __name__ == "__main__":
    unittest.main()
