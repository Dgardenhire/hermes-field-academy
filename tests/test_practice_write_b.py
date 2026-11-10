"""practice_write.py for missions 7 to 11: practice-folder files, the new config keys, and the working folder."""

from __future__ import annotations

import os
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402


class PracticeFolderWrites(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.row = self.ready()
        self.rec = self.practice.record("academy-practice")
        self.h = self.home()

    def test_files_land_only_inside_the_practice_folder(self):
        out = self.practice_write.write_practice_file(self.h, self.rec, "orders/order-101.txt", "Order 101\n")
        self.assertEqual(out["rel_path"], "practice-folder/orders/order-101.txt")
        self.assertEqual((self.h / "practice-folder" / "orders" / "order-101.txt").read_text(), "Order 101\n")
        for bad in ("../config.yaml", "/etc/passwd", "a/b/c/d.txt", ".env", "orders/../../x.txt"):
            with self.assertRaises(self.practice_write.Refused):
                self.practice_write.write_practice_file(self.h, self.rec, bad, "x")

    def test_a_link_in_the_folder_is_refused(self):
        folder = self.h / "practice-folder"
        folder.mkdir()
        os.symlink(self.tmp, folder / "orders")
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.write_practice_file(self.h, self.rec, "orders/order-101.txt", "x")

    def test_after_the_first_chat_nothing_is_written(self):
        self.chat()
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.write_practice_file(self.h, self.rec, "notes.md", "x")

    def test_new_keys_are_allowed_and_cwd_may_be_the_practice_folder_only(self):
        folder = self.practice_write.ensure_practice_folder(self.h, self.rec)
        self.practice_write.set_config(self.h, self.rec, {"terminal.cwd": folder, "command_allowlist": ["recursive delete"],
                                                          "mcp_servers.files.trust": "untrusted", "agent.disabled_toolsets": ["file"]})
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.set_config(self.h, self.rec, {"terminal.cwd": str(self.tmp)})
        for key in ("mcp_servers.files.env", "mcp_servers.files.headers", "agent.system_prompt"):
            with self.assertRaises(self.practice_write.Refused):
                self.practice_write.set_config(self.h, self.rec, {key: "x"})


if __name__ == "__main__":
    unittest.main()
