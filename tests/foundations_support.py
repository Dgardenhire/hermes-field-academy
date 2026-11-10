"""Shared setup for the Foundations tests: a scratch Hermes root, and a stand-in for Hermes's profiles.create.

The stand-in only lays down what the gateway call would: a folder under profiles/, the planned SOUL.md, a config.yaml,
mirrored credential files and an empty chat store. Nothing runs Hermes.
"""

from __future__ import annotations

import importlib
import os
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from support import AcademyCase  # noqa: E402


class FoundationsCase(AcademyCase):
    def setUp(self):
        super().setUp()
        self.root = pathlib.Path(self.tmp) / "hermes-root"
        (self.root / "profiles").mkdir(parents=True)
        self._saved_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(self.root)
        self.practice = self.mod("practice")
        self.practice_write = self.mod("practice_write")
        self.plants = self.mod("plants")
        self.hermes_read = self.mod("hermes_read")

    def tearDown(self):
        if self._saved_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._saved_home
        super().tearDown()

    def mod(self, name):
        return importlib.import_module(f"{self.name}.{name}")

    def create_like_hermes(self, planned, config=hf.CONFIG, soul=None):
        """What profiles.create leaves behind. Returns the result the page would report."""
        params = planned["request"]["params"]
        home = self.root / "profiles" / params["name"]
        home.mkdir()
        (home / "SOUL.md").write_text(soul if soul is not None else params["soul"], encoding="utf-8")
        hf.write_config(home, config)
        (home / ".env").write_text("OPENROUTER_API_KEY=" + hf.fake_key() + "\n", encoding="utf-8")
        (home / "auth.json").write_text('{"k": "' + hf.fake_key() + '"}', encoding="utf-8")
        (home / "memories").mkdir()
        hf.state_db(home).close()
        return {"ok": True, "name": params["name"], "path": str(home), "soul_written": True, "model_set": False,
                "mirrored": {"env": True, "auth": True, "model_inherited": True, "voice": False}}

    def ready(self, which="a"):
        planned = self.practice.plan(which)
        result = self.create_like_hermes(planned)
        return self.practice.confirm(planned["name"], result)

    def home(self, name="academy-practice"):
        return self.root / "profiles" / name

    def chat(self, name="academy-practice", user="hello", tool=None, assistant="Hi.", started=hf.T0 + 100):
        con = hf.state_db(self.home(name))
        sid = hf.add_session(con, started_at=started)
        hf.add_message(con, sid, "user", user, started + 1)
        if tool is not None:
            hf.add_message(con, sid, "tool", tool, started + 2, tool_name="memory")
        hf.add_message(con, sid, "assistant", assistant, started + 3)
        con.close()
        return sid

    def gone(self, name):
        shutil.rmtree(self.home(name))
