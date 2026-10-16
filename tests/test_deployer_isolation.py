"""Isolation. The Deployer tier builds disposable folders and reads Hermes. It must never touch the real Hermes home.

Three layers, because a past scratch Hermes home was not isolated and rewrote real launchers:

1. The whole path is run with HOME and HERMES_HOME pointed at a folder that does not exist. If any code
   reached for the real home, the folder would appear (DeployerCase.tearDown fails the test).
2. The real ~/.hermes is fingerprinted before and after, read only. If a single watched entry changes,
   this test fails.
3. The source is searched for the ways code could run a program, reach the network, or write to Hermes.
"""

from __future__ import annotations

import pathlib
import re
import unittest

from deployer_support import DeployerCase, REAL_HERMES_HOME, real_home_fingerprint, good_proposal

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULES = ("labs", "grade", "evidence", "deployer", "walkthrough", "brief", "scenarios", "deployer_content", "ed25519", "fileaccess")

FORBIDDEN = {
    "running a program": re.compile(r"\bsubprocess\b|\bos\.system\b|\bos\.popen\b|\bos\.exec\w*\b|\bos\.spawn\w*\b|\bpty\b|\bshlex\b"),
    "dynamic code": re.compile(r"(?<![\w.])eval\(|(?<![\w.])exec\(|\b__import__\("),
    "the network": re.compile(r"\b(?:import|from) (?:socket|requests|httpx|aiohttp|smtplib|ssl|ftplib|telnetlib|http\.client)\b|\burllib\.request\b|\burlopen\b"),
    "a hermes command": re.compile(r"\bhermes (?:doctor|plugins|gateway|chat|cron|config|model|update|setup|dashboard|sessions|skills|tools|profile)\b"),
}


class Static(unittest.TestCase):
    def source(self, name):
        return (ROOT / f"{name}.py").read_text(encoding="utf-8")

    def test_no_module_of_the_tier_can_run_a_program_reach_the_network_or_call_hermes(self):
        for name in MODULES:
            text = self.source(name)
            for label, pattern in FORBIDDEN.items():
                hit = pattern.search(text)
                self.assertIsNone(hit, f"{name}.py uses {label}: {hit.group(0) if hit else ''}")

    def test_the_evidence_reader_never_writes(self):
        """evidence.py reads Hermes. Any call in it that could write, delete or change a file or a database fails this test.

        Checked on the parsed source, so a word in a comment cannot trip it and a call cannot hide in a string.
        """
        import ast

        tree = ast.parse(self.source("evidence"))
        forbidden_attrs = {"write_text", "write_bytes", "unlink", "rmdir", "mkdir", "touch", "rename", "chmod", "chown", "symlink_to", "truncate",
                           "write", "writelines", "makedirs", "remove", "removedirs", "utime", "copy", "copy2", "copyfile", "copytree", "move", "rmtree", "executescript", "commit"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, forbidden_attrs, f"evidence.py line {node.lineno} uses .{node.attr}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(alias.name, ("shutil", "subprocess", "tempfile"), f"evidence.py imports {alias.name}")
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
                if name == "open":
                    mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
                    if isinstance(node.func, ast.Attribute) and node.args:
                        mode = node.args[0]
                    if mode is not None:
                        self.assertIsInstance(mode, ast.Constant, f"evidence.py line {node.lineno}: open mode must be a plain string")
                        self.assertTrue(set(mode.value) <= set("rbt"), f"evidence.py line {node.lineno} opens a file with mode {mode.value!r}")
                if name == "execute" and node.args:
                    arg = node.args[0]
                    self.assertIsInstance(arg, (ast.Constant, ast.JoinedStr), f"evidence.py line {node.lineno}")
                    text = arg.value if isinstance(arg, ast.Constant) else "".join(v.value for v in arg.values if isinstance(v, ast.Constant))
                    self.assertRegex(text.strip(), r"^(?i:SELECT\b|PRAGMA query_only)", f"evidence.py line {node.lineno} runs SQL that is not a read: {text[:40]!r}")
        text = self.source("evidence")
        self.assertIn("mode=ro&immutable=1", text, "run history must be opened read-only and immutable")
        self.assertIn("PRAGMA query_only = ON", text)

    def test_only_two_places_delete_anything_and_both_are_guarded(self):
        removers = {name: len(re.findall(r"shutil\.rmtree|\.unlink\(|os\.remove", self.source(name))) for name in MODULES}
        self.assertEqual({k: v for k, v in removers.items() if v}, {"labs": 1, "walkthrough": 1})
        labs_text = self.source("labs")
        reset = labs_text[labs_text.index("def reset_lab"):labs_text.index("def listing")]
        self.assertIn("MARKER", reset, "reset_lab must check the marker file before deleting")
        self.assertIn("shutil.rmtree(root.parent)", reset)
        wt = self.source("walkthrough")
        self.assertEqual(wt.count("shutil.rmtree(copies)"), 1, "the packet only ever removes its own labs/ copy")

    def test_the_lab_builder_is_the_only_code_that_looks_for_a_hermes_home_and_only_to_refuse_it(self):
        text = self.source("labs")
        guard = text[text.index("def safe_labs_dir"):text.index("def lab_root")]
        everywhere = len(re.findall(r"Path\.home\(\)|expanduser\(", text))
        self.assertGreaterEqual(everywhere, 2)
        self.assertEqual(everywhere, len(re.findall(r"Path\.home\(\)|expanduser\(", guard)), "every look for a home sits in safe_labs_dir, which refuses it")
        for other in ("grade", "brief", "scenarios", "walkthrough", "deployer_content"):
            self.assertNotRegex(self.source(other), r"Path\.home\(\)|HERMES_HOME")

    def test_only_the_reads_of_hermes_use_its_home_and_only_the_checks_pass_it_in(self):
        deployer = self.source("deployer")
        self.assertEqual(deployer.count("HERMES_HOME"), 1)
        self.assertIn("def _hermes_home", deployer)
        evidence = self.source("evidence")
        self.assertNotIn("HERMES_HOME", evidence)
        self.assertNotIn("Path.home", evidence)

    def test_the_lab_never_names_a_real_hermes_path_a_learner_could_mistake_for_their_own(self):
        text = self.source("labs")
        self.assertNotIn("~/.hermes", text.replace("never a Hermes home", ""))
        self.assertIn("/srv/hermes-client", text)


class FullPath(DeployerCase):
    """Run the whole path and prove nothing outside Field Academy's data folder was touched."""

    def test_the_whole_path_leaves_the_real_hermes_home_exactly_as_it_was(self):
        before = real_home_fingerprint()
        for lab_id in self.labs.LAB_IDS:
            view, spec, diagnosis = self.open_and_solve(lab_id)
            self.deployer.check_lab(lab_id, diagnosis)
            self.deployer.new_variant(lab_id)
        brief = self.brief.brief_for(1)
        self.deployer.brief_submit(self.file("p.md", good_proposal(self.deployer_brief_case())))
        self.deployer.snapshot()
        self.deployer.deploy_start("A test service", "deployer-isolation-check")
        self.deployer.deploy_check(home=self.fence / "nothing-here")
        self.assertEqual(real_home_fingerprint(), before, f"the real Hermes home at {REAL_HERMES_HOME} changed while the Deployer tier ran")

    def deployer_brief_case(self):
        with self.store.connect() as conn:
            return self.brief.brief_for(self.deployer._brief_seed(conn))

    def test_every_file_written_is_inside_the_data_folder(self):
        for lab_id in self.labs.LAB_IDS:
            self.open_and_solve(lab_id)
        self.deployer.snapshot()
        data = self.data.resolve()
        for lab_id in self.labs.LAB_IDS:
            with self.store.connect() as conn:
                row = self.deployer._lab_row(conn, lab_id)
            self.assertTrue(pathlib.Path(row["folder"]).resolve().is_relative_to(data / "labs"))
        self.assertFalse((self.fence / "home").exists())
        self.assertEqual(sorted(p.name for p in self.fence.iterdir()), [])

    def test_a_test_that_touched_the_fake_home_would_fail(self):
        """Prove the fence works: if code made the fake home, tearDown reports it."""
        self.fake_home.mkdir()
        with self.assertRaises(AssertionError):
            try:
                self.tearDown()
            finally:
                self.setUp()

    def test_the_fingerprint_notices_a_change(self):
        """The real-home test can only fail if the fingerprint can change. Prove it on a stand-in folder."""
        import deployer_support

        stand_in = self.fence / ".hermes"
        (stand_in / "cron").mkdir(parents=True)
        (stand_in / "config.yaml").write_text("a: 1\n")
        original = deployer_support.REAL_HERMES_HOME
        deployer_support.REAL_HERMES_HOME = stand_in
        try:
            first = deployer_support.real_home_fingerprint()
            (stand_in / "config.yaml").write_text("a: 22\n")
            self.assertNotEqual(deployer_support.real_home_fingerprint(), first)
            second = deployer_support.real_home_fingerprint()
            (stand_in / "cron" / "jobs.json").write_text("{}")
            self.assertNotEqual(deployer_support.real_home_fingerprint(), second)
            (stand_in / "logs").mkdir()
            (stand_in / "logs" / "agent.log").write_text("noise")
            third = deployer_support.real_home_fingerprint()
            (stand_in / "logs" / "agent.log").write_text("more noise")
            self.assertEqual(deployer_support.real_home_fingerprint(), third, "a running Hermes writing logs must not fail the test")
        finally:
            deployer_support.REAL_HERMES_HOME = original


if __name__ == "__main__":
    unittest.main()
