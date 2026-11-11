"""Fixture tests for the live-check readers of Foundations missions 7 to 11 (one class per reader id, the class
docstring is the id, as scripts/check_foundations.py requires)."""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
import hermes_fixture_b as hb  # noqa: E402
from test_scrub import load  # noqa: E402

T0 = hf.T0


class ReaderCase(unittest.TestCase):
    def setUp(self):
        self.c = load("foundations_checks")
        self.pb = load("plants_b")
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.home = hf.build_home(self.tmp / "profiles" / "academy-practice")
        self.folder = hb.folder(self.home)
        self.ctx = {"home": self.home, "note": {}, "planted": {}, "setup": {"folder": str(self.folder.resolve()), "server": "files"},
                    "row": {"plan": {"folder": str(self.folder.resolve())}, "planted_at": hb.iso(T0)}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_reader(self, reader_id, **ctx):
        return self.c.run(reader_id, {**self.ctx, **ctx})

    def config_at(self, epoch):
        hb.touch_back(self.home / "config.yaml", epoch)

    def files_connector(self, **kw):
        hb.write_servers(self.home, hb.server_block("files", ["-y", hb.FS, str(self.folder)], **kw))
        self.config_at(T0)

    def session(self, started, *messages):
        con = hf.state_db(self.home)
        sid = hf.add_session(con, started_at=started)
        for n, (role, content, tool) in enumerate(messages, start=1):
            hf.add_message(con, sid, role, content, started + n, tool_name=tool)
        con.close()
        return sid


# --------------------------------------------------------------- connectors --


class OneScoped(ReaderCase):
    """connectors.one_scoped"""

    def test_one_connector_with_the_job_tools_passes(self):
        self.files_connector(trust="untrusted", include=["list_directory", "read_text_file", "write_file"])
        out = self.run_reader("connectors.one_scoped")
        self.assertTrue(out["passed"], out["detail"])

    def test_a_twin_an_exclude_list_or_an_extra_tool_fails(self):
        hb.write_servers(self.home, hb.server_block("files", ["-y", hb.FS, str(self.folder)], include=["write_file"]),
                         hb.server_block("docs", ["-y", hb.FS, str(self.folder)]))
        self.assertEqual(self.run_reader("connectors.one_scoped")["missing"][0]["id"], "scope")
        self.files_connector(exclude=["move_file"])
        self.assertEqual(self.run_reader("connectors.one_scoped")["missing"][0]["id"], "no_include")
        self.files_connector(include=["write_file", "move_file"])
        self.assertEqual(self.run_reader("connectors.one_scoped")["missing"][0]["id"], "extra_tool")

    def test_a_switched_off_twin_does_not_count(self):
        hb.write_servers(self.home, hb.server_block("files", ["-y", hb.FS, str(self.folder)], include=["write_file"]),
                         hb.server_block("docs", ["-y", hb.FS, str(self.folder)], enabled=False))
        self.assertTrue(self.run_reader("connectors.one_scoped")["passed"])


class Untrusted(ReaderCase):
    """connectors.untrusted"""

    def test_the_word_untrusted_passes_and_unset_or_a_typo_fails(self):
        self.files_connector(trust="untrusted", include=["write_file"])
        self.assertTrue(self.run_reader("connectors.untrusted")["passed"])
        self.files_connector(include=["write_file"])
        self.assertFalse(self.run_reader("connectors.untrusted")["passed"])
        self.files_connector(trust="untrustd", include=["write_file"])
        out = self.run_reader("connectors.untrusted")
        self.assertFalse(out["passed"])
        self.assertIn("untrustd", out["detail"])


class RefusalSeen(ReaderCase):
    """connectors.refusal_seen"""

    def test_a_refusal_after_the_last_change_passes(self):
        self.files_connector(trust="untrusted", include=["write_file"])
        self.session(T0 + 100, ("user", "Write the summary.", None), ("tool", hb.refusal("write_file", "files"), "mcp__files__write_file"))
        out = self.run_reader("connectors.refusal_seen")
        self.assertTrue(out["passed"], out["detail"])
        self.assertIn("did not approve", out["evidence"][0][2])

    def test_a_refusal_before_the_change_or_on_another_server_fails(self):
        self.files_connector(trust="untrusted", include=["write_file"])
        self.session(T0 - 100, ("tool", hb.refusal("write_file", "files"), "mcp__files__write_file"))
        self.session(T0 + 100, ("tool", hb.refusal("write_file", "docs"), "mcp__docs__write_file"))
        self.assertFalse(self.run_reader("connectors.refusal_seen")["passed"])


class CleanStart(ReaderCase):
    """connectors.clean_start"""

    def test_a_banner_after_the_change_and_a_good_call_pass(self):
        self.files_connector(trust="untrusted", include=["write_file", "list_directory"])
        hb.banner(self.home, "files", T0 + 50)
        self.session(T0 + 60, ("tool", json.dumps({"content": "order-101.txt"}), "mcp__files__list_directory"))
        self.assertTrue(self.run_reader("connectors.clean_start")["passed"])

    def test_no_banner_since_the_change_or_only_failed_calls_fail(self):
        self.files_connector(trust="untrusted", include=["write_file"])
        hb.banner(self.home, "files", T0 - 50)
        self.assertEqual(self.run_reader("connectors.clean_start")["missing"][0]["id"], "no_start")
        hb.banner(self.home, "files", T0 + 50)
        self.session(T0 + 60, ("tool", hb.refusal("write_file", "files"), "mcp__files__write_file"))
        self.assertEqual(self.run_reader("connectors.clean_start")["missing"][0]["id"], "no_call")


class FolderOutcome(ReaderCase):
    """connectors.folder_outcome"""

    def setUp(self):
        super().setUp()
        (self.folder / "orders").mkdir()
        orders = {}
        for n in (101, 102):
            text = f"Order {n}\n"
            (self.folder / "orders" / f"order-{n}.txt").write_text(text, encoding="utf-8")
            hb.touch_back(self.folder / "orders" / f"order-{n}.txt", T0)
            orders[f"orders/order-{n}.txt"] = self.pb._sha(text)
        self.ctx["setup"]["orders"] = orders

    def test_a_summary_and_orders_in_place_pass(self):
        (self.folder / "summary.txt").write_text("Two orders this week.\n", encoding="utf-8")
        self.assertTrue(self.run_reader("connectors.folder_outcome")["passed"])

    def test_a_moved_order_or_no_summary_fails(self):
        self.assertEqual(self.run_reader("connectors.folder_outcome")["missing"][0]["id"], "no_summary")
        (self.folder / "archive").mkdir()
        os.replace(self.folder / "orders" / "order-102.txt", self.folder / "archive" / "order-102.txt")
        self.assertEqual(self.run_reader("connectors.folder_outcome")["missing"][0]["id"], "moved")


class Reading(ReaderCase):
    """connectors.reading"""

    def mission(self):
        return {"transfer": {"example": {"command": "npx", "trust": "untrusted", "tools": {"exclude": ["move_file"]}}}}

    def test_the_right_columns_pass(self):
        note = {"t_free": "10", "t_ask": "create_directory, write_file and edit_file", "t_blocked": "move_file",
                "t_change": "An allow list of the two it needs."}
        self.assertTrue(self.run_reader("connectors.reading", note=note, mission=self.mission())["passed"])

    def test_a_wrong_column_fails(self):
        note = {"t_free": "9", "t_ask": "write_file, edit_file, create_directory, move_file", "t_blocked": "", "t_change": "Fine as is."}
        out = self.run_reader("connectors.reading", note=note, mission=self.mission())
        self.assertFalse(out["passed"])
        self.assertEqual(len(out["missing"]), 3)


# --------------------------------------------------------------- schedules --


class ScheduleCase(ReaderCase):
    def job(self, **extra):
        hf.write_jobs(self.home, [hf.job("job-y1", "late-list", **extra)])
        self.ctx["note"] = {"job_name": "late-list"}

    def file(self, name="orders-week.csv"):
        (self.folder / name).write_text("order,status\n1,late\n", encoding="utf-8")


class RequestParts(ScheduleCase):
    """schedules.request_parts"""

    def test_a_request_for_a_stranger_passes(self):
        self.file()
        self.job(prompt="Read orders-week.csv in the practice folder and list each late order as a bullet. If the file is "
                        "missing or empty, start your reply with [CRON_FAILURE].")
        out = self.run_reader("schedules.request_parts")
        self.assertTrue(out["passed"], out["detail"])

    def test_a_vague_or_partial_request_fails(self):
        self.file()
        self.job(prompt="Summarize the file we talked about and send it to me.")
        out = self.run_reader("schedules.request_parts")
        self.assertFalse(out["passed"])
        self.assertIn("we talked about", out["detail"])
        self.job(prompt="List the late orders in orders-week.csv.")
        self.assertIn("if it fails", self.run_reader("schedules.request_parts")["detail"])

    def test_no_job_name_cannot_be_read(self):
        self.assertFalse(self.run_reader("schedules.request_parts", note={})["readable"])


class TestedPaused(ScheduleCase):
    """schedules.tested_paused"""

    def test_a_hand_run_first_passes(self):
        self.job()
        hb.runs_db(self.home, [{"job_id": "job-y1", "source": "direct", "claimed_at": hb.iso(T0)},
                               {"job_id": "job-y1", "claimed_at": hb.iso(T0 + 3600), "scheduled_instant": hb.iso(T0 + 3600)}])
        self.assertTrue(self.run_reader("schedules.tested_paused")["passed"])

    def test_a_scheduled_first_run_or_none_fails(self):
        self.job()
        hb.runs_db(self.home, [])
        self.assertEqual(self.run_reader("schedules.tested_paused")["missing"][0]["id"], "no_runs")
        hb.runs_db(self.home, [{"job_id": "job-y1", "claimed_at": hb.iso(T0), "scheduled_instant": hb.iso(T0)}])
        self.assertEqual(self.run_reader("schedules.tested_paused")["missing"][0]["id"], "untested")


class MissedSlots(ScheduleCase):
    """Hermes 0.23.0 books a ``missed`` row, with ``scheduled_instant`` set, when a job's slots go by unfired (the machine
    asleep). It is not a run: a hand test after it still counts as the first run (cron/executions.py:39-40)."""

    def test_a_missed_row_is_not_a_run(self):
        self.job()
        hb.runs_db(self.home, [{"job_id": "job-y1", "source": "scheduler", "status": "missed", "claimed_at": hb.iso(T0 - 60),
                                "scheduled_instant": hb.iso(T0 - 60)},
                               {"job_id": "job-y1", "source": "direct", "claimed_at": hb.iso(T0)}], version="0.23.0")
        out = self.run_reader("schedules.tested_paused")
        self.assertTrue(out["passed"], out["detail"])
        hrb = load("hermes_read_b")
        read = hrb.runs(self.home, "job-y1")
        self.assertEqual(len(read["executions"]), 1)
        self.assertEqual(read["missed"], 1)

    def test_only_missed_rows_means_never_run(self):
        self.job()
        hb.runs_db(self.home, [{"job_id": "job-y1", "source": "scheduler", "status": "missed", "claimed_at": hb.iso(T0),
                                "scheduled_instant": hb.iso(T0)}], version="0.23.0")
        self.assertEqual(self.run_reader("schedules.tested_paused")["missing"][0]["id"], "no_runs")

    def test_a_room_delivery_is_a_real_target(self):
        """room:<id>[@profile] is a delivery target from 0.23.0 (cron/scheduler_delivery_room.py)."""
        self.assertTrue(self.pb.deliver_ok("room:team-ops"))
        self.assertTrue(self.pb.deliver_ok("local,room:team-ops@work"))
        self.assertFalse(self.pb.deliver_ok("roomz:team-ops"))


class ConnectorToolNames(unittest.TestCase):
    """Hermes names connector tools mcp__<server>__<tool> (tools/mcp_tool_schema.py:159, 0.22.0 to 0.23.0)."""

    def test_the_double_underscore_name_matches_and_nothing_else(self):
        hrb = load("hermes_read_b")
        self.assertTrue(hrb.is_connector_tool("mcp__files__write_file", "files"))
        self.assertTrue(hrb.is_connector_tool("mcp__my_files__read", "my-files"))
        self.assertTrue(hrb.is_connector_tool("mcp__my_files__read", "my.files"))
        self.assertFalse(hrb.is_connector_tool("mcp_files_write_file", "files"))
        self.assertFalse(hrb.is_connector_tool("mcp__filesystem__read", "files"))
        self.assertFalse(hrb.is_connector_tool("write_file", "files"))
        self.assertFalse(hrb.is_connector_tool("mcp__files__write_file", ""))
        self.assertFalse(hrb.is_connector_tool(None, "files"))


class ModelPinned(ScheduleCase):
    """schedules.model_pinned"""

    def test_a_model_passes_and_default_fails(self):
        self.job(model="openai/gpt-5-mini")
        self.assertTrue(self.run_reader("schedules.model_pinned")["passed"])
        self.job(model=None)
        self.assertFalse(self.run_reader("schedules.model_pinned")["passed"])


class TwoRuns(ScheduleCase):
    """schedules.two_runs"""

    def rows(self, late=False):
        return [{"job_id": "job-y1", "source": "direct", "claimed_at": hb.iso(T0), "finished_at": hb.iso(T0 + 40)},
                {"job_id": "job-y1", "claimed_at": hb.iso(T0 + 3600), "scheduled_instant": hb.iso(T0 + 3600)},
                {"job_id": "job-y1", "claimed_at": hb.iso(T0 + 7200 + (4000 if late else 10)), "scheduled_instant": hb.iso(T0 + 7200)}]

    def test_two_scheduled_runs_delivered_pass_and_keep_the_wait(self):
        self.job(last_status="ok", deliver="local")
        hb.runs_db(self.home, self.rows(late=True))
        hb.output_files(self.home, "job-y1", 3)
        out = self.run_reader("schedules.two_runs")
        self.assertTrue(out["passed"], out["detail"])
        facts = {f["label"]: f["value"] for f in out["facts"]}
        self.assertEqual(facts["Late runs (catch-up after sleep counts)"], "1")
        self.assertRegex(facts["Waiting for runs"], r"^\d+-\d+$")

    def test_one_run_a_bad_status_or_a_missing_result_fails(self):
        self.job(last_status="ok")
        hb.runs_db(self.home, self.rows()[:2])
        self.assertEqual(self.run_reader("schedules.two_runs")["missing"][0]["id"], "runs")
        self.job(last_status="delivery_failed")
        hb.runs_db(self.home, self.rows())
        self.assertEqual(self.run_reader("schedules.two_runs")["missing"][0]["id"], "status")
        self.job(last_status="ok", deliver="local")
        hb.output_files(self.home, "job-y1", 1)
        self.assertEqual(self.run_reader("schedules.two_runs")["missing"][0]["id"], "delivery")


class Chained(ScheduleCase):
    """schedules.chained"""

    def test_a_second_job_reading_the_first_passes(self):
        hf.write_jobs(self.home, [hf.job("job-y1", "late-list"),
                                  hf.job("job-y2", "late-digest", deliver="telegram", context_from=["job-y1"])])
        hb.runs_db(self.home, [{"job_id": "job-y2", "source": "direct", "claimed_at": hb.iso(T0)}])
        out = self.run_reader("schedules.chained", note={"first_job": "late-list", "job_name": "late-digest"})
        self.assertTrue(out["passed"], out["detail"])

    def test_same_delivery_or_no_link_fails(self):
        hf.write_jobs(self.home, [hf.job("job-y1", "late-list"), hf.job("job-y2", "late-digest")])
        out = self.run_reader("schedules.chained", note={"first_job": "late-list", "job_name": "late-digest"})
        self.assertFalse(out["passed"])


# ------------------------------------------------------------------ safety --


class SafetyCase(ReaderCase):
    def settings(self, mode="smart", checkpoints=False, allow=None):
        text = hf.CONFIG.replace("mode: manual", f"mode: {json.dumps(mode)}").replace("  enabled: false\n  max_snapshots", f"  enabled: {'true' if checkpoints else 'false'}\n  max_snapshots")
        if allow is not None:
            text += "command_allowlist: [" + ", ".join(json.dumps(a) for a in allow) + "]\n"
        text = text.replace("mcp_servers:\n  github:\n    enabled: true\n    trust: untrusted", "mcp_servers:\n  github:\n    enabled: false\n    trust: untrusted")
        hf.write_config(self.home, text)


class CheckpointsOn(SafetyCase):
    """safety.checkpoints_on"""

    def test_on_passes_and_off_fails(self):
        self.settings(checkpoints=True)
        self.assertTrue(self.run_reader("safety.checkpoints_on")["passed"])
        self.settings(checkpoints=False)
        self.assertFalse(self.run_reader("safety.checkpoints_on")["passed"])


class RolledBack(SafetyCase):
    """safety.rolled_back"""

    def test_a_branch_and_the_apps_list_with_a_rollback_pass(self):
        hb.checkpoint_branch(self.home, self.folder)
        sample = {"source": "rollback.list", "checkpoints": [{"message": "pre-rollback snapshot (restoring to 1a2b3c4d)"},
                                                             {"message": "before write_file"}]}
        self.assertTrue(self.run_reader("safety.rolled_back", sample=sample)["passed"])

    def test_the_page_alone_never_passes_and_no_list_says_how_to_check(self):
        sample = {"source": "rollback.list", "checkpoints": [{"message": "pre-rollback snapshot (restoring to 1a2b3c4d)"}]}
        self.assertEqual(self.run_reader("safety.rolled_back", sample=sample)["missing"][0]["id"], "no_snapshot")
        hb.checkpoint_branch(self.home, self.folder)
        out = self.run_reader("safety.rolled_back")
        self.assertFalse(out["passed"])
        self.assertFalse(out["readable"])
        self.assertIn("/rollback", out["detail"])
        self.assertEqual(self.run_reader("safety.rolled_back", sample={"source": "rollback.list", "checkpoints": [{"message": "x"}]})["missing"][0]["id"],
                         "no_rollback")


class ApprovalsSafe(SafetyCase):
    """safety.approvals_safe"""

    def test_smart_and_an_empty_list_pass(self):
        self.settings(allow=[])
        self.assertTrue(self.run_reader("safety.approvals_safe")["passed"])

    def test_off_or_a_saved_recursive_delete_fails(self):
        self.settings(mode="off")
        self.assertEqual(self.run_reader("safety.approvals_safe")["missing"][0]["id"], "mode")
        self.settings(allow=["recursive delete"])
        self.assertEqual(self.run_reader("safety.approvals_safe")["missing"][0]["id"], "always")


GOOD_GRID = {"tb": "asks", "ta": "undo", "fb": "nothing", "fa": "undo", "cb": "no_connector", "ca": "nothing"}


class GridMatches(SafetyCase):
    """safety.grid_matches"""

    def test_a_grid_that_matches_passes(self):
        self.settings(checkpoints=True)
        self.assertTrue(self.run_reader("safety.grid_matches", note=GOOD_GRID)["passed"])

    def test_a_cell_from_memory_fails(self):
        self.settings(mode="off", checkpoints=True)
        out = self.run_reader("safety.grid_matches", note=GOOD_GRID)
        self.assertFalse(out["passed"])
        self.assertEqual(out["missing"][0]["id"], "cell:tb")

    def test_cells_are_shown_in_words_never_raw_values(self):
        self.settings(mode="off", checkpoints=True)
        values = {"no_connector", "asks", "nothing", "undo", "some_slip"}
        for out in (self.run_reader("safety.grid_matches", note=GOOD_GRID),
                    self.run_reader("safety.shared_grid", note={**GOOD_GRID, "worry": "The invoice email, untrusted asks first."})):
            for f in out["facts"]:
                said = re.fullmatch(r"You: (.+)\. The profile: (.+)\.", f["value"])
                self.assertTrue(said, f["value"])
                self.assertFalse(values & set(said.groups()), f["value"])
        facts = {f["label"]: f["value"] for f in self.run_reader("safety.grid_matches", note=GOOD_GRID)["facts"]}
        self.assertEqual(facts["Connected tools, before"], "You: No connector in this profile. The profile: No connector in this profile.")
        self.assertEqual(facts["Terminal, before"], "You: Something asks first. The profile: Nothing asks.")
        self.assertEqual(facts["Terminal, after"], "You: A snapshot can undo it. The profile: A snapshot can undo it.")


class SharedGrid(SafetyCase):
    """safety.shared_grid"""

    def test_the_taught_setup_and_a_worry_pass(self):
        note = {"tb": "asks", "ta": "undo", "fb": "nothing", "fa": "undo", "cb": "asks", "ca": "nothing",
                "worry": "Bottom right: a sent invoice can't come back; untrusted makes it ask first."}
        self.assertTrue(self.run_reader("safety.shared_grid", note=note)["passed"])
        self.assertFalse(self.run_reader("safety.shared_grid", note={**note, "ca": "undo"})["passed"])
        self.assertFalse(self.run_reader("safety.shared_grid", note={**note, "worry": ""})["passed"])


# ---------------------------------------------------------------- diagnose --


class DiagnoseCase(ReaderCase):
    def connector_break(self):
        command = str(self.folder / "tools" / "inbox-tool-server")
        hb.write_servers(self.home, hb.server_block("inbox-tool", [], command=command))
        self.ctx["planted"] = {"broken_connector": {"server": "inbox-tool", "command": command, "layer": "connector"}}
        return command


class LayerNamed(DiagnoseCase):
    """diagnose.layer_named"""

    def test_the_right_layer_passes(self):
        self.connector_break()
        self.assertTrue(self.run_reader("diagnose.layer_named", note={"layer": "connector"})["passed"])
        self.assertFalse(self.run_reader("diagnose.layer_named", note={"layer": "model"})["passed"])


class LineQuoted(DiagnoseCase):
    """diagnose.line_quoted"""

    def test_a_quoted_line_from_the_logs_passes(self):
        command = self.connector_break()
        line = hb.mcp_failure_line(T0 + 300, "inbox-tool", command)
        hb.log(self.home, "errors.log.1", [line])
        quote = "Failed to connect to MCP server 'inbox-tool'"
        self.assertTrue(self.run_reader("diagnose.line_quoted", note={"quote": quote})["passed"])

    def test_a_line_not_in_the_logs_or_about_something_else_fails(self):
        self.connector_break()
        self.assertEqual(self.run_reader("diagnose.line_quoted", note={"quote": "Failed to connect to MCP server 'other'"})["missing"][0]["id"],
                         "not_found")
        hb.log(self.home, "errors.log", [f"{hb.local_stamp(T0 + 400)} WARNING tools.memory: over budget again"])
        self.assertEqual(self.run_reader("diagnose.line_quoted", note={"quote": "WARNING tools.memory: over budget again"})["missing"][0]["id"],
                         "elsewhere")


class BackupFirst(DiagnoseCase):
    """diagnose.backup_first"""

    def test_a_backup_before_the_fix_passes(self):
        self.connector_break()
        hb.backup(self.home, T0 + 200)
        hb.write_servers(self.home, hb.server_block("inbox-tool", [], command="npx", enabled=False))
        self.config_at(T0 + 400)
        self.assertTrue(self.run_reader("diagnose.backup_first")["passed"])

    def test_a_backup_after_the_fix_or_no_fix_fails(self):
        self.connector_break()
        self.assertEqual(self.run_reader("diagnose.backup_first")["missing"][0]["id"], "not_fixed")
        hb.write_servers(self.home, hb.server_block("inbox-tool", [], command="npx", enabled=False))
        self.config_at(T0 + 400)
        hb.backup(self.home, T0 + 500, quick=True)
        self.assertEqual(self.run_reader("diagnose.backup_first")["missing"][0]["id"], "no_backup")


class WorksAfter(DiagnoseCase):
    """diagnose.works_after"""

    def test_a_new_chat_with_an_answer_after_the_fix_passes(self):
        self.connector_break()
        self.config_at(T0 + 400)
        self.assertFalse(self.run_reader("diagnose.works_after")["passed"])
        self.session(T0 + 500, ("user", "hello", None), ("assistant", "Hello. How can I help?", None))
        self.assertTrue(self.run_reader("diagnose.works_after")["passed"])

    def test_the_job_variant_needs_a_good_run_after_the_fix(self):
        hf.write_jobs(self.home, [hf.job("job-b1", "academy-daily-check", deliver="local", last_status="ok")])
        hb.touch_back(self.home / "cron" / "jobs.json", T0 + 400)
        planted = {"job_blocked": {"job": "academy-daily-check", "deliver": "telgram", "layer": "scheduled job"}}
        hb.runs_db(self.home, [{"job_id": "job-b1", "claimed_at": hb.iso(T0 + 100), "status": "completed"}])
        self.assertFalse(self.run_reader("diagnose.works_after", planted=planted)["passed"])
        hb.runs_db(self.home, [{"job_id": "job-b1", "claimed_at": hb.iso(T0 + 3600), "scheduled_instant": hb.iso(T0 + 3600)}])
        self.assertTrue(self.run_reader("diagnose.works_after", planted=planted)["passed"])


class RoundOne(DiagnoseCase):
    """diagnose.round_one"""

    def test_round_one_is_shown_and_never_fails_when_readable(self):
        setup = {"typo": "anthropic/claude-sonnet-4.6x", "model": "anthropic/claude-sonnet-4.6"}
        out = self.run_reader("diagnose.round_one", setup=setup)
        self.assertTrue(out["passed"])
        self.assertIn("fixed", json.dumps(out["facts"]))
        self.assertFalse(self.run_reader("diagnose.round_one", setup={})["readable"])


# ------------------------------------------------------------------ review --


class ClaimsChecked(ReaderCase):
    """review.claims_checked"""

    def test_marked_claims_that_agree_with_the_files_pass(self):
        (self.folder / "clean.csv").write_text("a,b\n", encoding="utf-8")
        self.session(T0 + 10, ("user", "Tidy it.", None), ("assistant", "Done. I wrote clean.csv with 12 rows.", None))
        note = {"claims": "Wrote clean.csv - held\n12 rows - didn't", "wrong": "Two rows were dropped from the export."}
        self.assertTrue(self.run_reader("review.claims_checked", note=note)["passed"])

    def test_an_unmarked_claim_or_a_held_file_that_isnt_there_fails(self):
        self.session(T0 + 10, ("assistant", "Done. I wrote report.md.", None))
        self.assertEqual(self.run_reader("review.claims_checked", note={"claims": "Wrote report.md", "wrong": "Nothing found after checking."})["missing"][0]["id"],
                         "unmarked")
        self.assertEqual(self.run_reader("review.claims_checked", note={"claims": "Wrote report.md - held", "wrong": "Nothing found after checking."})["missing"][0]["id"],
                         "clash")


class ModelsMatch(ReaderCase):
    """review.models_match"""

    def test_a_list_that_matches_the_settings_passes(self):
        note = {"main_model": "claude-sonnet-4.6", "fallback": "gpt-5-mini", "subagents": "same as main", "job_model": "none",
                "subagents_ran": "no"}
        out = self.run_reader("review.models_match", note=note)
        self.assertTrue(out["passed"], out["detail"])

    def test_a_wrong_backup_or_a_helper_that_never_ran_fails(self):
        note = {"main_model": "claude-sonnet-4.6", "fallback": "none", "subagents": "same as main", "job_model": "none"}
        self.assertFalse(self.run_reader("review.models_match", note=note)["passed"])
        note = {**note, "fallback": "gpt-5-mini", "subagents_ran": "yes"}
        self.assertIn("Helper agents ran", self.run_reader("review.models_match", note=note)["detail"])


class SelfEdits(ReaderCase):
    """review.self_edits"""

    def test_every_change_listed_passes(self):
        base = self.c.READERS and load("foundations_checks_b").baseline(self.home)
        hf.write_memory(self.home, ["Harbor Bakery uses QuickBooks Online; the other five use Xero.", "Reports go out on Fridays at noon."], None)
        row = {"plan": {"baseline": base}}
        note = {"edits": "MEMORY.md: Reports go out on Fridays at noon - on its own - keep"}
        out = self.run_reader("review.self_edits", row=row, note=note)
        self.assertTrue(out["passed"], out["detail"])

    def test_an_unlisted_change_or_no_snapshot_fails(self):
        b = load("foundations_checks_b")
        base = b.baseline(self.home)
        hf.stage_pending(self.home, content="Prefers tables over lists")
        out = self.run_reader("review.self_edits", row={"plan": {"baseline": base}}, note={"edits": "Nothing changed."})
        self.assertEqual(out["missing"][0]["id"], "unlisted")
        self.assertFalse(self.run_reader("review.self_edits", row={"plan": {}}, note={"edits": "x"})["readable"])


class CanClaimRead(ReaderCase):
    """review.can_claim_read"""

    def test_a_named_claim_passes_and_a_blank_cannot_be_read(self):
        self.assertTrue(self.run_reader("review.can_claim_read", note={"claim_review": "The schedules claim: one run was late."})["passed"])
        self.assertFalse(self.run_reader("review.can_claim_read", note={})["readable"])


# ------------------------------------------------------------------ plants --


class AllFixed(ReaderCase):
    """plants.all_fixed"""

    def test_fixed_and_unfixed_plants(self):
        self.ctx["planted"] = {"open_connector": {"server": "docs"}}
        block = "mcp_servers:\n  docs:\n    command: npx\n    args: [-y, pkg, /tmp/x]\n"
        hf.write_config(self.home, hf.CONFIG + "\n" + block)
        out = self.run_reader("plants.all_fixed")
        self.assertFalse(out["passed"])
        hf.write_config(self.home, hf.CONFIG + "\n" + block.replace("args:", "trust: untrusted\n    args:"))
        self.assertTrue(self.run_reader("plants.all_fixed")["passed"])
        hf.write_config(self.home, hf.CONFIG)
        self.assertTrue(self.run_reader("plants.all_fixed")["passed"])
        self.assertFalse(self.run_reader("plants.all_fixed", planted={})["readable"])


if __name__ == "__main__":
    unittest.main()
