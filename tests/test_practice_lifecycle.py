"""The practice profile's life: plan, record, plant, use, remove. Field Academy writes only into what it made."""

from __future__ import annotations

import json
import os
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402


class Plan(FoundationsCase):
    def test_the_request_is_exactly_what_hermes_needs_and_nothing_more(self):
        planned = self.practice.plan()
        self.assertEqual(planned["name"], "academy-practice")
        self.assertEqual(planned["status"], "planned")
        request = planned["request"]
        self.assertEqual(request["method"], "profiles.create")
        params = request["params"]
        self.assertEqual(set(params), {"name", "description", "soul", "no_alias", "no_skills"})
        self.assertIs(params["no_alias"], True)
        self.assertIs(params["no_skills"], True)
        self.assertNotIn("clone_from", params, "never copy the learner's real config and memory")
        self.assertIn("Field Academy practice profile", params["soul"])

    def test_a_taken_name_moves_to_the_next_free_one(self):
        (self.root / "profiles" / "academy-practice").mkdir()
        self.assertEqual(self.practice.plan()["name"], "academy-practice-2")

    def test_the_second_profile_has_its_own_name(self):
        self.ready("a")
        self.assertEqual(self.practice.plan("b")["name"], "academy-practice-b")

    def test_a_second_main_profile_is_refused_while_one_is_set_up(self):
        self.ready("a")
        with self.assertRaises(ValueError):
            self.practice.plan("a")

    def test_planning_again_before_creating_replaces_the_plan(self):
        first = self.practice.plan()
        second = self.practice.plan()
        self.assertEqual(first["name"], second["name"])
        self.assertNotEqual(first["request"]["params"]["soul"], second["request"]["params"]["soul"])


class Record(FoundationsCase):
    def test_a_profile_made_as_planned_is_recorded_with_a_fingerprint(self):
        view = self.ready()
        self.assertEqual(view["status"], "ready")
        row = self.practice.record("academy-practice")
        prints = json.loads(row["fingerprint_json"])
        self.assertIn("SOUL.md", prints)
        self.assertEqual(prints[".env"][3], "", "a credential file is never hashed")
        self.assertEqual(prints["auth.json"][3], "")
        self.assertNotIn("state.db", prints, "Hermes's own runtime files are not the profile's content")

    def test_a_folder_that_was_there_before_the_plan_is_refused(self):
        planned = self.practice.plan()
        result = self.create_like_hermes(planned)
        row = self.practice.record("academy-practice")
        body = row["plan"]
        body["planned_epoch"] = body["planned_epoch"] + 3600
        with self.practice._conn() as conn:
            conn.execute("UPDATE f_practice SET plan_json = ? WHERE name = ?", (json.dumps(body), "academy-practice"))
        with self.assertRaisesRegex(ValueError, "before this plan"):
            self.practice.confirm("academy-practice", result)

    def test_different_instructions_mean_a_different_profile(self):
        planned = self.practice.plan()
        result = self.create_like_hermes(planned, soul="Someone else's bot.\n")
        with self.assertRaisesRegex(ValueError, "instructions"):
            self.practice.confirm("academy-practice", result)

    def test_windows_line_endings_in_soul_are_the_same_text(self):
        planned = self.practice.plan()
        result = self.create_like_hermes(planned, soul=planned["request"]["params"]["soul"].replace("\n", "\r\n"))
        self.assertEqual(self.practice.confirm("academy-practice", result)["status"], "ready")

    def test_a_hermes_bots_profile_is_refused(self):
        for marker in ("bot-blueprint.yaml", "profile.yaml"):
            with self.subTest(marker=marker):
                planned = self.practice.plan()
                result = self.create_like_hermes(planned)
                text = "catalog_entry:\n  name: x\n" if marker == "bot-blueprint.yaml" else "provenance:\n  kind: bot-catalog\n"
                (self.home() / marker).write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Hermes Bots"):
                    self.practice.confirm("academy-practice", result)
                self.gone("academy-practice")

    def test_a_path_hermes_reports_elsewhere_is_refused(self):
        planned = self.practice.plan()
        result = self.create_like_hermes(planned)
        result["path"] = str(pathlib.Path(self.tmp) / "elsewhere" / "academy-practice")
        with self.assertRaises(ValueError):
            self.practice.confirm("academy-practice", result)

    def test_no_model_is_noted_for_the_page_to_block_the_lab(self):
        planned = self.practice.plan()
        result = self.create_like_hermes(planned)
        result["mirrored"]["model_inherited"] = False
        self.assertIs(self.practice.confirm("academy-practice", result)["model_ok"], False)

    def test_a_profile_field_academy_did_not_plan_is_never_recorded(self):
        (self.root / "profiles" / "academy-practice").mkdir()
        with self.assertRaisesRegex(ValueError, "no plan"):
            self.practice.confirm("academy-practice", {})
        with self.assertRaises(ValueError):
            self.practice.confirm("work", {})


class Plant(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.ready()

    def changed(self, before):
        return self.practice.changed_files(self.home(), before)

    def test_write_approval_changes_one_config_line_and_nothing_else(self):
        before = self.practice.fingerprint(self.home())
        config_before = (self.home() / "config.yaml").read_text().splitlines()
        self.practice.plant("academy-practice", ["write_approval"], "seed-1")
        self.assertEqual(self.changed(before), ["config.yaml"])
        after = (self.home() / "config.yaml").read_text().splitlines()
        self.assertEqual([(a, b) for a, b in zip(config_before, after) if a != b], [("  write_approval: false", "  write_approval: true")])
        self.assertIs(self.hermes_read.config(self.home())["values"]["memory.write_approval"], True)

    def test_memory_full_fills_memory_to_just_under_the_limit(self):
        before = self.practice.fingerprint(self.home())
        self.practice.plant("academy-practice", ["memory_full"], "seed-1")
        self.assertEqual(self.changed(before), ["memories/MEMORY.md"])
        mem = self.hermes_read.memory(self.home())["memory"]
        self.assertLessEqual(mem["chars"], 2200 - 30)
        self.assertGreaterEqual(mem["chars"], 2200 - 180)

    def test_the_fill_follows_a_raised_limit(self):
        self.gone("academy-practice")
        with self.practice._conn() as conn:
            conn.execute("UPDATE f_practice SET status = 'removed' WHERE name = 'academy-practice'")
        planned = self.practice.plan()
        self.practice.confirm(planned["name"], self.create_like_hermes(planned, config=hf.CONFIG.replace("memory_char_limit: 2200", "memory_char_limit: 1500")))
        self.practice.plant(planned["name"], ["memory_full"], "seed-2")
        mem = self.hermes_read.memory(self.home(planned["name"]))["memory"]
        self.assertTrue(1500 - 180 <= mem["chars"] <= 1500 - 30)

    def test_different_seeds_fill_differently(self):
        self.practice.plant("academy-practice", ["memory_full"], "seed-1")
        first = self.hermes_read.memory(self.home())["memory"]["entries"]
        self.assertEqual(self.practice.planted("academy-practice")["memory_full"]["limit"], 2200)
        page = json.dumps(self.practice.listing())
        for hidden in ("planted", "memory_full", "filler", "filled_to"):
            self.assertNotIn(hidden, page, "the page never sees what was planted")
        rng_a = self.plants._rng("seed-1", "memory_full").random()
        rng_b = self.plants._rng("seed-2", "memory_full").random()
        self.assertNotEqual(rng_a, rng_b)
        self.assertTrue(first)

    def test_wrong_profile_needs_the_second_profile_and_writes_nothing(self):
        with self.assertRaisesRegex(ValueError, "academy-practice-b"):
            self.practice.plant("academy-practice", ["wrong_profile"], "seed-1")
        self.ready("b")
        before = self.practice.fingerprint(self.home())
        self.practice.plant("academy-practice", ["wrong_profile"], "seed-1", partner="academy-practice-b")
        self.assertEqual(self.changed(before), [])
        self.assertEqual(self.practice.planted("academy-practice")["wrong_profile"]["decoy"], "academy-practice-b")

    def test_two_plants_at_once(self):
        self.practice.plant("academy-practice", ["write_approval", "memory_full"], "seed-3")
        self.assertEqual(sorted(self.practice.planted("academy-practice")), ["memory_full", "write_approval"])

    def test_nothing_is_planted_after_the_first_chat(self):
        self.chat()
        with self.assertRaisesRegex(ValueError, "changed|chatted"):
            self.practice.plant("academy-practice", ["write_approval"], "seed-1")
        row = self.practice.record("academy-practice")
        with self.assertRaisesRegex(self.practice_write.Refused, "chatted"):
            self.practice_write.set_config(self.home(), row, {"memory.write_approval": True})

    def test_nothing_is_written_while_the_profile_backend_runs(self):
        (self.home() / "gateway.pid").write_text("4242")
        row = self.practice.record("academy-practice")
        with self.assertRaisesRegex(self.practice_write.Refused, "running"):
            self.practice_write.write_memory(self.home(), row, "memory", ["x"])

    def test_nothing_is_planted_in_a_profile_changed_since_it_was_recorded(self):
        (self.home() / "config.yaml").write_text(hf.CONFIG + "extra: 1\n")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.practice.plant("academy-practice", ["write_approval"], "seed-1")

    def test_planting_twice_is_refused(self):
        self.practice.plant("academy-practice", ["write_approval"], "seed-1")
        with self.assertRaises(ValueError):
            self.practice.plant("academy-practice", ["memory_full"], "seed-1")


class WriterRefusals(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.ready()
        self.row = self.practice.record("academy-practice")

    def test_only_named_keys_and_files(self):
        with self.assertRaisesRegex(self.practice_write.Refused, "never changes"):
            self.practice_write.set_config(self.home(), self.row, {"providers.openrouter.api_key": "x"})
        with self.assertRaisesRegex(self.practice_write.Refused, "never writes"):
            self.practice_write._target(self.home(), ".env")
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.write_memory(self.home(), self.row, "soul", ["x"])

    def test_a_profile_field_academy_did_not_record_is_refused(self):
        other = self.root / "profiles" / "work"
        other.mkdir()
        fake = dict(self.row, name="work", path=str(other))
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.set_config(other, fake, {"memory.write_approval": True})
        moved = dict(self.row, path=str(other))
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.set_config(self.home(), moved, {"memory.write_approval": True})
        unrecorded = dict(self.row, status="planned")
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.set_config(self.home(), unrecorded, {"memory.write_approval": True})

    @unittest.skipIf(os.name == "nt", "symbolic links need extra rights on Windows")
    def test_links_are_never_written_through(self):
        outside = pathlib.Path(self.tmp) / "outside.md"
        outside.write_text("keep me")
        (self.home() / "memories" / "MEMORY.md").symlink_to(outside)
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.write_memory(self.home(), self.row, "memory", ["x"])
        self.assertEqual(outside.read_text(), "keep me")


class DetectAndVerify(FoundationsCase):
    FACT = "Harbor Bakery uses QuickBooks Online"

    def setUp(self):
        super().setUp()
        self.ready()

    def details(self, kind):
        return self.practice.planted("academy-practice")[kind]

    def test_write_approval(self):
        self.practice.plant("academy-practice", ["write_approval"], "s")
        d = self.details("write_approval")
        self.assertFalse(self.plants.detect("write_approval", self.home(), d)["fired"])
        hf.stage_pending(self.home(), content=self.FACT)
        self.assertTrue(self.plants.detect("write_approval", self.home(), d)["fired"])
        self.assertFalse(self.plants.verify("write_approval", self.home(), d, self.FACT)["fixed"])
        # The learner approves the queued save: the line lands and the queue empties.
        for p in (self.home() / "pending" / "memory").glob("*.json"):
            p.unlink()
        hf.write_memory(self.home(), [self.FACT + "; the other five use Xero."], None)
        self.assertTrue(self.plants.verify("write_approval", self.home(), d, self.FACT)["fixed"])

    def test_memory_full(self):
        self.practice.plant("academy-practice", ["memory_full"], "s")
        d = self.details("memory_full")
        self.chat(user="Save to memory: " + self.FACT, tool=hf.memory_full_error())
        self.assertTrue(self.plants.detect("memory_full", self.home(), d)["fired"])
        self.assertFalse(self.plants.verify("memory_full", self.home(), d, self.FACT)["fixed"])
        entries = self.hermes_read.memory(self.home())["memory"]["entries"]
        hf.write_memory(self.home(), entries[2:] + [self.FACT], None)
        self.assertTrue(self.plants.verify("memory_full", self.home(), d, self.FACT)["fixed"])

    def test_wrong_profile(self):
        self.ready("b")
        self.practice.plant("academy-practice", ["wrong_profile"], "s", partner="academy-practice-b")
        d = self.details("wrong_profile")
        self.assertFalse(self.plants.detect("wrong_profile", self.home(), d)["fired"])
        hf.write_memory(self.home("academy-practice-b"), [self.FACT], None)
        self.assertTrue(self.plants.detect("wrong_profile", self.home(), d)["fired"])
        self.assertFalse(self.plants.verify("wrong_profile", self.home(), d, self.FACT)["fixed"])
        hf.write_memory(self.home(), [self.FACT], None)
        self.assertTrue(self.plants.verify("wrong_profile", self.home(), d, self.FACT)["fixed"])

    def test_every_kind_has_a_planter_a_detector_and_a_verifier(self):
        for kind in self.plants.KINDS:
            self.assertEqual(set(self.plants.REGISTRY[kind]), {"plant", "detect", "verify"})


class Remove(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.ready()

    def test_delete_needs_a_confirm_and_snapshots_the_evidence_first(self):
        with self.assertRaises(ValueError):
            self.practice.prepare_remove("academy-practice")
        hf.write_memory(self.home(), ["A fact worth keeping."], None)
        out = self.practice.prepare_remove("academy-practice", confirmed=True)
        snap = pathlib.Path(out["snapshot"])
        self.assertTrue(snap.resolve().is_relative_to(pathlib.Path(self.tmp).resolve()))
        self.assertNotIn(str(self.root), str(snap))
        body = snap.read_text()
        self.assertIn("A fact worth keeping.", body)
        self.assertNotIn(hf.fake_key(), body)
        self.assertEqual(out["delete"], "academy-practice")

    def test_it_is_marked_removed_only_once_the_folder_is_gone(self):
        self.practice.prepare_remove("academy-practice", confirmed=True)
        with self.assertRaisesRegex(ValueError, "still there"):
            self.practice.removed("academy-practice")
        self.gone("academy-practice")
        self.assertEqual(self.practice.removed("academy-practice")["status"], "removed")
        self.assertEqual(self.practice.plan()["name"], "academy-practice", "a removed name can be planned again")

    def test_a_profile_field_academy_did_not_make_is_never_offered_for_deletion(self):
        (self.root / "profiles" / "academy-practice-3").mkdir()
        for name in ("academy-practice-3", "work", "default"):
            with self.assertRaises(ValueError, msg=name):
                self.practice.prepare_remove(name, confirmed=True)


if __name__ == "__main__":
    unittest.main()


class WorkingFolder(FoundationsCase):
    """A chat opened with host.newChat(profile) works in the practice folder: terminal.cwd is set when it is recorded."""

    def test_recording_sets_terminal_cwd_to_the_practice_folder_and_nothing_else(self):
        planned = self.practice.plan()
        self.create_like_hermes(planned)
        before = (self.home() / "config.yaml").read_text()
        self.practice.confirm(planned["name"])
        yaml = self.mod("yaml_keys")
        written = yaml.parse((self.home() / "config.yaml").read_text())
        self.assertEqual(written["terminal"]["cwd"], str(self.home().resolve()))
        self.assertIn("terminal.cwd", self.hermes_read.config(self.home())["values"], "the reader lists the key")
        self.assertEqual(self.practice.changed_files(self.home(), json.loads(self.practice.record(planned["name"])["fingerprint_json"])), [],
                         "the fingerprint is taken after Field Academy's own write")
        self.assertEqual(yaml.parse(before).get("memory"), yaml.parse((self.home() / "config.yaml").read_text()).get("memory"))
        self.practice.plant(planned["name"], ["write_approval"], "seed-1")

    def test_the_working_folder_can_only_be_the_profile_itself(self):
        self.ready()
        row = self.practice.record("academy-practice")
        for elsewhere in (str(self.root), str(self.root / "profiles" / "work"), "/", "~"):
            with self.assertRaisesRegex(self.practice_write.Refused, "own folder"):
                self.practice_write.set_config(self.home(), row, {"terminal.cwd": elsewhere})
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.set_config(self.home(), row, {"terminal.cwd": True})
