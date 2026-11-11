"""The catalog entry reads plainly and says what it does: a short description with a "Disclosure:" sentence, honest
known_issues, and the same Hermes floor as plugin.yaml. The sha stays a placeholder until release pins it."""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENTRY_PATH = ROOT / "docs" / "catalog" / "field-academy.yaml"
# docs/catalog is private (.public-exclude): the public package has no catalog entry to check.
ENTRY = ENTRY_PATH.read_text(encoding="utf-8") if ENTRY_PATH.exists() else ""
PLUGIN = (ROOT / "plugin.yaml").read_text(encoding="utf-8")


def field(text, name):
    match = re.search(rf'^{name}:\s*"?(.*?)"?\s*$', text, re.M)
    return match.group(1) if match else None


@unittest.skipUnless(ENTRY_PATH.exists(), "docs/catalog is left out of the public package (.public-exclude)")
class CatalogEntry(unittest.TestCase):
    def test_the_description_is_short_and_carries_one_disclosure_sentence(self):
        description = field(ENTRY, "description")
        self.assertIsNotNone(description)
        self.assertLess(len(description), 1500)
        self.assertEqual(description.count("Disclosure:"), 1)
        self.assertNotIn("Disclosure —", description)
        for must in ("no network calls of its own", "sign-in", "npx", "hourly", "pre_llm_call", "Settings",
                     "plugin-data/field-academy"):
            self.assertIn(must, description)

    def test_known_issues_are_listed(self):
        block = ENTRY.split("known_issues:\n", 1)[1].split("\ncapabilities:", 1)[0]
        items = [line for line in block.splitlines() if line.startswith("- ")]
        self.assertGreaterEqual(len(items), 4)

    def test_the_hermes_floor_matches_plugin_yaml(self):
        self.assertEqual(field(ENTRY, "requires_hermes"), ">=0.22.0")
        self.assertEqual(field(PLUGIN, "requires_hermes"), ">=0.22.0")

    def test_the_sha_is_left_for_release(self):
        self.assertEqual(field(ENTRY, "sha"), "SHA_PLACEHOLDER")


if __name__ == "__main__":
    unittest.main()
