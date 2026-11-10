"""Fixture tests for the capability missions' live checks and planted problems: helper agents (f.delegation) and
toolsets (f.toolsets). One class per reader id, the class docstring is the id, as scripts/check_foundations.py
requires."""

from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
import hermes_fixture_b as hb  # noqa: E402
from test_scrub import load  # noqa: E402

T0 = hf.T0
CLIENTS = {"harbor-dental": {"name": "Harbor Dental", "budget": "$3,250", "issue": "x"},
           "quill-books": {"name": "Quill & Co Books", "budget": "$7,500", "issue": "y"},
           "vale-bakery": {"name": "Vale Street Bakery", "budget": "$1,000", "issue": "z"}}
RULE = "Checked by: Priya"
NOTES = {"van-lease": {"title": "Van lease", "point": "p"}, "rent-review": {"title": "Rent review", "point": "q"},
         "website": {"title": "Website", "point": "r"}}


def call(name, **args):
    return json.dumps([{"id": "c1", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}])


class Case(unittest.TestCase):
    def setUp(self):
        self.c = load("foundations_checks")
        self.pc = load("plants_c")
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.home = hf.build_home(self.tmp / "profiles" / "academy-practice")
        self.folder = hb.folder(self.home)
        self.ctx = {"home": self.home, "note": {}, "planted": {},
                    "setup": {"folder": str(self.folder.resolve()), "clients": CLIENTS, "rule_line": RULE, "notes": NOTES},
                    "row": {"plan": {"folder": str(self.folder.resolve())}, "planted_at": hb.iso(T0)}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_reader(self, reader_id, **ctx):
        return self.c.run(reader_id, {**self.ctx, **ctx})

    def chat(self, started, rows, **cols):
        con = hf.state_db(self.home)
        sid = hf.add_session(con, started_at=started, **cols)
        for n, (role, content, tool, calls) in enumerate(rows, start=1):
            extra = {"tool_calls": calls} if calls else {}
            hf.add_message(con, sid, role, content, started + n, tool_name=tool, **extra)
        con.close()
        return sid

    def batch(self, count=3, result="{\"results\": []}"):
        tasks = [{"goal": f"summarise clients/{slug}/notes.txt"} for slug in list(CLIENTS)[:count]]
        return self.chat(T0 + 100, [("user", "one helper per client", None, None),
                                    ("assistant", "", None, call("delegate_task", tasks=tasks)),
                                    ("tool", result, "delegate_task", None)])

    def helper(self, parent, slugs, started=T0 + 200):
        rows = [("assistant", "", None, call("read_file", path=f"{self.folder}/clients/{s}/notes.txt")) for s in slugs]
        return self.chat(started, rows, source="subagent", parent_session_id=parent)

    def write(self, rel, text):
        path = self.folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


# -------------------------------------------------------------- delegation --


class Batch(Case):
    """delegation.batch"""

    def test_one_call_with_every_client_passes(self):
        self.batch()
        out = self.run_reader("delegation.batch")
        self.assertTrue(out["passed"], out["detail"])

    def test_a_refused_batch_fails_and_quotes_the_refusal(self):
        self.batch(result="Too many tasks: 3 provided, but max_concurrent_children is 1. Either reduce")
        out = self.run_reader("delegation.batch")
        self.assertFalse(out["passed"])
        self.assertEqual(out["missing"][0]["id"], "refused")
        self.assertIn("max_concurrent_children is 1", out["detail"])

    def test_two_clients_or_nothing_fails(self):
        self.assertEqual(self.run_reader("delegation.batch")["missing"][0]["id"], "no_delegation")
        self.batch(count=2)
        self.assertEqual(self.run_reader("delegation.batch")["missing"][0]["id"], "not_one_batch")

    def test_a_batch_before_setup_does_not_count(self):
        self.chat(T0 - 100, [("assistant", "", None, call("delegate_task", tasks=[{"goal": "a"}, {"goal": "b"}, {"goal": "c"}])),
                             ("tool", "{}", "delegate_task", None)])
        self.assertFalse(self.run_reader("delegation.batch")["passed"])


class HelpersRan(Case):
    """delegation.helpers_ran"""

    def test_one_helper_per_client_passes(self):
        parent = self.batch()
        for slug in CLIENTS:
            self.helper(parent, [slug])
        out = self.run_reader("delegation.helpers_ran")
        self.assertTrue(out["passed"], out["detail"])

    def test_a_helper_that_read_two_folders_leaves_one_client_uncovered(self):
        parent = self.batch()
        self.helper(parent, ["harbor-dental"])
        self.helper(parent, ["quill-books", "vale-bakery"])
        out = self.run_reader("delegation.helpers_ran")
        self.assertFalse(out["passed"])
        self.assertIn("more than one", out["detail"])

    def test_no_helpers_fails(self):
        self.batch()
        self.assertEqual(self.run_reader("delegation.helpers_ran")["missing"][0]["id"], "no_helpers")


class SummariesRight(Case):
    """delegation.summaries_right"""

    def summaries(self, rule=True, swap=False):
        slugs = list(CLIENTS)
        for i, slug in enumerate(slugs):
            figure = CLIENTS[slugs[(i + 1) % 3] if swap and i == 0 else slug]["budget"]
            self.write(f"clients/{slug}/summary.md", f"# {CLIENTS[slug]['name']}\nBudget: {figure}\n" + (f"\n{RULE}\n" if rule else ""))

    def test_right_figures_and_the_rule_pass(self):
        self.summaries()
        out = self.run_reader("delegation.summaries_right")
        self.assertTrue(out["passed"], out["detail"])

    def test_a_missing_rule_line_fails_and_says_why(self):
        self.summaries(rule=False)
        out = self.run_reader("delegation.summaries_right")
        self.assertEqual(out["missing"][0]["id"], "rule_missing")
        self.assertIn("without memory", out["detail"])

    def test_another_clients_figure_or_a_missing_file_fails(self):
        self.summaries(swap=True)
        self.assertEqual(self.run_reader("delegation.summaries_right")["missing"][0]["id"], "wrong_figure")
        (self.folder / "clients" / "vale-bakery" / "summary.md").unlink()
        self.assertEqual(self.run_reader("delegation.summaries_right")["missing"][0]["id"], "no_summary")

    def test_the_rule_in_bold_still_counts(self):
        self.summaries(rule=False)
        for slug in CLIENTS:
            path = self.folder / "clients" / slug / "summary.md"
            path.write_text(path.read_text() + f"\n**{RULE}**\n")
        self.assertTrue(self.run_reader("delegation.summaries_right")["passed"])


class DelegationReading(Case):
    """delegation.reading"""

    def test_none_run_main_model_no_rule_passes(self):
        note = {"t_runs": "0", "t_model": "the main model", "t_rule": "no", "t_change": "raise the cap to 4 and copy the rule into each task"}
        self.assertTrue(self.run_reader("delegation.reading", note=note)["passed"])

    def test_two_run_fails(self):
        note = {"t_runs": "2", "t_model": "same as main", "t_rule": "no", "t_change": "split the batch into two calls"}
        out = self.run_reader("delegation.reading", note=note)
        self.assertEqual(out["missing"][0]["id"], "runs")

    def test_unanswered_cannot_read(self):
        self.assertFalse(self.run_reader("delegation.reading")["readable"])


class DelegationPlants(Case):
    def row(self):
        return {"name": "academy-practice", "status": "planted"}

    def test_one_helper_is_fixed_by_three_or_by_removing_it(self):
        text = (self.home / "config.yaml").read_text().replace("delegation:\n", "delegation:\n  max_concurrent_children: 1\n")
        (self.home / "config.yaml").write_text(text)
        self.assertFalse(self.pc.REGISTRY["one_helper"]["verify"](self.home, {}, "")["fixed"])
        (self.home / "config.yaml").write_text(text.replace("max_concurrent_children: 1", "max_concurrent_children: 3"))
        self.assertTrue(self.pc.REGISTRY["one_helper"]["verify"](self.home, {}, "")["fixed"])

    def test_the_helper_model_typo_is_fixed_by_emptying_it(self):
        text = (self.home / "config.yaml").read_text()
        (self.home / "config.yaml").write_text(text.replace("delegation:\n  model: ''", "delegation:\n  model: anthropic/claude-sonnat-4.6"))
        details = {"typo": "anthropic/claude-sonnat-4.6"}
        self.assertFalse(self.pc.REGISTRY["helper_model_typo"]["verify"](self.home, details, "")["fixed"])
        (self.home / "config.yaml").write_text(text)
        self.assertTrue(self.pc.REGISTRY["helper_model_typo"]["verify"](self.home, details, "")["fixed"])

    def test_refusals_are_detected(self):
        self.batch(result="Too many tasks: 3 provided, but max_concurrent_children is 1.")
        self.assertTrue(self.pc.REGISTRY["one_helper"]["detect"](self.home, {})["fired"])


# ---------------------------------------------------------------- toolsets --


def toolsets_config(home, cli=None, disabled=None, extra=""):
    text = (pathlib.Path(home) / "config.yaml").read_text()
    if cli is not None:
        text += "platform_toolsets:\n  cli: [" + ", ".join(cli) + "]\n"
    if disabled is not None:
        text = text.replace("agent:\n", "agent:\n  disabled_toolsets: [" + ", ".join(disabled) + "]\n", 1)
    (pathlib.Path(home) / "config.yaml").write_text(text + extra)


class Trimmed(Case):
    """toolsets.trimmed"""

    def test_file_only_passes(self):
        toolsets_config(self.home, cli=["file", "memory", "todo"])
        out = self.run_reader("toolsets.trimmed")
        self.assertTrue(out["passed"], out["detail"])

    def test_nothing_pinned_fails(self):
        self.assertEqual(self.run_reader("toolsets.trimmed")["missing"][0]["id"], "all_on")

    def test_terminal_left_on_fails_unless_disabled_elsewhere(self):
        toolsets_config(self.home, cli=["file", "terminal"])
        self.assertEqual(self.run_reader("toolsets.trimmed")["missing"][0]["id"], "extra")

    def test_disabled_toolsets_take_terminal_off(self):
        toolsets_config(self.home, cli=["file", "terminal"], disabled=["terminal"])
        self.assertTrue(self.run_reader("toolsets.trimmed")["passed"])

    def test_file_off_fails(self):
        toolsets_config(self.home, cli=["memory"])
        self.assertEqual(self.run_reader("toolsets.trimmed")["missing"][0]["id"], "file_off")

    def test_a_composite_list_counts_as_everything(self):
        toolsets_config(self.home, cli=["hermes-cli"])
        self.assertEqual(self.run_reader("toolsets.trimmed")["missing"][0]["id"], "all_on")


class ProbeRefused(Case):
    """toolsets.probe_refused"""

    def test_a_probe_after_the_change_that_ran_nothing_passes(self):
        hb.touch_back(self.home / "config.yaml", T0)
        self.chat(T0 + 50, [("user", "Run the command date in the terminal.", None, None), ("assistant", "I have no terminal tool.", None, None)])
        out = self.run_reader("toolsets.probe_refused")
        self.assertTrue(out["passed"], out["detail"])

    def test_a_probe_that_ran_the_terminal_fails(self):
        hb.touch_back(self.home / "config.yaml", T0)
        self.chat(T0 + 50, [("user", "Run the command date in the terminal.", None, None), ("tool", "Mon Nov 9", "terminal", None)])
        self.assertEqual(self.run_reader("toolsets.probe_refused")["missing"][0]["id"], "ran")

    def test_a_probe_before_the_change_does_not_count(self):
        hb.touch_back(self.home / "config.yaml", T0 + 500)
        self.chat(T0 + 50, [("user", "Run the command date in the terminal.", None, None)])
        self.assertEqual(self.run_reader("toolsets.probe_refused")["missing"][0]["id"], "no_probe")


class JobDone(Case):
    """toolsets.job_done"""

    def test_a_brief_naming_every_meeting_written_by_hermes_passes(self):
        self.write("brief.md", "Van lease: two quotes.\nRent review: 4 percent.\nWebsite: slow on phones.\n")
        self.chat(T0 + 50, [("tool", "{\"ok\": true}", "write_file", None)])
        out = self.run_reader("toolsets.job_done")
        self.assertTrue(out["passed"], out["detail"])

    def test_a_missing_meeting_or_brief_fails(self):
        self.assertEqual(self.run_reader("toolsets.job_done")["missing"][0]["id"], "no_brief")
        self.write("brief.md", "Van lease only.\n")
        self.assertEqual(self.run_reader("toolsets.job_done")["missing"][0]["id"], "missed")

    def test_a_brief_hermes_never_wrote_fails(self):
        self.write("brief.md", "Van lease. Rent review. Website.\n")
        self.assertEqual(self.run_reader("toolsets.job_done")["missing"][0]["id"], "not_hermes")


class ToolsetsReading(Case):
    """toolsets.reading"""

    def test_file_and_web_no_program_yes_home_passes(self):
        note = {"t_on": "file and web", "t_run": "no", "t_home": "yes", "t_change": "point disk at one project folder"}
        self.assertTrue(self.run_reader("toolsets.reading", note=note)["passed"])

    def test_counting_terminal_fails(self):
        note = {"t_on": "file, web, terminal", "t_run": "no", "t_home": "yes", "t_change": "point disk at one project folder"}
        self.assertEqual(self.run_reader("toolsets.reading", note=note)["missing"][0]["id"], "on")

    def test_missing_the_connector_fails(self):
        note = {"t_on": "file, web", "t_run": "no", "t_home": "no", "t_change": "nothing to change here"}
        self.assertEqual(self.run_reader("toolsets.reading", note=note)["missing"][0]["id"], "home")


class WideConnector(Case):
    def test_a_connector_on_the_profile_folder_is_found_and_fixed_by_narrowing(self):
        hb.write_servers(self.home, hb.server_block("notes", ["-y", hb.FS, str(self.home)]))
        verify = self.pc.REGISTRY["wide_connector"]["verify"]
        self.assertFalse(verify(self.home, {"server": "notes"}, "")["fixed"])
        hb.write_servers(self.home, hb.server_block("notes", ["-y", hb.FS, str(self.folder)]))
        self.assertTrue(verify(self.home, {"server": "notes"}, "")["fixed"])
        hb.write_servers(self.home, hb.server_block("notes", ["-y", hb.FS, str(self.home)], enabled=False))
        self.assertTrue(verify(self.home, {"server": "notes"}, "")["fixed"])


if __name__ == "__main__":
    unittest.main()
