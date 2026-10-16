"""Motivation: the learner's own goal, woven into missions, and honest progress with no streaks."""

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase, ROOT  # noqa: E402

GOAL = "Write my weekly status email from my project notes."


class GoalTests(AcademyCase):
    def test_a_new_learner_has_not_been_asked_yet(self):
        goal = self.state.snapshot()["goal"]
        self.assertEqual(goal, {"text": "", "asked": False, "skipped": False})

    def test_the_answer_is_saved_and_shown(self):
        goal = self.state.set_use_goal(GOAL)["goal"]
        self.assertEqual((goal["text"], goal["asked"], goal["skipped"]), (GOAL, True, False))

    def test_a_few_words_at_least(self):
        with self.assertRaisesRegex(ValueError, "few words"):
            self.state.set_use_goal("emails")

    def test_skipping_is_a_real_choice_and_is_remembered(self):
        goal = self.state.set_use_goal("", skipped=True)["goal"]
        self.assertEqual((goal["text"], goal["asked"], goal["skipped"]), ("", True, True))

    def test_the_goal_can_be_changed_later(self):
        self.state.set_use_goal(GOAL)
        goal = self.state.set_use_goal("Answer client questions from our documents.")["goal"]
        self.assertEqual(goal["text"], "Answer client questions from our documents.")

    def test_a_skipped_question_can_be_answered_later(self):
        self.state.set_use_goal("", skipped=True)
        self.assertFalse(self.state.set_use_goal(GOAL)["goal"]["skipped"])

    def test_the_answer_is_trimmed_to_a_sensible_length(self):
        goal = self.state.set_use_goal("word " * 200)["goal"]
        self.assertLessEqual(len(goal["text"]), 240)

    def test_whitespace_is_collapsed(self):
        self.assertEqual(self.state.set_use_goal("Write   my\n weekly   report  today")["goal"]["text"], "Write my weekly report today")


class WovenIntoMissionsTests(AcademyCase):
    def test_every_mission_says_why_it_matters_to_you_in_the_learners_own_words(self):
        self.state.set_use_goal(GOAL)
        for track in self.state.snapshot()["tracks"]:
            for mission in track["missions"]:
                self.assertIn("“Write my weekly status email from my project notes”", mission["use_text"], mission["id"])
                self.assertNotIn("{goal}", mission["use_text"])

    def test_the_quoted_goal_does_not_end_in_a_double_period(self):
        self.state.set_use_goal(GOAL)
        for track in self.state.snapshot()["tracks"]:
            for mission in track["missions"]:
                self.assertNotIn("..", mission["use_text"], mission["id"])
                self.assertNotIn("”.”", mission["use_text"])

    def test_without_a_goal_the_plain_line_is_used(self):
        for track in self.state.snapshot()["tracks"]:
            for mission in track["missions"]:
                self.assertTrue(mission["use_text"], mission["id"])
                self.assertNotIn("You said", mission["use_text"])

    def test_the_plain_line_never_shows_a_raw_placeholder(self):
        for mission in self.curriculum.MISSIONS.values():
            self.assertNotIn("{goal}", mission["use_plain"])
            self.assertEqual(mission["use"].count("{goal}"), 1)

    def test_practice_prompts_use_the_learners_goal_as_the_example(self):
        self.state.set_use_goal(GOAL)
        coach = [s for s in self.mission("operator.learning")["steps"] if s["kind"] == "lab"][0]
        self.assertIn("Use my own goal as the example whenever you need one", coach["prompt"])
        self.assertIn("“Write my weekly status email from my project notes”.", coach["prompt"])

    def test_without_a_goal_prompts_are_left_as_written(self):
        base = self.step("operator.learning", "lab")["prompt"]
        self.assertEqual([s for s in self.mission("operator.learning")["steps"] if s["kind"] == "lab"][0]["prompt"], base)

    def test_a_marker_prompt_still_starts_with_its_marker_after_the_goal_is_added(self):
        self.state.set_use_goal(GOAL)
        prompt = [s for s in self.mission("operator.desktop")["steps"] if s["kind"] == "lab"][0]["prompt"]
        self.assertTrue(prompt.startswith("[FA-DESKTOP]"), prompt[:40])

    def test_the_next_mission_card_carries_the_why(self):
        self.state.set_use_goal(GOAL)
        self.assertIn("Write my weekly status email", self.state.snapshot()["next_up"]["use_text"])

    def test_the_agent_sees_the_goal_and_the_missions_why(self):
        import json

        self.state.set_use_goal(GOAL)
        self.assertEqual(self.state.compact()["learner_goal"], GOAL)
        tools = sys.modules[f"{self.name}.tools"]
        payload = json.loads(tools.field_academy_mission({"mission_id": "operator.runtime"}))
        self.assertEqual(payload["learner_goal"], GOAL)
        self.assertIn("Write my weekly status email", payload["why_it_matters"])


class HonestProgressTests(AcademyCase):
    def test_every_mission_says_how_long_it_will_take(self):
        for track in self.state.snapshot()["tracks"]:
            for mission in track["missions"]:
                self.assertGreater(mission["minutes"], 0, mission["id"])
                self.assertEqual(set(mission["time"]), {"lesson", "example", "complete", "lab", "explain", "gate"}, mission["id"])

    def test_the_next_up_card_has_the_time(self):
        self.assertGreater(self.state.snapshot()["next_up"]["minutes"], 0)

    def test_passed_and_holding_are_counted_apart(self):
        self.pass_mission("operator.runtime", score=90)
        honest = self.state.snapshot()["honest"]
        self.assertEqual((honest["passed"], honest["holding"]), (1, 1))

    def test_no_streak_counter_exists_anywhere_in_the_backend(self):
        for name in ("state.py", "review.py", "learning.py", "pathways.py", "store.py"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"\bstreak|days_in_a_row|consecutive_days", text, re.I), name)

    def test_the_passport_has_no_streak_or_points_field(self):
        text = str(self.state.snapshot()).lower()
        for banned in ("streak", "points", "badge", "xp", "leaderboard"):
            self.assertNotIn(f"'{banned}'", text)

    def test_a_missed_review_costs_nothing_but_strength(self):
        self.pass_mission("operator.runtime")
        self.advance(days=90)
        mission = next(m for m in self.track("operator")["missions"] if m["id"] == "operator.runtime")
        self.assertEqual(mission["status"], "verified")
        self.assertEqual(self.state.snapshot()["honest"]["passed"], 1)


if __name__ == "__main__":
    unittest.main()
