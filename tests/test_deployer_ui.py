"""The Deployer path's page: its logic runs under node, its routes exist, and its words follow the curriculum voice."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from deployer_support import DeployerCase

ROOT = pathlib.Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


def run_node(test_file, env=None):
    import os

    result = subprocess.run([NODE, "--test", str(ROOT / "tests" / test_file)], capture_output=True, text=True, timeout=180, env={**os.environ, **(env or {})})
    return result


class Node(unittest.TestCase):
    def setUp(self):
        if not NODE:
            self.skipTest("node is not installed, so the page's logic can't run here")

    def test_the_reading_logic_runs_under_node(self):
        result = run_node("deploy.test.mjs")
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])

    def test_the_pure_module_imports_nothing(self):
        text = (ROOT / "desktop" / "src" / "deploy.js").read_text(encoding="utf-8")
        self.assertEqual([line for line in text.splitlines() if line.startswith("import ")], [])


class Trail(DeployerCase):
    def test_the_trail_runs_against_real_snapshots(self):
        if not NODE:
            self.skipTest("node is not installed")
        states = {"fresh": self.deployer.snapshot()}
        self.pass_labs()
        states["labs"] = self.deployer.snapshot()
        out = pathlib.Path(tempfile.mkdtemp()) / "deployer.json"
        out.write_text(json.dumps(states, default=str))
        result = run_node("deployer_trail.test.mjs", {"FA_DEPLOYER": str(out)})
        self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-3000:])


class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = (ROOT / "desktop" / "src" / "deployer.js").read_text(encoding="utf-8")
        cls.plugin = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")
        cls.api = (ROOT / "dashboard" / "plugin_api.py").read_text(encoding="utf-8")
        cls.bundle = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")

    def test_every_route_the_page_calls_exists_on_the_backend(self):
        calls = {re.sub(r"\$\{[^}]+\}", "{x}", c) for c in re.findall(r"ctxRest\(\s*[`'](/deployer[^`'?]*)", self.src + self.plugin)}
        self.assertGreaterEqual(len(calls), 15)
        routes = {re.sub(r"\{[^}]+\}", "{x}", r) for r in re.findall(r'@router\.(?:get|post)\("([^"]+)"', self.api)}
        for call in calls:
            self.assertIn(call, routes, f"the page calls {call} and the backend has no such route")

    def test_the_page_imports_only_what_a_plugin_may(self):
        for rel in ("deployer.js", "deploy.js"):
            text = (ROOT / "desktop" / "src" / rel).read_text(encoding="utf-8")
            for module in re.findall(r"^import .* from '([^']+)'", text, re.M):
                self.assertTrue(module in ("@hermes/plugin-sdk", "react", "react/jsx-runtime", "hermes-ui-kit") or module.startswith("./"), f"{rel} imports {module}")
        for module in re.findall(r"^\s*import\s[\s\S]*?\sfrom\s*[\"']([^\"']+)[\"']", self.bundle, re.M):
            self.assertIn(module, ("@hermes/plugin-sdk", "react", "react/jsx-runtime"), "the built page imports something else")

    def test_the_page_never_writes_to_hermes(self):
        """The only Hermes calls from the page are reads: the lists and the runtime check."""
        calls = re.findall(r"rpc\('([a-z._]+)'(?:,\s*(\{[^}]*\}))?", self.plugin)
        for method, args in calls:
            if method in ("cron.manage", "skills.manage"):
                self.assertIn("action: 'list'", args, f"{method} must only list")
        for method in ("cron.manage", "session.list", "setup.runtime_check"):
            self.assertIn(f"rpc('{method}'", self.plugin)
        self.assertNotRegex(self.src, r"rpc\(|host\.request")

    def test_the_honest_words_are_on_the_screens(self):
        for text in (
            "Guide, awaiting review", "Re-verify needed", "Hermes could not be read for this", "Field Academy will not take your word for it",
            "It cannot read", "Open the folder", "Copy the path", "Open the client\\'s machine", "Every key in a lab is made up",
            "Nothing in it runs",
        ):
            self.assertTrue(text in self.src or text.replace("\\'", "'") in self.src or text in self.plugin, text)
        self.assertIn("lifecycle_credit", self.src)
        self.assertIn("Whether a Kanban card exists", (ROOT / "deployer_content.py").read_text(encoding="utf-8"))
        self.assertIn("Deployer path", self.plugin)

    def test_the_built_page_carries_the_new_screens(self):
        for name in ("DeployerPath", "DeployerCertificate", "LabView", "DrillCard", "ReviewPanel", "FallbackBox"):
            self.assertIn(name, self.bundle)

    def test_the_map_shows_the_deployer_trail_and_the_page_routes_to_it(self):
        self.assertIn("view.id === 'deployer'", self.plugin)
        self.assertIn("view.name === 'deployer'", self.plugin)
        self.assertIn("DeployerTrailPanel", self.plugin)
        self.assertIn("useDeployer", self.plugin)

    def test_a_backend_without_the_tier_gets_a_plain_message_not_a_blank_page(self):
        self.assertIn("DeployerUnavailable", self.plugin)
        self.assertIn("Quit Hermes and open it again", self.plugin)


# ---------------------------------------------------------------- the voice --

CHECK_VOICE = ROOT / "scripts" / "check_voice.py"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆✅❌\U0001F000-\U0001F2FF]")


def voice():
    spec = importlib.util.spec_from_file_location("fa_check_voice", CHECK_VOICE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fa_check_voice"] = module
    spec.loader.exec_module(module)
    return module


class Words(DeployerCase):
    def strings(self):
        """Every learner-facing string the Deployer path owns, with where it came from."""
        out = []
        C = self.deployer_content
        for key in ("TITLE", "EYEBROW", "PROMISE", "LIFECYCLE_CREDIT", "ISSUER", "HONEST_LIMITS", "DRILL_NOTE"):
            out.append((key, getattr(C, key)))
        for line in C.WHAT_IT_CERTIFIES + C.WHAT_IT_DOES_NOT:
            out.append(("certifies", line))
        for phase in C.PHASES:
            out += [(f"phase {phase['id']}", phase["name"]), (f"phase {phase['id']} meaning", phase["meaning"])]
        out += [("item title", t) for t in C.ITEM_TITLES.values()]
        dep = C.DEPLOY
        out += [("deploy", dep["title"]), ("deploy", dep["intro"])] + [("deploy step", s) for s in dep["steps"] + dep["reads"] + dep["cannot_read"]]
        for rule in dep["record_sections"] + C.DRILL_SECTIONS:
            out += [(f"rule {rule['heading']}", rule[k]) for k in ("what", "fix", "hint", "example")]
        for d in C.DRILLS:
            out += [(f"drill {d['id']}", d["title"]), (f"drill {d['id']}", d["intro"]), (f"drill {d['id']} risk", d["risk"])] + [(f"drill {d['id']} step", s) for s in d["steps"]]
        out += [("walkthrough", C.WALKTHROUGH[k]) for k in ("title", "intro", "prompt")]
        for sc in self.scenarios.SCENARIOS:
            out += [(f"scenario {sc['id']}", sc["title"]), (f"scenario {sc['id']}", sc["situation"]), (f"scenario {sc['id']}", sc["question"])] + [(f"scenario {sc['id']} point", c) for c in sc["covers"]]
            for entry in sc["coach"]:
                out += [(f"scenario {sc['id']} coach", entry["hint"]), (f"scenario {sc['id']} coach", entry["example"])]
        for rule in self.brief.SECTIONS:
            out += [(f"brief {rule['heading']}", rule[k]) for k in ("what", "fix", "hint", "example")]
        for entry in self.brief.RUBRIC:
            out += [("brief rubric", entry["point"]), ("brief rubric", entry["hint"]), ("brief rubric", entry["example"])]
        for case_seed in (1, 2, 3):
            case = self.brief.brief_for(case_seed)
            out += [("brief case", case["brief"])] + [("brief case", c) for c in case["constraints"]]
        for key, entry in self.deployer.BRIEF_COACH.items():
            out += [(f"brief coach {key}", entry["hint"]), (f"brief coach {key}", entry["example"])]
        for lab_id in self.labs.LAB_IDS:
            for seed in (1, 2, 3, 4):
                spec = self.labs.spec_for(lab_id, seed)
                out += [(f"{lab_id} note", self.labs._client_note(spec))]
            built = self.labs.manifest(self.labs.spec_for(lab_id, 1), pathlib.Path("/x"))
            out += [(f"{lab_id} symptom", s) for s in built["symptoms"]] + [(f"{lab_id} hand in", s) for s in built["hand_in"]]
            out += [(f"{lab_id} title", self.labs.TITLES[lab_id]), (f"{lab_id} worked", self.grade.WORKED[lab_id]["title"]), (f"{lab_id} worked", self.grade.WORKED[lab_id]["body"])]
        for key, entry in list(self.grade.COACH.items()) + list(self.grade.WINDOWS_COACH.items()):
            out += [(f"coach {key}", entry["hint"]), (f"coach {key}", entry["example"])]
        out += [("lab.reboot worked on Windows", self.grade.WINDOWS_WORKED["lab.reboot"]["body"])]
        for rubric in self.walkthrough.RUBRIC:
            out += [(f"review {rubric['id']}", rubric["title"]), (f"review {rubric['id']}", rubric["look_for"])] + [(f"review {rubric['id']}", v) for v in rubric["scores"].values()]
        return [(where, text) for where, text in out if isinstance(text, str) and text.strip()]

    def test_the_curriculum_voice_check_finds_nothing_in_the_deployer_path(self):
        v = voice()
        findings = []
        for where, text in self.strings():
            for name, reason, pattern in v.CHECKS:
                hit = pattern.search(text)
                if hit:
                    findings.append(f"{where}: [{name}] {hit.group(0)[:70]!r}")
            for word, advice in v.JARGON.items():
                if advice and re.search(rf"\b{re.escape(word)}\b", text, re.I):
                    findings.append(f"{where}: [jargon] {word}")
            for hit in v.triads(text):
                findings.append(f"{where}: [triad] {hit[:70]!r}")
        self.assertEqual(findings, [], "\n".join(findings[:40]))

    def test_headings_name_the_thing_and_never_end_in_a_period(self):
        heads = list(self.deployer_content.ITEM_TITLES.values()) + [p["name"] for p in self.deployer_content.PHASES]
        heads += [d["title"] for d in self.deployer_content.DRILLS] + [s["title"] for s in self.scenarios.SCENARIOS] + list(self.labs.TITLES.values())
        heads += [self.deployer_content.DEPLOY["title"], self.deployer_content.WALKTHROUGH["title"], self.deployer_content.TITLE]
        for head in heads:
            self.assertFalse(head.rstrip().endswith("."), head)
        src = (ROOT / "desktop" / "src" / "deployer.js").read_text(encoding="utf-8")
        for title in re.findall(r"title: '([^']+)'", src):
            self.assertFalse(title.endswith("."), title)

    def test_no_emoji_anywhere_in_the_new_files(self):
        files = ["labs.py", "grade.py", "brief.py", "scenarios.py", "evidence.py", "walkthrough.py", "deployer.py", "deployer_content.py", "ed25519.py",
                 "desktop/src/deployer.js", "desktop/src/deploy.js", "docs/deployer-pedagogy.md", "docs/reviewing.md", "scripts/sign_review.py", "README.md", "CHANGELOG.md", "CREDITS.md"]
        for rel in files:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIsNone(EMOJI.search(text), f"{rel} holds an emoji")
        for where, text in self.strings():
            self.assertIsNone(EMOJI.search(text), where)

    def test_no_text_claims_more_than_the_path_can_back(self):
        blob = " ".join(text for _, text in self.strings()).lower()
        for banned in ("guarantee", "industry-recognized", "accredited", "official certification", "nous research certified", "endorsed by", "approved by nous"):
            self.assertNotIn(banned, blob)

    def test_the_lifecycle_credit_names_the_source_and_does_not_imply_endorsement(self):
        credit = self.deployer_content.LIFECYCLE_CREDIT
        self.assertIn("tonysimons.dev", credit)
        self.assertIn("has not reviewed", credit)
        self.assertIn("does not endorse", credit)
        self.assertIn("no certification", credit)
        for rel in ("README.md", "CREDITS.md", "docs/deployer-pedagogy.md"):
            self.assertIn("tonysimons.dev", (ROOT / rel).read_text(encoding="utf-8"), rel)

    def test_the_pedagogy_doc_says_what_could_not_be_verified_and_cites_each_source_it_uses(self):
        doc = (ROOT / "docs" / "deployer-pedagogy.md").read_text(encoding="utf-8")
        self.assertIn("**checked**", doc)
        self.assertIn("**from memory**", doc)
        self.assertIn("**not verified**", doc.lower().replace("not verified:", "**not verified**") if "**Not verified" not in doc else "**not verified**")
        for source in ("Wiggins", "Miller", "Harden", "Basiri", "McDaniel", "Jonsson", "Saltzer", "12factor.net", "Kane"):
            self.assertIn(source, doc)

    def test_the_reviewer_rubric_file_covers_every_line_the_plugin_scores(self):
        doc = (ROOT / "docs" / "reviewing.md").read_text(encoding="utf-8")
        self.assertIn("sign_review.py", doc)
        packet_rubric = self.walkthrough.rubric_markdown()
        for rid in self.walkthrough.RUBRIC_IDS:
            self.assertIn(rid, packet_rubric)
        self.assertEqual(len(self.walkthrough.RUBRIC), 6)


class SignScript(DeployerCase):
    def test_the_reviewers_script_makes_a_key_and_signs_a_packet_the_plugin_accepts(self):
        import os

        folder = pathlib.Path(tempfile.mkdtemp())
        key = folder / "reviewer.key"
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sign_review.py"), "keygen", "--out", str(key)], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        fileaccess = importlib.import_module(f"{self.name}.fileaccess")
        self.assertTrue(fileaccess.is_private(key), f"the secret key must be readable only by its owner: {fileaccess.others(key)}")
        if not fileaccess.ON_WINDOWS:
            self.assertEqual(oct(key.stat().st_mode & 0o777), "0o600")
        again = subprocess.run([sys.executable, str(ROOT / "scripts" / "sign_review.py"), "keygen", "--out", str(key)], capture_output=True, text=True)
        self.assertNotEqual(again.returncode, 0, "it must not overwrite an existing key")
        public = re.search(r"Public key:\s+([0-9a-f]{64})", out.stdout).group(1)
        packet = self.walkthrough.build_packet(
            {"learner": "Ada", "labs": [], "brief": {}, "scenarios": [], "deployment": {}, "drills": [], "fallback_evidence": [{"item": "deploy"}], "walkthrough": {}, "limits": ""},
            "2026-10-03T00:00:00Z",
        )
        path = folder / "packet.json"
        path.write_text(json.dumps(packet))
        args = [sys.executable, str(ROOT / "scripts" / "sign_review.py"), "sign", "--packet", str(path), "--key", str(key), "--name", "Dr. Reviewer", "--decision", "approved", "--out", str(folder / "so.json"), "--accept", "deploy"]
        for rid in self.walkthrough.RUBRIC_IDS:
            args += ["--score", f"{rid}=3"]
        signed = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(signed.returncode, 0, signed.stderr)
        signoff = json.loads((folder / "so.json").read_text(encoding="utf-8"))
        packet_check = self.walkthrough.verify_signoff(signoff, packet, {public: {"name": "Dr. Reviewer", "list": "published"}})
        self.assertTrue(packet_check["approved"], packet_check["problems"])
        self.assertEqual(packet_check["accepted_evidence"], ["deploy"])
        # a score outside the scale, a missing line, an unknown accept, and an edited packet are all refused
        for extra, label in (([ "--score", "safety=9"], "scale"), ([ "--accept", "nope"], "accept")):
            bad = subprocess.run(args + extra, capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0, label)
        short = [a for a in args if not a.startswith(("diagnosis=", "safety="))]
        edited = dict(packet, learner="Someone Else")
        path.write_text(json.dumps(edited))
        self.assertNotEqual(subprocess.run(args, capture_output=True, text=True).returncode, 0, "an edited packet must not be signed")

    def test_the_published_reviewer_list_ships_and_is_valid_json(self):
        data = json.loads((ROOT / "reviewers" / "trusted-reviewers.json").read_text(encoding="utf-8"))
        self.assertEqual(data["reviewers"], [])
        self.assertIn("ships empty", data["about"])
        self.assertEqual(self.walkthrough.load_trusted(ROOT / "reviewers" / "trusted-reviewers.json", None), {})

    def test_a_garbled_reviewer_list_is_ignored_not_trusted(self):
        bad = pathlib.Path(tempfile.mkdtemp()) / "r.json"
        bad.write_text("{not json")
        self.assertEqual(self.walkthrough.load_trusted(bad, None), {})
        bad.write_text(json.dumps({"reviewers": [{"name": "x", "public_key": "abc"}, {"name": "y", "public_key": "00" * 32}]}))
        self.assertEqual(list(self.walkthrough.load_trusted(bad, None)), ["00" * 32])


if __name__ == "__main__":
    unittest.main()
