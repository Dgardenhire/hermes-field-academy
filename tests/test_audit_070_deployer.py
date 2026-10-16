"""Deployer fixes from the 0.7.0 audit: a reviewer can be trusted locally, and waiting is not a mistake."""

import json
import unittest
from datetime import timedelta

from deployer_support import DeployerCase


class TrustLocalReviewerTests(DeployerCase):
    KEY = "ab" * 32

    def test_a_reviewer_added_here_is_trusted_and_labelled_local(self):
        out = self.deployer.trust_local_reviewer("Dana Reviewer", self.KEY)
        self.assertEqual(out["list"], "local")
        with self.deployer._conn() as conn:
            trusted = self.deployer.trusted_reviewers(conn)
            view = self.deployer._review_view(conn)
        self.assertEqual(trusted[self.KEY], {"name": "Dana Reviewer", "list": "local"})
        self.assertEqual(view["reviewers"]["local"], ["Dana Reviewer"])
        self.assertEqual(view["reviewers"]["published"], [])

    def test_adding_the_same_key_twice_keeps_one_entry(self):
        self.deployer.trust_local_reviewer("Dana", self.KEY)
        out = self.deployer.trust_local_reviewer("Dana R.", self.KEY.upper())
        self.assertEqual(out["count"], 1)

    def test_a_bad_key_or_missing_name_is_refused(self):
        with self.assertRaises(ValueError):
            self.deployer.trust_local_reviewer("Dana", "not-a-key")
        with self.assertRaises(ValueError):
            self.deployer.trust_local_reviewer("  ", self.KEY)


class WaitingIsNotAMissTests(DeployerCase):
    def test_checking_an_untouched_lab_does_not_climb_the_hint_ladder(self):
        lab_id = self.labs.LAB_IDS[0]
        self.deployer.open_lab(lab_id)
        for _ in range(3):
            out = self.deployer.check_lab(lab_id, "")
            self.assertFalse(out["outcome"]["passed"])
            self.assertEqual(out["outcome"]["missing"][0]["id"], "unchanged")
            self.assertEqual(out["outcome"]["feedback"]["level"], 1)
        with self.deployer._conn() as conn:
            row = self.deployer._lab_row(conn, lab_id)
        self.assertEqual(row["attempts"], 0)

    def test_the_waiting_misses_are_named(self):
        self.assertEqual(self.deployer.WAITING_MISSES, {"few_runs", "few_days", "short_span"})


if __name__ == "__main__":
    unittest.main()
