"""The Field Record read by a stranger in five minutes (0.9 persona test, the hiring manager).

record.md now opens with a verdict line, captions each excerpt with the check it backs and what that check found,
gives every date its time, never ends an excerpt inside a word, labels a claim kept in the course's words as the
course's, says "not graded" instead of "not graded yet" in a saved record, and ends each entry with questions to ask the
holder. README.txt keeps its honesty about what the checks don't prove. Built on mission 3's shipped content with a
stand-in Hermes root; nothing runs Hermes.
"""

from __future__ import annotations

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
import test_field_record as tfr  # noqa: E402

FACT = tfr.tmm.FACT


class Reader(tfr.RecordCase):
    def md(self, **kw):
        out = self.issue(**kw)
        return (pathlib.Path(out["folder"]) / "record.md").read_text(encoding="utf-8"), out

    def test_the_record_opens_with_a_verdict_line_counted_from_the_body(self):
        aid = self.finished()
        self.f.submit_explanation(aid, "The save can be staged, so check the row, the file and a new chat. " * 3)
        self.f.grade_rubric(tfr.tmm.MID, f"explain@{aid}", 3, "Three causes, each with a check.")
        self.f.add_to_record(aid, confirmed=True)
        md, _ = self.md()
        head = md.split("## Scope")[0]
        self.assertIn("**Verdict:**", head)
        verdict = re.search(r"\*\*Verdict:\*\* (.*?) \*\(", head).group(1)
        self.assertEqual(verdict, f"1 of {len(self.fr._missions())} missions passed (1 the first time). 1 planted problem caught, 0 missed. "
                                  "Explanations graded by the holder's own Hermes. No outside review.")
        self.assertEqual(self.fr.preview("Ada", tfr.LIMITS)["verdict"], verdict)

    def test_each_excerpt_says_which_check_it_backs_and_what_that_check_found(self):
        self.added()
        md, _ = self.md()
        evidence = md.split("**Evidence:**")[1].split("**Ask the holder:**")[0]
        items = [line for line in evidence.splitlines() if line.startswith("- **")]
        self.assertTrue(items)
        for line in items:
            self.assertRegex(line, r"^- \*\*Backs (check \d|the transfer task|a check Field Academy ran)")
        session = next(line for line in items if "`state.db`" in line and "Backs check 2" in line)
        self.assertIn("A brand-new chat uses the fact without you mentioning it.", session)
        self.assertIn("What the check found: Saved at:", session)
        self.assertIn("The chat that used it started:", session)
        self.assertTrue(any("Backs check 1" in line and "MEMORY.md" in line for line in items))
        body = self.fr.build("Ada", tfr.LIMITS)
        backs = {ev["check"]: ev["backs"] for ev in body["entries"][0]["evidence"]}
        self.assertEqual(backs["memory_line"]["n"], 1)
        self.assertEqual(backs["fresh_use"]["n"], 2)
        self.assertEqual(backs["user_line"]["label"], "Backs the transfer task")

    def test_dates_carry_their_times(self):
        self.added()
        md, _ = self.md()
        dates = next(line for line in md.splitlines() if line.startswith("- **Dates:**"))
        self.assertEqual(len(re.findall(r"\d{4}, \d{2}:\d{2} UTC", dates)), 3, dates)
        self.assertRegex(md, r"Added [A-Z][a-z]+ \d+, \d{4}, \d{2}:\d{2} UTC\.")
        self.assertRegex(md, r"read [A-Z][a-z]+ \d+, \d{4}, \d{2}:\d{2} UTC\.")
        self.assertRegex(md, r"\*\*Standard, frozen [A-Z][a-z]+ \d+, \d{4}, \d{2}:\d{2} UTC:\*\*")

    def test_a_held_save_is_kept_whole_never_cut_inside_a_word(self):
        aid = self.lab(["write_approval"])
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"], None)
        hf.stage_pending(self.home(), content=FACT)
        self.save_and_use(staged=True)
        self.to_first_check(aid)
        # The planted problem's check is hidden on the page, so its excerpts show in the record entry.
        pending = [e for e in self.f.record_preview(aid)["entry"]["evidence"] if e["kind"] == "pending"]
        self.assertTrue(pending)
        self.assertEqual(pending[0]["excerpt"], f"add {FACT}")
        checks = self.mod("foundations_checks")
        # Hermes's own summary is cut at 40 characters; with no content the summary is all there is, as before.
        self.assertEqual(checks._pending_words({"summary": "add Harbor Bakery uses QuickBooks Online; th"}), "add Harbor Bakery uses QuickBooks Online; th")
        self.assertEqual(checks._pending_words({"action": "replace", "content": "Shifts start at 7."}), "replace Shifts start at 7.")

    def test_no_kept_excerpt_ends_inside_a_word(self):
        aid = self.lab(["write_approval"])
        long_fact = FACT + ". " + "Payroll runs every second Friday from the shared calendar " * 8
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"], None)
        hf.stage_pending(self.home(), content=long_fact)
        self.save_and_use(staged=True)
        self.to_first_check(aid)
        evidence = self.f.record_preview(aid)["entry"]["evidence"]
        self.assertTrue(any(ev["kind"] == "pending" and ev["excerpt"].endswith("…") for ev in evidence))
        for ev in evidence:
            text = ev["excerpt"]
            if text.endswith("…"):
                head = text[:-1]
                source = f"add {long_fact}" if ev["kind"] == "pending" else None
                if source:
                    self.assertTrue(source.startswith(head))
                    self.assertIn(source[len(head)], " \n", f"cut inside a word: {text[-30:]!r}")

    def test_a_claim_in_the_courses_words_is_labelled_the_courses(self):
        self.added()
        md, _ = self.md()
        claim = next(line for line in md.splitlines() if line.startswith("**Claim:**"))
        self.assertIn("*(Field Academy's course wrote it, and the holder kept it.)*", claim)
        self.assertNotIn("The holder wrote it", claim)
        self.assertEqual(self.fr._claim_tag("learner"), "you wrote it")
        self.assertEqual(self.fr._words(self.fr._claim_tag("learner")), "the holder wrote it")

    def test_a_saved_record_never_says_not_graded_yet(self):
        self.added()
        md, _ = self.md()
        self.assertNotIn("Not graded yet", md)
        self.assertNotIn("not graded yet", md)
        self.assertIn("*(The holder wrote it, not graded.)*", md)

    def test_each_entry_ends_with_questions_for_the_holder(self):
        self.added()
        md, _ = self.md()
        ask = md.split("**Ask the holder:**")[1].split("Entry fingerprint")[0]
        questions = [line for line in ask.splitlines() if line.startswith("- ")]
        self.assertTrue(2 <= len(questions) <= 3, questions)
        self.assertTrue(any("Saves waited for approval" in q for q in questions))
        self.assertTrue(all(q.rstrip().endswith("?") for q in questions))

    def test_fingerprints_are_short_in_the_text_and_whole_in_the_data(self):
        self.added()
        md, out = self.md()
        body = self.fr.build("Ada", tfr.LIMITS)
        sha = body["entries"][0]["evidence"][0]["sha256"]
        kept = [ev for ev in body["entries"][0]["evidence"] if not ev["withheld"]]
        self.assertIn(f"`{kept[0]['sha256'][:12]}`", md)
        self.assertNotIn(kept[0]["sha256"], md)
        self.assertIn(kept[0]["sha256"], (pathlib.Path(out["folder"]) / "record.json").read_text(encoding="utf-8"))
        self.assertTrue(len(sha) == 64)

    def test_the_readme_keeps_its_honesty_and_the_record_agrees_with_it(self):
        self.added()
        md, out = self.md()
        readme = (pathlib.Path(out["folder"]) / "README.txt").read_text(encoding="utf-8")
        self.assertIn("They don't show the folder is the one the holder saved.", readme)
        self.assertIn("They don't prove Hermes produced them.", readme)
        self.assertIn("ask the holder to walk you through one entry", readme)
        self.assertNotIn("haven't changed since they were saved", md)
        self.assertIn("they don't show this folder is the one the holder saved", md)

    def test_an_excerpt_read_twice_shows_once_in_the_entry(self):
        aid = self.finished()
        entry = self.f.record_preview(aid)["entry"]
        shas = [ev["sha256"] for ev in entry["evidence"]]
        self.assertEqual(len(shas), len(set(shas)))

    def test_one_memory_line_reads_as_one_line(self):
        checks = self.mod("foundations_checks")
        self.assertEqual(checks._fill_words({"chars": 35, "limit": 1375, "entries": ["x"]}), "35 of 1,375 characters, 1 line")
        self.assertEqual(checks._fill_words({"chars": 479, "limit": 2200, "entries": ["a", "b"]}), "479 of 2,200 characters, 2 lines")


if __name__ == "__main__":
    unittest.main()
