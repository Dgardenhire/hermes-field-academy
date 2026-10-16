"""Moving a 0.4.0 database to 0.5.0 safely: back up first, add only, keep every pass."""

import json
import pathlib
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402

OLD_SCHEMA = (
    "CREATE TABLE evidence (id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL, step_id TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL DEFAULT 'artifact', summary TEXT NOT NULL DEFAULT '', artifact TEXT NOT NULL DEFAULT '', sha256 TEXT NOT NULL DEFAULT '', bytes INTEGER NOT NULL DEFAULT 0, session_id TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL)",
    "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE mission_steps (mission_id TEXT NOT NULL, step_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ready', note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL, PRIMARY KEY (mission_id, step_id))",
    "CREATE TABLE explanations (mission_id TEXT NOT NULL, step_id TEXT NOT NULL, answer TEXT NOT NULL DEFAULT '', score INTEGER, feedback TEXT NOT NULL DEFAULT '', attempts INTEGER NOT NULL DEFAULT 1, session_id TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, graded_at TEXT NOT NULL DEFAULT '', PRIMARY KEY (mission_id, step_id))",
    "CREATE TABLE certificates (track_id TEXT PRIMARY KEY, name TEXT NOT NULL, number TEXT NOT NULL, issued_at TEXT NOT NULL, body_json TEXT NOT NULL)",
    "CREATE TABLE opportunities (id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL, tool_name TEXT NOT NULL, session_id TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL)",
)
STAMP = "2026-09-20T10:00:00+00:00"


class MigrationCase(AcademyCase):
    def setUp(self):
        super().setUp()
        # Build a database exactly as 0.4.0 left it, before the package ever opens it.
        self.db = pathlib.Path(self.tmp) / "data.db"
        con = sqlite3.connect(self.db)
        for statement in OLD_SCHEMA:
            con.execute(statement)
        for step in ("concept", "lab_unknown", "explain", "gate"):
            pass
        old = {
            "operator.runtime": ("concept", "locate", "explain", "gate"),
            "operator.desktop": ("concept", "workflow", "explain", "gate"),
        }
        for mission_id, steps in old.items():
            for step_id in steps:
                con.execute("INSERT INTO mission_steps VALUES (?, ?, 'done', '', ?)", (mission_id, step_id, STAMP))
            con.execute(
                "INSERT INTO evidence(mission_id, step_id, kind, summary, created_at) VALUES (?, 'gate', 'check', 'Hermes is connected', ?)",
                (mission_id, STAMP),
            )
            con.execute("INSERT INTO explanations(mission_id, step_id, answer, score, feedback, created_at, graded_at) VALUES (?, 'explain', 'old answer', 84, 'ok', ?, ?)", (mission_id, STAMP, STAMP))
        con.execute("INSERT INTO mission_steps VALUES ('operator.learning', 'concept', 'done', '', ?)", (STAMP,))
        con.execute("INSERT INTO meta VALUES ('goal_track', 'operator')")
        con.commit()
        con.close()

    def tables(self):
        con = sqlite3.connect(self.db)
        try:
            return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        finally:
            con.close()


class BackupTests(MigrationCase):
    def test_the_database_is_copied_before_anything_changes(self):
        self.state.snapshot()
        backups = list((pathlib.Path(self.tmp) / "backups").glob("data-before-6-*.db"))
        self.assertEqual(len(backups), 1)
        con = sqlite3.connect(backups[0])
        try:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            self.assertNotIn("reviews", tables)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM mission_steps").fetchone()[0], 9)
        finally:
            con.close()

    def test_the_backup_is_taken_once_not_on_every_open(self):
        for _ in range(4):
            self.state.snapshot()
        self.assertEqual(len(list((pathlib.Path(self.tmp) / "backups").glob("*.db"))), 1)

    def test_a_fresh_install_has_nothing_to_back_up(self):
        fresh = pathlib.Path(self.tmp) / "fresh"
        fresh.mkdir()
        import os

        os.environ["FIELD_ACADEMY_DATA_DIR"] = str(fresh)
        self.state.snapshot()
        self.assertFalse((fresh / "backups").exists())
        os.environ["FIELD_ACADEMY_DATA_DIR"] = self.tmp


class AddOnlyTests(MigrationCase):
    def test_new_tables_and_columns_are_added(self):
        self.state.snapshot()
        self.assertTrue({"attempts", "reviews", "review_sessions", "completions", "placements", "mission_versions"} <= self.tables())
        columns = [r["name"] for r in self.rows("PRAGMA table_info(explanations)")]
        self.assertIn("ladder_json", columns)

    def test_no_old_row_is_lost_or_changed(self):
        before = self.rows("SELECT * FROM evidence ORDER BY id")
        self.state.snapshot()
        self.assertEqual(before, self.rows("SELECT * FROM evidence ORDER BY id"))
        self.assertEqual(self.rows("SELECT answer, score FROM explanations WHERE mission_id = 'operator.runtime'"), [{"answer": "old answer", "score": 84}])
        self.assertEqual(self.rows("SELECT value FROM meta WHERE key = 'goal_track'"), [{"value": "operator"}])

    def test_the_schema_version_is_recorded(self):
        self.state.snapshot()
        self.assertEqual(self.rows("SELECT value FROM meta WHERE key = 'schema_version'"), [{"value": "6"}])

    def test_opening_twice_does_not_migrate_twice(self):
        self.state.snapshot()
        first = self.rows("SELECT * FROM mission_steps ORDER BY mission_id, step_id")
        self.state.snapshot()
        self.assertEqual(first, self.rows("SELECT * FROM mission_steps ORDER BY mission_id, step_id"))

    def test_the_source_never_drops_or_deletes_whole_tables(self):
        text = (pathlib.Path(__file__).resolve().parents[1] / "store.py").read_text(encoding="utf-8").upper()
        for banned in ("DROP TABLE", "DELETE FROM", "RENAME TO", "RENAME COLUMN", "DROP COLUMN"):
            self.assertNotIn(banned, text)


class CarryOverTests(MigrationCase):
    def test_a_mission_passed_under_0_4_0_stays_passed(self):
        missions = {m["id"]: m for m in self.track("operator")["missions"]}
        self.assertEqual(missions["operator.runtime"]["status"], "verified")
        self.assertEqual(missions["operator.desktop"]["status"], "verified")

    def test_the_two_new_steps_are_carried_over_as_done(self):
        self.state.snapshot()
        steps = {s["id"]: s for s in self.mission("operator.runtime")["steps"]}
        self.assertEqual((steps["example"]["status"], steps["complete"]["status"]), ("done", "done"))
        self.assertEqual(steps["example"]["note"], "Carried over from 0.4.0")

    def test_a_half_finished_mission_does_not_get_free_steps(self):
        self.state.snapshot()
        steps = {s["id"]: s["status"] for s in self.mission("operator.learning")["steps"]}
        self.assertEqual(steps["concept"], "done")
        self.assertEqual(steps["example"], "ready")
        self.assertEqual(steps["complete"], "ready")

    def test_old_passes_are_recorded_as_version_1_and_flagged(self):
        self.state.snapshot()
        rows = self.rows("SELECT mission_id, passed_version, carried_over FROM mission_versions ORDER BY mission_id")
        self.assertEqual([(r["mission_id"], r["passed_version"], r["carried_over"]) for r in rows], [("operator.desktop", 1, 1), ("operator.runtime", 1, 1)])
        flagged = {c["mission_id"] for c in self.state.snapshot()["changes"]}
        self.assertEqual(flagged, {"operator.runtime", "operator.desktop"})
        self.assertTrue(all(c["carried_over"] for c in self.state.snapshot()["changes"]))

    def test_old_passes_enter_the_review_queue_spread_out_not_all_at_once(self):
        overview = self.state.review_overview()
        self.assertEqual(overview["passed_missions"], 2)
        self.assertEqual(overview["due_count"], 2)

    def test_many_old_passes_are_spread_three_a_day(self):
        con = sqlite3.connect(self.db)
        for mission_id in ("ambassador.story", "ambassador.qualify", "ambassador.handoff", "integrator.deploy"):
            con.execute("DELETE FROM mission_steps WHERE mission_id = ?", (mission_id,))
        con.close()
        # Pass four more under the old shape.
        con = sqlite3.connect(self.db)
        for mission_id, steps in {
            "ambassador.story": ("concept", "pitch", "explain", "gate"),
            "ambassador.qualify": ("concept", "roleplay", "explain", "gate"),
            "ambassador.handoff": ("concept", "rehearse", "explain", "gate"),
            "integrator.deploy": ("concept", "gateways", "explain", "gate"),
        }.items():
            for step_id in steps:
                con.execute("INSERT INTO mission_steps VALUES (?, ?, 'done', '', ?)", (mission_id, step_id, STAMP))
            con.execute("INSERT INTO evidence(mission_id, step_id, kind, summary, created_at) VALUES (?, 'gate', 'check', 'ok', ?)", (mission_id, STAMP))
        con.commit()
        con.close()
        overview = self.state.review_overview()
        self.assertEqual(overview["passed_missions"], 6)
        self.assertEqual(overview["due_count"], 3)
        self.assertTrue(overview["next_due_at"])

    def test_an_issued_certificate_survives_the_move(self):
        con = sqlite3.connect(self.db)
        body = {"certificate": "Field Academy certificate", "path_id": "operator", "name": "Ada"}
        body["number"] = "FA-AAAA-BBBB-CCCC"
        con.execute("INSERT INTO certificates VALUES ('operator', 'Ada', 'FA-AAAA-BBBB-CCCC', ?, ?)", (STAMP, json.dumps(body)))
        con.commit()
        con.close()
        track = self.track("operator")
        self.assertEqual(track["certificate"]["status"], "issued")
        self.assertEqual(track["certificate"]["issued"]["number"], "FA-AAAA-BBBB-CCCC")

    def test_the_orphan_cleanup_leaves_the_new_steps_alone(self):
        self.state.snapshot()
        self.assertEqual(self.state.purge_orphans(), {"missions": 0, "steps": 0})

    def test_a_learner_on_the_old_version_keeps_their_progress_numbers(self):
        track = self.track("operator")
        self.assertEqual(track["verified_missions"], 2)


if __name__ == "__main__":
    unittest.main()
