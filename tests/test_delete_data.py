"""Delete my progress keeps saved Field Records; Delete everything removes them; both keep the two switches and refuse
while a practice profile is still set up."""

from __future__ import annotations

import importlib
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402


class DeleteData(AcademyCase):
    def setUp(self):
        super().setUp()
        self.forget = importlib.import_module(f"{self.name}.forget")
        self.root = pathlib.Path(self.tmp)
        self.state.set_ai_settings(ai_help=False)
        with self.store.connect() as conn:
            conn.execute("INSERT INTO meta(key, value) VALUES('use_goal', 'Run my shop')")
            conn.execute("INSERT INTO f_issued(number, issued_at, body_json, folder) VALUES('FR-1', '2026-11-11', '{}', '')")
            conn.execute("INSERT INTO f_record(attempt_id, mission_id, body_json, hash, created_at) VALUES(1, 'm', '{}', 'h', 'now')")
            conn.commit()
        for name in ("field-records/foundations-1/MANIFEST.sha256", "labs/x/a.txt", "guide-cache/c.json", "backups/data-old.db"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x")
        (self.root / "ai-usage.jsonl").write_text("{}\n")

    def count(self, table):
        with self.store.connect() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def test_progress_goes_and_records_stay(self):
        out = self.forget.delete_data(True)
        self.assertTrue(out["kept_records"])
        self.assertEqual(self.count("f_issued"), 1)
        self.assertEqual(self.count("f_record"), 0)
        self.assertTrue((self.root / "field-records/foundations-1/MANIFEST.sha256").exists())
        for gone in ("labs", "guide-cache", "backups", "ai-usage.jsonl"):
            self.assertFalse((self.root / gone).exists(), gone)
        self.assertEqual(self.state.ai_settings()["ai_help"], False)
        with self.store.connect() as conn:
            self.assertIsNone(conn.execute("SELECT value FROM meta WHERE key = 'use_goal'").fetchone())

    def test_everything_goes(self):
        self.forget.delete_data(False)
        self.assertEqual(self.count("f_issued"), 0)
        self.assertFalse((self.root / "field-records").exists())
        self.assertTrue((self.root / "data.db").exists())
        self.assertEqual(self.state.ai_settings()["ai_help"], False)

    def test_append_only_still_holds_after(self):
        self.forget.delete_data(False)
        with self.store.connect() as conn:
            conn.execute("INSERT INTO f_record(attempt_id, mission_id, body_json, hash, created_at) VALUES(1, 'm', '{}', 'h', 'now')")
            conn.commit()
            with self.assertRaises(Exception):
                conn.execute("DELETE FROM f_record")

    def test_refuses_while_a_practice_profile_is_set_up(self):
        with self.store.connect() as conn:
            conn.execute("INSERT INTO f_practice(name, path, created_at, status) VALUES('academy-practice', '', 'now', 'planted')")
            conn.commit()
        with self.assertRaisesRegex(ValueError, "academy-practice"):
            self.forget.delete_data(True)
        self.assertEqual(self.count("f_record"), 1)

    def test_only_a_real_choice(self):
        with self.assertRaises(ValueError):
            self.forget.delete_data("yes")


if __name__ == "__main__":
    unittest.main()
