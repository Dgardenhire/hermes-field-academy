"""The lab builder: reproducible per seed, varied across seeds, fake everywhere, and fenced in."""

from __future__ import annotations

import importlib
import json
import os
import pathlib
import re
import unittest

from deployer_support import DeployerCase

SEEDS = list(range(1, 31))


class RFC8032(unittest.TestCase):
    """The signature code is the reference algorithm, so it must reproduce the RFC's own vectors."""

    def setUp(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("fa_ed", pathlib.Path(__file__).resolve().parents[1] / "ed25519.py")
        self.ed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ed)

    def test_test_vector_1_empty_message(self):
        secret = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
        self.assertEqual(self.ed.public_key(secret).hex(), "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        self.assertEqual(
            self.ed.sign(secret, b"").hex(),
            "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
        )

    def test_test_vector_2_one_byte(self):
        secret = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")
        self.assertEqual(self.ed.public_key(secret).hex(), "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c")
        self.assertEqual(
            self.ed.sign(secret, bytes.fromhex("72")).hex(),
            "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00",
        )

    def test_a_signature_fails_when_the_message_or_key_changes(self):
        secret = bytes(range(32))
        public = self.ed.public_key(secret)
        signature = self.ed.sign(secret, b"hello")
        self.assertTrue(self.ed.verify(public, b"hello", signature))
        self.assertFalse(self.ed.verify(public, b"hellp", signature))
        other = self.ed.public_key(bytes(range(1, 33)))
        self.assertFalse(self.ed.verify(other, b"hello", signature))
        self.assertFalse(self.ed.verify(public, b"hello", signature[:-1] + bytes([signature[-1] ^ 1])))
        self.assertFalse(self.ed.verify(public, b"hello", b"short"))


class Builder(DeployerCase):
    def tree(self, root):
        out = {}
        for path in sorted(pathlib.Path(root).rglob("*")):
            if path.is_file():
                out[str(path.relative_to(root))] = (path.read_text(encoding="utf-8"), path.stat().st_mode & 0o777)
        return out

    def test_the_same_seed_builds_the_same_folder_byte_for_byte(self):
        for lab_id in self.labs.LAB_IDS:
            first = self.labs.build_lab(lab_id, 77, self.data / "a")
            second = self.labs.build_lab(lab_id, 77, self.data / "b")
            self.assertEqual(self.tree(first["path"]), self.tree(second["path"]), lab_id)
            self.assertEqual(self.labs.tree_fingerprint(first["path"]), self.labs.tree_fingerprint(second["path"]))
            self.assertEqual(self.labs.tree_fingerprint(first["path"]), self.labs.pristine_fingerprint(lab_id, 77))

    def test_lab_files_are_written_with_unix_line_endings_on_every_platform(self):
        # They stand in for a Linux server's files; Windows text mode would turn every newline into CRLF.
        for lab_id in self.labs.LAB_IDS:
            built = self.labs.build_lab(lab_id, 5, self.data / "eol")
            for rel in built["files"]:
                raw = (pathlib.Path(built["path"]) / rel).read_bytes()
                self.assertNotIn(b"\r\n", raw, f"{lab_id}: {rel}")
                self.assertEqual(raw, self.labs.pristine_files(lab_id, 5)[rel][0].encode("utf-8"), f"{lab_id}: {rel}")

    def test_the_listing_uses_forward_slashes_on_every_platform(self):
        built = self.labs.build_lab("lab.reboot", 5, self.data / "slashes")
        self.assertTrue(all("\\" not in rel for rel in built["files"]), built["files"])
        self.assertIn("cron/jobs.json", built["files"])
        self.assertEqual(set(built["files"]), set(self.labs.pristine_files("lab.reboot", 5)))

    def test_a_fresh_lab_has_no_changed_files_on_any_platform(self):
        for lab_id in self.labs.LAB_IDS:
            built = self.labs.build_lab(lab_id, 9, self.data / "fresh")
            self.assertEqual(self.labs.changed_files(lab_id, 9, built["path"]), [], lab_id)
            self.assertEqual(self.labs.tree_fingerprint(built["path"]), self.labs.pristine_fingerprint(lab_id, 9), lab_id)

    def test_different_seeds_change_the_names_the_keys_and_the_numbers(self):
        for lab_id in self.labs.LAB_IDS:
            specs = [self.labs.spec_for(lab_id, s) for s in SEEDS]
            self.assertGreater(len({json.dumps(s, sort_keys=True) for s in specs}), 25, lab_id)
            fingerprints = {self.labs.pristine_fingerprint(lab_id, s) for s in SEEDS}
            self.assertEqual(len(fingerprints), len(SEEDS), "two seeds built the identical folder")

    def test_every_variant_of_each_hidden_fault_turns_up_across_seeds(self):
        reboot = [self.labs.spec_for("lab.reboot", s) for s in SEEDS]
        self.assertEqual({s["unit_fault"] for s in reboot}, {"no_install", "no_restart", "no_network"})
        self.assertEqual({s["backup_fault"] for s in reboot}, {"wrong_path", "not_executable", "impossible_date"})
        cost = [self.labs.spec_for("lab.cost", s) for s in SEEDS]
        self.assertEqual({s["budget_variant"] for s in cost}, {"absent", "disabled"})
        leak = [self.labs.spec_for("lab.leak", s) for s in SEEDS]
        self.assertEqual({len(s["leaked"]) for s in leak}, {1, 2})
        self.assertGreater(len({s["leak_file"] for s in leak}), 1)

    def test_every_secret_in_every_lab_is_marked_fake(self):
        shaped_like_real = re.compile(r"(?:sk|pk)[-_][A-Za-z0-9]{12,}|(?<![-\w])[0-9a-fA-F]{20,}(?![-\w])|[A-Za-z0-9+/]{40,}")
        for lab_id in self.labs.LAB_IDS:
            for seed in SEEDS[:12]:
                for rel, (text, _) in self.labs.pristine_files(lab_id, seed).items():
                    self.assertIsNone(shaped_like_real.search(text), f"{lab_id} seed {seed} {rel} holds something shaped like a real key")
                    for secret in re.findall(r"FAKE-[A-Za-z0-9-]+", text):
                        self.assertTrue(secret.startswith("FAKE-"))
        text = self.labs.pristine_files("lab.leak", 5)[".env"][0]
        self.assertIn("FAKE KEYS FOR A TRAINING LAB", text)

    def test_the_folder_says_it_is_a_lab_and_carries_the_marker(self):
        view = self.deployer.open_lab("lab.cost")
        root = pathlib.Path(view["path"])
        self.assertTrue((root / self.labs.MARKER).is_file())
        self.assertIn("is not a Hermes home", (root / self.labs.MARKER).read_text(encoding="utf-8"))
        self.assertTrue(root.resolve().is_relative_to((self.data / "labs").resolve()))

    def test_the_folder_imitates_a_hermes_home(self):
        view = self.deployer.open_lab("lab.reboot")
        files = set(view["files"])
        for needed in ("config.yaml", ".env", "cron/jobs.json", "logs/gateway.log", "systemd/hermes-gateway.service", "scripts/backup.sh", "crontab.txt", "README-CLIENT.txt"):
            self.assertIn(needed, files)
        self.assertTrue(any(f.startswith("profiles/") for f in files))

    def test_opening_twice_never_overwrites_the_learners_work(self):
        view = self.deployer.open_lab("lab.cost")
        marker = pathlib.Path(view["path"]) / "config.yaml"
        marker.write_text("# my edit\n")
        again = self.deployer.open_lab("lab.cost")
        self.assertEqual(again["seed"], view["seed"])
        self.assertEqual(marker.read_text(encoding="utf-8"), "# my edit\n")

    def test_a_new_variant_deletes_an_unfinished_folder_but_keeps_a_passed_one(self):
        first = self.deployer.open_lab("lab.cost")
        second = self.deployer.new_variant("lab.cost")
        self.assertNotEqual(first["seed"], second["seed"])
        self.assertFalse(pathlib.Path(first["path"]).exists())
        solved = self.pass_lab("lab.leak")
        third = self.deployer.new_variant("lab.leak")
        self.assertTrue(pathlib.Path(solved["path"]).exists(), "a passed folder is evidence and must stay")
        self.assertNotEqual(third["seed"], solved["seed"])
        with self._conn() as conn:
            self.assertEqual(self.deployer.lab_view(conn, "lab.leak")["status"], "in_progress")
            self.assertIsNotNone(self.deployer._passed_lab_row(conn, "lab.leak"))

    def _conn(self):
        return self.store.connect()

    def test_reset_refuses_a_folder_without_the_marker(self):
        root = self.labs.lab_root(self.data, "lab.leak", 5)
        root.mkdir(parents=True)
        (root / "precious.txt").write_text("keep")
        with self.assertRaises(self.labs.LabError):
            self.labs.reset_lab("lab.leak", 5, self.data)
        with self.assertRaises(self.labs.LabError):
            self.labs.build_lab("lab.leak", 5, self.data)
        self.assertEqual((root / "precious.txt").read_text(encoding="utf-8"), "keep")

    def test_a_data_folder_that_looks_like_a_hermes_home_is_refused(self):
        home = self.fence / "looks-like-home"
        home.mkdir()
        (home / "config.yaml").write_text("x: 1\n")
        with self.assertRaises(self.labs.LabError):
            self.labs.build_lab("lab.leak", 1, home)
        for name in (".env", "cron", "profiles", "skills"):
            other = self.fence / f"home-{name}"
            other.mkdir()
            (other / name).mkdir() if name in ("cron", "profiles", "skills") else (other / name).write_text("x")
            with self.assertRaises(self.labs.LabError, msg=name):
                self.labs.safe_labs_dir(other)

    def test_the_real_hermes_home_itself_is_refused(self):
        os.environ["HERMES_HOME"] = str(self.fence / "named-home")
        (self.fence / "named-home").mkdir()
        with self.assertRaises(self.labs.LabError):
            self.labs.safe_labs_dir(self.fence / "named-home")

    def test_the_lab_never_sets_an_environment_variable_or_runs_anything(self):
        before = dict(os.environ)
        for lab_id in self.labs.LAB_IDS:
            self.labs.build_lab(lab_id, 3, self.data)
        self.assertEqual(dict(os.environ), before)

    def test_permissions_are_real_in_the_reboot_lab(self):
        # Real modes on Linux and macOS; on Windows, real access lists and a schedule line that names its program.
        fileaccess = importlib.import_module(f"{self.name}.fileaccess")
        for seed in SEEDS[:10]:
            spec = self.labs.spec_for("lab.reboot", seed)
            built = self.labs.build_lab("lab.reboot", seed, self.data)
            root = pathlib.Path(built["path"])
            for rel in spec["secret_files"]:
                self.assertFalse(fileaccess.is_private(root / rel), f"{rel} should start readable by others")
                if not fileaccess.ON_WINDOWS:
                    self.assertTrue((root / rel).stat().st_mode & 0o044, f"{rel} should start world-readable")
            if f"profiles/{spec['profile']}/memory.db" not in spec["secret_files"]:
                self.assertTrue(fileaccess.is_private(root / f"profiles/{spec['profile']}/memory.db"))
            broken = spec["backup_fault"] == "not_executable"
            if fileaccess.ON_WINDOWS:
                line = [x for x in (root / "crontab.txt").read_text(encoding="utf-8").splitlines() if x and not x.startswith("#")][0]
                self.assertEqual(line.split()[5] != "/bin/sh", broken, line)
            else:
                self.assertEqual(not (root / "scripts/backup.sh").stat().st_mode & 0o111, broken)

    def test_the_manifest_never_leaks_a_hidden_fact(self):
        view = self.deployer.open_lab("lab.leak")
        spec = self.labs.spec_for("lab.leak", view["seed"])
        blob = json.dumps(view)
        for item in spec["leaked"]:
            self.assertNotIn(item["value"], blob)
        self.assertNotIn("replacement_secrets", blob)
        for key in ("faults", "leaked", "unit_fault", "backup_fault", "budget_variant"):
            self.assertNotIn(f'"{key}"', blob)


class CronAndYaml(DeployerCase):
    def test_cron_runs_per_day(self):
        for expr, runs in (("* * * * *", 1440), ("*/1 * * * *", 1440), ("0-59 * * * *", 1440), ("30 7 * * 1-5", 1), ("*/15 9-17 * * *", 36), ("0 8,12,17 * * *", 3), ("@daily", 1)):
            self.assertEqual(self.labs.runs_per_firing_day(expr), runs, expr)

    def test_cron_monthly_and_impossible_dates(self):
        self.assertAlmostEqual(self.labs.runs_per_month("30 7 * * 1-5"), 30 * 5 / 7, places=3)
        self.assertFalse(self.labs.can_fire("30 2 31 2 *"))
        self.assertTrue(self.labs.can_fire("30 2 30 * *"))
        self.assertEqual(self.labs.runs_per_month("30 2 31 2 *"), 0)
        for bad in ("* * * *", "60 * * * *", "a b c d e", "*/0 * * * *"):
            with self.assertRaises(ValueError, msg=bad):
                self.labs.parse_cron(bad)

    def test_the_yaml_reader_reads_the_labs_own_files_and_says_what_it_cannot(self):
        for lab_id in self.labs.LAB_IDS:
            for seed in SEEDS[:6]:
                for rel, (text, _) in self.labs.pristine_files(lab_id, seed).items():
                    if rel.endswith("config.yaml"):
                        data = self.labs.parse_yaml(text)
                        self.assertIsInstance(data, dict, rel)
        data = self.labs.parse_yaml("a:\n  b: 1\n  c: [x, y]\nd: \"q\"  # note\ne:\n  - 1\n  - two\n")
        self.assertEqual(data, {"a": {"b": 1, "c": ["x", "y"]}, "d": "q", "e": [1, "two"]})
        with self.assertRaises(self.labs.YamlError):
            self.labs.parse_yaml("a: 1\n  b: 2\n")
        with self.assertRaises(self.labs.YamlError):
            self.labs.parse_yaml("no colon here\n")


if __name__ == "__main__":
    unittest.main()
