"""The AI routes' JSON, one fixture per route and state, for the Desk lane (contract 2 in the AI lane brief).

Every fixture in tests/data/ai_contract/ is made by the real code on mission 3's shipped content, through the page
routes, with a stand-in model. This test rebuilds each one and checks its shape (keys and value types, recursively)
still matches the committed file, so a shape can't change without the fixtures changing with it.

Rewrite the fixtures after a deliberate change:  FA_WRITE_AI_CONTRACT=1 /usr/bin/python3 -m unittest test_ai_contract
(then tell the product owner: the Desk lane builds against these).
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_ai_guide as tg  # noqa: E402
import test_ai_replay as tr  # noqa: E402
from test_ai_fakes import AuxiliaryClientUnavailable, FakeLlm, RoutedLlm  # noqa: E402
from test_ai_grading import ANSWER, QUOTE, reply  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "data" / "ai_contract"
WRITE = os.environ.get("FA_WRITE_AI_CONTRACT") == "1"
FAILURES = {
    "no_model": lambda: AuxiliaryClientUnavailable("No LLM provider configured for task=field_academy_grader"),
    "timeout": lambda: TimeoutError("Auxiliary call timed out after 60s"),
    "provider_error": lambda: RuntimeError("provider returned error envelope: 429 rate limit"),
}


def shape(value):
    if isinstance(value, dict):
        return {k: shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [shape(value[0])] if value else []
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if value is None:
        return "null"
    return "text"


class Contract(tg.GuideCase):
    def setUp(self):
        super().setUp()
        import test_api_and_content as api_tests

        self._saved = sys.modules.get("fastapi")
        sys.modules["fastapi"] = api_tests.stub_fastapi()
        spec = importlib.util.spec_from_file_location(f"{self.name}_api", pathlib.Path(self.pkg.__file__).parent / "dashboard" / "plugin_api.py")
        self.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.api)
        self.api_store = sys.modules["field_academy_dashboard_package.store"]
        self.api_store.clock = self.store.clock
        self.api_guide = sys.modules["field_academy_dashboard_package.guide"]
        self.made = {}

    def tearDown(self):
        for key in [k for k in sys.modules if k.startswith("field_academy_dashboard_package")]:
            del sys.modules[key]
        if self._saved is None:
            sys.modules.pop("fastapi", None)
        else:
            sys.modules["fastapi"] = self._saved
        super().tearDown()

    def call(self, method, path, *args, **kwargs):
        return asyncio.run(self.api.router.routes[(method, path)](*args, **kwargs))

    def keep(self, name, payload, route):
        doc = {"route": route, "response": payload}
        self.made[name] = doc
        path = OUT / f"{name}.json"
        if WRITE:
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        else:
            self.assertTrue(path.exists(), f"missing fixture {name}.json (run with FA_WRITE_AI_CONTRACT=1)")
            committed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(committed["route"], route, name)
            self.assertEqual(shape(committed["response"]), shape(payload), f"{name}.json no longer matches the route's shape")

    # ------------------------------------------------------------- grading --

    def test_grade_fixtures(self):
        route = "POST /ai/grade/{mission_id}/{step_id}"
        aid = self.lab(["write_approval"])
        step = f"explain@{aid}"
        for kind, make in FAILURES.items():
            self.runtime.set_llm(FakeLlm([make()]))
            self.keep(f"grade-{kind}", self.call("POST", "/ai/grade/{mission_id}/{step_id}", tg.MID, step, {"answer": ANSWER}), route)
        self.runtime.set_llm(FakeLlm(["not json", "still not json"]))
        self.keep("grade-bad_json", self.call("POST", "/ai/grade/{mission_id}/{step_id}", tg.MID, step, {"answer": ANSWER}), route)
        self.state.set_ai_settings(ai_help=False)
        self.keep("grade-off-switch", self.call("POST", "/ai/grade/{mission_id}/{step_id}", tg.MID, step, {"answer": ANSWER}), route)
        self.state.set_ai_settings(ai_help=True)
        self.runtime.set_llm(FakeLlm([reply(3, quote=QUOTE)]))
        self.keep("grade-ok", self.call("POST", "/ai/grade/{mission_id}/{step_id}", tg.MID, step, {"answer": ANSWER}), route)

    def test_settings_fixtures(self):
        self.keep("settings-get", self.call("GET", "/settings/ai"), "GET /settings/ai")
        self.keep("settings-post", self.call("POST", "/settings/ai", {"ai_help": False}), "POST /settings/ai")

    # --------------------------------------------------------------- guide --

    def guide_get(self, aid, step="check", active="own"):
        return self.call("GET", "/guide/{attempt_id}", aid, step, active)

    def test_guide_fixtures(self):
        route = "GET /guide/{attempt_id}?step=&active="
        aid = self.missed()
        self.keep("guide-check-before-check", self.call("GET", "/guide/{attempt_id}", aid, "evidence", "own"), route)
        llm = RoutedLlm({"field_academy_nudge": [self.good_nudge(aid)], "field_academy_explain": [self.explain_reply()] * 6,
                         "field_academy_ask": [tr.LOOP1_ASK, tr.LOOP1_ASK]}, delay=0.2)
        self.runtime.set_llm(llm)
        self.keep("guide-check-fetching", self.guide_get(aid), route)
        self.api_guide.wait_prefetch(aid, 10)
        self.keep("guide-check-ready", self.guide_get(aid), route)
        self.keep("help-rung1-nudge", self.call("POST", "/guide/{attempt_id}/help", aid, {"rung": 1, "step": "check"}),
                  "POST /guide/{attempt_id}/help")
        self.keep("ask-hunt-held-back", self.call("POST", "/guide/{attempt_id}/ask", aid, {"question": "Why isn't my fact saved?", "step": "check"}),
                  "POST /guide/{attempt_id}/ask")
        self.keep("replay-before-compare", self.call("GET", "/replay/{attempt_id}", aid, "check"), "GET /replay/{attempt_id}?step=")
        self.keep("guide-check-after-nudge", self.guide_get(aid), route)
        self.keep("help-rung2-where", self.call("POST", "/guide/{attempt_id}/help", aid, {"rung": 2, "step": "check"}),
                  "POST /guide/{attempt_id}/help")
        self.keep("help-rung3-reveal", self.call("POST", "/guide/{attempt_id}/help", aid, {"rung": 3, "step": "check"}),
                  "POST /guide/{attempt_id}/help")
        replay = self.call("GET", "/replay/{attempt_id}", aid, "compare")
        self.keep("replay-ready", replay, "GET /replay/{attempt_id}?step=")
        joined = replay["bracket"]
        self.runtime.set_llm(RoutedLlm({"field_academy_pins": [{"pins": [
            {"event_id": joined["from"], "why": "This is where your score and Hermes split. Open that memory row in your chat."},
            {"event_id": joined["to"], "why": "The save sits here, held, so MEMORY.md never changed."}]}],
            "field_academy_why": [{"why": "The save is held, so approving it by its id writes it into MEMORY.md."}],
            "field_academy_explain": [self.explain_reply()] * 6}))
        self.keep("pins-make", self.call("POST", "/guide/{attempt_id}/pins", aid, {"make": True, "step": "compare"}),
                  "POST /guide/{attempt_id}/pins")
        self.keep("pins-update", self.call("POST", "/guide/{attempt_id}/pins", aid, {"keep": [joined["from"]], "dismiss": [], "add": []}),
                  "POST /guide/{attempt_id}/pins")
        self.keep("guide-compare-pins", self.guide_get(aid, "compare"), route)
        # Why did this miss? lives on Compare (Nov 9): no Explain call is made before it.
        self.keep("help-explain", self.call("POST", "/guide/{attempt_id}/help", aid, {"action": "explain", "step": "compare"}),
                  "POST /guide/{attempt_id}/help")
        self.api_guide.wait_prefetch(aid, 10, what="why")
        self.keep("help-do-it-with-me", self.call("POST", "/guide/{attempt_id}/help", aid, {"action": "do_it_with_me", "step": "fix"}),
                  "POST /guide/{attempt_id}/help")
        self.keep("guide-fix-do-it-with-me", self.guide_get(aid, "fix"), route)
        self.api_guide.wait_prefetch(aid, 10)
        self.runtime.set_llm(FakeLlm([
            {"sentences": [{"text": "MEMORY.md holds 2,200 characters by default.", "source_ids": ["asof-1"]}], "not_in_sources": False},
            {"sentences": [], "not_in_sources": True},
            TimeoutError("timed out"),
        ]))
        self.keep("ask-answered", self.call("POST", "/guide/{attempt_id}/ask", aid, {"question": "How big is MEMORY.md?", "step": "compare"}),
                  "POST /guide/{attempt_id}/ask")
        self.keep("ask-not-covered", self.call("POST", "/guide/{attempt_id}/ask", aid, {"question": "How do I connect Slack?", "step": "compare"}),
                  "POST /guide/{attempt_id}/ask")
        self.keep("ask-timeout", self.call("POST", "/guide/{attempt_id}/ask", aid, {"question": "Why was it held?", "step": "compare"}),
                  "POST /guide/{attempt_id}/ask")
        self.state.set_ai_settings(ai_help=False)
        self.keep("guide-off-switch", self.guide_get(aid), route)

    def test_pins_too_long_fixture(self):
        aid = self.missed()
        joined = self.call("GET", "/replay/{attempt_id}", aid, "compare")["bracket"]
        too_long = {"pins": [{"event_id": joined["from"], "why": ("very " * 25).strip()}]}
        self.runtime.set_llm(RoutedLlm({"field_academy_pins": [too_long, too_long]}))
        self.keep("pins-too-long", self.call("POST", "/guide/{attempt_id}/pins", aid, {"make": True, "step": "compare"}),
                  "POST /guide/{attempt_id}/pins")

    def test_why_fetching_fixture(self):
        aid = self.missed()
        self.runtime.set_llm(RoutedLlm({"field_academy_nudge": [self.good_nudge(aid)], "field_academy_explain": [self.explain_reply()] * 6,
                                        "field_academy_why": [{"why": "The save is held, so approving it by its id writes it."}]}, delay=0.3))
        self.guide_get(aid)
        self.api_guide.wait_prefetch(aid, 10)
        self.guide_get(aid, "compare")
        self.keep("guide-fix-why-fetching", self.guide_get(aid, "fix"), "GET /guide/{attempt_id}?step=&active=")
        self.api_guide.wait_prefetch(aid, 10, what="why")

    def test_replay_state_fixtures(self):
        route = "GET /replay/{attempt_id}?step="
        aid = self.lab(["write_approval"])
        self.to_first_check(aid)
        self.keep("replay-empty", self.call("GET", "/replay/{attempt_id}", aid, "compare"), route)
        self.tearDown()
        self.setUp()
        aid = self.missed()
        import sqlite3

        con = sqlite3.connect(pathlib.Path(self.home()) / "state.db")
        con.execute("ALTER TABLE messages RENAME COLUMN content TO body")
        con.commit()
        con.close()
        self.keep("replay-schema-changed", self.call("GET", "/replay/{attempt_id}", aid, "compare"), route)
        self.keep("replay-sample", self.call("GET", "/replay/sample"), "GET /replay/sample")

    def test_first_flight_fixtures(self):
        start = self.call("POST", "/first-flight/start", {})
        self.keep("first-flight-start", start, "POST /first-flight/start")
        self.keep("first-flight-info", self.call("GET", "/first-flight"), "GET /first-flight")
        aid = start["attempt"]["id"]
        self.keep("guide-first-flight-locked", self.guide_get(aid, "predict"), "GET /guide/{attempt_id}?step=&active=")

    def test_guide_failure_fixtures(self):
        route = "GET /guide/{attempt_id}?step=&active="
        for kind, make in FAILURES.items():
            with self.subTest(kind=kind):
                self.setUp()
                aid = self.missed()
                self.runtime.set_llm(RoutedLlm({}, default=make()))
                self.guide_get(aid)
                self.api_guide.wait_prefetch(aid, 10)
                self.keep(f"guide-check-{kind}", self.guide_get(aid), route)
                self.tearDown()
        self.setUp()
        aid = self.missed()
        leak = {"question": "It was staged. Is it pending?", "event_id": self.chat_events(aid)[0]["event_id"]}
        self.runtime.set_llm(RoutedLlm({"field_academy_nudge": [leak, leak], "field_academy_explain": [self.explain_reply()] * 6}))
        self.guide_get(aid)
        self.api_guide.wait_prefetch(aid, 10)
        self.call("POST", "/guide/{attempt_id}/help", aid, {"rung": 1})
        self.keep("guide-check-bad_json-course-words", self.guide_get(aid), route)
        self.keep("guide-check-practice-active", self.call("GET", "/guide/{attempt_id}", aid, "check", "practice"), route)

    def test_guide_test_out_fixture(self):
        self.salt_for(["write_approval"])
        aid = self.f.start(tg.MID, test_out=True)["attempt"]["id"]
        self.keep("guide-off-test-out", self.guide_get(aid), "GET /guide/{attempt_id}?step=&active=")


if __name__ == "__main__":
    unittest.main()
