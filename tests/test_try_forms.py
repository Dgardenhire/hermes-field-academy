"""Every Foundations mission's Practice step has its own try note, or none (0.9 persona test, fix 1).

Before, foundations.js sent every mission outside Part A to mission 3's memory form ("Your guess: how much does Hermes
carry?", "Your Memory line, in tokens"), and whatever the learner typed went into the record as "Guessed ...; Memory
line was N tokens". These tests run each of the eleven shipped missions: its own try note saves, the memory-shaped note
is refused where it doesn't belong, the record entry reads the try in the mission's own labels, and the page's router
(tryFormKind in desktop/src/loop_b.js, run with node) picks the right form for each mission.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from foundations_support import FoundationsCase  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORDER = ["f.loop", "f.cost", "f.memory", "f.new-chats", "f.skills", "f.profiles", "f.connectors", "f.schedules", "f.safety",
         "f.diagnose", "f.review"]
EXPECTED_KIND = {"f.loop": "a", "f.cost": "a", "f.memory": "memory", "f.new-chats": "a", "f.skills": "a", "f.profiles": "a",
                 "f.connectors": "fields", "f.schedules": "fields", "f.safety": "fields", "f.diagnose": "fields", "f.review": "none"}
MEMORY_NOTE = {"guess": "A page or so", "memory_tokens": "260"}


def sample_value(field, lab):
    """A valid answer for one field, from its own rules."""
    kind = field.get("kind", "text")
    if kind in ("int", "number"):
        return max(int(field.get("min", 0)), 3)
    if kind == "bool":
        return True
    if kind == "choice":
        choices = field.get("choices") or lab.get(field.get("choices_from", ""), [])
        first = choices[0]
        return first.get("value", first.get("id"))
    if kind == "lines":
        return "\n".join(f"Line number {n} of the answer" for n in range(1, int(field.get("min_lines", 1)) + 2))
    text = "A short, honest answer for this field."
    return (text * 4)[: max(int(field.get("min", 1)), len(text))]


class TryForms(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.f = self.mod("foundations")
        self.f.CONTENT_DIR = None
        self.content = self.mod("foundations_content")
        self.content.clear_cache()

    def opened(self, mid):
        mission = self.content.get(mid)
        aid = self.f.start(mid)["attempt"]["id"]
        self.f.save_entry(aid, "recall", {"answers": ["One answer from memory." for _ in mission["recall"]["prompts"]]})
        if mission.get("level") == "advanced":
            self.f.save_entry(aid, "claim", {"text": "I can do this small job in Hermes and account for it with evidence.", "author": "learner"})
        else:
            self.f.save_entry(aid, "claim", {"text": mission["claim"]["text"], "author": "course"})
        checks = [{"id": c["id"], "text": c["text"]} for c in mission["standard"]]
        self.f.save_entry(aid, "standard", {"checks": checks})
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 70} for c in checks},
                                              "where_wrong": "Somewhere in the planted setup."})
        self.f.open_lab(aid)
        return mission, aid

    def own_note(self, mission):
        lab = mission.get("lab") or {}
        if lab.get("try_fields"):
            return {f["id"]: sample_value(f, lab) for f in lab["try_fields"]}
        if (lab.get("note_fields_a") or {}).get("try"):
            return {f["id"]: sample_value(f, lab) for f in lab["note_fields_a"]["try"]}
        return dict(MEMORY_NOTE)

    def tries(self, aid):
        return [e["body"] for e in self.f.attempt_view(aid)["entries"] if e["kind"] == "try_note"]

    def check_mission(self, mid):
        mission, aid = self.opened(mid)
        kind = EXPECTED_KIND[mid]
        if kind == "none":
            with self.assertRaises(ValueError):
                self.f.save_entry(aid, "try_note", MEMORY_NOTE)
            with self.assertRaises(ValueError):
                self.f.save_entry(aid, "try_note", {"anything": "at all"})
            self.assertEqual(self.tries(aid), [])
            self.assertEqual(self.f.record_preview(aid)["entry"]["try_lines"], [])
            return
        if kind != "memory":
            # The memory mission's note never lands in another mission's attempt.
            with self.assertRaises(ValueError):
                self.f.save_entry(aid, "try_note", MEMORY_NOTE)
            self.assertEqual(self.tries(aid), [])
        note = self.own_note(mission)
        self.f.save_entry(aid, "try_note", note)
        saved = self.tries(aid)[-1]
        self.assertNotIn("memory_tokens", saved) if kind != "memory" else self.assertEqual(saved["memory_tokens"], 260)
        lines = self.f.record_preview(aid)["entry"]["try_lines"]
        self.assertTrue(lines, f"{mid}: the record entry has no try lines")
        labels = [line["label"] for line in lines]
        if kind == "memory":
            self.assertEqual(labels, ["Your guess: how much Hermes carries", "Your Memory line"])
            return
        lab = mission["lab"]
        own = [f["label"] for f in (lab.get("try_fields") or lab["note_fields_a"]["try"])]
        self.assertEqual(labels, [label for label in own if label in labels])
        self.assertTrue(set(labels) <= set(own), f"{mid}: {labels} are not the mission's own labels")
        text = json.dumps(lines)
        self.assertNotIn("Memory line", text)
        self.assertNotIn("how much Hermes carries", text)
        # Choices read as their labels, never as raw values.
        for field in lab.get("try_fields") or []:
            if field.get("kind") == "choice" and field["id"] in note:
                label = next(c["label"] for c in field["choices"] if c["value"] == note[field["id"]])
                self.assertIn({"label": field["label"], "value": label}, lines)

    def test_mission_1_loop(self):
        self.check_mission("f.loop")

    def test_mission_2_cost(self):
        self.check_mission("f.cost")

    def test_mission_3_memory(self):
        self.check_mission("f.memory")

    def test_mission_4_new_chats(self):
        self.check_mission("f.new-chats")

    def test_mission_5_skills(self):
        self.check_mission("f.skills")

    def test_mission_6_profiles(self):
        self.check_mission("f.profiles")

    def test_mission_7_connectors(self):
        self.check_mission("f.connectors")

    def test_mission_8_schedules(self):
        self.check_mission("f.schedules")

    def test_mission_9_safety(self):
        self.check_mission("f.safety")

    def test_mission_10_diagnose(self):
        self.check_mission("f.diagnose")

    def test_mission_11_review_has_no_try_note(self):
        self.check_mission("f.review")

    def test_required_try_fields_are_required(self):
        mission, aid = self.opened("f.safety")
        with self.assertRaises(ValueError) as cm:
            self.f.save_entry(aid, "try_note", {"asked": "yes"})
        self.assertIn("needed", str(cm.exception))
        with self.assertRaises(ValueError):
            self.f.save_entry(aid, "try_note", {"guess_asks": "maybe", "guess_undo": "no"})
        self.f.save_entry(aid, "try_note", {"guess_asks": "yes", "guess_undo": "no", "extra": "dropped"})
        self.assertEqual(self.tries(aid)[-1], {"guess_asks": "yes", "guess_undo": "no"})

    def test_try_fields_never_collide_with_a_missions_lab_note(self):
        for mid in ORDER:
            lab = self.content.get(mid).get("lab") or {}
            ids = [f["id"] for f in lab.get("try_fields") or []]
            self.assertEqual(len(ids), len(set(ids)), mid)
            for f in lab.get("try_fields") or []:
                self.assertIn(f.get("kind", "text"), ("text", "long", "choice", "number"), f"{mid}: {f['id']}")

    def test_the_page_picks_each_missions_own_form(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed, so the page's router can't run here")
        missions = {mid: self.content.public(self.content.get(mid)) for mid in ORDER}
        script = ("import { tryFormKind } from %s;\n"
                  "import { showsMemory } from %s;\n"
                  "const ms = JSON.parse(process.argv[1]);\n"
                  "const out = {};\n"
                  "for (const [id, m] of Object.entries(ms)) out[id] = [tryFormKind(m), showsMemory(m)];\n"
                  "console.log(JSON.stringify(out));\n") % (json.dumps((ROOT / "desktop" / "src" / "loop_b.js").as_uri()),
                                                             json.dumps((ROOT / "desktop" / "src" / "loop.js").as_uri()))
        result = subprocess.run([node, "--input-type=module", "-e", script, json.dumps(missions)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        got = json.loads(result.stdout)
        self.assertEqual({k: v[0] for k, v in got.items()}, EXPECTED_KIND)
        memory = {k for k, v in got.items() if v[1]}
        self.assertEqual(memory, {"f.memory", "f.new-chats", "f.skills", "f.schedules", "f.review"})

    def test_the_bundle_routes_the_try_and_drops_the_old_fallback(self):
        source = (ROOT / "desktop" / "src" / "foundations.js").read_text(encoding="utf-8")
        self.assertIn("tryFormKind(mission)", source)
        self.assertIn("B.TryForm", source)
        built = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
        for words in ("Save my guesses", "The try, before the lesson"):
            self.assertTrue(words in built, f"the bundle lacks {words!r}; rebuild desktop/plugin.js")


if __name__ == "__main__":
    unittest.main()
