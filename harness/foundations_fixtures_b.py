"""Fixture states for Foundations missions 7 to 11, one key state per mission, built by driving the real backend the
way harness/foundations_fixtures.py does (a stand-in Hermes root, no `hermes` command, nothing under ~/.hermes).

* f7_lab: mission 7's lab, with the connector settings text the page renders for Ctrl+A, paste, Save.
* f8_watch: mission 8 after two scheduled runs landed, the notice and the cleanup reminder showing.
* f9_checked: mission 9's first check, the rollback read from the app's snapshot list beside the checkpoint branch.
* f10_lab: mission 10's round two, with the logs folder and the doctor and backup commands.
* f11_lab: mission 11's run, with the Start snapshot on the page.
"""

from __future__ import annotations

import json
import time

import foundations_fixtures as base

class KitB(base.Kit):
    MID = ""

    def __init__(self, state, store, data_dir, mid):
        super().__init__(state, store, data_dir)
        self.MID = mid
        self.mission = self.content.get(mid)
        import importlib

        package = state.__name__.rsplit(".", 1)[0]
        self.fb = importlib.import_module(f"{package}.foundations_b")
        self.hr = importlib.import_module(f"{package}.hermes_read_b")
        self.pb = importlib.import_module(f"{package}.plants_b")
        self.hfb = None

    def salt_for(self, wanted):
        lab = self.mission["lab"]
        for n in range(4000):
            salt = f"{n:032x}"
            seed = self.f.seed_for(salt, self.MID, 1)
            got = self.fb.review_pick([], seed) if lab.get("pick") == "review" else self.f.choose_plants(lab["plants"], lab["plants_at"][self.mission["level"]], [], seed)
            if got == list(wanted):
                with self.store.connect() as conn:
                    self.store.meta_set(conn, "f_salt", salt)
                return

    def start(self, plants=()):
        self.salt_for(list(plants))
        self.aid = self.f.start(self.MID)["attempt"]["id"]

    def frozen(self):
        checks = [{"id": c["id"], "text": c["text"]} for c in self.mission["standard"]]
        self.entry("recall", {"answers": ["From memory, as well as I can." for _ in self.mission["recall"]["prompts"]]})
        if self.mission["level"] == "advanced":
            self.entry("claim", {"text": "I can tidy a messy export into one clean table in Hermes and account for every claim, model and change.",
                                 "author": "learner"})
        else:
            self.entry("claim", {"text": self.mission["claim"]["text"], "author": "course"})
        self.entry("standard", {"checks": checks})
        self.entry("prediction", {"checks": {c["id"]: {"expect_pass": n != 3, "confidence": 70 + 5 * n} for n, c in enumerate(checks)},
                                  "where_wrong": "Finding whatever is planted, and the part that needs the live app."})

    def make(self, which):
        planned = self.practice.plan(which, self.aid)
        params = planned["request"]["params"]
        home = self.home(params["name"])
        home.mkdir()
        (home / "SOUL.md").write_text(params["soul"], encoding="utf-8")
        config = self.hf.CONFIG.replace("fallback_providers:\n- provider: openrouter\n  model: openai/gpt-5-mini\n", "fallback_providers: []\n") \
            .replace("mcp_servers:\n  github:\n    enabled: true", "mcp_servers:\n  github:\n    enabled: false")
        self.hf.write_config(home, config)
        (home / "memories").mkdir()
        self.hf.state_db(home).close()
        self.practice.confirm(params["name"], {"path": str(home), "mirrored": {"model_inherited": True}})

    def lab(self, plants):
        self.start(plants)
        self.frozen()
        self.set_up()
        con = self.hf.state_db(self.home())
        folder = self.home() / "practice-folder"
        self.hf.add_session(con, started_at=self.hf.T0 + 1, cwd=str(folder), title="First practice chat")
        con.close()
        self.entry("read", {"step": "idea"})
        self.entry("read", {"step": "expert"})

    def jobs_like_hermes(self):
        todo = self.practice.jobs_to_make("academy-practice")["jobs"]
        jobs = [self.hf.job(f"job-{n}", j["name"], prompt=j["prompt"], deliver=j["deliver"], enabled=not j.get("pause"))
                for n, j in enumerate(todo, start=1)]
        self.hf.write_jobs(self.home(), jobs)
        self.practice.jobs_made("academy-practice")
        return jobs

    def out(self):
        text_base = super().out()
        mid = self.MID
        text_base["mission"] = self.f.mission_view(mid)
        view = self.f.attempt_view(self.aid)
        text_base["view"] = view
        name = view["attempt"]["profile"]
        extra = {}
        for key, call in (("connector_text", lambda: self.fb.connector_text(name)), ("jobs", lambda: self.practice.jobs_to_make(name)),
                          ("ops", lambda: self.fb.ops(name)), ("baseline", lambda: self.fb.baseline_view(name)),
                          ("watch", lambda: self.fb.watch(self.aid))):
            try:
                extra[key] = call()
            except ValueError:
                pass
        text = json.dumps(extra, default=str)
        for raw in {str(self.root.resolve()), str(self.root)}:
            text = text.replace(raw, "~/.hermes")
        text_base.update(json.loads(text))
        # A temp folder under /var resolves to /private/var on a Mac; show both as the home the learner would see.
        return json.loads(json.dumps(text_base).replace("/private~/.hermes", "~/.hermes"))


def f7_lab(kit):
    kit.lab(["twin_connector"])


def f8_watch(kit):
    kit.lab(["vague_request"])
    kit.jobs_like_hermes()
    import sys

    sys.path.insert(0, str(base.ROOT / "tests"))
    import hermes_fixture_b as hb

    hf, T0 = kit.hf, kit.hf.T0
    jobs = json.loads((kit.home() / "cron" / "jobs.json").read_text())["jobs"]
    jobs.append(hf.job("job-y1", "late-orders-list", model="openai/gpt-5-mini", last_status="ok", deliver="local", enabled=True,
                       prompt="Read orders-week.csv in the practice folder and list each late order as a bullet. If the file is missing, "
                              "start your reply with [CRON_FAILURE]."))
    hf.write_jobs(kit.home(), jobs)
    hb.runs_db(kit.home(), [{"job_id": "job-y1", "source": "direct", "claimed_at": hb.iso(T0), "finished_at": hb.iso(T0 + 30)},
                            {"job_id": "job-y1", "claimed_at": hb.iso(T0 + 3600), "scheduled_instant": hb.iso(T0 + 3600)},
                            {"job_id": "job-y1", "claimed_at": hb.iso(T0 + 7800), "scheduled_instant": hb.iso(T0 + 7200)}])
    hb.output_files(kit.home(), "job-y1", 3)
    kit.entry("lab_note", {"for": "first", "job_name": "late-orders-list", "sleep_setting": "Sleep after 30 minutes on power."})


def f9_checked(kit):
    kit.lab(["approvals_off"])
    import sys

    sys.path.insert(0, str(base.ROOT / "tests"))
    import hermes_fixture_b as hb

    hb.checkpoint_branch(kit.home(), kit.home() / "practice-folder")
    import importlib

    yk = importlib.import_module(kit.f.__name__.rsplit(".", 1)[0] + ".yaml_keys")
    path = kit.home() / "config.yaml"
    path.write_text(yk.set_values(path.read_text(encoding="utf-8"), {"checkpoints.enabled": True}), encoding="utf-8")
    kit.entry("lab_note", {"for": "first", "tb": "nothing", "tb_why": "Settings, Safety, Approvals reads Off.", "ta": "undo", "fb": "nothing",
                           "fa": "undo", "cb": "no_connector", "cb_why": "No connectors; a new one starts at full trust.", "ca": "nothing"})
    kit.entry("self_score", {"checks": {c["id"]: {"pass": True} for c in kit.mission["standard"]}})
    sample = {"source": "rollback.list", "enabled": True, "checkpoints": [{"message": "pre-rollback snapshot (restoring to 1a2b3c4d)"},
                                                                         {"message": "before write_file notes.md"}]}
    kit.f.run_checks(kit.aid, "first", sample)


def f10_lab(kit):
    kit.lab(["broken_connector"])


def f11_lab(kit):
    kit.lab(["memory_full", "always_allow"])
    kit.entry("lab_note", {"for": "first", "job": "Turn a messy client export into one clean table."})


def fc_delegation_lab(kit):
    kit.lab(["one_helper"])


def fc_toolsets_lab(kit):
    kit.lab(["wide_connector"])


def fc_teach_review_lab(kit):
    kit.lab(["edited_excerpt"])


RECIPES = (("fc_teach_review_lab", "f.teach-review", fc_teach_review_lab), ("fc_delegation_lab", "f.delegation", fc_delegation_lab), ("fc_toolsets_lab", "f.toolsets", fc_toolsets_lab),
           ("f7_lab", "f.connectors", f7_lab), ("f8_watch", "f.schedules", f8_watch), ("f9_checked", "f.safety", f9_checked),
           ("f10_lab", "f.diagnose", f10_lab), ("f11_lab", "f.review", f11_lab))
