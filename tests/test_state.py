"""Invariant tests. Stdlib only: use `python -m unittest`, not pytest."""

import importlib.util
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]



def _fixtures():
    spec = importlib.util.spec_from_file_location("fa_make_fixtures_for_tests", ROOT / "harness" / "make_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(tmpdir):
    os.environ["FIELD_ACADEMY_DATA_DIR"] = tmpdir
    spec = importlib.util.spec_from_file_location(
        "field_academy_under_test", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules["field_academy_under_test"] = package
    spec.loader.exec_module(package)
    return sys.modules["field_academy_under_test"]


class FieldAcademyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pkg = load(self.tmp)
        self.state = self.pkg.state
        self.curriculum = sys.modules.get(f"{self.pkg.__name__}.curriculum") or self.pkg.curriculum

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("FIELD_ACADEMY_DATA_DIR", None)

    def docs(self):
        return pathlib.Path(self.tmp)

    def document(self, mission_id):
        """A document that passes the mission's gate and is not the worked example."""
        gate = next(s for s in self.curriculum.MISSIONS[mission_id]["steps"] if s["kind"] == "gate")
        return _fixtures().build_document(gate)

    # -- shape ---------------------------------------------------------------

    def test_every_mission_fades_from_example_to_gaps_to_alone(self):
        snapshot = self.state.snapshot()
        for track in snapshot["tracks"]:
            for mission in track["missions"]:
                kinds = [step["kind"] for step in mission["steps"]]
                # A story-first mission shows the finished example before the short takeaway.
                first = ["example", "lesson"] if mission.get("story_first") else ["lesson", "example"]
                self.assertEqual(kinds, first + ["complete", "lab", "explain", "gate"], mission["id"])

    def test_every_mission_has_a_graded_question_with_a_rubric(self):
        snapshot = self.state.snapshot()
        for track in snapshot["tracks"]:
            for mission in track["missions"]:
                step = next(item for item in mission["steps"] if item["kind"] == "explain")
                self.assertGreater(len(step["body"]), 80, mission["id"])
                self.assertGreaterEqual(len(step["covers"]), 3, mission["id"])
                self.assertEqual(step["threshold"], 70)

    def test_explain_step_cannot_be_closed_by_hand(self):
        with self.assertRaises(ValueError):
            self.state.update_step("operator.runtime", "explain", "done")

    def test_a_one_line_answer_is_refused(self):
        with self.assertRaises(ValueError):
            self.state.submit_explanation("operator.runtime", "explain", "The gateway.")

    def test_grading_needs_a_submitted_answer_first(self):
        with self.assertRaises(ValueError):
            self.state.grade_explanation("operator.runtime", "explain", 90, "great")

    def test_a_submission_returns_a_grading_instruction(self):
        payload = self.state.submit_explanation(
            "operator.runtime", "explain", "The window is not the machine. " * 8
        )
        prompt = payload["prompt"]
        self.assertIn("field_academy_grade_explanation", prompt)
        self.assertIn("operator.runtime", prompt)
        self.assertIn("Score 0-100 on substance only", prompt)

    def test_a_failing_score_leaves_the_step_open_and_passes_nothing(self):
        self.state.submit_explanation("operator.runtime", "explain", "The window is not the machine. " * 8)
        result = self.state.grade_explanation("operator.runtime", "explain", 45, "Vague on the profile.")
        self.assertFalse(result["passed"])
        mission = self.state.mission_snapshot("operator.runtime")
        step = next(item for item in mission["steps"] if item["kind"] == "explain")
        self.assertEqual(step["status"], "needs_attention")
        self.assertEqual(mission["evidence"], [])

    def test_a_passing_score_closes_the_step_and_records_it(self):
        self.state.submit_explanation("operator.runtime", "explain", "The window is not the machine. " * 8)
        result = self.state.grade_explanation("operator.runtime", "explain", 82, "Named the profile, missed the log.")
        self.assertTrue(result["passed"])
        mission = self.state.mission_snapshot("operator.runtime")
        step = next(item for item in mission["steps"] if item["kind"] == "explain")
        self.assertEqual(step["status"], "done")
        self.assertEqual(step["explanation"]["score"], 82)
        self.assertEqual(len(mission["evidence"]), 1)
        self.assertEqual(mission["evidence"][0]["kind"], "explanation")

    def test_resubmitting_keeps_the_attempt_count(self):
        for _ in range(3):
            self.state.submit_explanation("operator.runtime", "explain", "The window is not the machine. " * 8)
        self.state.grade_explanation("operator.runtime", "explain", 30, "Try again.")
        record = self.state.snapshot_explanation("operator.runtime", "explain")
        self.assertEqual(record["attempts"], 3)

    def test_a_grade_is_clamped_to_the_range(self):
        self.state.submit_explanation("operator.runtime", "explain", "The window is not the machine. " * 8)
        self.assertEqual(self.state.grade_explanation("operator.runtime", "explain", 900, "x")["score"], 100)

    def test_compact_shape_stays_small(self):
        """The agent tool must not carry the curriculum into context."""
        self.assertLess(len(json.dumps(self.state.compact())), 6000)

    def test_lesson_text_is_not_rubric_language(self):
        """Instructions describe work; they do not order the reader to file paperwork."""
        banned = ("save the ", "record the ", "make me ", "prove that ")
        snapshot = self.state.snapshot()
        for track in snapshot["tracks"]:
            for mission in track["missions"]:
                for step in mission["steps"]:
                    body = step.get("body", "").lower()
                    for phrase in banned:
                        self.assertNotIn(phrase, body, f"{mission['id']}/{step['id']}")

    # -- gates ---------------------------------------------------------------

    def test_gate_cannot_be_closed_by_hand(self):
        with self.assertRaises(ValueError):
            self.state.update_step("operator.runtime", "gate", "done")

    def test_artifact_gate_rejects_a_stub(self):
        target = self.docs() / "stub.md"
        target.write_text("# Client\nnot much here")
        outcome = self.state.verify_artifact("integrator.discovery", "gate", str(target))
        self.assertFalse(outcome["passed"])

    def test_artifact_gate_rejects_a_missing_section(self):
        target = self.docs() / "partial.md"
        target.write_text("## Client\n" + "real content " * 60)
        outcome = self.state.verify_artifact("integrator.discovery", "gate", str(target))
        self.assertFalse(outcome["passed"])

    def test_artifact_gate_accepts_a_real_document_and_hashes_it(self):
        target = self.docs() / "scope.md"
        target.write_text(self.document("integrator.discovery"))
        outcome = self.state.verify_artifact("integrator.discovery", "gate", str(target))
        self.assertTrue(outcome["passed"], outcome["missing"])
        self.state.record_gate("integrator.discovery", "gate", outcome, artifact=str(target))
        mission = self.state.mission_snapshot("integrator.discovery")
        self.assertEqual(mission["steps"][-1]["status"], "done")
        self.assertEqual(len(mission["evidence"]), 1)
        self.assertEqual(len(mission["evidence"][0]["sha256"]), 64)

    def test_missing_file_fails_the_gate_cleanly(self):
        outcome = self.state.verify_artifact("integrator.discovery", "gate", str(self.docs() / "nope.md"))
        self.assertFalse(outcome["passed"])
        self.assertIn("No file", outcome["title"])

    def test_artifact_gate_rejects_an_empty_file(self):
        target = self.docs() / "empty.md"
        target.write_text("", encoding="utf-8")
        outcome = self.state.verify_artifact("integrator.discovery", "gate", str(target))
        self.assertFalse(outcome["passed"])
        self.assertIn("empty", outcome["title"].lower())

    def test_artifact_gate_rejects_a_binary_file(self):
        """A PDF or an image read as text can satisfy a heading check by accident."""
        target = self.docs() / "scan.pdf"
        target.write_bytes(b"%PDF-1.4\n" + bytes(range(256)) * 40)
        outcome = self.state.verify_artifact("integrator.discovery", "gate", str(target))
        self.assertFalse(outcome["passed"])
        self.assertIn("text document", outcome["title"])

    def test_artifact_gate_refuses_a_file_over_the_cap(self):
        """The backend runs inside the gateway process; an unbounded read is a
        way to take the agent down with one file."""
        original = self.state.MAX_ARTIFACT_BYTES
        self.state.MAX_ARTIFACT_BYTES = 64
        try:
            target = self.docs() / "big.md"
            target.write_text("x" * 500, encoding="utf-8")
            outcome = self.state.verify_artifact("integrator.discovery", "gate", str(target))
            self.assertFalse(outcome["passed"])
            self.assertIn("large", outcome["title"].lower())
        finally:
            self.state.MAX_ARTIFACT_BYTES = original

    def test_a_real_document_under_the_cap_still_passes(self):
        """The bound must not break the feature it protects."""
        target = self.docs() / "scope.md"
        target.write_text(self.document("integrator.discovery"), encoding="utf-8")
        self.assertLess(target.stat().st_size, self.state.MAX_ARTIFACT_BYTES)
        self.assertTrue(self.state.verify_artifact("integrator.discovery", "gate", str(target))["passed"])

    # -- the payload the pane reads ------------------------------------------

    def test_the_passport_carries_what_the_pane_reads(self):
        """The desktop half branches on step.status and step.explanation. The
        passport used to omit both, so no step ever rendered as done, a passed
        gate kept offering 'Run the check', and a graded explanation never
        showed its score."""
        self.state.update_step("operator.runtime", "concept", "done")
        snap = self.state.snapshot()
        mission = next(m for t in snap["tracks"] for m in t["missions"] if m["id"] == "operator.runtime")
        for step in mission["steps"]:
            self.assertIn("status", step, step["id"])
            self.assertIn(step["status"], {"ready", "done", "needs_attention", "placed"}, step["id"])
            if step["kind"] == "explain":
                self.assertIn("explanation", step, step["id"])
        concept = next(s for s in mission["steps"] if s["id"] == "concept")
        self.assertEqual(concept["status"], "done")

    def test_the_passport_and_the_mission_view_agree_on_step_status(self):
        """Two shapes of the same thing. If they disagree, the pane and the
        agent are describing different states of the same step."""
        self.state.update_step("operator.runtime", "concept", "done")
        snap = self.state.snapshot()
        passport = next(m for t in snap["tracks"] for m in t["missions"] if m["id"] == "operator.runtime")
        view = self.state.mission_snapshot("operator.runtime")
        self.assertEqual(
            [s["status"] for s in passport["steps"]],
            [s["status"] for s in view["steps"]],
        )

    def test_snapshot_is_idempotent(self):
        """A snapshot that mutates shared state makes every later read drift."""
        self.state.update_step("operator.runtime", "concept", "done")
        self.assertEqual(self.state.snapshot()["tracks"], self.state.snapshot()["tracks"])

    # -- the two halves ------------------------------------------------------

    def test_both_halves_agree_on_the_directive_name(self):
        """A directive renamed on one side only is a silent no-op: the model
        emits a name nothing renders and the offer vanishes with no error."""
        # Read the source: the built desktop/plugin.js prints the same line in double quotes.
        source = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")
        match = re.search(r"const DIRECTIVE = '([^']+)'", source)
        self.assertIsNotNone(match, "desktop/plugin.js must declare DIRECTIVE")
        declared = match.group(1) if match else ""
        self.assertEqual(declared, self.pkg.DIRECTIVE)
        self.assertIn("name: DIRECTIVE", source, "the desktop half must register the shared name")

    def test_the_offer_carries_the_registered_directive(self):
        # The offer only names a mission on the learner's chosen path.
        self.state.set_goal("operator")
        self.state.observe_tool("operator.runtime", "terminal", "sess-1")
        context = self.pkg._pre_llm_call(session_id="sess-1")["context"]
        self.assertIn(f"::{self.pkg.DIRECTIVE}{{", context)
        self.assertNotIn("hermes-growth", context)

    def test_no_public_name_is_left_over_from_the_predecessor_plugin(self):
        """Legacy names carry collision risk and no benefit."""
        for rel in ("__init__.py", "schemas.py", "tools.py", "plugin.yaml", "desktop/plugin.js", "desktop/src/plugin.js"):
            source = (ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("hermes-growth", source, rel)
            self.assertNotIn("hermes_growth", source, rel)
            self.assertNotIn("growth_snapshot", source, rel)

    # -- catalog entry -------------------------------------------------------

    @staticmethod
    def _declared(path, key):
        """Read a `key:` list out of a YAML file without pulling in PyYAML."""
        names, inside = [], False
        for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
            if re.match(rf"^\s*{key}:\s*$", line):
                inside = True
                continue
            if inside:
                item = re.match(r"^\s+-\s+(\S+)\s*$", line)
                if item:
                    names.append(item.group(1))
                elif line.strip():
                    break
        return names

    def test_the_catalog_entry_agrees_with_the_manifest(self):
        """A stale catalog entry passes every machine check: the structural
        validator only proves the block is a list of strings, so an entry that
        understates the plugin is caught by a human reading the diff. Catch it
        here instead of in review."""
        for key in ("provides_tools", "provides_hooks"):
            manifest = self._declared("plugin.yaml", key)
            self.assertTrue(manifest, f"plugin.yaml declares no {key}")
            self.assertEqual(
                self._declared("catalog-entry.yaml", key),
                manifest,
                f"catalog-entry.yaml {key} disagrees with plugin.yaml",
            )

    def test_the_catalog_entry_pins_a_real_sha_or_says_so(self):
        source = (ROOT / "catalog-entry.yaml").read_text(encoding="utf-8")
        match = re.search(r"^sha:\s*(\S+)", source, re.M)
        self.assertIsNotNone(match, "catalog-entry.yaml must carry a sha")
        value = match.group(1) if match else ""
        self.assertTrue(
            re.fullmatch(r"[0-9a-f]{40}", value) or value.startswith("REPLACE_WITH"),
            f"sha must be 40 lowercase hex characters or an explicit placeholder, got {value!r}",
        )

    # -- hooks ---------------------------------------------------------------

    def test_an_unmatched_scan_consumes_nothing(self):
        """The spotlight watermark may only advance past rows that were actually
        offered. Advancing on a scan that matched nothing silently eats an
        opportunity the learner would have seen after switching level."""
        self.state.set_goal("operator")
        self.assertTrue(self.state.observe_tool("integrator.discovery", "terminal", "sess-a"))
        self.assertIsNone(self.state.claim_spotlight("sess-a"))
        self.state.set_goal("integrator")
        offered = self.state.claim_spotlight("sess-a")
        self.assertIsNotNone(offered, "a scan that offered nothing must not consume the opportunity")
        self.assertEqual(offered["id"], "integrator.discovery")

    def test_a_consumed_opportunity_is_not_offered_twice(self):
        self.state.set_goal("operator")
        self.state.observe_tool("operator.runtime", "terminal", "sess-b")
        self.assertIsNotNone(self.state.claim_spotlight("sess-b"))
        self.assertIsNone(self.state.claim_spotlight("sess-b"))

    def test_scheduled_and_gateway_sessions_are_not_learners(self):
        for session in ("cron:abc", "cron_abc_20260101", "webhook:x", "gateway:telegram"):
            self.assertFalse(self.state.is_learner_session(session), session)
        self.assertTrue(self.state.is_learner_session("20260916_120000_abcd"))

    def test_no_opportunity_is_recorded_from_a_scheduled_run(self):
        self.assertFalse(self.state.observe_tool("operator.runtime", "terminal", "cron:abc"))
        self.assertIsNone(self.state.claim_spotlight("cron:abc"))

    def test_opportunity_is_offered_once_per_session(self):
        self.assertTrue(self.state.observe_tool("operator.runtime", "terminal", "sess-1"))
        self.assertFalse(self.state.observe_tool("operator.runtime", "terminal", "sess-1"))

    def test_directive_only_fires_inside_a_learner_session(self):
        self.state.observe_tool("operator.runtime", "terminal", "sess-1")
        self.assertIsNone(self.pkg._pre_llm_call(session_id="cron:abc"))
        self.assertIsNone(self.pkg._pre_llm_call(session_id=""))

    def test_directive_stays_out_of_messaging_apps(self):
        # Gateway session ids carry no prefix, so the platform Hermes passes decides.
        self.state.set_goal("operator")
        self.state.observe_tool("operator.runtime", "terminal", "20261015_090000_ab12")
        for platform in ("telegram", "slack", "webhook", "cron"):
            self.assertIsNone(self.pkg._pre_llm_call(session_id="20261015_090000_ab12", platform=platform))
        self.assertIsNotNone(self.pkg._pre_llm_call(session_id="20261015_090000_ab12", platform="desktop"))

    # -- housekeeping --------------------------------------------------------

    def test_rows_from_an_older_version_are_purged(self):
        with self.state._connection() as conn:
            conn.execute(
                "INSERT INTO evidence(mission_id, step_id, kind, summary, created_at) VALUES (?,?,'note',?,?)",
                ("operator.setup", "", "Hermes observed use of the terminal capability.", "2026-09-15T00:00:00+00:00"),
            )
        snapshot = self.state.snapshot()
        self.assertEqual(snapshot["recent_evidence"], [])

    def test_sources_all_resolve_to_a_url(self):
        for track in self.state.snapshot()["tracks"]:
            for mission in track["missions"]:
                for source in mission["sources"]:
                    self.assertTrue(source["url"].startswith("https://"))

    def test_every_reference_is_complete_and_well_formed(self):
        """A dead or half-filled link claims teaching that is not there."""
        for key, episode in self.curriculum.EPISODES.items():
            for field in ("course", "part", "title", "creator", "where", "credit", "url"):
                self.assertTrue(episode.get(field), f"{key} {field}")
            self.assertTrue(episode["url"].startswith("https://"), key)
            self.assertIn(episode["creator"], episode["credit"], key)
            if "youtube.com" in episode["url"]:
                self.assertRegex(episode["url"], r"watch\?v=[A-Za-z0-9_-]{11}$", key)

    def test_every_mission_routes_to_specific_material(self):
        watch = self.curriculum.WATCH
        self.assertEqual(len(watch), 20)
        self.assertEqual(self.curriculum.unwatched_missions(), [])
        for mission_id, keys in watch.items():
            self.assertGreaterEqual(len(keys), 3, mission_id)
            for key in keys:
                self.assertIn(key, self.curriculum.EPISODES, mission_id)

    def test_every_mission_lists_the_official_docs_first(self):
        for mission_id, keys in self.curriculum.WATCH.items():
            first = self.curriculum.EPISODES[keys[0]]
            self.assertEqual(first["creator"], "Nous Research", mission_id)
            self.assertTrue(first["url"].startswith("https://hermes-agent.nousresearch.com/docs/"), mission_id)

    def test_tonbis_masterclass_goes_through_hermes_atlas(self):
        """Credits rule: credit Tonbi on Atlas, which carries timestamped notes."""
        for key, episode in self.curriculum.EPISODES.items():
            if episode["course"] == "Hermes Agent Masterclass" and key != "t.quickstart":
                self.assertRegex(episode["url"], r"^https://hermesatlas\.com/masterclass/#episode-(10|[1-9])$", key)
                self.assertEqual(episode["credit"], "Tonbi, on Hermes Atlas", key)

    def test_the_community_hubs_are_credited_by_name(self):
        credits = {episode["credit"] for episode in self.curriculum.EPISODES.values()}
        self.assertIn("Kevin Simback, on Hermes Atlas", credits)
        self.assertIn("iamlukethedev, on the Hermes Bible", credits)
        for key, episode in self.curriculum.EPISODES.items():
            if "hermesbible.com" in episode["url"]:
                self.assertEqual(episode["credit"], "iamlukethedev, on the Hermes Bible", key)
            if "hermesatlas.com/guide" in episode["url"]:
                self.assertEqual(episode["credit"], "Kevin Simback, on Hermes Atlas", key)
                # These two sections contradict how Field Academy teaches; never link them.
                self.assertNotIn("#channels", episode["url"], key)
                self.assertNotIn("#plugins", episode["url"], key)

    def test_the_commercial_missions_route_into_the_provider_labs(self):
        """The four non-technical missions have no video; the labs carry them."""
        watch = self.curriculum.WATCH
        for mission_id in ("integrator.discovery", "integrator.handoff", "ambassador.qualify", "ambassador.handoff"):
            self.assertTrue(any(key.startswith("lab.") for key in watch[mission_id]), mission_id)

    def test_every_source_family_is_represented(self):
        keys = {key.split(".")[0] for keys in self.curriculum.WATCH.values() for key in keys}
        self.assertEqual(keys, {"nous", "t", "d", "atlas", "bible", "tony", "lab"})

    def test_watch_rides_along_on_the_lesson_step(self):
        mission = self.state.mission_snapshot("operator.learning")
        lesson = next(step for step in mission["steps"] if step["kind"] == "lesson")
        credits = [episode["credit"] for episode in lesson["watch"]]
        self.assertEqual(credits[0], "Nous Research, Hermes docs")
        self.assertIn("Tonbi, on Hermes Atlas", credits)
        self.assertIn("Kevin Simback, on Hermes Atlas", credits)
        self.assertIn("iamlukethedev, on the Hermes Bible", credits)
        self.assertIn("Tony Simons, on X", credits)
        self.assertEqual(lesson["watch"][1]["part"], "Episode 3")

if __name__ == "__main__":
    unittest.main()
