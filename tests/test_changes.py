"""After the certificate: what changed since you learned this, and re-verifying."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402

M = "operator.runtime"


class VersionTests(AcademyCase):
    def test_every_mission_has_a_version_and_a_changelog_entry(self):
        for mission_id, mission in self.curriculum.MISSIONS.items():
            self.assertGreaterEqual(mission["version"], 1, mission_id)
            self.assertTrue([r for r in self.curriculum.REVISIONS if r["mission_id"] == mission_id], mission_id)

    def test_the_changelog_is_a_versioned_list_in_plain_words(self):
        for entry in self.curriculum.REVISIONS:
            for key in ("id", "mission_id", "version", "kind", "released", "date", "summary"):
                self.assertTrue(entry[key], entry)
            self.assertIn(entry["kind"], ("check", "content", "added"))
            self.assertGreater(len(entry["summary"].split()), 8, entry["id"])

    def test_the_old_missions_changed_their_check_in_this_version(self):
        # Missions added after 0.4.0 carry an "added" revision and have no old check to change.
        added = {r["mission_id"] for r in self.curriculum.REVISIONS if r["kind"] == "added"}
        old = [m for m in self.curriculum.MISSIONS if not m.endswith(".capstone") and m not in added]
        self.assertEqual(len(old), 15)
        for mission_id in old:
            kinds = [r["kind"] for r in self.curriculum.REVISIONS if r["mission_id"] == mission_id]
            self.assertIn("check", kinds, mission_id)
            self.assertGreaterEqual(self.curriculum.MISSIONS[mission_id]["version"], 2, mission_id)

    def test_the_firsthand_mission_is_added_and_opens_the_messenger_path(self):
        entries = [r for r in self.curriculum.REVISIONS if r["mission_id"] == "ambassador.firsthand"]
        self.assertEqual([(r["kind"], r["version"], r["released"]) for r in entries], [("added", 1, "0.8.0")])
        first = self.curriculum.TRACKS["ambassador"]["missions"][0]
        self.assertEqual((first["id"], first["level"]), ("ambassador.firsthand", "beginner"))
        self.assertTrue(self.curriculum.MISSIONS["ambassador.firsthand"]["story_first"])

    def test_the_capstones_are_added_not_changed(self):
        for track_id in self.curriculum.TRACKS:
            kinds = [r["kind"] for r in self.curriculum.REVISIONS if r["mission_id"] == f"{track_id}.capstone"]
            self.assertEqual(kinds, ["added"])

    def test_revisions_since_lists_only_newer_versions(self):
        current = self.curriculum.MISSIONS[M]["version"]
        self.assertEqual(len(self.curriculum.revisions_since(M, 1)), current - 1)
        self.assertEqual(self.curriculum.revisions_since(M, current), [])

    def test_a_pass_records_the_version_it_was_made_at(self):
        self.pass_mission(M)
        self.assertEqual(self.rows("SELECT passed_version, carried_over FROM mission_versions"), [{"passed_version": self.curriculum.MISSIONS[M]["version"], "carried_over": 0}])

    def test_a_current_pass_has_nothing_to_re_verify(self):
        self.pass_mission(M)
        self.assertEqual(self.state.snapshot()["changes"], [])


class ChangedSinceTests(AcademyCase):
    def passed_long_ago(self):
        self.pass_mission(M)
        with self.state._connection() as conn:
            conn.execute("UPDATE mission_versions SET passed_version = 1 WHERE mission_id = ?", (M,))

    def test_a_mission_passed_at_an_older_version_is_flagged(self):
        self.passed_long_ago()
        changes = self.state.snapshot()["changes"]
        self.assertEqual([c["mission_id"] for c in changes], [M])
        self.assertEqual((changes[0]["passed_version"], changes[0]["version"]), (1, self.curriculum.MISSIONS[M]["version"]))

    def test_the_flag_says_what_changed_in_words(self):
        self.passed_long_ago()
        change = self.state.changes()[0]
        self.assertIn("profile name", change["revisions"][0]["summary"])
        self.assertEqual(change["needs"], "check")

    def test_the_flagged_mission_is_marked_on_the_map(self):
        self.passed_long_ago()
        mission = next(m for m in self.track("operator")["missions"] if m["id"] == M)
        self.assertTrue(mission["changed"])
        self.assertEqual(mission["status"], "verified")

    def test_an_unpassed_mission_is_never_flagged(self):
        self.assertEqual(self.state.snapshot()["changes"], [])

    def test_a_mission_in_progress_is_not_flagged(self):
        self.state.update_step(M, "concept", "done")
        self.assertEqual(self.state.changes(), [])

    def test_the_pass_stays_a_pass(self):
        self.passed_long_ago()
        self.assertEqual(self.mission(M)["status"], "verified")

    def test_re_verifying_marks_the_request_and_keeps_the_pass(self):
        self.passed_long_ago()
        mission = self.state.reverify(M)
        self.assertTrue(mission["reverify"])
        self.assertEqual(mission["status"], "verified")
        self.assertTrue(self.state.changes()[0]["reverify_requested"])

    def test_a_mission_that_was_never_passed_cannot_be_re_verified(self):
        with self.assertRaisesRegex(ValueError, "Pass the mission first"):
            self.state.reverify(M)

    def test_passing_the_new_check_clears_the_flag(self):
        self.passed_long_ago()
        self.state.reverify(M)
        self.state.record_gate(M, "gate", {"passed": True, "title": "ok", "detail": "ok", "facts": []})
        self.assertEqual(self.state.changes(), [])
        self.assertFalse(self.mission(M)["reverify"])
        self.assertEqual(self.rows("SELECT passed_version FROM mission_versions")[0]["passed_version"], self.curriculum.MISSIONS[M]["version"])

    def test_missing_the_new_check_leaves_the_mission_passed_and_flagged(self):
        self.passed_long_ago()
        outcome = {"passed": False, "title": "That doesn't match yet", "detail": "x", "facts": [], "missing": [{"id": "profile_mismatch", "what": "x"}]}
        self.state.record_gate(M, "gate", outcome)
        self.assertEqual(self.mission(M)["status"], "verified")
        self.assertEqual(len(self.state.changes()), 1)
        self.assertEqual(self.passport_step(M, "gate")["feedback"]["level"], 1)

    def test_a_change_to_the_check_cannot_be_dismissed_without_the_check(self):
        self.passed_long_ago()
        with self.assertRaisesRegex(ValueError, "Run the check again"):
            self.state.acknowledge_changes(M)

    def test_a_change_to_the_lesson_can_be_marked_as_read(self):
        self.passed_long_ago()
        current = self.curriculum.MISSIONS[M]["version"]
        extra = {"id": f"{M}@{current + 1}", "mission_id": M, "version": current + 1, "kind": "content", "released": "9.9.9", "date": "2099-01-01", "summary": "The lesson now says where the gateway keeps its log."}
        self.curriculum.REVISIONS[:] = self.curriculum.REVISIONS + [extra]
        self.curriculum.MISSIONS[M]["version"] = current + 1
        with self.state._connection() as conn:
            conn.execute("UPDATE mission_versions SET passed_version = ? WHERE mission_id = ?", (current, M))
        change = self.state.changes()[0]
        self.assertEqual(change["needs"], "read")
        self.assertEqual(self.state.acknowledge_changes(M), [])

    def test_a_certificate_stays_valid_when_a_mission_changes(self):
        self.pass_track("ambassador")
        cert = self.state.issue_certificate("ambassador", "Ada Lovelace")
        with self.state._connection() as conn:
            conn.execute("UPDATE mission_versions SET passed_version = 1")
        self.assertTrue(self.state.get_certificate("ambassador")["valid"])
        self.assertEqual(self.state.get_certificate("ambassador")["number"], cert["number"])
        self.assertEqual(len(self.state.changes()), 3)

    def test_the_certificate_records_which_check_version_each_mission_passed(self):
        self.pass_track("ambassador")
        body = self.state.issue_certificate("ambassador", "Ada Lovelace")["body"]
        self.assertEqual({m["check_version"] for m in body["missions"]}, {2, 1})


class NewMissionTests(AcademyCase):
    def test_a_path_you_started_offers_its_new_capstone(self):
        self.pass_mission("operator.runtime")
        added = self.state.snapshot()["new_missions"]
        self.assertIn("operator.capstone", [m["mission_id"] for m in added])

    def test_a_path_you_never_started_does_not_nag(self):
        self.pass_mission("operator.runtime")
        ids = [m["mission_id"] for m in self.state.snapshot()["new_missions"]]
        self.assertNotIn("architect.capstone", ids)

    def test_a_path_with_an_earned_certificate_before_the_capstone_keeps_it(self):
        self.pass_track("ambassador")
        self.state.issue_certificate("ambassador", "Ada Lovelace")
        track = self.track("ambassador")
        self.assertEqual(track["certificate"]["status"], "issued")


if __name__ == "__main__":
    unittest.main()
