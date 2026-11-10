-- Copied from hermes-agent v0.22.4 cron/executions.py _initialize_schema: the columns added after the CREATE TABLE
-- (add_column_if_missing), as plain ALTER TABLE statements.
ALTER TABLE executions ADD COLUMN delivery_outcome TEXT;
ALTER TABLE executions ADD COLUMN scheduled_instant TEXT;
ALTER TABLE executions ADD COLUMN progress_at TEXT;
