"""The practice-profile readers, run against fixture homes built from Hermes 0.22.4's own schema strings.

Isolation, in three layers: the source can't write, run a program, reach the network or import Hermes; a run of
every reader opens no .env or auth.json (every open is watched) and leaves the fixture home byte for byte as it was;
and a link planted where a memory file should be is refused.
"""

from __future__ import annotations

import ast
import builtins
import io
import json
import os
import pathlib
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from test_scrub import load  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Readers(unittest.TestCase):
    def setUp(self):
        self.r = load("hermes_read")
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.home = hf.build_home(self.tmp / "profiles" / "academy-practice")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_memory_entries_counts_and_limits(self):
        mem = self.r.memory(self.home)
        self.assertEqual(mem["memory"]["entries"], ["Harbor Bakery uses QuickBooks Online; the other five use Xero."])
        self.assertEqual(mem["memory"]["limit"], 2200)
        self.assertEqual(mem["user"]["limit"], 1375)
        hf.write_memory(self.home, ["a" * 100, "b" * 50], None)
        self.assertEqual(self.r.memory(self.home)["memory"]["chars"], 100 + len(hf.DELIM) + 50)

    def test_memory_limits_follow_the_config(self):
        hf.write_config(self.home, hf.CONFIG.replace("memory_char_limit: 2200", "memory_char_limit: 3000"))
        self.assertEqual(self.r.memory(self.home)["memory"]["limit"], 3000)

    def test_missing_memory_files_read_as_empty(self):
        shutil.rmtree(self.home / "memories")
        mem = self.r.memory(self.home)
        self.assertFalse(mem["memory"]["exists"])
        self.assertEqual(mem["memory"]["entries"], [])

    def test_staged_writes_are_listed_oldest_first(self):
        hf.stage_pending(self.home, content="second", created_at=hf.T0 + 10)
        hf.stage_pending(self.home, content="first", created_at=hf.T0)
        hf.stage_pending(self.home, subsystem="skills", action="create", content="skill body")
        out = self.r.pending(self.home)
        self.assertEqual([p["content"] for p in out["memory"]], ["first", "second"])
        self.assertEqual(out["skills"][0]["action"], "create")

    def test_config_keeps_only_named_keys_and_never_a_reference_or_a_url_secret(self):
        values = self.r.config(self.home)["values"]
        self.assertIs(values["memory.write_approval"], False)
        self.assertEqual(values["toolsets"], ["hermes-cli", "web"])
        self.assertEqual(values["mcp_servers.github.trust"], "untrusted")
        self.assertEqual(values["mcp_servers.github.url"], "mcp.example.com")
        self.assertEqual(values["fallback_providers"], ["openai/gpt-5-mini"])
        self.assertEqual(values["providers.openrouter.model"], "anthropic/claude-sonnet-4.6")
        self.assertIs(values["sessions.auto_prune"], False)
        flat = json.dumps(values)
        for leak in ("OPENROUTER_API_KEY", "GITHUB_TOKEN", "user:pw", "token=abc", "Be brief"):
            self.assertNotIn(leak, flat)
        self.assertNotIn("providers.openrouter.api_key", values)

    def test_skills_are_found_like_hermes_finds_them(self):
        names = [s["name"] for s in self.r.skills(self.home)["skills"]]
        self.assertEqual(names, ["weekly-invoice"], "support folders and node_modules are not walked")

    def test_a_profile_distribution_swap_folder_is_not_walked(self):
        """Hermes 0.23.0 skips .hermes-dist (agent/skill_utils.py DIST_SWAP_DIR): a backup there is not a second skill."""
        swap = self.home / "skills" / ".hermes-dist" / "weekly-invoice"
        swap.mkdir(parents=True)
        (swap / "SKILL.md").write_text("---\nname: weekly-invoice\ndescription: Old copy.\n---\nBody.\n", encoding="utf-8")
        names = [s["name"] for s in self.r.skills(self.home)["skills"]]
        self.assertEqual(names, ["weekly-invoice"])
        self.assertIn(".hermes-dist", self.r.EXCLUDED_SKILL_DIRS)
        self.assertTrue(set(hf.FACTS["excluded_skill_dirs"]) <= set(self.r.EXCLUDED_SKILL_DIRS))

    def test_chat_store_sessions_messages_usage_and_prompt_size(self):
        store = self.r.chat_store(self.home)
        self.assertEqual((store["schema_version"], store["schema_ok"]), (32, True))
        sessions = self.r.sessions(self.home)["sessions"]
        self.assertEqual(len(sessions), 1)
        self.assertEqual((sessions[0]["input_tokens"], sessions[0]["cache_write_tokens"], sessions[0]["api_call_count"]), (5100, 4800, 1))
        msgs = self.r.messages(self.home, sessions[0]["id"])["messages"]
        self.assertEqual([m["role"] for m in msgs], ["user", "assistant", "tool", "assistant"])
        self.assertEqual(msgs[2]["tool_name"], "memory")
        tasks = sorted(u["task"] for u in self.r.usage(self.home)["usage"])
        self.assertEqual(tasks, ["", "background_review"])
        size = self.r.system_prompt_size(self.home, sessions[0]["id"])
        self.assertGreater(size["chars"], 10)
        self.assertNotIn("prompt", size)
        self.assertEqual(self.r.user_message_count(self.home), 1)

    def test_a_newer_schema_is_flagged_and_still_read(self):
        con = sqlite3.connect(self.home / "state.db")
        con.execute("UPDATE schema_version SET version = 33")
        con.commit()
        con.close()
        store = self.r.chat_store(self.home)
        self.assertFalse(store["schema_ok"])
        self.assertTrue(self.r.sessions(self.home)["readable"])

    def test_no_chat_store_is_unreadable_not_a_pass(self):
        (self.home / "state.db").unlink()
        self.assertFalse(self.r.sessions(self.home)["readable"])
        self.assertFalse(self.r.chat_store(self.home)["readable"])
        self.assertEqual(self.r.user_message_count(self.home), 0)

    def test_cron_jobs_and_runs(self):
        jobs = self.r.cron_jobs(self.home)["jobs"]
        self.assertEqual(jobs[0]["name"], "Morning brief")
        self.assertIn("last_delivery_unverified", jobs[0])
        runs = self.r.cron_runs(self.home, "job-a1")
        self.assertEqual(sorted(r["status"] for r in runs["executions"]), ["completed", "failed"])
        self.assertEqual(runs["incidents"][0]["failure_type"], "auth")

    def test_logs_are_a_scrubbed_tail(self):
        out = self.r.logs(self.home, max_lines=2)["files"]
        self.assertEqual(len(out["agent.log"]), 2)
        self.assertNotIn(hf.fake_key(), json.dumps(out))
        self.assertEqual(self.r.logs(self.home, contains="over budget")["files"]["errors.log"][0][-11:], "over budget")

    def test_checkpoints_are_counted_never_opened(self):
        out = self.r.checkpoints(self.home)
        self.assertEqual((out["exists"], out["files"]), (True, 1))

    def test_the_summary_holds_no_message_text(self):
        flat = json.dumps(self.r.summary(self.home))
        self.assertNotIn("Save to memory", flat)
        self.assertIn("Harbor Bakery", flat)


class Isolation(unittest.TestCase):
    def setUp(self):
        self.r = load("hermes_read")
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.home = hf.build_home(self.tmp / "profiles" / "academy-practice")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_every_reader(self):
        sid = self.r.sessions(self.home)["sessions"][0]["id"]
        for call in (
            lambda: self.r.memory(self.home), lambda: self.r.pending(self.home), lambda: self.r.config(self.home),
            lambda: self.r.skills(self.home), lambda: self.r.chat_store(self.home), lambda: self.r.sessions(self.home),
            lambda: self.r.messages(self.home), lambda: self.r.usage(self.home), lambda: self.r.system_prompt_size(self.home, sid),
            lambda: self.r.cron_jobs(self.home), lambda: self.r.cron_runs(self.home), lambda: self.r.logs(self.home),
            lambda: self.r.checkpoints(self.home), lambda: self.r.summary(self.home), lambda: self.r.user_message_count(self.home),
            lambda: self.r.gateway_running(self.home),
        ):
            call()

    def test_no_reader_opens_a_credential_file_or_changes_a_byte(self):
        before = hf.tree_state(self.home)
        opened = []
        real_open, real_io_open, real_os_open, real_connect = builtins.open, io.open, os.open, sqlite3.connect

        def watch(fn):
            def inner(file, *args, **kwargs):
                opened.append(str(file))
                return fn(file, *args, **kwargs)
            return inner

        def no_program(*args, **kwargs):
            raise AssertionError("a reader tried to run a program")

        with mock.patch.object(builtins, "open", watch(real_open)), mock.patch.object(io, "open", watch(real_io_open)), \
                mock.patch.object(os, "open", watch(real_os_open)), mock.patch.object(sqlite3, "connect", watch(real_connect)), \
                mock.patch.object(subprocess, "Popen", no_program), mock.patch.object(os, "system", no_program):
            self.run_every_reader()
        self.assertTrue(opened, "the watch saw the reads")
        touched = [p for p in opened if pathlib.PurePath(p.split("?")[0]).name in (".env", "auth.json")]
        self.assertEqual(touched, [])
        self.assertEqual(hf.tree_state(self.home), before)
        self.assertNotIn("hermes_cli", sys.modules)

    def test_forbidden_names_are_refused_even_when_asked_for(self):
        for rel in (".env", "auth.json", "mcp-tokens/github.json", "pairing/x", "platforms/telegram.json", "../escape", "memories/../.env"):
            self.assertIsNone(self.r.safe_path(self.home, rel), rel)
        self.assertIsNone(self.r._read_text(self.home, ".env"))

    @unittest.skipIf(os.name == "nt", "symbolic links need extra rights on Windows")
    def test_a_link_in_place_of_a_memory_file_is_not_followed(self):
        (self.home / "memories" / "MEMORY.md").unlink()
        (self.home / "memories" / "MEMORY.md").symlink_to(self.home / ".env")
        mem = self.r.memory(self.home)
        self.assertFalse(mem["memory"]["exists"])
        self.assertNotIn(hf.fake_key(), json.dumps(mem))

    @unittest.skipIf(os.name == "nt", "symbolic links need extra rights on Windows")
    def test_a_linked_memories_folder_is_unreadable(self):
        elsewhere = self.tmp / "elsewhere"
        shutil.move(str(self.home / "memories"), str(elsewhere))
        (self.home / "memories").symlink_to(elsewhere, target_is_directory=True)
        self.assertFalse(self.r.memory(self.home)["readable"])

    def test_the_source_cannot_write_run_a_program_or_import_hermes(self):
        text = (ROOT / "hermes_read.py").read_text(encoding="utf-8")
        tree = ast.parse(text)
        forbidden_attrs = {"write_text", "write_bytes", "unlink", "rmdir", "mkdir", "touch", "rename", "replace", "chmod", "chown",
                           "symlink_to", "truncate", "write", "writelines", "makedirs", "remove", "removedirs", "utime", "copy",
                           "copy2", "copyfile", "copytree", "move", "rmtree", "executescript", "commit"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, forbidden_attrs, f"hermes_read.py line {node.lineno} uses .{node.attr}")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
                for name in names:
                    self.assertFalse(re.match(r"(hermes_cli|hermes_constants|tools|agent|cron|subprocess|shutil|tempfile|socket|urllib\.request)\b", name or ""), name)
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
                if name == "open":
                    self.assertEqual(node.args[1].value if len(node.args) > 1 else "r", "rb", f"line {node.lineno}")
                if name == "execute" and node.args and isinstance(node.args[0], ast.Constant):
                    self.assertRegex(node.args[0].value.strip(), r"^SELECT\b", f"line {node.lineno}")
        self.assertNotRegex(text, r"\bsubprocess\b|\bos\.system\b|\bpopen\b")
        docstrings = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                if ".env" in node.value or "auth.json" in node.value:
                    self.assertIn(node.value, (".env", "auth.json"), f"line {node.lineno}: credential names appear only in the never-read list")


if __name__ == "__main__":
    unittest.main()
