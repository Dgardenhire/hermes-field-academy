"""The path map, the level ladder, the certificate route and the certificate itself.

Stdlib only: run with `python -m unittest discover -s tests`.
"""

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
ANSWER = "Hermes runs scheduled work through the gateway, which is a separate program from the app window. " * 2



def _fixtures():
    spec = importlib.util.spec_from_file_location("fa_make_fixtures_for_tests", ROOT / "harness" / "make_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(tmpdir):
    os.environ["FIELD_ACADEMY_DATA_DIR"] = tmpdir
    spec = importlib.util.spec_from_file_location(
        "field_academy_paths_under_test", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules["field_academy_paths_under_test"] = package
    spec.loader.exec_module(package)
    return package


class PathwayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pkg = load(self.tmp)
        self.state = self.pkg.state
        self.curriculum = sys.modules[f"{self.pkg.__name__}.curriculum"]
        self.pathways = sys.modules[f"{self.pkg.__name__}.pathways"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("FIELD_ACADEMY_DATA_DIR", None)

    # -- helpers -------------------------------------------------------------

    def track(self, track_id):
        return next(t for t in self.state.snapshot()["tracks"] if t["id"] == track_id)

    def pass_mission(self, mission_id, score=88):
        _fixtures().pass_mission(self.state, self.curriculum, self.tmp, mission_id, score)

    def pass_track(self, track_id):
        for item in self.curriculum.TRACKS[track_id]["missions"]:
            self.pass_mission(item["id"])

    # -- the map -------------------------------------------------------------

    def test_every_path_has_three_levels_and_a_capstone_in_order(self):
        for track in self.state.snapshot()["tracks"]:
            self.assertEqual([rung["name"] for rung in track["levels"]], ["Beginner", "Intermediate", "Advanced", "Capstone"], track["id"])
            self.assertEqual([rung["number"] for rung in track["levels"]], [1, 2, 3, 4])

    def test_every_level_says_what_it_means_and_has_a_mission(self):
        for track in self.state.snapshot()["tracks"]:
            for rung in track["levels"]:
                self.assertGreater(len(rung["meaning"]), 30, f"{track['id']}/{rung['id']}")
                self.assertTrue(rung["meaning"].startswith(("You ", "Hermes ")), rung["meaning"])
                self.assertGreaterEqual(rung["total"], 1, f"{track['id']}/{rung['id']}")

    def test_every_mission_belongs_to_exactly_one_level(self):
        for track in self.state.snapshot()["tracks"]:
            placed = [mission_id for rung in track["levels"] for mission_id in rung["missions"]]
            self.assertEqual(sorted(placed), sorted(m["id"] for m in track["missions"]), track["id"])

    def test_a_fresh_learner_is_at_the_first_beginner_mission(self):
        track = self.track("operator")
        self.assertEqual(track["current_level"], "beginner")
        self.assertEqual(track["here"], "operator.runtime")
        self.assertTrue(track["levels"][0]["current"])
        self.assertFalse(any(rung["current"] for rung in track["levels"][1:]))

    def test_next_up_points_at_the_start_of_the_chosen_path(self):
        # A fresh learner starts on the Messenger path, which is listed first.
        data = self.state.snapshot()
        self.assertEqual(data["next_up"]["mission_id"], "ambassador.firsthand")
        self.assertIn("starts", data["next_up"]["reason"])
        self.state.set_goal("operator")
        self.assertEqual(self.state.snapshot()["next_up"]["mission_id"], "operator.runtime")

    def test_passing_the_beginner_level_moves_you_up_a_rung(self):
        self.pass_mission("operator.runtime")
        self.assertEqual(self.track("operator")["current_level"], "beginner")
        self.pass_mission("operator.desktop")
        track = self.track("operator")
        self.assertEqual(track["levels"][0]["status"], "passed")
        self.assertEqual(track["current_level"], "intermediate")
        self.assertEqual(track["here"], "operator.learning")

    def test_a_passed_mission_carries_its_pass_date(self):
        self.pass_mission("operator.runtime")
        mission = next(m for m in self.track("operator")["missions"] if m["id"] == "operator.runtime")
        self.assertEqual(mission["status"], "verified")
        self.assertRegex(mission["passed_at"], r"^\d{4}-\d{2}-\d{2}T")

    def test_a_started_mission_shows_as_started_on_its_level(self):
        self.state.update_step("operator.runtime", "concept", "done")
        rung = self.track("operator")["levels"][0]
        self.assertEqual(rung["status"], "started")
        self.assertEqual(self.state.snapshot()["next_up"]["reason"], "You've started it. Pick up where you left off.")

    # -- the certificate route ----------------------------------------------

    def test_the_route_says_what_to_do_what_proof_and_what_you_get(self):
        for track in self.state.snapshot()["tracks"]:
            route = track["certificate"]
            self.assertEqual(route["status"], "not_started")
            self.assertEqual(len(route["steps"]), 3)
            self.assertEqual(len(route["proof"]), len(track["missions"]))
            for row in route["proof"]:
                self.assertTrue(row["check"], row["mission_id"])
                self.assertIn("70 or more", row["explain"])
            self.assertGreaterEqual(len(route["receive"]), 3)
            self.assertIn("Created by its holder", route["issuer"])
            self.assertEqual(route["disclaimer"], "Self-issued with Field Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research.")
            self.assertEqual(route["title"], f"{track['name']} Field Record")

    def test_the_proof_list_runs_beginner_to_advanced(self):
        order = {"Beginner": 0, "Intermediate": 1, "Advanced": 2, "Capstone": 3}
        for track in self.state.snapshot()["tracks"]:
            levels = [order[row["level_name"]] for row in track["certificate"]["proof"]]
            self.assertEqual(levels, sorted(levels), track["id"])

    def test_document_missions_say_the_fingerprint_goes_on_the_field_record(self):
        for mission in self.curriculum.MISSIONS.values():
            gate = next(step for step in mission["steps"] if step["kind"] == "gate")
            if gate["verify"] == "artifact":
                self.assertIn("fingerprint goes on your Field Record", gate["proof"], mission["id"])

    def test_the_route_counts_down_as_missions_pass(self):
        self.pass_mission("ambassador.story")
        route = self.track("ambassador")["certificate"]
        self.assertEqual(route["status"], "in_progress")
        self.assertEqual((route["passed"], route["remaining"]), (1, 4))
        story = next(item for item in route["proof"] if item["mission_id"] == "ambassador.story")
        self.assertTrue(story["passed"])

    # -- issuing ---------------------------------------------------------------

    def test_a_certificate_is_refused_until_every_mission_passes(self):
        self.pass_mission("ambassador.story")
        with self.assertRaisesRegex(ValueError, "4 missions to go"):
            self.state.issue_certificate("ambassador", "Ada Lovelace")
        self.assertIsNone(self.state.get_certificate("ambassador"))

    def test_a_certificate_needs_a_name(self):
        self.pass_track("ambassador")
        self.assertEqual(self.track("ambassador")["certificate"]["status"], "ready")
        with self.assertRaisesRegex(ValueError, "name"):
            self.state.issue_certificate("ambassador", "   ")

    def test_an_unknown_path_is_refused(self):
        with self.assertRaises(ValueError):
            self.state.issue_certificate("wizard", "Ada")

    def test_a_finished_path_issues_a_certificate_with_the_proof(self):
        self.pass_track("ambassador")
        cert = self.state.issue_certificate("ambassador", "Ada Lovelace")
        self.assertRegex(cert["number"], r"^FA-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$")
        self.assertTrue(cert["valid"])
        body = cert["body"]
        self.assertEqual(body["name"], "Ada Lovelace")
        self.assertEqual(body["path"], "Messenger")
        self.assertEqual([m["level"] for m in body["missions"]], ["Beginner", "Beginner", "Intermediate", "Advanced", "Capstone"])
        for item in body["missions"]:
            self.assertEqual(item["question_score"], 88)
            self.assertEqual(item["check_version"], self.curriculum.MISSIONS[item["mission_id"]]["version"])
            self.assertTrue(item["passed_at"])
            self.assertTrue(item["document"].endswith(".md"))
            self.assertEqual(len(item["fingerprint"]), 64)
        track = self.track("ambassador")
        self.assertEqual(track["certificate"]["status"], "issued")
        self.assertEqual(track["certificate"]["issued"]["number"], cert["number"])

    def test_the_certificate_never_carries_a_full_file_path_or_an_answer(self):
        self.pass_track("ambassador")
        cert = self.state.issue_certificate("ambassador", "Ada Lovelace")
        text = json.dumps(cert["body"])
        self.assertNotIn(self.tmp, text)
        self.assertNotIn("separate program from the app window", text)

    def test_claiming_twice_returns_the_same_certificate(self):
        self.pass_track("ambassador")
        first = self.state.issue_certificate("ambassador", "Ada Lovelace")
        second = self.state.issue_certificate("ambassador", "Someone Else")
        self.assertEqual(first["number"], second["number"])
        self.assertEqual(second["name"], "Ada Lovelace")

    def test_editing_a_certificate_breaks_its_number(self):
        self.pass_track("ambassador")
        body = dict(self.state.issue_certificate("ambassador", "Ada Lovelace")["body"])
        self.assertTrue(self.state.verify_certificate(body))
        body["name"] = "Mallory"
        self.assertFalse(self.state.verify_certificate(body))

    def test_saving_writes_a_readable_file_and_a_matching_json(self):
        self.pass_track("ambassador")
        cert = self.state.issue_certificate("ambassador", "Ada Lovelace")
        saved = self.state.save_certificate("ambassador")
        markdown = pathlib.Path(saved["markdown"]).read_text(encoding="utf-8")
        self.assertIn("# Field Record: Messenger path", markdown)
        self.assertIn("Kept by **Ada Lovelace**", markdown)
        self.assertIn(f"Record number: `{cert['number']}`", markdown)
        self.assertIn("Spot a real opportunity", markdown)
        self.assertIn("Self-issued with Field Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research.", markdown)
        self.assertNotIn("Awarded", markdown)
        self.assertNotIn("0.8.2 or earlier", markdown)
        self.assertTrue(saved["json"].endswith("field-academy-ambassador-field-record.json"))
        stored = json.loads(pathlib.Path(saved["json"]).read_text(encoding="utf-8"))
        self.assertTrue(self.state.verify_certificate(stored))
        self.assertTrue(saved["markdown"].startswith(self.tmp))

    def test_saving_before_claiming_is_refused(self):
        with self.assertRaises(ValueError):
            self.state.save_certificate("operator")

    # -- the other surfaces ----------------------------------------------------

    def test_the_academy_command_prints_the_map(self):
        self.pass_mission("operator.runtime")
        text = self.pkg._academy_command("")
        self.assertIn("Traveler: 1 of 5 passed, at Beginner. Field Record: 4 missions to go", text)
        self.assertIn("Messenger: 0 of 5 passed", text)
        self.assertIn("Next: Learn what the app keeps when you close it", text)

    def test_the_academy_command_shows_a_created_field_record(self):
        self.pass_track("ambassador")
        number = self.state.issue_certificate("ambassador", "Ada Lovelace")["number"]
        self.assertIn(f"Field Record: created, number {number}", self.pkg._academy_command(""))

    def test_the_mission_tool_carries_level_and_proof(self):
        tools = sys.modules[f"{self.pkg.__name__}.tools"]
        payload = json.loads(tools.field_academy_mission({"mission_id": "operator.automation"}))
        self.assertEqual(payload["level"], "Advanced")
        self.assertEqual(payload["minutes"], self.curriculum.MISSIONS["operator.automation"]["minutes"])
        self.assertIn("scheduled job", payload["proof"])

    # -- copy rules on everything a learner reads here -------------------------

    def learner_text(self):
        """(where, text) for every learner-facing string in the curriculum and the routes."""
        for track_id, track in self.curriculum.TRACKS.items():
            yield f"{track_id}.name", track["name"]
            yield f"{track_id}.promise", track["promise"]
            for level, meaning in track["level_meanings"].items():
                yield f"{track_id}.{level}", meaning
        for mission_id, mission in self.curriculum.MISSIONS.items():
            for field in ("title", "promise", "outcome"):
                yield f"{mission_id}.{field}", mission[field]
            for step in mission["steps"]:
                for field in ("title", "body", "proof", "route_label"):
                    if step.get(field):
                        yield f"{mission_id}.{step['id']}.{field}", step[field]
        route = self.track("operator")["certificate"]
        for index, step in enumerate(route["steps"]):
            yield f"route.step{index}.title", step["title"]
            yield f"route.step{index}.detail", step["detail"]
        for index, line in enumerate(route["receive"]):
            yield f"route.receive{index}", line
        yield "route.issuer", route["issuer"]
        yield "route.shows", route["shows"]

    def headings(self):
        for track in self.curriculum.TRACKS.values():
            yield track["name"]
        for mission in self.curriculum.MISSIONS.values():
            yield mission["title"]
            for step in mission["steps"]:
                yield step["title"]
        for step in self.track("operator")["certificate"]["steps"]:
            yield step["title"]

    def test_no_heading_ends_with_a_period(self):
        for heading in self.headings():
            self.assertFalse(heading.rstrip().endswith("."), heading)

    def test_no_negation_device_or_meta_narrative(self):
        banned = [
            (re.compile(r"\bnot [^.;]{1,60}, but\b", re.I), "not X, but Y"),
            (re.compile(r"\b(?:is|are|was|were) not (?:a|an|the) [a-z][^.]{0,60}[.,]"), "X is not Y"),
            (re.compile(r", not (?:a|an|the|just|only) ", re.I), "X, not Y"),
            (re.compile(r"window is not the machine", re.I), "flagged line"),
            (re.compile(r"closes only by", re.I), "flagged line"),
            (re.compile(r"asks you for nothing", re.I), "flagged line"),
            (re.compile(r"walk away with|end up with|field case", re.I), "robot label"),
            (re.compile(r"\b(?:gate|this check) (?:closes|records)\b", re.I), "the product narrating itself"),
        ]
        for where, text in self.learner_text():
            for pattern, name in banned:
                self.assertIsNone(pattern.search(text), f"{name} in {where}: {text}")

    def test_no_emoji_anywhere_a_learner_reads(self):
        emoji = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⭕]")
        for where, text in self.learner_text():
            self.assertIsNone(emoji.search(text), where)
        self.assertIsNone(emoji.search((ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")))
        self.assertIsNone(emoji.search((ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")))

    def test_steps_stay_short_enough_to_read(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            self.assertLessEqual(len(mission["promise"].split()), 30, mission_id)
            for step in mission["steps"]:
                if step["kind"] == "lesson":
                    self.assertLessEqual(len(step["body"].split()), 90, mission_id)
                elif step["kind"] in ("lab", "gate"):
                    self.assertLessEqual(len(step["body"].split()), 45, f"{mission_id}/{step['id']}")


class DesktopHalfTests(unittest.TestCase):
    """Static checks on the desktop half. The page itself renders in harness/.

    desktop/plugin.js is BUILT: esbuild bundles desktop/src/plugin.js with the shared hermes-ui-kit
    (`node ../hermes-ui-kit/scripts/build.mjs .`). Rules about what Hermes loads read the built file
    (`bundle`); checks about how the page is written read the source it is built from (`source`).
    esbuild prints string literals in double quotes, so the import check accepts either quote."""

    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")
        cls.bundle = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")

    def test_imports_only_the_sdk_and_react(self):
        modules = set(re.findall(r"^import [^;]*? from [\"']([^\"']+)[\"']", self.bundle, re.M))
        self.assertEqual(modules, {"@hermes/plugin-sdk", "react", "react/jsx-runtime"})
        source_modules = set(re.findall(r"^import [^;]*? from '([^']+)'", self.source, re.M))
        local = {m for m in source_modules if m.startswith("./")}
        self.assertEqual(source_modules - local, {"@hermes/plugin-sdk", "react", "react/jsx-runtime", "hermes-ui-kit"})
        # Field Academy's own helper modules sit beside plugin.js and are bundled in; they
        # import nothing beyond what plugin.js may, plus each other.
        for name in sorted(local):
            text = (ROOT / "desktop" / "src" / name[2:]).read_text(encoding="utf-8")
            imported = set(re.findall(r"^import [^;]*? from '([^']+)'", text, re.M))
            self.assertLessEqual({m for m in imported if not m.startswith("./")},
                                 {"@hermes/plugin-sdk", "react", "react/jsx-runtime", "hermes-ui-kit"}, name)

    def test_no_dimmed_text_tokens_and_no_undefined_colors(self):
        for token in ("--ui-text-secondary", "--ui-text-tertiary", "--ui-text-quaternary", "--ui-warning", "--ui-danger"):
            self.assertNotIn(token, self.source, token)
            self.assertNotIn(token, self.bundle, token)

    def test_the_page_opens_on_the_map(self):
        self.assertRegex(self.source, r"useState\(\(\) => readView\(\)\)")
        self.assertIn("function readView()", self.source)
        self.assertRegex(self.source, r"return \{ name: 'map' \}")

    def test_the_four_screens_exist(self):
        for name in ("function MapView", "function PathView", "function MissionView", "function CertificateView"):
            self.assertIn(name, self.source)

    def test_the_certificate_routes_exist_on_both_halves(self):
        api = (ROOT / "dashboard" / "plugin_api.py").read_text(encoding="utf-8")
        self.assertIn('@router.post("/certificate/{track_id}")', api)
        self.assertIn('@router.post("/certificate/{track_id}/save")', api)
        self.assertIn("`/certificate/${", self.source)

    def test_no_all_caps_labels(self):
        for literal in re.findall(r"children: '([^']+)'", self.source):
            letters = re.sub(r"[^A-Za-z]", "", literal)
            if len(letters) > 3:
                self.assertFalse(letters.isupper(), literal)

    def test_no_heading_ends_with_a_period(self):
        for literal in re.findall(r"jsx\('h[1-3]', \{[^}]*?children: '([^']+)'", self.source):
            self.assertFalse(literal.endswith("."), literal)


if __name__ == "__main__":
    unittest.main()
