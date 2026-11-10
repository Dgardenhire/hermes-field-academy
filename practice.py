"""Where a Field Academy practice profile lives, worked out without importing Hermes.

Hermes resolves a home as override, then ``HERMES_HOME``, then the platform default: ``~/.hermes``, or
``%LOCALAPPDATA%\\hermes`` on Windows (``hermes_constants.py`` 0.22.4, ``_platform_default_hermes_home`` and
``_hermes_root_of``). In profile mode ``HERMES_HOME`` is ``<root>/profiles/<name>``. This plugin's backend runs inside
the active profile's process, so its own ``HERMES_HOME`` may be a profile; the root is what holds ``profiles/``.

The rule is copied here, not imported: a plugin may not import Hermes's private modules.

A practice profile's folder is only ever ``<root>/profiles/academy-practice[-N|-b[-N]]``. Anything else, a link in
its place, or a ``profiles`` folder that is itself a link, is refused.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

PREFIX = "academy-practice"
# academy-practice, academy-practice-2, academy-practice-b, academy-practice-b-2. Lower case only, as Hermes requires.
NAME = re.compile(r"^academy-practice(?:-b)?(?:-[2-9]|-[1-9][0-9])?$")


def _flavor(platform: str):
    if platform == sys.platform:
        return Path
    return PureWindowsPath if platform == "win32" else PurePosixPath


def _expand(text: str, environ, flavor):
    """``~`` and ``$VAR``/``%VAR%`` from the given environment, never the process's own when another is passed."""
    def var(match):
        name = match.group(1) or match.group(2) or match.group(3)
        return environ.get(name, match.group(0))

    out = re.sub(r"%([^%]+)%|\$\{([^}]+)\}|\$([A-Za-z0-9_]+)", var, text)
    if flavor is Path:
        out = os.path.expanduser(out)
    return flavor(out)


def native_home(environ=None, platform: str | None = None, user_home=None):
    """Hermes's platform default home: ``~/.hermes`` or ``%LOCALAPPDATA%\\hermes``, plus HERMES_DATA_DIR_SUFFIX."""
    environ = os.environ if environ is None else environ
    platform = platform or sys.platform
    flavor = _flavor(platform)
    user_home = user_home or Path.home
    suffix = environ.get("HERMES_DATA_DIR_SUFFIX", "")
    if platform == "win32":
        local = environ.get("LOCALAPPDATA", "").strip()
        base = flavor(local) if local else flavor(user_home()) / "AppData" / "Local"
        return base / ("hermes" + suffix)
    return flavor(user_home()) / (".hermes" + suffix)


def _under(child, parent) -> bool:
    if isinstance(child, Path) and isinstance(parent, Path):
        child, parent = child.resolve(strict=False), parent.resolve(strict=False)
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def hermes_root(environ=None, platform: str | None = None, user_home=None):
    """The folder that holds ``profiles/``, by Hermes's own rule (``get_default_hermes_root``)."""
    environ = os.environ if environ is None else environ
    platform = platform or sys.platform
    flavor = _flavor(platform)
    native = native_home(environ, platform, user_home)
    raw = environ.get("HERMES_HOME", "").strip()
    if not raw:
        return native
    env_path = _expand(raw, environ, flavor)
    if _under(env_path, native):
        return native
    return env_path.parent.parent if env_path.parent.name == "profiles" else env_path


def shown_path(path, user_home=None) -> str:
    """A folder path as the page shows it: home-relative (``~/.hermes/profiles/academy-practice``) when it is under the
    user's home, each segment scrubbed on its own so only a key-shaped folder name is removed. The page copies the
    real path; this one is only for reading."""
    from . import scrub

    text = str(path or "")
    if not text:
        return ""
    try:
        home = Path(user_home) if user_home is not None else Path.home()
        rel = Path(text).relative_to(home)
        text = "~/" + rel.as_posix() if str(rel) != "." else "~"
    except (ValueError, RuntimeError, OSError):
        pass
    return re.sub(r"[^/\\]+", lambda m: scrub.scrub_name(m.group(0), 200), text)[:400]


def valid_name(name) -> bool:
    return isinstance(name, str) and bool(NAME.match(name))


def practice_home(name: str, root=None) -> Path:
    """``<root>/profiles/<name>`` for a Field Academy practice name. Refuses any other name and any link on the way."""
    if not valid_name(name):
        raise ValueError("Field Academy only works in its own practice profiles, named academy-practice.")
    root = Path(root) if root is not None else Path(hermes_root())
    profiles = root / "profiles"
    if profiles.is_symlink():
        raise ValueError("Hermes's profiles folder is a link, so Field Academy won't work in it.")
    target = profiles / name
    if target.is_symlink():
        raise ValueError(f"The folder for {name} is a link, so Field Academy won't touch it.")
    if target.resolve(strict=False).parent != profiles.resolve(strict=False):
        raise ValueError("That name would put the profile outside Hermes's profiles folder.")
    return target


# ------------------------------------------------------------ lifecycle ----
#
# Follows Cabinet's plan -> create -> record pattern (cab-0311/installer.py), without importing hermes_cli.profiles:
#
#   1. PLAN     This side picks a free name and builds the exact profiles.create request. Nothing is written.
#   2. CREATE   The desktop page sends that request to Hermes's own gateway (host.request, 120 s). Hermes makes the
#               profile and, by default, mirrors the current sign-in into it. Field Academy never reads those files.
#   3. RECORD   The page reports back. This side checks the folder is the one planned (inside profiles/, made after
#               the plan, carrying the planned SOUL.md, not a Hermes Bots profile, nobody has chatted in it) and keeps
#               a fingerprint of every file in it.
#   4. PLANT    Before the first chat, planted problems are written through practice_write.py, the only writer.
#   5. REMOVE   On a confirm click, evidence is snapshotted into Field Academy's own folder, the page calls
#               host.deleteProfile, and this side checks the folder is gone.

import hashlib  # noqa: E402
import json  # noqa: E402
import secrets  # noqa: E402
import stat  # noqa: E402
import time  # noqa: E402
from contextlib import contextmanager  # noqa: E402

from . import store  # noqa: E402

PLAN_SLACK_SECONDS = 5
SOUL = (
    "You are a Field Academy practice profile. A learner uses you to practise Hermes skills, and Field Academy reads "
    "this profile's files to check their work. Help with what they ask, plainly and honestly. If you did not use a "
    "tool, say so. Practice plan {token}.\n"
)
DESCRIPTION = "Field Academy practice profile"
ACTIVE = ("planned", "ready", "planted", "removing")

# Hermes's own runtime files and folders, which it writes on its own (copied from Cabinet's list, which names its
# Hermes 0.22.2 sources). Anything else counts as the profile's content.
RUNTIME_FILES = frozenset({
    "state.db", "state.db-wal", "state.db-shm", "state.db-journal", "projects.db", "projects.db-wal", "projects.db-shm",
    "projects.db-journal", "gateway.pid", "gateway.lock", "gateway_state.json", "processes.json", "active_profile",
    "auth.lock", ".env.lock", ".backup.lock", ".update_check", "errors.log", "context_length_cache.yaml",
    "models_dev_cache.json", "models_dev_cache.etag", "provider_models_cache.json", ".skills_prompt_snapshot.json",
})
RUNTIME_DIRS = frozenset({
    "logs", "cache", "image_cache", "audio_cache", "document_cache", "browser_screenshots", "checkpoints", "sandboxes",
    "source-checks", "state-snapshots", "backups", "runtime", "state", "telemetry", "desktop", "desktop-plugins",
    "bin", "installs", "tools", "models", "runtimes", "node", "assets", "pending",
})
NEVER_HASHED = frozenset({".env", "auth.json"})  # credentials: size and time only, so no hash of a key is ever kept
NEVER_HASHED_DIRS = frozenset({"mcp-tokens", "pairing", "platforms"})  # sign-in tokens Hermes keeps, same rule


def _secret_file(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return name in NEVER_HASHED or name.startswith(".env") or rel.split("/", 1)[0] in NEVER_HASHED_DIRS
MAX_FILES = 5000
HASH_LIMIT = 8 * 1024 * 1024


def _wall() -> float:
    """Real time, for comparing with the folder's own birth time. Tests replace it."""
    return time.time()


@contextmanager
def _conn():
    conn = store.connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _row(conn, name):
    row = conn.execute("SELECT * FROM f_practice WHERE name = ?", (name,)).fetchone()
    if row is None:
        return None
    out = dict(row)
    out["plan"] = json.loads(out.get("plan_json") or "{}")
    return out


def _runtime(rel: str) -> bool:
    top, _, rest = rel.partition("/")
    if top in RUNTIME_DIRS or (not rest and top in RUNTIME_FILES):
        return True
    return top == "memories" and "/" not in rest and rest.endswith(".lock")


def _scan(directory: Path) -> dict:
    found = {}

    def fail(exc):
        raise exc

    for top, dirs, files in os.walk(directory, onerror=fail, followlinks=False):
        here = Path(top)
        prefix = here.relative_to(directory).as_posix()
        prefix = "" if prefix == "." else prefix + "/"
        walk_into = []
        for name in dirs:
            if (here / name).is_symlink():
                files.append(name)
            elif not _runtime(prefix + name):
                walk_into.append(name)
        dirs[:] = walk_into
        for name in files:
            rel = prefix + name
            if _runtime(rel):
                continue
            found[rel] = os.lstat(here / name)
            if len(found) > MAX_FILES:
                raise OSError("too many files")
    return found


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(directory) -> dict:
    """Every file in the profile (except Hermes's runtime files): ["file", size, mtime_ns, sha256 or ""] or ["link", target].

    .env and auth.json are listed by size and time only: their contents are never read or hashed.
    """
    directory = Path(directory)
    out = {}
    for rel, st in sorted(_scan(directory).items()):
        path = directory / rel
        if stat.S_ISLNK(st.st_mode):
            out[rel] = ["link", os.readlink(path)]
        elif stat.S_ISREG(st.st_mode):
            hashed = st.st_size <= HASH_LIMIT and not _secret_file(rel)
            out[rel] = ["file", st.st_size, st.st_mtime_ns, _digest(path) if hashed else ""]
        else:
            out[rel] = ["other"]
    return out


def changed_files(directory, recorded: dict) -> list:
    """Paths added, removed or changed since the fingerprint was taken."""
    try:
        now = fingerprint(directory)
    except OSError:
        return ["(the folder could not be read)"]
    out = []
    for rel in sorted(set(now) | set(recorded or {})):
        if not _same_entry((recorded or {}).get(rel), now.get(rel)):
            out.append(rel)
    return out


def _same_entry(was, is_) -> bool:
    if not was or not is_ or was[0] != is_[0]:
        return False
    if was[0] == "link":
        return was[1] == is_[1]
    if was[0] != "file":
        return True
    if was[1] != is_[1]:
        return False
    if was[3] and is_[3]:
        return was[3] == is_[3]
    return was[2] == is_[2]


def _born_after(directory: Path, planned_at: float) -> bool:
    """Was the folder made after the plan? Birth time where the system records it, else the oldest entry in it."""
    try:
        st = directory.stat()
        born = getattr(st, "st_birthtime", None) or (st.st_ctime if os.name == "nt" else None)
        if born is None:
            times = [st.st_mtime]
            for n, entry in enumerate(directory.iterdir()):
                if n >= 2000:
                    break
                times.append(entry.lstat().st_mtime)
            born = min(times)
    except OSError:
        return False
    return born >= planned_at - PLAN_SLACK_SECONDS


def _same_text(path: Path, text: str) -> bool:
    if path.is_symlink():  # a link could stand in for the planned file with someone else's
        return False
    try:
        with open(path, "rb") as handle:
            on_disk = handle.read(256 * 1024).decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return on_disk.replace("\r\n", "\n") == text.replace("\r\n", "\n")


def folder_id(directory) -> list:
    """The folder's identity on disk, ``[device, inode]``, read without following a link. A profile deleted and made
    again under the same name, or another profile renamed to this name, gets a different one."""
    st = os.lstat(directory)
    return [int(st.st_dev), int(st.st_ino)]


def is_ours(row, home=None) -> bool:
    """Is the folder at the recorded path still the practice profile Field Academy made and recorded?

    Checked by the folder identity kept when the profile was recorded (``folder_id``). A record kept before 0.9.1 has
    none; then the folder must still carry this plan's token in SOUL.md. Fails closed: a folder that can't be read, a
    link, or a record with neither is not ours.
    """
    if not row or not row.get("path"):
        return False
    home = Path(home if home is not None else row["path"])
    plan_body = row.get("plan") or {}
    try:
        if home.is_symlink() or not home.is_dir():
            return False
        recorded = plan_body.get("folder_id")
        if isinstance(recorded, list) and len(recorded) == 2:
            return folder_id(home) == [int(recorded[0]), int(recorded[1])]
    except (OSError, ValueError, TypeError):
        return False
    token = str(plan_body.get("token") or "")
    if not token or (home / "SOUL.md").is_symlink():
        return False
    try:
        with open(home / "SOUL.md", "rb") as handle:
            text = handle.read(256 * 1024).decode("utf-8", errors="replace")
    except OSError:
        return False
    return f"Practice plan {token}." in text


NOT_OURS = ("The folder called {name} isn't the practice profile Field Academy made: it was deleted and made again, or "
            "another profile now has that name. Field Academy won't read, change or delete it, and has let go of its record. "
            "Make a new practice profile from the mission page.")


def _let_go(conn, name: str) -> None:
    """Forget a practice record whose folder is no longer ours, so nothing reads, writes or deletes it again. Committed
    at once, so it holds even though the caller then refuses."""
    conn.execute("UPDATE f_practice SET status = 'removed', removed_at = ? WHERE name = ?", (store.now(), name))
    conn.commit()


def require_ours(row) -> None:
    """Raise ValueError when something is at the recorded path that isn't ours, and let go of the record. A folder that
    is simply gone passes: the readers then find nothing, and a check that can't read never passes."""
    if not row or not row.get("path") or is_ours(row):
        return
    if Path(row["path"]).exists() or Path(row["path"]).is_symlink():
        with _conn() as conn:
            _let_go(conn, row["name"])
        raise ValueError(NOT_OURS.format(name=row["name"]))


def catalog_profile(directory: Path) -> bool:
    """True when Hermes's Bots catalog added this profile (bot-blueprint.yaml, or profile.yaml kind: bot-catalog).

    Fails closed: a profile.yaml that can't be read counts as a catalog profile.
    """
    if (directory / "bot-blueprint.yaml").exists() or (directory / "bot-blueprint.yaml").is_symlink():
        return True
    meta = directory / "profile.yaml"
    if not meta.exists() and not meta.is_symlink():
        return False
    if meta.is_symlink():  # never followed; counts as a catalog profile, so it's left alone
        return True
    try:
        with open(meta, "rb") as handle:
            text = handle.read(200_000).decode("utf-8", errors="replace")
    except OSError:
        return True
    return bool(re.search(r"(?m)^\s*kind:\s*['\"]?bot-catalog\b", text))


def _taken(conn, name: str, root: Path) -> bool:
    folder = root / "profiles" / name
    if folder.exists() or folder.is_symlink():
        return True
    row = _row(conn, name)
    return bool(row and row["status"] in ("ready", "planted", "removing"))


def free_name(conn, which: str, root: Path) -> str:
    base = PREFIX if which == "a" else PREFIX + "-b"
    for n in range(1, 100):
        name = base if n == 1 else f"{base}-{n}"
        if not _taken(conn, name, root):
            return name
    raise ValueError("Couldn't find a free name for a practice profile. Delete an old one in Profiles first.")


def view(row, root=None) -> dict:
    """What the page may see about a practice profile. Never the planted details."""
    if not row:
        return {}
    plan = row.get("plan") or {}
    status = row["status"]
    # The page's pill reads planned, ready, in use, removing or removed. "planted" shows as ready: whether and what
    # was planted stays hidden until Compare.
    out = {"name": row["name"], "status": "ready" if status == "planted" else status, "path": row.get("path", ""),
           "path_shown": shown_path(row.get("path", "")), "which": plan.get("which", "a"),
           "request": plan.get("request"), "model_ok": plan.get("model_ok"), "created_at": row.get("created_at", ""),
           # Set up means the lab's notes and problems are in place. Every attempt plants at least one, so this says
           # nothing about which.
           "set_up": status == "planted", "attempt_id": row.get("attempt_id")}
    if status in ("ready", "planted") and row.get("path") and not is_ours(row):
        out["replaced"] = True  # the folder at this name isn't ours any more: nothing in it is read
    elif status in ("ready", "planted") and row.get("path"):
        said = None
        try:
            from . import hermes_read

            said = hermes_read.user_message_count(row["path"])
        except Exception:  # a page view never fails on a read
            said = None
        if said:
            out["status"] = "in_use"
    return out


def listing() -> list:
    with _conn() as conn:
        rows = [_row(conn, r["name"]) for r in conn.execute("SELECT name FROM f_practice ORDER BY created_at, name")]
    return [view(r) for r in rows]


def plan(which: str = "a", attempt_id=None, root=None) -> dict:
    """Pick a free practice name and build the exact profiles.create request for the page to send."""
    if which not in ("a", "b"):
        raise ValueError("A practice profile is either the main one (a) or the second one (b).")
    root = Path(root) if root is not None else Path(hermes_root())
    with _conn() as conn:
        active = [r for r in (_row(conn, x["name"]) for x in conn.execute("SELECT name FROM f_practice"))
                  if r["status"] in ("ready", "planted", "removing") and (r["plan"].get("which", "a") == which)]
        if active:
            raise ValueError(f"{active[0]['name']} is still set up. Reset or delete it first.")
        name = free_name(conn, which, root)
        token = secrets.token_hex(6)
        soul = SOUL.format(token=token)
        request = {"method": "profiles.create", "params": {"name": name, "description": DESCRIPTION, "soul": soul,
                                                           "no_alias": True, "no_skills": True}}
        request = _plan_extra(conn, which, attempt_id, root, request)  # mission 6: B cloned from a recorded A
        body = {"which": which, "request": request, "planned_epoch": _wall(), "token": token}
        path = str(root / "profiles" / name)
        conn.execute(
            """INSERT INTO f_practice(name, path, plan_json, created_at, status, attempt_id, fingerprint_json, removed_at, planted_at)
               VALUES (?, ?, ?, ?, 'planned', ?, '', '', '')
               ON CONFLICT(name) DO UPDATE SET path = excluded.path, plan_json = excluded.plan_json, created_at = excluded.created_at,
                 status = 'planned', attempt_id = excluded.attempt_id, fingerprint_json = '', removed_at = '', planted_at = ''""",
            (name, path, json.dumps(body), store.now(), attempt_id),
        )
        return view(_row(conn, name))


def _plan_extra(conn, which, attempt_id, root, request) -> dict:
    from . import plants_a

    return plants_a.plan_extra(conn, which, attempt_id, root, request)


def confirm(name: str, result=None, root=None) -> dict:
    """Record the profile Hermes made, after checking it is exactly the one planned."""
    root = Path(root) if root is not None else Path(hermes_root())
    home = practice_home(name, root=root)
    with _conn() as conn:
        row = _row(conn, name)
        if row is None or row["status"] != "planned":
            raise ValueError(f"Field Academy has no plan waiting for {name}.")
        plan_body = row["plan"]
        if isinstance(result, dict) and result.get("path"):
            if Path(str(result["path"])).resolve(strict=False) != home.resolve(strict=False):
                raise ValueError("Hermes made the profile somewhere other than its profiles folder, so Field Academy won't use it.")
        if not home.is_dir():
            raise ValueError(f"Hermes hasn't made {name} yet. Create it, then come back.")
        if catalog_profile(home):
            raise ValueError(f"Hermes Bots added {name}, so Field Academy leaves it alone.")
        if not _born_after(home, float(plan_body.get("planned_epoch", 0))):
            raise ValueError(f"A folder called {name} was there before this plan, so Field Academy won't use it.")
        if not _same_text(home / "SOUL.md", plan_body["request"]["params"]["soul"]):
            raise ValueError(f"{name} doesn't carry the instructions Field Academy planned, so it isn't the one it asked for.")
        from . import hermes_read

        said = hermes_read.user_message_count(home)
        if said is None or said:
            raise ValueError(f"Someone has already chatted in {name}, so it can't be a fresh practice profile.")
        mirrored = (result or {}).get("mirrored") if isinstance(result, dict) else None
        if isinstance(mirrored, dict) and "model_inherited" in mirrored:
            plan_body["model_ok"] = bool(mirrored.get("model_inherited"))
        plan_body["folder_id"] = folder_id(home)  # what later reads, writes and the delete check the folder against
        conn.execute("UPDATE f_practice SET status = 'ready', path = ?, plan_json = ? WHERE name = ?", (str(home), json.dumps(plan_body), name))
        # Chats opened with host.newChat(profile) work in this folder, not the app's own workspace: Hermes uses a
        # named profile's terminal.cwd when it is an existing absolute folder (tui_gateway/session_workdir.py).
        from . import practice_write

        practice_write.set_config(home, _row(conn, name), {"terminal.cwd": str(home.resolve())})
        try:
            prints = fingerprint(home)
        except OSError as exc:
            raise ValueError(f"Field Academy couldn't read {name}'s files.") from exc
        conn.execute("UPDATE f_practice SET fingerprint_json = ? WHERE name = ?", (json.dumps(prints), name))
        return view(_row(conn, name))


def _home_for(row) -> Path:
    return Path(row["path"])


def plant(name: str, kinds, seed: str, partner: str = "", seed_notes=None, setup=None, folder: bool = False) -> dict:
    """Write the seed notes, then the planted problems, into a recorded, unopened practice profile.

    ``seed_notes`` is the mission's ``lab.seed_notes`` (``[{"text", "key"}]``). ``setup`` names a mission's setup step
    (plants.SETUPS: sample files, a connector, settings every learner gets), run before the planted problems.
    ``folder`` points the profile's ``terminal.cwd`` at its practice folder. Returns a public view, never the details.
    """
    from . import plants

    seed_body = plants.clean_seed(seed_notes)
    with _conn() as conn:
        row = _row(conn, name)
        if row is None or row["status"] != "ready":
            raise ValueError(f"{name} isn't recorded and ready, so nothing can be planted in it.")
        home = _home_for(row)
        moved = changed_files(home, json.loads(row["fingerprint_json"] or "{}"))
        if moved:
            raise ValueError(f"{name} has changed since Field Academy recorded it ({moved[0]}). Reset it to start over.")
        partner_row = _row(conn, partner) if partner else None
        seeded = plants.seed_memory(home, row, seed_body)
        body = row["plan"]
        if folder:
            from . import practice_write

            body["folder"] = practice_write.ensure_practice_folder(home, row)
            practice_write.set_config(home, row, {"terminal.cwd": body["folder"]})
        if setup:
            body["setup"] = plants.run_setup(setup, home, row, seed)
        details = plants.plant_all(home, row, list(kinds), seed, partner_row, seeded, setup=body.get("setup"))
        body["planted"] = details
        body["seed_notes"] = seeded
        conn.execute("UPDATE f_practice SET status = 'planted', planted_at = ?, plan_json = ?, seed = ?, fingerprint_json = ? WHERE name = ?",
                     (store.now(), json.dumps(body), seed, json.dumps(fingerprint(home)), name))
        if partner_row and "wrong_profile" in details and partner_row["status"] == "ready":
            # The second profile may have been given the same seed notes. Record its new state, so nothing else
            # mistakes Field Academy's own write for the learner's.
            conn.execute("UPDATE f_practice SET status = 'planted', planted_at = ?, fingerprint_json = ? WHERE name = ?",
                         (store.now(), json.dumps(fingerprint(_home_for(partner_row))), partner))
        return view(_row(conn, name))


def plant_more(name: str, kinds, seed: str) -> dict:
    """Add planted problems to a practice profile that is already set up (mission 4's second profile, made after the
    try). Nothing in this profile is written: these plants only record what they read. The learner has used the
    profile by now, so its fingerprint is left as it was. Returns the public view."""
    from . import plants

    with _conn() as conn:
        row = _row(conn, name)
        if row is None or row["status"] != "planted":
            raise ValueError(f"{name} isn't set up yet, so nothing more can be planted in it.")
        body = row["plan"]
        have = body.get("planted") or {}
        todo = [k for k in kinds if k not in have]
        if todo:
            details = plants.plant_all(_home_for(row), row, todo, seed, None, body.get("seed_notes") or {}, setup=body.get("setup"))
            body["planted"] = {**have, **details}
            conn.execute("UPDATE f_practice SET plan_json = ? WHERE name = ?", (json.dumps(body), name))
        return view(_row(conn, name))


def planted(name: str) -> dict:
    """The hidden planted details, for the checks on this side only. Never sent to the page before Compare."""
    with _conn() as conn:
        row = _row(conn, name)
    return (row or {}).get("plan", {}).get("planted", {}) if row else {}


def seed_notes(name: str) -> dict:
    """The seed notes written into this profile, ``{"notes", "key"}``. Hidden: which notes are key shows at Compare."""
    with _conn() as conn:
        row = _row(conn, name)
    return (row or {}).get("plan", {}).get("seed_notes", {}) if row else {}


def record(name: str):
    with _conn() as conn:
        return _row(conn, name)


def _data_dir(conn) -> Path:
    override = os.environ.get("FIELD_ACADEMY_DATA_DIR")
    if override:
        return Path(override)
    db = conn.execute("PRAGMA database_list").fetchone()
    return Path(db[2]).parent


def _save_snapshot(folder: Path, name: str, body: dict) -> Path:
    """The evidence a record needs, kept in Field Academy's own folder before the profile is deleted."""
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{name}-{store.clock().strftime('%Y%m%dT%H%M%S')}.json"
    target.write_text(json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return target


def prepare_remove(name: str, confirmed: bool = False, root=None) -> dict:
    """Agree to delete a practice profile Field Academy recorded, after a confirm click, and snapshot its evidence."""
    if not confirmed:
        raise ValueError("Deleting a practice profile needs your confirmation.")
    root = Path(root) if root is not None else Path(hermes_root())
    home = practice_home(name, root=root)
    with _conn() as conn:
        row = _row(conn, name)
        if row is None or row["status"] not in ("ready", "planted", "removing", "planned"):
            raise ValueError(f"Field Academy didn't make {name}, so it won't delete it.")
        if row["status"] != "planned" and Path(row["path"]).resolve(strict=False) != home.resolve(strict=False):
            raise ValueError(f"{name} isn't where Field Academy recorded it, so it won't delete it.")
        if home.exists() or home.is_symlink():
            if row["status"] == "planned":
                # Never recorded: only the profile Field Academy asked Hermes for (made after the plan, carrying the
                # planned instructions, not a Hermes Bots profile) may be deleted. Anything else at that name stays.
                plan_body = row["plan"]
                mine = (not home.is_symlink() and home.is_dir() and not catalog_profile(home)
                        and _born_after(home, float(plan_body.get("planned_epoch", 0)))
                        and _same_text(home / "SOUL.md", ((plan_body.get("request") or {}).get("params") or {}).get("soul", "")))
            else:
                mine = is_ours(row, home)
            if not mine:
                _let_go(conn, name)
                raise ValueError(NOT_OURS.format(name=name))
        snapshot = ""
        if home.is_dir() and row["status"] != "planned":
            from . import plants_a

            plants_a.before_remove(row, home)  # clear a lock Field Academy set, so Hermes can delete the folder
            from . import hermes_read

            snapshot = str(_save_snapshot(_data_dir(conn) / "practice-snapshots", name, hermes_read.summary(home)))
        conn.execute("UPDATE f_practice SET status = 'removing' WHERE name = ?", (name,))
        return {"delete": name, "snapshot": snapshot, "practice": view(_row(conn, name))}


def removed(name: str, root=None) -> dict:
    """The page deleted the profile through Hermes. Check the folder is gone, then mark it removed."""
    root = Path(root) if root is not None else Path(hermes_root())
    home = practice_home(name, root=root)
    with _conn() as conn:
        row = _row(conn, name)
        if row is None or row["status"] != "removing":
            raise ValueError(f"{name} wasn't being deleted.")
        if home.exists():
            raise ValueError(f"{name} is still there. Delete it from Hermes, then check again.")
        conn.execute("UPDATE f_practice SET status = 'removed', removed_at = ? WHERE name = ?", (store.now(), name))
        return view(_row(conn, name))


def plant_for_attempt(attempt_id, seed_notes=None, setup=None, folder: bool = False, kinds=None) -> dict:
    """Plant what an attempt drew, in the practice profile the attempt names. Only after the attempt is frozen."""
    with _conn() as conn:
        row = conn.execute("SELECT * FROM f_attempts WHERE id = ?", (int(attempt_id),)).fetchone()
        if row is None:
            raise ValueError("No such attempt.")
        if not row["frozen_at"]:
            raise ValueError("Save your recall, claim, standard and prediction first. Then the practice profile is set up.")
        kinds = list(kinds) if kinds is not None else json.loads(row["plants_json"] or "[]")
        name = row["profile"] or ""
        main = _row(conn, name) if name else None
        if main is None:
            candidates = [_row(conn, r["name"]) for r in conn.execute("SELECT name FROM f_practice WHERE status = 'ready'")]
            main = next((r for r in candidates if r["plan"].get("which", "a") == "a"), None)
        if main is None:
            raise ValueError("Create the practice profile first.")
        partner = ""
        if "wrong_profile" in kinds:
            bs = [_row(conn, r["name"]) for r in conn.execute("SELECT name FROM f_practice WHERE status IN ('ready', 'planted')")]
            partner = next((r["name"] for r in bs if r["plan"].get("which") == "b"), "")
        if not row["profile"]:
            conn.execute("UPDATE f_attempts SET profile = ? WHERE id = ?", (main["name"], int(attempt_id)))
        conn.execute("UPDATE f_practice SET attempt_id = ? WHERE name = ?", (int(attempt_id), main["name"]))
    return plant(main["name"], kinds, row["seed"], partner=partner, seed_notes=seed_notes, setup=setup, folder=folder)


def memory_files(name: str) -> dict:
    """The practice profile's MEMORY.md and USER.md, line by line, scrubbed, for the page's "Show memory file" view.

    Only a practice profile Field Academy recorded, at its recorded path. Read-only, through hermes_read.
    """
    from . import hermes_read, scrub

    if not valid_name(name):
        raise ValueError("Field Academy only shows the memory of its own practice profiles.")
    row = record(name)
    if not row or row["status"] not in ("ready", "planted") or not row.get("path"):
        raise ValueError(f"{name} isn't set up, so there is no memory file to show.")
    require_ours(row)
    home = Path(row["path"])
    mem = hermes_read.memory(home)
    if not mem.get("readable"):
        raise ValueError(mem.get("why") or "The memory files could not be read.")
    waiting = len(hermes_read.pending(home).get("memory", []))
    # Staged saves are never shown as saved lines: only how many wait, and where to see them.
    out = {"name": name, "folder": str(home / "memories"), "folder_shown": shown_path(home / "memories"), "files": [],
           "pending": waiting}
    for key, label in (("memory", "MEMORY.md"), ("user", "USER.md")):
        part = mem[key]
        out["files"].append({"file": label, "path": str(home / part["rel_path"]), "path_shown": shown_path(home / part["rel_path"]),
                             "exists": part["exists"], "chars": part["chars"],
                             "limit": part["limit"], "entries": [scrub.scrub(e, 600) for e in part["entries"]], "mtime": part["mtime"]})
    return out


FOLDER_FIX = ("Your app opened that chat in another folder, most likely a workspace you chose for new chats. Copy the "
              "practice folder above, set it as the chat's working folder, then press Open practice chat again.")


def working_folder(name: str) -> dict:
    """Did the first practice chat work in the practice folder? Read from the chat's own row in state.db (sessions.cwd).

    ``state``: ``no_chat`` (nothing to read yet), ``pass``, ``fail`` or ``unknown`` (Hermes didn't stamp a folder).
    Only a practice profile Field Academy recorded. The folder is shown as written; nothing is changed.
    """
    from . import hermes_read, scrub

    if not valid_name(name):
        raise ValueError("Field Academy only checks its own practice profiles.")
    row = record(name)
    if not row or row["status"] not in ("ready", "planted") or not row.get("path"):
        raise ValueError(f"{name} isn't set up, so there is no chat to check.")
    require_ours(row)
    home = Path(row["path"])
    target = Path(row["plan"].get("folder") or home)
    found = hermes_read.sessions(home)
    if not found.get("readable"):
        return {"state": "no_chat", "expected": str(target), "cwd": "", "fix": ""}
    chats = list(found["sessions"])
    if not chats:
        return {"state": "no_chat", "expected": str(target), "cwd": "", "fix": ""}
    first = chats[0]
    cwd = str(first.get("cwd") or "").strip()
    # Shown home-relative and scrubbed one segment at a time (shown_path): the catch-all for long key-like runs would
    # otherwise take a long path for a key, while a key-shaped folder name is still removed.
    out = {"expected": str(home), "expected_shown": shown_path(home), "cwd": shown_path(cwd), "session_title": first.get("title", ""),
           "checked_by": "Field Academy read it"}
    if not cwd:
        return {**out, "state": "unknown", "fix": "Hermes didn't record a folder for that chat. Ask Hermes in a practice chat which folder it is working in."}
    out["expected"], out["expected_shown"] = str(target), shown_path(target)
    try:
        same = Path(cwd).expanduser().resolve(strict=False) == target.resolve(strict=False)
    except (OSError, ValueError):
        same = False
    return {**out, "state": "pass" if same else "fail", "fix": "" if same else FOLDER_FIX}


# ------------------------------------------------------------- missions 7 to 11 --
#
# Setup details (the sample files and settings every learner gets), a few values Field Academy records after the
# plants (mission 11's baseline), and the scheduled jobs a planted problem needs. Jobs are never written into
# cron/jobs.json: the page asks Hermes to make them with cron.manage through host.requestProfile, then reports back,
# and this side checks the job list itself.


def setup_details(name: str) -> dict:
    """What a mission's setup step wrote. Hidden from the page like the plants."""
    row = record(name)
    return (row or {}).get("plan", {}).get("setup", {}) if row else {}


def set_extra(name: str, key: str, value) -> None:
    """Keep one more value in the practice record (``plan[key]``). Only Field Academy's own names."""
    if key not in ("baseline", "jobs_made"):
        raise ValueError("Field Academy keeps only its own values here.")
    with _conn() as conn:
        row = _row(conn, name)
        if row is None:
            raise ValueError(f"Field Academy has no record of {name}.")
        body = row["plan"]
        body[key] = value
        conn.execute("UPDATE f_practice SET plan_json = ? WHERE name = ?", (json.dumps(body), name))


def extra(name: str, key: str):
    row = record(name)
    return (row or {}).get("plan", {}).get(key) if row else None


def _listed_jobs(row) -> dict:
    """The practice profile's job list by name, read from disk (never written)."""
    from . import hermes_read

    listed = hermes_read.cron_jobs(Path(row["path"]))
    return {j.get("name"): j for j in listed.get("jobs", []) if isinstance(j, dict) and j.get("name")}


def _planned_paused_but_on(job: dict, found) -> bool:
    return bool(job.get("pause")) and isinstance(found, dict) and found.get("enabled") is not False


def jobs_to_make(name: str) -> dict:
    """The scheduled jobs the page should ask Hermes to make in this practice profile, in order. Each is
    ``{"name", "schedule", "prompt", "deliver", "pause"}``. Nothing about why a job looks the way it does.

    ``still_on`` lists the jobs that should have started paused but that the job list shows on, each with the id the
    list gives it (``{"name", "id"}``). They aren't recorded as made and aren't on the add list (that would make a
    second job with the same name): the page pauses them by that id, or deletes them, and reports back (audit B1)."""
    if not valid_name(name):
        raise ValueError("Field Academy only makes jobs in its own practice profiles.")
    row = record(name)
    if not row or row["status"] not in ("ready", "planted"):
        raise ValueError(f"{name} isn't set up.")
    require_ours(row)
    merged = {}
    plan_body = row.get("plan") or {}
    for source in [plan_body.get("setup") or {}] + [plan_body.get("planted", {})[k] for k in sorted(plan_body.get("planted") or {})]:
        for job in (source or {}).get("jobs") or []:
            if job["name"] in merged:  # two problems planted in one job: each keeps only the field it plants
                merged[job["name"]].update({k: job[k] for k in job.get("sets") or [] if k in job})
            else:
                merged[job["name"]] = {k: job[k] for k in ("name", "schedule", "prompt", "deliver", "pause") if k in job}
    made = plan_body.get("jobs_made") or {}
    todo = [j for j in merged.values() if j["name"] not in made]
    by_name = _listed_jobs(row) if any(j.get("pause") for j in todo) else {}
    still_on = [{"name": j["name"], "id": str(by_name[j["name"]].get("id") or "")[:64]}
                for j in todo if _planned_paused_but_on(j, by_name.get(j["name"]))]
    on = {s["name"] for s in still_on}
    return {"name": name, "jobs": [j for j in todo if j["name"] not in on], "made": sorted(made), "still_on": still_on}


def jobs_made(name: str) -> dict:
    """The page says it made the jobs. Read the job list and record each job's id by name; a job that isn't there
    stays on the to-make list, and a job meant to start paused that the list shows on stays in ``still_on`` until it
    reads paused (audit B1: fail closed, never record a planned-paused job as made while it runs)."""
    todo = jobs_to_make(name)
    row = record(name)
    by_name = _listed_jobs(row)
    made = dict((row.get("plan") or {}).get("jobs_made") or {})
    for job in todo["jobs"]:
        found = by_name.get(job["name"])
        if found is not None and not _planned_paused_but_on(job, found):
            made[job["name"]] = {"id": found.get("id"), "enabled": found.get("enabled"), "state": found.get("state")}
    set_extra(name, "jobs_made", made)
    return jobs_to_make(name)
