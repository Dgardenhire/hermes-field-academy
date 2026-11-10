"""Isolation twins for the mission 7 to 11 modules: they read and judge, and never write, run a program, reach the
network, read .env or auth.json, or import Hermes. The only writer stays practice_write.py."""

from __future__ import annotations

import ast
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_foundations_isolation import FORBIDDEN, ROOT, writes_in  # noqa: E402

MODULES = ("hermes_read_b", "plants_b", "foundations_checks_b", "foundations_b")


class StaticB(unittest.TestCase):
    def test_no_writes_programs_network_or_hermes_imports(self):
        for name in MODULES:
            text = (ROOT / f"{name}.py").read_text(encoding="utf-8")
            for label, pattern in FORBIDDEN.items():
                hit = pattern.search(text)
                self.assertIsNone(hit, f"{name}.py uses {label}: {hit.group(0) if hit else ''}")
            self.assertEqual(writes_in(ast.parse(text)), [], f"{name}.py writes")

    def test_credentials_are_never_named_for_reading(self):
        for name in MODULES:
            text = (ROOT / f"{name}.py").read_text(encoding="utf-8")
            self.assertNotRegex(text, r"""["'](?:\.env|auth\.json)["']""", name)

    def test_practice_write_keeps_its_folder_files_inside_the_practice_folder(self):
        text = (ROOT / "practice_write.py").read_text(encoding="utf-8")
        self.assertIn('PRACTICE_FOLDER = "practice-folder"', text)
        self.assertIn("def write_practice_file", text)


if __name__ == "__main__":
    unittest.main()
