"""Field Records old and new: format 1 records from 0.8.2 still verify, new ones are format 2.

A record's number is a SHA-256 over every stored line, its wording included. 0.8.3
renamed the certificate to a Field Record and reworded the issuer line, so these
tests pin the promise that came with that: a record made by 0.8.2 keeps its exact
stored text and still verifies, a new record carries the new wording and verifies,
and an edit to either one stops matching. tests/data/records-format-1.json holds a
path record and a Guide record exactly as 0.8.2 wrote them.

Stdlib only: run with `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

from deployer_support import DeployerCase
from support import AcademyCase, ROOT

FORMAT_1 = json.loads((ROOT / "tests" / "data" / "records-format-1.json").read_text(encoding="utf-8"))
DISCLAIMER = "Self-issued with Field Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research."


def copy(body):
    return json.loads(json.dumps(body))


class RecordFormats(AcademyCase):
    def setUp(self):
        super().setUp()
        self.pathways = sys.modules[f"{self.name}.pathways"]

    def store_legacy(self, track_id, body):
        with self.state._connection() as conn:
            conn.execute(
                "INSERT INTO certificates(track_id, name, number, issued_at, body_json) VALUES (?, ?, ?, ?, ?)",
                (track_id, body["name"], body["number"], body["issued_at"], self.state._canonical(body)),
            )

    # -- format 1, as 0.8.2 wrote it ---------------------------------------------

    def test_a_format_1_path_record_from_082_still_verifies(self):
        body = copy(FORMAT_1["path"])
        self.assertEqual(body["certificate"], "Field Academy certificate")
        self.assertNotIn("record_format", body)
        self.assertEqual(self.state.record_format(body), 1)
        self.assertEqual(body["number"], "FA-0C1F-BFE9-2528")
        self.assertEqual(self.state.certificate_number(body), "FA-0C1F-BFE9-2528")
        self.assertTrue(self.state.verify_certificate(body))

    def test_a_format_1_guide_record_from_082_still_verifies(self):
        body = copy(FORMAT_1["deployer"])
        self.assertEqual(body["certificate"], "Field Academy Guide certificate")
        self.assertEqual(body["number"], "FA-58DA-3662-39F6")
        self.assertTrue(self.state.verify_certificate(body))

    def test_tampering_with_a_format_1_record_still_fails(self):
        for key in ("path", "deployer"):
            body = copy(FORMAT_1[key])
            body["name"] = "Mallory"
            self.assertFalse(self.state.verify_certificate(body), key)

    def test_rewording_a_format_1_record_would_break_it_so_the_wording_is_never_rewritten(self):
        body = copy(FORMAT_1["path"])
        body["issuer"] = self.pathways.ISSUER
        self.assertFalse(self.state.verify_certificate(body))
        body = copy(FORMAT_1["path"])
        body["record_format"] = 2
        self.assertFalse(self.state.verify_certificate(body))

    def test_a_stored_format_1_record_stays_valid_and_shows_the_new_wording(self):
        body = copy(FORMAT_1["path"])
        self.store_legacy("ambassador", body)
        view = self.state.get_certificate("ambassador")
        self.assertTrue(view["valid"])
        self.assertEqual(view["body"], body)
        self.assertEqual(view["display"]["format"], 1)
        self.assertTrue(view["display"]["legacy"])
        self.assertEqual(view["display"]["disclaimer"], DISCLAIMER)
        self.assertEqual(view["display"]["issuer"], self.pathways.ISSUER)
        track = next(t for t in self.state.snapshot()["tracks"] if t["id"] == "ambassador")
        self.assertEqual(track["certificate"]["status"], "issued")
        self.assertTrue(track["certificate"]["issued"]["valid"])

    def test_saving_a_format_1_record_keeps_its_json_byte_for_byte_and_rewords_the_md(self):
        body = copy(FORMAT_1["path"])
        self.store_legacy("ambassador", body)
        saved = self.state.save_certificate("ambassador")
        stored = json.loads(pathlib.Path(saved["json"]).read_text(encoding="utf-8"))
        self.assertEqual(stored, body)
        self.assertTrue(self.state.verify_certificate(stored))
        markdown = pathlib.Path(saved["markdown"]).read_text(encoding="utf-8")
        self.assertIn("# Field Record: Messenger path", markdown)
        self.assertIn(DISCLAIMER, markdown)
        self.assertIn("0.8.2 or earlier, which called it a certificate", markdown)
        self.assertIn("FA-0C1F-BFE9-2528", markdown)
        self.assertNotIn("Awarded", markdown)
        self.assertNotIn("Field Academy issues this certificate", markdown)

    # -- format 2, from 0.8.3 on -------------------------------------------------

    def test_a_new_record_is_format_2_carries_the_disclaimer_and_verifies(self):
        self.pass_track("ambassador")
        record = self.state.issue_certificate("ambassador", "Ada Lovelace")
        body = record["body"]
        self.assertEqual(body["record_format"], 2)
        self.assertEqual(body["record"], "Field Academy Field Record")
        self.assertNotIn("certificate", body)
        self.assertEqual(body["disclaimer"], DISCLAIMER)
        self.assertEqual(body["issuer"], "Created by its holder with the Field Academy plugin.")
        self.assertTrue(record["valid"])
        self.assertTrue(self.state.verify_certificate(body))
        self.assertFalse(record["display"]["legacy"])
        self.assertEqual(record["display"]["issuer"], body["issuer"])

    def test_tampering_with_a_format_2_record_fails(self):
        self.pass_track("ambassador")
        body = copy(self.state.issue_certificate("ambassador", "Ada Lovelace")["body"])
        for change in (
            lambda b: b.update(name="Mallory"),
            lambda b: b.pop("disclaimer"),
            lambda b: b.update(issuer="Issued by Nous Research."),
            lambda b: b.update(record_format=1),
        ):
            edited = copy(body)
            change(edited)
            self.assertFalse(self.state.verify_certificate(edited))

    def test_old_and_new_records_verify_side_by_side(self):
        self.store_legacy("ambassador", copy(FORMAT_1["path"]))
        self.pass_track("operator")
        new = self.state.issue_certificate("operator", "Ada Lovelace")
        old = self.state.get_certificate("ambassador")
        self.assertTrue(old["valid"] and new["valid"])
        self.assertEqual((old["display"]["format"], new["display"]["format"]), (1, 2))


class GuideRecordFormats(DeployerCase):
    def test_a_stored_format_1_guide_record_stays_valid_and_its_md_carries_the_disclaimer(self):
        body = copy(FORMAT_1["deployer"])
        with self.state._connection() as conn:
            conn.execute(
                "INSERT INTO certificates(track_id, name, number, issued_at, body_json) VALUES ('deployer', ?, ?, ?, ?)",
                (body["name"], body["number"], body["issued_at"], self.state._canonical(body)),
            )
        snap = self.deployer.snapshot()
        issued = snap["certificate"]["issued"]
        self.assertTrue(issued["valid"])
        self.assertTrue(issued["display"]["legacy"])
        self.assertEqual(issued["display"]["shows"], self.deployer_content.WHAT_IT_SHOWS)
        self.assertNotIn("proposal for Nous", " ".join(issued["display"]["does_not_show"]))
        saved = self.deployer.save_certificate()
        stored = json.loads(pathlib.Path(saved["json"]).read_text(encoding="utf-8"))
        self.assertEqual(stored, body)
        self.assertTrue(self.state.verify_certificate(stored))
        markdown = pathlib.Path(saved["markdown"]).read_text(encoding="utf-8")
        self.assertIn("# Field Record: Guide path", markdown)
        self.assertIn(DISCLAIMER, markdown)
        self.assertIn("a reviewer the holder chose", markdown)
        self.assertIn("0.8.2 or earlier", markdown)
        self.assertNotIn("proposal for Nous", markdown)
        self.assertNotIn("Awarded", markdown)


class DisclaimerEverywhere(AcademyCase):
    def test_the_page_falls_back_to_the_same_disclaimer_as_the_backend(self):
        source = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")
        found = re.search(r"const RECORD_DISCLAIMER = '([^']+)'", source)
        self.assertIsNotNone(found)
        self.assertEqual(found.group(1), sys.modules[f"{self.name}.pathways"].DISCLAIMER)

    def test_the_snapshot_and_both_record_screens_carry_the_disclaimer(self):
        self.assertEqual(self.state.snapshot()["record_disclaimer"], DISCLAIMER)
        plugin = (ROOT / "desktop" / "src" / "plugin.js").read_text(encoding="utf-8")
        deployer = (ROOT / "desktop" / "src" / "deployer.js").read_text(encoding="utf-8")
        self.assertIn("children: display.disclaimer", plugin)
        self.assertIn("children: display.disclaimer", deployer)
        self.assertIn("route.disclaimer", plugin)

    def test_no_shipped_screen_text_calls_the_record_a_certificate_or_a_nous_credential(self):
        for name in ("plugin.js", "deployer.js", "field.js", "banner.js", "trail.js"):
            source = (ROOT / "desktop" / "src" / name).read_text(encoding="utf-8")
            strings = re.findall(r"'([^'\n]*)'|`([^`\n]*)`|\"([^\"\n]*)\"", source)
            visible = [next(part for part in group if part) for group in strings if any(group)]
            for text in visible:
                text = re.sub(r"\$\{[^}]*\}", "", text)  # template expressions are code, not words
                if text.startswith("/") or " " not in text.strip():
                    continue  # route paths, view names, keys and class names
                self.assertNotRegex(text, r"(?i)\bcertif|\bnous research credential|proposal for nous|this certifies", f"{name}: {text}")
