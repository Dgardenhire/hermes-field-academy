"""Loop 3 (the live gate on Hermes 0.23, Nov 9 2026): what the real run showed, fixed and pinned here.

1. Hermes 0.23 stages a memory call as one ``batch`` payload, with the note inside ``operations`` and a summary that
   reads "apply 1 op(s) to memory: - add: ...". Field Academy read only ``payload.content``, so the page showed that
   raw summary. The held save now reads as the note itself.
2. The home card did not offer to resume a First Flight under way. The Foundations snapshot now says how far each
   attempt got (``stage``), and the card uses it.

The page side (the plain sentence, the resume words, Compare's Retry) is pinned in tests/desk.test.mjs.
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
import test_field_record as tfr  # noqa: E402

FACT = "Harbor Bakery uses QuickBooks Online; the other five clients use Xero."


def stage_batch(home, ops, created_at=None):
    """A record exactly as Hermes 0.23 lays one down for a memory call with ``operations`` (tools/memory_tool.py
    _apply_write_gate, then tools/write_approval.stage_write)."""
    pid = uuid.uuid4().hex[:8]
    lines = "\n".join(f"- {op['action']}: {op.get('content') or op.get('old_text') or ''}" for op in ops)
    record = {"id": pid, "subsystem": "memory", "action": "batch",
              "summary": f"apply {len(ops)} op(s) to memory: {lines[:120]}", "origin": "foreground",
              "created_at": created_at if created_at is not None else hf.T0,
              "payload": {"action": "batch", "target": "memory", "operations": ops}}
    folder = pathlib.Path(home) / "pending" / "memory"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{pid}.json").write_text(json.dumps(record), encoding="utf-8")
    return record


class HeldSave(tfr.RecordCase):
    def test_a_batch_of_one_reads_as_its_note_not_hermess_summary(self):
        home = self.home()
        stage_batch(home, [{"action": "add", "content": FACT}])
        item = self.hermes_read.pending(home)["memory"][0]
        self.assertEqual((item["action"], item["content"]), ("add", FACT))
        words = self.hermes_read.pending_words(item)
        self.assertEqual(words, f"add {FACT}")
        self.assertNotIn("op(s)", words)

    def test_the_raw_record_and_the_listed_item_give_the_same_words(self):
        # recorder._pending_created_at matches the two, so they must agree or the held save loses its own time.
        home = self.home()
        record = stage_batch(home, [{"action": "add", "content": FACT}])
        item = self.hermes_read.pending(home)["memory"][0]
        self.assertEqual(self.hermes_read.pending_words(record), self.hermes_read.pending_words(item))

    def test_a_record_with_only_the_summary_still_reads_plainly(self):
        self.assertEqual(self.hermes_read.summary_words(f"apply 1 op(s) to memory: - add: {FACT}"), f"add {FACT}")
        self.assertEqual(self.hermes_read.pending_words({"summary": f"apply 1 op(s) to memory: - add: {FACT[:40]}"}), f"add {FACT[:40]}")
        self.assertEqual(self.hermes_read.summary_words("add Harbor Bakery"), "add Harbor Bakery")

    def test_a_batch_of_two_keeps_both_notes(self):
        home = self.home()
        stage_batch(home, [{"action": "add", "content": "One."}, {"action": "add", "content": "Two."}])
        item = self.hermes_read.pending(home)["memory"][0]
        self.assertIn("One.", item["content"])
        self.assertIn("Two.", item["content"])

    def test_the_old_single_save_shape_is_unchanged(self):
        home = self.home()
        hf.stage_pending(home, content=FACT)
        item = self.hermes_read.pending(home)["memory"][0]
        self.assertEqual(self.hermes_read.pending_words(item), f"add {FACT}")


class ResumeStage(tfr.RecordCase):
    def stage(self):
        m = next(m for m in self.f.snapshot()["missions"] if m["id"] == tfr.tmm.MID)
        return m["attempts"][-1]["stage"]

    def test_the_snapshot_says_how_far_an_attempt_got(self):
        aid = self.f.start(tfr.tmm.MID)["attempt"]["id"]
        self.assertEqual(self.stage(), "guess")

    def test_practice_then_checked(self):
        aid = self.lab(["write_approval"])
        self.assertEqual(self.stage(), "practice")
        self.save_and_use(staged=True)
        self.to_first_check(aid)
        self.assertEqual(self.stage(), "checked")


if __name__ == "__main__":
    unittest.main()
