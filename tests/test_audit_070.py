"""The fixes from the 0.7.0 end-to-end audit, one test each."""

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from support import AcademyCase

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")
DEPLOYER_SRC = (ROOT / "desktop" / "src" / "deployer.js").read_text(encoding="utf-8")
API = (ROOT / "dashboard" / "plugin_api.py").read_text(encoding="utf-8")


class ExplainPassStaysTests(AcademyCase):
    ANSWER = "Scheduled work runs through the gateway, a background program separate from the app window. " * 2

    def test_a_later_answer_never_takes_a_pass_back(self):
        self.pass_mission("operator.runtime")
        self.assertEqual(self.mission("operator.runtime")["status"], "verified")
        with self.assertRaises(ValueError) as caught:
            self.state.submit_explanation("operator.runtime", "explain", self.ANSWER)
        self.assertIn("pass stays", str(caught.exception))
        self.assertEqual(self.mission("operator.runtime")["status"], "verified")

    def test_a_failed_answer_can_still_be_tried_again(self):
        self.state.submit_explanation("operator.runtime", "explain", self.ANSWER)
        self.state.grade_explanation("operator.runtime", "explain", 40, "Missing the profile.", [2])
        again = self.state.submit_explanation("operator.runtime", "explain", self.ANSWER + " A profile holds its own memory.")
        self.assertEqual(again["attempts"], 2)

    def test_a_waiting_answer_can_be_sent_for_scoring_again(self):
        self.state.submit_explanation("operator.runtime", "explain", self.ANSWER)
        resent = self.state.resend_explanation("operator.runtime", "explain")
        self.assertIn("field_academy_grade_explanation", resent["prompt"])
        self.assertIn(self.ANSWER.strip()[:40], resent["prompt"])
        self.state.grade_explanation("operator.runtime", "explain", 90, "Clear.", [])
        with self.assertRaises(ValueError):
            self.state.resend_explanation("operator.runtime", "explain")

    def test_nothing_to_resend_is_a_plain_refusal(self):
        with self.assertRaises(ValueError):
            self.state.resend_explanation("operator.runtime", "explain")


class ScoreRoutesTests(unittest.TestCase):
    def test_no_web_route_writes_a_score(self):
        """Scores come only through the agent tools. A route that took a score would let the page grade itself."""
        for route in ('"/grade/{mission_id}/{step_id}"', '"/review/{session_id}/grade"', '"/deployer/grade"'):
            self.assertNotIn(route, API, route)
        self.assertIn('"/explain/{mission_id}/{step_id}/resend"', API)

    def test_every_route_the_page_calls_exists(self):
        calls = set(re.findall(r"ctxRest\(\s*[`']([^`'$]+)", SRC + DEPLOYER_SRC))
        routes = set(re.findall(r'@router\.(?:get|post)\("([^"]+)"', API))
        for call in calls:
            if call.endswith("/"):
                continue
            self.assertIn(call, routes, f"the page calls {call} and no route serves it")
        self.assertIn("/deployer/review/trust", routes)


class PastedDocumentTests(AcademyCase):
    def test_a_pasted_document_is_checked_like_a_file(self):
        text = self.document("integrator.discovery")
        path = self.state.save_pasted_document("integrator.discovery", "gate", text)
        self.assertTrue(Path(path).is_file())
        self.assertIn("pasted", path)
        outcome = self.state.verify_artifact("integrator.discovery", "gate", path)
        self.assertTrue(outcome["passed"], outcome.get("missing"))

    def test_only_a_document_gate_takes_a_paste(self):
        with self.assertRaises(ValueError):
            self.state.save_pasted_document("operator.runtime", "gate", "# Doc\n\n## A\nWords.")
        with self.assertRaises(ValueError):
            self.state.save_pasted_document("integrator.discovery", "gate", "   ")

    def test_the_gate_route_accepts_pasted_text(self):
        self.assertIn('body.get("text")', API)
        self.assertIn("save_pasted_document", API)
        self.assertIn("Paste the document instead", SRC)


class NewMissionNoticeTests(AcademyCase):
    def test_a_mission_added_before_you_started_is_not_news(self):
        self.set_time(self.store.clock().replace(year=2026, month=11, day=20))
        self.pass_mission("operator.runtime")
        fresh = [m["mission_id"] for m in self.state.snapshot()["new_missions"]]
        self.assertNotIn("operator.capstone", fresh)


class ReleaseRevisionTests(AcademyCase):
    def test_each_lesson_fix_reaches_learners_who_passed(self):
        c = self.curriculum
        released = [r for r in c.REVISIONS if r["released"] == "0.7.0"]
        self.assertEqual({r["mission_id"] for r in released}, set(c.RELEASE_REVISIONS))
        automation = [r for r in released if r["mission_id"] == "operator.automation"]
        self.assertEqual(automation[0]["kind"], "check")
        self.assertEqual(c.MISSIONS["operator.automation"]["version"], automation[0]["version"])

    def test_a_learner_who_passed_sees_the_automation_check_changed(self):
        self.pass_mission("operator.automation")
        with self.state._connection() as conn:
            conn.execute("UPDATE mission_versions SET passed_version = 2 WHERE mission_id = 'operator.automation'")
        changes = {c["mission_id"]: c for c in self.state.snapshot()["changes"]}
        self.assertEqual(changes["operator.automation"]["needs"], "check")


class ContentAccuracyTests(AcademyCase):
    def all_text(self):
        parts = []
        for path in [ROOT / "curriculum.py", ROOT / "deployer_content.py", *sorted((ROOT / "content").glob("*.py"))]:
            parts.append(path.read_text(encoding="utf-8"))
        return "\n".join(parts)

    def test_the_hosted_option_has_its_real_name(self):
        self.assertNotIn("Nous Cloud", self.all_text())
        self.assertNotIn("Nous Cloud", SRC)

    def test_the_approval_test_uses_the_prompt_hermes_actually_shows(self):
        mission = self.curriculum.MISSIONS["integrator.connect"]
        lab = next(s for s in mission["steps"] if s["kind"] == "lab")
        lesson = next(s for s in mission["steps"] if s["kind"] == "lesson")
        self.assertIn("risky command", lesson["body"])
        self.assertIn("draft-only", lesson["body"])
        self.assertIn("approvals", lab["body"])
        self.assertIn("scratch folder", lab["body"])

    def test_hiding_and_closing_a_pane_are_told_apart(self):
        lesson = next(s for s in self.curriculum.MISSIONS["operator.desktop"]["steps"] if s["kind"] == "lesson")
        self.assertIn("Hiding", lesson["body"])
        self.assertIn("Closing its tab", lesson["body"])

    def test_lessons_name_what_their_checks_read(self):
        def lesson(mission_id):
            return next(s for s in self.curriculum.MISSIONS[mission_id]["steps"] if s["kind"] == "lesson")["body"].lower()
        self.assertIn("price", lesson("integrator.discovery"))
        for word in ("profiles", "keys", "scheduled job"):
            self.assertIn(word, lesson("integrator.handoff"))
        for word in ("how long logs are kept", "access is reviewed"):
            self.assertIn(word, lesson("architect.governance"))
        for word in ("recovery time", "roll back"):
            self.assertIn(word, lesson("architect.reliability"))

    def test_no_invented_action_log(self):
        self.assertNotIn("action log", (ROOT / "content" / "track_architect.py").read_text(encoding="utf-8"))

    def test_teams_page_is_not_cited_for_tools_or_governance(self):
        for mission_id in ("integrator.connect", "architect.governance"):
            self.assertNotIn("official_teams", self.curriculum.MISSIONS[mission_id]["source_ids"])


class LiveCheckShapeTests(unittest.TestCase):
    def test_paused_jobs_are_asked_for(self):
        self.assertIn("rpc('cron.manage', { action: 'list', include_disabled: true })", SRC)

    def test_skills_are_read_fresh_and_flattened(self):
        self.assertIn("rpc('commands.catalog')", SRC)
        self.assertIn("flattenSkills(listed)", SRC)

    def test_the_automation_check_asks_for_the_whole_request(self):
        self.assertIn("paste_request", SRC)
        self.assertIn("request_mismatch", SRC)
        fixes = (ROOT / "content" / "track_operator.py").read_text(encoding="utf-8")
        self.assertIn('"paste_request"', fixes)
        self.assertIn('"request_mismatch"', fixes)

    def test_a_busy_hermes_still_gets_the_scoring_request(self):
        # Scoring goes to its own new chat, so a busy chat never swallows it, and a failed
        # submit copies the request for the learner to paste.
        send = SRC[SRC.index("async function sendToHermes(text)"):]
        self.assertIn("return sendInNewChat(text", send[:300])
        fallback = SRC[SRC.index("async function sendInNewChat("):]
        self.assertIn("writeClipboard(text)", fallback[:700])

    def test_the_node_checks_pass(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        out = subprocess.run([node, "--test", str(ROOT / "tests" / "release.test.mjs")], capture_output=True, text=True, timeout=120)
        self.assertEqual(out.returncode, 0, out.stdout[-2000:] + out.stderr[-2000:])


class ReviewerTrustTests(unittest.TestCase):
    def test_the_page_says_the_published_list_is_empty_and_how_to_add_one(self):
        self.assertIn("published reviewer list is empty", DEPLOYER_SRC)
        self.assertIn("/deployer/review/trust", DEPLOYER_SRC)


if __name__ == "__main__":
    unittest.main()
