"""Writing short lists into a practice config.yaml (missions 7, 9 and 10): connector arguments, tool allow lists,
switched-off toolsets and the always-allow list. Inline lists only; a block list is never rewritten."""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_scrub import load  # noqa: E402

FRESH = """model:
  default: anthropic/claude-sonnet-4.6
agent:
  disabled_toolsets: []
mcp_servers: {}
command_allowlist: []
toolsets:
- hermes-cli
"""


class Lists(unittest.TestCase):
    def setUp(self):
        self.y = load("yaml_keys")

    def test_a_connector_entry_and_lists_are_written_and_read_back(self):
        folder = "C:\\Users\\Ada Lin\\practice-folder"
        out = self.y.set_values(FRESH, {
            "mcp_servers.files.command": "npx",
            "mcp_servers.files.args": ["-y", "@modelcontextprotocol/server-filesystem@2026.8.31", folder],
            "mcp_servers.files.tools.include": [],
            "agent.disabled_toolsets": ["file", "terminal"],
            "command_allowlist": ["recursive delete"],
        })
        tree = self.y.parse(out)
        self.assertEqual(self.y.get(tree, "mcp_servers.files.args")[2], folder)
        self.assertEqual(self.y.get(tree, "mcp_servers.files.tools.include"), [])
        self.assertEqual(self.y.get(tree, "agent.disabled_toolsets"), ["file", "terminal"])
        self.assertEqual(self.y.get(tree, "command_allowlist"), ["recursive delete"])
        self.assertIn("- hermes-cli", out)  # the block list is untouched

    def test_an_inline_list_is_replaced_but_a_block_list_is_refused(self):
        out = self.y.set_values(FRESH, {"command_allowlist": ["recursive delete"]})
        out = self.y.set_values(out, {"command_allowlist": []})
        self.assertEqual(self.y.get(self.y.parse(out), "command_allowlist"), [])
        with self.assertRaises(ValueError):
            self.y.set_values(FRESH, {"toolsets": ["web"]})

    def test_only_short_lists_of_one_line_strings(self):
        for bad in (["a\nb"], [1, 2], ["x"] * 60, [{"a": 1}]):
            with self.assertRaises(ValueError):
                self.y.set_values(FRESH, {"command_allowlist": bad})


if __name__ == "__main__":
    unittest.main()
