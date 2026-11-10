"""Mission 3 (f.memory) end to end, from the shipped content: seed notes, each planted problem, the checks, the
memory-file view, and the Field Record entry. A stand-in lays down what Hermes would; nothing runs Hermes."""

from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402

MID = "f.memory"
FACT = "Harbor Bakery uses QuickBooks Online; the other five use Xero"
TERM = "QuickBooks"
# Hermes's own staged result line (tools/write_approval.py:165-168, Hermes 0.22.4).
STAGED_MESSAGE = "Staged for approval (memory.write_approval is on). Not yet saved \u2014 review with /memory pending."
# What a fresh chat says when the save never landed: it doesn't know which software Harbor Bakery uses.
STALE_ANSWER = "1. Export the bank feed from your accounting software. Which one does Harbor Bakery use?"


class MemoryMission(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.f = self.mod("foundations")
        self.f.CONTENT_DIR = None
        self.content = self.mod("foundations_content")
        self.content.clear_cache()
        self.mission = self.content.get(MID)

    # ------------------------------------------------------------- helpers --

    def salt_for(self, wanted, level="beginner"):
        for n in range(800):
            salt = f"{n:032x}"
            seed = self.f.seed_for(salt, MID, 1)
            if self.f.choose_plants(self.mission["lab"]["plants"], self.mission["lab"]["plants_at"][level], [], seed) == wanted:
                with self.store.connect() as conn:
                    self.store.meta_set(conn, "f_salt", salt)
                return
        self.fail("no salt found")

    def lab(self, plants):
        self.salt_for(list(plants))
        aid = self.f.start(MID)["attempt"]["id"]
        self.f.save_entry(aid, "recall", {"answers": ["Words, then the row, then the file.", "The tool schemas were biggest."]})
        self.f.save_entry(aid, "claim", {"text": self.mission["claim"]["text"], "author": "course"})
        self.f.save_entry(aid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in self.mission["standard"]]})
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 80} for c in self.mission["standard"]},
                                              "where_wrong": "The new chat might not use the fact."})
        self.f.open_lab(aid)
        for which in self.content.profiles_needed(self.mission):
            self.ready(which)
        self.f.plant_lab(aid)
        return aid

    def memory(self, name="academy-practice"):
        return self.hermes_read.memory(self.home(name))

    def save_and_use(self, home=None, staged=False):
        """A chat that saves the fact (or has it staged), then a new chat. Saved: the new chat uses the fact unprompted.
        Staged: the tool row carries Hermes's own staged result (tools/memory_tool.py:99, the message from
        tools/write_approval.py:165) and the new chat does not know the fact, as the failed fresh-chat check says."""
        home = home or self.home()
        con = hf.state_db(home)
        sid = hf.add_session(con, started_at=hf.T0 + 10)
        hf.add_message(con, sid, "user", "Save to memory: " + FACT, hf.T0 + 11)
        hf.add_message(con, sid, "assistant", "", hf.T0 + 12, tool_calls=json.dumps([{"function": {"name": "memory", "arguments": FACT}}]))
        result = {"success": True, "staged": True, "pending_id": "ab12cd34", "message": STAGED_MESSAGE} if staged else \
            {"success": True, "usage": "31% — 690/2,200 chars"}
        hf.add_message(con, sid, "tool", json.dumps(result), hf.T0 + 13, tool_name="memory")
        sid2 = hf.add_session(con, started_at=hf.T0 + 100)
        hf.add_message(con, sid2, "user", "Draft this month's reconciliation checklist for Harbor Bakery.", hf.T0 + 101)
        hf.add_message(con, sid2, "assistant", STALE_ANSWER if staged else "1. Export the bank feed from QuickBooks Online.", hf.T0 + 102)
        con.close()

    def to_first_check(self, aid):
        self.f.save_entry(aid, "lab_note", {"fact": FACT, "key_term": TERM})
        self.f.save_entry(aid, "self_score", {"checks": {c["id"]: {"pass": True} for c in self.mission["standard"]}})
        return self.f.run_checks(aid, "first")["outcome"]

    def visible(self, outcome):
        return {c["id"]: c["passed"] for c in outcome["checks"]}

    # ------------------------------------------------------------- content --

    def test_the_mission_loads_and_the_page_never_sees_the_puzzle(self):
        public = self.f.mission_view(MID)
        self.assertEqual([c["id"] for c in public["standard"]], ["s1", "s2", "s3", "s4"])
        self.assertTrue(public["try_text"].strip())
        self.assertEqual(len(public["expert_steps"]), 6)
        self.assertTrue(all(all(step[k] for k in ("did", "saw", "noticed", "ruled_out")) for step in public["expert_steps"]))
        page = json.dumps(public)
        for hidden in ("write_approval", "memory_full", "wrong_profile", "seed_notes", "plant_fixed", "Refunds over 200", "expert_slots", "DAMON"):
            self.assertNotIn(hidden, page)
        self.assertEqual(public["hidden_checks"], 1)
        self.assertEqual(public["lab"]["profiles"], ["a"], "one practice profile: the wrong-profile plant was dropped Oct 22")

    # --------------------------------------------------------------- seeds --

    def test_every_variant_starts_with_the_seed_notes_and_an_empty_user_file(self):
        self.lab(["write_approval"])
        mem = self.memory()
        seeds = self.practice.seed_notes("academy-practice")["notes"]
        self.assertEqual(mem["memory"]["entries"], seeds)
        self.assertEqual(len(seeds), 5)
        self.assertEqual(len(self.practice.seed_notes("academy-practice")["key"]), 2)
        self.assertLess(mem["memory"]["chars"], 700)
        self.assertEqual(mem["user"]["entries"], [])
        self.assertEqual([p["name"] for p in self.practice.listing()], ["academy-practice"])

    def test_the_page_learns_the_setup_is_done_and_nothing_about_what(self):
        self.lab(["memory_full"])
        listing = self.practice.listing()
        main = next(p for p in listing if p["name"] == "academy-practice")
        self.assertTrue(main["set_up"])
        self.assertEqual(main["status"], "ready")
        for hidden in ("planted", "memory_full", "filler", "seed_notes", '"key"'):
            self.assertNotIn(hidden, json.dumps(listing))

    # -------------------------------------------------------- write_approval --

    def test_write_approval_a_staged_save_fails_the_check_then_the_fix_passes(self):
        aid = self.lab(["write_approval"])
        self.save_and_use(staged=True)
        hf.stage_pending(self.home(), content=FACT)
        out = self.to_first_check(aid)
        self.assertFalse(out["passed"])
        self.assertEqual(self.visible(out)["memory_line"], False)
        self.assertEqual(out["hidden"], {"count": 1, "passed": 0})
        plant = self.f.attempt_view(aid)["compare"]["plants"][0]
        self.assertEqual(plant["kind"], "write_approval")
        self.assertTrue(plant["fired"])
        self.assertIn({"label": "Saves Hermes staged in a chat", "value": "1"}, plant["facts"])
        # The learner approves the save: the queue empties and the line lands. A fresh chat uses it.
        for p in (self.home() / "pending" / "memory").glob("*.json"):
            p.unlink()
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"] + [FACT], None)
        con = hf.state_db(self.home())
        sid = hf.add_session(con, started_at=hf.now_epoch() + 60)
        hf.add_message(con, sid, "user", "Draft the checklist for Harbor Bakery.", hf.now_epoch() + 61)
        hf.add_message(con, sid, "assistant", "Export the bank feed from QuickBooks Online.", hf.now_epoch() + 62)
        con.close()
        self.f.save_entry(aid, "gap_note", {"text": "I trusted Saved to memory. Expanded, it said staged for approval."})
        after = self.f.run_checks(aid, "after_fix")["outcome"]
        self.assertTrue(after["passed"], after)
        self.assertTrue(self.f.attempt_view(aid)["compare"]["plants"][0]["fired"], "approving later doesn't hide that it happened")

    # ------------------------------------------------------------ memory_full --

    def test_memory_full_hermes_cuts_a_key_note_and_the_learner_puts_it_back(self):
        aid = self.lab(["memory_full"])
        mem = self.memory()["memory"]
        self.assertGreaterEqual(mem["chars"], 2200 - 90)
        self.assertLessEqual(mem["chars"], 2200 - 30)
        seeds = self.practice.seed_notes("academy-practice")["notes"]
        key = self.practice.seed_notes("academy-practice")["key"]
        self.assertEqual(mem["entries"][:len(seeds)], seeds, "the seed notes come first, then the filler")
        # Hermes's first try comes back over the limit; then it cuts the first key note and two others and saves.
        self.chat(user="Save to memory: " + FACT, tool=hf.memory_full_error(), started=hf.T0 + 5)
        kept = [e for e in mem["entries"] if e != key[0]][:-2]
        hf.write_memory(self.home(), kept + [FACT], None)
        self.save_and_use()
        out = self.to_first_check(aid)
        self.assertEqual(self.visible(out)["memory_line"], True)
        self.assertEqual(self.visible(out)["notes_kept"], False)
        self.assertIn(key[0], next(c for c in out["checks"] if c["id"] == "notes_kept")["detail"])
        compare = self.f.attempt_view(aid)["compare"]
        self.assertTrue(compare["plants"][0]["fired"])
        facts = {f["label"]: f["value"] for f in compare["plants"][0]["facts"]}
        self.assertEqual(facts["Notes the practice jobs rely on, still there"], "1 of 2")
        # Watch what a full memory cuts: put it back and cut something else.
        hf.write_memory(self.home(), [key[0]] + kept[:-1] + [FACT], None)
        self.f.save_entry(aid, "gap_note", {"text": "Hermes made room by cutting the shift plan note, and I didn't look."})
        after = self.f.run_checks(aid, "after_fix")["outcome"]
        self.assertTrue(after["passed"], after)

    # ---------------------------------------------------------- wrong_profile --

    def test_wrong_profile_the_second_profile_is_a_twin_and_work_there_is_caught(self):
        # Mission 3 no longer draws this plant (v2 build notes, Oct 22); the planter stays for later missions, so it
        # runs here on mission 3's content with the plant added back.
        self.mission["lab"]["plants"] = ["write_approval", "memory_full", "wrong_profile"]
        try:
            self._wrong_profile()
        finally:
            self.content.clear_cache()

    def _wrong_profile(self):
        aid = self.lab(["wrong_profile"])
        seeds = self.practice.seed_notes("academy-practice")["notes"]
        self.assertEqual(self.memory("academy-practice-b")["memory"]["entries"], seeds, "the twin answers like the right one")
        hf.write_memory(self.home("academy-practice-b"), seeds + [FACT], None)
        self.save_and_use(home=self.home("academy-practice-b"))
        out = self.to_first_check(aid)
        self.assertFalse(out["passed"])
        self.assertEqual(self.visible(out)["memory_line"], False)
        plant = self.f.attempt_view(aid)["compare"]["plants"][0]
        self.assertEqual(plant["kind"], "wrong_profile")
        self.assertTrue(plant["fired"])

    # ------------------------------------------------------------ the notes --

    def test_the_try_note_and_the_removed_note_answer(self):
        aid = self.lab(["write_approval"])
        self.f.save_entry(aid, "try_note", {"guess": "A few pages", "memory_tokens": "240"})
        self.f.save_entry(aid, "try_note", {"guess": "A paragraph", "memory_tokens": ""})
        with self.assertRaisesRegex(ValueError, "whole number"):
            self.f.save_entry(aid, "try_note", {"guess": "A page", "memory_tokens": "lots"})
        self.f.save_entry(aid, "lab_note", {"fact": FACT, "key_term": TERM, "removed_ok": "Hermes cut the supplier orders note; it was stale."})
        notes = [e["body"] for e in self.f.attempt_view(aid)["entries"] if e["kind"] in ("try_note", "lab_note")]
        self.assertEqual(notes[0], {"guess": "A few pages", "memory_tokens": 240})
        self.assertIn("removed_ok", notes[-1])

    # ---------------------------------------------------------------- view --

    def test_results_evidence_and_the_explain_state_survive_a_reload(self):
        aid = self.lab(["write_approval"])
        hf.write_memory(self.home(), [FACT], None)
        self.save_and_use()
        self.to_first_check(aid)
        view = self.f.attempt_view(aid)
        self.assertEqual(set(view["runs"]), {"first"})
        self.assertEqual(view["runs"]["first"]["hidden"]["count"], 1)
        self.assertTrue(all(c["id"] != "plant_fixed" for c in view["runs"]["first"]["checks"]))
        self.assertTrue(view["evidence"])
        self.assertTrue(all(e["check_id"] != "plant_fixed" for e in view["evidence"]), "a hidden check's excerpts stay off the page")
        self.assertTrue(all(len(e["sha256"]) == 64 for e in view["evidence"]))
        self.assertEqual(view["explain"]["submitted"], 0)
        self.f.submit_explanation(aid, "x" * 130)
        self.assertTrue(self.f.attempt_view(aid)["explain"]["waiting"])
        self.f.grade_rubric(MID, f"explain@{aid}", 3, "Three causes, each with a check.")
        explain = self.f.attempt_view(aid)["explain"]
        self.assertEqual((explain["level"], explain["passed"], explain["waiting"]), (3, True, False))
        grid = {g["id"]: g for g in self.f.attempt_view(aid)["compare"]["grid"]}
        self.assertIs(grid["s3"]["passed"], True)

    def test_the_memory_file_view_is_scrubbed_and_only_for_practice_profiles(self):
        self.lab(["write_approval"])
        secret = hf.fake_key()
        hf.write_memory(self.home(), ["The shop key is " + secret], ["Ada prefers short answers."])
        shown = self.practice.memory_files("academy-practice")
        self.assertNotIn(secret, json.dumps(shown))
        self.assertEqual([f["file"] for f in shown["files"]], ["MEMORY.md", "USER.md"])
        self.assertEqual(shown["files"][1]["entries"], ["Ada prefers short answers."])
        self.assertTrue(shown["folder"].endswith("memories"))
        for name in ("default", "work", "../academy-practice"):
            with self.assertRaises(ValueError):
                self.practice.memory_files(name)

    # -------------------------------------------------------------- record --

    def finished(self):
        aid = self.lab(["write_approval"])
        with self.assertRaisesRegex(ValueError, "transfer"):
            self.f.add_to_record(aid, confirmed=True)
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"] + [FACT], ["Ada prefers short answers."])
        self.save_and_use()
        self.to_first_check(aid)
        self.f.save_entry(aid, "gap_note", {"text": "I scored check 4 a pass without looking for anything planted."})
        self.f.run_checks(aid, "after_fix")
        self.f.save_entry(aid, "lab_note", {"fact": "Ada prefers short answers", "key_term": "short", "for": "transfer",
                                            "one_off": "The printer quote came in at noon today", "one_off_saved": False,
                                            "one_off_why": "It matters for one afternoon, so it doesn't earn a line."})
        self.f.run_checks(aid, "transfer")
        return aid

    def test_the_record_entry_is_previewed_then_added_once_and_for_good(self):
        aid = self.finished()
        preview = self.f.record_preview(aid)
        self.assertTrue(preview["ready"])
        entry = preview["entry"]
        self.assertEqual(entry["mission"], MID)
        self.assertEqual(entry["claim"], self.mission["claim"]["text"])
        self.assertEqual([c["id"] for c in entry["standard"]], ["s1", "s2", "s3", "s4"])
        self.assertTrue(entry["evidence"])
        self.assertEqual(entry["caught"] + entry["missed"], [dict(x) for x in entry["caught"] + entry["missed"]])
        with self.assertRaisesRegex(ValueError, "confirm"):
            self.f.add_to_record(aid)
        first_id = entry["evidence"][0]["id"]
        added = self.f.add_to_record(aid, withhold=[first_id], confirmed=True)
        self.assertEqual(added["attempt"]["attempt"]["status"], "done")
        self.assertEqual(added["attempt"]["record"]["hash"], added["added"]["hash"])
        with self.assertRaisesRegex(ValueError, "already"):
            self.f.add_to_record(aid, confirmed=True)
        with self.store.connect() as conn:
            body = json.loads(conn.execute("SELECT body_json FROM f_record WHERE attempt_id = ?", (aid,)).fetchone()[0])
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE f_record SET body_json = '{}'")
        withheld = next(e for e in body["evidence"] if e["id"] == first_id)
        self.assertEqual((withheld["excerpt"], withheld["withheld"]), ("", True))
        self.assertEqual(len(withheld["sha256"]), 64, "a withheld excerpt keeps its hash")


if __name__ == "__main__":
    unittest.main()


class WorkingFolderAndSources(MemoryMission):
    def test_the_first_practice_chats_folder_is_checked(self):
        self.lab(["write_approval"])
        out = self.practice.working_folder("academy-practice")
        self.assertEqual(out["state"], "no_chat")
        con = hf.state_db(self.home())
        hf.add_session(con, started_at=hf.T0 + 1, cwd=str(self.home()))
        con.close()
        self.assertEqual(self.practice.working_folder("academy-practice")["state"], "pass")
        self.assertEqual(self.practice.working_folder("academy-practice")["cwd"], self.practice.shown_path(self.home()),
                         "a long path is shown, not taken for a key")

    def test_a_folder_path_is_shown_home_relative_and_only_a_key_shaped_name_is_removed(self):
        shown = self.practice.shown_path
        home = pathlib.Path("/home/ada")
        self.assertEqual(shown("/home/ada/.hermes/profiles/academy-practice", home), "~/.hermes/profiles/academy-practice")
        long_path = "/home/ada/Documents/client-work/harbor-bakery-quarterly-reconciliation-2026/hermes/profiles/academy-practice"
        self.assertEqual(shown(long_path, home), "~/Documents/client-work/harbor-bakery-quarterly-reconciliation-2026/hermes/profiles/academy-practice")
        self.assertEqual(shown("/srv/hermes/profiles/academy-practice", home), "/srv/hermes/profiles/academy-practice")
        self.assertEqual(shown("C:\\Users\\Ada\\AppData\\Local\\hermes\\profiles\\academy-practice", home),
                         "C:\\Users\\Ada\\AppData\\Local\\hermes\\profiles\\academy-practice")
        secret = hf.fake_key()
        out = shown(f"/home/ada/{secret}/academy-practice", home)
        self.assertNotIn(secret, out)
        self.assertTrue(out.startswith("~/") and out.endswith("/academy-practice"))
        self.lab(["write_approval"])
        con = hf.state_db(self.home())
        hf.add_session(con, started_at=hf.T0 + 1, cwd=str(self.root / secret))
        con.close()
        folder = self.practice.working_folder("academy-practice")
        self.assertEqual(folder["state"], "fail")
        self.assertNotIn(secret, json.dumps(folder))
        self.assertTrue(self.practice.listing()[0]["path_shown"].endswith("profiles/academy-practice"))

    def test_a_chat_in_another_folder_fails_with_one_line_to_fix_it(self):
        self.lab(["write_approval"])
        con = hf.state_db(self.home())
        hf.add_session(con, started_at=hf.T0 + 1, cwd=str(self.root))
        hf.add_session(con, started_at=hf.T0 + 2, cwd=str(self.home()))
        con.close()
        out = self.practice.working_folder("academy-practice")
        self.assertEqual(out["state"], "fail", "the first chat counts")
        self.assertIn("working folder", out["fix"])
        self.assertEqual(out["checked_by"], "Field Academy read it")
        con = hf.state_db(self.home("academy-practice"))
        con.execute("UPDATE sessions SET cwd = NULL")
        con.commit()
        con.close()
        self.assertEqual(self.practice.working_folder("academy-practice")["state"], "unknown")
        with self.assertRaises(ValueError):
            self.practice.working_folder("default")

    def test_every_result_and_record_line_says_who_checked_it(self):
        aid = self.finished()
        view = self.f.attempt_view(aid)
        self.assertTrue(all(c["checked_by"] == "Field Academy read it" for run in view["runs"].values() for c in run["checks"]))
        grid = {g["id"]: g for g in view["compare"]["grid"]}
        self.assertEqual(grid["s1"]["checked_by"], "Field Academy read it")
        self.assertEqual(grid["s3"]["checked_by"], "your Hermes graded it")
        entry = self.f.record_preview(aid)["entry"]
        self.assertEqual(entry["explain"]["checked_by"], "your Hermes graded it")
        self.assertEqual(entry["result_first"]["checked_by"], "Field Academy read it")
        self.assertTrue(all(e["checked_by"] == "Field Academy read it" for e in entry["evidence"]))


class ProtectedNotesAndOneOff(MemoryMission):
    def test_two_protected_notes_are_drawn_per_learner_and_shown_on_the_page(self):
        aid = self.lab(["write_approval"])
        view = self.f.attempt_view(aid)
        protected = view["protected_notes"]
        self.assertEqual(len(protected), 2)
        seed = self._seed(aid)
        drawn = [n["text"] for n in self.f.seed_notes_for(self.mission, seed) if n.get("key")]
        self.assertEqual(sorted(protected), sorted(drawn))
        self.assertFalse(any("{" in text for text in protected), "every name and number is filled in")
        draws = {tuple(sorted(n["text"] for n in self.f.seed_notes_for(self.mission, f"{i:032x}") if n.get("key"))) for i in range(40)}
        self.assertGreater(len(draws), 1, "two learners don't all get the same protected notes")
        self.assertEqual(self.f.seed_notes_for(self.mission, "abc"), self.f.seed_notes_for(self.mission, "abc"))
        self.assertNotIn("seed_notes", json.dumps(self.f.mission_view(MID)))

    def _seed(self, aid):
        with self.store.connect() as conn:
            return conn.execute("SELECT seed FROM f_attempts WHERE id = ?", (aid,)).fetchone()[0]

    def test_names_and_numbers_in_the_seed_notes_vary_by_seed_and_hold_for_an_attempt(self):
        texts = {tuple(sorted(n["text"] for n in self.f.seed_notes_for(self.mission, f"{i:032x}"))) for i in range(40)}
        self.assertGreater(len(texts), 30, "two learners rarely get identical notes")
        refunds = {self.f.seed_params_for(self.mission, f"{i:032x}")["refund"] for i in range(40)}
        self.assertGreater(len(refunds), 2, "the numbers themselves vary, not only which notes are drawn")
        for i in range(10):
            seed = f"{i:032x}"
            self.assertEqual(self.f.seed_notes_for(self.mission, seed), self.f.seed_notes_for(self.mission, seed))
            for note in self.f.seed_notes_for(self.mission, seed):
                self.assertNotIn("{", note["text"])
                self.assertLessEqual(len(note["text"]), 240)
        self.assertNotIn("seed_params", json.dumps(self.f.mission_view(MID)), "the page never sees the choices")

    def test_the_planted_full_memory_varies_by_seed_and_repeats_for_the_same_seed(self):
        rng = self.plants._rng
        one = [self.plants.filler_notes(rng(f"{i:032x}", "memory_full")) for i in range(12)]
        self.assertEqual(self.plants.filler_notes(rng("a" * 32, "memory_full")), self.plants.filler_notes(rng("a" * 32, "memory_full")))
        self.assertGreater(len({tuple(x) for x in one}), 10)
        self.assertFalse(any("{" in note for notes in one for note in notes))
        margins = {self.plants.margin(rng(f"{i:032x}", "memory_full")) for i in range(12)}
        self.assertGreater(len(margins), 3, "the free space left under the limit differs between learners")
        self.lab(["memory_full"])
        details = self.practice.planted("academy-practice")["memory_full"]
        low, high = details["margin"]
        self.assertTrue(self.plants.FILL_LOW[0] <= low <= self.plants.FILL_LOW[1] and self.plants.FILL_HIGH[0] <= high <= self.plants.FILL_HIGH[1])
        mem = self.memory()
        self.assertEqual(details["free"], mem["memory"]["limit"] - mem["memory"]["chars"])
        self.assertTrue(low <= details["free"] <= high * 2, details["free"])

    def test_the_memory_view_counts_staged_saves_and_never_shows_them_as_lines(self):
        self.lab(["write_approval"])
        hf.stage_pending(self.home(), content="A staged line that isn't saved")
        shown = self.practice.memory_files("academy-practice")
        self.assertEqual(shown["pending"], 1)
        self.assertNotIn("staged line", json.dumps(shown))

    def test_the_save_or_skip_call_is_kept_and_checked(self):
        aid = self.finished()
        out = self.f.attempt_view(aid)["runs"]["transfer"]
        self.assertEqual({c["id"] for c in out["checks"]}, {"user_line", "one_off"})
        one_off = self.f.record_preview(aid)["entry"]["transfer"]["one_off"]
        self.assertEqual((one_off["saved"], one_off["checked_by"], one_off["why_checked_by"]), (False, "Field Academy read it", "not graded yet"))
        with self.assertRaisesRegex(ValueError, "left it out"):
            self.f.save_entry(aid, "lab_note", {"fact": "Ada prefers short answers", "key_term": "short", "for": "transfer", "one_off": "printer quote"})

