"""Spaced review through the real state module, with the clock moved by hand."""

import json
import pathlib
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402


class ReviewScheduleTests(AcademyCase):
    def test_a_passed_mission_comes_due_two_days_later(self):
        self.pass_mission("operator.runtime")
        rows = self.rows("SELECT * FROM reviews")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["mission_id"], "operator.runtime")
        self.assertEqual(rows[0]["due_at"], (self.now + timedelta(days=2)).isoformat())
        self.assertEqual(rows[0]["stage"], 0)

    def test_an_unfinished_mission_has_no_review(self):
        self.state.update_step("operator.runtime", "concept", "done")
        self.assertEqual(self.rows("SELECT * FROM reviews"), [])

    def test_nothing_is_due_straight_after_a_pass(self):
        self.pass_mission("operator.runtime")
        overview = self.state.review_overview()
        self.assertEqual(overview["due_count"], 0)
        self.assertEqual(overview["next_due_title"], "Find where Hermes is running")

    def test_it_is_due_after_two_days(self):
        self.pass_mission("operator.runtime")
        self.advance(days=2)
        overview = self.state.review_overview()
        self.assertEqual([item["mission_id"] for item in overview["due"]], ["operator.runtime"])

    def test_the_first_strength_is_the_score_on_the_question(self):
        self.pass_mission("operator.runtime", score=91)
        self.assertEqual(self.state.review_overview()["strength"]["operator.runtime"]["strength"], 91)

    def test_the_queue_lists_the_mission_title_and_a_strength_word(self):
        self.pass_mission("operator.runtime", score=91)
        entry = self.state.review_overview()["strength"]["operator.runtime"]
        self.assertEqual(entry["title"], "Find where Hermes is running")
        self.assertEqual(entry["strength_word"], "Strong")

    def test_a_mission_not_reviewed_for_a_long_time_stops_showing_as_strong(self):
        self.pass_mission("operator.runtime", score=91)
        self.advance(days=60)
        entry = self.state.review_overview()["strength"]["operator.runtime"]
        self.assertLess(entry["strength"], 40)
        self.assertEqual(entry["strength_word"], "Weak")

    def test_the_review_schedule_is_saved_across_a_restart(self):
        self.pass_mission("operator.runtime")
        before = self.rows("SELECT * FROM reviews")
        self.assertEqual(before, self.rows("SELECT * FROM reviews"))
        self.assertEqual(self.state.snapshot()["reviews"]["passed_missions"], 1)

    def test_every_mission_has_three_review_questions(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            self.assertEqual([r["id"] for r in mission["review"]], ["r1", "r2", "r3"], mission_id)

    def test_review_questions_stay_out_of_the_passport(self):
        for track in self.state.snapshot()["tracks"]:
            for mission in track["missions"]:
                self.assertNotIn("review", mission, mission["id"])


class ReviewSessionTests(AcademyCase):
    ANSWER = "In my own words, a scheduled job needs the gateway, which runs apart from the window."

    def due_session(self, *missions):
        for mission_id in missions:
            self.pass_mission(mission_id)
        self.advance(days=3)
        return self.state.start_review()

    def answers(self, session):
        return {item["mission_id"]: self.ANSWER for item in session["items"]}

    def test_a_session_asks_one_question_from_each_due_mission(self):
        session = self.due_session("operator.runtime", "operator.desktop", "ambassador.story")
        self.assertEqual(len(session["items"]), 3)
        self.assertEqual(len({item["mission_id"] for item in session["items"]}), 3)
        for item in session["items"]:
            self.assertTrue(item["question"])
            self.assertIn(item["item_id"], ("r1", "r2", "r3"))

    def test_a_session_is_never_longer_than_three(self):
        session = self.due_session("operator.runtime", "operator.desktop", "ambassador.story", "ambassador.qualify")
        self.assertEqual(len(session["items"]), 3)

    def test_nothing_due_says_when_the_next_one_is(self):
        self.pass_mission("operator.runtime")
        with self.assertRaisesRegex(ValueError, "Nothing is due.*Find where Hermes is running"):
            self.state.start_review()

    def test_before_any_pass_there_is_nothing_to_review(self):
        with self.assertRaisesRegex(ValueError, "two days after you pass it"):
            self.state.start_review()

    def test_practice_early_works_when_nothing_is_due(self):
        self.pass_mission("operator.runtime")
        session = self.state.start_review(practice=True)
        self.assertTrue(session["practice"])
        self.assertTrue(session["items"][0]["early"])

    def test_starting_twice_resumes_the_same_session(self):
        first = self.due_session("operator.runtime")
        self.assertEqual(self.state.start_review()["id"], first["id"])

    def test_an_old_unfinished_session_is_replaced(self):
        first = self.due_session("operator.runtime")
        self.advance(hours=30)
        self.assertNotEqual(self.state.start_review()["id"], first["id"])

    def test_answers_need_a_sentence_each(self):
        session = self.due_session("operator.runtime")
        with self.assertRaisesRegex(ValueError, "at least a sentence"):
            self.state.submit_review(session["id"], {"operator.runtime": "short"})

    def test_submitting_returns_a_grading_instruction_for_the_learners_own_hermes(self):
        session = self.due_session("operator.runtime", "operator.desktop")
        payload = self.state.submit_review(session["id"], self.answers(session))
        prompt = payload["prompt"]
        self.assertIn("field_academy_grade_review", prompt)
        self.assertIn(session["id"], prompt)
        self.assertIn("Never offer to pass anyone anyway", prompt)
        for item in session["items"]:
            self.assertIn(item["question"], prompt)
            self.assertIn(self.ANSWER, prompt)
        self.assertIn("The threshold to pass is 70", prompt)

    def test_the_session_waits_for_scores_after_submitting(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        self.assertEqual(self.state.get_review_session(session["id"])["status"], "submitted")

    def grade(self, session, scores, missed=None):
        grades = [
            {"mission_id": item["mission_id"], "score": scores[i], "missed": (missed or {}).get(i, []), "feedback": "You named the gateway."}
            for i, item in enumerate(session["items"])
        ]
        return self.state.grade_review(session["id"], grades)

    def test_a_strong_answer_moves_the_mission_up_a_rung(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        result = self.grade(session, [92])["results"][0]
        self.assertEqual((result["outcome"], result["stage"]), ("advanced", 1))
        self.assertEqual(result["interval_days"], 7)
        due = self.rows("SELECT due_at FROM reviews")[0]["due_at"]
        self.assertEqual(due, (self.now + timedelta(days=7)).isoformat())

    def test_a_passing_answer_that_is_not_strong_holds_the_rung(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        result = self.grade(session, [75])["results"][0]
        self.assertEqual((result["outcome"], result["stage"], result["interval_days"]), ("held", 0, 2))

    def test_a_weak_answer_brings_the_mission_back_tomorrow(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        result = self.grade(session, [45], {0: [1]})["results"][0]
        self.assertEqual((result["outcome"], result["interval_days"]), ("lapsed", 1))
        self.assertEqual(self.rows("SELECT lapses FROM reviews")[0]["lapses"], 1)
        self.advance(days=1)
        self.assertEqual(self.state.review_overview()["due_count"], 1)

    def test_a_miss_says_what_was_missing_and_gives_a_hint(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        result = self.grade(session, [45], {0: [1]})["results"][0]
        ladder = result["ladder"]
        self.assertEqual(ladder["level"], 1)
        self.assertTrue(ladder["missing"][0]["what"].startswith("Missing point:"))
        self.assertTrue(ladder["hint"])
        self.assertEqual(ladder["example"], "")

    def test_a_second_miss_in_a_row_adds_a_worked_example(self):
        for round_number in range(2):
            session = self.due_session("operator.runtime") if round_number == 0 else self.state.start_review()
            self.state.submit_review(session["id"], self.answers(session))
            result = self.grade(session, [45], {0: [1]})["results"][0]
            self.advance(days=2)
        self.assertEqual(result["ladder"]["level"], 2)
        self.assertTrue(result["ladder"]["example"])

    def test_a_pass_clears_the_run_of_misses(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        self.grade(session, [45], {0: [1]})
        self.advance(days=1)
        second = self.state.start_review()
        self.state.submit_review(second["id"], self.answers(second))
        self.grade(second, [90])
        self.assertEqual(self.rows("SELECT consecutive_misses FROM reviews")[0]["consecutive_misses"], 0)

    def test_the_question_changes_each_time_a_mission_comes_back(self):
        seen = []
        session = self.due_session("operator.runtime")
        for _ in range(3):
            seen.append(session["items"][0]["item_id"])
            self.state.submit_review(session["id"], self.answers(session))
            self.grade(session, [90])
            self.advance(days=100)
            session = self.state.start_review()
        self.assertEqual(seen, ["r1", "r2", "r3"])

    def test_strength_is_a_running_mean_leaning_on_the_latest_answer(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        result = self.grade(session, [60])["results"][0]
        self.assertEqual(result["strength"], round(0.4 * 88 + 0.6 * 60))

    def test_early_practice_changes_strength_but_not_the_schedule(self):
        self.pass_mission("operator.runtime")
        before = self.rows("SELECT * FROM reviews")[0]
        session = self.state.start_review(practice=True)
        self.state.submit_review(session["id"], self.answers(session))
        result = self.grade(session, [95])["results"][0]
        after = self.rows("SELECT * FROM reviews")[0]
        self.assertEqual(result["outcome"], "practiced")
        self.assertEqual((after["stage"], after["due_at"]), (before["stage"], before["due_at"]))
        self.assertNotEqual(after["strength"], before["strength"])

    def test_a_session_cannot_be_scored_twice(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        self.grade(session, [90])
        with self.assertRaisesRegex(ValueError, "already scored"):
            self.grade(session, [20])

    def test_scoring_needs_a_submitted_session(self):
        session = self.due_session("operator.runtime")
        with self.assertRaisesRegex(ValueError, "Nothing has been submitted"):
            self.grade(session, [90])

    def test_every_question_needs_a_grade(self):
        session = self.due_session("operator.runtime", "operator.desktop")
        self.state.submit_review(session["id"], self.answers(session))
        with self.assertRaisesRegex(ValueError, "Add a grade"):
            self.state.grade_review(session["id"], [{"mission_id": session["items"][0]["mission_id"], "score": 80}])

    def test_a_score_is_clamped_to_the_range(self):
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        self.assertEqual(self.grade(session, [900])["results"][0]["score"], 100)

    def test_the_agent_tool_scores_a_review(self):
        tools = sys.modules[f"{self.name}.tools"]
        session = self.due_session("operator.runtime")
        self.state.submit_review(session["id"], self.answers(session))
        grades = [{"mission_id": "operator.runtime", "score": 91, "missed": [], "feedback": "Clear."}]
        reply = json.loads(tools.field_academy_grade_review({"session_id": session["id"], "grades": grades}))
        self.assertEqual(reply["results"][0]["outcome"], "advanced")

    def test_the_agent_tool_reports_a_bad_session_as_an_error_message(self):
        tools = sys.modules[f"{self.name}.tools"]
        reply = json.loads(tools.field_academy_grade_review({"session_id": "nope", "grades": []}))
        self.assertIn("error", reply)

    def test_the_review_tool_is_registered_and_declared(self):
        names = []

        class Ctx:
            def register_tool(self, name, **kwargs):
                names.append(name)

            def register_hook(self, *args, **kwargs):
                pass

            def register_command(self, *args, **kwargs):
                pass

            def register_skill(self, *args, **kwargs):
                pass

        self.pkg.register(Ctx())
        self.assertIn("field_academy_grade_review", names)
        text = (pathlib.Path(sys.modules[self.name].__file__).parent / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("field_academy_grade_review", text)


class ReviewQueueScreenDataTests(AcademyCase):
    def test_the_passport_carries_the_queue(self):
        self.pass_mission("operator.runtime")
        self.advance(days=3)
        reviews = self.state.snapshot()["reviews"]
        for key in ("due_count", "due", "strength", "passed_missions", "next_due_at", "minutes", "can_practice", "open_session", "last_session"):
            self.assertIn(key, reviews)
        self.assertEqual(reviews["due_count"], 1)
        self.assertEqual(reviews["minutes"], 2)

    def test_a_session_in_progress_shows_on_the_queue(self):
        self.pass_mission("operator.runtime")
        self.advance(days=3)
        session = self.state.start_review()
        self.assertEqual(self.state.snapshot()["reviews"]["open_session"]["id"], session["id"])

    def test_a_scored_session_shows_as_the_last_one(self):
        self.pass_mission("operator.runtime")
        self.advance(days=3)
        session = self.state.start_review()
        self.state.submit_review(session["id"], {"operator.runtime": "Scheduled jobs need the gateway, which runs apart from the window."})
        self.state.grade_review(session["id"], [{"mission_id": "operator.runtime", "score": 88, "feedback": "Good."}])
        last = self.state.snapshot()["reviews"]["last_session"]
        self.assertEqual(last["status"], "graded")
        self.assertEqual(last["results"][0]["score"], 88)

    def test_the_mission_shows_its_strength_on_the_map(self):
        self.pass_mission("operator.runtime", score=90)
        mission = next(m for m in self.track("operator")["missions"] if m["id"] == "operator.runtime")
        self.assertEqual(mission["strength"], 90)
        self.assertEqual(mission["strength_word"], "Strong")
        self.assertTrue(mission["review_due_at"])

    def test_the_honest_count_separates_passed_from_holding(self):
        self.pass_mission("operator.runtime", score=90)
        self.pass_mission("operator.desktop", score=90)
        self.advance(days=200)
        honest = self.state.snapshot()["honest"]
        self.assertEqual((honest["passed"], honest["holding"]), (2, 0))

    def test_the_agent_summary_mentions_what_is_due(self):
        self.pass_mission("operator.runtime")
        self.advance(days=3)
        self.assertEqual(self.state.compact()["reviews_due"], 1)

    def test_the_academy_command_mentions_reviews_due(self):
        self.pass_mission("operator.runtime")
        self.advance(days=3)
        self.assertIn("Review: 1 mission due", self.pkg._academy_command(""))


if __name__ == "__main__":
    unittest.main()
