"""Delete my Field Academy data: the learner's two choices, from Settings.

* ``keep_records=True``  ("Delete my progress"): progress, answers, practice labs, pasted text, caches, usage notes
  and database backups go. Saved Field Records stay: the files in ``field-records/`` and the rows that list them
  (``certificates`` and ``f_issued``), so the Field Record screen still shows them and their MANIFEST.sha256 still
  verifies.
* ``keep_records=False`` ("Delete everything"): all of that, and the saved Field Records too.

Either way the two Settings switches keep their values, because someone who turned AI help off didn't ask to have it
turned back on. Records saved somewhere outside the data folder are never touched; this only deletes inside it.

It refuses while a practice profile is still set up: Field Academy remembers which profiles it made only in its own
database, and once that is gone it could no longer find them to delete them. The page deletes them first.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import labs, practice, runtime, store

KEPT_FOR_RECORDS = ("certificates", "f_issued")
LIVE = ("ready", "planted", "in_use", "removing")
DATABASE_FILES = ("data.db", "data.db-wal", "data.db-shm", "data.db-journal")


def live_practice() -> list:
    return [p["name"] for p in practice.listing() if p.get("status") in LIVE]


def _safe_folder() -> Path:
    folder = runtime.data_dir().resolve()
    if labs._looks_like_hermes_home(folder) or folder == Path.home().resolve():
        raise ValueError("Field Academy's data folder looks like a Hermes home, so nothing was deleted.")
    return folder


def delete_data(keep_records: bool) -> dict:
    if not isinstance(keep_records, bool):
        raise ValueError("Choose Delete my progress or Delete everything.")
    still = live_practice()
    if still:
        raise ValueError(f"Delete the practice profile first: {', '.join(still)}. Field Academy needs its notes to find it.")
    folder = _safe_folder()
    keep_tables = set(KEPT_FOR_RECORDS) if keep_records else set()
    conn = store.connect()
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            if table == "meta" or table in keep_tables:
                continue
            conn.execute(f'DROP TABLE IF EXISTS "{table}"')  # takes its append-only triggers with it
        conn.execute("DELETE FROM meta WHERE key != 'schema_version' AND key NOT LIKE 'setting:%'")
        conn.commit()
        conn.execute("VACUUM")  # so the deleted rows don't linger in the file's free pages
    finally:
        conn.close()
    removed = []
    for item in sorted(folder.iterdir()):
        if item.name in DATABASE_FILES or (keep_records and item.name == "field-records"):
            continue
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()
        removed.append(item.name)
    store.connect().close()  # make the empty tables again, so the page opens on a fresh start
    kept = "Your saved Field Records are still there." if keep_records else "Your saved Field Records are gone too."
    return {"deleted": True, "kept_records": keep_records, "removed": removed,
            "words": f"Field Academy's data is deleted. {kept} Records you saved somewhere else were not touched."}
