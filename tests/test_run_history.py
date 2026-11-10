"""The Guide's run-history reader knows Hermes 0.22.4's executions table, and still scans any other layout."""

from __future__ import annotations

import pathlib
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from test_scrub import load  # noqa: E402

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


class SchemaAware(unittest.TestCase):
    def setUp(self):
        self.evidence = load("evidence")
        self.home = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def build(self, rows, jobs=None):
        hf.write_jobs(self.home, jobs if jobs is not None else [hf.job("job-a1", "Morning brief"), hf.job("job-b2", "Other job")])
        hf.executions_db(self.home, rows=rows, incidents=[{"job_id": "job-a1", "error": "provider 401 Morning brief"}])

    def test_completed_and_failed_runs_are_read_by_job_id_from_jobs_json(self):
        self.build([
            {"job_id": "job-a1", "status": "completed", "started_at": "2026-10-19T09:00:00+00:00", "finished_at": "2026-10-19T09:00:40+00:00"},
            {"job_id": "job-a1", "status": "failed", "started_at": "2026-10-20T09:00:00+00:00", "finished_at": "2026-10-20T09:00:05+00:00", "error": "401"},
            {"job_id": "job-a1", "status": "running", "started_at": "2026-10-21T09:00:00+00:00"},
            {"job_id": "job-b2", "status": "completed", "started_at": "2026-10-19T10:00:00+00:00", "finished_at": "2026-10-19T10:00:30+00:00"},
        ])
        out = self.evidence.read_run_history(self.home, "Morning brief", NOW)
        self.assertEqual(out["schema"], "executions")
        self.assertEqual(out["times"], ["2026-10-19T09:00:40Z"], "a finished run is dated by when it finished; a running one is not a run yet")
        self.assertEqual(out["failed"], ["2026-10-20T09:00:05Z"])
        self.assertTrue(out["found"])
        self.assertEqual(out["tables"], ["executions"])

    def test_an_incident_is_not_counted_again_as_a_run(self):
        self.build([{"job_id": "job-a1", "status": "completed", "started_at": "2026-10-19T09:00:00+00:00", "finished_at": "2026-10-19T09:00:40+00:00"}])
        out = self.evidence.read_run_history(self.home, "Morning brief", NOW)
        self.assertEqual(out["failed"], [])

    def test_the_job_can_be_named_by_its_id(self):
        self.build([{"job_id": "job-b2", "status": "completed", "started_at": "2026-10-19T10:00:00+00:00", "finished_at": "2026-10-19T10:00:30+00:00"}])
        self.assertEqual(self.evidence.read_run_history(self.home, "job-b2", NOW)["times"], ["2026-10-19T10:00:30Z"])

    def test_a_run_with_no_finish_time_falls_back_to_its_start(self):
        self.build([{"job_id": "job-a1", "status": "completed", "started_at": "2026-10-19T09:00:00+00:00"}])
        self.assertEqual(self.evidence.read_run_history(self.home, "Morning brief", NOW)["times"], ["2026-10-19T09:00:00Z"])

    def test_an_unknown_layout_is_still_scanned(self):
        (self.home / "cron").mkdir(parents=True)
        hf.write_jobs(self.home, [hf.job("job-a1", "Morning brief")])
        con = sqlite3.connect(self.home / "cron" / "executions.db")
        con.execute("CREATE TABLE runs (id INTEGER PRIMARY KEY, job TEXT, at TEXT, outcome TEXT)")
        con.execute("INSERT INTO runs(job, at, outcome) VALUES ('job-a1', '2026-10-19T09:00:00Z', 'ok')")
        con.execute("INSERT INTO runs(job, at, outcome) VALUES ('job-a1', '2026-10-20T09:00:00Z', 'failed')")
        con.commit()
        con.close()
        out = self.evidence.read_run_history(self.home, "Morning brief", NOW)
        self.assertEqual(out["schema"], "scan")
        self.assertEqual(out["times"], ["2026-10-19T09:00:00Z"])
        self.assertEqual(out["failed"], ["2026-10-20T09:00:00Z"])

    def test_nothing_there_says_so(self):
        out = self.evidence.read_run_history(self.home, "Morning brief", NOW)
        self.assertFalse(out["found"])
        self.assertEqual(out["schema"], "")


if __name__ == "__main__":
    unittest.main()
