"""Placement for Foundations: an experienced learner can test out of a mission (0.9 persona test, Kwame).

A test-out skips Recall. The claim, the guess, the practice profile with its planted problem, the job, the self-score
and the check all stay. Pass every check on the first run, the explanation included, and the entry goes into the record
marked "tested out", never "completed"; a miss turns the try into the usual mission, and the record still says it began
as a test-out. Built on mission 3's shipped content with a stand-in Hermes root; nothing runs Hermes.
"""

from __future__ import annotations

import itertools
import json
import pathlib
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
import test_foundations_memory_mission as tmm  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402
from support import START  # noqa: E402

MID = tmm.MID
FACT = tmm.FACT
LIMITS = "It shows one practice mission on my own laptop. Nobody else watched, and my Hermes graded my explanation."


class TestOut(FoundationsCase):
    salt_for = tmm.MemoryMission.salt_for
    save_and_use = tmm.MemoryMission.save_and_use
    to_first_check = tmm.MemoryMission.to_first_check

    def setUp(self):
        super().setUp()
        self.f = self.mod("foundations")
        self.f.CONTENT_DIR = None
        self.content = self.mod("foundations_content")
        self.content.clear_cache()
        self.mission = self.content.get(MID)
        self.fr = self.mod("field_record")
        self.mod("evidence").detect_version_detail = lambda: {"value": "0.23.0", "source": "git tag", "exact": True}
        counter = itertools.count()
        self.store.clock = lambda: START + timedelta(minutes=2) * next(counter)

    def lab_test_out(self):
        self.salt_for(["write_approval"])
        aid = self.f.start(MID, test_out=True)["attempt"]["id"]
        self.f.save_entry(aid, "claim", {"text": self.mission["claim"]["text"], "author": "course"})
        self.f.save_entry(aid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in self.mission["standard"]]})
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 90} for c in self.mission["standard"]},
                                              "where_wrong": "Nowhere, I hope: I do this every week."})
        self.f.open_lab(aid)  # no recall: a test-out skips it
        for which in self.content.profiles_needed(self.mission):
            planned = self.practice.plan(which)
            self.practice.confirm(planned["name"], self.create_like_hermes(planned))
        self.f.plant_lab(aid)
        return aid

    def clean_run(self, aid):
        """The job done right the first time: the fact saved (nothing held for approval), the seed notes kept, a new
        chat that uses it, and a level 3 explanation."""
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"] + [FACT], None)
        self.save_and_use()
        self.to_first_check(aid)
        self.f.submit_explanation(aid, "The save can be staged for approval, so I check the row, the file and a new chat. " * 2)
        self.f.grade_rubric(MID, f"explain@{aid}", 3, "Three causes, each with a check.")

    def steps(self, aid):
        return {s["id"]: s["status"] for s in self.f.attempt_view(aid)["steps"]}

    # ------------------------------------------------------------------ start --

    def test_a_test_out_skips_recall_and_still_freezes_the_claim_and_the_guess(self):
        aid = self.f.start(MID, test_out=True)["attempt"]["id"]
        view = self.f.attempt_view(aid)
        self.assertEqual(view["test_out"], {"on": True, "passed": None})
        self.assertEqual(self.steps(aid)["recall"], "skipped")
        with self.assertRaisesRegex(ValueError, "claim"):
            self.f.open_lab(aid)  # the claim, the standard and the guess are still needed
        self.f.save_entry(aid, "claim", {"text": self.mission["claim"]["text"], "author": "course"})
        self.f.save_entry(aid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in self.mission["standard"]]})
        with self.assertRaisesRegex(ValueError, "prediction"):
            self.f.open_lab(aid)
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 70} for c in self.mission["standard"]},
                                              "where_wrong": "The planted problem."})
        self.assertTrue(self.f.open_lab(aid)["attempt"]["frozen_at"])

    def test_the_usual_mission_still_needs_its_recall(self):
        aid = self.f.start(MID)["attempt"]["id"]
        self.assertEqual(self.f.attempt_view(aid)["test_out"], {"on": False, "passed": None})
        self.f.save_entry(aid, "claim", {"text": self.mission["claim"]["text"], "author": "course"})
        self.f.save_entry(aid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in self.mission["standard"]]})
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 70} for c in self.mission["standard"]},
                                              "where_wrong": "The planted problem."})
        with self.assertRaisesRegex(ValueError, "recall"):
            self.f.open_lab(aid)

    def test_an_open_try_can_become_a_test_out_before_practice_but_not_after(self):
        aid = self.f.start(MID)["attempt"]["id"]
        self.assertEqual(self.f.start(MID, test_out=True)["attempt"]["id"], aid)
        self.assertTrue(self.f.attempt_view(aid)["test_out"]["on"])
        self.f.start(MID, test_out=True)  # marking twice is harmless
        marks = [e for e in self.f.attempt_view(aid)["entries"] if e["kind"] == "test_out"]
        self.assertEqual(len(marks), 1)

        other = self.content.get("f.loop")
        bid = self.f.start("f.loop")["attempt"]["id"]
        self.f.save_entry(bid, "recall", {"answers": ["One." for _ in other["recall"]["prompts"]]})
        self.f.save_entry(bid, "claim", {"text": other["claim"]["text"], "author": "course"})
        self.f.save_entry(bid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in other["standard"]]})
        self.f.save_entry(bid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 70} for c in other["standard"]},
                                              "where_wrong": "Counting the rows."})
        self.f.open_lab(bid)
        with self.assertRaisesRegex(ValueError, "already in practice"):
            self.f.start("f.loop", test_out=True)

    def test_the_review_has_no_test_out_and_no_page_can_write_the_mark(self):
        with self.assertRaisesRegex(ValueError, "review"):
            self.f.start("f.review", test_out=True)
        aid = self.f.start(MID)["attempt"]["id"]
        with self.assertRaisesRegex(ValueError, "Unknown entry"):
            self.f.save_entry(aid, "test_out", {"skips": ["recall"]})

    # ---------------------------------------------------------------- results --

    def test_passing_every_check_first_time_goes_in_the_record_as_tested_out(self):
        aid = self.lab_test_out()
        self.assertEqual(self.steps(aid)["record"], "locked")
        with self.assertRaisesRegex(ValueError, "test out"):
            self.f.add_to_record(aid, confirmed=True)
        self.clean_run(aid)
        view = self.f.attempt_view(aid)
        self.assertEqual(view["test_out"], {"on": True, "passed": True})
        self.assertEqual(self.steps(aid)["record"], "open")
        self.assertEqual(self.steps(aid)["fix_transfer"], "locked", "the fix and the transfer stay optional, and undone")
        preview = self.f.record_preview(aid)
        self.assertTrue(preview["ready"])
        self.assertEqual((preview["entry"]["mode"], preview["entry"]["tested_out"]), ("test_out", True))
        self.assertEqual(preview["entry"]["skipped"], ["recall", "fix", "transfer"])
        self.f.add_to_record(aid, confirmed=True)

        body = self.fr.build("Kwame Mensah", LIMITS)
        entry = body["entries"][0]
        self.assertEqual((entry["mode"], entry["tested_out"]), ("test_out", True))
        claimed = body["can_claim"]["passed"][0]
        self.assertTrue(claimed["tested_out"])
        self.assertFalse(claimed["after_fix"])
        md = self.fr.record_markdown(dict(body, number="FA-TEST-TEST-TEST"))
        self.assertIn("Tested out", md)
        self.assertIn("a test-out", md)
        self.assertIn("skipped the recall, the fix and the transfer", md)
        self.assertNotIn("Completed", md)

        listed = next(m for m in self.f.snapshot()["missions"] if m["id"] == MID)
        self.assertEqual((listed["attempts"][-1]["test_out"], listed["attempts"][-1]["tested_out"]), (True, True))

    def test_a_miss_turns_the_test_out_into_the_usual_mission_and_the_record_says_so(self):
        aid = self.lab_test_out()
        # The planted approval holds the save: check 1 misses on the first run.
        self.save_and_use(staged=True)
        self.to_first_check(aid)
        self.assertEqual(self.f.attempt_view(aid)["test_out"], {"on": True, "passed": False})
        self.assertEqual(self.steps(aid)["record"], "locked")
        with self.assertRaisesRegex(ValueError, "transfer"):
            self.f.add_to_record(aid, confirmed=True)
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"] + [FACT], ["Kwame prefers short answers."])
        self.save_and_use()
        self.f.save_entry(aid, "gap_note", {"text": "I didn't look for a held save before I scored check 1."})
        self.f.run_checks(aid, "after_fix")
        self.f.save_entry(aid, "lab_note", {"fact": "Kwame prefers short answers", "key_term": "short", "for": "transfer",
                                            "one_off": "The printer quote came in at noon today", "one_off_saved": False,
                                            "one_off_why": "It matters for one afternoon, so it doesn't earn a line."})
        self.f.run_checks(aid, "transfer")
        self.assertEqual(self.steps(aid)["record"], "open")
        self.f.add_to_record(aid, confirmed=True)
        body = self.fr.build("Kwame Mensah", LIMITS)
        entry = body["entries"][0]
        self.assertEqual((entry["mode"], entry["tested_out"]), ("test_out", False))
        self.assertFalse(body["can_claim"]["passed"] and body["can_claim"]["passed"][0].get("tested_out"))
        md = self.fr.record_markdown(dict(body, number="FA-TEST-TEST-TEST"))
        self.assertIn("began as a test-out", md)
        self.assertNotIn("- **Tested out", md)


if __name__ == "__main__":
    unittest.main()
