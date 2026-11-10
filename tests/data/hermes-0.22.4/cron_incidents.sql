-- Copied verbatim from hermes-agent v0.22.4 cron/incidents.py _initialize_schema.
CREATE TABLE IF NOT EXISTS cron_incidents (
             id            TEXT PRIMARY KEY,
             job_id        TEXT NOT NULL,
             error_sig     TEXT NOT NULL,
             state         TEXT NOT NULL,
             failure_type  TEXT NOT NULL DEFAULT 'unknown',
             first_seen_at TEXT NOT NULL,
             last_seen_at  TEXT NOT NULL,
             acked_at      TEXT,
             alerted_at    TEXT,
             closed_at     TEXT,
             error         TEXT NOT NULL,
             output_file   TEXT
           );
