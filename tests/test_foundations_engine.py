"""The Foundations loop engine: attempts, the freeze, append-only entries, seeded rotating plants, live checks with
hidden criteria, the page's sample, and four-level rubric grading through the learner's own Hermes."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402
from test_scrub import load  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTENT = pathlib.Path(__file__).resolve().parent / "data" / "foundations"
FACT = "Harbor Bakery uses QuickBooks Online"
MID = "f.fixture"
IDS = ["s1", "s2", "s3", "s4"]
STANDARD = [{"id": "s1", "text": "The fact is in the memory file of the profile you used, as one short line."},
            {"id": "s2", "text": "A brand-new chat uses the fact without you mentioning it."},
            {"id": "s3", "text": "You can say which kind of memory holds it, and why that kind."},
            {"id": "s4", "text": "If something in your setup stops the save, you find it and say how."}]
CLAIM = "I can get one fact into Hermes's memory and prove, from the memory file and a brand-new chat, that it stuck."
ANSWER = ("On Telegram one conversation is one chat that can run for weeks, so the memory saved yesterday was never read "
          "into it: start a new chat first. Then check the memory file of the profile the bot runs as, because each "
          "profile has its own memory. Then look for saves waiting for approval with /memory pending, which is what I hit today.")


class EngineCase(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.f = self.mod("foundations")
        self.f.CONTENT_DIR = CONTENT
        self.content = self.mod("foundations_content")
        self.content.clear_cache()

    def salt_for(self, wanted, level="beginner"):
        """Set the install salt to one whose first draw is ``wanted``."""
        mission = self.content.get(MID, CONTENT)
        for n in range(500):
            salt = f"{n:032x}"
            seed = self.f.seed_for(salt, MID, 1)
            if self.f.choose_plants(mission["lab"]["plants"], mission["lab"]["plants_at"][level], [], seed) == wanted:
                with self.store.connect() as conn:
                    self.store.meta_set(conn, "f_salt", salt)
                return
        self.fail("no salt found")

    def plants_of(self, attempt_id):
        with self.store.connect() as conn:
            return json.loads(conn.execute("SELECT plants_json FROM f_attempts WHERE id = ?", (attempt_id,)).fetchone()[0])

    def frozen(self, level="beginner", plants=None):
        if plants is not None:
            self.salt_for(plants, level)
        view = self.f.start(MID, level)
        aid = view["attempt"]["id"]
        self.f.save_entry(aid, "recall", {"answers": ["It used a tool I didn't expect.", "Trusting the reply."]})
        self.f.save_entry(aid, "claim", {"text": CLAIM, "author": "course"})
        self.f.save_entry(aid, "standard", {"checks": STANDARD})
        self.f.save_entry(aid, "prediction", {"checks": {i: {"expect_pass": True, "confidence": 80} for i in IDS},
                                              "where_wrong": "The new chat might not use the fact."})
        self.f.open_lab(aid)
        return aid

    def lab(self, plants=("write_approval",)):
        aid = self.frozen(plants=list(plants))
        self.ready("a")
        if "wrong_profile" in plants:
            self.ready("b")
        self.practice.plant_for_attempt(aid)
        return aid

    def self_score(self, aid, value=True):
        self.f.save_entry(aid, "self_score", {"checks": {i: {"pass": value} for i in IDS}})

    def note(self, aid, fact=FACT, term="QuickBooks", **extra):
        self.f.save_entry(aid, "lab_note", {"fact": fact, "key_term": term, **extra})


class Attempts(EngineCase):
    def test_an_attempt_draws_hidden_plants_from_a_per_install_seed(self):
        view = self.f.start(MID, "beginner")
        attempt = view["attempt"]
        self.assertEqual(attempt["attempt_no"], 1)
        page = json.dumps(view)
        for hidden in ("plants", "seed", "f_salt", "write_approval", "memory_full", "wrong_profile"):
            self.assertNotIn(hidden, page)
        self.assertEqual(len(self.plants_of(attempt["id"])), 1)
        with self.store.connect() as conn:
            salt = self.store.meta_get(conn, "f_salt")
            seed = conn.execute("SELECT seed FROM f_attempts WHERE id = ?", (attempt["id"],)).fetchone()[0]
        self.assertEqual(len(salt), 32, "128 bits")
        self.assertEqual(seed, self.f.seed_for(salt, MID, 1))
        self.assertEqual(seed, hashlib.sha256(f"{salt}|{MID}|1".encode()).hexdigest()[:32])

    def test_starting_again_resumes_the_open_attempt(self):
        first = self.f.start(MID, "beginner")["attempt"]["id"]
        self.assertEqual(self.f.start(MID, "beginner")["attempt"]["id"], first)

    def test_plants_rotate_so_the_last_two_kinds_are_not_repeated(self):
        drawn = []
        for _ in range(4):
            aid = self.f.start(MID, "beginner")["attempt"]["id"]
            drawn.append(self.plants_of(aid)[0])
            self.f.abandon(aid)
        self.assertEqual(len(set(drawn[:3])), 3, drawn)
        self.assertNotIn(drawn[3], drawn[1:3])

    def test_intermediate_and_advanced_draw_two(self):
        aid = self.f.start(MID, "intermediate")["attempt"]["id"]
        self.assertEqual(len(set(self.plants_of(aid))), 2)

    def test_two_installs_draw_from_different_seeds(self):
        self.assertNotEqual(self.f.seed_for("a" * 32, MID, 1), self.f.seed_for("b" * 32, MID, 1))

    def test_an_unknown_mission_or_level_is_refused(self):
        with self.assertRaises(ValueError):
            self.f.start("f.nope", "beginner")
        with self.assertRaises(ValueError):
            self.f.start(MID, "expert")


class Freeze(EngineCase):
    def test_the_lab_stays_shut_until_recall_claim_standard_and_prediction_are_saved(self):
        aid = self.f.start(MID, "beginner")["attempt"]["id"]
        with self.assertRaisesRegex(ValueError, "recall"):
            self.f.open_lab(aid)
        self.f.save_entry(aid, "recall", {"answers": ["one", "two"]})
        self.f.save_entry(aid, "claim", {"text": CLAIM, "author": "course"})
        with self.assertRaisesRegex(ValueError, "standard"):
            self.f.open_lab(aid)
        with self.assertRaisesRegex(ValueError, "standard"):
            self.f.save_entry(aid, "prediction", {"checks": {}, "where_wrong": "somewhere in the middle"})
        self.f.save_entry(aid, "standard", {"checks": STANDARD})
        with self.assertRaisesRegex(ValueError, "s4"):
            self.f.save_entry(aid, "prediction", {"checks": {i: {"expect_pass": True, "confidence": 70} for i in IDS[:3]}, "where_wrong": "the new chat"})
        with self.assertRaisesRegex(ValueError, "50"):
            self.f.save_entry(aid, "prediction", {"checks": {i: {"expect_pass": True, "confidence": 20} for i in IDS}, "where_wrong": "the new chat"})
        self.f.save_entry(aid, "prediction", {"checks": {i: {"expect_pass": True, "confidence": 70} for i in IDS}, "where_wrong": "the new chat"})
        view = self.f.open_lab(aid)
        self.assertTrue(view["attempt"]["frozen_at"])
        self.assertEqual(view["lab"]["profiles"], ["a", "b"])

    def test_at_beginner_the_course_writes_the_claim_and_standard(self):
        aid = self.f.start(MID, "beginner")["attempt"]["id"]
        with self.assertRaisesRegex(ValueError, "course"):
            self.f.save_entry(aid, "claim", {"text": "I can do anything, really well, anywhere at all.", "author": "learner"})
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "standard", {"checks": STANDARD[:3]})

    def test_at_advanced_the_learner_writes_their_own(self):
        aid = self.f.start(MID, "advanced")["attempt"]["id"]
        self.f.save_entry(aid, "claim", {"text": "I can get a client's fact into a shared profile and prove it stuck.", "author": "learner"})
        mine = [{"id": "m1", "text": "The line is in USER.md."}, {"id": "m2", "text": "A new chat uses it."}, {"id": "m3", "text": "No save is left waiting."}]
        self.f.save_entry(aid, "standard", {"checks": mine})
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "standard", {"checks": mine[:2]})

    def test_after_the_freeze_the_first_four_are_closed_and_a_standard_change_is_recorded(self):
        aid = self.frozen()
        for kind, body in (("recall", {"answers": ["x"]}), ("claim", {"text": CLAIM, "author": "course"}),
                           ("standard", {"checks": STANDARD}), ("prediction", {"checks": {}, "where_wrong": "x" * 20})):
            with self.assertRaisesRegex(ValueError, "frozen", msg=kind):
                self.f.save_entry(aid, kind, body)
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "standard_change", {"checks": STANDARD})
        self.f.save_entry(aid, "standard_change", {"checks": STANDARD[:3] + [{"id": "s4", "text": "Find what stopped the save."}],
                                                   "why": "The fourth check was two checks in one."})
        view = self.f.attempt_view(aid)
        self.assertEqual(view["standard_changes"][0]["why"], "The fourth check was two checks in one.")

    def test_entries_are_chained_and_the_database_refuses_edits(self):
        aid = self.frozen()
        with self.store.connect() as conn:
            rows = conn.execute("SELECT kind, body_json, created_at, prev_hash, hash FROM f_entries ORDER BY id").fetchall()
            self.assertEqual(rows[0][3], "")
            for before, after in zip(rows, rows[1:]):
                self.assertEqual(after[3], before[4])
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE f_entries SET body_json = '{}'")
        self.assertTrue(self.f.verify_chain()["ok"])

    def test_an_unknown_kind_or_a_huge_body_is_refused(self):
        aid = self.f.start(MID, "beginner")["attempt"]["id"]
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "score", {"value": 100})
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "recall", {"answers": ["x" * 20000]})


class Checks(EngineCase):
    def test_checks_wait_for_the_self_score_and_the_self_score_closes_at_the_first_check(self):
        aid = self.lab()
        self.note(aid)
        with self.assertRaisesRegex(ValueError, "(?i)score yourself"):
            self.f.run_checks(aid, "first")
        self.self_score(aid)
        self.f.run_checks(aid, "first")
        with self.assertRaisesRegex(ValueError, "already"):
            self.self_score(aid)
        with self.assertRaisesRegex(ValueError, "first check"):
            self.f.run_checks(aid, "first")

    def test_hidden_checks_show_only_a_count_and_the_first_miss(self):
        aid = self.lab(["write_approval"])
        self.note(aid)
        self.self_score(aid)
        hf.stage_pending(self.home(), content=FACT)
        out = self.f.run_checks(aid, "first")["outcome"]
        self.assertFalse(out["passed"])
        self.assertEqual([c["id"] for c in out["checks"]], ["memory_line", "fresh_use"])
        self.assertEqual(out["hidden"], {"count": 1, "passed": 0})
        page = json.dumps(out)
        self.assertNotIn("plant_fixed", page)
        self.assertNotIn("write_approval", page)
        self.assertIn("ladder", out)

    def test_compare_reveals_the_plants_after_the_first_check(self):
        aid = self.lab(["write_approval"])
        self.note(aid)
        self.self_score(aid)
        self.assertNotIn("plants", self.f.attempt_view(aid))
        hf.stage_pending(self.home(), content=FACT)
        self.f.run_checks(aid, "first")
        compare = self.f.attempt_view(aid)["compare"]
        self.assertEqual(compare["plants"][0]["kind"], "write_approval")
        self.assertTrue(compare["plants"][0]["fired"])
        grid = {row["id"]: row for row in compare["grid"]}
        self.assertEqual(grid["s1"]["passed"], False)
        self.assertIs(grid["s1"]["expect_pass"], True)
        self.assertIs(grid["s1"]["self_pass"], True)
        self.assertIsNone(grid["s3"]["passed"], "the rubric check has no result until it is graded")
        self.assertEqual(compare["calibration"]["signed_gap"], 3)

    def test_the_fix_then_passes_on_the_after_fix_run(self):
        aid = self.lab(["write_approval"])
        self.note(aid)
        self.self_score(aid)
        self.f.run_checks(aid, "first")
        with self.assertRaisesRegex(ValueError, "gap"):
            self.f.run_checks(aid, "after_fix")
        self.f.save_entry(aid, "gap_note", {"text": "I trusted Saved. The save was waiting for approval."})
        hf.write_config(self.home(), hf.CONFIG)
        con = hf.state_db(self.home())
        sid = hf.add_session(con, started_at=hf.T0 + 10)
        hf.add_message(con, sid, "user", "Save: " + FACT, hf.T0 + 11)
        hf.add_message(con, sid, "assistant", "", hf.T0 + 12, tool_calls=json.dumps([{"function": {"name": "memory", "arguments": FACT}}]))
        sid2 = hf.add_session(con, started_at=hf.T0 + 100)
        hf.add_message(con, sid2, "user", "Draft the reconciliation checklist for Harbor Bakery.", hf.T0 + 101)
        hf.add_message(con, sid2, "assistant", "1. Export the bank feed from QuickBooks Online.", hf.T0 + 102)
        con.close()
        hf.write_memory(self.home(), [FACT + "; the other five use Xero."], None)
        out = self.f.run_checks(aid, "after_fix")["outcome"]
        self.assertTrue(out["passed"], out)
        self.assertEqual(out["hidden"], {"count": 1, "passed": 1})

    def test_the_pages_sample_is_kept_labelled_and_never_passes_a_check(self):
        aid = self.lab(["write_approval"])
        self.note(aid)
        self.self_score(aid)
        hf.write_memory(self.home(), ["Nothing about it."], None)
        sample = {"source": "session.list", "checks": {"memory_line": True}, "sessions": [{"id": "x", "title": "Save a fact"}]}
        out = self.f.run_checks(aid, "first", sample=sample)["outcome"]
        memory_line = next(c for c in out["checks"] if c["id"] == "memory_line")
        self.assertFalse(memory_line["passed"])
        with self.store.connect() as conn:
            rows = conn.execute("SELECT source, passed, facts_json FROM f_checks WHERE source = 'page_sample'").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0][1])
        self.assertIn("reported by the page", rows[0][2])

    def test_evidence_is_scrubbed_before_it_is_kept_and_hashed(self):
        aid = self.lab(["write_approval"])
        secret = hf.fake_key()
        hf.write_memory(self.home(), [f"{FACT} via key {secret}"], None)
        self.note(aid)
        self.self_score(aid)
        self.f.run_checks(aid, "first")
        with self.store.connect() as conn:
            rows = conn.execute("SELECT excerpt, excerpt_sha256 FROM f_evidence WHERE check_id = 'memory_line'").fetchall()
        self.assertTrue(rows)
        excerpt, digest = rows[0]
        self.assertNotIn(secret, excerpt)
        self.assertEqual(digest, hashlib.sha256(excerpt.encode()).hexdigest())

    def test_f_evidence_refuses_text_that_was_not_scrubbed(self):
        aid = self.frozen()
        with self.store.connect() as conn:
            with self.assertRaisesRegex(ValueError, "scrubbed"):
                self.f._store_evidence(conn, aid, "memory_line", ("memory", "memories/MEMORY.md", "key " + hf.fake_key(), ""))
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM f_evidence").fetchone()[0], 0)

    def test_a_token_in_memory_a_chat_or_a_detector_never_reaches_f_evidence(self):
        aid = self.lab(["write_approval"])
        secret = hf.fake_key()
        hf.write_memory(self.home(), [f"{FACT} key {secret}"], None)
        hf.stage_pending(self.home(), content=f"{FACT} {secret}")
        con = hf.state_db(self.home())
        sid = hf.add_session(con, started_at=hf.T0 + 600)
        hf.add_message(con, sid, "user", "Checklist for Harbor Bakery", hf.T0 + 601)
        hf.add_message(con, sid, "assistant", f"Use QuickBooks Online, token {secret}", hf.T0 + 602)
        con.close()
        self.note(aid)
        self.self_score(aid)
        out = self.f.run_checks(aid, "first")
        self.assertNotIn(secret, json.dumps(out))
        with self.store.connect() as conn:
            kept = json.dumps([list(r) for r in conn.execute("SELECT * FROM f_evidence")] + [list(r) for r in conn.execute("SELECT * FROM f_checks")])
        self.assertNotIn(secret, kept)
        self.assertIn("[removed]", kept)

    def test_transfer_checks_run_after_the_first_check(self):
        aid = self.lab(["write_approval"])
        self.note(aid)
        self.self_score(aid)
        with self.assertRaises(ValueError):
            self.f.run_checks(aid, "transfer")
        self.f.run_checks(aid, "first")
        self.f.save_entry(aid, "lab_note", {"fact": "Ada prefers short answers", "key_term": "short", "procedure_term": "invoice", "for": "transfer"})
        hf.write_memory(self.home(), None, ["Ada prefers short answers."])
        skill = self.home() / "skills" / "weekly-invoice"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: weekly-invoice\ndescription: Build the weekly invoice\n---\n1. Export.\n")
        out = self.f.run_checks(aid, "transfer")["outcome"]
        self.assertEqual([c["id"] for c in out["checks"]], ["user_line", "skill_not_memory"])
        self.assertTrue(out["passed"], out)

    def test_an_unreadable_profile_never_passes(self):
        aid = self.lab(["write_approval"])
        self.note(aid)
        self.self_score(aid)
        self.gone("academy-practice")
        out = self.f.run_checks(aid, "first")["outcome"]
        self.assertFalse(out["passed"])


class Rubric(EngineCase):
    def test_the_prompt_carries_four_levels_and_the_answer_as_untrusted_text(self):
        aid = self.frozen()
        out = self.f.submit_explanation(aid, ANSWER)
        prompt = out["prompt"]
        for level in ("1.", "2.", "3.", "4."):
            self.assertIn(level, prompt)
        self.assertIn("level", prompt)
        self.assertIn(f"explain@{aid}", prompt)
        self.assertIn("field_academy_grade_explanation", prompt)
        self.assertIn("Level 3 or higher passes", prompt)

    def test_a_level_closes_the_check_once(self):
        aid = self.frozen()
        self.f.submit_explanation(aid, ANSWER)
        with self.assertRaisesRegex(ValueError, "level"):
            self.f.grade_rubric(MID, f"explain@{aid}", None, "No level.")
        with self.assertRaisesRegex(ValueError, "1 to 4"):
            self.f.grade_rubric(MID, f"explain@{aid}", 5, "Too high.")
        result = self.f.grade_rubric(MID, f"explain@{aid}", 3, "Three Telegram reasons in order; add a check for the third.")
        self.assertTrue(result["passed"])
        with self.assertRaisesRegex(ValueError, "already"):
            self.f.grade_rubric(MID, f"explain@{aid}", 4, "Again.")
        self.f.submit_explanation(aid, ANSWER + " Also the profile.")
        self.assertFalse(self.f.grade_rubric(MID, f"explain@{aid}", 2, "Vaguer this time.")["passed"])

    def test_a_grade_for_another_mission_or_a_strange_step_is_refused(self):
        aid = self.frozen()
        self.f.submit_explanation(aid, ANSWER)
        for mission_id, step_id in (("f.other", f"explain@{aid}"), (MID, "explain"), (MID, "explain@999")):
            with self.assertRaises(ValueError):
                self.f.grade_rubric(mission_id, step_id, 3, "x")

    def test_the_agent_tool_routes_foundations_grades_and_keeps_old_grades_working(self):
        aid = self.frozen()
        self.f.submit_explanation(aid, ANSWER)
        tools = self.mod("tools")
        out = json.loads(tools.field_academy_grade_explanation({"mission_id": MID, "step_id": f"explain@{aid}", "score": 80, "feedback": "Good.", "level": 4}))
        self.assertTrue(out["passed"], out)
        self.assertEqual(out["level"], 4)
        out = json.loads(tools.field_academy_grade_explanation({"mission_id": MID, "step_id": f"explain@{aid}", "score": 80, "feedback": "No level."}))
        self.assertIn("error", out)

    def test_the_schema_gains_an_optional_level_and_the_capability_names_stay(self):
        schemas = self.mod("schemas")
        params = schemas.FIELD_ACADEMY_GRADE_EXPLANATION["parameters"]
        self.assertEqual(params["properties"]["level"], {"type": "integer", "minimum": 1, "maximum": 4, "description": params["properties"]["level"]["description"]})
        self.assertNotIn("level", params["required"])
        self.assertEqual(params["required"], ["mission_id", "step_id", "score", "feedback"])
        manifest = (ROOT / "plugin.yaml").read_text()
        for tool in ("field_academy_snapshot", "field_academy_mission", "field_academy_grade_explanation", "field_academy_grade_review",
                     "field_academy_grade_deployer", "field_academy_record_evidence"):
            self.assertIn(f"  - {tool}\n", manifest)
        self.assertEqual(manifest.count("\n  - field_academy_"), 6, "no new tool")

    def test_the_rubric_result_lands_in_the_compare_grid(self):
        aid = self.lab(["write_approval"])
        self.note(aid)
        self.self_score(aid)
        self.f.run_checks(aid, "first")
        self.f.submit_explanation(aid, ANSWER)
        self.f.grade_rubric(MID, f"explain@{aid}", 3, "Good order.")
        grid = {row["id"]: row for row in self.f.attempt_view(aid)["compare"]["grid"]}
        self.assertIs(grid["s3"]["passed"], True)
        self.assertEqual(grid["s3"]["level"], 3)


class Steps(EngineCase):
    def test_the_step_machine_opens_steps_in_order(self):
        aid = self.f.start(MID, "beginner")["attempt"]["id"]
        steps = {s["id"]: s["status"] for s in self.f.attempt_view(aid)["steps"]}
        self.assertEqual(steps["recall"], "open")
        self.assertEqual(steps["claim"], "locked")
        self.f.save_entry(aid, "recall", {"answers": ["one", "two"]})
        steps = {s["id"]: s["status"] for s in self.f.attempt_view(aid)["steps"]}
        self.assertEqual((steps["recall"], steps["claim"]), ("done", "open"))

    def test_snapshot_lists_missions_and_attempts_without_secrets(self):
        self.frozen()
        snap = self.f.snapshot()
        self.assertEqual(snap["missions"][0]["id"], MID)
        self.assertEqual(snap["missions"][0]["attempts"][0]["status"], "lab")
        self.assertNotIn("f_salt", json.dumps(snap))
        self.assertNotIn("plants", json.dumps(snap))


if __name__ == "__main__":
    unittest.main()


class TeachingOrder(unittest.TestCase):
    """The map and the Foundations page list missions 1 to 11 in teaching order, not by file name (f_connectors.py
    sorts before f_loop.py, which put mission 7 first)."""

    def test_the_real_missions_come_out_in_order(self):
        f = load("foundations")
        content = load("foundations_content")
        ordered = f._in_order(content.load_all(f.CONTENT_DIR))
        self.assertEqual([m.get("order") for _, m in ordered], list(range(1, len(ordered) + 1)))
        self.assertEqual(ordered[0][0], "f.loop")
        school = load("school")
        foundations_only = [mid for mid, _ in ordered if mid not in school.PLACEMENTS]
        self.assertEqual(foundations_only[-1], "f.review")
        self.assertEqual(len(foundations_only), 11)
        source = (pathlib.Path(__file__).resolve().parents[1] / "foundations.py").read_text(encoding="utf-8")
        self.assertIn("for mission_id, mission in _in_order(missions):", source)
