"""Isolation twins for Foundations (ENGINEERING-PLAN section 7).

* Only practice_write.py writes outside Field Academy's data folder, and only to the allowlisted files of a recorded
  practice profile. practice.py writes one thing, the evidence snapshot, into the data folder.
* Nothing reads .env or auth.json, runs a program, reaches the network or imports Hermes.
* A full run (plan, record, plant, use, remove) changes only the allowlisted files in the practice profile and
  leaves the account's real Hermes home exactly as it was.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from deployer_support import REAL_HERMES_HOME, real_home_fingerprint  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULES = ("practice", "practice_write", "plants", "hermes_read", "matching", "yaml_keys", "scrub",
           "foundations", "foundations_checks", "calibration", "foundations_content")
WRITERS = {"write_text", "write_bytes", "mkdir", "makedirs", "mkstemp", "fdopen", "replace", "rename", "unlink", "rmtree",
           "rmdir", "remove", "touch", "chmod", "symlink_to", "copy", "copy2", "copyfile", "copytree", "move", "truncate"}
FORBIDDEN = {
    "running a program": re.compile(r"\bsubprocess\b|\bos\.system\b|\bos\.popen\b|\bos\.exec\w*\b|\bos\.spawn\w*\b|\bpty\b"),
    "dynamic code": re.compile(r"(?<![\w.])eval\(|(?<![\w.])exec\(|\b__import__\("),
    "the network": re.compile(r"\b(?:import|from) (?:socket|requests|httpx|aiohttp|smtplib|ssl|http\.client)\b|\burllib\.request\b|\burlopen\b"),
    "a hermes command": re.compile(r"\bhermes (?:doctor|plugins|gateway|chat|cron|config|model|update|setup|dashboard|sessions|skills|tools|profile)\b"),
    "a Hermes import": re.compile(r"(?m)^\s*(?:from|import)\s+(?:hermes_cli|hermes_constants|hermes_state\w*|tools|agent|cron|tui_gateway|plugins)\b"),
}


def present():
    return [name for name in MODULES if (ROOT / f"{name}.py").exists()]


def writes_in(tree):
    """(line, what) for each call that could write, outside str.replace on text (os.replace counts)."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else (func.id if isinstance(func, ast.Name) else "")
            if name == "replace":
                if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "os"):
                    continue
            if name in WRITERS:
                out.append((node.lineno, name))
            if name == "open":
                mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
                if mode is not None and not (isinstance(mode, ast.Constant) and set(str(mode.value)) <= set("rbt")):
                    out.append((node.lineno, "open for writing"))
    return out


class Static(unittest.TestCase):
    def source(self, name):
        return (ROOT / f"{name}.py").read_text(encoding="utf-8")

    def test_no_module_runs_a_program_reaches_the_network_or_imports_hermes(self):
        for name in present():
            text = self.source(name)
            for label, pattern in FORBIDDEN.items():
                hit = pattern.search(text)
                self.assertIsNone(hit, f"{name}.py uses {label}: {hit.group(0) if hit else ''}")

    def test_only_practice_write_writes_and_practice_only_saves_its_snapshot(self):
        for name in present():
            tree = ast.parse(self.source(name))
            found = writes_in(tree)
            if name == "practice_write":
                self.assertTrue(found)
                continue
            if name == "practice":
                snapshot = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_save_snapshot")
                inside = set(writes_in(snapshot))
                self.assertEqual(set(found), inside, "practice.py writes only in _save_snapshot")
                continue
            self.assertEqual(found, [], f"{name}.py writes")

    def test_practice_write_names_its_three_files_and_never_a_credential(self):
        text = self.source("practice_write")
        self.assertIn('ALLOWED_FILES = ("config.yaml", "memories/MEMORY.md", "memories/USER.md")', text)
        tree = ast.parse(text)
        docstrings = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                self.assertNotRegex(node.value, r"\.env\b|auth\.json|mcp-tokens|pairing|platforms", f"line {node.lineno}")

    def test_no_new_module_names_a_credential_file_except_to_refuse_it(self):
        for name in present():
            tree = ast.parse(self.source(name))
            docstrings = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                    if re.search(r"(?<![\w-])\.env\b|auth\.json", node.value):
                        self.assertIn(node.value, (".env", "auth.json", ".env.lock", "auth.lock"), f"{name}.py line {node.lineno}: {node.value[:40]!r}")


class FullRun(FoundationsCase):
    def test_a_whole_practice_run_changes_only_allowlisted_files_and_never_the_real_home(self):
        before_real = real_home_fingerprint()
        self.ready("a")
        self.ready("b")
        start = self.practice.fingerprint(self.home())
        start_b = self.practice.fingerprint(self.home("academy-practice-b"))
        self.practice.plant("academy-practice", ["write_approval", "memory_full", "wrong_profile"], "seed", partner="academy-practice-b")
        changed = self.practice.changed_files(self.home(), start)
        self.assertTrue(set(changed) <= {"config.yaml", "memories/MEMORY.md", "memories/USER.md"}, changed)
        self.assertEqual(self.practice.changed_files(self.home("academy-practice-b"), start_b), [], "the second profile is never written")
        self.assertEqual((self.home() / ".env").read_text(), "OPENROUTER_API_KEY=" + hf.fake_key() + "\n")
        self.hermes_read.summary(self.home())
        out = self.practice.prepare_remove("academy-practice", confirmed=True)
        self.assertTrue(pathlib.Path(out["snapshot"]).resolve().is_relative_to(pathlib.Path(self.tmp).resolve() / "practice-snapshots"))
        self.assertEqual(real_home_fingerprint(), before_real, f"the real Hermes home at {REAL_HERMES_HOME} changed")


if __name__ == "__main__":
    unittest.main()
