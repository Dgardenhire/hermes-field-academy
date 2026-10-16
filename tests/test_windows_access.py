"""Windows: a file's lock is its access list, and a script runs when its schedule line names the program that reads it.

The Windows tests run on a Windows machine (the windows runner in .github/workflows/platforms.yml) and use icacls and
PowerShell the way a learner does. The checks in the last class run everywhere: they read the Windows text and the
schedule-line rule, which are the same on every platform.
"""

from __future__ import annotations

import importlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import file_access as fa
from deployer_support import DeployerCase
from lab_solutions import solve_reboot, solve_vault

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "nt", "Windows access lists exist only on Windows")
class WindowsAccessLists(DeployerCase):
    def setUp(self):
        super().setUp()
        self.fileaccess = importlib.import_module(f"{self.name}.fileaccess")
        self.scratch = pathlib.Path(tempfile.mkdtemp(prefix="fa-acl-"))

    def tearDown(self):
        shutil.rmtree(self.scratch, ignore_errors=True)
        super().tearDown()

    def file(self, name="secret.txt", text="FAKE-KEY-DO-NOT-USE-1\n"):
        path = self.scratch / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_a_file_in_your_own_folders_is_private_already_as_hermes_keeps_its_env(self):
        # Hermes keeps .env under %LOCALAPPDATA%. Its access list: you, SYSTEM and the administrators.
        self.assertTrue(str(self.scratch.resolve()).lower().startswith(str(pathlib.Path(os.environ["USERPROFILE"]).resolve()).lower()), self.scratch)
        path = self.file()
        self.assertTrue(self.fileaccess.is_private(path), self.fileaccess.others(path))

    def test_every_way_of_letting_others_in_is_caught_and_named(self):
        names = {"*S-1-5-32-545": "Users", "*S-1-1-0": "Everyone", "*S-1-5-11": "Authenticated Users", "*S-1-5-32-546": "Guests"}
        for opener in fa.WINDOWS_OPENERS:
            path = self.file(f"open-{len(list(self.scratch.iterdir()))}.txt")
            fa.open_up(path, opener)
            self.assertFalse(self.fileaccess.is_private(path), opener)
            self.assertIn(names[opener[0]], self.fileaccess.others(path), opener)

    def test_rights_that_do_not_reach_the_contents_and_deny_entries_do_not_count(self):
        path = self.file()
        fa.icacls(path, "/grant", "*S-1-5-32-545:(RA)")   # read attributes only
        fa.icacls(path, "/deny", "*S-1-1-0:(R)")          # an entry that takes access away
        self.assertTrue(self.fileaccess.is_private(path), self.fileaccess.others(path))

    def set_owner(self, path, sid):
        out = subprocess.run(["icacls", str(path), "/setowner", sid], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, f"icacls /setowner {sid}: {out.stdout} {out.stderr}")

    def test_a_file_owned_by_someone_else_is_not_private_even_with_a_tight_list(self):
        # The owner can always rewrite the access list, so a file another account owns is not yours alone.
        path = self.file()
        fa.lock(path)
        self.assertTrue(self.fileaccess.is_private(path))
        self.set_owner(path, "*S-1-5-32-545")
        self.assertIn("Users", self.fileaccess.others(path))
        self.set_owner(path, "*S-1-5-32-544")  # the administrators may own it: Windows gives them every file anyway
        self.assertTrue(self.fileaccess.is_private(path), self.fileaccess.others(path))

    def test_an_empty_list_is_private_only_when_the_owner_is_you(self):
        path = self.file()
        fa.icacls(path, "/inheritance:r")  # no entries left at all
        self.set_owner(path, f"{os.environ['USERDOMAIN']}\\{os.environ['USERNAME']}")
        self.assertTrue(self.fileaccess.is_private(path), self.fileaccess.others(path))
        self.set_owner(path, "*S-1-5-32-545")
        self.assertFalse(self.fileaccess.is_private(path))

    def test_the_right_to_run_a_file_counts_as_letting_someone_in(self):
        path = self.file()
        fa.lock(path)
        fa.icacls(path, "/grant", "*S-1-5-32-545:(X)")
        self.assertEqual(self.fileaccess.others(path), ["Users"])

    def test_the_private_file_handle_is_not_passed_to_child_programs(self):
        fd = self.fileaccess.create_private(self.scratch / "k.key")
        try:
            self.assertFalse(os.get_inheritable(fd))
        finally:
            os.close(fd)

    def test_the_lab_folder_lets_users_read_and_its_files_inherit_that(self):
        root = pathlib.Path(self.labs.build_lab("lab.cost", 2, self.data)["path"])
        listing = fa.icacls(root)
        self.assertRegex(listing, r"BUILTIN\\Users:\(OI\)\(CI\)\(RX\)")
        self.assertRegex(listing, r"NT AUTHORITY\\SYSTEM:\(OI\)\(CI\)\(F\)")
        self.assertRegex(listing, r"BUILTIN\\Administrators:\(OI\)\(CI\)\(F\)")
        self.assertIn(f"{os.environ['USERDOMAIN']}\\{os.environ['USERNAME']}:(OI)(CI)(F)".lower(), listing.lower())
        self.assertNotIn("(I)", listing, "protected: the folder takes nothing from the folder above")
        self.assertEqual(len([line for line in listing.splitlines() if ":(" in line]), 4, listing)
        self.assertRegex(fa.icacls(root / "config.yaml"), r"BUILTIN\\Users:\(I\)\(RX\)")

    def test_an_owner_rights_entry_counts_only_when_you_own_the_file(self):
        path = self.file()
        fa.lock(path)
        fa.icacls(path, "/grant", "*S-1-3-4:(R)")
        self.assertTrue(self.fileaccess.is_private(path), self.fileaccess.others(path))
        self.set_owner(path, "*S-1-5-32-545")
        self.assertFalse(self.fileaccess.is_private(path))
        self.assertIn("Users", self.fileaccess.others(path))

    def test_a_lab_is_never_made_through_a_junction(self):
        elsewhere = self.scratch / "elsewhere"
        elsewhere.mkdir()
        base = self.labs.safe_labs_dir(self.data)
        base.mkdir(parents=True, exist_ok=True)
        junction = base / "reboot-31"
        out = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(elsewhere)], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        with self.assertRaises(self.labs.LabError):
            self.labs.build_lab("lab.reboot", 31, self.data)
        self.assertEqual(list(elsewhere.iterdir()), [], "nothing was made where the junction points")
        os.rmdir(junction)

    def test_the_learners_powershell_line_locks_a_lab_file(self):
        built = self.labs.build_lab("lab.reboot", 3, self.data)
        root = pathlib.Path(built["path"])
        env = root / ".env"
        self.assertIn("Users", self.fileaccess.others(env))
        command = fa.lock_in_powershell(env)
        self.assertEqual(command, self.fileaccess.WINDOWS_LOCK_COMMAND.format(path=".env"))
        self.assertTrue(self.fileaccess.is_private(env), self.fileaccess.others(env))
        listing = fa.icacls(env)
        self.assertIn(os.environ["USERNAME"].lower(), listing.lower())
        self.assertNotIn("BUILTIN\\Users", listing)

    def test_the_coaching_shows_that_same_line(self):
        self.assertIn('icacls .env /inheritance:r /grant:r "${env:USERDOMAIN}\\${env:USERNAME}:F"', self.grade.COACH["perm_open"]["example"])
        self.assertIn("icacls", self.grade.COACH["env_open"]["example"])
        self.assertIn("/bin/sh", self.grade.COACH["script_not_executable"]["example"])
        self.assertIn("icacls", self.grade.WORKED["lab.reboot"]["body"])

    def test_the_plugins_own_lock_is_private_as_icacls_leaves_it(self):
        ours, theirs = self.file("ours.txt"), self.file("theirs.txt")
        self.fileaccess.make_private(ours)
        fa.lock(theirs)
        me = f"{os.environ['USERDOMAIN']}\\{os.environ['USERNAME']}:(F)".lower()
        for path in (ours, theirs):
            listing = fa.icacls(path)
            self.assertTrue(self.fileaccess.is_private(path), listing)
            self.assertIn(me, listing.lower())
            self.assertNotIn("(I)", listing, "nothing inherited from the folder")
        self.assertEqual(len([line for line in fa.icacls(ours).splitlines() if ":(" in line]), 1, "ours names only you")

    def test_a_new_private_file_is_private_from_the_start_and_never_overwritten(self):
        path = self.scratch / "reviewer.key"
        fd = self.fileaccess.create_private(path)
        with os.fdopen(fd, "w") as handle:
            handle.write("abc\n")
        self.assertEqual(path.read_text(), "abc\n")
        self.assertTrue(self.fileaccess.is_private(path))
        self.assertNotIn("(I)", fa.icacls(path), "nothing inherited from the folder")
        with self.assertRaises(FileExistsError):
            self.fileaccess.create_private(path)

    def test_the_drive_keeps_access_lists(self):
        self.assertTrue(self.fileaccess.keeps_access_lists(self.scratch))

    def test_a_lab_folder_starts_shared_and_its_private_files_start_private(self):
        for lab_id in self.labs.LAB_IDS:
            built = self.labs.build_lab(lab_id, 5, self.data)
            root = pathlib.Path(built["path"])
            for rel, (_, mode) in self.labs.pristine_files(lab_id, 5).items():
                self.assertEqual(self.fileaccess.is_private(root / rel), not mode & 0o077, f"{lab_id} {rel}")

    def test_a_new_file_in_a_lab_folder_is_open_until_locked(self):
        root, spec = pathlib.Path(self.labs.build_lab("lab.vault", 4, self.data)["path"]), self.labs.spec_for("lab.vault", 4)
        new = root / "profiles" / spec["agents"][0]["profile"] / ".env"
        new.write_text("X=FAKE-1\n", encoding="utf-8")
        self.assertFalse(self.fileaccess.is_private(new))
        fa.lock_in_powershell(new)
        self.assertTrue(self.fileaccess.is_private(new))

    def test_locking_shows_as_a_change_and_moves_the_fingerprint(self):
        built = self.labs.build_lab("lab.reboot", 6, self.data)
        root = pathlib.Path(built["path"])
        before = self.labs.tree_fingerprint(root)
        self.assertEqual(before, self.labs.pristine_fingerprint("lab.reboot", 6))
        fa.lock(root / ".env")
        self.assertNotEqual(self.labs.tree_fingerprint(root), before)
        self.assertIn({"path": ".env", "change": "permissions"}, self.labs.changed_files("lab.reboot", 6, root))

    def test_the_grader_names_who_else_can_read_the_keys(self):
        root, spec = pathlib.Path(self.labs.build_lab("lab.reboot", 3, self.data)["path"]), self.labs.spec_for("lab.reboot", 3)
        diagnosis = solve_reboot(spec, root, skip=("perms",))
        missing = self.grade.grade_lab("lab.reboot", 3, root, diagnosis)["missing"]
        self.assertEqual([m["id"] for m in missing], ["perm_open"])
        self.assertIn("Users", missing[0]["what"])
        self.assertIn("access list", missing[0]["what"])

    def test_the_cannot_run_variant_on_windows_is_a_line_with_no_program(self):
        for seed in range(1, 41):
            spec = self.labs.spec_for("lab.reboot", seed)
            if spec["backup_fault"] != "not_executable":
                continue
            root = pathlib.Path(self.labs.build_lab("lab.reboot", seed, self.data)["path"])
            diagnosis = solve_reboot(spec, root)
            self.assertTrue(self.grade.grade_lab("lab.reboot", seed, root, diagnosis)["passed"])
            line = (root / "crontab.txt").read_text(encoding="utf-8").replace("/bin/sh ", "")
            (root / "crontab.txt").write_text(line, encoding="utf-8")
            ids = {m["id"] for m in self.grade.grade_lab("lab.reboot", seed, root, "x" * 300)["missing"]}
            self.assertIn("script_not_executable", ids)
            return
        self.fail("no seed in 1-40 hides the cannot-run fault")

    def test_the_reviewers_key_is_private_on_windows(self):
        key = self.scratch / "reviewer.key"
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "sign_review.py"), "keygen", "--out", str(key)], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(self.fileaccess.is_private(key))
        self.assertNotIn("(I)", fa.icacls(key))


class WindowsTextEverywhere(DeployerCase):
    """The Windows wording and the schedule-line rule, checked on every platform."""

    def test_every_windows_coaching_entry_replaces_a_real_check_and_shows_a_command(self):
        for key, entry in self.grade.WINDOWS_COACH.items():
            self.assertIn(key, self.grade.COACH)
            self.assertTrue(entry["hint"].strip() and entry["example"].strip())
            self.assertNotIn("chmod", entry["hint"] + entry["example"], key)
        self.assertNotIn("chmod", self.grade.WINDOWS_WORKED["lab.reboot"]["body"])
        self.assertNotIn("600", self.grade.WINDOWS_WORKED["lab.reboot"]["body"])

    def test_the_windows_lock_command_is_valid_powershell_quoting(self):
        fileaccess = importlib.import_module(f"{self.name}.fileaccess")
        line = fileaccess.WINDOWS_LOCK_COMMAND.format(path=".env")
        self.assertEqual(line, 'icacls .env /inheritance:r /grant:r "${env:USERDOMAIN}\\${env:USERNAME}:F"')
        # "$env:USERNAME:F" would read as a variable named USERNAME:F and grant nobody. The braces end each name, and
        # DOMAIN\name says which account even where a local account and a domain account share a name.
        self.assertNotIn('$env:USERNAME:F', line)
        quoted = [found for entry in self.grade.WINDOWS_COACH.values() for found in re.findall(r'"[^"]*env:USERNAME[^"]*"', entry["example"])]
        self.assertEqual(len(quoted), 2)
        for found in quoted:
            self.assertEqual(found, '"${env:USERDOMAIN}\\${env:USERNAME}:F"')

    def test_a_schedule_line_that_names_its_program_can_start_the_script_on_any_platform(self):
        runner = self.grade._runner_and_script
        self.assertEqual(runner("/bin/sh /srv/hermes-client/scripts/backup.sh >> x 2>&1"), ("/bin/sh", "/srv/hermes-client/scripts/backup.sh"))
        self.assertEqual(runner("bash /srv/hermes-client/scripts/backup.sh"), ("bash", "/srv/hermes-client/scripts/backup.sh"))
        self.assertEqual(runner("/usr/bin/env bash /srv/x.sh"), ("bash", "/srv/x.sh"))
        self.assertEqual(runner("/srv/hermes-client/scripts/backup.sh >> x"), ("", "/srv/hermes-client/scripts/backup.sh"))
        self.assertEqual(runner("python /srv/x.sh"), ("", "python"))



@unittest.skipIf(os.name == "nt", "Windows has its own junction test above")
class NoLabThroughALink(DeployerCase):
    def test_a_lab_is_never_made_through_a_symbolic_link(self):
        elsewhere = pathlib.Path(tempfile.mkdtemp(prefix="fa-elsewhere-"))
        base = self.labs.safe_labs_dir(self.data)
        base.mkdir(parents=True, exist_ok=True)
        (base / "reboot-31").symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(self.labs.LabError):
            self.labs.build_lab("lab.reboot", 31, self.data)
        self.assertEqual(list(elsewhere.iterdir()), [])
        shutil.rmtree(elsewhere)

if __name__ == "__main__":
    unittest.main()
