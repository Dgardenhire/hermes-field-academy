"""The Foundations Field Record, format 3: what a stranger receives, and the promises it keeps.

Built from a real mission run (f.memory, from the shipped content) through the real foundations module, with a
stand-in Hermes root. Nothing runs Hermes. Covers: the body (scope, claims, entries, the checked-by tag on every line,
the calibration table with no average, first and last, what can be claimed, the empty reviewer), the saved folder
(record.md, record.json byte for byte, evidence/, MANIFEST.sha256 in ``shasum -a 256 -c`` format, README.txt),
withholding, active time only, the Hermes version and its source, corrections, and that formats 1 and 2 render as
before.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
import re
import shutil
import sqlite3
import subprocess
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import test_foundations_memory_mission as tmm  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402
from support import ROOT, START  # noqa: E402

TAGS = {"Field Academy read it", "your Hermes graded it", "you wrote it", "yours, not graded", "Field Academy counted it", "not graded yet",
        "the course wrote it"}  # 0.9 persona test: a claim kept in the course's words says so
LIMITS = "It shows one practice mission on my own laptop. Nobody else watched, and my Hermes graded my explanation."


class RecordCase(FoundationsCase):
    # The mission-run helpers from the memory mission's tests, borrowed without its tests.
    salt_for = tmm.MemoryMission.salt_for
    lab = tmm.MemoryMission.lab
    memory = tmm.MemoryMission.memory
    save_and_use = tmm.MemoryMission.save_and_use
    to_first_check = tmm.MemoryMission.to_first_check
    finished = tmm.MemoryMission.finished

    def setUp(self):
        super().setUp()
        self.f = self.mod("foundations")
        self.f.CONTENT_DIR = None
        self.content = self.mod("foundations_content")
        self.content.clear_cache()
        self.mission = self.content.get(tmm.MID)
        self.fr = self.mod("field_record")
        self.evidence = self.mod("evidence")
        self.evidence.detect_version_detail = lambda: {"value": "0.22.4", "source": "git tag", "exact": True}
        self.tick()

    def tick(self, step=timedelta(minutes=2), start=START):
        counter = itertools.count()
        self.store.clock = lambda: start + step * next(counter)

    def added(self, withhold=()):
        aid = self.finished()
        self.f.add_to_record(aid, withhold=withhold, confirmed=True)
        return aid

    def issue(self, **kw):
        args = dict(holder="Ada Lovelace", limits=LIMITS, case="", withhold=(), confirmed=True)
        args.update(kw)
        return self.fr.issue(args.pop("holder"), args.pop("limits"), args.pop("case"), args.pop("withhold"), confirmed=args.pop("confirmed"))

    def stored(self, number):
        with self.store.connect() as conn:
            return conn.execute("SELECT body_json FROM f_issued WHERE number = ?", (number,)).fetchone()[0]


class TheBody(RecordCase):
    def test_an_empty_record_has_nothing_to_issue(self):
        preview = self.fr.preview("Ada", LIMITS)
        self.assertFalse(preview["ready"])
        self.assertEqual(preview["body"]["entries"], [])
        with self.assertRaisesRegex(ValueError, "at least one entry"):
            self.issue()

    def test_the_body_is_format_3_with_every_part_the_plan_names(self):
        self.added()
        body = self.fr.preview("Ada Lovelace", LIMITS, "A case.")["body"]
        self.assertEqual((body["record"], body["record_format"], body["kind"]), ("Field Academy Field Record", 3, "foundations"))
        scope = body["scope"]
        self.assertEqual(scope["issuer"], "self")
        self.assertIn("not an official certificate", scope["not_official"])
        self.assertIn("not an official Hermes course from Nous Research", scope["not_official"])
        self.assertEqual(scope["holder"]["name"], "Ada Lovelace")
        self.assertTrue(scope["dates"]["first_work"] and scope["dates"]["last_entry"] and scope["dates"]["issued"])
        self.assertEqual((scope["hermes"]["version"], scope["hermes"]["read_from"]), ("0.22.4", "git tag"))
        self.assertIn("active_minutes", scope["hours"])
        claim = body["claims"][0]
        self.assertEqual(claim["claim"], self.mission["claim"]["text"])
        self.assertEqual([c["id"] for c in claim["standard"]], ["s1", "s2", "s3", "s4"])
        self.assertTrue(claim["standard_frozen_at"])
        self.assertEqual(claim["changes"], [])
        entry = body["entries"][0]
        for key in ("entry_hash", "prev_hash", "checks", "result_first", "result_after_fix", "caught", "missed", "gap", "fix", "transfer", "evidence"):
            self.assertIn(key, entry)
        self.assertTrue(all(len(ev["sha256"]) == 64 for ev in entry["evidence"]))
        self.assertIsNone(body["reviewer"])
        self.assertEqual(body["reviewer_note"], "Nobody outside has reviewed this record.")
        self.assertEqual(body["chain_head"], entry["entry_hash"])
        self.assertTrue(body["chain"]["intact"])
        self.assertIn("Not issued or endorsed by Nous Research", body["disclaimer"])

    def test_every_line_says_who_checked_it(self):
        self.added()
        body = self.fr.preview("Ada", LIMITS)["body"]
        seen = set()

        def walk(node):
            if isinstance(node, dict):
                if "checked_by" in node:
                    seen.add(node["checked_by"])
                    for part in node["checked_by"].split("; "):
                        self.assertIn(part, TAGS)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(body)
        self.assertTrue({"Field Academy read it", "you wrote it", "Field Academy counted it"} <= {p for s in seen for p in s.split("; ")})
        entry = body["entries"][0]
        for check in entry["checks"]:
            self.assertIn(check["checked_by"], ("Field Academy read it", "your Hermes graded it", "Field Academy read it; your Hermes graded it"))
        for part in ("where_wrong", "gap", "diagnosis", "fix"):
            self.assertEqual(entry[part]["checked_by"], "you wrote it")
        # The claim was kept in the course's words, so the record says the course wrote it (0.9 persona test, field_record.py:628).
        self.assertEqual(entry["claim"]["author"], "course")
        self.assertEqual(entry["claim"]["checked_by"], "the course wrote it")
        for ev in entry["evidence"]:
            self.assertEqual(ev["checked_by"], "Field Academy read it")

    def test_calibration_is_a_table_per_mission_with_no_average(self):
        self.added()
        body = self.fr.preview("Ada", LIMITS)["body"]
        cal = body["calibration"]
        for word in ("brier", "trend", "hit_rate", "mean", "gaps"):
            self.assertNotIn(word, cal)
        rows = cal["per_mission"]
        self.assertEqual([r["mission"] for r in rows], [m["id"] for m in self.fr._missions()])
        row = next(r for r in rows if r["mission"] == "f.memory")  # more missions sit beside it from M6
        self.assertTrue(row["in_record"])
        self.assertEqual(row["checks"], 4)
        self.assertEqual(row["predicted"], 4)
        self.assertIsInstance(row["passed_first"], int)
        empty = self.fr.calibration_rows([{"id": "f.other", "title": "Another", "order": 9}], {})
        self.assertEqual(empty[0], {"mission": "f.other", "title": "Another", "order": 9, "in_record": False, "checks": None,
                                    "predicted": None, "self_scored": None, "passed_first": None})
        markdown = self.fr.record_markdown(dict(body, number="FA-0000-0000-0000"))
        self.assertNotIn("Brier", markdown)
        self.assertNotRegex(markdown, r"(?i)guesses (high|low)|mean gap|average gap")

    def test_what_you_can_claim_comes_from_passed_checks_and_first_and_last_says_when_there_is_one(self):
        self.added()
        body = self.fr.preview("Ada", LIMITS)["body"]
        can = body["can_claim"]
        listed = [x["mission"] for x in can["passed"]] + [x["mission"] for x in can["not_yet"]]
        self.assertEqual(sorted(listed), sorted(m["id"] for m in self.fr._missions()))
        for item in can["passed"]:
            self.assertEqual(item["claim"], self.mission["claim"]["text"])
        for item in can["not_yet"]:
            self.assertTrue(item["why"])
        fl = body["first_and_last"]
        self.assertIsNotNone(fl["first"])
        self.assertIsNone(fl["last"])
        self.assertIn("Only one mission", fl["note"])

    def test_first_and_last_compares_what_was_found_wrong(self):
        a = {"n": 1, "mission": "f.loop", "mission_title": "First", "added_at": "2026-10-03T09:00:00", "gap": {"text": "The rows were stale."},
             "caught": [], "missed": [{"kind": "x"}], "result_first": {"passed": 2, "of": 4}}
        b = dict(a, n=2, mission_title="Last", gap={"text": "Two input files were empty."}, caught=[{"kind": "y"}], missed=[], result_first={"passed": 4, "of": 4})
        fl = self.fr._first_and_last([a, b])
        self.assertEqual((fl["first"]["found_wrong"], fl["last"]["found_wrong"]), ("The rows were stale.", "Two input files were empty."))
        self.assertEqual((fl["first"]["missed"], fl["last"]["caught"]), (1, 1))

    def test_a_check_that_passed_only_after_the_fix_says_so(self):
        entry = {"n": 1, "mission": "f.memory", "added_at": "2026-10-03", "claim": {"text": "I can."},
                 "checks": [{"text": "a", "passed": True, "passed_after_fix": True}, {"text": "b", "passed": False, "passed_after_fix": True}]}
        can = self.fr._can_claim([{"id": "f.memory", "title": "Memory"}], [entry])
        self.assertTrue(can["passed"][0]["after_fix"])
        entry["checks"][1]["passed_after_fix"] = False
        can = self.fr._can_claim([{"id": "f.memory", "title": "Memory"}], [entry])
        self.assertEqual(can["not_yet"][0]["why"], "Missed: b")


class ActiveTime(RecordCase):
    def test_gaps_over_15_minutes_and_waits_are_left_out(self):
        t = ["2026-10-03T09:00:00", "2026-10-03T09:10:00", "2026-10-03T09:20:00", "2026-10-03T12:20:00", "2026-10-03T12:25:00"]
        self.assertEqual(self.fr.active_seconds(t), (10 + 10 + 5) * 60)
        self.assertEqual(self.fr.active_seconds(t, waits=[("2026-10-03T09:12:00", "2026-10-03T09:18:00")]), (10 + 5) * 60)
        self.assertEqual(self.fr.active_seconds(t + t), (10 + 10 + 5) * 60, "two attempts side by side count once")
        self.assertEqual(self.fr.active_seconds(["nonsense", None]), 0)

    def test_a_long_wait_in_a_mission_doesnt_inflate_the_hours(self):
        aid = self.lab(["write_approval"])
        self.tick(start=START + timedelta(hours=5))  # the learner came back five hours later
        hf = sys.modules["hermes_fixture"]
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"] + [self.fact()], ["Ada prefers short answers."])
        self.save_and_use()
        self.to_first_check(aid)
        self.f.save_entry(aid, "gap_note", {"text": "I scored check 4 a pass without looking for anything planted."})
        self.f.run_checks(aid, "after_fix")
        self.f.save_entry(aid, "lab_note", {"fact": "Ada prefers short answers", "key_term": "short", "for": "transfer",
                                            "one_off": "The printer quote came in at noon today", "one_off_saved": False,
                                            "one_off_why": "It matters for one afternoon, so it doesn't earn a line."})
        self.f.run_checks(aid, "transfer")
        self.f.add_to_record(aid, confirmed=True)
        hours = self.fr.preview("Ada", LIMITS)["body"]["scope"]["hours"]
        self.assertLess(hours["active_minutes"], 120)
        self.assertGreater(hours["active_minutes"], 0)
        self.assertIn("15 minutes", hours["rule"])

    def fact(self):
        return tmm.FACT


class HermesVersion(RecordCase):
    def test_the_version_and_where_it_was_read(self):
        self.assertEqual(self.fr.version_line({"version": "0.22.4", "read_from": "git tag", "exact": True}),
                         "Hermes 0.22.4, read from the release tag of the Hermes code installed on this computer.")
        line = self.fr.version_line({"version": "0.21.5", "read_from": "install stamp base version; the checkout is 9 commits newer, so Hermes may be a later version", "exact": False})
        self.assertIn("Hermes may be newer", line)
        self.assertEqual(self.fr.version_line({"version": "", "read_from": ""}), "Field Academy couldn't find the Hermes version on this computer.")

    def test_a_missing_version_is_said_never_guessed(self):
        self.evidence.detect_version_detail = lambda: {"value": "", "source": "", "exact": False}
        self.added()
        body = self.fr.preview("Ada", LIMITS)["body"]
        self.assertEqual(body["scope"]["hermes"]["version"], "")
        self.assertIn("couldn't find the Hermes version", self.fr.record_markdown(body))


class TheFolder(RecordCase):
    def test_issuing_needs_a_yes_a_name_and_the_learners_limits(self):
        self.added()
        with self.assertRaisesRegex(ValueError, "confirmation"):
            self.issue(confirmed=False)
        with self.assertRaisesRegex(ValueError, "name"):
            self.issue(holder=" ")
        with self.assertRaisesRegex(ValueError, "doesn't show"):
            self.issue(limits="short")
        with self.assertRaisesRegex(ValueError, "300 words"):
            self.issue(case="word " * 301)

    def test_the_folder_a_stranger_receives(self):
        self.added()
        out = self.issue(case="A friend's notes were lost because a save waited for approval.")
        folder = pathlib.Path(out["folder"])
        self.assertTrue(folder.name.startswith("foundations-2026-10-03"))
        self.assertEqual(folder.parent.name, "field-records")
        names = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
        self.assertTrue({"record.md", "record.json", "README.txt", "MANIFEST.sha256"} <= names)
        self.assertTrue(any(n.startswith("evidence/") for n in names))
        self.assertEqual((folder / "record.json").read_bytes(), self.stored(out["number"]).encode("utf-8"), "record.json is the stored body, byte for byte")
        body = json.loads((folder / "record.json").read_text(encoding="utf-8"))
        self.assertTrue(self.fr.verify(body))
        self.assertTrue(self.state.verify_certificate(body), "the same number rule as every Field Record")
        self.assertEqual(self.state.record_display(body)["issuer"], body["scope"]["issuer_line"])
        manifest = (folder / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}  [\w./-]+", line) for line in manifest), manifest)
        self.assertEqual(sorted(line.split("  ")[1] for line in manifest), sorted(names - {"MANIFEST.sha256"}))
        for ev in (ev for e in body["entries"] for ev in e["evidence"] if ev["excerpt_file"]):
            self.assertEqual(hashlib.sha256((folder / ev["excerpt_file"]).read_bytes()).hexdigest(), ev["sha256"])
        self.assertTrue(self.fr.check_folder(folder)["ok"])
        markdown = (folder / "record.md").read_text(encoding="utf-8")
        for part in ("# Field Record: Foundations", out["number"], "## Scope", "## Claims", "## Entries", "## How the holder's self-judgment moved",
                     "## First and last", "## What the holder can now claim", "## A case for a stranger", "## Outside reviewer",
                     "Nobody outside has reviewed this record.", "Hermes 0.22.4, read from", LIMITS, "(Field Academy read it.)", "(The holder wrote it.)"):
            self.assertIn(part, markdown)
        readme = (folder / "README.txt").read_text(encoding="utf-8")
        for part in ("shasum -a 256 -c MANIFEST.sha256", "Get-FileHash", out["number"], "don't prove Hermes produced them", "Ada Lovelace"):
            self.assertIn(part, readme)
        self.assertNotIn(self.tmp, markdown + readme + (folder / "record.json").read_text(encoding="utf-8"))

    def test_shasum_itself_accepts_the_manifest(self):
        self.added()
        folder = pathlib.Path(self.issue()["folder"])
        tool = shutil.which("shasum") and ["shasum", "-a", "256", "-c", "MANIFEST.sha256"] or shutil.which("sha256sum") and ["sha256sum", "-c", "MANIFEST.sha256"]
        if not tool:
            self.skipTest("no shasum or sha256sum on this system")
        done = subprocess.run(tool, cwd=folder, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        (folder / "record.md").write_text("changed", encoding="utf-8")
        self.assertNotEqual(subprocess.run(tool, cwd=folder, capture_output=True, text=True).returncode, 0)

    def test_a_changed_file_or_number_is_caught(self):
        self.added()
        folder = pathlib.Path(self.issue()["folder"])
        first = next(folder.glob("evidence/*.txt"))
        first.write_text(first.read_text(encoding="utf-8") + " edited", encoding="utf-8")
        result = self.fr.check_folder(folder)
        self.assertFalse(result["ok"])
        self.assertEqual([r["file"] for r in result["files"] if not r["ok"]], [first.relative_to(folder).as_posix()])
        body = json.loads((folder / "record.json").read_text(encoding="utf-8"))
        body["scope"]["holder"]["name"] = "Mallory"
        self.assertFalse(self.fr.verify(body))

    def test_withheld_excerpts_show_as_withheld_and_keep_only_their_fingerprint(self):
        self.added()
        items = self.fr.preview("Ada", LIMITS)["excerpts"]
        self.assertTrue(items)
        target = items[0]
        preview = self.fr.preview("Ada", LIMITS, withhold=[target["id"]])
        hidden = next(x for x in preview["excerpts"] if x["id"] == target["id"])
        self.assertEqual((hidden["withheld"], hidden["excerpt"], hidden["excerpt_file"]), (True, "", None))
        self.assertEqual(hidden["sha256"], target["sha256"])
        out = self.issue(withhold=[target["id"]])
        folder = pathlib.Path(out["folder"])
        self.assertFalse(any(target["excerpt"] and target["excerpt"] in p.read_text(encoding="utf-8") for p in folder.rglob("*.txt") if p.name != "README.txt"))
        self.assertIn(target["sha256"], (folder / "record.md").read_text(encoding="utf-8"))
        self.assertIn("withheld by the holder", (folder / "record.md").read_text(encoding="utf-8"))
        self.assertTrue(self.fr.check_folder(folder)["ok"])

    def test_an_excerpt_withheld_when_the_entry_was_added_stays_withheld(self):
        aid = self.finished()
        first = self.f.record_preview(aid)["entry"]["evidence"][0]["id"]
        self.f.add_to_record(aid, withhold=[first], confirmed=True)
        hidden = next(x for x in self.fr.preview("Ada", LIMITS)["excerpts"] if x["id"] == first)
        self.assertTrue(hidden["withheld"])

    def test_issued_records_are_append_only_and_can_be_saved_again(self):
        self.added()
        out = self.issue()
        folder = pathlib.Path(out["folder"])
        shutil.rmtree(folder)
        again = self.fr.save_again(out["number"])
        self.assertEqual(again["folder"], out["folder"])
        self.assertTrue(self.fr.check_folder(folder)["ok"])
        second = self.issue()
        self.assertNotEqual(second["folder"], out["folder"], "a second record gets its own folder")
        self.assertEqual(len(self.fr.issued()), 2)
        with self.store.connect() as conn, self.assertRaises(sqlite3.DatabaseError):
            conn.execute("UPDATE f_issued SET body_json = '{}'")

    def test_secrets_in_the_learners_own_text_are_removed(self):
        self.added()
        fake = "sk-" + "a1B2" * 8
        body = self.fr.preview("Ada", LIMITS + " My key was " + fake, "Case " + fake)["body"]
        self.assertNotIn(fake, json.dumps(body))


class Corrections(RecordCase):
    def test_a_correction_goes_under_its_entry_and_the_chain_still_holds(self):
        self.added()
        entry_hash = self.fr.preview("Ada", LIMITS)["body"]["entries"][0]["entry_hash"]
        with self.assertRaisesRegex(ValueError, "confirmation"):
            self.f.add_correction(entry_hash, "The fact was mine, not the client's.")
        self.f.add_correction(entry_hash, "The fact was mine, not the client's.", confirmed=True)
        body = self.fr.preview("Ada", LIMITS)["body"]
        self.assertEqual(len(body["entries"]), 1)
        self.assertEqual(body["entries"][0]["corrections"][0]["text"], "The fact was mine, not the client's.")
        self.assertEqual(body["chain"]["entries"], 2)
        self.assertTrue(body["chain"]["intact"])
        self.assertNotEqual(body["chain_head"], entry_hash)
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            self.f.add_correction("0" * 64, "Nothing to correct here.", confirmed=True)


class Compatibility(RecordCase):
    def test_format_1_and_2_records_render_exactly_as_before(self):
        golden = json.loads((ROOT / "tests" / "data" / "records-format-1-2-rendered.json").read_text(encoding="utf-8"))
        for key in ("path_format_1", "path_format_2"):
            body = golden[key]["body"]
            view = {"body": body, "display": self.state.record_display(body), "number": body["number"]}
            self.assertEqual(self.state.certificate_markdown(view), golden[key]["markdown"], key)
            self.assertEqual(self.state.record_display(body), golden[key]["display"], key)
            self.assertTrue(self.state.verify_certificate(body))
        deployer = self.mod("deployer")
        body = golden["deployer_format_1"]["body"]
        view = {"body": body, "display": self.state.record_display(body), "number": body["number"]}
        self.assertEqual(deployer.certificate_markdown(view), golden["deployer_format_1"]["markdown"])

    def test_dates_read_the_same_on_every_python(self):
        # The golden above was once made on Python 3.9, which can't parse a trailing "Z", so it kept the raw stamp
        # while 3.11+ (what Hermes runs) printed the date. Both now print the date.
        self.assertEqual(self.state._human_date("2026-10-02T15:00:00Z"), "October 2, 2026")
        self.assertEqual(self.state._human_date("2026-10-02T15:00:00+00:00"), "October 2, 2026")
        self.assertEqual(self.state._human_date("not a date"), "not a date")
        self.assertEqual(self.state._human_date(None), "")

    def test_path_and_guide_records_stay_format_2_and_foundations_never_touches_certificates(self):
        self.assertEqual(self.mod("pathways").RECORD_FORMAT, 2)
        self.assertEqual(self.fr.RECORD_FORMAT, 3)
        self.added()
        self.issue()
        with self.store.connect() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM certificates").fetchone()[0], 0)

    def test_the_path_page_gets_the_same_table(self):
        aid = self.finished()
        snap = self.f.snapshot()
        rows = snap["calibration_table"]
        memory = next(r for r in rows if r["mission"] == "f.memory")  # more missions sit beside it from M6
        self.assertEqual(memory["checks"], 4)
        self.assertEqual(snap["record"], [])
        self.f.add_to_record(aid, confirmed=True)
        self.issue()
        self.assertEqual(len(self.f.snapshot()["record"]), 1)


if __name__ == "__main__":
    unittest.main()
