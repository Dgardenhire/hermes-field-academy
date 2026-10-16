"""The scripted graders: they reject the broken folder, accept a correct repair on every variant, and reject the repairs that look right and are not."""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import unittest

from deployer_support import DeployerCase
import file_access as fa
from lab_solutions import SOLVERS, solve_cost, solve_leak, solve_reboot, solve_vault

SEEDS = list(range(1, 41))


class Graders(DeployerCase):
    def build(self, lab_id, seed, where="g"):
        built = self.labs.build_lab(lab_id, seed, self.data / where)
        return pathlib.Path(built["path"]), self.labs.spec_for(lab_id, seed)

    def g(self, lab_id, seed, root, diagnosis=""):
        return self.grade.grade_lab(lab_id, seed, root, diagnosis)

    def ids(self, outcome):
        return {m["id"] for m in outcome["missing"]}

    def setUp(self):
        super().setUp()
        self.grade_mod = self.grade

    # -- the broken state and the right fix --------------------------------

    def test_the_original_broken_folder_is_rejected_even_with_a_perfect_diagnosis(self):
        for lab_id in self.labs.LAB_IDS:
            for seed in SEEDS[:12]:
                root, spec = self.build(lab_id, seed, f"orig-{lab_id}-{seed}")
                scratch = pathlib.Path(self.data / f"scratch-{lab_id}-{seed}")
                shutil.copytree(root, scratch, copy_function=shutil.copy2)
                diagnosis = SOLVERS[lab_id](spec, scratch)
                outcome = self.g(lab_id, seed, root, diagnosis)
                self.assertFalse(outcome["passed"], f"{lab_id} seed {seed}")
                self.assertTrue(outcome["missing"])

    def test_a_correct_repair_passes_on_every_variant_of_every_lab(self):
        for lab_id in self.labs.LAB_IDS:
            for seed in SEEDS:
                root, spec = self.build(lab_id, seed, f"fix-{lab_id}-{seed}")
                diagnosis = SOLVERS[lab_id](spec, root)
                outcome = self.g(lab_id, seed, root, diagnosis)
                self.assertTrue(outcome["passed"], f"{lab_id} seed {seed}: {outcome['missing']}")
                self.assertEqual(outcome["missing"], [])

    def test_the_grader_is_deterministic(self):
        root, spec = self.build("lab.leak", 5)
        diagnosis = solve_leak(spec, root)
        first = self.g("lab.leak", 5, root, diagnosis)
        second = self.g("lab.leak", 5, root, diagnosis)
        self.assertEqual(first, second)

    def test_a_repair_made_for_a_different_seed_is_rejected(self):
        """Answers cannot be shared: the same fix for another case fails on the other case's details."""
        for lab_id in self.labs.LAB_IDS:
            for a, b in ((3, 4), (11, 12), (20, 21)):
                root_a, spec_a = self.build(lab_id, a, f"A-{lab_id}-{a}")
                diagnosis_a = SOLVERS[lab_id](spec_a, root_a)
                root_b, spec_b = self.build(lab_id, b, f"B-{lab_id}-{b}")
                for path in root_a.rglob("*"):
                    if path.is_file() and path.name != self.labs.MARKER:
                        target = root_b / path.relative_to(root_a)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(path, target)
                outcome = self.g(lab_id, b, root_b, diagnosis_a)
                self.assertFalse(outcome["passed"], f"{lab_id}: a repair for seed {a} passed seed {b}")

    def test_a_missing_folder_is_a_plain_miss_not_a_crash(self):
        outcome = self.g("lab.leak", 1, self.data / "nope", "x" * 200)
        self.assertFalse(outcome["passed"])
        self.assertEqual(self.ids(outcome), {"folder"})
        outcome = self.g("lab.leak", 1, self.data, "x")
        self.assertFalse(outcome["passed"])

    def test_the_result_never_reveals_how_many_checks_there_are(self):
        root, spec = self.build("lab.cost", 8)
        outcome = self.g("lab.cost", 8, root, "short")
        self.assertNotRegex(outcome["detail"], r"\d+ of \d+")
        self.assertNotIn("total", outcome)
        self.assertRegex(outcome["detail"], r"still missing")

    # -- leaked key --------------------------------------------------------

    def leak(self, seed=2, **options):
        root, spec = self.build("lab.leak", seed, f"leak-{seed}-{len(options)}")
        diagnosis = solve_leak(spec, root, **options)
        return root, spec, diagnosis

    def test_leak_deleting_the_key_line_is_not_a_fix(self):
        root, spec = self.build("lab.leak", 2)
        path = root / spec["leak_file"]
        text = path.read_text(encoding="utf-8")
        for item in spec["leaked"]:
            text = re.sub(rf"\n\s+{item['yaml_key']}: .*", "", text)
        path.write_text(text)
        outcome = self.g("lab.leak", 2, root, "x" * 300)
        self.assertIn("not_wired", self.ids(outcome))
        self.assertIn("old_not_revoked", self.ids(outcome))

    def test_leak_moving_the_key_to_env_without_rotating_is_not_a_fix(self):
        root, spec = self.build("lab.leak", 6)
        path = root / spec["leak_file"]
        text = path.read_text(encoding="utf-8")
        env = (root / ".env").read_text(encoding="utf-8")
        for item in spec["leaked"]:
            text = text.replace(f"{item['yaml_key']}: {item['value']}", f"{item['yaml_key']}_env: {item['var']}")
            env += f"{item['var']}={item['value']}\n"
        path.write_text(text)
        (root / ".env").write_text(env)
        outcome = self.g("lab.leak", 6, root, "x" * 300)
        self.assertIn("env_missing_new", self.ids(outcome))
        self.assertIn("old_not_revoked", self.ids(outcome))

    def test_leak_rotating_but_leaving_the_old_key_in_the_file_is_not_a_fix(self):
        root, spec, diagnosis = self.leak(7)
        path = root / spec["leak_file"]
        path.write_text(path.read_text(encoding="utf-8") + f"# old: {spec['leaked'][0]['value']}\n")
        outcome = self.g("lab.leak", 7, root, diagnosis)
        self.assertIn("secret_in_file", self.ids(outcome))

    def test_leak_writing_the_whole_key_into_the_incident_note_is_caught(self):
        root, spec, diagnosis = self.leak(8)
        note = root / "INCIDENT.md"
        note.write_text(note.read_text(encoding="utf-8") + f"The key was {spec['leaked'][0]['value']}.\n")
        self.assertIn("secret_in_file", self.ids(self.g("lab.leak", 8, root, diagnosis)))

    def test_leak_without_the_console_step_leaves_the_old_key_alive(self):
        root, spec, diagnosis = self.leak(9, skip=("console",))
        ids = self.ids(self.g("lab.leak", 9, root, diagnosis))
        self.assertIn("old_not_revoked", ids)

    def test_leak_without_an_incident_note_fails_with_its_own_check(self):
        root, spec, diagnosis = self.leak(10)
        (root / "INCIDENT.md").unlink()
        self.assertEqual(self.ids(self.g("lab.leak", 10, root, diagnosis)), {"incident_missing"})

    def test_leak_each_part_of_the_incident_note_is_checked(self):
        root, spec, diagnosis = self.leak(11)
        (root / "INCIDENT.md").write_text("Something happened and I fixed it.\n")
        ids = self.ids(self.g("lab.leak", 11, root, diagnosis))
        self.assertEqual(ids, {"incident_key", "incident_when", "incident_who", "incident_fix", "incident_prevent"} - {"incident_fix"} | ({"incident_fix"} if "incident_fix" in ids else set()))
        self.assertTrue({"incident_key", "incident_when", "incident_who", "incident_prevent"} <= ids)

    def test_leak_env_left_open_to_the_repository_is_caught(self):
        root, spec, diagnosis = self.leak(12)
        (root / ".gitignore").write_text("*.log\n")
        self.assertIn("env_unprotected", self.ids(self.g("lab.leak", 12, root, diagnosis)))

    def test_leak_deleting_other_env_settings_is_a_regression(self):
        root, spec, diagnosis = self.leak(13)
        lines = [l for l in (root / ".env").read_text(encoding="utf-8").splitlines() if "CALENDAR" not in l]
        (root / ".env").write_text("\n".join(lines) + "\n")
        self.assertIn("env_damaged", self.ids(self.g("lab.leak", 13, root, diagnosis)))

    def test_leak_a_broken_config_is_reported_in_plain_words(self):
        root, spec, diagnosis = self.leak(14)
        (root / spec["leak_file"]).write_text("provider\n  broken\n")
        outcome = self.g("lab.leak", 14, root, diagnosis)
        self.assertEqual(self.ids(outcome), {"config_parses"})
        self.assertIn("no longer reads", outcome["missing"][0]["what"])

    def test_leak_the_diagnosis_must_name_the_file_the_evidence_and_the_fix(self):
        root, spec, diagnosis = self.leak(15)
        outcome = self.g("lab.leak", 15, root, "Something went wrong with the setup and now it is all sorted out and fine and working again, I think so." * 2)
        self.assertEqual(self.ids(outcome), {"diag_cause", "diag_where", "diag_evidence", "diag_fix", "diag_prevent"})
        self.assertEqual(self.ids(self.g("lab.leak", 15, root, "short")), {"diag_short"})

    # -- runaway bill ------------------------------------------------------

    def cost(self, seed=3, **options):
        root, spec = self.build("lab.cost", seed, f"cost-{seed}-{len(options)}")
        diagnosis = solve_cost(spec, root, **options)
        return root, spec, diagnosis

    def edit_jobs(self, root, fn):
        data = json.loads((root / "cron/jobs.json").read_text(encoding="utf-8"))
        fn(data["jobs"])
        (root / "cron/jobs.json").write_text(json.dumps(data, indent=2))

    def test_cost_switching_the_job_off_is_not_a_fix(self):
        root, spec, diagnosis = self.cost(4)
        def off(jobs):
            for j in jobs:
                if j["name"] == spec["runaway_job"]:
                    j["enabled"] = False
        self.edit_jobs(root, off)
        self.assertIn("job_removed", self.ids(self.g("lab.cost", 4, root, diagnosis)))

    def test_cost_deleting_the_job_is_not_a_fix(self):
        root, spec, diagnosis = self.cost(5)
        self.edit_jobs(root, lambda jobs: jobs.remove(next(j for j in jobs if j["name"] == spec["runaway_job"])))
        self.assertIn("job_removed", self.ids(self.g("lab.cost", 5, root, diagnosis)))

    def test_cost_a_schedule_every_five_minutes_is_still_a_runaway(self):
        root, spec, diagnosis = self.cost(6)
        def slow(jobs):
            for j in jobs:
                if j["name"] == spec["runaway_job"]:
                    j["schedule"] = "*/5 * * * *"
        self.edit_jobs(root, slow)
        self.assertIn("still_runaway", self.ids(self.g("lab.cost", 6, root, diagnosis)))

    def test_cost_a_schedule_that_never_fires_is_not_a_fix(self):
        root, spec, diagnosis = self.cost(7)
        def never(jobs):
            for j in jobs:
                if j["name"] == spec["runaway_job"]:
                    j["schedule"] = "30 7 31 2 *"
        self.edit_jobs(root, never)
        self.assertIn("never_runs", self.ids(self.g("lab.cost", 7, root, diagnosis)))

    def test_cost_a_schedule_that_does_not_read_is_reported(self):
        root, spec, diagnosis = self.cost(8)
        def bad(jobs):
            for j in jobs:
                if j["name"] == spec["runaway_job"]:
                    j["schedule"] = "every morning"
        self.edit_jobs(root, bad)
        self.assertIn("schedule_unreadable", self.ids(self.g("lab.cost", 8, root, diagnosis)))

    def test_cost_fixing_the_schedule_without_a_cap_still_fails(self):
        root, spec, diagnosis = self.cost(9, skip=("cap",))
        self.assertEqual(self.ids(self.g("lab.cost", 9, root, diagnosis)), {"cap_missing"})

    def test_cost_a_cap_that_only_warns_fails_and_a_cap_of_zero_counts_as_none(self):
        for seed in SEEDS:
            spec = self.labs.spec_for("lab.cost", seed)
            if spec["budget_variant"] == "disabled":
                root, spec, diagnosis = self.cost(seed, skip=("cap",))
                self.assertEqual(self.ids(self.g("lab.cost", seed, root, diagnosis)), {"cap_missing"}, "a disabled cap of 0 must not count")
                cfg = (root / "config.yaml").read_text(encoding="utf-8")
                (root / "config.yaml").write_text(cfg + f"budget:\n  daily_usd_cap: {round(spec['budget_monthly'] / 30, 2)}\n  on_exceed: alert\n")
                self.assertEqual(self.ids(self.g("lab.cost", seed, root, diagnosis)), {"cap_soft"})
                return
        self.fail("no seed produced the disabled-cap variant")

    def test_cost_a_cap_far_above_the_budget_fails(self):
        root, spec, diagnosis = self.cost(10, skip=("cap",))
        (root / "config.yaml").write_text((root / "config.yaml").read_text(encoding="utf-8") + f"budget:\n  daily_usd_cap: {spec['budget_monthly']}\n  on_exceed: stop\n")
        self.assertEqual(self.ids(self.g("lab.cost", 10, root, diagnosis)), {"cap_too_high"})

    def test_cost_changing_the_summary_job_itself_is_rejected(self):
        root, spec, diagnosis = self.cost(11)
        def change(jobs):
            for j in jobs:
                if j["name"] == spec["runaway_job"]:
                    j["deliver_to"] = "someone@else.example"
        self.edit_jobs(root, change)
        self.assertIn("summary_changed", self.ids(self.g("lab.cost", 11, root, diagnosis)))

    def test_cost_touching_a_healthy_job_is_rejected(self):
        root, spec, diagnosis = self.cost(12)
        self.edit_jobs(root, lambda jobs: [j.update({"schedule": "0 * * * *"}) for j in jobs if j["name"] == "weekly-invoice-digest"])
        self.assertIn("other_job_changed", self.ids(self.g("lab.cost", 12, root, diagnosis)))

    def test_cost_an_unknown_model_is_reported(self):
        root, spec, diagnosis = self.cost(13)
        self.edit_jobs(root, lambda jobs: [j.update({"model": "made-up-model"}) for j in jobs if j["name"] == spec["runaway_job"]])
        self.assertIn("model_unknown", self.ids(self.g("lab.cost", 13, root, diagnosis)))

    def test_cost_keeping_the_premium_model_is_fine_when_the_budget_holds(self):
        root, spec, diagnosis = self.cost(14, keep_premium=True)
        self.assertTrue(self.g("lab.cost", 14, root, diagnosis)["passed"])

    def test_cost_lying_about_tokens_in_the_file_does_not_help(self):
        """The grader uses the lab's true token counts, so editing the file's own number changes nothing."""
        root, spec = self.build("lab.cost", 15)
        self.edit_jobs(root, lambda jobs: [j.update({"tokens_per_run": 1}) for j in jobs])
        self.assertIn("still_runaway", self.ids(self.g("lab.cost", 15, root, "x" * 300)))

    def test_cost_the_diagnosis_needs_the_job_the_cause_and_the_number(self):
        root, spec, diagnosis = self.cost(16)
        text = "It was costing too much money because of how things had been set up for the office, and I made it cheaper and put a limit in place." * 2
        ids = self.ids(self.g("lab.cost", 16, root, text))
        self.assertEqual(ids, {"diag_job", "diag_cause", "diag_number"})
        wrong_number = diagnosis.replace(f"${spec['daily_cost']:.2f}", "$3.00")
        self.assertIn("diag_number", self.ids(self.g("lab.cost", 16, root, wrong_number)))

    # -- service, permissions, backup -------------------------------------

    def reboot(self, seed=3, **options):
        root, spec = self.build("lab.reboot", seed, f"reboot-{seed}-{len(options)}")
        diagnosis = solve_reboot(spec, root, **options)
        return root, spec, diagnosis

    def test_reboot_fixing_only_the_permissions_leaves_the_rest_broken(self):
        root, spec = self.build("lab.reboot", 2)
        for rel in spec["secret_files"]:
            fa.lock(root / rel)
        ids = self.ids(self.g("lab.reboot", 2, root, "x" * 300))
        self.assertNotIn("perm_open", ids)
        self.assertIn("unit_not_enabled", ids)
        self.assertIn("restore_missing", ids)

    def test_reboot_group_or_world_access_of_any_kind_fails(self):
        for opener in fa.OPENERS:
            root, spec, diagnosis = self.reboot(3, skip=("perms",))
            for rel in spec["secret_files"]:
                fa.lock(root / rel)
            fa.open_up(root / spec["secret_files"][-1], opener)
            self.assertIn("perm_open", self.ids(self.g("lab.reboot", 3, root, diagnosis)), str(opener))
            shutil.rmtree(root.parent)

    def test_reboot_deleting_the_secret_file_is_not_locking_it_down(self):
        root, spec, diagnosis = self.reboot(4)
        os.remove(root / spec["secret_files"][0])
        self.assertIn("secret_deleted", self.ids(self.g("lab.reboot", 4, root, diagnosis)))

    def test_reboot_a_service_file_without_the_enable_step_still_fails(self):
        root, spec, diagnosis = self.reboot(5)
        (root / "systemd/enabled-units.txt").write_text("cups.service\ncron.service\n")
        self.assertEqual(self.ids(self.g("lab.reboot", 5, root, diagnosis)), {"unit_not_enabled"})

    def test_reboot_each_unit_fault_is_caught_on_its_own(self):
        seen = set()
        for seed in SEEDS:
            spec = self.labs.spec_for("lab.reboot", seed)
            if spec["unit_fault"] in seen:
                continue
            seen.add(spec["unit_fault"])
            root, spec = self.build("lab.reboot", seed, f"unit-{seed}")
            outcome = self.g("lab.reboot", seed, root, "x" * 300)
            wanted = {"no_install": "unit_install", "no_restart": "unit_restart", "no_network": "unit_network"}[spec["unit_fault"]]
            self.assertIn(wanted, self.ids(outcome))
        self.assertEqual(len(seen), 3)

    def test_reboot_each_backup_fault_is_caught_and_a_half_fix_is_not_enough(self):
        halves = {"wrong_path": "cron_path", "not_executable": "script_not_executable", "impossible_date": "cron_never"}
        seen = set()
        for seed in SEEDS:
            spec = self.labs.spec_for("lab.reboot", seed)
            fault = spec["backup_fault"]
            if fault in seen:
                continue
            seen.add(fault)
            root, spec, diagnosis = self.reboot(seed)
            self.assertTrue(self.g("lab.reboot", seed, root, diagnosis)["passed"], fault)
            # undo just the backup fix
            minute, hour = spec["backup_time"].split(":")[1], spec["backup_time"].split(":")[0]
            if fault == "wrong_path":
                line = f"{minute} {hour} * * * /opt/hermes/backup.sh\n"
            elif fault == "impossible_date":
                line = f"{minute} {hour} 31 2 * /srv/hermes-client/scripts/backup.sh\n"
            else:
                line = None
            if line:
                (root / "crontab.txt").write_text(line)
            elif fa.ON_WINDOWS:
                # Windows: the line goes back to naming the script alone, with no program to run it.
                (root / "crontab.txt").write_text(f"{minute} {hour} * * * /srv/hermes-client/scripts/backup.sh\n")
            else:
                os.chmod(root / "scripts/backup.sh", 0o644)
            self.assertIn(halves[fault], self.ids(self.g("lab.reboot", seed, root, diagnosis)), fault)

    def test_reboot_a_backup_that_runs_less_than_weekly_fails(self):
        root, spec, diagnosis = self.reboot(6)
        (root / "crontab.txt").write_text("30 2 1 1 * /srv/hermes-client/scripts/backup.sh\n")
        self.assertIn("cron_rare", self.ids(self.g("lab.reboot", 6, root, diagnosis)))

    def test_reboot_the_restore_test_needs_a_day_a_count_and_a_file(self):
        root, spec, diagnosis = self.reboot(7)
        (root / "RESTORE-TEST.md").write_text("I tried restoring and it was fine.\n")
        self.assertEqual(self.ids(self.g("lab.reboot", 7, root, diagnosis)), {"restore_date", "restore_count", "restore_which"})

    # -- one key for everything -------------------------------------------

    def vault(self, seed=3, **options):
        root, spec = self.build("lab.vault", seed, f"vault-{seed}-{len(options)}")
        diagnosis = solve_vault(spec, root, **options)
        return root, spec, diagnosis

    def edit_console(self, root, fn):
        data = json.loads((root / "provider-console/keys.json").read_text(encoding="utf-8"))
        fn(data["keys"])
        (root / "provider-console/keys.json").write_text(json.dumps(data, indent=2))

    def test_vault_a_scope_wider_than_the_job_needs_fails(self):
        root, spec, diagnosis = self.vault(2)
        self.edit_console(root, lambda keys: [k.update({"scopes": k["scopes"] + ["admin"]}) for k in keys if k.get("label") == spec["agents"][1]["profile"]])
        self.assertIn("scopes_wide", self.ids(self.g("lab.vault", 2, root, diagnosis)))

    def test_vault_a_scope_narrower_than_the_job_needs_fails(self):
        root, spec, diagnosis = self.vault(3)
        self.edit_console(root, lambda keys: [k.update({"scopes": ["mail:read"]}) for k in keys if k.get("label") == spec["agents"][0]["profile"]])
        self.assertIn("scopes_short", self.ids(self.g("lab.vault", 3, root, diagnosis)))

    def test_vault_a_key_with_no_scopes_fails(self):
        root, spec, diagnosis = self.vault(4)
        self.edit_console(root, lambda keys: [k.update({"scopes": []}) for k in keys if k.get("label") == spec["agents"][0]["profile"]])
        self.assertIn("scopes_empty", self.ids(self.g("lab.vault", 4, root, diagnosis)))

    def test_vault_both_profiles_on_one_variable_is_still_shared(self):
        root, spec, diagnosis = self.vault(5)
        for agent in spec["agents"]:
            path = root / f"profiles/{agent['profile']}/config.yaml"
            path.write_text(path.read_text(encoding="utf-8").replace(spec["new_vars"][1], spec["new_vars"][0]))
        self.assertIn("still_shared", self.ids(self.g("lab.vault", 5, root, diagnosis)))

    def test_vault_the_old_shared_key_must_be_revoked(self):
        root, spec, diagnosis = self.vault(6)
        self.edit_console(root, lambda keys: [k.update({"status": "active"}) for k in keys if k["id"] == spec["shared_id"]])
        self.assertIn("shared_active", self.ids(self.g("lab.vault", 6, root, diagnosis)))

    def test_vault_a_key_left_written_in_a_config_file_fails(self):
        root, spec, diagnosis = self.vault(7)
        path = root / f"profiles/{spec['agents'][1]['profile']}/config.yaml"
        path.write_text(path.read_text(encoding="utf-8") + f"  api_key: {spec['shared_secret']}\n")
        self.assertIn("secret_in_file", self.ids(self.g("lab.vault", 7, root, diagnosis)))

    def test_vault_per_profile_env_files_must_exist_and_be_private(self):
        root, spec, diagnosis = self.vault(8)
        fa.open_up(root / f"profiles/{spec['agents'][0]['profile']}/.env")
        self.assertIn("env_open", self.ids(self.g("lab.vault", 8, root, diagnosis)))
        fa.undo_open(root / f"profiles/{spec['agents'][0]['profile']}/.env")
        self.assertNotIn("env_open", self.ids(self.g("lab.vault", 8, root, diagnosis)))
        os.remove(root / f"profiles/{spec['agents'][1]['profile']}/.env")
        self.assertIn("env_missing", self.ids(self.g("lab.vault", 8, root, diagnosis)))

    def test_vault_the_rotation_note_needs_every_key_an_owner_an_interval_and_a_leak_step(self):
        root, spec, diagnosis = self.vault(9)
        (root / "ROTATION.md").write_text("We will change the keys sometime.\n")
        self.assertEqual(self.ids(self.g("lab.vault", 9, root, diagnosis)), {"rotation_keys", "rotation_owner", "rotation_interval", "rotation_leak"})
        (root / "ROTATION.md").unlink()
        self.assertEqual(self.ids(self.g("lab.vault", 9, root, diagnosis)), {"rotation_missing"})
        names = " ".join(spec["new_vars"])
        (root / "ROTATION.md").write_text(f"{names} owner Alice Moreno, changes every 365 days. If one leaks, switch it off first.\n")
        self.assertIn("rotation_interval", self.ids(self.g("lab.vault", 9, root, diagnosis)))

    # -- the hint ladder ---------------------------------------------------

    def test_every_check_a_grader_can_report_has_a_hint_and_an_example(self):
        for lab_id in self.labs.LAB_IDS:
            for check in self.grade.check_ids(lab_id):
                self.assertIn(check, self.grade.COACH, f"{lab_id}: {check} has no coaching")
                self.assertTrue(self.grade.COACH[check]["hint"].strip())
                self.assertTrue(self.grade.COACH[check]["example"].strip())

    def test_every_id_a_grader_actually_reports_is_declared(self):
        declared = {lab: set(self.grade.LAB_CHECK_IDS[lab]) for lab in self.labs.LAB_IDS}
        seen = {lab: set() for lab in self.labs.LAB_IDS}
        for lab_id in self.labs.LAB_IDS:
            for seed in SEEDS[:15]:
                root, spec = self.build(lab_id, seed, f"decl-{lab_id}-{seed}")
                seen[lab_id] |= self.ids(self.g(lab_id, seed, root, "x" * 200))
                seen[lab_id] |= self.ids(self.g(lab_id, seed, root, ""))
        for lab_id in self.labs.LAB_IDS:
            self.assertFalse(seen[lab_id] - declared[lab_id], f"{lab_id} reports undeclared ids")

    def test_the_ladder_goes_hint_then_example_then_a_whole_worked_case(self):
        view = self.deployer.open_lab("lab.cost")
        spec = self.labs.spec_for("lab.cost", view["seed"])
        pathlib.Path(view["path"], "README-CLIENT.txt").write_text("changed\n")  # a change, so it is graded rather than 'unchanged'
        first = self.deployer.check_lab("lab.cost", "")["outcome"]
        self.assertEqual(first["feedback"]["level"], 1)
        self.assertTrue(first["feedback"]["hint"])
        self.assertEqual(first["feedback"]["example"], "")
        self.assertIsNone(self.deployer.open_lab("lab.cost")["worked"])
        second = self.deployer.check_lab("lab.cost", "")["outcome"]
        self.assertEqual(second["feedback"]["level"], 2)
        self.assertTrue(second["feedback"]["example"])
        after = self.deployer.open_lab("lab.cost")
        self.assertIn("A finished example", after["worked"]["title"])
        self.assertNotIn(spec["runaway_job"], after["worked"]["body"], "the worked case is about a different business")

    def test_the_unchanged_folder_is_told_to_look_at_the_evidence(self):
        self.deployer.open_lab("lab.leak")
        outcome = self.deployer.check_lab("lab.leak", "x" * 200)["outcome"]
        self.assertEqual({m["id"] for m in outcome["missing"]}, {"unchanged"})
        self.assertFalse(outcome["passed"])

    def test_a_passed_lab_stays_passed_and_records_what_changed(self):
        view = self.pass_lab("lab.leak")
        again = self.deployer.check_lab("lab.leak", "short")
        self.assertTrue(again.get("already_passed"))
        self.assertEqual(again["lab"]["status"], "verified")
        changed = {c["path"] for c in again["lab"]["changed"]}
        self.assertIn("INCIDENT.md", changed)
        self.assertIn(".env", changed)

    def test_the_diagnosis_is_stored_with_any_key_in_it_removed(self):
        view = self.deployer.open_lab("lab.leak")
        spec = self.labs.spec_for("lab.leak", view["seed"])
        pathlib.Path(view["path"], "README-CLIENT.txt").write_text("changed\n")
        self.deployer.check_lab("lab.leak", f"The key {spec['leaked'][0]['value']} was in config.yaml. " * 4)
        with self.store.connect() as conn:
            stored = conn.execute("SELECT diagnosis FROM deployer_labs").fetchone()[0]
        self.assertNotIn(spec["leaked"][0]["value"], stored)
        self.assertIn("[key removed]", stored)


if __name__ == "__main__":
    unittest.main()
