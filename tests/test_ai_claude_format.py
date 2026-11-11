"""Nov 10: Claude's strict output mode can refuse a structured-output request with a 400 before any answer (The
Clearing hit it live). Field Academy then asks for the JSON in plain words, reads it from the reply, and still holds
it to the same schema. Other failures are unchanged."""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_ai_fakes import FakeLlm  # noqa: E402
from test_ai_helper import SCHEMA, AiCase  # noqa: E402

REFUSED = RuntimeError("Incomplete upstream response (status 400, upstream said: output_config.format.schema: "
                       "For object type, additionalProperties must be explicitly set to false)")


def claude(kw):
    if kw.get("json_schema") is not None:
        return REFUSED
    return '{"text": "hi"}'


class ClaudeFormat(AiCase):
    def setUp(self):
        super().setUp()
        self.ai._FORMAT["plain"] = False

    def tearDown(self):
        self.ai._FORMAT["plain"] = False
        super().tearDown()

    def test_refused_schema_then_plain_answer_is_read_and_checked(self):
        llm = FakeLlm([claude] * 3)
        out = self.run_call(llm)
        self.assertEqual(out["parsed"], {"text": "hi"})
        last = llm.calls[-1]
        self.assertNotIn("json_schema", last)
        self.assertIn("Reply with one complete JSON object", last["instructions"])
        self.assertIn('"required":["text"]', last["instructions"])
        self.assertTrue(self.ai._FORMAT["plain"])

    def test_plain_sticks_one_call_each(self):
        llm = FakeLlm([claude] * 5)
        self.run_call(llm)
        before = len(llm.calls)
        self.run_call(llm)
        self.assertEqual(len(llm.calls) - before, 1)

    def test_a_plain_reply_that_misses_the_schema_still_gets_the_repair_try(self):
        llm = FakeLlm([REFUSED, '{"wrong": 1}', '{"text": "fixed"}'])
        out = self.run_call(llm)
        self.assertEqual(out["parsed"], {"text": "fixed"})

    def test_other_failures_are_unchanged(self):
        llm = FakeLlm([RuntimeError("Error code: 529 - overloaded")])
        with self.assertRaises(self.ai.AiFailure):
            self.run_call(llm)
        self.assertFalse(self.ai._FORMAT["plain"])


if __name__ == "__main__":
    unittest.main()
