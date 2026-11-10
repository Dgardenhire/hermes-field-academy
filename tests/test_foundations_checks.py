"""Fixture tests for every Foundations live-check reader (scripts/check_foundations.py requires one per reader id)."""

from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from test_scrub import load  # noqa: E402

FACT = "Harbor Bakery uses QuickBooks Online"


def memory_call(fact):
    return json.dumps([{"function": {"name": "memory", "arguments": json.dumps({"action": "add", "target": "memory", "content": fact})}}])


class ReaderCase(unittest.TestCase):
    def setUp(self):
        self.c = load("foundations_checks")
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.home = hf.build_home(self.tmp / "profiles" / "academy-practice")
        self.ctx = {"home": self.home, "note": {"fact": FACT, "key_term": "QuickBooks", "procedure_term": "invoice"}, "planted": {}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_reader(self, reader_id, **ctx):
        return self.c.run(reader_id, {**self.ctx, **ctx})


class MemoryLine(ReaderCase):
    """memory.line_matching"""

    def test_a_reworded_line_still_counts(self):
        out = self.run_reader("memory.line_matching")
        self.assertTrue(out["passed"])
        self.assertEqual(out["evidence"][0][1], "memories/MEMORY.md")

    def test_a_missing_fact_fails_and_a_long_line_is_named(self):
        hf.write_memory(self.home, ["Something else entirely."], None)
        self.assertFalse(self.run_reader("memory.line_matching")["passed"])
        hf.write_memory(self.home, [FACT + ". " + "x" * 400], None)
        out = self.run_reader("memory.line_matching")
        self.assertFalse(out["passed"])
        self.assertIn("characters", out["detail"])

    def test_no_stated_fact_never_passes(self):
        out = self.run_reader("memory.line_matching", note={})
        self.assertFalse(out["passed"])
        self.assertFalse(out["readable"])


class UserLine(ReaderCase):
    """memory.user_line"""

    def test_user_md_specifically(self):
        note = {"fact": "Ada prefers short answers", "key_term": "short"}
        self.assertTrue(self.run_reader("memory.user_line", note=note)["passed"])
        hf.write_memory(self.home, ["Ada prefers short answers."], [])
        out = self.run_reader("memory.user_line", note=note)
        self.assertFalse(out["passed"])
        self.assertEqual(out["missing"][0]["id"], "wrong_file")


class UsedBeforeSaid(ReaderCase):
    """sessions.used_before_said"""

    def save_call(self, at=hf.T0 + 2):
        con = hf.state_db(self.home)
        sid = hf.add_session(con, started_at=at - 1)
        hf.add_message(con, sid, "user", "Save to memory: " + FACT, at - 0.5)
        hf.add_message(con, sid, "assistant", "", at, tool_calls=memory_call(FACT))
        con.close()

    def new_chat(self, first_user, first_assistant, started=hf.T0 + 500):
        con = hf.state_db(self.home)
        sid = hf.add_session(con, started_at=started)
        hf.add_message(con, sid, "user", first_user, started + 1)
        hf.add_message(con, sid, "assistant", first_assistant, started + 2)
        con.close()

    def test_a_new_chat_that_uses_the_fact_unprompted_passes(self):
        self.save_call()
        self.new_chat("Draft this month's reconciliation checklist for Harbor Bakery.", "1. Export the bank feed from QuickBooks Online.")
        out = self.run_reader("sessions.used_before_said")
        self.assertTrue(out["passed"], out)
        self.assertIn("QuickBooks", out["evidence"][0][2])

    def test_a_chat_where_the_learner_said_it_first_fails(self):
        self.save_call()
        self.new_chat("What does Harbor Bakery use, QuickBooks?", "Yes, QuickBooks Online.")
        self.assertFalse(self.run_reader("sessions.used_before_said")["passed"])

    def test_a_chat_from_before_the_save_does_not_count(self):
        self.new_chat("Checklist for Harbor Bakery", "Export from QuickBooks Online.", started=hf.T0 - 500)
        self.save_call()
        out = self.run_reader("sessions.used_before_said")
        self.assertFalse(out["passed"])
        self.assertIn("/new", out["detail"])

    def test_without_a_key_term_it_cannot_judge(self):
        self.assertFalse(self.run_reader("sessions.used_before_said", note={"fact": FACT})["readable"])


class PendingCleared(ReaderCase):
    """pending.cleared"""

    def test_waiting_saves_fail_and_an_empty_queue_passes(self):
        self.assertTrue(self.run_reader("pending.cleared")["passed"])
        hf.stage_pending(self.home, content=FACT)
        out = self.run_reader("pending.cleared")
        self.assertFalse(out["passed"])
        self.assertTrue(out["evidence"])


class PlantFixed(ReaderCase):
    """plant.fixed"""

    def test_it_judges_every_planted_kind(self):
        planted = {"write_approval": {"key": "memory.write_approval", "value": True}}
        hf.write_config(self.home, hf.CONFIG.replace("  write_approval: false\n  memory_char_limit", "  write_approval: true\n  memory_char_limit"))
        hf.stage_pending(self.home, content="Ada uses Xero")
        out = self.run_reader("plant.fixed", planted=planted, note={"fact": "Ada uses Xero for the shop"})
        self.assertFalse(out["passed"])
        self.assertEqual(out["missing"][0]["id"], "plant:write_approval")
        for p in (self.home / "pending" / "memory").glob("*.json"):
            p.unlink()
        hf.write_memory(self.home, ["Ada uses Xero for the shop."], None)
        self.assertTrue(self.run_reader("plant.fixed", planted=planted, note={"fact": "Ada uses Xero for the shop"})["passed"])

    def test_no_record_of_a_plant_never_passes(self):
        self.assertFalse(self.run_reader("plant.fixed")["passed"])


class ProcedureNotMemory(ReaderCase):
    """skills.procedure_not_memory"""

    def test_a_skill_and_no_copy_in_memory_passes(self):
        self.assertTrue(self.run_reader("skills.procedure_not_memory")["passed"])

    def test_steps_left_in_memory_fail(self):
        hf.write_memory(self.home, ["Weekly invoice: 1. export the hours 2. build the invoice 3. send it by Friday."], None)
        out = self.run_reader("skills.procedure_not_memory")
        self.assertFalse(out["passed"])
        self.assertEqual(out["missing"][0]["id"], "in_memory")

    def test_no_skill_fails(self):
        shutil.rmtree(self.home / "skills")
        self.assertEqual(self.run_reader("skills.procedure_not_memory")["missing"][0]["id"], "no_skill")


class Registry(ReaderCase):
    def test_every_reader_has_a_test_class_here(self):
        text = "\n".join(p.read_text(encoding="utf-8") for p in sorted(pathlib.Path(__file__).parent.glob("test_*.py")))
        for reader_id in self.c.READERS:
            self.assertIn(f'"""{reader_id}"""', text)

    def test_an_unknown_reader_never_passes(self):
        self.assertFalse(self.run_reader("nope")["passed"])


if __name__ == "__main__":
    unittest.main()


class NoSecretInEvidence(ReaderCase):
    """Every excerpt goes through one scrubbing choke point, whatever reader made it."""

    def assert_clean(self, out, secret):
        self.assertNotIn(secret, json.dumps(out))
        for item in out["evidence"]:
            self.assertLessEqual(len(item[2]), 300)

    def test_a_token_in_a_memory_line_a_chat_and_a_detector_never_reaches_an_outcome(self):
        secret = hf.fake_key()
        hf.write_memory(self.home, [f"{FACT} key {secret}"], [f"Ada prefers short answers {secret}"])
        self.assert_clean(self.run_reader("memory.line_matching"), secret)
        self.assert_clean(self.run_reader("memory.user_line", note={"fact": "Ada prefers short answers", "key_term": "short"}), secret)
        con = hf.state_db(self.home)
        sid = hf.add_session(con, started_at=hf.T0 + 2)
        hf.add_message(con, sid, "assistant", "", hf.T0 + 3, tool_calls=memory_call(FACT))
        sid2 = hf.add_session(con, started_at=hf.T0 + 500)
        hf.add_message(con, sid2, "user", "Checklist for Harbor Bakery", hf.T0 + 501)
        hf.add_message(con, sid2, "assistant", f"Export from QuickBooks Online with {secret}", hf.T0 + 502)
        hf.add_message(con, sid2, "tool", json.dumps({"success": False, "error": f"would exceed the limit {secret}"}), hf.T0 + 503, tool_name="memory")
        con.close()
        used = self.run_reader("sessions.used_before_said")
        self.assertTrue(used["passed"])
        self.assert_clean(used, secret)
        planted = {"memory_full": {"limit": 2200}}
        out = self.run_reader("plant.fixed", planted=planted)
        self.assertTrue(out["evidence"], "the detector's evidence came through")
        self.assert_clean(out, secret)

    def test_make_evidence_is_the_only_shape(self):
        item = self.c.make_evidence("memory", "memories/MEMORY.md", "word " * 200 + hf.fake_key())
        self.assertNotIn(hf.fake_key(), self.c.make_evidence("m", "r", "a " + hf.fake_key())[2])
        self.assertEqual(len(item[2]), 300)


class SeedKept(ReaderCase):
    """memory.seed_kept"""

    SEED = {"notes": ["Shift plans use 24-hour times, like 14:00, never 2 pm.", "Weekly ops summary goes to the ops channel as five bullets.",
                      "Supplier orders are placed on Tuesdays before noon."],
            "key": ["Shift plans use 24-hour times, like 14:00, never 2 pm.", "Weekly ops summary goes to the ops channel as five bullets."]}

    def test_kept_or_shortened_key_notes_pass(self):
        hf.write_memory(self.home, self.SEED["notes"] + [FACT], None)
        self.assertTrue(self.run_reader("memory.seed_kept", seed_notes=self.SEED)["passed"])
        hf.write_memory(self.home, ["Shift plans use 24-hour times like 14:00.", "Weekly ops summary: ops channel, five bullets.", FACT], None)
        out = self.run_reader("memory.seed_kept", seed_notes=self.SEED)
        self.assertTrue(out["passed"], out)
        self.assertIn({"label": "Gone", "value": "1"}, out["facts"])

    def test_a_cut_key_note_fails_and_names_it(self):
        hf.write_memory(self.home, self.SEED["notes"][1:] + [FACT], None)
        out = self.run_reader("memory.seed_kept", seed_notes=self.SEED)
        self.assertFalse(out["passed"])
        self.assertIn("24-hour", out["detail"])
        self.assertEqual(out["missing"][0]["id"], "note_gone")

    def test_saying_which_note_went_and_why_counts(self):
        hf.write_memory(self.home, self.SEED["notes"][1:] + [FACT], None)
        short = {**self.ctx["note"], "removed_ok": "The shift plans note."}
        self.assertFalse(self.run_reader("memory.seed_kept", seed_notes=self.SEED, note=short)["passed"], "a reason is needed")
        why = {**self.ctx["note"], "removed_ok": "Hermes cut the shift plans 24-hour times note. We no longer make shift plans here, so it was stale."}
        self.assertTrue(self.run_reader("memory.seed_kept", seed_notes=self.SEED, note=why)["passed"])

    def test_no_record_of_the_seed_never_passes(self):
        self.assertFalse(self.run_reader("memory.seed_kept")["readable"])


class OneOffDecision(ReaderCase):
    """memory.one_off_decision"""

    def note(self, saved):
        return {**self.ctx["note"], "one_off": "The printer quote came in at noon today", "one_off_saved": saved, "one_off_why": "One afternoon only."}

    def test_memory_has_to_match_the_call(self):
        self.assertTrue(self.run_reader("memory.one_off_decision", note=self.note(False))["passed"])
        self.assertEqual(self.run_reader("memory.one_off_decision", note=self.note(True))["missing"][0]["id"], "not_saved")
        hf.write_memory(self.home, [FACT, "The printer quote came in at noon today."], None)
        self.assertTrue(self.run_reader("memory.one_off_decision", note=self.note(True))["passed"])
        self.assertEqual(self.run_reader("memory.one_off_decision", note=self.note(False))["missing"][0]["id"], "saved_anyway")

    def test_no_call_written_never_passes(self):
        self.assertFalse(self.run_reader("memory.one_off_decision")["readable"])

