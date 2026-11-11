"""No planted problem may leave a sign-in file within a model's reach.

Hermes's profiles.create copies the learner's sign-in (.env, auth.json, mcp-tokens/ and more) into every new practice
profile. A filesystem connector has none of Hermes's own read guards, so every connector Field Academy writes must stay
clear of the profile's own folder, everything above it, and every sign-in path. This plants every problem every mission
can draw, on the shipped content, and reads the connector folders back out of config.yaml.
"""

from __future__ import annotations

import inspect
import os
import pathlib
import shutil
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_foundations_missions_b import MissionCase  # noqa: E402

SIGN_IN = (".env", "auth.json", "mcp-tokens", "pairing", "platforms")


def _wipe(folder):
    """Remove a practice profile, clearing any Locked flag a mission-1 plant set first."""
    for path in [folder, *folder.rglob("*")]:
        try:
            if hasattr(os, "chflags"):
                os.chflags(path, 0, follow_symlinks=False)
            if not path.is_symlink():
                os.chmod(path, 0o700 if path.is_dir() else 0o600)
        except OSError:
            pass
    shutil.rmtree(folder)


def _overlaps(a, b):
    return a == b or a in b.parents or b in a.parents


class NoCredentialReach(MissionCase):
    MID = "f.toolsets"

    def lay_sign_in(self, home):
        (home / "mcp-tokens").mkdir(exist_ok=True)
        (home / "mcp-tokens" / "github.json").write_text('{"token": "x"}')
        for name in ("pairing", "platforms"):
            (home / name).mkdir(exist_ok=True)
            (home / name / "x.json").write_text("{}")

    def connector_paths(self, home):
        found = self.mod("hermes_read_b").mcp_servers(home)
        self.assertTrue(found.get("readable"))
        return [(s["name"], p) for s in found["servers"] for p in (s.get("paths") or [])]

    def assert_clear(self, home, where):
        root = home.resolve()
        for name, raw in self.connector_paths(home):
            path = pathlib.Path(raw).expanduser().resolve()
            self.assertFalse(path == root or path in root.parents, f"{where}: {name} reaches the profile folder: {path}")
            for secret in SIGN_IN:
                self.assertFalse(_overlaps(path, (root / secret).resolve()), f"{where}: {name} reaches {secret}: {path}")

    def test_every_planted_problem_keeps_the_sign_in_out_of_reach(self):
        plants = self.mod("plants")
        checked = 0
        for kind in sorted(plants.REGISTRY):
            with self.subTest(kind=kind):
                for leftover in (self.root / "profiles").iterdir():
                    _wipe(leftover)
                with self.store.connect() as conn:
                    conn.execute("DELETE FROM f_practice")
                row = self.ready()
                home = self.home()
                self.lay_sign_in(home)
                with self.practice._conn() as conn:
                    rec = self.practice._row(conn, row["name"])
                for setup in sorted(plants.SETUPS):
                    try:
                        plants.run_setup(setup, home, rec, "seed")
                    except (ValueError, KeyError, TypeError):
                        pass
                try:
                    plants.plant_all(home, rec, [kind], "seed", None, [], setup=None)
                except ValueError as exc:
                    # The two-profile plants (memory and SOUL.md in academy-practice-b) need a partner profile. They
                    # write no connector, which the source check below holds them to.
                    self.assertIn("second practice profile", str(exc))
                    source = inspect.getsource(plants.REGISTRY[kind]["plant"])
                    self.assertNotIn("mcp_servers", source)
                    self.assertNotIn("add_mcp_server", source)
                    continue
                self.assert_clear(home, kind)
                checked += 1
        self.assertGreaterEqual(checked, len(plants.REGISTRY) - 4)
        self.assertIn("wide_connector", plants.REGISTRY)

    def test_the_wide_connector_reaches_the_settings_copy_and_no_sign_in(self):
        aid = self.lab(["wide_connector"])
        self.assert_clear(self.h, "wide_connector")
        copy = self.h / self.practice_write.SETTINGS_COPY
        self.assertTrue((copy / "config.yaml").is_file())
        self.assertFalse(any((copy / s).exists() for s in SIGN_IN))
        wide = self.mod("plants_c").wide_servers(self.h)
        self.assertEqual([s["name"] for s in wide], ["notes"])
        self.assertTrue(aid)

    def test_the_writer_refuses_a_connector_on_the_profile_or_a_sign_in_file(self):
        self.ready()
        home = self.home()
        self.lay_sign_in(home)
        with self.practice._conn() as conn:
            rec = self.practice._row(conn, "academy-practice")
        pw = self.practice_write
        fs = self.mod("plants_b").FS_PACKAGE
        for bad in (home, home.parent, home / "mcp-tokens", home / "mcp-tokens" / "github.json", home / ".env",
                    home / "pairing", home / "platforms" / "x.json", ".", "./", "../academy-practice"):
            with self.subTest(bad=str(bad)):
                with self.assertRaises(pw.Refused):
                    pw.set_config(home, rec, {"mcp_servers.x.command": "npx", "mcp_servers.x.args": ["-y", fs, str(bad)]})
                with self.assertRaises(pw.Refused):
                    pw.add_mcp_server_a(home, rec, "academy-x", "npx", ["-y", fs, str(bad)])
        pw.set_config(home, rec, {"mcp_servers.x.command": "npx", "mcp_servers.x.args": ["-y", fs, pw.ensure_practice_folder(home, rec)]})


if __name__ == "__main__":
    unittest.main()
