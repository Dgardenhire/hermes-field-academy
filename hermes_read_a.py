"""More read-only readers for a practice profile, for Foundations missions 1, 2, 4, 5 and 6 (0.9 M6, part A).

Same rules as hermes_read.py, whose guards they use: bounded reads, no links followed, nothing written, no program run,
no Hermes import, and ``.env``, ``auth.json``, ``mcp-tokens/``, ``pairing/`` and ``platforms/`` never read. Shapes are
copied from the Hermes 0.22.4 source:

* ``SOUL.md`` in the profile home (hermes_cli/profiles.py ``_CLONE_CONFIG_FILES``);
* a chat's saved instructions: ``sessions.system_prompt_hash`` joined to ``system_prompts.prompt``
  (hermes_state_common.py SCHEMA_SQL; ``sessions.system_prompt`` is NULL now);
* a skill's whole ``SKILL.md`` and the skills sidecar ``skills/.usage.json`` (tools/skill_usage.py: ``created_by``
  is ``agent`` for a background-review save, ``learn`` for one asked for in a chat, ``created_at`` ISO time);
* steering notes: ``session_admissions.intent = 'steer'`` (hermes_state_common.py);
* the files of the practice folder, ``<home>/practice-folder/``, by size, time and whether they can be written;
* a chat's first trip to the model, from ``sessions.api_call_count`` and its token columns.

Text read here stays in this process for comparison. Anything kept is scrubbed by the caller.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from . import hermes_read, scrub, yaml_keys

FOLDER = "practice-folder"
MAX_FILES = 200


def _text(home, rel, limit=256 * 1024):
    found = hermes_read._read_text(home, rel, limit)
    if found is None:
        return None
    text, digest, mtime = found
    return {"text": text, "sha256": digest, "mtime": mtime, "rel_path": rel}


def soul(home) -> dict:
    """The profile's SOUL.md: text (for comparison), time and hash."""
    found = _text(home, "SOUL.md", 64 * 1024)
    if found is None:
        return hermes_read.unreadable("The practice profile has no SOUL.md Field Academy could read.")
    return {"readable": True, **found}


def system_prompt_text(home, session_id):
    """The instructions a chat started with, or None. In-process only."""
    conn = hermes_read._db(home, "state.db")
    if conn is None:
        return None
    try:
        row = conn.execute("SELECT p.prompt FROM sessions s JOIN system_prompts p ON p.hash = s.system_prompt_hash WHERE s.id = ?",
                           (str(session_id),)).fetchone()
        return str(row[0])[:400_000] if row and row[0] is not None else None
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def skill_text(home, rel: str) -> dict:
    """A whole SKILL.md (bounded), for the four-parts check."""
    if not str(rel).startswith("skills/") or not str(rel).endswith("/SKILL.md"):
        return hermes_read.unreadable("That isn't a skill file.")
    found = _text(home, rel, 128 * 1024)
    if found is None:
        return hermes_read.unreadable("The skill file could not be read.")
    return {"readable": True, **found}


def skill_usage(home) -> dict:
    """Name -> {created_by, created_at, last_patched_at, state} from skills/.usage.json. Empty when there is none."""
    found = _text(home, "skills/.usage.json", 2 * 1024 * 1024)
    if found is None:
        return {}
    try:
        data = json.loads(found["text"])
    except ValueError:
        return {}
    out = {}
    for name, rec in list(data.items())[:500] if isinstance(data, dict) else []:
        if isinstance(rec, dict):
            out[str(name)[:120]] = {k: rec.get(k) for k in ("created_by", "created_at", "last_patched_at", "state")}
    return out


def steers(home, session_id) -> int:
    """How many /steer notes Hermes admitted into a chat, from session_admissions; a typed /steer message counts too."""
    conn = hermes_read._db(home, "state.db")
    if conn is None:
        return 0
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        count = 0
        if "session_admissions" in tables:
            count += int(conn.execute("SELECT COUNT(*) FROM session_admissions WHERE target_session_id = ? AND intent = 'steer'",
                                      (str(session_id),)).fetchone()[0])
        count += int(conn.execute("SELECT COUNT(*) FROM messages WHERE session_id = ? AND role = 'user' AND content LIKE '/steer%'",
                                  (str(session_id),)).fetchone()[0])
        return count
    except sqlite3.Error:
        return 0
    finally:
        conn.close()


def work_files(home, sub: str = "") -> dict:
    """The practice folder's files: name, size, time and whether they can be written. No text."""
    rel = f"{FOLDER}/{sub}".rstrip("/")
    root = hermes_read.safe_path(home, rel)
    if root is None or not root.is_dir():
        return {"readable": root is not None, "files": []}
    out = []
    for path in sorted(root.iterdir())[:MAX_FILES]:
        if path.is_symlink() or not path.is_file():
            continue
        try:
            st = path.stat()
        except OSError:
            continue
        flags = getattr(st, "st_flags", 0)
        locked = bool(flags & 0x2) or not os.access(path, os.W_OK)  # 0x2 is UF_IMMUTABLE, Finder's Locked
        out.append({"name": path.name, "rel_path": f"{rel}/{path.name}", "size": st.st_size, "mtime": st.st_mtime, "locked": locked})
    return {"readable": True, "files": out}


def work_file(home, rel: str) -> dict:
    """One practice-folder file's text (bounded), time and whether it can be written."""
    if not str(rel).startswith(FOLDER + "/"):
        return hermes_read.unreadable("That isn't in the practice folder.")
    found = _text(home, rel, 256 * 1024)
    if found is None:
        return {"readable": True, "exists": False, "rel_path": rel}
    path = Path(home) / rel
    flags = getattr(path.stat(), "st_flags", 0)
    return {"readable": True, "exists": True, "locked": bool(flags & 0x2) or not os.access(path, os.W_OK), **found}


def first_trip(home, session) -> dict:
    """The tokens of a chat's first trip to the model: the fixed part plus the message.

    Hermes stores totals per chat, not per trip, so a chat that made exactly one call (a one-word hello, no tools)
    gives its first trip exactly: input plus cache read plus cache write. Anything else can't be read on its own.
    """
    calls = session.get("api_call_count")
    if calls == 1:
        total = sum(int(session.get(k) or 0) for k in ("input_tokens", "cache_read_tokens", "cache_write_tokens"))
        if total > 0:
            return {"readable": True, "tokens": total, "how": "one trip to the model, read from the chat's token count"}
    return hermes_read.unreadable("That chat made more than one trip, so its first trip can't be read on its own.")


def models(home) -> dict:
    """Which model each job in the profile would use, by name only: main, side jobs (auxiliary.*) and helper agents."""
    found = hermes_read._read_text(home, "config.yaml")
    if found is None:
        return hermes_read.unreadable("No config.yaml in the practice profile.")
    tree = yaml_keys.parse(found[0])

    def clean(value):
        if isinstance(value, str) and value.strip() and "$" not in value:
            return scrub.scrub(value.strip(), 120)
        return ""

    main = clean(yaml_keys.get(tree, "model.default")) or clean(yaml_keys.get(tree, "model.model")) or (
        clean(yaml_keys.get(tree, "model")) if isinstance(yaml_keys.get(tree, "model"), str) else "")
    aux = {}
    branch = yaml_keys.get(tree, "auxiliary")
    if isinstance(branch, dict):
        for slot, node in list(branch.items())[:40]:
            if isinstance(node, dict):
                aux[str(slot)[:40]] = clean(node.get("model")) or "auto"
    return {"readable": True, "main": main, "auxiliary": aux, "subagents": clean(yaml_keys.get(tree, "delegation.model"))}


def disabled_skills(home) -> dict:
    """Skill names on the profile's global switched-off list, ``skills.disabled``: what the Capabilities Skills tab
    writes (hermes_cli/skills_config.save_disabled_skills with no platform). Per-platform lists are left out: they
    hide a skill only on that platform. A missing list means nothing is switched off."""
    found = hermes_read._read_text(home, "config.yaml")
    if found is None:
        return hermes_read.unreadable("No config.yaml in the practice profile.")
    value = yaml_keys.get(yaml_keys.parse(found[0]), "skills.disabled")
    if isinstance(value, str) and value.strip().startswith("["):  # a list set from the command line is kept as a JSON string
        try:
            value = json.loads(value)
        except ValueError:
            pass
    names = [value] if isinstance(value, str) else value if isinstance(value, list) else []
    return {"readable": True, "disabled": {str(n).strip() for n in names[:500] if isinstance(n, str) and n.strip()}}


def connectors(home) -> dict:
    """Connector names, on or off, and the package each runs (names only)."""
    found = hermes_read._read_text(home, "config.yaml")
    if found is None:
        return hermes_read.unreadable("No config.yaml in the practice profile.")
    branch = yaml_keys.get(yaml_keys.parse(found[0]), "mcp_servers")
    out = {}
    if isinstance(branch, dict):
        for name, node in list(branch.items())[:50]:
            if not isinstance(node, dict):
                continue
            args = node.get("args") if isinstance(node.get("args"), list) else []
            package = next((str(a) for a in args if isinstance(a, str) and a.startswith("@")), "")
            out[str(name)[:60]] = {"enabled": node.get("enabled") is not False, "package": scrub.scrub(package, 120)}
    return {"readable": True, "connectors": out}
