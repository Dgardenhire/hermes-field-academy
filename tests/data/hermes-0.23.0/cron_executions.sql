-- Copied verbatim from hermes-agent v0.23.0 cron/executions.py _initialize_schema, with _STATUS_CHECK (line 40) filled in:
-- 0.23.0 adds the 'cancelled' and 'missed' statuses. The later columns are the same as 0.22.4's
-- (../hermes-0.22.4/cron_executions_columns.sql).
CREATE TABLE IF NOT EXISTS executions (
             id TEXT PRIMARY KEY,
             job_id TEXT NOT NULL,
             source TEXT NOT NULL,
             process_id TEXT NOT NULL,
             pid INTEGER NOT NULL,
             process_started_at INTEGER,
             status TEXT NOT NULL CHECK(status IN
               ('claimed','running','completed','failed','unknown','cancelled','missed')),
             handoff_pending INTEGER NOT NULL DEFAULT 0,
             handoff_started_at REAL,
             claimed_at TEXT NOT NULL,
             started_at TEXT,
             finished_at TEXT,
             error TEXT
           );
CREATE INDEX IF NOT EXISTS idx_executions_job_claimed ON executions(job_id, claimed_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_executions_status_claimed ON executions(status, claimed_at DESC, id DESC);
