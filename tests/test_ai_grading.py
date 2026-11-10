"""Score my answer: inline grading of Explain it, on mission 3's shipped content, with a stand-in model.

The level comes from the model's checked reply and goes through foundations.grade_rubric with source hermes_grader
and via inline. The quote is kept only when it is word for word in the answer. One answer gets one level. A failed
call records nothing and leaves the chat route working. The page can't pass a level in.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import pathlib
import sys
import threading
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_foundations_memory_mission as tmm  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402
from test_ai_fakes import FakeLlm  # noqa: E402

MID = tmm.MID
ANSWER = ("First I would open the memory row in the chat and read every line, because a save can be staged for approval "
          "and not written yet. Then I would open MEMORY.md in the practice profile and look for the line. Last, I would "
          "start a fresh chat and ask about it without saying it again.")
QUOTE = "a save can be staged for approval and not written yet"


def reply(level=3, quote=QUOTE, **extra):
    out = {"level": level, "right": "You check the chat row before the file.", "missing": "Say how a full memory could cut it.",
           "add_next": "Add the memory meter as a fourth check.", "quote": quote}
    out.update(extra)
    return out


class GradingCase(FoundationsCase):
    salt_for = tmm.MemoryMission.salt_for
    lab = tmm.MemoryMission.lab

    def setUp(self):
        super().setUp()
        self.f = self.mod("foundations")
        self.f.CONTENT_DIR = None
        self.content = self.mod("foundations_content")
        self.content.clear_cache()
        self.mission = self.content.get(MID)
        self.grading = self.mod("grading")
        self.runtime = self.mod("runtime")
        self.runtime.clear()
        self.aid = self.lab(["write_approval"])
        self.step = f"explain@{self.aid}"

    def tearDown(self):
        self.runtime.clear()
        super().tearDown()

    def grade(self, llm, answer=ANSWER):
        return self.grading.grade_inline(MID, self.step, answer, llm=llm)

    def rows(self):
        with self.store.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM f_checks WHERE attempt_id = ? AND check_id = 'explain'", (self.aid,))]


class InlineGrade(GradingCase):
    def test_a_level_right_missing_add_next_and_an_exact_quote(self):
        llm = FakeLlm([reply(3)])
        out = self.grade(llm)
        self.assertEqual(out["state"], "ok")
        self.assertEqual((out["level"], out["level_words"], out["passed"], out["pass_level"]), (3, "Level 3 of 4", True, 3))
        self.assertEqual(out["quote"], QUOTE)
        self.assertIn(out["quote"], out["answer"])
        for key in ("right", "missing", "add_next", "model", "ms", "tokens"):
            self.assertIn(key, out)
        self.assertEqual(llm.calls[0]["task"], "field_academy_grader")

    def test_it_is_recorded_through_grade_rubric_as_hermes_grader_via_inline(self):
        self.grade(FakeLlm([reply(2)]))
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row["source"], row["level"], row["passed"], row["phase"]), ("hermes_grader", 2, 0, "first"))
        facts = json.loads(row["facts_json"])
        self.assertEqual(facts["via"], "inline")
        self.assertEqual(facts["score"], 50)
        self.assertEqual(facts["quote"], QUOTE)
        self.assertEqual(facts["model"], "fake-model-1")
        self.assertRegex(facts["answer_hash"], r"^[0-9a-f]{64}$")
        self.assertTrue(self.f.verify_chain()["ok"])

    def test_a_quote_that_is_not_word_for_word_in_the_answer_is_dropped(self):
        for bad in ("a save can be STAGED for approval", "the save is waiting for approval in pending", "approval", ""):
            with self.subTest(bad=bad):
                self.setUp()
                out = self.grade(FakeLlm([reply(3, quote=bad)]))
                self.assertEqual(out["quote"], "")
                self.assertEqual(json.loads(self.rows()[0]["facts_json"])["quote"], "")
                self.tearDown()

    def test_smart_quotes_around_an_exact_quote_are_trimmed(self):
        out = self.grade(FakeLlm([reply(3, quote="“" + QUOTE + "”")]))
        self.assertEqual(out["quote"], QUOTE)

    def test_one_answer_gets_one_level(self):
        self.grade(FakeLlm([reply(2)]))
        llm = FakeLlm([reply(4)])
        with self.assertRaisesRegex(ValueError, "already has its level"):
            self.grade(llm)
        self.assertEqual(llm.calls, [], "no second model read of the same answer")
        with self.assertRaisesRegex(ValueError, "already has its level"):
            self.f.grade_rubric(MID, self.step, 4, "chat tries again")
        self.assertEqual(len(self.rows()), 1)

    def test_an_edited_answer_is_a_new_answer_with_its_own_single_level(self):
        self.grade(FakeLlm([reply(2)]))
        better = ANSWER + " I would also look at the memory meter, because a full memory can cut a note."
        out = self.grade(FakeLlm([reply(4, quote="a full memory can cut a note")]), answer=better)
        self.assertEqual(out["level"], 4)
        self.assertEqual([r["phase"] for r in self.rows()], ["first", "after_fix"])
        with self.assertRaisesRegex(ValueError, "already has its level"):
            self.grade(FakeLlm([reply(4)]), answer=better)

    def test_a_double_press_asks_the_model_once(self):
        gate = threading.Event()
        results = {}

        def slow(kw):
            gate.wait(2)
            return reply(3)

        llm = FakeLlm([slow, reply(4)])

        def first():
            results["first"] = self.grade(llm)

        worker = threading.Thread(target=first)
        worker.start()
        for _ in range(100):
            if llm.calls:
                break
            threading.Event().wait(0.01)
        with self.assertRaisesRegex(ValueError, "already reading"):
            self.grade(llm)
        gate.set()
        worker.join(5)
        self.assertEqual(results["first"]["level"], 3)
        self.assertEqual(len(llm.calls), 1)

    def test_the_model_never_sees_the_tool_instruction_and_the_answer_is_fenced(self):
        llm = FakeLlm([reply(3)])
        self.grade(llm)
        sent = llm.sent_text()
        self.assertNotIn("field_academy_grade_explanation", sent)
        self.assertIn(self.learning.ANSWER_START, sent)
        self.assertIn(self.mission["explain"]["question"], sent)
        self.assertIn(self.mission["explain"]["rubric"][3][:40], sent)

    def test_the_grading_text_is_rubric_prompt_minus_its_last_paragraph(self):
        with self.store.connect() as conn:
            attempt = self.f._attempt(conn, self.aid)
        full = self.f.rubric_prompt(attempt, self.mission, ANSWER)
        cut = self.grading.grading_text(attempt, self.mission, ANSWER)
        self.assertTrue(full.startswith(cut))
        self.assertIn("Level 3 or higher passes", cut)

    def test_a_secret_in_the_answer_never_reaches_the_model(self):
        llm = FakeLlm([reply(3)])
        self.grade(llm, answer=ANSWER + " My key was token=abc123 and the address https://ops:hunter2@db.example.com.")
        sent = llm.sent_text()
        self.assertNotIn("abc123", sent)
        self.assertNotIn("hunter2", sent)

    def test_a_reply_asking_for_level_five_gets_one_repair_and_then_fails_cleanly(self):
        out = self.grade(FakeLlm([reply(5), reply(9)]))
        self.assertEqual(out["state"], "bad_json")
        self.assertEqual(out["fallback"], "chat")
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.f.resend_explanation(self.aid)["step_id"], self.step, "the chat route still works")

    def test_failures_record_nothing_and_say_what_to_do(self):
        for exc, kind in ((TimeoutError("timed out"), "timeout"), (RuntimeError("503 unavailable"), "provider_error")):
            with self.subTest(kind=kind):
                out = self.grade(FakeLlm([exc]))
                self.assertEqual(out["state"], kind)
                self.assertTrue(out["message"] and out["next_step"])
                self.assertEqual(self.rows(), [])
        out = self.grade(FakeLlm([reply(3)]))
        self.assertEqual(out["state"], "ok", "the same waiting answer is graded once the model answers")
        self.assertEqual(len(self.rows()), 1)

    def test_no_model_in_this_process(self):
        out = self.grading.grade_inline(MID, self.step, ANSWER)
        self.assertEqual(out["state"], "no_model")

    def test_ai_help_off_returns_the_off_state_and_calls_nothing(self):
        self.state.set_ai_settings(ai_help=False)
        llm = FakeLlm([reply(3)])
        out = self.grade(llm)
        self.assertEqual((out["state"], out["off_reason"], out["fallback"]), ("off", "switch", "chat"))
        self.assertEqual(llm.calls, [])

    def test_the_wrong_mission_a_short_answer_and_a_bad_step_are_refused(self):
        with self.assertRaisesRegex(ValueError, "different mission"):
            self.grading.grade_inline("f.loop", self.step, ANSWER, llm=FakeLlm([reply()]))
        with self.assertRaisesRegex(ValueError, "too short"):
            self.grade(FakeLlm([reply()]), answer="too short")
        with self.assertRaisesRegex(ValueError, "step id"):
            self.grading.grade_inline(MID, "explain@x", ANSWER, llm=FakeLlm([reply()]))

    def test_grade_rubric_refuses_an_unknown_source(self):
        self.f.submit_explanation(self.aid, ANSWER)
        with self.assertRaisesRegex(ValueError, "chat or from Score my answer"):
            self.f.grade_rubric(MID, self.step, 3, "x", via="page")


class GradeRoute(GradingCase):
    """The route through the page's API, with the FastAPI stand-in the other API tests use."""

    def setUp(self):
        super().setUp()
        import test_api_and_content as api_tests

        self._saved = sys.modules.get("fastapi")
        sys.modules["fastapi"] = api_tests.stub_fastapi()
        spec = importlib.util.spec_from_file_location(f"{self.name}_api", pathlib.Path(self.pkg.__file__).parent / "dashboard" / "plugin_api.py")
        self.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.api)

    def tearDown(self):
        for key in [k for k in sys.modules if k.startswith("field_academy_dashboard_package")]:
            del sys.modules[key]
        if self._saved is None:
            sys.modules.pop("fastapi", None)
        else:
            sys.modules["fastapi"] = self._saved
        super().tearDown()

    def call(self, method, path, *args):
        return asyncio.run(self.api.router.routes[(method, path)](*args))

    def test_the_route_takes_only_the_answer(self):
        self.runtime.set_llm(FakeLlm([reply(4, quote=QUOTE)]))
        out = self.call("POST", "/ai/grade/{mission_id}/{step_id}", MID, self.step,
                        {"answer": ANSWER, "level": 1, "quote": "injected", "passed": True})
        self.assertEqual((out["state"], out["level"], out["quote"]), ("ok", 4, QUOTE))

    def test_a_refusal_is_a_400_with_plain_words(self):
        self.runtime.set_llm(FakeLlm([reply(3)]))
        with self.assertRaises(Exception) as caught:
            self.call("POST", "/ai/grade/{mission_id}/{step_id}", MID, self.step, {"answer": "short"})
        self.assertEqual(caught.exception.status_code, 400)

    def test_settings_route(self):
        self.assertEqual(self.call("GET", "/settings/ai"), {"ai_help": True, "practice_offer": True})
        self.assertEqual(self.call("POST", "/settings/ai", {"ai_help": False}), {"ai_help": False, "practice_offer": True})
        with self.assertRaises(Exception) as caught:
            self.call("POST", "/settings/ai", {"ai_help": "off"})
        self.assertEqual(caught.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
