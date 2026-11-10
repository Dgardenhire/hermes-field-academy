"""One scrubber for every excerpt Field Academy keeps: the Guide's shapes, Cabinet's shapes, Telegram tokens and .env lines.

Every fake key and token here is built from parts when the test runs, so no scanner and no reader mistakes one for real.
"""

from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import random
import string
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name):
    package = sys.modules.get("fa_scrub_pkg")
    if package is None:
        package = types.ModuleType("fa_scrub_pkg")
        package.__path__ = [str(ROOT)]
        sys.modules["fa_scrub_pkg"] = package
    from importlib import import_module

    return import_module(f"fa_scrub_pkg.{name}")


RNG = random.Random(85)


def chars(n, alphabet=string.ascii_letters + string.digits):
    return "".join(RNG.choice(alphabet) for _ in range(n))


def fakes():
    """One made-up secret of every shape the scrubber must catch, keyed by shape."""
    return {
        "openai": "sk" + "-" + chars(32),
        "github": "gh" + "p_" + chars(36),
        "github_pat": "github" + "_pat_" + chars(40, string.ascii_letters + string.digits + "_"),
        "aws": "AK" + "IA" + chars(16, string.ascii_uppercase + string.digits),
        "slack": "xo" + "xb-" + chars(12, string.digits) + "-" + chars(24),
        "google": "AI" + "za" + chars(35, string.ascii_letters + string.digits + "_-"),
        "pem": "-----BEGIN " + "RSA PRIVATE" + " KEY-----",
        "bearer": "Bear" + "er " + chars(30),
        "jwt": "ey" + "J" + chars(20) + "." + chars(30) + "." + chars(22),
        "telegram": chars(9, string.digits) + ":" + chars(35, string.ascii_letters + string.digits + "_-"),
        "keyvalue": "api" + "_key = " + chars(24),
        "long": chars(48),
    }


class ScrubTests(unittest.TestCase):
    def setUp(self):
        self.scrub = load("scrub")

    def test_every_shape_is_removed(self):
        for kind, secret in fakes().items():
            text = f"before {secret} after"
            out = self.scrub.scrub(text)
            self.assertNotIn(secret, out, kind)
            self.assertIn("before", out, kind)
            self.assertIn("[removed]", out, kind)

    def test_a_telegram_bot_token_is_caught_on_its_own(self):
        token = chars(10, string.digits) + ":" + chars(35, string.ascii_letters + string.digits + "_-")
        self.assertEqual(self.scrub.scrub(f"bot {token} sent"), "bot [removed] sent")
        self.assertIn("a Telegram bot token", self.scrub.kinds(token))

    def test_env_lines_keep_the_name_and_lose_the_value(self):
        value = chars(10)
        text = "\n".join([
            f"OPENROUTER_API_KEY={value}",
            f"export TELEGRAM_BOT_TOKEN='{value}'",
            f"MY_SERVICE_SECRET = \"{value}\"",
            "HERMES_DEBUG=1",
        ])
        out = self.scrub.scrub(text)
        self.assertNotIn(value, out)
        self.assertIn("OPENROUTER_API_KEY=[removed]", out)
        self.assertIn("TELEGRAM_BOT_TOKEN", out)
        self.assertIn("MY_SERVICE_SECRET", out)
        self.assertIn("HERMES_DEBUG=1", out, "a line that names no key, token or secret stays")

    def test_ordinary_text_and_timestamps_are_left_alone(self):
        text = "2026-10-21T09:00:00Z Harbor Bakery uses QuickBooks Online; the other five use Xero. 1,234 chars."
        self.assertEqual(self.scrub.scrub(text), text)

    def test_the_limit_applies_after_scrubbing(self):
        secret = fakes()["openai"]
        out = self.scrub.scrub(secret + " tail", limit=12)
        self.assertNotIn(secret[:12], out)
        self.assertLessEqual(len(out), 12)

    def test_the_excerpt_hash_is_of_the_scrubbed_text(self):
        secret = fakes()["github"]
        excerpt, digest = self.scrub.excerpt(f"token in a line {secret}", limit=200)
        self.assertNotIn(secret, excerpt)
        self.assertEqual(digest, hashlib.sha256(excerpt.encode("utf-8")).hexdigest())

    def test_none_and_non_text_are_safe(self):
        self.assertEqual(self.scrub.scrub(None), "")
        self.assertEqual(self.scrub.scrub(12), "12")

    def test_the_guide_reader_uses_the_same_scrubber(self):
        evidence = load("evidence")
        secret = fakes()["telegram"]
        self.assertNotIn(secret, evidence.redact(f"run failed {secret}"))
        self.assertIs(evidence.SECRET_SHAPES, self.scrub.SHAPES_FOR_GUIDE)

    def test_kinds_name_what_was_found_without_the_value(self):
        found = self.scrub.kinds(fakes()["aws"] + " " + fakes()["pem"])
        self.assertIn("an AWS key", found)
        self.assertIn("a private key", found)


if __name__ == "__main__":
    unittest.main()


class Names(unittest.TestCase):
    def test_a_long_folder_name_made_of_words_stays_and_a_key_shaped_one_goes(self):
        scrub = load("scrub")
        self.assertEqual(scrub.scrub_name("harbor-bakery-quarterly-reconciliation-2026"), "harbor-bakery-quarterly-reconciliation-2026")
        self.assertEqual(scrub.scrub_name("academy-practice"), "academy-practice")
        self.assertEqual(scrub.scrub_name("Q" + "x7" * 25), scrub.REMOVED)
        self.assertNotIn("f1x7ure", scrub.scrub_name("sk" + "-" + "f1x7ure" + "0" * 14 + "abc"))

