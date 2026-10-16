"""Reading a learner's document: sections, what each needs, placeholders, copying and the capstone's criteria check."""

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fa_documents_pure", ROOT / "documents.py")
documents = importlib.util.module_from_spec(spec)
spec.loader.exec_module(documents)

STEP = {
    "sections": [
        {"heading": "Client", "min_words": 5, "needs": ["name"], "what": "who the client is", "fix": "Name the business."},
        {"heading": "Acceptance", "min_words": 6, "needs": ["number"], "what": "what good looks like", "fix": "Put a number on it."},
        {"heading": "Out of scope", "min_words": 6, "needs": ["list"], "what": "two things left out", "fix": "List two."},
        {"heading": "Price", "min_words": 4, "needs": ["money"], "what": "the price", "fix": "Put the price in dollars."},
    ]
}

GOOD = """# Scope

## Client
Harbor Roofing is a family business in Wilmington that repairs roofs.

## Acceptance
Every open quote older than seven days gets a follow-up by Friday afternoon.

## Out of scope
- Sending anything without approval
- Changing the price of a quote

## Price
$2,400 for setup and a monthly fee.
"""


def missing_ids(text, step=STEP, models=None):
    return [m["id"] for m in documents.analyze(text, step, models)["missing"]]


class SectionTests(unittest.TestCase):
    def test_a_heading_is_a_line_that_starts_with_its_words(self):
        found = documents.sections("## Client\nAcme\n\n## Price\n$5", ["Client", "Price"])
        self.assertEqual(found, {"Client": "Acme", "Price": "$5"})

    def test_a_heading_mentioned_in_a_sentence_is_not_a_heading(self):
        found = documents.sections("I will write the Client section later.\n", ["Client"])
        self.assertIsNone(found["Client"])

    def test_headings_match_with_bold_marks_bullets_and_numbers(self):
        for heading_line in ("**Client**", "1. Client", "- Client", "### Client", "client:"):
            found = documents.sections(f"{heading_line}\nAcme Corp\n", ["Client"])
            self.assertEqual(found["Client"], "Acme Corp", heading_line)

    def test_text_after_a_colon_on_the_heading_line_belongs_to_the_section(self):
        self.assertEqual(documents.sections("Client: Acme Corp, a bakery\n", ["Client"])["Client"], "Acme Corp, a bakery")

    def test_a_section_runs_to_the_next_heading_of_any_kind(self):
        found = documents.sections("## Client\nAcme\n## Notes\nignore me\n## Price\n$5\n", ["Client", "Price"])
        self.assertEqual(found["Client"], "Acme")

    def test_headings_are_matched_without_regard_to_case(self):
        self.assertEqual(documents.sections("## OUT OF SCOPE\n- a\n- b\n", ["Out of scope"])["Out of scope"], "- a\n- b")

    def test_a_missing_heading_is_none(self):
        self.assertIsNone(documents.sections("## Client\nx\n", ["Price"])["Price"])


class NeedTests(unittest.TestCase):
    def test_a_name_is_a_capital_in_the_middle_of_a_sentence_or_two_in_a_row(self):
        self.assertTrue(documents.has_name("The owner is Priya and she signs off."))
        self.assertTrue(documents.has_name("Marcus Bell reviews the list."))
        self.assertTrue(documents.has_name("Reviewed by Dr. Ruiz every week."))

    def test_a_role_with_no_name_is_not_a_name(self):
        self.assertFalse(documents.has_name("the office manager reads every message before it goes out."))
        self.assertFalse(documents.has_name("The team owns it and the manager signs."))

    def test_products_and_days_do_not_count_as_people(self):
        self.assertFalse(documents.has_name("it goes to Slack every Monday."))
        self.assertFalse(documents.has_name("Hermes runs on Docker."))

    def test_numbers_are_digits_or_number_words(self):
        self.assertTrue(documents.has_need("number", "about 12 orders"))
        self.assertTrue(documents.has_need("number", "three weeks"))
        self.assertFalse(documents.has_need("number", "a few orders every so often"))

    def test_money_needs_a_price(self):
        self.assertTrue(documents.has_need("money", "$2,400 for setup"))
        self.assertTrue(documents.has_need("money", "250 dollars a month"))
        self.assertFalse(documents.has_need("money", "it costs something"))

    def test_time_accepts_digits_words_and_how_often(self):
        for text in ("30 minutes", "two weeks", "30-minute call", "every Friday", "weekly", "at 8 am", "95%"):
            self.assertTrue(documents.has_need("time", text), text)
        self.assertFalse(documents.has_need("time", "whenever it suits them"))

    def test_a_list_needs_two_separate_lines(self):
        self.assertTrue(documents.has_need("list", "- one\n- two"))
        self.assertTrue(documents.has_need("list", "1. one\n2) two"))
        self.assertFalse(documents.has_need("list", "- only one"))
        self.assertFalse(documents.has_need("list", "one, two and three in a sentence"))

    def test_a_decision_must_come_first(self):
        self.assertTrue(documents.has_need("decision", "Yes, because the owner can approve spending."))
        self.assertTrue(documents.has_need("decision", "Later. The budget isn't there yet."))
        self.assertFalse(documents.has_need("decision", "The owner can approve spending, so yes."))

    def test_a_verdict_is_met_partly_or_not_met(self):
        self.assertTrue(documents.has_need("verdict", "It arrived at 8 am. Met."))
        self.assertTrue(documents.has_need("verdict", "Partly met."))
        self.assertFalse(documents.has_need("verdict", "It arrived at 8 am."))


class AnalyzeTests(unittest.TestCase):
    def test_a_complete_document_has_nothing_missing(self):
        self.assertEqual(missing_ids(GOOD), [])

    def test_an_absent_section_is_named(self):
        ids = missing_ids(GOOD.replace("## Price\n$2,400 for setup and a monthly fee.\n", ""))
        self.assertEqual(ids, ["section:Price"])

    def test_a_heading_with_nothing_under_it_is_too_short(self):
        result = documents.analyze(GOOD.replace("Harbor Roofing is a family business in Wilmington that repairs roofs.", "A company."), STEP)
        self.assertEqual([m["id"] for m in result["missing"]], ["section:Client"])
        self.assertIn("2 words", result["missing"][0]["what"])
        self.assertIn("at least 5", result["missing"][0]["what"])

    def test_every_missing_part_is_reported_together(self):
        ids = missing_ids("## Client\nA company.\n\n## Price\nSoon.\n")
        self.assertEqual(ids, ["section:Client", "section:Acceptance", "section:Out of scope", "section:Price"])

    def test_a_section_missing_its_number_says_so_and_how_to_fix_it(self):
        text = GOOD.replace("Every open quote older than seven days gets a follow-up by Friday afternoon.", "Every open quote gets a prompt follow-up before the end of the week.")
        result = documents.analyze(text, STEP)
        self.assertEqual([m["id"] for m in result["missing"]], ["section:Acceptance"])
        self.assertIn("no a number", result["missing"][0]["what"].replace("has no a number", "no a number"))
        self.assertIn("Put a number on it.", result["missing"][0]["what"])

    def test_placeholder_text_is_caught(self):
        for stub in ("TODO", "[...]", "____", "tbd", "<insert name>", "xxx"):
            text = GOOD.replace("Harbor Roofing is a family business in Wilmington that repairs roofs.", f"Harbor Roofing family business {stub} in Wilmington repairs roofs.")
            self.assertIn("section:Client", missing_ids(text), stub)

    def test_two_sections_with_the_same_words_are_caught(self):
        same = "Marcus Bell reviews every message in the office before it goes out to patients."
        step = {"sections": [
            {"heading": "Owner", "min_words": 5, "needs": []},
            {"heading": "Approver", "min_words": 5, "needs": []},
        ]}
        self.assertIn("duplicate", missing_ids(f"## Owner\n{same}\n\n## Approver\n{same}\n", step))

    def test_one_repeated_phrase_is_caught(self):
        step = {"sections": [{"heading": "A", "min_words": 5}, {"heading": "B", "min_words": 5}, {"heading": "C", "min_words": 5}]}
        filler = "working notes about the plan " * 12
        text = f"## A\n{filler}\n## B\n{filler} again\n## C\n{filler} more\n"
        self.assertIn("repetition", missing_ids(text, step))

    def test_a_document_that_is_the_example_is_caught(self):
        self.assertIn("copied", missing_ids(GOOD, models=[GOOD]))

    def test_a_document_that_only_borrows_a_phrase_is_fine(self):
        other = GOOD.replace("Harbor Roofing", "Lakeside Dental").replace("Wilmington", "Tulsa")
        model = "# Scope\n\n## Client\nHarbor Roofing family business in Wilmington.\n\n## Price\n$2,400 for setup.\n"
        self.assertNotIn("copied", missing_ids(other, models=[model]))

    def test_a_short_document_is_not_judged_a_copy(self):
        self.assertEqual(documents.copied_share("a few words only", ["a few words only"]), 0.0)

    def test_the_result_counts_sections_found_and_words(self):
        result = documents.analyze(GOOD, STEP)
        self.assertEqual((result["found"], result["total"]), (4, 4))
        self.assertGreater(result["words"], 20)


CRITERIA_STEP = {
    "cross": "criteria",
    "sections": [
        {"heading": "Problem", "min_words": 4},
        {"heading": "Criteria", "min_words": 4},
        {"heading": "Evidence", "min_words": 4},
    ],
}
CRITERIA_GOOD = """## Problem
Our weekly summary takes too long to write by hand.

## Criteria
1. The summary arrives by 8 am every Monday.
2. It lists every open order older than 7 days.
3. I spend under 10 minutes reading it.

## Evidence
1. It arrived at 7:52 am on 4 Mondays. Met.
2. It listed 9 of the 11 open orders. Partly met.
3. Reading took 6 minutes. Met.
"""


class CriteriaTests(unittest.TestCase):
    def test_criteria_with_matching_evidence_pass(self):
        self.assertEqual(missing_ids(CRITERIA_GOOD, CRITERIA_STEP), [])

    def test_fewer_than_three_criteria_is_caught(self):
        text = CRITERIA_GOOD.replace("3. I spend under 10 minutes reading it.\n", "").replace("3. Reading took 6 minutes. Met.\n", "")
        self.assertIn("criteria_count", missing_ids(text, CRITERIA_STEP))

    def test_criteria_with_no_number_or_time_are_caught(self):
        text = CRITERIA_GOOD.replace("by 8 am every Monday", "at some point soon").replace("older than 7 days", "that are old").replace("under 10 minutes", "a short while")
        self.assertIn("criteria_measurable", missing_ids(text, CRITERIA_STEP))

    def test_one_evidence_line_per_criterion(self):
        text = CRITERIA_GOOD.replace("3. Reading took 6 minutes. Met.\n", "")
        self.assertIn("evidence_count", missing_ids(text, CRITERIA_STEP))

    def test_every_evidence_line_needs_a_verdict(self):
        text = CRITERIA_GOOD.replace("It listed 9 of the 11 open orders. Partly met.", "It listed 9 of the 11 open orders.")
        self.assertIn("evidence_verdict", missing_ids(text, CRITERIA_STEP))

    def test_a_criterion_too_short_to_test_is_caught(self):
        text = CRITERIA_GOOD.replace("3. I spend under 10 minutes reading it.", "3. Quick.")
        self.assertIn("criteria_thin", missing_ids(text, CRITERIA_STEP))

    def test_the_cross_check_waits_until_the_sections_exist(self):
        ids = missing_ids("## Problem\nOur weekly summary takes too long to write.\n", CRITERIA_STEP)
        self.assertEqual(ids, ["section:Criteria", "section:Evidence"])


if __name__ == "__main__":
    unittest.main()
