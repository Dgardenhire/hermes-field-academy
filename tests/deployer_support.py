"""Shared setup for the Deployer tests.

Every test runs with HOME and HERMES_HOME pointed at a folder that does not
exist. If any code under test tried to use the real Hermes home, or wrote
anywhere but the data folder, the folder would appear and tearDown fails the
test. The real ~/.hermes is also fingerprinted by the isolation test.
"""

from __future__ import annotations

import importlib
import itertools
import json
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from support import AcademyCase  # noqa: E402
from lab_solutions import SOLVERS  # noqa: E402


class DeployerCase(AcademyCase):
    def setUp(self):
        super().setUp()
        self.fence = pathlib.Path(tempfile.mkdtemp(prefix="fa-fence-"))
        self.fake_home = self.fence / "home"
        self._saved = {key: os.environ.get(key) for key in ("HOME", "HERMES_HOME")}
        os.environ["HOME"] = str(self.fake_home)
        os.environ["HERMES_HOME"] = str(self.fake_home / ".hermes")
        for name in ("labs", "grade", "deployer", "evidence", "walkthrough", "brief", "scenarios", "deployer_content", "ed25519"):
            setattr(self, name, importlib.import_module(f"{self.name}.{name}"))
        counter = itertools.count(1000)
        self.deployer.new_seed = lambda: next(counter)
        self.data = pathlib.Path(self.tmp)

    def tearDown(self):
        created = self.fake_home.exists()
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(self.fence, ignore_errors=True)
        super().tearDown()
        self.assertFalse(created, "something created the fake home: code under test reached for the real Hermes home")

    # -- labs ------------------------------------------------------------

    def open_and_solve(self, lab_id, **options):
        view = self.deployer.open_lab(lab_id)
        spec = self.labs.spec_for(lab_id, view["seed"])
        diagnosis = SOLVERS[lab_id](spec, pathlib.Path(view["path"]), **options)
        return view, spec, diagnosis

    def pass_lab(self, lab_id):
        view, spec, diagnosis = self.open_and_solve(lab_id)
        reply = self.deployer.check_lab(lab_id, diagnosis)
        self.assertTrue(reply["outcome"]["passed"], reply["outcome"].get("missing"))
        return view

    def pass_labs(self):
        for lab_id in self.deployer.LAB_ORDER:
            self.pass_lab(lab_id)

    # -- documents -------------------------------------------------------

    def file(self, name, text):
        target = self.data / name
        target.write_text(text, encoding="utf-8")
        return str(target)

    def clock_at(self, when):
        self.set_time(when)


from proposals import good_proposal  # noqa: E402,F401


def _real_home():
    """The person's real Hermes home: ~/.hermes on macOS and Linux (read through pwd, which HOME can't fool),
    %LOCALAPPDATA%\\hermes on Windows, which has no pwd module."""
    try:
        import pwd
    except ImportError:
        local = os.environ.get("LOCALAPPDATA")
        return pathlib.Path(local) / "hermes" if local else pathlib.Path.home() / ".hermes"
    return pathlib.Path(pwd.getpwuid(os.getuid()).pw_dir) / ".hermes"


REAL_HERMES_HOME = _real_home()


def real_home_fingerprint():
    """A read-only fingerprint of the parts of the real Hermes home a stray write would land in.

    Names, sizes and modification times of the top-level entries, and the listings of the folders that
    matter (cron, profiles, skills, plugins, launchers). Folders Hermes itself writes while running
    (logs, sessions, caches, databases) are left out, so an open Hermes cannot fail the test. It is
    taken from the account's own home, not from HOME, which the tests point elsewhere. Returns None
    when there is no real home at all.
    """
    home = REAL_HERMES_HOME
    if not home.is_dir():
        return None
    noisy = {"logs", "sessions", "cache", "plugin-data", "tmp", ".cache", "checkpoints", "history", "sandboxes", "audio_cache", "image_cache",
             "browser_recordings", "gateway.pid", "gateway_state.json", "processes.json", "channel_directory.json", "models_dev_cache.json",
             "last_update_check", ".update_check", ".hermes_history"}
    out = {}
    for entry in sorted(home.iterdir()):
        if entry.name in noisy or entry.name.endswith((".log", ".pid", ".lock", ".db", ".db-wal", ".db-shm", ".sock")):
            continue
        try:
            stat = entry.stat()
        except OSError:
            continue
        out[entry.name] = (stat.st_size if entry.is_file() else -1, stat.st_mtime_ns if entry.is_file() else -1)
        if entry.is_dir() and entry.name in ("cron", "profiles", "skills", "desktop-plugins", "plugins", "launchers", "bin"):
            out[entry.name + "/"] = sorted(child.name for child in entry.iterdir())
    return out
