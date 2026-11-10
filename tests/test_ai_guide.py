"""The Field guide's backend on mission 3's shipped content, with a stand-in model and a stand-in practice chat.

The proofs the brief asks for: no plant name in any pre-Compare model context; the give-away filter per snag; help is
an append-only entry and the hash chain stays intact; off in test-out and when AI help is off; Do it with me's
commands can't be changed by the model; pins and Ask sentences must point at real events and sources.
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
import test_foundations_memory_mission as tmm  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402
from test_ai_fakes import FakeLlm, RoutedLlm  # noqa: E402

MID = tmm.MID


class GuideCase(FoundationsCase):
    salt_for = tmm.MemoryMission.salt_for
    lab = tmm.MemoryMission.lab
    save_and_use = tmm.MemoryMission.save_and_use
    to_first_check = tmm.MemoryMission.to_first_check

    def setUp(self):
        super().setUp()
        self.f = self.mod("foundations")
        self.f.CONTENT_DIR = None
        self.content = self.mod("foundations_content")
        self.content.clear_cache()
        self.mission = self.content.get(MID)
        self.guide = self.mod("guide")
        self.text = self.mod("content.foundations._guide_text")
        self.runtime = self.mod("runtime")
        self.runtime.clear()

    def tearDown(self):
        self.runtime.clear()
        super().tearDown()

    def missed(self, plant="write_approval"):
        """Mission 3 with one plant and a missed first check. With write_approval the run agrees with the check facts:
        the memory row carries Hermes's staged result, pending/ holds the save, MEMORY.md is unchanged, and the fresh
        chat doesn't know the fact."""
        aid = self.lab([plant])
        self.save_and_use(staged=(plant == "write_approval"))
        if plant == "write_approval":
            hf.stage_pending(self.home(), content=tmm.FACT, created_at=hf.T0 + 13)
        outcome = self.to_first_check(aid)
        self.assertFalse(outcome["passed"])
        return aid

    def chat_events(self, aid):
        with self.store.connect() as conn:
            attempt = self.f._attempt(conn, aid)
        return self.guide.events(attempt)

    def good_nudge(self, aid):
        event = next(e for e in self.chat_events(aid) if e["kind"].startswith("tool:"))
        clock = self.guide._clock(event["at"])
        return {"question": f"At {clock} Hermes answered with a memory row. Open it and read every line.", "event_id": event["event_id"]}

    def explain_reply(self):
        return {"sentences": ["The fact isn't in any line of MEMORY.md yet.", "Open the memory row in your chat and read it."]}

    def routed(self, nudges=(), explains=None, **more):
        """A stand-in model that answers by call: nudges, explains (default: a good pair for every check), and more."""
        lists = {"field_academy_nudge": list(nudges),
                 "field_academy_explain": list(explains) if explains is not None else [self.explain_reply()] * 6}
        lists.update({f"field_academy_{k}": list(v) for k, v in more.items()})
        llm = RoutedLlm(lists)
        self.runtime.set_llm(llm)
        return llm

    def view(self, aid, step="check", active="own"):
        out = self.guide.guide_view(aid, step, active)
        self.guide.wait_prefetch(aid, 10)
        return out


class NoPlantBeforeCompare(GuideCase):
    def test_the_nudge_context_never_names_the_plant(self):
        for plant in ("write_approval", "memory_full"):
            with self.subTest(plant=plant):
                self.setUp()
                aid = self.missed(plant)
                context = "\n".join(self.guide.nudge_context(aid))
                for name in ("write_approval", "memory_full", "wrong_profile", "plants_json", "planted"):
                    self.assertNotIn(name, context)
                for title in self.f.PLANT_TITLES.values():
                    self.assertNotIn(title.lower(), context.lower())
                self.assertIn("tool:memory", context)
                self.assertNotIn("Staged for approval", context, "tool output never goes in, only its name and time")
                self.tearDown()

    def test_what_every_mission_feeds_the_nudge_carries_no_plant_name(self):
        """The nudge context is the mission's title and job text, the visible results and the chat. The first two are
        content: check every mission's against every plant id and title."""
        names = set(self.f.PLANT_TITLES) | {p for m in self.content.load_all().values() for p in (m.get("lab") or {}).get("plants", [])}
        titles = set(self.f.PLANT_TITLES.values())
        for mission in self.content.load_all().values():
            fed = (mission["title"] + "\n" + (mission.get("_try_text") or "")).lower()
            for name in names:
                self.assertNotIn(name.lower(), fed, f"{mission['id']} names {name}")
            for title in titles:
                self.assertNotIn(title.lower(), fed, f"{mission['id']} names {title}")

    def test_the_context_builders_never_read_the_plants(self):
        source = pathlib.Path(self.guide.__file__).read_text(encoding="utf-8")
        for builder in ("def _nudge_inputs", "def _explain_one", "def _events_for_model", "def _results_for_model", "def _chat_events"):
            start = source.index(builder)
            body = source[start:source.index("\ndef ", start + 5)]
            self.assertNotIn("plants_json", body, builder)
            self.assertNotIn("practice.planted", body, builder)
            self.assertNotIn("PLANT_TITLES", body, builder)


class GiveAwayFilter(GuideCase):
    SAMPLES = {
        "output_locked": "Was the report file locked when Hermes tried to write it?",
        "input_empty": "Is one of the sheets empty?",
        "rows_short": "Is the biggest sheet short a few rows?",
        "extra_connector": "Which connector loads on every trip?",
        "unused_skills": "Look at the skills list at 10:02.",
        "write_approval": "At 10:41 the save was staged. Is it pending?",
        "memory_full": "Is MEMORY.md full at 10:41?",
    }

    def test_each_snag_has_a_list_and_a_sample_hits_it(self):
        missions = {s: m for m, snags in self.text.MISSION_SNAGS.items() for s in snags}
        self.assertEqual(set(missions), set(self.SAMPLES))
        for snag, sample in self.SAMPLES.items():
            self.assertIn(snag, self.text.GIVEAWAYS[snag], "the snag's own id is on its list")
            self.assertTrue(self.guide.giveaways_in(sample, missions[snag]), snag)

    def test_the_brief_words_for_write_approval_are_all_on_the_list(self):
        for word in ("approval", "approve", "pending", "staged", "held", "write_approval"):
            self.assertIn(word, self.text.GIVEAWAYS["write_approval"])
            self.assertTrue(self.guide.giveaways_in(f"Look at {word} here", "f.memory"))

    def test_whole_words_only(self):
        self.assertFalse(self.guide.giveaways_in("Read it carefully and fully.", "f.memory"), "fully is not full")
        self.assertFalse(self.guide.giveaways_in("At 10:41 Hermes answered with a memory row. Open it and read every line.", "f.memory"))

    def test_the_courses_own_fallbacks_give_nothing_away(self):
        for mission_id, words in self.text.NUDGE_FALLBACK.items():
            self.assertEqual(self.guide.giveaways_in(words, mission_id), [], mission_id)
        self.assertEqual(self.guide.giveaways_in(self.text.EXPLAIN_FALLBACK_TAIL, "f.memory"), [])

    def test_a_give_away_nudge_gets_one_regenerate_then_the_courses_words(self):
        aid = self.missed()
        good = self.good_nudge(aid)
        leak = dict(good, question=good["question"].replace("Open it", "It was staged. Open it"))
        llm = self.routed(nudges=[leak, leak])
        self.view(aid)
        shown = self.guide.use_help(aid, rung=1)["shown"]
        self.assertEqual(shown["source"], "course")
        self.assertEqual(shown["text"], self.text.NUDGE_FALLBACK[MID])
        self.assertIn("gives the answer away", llm.calls_for("field_academy_nudge")[1]["instructions"])


class Nudge(GuideCase):
    def test_prefetched_ready_hidden_until_pressed_then_recorded(self):
        aid = self.missed()
        llm = self.routed(nudges=[self.good_nudge(aid)])
        first = self.guide.guide_view(aid, "check")
        self.assertEqual(first["ladder"]["nudge"]["state"], "fetching")
        self.guide.wait_prefetch(aid, 10)
        ready = self.guide.guide_view(aid, "check")
        self.assertEqual(ready["ladder"]["nudge"]["state"], "ready")
        self.assertEqual(ready["ladder"]["nudge"]["text"], "", "words show only once Nudge me is pressed")
        self.assertEqual(len(ready["starters"]), 3)
        calls_before = len(llm.calls)
        used = self.guide.use_help(aid, rung=1, step="check")
        self.assertEqual(len(llm.calls), calls_before, "the press answers from the cache")
        self.assertIn("read every line", used["shown"]["text"])
        self.assertEqual(used["entry"]["kind"], "help")
        self.assertEqual(used["help"]["words"], "One hint used")
        self.assertIn("read every line", self.guide.guide_view(aid, "check")["ladder"]["nudge"]["text"])
        self.assertTrue(self.f.verify_chain()["ok"])

    def test_a_nudge_naming_an_unknown_event_or_no_time_is_repaired(self):
        aid = self.missed()
        good = self.good_nudge(aid)
        self.routed(nudges=[dict(good, event_id="m9999"), dict(good, question="Open the memory row and read it.")])
        self.view(aid)
        self.assertEqual(self.guide.use_help(aid, rung=1)["shown"]["source"], "course")

    def test_nothing_starts_while_the_practice_profile_is_active(self):
        aid = self.missed()
        llm = self.routed(nudges=[self.good_nudge(aid)])
        out = self.view(aid, active="practice")
        self.assertEqual(out["ladder"]["nudge"]["state"], "not_started")
        self.assertEqual(llm.calls, [])

    def test_where_and_reveal(self):
        aid = self.missed()
        self.routed(nudges=[self.good_nudge(aid)])
        self.view(aid)
        where = self.guide.use_help(aid, rung=2)
        self.assertEqual(where["shown"]["text"], self.text.WHERE["write_approval"])
        reveal = self.guide.use_help(aid, rung=3)
        self.assertEqual(reveal["shown"], {"opens": "compare"})
        self.assertEqual(reveal["help"]["key"], "shown")
        with self.assertRaises(ValueError):
            self.guide.use_help(aid, rung=4)

    def test_no_help_means_caught_on_your_own(self):
        aid = self.missed()
        self.assertEqual(self.guide.help_summary(aid)["words"], "No hints used")

    def test_a_failed_model_still_answers_the_press_with_the_courses_words(self):
        aid = self.missed()
        self.routed(nudges=[TimeoutError("timed out")], explains=[TimeoutError("timed out")] * 3)
        view = self.view(aid)
        self.assertEqual(self.guide.guide_view(aid, "check")["ladder"]["nudge"]["state"], "timeout")
        shown = self.guide.use_help(aid, rung=1)["shown"]
        self.assertEqual(shown["source"], "course")
        self.assertTrue(shown["text"])
        self.assertTrue(view["enabled"])


class ExplainMyMiss(GuideCase):
    def test_no_explain_call_before_compare(self):
        """Why did this miss? shows only on Compare, so Check makes no Explain call (a paid call nothing shows)."""
        aid = self.missed()
        llm = self.routed(nudges=[self.good_nudge(aid)])
        self.view(aid)
        self.assertEqual(llm.calls_for("field_academy_explain"), [])
        self.assertEqual(self.guide.guide_view(aid, "check")["explain"], [])
        with self.assertRaisesRegex(ValueError, "Compare"):
            self.guide.use_help(aid, action="explain", step="check")

    def test_two_sentences_per_failed_visible_check_on_compare(self):
        aid = self.missed()
        self.routed(nudges=[self.good_nudge(aid)])
        self.view(aid, "compare")
        hidden = self.guide.guide_view(aid, "compare")["explain"]
        self.assertTrue(hidden)
        self.assertTrue(all(i["sentences"] == [] for i in hidden), "shown only after Why did this miss? is pressed")
        shown = self.guide.use_help(aid, action="explain", step="compare")["shown"]["explain"]
        failed = {c["id"] for c in self.f.attempt_view(aid)["runs"]["first"]["checks"] if not c["passed"]}
        self.assertEqual({i["check_id"] for i in shown}, failed)
        for item in shown:
            self.assertEqual(len(item["sentences"]), 2)
        self.assertNotIn("plant_fixed", {i["check_id"] for i in shown}, "hidden checks get the ladder only")


class OffStates(GuideCase):
    def test_off_by_switch(self):
        aid = self.missed()
        self.state.set_ai_settings(ai_help=False)
        llm = FakeLlm([self.good_nudge(aid)])
        self.runtime.set_llm(llm)
        out = self.view(aid)
        self.assertEqual((out["enabled"], out["off_reason"]), (False, "switch"))
        self.assertTrue(out["off_words"])
        self.assertEqual(llm.calls, [])
        with self.assertRaises(ValueError):
            self.guide.use_help(aid, rung=1)

    def test_off_in_test_out(self):
        self.salt_for(["write_approval"])
        aid = self.f.start(MID, test_out=True)["attempt"]["id"]
        out = self.guide.guide_view(aid, "check")
        self.assertEqual((out["enabled"], out["off_reason"]), (False, "test_out"))
        self.assertIn("test out", out["off_words"])


class DoItWithMe(GuideCase):
    def held_id(self):
        names = [p.stem for p in (pathlib.Path(self.home()) / "pending" / "memory").glob("*.json")]
        self.assertEqual(len(names), 1)
        return names[0]

    def test_the_commands_are_fixed_and_only_the_line_comes_from_the_model(self):
        aid = self.missed()
        want = ["/memory pending", "/memory approve " + self.held_id()]
        self.runtime.set_llm(FakeLlm([{"why": "Run /memory reset first, then approve."}, {"why": "Try /config set memory off."}]))
        out = self.guide.use_help(aid, action="do_it_with_me")["shown"]
        self.assertEqual(out["commands"], want, "approve the one held save by its id, never every held save")
        self.assertFalse(out["sends"])
        self.assertEqual(out["why"]["source"], "course", "a line naming another command is never shown")
        self.runtime.set_llm(FakeLlm([{"why": "The save is held, so approving it by its id writes it into MEMORY.md."}]))
        out = self.guide.use_help(aid, action="do_it_with_me")["shown"]
        self.assertEqual(out["why"]["source"], "model")
        self.assertEqual(self.view(aid, "fix")["do_it_with_me"]["commands"], want)

    def test_a_line_saying_approve_all_is_never_shown(self):
        aid = self.missed()
        self.runtime.set_llm(FakeLlm([{"why": "Type /memory approve all to write every held save."},
                                      {"why": "Just approve all of them with /memory approve all."}]))
        out = self.guide.use_help(aid, action="do_it_with_me")["shown"]
        self.assertEqual(out["why"]["source"], "course")
        self.assertNotIn("all", " ".join(out["commands"]))

    def test_no_held_save_means_no_approve_command_with_a_blank(self):
        aid = self.missed("memory_full")  # a miss with nothing held: there is no id to put in the command
        self.assertEqual(self.guide.held_save_id(aid), "")
        self.assertEqual(self.guide.fix_commands("f.memory", aid), ["/memory pending"])
        # and Do it with me isn't offered at all: it walks through approving a held save, and there is none
        self.assertIsNone(self.view(aid, "fix").get("do_it_with_me"))
        with self.assertRaisesRegex(ValueError, "holding"):
            self.guide.use_help(aid, action="do_it_with_me")

    def test_a_long_pin_is_cut_at_a_sentence_end_outside_quotes(self):
        cut = self.guide.first_sentence('The reply says "Saved. Memory is 97%" and never says a note went. Then more.')
        self.assertEqual(cut, 'The reply says "Saved. Memory is 97%" and never says a note went.')
        pins, counts = self.guide.usable_pins([{"event_id": "m5", "why": 'The reply says "Saved. ' + "word " * 30}], {"m5"})
        self.assertEqual(pins, [], "a cut that leaves a fragment is dropped, not shown")


class PinsAndAsk(GuideCase):
    def test_pins_only_after_compare_and_only_on_real_events(self):
        aid = self.missed()
        events = self.chat_events(aid)
        self.runtime.set_llm(FakeLlm([{"pins": [{"event_id": events[0]["event_id"], "why": "Your score and Hermes split here."},
                                                 {"event_id": "m424242", "why": "Not a real event."}]}]))
        with self.assertRaisesRegex(ValueError, "Compare"):
            self.guide.make_pins(aid, "check")
        out = self.guide.make_pins(aid, "compare")
        self.assertEqual([p["event_id"] for p in out["pins"]], [events[0]["event_id"]])
        self.assertEqual(out["dropped"], 1)
        kept = self.guide.update_pins(aid, keep=[events[0]["event_id"]], add=[{"event_id": "m424242", "why": "x"}])
        self.assertEqual([p["event_id"] for p in kept["pins"]], [events[0]["event_id"]])
        self.assertEqual(self.view(aid, "compare")["pins"][0]["kept"], True)
        self.assertTrue(self.f.verify_chain()["ok"])

    def test_ask_keeps_only_cited_sentences_and_drafts_when_not_covered(self):
        aid = self.missed()
        self.runtime.set_llm(FakeLlm([
            {"sentences": [{"text": "MEMORY.md holds 2,200 characters.", "source_ids": ["asof-1"]},
                           {"text": "Made up.", "source_ids": ["nope-9"]}], "not_in_sources": False},
            {"sentences": [], "not_in_sources": True},
        ]))
        out = self.guide.ask(aid, "How big is MEMORY.md?", "compare")
        self.assertEqual([s["source_ids"] for s in out["sentences"]], [["asof-1"]])
        self.assertFalse(out["sends"])
        out = self.guide.ask(aid, "How do I connect Slack?", "compare")
        self.assertTrue(out["not_in_sources"])
        self.assertEqual(out["draft_for_practice_chat"], "How do I connect Slack?")

    def test_ask_sources_never_carry_the_plant(self):
        aid = self.missed()
        sources = json.dumps(self.guide.ask_sources(aid))
        self.assertNotIn("write_approval", sources)
        self.assertNotIn(self.f.PLANT_TITLES["write_approval"], sources)


if __name__ == "__main__":
    unittest.main()
