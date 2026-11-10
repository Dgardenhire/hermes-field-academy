"""How well the learner judges their own work: hit rate, Brier score, signed gap and its trend. Pure math, no storage."""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_scrub import load  # noqa: E402

IDS = ["s1", "s2", "s3", "s4"]


class OneMission(unittest.TestCase):
    def setUp(self):
        self.c = load("calibration")

    def test_a_perfectly_judged_mission(self):
        prediction = {i: {"expect_pass": True, "confidence": 100} for i in IDS}
        self_scores = {i: True for i in IDS}
        results = {i: True for i in IDS}
        out = self.c.mission(IDS, prediction, self_scores, results)
        self.assertEqual(out["hit_rate"], 1.0)
        self.assertEqual(out["brier"], 0.0)
        self.assertEqual(out["signed_gap"], 0)

    def test_the_sample_record_four_predicted_three_passed(self):
        # "Prediction: 4 of 4 ... Result: 3 of 4 on the first try" (SAMPLE-MISSION-memory).
        prediction = {i: {"expect_pass": True, "confidence": 80} for i in IDS}
        self_scores = {i: True for i in IDS}
        results = {"s1": False, "s2": True, "s3": True, "s4": True}
        out = self.c.mission(IDS, prediction, self_scores, results)
        self.assertEqual((out["predicted_passes"], out["self_passes"], out["actual_passes"]), (4, 4, 3))
        self.assertEqual(out["signed_gap"], 1, "self minus check: the learner scored themselves one higher")
        self.assertEqual(out["hit_rate"], 0.75)
        self.assertAlmostEqual(out["brier"], (3 * 0.2 ** 2 + 0.8 ** 2) / 4)
        miss = next(c for c in out["per_check"] if c["id"] == "s1")
        self.assertEqual((miss["hit"], miss["self_gap"]), (False, 1))

    def test_a_confident_wrong_fail_prediction_scores_badly(self):
        out = self.c.mission(["s1"], {"s1": {"expect_pass": False, "confidence": 90}}, {"s1": False}, {"s1": True})
        self.assertAlmostEqual(out["brier"], 0.81)
        self.assertEqual(out["signed_gap"], -1, "underrating yourself is a negative gap")

    def test_checks_without_a_result_yet_are_left_out_not_counted_as_fails(self):
        out = self.c.mission(IDS, {i: {"expect_pass": True, "confidence": 70} for i in IDS}, {i: True for i in IDS}, {"s1": True})
        self.assertEqual(out["checked"], 1)
        self.assertEqual(out["hit_rate"], 1.0)

    def test_confidence_is_clamped_to_50_100_and_odd_input_is_safe(self):
        out = self.c.mission(["s1"], {"s1": {"expect_pass": True, "confidence": 300}}, {}, {"s1": True})
        self.assertEqual(out["per_check"][0]["confidence"], 100)
        out = self.c.mission(["s1"], {"s1": "junk"}, None, {"s1": False})
        self.assertIsNone(out["per_check"][0]["expect_pass"])
        self.assertIsNone(out["brier"])


class Across(unittest.TestCase):
    def setUp(self):
        self.c = load("calibration")

    def test_the_trend_shows_the_gap_closing(self):
        missions = [{"signed_gap": 3, "brier": 0.4, "hit_rate": 0.25, "checked": 4},
                    {"signed_gap": 2, "brier": 0.3, "hit_rate": 0.5, "checked": 4},
                    {"signed_gap": 0, "brier": 0.1, "hit_rate": 1.0, "checked": 4}]
        out = self.c.across(missions)
        self.assertLess(out["trend"], 0)
        self.assertAlmostEqual(out["brier"], (0.4 + 0.3 + 0.1) / 3)
        self.assertEqual(out["gaps"], [3, 2, 0])

    def test_one_mission_has_no_trend(self):
        self.assertIsNone(self.c.across([{"signed_gap": 1, "brier": 0.2, "hit_rate": 0.5, "checked": 2}])["trend"])
        self.assertIsNone(self.c.across([])["brier"])


if __name__ == "__main__":
    unittest.main()
