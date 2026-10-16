"""The learning rules in learning.py: spacing, strength, which missions to review, the hint ladder and placement marking.

Pure functions, so no database and no clock: every date here is made up.
"""

import importlib.util
import pathlib
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fa_learning_pure", ROOT / "learning.py")
learning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learning)

NOW = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)


def row(mission_id, due_days, stage=0, strength=80, interval=2, lapses=0, last_item=""):
    return {
        "mission_id": mission_id,
        "due_at": (NOW + timedelta(days=due_days)).isoformat(),
        "stage": stage,
        "strength": strength,
        "interval_days": interval,
        "lapses": lapses,
        "last_item": last_item,
    }


class SpacingTests(unittest.TestCase):
    def test_the_gaps_grow_from_two_days_to_two_months_then_ninety(self):
        self.assertEqual([learning.interval_for(n) for n in range(6)], [2, 7, 21, 60, 90, 90])

    def test_the_first_review_is_two_days_after_the_pass(self):
        self.assertEqual(learning.first_due(NOW), NOW + timedelta(days=2))

    def test_a_strong_answer_moves_up_a_rung(self):
        step = learning.after_review(0, 90, NOW)
        self.assertEqual((step["stage"], step["interval_days"], step["outcome"]), (1, 7, "advanced"))

    def test_the_threshold_for_moving_up_is_85(self):
        self.assertEqual(learning.after_review(1, 85, NOW)["outcome"], "advanced")
        self.assertEqual(learning.after_review(1, 84, NOW)["outcome"], "held")

    def test_an_answer_that_passes_but_is_not_strong_repeats_the_same_gap(self):
        step = learning.after_review(2, 74, NOW)
        self.assertEqual((step["stage"], step["interval_days"], step["outcome"]), (2, 21, "held"))

    def test_a_miss_drops_two_rungs_and_returns_tomorrow(self):
        step = learning.after_review(3, 55, NOW)
        self.assertEqual((step["stage"], step["interval_days"], step["outcome"]), (1, 1, "lapsed"))

    def test_a_miss_never_drops_below_the_first_rung(self):
        self.assertEqual(learning.after_review(0, 10, NOW)["stage"], 0)
        self.assertEqual(learning.after_review(1, 10, NOW)["stage"], 0)

    def test_weak_items_return_sooner_than_strong_ones(self):
        weak = learning.after_review(2, 40, NOW)["interval_days"]
        strong = learning.after_review(2, 95, NOW)["interval_days"]
        self.assertLess(weak, strong)

    def test_early_practice_never_moves_the_rung(self):
        step = learning.after_review(2, 99, NOW, early=True)
        self.assertEqual((step["stage"], step["outcome"], step["due_shift"]), (2, "practiced", False))
        self.assertFalse(learning.after_review(2, 10, NOW, early=True)["due_shift"])

    def test_an_answer_at_the_ceiling_stays_on_ninety_days(self):
        self.assertEqual(learning.after_review(4, 95, NOW)["interval_days"], 90)


class StrengthTests(unittest.TestCase):
    def test_the_first_answer_sets_the_strength(self):
        self.assertEqual(learning.new_strength(None, 76), 76)

    def test_a_later_answer_leans_sixty_percent_on_the_latest(self):
        self.assertEqual(learning.new_strength(80, 40), round(0.4 * 80 + 0.6 * 40))

    def test_strength_stays_between_zero_and_a_hundred(self):
        self.assertEqual(learning.new_strength(None, 400), 100)
        self.assertEqual(learning.new_strength(50, -50), round(0.4 * 50))

    def test_strength_holds_until_the_review_is_due(self):
        due = (NOW + timedelta(days=3)).isoformat()
        self.assertEqual(learning.current_strength(86, due, 7, NOW), 86)

    def test_strength_fades_once_a_review_is_overdue(self):
        due = (NOW - timedelta(days=6)).isoformat()
        value = learning.current_strength(80, due, 2, NOW)
        self.assertLess(value, 80)
        self.assertEqual(value, round(80 * 0.5 ** (6 / 6)))

    def test_a_longer_gap_fades_more_slowly(self):
        due = (NOW - timedelta(days=6)).isoformat()
        self.assertGreater(learning.current_strength(80, due, 21, NOW), learning.current_strength(80, due, 2, NOW))

    def test_a_mission_never_reviewed_has_no_strength(self):
        self.assertIsNone(learning.current_strength(None, None, 2, NOW))

    def test_strength_is_always_said_in_a_word(self):
        words = [learning.strength_word(v) for v in (None, 92, 85, 78, 70, 55, 39)]
        self.assertEqual(words, ["Not reviewed yet", "Strong", "Strong", "Holding", "Holding", "Fading", "Weak"])


class SessionTests(unittest.TestCase):
    def test_only_due_missions_are_picked(self):
        rows = [row("a", -1), row("b", 3), row("c", 0)]
        picked = learning.pick_session(rows, NOW)
        self.assertEqual({r["mission_id"] for r in picked}, {"a", "c"})

    def test_a_session_is_at_most_three(self):
        rows = [row(f"m{i}", -1) for i in range(7)]
        self.assertEqual(len(learning.pick_session(rows, NOW)), 3)

    def test_a_lapsed_mission_goes_before_one_that_is_merely_late(self):
        rows = [row("late", -10, lapses=0), row("lapsed", -1, lapses=2)]
        self.assertEqual(learning.pick_session(rows, NOW)[0]["mission_id"], "lapsed")

    def test_among_the_rest_the_longest_overdue_goes_first(self):
        rows = [row("a", -1), row("b", -8), row("c", -3)]
        order = [r["mission_id"] for r in learning.pick_session(rows, NOW)]
        self.assertEqual(order, ["b", "c", "a"])

    def test_overdue_is_measured_against_the_missions_own_gap(self):
        rows = [row("short", -2, interval=2), row("long", -2, interval=60)]
        self.assertEqual(learning.pick_session(rows, NOW)[0]["mission_id"], "short")

    def test_practice_fills_with_the_weakest_missions_when_few_are_due(self):
        rows = [row("due", -1, strength=90), row("weak", 5, strength=30), row("firm", 5, strength=95)]
        picked = learning.pick_session(rows, NOW, practice=True)
        self.assertEqual([r["mission_id"] for r in picked], ["due", "weak", "firm"])
        self.assertEqual([r["early"] for r in picked], [False, True, True])

    def test_nothing_due_means_an_empty_session(self):
        self.assertEqual(learning.pick_session([row("a", 4), row("b", 9)], NOW), [])

    def test_the_question_rotates_and_never_repeats_back_to_back(self):
        variants = ["r1", "r2", "r3"]
        self.assertEqual(learning.next_variant(variants, None), "r1")
        self.assertEqual(learning.next_variant(variants, "r1"), "r2")
        self.assertEqual(learning.next_variant(variants, "r3"), "r1")
        self.assertEqual(learning.next_variant([], "r1"), "")


class LadderTests(unittest.TestCase):
    MISSING = [
        {"id": "section:Owner", "what": '"Owner" has 2 words.'},
        {"id": "section:Price", "what": "There is no Price section."},
    ]
    COACH = {
        "section:Owner": {"hint": "Name one person.", "example": "Example: Marcus Bell reviews the list."},
        "section:Price": {"hint": "Write a price.", "example": "Example: $900."},
    }

    def test_the_first_miss_says_what_was_missing_and_gives_one_hint(self):
        ladder = learning.ladder(1, self.MISSING, self.COACH)
        self.assertEqual(ladder["level"], 1)
        self.assertEqual(len(ladder["missing"]), 2)
        self.assertEqual(ladder["hint"], "Name one person.")
        self.assertEqual(ladder["example"], "")

    def test_the_second_miss_adds_a_worked_example(self):
        ladder = learning.ladder(2, self.MISSING, self.COACH)
        self.assertEqual(ladder["level"], 2)
        self.assertEqual(ladder["hint"], "Name one person.")
        self.assertEqual(ladder["example"], "Example: Marcus Bell reviews the list.")

    def test_later_misses_keep_the_example(self):
        self.assertEqual(learning.ladder(7, self.MISSING, self.COACH)["level"], 2)

    def test_the_help_is_about_the_first_thing_on_the_list(self):
        self.assertEqual(learning.ladder(2, self.MISSING, self.COACH)["focus"], "section:Owner")

    def test_a_miss_is_never_just_not_yet(self):
        for count in (1, 2, 5):
            ladder = learning.ladder(count, self.MISSING, self.COACH)
            self.assertTrue(ladder["headline"])
            self.assertNotEqual(ladder["headline"].lower().strip(" ."), "not yet")
            self.assertTrue(ladder["retry"])

    def test_with_nothing_specific_it_still_tells_you_what_to_do(self):
        ladder = learning.ladder(1, [], {})
        self.assertIn("check again", ladder["headline"].lower())
        self.assertEqual(ladder["missing"], [])

    def test_an_unknown_miss_has_no_hint_but_keeps_its_description(self):
        ladder = learning.ladder(1, [{"id": "odd", "what": "Something specific."}], {})
        self.assertEqual(ladder["missing"][0]["what"], "Something specific.")
        self.assertEqual(ladder["hint"], "")

    def test_every_general_hint_has_words_and_the_documents_ones_have_examples(self):
        for key, spec in learning.GENERIC_COACH.items():
            self.assertTrue(spec["hint"], key)
            if key != "feedback":
                self.assertTrue(spec["example"], key)


class PlacementTests(unittest.TestCase):
    LEVELS = ("beginner", "intermediate", "advanced")
    QUESTIONS = [
        {"id": "p1", "level": "beginner", "answer": 1, "why": "a"},
        {"id": "p2", "level": "beginner", "answer": 0, "why": "b"},
        {"id": "p3", "level": "intermediate", "answer": 2, "why": "c"},
        {"id": "p4", "level": "intermediate", "answer": 1, "why": "d"},
        {"id": "p5", "level": "advanced", "answer": 0, "why": "e"},
        {"id": "p6", "level": "advanced", "answer": 3, "why": "f"},
    ]

    def test_a_level_is_known_only_when_every_question_on_it_is_right(self):
        result = learning.score_placement(self.QUESTIONS, {"p1": 1, "p2": 0, "p3": 2, "p4": 0, "p5": 0, "p6": 3}, self.LEVELS)
        known = {level: item["known"] for level, item in result["levels"].items()}
        self.assertEqual(known, {"beginner": True, "intermediate": False, "advanced": True})

    def test_one_lucky_guess_is_not_enough(self):
        result = learning.score_placement(self.QUESTIONS, {"p1": 1, "p2": 3, "p3": 0, "p4": 0, "p5": 1, "p6": 0}, self.LEVELS)
        self.assertFalse(any(item["known"] for item in result["levels"].values()))

    def test_every_question_comes_back_with_its_why(self):
        result = learning.score_placement(self.QUESTIONS, {}, self.LEVELS)
        self.assertEqual([q["why"] for q in result["questions"]], list("abcdef"))
        self.assertTrue(all(q["right"] is False for q in result["questions"]))

    def test_the_count_per_level_is_reported(self):
        result = learning.score_placement(self.QUESTIONS, {"p1": 1, "p2": 3}, self.LEVELS)
        self.assertEqual(result["levels"]["beginner"], {"right": 1, "total": 2, "known": False})


if __name__ == "__main__":
    unittest.main()
