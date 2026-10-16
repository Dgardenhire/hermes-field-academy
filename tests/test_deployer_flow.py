"""The Deployer path end to end: proposal, scenarios, real-deployment evidence, drills, the review packet,
the reviewer's signature, the certificate and the expiry."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from unittest import mock

from deployer_support import DeployerCase, good_proposal

START = datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)
SECRET = bytes(range(32))


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class Flow(DeployerCase):
    def setUp(self):
        super().setUp()
        self.set_time(START)
        self.hermes = self.fence / "fake-hermes-home"  # a stand-in; the real one is never read

    def conn(self):
        return self.store.connect()

    def tools(self):
        import importlib

        return importlib.import_module(f"{self.name}.tools")

    # ------------------------------------------------------------ the brief

    def firm_case(self):
        with self.conn() as c:
            return self.brief_mod().brief_for(self.deployer._brief_seed(c))

    def brief_mod(self):
        import importlib

        return importlib.import_module(f"{self.name}.brief")

    def submit_good_brief(self, **kw):
        path = self.file("proposal.md", good_proposal(self.firm_case(), **kw))
        return self.deployer.brief_submit(path)

    def grade_tool(self, item_id, score, missed=(), feedback="Good on scope; add numbers."):
        return json.loads(self.tools().field_academy_grade_deployer({"item_id": item_id, "score": score, "missed": list(missed), "feedback": feedback}))

    def test_the_brief_is_a_vague_note_with_a_budget_and_one_unsafe_request(self):
        with self.conn() as c:
            view = self.deployer.brief_view(c)
        brief = self.firm_case()
        self.assertIn(brief["owner"], view["brief"])
        self.assertTrue(any("$" in line for line in view["constraints"]))
        self.assertIn(brief["unsafe"]["ask"], view["brief"])
        self.assertEqual(view["sections"], [s["heading"] for s in self.brief_mod().SECTIONS])
        self.assertIsNone(view["rubric"], "the prose rubric stays hidden until the learner sends the document")

    def test_the_brief_follows_audit_architect_build_and_staged_verification(self):
        headings = [s["heading"] for s in self.brief_mod().SECTIONS]
        for needed in ("Audit", "Access list", "Build plan", "Staged verification"):
            self.assertIn(needed, headings)
        self.assertLess(headings.index("Audit"), headings.index("Access list"))
        self.assertLess(headings.index("Access list"), headings.index("Build plan"))
        self.assertLess(headings.index("Build plan"), headings.index("Staged verification"))

    def test_a_proposal_that_meets_every_check_goes_on_to_be_scored_by_your_own_hermes(self):
        reply = self.submit_good_brief()
        self.assertTrue(reply["awaiting_score"], reply.get("missing"))
        self.assertIn("field_academy_grade_deployer", reply["prompt"])
        self.assertIn('item_id "brief"', reply["prompt"])
        self.assertIn(self.firm_case()["brief"], reply["prompt"])

    def test_every_deterministic_check_catches_its_own_failure(self):
        brief = self.firm_case()
        text = good_proposal(brief)
        cases = {
            "price_over": good_proposal(brief, price_setup=brief["setup_budget"] + 500),
            "price_low": good_proposal(brief, price_setup=int(brief["setup_budget"] * 0.2)),
            "monthly_over": good_proposal(brief, monthly=brief["monthly_ceiling"] + 40),
            "build_late": good_proposal(brief, weeks=brief["weeks"] + 3),
            "unsafe_not_refused": good_proposal(brief, unsafe_sentence="We discussed the second request at some length with the partners and agreed that it is a sensible idea for the firm to revisit later on, once the first version of the helper has been running smoothly for a while."),
            "unsafe_no_alternative": good_proposal(brief, unsafe_sentence={"password": "I will not give the helper the shared administrator login to the accounting software, and the reason is simple: every action it took would look as if a partner had done it, which the firm could never explain to a client or an auditor afterwards.", "autosend": "I will not let the helper email client tax figures on its own as soon as it has them, with nobody reading the message first, because one wrong figure sent to a real client cannot be taken back and the firm would carry that.", "ssn": "I will not put Social Security numbers into the prompts the helper sees, because anything placed in a prompt travels to the model provider and the firm should never send that kind of identifier outside its own systems at all."}[brief["unsafe"]["id"]]),
            "unsafe_unnamed": good_proposal(brief, unsafe_sentence="I will not do the second request that came in the second note, because it is far too risky for the firm and for its clients. I offer something safer in its place that the partners can read and approve themselves."),
            "access_broad": good_proposal(brief, access=[f"- {brief['tools'][0]}: full access to everything", f"- {brief['tools'][1]}: read the shared inbox", f"- {brief['tools'][2]}: read the Clients folder"]),
            "access_count": good_proposal(brief, access=[f"- {brief['tools'][0]}: read invoices and balances only, and it cannot create or change anything in the books at all", f"- {brief['tools'][1]}: read the shared inbox and create drafts, and it cannot send mail"]),
            "access_permission": good_proposal(brief, access=[f"- {brief['tools'][0]}: connected to this tool for the purposes in the scope and used by the firm every working day", f"- {brief['tools'][1]}: connected to this tool for the purposes in the scope and used by the firm every working day", f"- {brief['tools'][2]}: connected to this tool for the purposes in the scope and used by the firm every working day"]),
            "access_tools": good_proposal(brief, access=["- the first connected thing: read its entries and list them for the staff each morning in a short summary", "- another connected thing: read its entries and list them for the staff each morning in a short summary", "- one more connected thing: read its entries and list them for the staff each morning in a short summary"]),
        }
        for expected, document in cases.items():
            path = self.file(f"p-{expected}.md", document)
            reply = self.deployer.brief_submit(path)
            found = {m["id"] for m in reply.get("missing", [])}
            self.assertIn(expected, found, f"{expected}: got {found}")
            self.assertFalse(reply.get("awaiting_score"), expected)
        self.assertTrue(self.deployer.brief_submit(self.file("ok.md", text))["awaiting_score"])

    def test_a_blanket_permission_is_fine_when_it_is_refused(self):
        brief = self.firm_case()
        access = [f"- {brief['tools'][0]}: read invoices. No admin rights.", f"- {brief['tools'][1]}: read the shared inbox and create drafts", f"- {brief['tools'][2]}: read the Clients folder only"]
        self.assertTrue(self.deployer.brief_submit(self.file("neg.md", good_proposal(brief, access=access)))["awaiting_score"])

    def test_the_document_must_be_about_this_firm_and_name_the_decider(self):
        brief = self.firm_case()
        other = good_proposal(brief).replace(brief["firm"], "Some Other Firm").replace(brief["owner"], "Alex Doe")
        found = {m["id"] for m in self.deployer.brief_submit(self.file("other.md", other))["missing"]}
        self.assertTrue({"firm_named", "owner_named"} <= found)

    def test_a_missing_section_or_file_is_a_plain_miss(self):
        brief = self.firm_case()
        text = good_proposal(brief).replace("## Staged verification", "## Notes")
        found = {m["id"] for m in self.deployer.brief_submit(self.file("m.md", text))["missing"]}
        self.assertIn("section:Staged verification", found)
        self.assertFalse(self.deployer.brief_submit(str(self.data / "nope.md"))["passed"])
        self.assertFalse(self.deployer.brief_submit(self.file("empty.md", ""))["passed"])
        binary = self.data / "b.bin"
        binary.write_bytes(b"\xff\xfe\x00\x01")
        self.assertIn("not a text document", self.deployer.brief_submit(str(binary))["missing"][0]["what"])

    def test_misses_climb_the_same_hint_ladder_as_missions(self):
        brief = self.firm_case()
        bad = self.file("bad.md", good_proposal(brief, weeks=brief["weeks"] + 4))
        first = self.deployer.brief_submit(bad)["feedback"]
        second = self.deployer.brief_submit(bad)["feedback"]
        self.assertEqual((first["level"], second["level"]), (1, 2))
        self.assertTrue(first["hint"])
        self.assertTrue(second["example"])

    def test_the_prose_is_scored_by_the_learners_own_hermes_through_the_tool(self):
        self.submit_good_brief()
        low = self.grade_tool("brief", 55, missed=[3, 5], feedback="The access list is too wide in one place.")
        self.assertFalse(low["passed"])
        self.assertEqual({m["id"] for m in low["ladder"]["missing"]}, {"point:3", "point:5"})
        self.assertTrue(low["ladder"]["hint"])
        with self.conn() as c:
            self.assertEqual(self.deployer.brief_view(c)["status"], "in_progress")
        self.submit_good_brief()
        high = self.grade_tool("brief", 88)
        self.assertTrue(high["passed"])
        with self.conn() as c:
            view = self.deployer.brief_view(c)
        self.assertEqual(view["status"], "verified")
        self.assertEqual(len(view["rubric"]), 6, "the rubric is shown after scoring")

    def test_a_score_cannot_be_recorded_twice_for_the_same_answer_or_before_one_exists(self):
        self.assertIn("error", self.grade_tool("brief", 90))
        self.submit_good_brief()
        self.assertTrue(self.grade_tool("brief", 90)["passed"])
        self.assertIn("already has a score", self.grade_tool("brief", 99)["error"])

    def test_a_passed_proposal_cannot_be_rechecked_into_a_new_state(self):
        self.submit_good_brief()
        self.grade_tool("brief", 90)
        with self.assertRaises(ValueError):
            self.deployer.brief_submit(self.file("again.md", good_proposal(self.firm_case())))
        with self.assertRaises(ValueError):
            self.deployer.new_brief_case()

    def test_a_new_case_is_a_different_firm_or_budget(self):
        first = self.firm_case()
        self.deployer.new_brief_case()
        second = self.firm_case()
        self.assertNotEqual(first["seed"], second["seed"])

    # -------------------------------------------------------- the scenarios

    def scenario_answer(self):
        return ("I would not just say yes or no. The risk is a wrong message to a real person, so I would offer drafts first and name who approves each one at the practice. "
                "I would put the approval rule and the cost of a mistake in writing, and I would stop if they insisted on sending with nobody reading.")

    def test_there_are_nine_scenarios_with_five_hidden_rubric_points_each(self):
        sc = importlib_import(self.name, "scenarios")
        self.assertEqual(len(sc.SCENARIOS), 9)
        self.assertIn("mcp-integration", sc.IDS)
        for item in sc.SCENARIOS:
            self.assertEqual(len(item["covers"]), 5, item["id"])
            self.assertEqual(len(item["coach"]), 5, item["id"])
        with self.conn() as c:
            views = [self.deployer.scenario_view(c, i) for i in sc.IDS]
        self.assertTrue(all(v["covers"] is None for v in views), "the rubric is hidden until a scenario is scored")

    def test_a_scenario_answer_goes_to_the_learners_hermes_with_the_rubric_and_no_verdict_bias(self):
        reply = self.deployer.scenario_submit("email-customers", self.scenario_answer())
        self.assertIn("scenario.email-customers", reply["prompt"])
        self.assertIn("no single right verdict", reply["prompt"])
        self.assertIn("field_academy_grade_deployer", reply["prompt"])
        with self.assertRaises(ValueError):
            self.deployer.scenario_submit("email-customers", "Yes.")
        with self.assertRaises(ValueError):
            self.deployer.scenario_submit("nope", self.scenario_answer())

    def test_scoring_a_scenario_passes_at_70_and_shows_the_rubric_afterwards(self):
        self.deployer.scenario_submit("shared-login", self.scenario_answer())
        miss = self.grade_tool("scenario.shared-login", 52, missed=[2], feedback="You did not answer the cost concern.")
        self.assertFalse(miss["passed"])
        self.assertEqual(miss["ladder"]["missing"][0]["id"], "point:2")
        self.deployer.scenario_submit("shared-login", self.scenario_answer())
        self.assertTrue(self.grade_tool("scenario.shared-login", 72)["passed"])
        with self.conn() as c:
            view = self.deployer.scenario_view(c, "shared-login")
        self.assertEqual(view["status"], "verified")
        self.assertEqual(len(view["covers"]), 5)
        self.assertIn("error", self.grade_tool("scenario.shared-login", 99))

    def test_the_tool_refuses_an_unknown_item(self):
        self.assertIn("error", self.grade_tool("scenario.nope", 80))
        self.assertIn("error", self.grade_tool("lab.leak", 80))

    def pass_scenarios(self):
        sc = importlib_import(self.name, "scenarios")
        for sid in sc.IDS:
            self.deployer.scenario_submit(sid, self.scenario_answer())
            self.assertTrue(self.grade_tool(f"scenario.{sid}", 80)["passed"])

    # ---------------------------------------------------------- deployment

    def runs(self, now, missed=()):
        out = []
        for day in range(1, 40):
            for hour in (1, 13):
                t = START + timedelta(days=day, hours=hour - 9)
                if t > now:
                    continue
                if any(a <= t <= b for a, b in missed):
                    continue
                out.append(iso(t))
        return out

    def sample(self, now, missed=(), failed=()):
        return {"source": "desktop scheduler list", "times": self.runs(now, missed), "failed": list(failed)}

    def record_doc(self, **overrides):
        sections = {
            "Service": "Google Calendar, owned by Alice Moreno.",
            "Access granted": "- Read events on the Work calendar\n- Nothing else",
            "Access refused": "- Create or change events, not needed\n- Other calendars, not needed",
            "Expiry": "The token expires in 90 days and I change it every 60.",
            "Owner": "Alice Moreno can revoke it in her account settings.",
            "If it leaks": "Revoke the token first, then make a new one, then put it in the profile's .env file.",
        }
        sections.update(overrides)
        return "\n\n".join(f"## {k}\n{v}" for k, v in sections.items()) + "\n"

    def start_deploy(self):
        self.deployer.deploy_start("Google Calendar", "deployer-calendar-brief")

    def pass_deploy(self):
        self.start_deploy()
        reply = self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.assertTrue(reply["passed"], reply.get("missing"))
        self.set_time(START + timedelta(days=4, hours=1))
        out = self.deployer.deploy_check(sample=self.sample(self.now), home=self.hermes)
        self.assertTrue(out["outcome"]["passed"], out["outcome"])

    def test_the_clock_starts_once_and_the_job_must_be_findable(self):
        with self.assertRaises(ValueError):
            self.deployer.deploy_start("Calendar", "my-job")
        with self.assertRaises(ValueError):
            self.deployer.deploy_start("", "deployer-x")
        self.start_deploy()
        with self.assertRaises(ValueError):
            self.deployer.deploy_start("Calendar", "deployer-other")

    def test_the_access_record_is_checked_and_a_blanket_grant_is_refused(self):
        self.start_deploy()
        wide = self.deployer.deploy_record(self.file("wide.md", self.record_doc(**{"Access granted": "- Full access to everything\n- Read events"})))
        self.assertFalse(wide["passed"])
        self.assertIn("access_broad", {m["id"] for m in wide["missing"]})
        thin = self.deployer.deploy_record(self.file("thin.md", self.record_doc(**{"If it leaks": "Tell someone."})))
        self.assertFalse(thin["passed"])
        self.assertEqual(wide["feedback"]["level"], 1)
        self.assertEqual(thin["feedback"]["level"], 2)

    def test_the_check_needs_runs_on_several_days_and_says_which_part_is_short(self):
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.set_time(START + timedelta(days=1, hours=5))
        out = self.deployer.deploy_check(sample=self.sample(self.now), home=self.hermes)["outcome"]
        self.assertFalse(out["passed"])
        ids = {m["id"] for m in out["missing"]}
        self.assertTrue({"few_runs", "few_days", "short_span"} & ids)
        self.assertTrue(out["feedback"]["hint"])
        self.set_time(START + timedelta(days=4, hours=1))
        self.assertTrue(self.deployer.deploy_check(sample=self.sample(self.now), home=self.hermes)["outcome"]["passed"])

    def test_samples_from_separate_checks_add_up(self):
        """If Hermes only shows the last run, checking on different days still builds a history."""
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        final = None
        for day in range(1, 5):
            self.set_time(START + timedelta(days=day, hours=15))
            moments = [iso(START + timedelta(days=day, hours=h - 9)) for h in (1, 13)]
            for stamp in moments:
                final = self.deployer.deploy_check(sample={"source": "desktop scheduler list", "times": [stamp]}, home=self.hermes)
        self.assertTrue(final["outcome"]["passed"], final["outcome"])
        self.assertEqual(final["deploy"]["checks"], 8)

    def test_runs_in_the_future_or_before_the_clock_started_are_ignored(self):
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.set_time(START + timedelta(days=1))
        early = [iso(START - timedelta(days=d)) for d in range(1, 10)]
        future = [iso(START + timedelta(days=d)) for d in range(5, 15)]
        out = self.deployer.deploy_check(sample={"source": "x", "times": early + future}, home=self.hermes)["outcome"]
        self.assertFalse(out["passed"])
        self.assertFalse(out["readable"], "nothing usable remains, so it says it could not read")

    def test_runs_all_in_one_minute_do_not_count_as_a_schedule(self):
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.set_time(START + timedelta(days=5))
        stamps = [iso(START + timedelta(days=d, hours=3)) for d in (1, 2, 3, 4)] + [iso(START + timedelta(days=4, hours=3, seconds=s)) for s in range(1, 8)]
        out = self.deployer.deploy_check(sample={"source": "x", "times": stamps}, home=self.hermes)["outcome"]
        self.assertIn("clustered", {m["id"] for m in out["missing"]})

    def test_a_job_that_mostly_fails_or_has_stopped_does_not_pass(self):
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.set_time(START + timedelta(days=6))
        good = self.runs(START + timedelta(days=4))
        failed = [iso(START + timedelta(days=1, hours=h)) for h in range(0, 30)]
        out = self.deployer.deploy_check(sample={"source": "x", "times": good, "failed": failed}, home=self.hermes)["outcome"]
        self.assertIn("mostly_failed", {m["id"] for m in out["missing"]})
        self.set_time(START + timedelta(days=20))
        out = self.deployer.deploy_check(sample={"source": "x", "times": good}, home=self.hermes)["outcome"]
        self.assertIn("stopped", {m["id"] for m in out["missing"]})

    def test_the_record_must_be_written_before_the_check_can_pass(self):
        self.start_deploy()
        self.set_time(START + timedelta(days=4, hours=1))
        out = self.deployer.deploy_check(sample=self.sample(self.now), home=self.hermes)["outcome"]
        self.assertFalse(out["passed"])
        self.assertIn("record_missing", {m["id"] for m in out["missing"]})

    def fake_hermes(self, job, db=True, logs=True):
        """A stand-in Hermes home under the fence, with a plausible run-history database and a log. Never the real one."""
        home = self.hermes
        (home / "cron").mkdir(parents=True, exist_ok=True)
        (home / "logs").mkdir(exist_ok=True)
        (home / "jobs.json").write_text(json.dumps({"jobs": [{"id": "j-42", "name": job}]}))
        if db:
            con = sqlite3.connect(home / "cron" / "executions.db")
            con.execute("CREATE TABLE executions (id INTEGER PRIMARY KEY, job_id TEXT, started_at TEXT, status TEXT)")
            for stamp in self.runs(START + timedelta(days=5)):
                con.execute("INSERT INTO executions(job_id, started_at, status) VALUES (?, ?, 'ok')", ("j-42", stamp))
            con.execute("INSERT INTO executions(job_id, started_at, status) VALUES ('other', ?, 'ok')", (iso(START + timedelta(days=2)),))
            con.commit()
            con.close()
        if logs:
            lines = [f"{stamp} cron job={job} status=ok" for stamp in self.runs(START + timedelta(days=5))[:3]] + [f"{iso(START + timedelta(days=2))} cron job=another status=ok"]
            (home / "logs" / "agent.log").write_text("\n".join(lines) + "\nBearer abcdefghijklmnopqrstuvwxyz0123456789 in the log\n")

    def test_the_backend_reads_hermes_run_history_without_changing_it(self):
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.fake_hermes("deployer-calendar-brief")
        before = {str(p.relative_to(self.hermes)): (p.stat().st_mtime_ns, p.stat().st_size) for p in self.hermes.rglob("*") if p.is_file()}
        self.set_time(START + timedelta(days=5))
        out = self.deployer.deploy_check(home=self.hermes)
        after = {str(p.relative_to(self.hermes)): (p.stat().st_mtime_ns, p.stat().st_size) for p in self.hermes.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "reading Hermes must not change a single file, nor add a journal or lock file")
        self.assertTrue(out["outcome"]["passed"], out["outcome"])
        self.assertIn("hermes files", out["deploy"]["evidence_note"])

    def test_a_job_with_no_matching_rows_is_unreadable_and_names_the_fallback(self):
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.fake_hermes("some-other-job")
        self.set_time(START + timedelta(days=5))
        out = self.deployer.deploy_check(home=self.hermes)["outcome"]
        self.assertFalse(out["passed"])
        self.assertFalse(out["readable"])
        self.assertTrue(out["fallback"])
        self.assertIn("reviewer", out["detail"])
        self.assertIn("will not take your word", out["detail"])

    def test_nothing_in_the_home_means_the_same_honest_message(self):
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.set_time(START + timedelta(days=5))
        out = self.deployer.deploy_check(home=self.hermes / "does-not-exist")["outcome"]
        self.assertFalse(out["readable"])

    def test_fallback_evidence_never_passes_on_its_own(self):
        self.start_deploy()
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        self.set_time(START + timedelta(days=5))
        excerpt = "\n".join(f"{t} cron deployer-calendar-brief ran ok token=abc123secretvalue456" for t in self.runs(self.now))
        reply = self.deployer.deploy_fallback(excerpt, "Hermes showed no history on my version.")
        self.assertEqual(reply["deploy"]["status"], "awaiting_review")
        self.assertNotEqual(reply["deploy"]["status"], "verified")
        self.assertGreaterEqual(reply["fallback"]["timestamps"], 5)
        with self.conn() as c:
            self.assertEqual(self.deployer._item_state(c, "deploy"), "awaiting_review")
            stored = self.deployer._item(c, "deploy")["detail"]["fallback"]["excerpt"]
        self.assertNotIn("abc123secretvalue456", stored)
        self.assertIn("[removed]", stored)

    def test_fallback_needs_a_real_excerpt_and_the_written_record_first(self):
        self.start_deploy()
        with self.assertRaises(ValueError):
            self.deployer.deploy_fallback("x" * 200, "")
        self.deployer.deploy_record(self.file("access.md", self.record_doc()))
        with self.assertRaises(ValueError):
            self.deployer.deploy_fallback("ran fine", "")
        with self.assertRaises(ValueError):
            self.deployer.deploy_fallback("The job ran on Tuesday and again Wednesday and it all looked fine to me, honestly.", "")

    # ---------------------------------------------------------------- drills

    def note_doc(self):
        return (
            "## What I did\nAt 2 pm on Friday I revoked the token in the service's settings.\n\n"
            "## How I knew\nThe 3 pm scheduled run failed with an error about authorization, and the job list showed the red failed marker.\n\n"
            "## How I fixed it\nI made a new token with read only access and put it in the profile's .env file, then restarted the job.\n\n"
            "## How to stop it surprising a client\nThe job messages the owner when a run fails, so a client hears within the hour.\n"
        )

    def do_drill(self, drill_id, day):
        start = START + timedelta(days=day, hours=-7)   # 02:00, after the 01:00 run
        end = START + timedelta(days=day, hours=5)       # 14:00, after the 13:00 slot is missed
        self.set_time(start)
        self.deployer.drill_start(drill_id)
        self.set_time(end)
        self.deployer.drill_recover(drill_id)
        note = self.deployer.drill_note(drill_id, self.file(f"note-{drill_id}.md", self.note_doc()))
        self.assertTrue(note["passed"], note.get("missing"))
        self.set_time(START + timedelta(days=day + 1, hours=-6))
        return self.deployer.drill_check(drill_id, sample=self.sample(self.now, missed=[(start, end)]), home=self.hermes)

    def test_a_drill_is_yours_to_run_and_says_so(self):
        snap = self.deployer.snapshot()
        self.assertIn("yours to run on your own setup", snap["drill_note"])
        self.assertIn("Nothing is run for you", snap["drill_note"])
        self.assertEqual(len(snap["drills"]), 3)
        self.assertTrue([d for d in snap["drills"] if d["id"] == "ratelimit"][0]["optional"])

    def test_a_drill_needs_the_deployment_first_and_cannot_be_checked_before_recovery(self):
        with self.assertRaises(ValueError):
            self.deployer.drill_start("revoke")
        self.pass_deploy()
        self.deployer.drill_start("revoke")
        with self.assertRaises(ValueError):
            self.deployer.drill_note("revoke", self.file("n.md", self.note_doc()))
        out = self.deployer.drill_check("revoke", sample=self.sample(self.now), home=self.hermes)["outcome"]
        self.assertFalse(out["passed"])
        with self.assertRaises(ValueError):
            self.deployer.drill_start("nope")

    def test_a_drill_passes_when_the_history_shows_a_gap_and_then_a_recovered_run(self):
        self.pass_deploy()
        result = self.do_drill("revoke", 5)
        self.assertTrue(result["outcome"]["passed"], result["outcome"])
        facts = {f["label"]: f["value"] for f in result["outcome"]["facts"]}
        self.assertEqual(facts["Runs during the drill"], "0")
        self.assertEqual(result["drill"]["status"], "verified")

    def test_a_drill_with_runs_that_kept_succeeding_shows_no_gap_and_fails(self):
        self.pass_deploy()
        start = START + timedelta(days=5, hours=-7)
        end = START + timedelta(days=5, hours=5)
        self.set_time(start)
        self.deployer.drill_start("revoke")
        self.set_time(end)
        self.deployer.drill_recover("revoke")
        self.deployer.drill_note("revoke", self.file("n.md", self.note_doc()))
        self.set_time(START + timedelta(days=6, hours=-6))
        out = self.deployer.drill_check("revoke", sample=self.sample(self.now), home=self.hermes)["outcome"]
        self.assertIn("no_gap", {m["id"] for m in out["missing"]})
        self.assertFalse(out["passed"])

    def test_a_failed_run_during_the_drill_counts_as_the_gap(self):
        self.pass_deploy()
        start = START + timedelta(days=5, hours=-7)
        end = START + timedelta(days=5, hours=5)
        self.set_time(start)
        self.deployer.drill_start("revoke")
        self.set_time(end)
        self.deployer.drill_recover("revoke")
        self.deployer.drill_note("revoke", self.file("n.md", self.note_doc()))
        self.set_time(START + timedelta(days=6, hours=-6))
        sample = self.sample(self.now, missed=[(start, end)], failed=[iso(start + timedelta(hours=11))])
        self.assertTrue(self.deployer.drill_check("revoke", sample=sample, home=self.hermes)["outcome"]["passed"])

    def test_a_drill_too_short_to_miss_a_scheduled_run_is_not_proven(self):
        self.pass_deploy()
        start = START + timedelta(days=5, hours=-7)
        end = start + timedelta(minutes=30)
        self.set_time(start)
        self.deployer.drill_start("revoke")
        self.set_time(end)
        self.deployer.drill_recover("revoke")
        self.deployer.drill_note("revoke", self.file("n.md", self.note_doc()))
        self.set_time(START + timedelta(days=6, hours=-6))
        out = self.deployer.drill_check("revoke", sample=self.sample(self.now), home=self.hermes)["outcome"]
        self.assertIn("too_short", {m["id"] for m in out["missing"]})

    def test_a_drill_with_no_recovered_run_yet_says_wait(self):
        self.pass_deploy()
        start = START + timedelta(days=5, hours=-7)
        end = START + timedelta(days=5, hours=5)
        self.set_time(start)
        self.deployer.drill_start("revoke")
        self.set_time(end)
        self.deployer.drill_recover("revoke")
        self.deployer.drill_note("revoke", self.file("n.md", self.note_doc()))
        self.set_time(end + timedelta(minutes=10))
        out = self.deployer.drill_check("revoke", sample=self.sample(self.now, missed=[(start, end)]), home=self.hermes)["outcome"]
        self.assertIn("no_recovery", {m["id"] for m in out["missing"]})

    def test_the_recovery_note_is_checked_and_needed(self):
        self.pass_deploy()
        self.set_time(START + timedelta(days=5, hours=-7))
        self.deployer.drill_start("restart")
        self.set_time(START + timedelta(days=5, hours=5))
        self.deployer.drill_recover("restart")
        bad = self.deployer.drill_note("restart", self.file("bad.md", "## What I did\nI did it.\n"))
        self.assertFalse(bad["passed"])
        self.set_time(START + timedelta(days=6, hours=-6))
        out = self.deployer.drill_check("restart", sample=self.sample(self.now, missed=[(START + timedelta(days=5, hours=-7), START + timedelta(days=5, hours=5))]), home=self.hermes)["outcome"]
        self.assertIn("note_missing", {m["id"] for m in out["missing"]})

    def test_a_drill_without_readable_history_falls_back_to_the_reviewer(self):
        self.pass_deploy()
        start = START + timedelta(days=5, hours=-7)
        end = START + timedelta(days=5, hours=5)
        self.set_time(start)
        self.deployer.drill_start("revoke")
        self.set_time(end)
        self.deployer.drill_recover("revoke")
        self.deployer.drill_note("revoke", self.file("n.md", self.note_doc()))
        self.set_time(end + timedelta(hours=12))
        excerpt = f"{iso(start - timedelta(hours=1))} scheduled run finished ok\n{iso(start + timedelta(hours=11))} scheduled run failed authorization error\n{iso(end + timedelta(hours=11))} scheduled run finished ok after the new token\n"
        reply = self.deployer.drill_fallback("revoke", excerpt, "Hermes did not show history.")
        self.assertEqual(reply["drill"]["status"], "awaiting_review")

    def pass_two_drills(self):
        self.assertTrue(self.do_drill("revoke", 5)["outcome"]["passed"])
        self.assertTrue(self.do_drill("restart", 8)["outcome"]["passed"])

    # --------------------------------------------------------- walkthrough

    def walk_text(self):
        with self.conn() as c:
            job = self.labs.spec_for("lab.cost", self.deployer._passed_lab_row(c, "lab.cost")["seed"])["runaway_job"]
        return (
            f"The client's bill had jumped, and the first thing I did was read the log, which showed the {job} job running every minute. "
            "I explained it to the partner as a schedule that had been left from a test. I changed the schedule to once each weekday, moved it to a cheaper model, and added a daily cap that pauses the jobs. "
            "I told the partner what the cap does and who would be told if it was reached, and I wrote the daily number down for her so she could check it against the next bill herself. "
            "Next time I would read the log before opening any file, because I lost ten minutes opening the wrong one first, and I would say the number out loud to the client sooner."
        )

    def test_the_walkthrough_must_be_about_your_own_labs(self):
        self.pass_labs()
        short = self.deployer.walkthrough_save("I did the labs and they went fine.")
        self.assertFalse(short["passed"])
        generic = self.deployer.walkthrough_save("Something looked wrong and I looked at the files and found the problem and changed it and told the client about what I did. " * 5 + "Next time I would be faster.")
        self.assertIn("walk_specific", {m["id"] for m in generic["missing"]})
        no_reflection = self.deployer.walkthrough_save(self.walk_text().replace("Next time I would read the log", "I read the log").replace("because I lost ten minutes opening the wrong one first", "and it was fine").replace("wrong one", "right one"))
        self.assertIn("walk_reflect", {m["id"] for m in no_reflection["missing"]})
        ok = self.deployer.walkthrough_save(self.walk_text())
        self.assertTrue(ok["passed"], ok.get("missing"))

    def test_a_recording_is_fingerprinted_and_never_copied(self):
        self.pass_labs()
        media = self.fence / "walk.mp4"
        media.write_bytes(b"not really a video" * 1000)
        self.assertTrue(self.deployer.walkthrough_save(self.walk_text(), str(media))["passed"])
        with self.conn() as c:
            saved = self.deployer._item(c, "walkthrough")["detail"]["media"]
        self.assertEqual(saved["name"], "walk.mp4")
        self.assertEqual(saved["bytes"], 18000)
        self.assertEqual(len(saved["sha256"]), 64)
        self.assertFalse(any(p.name == "walk.mp4" for p in self.data.rglob("*")))
        self.assertFalse(self.deployer.walkthrough_save(self.walk_text(), str(self.fence / "missing.mp4"))["passed"])

    # --------------------------------------------------------------- review

    def everything(self, fallback=False):
        self.pass_labs()
        self.submit_good_brief()
        self.assertTrue(self.grade_tool("brief", 86)["passed"])
        self.pass_scenarios()
        if fallback:
            self.start_deploy()
            self.deployer.deploy_record(self.file("access.md", self.record_doc()))
            self.set_time(START + timedelta(days=5))
            excerpt = "\n".join(f"{t} cron deployer-calendar-brief ran ok" for t in self.runs(self.now))
            self.deployer.deploy_fallback(excerpt, "No history shown.")
            for drill, day in (("revoke", 7), ("restart", 10)):
                start, end = START + timedelta(days=day, hours=-7), START + timedelta(days=day, hours=5)
                self.set_time(start)
                self.deployer.drill_start(drill)
                self.set_time(end)
                self.deployer.drill_recover(drill)
                self.deployer.drill_note(drill, self.file(f"note-{drill}.md", self.note_doc()))
                self.set_time(end + timedelta(hours=12))
                self.deployer.drill_fallback(drill, f"{iso(start - timedelta(hours=1))} scheduled run finished ok\n{iso(start + timedelta(hours=11))} scheduled run failed authorization error\n{iso(end + timedelta(hours=11))} scheduled run finished ok after the new token\n", "no history")
        else:
            self.pass_deploy()
            self.pass_two_drills()
        self.assertTrue(self.deployer.walkthrough_save(self.walk_text())["passed"])

    def signoff(self, packet_view, *, scores=None, decision="approved", accepted=None, secret=SECRET, tamper=None, name="Dr. Reviewer"):
        wk = importlib_import(self.name, "walkthrough")
        with self.conn() as c:
            packet = self.deployer._item(c, "review")["detail"]["packet"]
        body = {
            "signoff": "Field Academy Deployer review", "version": 1, "packet_fingerprint": packet["fingerprint"],
            "reviewer": {"name": name, "role": "Hermes consultant"}, "decision": decision,
            "scores": scores or {rid: 3 for rid in wk.RUBRIC_IDS},
            "accepted_evidence": accepted or [], "comments": "Clear work.", "signed_at": iso(self.now + timedelta(days=1)),
        }
        signed = wk.sign(body, secret)
        if tamper:
            tamper(signed)
        return signed

    def trust(self, secret=SECRET, where="local"):
        ed = importlib_import(self.name, "ed25519")
        entry = {"reviewers": [{"name": "Dr. Reviewer", "public_key": ed.public_key(secret).hex()}]}
        if where == "local":
            target = self.data / "deployer" / "reviewers.local.json"
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target = self.fence / "published.json"
            self.deployer.PUBLISHED_REVIEWERS = target
        target.write_text(json.dumps(entry))

    def test_the_packet_waits_until_everything_else_is_done_and_says_what_is_left(self):
        with self.assertRaises(ValueError) as caught:
            self.deployer.build_review_packet("Ada Lovelace")
        message = str(caught.exception)
        for part in ("The key in the open", "A proposal for a three-person firm", "Run one real service for several days", "The walkthrough in your own words"):
            self.assertIn(part, message)

    def test_the_packet_holds_all_the_evidence_with_fingerprints_and_the_learners_own_words(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.assertEqual(view["status"], "awaiting_review")
        folder = pathlib.Path(view["paths"]["folder"])
        for name in ("packet.json", "packet.md", "rubric.md", "signoff-template.json"):
            self.assertTrue((folder / name).is_file(), name)
        packet = json.loads((folder / "packet.json").read_text(encoding="utf-8"))
        wk = importlib_import(self.name, "walkthrough")
        self.assertEqual(packet["fingerprint"], wk.packet_fingerprint(packet))
        self.assertEqual(len(packet["labs"]), 4)
        for lab in packet["labs"]:
            self.assertEqual(len(lab["tree_fingerprint"]), 64)
            self.assertTrue(lab["diagnosis"])
            self.assertTrue(lab["changed"])
        self.assertEqual(len(packet["scenarios"]), 9)
        self.assertEqual(packet["deployment"]["job"], "deployer-calendar-brief")
        self.assertIn("The client's bill had jumped", packet["walkthrough"]["explanation"])
        self.assertTrue(packet["brief"]["text"])
        self.assertEqual(len(packet["brief"]["sha256"]), 64)
        text = (folder / "packet.md").read_text(encoding="utf-8")
        self.assertIn("Their diagnosis", text)
        self.assertIn("could and could not check", text)
        self.assertTrue((folder / "labs" / "leak" / "INCIDENT.md").is_file(), "the repaired folders are copied in for the reviewer")
        rubric = (folder / "rubric.md").read_text(encoding="utf-8")
        for rid in wk.RUBRIC_IDS:
            self.assertIn(rid, rubric)

    def test_the_packet_never_contains_a_key_even_a_fake_one(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        raw = pathlib.Path(view["paths"]["packet_json"]).read_text(encoding="utf-8") + pathlib.Path(view["paths"]["packet_md"]).read_text(encoding="utf-8")
        self.assertNotRegex(raw, r"FAKE-KEY-DO-NOT-USE-[0-9a-f]{8}")

    def test_a_valid_signoff_from_a_published_reviewer_completes_the_path(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust(where="published")
        result = self.deployer.load_signoff(json.dumps(self.signoff(view)))
        self.assertEqual(result["status"], "signed", result["problems"])
        self.assertEqual(result["list"], "published")
        self.assertEqual(result["reviewer"]["name"], "Dr. Reviewer")
        with self.conn() as c:
            self.assertEqual(self.deployer._certificate_status(c), "ready")

    def test_a_local_reviewer_counts_and_is_labelled_as_not_on_the_published_list(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust(where="local")
        result = self.deployer.load_signoff(self.signoff(view))
        self.assertEqual(result["status"], "signed")
        self.assertEqual(result["list"], "local")
        self.deployer.set_version("0.21.3")
        cert = self.deployer.issue_certificate("Ada Lovelace")
        self.assertEqual(cert["body"]["review"]["list"], "local")
        self.assertIn("not on Field Academy's published reviewer list", self.deployer.certificate_markdown(cert))

    def test_a_signature_from_an_unlisted_key_is_valid_but_does_not_count(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        result = self.deployer.load_signoff(self.signoff(view))
        self.assertNotEqual(result["status"], "signed")
        self.assertTrue(any("neither the published list nor your local list" in p for p in result["problems"]))

    def test_a_tampered_signoff_is_refused_whatever_was_changed(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust()
        changes = {
            "score down": (None, lambda s: s["scores"].update({"safety": 1})),
            "score up": ({"safety": 1}, lambda s: s["scores"].update({"safety": 3})),
            "comments": (None, lambda s: s.update({"comments": "Edited."})),
            "name": (None, lambda s: s["reviewer"].update({"name": "Someone Else"})),
            "decision": ({}, lambda s: s.update({"decision": "approved"} if s["decision"] != "approved" else {"decision": "changes_requested"})),
        }
        wk = importlib_import(self.name, "walkthrough")
        for label, (base, change) in changes.items():
            scores = dict({rid: 3 for rid in wk.RUBRIC_IDS}, **(base or {}))
            signed = self.signoff(view, scores=scores)
            change(signed)
            result = self.deployer.load_signoff(signed)
            self.assertNotEqual(result["status"], "signed", label)
            self.assertTrue(any("signature does not match" in p for p in result["problems"]), label)

    def test_a_signoff_for_another_packet_is_refused(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust()
        wrong = self.signoff(view)
        wrong["packet_fingerprint"] = "0" * 64
        resigned = importlib_import(self.name, "walkthrough").sign(wrong, SECRET)
        result = self.deployer.load_signoff(resigned)
        self.assertNotEqual(result["status"], "signed")
        self.assertTrue(any("different packet" in p for p in result["problems"]))

    def test_a_low_score_or_a_refusal_does_not_complete_the_path(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust()
        wk = importlib_import(self.name, "walkthrough")
        scores = {rid: 3 for rid in wk.RUBRIC_IDS}
        scores["safety"] = 1
        low = self.deployer.load_signoff(self.signoff(view, scores=scores))
        self.assertNotEqual(low["status"], "signed")
        self.assertTrue(any("Below the floor: safety" in p for p in low["problems"]))
        refused = self.deployer.load_signoff(self.signoff(view, decision="changes_requested"))
        self.assertNotEqual(refused["status"], "signed")
        self.assertEqual(refused["status"], "rejected")
        incomplete = self.signoff(view)
        incomplete["scores"].pop("lifecycle")
        incomplete = wk.sign(incomplete, SECRET)
        self.assertNotEqual(self.deployer.load_signoff(incomplete)["status"], "signed")

    def test_garbage_in_the_signoff_box_is_a_plain_message(self):
        self.everything()
        self.deployer.build_review_packet("Ada Lovelace")
        with self.assertRaises(ValueError):
            self.deployer.load_signoff("not json at all")
        for junk in ({}, {"reviewer": {"public_key": "zz"}}, {"reviewer": {"public_key": "00" * 32}, "signature": "00" * 64}, []):
            result = self.deployer.load_signoff(junk)
            self.assertNotEqual(result["status"], "signed")

    def test_changing_your_work_after_the_packet_makes_it_stale(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust()
        signed = self.signoff(view)
        self.deployer.walkthrough_save(self.walk_text() + " I also checked the second client's log again.")
        with self.assertRaises(ValueError) as caught:
            self.deployer.load_signoff(signed)
        self.assertIn("Build a new packet", str(caught.exception))

    def test_without_a_signoff_the_learner_holds_deployer_awaiting_review_and_cannot_claim(self):
        self.everything()
        self.deployer.build_review_packet("Ada Lovelace")
        snap = self.deployer.snapshot()
        self.assertEqual(snap["certificate"]["status"], "awaiting_review")
        self.assertEqual(snap["certificate"]["label"], "Guide, awaiting review")
        self.assertEqual(snap["track"]["certificate"]["status"], "in_progress")
        with self.assertRaises(ValueError) as caught:
            self.deployer.issue_certificate("Ada Lovelace")
        self.assertIn("awaiting review", str(caught.exception))

    def test_evidence_that_could_not_be_read_needs_the_reviewers_acceptance_to_count(self):
        self.everything(fallback=True)
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.assertEqual(set(view["fallback_items"]), {"deploy", "drill.revoke", "drill.restart"})
        self.trust()
        snap = self.deployer.snapshot()
        self.assertEqual(snap["certificate"]["status"], "awaiting_review")
        # approved, but accepting only the deployment
        result = self.deployer.load_signoff(self.signoff(view, accepted=["deploy"]))
        self.assertEqual(result["status"], "signed")
        self.assertEqual(set(result["needs_acceptance"]), {"drill.revoke", "drill.restart"})
        with self.conn() as c:
            self.assertEqual(self.deployer._item_state(c, "deploy"), "verified")
            self.assertEqual(self.deployer._item_state(c, "drills"), "awaiting_review")
            self.assertEqual(self.deployer._certificate_status(c), "awaiting_review")
        with self.assertRaises(ValueError):
            self.deployer.issue_certificate("Ada Lovelace")

    def test_when_the_reviewer_accepts_all_of_it_the_certificate_can_be_claimed_and_says_how_it_was_proved(self):
        self.everything(fallback=True)
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust()
        self.deployer.load_signoff(self.signoff(view, accepted=["deploy", "drill.revoke", "drill.restart"]))
        self.deployer.set_version("0.21.3")
        cert = self.deployer.issue_certificate("Ada Lovelace")
        self.assertEqual(cert["body"]["deployment"]["status"], "accepted by the reviewer")
        self.assertTrue(all(d["status"] == "accepted by the reviewer" for d in cert["body"]["drills"]))

    # ----------------------------------------------------------- certificate

    def issue(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust(where="published")
        self.deployer.load_signoff(self.signoff(view))
        self.deployer.set_version("0.21.3", "typed by you")
        return self.deployer.issue_certificate("Ada Lovelace")

    def test_the_certificate_carries_the_proof_the_review_and_the_hermes_version(self):
        cert = self.issue()
        body = cert["body"]
        state = importlib_import(self.name, "state")
        self.assertTrue(cert["valid"])
        self.assertTrue(state.verify_certificate(body))
        self.assertEqual(body["hermes_version"]["value"], "0.21.3")
        self.assertEqual(body["review"]["reviewer"], "Dr. Reviewer")
        self.assertEqual(body["review"]["list"], "published")
        self.assertEqual(len(body["review"]["key_fingerprint"]), 16)
        self.assertEqual(len(body["labs"]), 4)
        self.assertEqual(len(body["scenarios"]), 9)
        self.assertIn("review", " ".join(body["shows"]).lower())
        self.assertTrue(any("don't issue, review or endorse it" in line for line in body["does_not_show"]))
        self.assertEqual(body["record_format"], 2)
        self.assertEqual(body["record"], "Field Academy Guide Field Record")
        self.assertNotIn("certificate", body)
        self.assertEqual(body["disclaimer"], "Self-issued with Field Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research.")
        self.assertTrue(any("not years of client work" in line for line in body["does_not_show"]))
        self.assertIn("tonysimons.dev", body["lifecycle_credit"])
        self.assertIn("does not endorse", body["lifecycle_credit"])
        self.assertIn("review", body["issuer"].lower())

    def test_an_edited_certificate_stops_matching_its_number(self):
        cert = self.issue()
        state = importlib_import(self.name, "state")
        body = json.loads(json.dumps(cert["body"]))
        body["review"]["scores"]["safety"] = 3
        body["name"] = "Someone Else"
        self.assertFalse(state.verify_certificate(body))

    def test_the_certificate_needs_a_name_and_a_known_hermes_version(self):
        self.everything()
        view = self.deployer.build_review_packet("Ada Lovelace")
        self.trust()
        self.deployer.load_signoff(self.signoff(view))
        # No Hermes the plugin can read a version from. Run inside Hermes (or with Hermes importable), the version is
        # read from its install stamp, so the premise is pinned here instead of depending on the machine.
        evidence = importlib_import(self.name, "evidence")
        with mock.patch.object(evidence, "detect_version", return_value=("", "")), self.assertRaises(ValueError) as caught:
            self.deployer.issue_certificate("Ada Lovelace")
        self.assertIn("Hermes version", str(caught.exception))
        self.deployer.set_version("0.21.3")
        with self.assertRaises(ValueError):
            self.deployer.issue_certificate("   ")

    def test_the_certificate_is_issued_once_and_saves_a_readable_copy(self):
        cert = self.issue()
        again = self.deployer.issue_certificate("Someone Else")
        self.assertEqual(again["number"], cert["number"])
        saved = self.deployer.save_certificate()
        text = pathlib.Path(saved["markdown"]).read_text(encoding="utf-8")
        self.assertIn("Guide path", text)
        self.assertIn(cert["number"], text)
        self.assertIn("When the major version of Hermes changes", text)
        self.assertEqual(json.loads(pathlib.Path(saved["json"]).read_text(encoding="utf-8"))["number"], cert["number"])

    def test_the_other_paths_certificates_and_snapshot_are_untouched(self):
        self.pass_track("ambassador")
        state = self.state
        before = state.issue_certificate("ambassador", "Ada Lovelace")
        self.issue()
        after = state.get_certificate("ambassador")
        self.assertEqual(before["number"], after["number"])
        self.assertEqual([t["id"] for t in state.snapshot()["tracks"]], ["ambassador", "operator", "integrator", "architect"])

    # -------------------------------------------------------------- expiry

    def test_the_certificate_says_current_until_the_series_changes(self):
        self.issue()
        for version in ("0.21.3", "0.21.9", "v0.21.10"):
            self.deployer.set_version(version)
            with self.conn() as c:
                self.assertEqual(self.deployer.reverify_view(c)["status"], "current", version)
        self.deployer.set_version("0.22.0")
        with self.conn() as c:
            status = self.deployer.reverify_view(c)
        self.assertEqual(status["status"], "reverify")
        self.assertIn("Re-verify needed", status["words"])
        self.assertIn("0.21.3", status["words"])
        self.assertEqual(self.deployer.snapshot()["certificate"]["reverify"]["status"], "reverify")

    def test_a_major_version_change_expires_it_and_once_the_major_is_above_zero_only_the_major_counts(self):
        ev = importlib_import(self.name, "evidence")
        self.assertEqual(ev.reverify_status("1.4.0", "1.9.2")["status"], "current")
        self.assertEqual(ev.reverify_status("1.4.0", "2.0.0")["status"], "reverify")
        self.assertEqual(ev.reverify_status("0.21.3", "0.22.0")["status"], "reverify")
        self.assertEqual(ev.reverify_status("", "1.0")["status"], "unknown")
        self.assertEqual(ev.reverify_status("1.0", "")["status"], "unknown")
        self.assertEqual(ev.parse_version("Hermes Agent v0.21.3-beta"), (0, 21, 3))
        self.assertIsNone(ev.parse_version("none"))

    def test_a_version_that_does_not_read_as_one_is_refused(self):
        with self.assertRaises(ValueError):
            self.deployer.set_version("latest")

    def test_reverify_repeats_the_four_labs_on_new_cases_and_records_the_new_version(self):
        self.issue()
        with self.assertRaises(ValueError):
            self.deployer.start_reverify()
        self.deployer.set_version("0.22.0")
        old_seeds = {lab: self.deployer.lab_view_by(lab)["seed"] if hasattr(self.deployer, "lab_view_by") else None for lab in ()}
        before = self.deployer.snapshot()
        started = self.deployer.start_reverify()
        self.assertTrue(started["open"])
        after = self.deployer.snapshot()
        for old, new in zip(before["labs"], after["labs"]):
            self.assertNotEqual(old["seed"], new["seed"], "re-verify needs a new case")
            self.assertEqual(new["status"], "in_progress")
        with self.assertRaises(ValueError):
            self.deployer.finish_reverify()
        self.set_time(self.now + timedelta(days=2))
        for lab_id in self.deployer.LAB_ORDER:
            self.pass_lab_current(lab_id)
        done = self.deployer.finish_reverify()
        self.assertEqual(done["status"], "current")
        self.assertEqual(done["renewed"][0]["version"], "0.22.0")
        self.assertEqual(self.deployer.snapshot()["certificate"]["issued"]["body"]["hermes_version"]["value"], "0.21.3", "the issued certificate itself is never rewritten")

    def pass_lab_current(self, lab_id):
        from lab_solutions import SOLVERS

        with self.conn() as c:
            row = self.deployer._lab_row(c, lab_id)
        spec = self.labs.spec_for(lab_id, row["seed"])
        diagnosis = SOLVERS[lab_id](spec, pathlib.Path(row["folder"]))
        self.assertTrue(self.deployer.check_lab(lab_id, diagnosis)["outcome"]["passed"])

    def test_the_version_can_be_read_from_package_metadata_without_running_hermes(self):
        ev = importlib_import(self.name, "evidence")
        found = ev.detect_version()
        self.assertIsInstance(found, tuple)
        with self.conn() as c:
            current = self.deployer.current_version(c)
        self.assertIn("machine_read", current)

    def test_the_install_stamp_wins_over_stale_package_metadata(self):
        # Hermes reports its version from install-stamp.json; package metadata can lag behind it.
        ev = importlib_import(self.name, "evidence")
        folder = pathlib.Path(tempfile.mkdtemp())
        stamp = folder / "install-stamp.json"
        stamp.write_text('{"schemaVersion": 2, "baseVersion": "0.22.0", "displayVersion": "0.22.0+5.g09ba2eb"}', encoding="utf-8")
        self.assertEqual(ev._stamp_version(stamp), "0.22.0")
        stamp.write_text('{"baseVersion": "not a version"}', encoding="utf-8")
        self.assertEqual(ev._stamp_version(stamp), "")
        self.assertEqual(ev._stamp_version(folder / "missing.json"), "")

    # ------------------------------------------------------------------ view

    def test_the_trail_has_four_phases_nine_waypoints_and_a_summit(self):
        snap = self.deployer.snapshot()
        track = snap["track"]
        self.assertEqual([p["name"] for p in track["levels"]], ["Audit", "Architect", "Build and integrate", "Staged verification"])
        self.assertEqual(len(track["missions"]), 9)
        self.assertEqual(track["certificate"]["status"], "in_progress")
        self.assertTrue(track["here"])
        for phase in track["levels"]:
            self.assertTrue(set(phase["missions"]) <= {m["id"] for m in track["missions"]})
        self.assertEqual(sum(len(p["missions"]) for p in track["levels"]), 9)

    def test_the_summary_line_for_the_terminal_command(self):
        self.assertIn("Guide: 0 of 9 parts passed", self.deployer.summary_line())
        command = self.pkg._academy_command("")
        self.assertIn("Guide:", command)

    def test_the_honest_copy_says_what_it_shows_and_what_it_does_not(self):
        about = self.deployer.snapshot()["about"]
        joined = " ".join(about["shows"] + about["does_not"])
        self.assertIn("competence shown in labs", joined)
        self.assertIn("not years of client work", joined)
        self.assertIn("Nous Research and the Hermes team don't issue, review or endorse it", joined)
        self.assertIn("reviewer you chose", joined)
        self.assertIn("could not read Hermes", joined)
        self.assertEqual(about["disclaimer"], "Self-issued with Field Academy, a community plugin for Hermes Agent. Not issued or endorsed by Nous Research.")
        self.assertIn("Created by its holder", about["issuer"])
        self.assertIn("reviewer the holder chose", about["issuer"])
        self.assertNotIn("proposal for Nous", joined + about["issuer"])
        self.assertIn("does not endorse", about["lifecycle_credit"])
        self.assertIn("offers no certification", about["lifecycle_credit"])


class BriefVariants(DeployerCase):
    def test_a_good_proposal_passes_on_every_variant_of_the_brief(self):
        kinds, tools, firms = set(), set(), set()
        for seed in range(1, 60):
            case = self.brief.brief_for(seed)
            kinds.add(case["unsafe"]["id"])
            tools.add(tuple(case["tools"]))
            firms.add(case["firm"])
            result = self.brief.check(good_proposal(case), case)
            self.assertEqual(result["missing"], [], f"seed {seed}: {result['missing']}")
        self.assertEqual(kinds, {"password", "autosend", "ssn"})
        self.assertEqual(len(tools), 2)
        self.assertEqual(len(firms), 3)

    def test_the_brief_is_reproducible_per_seed_and_varies_across_seeds(self):
        self.assertEqual(self.brief.brief_for(9), self.brief.brief_for(9))
        self.assertGreater(len({self.brief.brief_for(s)["brief"] for s in range(1, 40)}), 20)

    def test_using_the_refused_login_anywhere_else_is_caught(self):
        for seed in range(1, 80):
            case = self.brief.brief_for(seed)
            if case["unsafe"]["id"] != "password":
                continue
            text = good_proposal(case).replace("## Build plan\nWeek 1", "## Build plan\nWeek 1 log in with the shared administrator login and")
            ids = {m["id"] for m in self.brief.check(text, case)["missing"]}
            self.assertIn("unsafe_granted", ids)
            return
        self.fail("no seed gave the password variant")

    def test_a_proposal_for_one_firm_does_not_pass_for_another(self):
        a, b = self.brief.brief_for(1), self.brief.brief_for(2)
        if a["firm"] == b["firm"]:
            b = next(self.brief.brief_for(s) for s in range(3, 40) if self.brief.brief_for(s)["firm"] != a["firm"])
        ids = {m["id"] for m in self.brief.check(good_proposal(a), b)["missing"]}
        self.assertIn("firm_named", ids)


def importlib_import(name, module):
    import importlib

    return importlib.import_module(f"{name}.{module}")
