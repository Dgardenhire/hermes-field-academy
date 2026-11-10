"""The Foundations routes, through the dashboard API with a stand-in for FastAPI."""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from foundations_support import FoundationsCase  # noqa: E402
from test_api_and_content import ApiCase  # noqa: E402


class FoundationsApiCase(FoundationsCase, ApiCase):
    def frozen_attempt(self, plants='["write_approval"]'):
        with self.practice._conn() as conn:
            cur = conn.execute(
                "INSERT INTO f_attempts(mission_id, attempt_no, level, seed, plants_json, started_at, frozen_at, status) VALUES ('f.test', 1, 'beginner', 'abc', ?, ?, ?, 'lab')",
                (plants, "2026-10-03T09:00:00+00:00", "2026-10-03T09:05:00+00:00"),
            )
            return cur.lastrowid


class PracticeRoutes(FoundationsApiCase):
    def test_the_routes_exist_and_none_records_a_score(self):
        for key in (("GET", "/foundations/practice"), ("POST", "/foundations/practice/plan"), ("POST", "/foundations/practice/confirm"),
                    ("POST", "/foundations/practice/plant"), ("POST", "/foundations/practice/remove"), ("POST", "/foundations/practice/removed")):
            self.assertIn(key, self.api.router.routes)
        # 0.9 premium: one route grades, Score my answer. It takes only the answer; the level comes from the backend's
        # own model call (tests/test_ai_grading.py, GradeRoute.test_the_route_takes_only_the_answer).
        self.assertEqual([key for key in self.api.router.routes if "grade" in key[1] or "score" in key[1]],
                         [("POST", "/ai/grade/{mission_id}/{step_id}")])

    def test_plan_create_record_plant_and_remove(self):
        planned = self.call("POST", "/foundations/practice/plan", {})
        result = self.create_like_hermes(planned)
        recorded = self.call("POST", "/foundations/practice/confirm", {"name": planned["name"], "result": result})
        self.assertEqual(recorded["status"], "ready")
        attempt = self.frozen_attempt()
        planted = self.call("POST", "/foundations/practice/plant", {"attempt_id": attempt})
        self.assertEqual(planted["status"], "ready", "the page sees ready, never planted")
        self.assertNotIn("planted", str(self.call("GET", "/foundations/practice")))
        self.assertIs(self.hermes_read.config(self.home())["values"]["memory.write_approval"], True)
        self.fails("POST", "/foundations/practice/remove", {"name": planned["name"]})
        out = self.call("POST", "/foundations/practice/remove", {"name": planned["name"], "confirm": True})
        self.assertEqual(out["delete"], "academy-practice")
        self.fails("POST", "/foundations/practice/removed", {"name": planned["name"]})
        self.gone(planned["name"])
        self.assertEqual(self.call("POST", "/foundations/practice/removed", {"name": planned["name"]})["status"], "removed")

    def test_nothing_is_planted_before_the_attempt_is_frozen(self):
        planned = self.call("POST", "/foundations/practice/plan", {})
        self.call("POST", "/foundations/practice/confirm", {"name": planned["name"], "result": self.create_like_hermes(planned)})
        with self.practice._conn() as conn:
            cur = conn.execute("INSERT INTO f_attempts(mission_id, attempt_no, level, seed, plants_json, started_at) VALUES ('f.test', 1, 'beginner', 'abc', '[\"write_approval\"]', '2026-10-03T09:00:00+00:00')")
            attempt = cur.lastrowid
        detail = self.fails("POST", "/foundations/practice/plant", {"attempt_id": attempt})
        self.assertIn("prediction", detail)

    def test_bad_input_is_a_plain_refusal(self):
        self.fails("POST", "/foundations/practice/confirm", {"name": "../etc"})
        self.fails("POST", "/foundations/practice/plant", {"attempt_id": "x"})
        self.fails("POST", "/foundations/practice/plan", {"which": "z"})


class LoopRoutes(FoundationsApiCase):
    def setUp(self):
        super().setUp()
        api_foundations = sys.modules["field_academy_dashboard_package.foundations"]
        api_foundations.CONTENT_DIR = pathlib.Path(__file__).resolve().parent / "data" / "foundations"

    def test_a_test_out_starts_through_the_route_and_only_a_true_flag_counts(self):
        view = self.call("POST", "/foundations/attempt/start", {"mission_id": "f.fixture", "test_out": "yes"})
        self.assertFalse(view["test_out"]["on"], "only test_out: true starts a test-out")
        view = self.call("POST", "/foundations/attempt/start", {"mission_id": "f.fixture", "test_out": True})
        self.assertEqual(view["test_out"], {"on": True, "passed": None})
        self.assertEqual({s["id"]: s["status"] for s in view["steps"]}["recall"], "skipped")

    def test_start_save_freeze_and_explain_through_the_routes(self):
        from test_foundations_engine import ANSWER, CLAIM, IDS, STANDARD

        snap = self.call("GET", "/foundations")
        self.assertEqual(snap["missions"][0]["id"], "f.fixture")
        mission = self.call("GET", "/foundations/mission/{mission_id}", "f.fixture")
        self.assertNotIn("plants", mission["lab"])
        self.assertEqual(mission["hidden_checks"], 1)
        aid = self.call("POST", "/foundations/attempt/start", {"mission_id": "f.fixture", "level": "beginner"})["attempt"]["id"]
        self.fails("POST", "/foundations/attempt/{attempt_id}/lab/open", str(aid))
        for kind, body in (("recall", {"answers": ["one", "two"]}), ("claim", {"text": CLAIM, "author": "course"}),
                           ("standard", {"checks": STANDARD}),
                           ("prediction", {"checks": {i: {"expect_pass": True, "confidence": 60} for i in IDS}, "where_wrong": "the new chat"})):
            self.call("POST", "/foundations/attempt/{attempt_id}/entry", str(aid), {"kind": kind, "body": body})
        view = self.call("POST", "/foundations/attempt/{attempt_id}/lab/open", str(aid))
        self.assertTrue(view["attempt"]["frozen_at"])
        self.fails("POST", "/foundations/attempt/{attempt_id}/check", str(aid), {"phase": "first"})
        out = self.call("POST", "/foundations/attempt/{attempt_id}/explain", str(aid), {"answer": ANSWER, "level": 4, "score": 100})
        self.assertIn("explain@", out["prompt"])
        self.assertEqual(self.rows("SELECT COUNT(*) AS n FROM f_checks WHERE source = 'hermes_grader'"), [{"n": 0}], "the page can't set a level")
        self.assertIn("prompt", self.call("POST", "/foundations/attempt/{attempt_id}/explain/resend", str(aid)))
        self.fails("GET", "/foundations/attempt/{attempt_id}", "999")
        self.fails("POST", "/foundations/attempt/{attempt_id}/entry", str(aid), {"kind": "score", "body": {}})


class RecordRoutes(FoundationsApiCase):
    def test_the_record_routes_refuse_plainly_until_there_is_an_entry(self):
        for key in (("GET", "/foundations/record"), ("POST", "/foundations/record/preview"), ("POST", "/foundations/record/issue"),
                    ("POST", "/foundations/record/save"), ("POST", "/foundations/record/correction")):
            self.assertIn(key, self.api.router.routes)
        preview = self.call("POST", "/foundations/record/preview", {"holder": "Ada", "limits": "x", "withhold": ["not a number"]})
        self.assertFalse(preview["ready"])
        self.assertTrue(preview["problems"])
        self.assertEqual(self.call("GET", "/foundations/record")["body"]["record_format"], 3)
        self.assertIn("confirmation", self.fails("POST", "/foundations/record/issue", {"holder": "Ada", "limits": "It shows practice work only, on my laptop."}))
        self.assertIn("entry", self.fails("POST", "/foundations/record/issue", {"holder": "Ada", "limits": "It shows practice work only, on my laptop.", "confirm": True}))
        self.fails("POST", "/foundations/record/save", {"number": "FA-0000-0000-0000"})
        self.fails("POST", "/foundations/record/correction", {"entry_hash": "0" * 64, "text": "A correction to nothing.", "confirm": True})


if __name__ == "__main__":
    unittest.main()
