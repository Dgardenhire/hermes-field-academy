"""Schema 7 adds the Foundations tables to a 0.8.5 database (schema 6) and changes nothing that was there.

The new evidence tables are append-only, enforced by SQLite triggers inside Field Academy's own database: an UPDATE
or DELETE is refused by the database itself, whatever code asks.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402

STAMP = "2026-10-01T10:00:00+00:00"
F_TABLES = ("f_attempts", "f_entries", "f_checks", "f_evidence", "f_record", "f_practice", "f_issued")
APPEND_ONLY = ("f_entries", "f_checks", "f_evidence", "f_record", "f_issued")


class FromSix(AcademyCase):
    def setUp(self):
        super().setUp()
        self.db = pathlib.Path(self.tmp) / "data.db"
        con = sqlite3.connect(self.db)
        for statement in self.store.TABLES:
            if not any(f"EXISTS {name} " in statement or f"EXISTS {name}(" in statement for name in F_TABLES) and "TRIGGER" not in statement:
                con.execute(statement)
        con.execute("ALTER TABLE explanations ADD COLUMN ladder_json TEXT NOT NULL DEFAULT ''")
        con.execute("INSERT INTO meta VALUES ('schema_version', '6')")
        con.execute("INSERT INTO meta VALUES ('goal_track', 'operator')")
        for step in ("concept", "example", "complete", "locate", "explain", "gate"):
            con.execute("INSERT INTO mission_steps VALUES ('operator.runtime', ?, 'done', '', ?)", (step, STAMP))
        con.execute("INSERT INTO evidence(mission_id, step_id, kind, summary, created_at) VALUES ('operator.runtime', 'gate', 'check', 'ok', ?)", (STAMP,))
        con.execute("INSERT INTO explanations(mission_id, step_id, answer, score, feedback, created_at, graded_at) VALUES ('operator.runtime', 'explain', 'old answer', 84, 'ok', ?, ?)", (STAMP, STAMP))
        old = {"certificate": "Field Academy certificate", "path_id": "operator", "name": "Ada", "number": "FA-AAAA-BBBB-CCCC"}
        new = {"record": "Field Academy Field Record", "record_format": 2, "path_id": "ambassador", "name": "Ada", "number": "FA-DDDD-EEEE-FFFF"}
        con.execute("INSERT INTO certificates VALUES ('operator', 'Ada', 'FA-AAAA-BBBB-CCCC', ?, ?)", (STAMP, json.dumps(old)))
        con.execute("INSERT INTO certificates VALUES ('ambassador', 'Ada', 'FA-DDDD-EEEE-FFFF', ?, ?)", (STAMP, json.dumps(new)))
        con.execute("INSERT INTO deployer_items(item_id, status, score, detail_json, updated_at) VALUES ('brief', 'passed', 88, '{\"a\": 1}', ?)", (STAMP,))
        con.execute("INSERT INTO deployer_samples(item_id, taken_at, source, times_json) VALUES ('deploy', ?, 'hermes files', '[]')", (STAMP,))
        con.commit()
        con.close()
        self.before = self.dump()

    def dump(self):
        con = sqlite3.connect(self.db)
        try:
            names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            return {name: con.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall() for name in names if not name.startswith("f_")}
        finally:
            con.close()

    def open(self):
        return self.store.connect()

    def test_every_old_row_is_byte_for_byte_the_same(self):
        self.open().close()
        after = self.dump()
        for table, rows in self.before.items():
            if table == "meta":
                continue
            self.assertEqual(after[table], rows, table)
        meta_after = dict(r for r in after["meta"])
        self.assertEqual(meta_after["goal_track"], "operator")
        self.assertEqual(meta_after["schema_version"], "7")

    def test_the_new_tables_are_there_and_empty(self):
        conn = self.open()
        try:
            for name in F_TABLES:
                self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0], 0, name)
        finally:
            conn.close()

    def test_a_backup_is_taken_before_the_move(self):
        self.open().close()
        backups = list((pathlib.Path(self.tmp) / "backups").glob("data-before-7-*.db"))
        self.assertEqual(len(backups), 1)
        con = sqlite3.connect(backups[0])
        try:
            names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        finally:
            con.close()
        self.assertFalse(names & set(F_TABLES))

    def test_old_records_still_render(self):
        self.assertEqual(self.track("operator")["certificate"]["status"], "issued")
        self.assertEqual(self.track("operator")["certificate"]["issued"]["number"], "FA-AAAA-BBBB-CCCC")

    def test_opening_again_changes_nothing(self):
        self.open().close()
        first = self.dump()
        self.open().close()
        self.assertEqual(first, self.dump())


class AppendOnly(AcademyCase):
    def conn(self):
        return self.store.connect()

    def test_updates_and_deletes_are_refused_by_the_database(self):
        conn = self.conn()
        try:
            conn.execute("INSERT INTO f_attempts(mission_id, attempt_no, level, seed, plants_json, started_at) VALUES ('f.x', 1, 'beginner', 'ab', '[]', ?)", (STAMP,))
            conn.execute("INSERT INTO f_entries(attempt_id, kind, body_json, created_at, prev_hash, hash) VALUES (1, 'recall', '{}', ?, '', 'h1')", (STAMP,))
            conn.execute("INSERT INTO f_checks(attempt_id, check_id, phase, passed, source, facts_json, created_at) VALUES (1, 'c', 'first', 1, 'practice_profile', '[]', ?)", (STAMP,))
            conn.execute("INSERT INTO f_evidence(attempt_id, check_id, kind, rel_path, excerpt, excerpt_sha256, source_sha256, read_at) VALUES (1, 'c', 'memory', 'memories/MEMORY.md', 'x', 'e', 's', ?)", (STAMP,))
            conn.execute("INSERT INTO f_record(attempt_id, mission_id, body_json, hash, prev_hash, created_at) VALUES (1, 'f.x', '{}', 'r1', '', ?)", (STAMP,))
            conn.execute("INSERT INTO f_issued(number, issued_at, body_json, folder) VALUES ('FA-1', ?, '{}', '')", (STAMP,))
            conn.commit()
            for table in APPEND_ONLY:
                with self.assertRaises(sqlite3.DatabaseError, msg=f"update {table}"):
                    conn.execute(f"UPDATE {table} SET id = id")
                with self.assertRaises(sqlite3.DatabaseError, msg=f"delete {table}"):
                    conn.execute(f"DELETE FROM {table}")
                self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 1)
        finally:
            conn.close()

    def test_an_attempts_seed_plants_and_freeze_time_never_change_once_set(self):
        conn = self.conn()
        try:
            conn.execute("INSERT INTO f_attempts(mission_id, attempt_no, level, seed, plants_json, started_at) VALUES ('f.x', 1, 'beginner', 'ab', '[\"memory_full\"]', ?)", (STAMP,))
            for column, value in (("seed", "cd"), ("plants_json", "[]"), ("mission_id", "f.y"), ("attempt_no", 2), ("level", "advanced")):
                with self.assertRaises(sqlite3.DatabaseError, msg=column):
                    conn.execute(f"UPDATE f_attempts SET {column} = ? WHERE id = 1", (value,))
            conn.execute("UPDATE f_attempts SET frozen_at = ?, status = 'lab' WHERE id = 1", (STAMP,))
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE f_attempts SET frozen_at = '2027-01-01' WHERE id = 1")
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM f_attempts")
            conn.execute("UPDATE f_attempts SET finished_at = ?, status = 'done' WHERE id = 1", (STAMP,))
        finally:
            conn.close()

    def test_a_check_phase_and_source_must_be_known(self):
        conn = self.conn()
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO f_checks(attempt_id, check_id, phase, passed, source, facts_json, created_at) VALUES (1, 'c', 'later', 1, 'practice_profile', '[]', ?)", (STAMP,))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO f_checks(attempt_id, check_id, phase, passed, source, facts_json, created_at) VALUES (1, 'c', 'first', 1, 'the learner', '[]', ?)", (STAMP,))
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
