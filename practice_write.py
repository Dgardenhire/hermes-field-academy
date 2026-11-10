"""The only code in Field Academy that writes outside its own data folder.

It writes into one place: a practice profile Field Academy planned and recorded itself (``f_practice``), before that
profile's first chat. Three files, and named keys only:

* ``config.yaml``: the keys in WRITABLE_KEYS, through ``yaml_keys.set_values``, which changes only those lines.
  ``terminal.cwd`` may only be set to the practice profile's own folder, so a chat opened there with
  ``host.newChat(profile)`` works in that folder (Hermes's ``_completion_cwd`` prefers a named profile's configured
  ``terminal.cwd`` over the app's inherited workspace);
* ``memories/MEMORY.md`` and ``memories/USER.md``: whole-file prefills, entries joined with Hermes's ``"\\n§\\n"``.
* ``practice-folder/...``: sample text files for missions 7 to 11 (orders, CSVs, notes), through
  ``write_practice_file``, at most two folders deep inside the practice folder;
* for missions 7 to 11, the keys in WRITABLE_KEYS_B: connector entries, ``agent.disabled_toolsets``,
  ``command_allowlist`` and ``fallback_providers`` (cleared for mission 10, so a broken model isn't hidden).

Every write refuses when: the profile isn't recorded (status ``ready`` or ``planted``) at exactly this path; the
folder, the file or the ``memories`` folder is a link; the profile's backend is up (``gateway.pid``); or anyone has
sent a message in it (Hermes freezes memory per chat, and a planted problem must be in place before the first one).
Writes go through a fresh temporary file in the same folder, then ``os.replace``, the way Cabinet writes SOUL.md.

Never written, whatever asks: any other file, ``.env``, ``auth.json``, ``mcp-tokens/``, ``pairing/``, ``platforms/``,
any profile Field Academy didn't record, and the learner's own profiles.
"""

from __future__ import annotations

import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

from . import hermes_read, practice, yaml_keys

ALLOWED_FILES = ("config.yaml", "memories/MEMORY.md", "memories/USER.md")
WRITABLE_KEYS = (
    re.compile(r"^memory\.write_approval$"),
    re.compile(r"^skills\.write_approval$"),
    re.compile(r"^approvals\.(?:mode|timeout|cron_mode)$"),
    re.compile(r"^checkpoints\.enabled$"),
    re.compile(r"^cron\.model$"),
    re.compile(r"^delegation\.model$"),
    re.compile(r"^model\.default$"),
    re.compile(r"^mcp_servers\.[A-Za-z0-9_-]+\.trust$"),
    re.compile(r"^terminal\.cwd$"),
)
# Missions 7 to 11: connector entries (command, arguments, on/off, trust, tool filters), switched-off toolsets and the
# always-allow list, practice profiles only, before the first chat.
WRITABLE_KEYS_B = (
    re.compile(r"^mcp_servers\.[A-Za-z0-9_-]+\.(?:command|args|enabled|trust)$"),
    re.compile(r"^mcp_servers\.[A-Za-z0-9_-]+\.tools\.(?:include|exclude)$"),
    re.compile(r"^agent\.disabled_toolsets$"),
    re.compile(r"^command_allowlist$"),
    re.compile(r"^fallback_providers$"),
    # The Intermediate core missions: how many helper agents may run at once (f.delegation).
    re.compile(r"^delegation\.max_concurrent_children$"),
)
WRITABLE_STATUS = ("ready", "planted")
DELIM = hermes_read.DELIM


class Refused(ValueError):
    """A write Field Academy will not make. The message is safe to show the learner."""


def _same_place(a, b) -> bool:
    return Path(a).resolve(strict=False) == Path(b).resolve(strict=False)


def guard(home, row) -> Path:
    """Raise Refused unless ``home`` is a recorded, unopened practice profile at its recorded path."""
    home = Path(home)
    if not row or not practice.valid_name(row.get("name", "")):
        raise Refused("Field Academy writes only into a practice profile it made.")
    if row.get("status") not in WRITABLE_STATUS:
        raise Refused(f"{row['name']} is {row.get('status') or 'not recorded'}, so Field Academy won't write into it.")
    if not row.get("path") or not _same_place(row["path"], home):
        raise Refused("That folder is not the practice profile Field Academy recorded.")
    if home.is_symlink() or not home.is_dir():
        raise Refused("The practice profile's folder is missing or is a link.")
    expected = practice.practice_home(row["name"], root=home.parent.parent)
    if not _same_place(expected, home):
        raise Refused("The practice profile is not inside Hermes's profiles folder.")
    if not practice.is_ours(row, home):
        raise Refused(f"The folder called {row['name']} isn't the practice profile Field Academy made, so Field Academy won't write into it.")
    if hermes_read.gateway_running(home):
        raise Refused("The practice profile's chat backend is running, so Field Academy won't change its files now.")
    said = hermes_read.user_message_count(home)
    if said is None:
        raise Refused("Field Academy couldn't read the practice profile's chat records, so it won't write into it.")
    if said:
        raise Refused("Someone has already chatted in the practice profile. Reset it to start over.")
    return home


def _target(home: Path, rel: str) -> Path:
    if rel not in ALLOWED_FILES:
        raise Refused(f"Field Academy never writes {rel}.")
    path = home / rel
    if path.parent != home and path.parent.is_symlink():
        raise Refused(f"{path.parent.name} is a link, so Field Academy won't write into it.")
    if path.is_symlink():
        raise Refused(f"{rel} is a link, so Field Academy won't write it.")
    return path


def _write_atomic(path: Path, text: str) -> None:
    """A fresh temporary file in the same folder, then swapped in. A link planted beside it can't redirect the write."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".field-academy")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        try:
            os.chmod(tmp, stat.S_IMODE(os.stat(path).st_mode))
        except OSError:
            pass
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ------------------------------------------------- missions 1, 2, 5 and 6 (0.9 M6, part A) --
#
# Four more writes, each as narrow as the one it serves, all before the practice profile's first chat:
#
# * work files the mission's jobs read, under ``<home>/practice-folder/`` only (mission 1's warm-up and job sheets,
#   mission 2's job file), and the Read-only/Locked flag on one of them (mission 1's locked output);
# * a skill Field Academy wrote by hand, at ``skills/academy-<name>/SKILL.md`` only (mission 5);
# * one connector block under ``mcp_servers:`` in config.yaml, read back before it is kept (mission 2);
# * a notes file in Field Academy's own data folder, outside every profile (mission 6's shared "street").
#
# Clearing a lock Field Academy set is the one write allowed after the first chat: before the profile is deleted, so
# Hermes can remove the folder (a Locked file can't be deleted on a Mac, nor a Read-only one on Windows).

WORK_FILE = re.compile(r"^practice-folder/(?:[a-z0-9][a-z0-9-]{0,40}/)?[a-z0-9][a-z0-9._-]{0,60}\.(?:md|txt|csv)$")
SKILL_FILE = re.compile(r"^skills/academy-[a-z0-9][a-z0-9-]{0,50}/SKILL\.md$")
SERVER_NAME = re.compile(r"^academy-[a-z0-9-]{1,40}$")
SHARED_FILE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}\.txt$")


def _plain_folders(home: Path, rel: str) -> Path:
    """``home/rel``, making its folders, refusing any link on the way."""
    path = home / rel
    current = home
    for part in Path(rel).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise Refused(f"{part} is a link, so Field Academy won't write into it.")
        current.mkdir(exist_ok=True)
    if path.is_symlink():
        raise Refused(f"{rel} is a link, so Field Academy won't write it.")
    return path


def write_work_file_a(home, row, rel: str, text: str) -> dict:
    """A file a practice job reads, under the practice profile's ``practice-folder/``."""
    home = guard(home, row)
    if not WORK_FILE.match(str(rel)):
        raise Refused(f"Field Academy never writes {rel}.")
    path = _plain_folders(home, rel)
    if path.exists() and not os.access(path, os.W_OK):
        raise Refused(f"{rel} is locked.")
    _write_atomic(path, str(text))
    return {"rel_path": rel, "chars": len(str(text))}


def _set_lock(path: Path, locked: bool) -> None:
    if sys.platform == "darwin" and hasattr(os, "chflags"):
        flags = os.lstat(path).st_flags
        os.chflags(path, (flags | stat.UF_IMMUTABLE) if locked else (flags & ~stat.UF_IMMUTABLE))
        return
    mode = stat.S_IMODE(os.lstat(path).st_mode)
    os.chmod(path, (mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)) if locked else (mode | stat.S_IWUSR))


def lock_work_file_a(home, row, rel: str) -> dict:
    """Mark a work file Locked (Mac), Read-only (Windows) or not writable (Linux), as the learner's OS would show it."""
    home = guard(home, row)
    if not WORK_FILE.match(str(rel)):
        raise Refused(f"Field Academy never locks {rel}.")
    path = home / rel
    if path.is_symlink() or not path.is_file():
        raise Refused(f"{rel} isn't a plain file.")
    _set_lock(path, True)
    return {"rel_path": rel, "locked": True}


def unlock_work_file_a(home, row, rel: str) -> dict:
    """Clear a lock Field Academy set, so the profile can be deleted. Its recorded profile only, at its path."""
    home = Path(home)
    if not row or not practice.valid_name(row.get("name", "")) or row.get("status") not in ("ready", "planted", "removing"):
        raise Refused("Field Academy unlocks files only in a practice profile it made.")
    if not row.get("path") or not _same_place(row["path"], home) or home.is_symlink() or not practice.is_ours(row, home):
        raise Refused("That folder is not the practice profile Field Academy recorded.")
    if not WORK_FILE.match(str(rel)):
        raise Refused(f"Field Academy never unlocks {rel}.")
    path = home / rel
    if path.is_symlink() or not path.is_file():
        return {"rel_path": rel, "locked": False}
    _set_lock(path, False)
    return {"rel_path": rel, "locked": False}


def write_skill_a(home, row, rel: str, text: str) -> dict:
    """A skill Field Academy wrote by hand, ``skills/academy-<name>/SKILL.md``."""
    home = guard(home, row)
    if not SKILL_FILE.match(str(rel)):
        raise Refused(f"Field Academy never writes {rel}.")
    path = _plain_folders(home, rel)
    _write_atomic(path, str(text))
    return {"rel_path": rel, "chars": len(str(text))}


def add_mcp_server_a(home, row, name: str, command: str, args, enabled: bool = True) -> dict:
    """Add one connector, ``mcp_servers.<name>``, to config.yaml. Every other setting must read back unchanged."""
    home = guard(home, row)
    if not SERVER_NAME.match(str(name)):
        raise Refused("Field Academy names its own connectors academy-something.")
    args = [str(a) for a in (args or [])]
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,40}", str(command)) or any("\n" in a or len(a) > 400 for a in args) or len(args) > 10:
        raise Refused("That connector command can't be written.")
    path = _target(home, "config.yaml")
    text = ""
    if path.exists():
        with open(path, "rb") as handle:
            text = handle.read(1024 * 1024).decode("utf-8")
    before = yaml_keys.parse(text)
    servers = yaml_keys.get(before, "mcp_servers")
    if isinstance(servers, dict) and name in servers:
        raise Refused(f"A connector named {name} is already there.")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").split("\n")
    top = next((i for i, line in enumerate(lines) if re.match(r"^mcp_servers\s*:", line)), None)
    indent = "  "
    if top is not None:
        rest = lines[top].split(":", 1)[1].split("#", 1)[0].strip()
        if rest not in ("", "{}"):
            raise Refused("The connectors setting isn't laid out in a way Field Academy can add to.")
        lines[top] = "mcp_servers:"
        child = next((line for line in lines[top + 1:] if line.strip() and not line.lstrip().startswith("#")), "")
        if child[:1] == " ":
            indent = child[:len(child) - len(child.lstrip())]
    block = [f"{indent}{name}:", f"{indent}  command: {command}", f"{indent}  args: {json.dumps(args, ensure_ascii=False)}",
             f"{indent}  enabled: {'true' if enabled else 'false'}"]
    if top is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["mcp_servers:"] + block + [""]
    else:
        lines[top + 1:top + 1] = block
    new = newline.join(lines)
    after = yaml_keys.parse(new)
    got = yaml_keys.get(after, f"mcp_servers.{name}")
    if not isinstance(got, dict) or got.get("command") != command or got.get("args") != args or got.get("enabled") is not enabled:
        raise Refused("The connector didn't read back as written, so it wasn't added.")
    def without(tree):
        tree = dict(tree)
        servers = dict(tree.get("mcp_servers") or {}) if isinstance(tree.get("mcp_servers"), dict) else {}
        servers.pop(name, None)
        tree["mcp_servers"] = servers or None
        return {k: v for k, v in tree.items() if v not in (None, {})}
    if without(before) != without(after):
        raise Refused("Adding the connector would have changed other settings, so it wasn't added.")
    _write_atomic(path, new)
    return {"name": name, "command": command, "args": args, "enabled": enabled}


def write_shared_file_a(data_dir, rel: str, text: str) -> dict:
    """A notes file in Field Academy's own folder (``<data>/practice-files/``), outside every profile."""
    if not SHARED_FILE.match(str(rel)):
        raise Refused(f"Field Academy never writes {rel}.")
    folder = Path(data_dir) / "practice-files"
    if folder.is_symlink():
        raise Refused("The practice files folder is a link, so Field Academy won't write into it.")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / rel
    if path.is_symlink():
        raise Refused(f"{rel} is a link, so Field Academy won't write it.")
    _write_atomic(path, str(text))
    return {"path": str(path)}


def set_config(home, row, values: dict) -> dict:
    """Set named keys in the practice profile's config.yaml. Returns {key: value} as written."""
    home = guard(home, row)
    for key in values:
        if not any(pattern.match(key) for pattern in WRITABLE_KEYS + WRITABLE_KEYS_B):
            raise Refused(f"Field Academy never changes {key}.")
    if "terminal.cwd" in values and (not isinstance(values["terminal.cwd"], str) or not (_same_place(values["terminal.cwd"], home) or _same_place(values["terminal.cwd"], home / PRACTICE_FOLDER))):
        raise Refused("A practice profile's working folder can only be its own folder.")
    path = _target(home, "config.yaml")
    text = ""
    if path.exists():
        with open(path, "rb") as handle:
            text = handle.read(1024 * 1024).decode("utf-8")
    new = yaml_keys.set_values(text, values)
    _write_atomic(path, new)
    return dict(values)


def write_memory(home, row, target: str, entries) -> dict:
    """Replace MEMORY.md (target "memory") or USER.md (target "user") with these entries."""
    home = guard(home, row)
    rel = {"memory": "memories/MEMORY.md", "user": "memories/USER.md"}.get(target)
    if rel is None:
        raise Refused("Memory is either memory or user.")
    folder = home / "memories"
    if folder.is_symlink():
        raise Refused("The memories folder is a link, so Field Academy won't write into it.")
    folder.mkdir(exist_ok=True)
    path = _target(home, rel)
    clean = [str(e).strip() for e in entries if str(e).strip()]
    if any(DELIM.strip() in e.split("\n") for e in clean):
        raise Refused("A memory line can't contain Hermes's entry separator.")
    text = DELIM.join(clean)
    _write_atomic(path, text)
    return {"rel_path": rel, "entries": len(clean), "chars": len(text)}


# ------------------------------------------------------------ practice folder --
#
# Missions 7 to 11 put sample files in <home>/practice-folder: orders, CSVs, notes. Only there, only text, only before
# the first chat, through the same guard and atomic write. A link anywhere on the way is refused.

PRACTICE_FOLDER = "practice-folder"
_FOLDER_FILE = re.compile(r"^(?:[A-Za-z0-9][A-Za-z0-9 ._-]{0,60}/){0,2}[A-Za-z0-9][A-Za-z0-9 ._-]{0,80}$")


def write_practice_file(home, row, rel: str, text: str) -> dict:
    """Write one text file under the practice profile's practice-folder. Folders on the way are made as needed."""
    home = guard(home, row)
    rel = str(rel or "").replace("\\", "/")
    if not _FOLDER_FILE.match(rel) or ".." in rel.split("/"):
        raise Refused(f"Field Academy never writes {rel} in the practice folder.")
    if not isinstance(text, str) or len(text) > 64 * 1024:
        raise Refused("A practice file is short text.")
    folder = home / PRACTICE_FOLDER
    current = folder
    for part in [""] + rel.split("/")[:-1]:
        current = current / part if part else current
        if current.is_symlink():
            raise Refused("A folder in the practice folder is a link, so Field Academy won't write into it.")
        current.mkdir(exist_ok=True)
    path = folder / rel
    if path.is_symlink():
        raise Refused(f"{rel} is a link, so Field Academy won't write it.")
    if path.parent.resolve(strict=False) != current.resolve(strict=False) or not str(path.resolve(strict=False)).startswith(str(folder.resolve(strict=False))):
        raise Refused("That file would land outside the practice folder.")
    _write_atomic(path, text)
    return {"rel_path": f"{PRACTICE_FOLDER}/{rel}", "chars": len(text)}


def ensure_practice_folder(home, row) -> str:
    """Make <home>/practice-folder if it isn't there. Returns its absolute path."""
    home = guard(home, row)
    folder = home / PRACTICE_FOLDER
    if folder.is_symlink():
        raise Refused("The practice folder is a link, so Field Academy won't use it.")
    folder.mkdir(exist_ok=True)
    return str(folder.resolve())
