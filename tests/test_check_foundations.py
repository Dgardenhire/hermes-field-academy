"""scripts/check_foundations.py: the rules a Foundations mission must meet, and the "as of Hermes" source check.

The first real catch of the source check: Hermes 0.22.4 turned sessions.auto_prune off by default (0.22.2 had it on).
A fixture source tree laid out like 0.22.2 must fail the fixture mission's auto_prune fact; one like 0.22.4 must pass.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import re
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = pathlib.Path(__file__).resolve().parent / "data" / "foundations"
TESTS = pathlib.Path(__file__).resolve().parent

SOURCE_0224 = '''DEFAULTS = {
    "memory": {
        "write_approval": False,
        "memory_char_limit": 2200,   # ~800 tokens at 2.75 chars/token
        "user_char_limit": 1375,     # ~500 tokens at 2.75 chars/token
    },
    "checkpoints": {
        "auto_prune": True,
        "retention_days": 7,
    },
    "sessions": {
        # Off by default (deleting history is opt-in).
        "auto_prune": False,
        # Inactive days of ended-session history to keep (= `hermes sessions prune`).
        "retention_days": 90,
    },
}
'''
SOURCE_0222 = SOURCE_0224.replace('''        # Off by default (deleting history is opt-in).
        "auto_prune": False,''', '''        "auto_prune": True,''')


def checker():
    spec = importlib.util.spec_from_file_location("fa_check_foundations", ROOT / "scripts" / "check_foundations.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckerCase(unittest.TestCase):
    def setUp(self):
        self.c = checker()
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.content = self.tmp / "content"
        shutil.copytree(FIXTURE, self.content)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_check(self, source=None, folder=None):
        out = io.StringIO()
        args = ["--dir", str(folder or self.content), "--tests", str(TESTS)]
        if source is not None:
            args += ["--hermes-source", str(source)]
        with contextlib.redirect_stdout(out):
            code = self.c.main(args)
        return code, out.getvalue()

    def edit(self, old, new, name="f_fixture.py"):
        path = self.content / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def source_tree(self, text):
        tree = self.tmp / "hermes-agent"
        (tree / "hermes_cli").mkdir(parents=True, exist_ok=True)
        (tree / "hermes_cli" / "config_defaults.py").write_text(text, encoding="utf-8")
        return tree


class Rules(CheckerCase):
    def test_the_fixture_mission_passes(self):
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_the_shipped_folder_passes(self):
        code, out = self.run_check(folder=ROOT / "content" / "foundations")
        self.assertEqual(code, 0, out)

    def assert_fails(self, needle):
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertRegex(out, needle)

    def test_an_authors_note_or_a_meta_header_in_learner_text_fails(self):
        path = self.content / "md" / "f.fixture.idea.md"
        text = path.read_text(encoding="utf-8")
        for note, needle in (("[DAMON: what do you check first?]", r"author's note"), ("[BUILD: wire this]", r"author's note"),
                             ("[STAMP 0.22]", r"author's note"), ("## Build notes", r"how the lesson was made"),
                             ("Rewritten Oct 21 to TEACHING-STANDARD.md.", r"how the lesson was made")):
            path.write_text(text + "\n\n" + note + "\n", encoding="utf-8")
            self.content_mod.clear_cache() if hasattr(self, "content_mod") else None
            self.assert_fails(needle)
        path.write_text(text, encoding="utf-8")

    def test_the_shipped_folder_has_no_warnings(self):
        code, out = self.run_check(folder=ROOT / "content" / "foundations")
        self.assertNotIn("warning:", out)

    def test_a_list_whose_first_item_lost_its_marker_fails(self):
        path = self.content / "md" / "f.fixture.idea.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text + "\n\n## Also good to know\n\n**One.** First.\n- **Two.** Second.\n", encoding="utf-8")
        self.assert_fails(r"first item lost its '- '")

    def test_a_short_idea_fails(self):
        (self.content / "md" / "f.fixture.idea.md").write_text("Too short. " * 30, encoding="utf-8")
        self.assert_fails(r"idea.*words")

    def test_an_expert_run_needs_four_full_steps(self):
        path = self.content / "md" / "f.fixture.expert.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text[: text.index("## Step 4")], encoding="utf-8")
        self.assert_fails(r"expert run has 3 steps")
        path.write_text(text.replace("- **Ruled out:** Trusting the reply on its own.\n", ""), encoding="utf-8")
        self.assert_fails(r"ruled out")

    def test_the_standard_has_three_to_five_checks_each_proved_by_something_real(self):
        self.edit('"proves_by": "live:fresh_use"', '"proves_by": "live:nothing"')
        self.assert_fails(r"s2.*nothing")

    def test_every_reader_must_be_registered(self):
        self.edit('"reader": "memory.user_line"', '"reader": "memory.unknown"')
        self.assert_fails(r"memory\.unknown")

    def test_every_plant_needs_a_planter_detector_and_verifier(self):
        self.edit('"plants": ["write_approval", "memory_full", "wrong_profile"]', '"plants": ["write_approval", "stale_file"]')
        self.assert_fails(r"stale_file")

    def test_the_rubric_has_exactly_four_levels_and_a_pass_level_from_two_to_four(self):
        self.edit('"pass_level": 3', '"pass_level": 1')
        self.assert_fails(r"pass_level")
        self.edit('"pass_level": 1', '"pass_level": 3')
        self.edit('            4: "Three reasons', '            "x": "Three reasons')
        self.assert_fails(r"four levels")

    def test_cost_and_transfer_are_required(self):
        self.edit('"cost": {"chats": 2, "words": "a few cents in model fees"},', "")
        self.assert_fails(r"cost")

    def test_a_transfer_check_must_exist(self):
        self.edit('"live_checks": ["user_line", "skill_not_memory"]', '"live_checks": ["missing_check"]')
        self.assert_fails(r"missing_check")

    def test_the_voice_rules_apply(self):
        self.edit("Pick one real fact", "This is not a quiz, but a test. Pick one real fact")
        self.assert_fails(r"negation|voice")

    def test_every_reader_has_a_fixture_test(self):
        empty = self.tmp / "no-tests"
        empty.mkdir()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.c.main(["--dir", str(self.content), "--tests", str(empty)])
        self.assertEqual(code, 1)
        self.assertIn("fixture test", out.getvalue())


class AsOfHermes(CheckerCase):
    def test_a_0_22_4_source_tree_passes(self):
        code, out = self.run_check(self.source_tree(SOURCE_0224))
        self.assertEqual(code, 0, out)
        self.assertIn("2 as-of facts match", out)

    def test_the_auto_prune_drift_fails_on_a_0_22_2_source_tree(self):
        code, out = self.run_check(self.source_tree(SOURCE_0222))
        self.assertEqual(code, 1, out)
        self.assertIn("Old chats are kept until you choose to clear them", out)
        self.assertNotRegex(out, re.escape("MEMORY.md holds 2,200 characters") + r".*no longer")

    def test_a_missing_file_fails(self):
        tree = self.tmp / "empty-source"
        tree.mkdir()
        code, out = self.run_check(tree)
        self.assertEqual(code, 1)
        self.assertIn("hermes_cli/config_defaults.py", out)

    def test_the_environment_variable_turns_it_on(self):
        tree = self.source_tree(SOURCE_0222)
        import os

        os.environ["HERMES_SOURCE"] = str(tree)
        try:
            code, _ = self.run_check()
        finally:
            del os.environ["HERMES_SOURCE"]
        self.assertEqual(code, 1)


class AsOfHermesRelease(CheckerCase):
    """--hermes-ref reads the facts at a release tag from git's objects, whatever branch the checkout is on."""

    def git(self, tree, *args):
        import subprocess
        env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        subprocess.run(["git", "-C", str(tree), *args], check=True, capture_output=True, env=env)

    def release_tree(self):
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        tree = self.source_tree(SOURCE_0224)
        self.git(tree, "init", "-q", "-b", "main")
        self.git(tree, "add", "-A")
        self.git(tree, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "release")
        self.git(tree, "tag", "v0.23.0")
        (tree / "hermes_cli" / "config_defaults.py").write_text(SOURCE_0222, encoding="utf-8")
        return tree

    def run_ref(self, tree, ref):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.c.main(["--dir", str(self.content), "--tests", str(TESTS), "--hermes-source", str(tree), "--hermes-ref", ref])
        return code, out.getvalue()

    def test_the_tag_is_read_not_the_working_tree(self):
        tree = self.release_tree()
        code, out = self.run_check(tree)
        self.assertEqual(code, 1, "the working tree has the 0.22.2 drift")
        code, out = self.run_ref(tree, "v0.23.0")
        self.assertEqual(code, 0, out)
        self.assertIn("match the Hermes source", out)
        self.assertIn("at v0.23.0", out)

    def test_an_unknown_tag_fails_and_a_strange_ref_is_refused(self):
        tree = self.release_tree()
        code, out = self.run_ref(tree, "v9.9.9")
        self.assertEqual(code, 1)
        self.assertIn("is not in the Hermes source", out)
        with self.assertRaises(SystemExit):
            self.run_ref(tree, "--output=/tmp/x")
        self.assertIsNone(self.c.source_reader(tree, "v0.23.0")("../outside.py"))


if __name__ == "__main__":
    unittest.main()
