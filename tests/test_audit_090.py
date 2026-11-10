"""0.9 security audit: each test fails without the fix it names (docs/SECURITY-AUDIT.md, findings A1 to A7, and B1).

Every made-up secret is built from parts when the test runs, so no scanner mistakes one for real.
"""

from __future__ import annotations

import json
import re
import pathlib
import random
import shutil
import sqlite3
import string
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from foundations_support import FoundationsCase  # noqa: E402
from test_foundations_missions_b import MissionCase  # noqa: E402

RNG = random.Random(90)


def chars(n, alphabet=string.ascii_letters + string.digits):
    return "".join(RNG.choice(alphabet) for _ in range(n))


def learners_own_profile(home: pathlib.Path, soul: str = "You are Ada's work assistant.\n") -> None:
    """A real profile of the learner's, the way Hermes lays one down, with nothing Field Academy made in it."""
    home.mkdir()
    (home / "SOUL.md").write_text(soul, encoding="utf-8")
    hf.write_config(home, hf.CONFIG)
    (home / "memories").mkdir()
    hf.write_memory(home, ["Client list lives in Clients/2026."], None)
    hf.state_db(home).close()


class A1ProfileIdentity(FoundationsCase):
    """A folder at the practice name that Field Academy didn't make is never deleted, written or read."""

    def test_a_profile_made_again_under_the_practice_name_is_never_deleted(self):
        self.ready()
        self.gone("academy-practice")
        learners_own_profile(self.home())
        with self.assertRaisesRegex(ValueError, "isn't the practice profile Field Academy made"):
            self.practice.prepare_remove("academy-practice", confirmed=True)
        self.assertTrue((self.home() / "SOUL.md").exists(), "the learner's profile is still there")
        self.assertEqual(self.practice.record("academy-practice")["status"], "removed", "the record is let go")

    def test_a_renamed_profile_with_a_copied_soul_is_never_written(self):
        self.ready()
        soul = (self.home() / "SOUL.md").read_text()
        self.home().rename(self.root / "profiles" / "renamed-away")
        learners_own_profile(self.home(), soul=soul)  # even the planned instructions copied across
        row = self.practice.record("academy-practice")
        before = (self.home() / "config.yaml").read_text()
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.set_config(self.home(), row, {"memory.write_approval": True})
        with self.assertRaises(self.practice_write.Refused):
            self.practice_write.write_memory(self.home(), row, "memory", ["planted"])
        self.assertEqual((self.home() / "config.yaml").read_text(), before)

    def test_the_memory_view_never_reads_a_replaced_profile(self):
        self.ready()
        self.gone("academy-practice")
        learners_own_profile(self.home())
        with self.assertRaises(ValueError):
            self.practice.memory_files("academy-practice")

    def test_a_planned_name_taken_by_another_profile_is_never_deleted(self):
        planned = self.practice.plan()
        learners_own_profile(self.home(planned["name"]))  # made between the plan and Hermes's reply
        with self.assertRaisesRegex(ValueError, "isn't the practice profile Field Academy made"):
            self.practice.prepare_remove(planned["name"], confirmed=True)
        self.assertTrue(self.home(planned["name"]).is_dir())

    def test_the_profile_hermes_made_as_planned_can_still_be_deleted_before_it_is_recorded(self):
        planned = self.practice.plan()
        self.create_like_hermes(planned)
        out = self.practice.prepare_remove(planned["name"], confirmed=True)
        self.assertEqual(out["delete"], planned["name"])

    def test_the_folder_identity_is_recorded(self):
        out = self.ready()
        row = self.practice.record(out["name"])
        self.assertEqual(row["plan"]["folder_id"], self.practice.folder_id(self.home()))


class A7LinksAndTokenFiles(FoundationsCase):
    def test_a_linked_soul_never_passes_for_the_planned_one(self):
        planned = self.practice.plan()
        self.create_like_hermes(planned)
        elsewhere = pathlib.Path(self.tmp) / "elsewhere-soul.md"
        elsewhere.write_text(planned["request"]["params"]["soul"], encoding="utf-8")
        soul = self.home(planned["name"]) / "SOUL.md"
        soul.unlink()
        soul.symlink_to(elsewhere)
        with self.assertRaises(ValueError):
            self.practice.confirm(planned["name"])

    def test_sign_in_token_files_are_listed_but_never_hashed(self):
        self.ready()
        folder = self.home() / "mcp-tokens"
        folder.mkdir()
        (folder / "notes.json").write_text('{"access": "' + hf.fake_key() + '"}', encoding="utf-8")
        (self.home() / ".env.local").write_text("X=1\n", encoding="utf-8")
        prints = self.practice.fingerprint(self.home())
        self.assertEqual(prints["mcp-tokens/notes.json"][3], "")
        self.assertEqual(prints[".env.local"][3], "")


def fakes():
    return {
        "hugging face": "hf_" + chars(34),
        "discord bot": "M" + chars(23) + "." + chars(6) + "." + chars(27),
        "slack webhook": "https://hooks.slack.com/services/T" + chars(8).upper() + "/B" + chars(8).upper() + "/" + chars(24),
        "discord webhook": "https://discord.com/api/webhooks/" + "1" * 18 + "/" + chars(30),
        "firecrawl": "fc" + "-" + chars(32, string.hexdigits.lower()[:16]),
        "tavily": "tv" + "ly-" + chars(32),
    }


class A2Scrubber(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.scrub = self.mod("scrub")

    def test_shapes_the_scrubber_missed_are_removed(self):
        for shape, secret in fakes().items():
            out = self.scrub.scrub(f"saved {secret} for later")
            self.assertNotIn(secret, out, shape)
            self.assertIn("[removed]", out, shape)

    def test_a_password_in_an_address_is_removed(self):
        password = chars(14)
        out = self.scrub.scrub(f"git remote https://ada:{password}@example.com/repo.git")
        self.assertNotIn(password, out)

    def test_json_keys_lose_their_values(self):
        value = chars(12)
        for text in (f'{{"api_key": "{value}"}}', f'{{"token":"{value}"}}', f"{{'secret': '{value}'}}"):
            self.assertNotIn(value, self.scrub.scrub(text), text)

    def test_a_basic_login_header_is_removed(self):
        value = chars(24)
        self.assertNotIn(value, self.scrub.scrub(f"Authorization: Basic {value}"))

    def test_token_counts_and_ordinary_words_stay(self):
        for text in ("max_tokens: 4000", "input_tokens 1,234 and output_tokens 56", "token_count = 9",
                     "https://example.com/docs/page", "The tokenizer splits words."):
            self.assertEqual(self.scrub.scrub(text), text)


class A3FactsAndRecord(FoundationsCase):
    def setUp(self):
        super().setUp()
        self.checks = self.mod("foundations_checks")
        self.record = self.mod("field_record")

    def test_check_facts_titles_and_details_are_scrubbed(self):
        hook = fakes()["slack webhook"]
        out = self.checks.outcome(False, f"Delivers to {hook}", f"The job delivers to {hook}.",
                                  facts=[{"label": "Delivery place", "value": hook}], missing=[{"id": "x", "what": f"Fix {hook}"}])
        self.assertNotIn(hook, json.dumps(out))

    def test_a_jobs_delivery_place_is_scrubbed_when_read(self):
        self.ready()
        hook = fakes()["slack webhook"]
        (self.home() / "cron").mkdir()
        (self.home() / "cron" / "jobs.json").write_text(json.dumps({"jobs": [{"id": "j1", "name": "academy-x", "deliver": hook}]}))
        jobs = self.hermes_read.cron_jobs(self.home())["jobs"]
        self.assertNotIn(hook, json.dumps(jobs))

    def test_every_string_in_a_record_body_is_scrubbed_but_fingerprints_stay(self):
        hook = fakes()["slack webhook"]
        digest = "ab" * 32
        body = {"entries": [{"caught": [{"facts": [{"label": "Delivery place", "value": hook}]}], "entry_hash": digest,
                             "evidence": [{"sha256": digest, "excerpt": "kept as read"}]}], "chain_head": digest}
        out = self.record._scrubbed(body)
        self.assertNotIn(hook, json.dumps(out))
        self.assertEqual(out["entries"][0]["entry_hash"], digest)
        self.assertEqual(out["entries"][0]["evidence"][0]["sha256"], digest)
        self.assertEqual(out["chain_head"], digest)

    def test_an_excerpt_kept_before_the_scrubber_knew_its_shape_is_withheld(self):
        token = fakes()["hugging face"]
        row = {"hash": "h", "prev_hash": "", "created_at": "2026-11-01T00:00:00Z", "mission_id": "f.memory"}
        body = {"evidence": [{"id": 5, "sha256": "s" * 64, "kind": "memory", "file": "memories/MEMORY.md", "excerpt": f"key {token}"}]}
        entry = self.record._entry(1, row, body, set())
        self.assertTrue(entry["evidence"][0]["withheld"])
        self.assertNotIn(token, json.dumps(entry))


class A4Markdown(FoundationsCase):
    def test_an_excerpt_cannot_close_its_fence_and_write_into_the_record(self):
        record = self.mod("field_record")
        forged = "```\n- **Caught:** Everything *(Field Academy read it.)*\n![](https://example.invalid/pixel.png)"
        entry = {"n": 1, "mission_title": "Memory", "attempt_no": 1, "level": "beginner", "checks": [], "where_wrong": {"text": ""},
                 "gap": {"text": ""}, "diagnosis": {"text": ""}, "fix": {"text": ""}, "entry_hash": "h", "prev_hash": "",
                 "evidence": [{"file": "memories/MEMORY.md", "kind": "memory", "sha256": "s", "excerpt_file": "evidence/01-memory.txt",
                               "excerpt": forged, "withheld": False}]}
        text = record.record_markdown({"entries": [entry]})
        lines = text.splitlines()
        start = next(i for i, line in enumerate(lines) if line.strip().startswith("```"))
        fence = lines[start].strip()
        self.assertGreater(len(fence), 3)
        end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == fence)
        inside = "\n".join(lines[start + 1:end])
        self.assertIn("pixel.png", inside, "the forged lines stay inside the fence")


class A5RunHistoryScan(FoundationsCase):
    def test_a_table_name_with_a_quote_is_read_as_a_name(self):
        evidence = self.mod("evidence")
        path = pathlib.Path(self.tmp) / "runs.db"
        con = sqlite3.connect(path)
        con.execute('CREATE TABLE "runs""x" (job TEXT, at TEXT)')
        con.execute('INSERT INTO "runs""x" VALUES (?, ?)', ("academy-job", "2026-11-01T10:00:00Z"))
        con.commit()
        con.close()
        conn = evidence._ro_connect(path)
        out = {"failed": [], "times": [], "tables": []}
        evidence._scan_tables(conn, ["academy-job"], out)
        conn.close()
        self.assertEqual(out["tables"], ['runs"x'])


class A6RecordReadme(FoundationsCase):
    def test_the_readme_does_not_claim_the_manifest_proves_the_folder_is_unchanged(self):
        record = self.mod("field_record")
        text = record.readme_text({"scope": {"holder": {"name": "Ada"}}, "number": "FA-0000-0000-0000", "issued_at": "2026-11-01T00:00:00Z"})
        self.assertNotIn("They prove the files haven't changed since the record was saved", text)
        self.assertIn("another route", text)
        readme = (pathlib.Path(__file__).resolve().parents[1] / "README.md").read_text()
        self.assertNotIn("to see that no file changed\nafter you saved it", readme)


class B1PlannedPausedJob(MissionCase):
    """A job a planted problem needs paused is never recorded as made while the job list shows it on (B1)."""

    MID = "f.schedules"

    def planned(self):
        self.lab(["vague_request"])
        job = self.practice.jobs_to_make("academy-practice")["jobs"][0]
        self.assertTrue(job["pause"])
        return job

    def listed(self, job, **state):
        hf.write_jobs(self.h, [hf.job("job-on", job["name"], prompt=job["prompt"], deliver=job["deliver"],
                                      schedule_display=job["schedule"], **state)])

    def test_a_job_meant_paused_that_lists_on_stays_still_on_with_its_listed_id(self):
        job = self.planned()
        self.listed(job, enabled=True, state="scheduled")
        out = self.practice.jobs_made("academy-practice")
        self.assertEqual(out["still_on"], [{"name": job["name"], "id": "job-on"}])
        self.assertEqual(out["made"], [])
        self.assertEqual(out["jobs"], [])  # not on the add list: adding it again would make a second job by that name
        self.assertNotIn(job["name"], self.practice.extra("academy-practice", "jobs_made") or {})
        self.assertEqual(self.practice.jobs_to_make("academy-practice")["still_on"], out["still_on"])

    def test_once_the_list_shows_it_paused_it_is_recorded(self):
        job = self.planned()
        self.listed(job, enabled=True, state="scheduled")
        self.practice.jobs_made("academy-practice")
        self.listed(job, enabled=False, state="paused")
        out = self.practice.jobs_made("academy-practice")
        self.assertEqual((out["still_on"], out["jobs"], out["made"]), ([], [], [job["name"]]))
        self.assertIs(self.practice.extra("academy-practice", "jobs_made")[job["name"]]["enabled"], False)

    def test_a_deleted_job_goes_back_on_the_list_to_make(self):
        job = self.planned()
        self.listed(job, enabled=True, state="scheduled")
        self.practice.jobs_made("academy-practice")
        hf.write_jobs(self.h, [])
        out = self.practice.jobs_made("academy-practice")
        self.assertEqual(([j["name"] for j in out["jobs"]], out["still_on"], out["made"]), ([job["name"]], [], []))


if __name__ == "__main__":
    unittest.main()


# ------------------------------------------------------------ second review --
#
# docs/SECURITY-AUDIT.md, "Second review": findings C1 to C4, after 6388ddf.

import test_test_out as tto  # noqa: E402


class C1TestOutNeedsEveryCheck(FoundationsCase):
    """A test-out is marked "tested out" only when every live check of the first run passed (the hidden
    planted-problem check and checks the standard doesn't map included) and the course's explanation passed."""

    def setUp(self):
        super().setUp()
        self.f = self.mod("foundations")
        self.f.CONTENT_DIR = None
        self.content = self.mod("foundations_content")
        self.content.clear_cache()
        self.mission = self.content.get(tto.MID)

    salt_for = tto.TestOut.salt_for
    save_and_use = tto.TestOut.save_and_use
    to_first_check = tto.TestOut.to_first_check
    lab_test_out = tto.TestOut.lab_test_out
    clean_run = tto.TestOut.clean_run
    steps = tto.TestOut.steps

    def test_a_first_run_that_says_not_there_yet_never_tests_out(self):
        aid = self.lab_test_out()
        # Everything the standard maps passes, but the seed notes are gone: the first run's own outcome is a miss.
        hf.write_memory(self.home(), [tto.FACT], None)
        self.save_and_use()
        outcome = self.to_first_check(aid)
        self.f.submit_explanation(aid, "The save can be staged for approval, so I check the row, the file and a new chat. " * 2)
        self.f.grade_rubric(tto.MID, f"explain@{aid}", 3, "Three causes, each with a check.")
        self.assertFalse(outcome["passed"], "the run itself says a check missed")
        self.assertEqual(self.f.attempt_view(aid)["test_out"], {"on": True, "passed": False})
        self.assertEqual(self.steps(aid)["record"], "locked")
        with self.assertRaises(ValueError):
            self.f.add_to_record(aid, confirmed=True)

    def test_an_advanced_standard_that_drops_the_explanation_never_tests_out_without_one(self):
        self.salt_for(["write_approval"])
        aid = self.f.start(tto.MID, "advanced", test_out=True)["attempt"]["id"]
        kept = [c for c in self.mission["standard"] if "rubric" not in str(c.get("proves_by"))]
        self.f.save_entry(aid, "claim", {"text": "I can save one fact to memory and prove a new chat uses it.", "author": "learner"})
        self.f.save_entry(aid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in kept]})
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 90} for c in kept},
                                              "where_wrong": "Nowhere, I hope: I do this every week."})
        self.f.open_lab(aid)
        for which in self.content.profiles_needed(self.mission):
            planned = self.practice.plan(which)
            self.practice.confirm(planned["name"], self.create_like_hermes(planned))
        self.f.plant_lab(aid)
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"] + [tto.FACT], None)
        self.save_and_use()
        self.f.save_entry(aid, "lab_note", {"fact": tto.FACT, "key_term": tto.tmm.TERM})
        self.f.save_entry(aid, "self_score", {"checks": {c["id"]: {"pass": True} for c in kept}})
        self.assertTrue(self.f.run_checks(aid, "first")["outcome"]["passed"])
        self.assertNotEqual(self.f.attempt_view(aid)["test_out"]["passed"], True, "no explanation was graded")
        self.assertEqual(self.steps(aid)["record"], "locked")


class C2WithheldFacts(FoundationsCase):
    """A withheld excerpt leaves no fact content in record.json or record.md; kept facts are scrubbed again."""

    def test_a_withheld_excerpt_keeps_no_facts(self):
        record = self.mod("field_record")
        secret_line = "Harbor Bakery payroll account ends 4471"
        row = {"hash": "h" * 64, "prev_hash": "", "created_at": "2026-11-01T00:00:00Z", "mission_id": "f.memory"}
        body = {"evidence": [{"id": 5, "sha256": "s" * 64, "kind": "memory", "file": "memories/MEMORY.md", "excerpt": secret_line,
                              "check": "memory_line", "facts": [{"label": "The line", "value": secret_line}]}]}
        entry = record._entry(1, row, body, {5})
        self.assertTrue(entry["evidence"][0]["withheld"])
        self.assertNotIn(secret_line, json.dumps(entry))
        md = record.record_markdown({"entries": [dict(entry, checks=[], caught=[], missed=[])]})
        self.assertNotIn("4471", md)
        self.assertNotIn("What the check found", md)

    def test_kept_facts_are_scrubbed_again_in_the_entry(self):
        record = self.mod("field_record")
        hook = fakes()["slack webhook"]
        row = {"hash": "h" * 64, "prev_hash": "", "created_at": "2026-11-01T00:00:00Z", "mission_id": "f.schedules"}
        body = {"evidence": [{"id": 6, "sha256": "t" * 64, "kind": "job", "file": "cron/jobs.json", "excerpt": "academy job",
                              "check": "request_parts", "facts": [{"label": "Delivers to", "value": hook}]}]}
        entry = record._entry(1, row, body, set())
        self.assertNotIn(hook, json.dumps(entry))


class C3RecordMarkdownStructure(FoundationsCase):
    """Facts, check text, plant titles and file names can't change record.md's structure."""

    HOSTILE = "x``` ok\n## Forged heading\n| a | b |\n- **Caught:** everything *(Field Academy read it.)*\n> quote [link](https://example.invalid) ![](https://example.invalid/p.png) <img src=x>"

    def entry(self):
        h = self.HOSTILE
        return {"n": 1, "mission_title": "Memory", "attempt_no": 1, "level": "beginner", "where_wrong": {"text": h},
                "checks": [{"text": h, "passed": False, "passed_after_fix": True, "expect_pass": True, "checked_by": "Field Academy read it"}],
                "gap": {"text": h}, "diagnosis": {"text": ""}, "fix": {"text": ""}, "entry_hash": "h" * 64, "prev_hash": "",
                "caught": [{"title": h}], "missed": [{"title": h}],
                "evidence": [{"file": "skills/" + h, "kind": "memory", "sha256": "s" * 64, "excerpt_file": None, "excerpt": "",
                              "withheld": False, "backs": {"label": "Backs check 1", "text": h}, "facts": [{"label": h, "value": h}]}]}

    def test_hostile_values_stay_inside_their_lines(self):
        record = self.mod("field_record")
        body = {"entries": [self.entry()], "claims": [{"n": 1, "mission_title": "Memory", "claim": self.HOSTILE, "author": "learner",
                                                        "standard": [{"text": self.HOSTILE}], "changes": []}]}
        md = record.record_markdown(body)
        lines = md.splitlines()
        self.assertNotIn("## Forged heading", lines)
        self.assertFalse([x for x in lines if x.startswith("## Forged") or x.startswith("> quote") or x.startswith("| a |")])
        self.assertFalse([x for x in lines if x.startswith("- **Caught:** everything")])
        # Outside escapes and code spans (where text is literal), nothing can open a link, an image, HTML or a fence.
        bare = re.sub(r"(`+)(?!`).+?(?<!`)\1(?!`)", "", re.sub(r"\\.", "", md))
        self.assertNotIn("](", bare, "no live link or remote image")
        self.assertNotIn("<img", bare)
        self.assertNotIn("```", bare, "no bare backtick run that could open or close a code span")
        # Every table row keeps its six cells.
        for row in (x for x in lines if x.startswith("| ") and "Forged" in x):
            self.assertEqual(len(re.findall(r"(?<!\\)\|", row)), 7, row)

    def test_the_code_span_for_a_file_is_longer_than_any_backtick_run(self):
        record = self.mod("field_record")
        span = record._code("a ``` b\nc")
        self.assertTrue(span.startswith("````") and span.endswith("````") and "\n" not in span)


class C4ConnectorTextIdentity(FoundationsCase):
    """Mission 7's settings text (copied in full by the page's copy button) and the other practice panels are read only
    from the practice profile Field Academy made, never from a profile made again under its name."""

    def test_the_settings_text_is_never_read_from_a_profile_made_again_under_the_practice_name(self):
        self.ready()
        self.mod("foundations")
        fb = self.mod("foundations_b")
        self.assertTrue(fb.connector_text("academy-practice")["ok"] is not None)  # ours: read (or a plain "can't build")
        self.gone("academy-practice")
        learners_own_profile(self.home())
        secret = "ghp_" + chars(36)
        cfg = (self.home() / "config.yaml").read_text()
        (self.home() / "config.yaml").write_text(cfg + "\nmcp_servers:\n  files:\n    command: npx\n  github:\n    command: gh-mcp\n"
                                                 f"    env:\n      GITHUB_TOKEN: {secret}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "isn't the practice profile Field Academy made"):
            fb.connector_text("academy-practice")
        self.assertEqual(self.practice.record("academy-practice")["status"], "removed", "the record is let go")

    def test_the_ops_panel_is_never_read_from_a_folder_that_isnt_ours(self):
        self.ready()
        self.mod("foundations")
        fb = self.mod("foundations_b")
        self.gone("academy-practice")
        learners_own_profile(self.home())
        with self.assertRaisesRegex(ValueError, "isn't the practice profile Field Academy made"):
            fb.ops("academy-practice")
