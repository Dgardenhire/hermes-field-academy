"""Foundations missions 1, 2, 4, 5 and 6 (0.9 M6, part A): planters, detectors, fix-verifiers, readers and notes.

Every reader here runs against a practice profile laid down the way Hermes's profiles.create would (foundations_support)
with chat records built from Hermes 0.22.4's own schema strings (hermes_fixture). Nothing runs Hermes. Each reader has
a test class whose docstring is its id (scripts/check_foundations.py requires it).
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402


def call(tool, **args):
    return json.dumps([{"id": "c1", "type": "function", "function": {"name": tool, "arguments": json.dumps(args)}}])


def calls(*pairs):
    return json.dumps([{"id": f"c{i}", "type": "function", "function": {"name": n, "arguments": json.dumps(a)}} for i, (n, a) in enumerate(pairs)])


class PartA(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.content = self.mod("foundations_content")
        self.checks = self.mod("foundations_checks")
        self.plants_a = self.mod("plants_a")
        self.read_a = self.mod("hermes_read_a")
        self.f = self.mod("foundations")
        self.fa = self.mod("foundations_a")

    def tearDown(self):
        for name in ("academy-practice", "academy-practice-b"):
            row = self.practice.record(name)
            if row and row.get("path") and pathlib.Path(row["path"]).is_dir():
                self.plants_a.before_remove(row, pathlib.Path(row["path"]))
        super().tearDown()

    def planted_profile(self, kinds, which=("a",), mission=None):
        for w in which:
            self.ready(w)
        self.practice.plant("academy-practice", kinds, "seed-1")
        return self.ctx(mission)

    def ctx(self, mission=None, note=None, name="academy-practice"):
        return {"home": self.home(name), "note": note or {}, "planted": self.practice.planted(name),
                "mission": self.content.get(mission) if mission else {}}

    def run_reader(self, reader, ctx, **note):
        if note:
            ctx = {**ctx, "note": {**ctx["note"], **note}}
        return self.checks.run(reader, ctx)

    def session(self, msgs, started=hf.T0 + 100, name="academy-practice", **cols):
        """msgs: (role, content, extra) tuples, one second apart."""
        con = hf.state_db(self.home(name))
        sid = hf.add_session(con, started_at=started, **cols)
        for i, (role, content, extra) in enumerate(msgs):
            hf.add_message(con, sid, role, content, started + 1 + i, **extra)
        con.close()
        return sid


# ============================================================= practice_write ==


class Writers(PartA):
    def test_work_files_only_under_the_practice_folder(self):
        self.ready("a")
        row = self.practice.record("academy-practice")
        self.practice_write.write_work_file_a(self.home(), row, "practice-folder/job/a.csv", "x\n")
        self.assertTrue((self.home() / "practice-folder/job/a.csv").is_file())
        for bad in ("config.yaml", "practice-folder/../SOUL.md", "practice-folder/a.sh", ".env", "practice-folder/x/y/z.md"):
            with self.assertRaises(self.practice_write.Refused):
                self.practice_write.write_work_file_a(self.home(), row, bad, "x")

    def test_lock_then_unlock_for_removal(self):
        self.ready("a")
        row = self.practice.record("academy-practice")
        self.practice_write.write_work_file_a(self.home(), row, "practice-folder/job/summary.md", "old\n")
        self.practice_write.lock_work_file_a(self.home(), row, "practice-folder/job/summary.md")
        path = self.home() / "practice-folder/job/summary.md"
        self.assertTrue(self.read_a.work_file(self.home(), "practice-folder/job/summary.md")["locked"])
        with self.assertRaises(OSError):
            path.write_text("new")
        self.practice_write.unlock_work_file_a(self.home(), row, "practice-folder/job/summary.md")
        path.write_text("new")

    def test_skills_only_academy_named(self):
        self.ready("a")
        row = self.practice.record("academy-practice")
        self.practice_write.write_skill_a(self.home(), row, "skills/academy-x/SKILL.md", "---\nname: academy-x\n---\n")
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.write_skill_a(self.home(), row, "skills/mine/SKILL.md", "x")

    def test_a_connector_is_added_and_everything_else_reads_back_the_same(self):
        self.ready("a")
        row = self.practice.record("academy-practice")
        before = self.hermes_read.config(self.home())["values"]
        self.practice_write.add_mcp_server_a(self.home(), row, "academy-files", "npx", ["-y", "@x/y@1.0", "/tmp/p f"])
        after = self.hermes_read.config(self.home())["values"]
        self.assertEqual({k: v for k, v in after.items() if "academy-files" not in k}, before)
        self.assertEqual(self.read_a.connectors(self.home())["connectors"]["academy-files"], {"enabled": True, "package": "@x/y@1.0"})
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.add_mcp_server_a(self.home(), row, "github", "npx", [])

    def test_no_write_after_the_first_chat(self):
        self.ready("a")
        self.chat()
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.write_work_file_a(self.home(), self.practice.record("academy-practice"), "practice-folder/a.md", "x")


# ================================================================== mission 1 ==


class Loop(PartA):
    def setUp(self):
        super().setUp()

    def base(self, kinds=("input_empty",)):
        ctx = self.planted_profile(list(kinds), mission="f.loop")
        base = self.plants_a.base_for(ctx["planted"], "f.loop")
        return ctx, base

    def job(self, base, answer, steps, started=hf.T0 + 100):
        msgs = [("user", self.plants_a.card_m1(base), {})]
        for group in steps:
            msgs.append(("assistant", "", {"tool_calls": calls(*group)}))
            for name, args in group:
                msgs.append(("tool", json.dumps({"ok": True}), {"tool_name": name}))
        msgs.append(("assistant", answer, {}))
        return self.session(msgs, started=started)

    def write_output(self, base, text):
        (self.home() / base["output"]).write_text(text)

    def good_summary(self, base, extra=""):
        sheets = self.plants_a.sheet_rows(self.home(), base)
        rows = [r for rs in sheets.values() for r in rs]
        total = sum(int(r["hours"]) for r in rows)
        return "".join(f"- {r['job']}, {r['client']}, {r['hours']}\n" for r in rows) + f"Total hours: {total}\n{extra}"


class Base(Loop):
    def test_the_base_varies_by_seed_and_never_puts_a_card_in_the_job_folder(self):
        _ctx, base = self.base()
        names = sorted(p.name for p in (self.home() / base["job_rel"]).iterdir())
        self.assertEqual(names, sorted(f"{d}.csv" for d in base["days"]))
        self.assertEqual(len(list((self.home() / "practice-folder/warm-up").iterdir())), 4)
        self.assertIn(base["job_path"], self.plants_a.card_m1(base))

    def test_each_planter_detector_and_verifier(self):
        for kind in ("output_locked", "input_empty", "rows_short"):
            self.assertEqual(set(self.plants.REGISTRY[kind]), {"plant", "detect", "verify"})


class StepsMatch(Loop):
    """loop.steps_match"""

    def test_steps_in_order_pass_and_a_missing_step_fails(self):
        ctx, base = self.base()
        sheets = [f"{base['job_path']}/{d}.csv" for d in base["days"]]
        self.job(base, "Done.", [[("read_file", {"path": p}) for p in sheets], [("write_file", {"path": base["job_path"] + "/summary.md"})]])
        out = self.run_reader("loop.steps_match", ctx, steps=["Read the three sheets", "Wrote summary.md"])
        self.assertTrue(out["passed"], out)
        out = self.run_reader("loop.steps_match", ctx, steps=["Wrote summary.md", "nothing else"])
        self.assertFalse(out["passed"])

    def test_no_job_chat_cannot_be_read(self):
        ctx, _ = self.base()
        self.assertFalse(self.run_reader("loop.steps_match", ctx, steps=["a", "b"])["readable"])


class ClaimsListed(Loop):
    """loop.claims_listed"""

    def test_every_claim_caught(self):
        ctx, base = self.base()
        self.job(base, "I read all three sheets. There were 18 jobs. I saved summary.md.", [[("read_file", {"path": "x"})]])
        out = self.run_reader("loop.claims_listed", ctx, claims=["read all three sheets", "18 jobs", "saved summary.md"])
        self.assertTrue(out["passed"], out)
        out = self.run_reader("loop.claims_listed", ctx, claims=["read all three sheets"])
        self.assertFalse(out["passed"])


class ResultRight(Loop):
    """loop.result_right"""

    def test_empty_input_named_and_output_fresh_passes(self):
        ctx, base = self.base(("input_empty",))
        empty = ctx["planted"]["input_empty"]["empty"]
        self.job(base, "I read all three sheets and wrote the summary.", [[("read_file", {"path": "x"})]], started=hf.now_epoch() - 60)
        note = {"wrong": f"{empty} is empty: a header row only.", "false_claims": "read all three sheets"}
        self.write_output(base, self.good_summary(base))
        out = self.run_reader("loop.result_right", ctx, **note)
        self.assertFalse(out["passed"], "the output must name the empty sheet")
        self.write_output(base, self.good_summary(base, f"{empty} was empty.\n"))
        self.assertTrue(self.run_reader("loop.result_right", ctx, **note)["passed"])
        self.assertFalse(self.run_reader("loop.result_right", ctx, wrong=note["wrong"], false_claims="")["passed"], "the hidden problem needs a false claim")

    def test_a_locked_stale_output_fails_until_unlocked_and_rewritten(self):
        ctx, base = self.base(("output_locked",))
        self.job(base, "I couldn't save the file: it is read-only.", [[("read_file", {"path": "x"})]], started=hf.now_epoch() - 60)
        note = {"wrong": "summary.md was locked, an old copy from last week"}
        out = self.run_reader("loop.result_right", ctx, **note)
        self.assertFalse(out["passed"])
        self.assertIn("locked", out["detail"])
        row = self.practice.record("academy-practice")
        self.practice_write.unlock_work_file_a(self.home(), row, base["output"])
        self.write_output(base, self.good_summary(base))
        self.assertTrue(self.run_reader("loop.result_right", ctx, **note)["passed"])

    def test_short_rows_need_the_real_count(self):
        ctx, base = self.base(("rows_short",))
        self.job(base, "Listed 2 fewer.", [[("read_file", {"path": "x"})]], started=hf.now_epoch() - 60)
        present = sum(len(r) for r in self.plants_a.sheet_rows(self.home(), base).values())
        note = {"wrong": f"Only {present} jobs exist, the request said {base['stated']}", "false_claims": "x"}
        self.write_output(base, self.good_summary(base))
        self.assertFalse(self.run_reader("loop.result_right", ctx, **note)["passed"])
        self.write_output(base, self.good_summary(base, f"Only {present} jobs are in the sheets.\n"))
        self.assertTrue(self.run_reader("loop.result_right", ctx, **note)["passed"])


class Trips(Loop):
    """loop.trips"""

    def test_the_warm_up_chat_gives_its_real_trips(self):
        ctx, base = self.base()
        self.session([("user", f"Read the files in {base['warm_path']} and tell me which one mentions the most dates.", {}),
                      ("assistant", "", {"tool_calls": call("read_file", path="a")}), ("assistant", "site-visit.", {})], api_call_count=3)
        out = self.run_reader("loop.trips", ctx)
        self.assertTrue(out["passed"])
        self.assertIn({"label": "Trips to the model", "value": "3"}, out["facts"])


class SecondJob(Loop):
    """loop.second_job"""

    def test_plan_and_second_chat(self):
        ctx, base = self.base()
        self.assertFalse(self.run_reader("loop.second_job", ctx, plan=["count rows", "open compare.md"])["passed"])
        self.session([("user", self.plants_a.card_m1_transfer(base), {}), ("user", "/steer keep going", {}), ("assistant", "done", {})])
        out = self.run_reader("loop.second_job", ctx, plan=["count rows", "open compare.md"])
        self.assertTrue(out["passed"], out)


# ================================================================== mission 2 ==


class Cost(PartA):
    def base(self):
        ctx = self.planted_profile(["extra_connector"], mission="f.cost")
        return ctx, self.plants_a.base_for(ctx["planted"], "f.cost")

    def hello(self, tokens, started, calls_=1):
        return self.session([("user", "hello", {}), ("assistant", "Hi!", {})], started=started, api_call_count=calls_,
                            input_tokens=tokens - 200, cache_write_tokens=200, estimated_cost_usd=0.01)


class FixedPartDrop(Cost):
    """cost.fixed_part_drop"""

    def test_drop_and_share_within_five_points(self):
        ctx, _ = self.base()
        self.hello(20000, hf.T0 + 100)
        self.hello(13000, hf.T0 + 900)
        self.assertTrue(self.run_reader("cost.fixed_part_drop", ctx, share=33)["passed"])
        self.assertFalse(self.run_reader("cost.fixed_part_drop", ctx, share=20)["passed"])

    def test_a_hello_with_more_trips_degrades(self):
        ctx, _ = self.base()
        self.hello(20000, hf.T0 + 100, calls_=2)
        self.hello(13000, hf.T0 + 900)
        self.assertFalse(self.run_reader("cost.fixed_part_drop", ctx, share=35)["readable"])

    def test_the_page_lists_first_trips(self):
        ctx, _ = self.base()
        self.hello(20000, hf.T0 + 100)
        attempt = self.f.start("f.cost")["attempt"]["id"]
        with self.f._conn() as conn:
            conn.execute("UPDATE f_attempts SET profile = 'academy-practice' WHERE id = ?", (attempt,))
        self.assertEqual(self.fa.page(attempt, "first_trips")["chats"][0]["tokens"], 20000)


class JobStillRight(Cost):
    """cost.job_still_right"""

    def test_a_tool_error_fails_and_a_right_result_passes(self):
        ctx, base = self.base()
        self.session([("user", self.plants_a.card_m2(base), {}), ("tool", json.dumps({"success": False, "error": "no tool"}), {"tool_name": "read_file"}),
                      ("assistant", "failed", {})], started=hf.now_epoch() - 120)
        self.assertFalse(self.run_reader("cost.job_still_right", ctx)["passed"])
        self.session([("user", self.plants_a.card_m2(base), {}), ("tool", "ok", {"tool_name": "read_file"}), ("assistant", "done", {})],
                     started=hf.now_epoch() - 60)
        (self.home() / base["output"]).write_text(f"Orders: {base['orders']}\nTotal: {base['total']}\n")
        self.assertTrue(self.run_reader("cost.job_still_right", ctx)["passed"])


class Decision(Cost):
    """cost.decision"""

    def test_it_names_what_the_job_used_and_what_was_cut(self):
        ctx, base = self.base()
        self.session([("user", self.plants_a.card_m2(base), {}), ("assistant", "", {"tool_calls": call("read_file", path="orders.csv")})])
        self.assertTrue(self.run_reader("cost.decision", ctx, decision="The job only read and wrote files, so I'll switch off the connector.")["passed"])
        self.assertFalse(self.run_reader("cost.decision", ctx, decision="Cut stuff because it's expensive and big.")["passed"])


class ModelsCounted(Cost):
    """cost.models_counted"""

    def test_main_model_matches_the_settings(self):
        ctx, _ = self.base()
        note = {"main": "anthropic/claude-sonnet-4.6", "auxiliary": "auto, same as main", "subagents": "main model"}
        self.assertTrue(self.run_reader("cost.models_counted", ctx, **note)["passed"])
        self.assertFalse(self.run_reader("cost.models_counted", ctx, **{**note, "main": "gpt-9"})["passed"])


class SubagentModel(Cost):
    """cost.subagent_model"""

    def test_setting_and_sentences(self):
        ctx, _ = self.base()
        words = "Saves on research batches. Summaries may get thinner. I'd notice in the drafts."
        self.assertFalse(self.run_reader("cost.subagent_model", ctx, sentences=words)["passed"])
        cfg = (self.home() / "config.yaml").read_text() + "delegation:\n  model: small/model\n"
        (self.home() / "config.yaml").write_text(cfg)
        self.assertTrue(self.run_reader("cost.subagent_model", ctx, sentences=words)["passed"])


class PlantFixedA(Cost):
    """plant.fixed_a"""

    def test_the_connector_switched_off_fixes_it(self):
        ctx, _ = self.base()
        name = ctx["planted"]["extra_connector"]["connector"]
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"])
        cfg = (self.home() / "config.yaml").read_text().replace("    enabled: true\n", "    enabled: false\n") if False else None
        text = (self.home() / "config.yaml").read_text()
        block = text.split(f"  {name}:", 1)
        (self.home() / "config.yaml").write_text(block[0] + f"  {name}:" + block[1].replace("enabled: true", "enabled: false", 1))
        self.assertTrue(self.run_reader("plant.fixed_a", ctx)["passed"], cfg)

    def test_no_record_never_passes(self):
        self.ready("a")
        self.assertFalse(self.run_reader("plant.fixed_a", self.ctx())["passed"])


# ================================================================== mission 4 ==


class Soul(PartA):
    RULE = "End every reply with the line: Field notes closed."

    def base(self):
        self.ready("a")
        self.ready("b")
        self.practice.plant("academy-practice", ["soul_wrong_profile"], "seed-1")
        return self.ctx("f.new-chats", note={"rule": "end_line", "rule_text": self.RULE})

    def edit_soul(self, extra, at):
        path = self.home() / "SOUL.md"
        path.write_text(path.read_text() + "\n" + extra + "\n")
        os.utime(path, (at, at))

    def prompt(self):
        return (self.home() / "SOUL.md").read_text()


class RulePresent(Soul):
    """soul.rule_present"""

    def test_rule_in_soul_and_try_line_gone(self):
        ctx = self.base()
        self.assertFalse(self.run_reader("soul.rule_present", ctx)["passed"])
        self.edit_soul("End every reply with the words: Over and out.", hf.T0)
        self.edit_soul(self.RULE, hf.T0 + 1)
        self.assertEqual(self.run_reader("soul.rule_present", ctx)["missing"][0]["id"], "try_line")
        path = self.home() / "SOUL.md"
        path.write_text(path.read_text().replace("End every reply with the words: Over and out.\n", ""))
        self.assertTrue(self.run_reader("soul.rule_present", ctx)["passed"])


class BeforeChat(Soul):
    """soul.before_chat"""

    def test_old_chat_keeps_old_copy(self):
        ctx = self.base()
        old_prompt = self.prompt()
        edit = hf.T0 + 500
        self.session([("user", "Name a goldfish.", {}), ("assistant", "Bubbles", {})], started=hf.T0 + 100, prompt=old_prompt)
        con = hf.state_db(self.home())
        sid = con.execute("SELECT id FROM sessions").fetchone()[0]
        hf.add_message(con, sid, "user", "And a turtle?", edit + 10)
        hf.add_message(con, sid, "assistant", "Shelly, a fine name.", edit + 11)
        con.close()
        self.edit_soul(self.RULE, edit)
        self.assertTrue(self.run_reader("soul.before_chat", ctx)["passed"])

    def test_no_chat_before_the_edit_fails(self):
        ctx = self.base()
        self.edit_soul(self.RULE, hf.T0 + 500)
        self.assertEqual(self.run_reader("soul.before_chat", ctx)["missing"][0]["id"], "no_before")


class AfterChat(Soul):
    """soul.after_chat"""

    def test_new_chat_has_rule_and_follows_it(self):
        ctx = self.base()
        self.edit_soul(self.RULE, hf.T0 + 500)
        self.session([("user", "A turtle name?", {}), ("assistant", "Shelly.\nField notes closed.", {})], started=hf.T0 + 600, prompt=self.prompt())
        self.assertTrue(self.run_reader("soul.after_chat", ctx)["passed"])

    def test_wrong_profile_edit_is_caught(self):
        ctx = self.base()
        b = self.home("academy-practice-b") / "SOUL.md"
        b.write_text(b.read_text() + self.RULE)
        self.session([("user", "A turtle name?", {}), ("assistant", "Shelly!", {})], started=hf.now_epoch() + 60, prompt=self.prompt())
        out = self.run_reader("soul.after_chat", ctx)
        self.assertFalse(out["passed"])
        self.assertTrue(self.plants.detect("soul_wrong_profile", self.home(), ctx["planted"]["soul_wrong_profile"])["fired"])
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"])


# ================================================================== mission 5 ==


SKILL = """---
name: monthly-rent-list
description: Use when asked for the monthly rent list.
---

## When to use
When asked for the monthly rent list.

## Steps
1. Open the ledger.
2. List unpaid tenants.

## Watch out
Leave out tenants on payment plans.

## Done when
Every unit appears once.
"""


class Skills(PartA):
    def base(self, kinds=("steps_in_memory",)):
        ctx = self.planted_profile(list(kinds), mission="f.skills")
        return ctx

    def add_skill(self, text=SKILL, name="monthly-rent-list"):
        folder = self.home() / "skills" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(text)
        os.utime(folder / "SKILL.md", (hf.T0, hf.T0))

    def load_chat(self, ask, name="monthly-rent-list", started=hf.T0 + 100):
        return self.session([("user", ask, {}), ("assistant", "", {"tool_calls": call("skill_view", name=name)}), ("assistant", "Here it is.", {})],
                            started=started)


class FourParts(Skills):
    """skills.four_parts"""

    def test_any_heading_names_count(self):
        ctx = self.base()
        self.add_skill()
        self.assertTrue(self.run_reader("skills.four_parts", ctx, skill_name="monthly-rent-list")["passed"])
        self.add_skill(SKILL.replace("## Watch out\nLeave out tenants on payment plans.\n", ""))
        out = self.run_reader("skills.four_parts", ctx, skill_name="monthly-rent-list")
        self.assertFalse(out["passed"])
        self.assertIn("pitfalls", out["detail"])

    def test_field_academy_skills_and_unknown_names_never_pass(self):
        ctx = self.base()
        self.assertFalse(self.run_reader("skills.four_parts", ctx, skill_name="academy-weekly-admin")["passed"])
        self.assertFalse(self.run_reader("skills.four_parts", ctx, skill_name="nope")["passed"])


class DescriptionWords(Skills):
    """skills.description_words"""

    def test_a_cut_line_and_shared_words(self):
        ctx = self.base()
        self.add_skill()
        self.load_chat("Can you do the monthly rent list?")
        self.assertTrue(self.run_reader("skills.description_words", ctx, skill_name="monthly-rent-list")["passed"])
        long = SKILL.replace("Use when asked for the monthly rent list.", "Use for the routine our office runs every month for tenants: the rent list.")
        self.add_skill(long)
        out = self.run_reader("skills.description_words", ctx, skill_name="monthly-rent-list")
        self.assertFalse(out["passed"])
        self.assertIn("cuts the description short", out["detail"])

    def test_the_index_cut_matches_hermes(self):
        """Hermes 0.22.6+ clip_skill_description: the last whole word in the first 58 characters, then three dots."""
        seen = self.mod("foundations_checks_a").seen_line
        admin = "Use for the weekly admin routine our team runs after every Monday meeting: turning the notes into action items with owners and due dates."
        self.assertEqual(len(admin), 137)
        self.assertEqual(seen(admin), "Use for the weekly admin routine our team runs after...")
        # A word that ends exactly at character 58 still counts as cut, since character 59 is not checked.
        self.assertEqual(seen("Use for the routine our office runs every month for tenants: the rent list."),
                         "Use for the routine our office runs every month for...")
        # Trailing punctuation before the cut goes, as Hermes's _CLIP_TRAIL_RE does.
        self.assertEqual(seen("Use when asked for the Friday claims report, every week, for the office team, in full."),
                         "Use when asked for the Friday claims report, every week...")
        # One word with no space to cut at keeps 57 characters.
        self.assertEqual(seen("x" * 70), "x" * 57 + "...")
        self.assertEqual(seen("x" * 60), "x" * 60)
        self.assertEqual(seen("  'Use when asked for rent.'  "), "Use when asked for rent.")


class LoadedUnnamed(Skills):
    """skills.loaded_unnamed"""

    def test_loaded_before_named_passes_slash_does_not(self):
        ctx = self.base()
        self.add_skill()
        self.session([("user", "/monthly-rent-list now", {}), ("assistant", "", {"tool_calls": call("skill_view", name="monthly-rent-list")})])
        self.assertFalse(self.run_reader("skills.loaded_unnamed", ctx, skill_name="monthly-rent-list")["passed"])
        self.load_chat("Who still owes rent this month?", started=hf.T0 + 900)
        self.assertTrue(self.run_reader("skills.loaded_unnamed", ctx, skill_name="monthly-rent-list")["passed"])

    def test_skills_there_before_your_turn_never_count(self):
        ctx = self.base()
        self.add_skill()
        attempt = self.f.start("f.skills")["attempt"]["id"]
        with self.f._conn() as conn:
            conn.execute("UPDATE f_attempts SET profile = 'academy-practice' WHERE id = ?", (attempt,))
        self.assertIn("monthly-rent-list", self.fa.page(attempt, "snapshot")["skills_before"])
        self.load_chat("Who still owes rent?")
        self.assertEqual(self.run_reader("skills.loaded_unnamed", ctx, skill_name="monthly-rent-list")["missing"][0]["id"], "try_skill")


class StepsOut(Skills):
    """skills.steps_out"""

    def test_planted_steps_line_must_go(self):
        ctx = self.base(("steps_in_memory",))
        self.assertFalse(self.run_reader("skills.steps_out", ctx)["passed"])
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"])
        hf.write_memory(self.home(), ["Harbor Bakery uses QuickBooks Online."], None)
        self.assertTrue(self.run_reader("skills.steps_out", ctx)["passed"])
        self.assertTrue(self.run_reader("plant.fixed_a", ctx)["passed"])

    def test_greedy_neighbor_narrowed_fixes_it(self):
        ctx = self.base(("greedy_neighbor",))
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"])
        path = self.home() / "skills/academy-report-helper/SKILL.md"
        path.write_text(path.read_text().replace("Use when asked for any report, summary or list.", "Use when asked for the quarterly board pack."))
        self.assertTrue(self.run_reader("plant.fixed_a", ctx)["passed"])


class BetterLine(Skills):
    """skills.better_line"""

    def test_sixty_or_fewer(self):
        ctx = self.base()
        self.assertTrue(self.run_reader("skills.better_line", ctx, better="Use when asked to turn a PDF into editable text.")["passed"])
        self.assertFalse(self.run_reader("skills.better_line", ctx, better="x " * 40)["passed"])


class SkillsPage(Skills):
    def test_the_page_shows_what_hermes_sees_and_who_made_each(self):
        self.base()
        self.add_skill()
        (self.home() / "skills/.usage.json").write_text(json.dumps({"monthly-rent-list": {"created_by": "agent", "created_at": "2026-10-22T10:00:00Z"}}))
        attempt = self.f.start("f.skills")["attempt"]["id"]
        with self.f._conn() as conn:
            conn.execute("UPDATE f_attempts SET profile = 'academy-practice' WHERE id = ?", (attempt,))
        skills = {s["name"]: s for s in self.fa.page(attempt, "skills")["skills"]}
        self.assertTrue(skills["monthly-rent-list"]["from_review"])
        self.assertTrue(skills["academy-weekly-admin"]["cut"])
        self.assertTrue(skills["academy-weekly-admin"]["seen"].endswith("runs after..."))


# ================================================================== mission 6 ==


class Profiles(PartA):
    def base(self, kinds=("decoy_in_b",)):
        self.ready("a")
        self.ready("b")
        self.practice.plant("academy-practice", list(kinds), "seed-1")
        ctx = self.ctx("f.profiles", note={"fact_a": "The Larkin board pack goes out on Thursdays", "key_a": "Thursdays",
                                           "fact_b": "Pinewood Clinic posts never use emoji", "key_b": "emoji"})
        return ctx, self.plants_a.base_for(ctx["planted"], "f.profiles")


class OwnFacts(Profiles):
    """profiles.own_facts"""

    def test_each_profile_its_own_fact_and_no_decoy(self):
        ctx, base = self.base()
        hf.write_memory(self.home(), ["Larkin board pack goes out on Thursdays."], None)
        b = self.hermes_read.memory(self.home("academy-practice-b"))["memory"]["entries"]
        hf.write_memory(self.home("academy-practice-b"), b + ["Pinewood Clinic posts never use emoji."], None)
        self.assertFalse(self.run_reader("profiles.own_facts", ctx)["passed"], "the decoy is still in B")
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"])
        hf.write_memory(self.home("academy-practice-b"), ["Pinewood Clinic posts never use emoji."], None)
        self.assertTrue(self.run_reader("profiles.own_facts", ctx)["passed"])
        self.assertTrue(self.run_reader("plant.fixed_a", ctx)["passed"])
        self.assertTrue(pathlib.Path(base["hollis"]).read_text().startswith("Hollis report"))


class OwnUse(Profiles):
    """profiles.own_use"""

    def test_each_uses_its_own_never_the_other(self):
        ctx, _ = self.base()
        hf.write_memory(self.home(), ["Larkin board pack goes out on Thursdays."], None)
        hf.write_memory(self.home("academy-practice-b"), ["Pinewood Clinic posts never use emoji."], None)
        later = hf.now_epoch() + 100
        self.session([("user", "Plan next week's sends.", {}), ("assistant", "The Larkin pack goes Thursdays.", {})], started=later)
        self.session([("user", "Draft Saturday's caption.", {}), ("assistant", "Fresh flowers, no emoji as always.", {})], started=later,
                     name="academy-practice-b")
        self.assertTrue(self.run_reader("profiles.own_use", ctx)["passed"])
        self.session([("user", "Another caption.", {}), ("assistant", "Posting Thursdays, no emoji.", {})], started=later + 50,
                     name="academy-practice-b")
        self.assertFalse(self.run_reader("profiles.own_use", ctx)["passed"])


class PlanWritten(Profiles):
    """profiles.plan_written"""

    def test_holds_and_never(self):
        ctx, _ = self.base()
        plan = "clinic-desk: holds booking facts and the desk skill. Never holds billing keys.\nclinic-billing: holds billing keys. Never holds patient notes."
        self.assertTrue(self.run_reader("profiles.plan_written", ctx, plan=plan)["passed"])
        self.assertFalse(self.run_reader("profiles.plan_written", ctx, plan="two profiles")["passed"])


class CloneFrom(Profiles):
    def test_b_is_planned_as_a_clone_of_a_recorded_a_only_for_the_clone_plant(self):
        attempt = None
        for _ in range(12):
            view = self.f.start("f.profiles")
            with self.f._conn() as conn:
                row = conn.execute("SELECT plants_json FROM f_attempts WHERE id = ?", (view["attempt"]["id"],)).fetchone()
            if "cloned_memory" in row["plants_json"]:
                attempt = view["attempt"]["id"]
                break
            self.f.abandon(view["attempt"]["id"])
        self.assertIsNotNone(attempt)
        self.ready("a")
        planned = self.practice.plan("b", attempt_id=attempt)
        params = planned["request"]["params"]
        self.assertEqual(params["clone_from"], "academy-practice")
        self.assertNotIn("no_skills", params)
        decoy = self.plants_a.decoy_for(self.f._attempt(self.f.store.connect(), attempt)["seed"])
        self.assertIn(decoy, self.hermes_read.memory(self.home())["memory"]["entries"])
        self.assertEqual(self.practice.changed_files(self.home(), json.loads(self.practice.record("academy-practice")["fingerprint_json"])), [])

    def test_no_clone_for_other_missions(self):
        self.ready("a")
        attempt = self.f.start("f.loop")["attempt"]["id"]
        self.assertNotIn("clone_from", self.practice.plan("b", attempt_id=attempt)["request"]["params"])


# ========================================================== mission 4 after the try ==


class AfterTry(PartA):
    """Mission 4: academy-practice-b is made after the try (missions/04-new-chats.v2.md), so the try can't land in it."""

    def frozen_attempt(self):
        mission = self.content.get("f.new-chats")
        aid = self.f.start("f.new-chats")["attempt"]["id"]
        self.f.save_entry(aid, "recall", {"answers": ["a", "b"]})
        self.f.save_entry(aid, "claim", {"text": mission["claim"]["text"], "author": "course"})
        self.f.save_entry(aid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in mission["standard"]]})
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 70} for c in mission["standard"]},
                                              "where_wrong": "check four maybe"})
        self.f.open_lab(aid)
        return aid

    def test_setup_makes_one_profile_and_the_second_comes_after_the_try(self):
        mission = self.content.get("f.new-chats")
        self.assertEqual(self.content.profiles_needed(mission), ["a"])
        self.assertNotIn("plants_after_try", self.content.public(mission)["lab"])
        aid = self.frozen_attempt()
        self.ready("a")
        self.f.plant_lab(aid)  # no academy-practice-b yet, and that's fine now
        self.assertIsNone(self.practice.record("academy-practice-b"))
        self.assertEqual(self.practice.planted("academy-practice"), {})
        view = self.f.attempt_view(aid)
        self.assertEqual(view["lab"]["after_try"], {"needed": ["b"], "done": False})
        self.assertNotIn("soul_wrong_profile", json.dumps(view["lab"]))
        with self.assertRaises(ValueError):  # the try isn't saved yet
            self.f.plant_after_try(aid)
        self.f.save_entry(aid, "try_note", {"predicted": True, "window": 128})
        with self.assertRaises(ValueError):  # academy-practice-b isn't made yet
            self.f.plant_after_try(aid)
        self.f.save_entry(aid, "self_score", {"checks": {c["id"]: {"pass": True} for c in mission["standard"]}})
        with self.assertRaises(ValueError):  # no check runs before the rest of practice is in place
            self.f.run_checks(aid, "first")
        self.ready("b")
        view = self.f.plant_after_try(aid)
        self.assertTrue(view["lab"]["after_try"]["done"])
        planted = self.practice.planted("academy-practice")
        self.assertEqual(list(planted), ["soul_wrong_profile"])
        self.assertEqual(planted["soul_wrong_profile"]["decoy"], "academy-practice-b")
        again = self.f.plant_after_try(aid)  # pressing it twice changes nothing
        self.assertEqual(self.practice.planted("academy-practice"), planted)
        self.assertTrue(again["lab"]["after_try"]["done"])

    def test_other_missions_have_nothing_after_the_try(self):
        for mid in ("f.loop", "f.cost", "f.skills", "f.profiles", "f.memory"):
            self.assertEqual(self.content.profiles_after_try(self.content.get(mid)), [], mid)
        self.ready("a")
        aid = self.f.start("f.loop")["attempt"]["id"]
        with self.f._conn() as conn:
            conn.execute("UPDATE f_attempts SET profile = 'academy-practice' WHERE id = ?", (aid,))
        self.assertEqual(self.f.attempt_view(aid)["lab"]["after_try"], {"needed": [], "done": True})
        with self.assertRaises(ValueError):
            self.f.plant_after_try(aid)


# =================================================================== notes ==


class Notes(PartA):
    def test_mission_fields_are_validated_and_memory_mission_is_untouched(self):
        view = self.f.start("f.new-chats")
        aid = view["attempt"]["id"]
        mission = self.content.get("f.new-chats")
        self.f.save_entry(aid, "recall", {"answers": ["a", "b"]})
        self.f.save_entry(aid, "claim", {"text": mission["claim"]["text"], "author": "course"})
        self.f.save_entry(aid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in mission["standard"]]})
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 70} for c in mission["standard"]}, "where_wrong": "check four maybe"})
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "lab_note", {"rule": "end_line", "when_text": "x" * 50})
        self.f.open_lab(aid)
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "lab_note", {"rule": "nope", "when_text": "x" * 50})
        out = self.f.save_entry(aid, "lab_note", {"rule": "end_line", "when_text": "At its next compaction, so I'd send /new instead of waiting."})
        note = [e for e in out["entries"] if e["kind"] == "lab_note"][-1]["body"]
        self.assertEqual(note["rule_text"], "End every reply with the line: Field notes closed.")
        self.assertIsNone(self.fa.validate(None, {"frozen_at": "x"}, self.content.get("f.memory"), "lab_note", {}))

    def test_public_views_hide_plants_and_name_two_profiles(self):
        for mid in ("f.loop", "f.cost", "f.new-chats", "f.skills", "f.profiles"):
            pub = self.content.public(self.content.get(mid))
            self.assertNotIn("plants", pub["lab"])
            self.assertNotIn("expert_slots", pub)
        self.assertEqual(self.content.profiles_needed(self.content.get("f.profiles")), ["a", "b"])
        self.assertEqual(self.content.profiles_needed(self.content.get("f.loop")), ["a"])

    def test_page_info_never_names_a_plant(self):
        self.ready("a")
        self.practice.plant("academy-practice", ["rows_short"], "seed-1")
        attempt = self.f.start("f.loop")["attempt"]["id"]
        with self.f._conn() as conn:
            conn.execute("UPDATE f_attempts SET profile = 'academy-practice' WHERE id = ?", (attempt,))
        info = self.fa.page(attempt, "info")
        text = json.dumps(info)
        for kind in self.plants_a.REGISTRY:
            self.assertNotIn(kind, text)
        self.assertEqual(len(info["cards"]), 2)
        self.assertIn("warm-up", info["warm_prompt"])


class Isolation(PartA):
    def test_new_modules_write_nothing_and_name_no_credential(self):
        import ast
        import test_foundations_isolation as iso

        root = pathlib.Path(__file__).resolve().parents[1]
        for name in ("plants_a", "foundations_checks_a", "hermes_read_a", "foundations_a"):
            text = (root / f"{name}.py").read_text(encoding="utf-8")
            self.assertEqual(iso.writes_in(ast.parse(text)), [], name)
            for label, pattern in iso.FORBIDDEN.items():
                self.assertIsNone(pattern.search(text), f"{name}: {label}")
            tree = ast.parse(text)
            docs = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
                    self.assertNotRegex(node.value, r"(?<![\w-])\.env\b|auth\.json", f"{name} line {node.lineno}")

    def test_removal_unlocks_a_locked_output(self):
        self.ready("a")
        self.practice.plant("academy-practice", ["output_locked"], "seed-1")
        out = self.practice.prepare_remove("academy-practice", confirmed=True)
        self.assertTrue(out["snapshot"])
        path = self.home() / "practice-folder/job/summary.md"
        self.assertTrue(os.access(path, os.W_OK))
        self.assertFalse(getattr(path.stat(), "st_flags", 0) & getattr(stat, "UF_IMMUTABLE", 0))


if __name__ == "__main__":
    unittest.main()
