"""Read-only readers for a Field Academy practice profile's own files.

Every reader takes the practice home (``<root>/profiles/academy-practice``), reads with bounded sizes and counts,
follows no links, and never writes, runs a program or imports Hermes. Shapes come from the Hermes 0.22.4 source
(copied, never imported):

* memory: ``memories/MEMORY.md`` and ``USER.md``, entries split on ``"\\n§\\n"`` (tools/memory_tool_store.py:25);
  limits from ``memory.memory_char_limit``/``user_char_limit``, default 2200/1375 (config_defaults.py:1334-1335).
* staged writes: ``pending/{memory,skills}/<id>.json`` (tools/write_approval.py:65-86).
* config: named keys only, through ``yaml_keys``; a ``${VAR}`` reference is never copied.
* skills: ``skills/**/SKILL.md`` front matter, walked like agent/skill_utils.py:859.
* chat records: ``state.db`` (hermes_state_common.py SCHEMA_SQL, SCHEMA_VERSION 32), opened ``mode=ro``.
* schedules: ``cron/jobs.json`` and ``cron/executions.db`` (cron/jobs.py, cron/executions.py, cron/incidents.py).
* logs: a bounded tail of ``logs/agent.log``, ``errors.log``, ``gateway.log`` (hermes_logging.py:3), scrubbed.
* checkpoints: existence, file count and size only.

What is never read, by name, whatever asks: ``.env``, ``auth.json``, ``mcp-tokens/``, ``pairing/``, ``platforms/``.
A reader that can't read says so (``readable: False`` and why). It never guesses and never passes on a failure.
"""

from __future__ import annotations

import hashlib
import json
import re
import os
import sqlite3
from pathlib import Path

from . import evidence, scrub, yaml_keys

STATE_SCHEMA_VERSION = 32  # hermes_state_common.py:289 in 0.22.4
DELIM = "\n§\n"
DEFAULT_LIMITS = {"memory": 2200, "user": 1375}
NEVER_READ = frozenset({".env", "auth.json", "mcp-tokens", "pairing", "platforms"})
MAX_TEXT = 256 * 1024
MAX_PENDING = 200
MAX_SKILLS = 500
MAX_WALK = 20000
MAX_ROWS = 2000
LOG_FILES = ("agent.log", "errors.log", "gateway.log")
# agent/skill_utils.py EXCLUDED_SKILL_DIRS. ".hermes-dist" (DIST_SWAP_DIR, where a profile-distribution install stages a
# folder it swaps in) is new in 0.23.0 (agent/skill_utils.py:26-32): a backup kept there is never a second copy of a skill.
EXCLUDED_SKILL_DIRS = frozenset({
    ".git", ".github", ".hub", ".archive", ".curator_backups", ".locks", ".hermes-dist", ".venv", "venv", "node_modules",
    "site-packages", "__pycache__", ".tox", ".nox", ".pytest_cache", ".mypy_cache", ".ruff_cache",
})
SKILL_SUPPORT_DIRS = frozenset({"references", "templates", "assets", "scripts"})

# The only config keys ever read. "*" is one level of names (a provider, a connector).
CONFIG_KEYS = (
    "model", "model.default", "model.provider", "model.model", "providers.*.model", "toolsets",
    "mcp_servers.*.enabled", "mcp_servers.*.trust", "mcp_servers.*.transport", "mcp_servers.*.url",
    "approvals.mode", "approvals.timeout", "approvals.deny", "approvals.cron_mode",
    "checkpoints.enabled", "checkpoints.max_snapshots",
    "memory.write_approval", "memory.memory_enabled", "memory.user_profile_enabled", "memory.provider",
    "memory.memory_char_limit", "memory.user_char_limit", "skills.write_approval",
    "delegation.model", "delegation.provider", "cron.model", "fallback_providers", "compression.threshold",
    "sessions.auto_prune", "sessions.retention_days", "terminal.cwd",
)

SESSION_COLUMNS = (
    "id", "source", "model", "title", "parent_session_id", "started_at", "ended_at", "end_reason", "message_count",
    "tool_call_count", "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "reasoning_tokens",
    "api_call_count", "estimated_cost_usd", "actual_cost_usd", "cost_status", "cost_source", "pricing_version",
    "billing_provider", "billing_mode", "system_prompt_hash", "last_activity_at", "profile_name", "cwd",
)
MESSAGE_COLUMNS = ("id", "session_id", "role", "content", "tool_name", "tool_calls", "timestamp", "active")
USAGE_COLUMNS = (
    "session_id", "model", "billing_provider", "task", "api_call_count", "input_tokens", "output_tokens",
    "cache_read_tokens", "cache_write_tokens", "reasoning_tokens", "estimated_cost_usd", "actual_cost_usd",
)
JOB_FIELDS = (
    "id", "name", "skills", "model", "provider", "schedule", "schedule_display", "enabled", "state", "created_at",
    "next_run_at", "last_run_at", "last_status", "last_error", "last_delivery_error", "last_delivery_unverified",
    "last_failure", "failure_streak", "deliver", "enabled_toolsets", "workdir",
)
EXECUTION_COLUMNS = ("id", "job_id", "source", "status", "claimed_at", "started_at", "finished_at", "error")
INCIDENT_COLUMNS = ("id", "job_id", "state", "failure_type", "first_seen_at", "last_seen_at", "error")


def unreadable(why: str) -> dict:
    return {"readable": False, "why": why}


# ----------------------------------------------------------------- guards --


def safe_path(home, rel: str):
    """``home/rel`` when it may be read: no forbidden name, no link anywhere below home, still inside home."""
    home = Path(home)
    parts = Path(rel).parts
    if not parts or any(part in NEVER_READ or part == ".." for part in parts):
        return None
    current = home
    if home.is_symlink():
        return None
    for part in parts:
        current = current / part
        if current.is_symlink():
            return None
    try:
        current.resolve(strict=False).relative_to(home.resolve(strict=False))
    except ValueError:
        return None
    return current


def _read_text(home, rel: str, limit: int = MAX_TEXT):
    """(text, sha256 of the bytes, mtime) or None. Reads at most ``limit`` bytes."""
    path = safe_path(home, rel)
    if path is None or not path.is_file():
        return None
    try:
        with open(path, "rb") as handle:
            raw = handle.read(limit)
        mtime = path.stat().st_mtime
    except OSError:
        return None
    return raw.decode("utf-8", errors="replace"), hashlib.sha256(raw).hexdigest(), mtime


def _tail(home, rel: str, limit: int = MAX_TEXT):
    path = safe_path(home, rel)
    if path is None or not path.is_file():
        return None
    try:
        size = path.stat().st_size
        with open(path, "rb") as handle:
            handle.seek(max(0, size - limit))
            raw = handle.read(limit)
    except OSError:
        return None
    text = raw.decode("utf-8", errors="replace")
    if size > limit:
        text = text.split("\n", 1)[1] if "\n" in text else ""
    return text


def _db(home, rel: str):
    path = safe_path(home, rel)
    if path is None or not path.is_file():
        return None
    try:
        return evidence._ro_connect(path)
    except sqlite3.Error:
        return None


def _columns(conn, table: str) -> list:
    return [row[0] for row in conn.execute("SELECT name FROM pragma_table_info(?)", (table,))]


# ----------------------------------------------------------------- memory --


def split_entries(text: str) -> list:
    return [entry.strip() for entry in (text or "").split(DELIM) if entry.strip()]


def limits(home) -> dict:
    values = config(home).get("values", {})
    out = dict(DEFAULT_LIMITS)
    for key, name in (("memory", "memory.memory_char_limit"), ("user", "memory.user_char_limit")):
        value = values.get(name)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            out[key] = value
    return out


def memory(home) -> dict:
    """Both memory files: entries, characters used against the limit, file time and hash. Text stays in memory only."""
    caps = limits(home)
    out = {"readable": True}
    for key, name in (("memory", "MEMORY.md"), ("user", "USER.md")):
        found = _read_text(home, f"memories/{name}", 64 * 1024)
        if found is None:
            out[key] = {"exists": False, "entries": [], "chars": 0, "limit": caps[key], "mtime": None, "sha256": "", "rel_path": f"memories/{name}"}
            continue
        text, digest, mtime = found
        entries = split_entries(text)
        out[key] = {"exists": True, "entries": entries, "chars": len(DELIM.join(entries)), "limit": caps[key], "mtime": mtime,
                    "sha256": digest, "rel_path": f"memories/{name}"}
    if safe_path(home, "memories") is None and (Path(home) / "memories").exists():
        return unreadable("The memories folder is a link, so Field Academy did not read it.")
    return out


def pending(home) -> dict:
    """Writes Hermes staged for approval (``memory.write_approval`` or ``skills.write_approval`` on)."""
    out = {"readable": True, "memory": [], "skills": []}
    for subsystem in ("memory", "skills"):
        folder = safe_path(home, f"pending/{subsystem}")
        if folder is None or not folder.is_dir():
            continue
        names = sorted(p.name for p in folder.iterdir() if p.suffix == ".json")[:MAX_PENDING]
        for name in names:
            found = _read_text(home, f"pending/{subsystem}/{name}", 64 * 1024)
            if found is None:
                continue
            try:
                record = json.loads(found[0])
            except ValueError:
                continue
            if not isinstance(record, dict):
                continue
            payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
            action, content = _payload_words(record, payload)
            out[subsystem].append({
                "id": str(record.get("id", ""))[:40], "action": action[:40],
                "origin": str(record.get("origin", ""))[:40], "created_at": record.get("created_at"),
                "summary": scrub.scrub(record.get("summary", ""), 200),
                "content": content[:2000],
                "rel_path": f"pending/{subsystem}/{name}",
            })
        out[subsystem].sort(key=lambda r: r["created_at"] if isinstance(r["created_at"], (int, float)) else 0)
    return out


_BATCH_SUMMARY = re.compile(r"^apply \d+ op\(s\) to [a-z ]+:\s*", re.I)
_OP_LINE = re.compile(r"^-\s*(add|patch|remove|replace)[^:]*:\s*(.*)$", re.I)


def _payload_words(record, payload) -> tuple:
    """A held save's action and the note it would write. Hermes stages a memory call with ``operations`` as one
    ``batch`` payload whose summary reads "apply 1 op(s) to memory: - add: ..." (Hermes 0.23). One operation is read
    as that operation, so the page shows the note, not Hermes's summary (Loop 3 live gate)."""
    action = str(record.get("action") or payload.get("action") or "")
    content = str(payload.get("content") or payload.get("new_content") or "")
    ops = payload.get("operations") if isinstance(payload.get("operations"), list) else []
    ops = [op for op in ops if isinstance(op, dict)]
    if not content and len(ops) == 1:
        op = ops[0]
        action = str(op.get("action") or action)
        content = str(op.get("content") or op.get("new_text") or op.get("old_text") or "")
    elif not content and ops:
        content = "; ".join(f"{op.get('action', '')} {op.get('content') or op.get('new_text') or op.get('old_text') or ''}".strip() for op in ops)
    if action == "batch" and len(ops) == 1:
        action = str(ops[0].get("action") or action)
    return action, content


def summary_words(summary) -> str:
    """Hermes's batch summary ("apply 1 op(s) to memory: - add: X") as "add X", for a record with no payload text."""
    text = str(summary or "").strip()
    if not _BATCH_SUMMARY.match(text):
        return text
    lines = [ln.strip() for ln in _BATCH_SUMMARY.sub("", text).splitlines() if ln.strip()]
    found = [_OP_LINE.match(ln) for ln in lines]
    if found and all(found):
        return "; ".join(f"{m.group(1).lower()} {m.group(2).strip()}" for m in found)
    return text


def pending_words(item) -> str:
    """A held save as evidence: its action and the full line it would save. Hermes's own summary is cut at 40
    characters, often inside a word ("add Harbor Bakery uses QuickBooks Online; th"), so the content is used when the
    record has it; the evidence maker then ends a long one at a word (0.9 persona test)."""
    content = " ".join(str(item.get("content") or "").split())
    action = str(item.get("action") or "").strip()
    if not content and isinstance(item.get("payload"), dict):
        action, content = _payload_words(item, item["payload"])
        content = " ".join(content.split())
        action = action.strip()
    if not content:
        return summary_words(item.get("summary"))
    return f"{action} {content}" if action else content


# ----------------------------------------------------------------- config --


def _clean_value(path: str, value):
    """A config value as Field Academy may keep it: plain values only, no reference, no secret, URLs as host only."""
    if isinstance(value, yaml_keys.Text):
        return None
    if isinstance(value, str):
        if "${" in value or "$" in value and value.strip().startswith("$"):
            return "[a reference to a secret]"
        if path.endswith(".url"):
            from urllib.parse import urlsplit

            try:
                return urlsplit(value).hostname or ""
            except ValueError:
                return ""
        return scrub.scrub(value, 200)
    if isinstance(value, list):
        if path == "fallback_providers":
            return [str(item.get("model", ""))[:120] for item in value if isinstance(item, dict)][:20]
        return [scrub.scrub(item, 120) for item in value if isinstance(item, (str, int, float, bool))][:50]
    if isinstance(value, dict):
        return None
    return value


def config(home) -> dict:
    """The whitelisted keys of the practice profile's config.yaml, by dotted path."""
    found = _read_text(home, "config.yaml")
    if found is None:
        return {"readable": False, "why": "No config.yaml in the practice profile.", "values": {}, "sha256": ""}
    text, digest, mtime = found
    tree = yaml_keys.parse(text)
    values = {}
    for key in CONFIG_KEYS:
        head, _, tail = key.partition(".*.")
        if tail:
            branch = yaml_keys.get(tree, head)
            if isinstance(branch, dict):
                for name, node in list(branch.items())[:50]:
                    if isinstance(node, dict) and tail in node:
                        clean = _clean_value(key, node[tail])
                        if clean is not None:
                            values[f"{head}.{name}.{tail}"] = clean
            continue
        value = yaml_keys.get(tree, key)
        if value is None or isinstance(value, dict):
            continue
        clean = _clean_value(key, value)
        if clean is not None:
            values[key] = clean
    return {"readable": True, "values": values, "sha256": digest, "mtime": mtime}


# ----------------------------------------------------------------- skills --


def _front_matter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    body = []
    for line in lines[1:200]:
        if line.strip() == "---":
            break
        body.append(line)
    tree = yaml_keys.parse("\n".join(body))
    return tree if isinstance(tree, dict) else {}


def skills(home) -> dict:
    """Every SKILL.md under skills/: name, description, size and time. Bounded, and links are never followed."""
    root = safe_path(home, "skills")
    if root is None or not root.is_dir():
        return {"readable": root is not None or not (Path(home) / "skills").exists(), "skills": []}
    found = []
    seen = 0
    for top, dirs, files in os.walk(root, followlinks=False):
        seen += len(files) + len(dirs)
        if seen > MAX_WALK or len(found) >= MAX_SKILLS:
            break
        has_skill = "SKILL.md" in files
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_SKILL_DIRS and not (has_skill and d in SKILL_SUPPORT_DIRS)
                         and not (Path(top) / d).is_symlink())
        if not has_skill:
            continue
        rel = (Path(top) / "SKILL.md").relative_to(Path(home)).as_posix()
        text = _read_text(home, rel, 64 * 1024)
        if text is None:
            continue
        meta = _front_matter(text[0])
        found.append({
            "name": scrub.scrub(meta.get("name") or Path(top).name, 120), "description": scrub.scrub(meta.get("description") or "", 300),
            "rel_path": rel, "bytes": len(text[0].encode("utf-8")), "mtime": text[2], "sha256": text[1],
        })
    return {"readable": True, "skills": found}


# ------------------------------------------------------------- chat store --


def _rows(conn, table, columns, where="", args=(), order="", limit=MAX_ROWS):
    present = set(_columns(conn, table))
    wanted = [c for c in columns if c in present]
    if not wanted:
        return []
    names = ", ".join(f'"{c}"' for c in wanted)
    sql = f'SELECT {names} FROM "{table}"' + (f" WHERE {where}" if where else "") + (f" ORDER BY {order}" if order else "") + f" LIMIT {int(limit)}"
    return [dict(zip(wanted, row)) for row in conn.execute(sql, args)]


def chat_store(home) -> dict:
    """The state.db schema version, and whether it is the one these readers were written for."""
    conn = _db(home, "state.db")
    if conn is None:
        return unreadable("No chat records (state.db) in the practice profile yet.")
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        version = None
        if "schema_version" in tables:
            row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            version = int(row[0]) if row and str(row[0]).isdigit() else None
        return {"readable": "sessions" in tables and "messages" in tables, "schema_version": version,
                "schema_ok": version == STATE_SCHEMA_VERSION, "tables": sorted(t for t in tables if not t.startswith("sqlite_"))[:40]}
    except sqlite3.Error as exc:
        return unreadable(f"state.db could not be read: {exc.__class__.__name__}")
    finally:
        conn.close()


def sessions(home, limit: int = 200) -> dict:
    conn = _db(home, "state.db")
    if conn is None:
        return unreadable("No chat records (state.db) in the practice profile yet.")
    try:
        rows = _rows(conn, "sessions", SESSION_COLUMNS, order="started_at", limit=limit)
        for row in rows:
            if "title" in row:
                row["title"] = scrub.scrub(row["title"] or "", 120)
        return {"readable": True, "sessions": rows}
    except sqlite3.Error as exc:
        return unreadable(f"Sessions could not be read: {exc.__class__.__name__}")
    finally:
        conn.close()


def messages(home, session_id=None, limit: int = MAX_ROWS) -> dict:
    """Messages, oldest first. Text is returned for comparison in this process only; callers keep scrubbed excerpts."""
    conn = _db(home, "state.db")
    if conn is None:
        return unreadable("No chat records (state.db) in the practice profile yet.")
    try:
        if session_id is None:
            rows = _rows(conn, "messages", MESSAGE_COLUMNS, order="timestamp, id", limit=limit)
        else:
            rows = _rows(conn, "messages", MESSAGE_COLUMNS, where="session_id = ?", args=(str(session_id),), order="timestamp, id", limit=limit)
        for row in rows:
            if isinstance(row.get("content"), str):
                row["content"] = row["content"][:20000]
        return {"readable": True, "messages": rows}
    except sqlite3.Error as exc:
        return unreadable(f"Messages could not be read: {exc.__class__.__name__}")
    finally:
        conn.close()


def user_message_count(home):
    """How many messages a person sent in the practice profile: 0, a number, or None when it can't be read."""
    conn = _db(home, "state.db")
    if conn is None:
        return None if (Path(home) / "state.db").exists() else 0
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "messages" not in tables:
            return 0
        return int(conn.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'").fetchone()[0])
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def usage(home, session_id=None) -> dict:
    """Tokens and cost per model and task (``background_review`` shows apart from the main model)."""
    conn = _db(home, "state.db")
    if conn is None:
        return unreadable("No chat records (state.db) in the practice profile yet.")
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "session_model_usage" not in tables:
            return {"readable": True, "usage": []}
        if session_id is None:
            rows = _rows(conn, "session_model_usage", USAGE_COLUMNS)
        else:
            rows = _rows(conn, "session_model_usage", USAGE_COLUMNS, where="session_id = ?", args=(str(session_id),))
        return {"readable": True, "usage": rows}
    except sqlite3.Error as exc:
        return unreadable(f"Usage could not be read: {exc.__class__.__name__}")
    finally:
        conn.close()


def system_prompt_size(home, session_id) -> dict:
    """Characters and bytes of a session's frozen system prompt. The text itself is never returned."""
    conn = _db(home, "state.db")
    if conn is None:
        return unreadable("No chat records (state.db) in the practice profile yet.")
    try:
        row = conn.execute(
            "SELECT p.prompt FROM sessions s JOIN system_prompts p ON p.hash = s.system_prompt_hash WHERE s.id = ?", (str(session_id),)
        ).fetchone()
        if not row or row[0] is None:
            return unreadable("That chat has no saved system prompt.")
        text = str(row[0])
        return {"readable": True, "chars": len(text), "bytes": len(text.encode("utf-8"))}
    except sqlite3.Error as exc:
        return unreadable(f"The system prompt could not be read: {exc.__class__.__name__}")
    finally:
        conn.close()


# ---------------------------------------------------------------- schedule --


def cron_jobs(home) -> dict:
    found = _read_text(home, "cron/jobs.json", 2 * 1024 * 1024)
    if found is None:
        return {"readable": True, "jobs": []}
    try:
        data = json.loads(found[0])
    except ValueError:
        return unreadable("cron/jobs.json is not readable JSON.")
    items = data.get("jobs", []) if isinstance(data, dict) else data
    jobs = []
    for job in items if isinstance(items, list) else []:
        if not isinstance(job, dict):
            continue
        clean = {key: job.get(key) for key in JOB_FIELDS if key in job}
        for key in ("last_error", "last_delivery_error", "deliver", "workdir", "model", "provider"):
            if isinstance(clean.get(key), str):  # a delivery place can be a webhook address with its secret in it
                clean[key] = scrub.scrub(clean[key], 300)
        clean["prompt"] = scrub.scrub(job.get("prompt") or "", 300)
        jobs.append(clean)
        if len(jobs) >= 200:
            break
    return {"readable": True, "jobs": jobs}


def cron_runs(home, job_id=None) -> dict:
    conn = _db(home, "cron/executions.db")
    if conn is None:
        return {"readable": True, "executions": [], "incidents": []}
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        out = {"readable": True, "executions": [], "incidents": []}
        for table, columns, key in (("executions", EXECUTION_COLUMNS, "executions"), ("cron_incidents", INCIDENT_COLUMNS, "incidents")):
            if table not in tables:
                continue
            if job_id is None:
                rows = _rows(conn, table, columns)
            else:
                rows = _rows(conn, table, columns, where="job_id = ?", args=(str(job_id),))
            for row in rows:
                if isinstance(row.get("error"), str):
                    row["error"] = scrub.scrub(row["error"], 300)
            out[key] = rows
        return out
    except sqlite3.Error as exc:
        return unreadable(f"The run history could not be read: {exc.__class__.__name__}")
    finally:
        conn.close()


# ------------------------------------------------------------- logs, store --


def logs(home, files=LOG_FILES, max_lines: int = 200, contains: str = "") -> dict:
    """The last lines of each log, scrubbed, optionally only those containing a word."""
    out = {"readable": True, "files": {}}
    needle = (contains or "").lower()
    for name in files:
        if name not in LOG_FILES:
            continue
        text = _tail(home, f"logs/{name}", 512 * 1024)
        if text is None:
            continue
        lines = [line for line in text.splitlines() if not needle or needle in line.lower()]
        out["files"][name] = [scrub.scrub(line, 500) for line in lines[-max_lines:]]
    return out


def checkpoints(home) -> dict:
    root = safe_path(home, "checkpoints")
    if root is None or not root.is_dir():
        return {"readable": True, "exists": False, "files": 0, "bytes": 0}
    files = 0
    size = 0
    for top, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(top) / d).is_symlink()]
        for name in names:
            path = Path(top) / name
            if path.is_symlink():
                continue
            files += 1
            try:
                size += path.stat().st_size
            except OSError:
                pass
            if files >= MAX_WALK:
                return {"readable": True, "exists": True, "files": files, "bytes": size, "capped": True}
    return {"readable": True, "exists": True, "files": files, "bytes": size}


def gateway_running(home) -> bool:
    """True when the practice profile's backend has left a gateway.pid: it may be writing, so nothing is planted."""
    path = safe_path(home, "gateway.pid")
    return path is not None and path.exists()


def summary(home) -> dict:
    """What a learner's evidence snapshot keeps before a practice profile is deleted. Scrubbed, no message text."""
    mem = memory(home)
    return {
        "memory": {k: {"entries": [scrub.scrub(e, 300) for e in v["entries"]], "chars": v["chars"], "limit": v["limit"]}
                   for k, v in mem.items() if isinstance(v, dict)},
        "pending": {k: [{"id": r["id"], "action": r["action"], "summary": r["summary"]} for r in v] for k, v in pending(home).items() if isinstance(v, list)},
        "config": config(home).get("values", {}),
        "skills": [{"name": s["name"], "description": s["description"]} for s in skills(home).get("skills", [])],
        "sessions": [{k: s.get(k) for k in ("id", "title", "started_at", "message_count", "input_tokens", "output_tokens", "estimated_cost_usd")}
                     for s in sessions(home).get("sessions", [])],
        "chat_store": chat_store(home),
    }
