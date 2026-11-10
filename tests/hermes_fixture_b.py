"""Fixture pieces for missions 7 to 11, built from Hermes 0.22.4's own shapes (copied strings, never imported):

* connector entries in config.yaml (hermes_cli/mcp_config.py:282-302);
* mcp-stderr.log start banners, ``<local time> ===== starting MCP server '<name>' =====`` (tools/mcp_tool_config.py:114,
  hermes_cli/stderr_timestamp.py:29-31);
* errors.log lines in ``%(asctime)s %(levelname)s%(session_tag)s %(name)s: %(message)s`` (hermes_logging.py:107);
* the refusal tool result (tools/mcp_tool_handlers.py:133-134) and the MCP failure warning (tools/mcp_tool_discovery.py:460);
* run history rows with ``scheduled_instant`` and ``delivery_outcome`` (cron/executions.py:92-93) and job output files
  (cron/jobs.py:2-3);
* backups (hermes_cli/web_routers/ops.py:577-600) and the checkpoint branch name (tools/checkpoint_manager.py:218-220).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import time
import uuid
from datetime import datetime, timezone

import hermes_fixture as hf

FS = "@modelcontextprotocol/server-filesystem@2026.8.31"


def local_stamp(epoch: float) -> str:
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S,%f")[:23]


def iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def folder(home) -> pathlib.Path:
    path = pathlib.Path(home) / "practice-folder"
    path.mkdir(parents=True, exist_ok=True)
    return path


def server_block(name, args=None, command="npx", trust=None, include=None, exclude=None, enabled=None) -> str:
    lines = [f"  {name}:", f"    command: {command}"]
    if args is not None:
        lines.append("    args: [" + ", ".join(json.dumps(a) for a in args) + "]")
    if enabled is not None:
        lines.append(f"    enabled: {'true' if enabled else 'false'}")
    if trust is not None:
        lines.append(f"    trust: {trust}")
    if include is not None or exclude is not None:
        lines.append("    tools:")
        if include is not None:
            lines.append("      include: [" + ", ".join(include) + "]")
        if exclude is not None:
            lines.append("      exclude: [" + ", ".join(exclude) + "]")
    return "\n".join(lines)


def write_servers(home, *blocks, extra="") -> None:
    """A config.yaml like the fixture's, with these connectors as its whole mcp_servers block."""
    base = hf.CONFIG.split("mcp_servers:")[0]
    rest = hf.CONFIG.split("approvals:", 1)[1]
    text = base + "mcp_servers:\n" + "\n".join(blocks) + "\n" + extra + "approvals:" + rest
    hf.write_config(home, text)


def set_config_text(home, old, new) -> None:
    path = pathlib.Path(home) / "config.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def log(home, name, lines) -> None:
    path = pathlib.Path(home) / "logs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line + "\n")


def banner(home, server, epoch) -> None:
    log(home, "mcp-stderr.log", ["", f"{local_stamp(epoch)} ===== starting MCP server '{server}' ====="])


def refusal(tool, server) -> str:
    return json.dumps({"error": f"The user did not approve running write-capable MCP tool '{tool}' on untrusted server "
                                f"'{server}'. The command was NOT run. Do not retry without explicit user direction."})


def mcp_failure_line(epoch, server, command) -> str:
    return f"{local_stamp(epoch)} WARNING tools.mcp_tool: Failed to connect to MCP server '{server}' (command={command}): No such file"


def touch_back(path, epoch) -> None:
    import os

    os.utime(path, (epoch, epoch))


def runs_db(home, rows, version="0.22.4") -> None:
    """cron/executions.db with the later columns, and these rows. ``version="0.23.0"`` uses that release's table,
    which also allows the ``cancelled`` and ``missed`` statuses."""
    cron = pathlib.Path(home) / "cron"
    cron.mkdir(parents=True, exist_ok=True)
    path = cron / "executions.db"
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(hf.schema("cron_executions.sql") if version == "0.22.4"
                      else (hf.DATA.parent / f"hermes-{version}" / "cron_executions.sql").read_text(encoding="utf-8"))
    con.executescript(hf.schema("cron_executions_columns.sql"))
    for row in rows:
        full = {"id": uuid.uuid4().hex, "source": "builtin", "process_id": "p1", "pid": 4242, "status": "completed", **row}
        names = ",".join(full)
        con.execute(f"INSERT INTO executions({names}) VALUES ({','.join('?' * len(full))})", tuple(full.values()))
    con.commit()
    con.close()


def output_files(home, job_id, count) -> None:
    out = pathlib.Path(home) / "cron" / "output" / job_id
    out.mkdir(parents=True, exist_ok=True)
    for n in range(count):
        (out / f"2026-10-19_{n:02d}0000.md").write_text("For Yusuf:\n- 3 late\n", encoding="utf-8")


def backup(home, epoch, quick=False) -> pathlib.Path:
    if quick:
        path = pathlib.Path(home) / "state-snapshots" / f"20261019-{int(epoch)}-before-fix"
        path.mkdir(parents=True)
    else:
        path = pathlib.Path(home) / "backups" / f"hermes-backup-20261019-{int(epoch)}-ab12.zip"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"PK\x05\x06" + b"\0" * 18)
    touch_back(path, epoch)
    return path


def checkpoint_branch(home, practice_folder) -> pathlib.Path:
    digest = hashlib.sha256(str(pathlib.Path(practice_folder).resolve()).encode()).hexdigest()[:16]
    ref = pathlib.Path(home) / "checkpoints" / "store" / "refs" / "hermes" / digest
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text("0" * 40 + "\n", encoding="utf-8")
    return ref


def now() -> float:
    return time.time()
