"""The audit of every check: none passes because something merely exists.

Each gate must ask for a specific thing the learner made during the mission:
a typed answer compared with what Hermes reports, an item carrying a
mission-specific marker, or a document whose sections each hold real content.
The limits that remain are written down in docs/checks.md, and this file checks
that the document and the code agree.
"""

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase, ROOT  # noqa: E402

DESKTOP = {
    "operator.runtime": ("runtime", ""),
    "operator.desktop": ("workspace", "[FA-DESKTOP]"),
    "operator.learning": ("knowledge", "academy-"),
    "operator.automation": ("automation", "academy-"),
}
OLD_EXISTS_CHECKS = ("agents", "estate_only", "workspace_any")


class AuditTests(AcademyCase):
    def gates(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            yield mission_id, next(s for s in mission["steps"] if s["kind"] == "gate")

    def test_the_four_live_checks_use_a_typed_answer_or_a_marker(self):
        for mission_id, (check, marker) in DESKTOP.items():
            gate = self.step(mission_id, "gate")
            self.assertEqual((gate["verify"], gate["check"]), ("desktop", check), mission_id)
            self.assertEqual(gate["marker"], marker, mission_id)
        self.assertEqual({i["id"] for i in self.step("operator.runtime", "gate")["inputs"]}, {"profile", "connection"})

    def test_no_other_gate_reads_only_the_live_app(self):
        desktop = [m for m, g in self.gates() if g["verify"] == "desktop"]
        self.assertEqual(sorted(desktop), sorted(DESKTOP))

    def test_every_document_gate_asks_for_content_in_every_section(self):
        for mission_id, gate in self.gates():
            if gate["verify"] != "artifact":
                continue
            self.assertGreaterEqual(len(gate["sections"]), 3, mission_id)
            for rule in gate["sections"]:
                self.assertGreaterEqual(rule["min_words"], 4, f"{mission_id} {rule['heading']}")
                self.assertTrue(rule["hint"] and rule["example"] and rule["what"], f"{mission_id} {rule['heading']}")

    def test_most_sections_also_need_something_specific(self):
        for mission_id, gate in self.gates():
            if gate["verify"] != "artifact":
                continue
            with_needs = [r for r in gate["sections"] if r.get("needs")]
            self.assertGreaterEqual(len(with_needs), 2, mission_id)

    def test_a_section_that_needs_a_name_names_a_person_not_a_team(self):
        for mission_id, gate in self.gates():
            for rule in gate.get("sections", []):
                if "name" in rule.get("needs", []):
                    self.assertTrue(rule.get("fix"), f"{mission_id} {rule['heading']}")

    def test_a_stub_with_every_heading_fails_every_document_gate(self):
        for mission_id, gate in self.gates():
            if gate["verify"] != "artifact":
                continue
            stub = "# Stub\n\n" + "\n\n".join(f"## {r['heading']}\nTODO" for r in gate["sections"])
            result = self.documents.analyze(stub, gate)
            self.assertGreaterEqual(len(result["missing"]), len(gate["sections"]), mission_id)

    def test_headings_alone_with_padding_fail_every_document_gate(self):
        """The 0.4.0 check passed any file that had the headings and 240 characters."""
        for mission_id, gate in self.gates():
            if gate["verify"] != "artifact":
                continue
            padded = "\n\n".join(f"## {r['heading']}\n" + "filler words here " * 6 for r in gate["sections"])
            self.assertFalse(self.documents.analyze(padded, gate)["missing"] == [], mission_id)

    def test_the_old_check_that_passed_a_padded_file_is_gone(self):
        text = (ROOT / "state.py").read_text(encoding="utf-8")
        self.assertNotIn("body_chars >= 240", text)

    def test_four_capstone_gates_compare_criteria_with_evidence(self):
        for track_id in self.curriculum.TRACKS:
            gate = self.step(f"{track_id}.capstone", "gate")
            self.assertEqual(gate["cross"], "criteria")
            self.assertEqual(gate["headings"][:1], ["Problem"])
            self.assertIn("Criteria", gate["headings"])
            self.assertIn("Evidence", gate["headings"])

    def test_a_document_gate_with_a_live_part_declares_which_one(self):
        lives = {m: g["live"] for m, g in self.gates() if g.get("live")}
        self.assertEqual(lives, {"integrator.deploy": "routes", "integrator.connect": "connections", "architect.estate": "estate"})

    def test_every_gate_proof_says_what_it_proves_in_plain_words(self):
        for mission_id, gate in self.gates():
            self.assertGreater(len(gate["proof"].split()), 6, mission_id)

    def test_the_limits_that_remain_are_documented(self):
        text = (ROOT / "docs" / "checks.md").read_text(encoding="utf-8")
        for mission_id in (
            "operator.runtime", "operator.desktop", "operator.automation",
            "integrator.connect", "architect.operations",
        ):
            self.assertIn(mission_id, text)
        self.assertIn("cannot be made strong", text)

    def test_every_mission_is_in_the_audit_table(self):
        text = (ROOT / "docs" / "checks.md").read_text(encoding="utf-8")
        for mission_id in self.curriculum.MISSIONS:
            self.assertIn(f"`{mission_id}`", text, mission_id)

    def test_the_marker_in_the_lab_matches_the_marker_in_the_check(self):
        lab = self.step("operator.desktop", "lab")
        self.assertTrue(lab["prompt"].startswith("[FA-DESKTOP]"))
        for mission_id in ("operator.learning", "operator.automation"):
            lab = self.step(mission_id, "lab")
            self.assertIn("academy-", lab["body"] + lab["prompt"], mission_id)


class BrowserSideTests(unittest.TestCase):
    """The live checks are JavaScript; these read the source for the rules that matter."""

    @classmethod
    def setUpClass(cls):
        cls.src = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")

    def test_every_live_check_returns_miss_ids_for_the_hint_ladder(self):
        for miss_id in (
            "not_connected", "no_answer", "missing_profile", "profile_mismatch", "connection_mismatch",
            "no_sessions", "no_marker", "no_skills", "no_marked_skill", "no_jobs", "no_marked_job", "no_schedule", "prompt_thin",
        ):
            self.assertIn(f"miss('{miss_id}'", self.src, miss_id)

    def test_the_old_exists_only_checks_are_gone(self):
        self.assertNotIn("async agents()", self.src)
        self.assertNotIn("Hermes lists installed skills and sets of tools", self.src)

    def test_a_live_check_runs_with_the_learners_typed_answers(self):
        self.assertIn("runDesktopCheck(live, values)", self.src)
        self.assertIn("runDesktopCheck({ check: step.live }, {})", self.src)

    def test_a_document_gate_sends_its_live_result_with_the_file(self):
        self.assertIn("record({ ...(pasting ? { text: pasted } : { path: path.trim() }), ...(liveOutcome ? { live: liveOutcome } : {}) })", self.src)


if __name__ == "__main__":
    unittest.main()
