"""Fixture states for the Deployer path, built by driving the real backend.

Used by make_fixtures.py. Each recipe takes the real deployer module and the store (so time can move), runs the
real functions in a throwaway data folder, and returns extra fixtures: real outcomes the harness hands back when a
button is pressed. The harness itself runs no `hermes` command and touches nothing under ~/.hermes. The reviewer's
key below is a made-up test key, used only to sign test sign-offs inside the throwaway folder.
"""

from __future__ import annotations

import importlib
import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=timezone.utc)
BASE = NOW - timedelta(days=15)
TEST_KEY = bytes(range(32))


def _tests():
    sys.path.insert(0, str(ROOT / "tests"))
    import lab_solutions
    import proposals

    return lab_solutions, proposals


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class Kit:
    """The pieces a recipe needs, found from the real package that make_fixtures loaded."""

    def __init__(self, state, store, data_dir):
        package = state.__name__.rsplit(".", 1)[0]
        self.state = state
        self.store = store
        self.data = pathlib.Path(data_dir)
        self.dep = importlib.import_module(f"{package}.deployer")
        self.labs = importlib.import_module(f"{package}.labs")
        self.brief = importlib.import_module(f"{package}.brief")
        self.scen = importlib.import_module(f"{package}.scenarios")
        self.wt = importlib.import_module(f"{package}.walkthrough")
        self.ed = importlib.import_module(f"{package}.ed25519")
        self.solutions, self.proposals = _tests()
        counter = iter(range(4100, 4200))
        self.dep.new_seed = lambda: next(counter)

    def at(self, moment):
        self.store.clock = lambda: moment
        self.now = moment

    def write(self, name, text):
        target = self.data / name
        target.write_text(text, encoding="utf-8")
        return str(target)

    # -- labs and the written parts --------------------------------------

    def solve_lab(self, lab_id, check=True):
        view = self.dep.open_lab(lab_id)
        spec = self.labs.spec_for(lab_id, view["seed"])
        diagnosis = self.solutions.SOLVERS[lab_id](spec, pathlib.Path(view["path"]))
        if check:
            reply = self.dep.check_lab(lab_id, diagnosis)
            assert reply["outcome"]["passed"], reply["outcome"]["missing"]
        return view, spec, diagnosis

    def pass_labs(self):
        for offset, lab_id in enumerate(self.dep.LAB_ORDER):
            self.at(BASE + timedelta(hours=3 * offset))
            self.solve_lab(lab_id)

    def firm_case(self):
        with self.store.connect() as conn:
            return self.brief.brief_for(self.dep._brief_seed(conn))

    def pass_brief(self):
        reply = self.dep.brief_submit(self.write("proposal.md", self.proposals.good_proposal(self.firm_case())))
        assert reply["awaiting_score"], reply["missing"]
        self.dep.grade_deployer("brief", 86, [], "Clear scope, a believable price and a firm, kind refusal. Add who restarts it on a bad Monday.")

    def answer(self):
        return ("I would not simply say yes or no. The risk is a wrong message to a real person, so I would offer drafts first and name who approves each one. "
                "I would put the approval rule and the cost of a mistake in writing, and I would stop if they insisted on sending with nobody reading.")

    def pass_scenarios(self, count=9):
        for sid in self.scen.IDS[:count]:
            self.dep.scenario_submit(sid, self.answer())
            self.dep.grade_deployer(f"scenario.{sid}", 80, [], "You weighed both duties and named who decides.")

    # -- deployment and drills -------------------------------------------

    def runs(self, now, start, missed=()):
        out = []
        for day in range(1, 40):
            for hour in (1, 13):
                t = start + timedelta(days=day, hours=hour - 9)
                if t > now or any(a <= t <= b for a, b in missed):
                    continue
                out.append(iso(t))
        return out

    def record_doc(self):
        return (
            "## Service\nGoogle Calendar, owned by Alice Moreno.\n\n"
            "## Access granted\n- Read events on the Work calendar\n- Nothing else\n\n"
            "## Access refused\n- Create or change events, not needed\n- Other calendars, not needed\n\n"
            "## Expiry\nThe token expires in 90 days and I change it every 60.\n\n"
            "## Owner\nAlice Moreno can revoke it in her account settings.\n\n"
            "## If it leaks\nRevoke the token first, then make a new one, then put it in the profile's .env file.\n"
        )

    def start_deploy(self, when):
        self.at(when)
        self.dep.deploy_start("Google Calendar, read only", "deployer-calendar-brief")
        out = self.dep.deploy_record(self.write("access-record.md", self.record_doc()))
        assert out["passed"], out["missing"]
        self.deploy_start_time = when

    def pass_deploy(self, start, days=5):
        self.start_deploy(start)
        self.at(start + timedelta(days=days, hours=1))
        out = self.dep.deploy_check(sample={"source": "desktop scheduler list", "times": self.runs(self.now, start)}, home=self.data / "no-hermes-here")
        assert out["outcome"]["passed"], out["outcome"]

    def note_doc(self):
        return (
            "## What I did\nAt 2 pm on Friday I revoked the token in the service's settings.\n\n"
            "## How I knew\nThe 3 pm scheduled run failed with an error about authorization, and the job list showed the red failed marker.\n\n"
            "## How I fixed it\nI made a new token with read only access and put it in the profile's .env file, then restarted the job.\n\n"
            "## How to stop it surprising a client\nThe job messages the owner when a run fails, so a client hears within the hour.\n"
        )

    def do_drill(self, drill_id, deploy_start, day, finish=True):
        start = deploy_start + timedelta(days=day, hours=-7)
        end = deploy_start + timedelta(days=day, hours=5)
        self.at(start)
        self.dep.drill_start(drill_id)
        self.at(end)
        self.dep.drill_recover(drill_id)
        note = self.dep.drill_note(drill_id, self.write(f"note-{drill_id}.md", self.note_doc()))
        assert note["passed"], note["missing"]
        if finish:
            self.at(deploy_start + timedelta(days=day + 1, hours=-6))
            out = self.dep.drill_check(drill_id, sample={"source": "desktop scheduler list", "times": self.runs(self.now, deploy_start, [(start, end)])}, home=self.data / "no-hermes-here")
            assert out["outcome"]["passed"], out["outcome"]

    def walk_text(self):
        with self.store.connect() as conn:
            job = self.labs.spec_for("lab.cost", self.dep._passed_lab_row(conn, "lab.cost")["seed"])["runaway_job"]
        return (
            f"The client's bill had jumped, and the first thing I did was read the log, which showed the {job} job running every minute. "
            "I explained it to the partner as a schedule that had been left from a test. I changed the schedule to once each weekday, moved it to a cheaper model, and added a daily cap that pauses the jobs. "
            "I told the partner what the cap does and who would be told if it was reached, and I wrote the daily number down for her so she could check it against the next bill herself. "
            "Next time I would read the log before opening any file, because I lost ten minutes opening the wrong one first, and I would say the number out loud to the client sooner."
        )

    def everything(self):
        self.pass_labs()
        self.at(BASE + timedelta(days=1))
        self.pass_brief()
        self.pass_scenarios()
        start = BASE + timedelta(days=2)
        self.pass_deploy(start)
        self.do_drill("revoke", start, 6)
        self.do_drill("restart", start, 9)
        self.at(BASE + timedelta(days=12))
        saved = self.dep.walkthrough_save(self.walk_text())
        assert saved["passed"], saved["missing"]
        self.at(BASE + timedelta(days=13))
        self.dep.build_review_packet("Ada Lovelace")

    def trust_and_sign(self, accepted=()):
        target = self.data / "deployer" / "reviewers.local.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"reviewers": [{"name": "Dr. Reviewer", "public_key": self.ed.public_key(TEST_KEY).hex()}]}))
        with self.store.connect() as conn:
            packet = self.dep._item(conn, "review")["detail"]["packet"]
        body = {
            "signoff": "Field Academy Deployer review", "version": 1, "packet_fingerprint": packet["fingerprint"],
            "reviewer": {"name": "Dr. Reviewer", "role": "Hermes consultant"}, "decision": "approved",
            "scores": {rid: 3 for rid in self.wt.RUBRIC_IDS}, "accepted_evidence": list(accepted),
            "comments": "Clear diagnoses and a firm, kind refusal. Say the daily number out loud sooner.",
            "signed_at": iso(self.now + timedelta(days=1)),
        }
        self.at(self.now + timedelta(days=1))
        self.dep.load_signoff(self.wt.sign(body, TEST_KEY))


# ------------------------------------------------------------------ recipes --


def fresh(kit):
    kit.at(NOW)
    return {}


def progress(kit):
    """One lab passed, one opened and missed twice, one opened, the proposal waiting to be scored, some scenarios."""
    kit.at(BASE)
    kit.solve_lab("lab.leak")
    kit.at(BASE + timedelta(days=1))
    cost = kit.dep.open_lab("lab.cost")
    (pathlib.Path(cost["path"]) / "README-CLIENT.txt").write_text((pathlib.Path(cost["path"]) / "README-CLIENT.txt").read_text() + "\n(I looked at this.)\n")
    outcome = None
    for _ in range(2):
        outcome = kit.dep.check_lab("lab.cost", "I think the job ran too often and cost too much money, so I will look at it and sort it out.")
    kit.dep.open_lab("lab.vault")
    kit.dep.brief_submit(kit.write("proposal.md", kit.proposals.good_proposal(kit.firm_case())))
    kit.pass_scenarios(3)
    kit.at(NOW)
    return {"lab_outcome": outcome["outcome"]}


def lab_open(kit):
    kit.at(BASE)
    kit.dep.open_lab("lab.leak")
    kit.at(NOW)
    return {}


def deploy(kit):
    """Labs, proposal and scenarios done; the deployment running for three days, one check short of enough history."""
    kit.pass_labs()
    kit.at(BASE + timedelta(days=1))
    kit.pass_brief()
    kit.pass_scenarios()
    start = NOW - timedelta(days=3, hours=2)
    kit.start_deploy(start)
    kit.at(start + timedelta(days=1, hours=5))
    out = kit.dep.deploy_check(sample={"source": "desktop scheduler list", "times": kit.runs(kit.now, start)}, home=kit.data / "no-hermes-here")
    kit.at(NOW)
    return {"deploy_check_outcome": out["outcome"]}


def deploy_unreadable(kit):
    """Hermes shows nothing for the job: the check says so and offers the reviewer's packet."""
    kit.pass_labs()
    kit.at(BASE + timedelta(days=1))
    kit.pass_brief()
    kit.pass_scenarios()
    start = NOW - timedelta(days=4)
    kit.start_deploy(start)
    kit.at(NOW)
    out = kit.dep.deploy_check(home=kit.data / "no-hermes-here")
    return {"deploy_check_outcome": out["outcome"]}


def drills(kit):
    """The deployment verified, one drill passed, one recovered and waiting for its check."""
    kit.pass_labs()
    kit.at(BASE + timedelta(days=1))
    kit.pass_brief()
    kit.pass_scenarios()
    start = NOW - timedelta(days=11)
    kit.pass_deploy(start)
    kit.do_drill("restart", start, 7)
    kit.do_drill("revoke", start, 9, finish=False)
    kit.at(NOW)
    return {}


def review(kit):
    kit.everything()
    kit.at(NOW)
    return {}


def ready(kit):
    kit.everything()
    kit.trust_and_sign()
    kit.at(NOW)
    return {}


def issued(kit):
    kit.everything()
    kit.trust_and_sign()
    kit.dep.set_version("0.21.3", "read from Hermes")
    kit.at(NOW)
    cert = kit.dep.issue_certificate("Ada Lovelace")
    return {"certificate": cert, "saved": kit.dep.save_certificate()}


def reverify(kit):
    out = issued(kit)
    kit.dep.set_version("0.22.0", "read from Hermes")
    return out


RECIPES = (
    ("dp_fresh", fresh), ("dp_progress", progress), ("dp_lab", lab_open), ("dp_deploy", deploy), ("dp_unreadable", deploy_unreadable),
    ("dp_drills", drills), ("dp_review", review), ("dp_ready", ready), ("dp_issued", issued), ("dp_reverify", reverify),
)
