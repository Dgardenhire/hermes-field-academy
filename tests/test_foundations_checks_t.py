"""Fixture tests for the teaching missions' live checks and planted problems (Guide trail): set Hermes up for someone,
write them a walkthrough, judge their Field Record. One class per reader id, the class docstring is the id."""

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
from test_foundations_checks_c import call, toolsets_config  # noqa: E402
from test_scrub import load  # noqa: E402

T0 = hf.T0
PERSON = {"name": "Marisol Vega", "first": "Marisol", "work": "a bike repair shop", "word": "bike",
          "fact": "The shop closes at 5 pm on Saturdays", "fact_words": ["saturday", "5"],
          "never": "Never email a customer without asking Marisol first", "never_words": ["email", "ask"]}


class Case(unittest.TestCase):
    def setUp(self):
        self.c = load("foundations_checks")
        self.pt = load("plants_t")
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.home = hf.build_home(self.tmp / "profiles" / "academy-practice")
        self.folder = hb.folder(self.home)
        self.ctx = {"home": self.home, "note": {}, "planted": {},
                    "setup": {"folder": str(self.folder.resolve()), "person": PERSON, "skill": self.pt.SKILL, "output": self.pt.OUTPUT},
                    "row": {"plan": {"folder": str(self.folder.resolve())}, "planted_at": hb.iso(T0)}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_reader(self, reader_id, **ctx):
        return self.c.run(reader_id, {**self.ctx, **ctx})

    def chat(self, started, rows):
        con = hf.state_db(self.home)
        sid = hf.add_session(con, started_at=started)
        for n, (role, content, tool, calls) in enumerate(rows, start=1):
            extra = {"tool_calls": calls} if calls else {}
            hf.add_message(con, sid, role, content, started + n, tool_name=tool, **extra)
        con.close()
        return sid

    def write(self, rel, text, epoch=None):
        path = self.folder / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if epoch is not None:
            hb.touch_back(path, epoch)


# ------------------------------------------------------------------ profile --


class SoulForThem(Case):
    """teach.soul_for_them"""

    def test_name_and_rule_pass(self):
        (self.home / "SOUL.md").write_text("You work for Marisol at her bike repair shop.\nNever email a customer without asking Marisol first.\n")
        self.assertTrue(self.run_reader("teach.soul_for_them")["passed"])

    def test_missing_rule_or_name_fails(self):
        (self.home / "SOUL.md").write_text("You work for Marisol.\n")
        self.assertEqual(self.run_reader("teach.soul_for_them")["missing"][0]["id"], "rule")
        (self.home / "SOUL.md").write_text("Never email a customer without asking first.\n")
        self.assertEqual(self.run_reader("teach.soul_for_them")["missing"][0]["id"], "who")


class MemoryForThem(Case):
    """teach.memory_for_them"""

    def test_the_fact_in_memory_passes(self):
        hf.write_memory(self.home, memory=["The shop closes at 5 pm on Saturdays."])
        self.assertTrue(self.run_reader("teach.memory_for_them")["passed"])

    def test_no_fact_fails(self):
        hf.write_memory(self.home, memory=["Something else."])
        self.assertEqual(self.run_reader("teach.memory_for_them")["missing"][0]["id"], "no_fact")


class SafeForThem(Case):
    """teach.safe_for_them"""

    def test_approvals_on_and_terminal_off_passes(self):
        toolsets_config(self.home, cli=["file", "memory"])
        self.assertTrue(self.run_reader("teach.safe_for_them")["passed"])

    def test_terminal_on_fails(self):
        self.assertEqual(self.run_reader("teach.safe_for_them")["missing"][0]["id"], "terminal")

    def test_approvals_off_fails(self):
        toolsets_config(self.home, cli=["file"])
        text = (self.home / "config.yaml").read_text().replace("mode: manual", "mode: 'off'")
        (self.home / "config.yaml").write_text(text)
        self.assertEqual(self.run_reader("teach.safe_for_them")["missing"][0]["id"], "approvals")


class FirstChatKnows(Case):
    """teach.first_chat_knows"""

    def test_a_reply_that_names_them_unprompted_passes(self):
        (self.home / "SOUL.md").write_text("You work for Marisol.\n")
        hb.touch_back(self.home / "SOUL.md", T0)
        hb.touch_back(self.home / "memories" / "MEMORY.md", T0)
        self.chat(T0 + 50, [("user", "Who do you work for, and what should you never do?", None, None),
                            ("assistant", "I work for Marisol at the bike shop.", None, None)])
        self.assertTrue(self.run_reader("teach.first_chat_knows")["passed"])

    def test_a_hint_in_the_message_does_not_count(self):
        (self.home / "SOUL.md").write_text("You work for Marisol.\n")
        hb.touch_back(self.home / "SOUL.md", T0)
        hb.touch_back(self.home / "memories" / "MEMORY.md", T0)
        self.chat(T0 + 50, [("user", "Do you work for Marisol?", None, None), ("assistant", "Yes, Marisol.", None, None)])
        self.assertEqual(self.run_reader("teach.first_chat_knows")["missing"][0]["id"], "no_chat")


class ProfileReading(Case):
    """teach.profile_reading"""

    def test_no_and_no_passes(self):
        self.assertTrue(self.run_reader("teach.profile_reading", note={"t_knows": "no", "t_asks": "no", "t_change": "Rule into SOUL.md, approvals on."})["passed"])

    def test_yes_fails(self):
        out = self.run_reader("teach.profile_reading", note={"t_knows": "yes", "t_asks": "no", "t_change": "Rule into SOUL.md, approvals on."})
        self.assertEqual(out["missing"][0]["id"], "knows")


# -------------------------------------------------------------- walkthrough --


class Walk(Case):
    def skill(self):
        path = self.home / "skills" / self.pt.SKILL / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.pt.skill_text(PERSON))

    def good(self, epoch=T0 + 10):
        self.write("walkthrough.md", f"1. In academy-practice, start a new chat.\n2. Type: run the {self.pt.SKILL} skill.\n"
                                     f"3. Open {self.pt.OUTPUT} in the practice folder and check there's one line per order.\n", epoch)


class NamesReal(Walk):
    """walkthrough.names_real"""

    def test_the_real_skill_passes(self):
        self.skill()
        self.good()
        self.assertTrue(self.run_reader("walkthrough.names_real")["passed"])

    def test_a_ghost_skill_or_none_fails(self):
        self.skill()
        self.write("walkthrough.md", "1. Type: run academy-orders.\n")
        self.assertEqual(self.run_reader("walkthrough.names_real")["missing"][0]["id"], "ghost")
        self.write("walkthrough.md", "1. Use the usual skill.\n")
        self.assertEqual(self.run_reader("walkthrough.names_real")["missing"][0]["id"], "unnamed")
        (self.folder / "walkthrough.md").unlink()
        self.assertEqual(self.run_reader("walkthrough.names_real")["missing"][0]["id"], "none")


class HasCheck(Walk):
    """walkthrough.has_check"""

    def test_a_check_step_passes_and_none_fails(self):
        self.good()
        self.assertTrue(self.run_reader("walkthrough.has_check")["passed"])
        self.write("walkthrough.md", "1. Run the skill. You're done.\n")
        self.assertEqual(self.run_reader("walkthrough.has_check")["missing"][0]["id"], "no_check")


class Tested(Walk):
    """walkthrough.tested"""

    def test_a_chat_after_it_that_used_the_skill_and_wrote_the_result_passes(self):
        self.good(T0 + 10)
        self.chat(T0 + 20, [("user", f"run the {self.pt.SKILL} skill", None, None)])
        self.write(self.pt.OUTPUT, "order 1\norder 2\n", T0 + 30)
        self.assertTrue(self.run_reader("walkthrough.tested")["passed"])

    def test_a_chat_before_it_does_not_count(self):
        self.chat(T0 + 5, [("user", f"run the {self.pt.SKILL} skill", None, None)])
        self.good(T0 + 10)
        self.write(self.pt.OUTPUT, "order 1\n", T0 + 30)
        self.assertEqual(self.run_reader("walkthrough.tested")["missing"][0]["id"], "untested")


class WalkReading(Case):
    """walkthrough.reading"""

    def test_no_and_no_passes(self):
        self.assertTrue(self.run_reader("walkthrough.reading", note={"t_stranger": "no", "t_done": "no", "t_change": "Name the skill; end with a check."})["passed"])


class WalkPlants(Walk):
    def test_stale_name_and_unsafe_tip(self):
        verify = self.pt.REGISTRY["stale_skill_name"]["verify"]
        self.write("walkthrough.md", "2. Type: run the weekly-orders skill.\n")
        self.assertFalse(verify(self.home, {"stale": "weekly-orders"}, "")["fixed"])
        self.good()
        self.assertTrue(verify(self.home, {"stale": "weekly-orders"}, "")["fixed"])
        unsafe = self.pt.REGISTRY["unsafe_tip"]["verify"]
        self.write("walkthrough.md", "5. If Hermes asks permission too often, just say yes to every card without reading it.\n")
        self.assertFalse(unsafe(self.home, {}, "")["fixed"])
        self.write("walkthrough.md", "5. Never say yes to a card without reading it. Yes only if it matches the job.\n")
        self.assertTrue(unsafe(self.home, {}, "")["fixed"])


# ------------------------------------------------------------------ review --


class Review(Case):
    def record(self, case_text=""):
        body = json.loads(self.pt.TEMPLATE.read_text())
        body["scope"]["holder"]["name"] = "Jun Park"
        if case_text:
            body["case"] = {"text": case_text, "checked_by": "you wrote it", "note": ""}
        files = self.pt.record_files(body)
        for rel, text in files.items():
            self.write(f"{self.pt.RECORD_DIR}/{rel}", text)
        number = json.loads(files["record.json"])["number"]
        self.ctx["setup"] = {**self.ctx["setup"], "holder": "Jun Park", "number": number}
        return number


class RanCheck(Review):
    """review.ran_check"""

    def test_a_shasum_call_on_the_folder_passes(self):
        self.chat(T0 + 10, [("assistant", "", None, call("terminal", command="cd their-record && shasum -a 256 -c MANIFEST.sha256"))])
        self.assertTrue(self.run_reader("review.ran_check")["passed"])

    def test_no_call_fails(self):
        self.assertEqual(self.run_reader("review.ran_check")["missing"][0]["id"], "not_run")


class Judged(Review):
    """review.judged"""

    def test_number_and_how_it_passed_pass(self):
        number = self.record()
        self.write("review.md", f"Record {number}. Jun, your memory mission passed after a fix: 1 of 4 first, 4 of 4 after.\n")
        self.assertTrue(self.run_reader("review.judged")["passed"])

    def test_no_number_fails(self):
        self.record()
        self.write("review.md", "Jun, it passed after a fix.\n")
        self.assertEqual(self.run_reader("review.judged")["missing"][0]["id"], "number")


class Question(Review):
    """review.question"""

    def test_a_named_question_passes(self):
        self.record()
        self.write("review.md", "Jun, can you walk me through the fix?\n")
        self.assertTrue(self.run_reader("review.question")["passed"])

    def test_no_question_fails(self):
        self.record()
        self.write("review.md", "Jun, it looks fine.\n")
        self.assertEqual(self.run_reader("review.question")["missing"][0]["id"], "no_question")


class ReviewReading(Case):
    """review.reading"""

    def test_yes_no_passes(self):
        self.assertTrue(self.run_reader("review.reading", note={"t_unchanged": "yes", "t_true": "no", "t_change": "A live run of one mission."})["passed"])


class ReviewPlants(Review):
    def test_the_folder_checks_clean_until_an_excerpt_is_edited(self):
        self.record()
        self.assertEqual(self.pt.mismatched(self.home), [])
        self.write(f"{self.pt.RECORD_DIR}/{self.pt.EDIT_FILE}", self.pt.EDIT_TEXT)
        self.assertEqual(self.pt.mismatched(self.home), [self.pt.EDIT_FILE])
        verify = self.pt.REGISTRY["edited_excerpt"]["verify"]
        self.write("review.md", "Jun, all good.\n")
        self.assertFalse(verify(self.home, {"file": self.pt.EDIT_FILE}, "")["fixed"])
        self.write("review.md", "Jun, 01-tool-result.txt failed its fingerprint check.\n")
        self.assertTrue(verify(self.home, {"file": self.pt.EDIT_FILE}, "")["fixed"])

    def test_an_overclaim_keeps_the_folder_clean_and_needs_naming(self):
        self.record(case_text=self.pt.OVERCLAIM)
        self.assertEqual(self.pt.mismatched(self.home), [])
        verify = self.pt.REGISTRY["overclaim"]["verify"]
        self.write("review.md", "Jun, all good.\n")
        self.assertFalse(verify(self.home, {}, "")["fixed"])
        self.write("review.md", "Jun, your case says first time, but the record shows it passed after a fix.\n")
        self.assertTrue(verify(self.home, {}, "")["fixed"])


if __name__ == "__main__":
    unittest.main()
