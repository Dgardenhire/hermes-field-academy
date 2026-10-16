"""Feedback on a miss: what was missing, one hint, then a worked example, and a retry every time.

Covers document checks, live checks and the question Hermes scores.
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402

DISCOVERY = "integrator.discovery"
STUB = "# Scope\n\n## Client\nA company.\n\n## Workflow\nTheir work.\n\n## Owner\nThe office.\n"


class DocumentFeedbackTests(AcademyCase):
    def miss(self, text=STUB, mission_id=DISCOVERY):
        path = self.write("scope.md", text)
        outcome = self.state.verify_artifact(mission_id, "gate", path)
        return self.state.record_gate(mission_id, "gate", outcome, artifact=path)

    def test_a_stub_is_told_exactly_which_sections_are_short_or_absent(self):
        outcome = self.miss()
        whats = [m["what"] for m in outcome["feedback"]["missing"]]
        self.assertTrue(any('"Client" has 2 words' in w for w in whats), whats)
        self.assertTrue(any('no "Price" section' in w for w in whats), whats)

    def test_the_first_miss_gives_one_hint_and_no_example(self):
        feedback = self.miss()["feedback"]
        self.assertEqual(feedback["level"], 1)
        self.assertEqual(feedback["focus"], "section:Client")
        self.assertIn("Name the business", feedback["hint"])
        self.assertEqual(feedback["example"], "")

    def test_the_second_miss_gives_a_worked_example_for_the_same_item(self):
        self.miss()
        feedback = self.miss()["feedback"]
        self.assertEqual(feedback["level"], 2)
        self.assertEqual(feedback["focus"], "section:Client")
        self.assertIn("Lakeside Dental", feedback["example"])

    def test_a_third_miss_keeps_the_example(self):
        for _ in range(2):
            self.miss()
        self.assertTrue(self.miss()["feedback"]["example"])

    def test_the_learner_can_retry_after_every_miss(self):
        for _ in range(4):
            self.assertTrue(self.miss()["feedback"]["retry"])
        path = self.write("good.md", self.document(DISCOVERY))
        outcome = self.state.verify_artifact(DISCOVERY, "gate", path)
        self.assertTrue(outcome["passed"], outcome["missing"])

    def test_a_miss_is_never_the_words_not_yet(self):
        feedback = self.miss()["feedback"]
        self.assertNotEqual(feedback["headline"].strip(" .").lower(), "not yet")
        self.assertGreater(len(feedback["headline"]), 20)

    def test_the_step_shows_the_last_feedback_after_a_restart(self):
        self.miss()
        self.miss()
        step = self.passport_step(DISCOVERY, "gate")
        self.assertEqual(step["misses"], 2)
        self.assertEqual(step["feedback"]["level"], 2)
        self.assertEqual(step["status"], "needs_attention")

    def test_a_pass_clears_the_count_and_the_feedback(self):
        self.miss()
        path = self.write("good.md", self.document(DISCOVERY))
        outcome = self.state.verify_artifact(DISCOVERY, "gate", path)
        self.state.record_gate(DISCOVERY, "gate", outcome, artifact=path)
        step = self.passport_step(DISCOVERY, "gate")
        self.assertEqual((step["misses"], step["feedback"], step["status"]), (0, None, "done"))

    def test_a_missing_file_gets_a_hint_too(self):
        path = str(pathlib.Path(self.tmp) / "nope.md")
        outcome = self.state.record_gate(DISCOVERY, "gate", self.state.verify_artifact(DISCOVERY, "gate", path))
        self.assertEqual(outcome["feedback"]["focus"], "file")
        self.assertIn("Markdown", outcome["feedback"]["hint"])

    def test_a_mission_without_its_own_hint_falls_back_to_the_general_one(self):
        gate_id = "integrator.handoff"
        path = self.write("guide.md", "# Guide\n\n## Topology\nOne.\n")
        outcome = self.state.verify_artifact(gate_id, "gate", path)
        feedback = self.state.record_gate(gate_id, "gate", outcome, artifact=path)["feedback"]
        self.assertTrue(feedback["hint"])

    def test_a_passed_step_stays_passed_when_a_later_check_misses(self):
        self.pass_mission(DISCOVERY)
        self.miss()
        step = self.passport_step(DISCOVERY, "gate")
        self.assertEqual(step["status"], "done")
        track = next(t for t in self.state.snapshot()["tracks"] if t["id"] == "integrator")
        self.assertEqual(track["missions"][0]["status"], "verified")

    def test_misses_are_counted_per_step(self):
        self.miss()
        other = self.step("integrator.handoff", "gate")
        path = self.write("guide.md", "# Guide\n")
        outcome = self.state.verify_artifact("integrator.handoff", other["id"], path)
        feedback = self.state.record_gate("integrator.handoff", other["id"], outcome)["feedback"]
        self.assertEqual(feedback["level"], 1)

    def test_the_same_file_cannot_pass_two_missions(self):
        import hashlib

        text = self.document(DISCOVERY)
        path = self.write("scope.md", text)
        digest = hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()  # the file's bytes: CRLF on Windows
        with self.state._connection() as conn:
            conn.execute(
                "INSERT INTO evidence(mission_id, step_id, kind, summary, sha256, created_at) VALUES (?, 'gate', 'artifact', 'earlier', ?, ?)",
                ("ambassador.qualify", digest, "2026-10-01T00:00:00+00:00"),
            )
        outcome = self.state.verify_artifact(DISCOVERY, "gate", path)
        self.assertEqual([m["id"] for m in outcome["missing"]], ["reused"])
        self.assertIn("Spot a real opportunity", outcome["missing"][0]["what"])

    def test_the_same_file_can_pass_the_same_mission_again(self):
        self.pass_mission(DISCOVERY)
        path = self.write("again.md", self.document(DISCOVERY))
        self.assertTrue(self.state.verify_artifact(DISCOVERY, "gate", path)["passed"])

    def test_a_document_copied_from_the_example_is_told_to_use_its_own_case(self):
        example = self.step(DISCOVERY, "example")["document"]
        path = self.write("copy.md", example)
        outcome = self.state.verify_artifact(DISCOVERY, "gate", path)
        self.assertFalse(outcome["passed"])
        self.assertIn("copied", [m["id"] for m in outcome["missing"]])
        feedback = self.state.record_gate(DISCOVERY, "gate", outcome, artifact=path)["feedback"]
        self.assertEqual(feedback["focus"], "copied")
        self.assertIn("your own", feedback["hint"])

    def test_a_pass_says_the_writing_is_the_learners_to_judge(self):
        path = self.write("good.md", self.document(DISCOVERY))
        outcome = self.state.verify_artifact(DISCOVERY, "gate", path)
        self.assertIn("judge the writing yourself", outcome["detail"])


class LiveCheckFeedbackTests(AcademyCase):
    def record(self, missing, mission_id="operator.runtime"):
        outcome = {"passed": False, "title": "That doesn't match yet", "detail": missing[0]["what"], "facts": [], "missing": missing}
        return self.state.record_gate(mission_id, "gate", outcome)

    def test_a_live_miss_gets_the_missions_own_hint(self):
        feedback = self.record([{"id": "profile_mismatch", "what": 'You typed "work". Hermes reports a different profile.'}])["feedback"]
        self.assertIn("Spelling counts", feedback["hint"])

    def test_the_second_live_miss_adds_the_example(self):
        self.record([{"id": "profile_mismatch", "what": "x"}])
        feedback = self.record([{"id": "profile_mismatch", "what": "x"}])["feedback"]
        self.assertIn("sidebar", feedback["example"])

    def test_every_miss_a_live_check_can_report_has_a_hint_and_an_example(self):
        wanted = {
            "operator.runtime": ["not_connected", "no_answer", "missing_profile", "profile_mismatch", "connection_mismatch"],
            "operator.desktop": ["no_sessions", "no_marker"],
            "operator.learning": ["no_skills", "no_marked_skill"],
            "operator.automation": ["no_jobs", "no_marked_job", "no_schedule", "prompt_thin"],
        }
        for mission_id, ids in wanted.items():
            coach = self.state.gate_coach(self.step(mission_id, "gate"))
            for miss_id in ids:
                self.assertTrue(coach[miss_id]["hint"], f"{mission_id} {miss_id}")
                self.assertTrue(coach[miss_id]["example"], f"{mission_id} {miss_id}")

    def test_a_live_miss_with_no_description_still_says_something(self):
        outcome = {"passed": False, "title": "Hermes didn't answer", "detail": "Reconnect.", "facts": []}
        feedback = self.state.record_gate("operator.runtime", "gate", outcome)["feedback"]
        self.assertEqual(feedback["missing"][0]["what"], "Reconnect.")

    def test_untrusted_miss_lists_are_trimmed_to_a_few_short_items(self):
        flood = [{"id": f"x{i}", "what": "w" * 900} for i in range(30)] + ["junk", {"what": "no id"}]
        feedback = self.record(flood)["feedback"]
        self.assertLessEqual(len(feedback["missing"]), 8)
        self.assertLessEqual(len(feedback["missing"][0]["what"]), 400)

    def test_a_pass_is_recorded_as_evidence_with_no_feedback(self):
        outcome = self.state.record_gate("operator.runtime", "gate", {"passed": True, "title": "Your answers match what Hermes reports", "detail": "ok", "facts": []})
        self.assertIsNone(outcome["feedback"])
        self.assertEqual(len(self.rows("SELECT * FROM evidence WHERE step_id = 'gate'")), 1)

    def test_a_document_gate_with_a_live_part_fails_when_the_live_part_did_not_run(self):
        path = self.write("setup.md", self.document("integrator.deploy"))
        outcome = self.state.verify_artifact("integrator.deploy", "gate", path)
        self.assertFalse(outcome["passed"])
        self.assertEqual([m["id"] for m in outcome["missing"]], ["live_failed"])

    def test_a_document_gate_with_a_live_part_passes_when_both_pass(self):
        path = self.write("setup.md", self.document("integrator.deploy"))
        live = {"passed": True, "title": "ok", "detail": "ok", "facts": [{"label": "default", "value": "local"}]}
        outcome = self.state.verify_artifact("integrator.deploy", "gate", path, live=live)
        self.assertTrue(outcome["passed"], outcome["missing"])
        self.assertTrue(any(f["label"].startswith("Hermes:") for f in outcome["facts"]))

    def test_a_failed_live_part_blocks_a_good_document(self):
        path = self.write("setup.md", self.document("integrator.deploy"))
        live = {"passed": False, "title": "No connection route yet", "detail": "This window has no connection route.", "facts": []}
        outcome = self.state.verify_artifact("integrator.deploy", "gate", path, live=live)
        self.assertEqual([m["id"] for m in outcome["missing"]], ["live_failed"])
        self.assertIn("no connection route", outcome["missing"][0]["what"])


class ExplainFeedbackTests(AcademyCase):
    ANSWER = "A scheduled job runs through the gateway and not the window, so the app being open tells you very little about it. " * 2

    def submit(self, score, missed, feedback="You named the gateway."):
        self.state.submit_explanation("operator.runtime", "explain", self.ANSWER)
        return self.state.grade_explanation("operator.runtime", "explain", score, feedback, missed)

    def test_a_miss_lists_the_points_left_out(self):
        result = self.submit(55, [3, 4])
        whats = [m["what"] for m in result["ladder"]["missing"]]
        self.assertEqual(len(whats), 2)
        self.assertTrue(all(w.startswith("Missing point:") for w in whats))
        self.assertIn("profile", whats[0])

    def test_the_first_miss_has_a_hint_and_the_second_has_an_example(self):
        first = self.submit(55, [3])["ladder"]
        self.assertTrue(first["hint"] and not first["example"])
        second = self.submit(60, [3])["ladder"]
        self.assertTrue(second["hint"] and second["example"])
        self.assertEqual(second["level"], 2)

    def test_the_hint_is_for_the_first_point_left_out(self):
        ladder = self.submit(55, [4, 2])["ladder"]
        self.assertEqual(ladder["focus"], "point:2")
        coach = self.step("operator.runtime", "explain")["coach"][1]
        self.assertEqual(ladder["hint"], coach["hint"])

    def test_with_no_points_listed_the_graders_words_are_the_description(self):
        ladder = self.submit(40, [], feedback="You restated the question without answering it.")["ladder"]
        self.assertEqual(ladder["missing"][0]["what"], "You restated the question without answering it.")

    def test_points_out_of_range_are_ignored(self):
        ladder = self.submit(55, [0, 99, "x", 2])["ladder"]
        self.assertEqual([m["id"] for m in ladder["missing"]], ["point:2"])

    def test_a_pass_clears_the_ladder(self):
        self.submit(55, [3])
        result = self.submit(88, [])
        self.assertIsNone(result["ladder"])
        explanation = self.passport_step("operator.runtime", "explain")["explanation"]
        self.assertIsNone(explanation["ladder"])
        self.assertEqual(self.rows("SELECT * FROM attempts WHERE step_id = 'explain'"), [])

    def test_the_ladder_is_in_the_passport_for_the_page(self):
        self.submit(55, [3])
        explanation = self.passport_step("operator.runtime", "explain")["explanation"]
        self.assertEqual(explanation["score"], 55)
        self.assertEqual(explanation["ladder"]["level"], 1)

    def test_the_grading_instruction_asks_for_the_points_missed_by_number(self):
        prompt = self.state.submit_explanation("operator.runtime", "explain", self.ANSWER)["prompt"]
        self.assertIn("missed", prompt)
        self.assertRegex(prompt, r"\n1\. that an open app window")
        self.assertIn("Never offer to pass them anyway", prompt)

    def test_the_agent_tool_passes_the_missed_points_through(self):
        import json

        tools = sys.modules[f"{self.name}.tools"]
        self.state.submit_explanation("operator.runtime", "explain", self.ANSWER)
        args = {"mission_id": "operator.runtime", "step_id": "explain", "score": 50, "feedback": "x", "missed": [2]}
        reply = json.loads(tools.field_academy_grade_explanation(args))
        self.assertEqual(reply["ladder"]["focus"], "point:2")

    def test_every_explain_point_has_a_hint_and_an_example(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            step = next(s for s in mission["steps"] if s["kind"] == "explain")
            self.assertEqual(len(step["coach"]), len(step["covers"]), mission_id)
            for entry in step["coach"]:
                self.assertTrue(entry["hint"] and entry["example"], mission_id)


if __name__ == "__main__":
    unittest.main()
