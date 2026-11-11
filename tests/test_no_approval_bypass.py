"""Catalog rule 12: Field Academy never routes around Hermes's approvals.

It must not write an approval setting or an always-allow entry, start a process, or tell a learner to switch approvals
off. These tests scan the code and the lesson text so a later edit can't bring any of that back.
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from foundations_support import FoundationsCase  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"tests", "docs", ".git", ".github", "__pycache__", "node_modules", "harness", "scripts"}


def sources(suffixes):
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if path.is_file() and path.suffix in suffixes and not (set(rel.parts) & SKIP_DIRS) and path.name != "plugin.js" \
                and path.name != "CHANGELOG.md":
            yield rel, path.read_text(encoding="utf-8", errors="replace")


class NoApprovalBypass(FoundationsCase):
    def test_no_code_writes_an_approval_setting_or_starts_a_process(self):
        bad = re.compile(r"""approvals\.mode["']?\s*[:=,]\s*["']?off|yolo|--yolo|auto.?approve|command_allowlist["']\s*:|"""
                         r"""subprocess|os\.system|os\.popen|Popen\(|child_process""", re.I)
        found = []
        for rel, text in sources({".py", ".js"}):
            if rel.parts[0] == "content":
                continue  # lesson text and the patterns it matches in Hermes's own source; the lesson test below covers it
            if rel.name in ("hermes_read.py", "hermes_read_b.py", "yaml_keys.py"):
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if bad.search(line) and "never" not in line.lower() and "cannot" not in line.lower():
                    found.append(f"{rel}:{n}: {line.strip()[:100]}")
        self.assertEqual(found, [])

    def test_the_writable_keys_exclude_approvals(self):
        practice_write = self.practice_write
        for key in ("approvals.mode", "approvals.timeout", "approvals.cron_mode", "command_allowlist"):
            self.assertFalse(any(p.match(key) for p in practice_write.WRITABLE_KEYS + practice_write.WRITABLE_KEYS_B), key)

    def test_no_lesson_tells_the_learner_to_switch_approvals_off(self):
        bad = re.compile(r"(?:switch|turn|set)\s+(?:the\s+)?(?:command\s+)?approvals?\s+(?:to\s+)?off|approvals?\s*(?:mode)?\s*:\s*off|"
                         r"disable\s+approvals|--yolo|set\s+yolo", re.I)
        found = []
        for rel, text in sources({".py", ".md", ".json"}):
            for n, line in enumerate(text.splitlines(), 1):
                if bad.search(line) and not re.search(r"never|don't|do not|not |without|nobody|if they|were off|is off|are off", line, re.I):
                    found.append(f"{rel}:{n}: {line.strip()[:110]}")
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
