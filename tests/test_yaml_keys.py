"""Reading named keys from a Hermes config.yaml, and setting a few, with no YAML package.

Why not PyYAML: the plugin takes no outside packages, and a load-then-dump round trip would rewrite the learner's
whole practice config (comments, order, quoting). The editor here changes only the lines it names, so the profile's
fingerprint shows exactly the planted keys and nothing else.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from test_scrub import load  # noqa: E402

try:  # only as an outside cross-check when it happens to be installed
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


class Reading(unittest.TestCase):
    def setUp(self):
        self.y = load("yaml_keys")
        self.tree = self.y.parse(hf.CONFIG)

    def test_nested_scalars_lists_and_list_items_with_keys(self):
        self.assertEqual(self.y.get(self.tree, "memory.write_approval"), False)
        self.assertEqual(self.y.get(self.tree, "memory.memory_char_limit"), 2200)
        self.assertEqual(self.y.get(self.tree, "toolsets"), ["hermes-cli", "web"])
        self.assertEqual(self.y.get(self.tree, "fallback_providers"), [{"provider": "openrouter", "model": "openai/gpt-5-mini"}])
        self.assertEqual(self.y.get(self.tree, "mcp_servers.github.trust"), "untrusted")
        self.assertEqual(self.y.get(self.tree, "compression.threshold"), 0.5)
        self.assertEqual(self.y.get(self.tree, "memory.provider"), "")
        self.assertIsNone(self.y.get(self.tree, "memory.nope"))

    def test_a_block_of_text_is_never_read_as_keys(self):
        # agent.system_prompt holds "memory:\n  write_approval: true" as text. It must not leak out as a key.
        self.assertEqual(self.y.get(self.tree, "memory.write_approval"), False)
        self.assertIsInstance(self.y.get(self.tree, "agent.system_prompt"), self.y.Text)

    def test_odd_lines_are_skipped_not_fatal(self):
        tree = self.y.parse("---\nmodel: x\n\tbad: tab\n  orphan: deeper\nflow: {a: 1, b: [2]}\nanchor: &a hello\nlist: [one, 'two, three']\nmode: 'wal'  # values: \"wal\", \"delete\"\nesc: 'it''s'\n")
        self.assertEqual(self.y.get(tree, "model"), "x")
        self.assertEqual(self.y.get(tree, "anchor"), "&a hello")
        self.assertEqual(self.y.get(tree, "list"), ["one", "two, three"])
        self.assertIsInstance(self.y.get(tree, "flow"), self.y.Text)
        self.assertEqual(self.y.get(tree, "mode"), "wal", "a quoted value followed by a comment (Hermes's example config has one)")
        self.assertEqual(self.y.get(tree, "esc"), "it's")

    def test_windows_line_endings_read_the_same(self):
        self.assertEqual(self.y.parse(hf.CONFIG.replace("\n", "\r\n")), self.tree)

    @unittest.skipIf(yaml is None, "PyYAML is not installed here")
    def test_agrees_with_pyyaml_on_every_plain_value(self):
        full = yaml.safe_load(hf.CONFIG)
        for path in ("memory.write_approval", "memory.user_char_limit", "toolsets", "approvals.mode", "sessions.retention_days", "checkpoints.enabled"):
            node = full
            for part in path.split("."):
                node = node[part]
            self.assertEqual(self.y.get(self.tree, path), node, path)


class Setting(unittest.TestCase):
    def setUp(self):
        self.y = load("yaml_keys")

    def test_an_existing_value_changes_and_nothing_else_does(self):
        out = self.y.set_values(hf.CONFIG, {"memory.write_approval": True})
        before, after = hf.CONFIG.splitlines(), out.splitlines()
        self.assertEqual(len(before), len(after))
        changed = [(a, b) for a, b in zip(before, after) if a != b]
        self.assertEqual(changed, [("  write_approval: false", "  write_approval: true")])
        self.assertIs(self.y.get(self.y.parse(out), "memory.write_approval"), True)
        self.assertIs(self.y.get(self.y.parse(out), "skills.write_approval"), False, "the other write_approval is untouched")

    def test_a_missing_key_is_added_under_its_section(self):
        text = "model:\n  default: x\nmemory:\n  memory_enabled: true\n"
        out = self.y.set_values(text, {"memory.write_approval": True})
        self.assertEqual(out, "model:\n  default: x\nmemory:\n  write_approval: true\n  memory_enabled: true\n")

    def test_a_missing_section_is_added_at_the_end(self):
        out = self.y.set_values("model:\n  default: x\n", {"memory.write_approval": True, "memory.memory_char_limit": 2200})
        tree = self.y.parse(out)
        self.assertIs(self.y.get(tree, "memory.write_approval"), True)
        self.assertEqual(self.y.get(tree, "memory.memory_char_limit"), 2200)
        self.assertTrue(out.startswith("model:\n  default: x\n"))

    def test_an_empty_section_is_filled(self):
        for empty in ("memory:\n", "memory: {}\n", "memory: null\n", "memory: ~\n"):
            out = self.y.set_values("model: x\n" + empty, {"memory.write_approval": True})
            self.assertIs(self.y.get(self.y.parse(out), "memory.write_approval"), True, empty)

    def test_strings_are_quoted_and_numbers_are_not(self):
        out = self.y.set_values("cron:\n  model: ''\n", {"cron.model": "openai/gpt-5-mini: fast", "compression.threshold": 0.4})
        tree = self.y.parse(out)
        self.assertEqual(self.y.get(tree, "cron.model"), "openai/gpt-5-mini: fast")
        self.assertEqual(self.y.get(tree, "compression.threshold"), 0.4)

    def test_a_value_that_is_a_block_or_a_full_flow_mapping_is_refused(self):
        with self.assertRaises(ValueError):
            self.y.set_values(hf.CONFIG, {"memory": True})
        with self.assertRaises(ValueError):
            self.y.set_values("memory: {write_approval: false}\n", {"memory.write_approval": True})

    def test_only_plain_values_can_be_written(self):
        for bad in ([1], {"a": 1}, None, "line\nbreak"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.y.set_values(hf.CONFIG, {"memory.write_approval": bad})

    def test_line_endings_are_kept(self):
        out = self.y.set_values(hf.CONFIG.replace("\n", "\r\n"), {"memory.write_approval": True})
        self.assertNotIn("\n", out.replace("\r\n", ""))

    @unittest.skipIf(yaml is None, "PyYAML is not installed here")
    def test_pyyaml_reads_the_edit_the_same_way(self):
        out = self.y.set_values(hf.CONFIG, {"memory.write_approval": True, "cron.model": "x: y", "sessions.auto_prune": True})
        full = yaml.safe_load(out)
        self.assertIs(full["memory"]["write_approval"], True)
        self.assertEqual(full["cron"]["model"], "x: y")
        self.assertIs(full["sessions"]["auto_prune"], True)


if __name__ == "__main__":
    unittest.main()
