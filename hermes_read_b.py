"""More read-only readers for a practice profile, for Foundations missions 7 to 11.

The same rules as hermes_read.py: read-only, bounded, no links followed, no Hermes import, no program run, and never
``.env``, ``auth.json``, ``mcp-tokens/``, ``pairing/`` or ``platforms/``. Shapes are copied from the Hermes 0.22.4
source, never imported:

* connectors: ``mcp_servers`` in ``config.yaml`` (hermes_cli/mcp_config.py:282-302). Kept: enabled, trust, command,
  the path arguments, ``tools.include``/``tools.exclude``, transport and the URL's host. Never ``env``, ``headers`` or
  any other value. ``trust`` normalizes as tools/mcp_tool_registration.py:37-46 does (unset is ``full``, an unknown
  word is ``untrusted``).
* the connector log: ``logs/mcp-stderr.log`` (tools/mcp_tool_config.py:39), whose start banner is
  ``<local time> ===== starting MCP server '<name>' =====`` (:108-117), the time in logging's default ``%(asctime)s``
  shape (hermes_cli/stderr_timestamp.py:29-31). ``errors.log`` and ``agent.log`` use the same local time
  (hermes_logging.py:107) and rotate to ``.1`` and ``.2`` (:397-400).
* run history: ``cron/executions.db`` with the later columns ``scheduled_instant`` and ``delivery_outcome``
  (cron/executions.py:92-93); job output files under ``cron/output/<job id>/`` (cron/jobs.py:2-3, :427). Names and
  times only.
* backups: ``backups/*.zip`` (hermes_cli/web_routers/ops.py:577-600) and ``state-snapshots/*`` (hermes_cli/backup.py).
  Names and times only: a backup holds the profile's keys, so nothing in one is ever opened.
* checkpoints: whether ``checkpoints/store/refs/hermes/<sha256(folder)[:16]>`` exists, the per-folder branch tip
  (tools/checkpoint_manager.py:19, :218-220). Its name and time only.
* the practice folder: ``<home>/practice-folder``, files listed with size, time and hash; small text files read for
  comparison in this process only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from . import hermes_read, scrub, yaml_keys

FOLDER = "practice-folder"
LOGS = ("errors.log", "agent.log", "mcp-stderr.log", "gateway.log")
ROTATED = ("", ".1", ".2")
STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3})")
BANNER = re.compile(r"===== starting MCP server '([^']+)' =====")
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
MAX_FOLDER_FILES = 500
TEXT_LIMIT = 256 * 1024


# --------------------------------------------------------------- connectors --


def normalize_trust(value) -> str:
    """tools/mcp_tool_registration.py:37-46: unset is full; full or untrusted as written; anything else untrusted."""
    if value is None:
        return "full"
    text = str(value).strip().lower()
    return text if text in ("full", "untrusted") else "untrusted"


def _looks_like_path(text) -> bool:
    text = str(text or "")
    return bool(text) and (text.startswith(("/", "~", "\\\\")) or bool(re.match(r"^[A-Za-z]:[\\/]", text)))


def _plain_list(value):
    if isinstance(value, list):
        return [str(v) for v in value if isinstance(v, (str, int, float))][:100]
    return None


def mcp_servers(home) -> dict:
    """Every connector in the practice profile's config: the fields the checks need, nothing else."""
    found = hermes_read._read_text(home, "config.yaml")
    if found is None:
        return hermes_read.unreadable("No config.yaml in the practice profile.")
    tree = yaml_keys.parse(found[0])
    branch = yaml_keys.get(tree, "mcp_servers")
    out = {"readable": True, "servers": [], "sha256": found[1], "mtime": found[2]}
    if not isinstance(branch, dict):
        return out
    for name, node in list(branch.items())[:50]:
        if not isinstance(node, dict):
            continue
        tools = node.get("tools") if isinstance(node.get("tools"), dict) else {}
        args = _plain_list(node.get("args")) or []
        enabled = node.get("enabled")
        url = node.get("url")
        host = ""
        if isinstance(url, str) and "$" not in url:
            from urllib.parse import urlsplit

            try:
                host = urlsplit(url).hostname or ""
            except ValueError:
                host = ""
        out["servers"].append({
            "name": str(name)[:80],
            "enabled": enabled is not False,
            "trust_raw": node.get("trust") if isinstance(node.get("trust"), (str, type(None))) else str(node.get("trust")),
            "trust": normalize_trust(node.get("trust")),
            "command": scrub.scrub(node.get("command") or "", 300) if isinstance(node.get("command"), str) else "",
            "command_raw": node.get("command") if isinstance(node.get("command"), str) else "",
            "paths": [a for a in args if _looks_like_path(a)],
            "args_shown": [scrub.scrub(a, 200) for a in args][:20],
            "include": _plain_list(tools.get("include")),
            "exclude": _plain_list(tools.get("exclude")),
            "transport": str(node.get("transport") or "")[:20],
            "host": host,
        })
    return out


def _plain(value):
    """A config value made of plain values only, or None when part of it can't be read safely."""
    if isinstance(value, yaml_keys.Text):
        return None
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            clean = _plain(item)
            if clean is None and item is not None:
                return None
            out[str(key)] = clean
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            clean = _plain(item)
            if clean is None and item is not None:
                return None
            out.append(clean)
        return out
    return value


def settings_text(home, server: str, extra: dict) -> dict:
    """The Connectors "Advanced" box's full replacement text, for the page only (never stored, never logged).

    ``{"mcpServers": {...}}`` with every entry copied as it is in config.yaml, except ``server``, which keeps its
    command and arguments and gets ``extra`` (trust and an empty allow list) on top. Missions 7: the learner pastes
    it over the box, so dropping or changing any other entry would erase what is there. When any part of
    ``mcp_servers`` is written in a form this reader can't copy exactly, it says so instead of guessing.
    """
    found = hermes_read._read_text(home, "config.yaml")
    if found is None:
        return hermes_read.unreadable("No config.yaml in the practice profile.")
    branch = yaml_keys.get(yaml_keys.parse(found[0]), "mcp_servers")
    if not isinstance(branch, dict) or server not in branch or not isinstance(branch[server], dict):
        return hermes_read.unreadable(f"The practice profile has no connector called {server}.")
    copied = _plain(branch)
    if copied is None:
        return hermes_read.unreadable("Part of the connector settings is written in a form Field Academy can't copy exactly. "
                                      "Add the two lines by hand instead.")
    entry = {k: v for k, v in copied[server].items() if k != "tools"}
    tools = dict(copied[server].get("tools") or {}) if isinstance(copied[server].get("tools"), dict) else {}
    tools.pop("exclude", None)
    tools.update(extra.get("tools") or {})
    entry.update({k: v for k, v in extra.items() if k != "tools"})
    entry["tools"] = tools
    copied[server] = entry
    return {"readable": True, "text": json.dumps({"mcpServers": copied}, indent=2, ensure_ascii=False), "sha256": found[1],
            "servers": sorted(copied)}


# --------------------------------------------------------------------- logs --


def log_time(line: str):
    """The epoch of a log line's local-time stamp, or None."""
    match = STAMP.match(str(line or ""))
    if not match:
        return None
    try:
        return time.mktime(datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").timetuple()) + int(match.group(2)) / 1000
    except (ValueError, OverflowError):
        return None


def log_lines(home, names=LOGS, max_lines: int = 400) -> dict:
    """The last lines of each named log and its two rotated copies, scrubbed, oldest first, with their times."""
    out = {"readable": True, "lines": []}
    for name in names:
        if name not in LOGS:
            continue
        for suffix in reversed(ROTATED):
            text = hermes_read._tail(home, f"logs/{name}{suffix}", 512 * 1024)
            if text is None:
                continue
            for line in text.splitlines()[-max_lines:]:
                if line.strip():
                    out["lines"].append({"file": f"logs/{name}{suffix}", "line": scrub.scrub(line, 600), "time": log_time(line)})
    return out


def banners(home) -> list:
    """Connector start banners in mcp-stderr.log: ``{"server", "time"}``, oldest first."""
    found = []
    for item in log_lines(home, ("mcp-stderr.log",), 2000)["lines"]:
        match = BANNER.search(item["line"])
        if match:
            found.append({"server": match.group(1), "time": item["time"], "file": item["file"]})
    return found


# --------------------------------------------------------------- schedules --


def jobs(home) -> dict:
    """hermes_read.cron_jobs plus the two fields missions 8 and 10 need: the job's prompt for checking, and
    ``context_from`` (cron jobs can read another job's latest output)."""
    base = hermes_read.cron_jobs(home)
    if not base.get("readable"):
        return base
    raw = hermes_read._read_text(home, "cron/jobs.json", 2 * 1024 * 1024)
    extra = {}
    if raw is not None:
        try:
            data = json.loads(raw[0])
        except ValueError:
            data = {}
        items = data.get("jobs", []) if isinstance(data, dict) else data
        for job in items if isinstance(items, list) else []:
            if isinstance(job, dict) and isinstance(job.get("id"), str):
                ctx = job.get("context_from")
                extra[job["id"]] = {"context_from": [str(x)[:80] for x in ctx][:10] if isinstance(ctx, list) else
                                    ([str(ctx)[:80]] if isinstance(ctx, str) and ctx else []),
                                    "prompt_full": str(job.get("prompt") or "")[:4000],
                                    "paused_at": job.get("paused_at")}
    for job in base["jobs"]:
        job.update(extra.get(job.get("id"), {"context_from": [], "prompt_full": "", "paused_at": None}))
    base["mtime"] = raw[2] if raw is not None else None
    return base


def _mcp_component(value) -> str:
    """tools/mcp_tool_schema.py sanitize_mcp_name_component: every character outside [A-Za-z0-9_] becomes "_"."""
    return re.sub(r"[^A-Za-z0-9_]", "_", str(value or ""))


def is_connector_tool(tool_name, server) -> bool:
    """True when a tool row in state.db is one of connector ``server``'s tools.

    Hermes names them ``mcp__<server>__<tool>`` (tools/mcp_tool_schema.py:159 MCP_TOOL_NAME_PREFIX and
    mcp_prefixed_tool_name, the same in 0.22.0 and 0.23.0); that name is what state.db keeps. A name longer than 64
    characters is clamped with a hash after the server part, so the prefix still holds."""
    server = _mcp_component(server)
    return bool(server) and str(tool_name or "").startswith(f"mcp__{server}__")


EXEC_COLUMNS = ("id", "job_id", "source", "status", "claimed_at", "started_at", "finished_at", "error", "scheduled_instant",
                "delivery_outcome")


def runs(home, job_id=None) -> dict:
    """Run history rows, with ``scheduled_instant`` (NULL for a hand run) and ``delivery_outcome`` where present.

    A ``missed`` row is not a run. Hermes 0.23.0 books one for every stretch of slots a job couldn't fire on time (the
    machine asleep, the gateway stopped), with ``scheduled_instant`` set to the first skipped slot
    (cron/executions.py:39-40, cron/missed_runs.py). Counted as a run it would read as "fired by the schedule", so it
    is left out of ``executions`` and only counted in ``missed``."""
    conn = hermes_read._db(home, "cron/executions.db")
    if conn is None:
        return {"readable": True, "executions": []}
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "executions" not in tables:
            return {"readable": True, "executions": []}
        if job_id is None:
            rows = hermes_read._rows(conn, "executions", EXEC_COLUMNS, order="claimed_at")
        else:
            rows = hermes_read._rows(conn, "executions", EXEC_COLUMNS, where="job_id = ?", args=(str(job_id),), order="claimed_at")
        missed = sum(1 for row in rows if row.get("status") == "missed")
        rows = [row for row in rows if row.get("status") != "missed"]
        for row in rows:
            if isinstance(row.get("error"), str):
                row["error"] = scrub.scrub(row["error"], 300)
        return {"readable": True, "executions": rows, "missed": missed}
    except sqlite3.Error as exc:
        return hermes_read.unreadable(f"The run history could not be read: {exc.__class__.__name__}")
    finally:
        conn.close()


def iso_epoch(text):
    """An ISO timestamp from Hermes's cron records as an epoch, or None."""
    if not isinstance(text, str) or not text:
        return None
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return time.mktime(stamp.timetuple())
    return stamp.timestamp()


def outputs(home, job_id) -> list:
    """Output files a job's runs left, by name and time. Nothing inside them is read."""
    if not SAFE_ID.match(str(job_id or "")):
        return []
    folder = hermes_read.safe_path(home, f"cron/output/{job_id}")
    if folder is None or not folder.is_dir():
        return []
    out = []
    for entry in sorted(folder.iterdir())[:500]:
        if entry.is_symlink() or not entry.is_file():
            continue
        out.append({"name": scrub.scrub(entry.name, 120), "mtime": entry.stat().st_mtime})
    return out


# ----------------------------------------------------------------- backups --


def backups(home) -> dict:
    """Backup archives and quick snapshots, by name and time only. Their contents are never opened."""
    out = {"readable": True, "items": []}
    for rel, kind in (("backups", "full backup"), ("state-snapshots", "quick snapshot")):
        folder = hermes_read.safe_path(home, rel)
        if folder is None or not folder.is_dir():
            continue
        for entry in sorted(folder.iterdir())[:200]:
            if entry.is_symlink():
                continue
            if kind == "full backup" and not entry.name.endswith(".zip"):
                continue
            try:
                mtime = entry.stat().st_mtime
            except OSError:
                continue
            out["items"].append({"kind": kind, "name": scrub.scrub(entry.name, 160), "mtime": mtime, "rel_path": f"{rel}/{entry.name}"})
    out["items"].sort(key=lambda i: i["mtime"])
    return out


# ------------------------------------------------------------- checkpoints --


def folder_hash(folder) -> str:
    """tools/checkpoint_manager.py:218-220: sha256 of the folder's absolute path, first 16 hex characters."""
    return hashlib.sha256(str(Path(folder).expanduser().resolve(strict=False)).encode()).hexdigest()[:16]


def checkpoint_ref(home, folder) -> dict:
    """Whether the checkpoint store has a branch for this folder, and when it last moved. The name only."""
    rel = f"checkpoints/store/refs/hermes/{folder_hash(folder)}"
    path = hermes_read.safe_path(home, rel)
    exists = path is not None and path.is_file()
    return {"readable": True, "exists": exists, "mtime": path.stat().st_mtime if exists else None, "rel_path": rel,
            "store": hermes_read.checkpoints(home)}


# ---------------------------------------------------------- practice folder --


def folder_path(home) -> Path:
    return Path(home) / FOLDER


def folder_files(home) -> dict:
    """Every file in the practice folder: relative path, size, time and hash. Links are skipped."""
    root = hermes_read.safe_path(home, FOLDER)
    if root is None or not root.is_dir():
        return {"readable": root is not None, "files": [], "why": "The practice folder isn't there."}
    out = []
    for top, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(top) / d).is_symlink())
        for name in sorted(names):
            path = Path(top) / name
            if path.is_symlink():
                continue
            rel = path.relative_to(root).as_posix()
            try:
                st = path.stat()
                digest = ""
                if st.st_size <= TEXT_LIMIT:
                    with open(path, "rb") as handle:
                        digest = hashlib.sha256(handle.read()).hexdigest()
            except OSError:
                continue
            out.append({"rel": rel, "size": st.st_size, "mtime": st.st_mtime, "sha256": digest})
            if len(out) >= MAX_FOLDER_FILES:
                return {"readable": True, "files": out, "capped": True}
    return {"readable": True, "files": out}


def folder_text(home, rel: str, limit: int = TEXT_LIMIT):
    """A small text file in the practice folder, for comparison in this process only. None when it can't be read."""
    found = hermes_read._read_text(home, f"{FOLDER}/{rel}", limit)
    return found[0] if found is not None else None


# ---------------------------------------------------------------- settings --


def settings(home) -> dict:
    """The safety and model settings missions 9 to 11 read: approval mode, the always-allow list (the rule keys, such
    as "recursive delete"), checkpoints, the main model, backup models, the helper-agent model, the side-job model
    slots by name and provider, and switched-off toolsets. Plain values only, scrubbed."""
    found = hermes_read._read_text(home, "config.yaml")
    if found is None:
        return hermes_read.unreadable("No config.yaml in the practice profile.")
    tree = yaml_keys.parse(found[0])

    def text(path, limit=200):
        value = yaml_keys.get(tree, path)
        if isinstance(value, bool):
            return "off" if value is False and path == "approvals.mode" else value
        if isinstance(value, (yaml_keys.Text, dict, list)) or value is None:
            return None
        return scrub.scrub(str(value), limit)

    def names(path):
        value = yaml_keys.get(tree, path)
        return [scrub.scrub(str(v), 160) for v in value if isinstance(v, (str, int, float))][:50] if isinstance(value, list) else []

    model = yaml_keys.get(tree, "model")
    fallbacks = yaml_keys.get(tree, "fallback_providers")
    aux = yaml_keys.get(tree, "auxiliary")
    return {
        "readable": True, "mtime": found[2], "sha256": found[1],
        "approvals_mode": text("approvals.mode"),
        "command_allowlist": names("command_allowlist"),
        "checkpoints_enabled": yaml_keys.get(tree, "checkpoints.enabled") is True,
        "model": scrub.scrub(model, 160) if isinstance(model, str) and not isinstance(model, yaml_keys.Text) else text("model.default"),
        "model_is_mapping": isinstance(model, dict),
        "provider": text("model.provider"),
        "fallbacks": [scrub.scrub(str(f.get("model", "")), 160) for f in fallbacks if isinstance(f, dict)][:20] if isinstance(fallbacks, list) else [],
        "fallbacks_block": isinstance(fallbacks, list) and bool(fallbacks),
        "delegation_model": text("delegation.model") or "",
        "auxiliary": {str(k): {"provider": scrub.scrub(str(v.get("provider", "")), 80), "model": scrub.scrub(str(v.get("model", "")), 160)}
                      for k, v in list(aux.items())[:30] if isinstance(v, dict)} if isinstance(aux, dict) else {},
        "disabled_toolsets": names("agent.disabled_toolsets"),
    }

