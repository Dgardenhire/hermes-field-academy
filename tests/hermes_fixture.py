"""Fixture Hermes homes built from the schema strings Hermes 0.22.4 itself uses (tests/data/hermes-0.22.4).

Nothing here imports or runs Hermes. Every table is made from the copied CREATE TABLE text, and every file shape
(memory entries, pending records, jobs.json, logs) follows the source lines named in facts.json. Fake secrets are
made at run time from parts.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3
import time
import uuid

DATA = pathlib.Path(__file__).resolve().parent / "data" / "hermes-0.22.4"
FACTS = json.loads((DATA / "facts.json").read_text(encoding="utf-8"))
DELIM = FACTS["entry_delimiter"]
T0 = 1792_400_000.0  # 2026-10-19, a time inside every test's window


def schema(name):
    return (DATA / name).read_text(encoding="utf-8")


def fake_key():
    return "sk" + "-" + "f1x7ure" + "0" * 14 + "abc"


def write_memory(home, memory=(), user=()):
    folder = pathlib.Path(home) / "memories"
    folder.mkdir(parents=True, exist_ok=True)
    if memory is not None:
        (folder / "MEMORY.md").write_text(DELIM.join(memory), encoding="utf-8")
    if user is not None:
        (folder / "USER.md").write_text(DELIM.join(user), encoding="utf-8")


def stage_pending(home, subsystem="memory", action="add", content="", origin="foreground", created_at=None):
    """A record exactly as tools/write_approval.stage_write() lays it down."""
    pid = uuid.uuid4().hex[:8]
    record = {
        "id": pid, "subsystem": subsystem, "action": action, "summary": f"{action} {content[:40]}".strip(),
        "origin": origin, "created_at": created_at if created_at is not None else T0,
        "payload": {"action": action, "target": "memory", "content": content},
    }
    folder = pathlib.Path(home) / "pending" / subsystem
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{pid}.json").write_text(json.dumps(record), encoding="utf-8")
    return record


def state_db(home):
    path = pathlib.Path(home) / "state.db"
    con = sqlite3.connect(path)
    con.executescript(schema("state_schema.sql"))
    if not con.execute("SELECT 1 FROM schema_version").fetchone():
        con.execute("INSERT INTO schema_version(version) VALUES (?)", (FACTS["state_schema_version"],))
    con.commit()
    return con


def add_session(con, sid=None, started_at=T0, title="", model="anthropic/claude-sonnet-4.6", prompt="", **cols):
    sid = sid or f"20261019_{uuid.uuid4().hex[:8]}"
    phash = ""
    if prompt:
        import hashlib

        phash = hashlib.sha256(prompt.encode()).hexdigest()
        con.execute("INSERT OR IGNORE INTO system_prompts(hash, prompt) VALUES (?, ?)", (phash, prompt))
    fields = {"id": sid, "source": "desktop", "started_at": started_at, "title": title, "model": model,
              "system_prompt_hash": phash or None, **cols}
    names = ",".join(fields)
    con.execute(f"INSERT INTO sessions({names}) VALUES ({','.join('?' * len(fields))})", tuple(fields.values()))
    con.commit()
    return sid


def add_message(con, sid, role, content, timestamp, tool_name=None, **cols):
    fields = {"session_id": sid, "role": role, "content": content, "timestamp": timestamp, "tool_name": tool_name, **cols}
    names = ",".join(fields)
    cur = con.execute(f"INSERT INTO messages({names}) VALUES ({','.join('?' * len(fields))})", tuple(fields.values()))
    con.commit()
    return cur.lastrowid


def add_usage(con, sid, model, task="", **cols):
    fields = {"session_id": sid, "model": model, "task": task, **cols}
    names = ",".join(fields)
    con.execute(f"INSERT INTO session_model_usage({names}) VALUES ({','.join('?' * len(fields))})", tuple(fields.values()))
    con.commit()


def memory_full_error(current=2150, limit=2200, size=80):
    over = current + len(DELIM) + size - limit
    return json.dumps({"success": False, "error": FACTS["memory_full_error"].format(current=current, limit=limit, size=size, over=over),
                       "current_entries": ["..."], "usage": f"{current:,}/{limit:,}"})


def write_jobs(home, jobs):
    folder = pathlib.Path(home) / "cron"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "jobs.json").write_text(json.dumps({"jobs": jobs, "updated_at": "2026-10-19T09:00:00+00:00"}), encoding="utf-8")


def job(job_id, name, **extra):
    base = {
        "id": job_id, "name": name, "prompt": "Summarise the inbox", "skills": [], "skill": None, "model": None, "provider": None,
        "schedule": {"kind": "cron", "expr": "0 9 * * *", "display": "0 9 * * *"}, "schedule_display": "0 9 * * *",
        "enabled": True, "state": "scheduled", "created_at": "2026-10-19T09:00:00+00:00", "next_run_at": "2026-10-20T09:00:00+00:00",
        "last_run_at": None, "last_status": None, "last_error": None, "last_delivery_error": None, "last_delivery_unverified": None,
        "last_failure": None, "failure_streak": 0, "deliver": "local", "origin": None, "enabled_toolsets": None, "workdir": None,
    }
    base.update(extra)
    return base


def executions_db(home, rows=(), incidents=()):
    folder = pathlib.Path(home) / "cron"
    folder.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(folder / "executions.db")
    con.executescript(schema("cron_executions.sql"))
    con.executescript(schema("cron_incidents.sql"))
    for row in rows:
        full = {"id": uuid.uuid4().hex, "source": "scheduler", "process_id": "p1", "pid": 4242, "status": "completed",
                "claimed_at": row.get("started_at") or "2026-10-19T09:00:00+00:00", **row}
        names = ",".join(full)
        con.execute(f"INSERT INTO executions({names}) VALUES ({','.join('?' * len(full))})", tuple(full.values()))
    for row in incidents:
        full = {"id": uuid.uuid4().hex, "error_sig": "sig", "state": "open", "first_seen_at": "2026-10-19T09:00:00+00:00",
                "last_seen_at": "2026-10-19T09:00:00+00:00", "error": "boom", **row}
        names = ",".join(full)
        con.execute(f"INSERT INTO cron_incidents({names}) VALUES ({','.join('?' * len(full))})", tuple(full.values()))
    con.commit()
    con.close()


def write_config(home, text):
    (pathlib.Path(home) / "config.yaml").write_text(text, encoding="utf-8")


CONFIG = """# Hermes config (fixture)
model:
  default: anthropic/claude-sonnet-4.6
  provider: openrouter
providers:
  openrouter:
    model: anthropic/claude-sonnet-4.6
    api_key: ${OPENROUTER_API_KEY}
toolsets:
- hermes-cli
- web
mcp_servers:
  github:
    enabled: true
    trust: untrusted
    transport: http
    url: https://user:pw@mcp.example.com:8443/sse?token=abc
    headers:
      Authorization: Bearer ${GITHUB_TOKEN}
approvals:
  mode: manual
  timeout: 60
checkpoints:
  enabled: false
  max_snapshots: 50
memory:
  memory_enabled: true
  user_profile_enabled: true
  write_approval: false
  memory_char_limit: 2200
  user_char_limit: 1375
  provider: ''
skills:
  write_approval: false
delegation:
  model: ''
  provider: ''
cron:
  model: ''
fallback_providers:
- provider: openrouter
  model: openai/gpt-5-mini
compression:
  threshold: 0.5
sessions:
  auto_prune: false
  retention_days: 90
agent:
  system_prompt: |
    memory:
      write_approval: true
    Be brief.
"""


def build_home(home, *, secrets=True):
    """A small practice home with something in every place Field Academy reads."""
    home = pathlib.Path(home)
    home.mkdir(parents=True, exist_ok=True)
    (home / "SOUL.md").write_text("Field Academy practice profile.\n", encoding="utf-8")
    write_config(home, CONFIG)
    write_memory(home, ["Harbor Bakery uses QuickBooks Online; the other five use Xero."], ["Ada prefers short answers."])
    skill = home / "skills" / "weekly-invoice"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: weekly-invoice\ndescription: Build the weekly invoice batch\n---\n\n1. Export.\n", encoding="utf-8")
    (skill / "references").mkdir()
    (skill / "references" / "SKILL.md").write_text("---\nname: not-a-skill\n---\n", encoding="utf-8")
    (home / "skills" / "node_modules" / "x").mkdir(parents=True)
    (home / "skills" / "node_modules" / "x" / "SKILL.md").write_text("---\nname: hidden\n---\n", encoding="utf-8")
    logs = home / "logs"
    logs.mkdir()
    (logs / "agent.log").write_text(
        "2026-10-19 09:00:01,000 INFO agent: turn started\n"
        f"2026-10-19 09:00:02,000 INFO agent: provider key {fake_key()}\n"
        "2026-10-19 09:00:03,000 INFO tools.memory: memory add ok\n", encoding="utf-8")
    (logs / "errors.log").write_text("2026-10-19 09:00:04,000 WARNING tools.memory: over budget\n", encoding="utf-8")
    (home / "checkpoints" / "store").mkdir(parents=True)
    (home / "checkpoints" / "store" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    if secrets:
        # The credential files Hermes mirrors into a new profile. Field Academy must never read them.
        (home / ".env").write_text("OPENROUTER_API_KEY=" + fake_key() + "\n", encoding="utf-8")
        (home / "auth.json").write_text(json.dumps({"active": "openrouter", "k": fake_key()}), encoding="utf-8")
    con = state_db(home)
    sid = add_session(con, started_at=T0, title="Save a fact", prompt="SOUL\n\nMEMORY (your personal notes)\n...", input_tokens=5100,
                      output_tokens=120, cache_write_tokens=4800, api_call_count=1, estimated_cost_usd=0.012, message_count=4)
    add_message(con, sid, "user", "Save to memory: Harbor Bakery uses QuickBooks Online.", T0 + 1)
    add_message(con, sid, "assistant", "", T0 + 2, tool_calls=json.dumps([{"function": {"name": "memory"}}]))
    add_message(con, sid, "tool", json.dumps({"success": True, "message": "Entry added."}), T0 + 3, tool_name="memory")
    add_message(con, sid, "assistant", "Saved.", T0 + 4)
    add_usage(con, sid, "anthropic/claude-sonnet-4.6", api_call_count=1, input_tokens=5100, output_tokens=120, estimated_cost_usd=0.012)
    add_usage(con, sid, "openai/gpt-5-mini", task="background_review", api_call_count=1, input_tokens=900, output_tokens=40, estimated_cost_usd=0.001)
    con.close()
    write_jobs(home, [job("job-a1", "Morning brief")])
    executions_db(home, rows=[
        {"job_id": "job-a1", "status": "completed", "started_at": "2026-10-19T09:00:00+00:00", "finished_at": "2026-10-19T09:00:40+00:00"},
        {"job_id": "job-a1", "status": "failed", "started_at": "2026-10-20T09:00:00+00:00", "finished_at": "2026-10-20T09:00:05+00:00", "error": "provider 401"},
    ], incidents=[{"job_id": "job-a1", "error": "provider 401", "failure_type": "auth"}])
    return home


def tree_state(root):
    """Every file under root with its size, time and bytes hash, to prove nothing was written."""
    import hashlib

    out = {}
    root = pathlib.Path(root)
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.name.endswith(("-wal", "-shm", "-journal")):
            st = path.stat()
            out[path.relative_to(root).as_posix()] = (st.st_size, st.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    return out


def now_epoch():
    return time.time()
