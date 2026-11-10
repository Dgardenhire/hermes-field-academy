"""Where a practice profile lives: Hermes's root rule, on macOS, Linux and Windows, with no Hermes import.

The rule is copied from hermes_constants.py (Hermes 0.22.4): the native home is ``~/.hermes`` or
``%LOCALAPPDATA%\\hermes`` (plus HERMES_DATA_DIR_SUFFIX); a HERMES_HOME under the native home has the native home as
its root; any other HERMES_HOME is ``<root>/profiles/<name>`` when its parent folder is named ``profiles``, and is
its own root otherwise.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from pathlib import PurePosixPath, PureWindowsPath

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_scrub import load  # noqa: E402


class RootRule(unittest.TestCase):
    def setUp(self):
        self.practice = load("practice")

    def root(self, environ, platform, home):
        return self.practice.hermes_root(environ=environ, platform=platform, user_home=lambda: home)

    def test_macos_and_linux_default(self):
        home = PurePosixPath("/home/ada")
        self.assertEqual(self.root({}, "darwin", home), PurePosixPath("/home/ada/.hermes"))
        self.assertEqual(self.root({}, "linux", PurePosixPath("/home/ada")), PurePosixPath("/home/ada/.hermes"))

    def test_windows_default_is_local_appdata(self):
        home = PureWindowsPath("C:/Users/you")
        env = {"LOCALAPPDATA": "C:\\Users\\you\\AppData\\Local"}
        self.assertEqual(self.root(env, "win32", home), PureWindowsPath("C:/Users/you/AppData/Local/hermes"))
        self.assertEqual(self.root({}, "win32", home), PureWindowsPath("C:/Users/you/AppData/Local/hermes"), "no LOCALAPPDATA falls back under the user folder")

    def test_the_data_dir_suffix_is_kept(self):
        home = PurePosixPath("/home/ada")
        self.assertEqual(self.root({"HERMES_DATA_DIR_SUFFIX": "-dev"}, "darwin", home), PurePosixPath("/home/ada/.hermes-dev"))

    def test_a_profile_home_under_the_native_home_has_the_native_root(self):
        home = PurePosixPath("/home/ada")
        env = {"HERMES_HOME": "/home/ada/.hermes/profiles/work"}
        self.assertEqual(self.root(env, "darwin", home), PurePosixPath("/home/ada/.hermes"))

    def test_a_windows_profile_home_has_the_windows_root(self):
        home = PureWindowsPath("C:/Users/you")
        env = {"LOCALAPPDATA": "C:\\Users\\you\\AppData\\Local", "HERMES_HOME": "C:\\Users\\you\\AppData\\Local\\hermes\\profiles\\work"}
        self.assertEqual(self.root(env, "win32", home), PureWindowsPath("C:/Users/you/AppData/Local/hermes"))

    def test_a_custom_root_in_profile_mode(self):
        env = {"HERMES_HOME": "/srv/hermes/profiles/client"}
        self.assertEqual(self.root(env, "linux", PurePosixPath("/home/ada")), PurePosixPath("/srv/hermes"))

    def test_a_custom_home_that_is_not_a_profile_is_its_own_root(self):
        env = {"HERMES_HOME": "/srv/hermes-main"}
        self.assertEqual(self.root(env, "linux", PurePosixPath("/home/ada")), PurePosixPath("/srv/hermes-main"))

    def test_blank_hermes_home_counts_as_unset(self):
        self.assertEqual(self.root({"HERMES_HOME": "  "}, "linux", PurePosixPath("/home/ada")), PurePosixPath("/home/ada/.hermes"))

    def test_the_module_never_imports_hermes(self):
        text = (pathlib.Path(__file__).resolve().parents[1] / "practice.py").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?m)^\s*(?:from|import)\s+(?:hermes_cli|hermes_constants|tools|agent)\b")


class PracticeHome(unittest.TestCase):
    def setUp(self):
        self.practice = load("practice")
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.root = self.tmp / "hermes"
        (self.root / "profiles").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_home_sits_in_profiles(self):
        self.assertEqual(self.practice.practice_home("academy-practice", root=self.root), self.root / "profiles" / "academy-practice")

    def test_only_field_academy_names_are_allowed(self):
        for bad in ("default", "work", "../escape", "academy-practice/../work", "Academy-Practice", "academy-practice\x00", "", "a" * 80):
            with self.assertRaises(ValueError, msg=bad):
                self.practice.practice_home(bad, root=self.root)
        for good in ("academy-practice", "academy-practice-2", "academy-practice-b", "academy-practice-b-3"):
            self.practice.practice_home(good, root=self.root)

    @unittest.skipIf(os.name == "nt", "symbolic links need extra rights on Windows")
    def test_a_link_in_place_of_the_profile_is_refused(self):
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        (self.root / "profiles" / "academy-practice").symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.practice.practice_home("academy-practice", root=self.root)

    @unittest.skipIf(os.name == "nt", "symbolic links need extra rights on Windows")
    def test_a_linked_profiles_folder_is_refused(self):
        other = self.tmp / "other-root"
        (other / "profiles-real").mkdir(parents=True)
        (other / "profiles").symlink_to(other / "profiles-real", target_is_directory=True)
        with self.assertRaises(ValueError):
            self.practice.practice_home("academy-practice", root=other)


if __name__ == "__main__":
    unittest.main()
