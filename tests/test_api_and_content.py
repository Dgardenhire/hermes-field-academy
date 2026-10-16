"""The desktop API routes (with a stand-in for FastAPI), the content validator, and the new screens' source."""

import asyncio
import importlib.util
import pathlib
import re
import subprocess
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase, ROOT  # noqa: E402


def stub_fastapi():
    """A minimal FastAPI: routes register as (method, path) -> function, HTTPException carries a status."""
    module = types.ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            super().__init__(detail)
            self.status_code, self.detail = status_code, detail

    class APIRouter:
        def __init__(self):
            self.routes = {}

        def _add(self, method):
            def decorator(path):
                def wrap(fn):
                    self.routes[(method, path)] = fn
                    return fn
                return wrap
            return decorator

        def __getattr__(self, name):
            if name in ("get", "post"):
                return self._add(name.upper())
            raise AttributeError(name)

    module.APIRouter, module.HTTPException = APIRouter, HTTPException
    return module


class ApiCase(AcademyCase):
    def setUp(self):
        super().setUp()
        self._saved = sys.modules.get("fastapi")
        sys.modules["fastapi"] = stub_fastapi()
        spec = importlib.util.spec_from_file_location(f"{self.name}_api", ROOT / "dashboard" / "plugin_api.py")
        self.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.api)
        # The dashboard loads its own copy of the package. It shares this test's database through the
        # data-folder variable, and gets this test's clock.
        self.api_store = sys.modules["field_academy_dashboard_package.store"]
        self.api_store.clock = lambda: self.now

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

    def fails(self, method, path, *args, status=400, **kwargs):
        with self.assertRaises(self.api.HTTPException) as caught:
            self.call(method, path, *args, **kwargs)
        self.assertEqual(caught.exception.status_code, status)
        return caught.exception.detail


class RouteTests(ApiCase):
    def test_every_new_route_exists(self):
        wanted = [
            ("POST", "/use"), ("POST", "/complete/{mission_id}/{step_id}"), ("GET", "/reviews"), ("POST", "/review/start"),
            ("GET", "/review/{session_id}"), ("POST", "/review/{session_id}/submit"),
            ("GET", "/placement/{track_id}"), ("POST", "/placement/{track_id}"), ("POST", "/placement/{track_id}/apply"),
            ("GET", "/changes"), ("POST", "/mission/{mission_id}/reverify"), ("POST", "/mission/{mission_id}/acknowledge"),
        ]
        for key in wanted:
            self.assertIn(key, self.api.router.routes, key)

    def test_the_goal_route_saves_and_refuses(self):
        self.assertTrue(self.call("POST", "/use", {"text": "Write my weekly report from my notes."})["goal"]["asked"])
        self.assertIn("few words", self.fails("POST", "/use", {"text": "hi"}))

    def test_a_review_goes_from_start_to_scored(self):
        self.pass_mission("operator.runtime")
        self.advance(days=3)
        session = self.call("POST", "/review/start", {})
        self.assertEqual(len(session["items"]), 1)
        text = "Scheduled work needs the gateway, which runs apart from the window."
        sent = self.call("POST", "/review/{session_id}/submit", session["id"], {"answers": {"operator.runtime": text}})
        self.assertIn("field_academy_grade_review", sent["prompt"])
        grades = [{"mission_id": "operator.runtime", "score": 90, "missed": [], "feedback": "Clear."}]
        graded = self.state.grade_review(session["id"], grades)  # scores arrive through the agent tool, never over HTTP
        self.assertEqual(graded["results"][0]["outcome"], "advanced")
        self.assertEqual(self.call("GET", "/review/{session_id}", session["id"])["status"], "graded")
        self.assertEqual(self.call("GET", "/reviews")["due_count"], 0)

    def test_nothing_due_is_a_plain_message_not_a_crash(self):
        self.assertIn("two days after you pass it", self.fails("POST", "/review/start", {}))

    def test_an_unknown_review_session_is_a_404(self):
        self.fails("GET", "/review/{session_id}", "nope", status=404)

    def test_placement_routes_serve_questions_without_answers_and_apply(self):
        spec = self.call("GET", "/placement/{track_id}", "operator")
        self.assertEqual(len(spec["questions"]), 6)
        answers = {q["id"]: q["answer"] for q in self.curriculum.PLACEMENTS["operator"]["questions"]}
        outcome = self.call("POST", "/placement/{track_id}", "operator", {"answers": answers})
        self.assertEqual(len(outcome["known_levels"]), 3)
        applied = self.call("POST", "/placement/{track_id}/apply", "operator")
        self.assertGreater(applied["steps_skipped"], 0)
        self.fails("GET", "/placement/{track_id}", "wizard", status=404)
        self.fails("POST", "/placement/{track_id}", "operator", {"answers": {}})

    def test_the_gap_route_checks_and_refuses_other_steps(self):
        reply = self.call("POST", "/complete/{mission_id}/{step_id}", "integrator.discovery", "complete", {"answers": {}})
        self.assertFalse(reply["ok"])
        self.fails("POST", "/complete/{mission_id}/{step_id}", "integrator.discovery", "concept", {"answers": {}})

    def test_the_gate_route_passes_the_live_result_to_a_document_check(self):
        path = self.write("setup.md", self.document("integrator.deploy"))
        live = {"passed": True, "title": "ok", "detail": "ok", "facts": []}
        reply = self.call("POST", "/gate/{mission_id}/{step_id}", "integrator.deploy", "gate", {"path": path, "live": live})
        self.assertTrue(reply["outcome"]["passed"], reply["outcome"]["missing"])

    def test_a_document_gate_without_its_live_part_says_so_and_gives_a_hint(self):
        path = self.write("c.md", self.document("integrator.connect"))
        reply = self.call("POST", "/gate/{mission_id}/{step_id}", "integrator.connect", "gate", {"path": path})
        self.assertEqual([m["id"] for m in reply["outcome"]["missing"]], ["live_failed"])
        self.assertEqual(reply["outcome"]["feedback"]["level"], 1)

    def test_the_gate_route_returns_the_hint_ladder_for_a_live_miss(self):
        outcome = {"passed": False, "title": "x", "detail": "x", "facts": [], "missing": [{"id": "no_marker", "what": "No chat has it."}]}
        reply = self.call("POST", "/gate/{mission_id}/{step_id}", "operator.desktop", "gate", {"outcome": outcome})
        self.assertEqual(reply["outcome"]["feedback"]["focus"], "no_marker")
        self.assertTrue(reply["outcome"]["feedback"]["hint"])
        self.assertEqual(reply["mission"]["steps"][-1]["feedback"]["focus"], "no_marker")

    def test_a_gate_needs_a_file_or_an_outcome(self):
        self.assertIn("file path or a check outcome", self.fails("POST", "/gate/{mission_id}/{step_id}", "operator.runtime", "gate", {}))

    def test_the_explain_grade_route_takes_the_missed_points(self):
        self.call("POST", "/explain/{mission_id}/{step_id}", "operator.runtime", "explain", {"answer": "Scheduled jobs run through the gateway. " * 5})
        reply = self.state.grade_explanation("operator.runtime", "explain", 50, "x", [2])
        self.assertEqual(reply["ladder"]["focus"], "point:2")

    def test_changes_and_re_verify_routes(self):
        self.pass_mission("operator.runtime")
        with self.state._connection() as conn:
            conn.execute("UPDATE mission_versions SET passed_version = 1")
        self.assertEqual(len(self.call("GET", "/changes")), 1)
        self.assertTrue(self.call("POST", "/mission/{mission_id}/reverify", "operator.runtime")["reverify"])
        self.assertIn("Run the check again", self.fails("POST", "/mission/{mission_id}/acknowledge", "operator.runtime"))
        self.fails("POST", "/mission/{mission_id}/reverify", "operator.desktop")

    def test_the_passport_route_carries_everything_the_page_reads(self):
        data = self.call("GET", "/passport")
        for key in ("goal", "reviews", "changes", "new_missions", "honest"):
            self.assertIn(key, data)


class ContentValidatorTests(unittest.TestCase):
    def run_script(self, name, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / name), *args], capture_output=True, text=True, timeout=120)

    def test_the_content_validator_finds_nothing_wrong(self):
        result = self.run_script("check_content.py")
        self.assertEqual(result.returncode, 0, result.stdout[-3000:])

    def test_the_voice_check_finds_nothing_in_any_learner_text(self):
        result = self.run_script("check_voice.py")
        self.assertEqual(result.returncode, 0, result.stdout[-3000:])

    def test_the_validator_catches_a_bad_text(self):
        spec = importlib.util.spec_from_file_location("fa_check_content", ROOT / "scripts" / "check_content.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        problems = []
        module.check_text("x", "This is not a plan, but a wish.", problems)
        self.assertTrue(problems)
        problems = []
        module.check_text("x", "A calm sentence of several words.", problems, limit=2)
        self.assertEqual(len(problems), 1)

    def test_the_validator_catches_a_worked_example_that_fails_its_own_check(self):
        spec = importlib.util.spec_from_file_location("fa_check_content2", ROOT / "scripts" / "check_content.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        curriculum, documents, _ = module.load()
        gate = {"sections": [{"heading": "Price", "min_words": 4, "needs": ["money"], "what": "x", "hint": "x", "example": "x", "fix": "x"},
                             {"heading": "Owner", "min_words": 4, "needs": ["name"], "what": "x", "hint": "x", "example": "x", "fix": "x"},
                             {"heading": "Scope", "min_words": 4, "needs": [], "what": "x", "hint": "x", "example": "x"}],
                "verify": "artifact", "title": "A", "body": "B", "proof": "C"}
        spec = {"worked": {"document": "## Price\nsoon enough maybe\n\n## Owner\nthe team\n\n## Scope\nwords words words words"}, "complete": {"parts": [{"text": "x"}]}}
        problems = []
        module.check_artifact_gate("x.y", spec, gate, documents, problems)
        self.assertTrue(any("fails its own check" in p for p in problems), problems)

    def test_each_path_validates_on_its_own(self):
        for track_id in ("operator", "integrator", "architect", "ambassador"):
            self.assertEqual(self.run_script("check_content.py", track_id).returncode, 0, track_id)


class NewScreenSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")
        cls.api = (ROOT / "dashboard" / "plugin_api.py").read_text(encoding="utf-8")

    def test_the_new_screens_exist(self):
        for name in ("function ReviewView", "function PlacementView", "function ReviewQueue", "function ChangesPanel",
                     "function GoalCard", "function ExampleStep", "function CompleteStep", "function Feedback"):
            self.assertIn(name, self.src)

    def test_every_route_the_page_calls_exists_on_the_backend(self):
        calls = set(re.findall(r"ctxRest\(`?'?(/[a-z]+)", self.src))
        self.assertGreaterEqual(len(calls), 8)
        for call in calls:
            self.assertIn(call, self.api, call)

    def test_the_page_opens_the_new_views(self):
        for view in ("'review'", "'placement'"):
            self.assertIn(f"view.name === {view}", self.src)

    def test_the_map_shows_the_goal_the_queue_and_the_changes(self):
        for part in ("jsx(GoalCard", "jsx(ReviewQueue", "jsx(ChangesPanel"):
            self.assertIn(part, self.src)

    def test_the_mission_shows_why_the_time_and_the_fading_support(self):
        # The support bar is gone; the time now shows on each step and as a total for the mission.
        for text in ("Why this matters to you", "minutesWords(step.minutes)", "in all`"):
            self.assertIn(text, self.src)

    def test_a_miss_says_what_was_missing_and_offers_a_retry(self):
        for text in ("You can retry as many times as you like", "What was missing", "One hint", "A worked example"):
            self.assertIn(text, self.src)

    def test_the_review_page_waits_for_hermes_to_score(self):
        self.assertIn("Waiting for Hermes to score your answers", self.src)
        self.assertIn("setInterval", self.src)

    def test_a_re_verify_button_and_an_acknowledge_button_exist(self):
        self.assertIn("'Re-verify'", self.src)
        self.assertIn("I've read the changes", self.src)

    def test_the_certificate_table_shows_the_check_version(self):
        self.assertIn("reading skipped by placement", self.src)

    def test_the_built_file_carries_the_new_screens(self):
        bundle = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        for name in ("ReviewView", "PlacementView", "GoalCard", "ChangesPanel"):
            self.assertIn(name, bundle)


if __name__ == "__main__":
    unittest.main()
