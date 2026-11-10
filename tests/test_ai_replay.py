"""Loop 2, AI lane: Replay your run (recorder.py), the pins that sit on it, faster prefetch, Explain my miss rules, Ask
during the hunt, and the First Flight mark. Stand-in model and stand-in practice chat; nothing runs Hermes.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
import test_ai_guide as tg  # noqa: E402
import test_foundations_memory_mission as tmm  # noqa: E402
from test_ai_fakes import FakeLlm  # noqa: E402

MID = tg.MID
# Loop 1's real Sonnet answer to Ask at Check (guide-calls-sonnet.json): it named the snag during the hunt.
LOOP1_ASK = {"sentences": [
    {"text": "The transcript shows Hermes called the memory tool, but the tool's result is blank, so nothing here confirms "
             "the save went through.", "source_ids": ["m2", "m3"]},
    {"text": "One possible cause is a save waiting for approval: it still gets the title Saved to memory and a check mark, "
             "but it is only staged and not yet written to the file.", "source_ids": ["asof-1"]},
    {"text": "Staged saves wait in the profile's pending folder, and expanding the memory row will say the save was staged "
             "and isn't saved yet.", "source_ids": ["asof-1"]}], "not_in_sources": False}


class ReplayCase(tg.GuideCase):
    def setUp(self):
        super().setUp()
        self.rec = self.mod("recorder")

    def ids(self, payload, lane=None):
        return [e["event_id"] for e in payload["events"] if lane is None or e["lane"] == lane]


class ExplainOnCompare(ReplayCase):
    """Why did this miss? lives on Compare (Nov 9): once the snag is revealed it may name the cause, and it is fetched
    again with the after-Compare wording and places (the pending folder), never served from the Check-time wording."""

    def test_compare_fetches_its_own_explain_that_may_name_the_cause(self):
        aid = self.missed()
        cause = {"sentences": ["The save sat in the pending folder, so MEMORY.md never got the line this check reads.",
                               "Open the pending folder in the practice profile to see it."]}
        llm = self.routed(explains=[cause] * 8)
        self.view(aid, "compare")
        out = self.guide.use_help(aid, action="explain", step="compare")["shown"]["explain"]
        self.assertTrue(out and all(i["source"] == "model" for i in out), out)
        self.assertIn("pending folder", out[0]["sentences"][0])
        sent = [c for c in llm.calls if c.get("schema_name") == "field_academy_explain"]
        self.assertTrue(sent and all(self.guide.EXPLAIN_ONE_AFTER in c.get("instructions", "") for c in sent),
                        "the after-Compare wording, which may name the cause")
        self.assertTrue(all("Never use these words" not in c.get("instructions", "") for c in sent), "no give-away list after Compare")


class MemoryFull(ReplayCase):
    """The sample run's snag (memory_full): the first save is refused, Hermes deletes notes to make room and saves.
    The replay joins that save to the note it deleted, read from the check's own evidence."""

    def test_the_save_that_made_room_is_bracketed_to_the_note_it_deleted(self):
        aid = self.lab(["memory_full"])
        mem = self.hermes_read.memory(self.home())["memory"]
        key = self.practice.seed_notes("academy-practice")["key"]
        con = hf.state_db(self.home())
        sid = hf.add_session(con, started_at=hf.T0 + 10)
        hf.add_message(con, sid, "user", "Save to memory: " + tmm.FACT, hf.T0 + 11)
        hf.add_message(con, sid, "tool", hf.memory_full_error(), hf.T0 + 13, tool_name="memory")
        hf.add_message(con, sid, "tool", json.dumps({"success": True, "usage": "97% — 2,140/2,200 chars"}), hf.T0 + 15, tool_name="memory")
        con.close()
        kept = [e for e in mem["entries"] if e != key[0]][:-2]
        hf.write_memory(self.home(), kept + [tmm.FACT], None)
        out = self.to_first_check(aid)
        self.assertFalse(out["passed"])
        self.f.save_entry(aid, "gap_note", {"text": "A note went."})
        rep = self.rec.replay(aid, "compare")
        rows = [e for e in rep["events"] if e["kind"] == "tool:memory"]
        self.assertEqual([r["failed"] for r in rows], [True, False])
        gone = next(e for e in rep["events"] if e["kind"] == "file:removed")
        self.assertEqual(gone["text"], key[0])
        self.assertEqual(gone["at"], rows[1]["at"], "placed at the save that made room")
        self.assertEqual(rep["bracket"], {"from": rows[1]["event_id"], "to": gone["event_id"], "words": self.rec.ROOM_WORDS})
        self.assertEqual(rep["snag_found_from"], "removed_note")


class Timeline(ReplayCase):
    def test_the_replay_agrees_with_the_check_facts(self):
        aid = self.missed()
        out = self.rec.replay(aid, "compare")
        self.assertEqual(out["state"], "ready")
        self.assertEqual([lane["id"] for lane in out["lanes"]], ["chat", "files"])
        self.assertEqual(out["snag_found_from"], "staged_flag")
        row = next(e for e in out["events"] if e["kind"] == "tool:memory")
        self.assertEqual(row["title"], "Saved to memory", "the app's own title, the same for a staged save")
        self.assertTrue(row["staged"])
        self.assertEqual(row["text"], tmm.STAGED_MESSAGE, "Hermes's own staged line")
        held = next(e for e in out["events"] if e["kind"] == "file:pending")
        self.assertEqual(held["title"], "Held for your approval")
        self.assertTrue(held["path"].startswith("pending/memory/"))
        meter = next(e for e in out["events"] if e["kind"] == "file:memory")
        self.assertEqual(meter["title"], "MEMORY.md unchanged")
        self.assertEqual(meter["meter"], {"used": 479, "limit": 2200, "changed": False})
        self.assertEqual(out["bracket"], {"from": row["event_id"], "to": held["event_id"],
                                          "words": "The chat showed Saved to memory, but the note is waiting for your approval and is not in MEMORY.md."})
        fresh = [e for e in out["events"] if e["lane"] == "chat" and e["at"] > hf.T0 + 50]
        self.assertTrue(fresh)
        self.assertFalse(any(tmm.TERM in e["text"] for e in fresh if e["kind"] != "user"),
                         "the fresh chat does not use the fact, as the failed fresh-chat check says")
        self.assertLessEqual(out["started_at"], out["ended_at"])
        for e in out["events"]:
            for key in ("event_id", "lane", "at", "kind", "title", "text"):
                self.assertIn(key, e)

    def test_the_snag_comes_from_the_staged_flag_never_the_title(self):
        aid = self.lab(["write_approval"])
        con = hf.state_db(self.home())
        sid = hf.add_session(con, started_at=hf.T0 + 10)
        hf.add_message(con, sid, "user", "Save to memory: " + tmm.FACT, hf.T0 + 11)
        # A real save: the same title in the app, no staged flag. No bracket.
        hf.add_message(con, sid, "tool", json.dumps({"success": True, "usage": "31% — 690/2,200 chars"}), hf.T0 + 13, tool_name="memory")
        con.close()
        hf.stage_pending(self.home(), content=tmm.FACT)
        self.to_first_check(aid)
        out = self.rec.replay(aid, "compare")
        row = next(e for e in out["events"] if e["kind"] == "tool:memory")
        self.assertEqual(row["title"], "Saved to memory")
        self.assertFalse(row["staged"])
        self.assertIsNone(out["bracket"])
        self.assertIn("690/2,200", row["text"])

    def test_before_compare_the_route_is_not_ready_and_gives_nothing_away(self):
        aid = self.missed()
        for step in ("", "check", "evidence"):
            out = self.rec.replay(aid, step)
            self.assertEqual(out["state"], "not_ready")
            self.assertEqual(out["events"], [])
            self.assertIsNone(out["bracket"])
            self.assertNotIn("staged", json.dumps(out).replace("staged_flag", ""))
        hunt = self.rec.timeline(aid, reveal=False)
        self.assertTrue(all(e["lane"] == "chat" for e in hunt["events"]))
        tool = next(e for e in hunt["events"] if e["kind"] == "tool:memory")
        self.assertEqual(tool["text"], "")
        self.assertNotIn("staged", tool)
        self.assertNotIn("Staged for approval", json.dumps(hunt))

    def test_a_gap_note_opens_the_replay_like_compare(self):
        aid = self.missed()
        self.f.save_entry(aid, "gap_note", {"text": "I trusted the title of the memory row."})
        self.assertEqual(self.rec.replay(aid, "")["state"], "ready")

    def test_empty_when_there_is_no_practice_chat(self):
        aid = self.lab(["write_approval"])
        self.to_first_check(aid)
        out = self.rec.replay(aid, "compare")
        self.assertEqual(out["state"], "empty")
        self.assertTrue(out["words"])

    def test_a_renamed_column_is_schema_changed_not_a_crash(self):
        aid = self.missed()
        con = sqlite3.connect(pathlib.Path(self.home()) / "state.db")
        con.execute("ALTER TABLE messages RENAME COLUMN content TO body")
        con.commit()
        con.close()
        out = self.rec.replay(aid, "compare")
        self.assertEqual(out["state"], "schema_changed")
        self.assertEqual(out["words"], "Hermes changed how it stores chats. Your checks still work.")
        self.assertIsNone(out["bracket"])
        # The guide still reads the run without crashing; it just has no chat.
        self.assertEqual(self.guide.events(self.attempt(aid)), [])

    def test_the_files_lane_is_the_frozen_first_check_not_a_later_folder(self):
        aid = self.missed()
        for p in (pathlib.Path(self.home()) / "pending" / "memory").glob("*.json"):
            p.unlink()  # the learner approves later; the replay still shows what the first check read
        out = self.rec.replay(aid, "compare")
        held = next(e for e in out["events"] if e["kind"] == "file:pending")
        self.assertEqual(held["at_source"], "the chat row that staged it")
        self.assertEqual(out["bracket"]["to"], held["event_id"])

    def test_the_sample_is_labelled_and_complete(self):
        sample = self.rec.sample()
        self.assertIn("Not a live Hermes recording", sample["label"])
        self.assertEqual(sample["state"], "ready")
        self.assertIsNotNone(sample["bracket"])
        self.assertTrue(sample["pins"]["pins"])
        ids = {e["event_id"] for e in sample["events"]}
        self.assertTrue(all(p["event_id"] in ids for p in sample["pins"]["pins"]))
        self.assertTrue(any(p["event_id"] in (sample["bracket"]["from"], sample["bracket"]["to"]) for p in sample["pins"]["pins"]))
        self.assertEqual((sample["compare"]["said"], sample["compare"]["of"]), (4, 4))
        self.assertIsInstance(sample["compare"]["shows"], int)

    def attempt(self, aid):
        with self.store.connect() as conn:
            return self.f._attempt(conn, aid)


class Pins(ReplayCase):
    def test_the_pin_context_carries_the_revealed_run(self):
        aid = self.missed()
        ctx = "\n".join(self.guide.pins_context(aid)["inputs"])
        self.assertIn(tmm.STAGED_MESSAGE, ctx)
        self.assertIn("pending/memory/", ctx)
        self.assertIn("Held for your approval", ctx)
        self.assertIn("staged: yes", ctx)
        self.assertIn("fill: 479 of 2200 characters, unchanged", ctx)
        self.assertIn("No new chat used the fact: NOT met", ctx)
        self.assertIn("The bracket:", ctx)

    def test_a_long_pin_is_trimmed_or_dropped_never_the_whole_call(self):
        aid = self.missed()
        bracket = self.rec.replay(aid, "compare")["bracket"]
        long_one = "Your chat said saved but it was held. " + "This sentence keeps going on and on " * 4 + "and never ends."
        too_long = "word " * 30
        self.routed(pins=[{"pins": [{"event_id": bracket["from"], "why": long_one},
                                    {"event_id": bracket["to"], "why": too_long.strip()},
                                    {"event_id": "m424242", "why": "Not real."}]}])
        out = self.guide.make_pins(aid, "compare")
        self.assertEqual(out["state"], "ready")
        self.assertEqual([p["event_id"] for p in out["pins"]], [bracket["from"]])
        self.assertEqual(out["pins"][0]["why"], "Your chat said saved but it was held.")
        self.assertEqual((out["trimmed"], out["dropped"]), (1, 2), "the pin on the files card is dropped: the card shows it")
        self.assertTrue(out["bracket_pinned"])

    def test_the_bracket_note_says_where_to_look_next_time_with_only_the_course_command(self):
        aid = self.missed()
        bracket = self.rec.replay(aid, "compare")["bracket"]
        self.routed(pins=[{"pins": [{"event_id": bracket["from"], "why": "Next time run /memory pending to see what waits."}]},
                                {"pins": [{"event_id": bracket["from"], "why": "Saved rows open collapsed; expand one, and Staged as the first word means not saved."}]}])
        out = self.guide.make_pins(aid, "compare")
        self.assertEqual([p["why"] for p in out["pins"]], ["Saved rows open collapsed; expand one, and Staged as the first word means not saved."],
                         "the row already prints its command, so a bracket note naming one is dropped; the tell is kept")
        self.assertIn("read its first word", self.guide.text.CATCH_IT["write_approval"][0])
        self.assertTrue(all(len(t.split()) <= 16 for t, _ in self.guide.text.CATCH_IT.values()), "short enough to fit a 20-word note")

    def test_no_note_sits_on_the_memory_card(self):
        aid = self.missed()
        rep = self.rec.replay(aid, "compare")
        bracket = rep["bracket"]
        meter = next(e for e in rep["events"] if e["kind"] == "file:memory")
        self.routed(pins=[{"pins": [{"event_id": bracket["from"], "why": "Saved rows open collapsed; expand one and read the first word inside."},
                                    {"event_id": meter["event_id"], "why": "MEMORY.md still shows the same size, so nothing new was added."}]}])
        out = self.guide.make_pins(aid, "compare")
        self.assertEqual([p["event_id"] for p in out["pins"]], [bracket["from"]], "the card already shows the meter")
        self.assertEqual(out["dropped"], 1)

    def test_nothing_usable_twice_is_too_long_not_bad_json(self):
        aid = self.missed()
        bracket = self.rec.replay(aid, "compare")["bracket"]
        too_long = {"pins": [{"event_id": bracket["from"], "why": ("very " * 25).strip()}]}
        llm = self.routed(pins=[too_long, too_long])
        out = self.guide.make_pins(aid, "compare")
        self.assertEqual(out["state"], "too_long")
        self.assertEqual(out["pins"], [])
        self.assertTrue(out["message"] and out["next_step"])
        self.assertEqual(len(llm.calls_for("field_academy_pins")), 2)
        self.assertIn("20 words", llm.calls_for("field_academy_pins")[1]["instructions"])

    def test_no_pin_on_the_bracket_gets_one_more_try(self):
        aid = self.missed()
        bracket = self.rec.replay(aid, "compare")["bracket"]
        llm = self.routed(pins=[{"pins": [{"event_id": "m1", "why": "You asked Hermes to remember the fact."}]},
                                {"pins": [{"event_id": bracket["from"], "why": "The row says saved, but Hermes held it."}]}])
        out = self.guide.make_pins(aid, "compare")
        self.assertEqual([p["event_id"] for p in out["pins"]], [bracket["from"]])
        self.assertTrue(out["bracket_pinned"])
        self.assertIn(bracket["from"], llm.calls_for("field_academy_pins")[0]["instructions"])


class Speed(ReplayCase):
    def test_fetching_items_carry_started_at_and_explains_run_at_once(self):
        aid = self.missed()
        llm = self.routed(nudges=[self.good_nudge(aid)])
        llm.delay = 0.4
        first = self.guide.guide_view(aid, "check")
        self.assertEqual(first["ladder"]["nudge"]["state"], "fetching")
        self.assertIsInstance(first["ladder"]["nudge"]["started_at"], float)
        import time

        started = time.monotonic()
        self.guide.wait_prefetch(aid, 10)
        took = time.monotonic() - started
        self.assertLess(took, 0.4 * 2.5, "the nudge and both Explain calls run at the same time, not one after another")
        ready = self.guide.guide_view(aid, "check")
        self.assertEqual(ready["ladder"]["nudge"]["state"], "ready")
        self.assertNotIn("started_at", ready["ladder"]["nudge"])
        self.assertTrue(all(i["state"] == "ready" for i in ready["explain"]))

    def test_do_it_with_me_starts_when_compare_opens(self):
        aid = self.missed()
        llm = self.routed(nudges=[self.good_nudge(aid)], why=[{"why": "The save is held, so approving it by its id writes it."}])
        self.view(aid)
        self.guide.guide_view(aid, "compare")
        self.guide.wait_prefetch(aid, 10, what="why")
        self.assertEqual(len(llm.calls_for("field_academy_why")), 1)
        fix = self.guide.guide_view(aid, "fix")
        self.assertEqual(fix["do_it_with_me"]["why"]["state"], "ready")
        shown = self.guide.use_help(aid, action="do_it_with_me")["shown"]
        self.assertEqual(shown["why"]["source"], "model")
        self.assertEqual(len(llm.calls_for("field_academy_why")), 1, "the press answers from the line fetched at Compare")


class Explain(ReplayCase):
    def results(self, aid):
        with self.store.connect() as conn:
            checks = self.f._checks(conn, aid)
        return {r["id"]: r for r in self.guide._visible_results(self.mission, self.guide._first_run(checks))}

    def test_the_rules(self):
        aid = self.missed()
        results = self.results(aid)
        places = self.guide.explain_places(self.mission, self.guide.events(Timeline.attempt(self, aid)), True)
        self.assertEqual([p["match"][-1] for p in places], ["memory row"],
                         "no pending folder before Compare, and not MEMORY.md, the file the check already read (Loop 2)")
        ok = ["Your fact is not in MEMORY.md yet.", "Open the memory row in your chat and read every line of it."]
        self.assertEqual(self.guide.explain_problems(ok, results["memory_line"], MID, places, True), [])
        long = ["One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
                "seventeen eighteen nineteen twenty twentyone.", ok[1]]
        self.assertTrue(self.guide.explain_problems(long, results["memory_line"], MID, places, True))
        herring = [ok[0], "Look at the memory row and USER.md, since USER.md has 0 lines."]
        self.assertIn("USER.md is not the place to look for this check",
                      self.guide.explain_problems(herring, results["memory_line"], MID, places, True))
        nowhere = [ok[0], "Think about what might have happened."]
        self.assertTrue(self.guide.explain_problems(nowhere, results["memory_line"], MID, places, True))
        giveaway = [ok[0], "Open the memory row: the save is pending."]
        self.assertTrue(self.guide.explain_problems(giveaway, results["memory_line"], MID, places, True))

    def test_the_zero_line_user_file_never_reaches_the_model(self):
        aid = self.missed()
        llm = self.routed(nudges=[self.good_nudge(aid)])
        self.view(aid, "compare")
        sent = "\n".join(b["text"] for c in llm.calls_for("field_academy_explain") for b in c["input"])
        self.assertNotIn("USER.md", sent)
        self.assertIn("Places to look", sent)
        self.assertIn("the memory row in your chat at", sent)
        self.assertIn("pending folder", sent, "after Compare the pending folder is a place to look")
        self.assertIn("this is the cause to name", sent)

    def test_a_long_reply_is_repaired_once_then_course_words(self):
        aid = self.missed()
        long = {"sentences": [("word " * 25).strip() + ".", "Open the memory row in your chat."]}
        self.routed(nudges=[self.good_nudge(aid)], explains=[long] * 8)
        self.view(aid, "compare")
        shown = self.guide.use_help(aid, action="explain", step="compare")["shown"]["explain"]
        self.assertTrue(shown)
        for item in shown:
            self.assertEqual(item["source"], "course")
            self.assertIn("memory row", item["sentences"][1])


class AskDuringTheHunt(ReplayCase):
    def test_loop1s_answer_is_regenerated_then_course_words_and_it_counts_as_help(self):
        aid = self.missed()
        llm = self.routed(ask=[LOOP1_ASK, LOOP1_ASK])
        out = self.guide.ask(aid, "Why isn't my fact in memory?", "check")
        self.assertTrue(out["held_back"])
        self.assertEqual(out["sentences"][0]["source"], "course")
        self.assertEqual(self.guide.giveaways_in(json.dumps(out["sentences"]), MID), [])
        self.assertEqual(len(llm.calls_for("field_academy_ask")), 2)
        self.assertIn("Never use these words", llm.calls_for("field_academy_ask")[1]["instructions"])
        summary = self.guide.help_summary(aid)
        self.assertEqual(summary["hunt_helps"], 1)
        self.assertNotEqual(summary["words"], "No hints used")
        self.assertTrue(self.f.verify_chain()["ok"])

    def test_a_clean_second_answer_is_kept(self):
        aid = self.missed()
        clean = {"sentences": [{"text": "Open the memory row in your first chat and read every line of it.", "source_ids": ["asof-1"]}],
                 "not_in_sources": False}
        self.routed(ask=[LOOP1_ASK, clean])
        out = self.guide.ask(aid, "Why isn't my fact in memory?", "check")
        self.assertFalse(out["held_back"])
        self.assertEqual(out["sentences"][0]["text"], clean["sentences"][0]["text"])
        self.assertEqual(self.guide.help_summary(aid)["hunt_helps"], 1)

    def test_at_compare_the_answer_may_name_it_and_is_not_a_hunt_help(self):
        aid = self.missed()
        self.routed(ask=[LOOP1_ASK])
        out = self.guide.ask(aid, "Why was it held?", "compare")
        self.assertFalse(out["held_back"])
        self.assertEqual(len(out["sentences"]), 3, "after Compare the answer may name the snag")
        self.assertEqual(self.guide.help_summary(aid)["hunt_helps"], 0)


class FirstFlight(ReplayCase):
    def start(self):
        return self.f.first_flight_start()

    def test_it_always_plants_write_approval_even_when_the_draw_would_skip_it(self):
        # An earlier try drew write_approval, so the usual draw skips it now ("not one of the last two").
        self.salt_for(["write_approval"])
        self.f.abandon(self.f.start(MID)["attempt"]["id"])
        with self.store.connect() as conn:
            history = self.f._history(conn)
        seed = self.f.seed_for("0" * 32, MID, 3)
        self.assertNotIn("write_approval", self.f.choose_plants(self.mission["lab"]["plants"], 1, history, seed))
        view = self.start()
        with self.store.connect() as conn:
            plants = json.loads(self.f._attempt(conn, view["attempt"]["id"])["plants_json"])
        self.assertEqual(plants, ["write_approval"])
        ff = view["first_flight"]
        self.assertEqual(ff["words"], "Began as a first flight; snag chosen for first flight")
        self.assertEqual(ff["skipped"], ["recall", "claim"])
        self.assertEqual(ff["guess"]["question"], "Where do you think Hermes will trip?")
        self.assertEqual(len(ff["guess"]["answers"]), 4)
        self.assertEqual([c["id"] for c in ff["guess"]["confidence"]], ["low", "medium", "high"])
        steps = {s["id"]: s["status"] for s in view["steps"]}
        self.assertEqual((steps["recall"], steps["claim"], steps["standard"]), ("skipped", "skipped", "done"))
        self.assertEqual(self.start()["attempt"]["id"], view["attempt"]["id"], "an open First Flight is returned as it is")

    def test_the_guess_is_one_tap_and_the_record_says_first_flight(self):
        aid = self.start()["attempt"]["id"]
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "prediction", {"guess": {"answer": "maybe", "confidence": "high"}})
        view = self.f.save_entry(aid, "prediction", {"guess": {"answer": "save", "confidence": "medium"}})
        self.assertEqual(view["first_flight"]["guessed"], {"answer": "save", "confidence": "medium"})
        pred = next(e["body"] for e in view["entries"] if e["kind"] == "prediction")
        self.assertEqual(pred["checks"]["s1"], {"expect_pass": False, "confidence": 75})
        self.f.open_lab(aid)
        self.ready("a")
        self.f.plant_lab(aid)
        self.save_and_use(staged=True)
        hf.stage_pending(self.home(), content=tmm.FACT)
        # The guide stays closed until the self-score is locked.
        closed = self.guide.guide_view(aid, "evidence")
        self.assertEqual((closed["enabled"], closed["off_reason"]), (False, "first_flight_locked"))
        self.assertEqual(closed["off_words"], "The Field guide opens after you answer Did it work?")
        with self.assertRaises(ValueError):
            self.guide.ask(aid, "Where should I look?", "evidence")
        self.to_first_check(aid)
        self.runtime.set_llm(FakeLlm([]))
        self.assertTrue(self.guide.guide_view(aid, "check", "practice")["enabled"], "open once the score is locked")
        body = self.f.record_preview(aid)["entry"]
        self.assertEqual(body["first_flight"]["words"], "Began as a first flight; snag chosen for first flight")
        self.assertIn("recall", body["skipped"])
        self.assertTrue(self.f.verify_chain()["ok"])

    def test_another_open_try_is_not_taken_over(self):
        self.salt_for(["memory_full"])
        self.f.start(MID)
        with self.assertRaisesRegex(ValueError, "first flight"):
            self.start()


if __name__ == "__main__":
    unittest.main()
