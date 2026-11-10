"""The plugin's SQLite database: connection, schema, backup and migration.

Rules this file keeps, because a learner's progress is the one thing here that
can't be rebuilt:

* Tables are made with CREATE TABLE IF NOT EXISTS and columns are added with
  ALTER TABLE ADD COLUMN. Nothing is dropped, renamed or rewritten in place.
* Before the first migration from an older version, the whole database is
  copied to a ``backups`` folder beside it, using SQLite's own backup call so
  the copy is consistent.
* A migration only adds rows. Missions a learner already passed stay passed.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_ID = "field-academy"
SCHEMA_VERSION = 7


def clock() -> datetime:
    """Now. Tests replace this to move time without waiting."""
    return datetime.now(timezone.utc)


def now() -> str:
    return clock().isoformat()


TABLES = (
    """CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    step_id TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL DEFAULT 'artifact',
    summary TEXT NOT NULL DEFAULT '',
    artifact TEXT NOT NULL DEFAULT '',
    sha256 TEXT NOT NULL DEFAULT '',
    bytes INTEGER NOT NULL DEFAULT 0,
    session_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS mission_steps (
    mission_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ready',
    note TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (mission_id, step_id)
)""",
    """CREATE TABLE IF NOT EXISTS explanations (
    mission_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    answer TEXT NOT NULL DEFAULT '',
    score INTEGER,
    feedback TEXT NOT NULL DEFAULT '',
    attempts INTEGER NOT NULL DEFAULT 1,
    session_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    graded_at TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (mission_id, step_id)
)""",
    """CREATE TABLE IF NOT EXISTS certificates (
    track_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    number TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    body_json TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    session_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
)""",
    # 0.5.0 -----------------------------------------------------------------
    # Misses in a row on a step, and the last feedback shown, so the hint ladder
    # survives a restart.
    """CREATE TABLE IF NOT EXISTS attempts (
    mission_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    misses INTEGER NOT NULL DEFAULT 0,
    last_feedback_json TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (mission_id, step_id)
)""",
    # One row per passed mission: where it sits on the review ladder.
    """CREATE TABLE IF NOT EXISTS reviews (
    mission_id TEXT PRIMARY KEY,
    stage INTEGER NOT NULL DEFAULT 0,
    interval_days REAL NOT NULL DEFAULT 2,
    due_at TEXT NOT NULL,
    strength INTEGER,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    consecutive_misses INTEGER NOT NULL DEFAULT 0,
    last_item TEXT NOT NULL DEFAULT '',
    last_score INTEGER,
    last_reviewed_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS review_sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    practice INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'open',
    items_json TEXT NOT NULL,
    answers_json TEXT NOT NULL DEFAULT '{}',
    results_json TEXT NOT NULL DEFAULT '',
    submitted_at TEXT NOT NULL DEFAULT '',
    graded_at TEXT NOT NULL DEFAULT ''
)""",
    # What the learner typed into the gaps of a half-finished example.
    """CREATE TABLE IF NOT EXISTS completions (
    mission_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    answers_json TEXT NOT NULL DEFAULT '{}',
    revealed INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (mission_id, step_id)
)""",
    """CREATE TABLE IF NOT EXISTS placements (
    track_id TEXT PRIMARY KEY,
    taken_at TEXT NOT NULL,
    answers_json TEXT NOT NULL DEFAULT '{}',
    results_json TEXT NOT NULL DEFAULT '',
    applied_json TEXT NOT NULL DEFAULT ''
)""",
    # The version of a mission's content that the learner passed.
    """CREATE TABLE IF NOT EXISTS mission_versions (
    mission_id TEXT PRIMARY KEY,
    passed_version INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    carried_over INTEGER NOT NULL DEFAULT 0
)""",
    # 0.6.0, the Deployer tier ------------------------------------------------
    # One row per lab and seed. The folder path is the learner's disposable
    # client machine under this plugin's own data folder.
    """CREATE TABLE IF NOT EXISTS deployer_labs (
    lab_id TEXT NOT NULL,
    seed INTEGER NOT NULL,
    folder TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    attempts INTEGER NOT NULL DEFAULT 0,
    diagnosis TEXT NOT NULL DEFAULT '',
    last_result_json TEXT NOT NULL DEFAULT '',
    tree_fingerprint TEXT NOT NULL DEFAULT '',
    changed_json TEXT NOT NULL DEFAULT '',
    passed_at TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (lab_id, seed)
)""",
    # Everything else in the tier: the brief, scenarios, the deployment, drills,
    # the walkthrough and the review. detail_json holds that item's own record.
    """CREATE TABLE IF NOT EXISTS deployer_items (
    item_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'open',
    score INTEGER,
    detail_json TEXT NOT NULL DEFAULT '{}',
    fingerprint TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    passed_at TEXT NOT NULL DEFAULT ''
)""",
    # A written answer to a scenario or the brief, and the score the learner's own Hermes gave it.
    """CREATE TABLE IF NOT EXISTS deployer_answers (
    item_id TEXT PRIMARY KEY,
    answer TEXT NOT NULL DEFAULT '',
    score INTEGER,
    feedback TEXT NOT NULL DEFAULT '',
    attempts INTEGER NOT NULL DEFAULT 1,
    ladder_json TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    graded_at TEXT NOT NULL DEFAULT ''
)""",
    # Misses in a row on any item in the tier, and the last feedback, so the hint ladder survives a restart.
    """CREATE TABLE IF NOT EXISTS deployer_attempts (
    item_id TEXT PRIMARY KEY,
    misses INTEGER NOT NULL DEFAULT 0,
    last_feedback_json TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
)""",
    # Run times read from Hermes at the moment of a check. Only timestamps and counts, never a prompt or a message.
    """CREATE TABLE IF NOT EXISTS deployer_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    taken_at TEXT NOT NULL,
    source TEXT NOT NULL,
    times_json TEXT NOT NULL DEFAULT '[]',
    failed_json TEXT NOT NULL DEFAULT '[]'
)""",
    """CREATE TABLE IF NOT EXISTS deployer_renewals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hermes_version TEXT NOT NULL,
    version_source TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    body_json TEXT NOT NULL
)""",    # 0.9.0, Foundations --------------------------------------------------------
    # One row per try at a Foundations mission. seed and plants_json are hidden from every page payload until the
    # learner reaches Compare; triggers below keep them, the level and the freeze time from ever changing.
    """CREATE TABLE IF NOT EXISTS f_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    attempt_no INTEGER NOT NULL,
    level TEXT NOT NULL DEFAULT 'beginner',
    seed TEXT NOT NULL DEFAULT '',
    plants_json TEXT NOT NULL DEFAULT '[]',
    profile TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL,
    frozen_at TEXT NOT NULL DEFAULT '',
    finished_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    UNIQUE (mission_id, attempt_no)
)""",
    # What the learner wrote, in order, chained by hash: recall, claim, standard, prediction, self-scores, notes.
    """CREATE TABLE IF NOT EXISTS f_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    body_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    prev_hash TEXT NOT NULL DEFAULT '',
    hash TEXT NOT NULL
)""",
    # What a check found, each time it ran.
    """CREATE TABLE IF NOT EXISTS f_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    check_id TEXT NOT NULL,
    phase TEXT NOT NULL CHECK (phase IN ('first', 'after_fix', 'transfer')),
    passed INTEGER,
    level INTEGER,
    source TEXT NOT NULL CHECK (source IN ('practice_profile', 'page_sample', 'hermes_grader')),
    facts_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
)""",
    # Scrubbed excerpts read from the practice profile, with the hash of the excerpt (never of the raw text).
    """CREATE TABLE IF NOT EXISTS f_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    check_id TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL,
    rel_path TEXT NOT NULL DEFAULT '',
    excerpt TEXT NOT NULL DEFAULT '',
    excerpt_sha256 TEXT NOT NULL DEFAULT '',
    source_sha256 TEXT NOT NULL DEFAULT '',
    read_at TEXT NOT NULL
)""",
    # Field Record entries. A correction is a new row that names the one it corrects.
    """CREATE TABLE IF NOT EXISTS f_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    mission_id TEXT NOT NULL,
    body_json TEXT NOT NULL,
    hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    corrects_id INTEGER
)""",
    # Practice profiles Field Academy planned, recorded and removed. Only a profile named here is ever written to.
    """CREATE TABLE IF NOT EXISTS f_practice (
    name TEXT PRIMARY KEY,
    path TEXT NOT NULL DEFAULT '',
    plan_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    fingerprint_json TEXT NOT NULL DEFAULT '',
    seed TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned',
    removed_at TEXT NOT NULL DEFAULT '',
    attempt_id INTEGER,
    planted_at TEXT NOT NULL DEFAULT ''
)""",
    # Foundations Field Records as issued.
    """CREATE TABLE IF NOT EXISTS f_issued (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    body_json TEXT NOT NULL,
    folder TEXT NOT NULL DEFAULT ''
)""",
)

# Append-only, enforced by the database. Nothing in Field Academy edits or removes these rows; a later version that
# tried would be stopped here.
APPEND_ONLY = ("f_entries", "f_checks", "f_evidence", "f_record", "f_issued")
TRIGGERS = tuple(
    statement
    for table in APPEND_ONLY
    for statement in (
        f"CREATE TRIGGER IF NOT EXISTS {table}_append_only_update BEFORE UPDATE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END",
        f"CREATE TRIGGER IF NOT EXISTS {table}_append_only_delete BEFORE DELETE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END",
    )
) + (
    "CREATE TRIGGER IF NOT EXISTS f_attempts_fixed BEFORE UPDATE ON f_attempts "
    "WHEN NEW.mission_id IS NOT OLD.mission_id OR NEW.attempt_no IS NOT OLD.attempt_no OR NEW.level IS NOT OLD.level "
    "OR NEW.seed IS NOT OLD.seed OR NEW.plants_json IS NOT OLD.plants_json OR NEW.started_at IS NOT OLD.started_at "
    "OR (OLD.frozen_at != '' AND NEW.frozen_at IS NOT OLD.frozen_at) "
    "BEGIN SELECT RAISE(ABORT, 'an attempt keeps its mission, level, seed, plants and freeze time'); END",
    "CREATE TRIGGER IF NOT EXISTS f_attempts_kept BEFORE DELETE ON f_attempts "
    "BEGIN SELECT RAISE(ABORT, 'attempts are kept'); END",
)

# Columns added to tables that older versions already created.
ADDED_COLUMNS = (
    ("explanations", "ladder_json", "TEXT NOT NULL DEFAULT ''"),
)

# The four steps every 0.4.0 mission had. A mission whose four were all done is
# a mission the learner passed under the old rules.
OLD_STEP_KINDS = ("lesson", "lab", "explain", "gate")


def _database_path(conn: sqlite3.Connection) -> Path | None:
    row = conn.execute("PRAGMA database_list").fetchone()
    raw = row[2] if row else ""
    return Path(raw) if raw else None


def meta_get(conn, key, default=""):
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def meta_set(conn, key, value):
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )


def _tables(conn):
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def backup(conn: sqlite3.Connection, label: str) -> Path | None:
    """Copy the whole database to backups/ beside it. Returns the copy's path, or None for an in-memory database."""
    source = _database_path(conn)
    if source is None:
        return None
    folder = source.parent / "backups"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = clock().strftime("%Y%m%dT%H%M%S")
    target = folder / f"data-{label}-{stamp}.db"
    counter = 1
    while target.exists():
        counter += 1
        target = folder / f"data-{label}-{stamp}-{counter}.db"
    copy = sqlite3.connect(target)
    try:
        conn.commit()
        conn.backup(copy)
    finally:
        copy.close()
    return target


def connect() -> sqlite3.Connection:
    override = os.environ.get("FIELD_ACADEMY_DATA_DIR")
    if override:
        root = Path(override)
        root.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(root / "data.db", timeout=5)
    else:
        from plugins.plugin_storage import plugin_db

        conn = plugin_db(PLUGIN_ID)
    conn.row_factory = sqlite3.Row
    existing = _tables(conn)
    had_progress = "mission_steps" in existing or "evidence" in existing
    version = 0
    if "meta" in existing:
        row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        version = int(row["value"]) if row and str(row["value"]).isdigit() else 0
    if had_progress and version < SCHEMA_VERSION:
        backup(conn, f"before-{SCHEMA_VERSION}")
    for statement in TABLES:
        conn.execute(statement)
    for table, column, ddl in ADDED_COLUMNS:
        if column not in _columns(conn, table):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
    for statement in TRIGGERS:
        conn.execute(statement)
    if version < SCHEMA_VERSION:
        _migrate(conn, version, had_progress)
    conn.commit()
    return conn


def _migrate(conn, from_version: int, had_progress: bool) -> None:
    """Move an older database to the current schema by adding rows, never by removing any."""
    from .curriculum import MISSIONS

    stamp = now()
    # The carry-over below is for a database made by 0.4.0. A 0.5.0 database
    # (version 5) already has its steps, 0.6.0 only adds the Deployer tables, and 0.9.0 (version 7) only adds the
    # Foundations tables, which start empty.
    if had_progress and from_version < 5:
        for mission_id, mission in MISSIONS.items():
            old = [step for step in mission["steps"] if step["kind"] in OLD_STEP_KINDS]
            rows = {
                row["step_id"]: row["status"]
                for row in conn.execute("SELECT step_id, status FROM mission_steps WHERE mission_id = ?", (mission_id,))
            }
            if not old or not all(rows.get(step["id"]) == "done" for step in old):
                continue
            # Passed under 0.4.0. The two steps 0.5.0 added are carried over as
            # done so the pass stands, and the mission is recorded at version 1
            # so "What changed since you learned this" can offer a re-check.
            for step in mission["steps"]:
                if step["kind"] in ("example", "complete") and step["id"] not in rows:
                    conn.execute(
                        "INSERT OR IGNORE INTO mission_steps(mission_id, step_id, status, note, updated_at) VALUES (?, ?, 'done', ?, ?)",
                        (mission_id, step["id"], "Carried over from 0.4.0", stamp),
                    )
            conn.execute(
                "INSERT OR IGNORE INTO mission_versions(mission_id, passed_version, updated_at, carried_over) VALUES (?, 1, ?, 1)",
                (mission_id, stamp),
            )
    meta_set(conn, "migrated_from", from_version)
    meta_set(conn, "schema_version", SCHEMA_VERSION)
