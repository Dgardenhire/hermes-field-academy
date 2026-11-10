"""Fixture states for the Foundations mission screens, built by driving the real backend.

Used by make_fixtures.py. Each recipe runs the real foundations and practice modules in the throwaway data folder,
with a stand-in Hermes root (tests/hermes_fixture.py lays down what profiles.create would) in a second throwaway
folder, and returns what the page's routes would answer. No `hermes` command runs and nothing under ~/.hermes is
touched. The stand-in root's path is replaced with ~/.hermes in the output so no temp path reaches a screenshot.
"""

from __future__ import annotations

import datetime
import importlib
import itertools
import json
import os
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
MID = "f.memory"
FACT = "Harbor Bakery uses QuickBooks Online; the other five use Xero"


def _hf():
    sys.path.insert(0, str(ROOT / "tests"))
    import hermes_fixture

    return hermes_fixture


class Kit:
    def __init__(self, state, store, data_dir):
        package = state.__name__.rsplit(".", 1)[0]
        self.store = store
        self.f = importlib.import_module(f"{package}.foundations")
        self.practice = importlib.import_module(f"{package}.practice")
        self.content = importlib.import_module(f"{package}.foundations_content")
        self.fr = importlib.import_module(f"{package}.field_record")
        evidence = importlib.import_module(f"{package}.evidence")
        # The shots show a version read the way a real install reports it, never this machine's own Hermes.
        evidence.detect_version_detail = lambda: {"value": "0.22.4", "source": "git tag", "exact": True}
        self.issued = None
        self.hf = _hf()
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="fa-harness-hermes-"))
        (self.root / "profiles").mkdir()
        self.saved_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = str(self.root)
        self.practice._wall = lambda: 0.0  # the stand-in profiles are always "made after the plan"
        self.mission = self.content.get(MID)
        self.aid = None
        # Time moves two minutes with every stamp, so the record's active time reads like a real sitting.
        start, ticks = store.clock(), itertools.count()
        store.clock = lambda: start + datetime.timedelta(minutes=2) * next(ticks)

    def close(self):
        if self.saved_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self.saved_home
        shutil.rmtree(self.root, ignore_errors=True)

    def home(self, name="academy-practice"):
        return self.root / "profiles" / name

    def salt_for(self, wanted):
        for n in range(800):
            salt = f"{n:032x}"
            seed = self.f.seed_for(salt, MID, 1)
            if self.f.choose_plants(self.mission["lab"]["plants"], 1, [], seed) == wanted:
                with self.store.connect() as conn:
                    self.store.meta_set(conn, "f_salt", salt)
                return

    def start(self, plants=("write_approval",)):
        self.salt_for(list(plants))
        self.aid = self.f.start(MID)["attempt"]["id"]

    def entry(self, kind, body):
        self.f.save_entry(self.aid, kind, body)

    def frozen(self):
        self.entry("recall", {"answers": ["Hermes's words, the row's result, then the file.", "The tool schemas, about 9,000 tokens."]})
        self.entry("claim", {"text": self.mission["claim"]["text"], "author": "course"})
        self.entry("standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in self.mission["standard"]]})
        self.entry("prediction", {"checks": {"s1": {"expect_pass": True, "confidence": 90}, "s2": {"expect_pass": True, "confidence": 75},
                                             "s3": {"expect_pass": True, "confidence": 70}, "s4": {"expect_pass": False, "confidence": 60}},
                                  "where_wrong": "Finding whatever is planted. I don't know where to look yet."})

    def make(self, which):
        planned = self.practice.plan(which, self.aid)
        params = planned["request"]["params"]
        home = self.home(params["name"])
        home.mkdir()
        (home / "SOUL.md").write_text(params["soul"], encoding="utf-8")
        self.hf.write_config(home, self.hf.CONFIG)
        (home / "memories").mkdir()
        self.hf.state_db(home).close()
        self.practice.confirm(params["name"], {"path": str(home), "mirrored": {"model_inherited": True}})

    def set_up(self):
        self.f.open_lab(self.aid)
        for which in self.mission["lab"]["profiles"] if "profiles" in self.mission["lab"] else self.content.profiles_needed(self.mission):
            self.make(which)
        self.f.plant_lab(self.aid)

    def worked(self, staged=True):
        hf = self.hf
        con = hf.state_db(self.home())
        sid = hf.add_session(con, started_at=hf.T0 + 10)
        hf.add_message(con, sid, "user", "Save to memory: " + FACT, hf.T0 + 11)
        hf.add_message(con, sid, "tool", json.dumps({"success": True, "staged": True, "message": "Staged for approval. Not yet saved."}),
                       hf.T0 + 12, tool_name="memory")
        sid2 = hf.add_session(con, started_at=hf.T0 + 100)
        hf.add_message(con, sid2, "user", "Draft this month's reconciliation checklist for Harbor Bakery.", hf.T0 + 101)
        hf.add_message(con, sid2, "assistant", "1. Export the bank feed from QuickBooks Online. 2. Match each deposit.", hf.T0 + 102)
        con.close()
        if staged:
            hf.stage_pending(self.home(), content=FACT)

    def fix(self):
        hf = self.hf
        for p in (self.home() / "pending" / "memory").glob("*.json"):
            p.unlink()
        hf.write_memory(self.home(), self.practice.seed_notes("academy-practice")["notes"] + [FACT], ["Ada prefers answers in short lists."])
        con = hf.state_db(self.home())
        sid = hf.add_session(con, started_at=hf.now_epoch() + 60)
        hf.add_message(con, sid, "user", "Draft the reconciliation checklist for Harbor Bakery.", hf.now_epoch() + 61)
        hf.add_message(con, sid, "assistant", "1. Export the bank feed from QuickBooks Online.", hf.now_epoch() + 62)
        con.close()
        skill = self.home() / "skills" / "weekly-invoice"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: weekly-invoice\ndescription: Build and send the weekly invoice\n---\n1. Export hours.\n", encoding="utf-8")

    def out(self):
        view = self.f.attempt_view(self.aid) if self.aid else None
        extra = {
            "snapshot": self.f.snapshot(),
            "mission": self.f.mission_view(MID),
            "view": view or self.f.start(MID),
            "practice": {"practice": self.practice.listing()},
        }
        if view and view["attempt"]["profile"]:
            try:
                extra["memory"] = self.practice.memory_files(view["attempt"]["profile"])
                extra["folder"] = self.practice.working_folder(view["attempt"]["profile"])
            except ValueError:
                pass
            extra["record"] = self.f.record_preview(self.aid)
        extra["field_record"] = self.fr.preview()
        if self.issued:
            extra["issued"] = self.issued
        text = json.dumps(extra, default=str)
        for raw in {str(self.root.resolve()), str(self.root)}:
            text = text.replace(raw, "~/.hermes")
        return json.loads(text)


def f_fresh(kit):
    return {}


def f_predict(kit):
    kit.start()
    kit.entry("recall", {"answers": ["Words, then the row, then the file.", "The tool schemas."]})
    kit.entry("claim", {"text": kit.mission["claim"]["text"], "author": "course"})
    kit.entry("standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in kit.mission["standard"]]})


def f_setup(kit):
    kit.start()
    kit.frozen()


def f_lab(kit):
    kit.start()
    kit.frozen()
    kit.set_up()
    con = kit.hf.state_db(kit.home())
    kit.hf.add_session(con, started_at=kit.hf.T0 + 1, cwd=str(kit.home()), title="What do you know about how things are set up here")
    con.close()
    kit.entry("try_note", {"guess": "A few pages", "memory_tokens": "180"})
    kit.entry("read", {"step": "idea"})
    kit.entry("read", {"step": "expert"})


def f_checked(kit):
    f_lab(kit)
    kit.worked()
    kit.entry("lab_note", {"fact": FACT, "key_term": "QuickBooks"})
    kit.entry("self_score", {"checks": {c["id"]: {"pass": True} for c in kit.mission["standard"]}})
    kit.f.run_checks(kit.aid, "first")


def f_compare(kit):
    f_checked(kit)
    kit.f.submit_explanation(kit.aid, "Check the save first: expand the memory row and open the file, because Saved can be staged for approval. "
                             "Then check the profile, since each has its own memory. Then a new chat, because an open chat never rereads memory.")
    kit.f.grade_rubric(MID, f"explain@{kit.aid}", 3, "Three real causes, each with a check. For level 4, use what happened in your own run.")


def f_record(kit):
    f_compare(kit)
    kit.entry("gap_note", {"text": "I trusted Saved to memory. Expanded, the row said the save was staged for approval."})
    kit.fix()
    kit.entry("fix_note", {"text": "Approved the waiting save with /memory pending, then checked the file and a new chat."})
    kit.f.run_checks(kit.aid, "after_fix")
    kit.entry("lab_note", {"fact": "Ada prefers answers in short lists", "key_term": "short", "for": "transfer",
                           "one_off": "The printer quote came in at noon today", "one_off_saved": False,
                           "one_off_why": "It matters for one afternoon, so it doesn't earn a line."})
    kit.f.run_checks(kit.aid, "transfer")


def f_done(kit):
    f_record(kit)
    kit.f.add_to_record(kit.aid, confirmed=True)


CASE = ("I asked Hermes to remember which client uses QuickBooks. It said Saved to memory, with a check. A new chat "
        "didn't know it. Opening the memory row showed the save was waiting for approval, because this profile holds every "
        "save until someone approves it. I approved it, opened MEMORY.md to see the line, and started a new chat, which "
        "used the fact without being told. Now I open the file before I trust Saved.")
LIMITS = "It shows one practice mission on my own laptop. Nobody else watched, and my own Hermes graded my explanation."


def f_saved(kit):
    f_record(kit)
    first = kit.f.record_preview(kit.aid)["entry"]["evidence"][-1]["id"]
    kit.f.add_to_record(kit.aid, withhold=[first], confirmed=True)
    kit.issued = kit.fr.issue("Ada Lovelace", LIMITS, CASE, confirmed=True)


RECIPES = (
    ("f_fresh", f_fresh), ("f_predict", f_predict), ("f_setup", f_setup), ("f_lab", f_lab), ("f_checked", f_checked),
    ("f_compare", f_compare), ("f_record", f_record), ("f_done", f_done), ("f_saved", f_saved),
)


# ---------------------------------------------------------------- missions 1, 2, 4, 5 and 6 (0.9 M6, part A) --
#
# One key state per mission, each the real backend after the real steps, with the page data the mission's own
# routes (/foundations/a/<attempt>/<what>) would answer.


class KitA(Kit):
    def __init__(self, state, store, data_dir, mid):
        super().__init__(state, store, data_dir)
        package = state.__name__.rsplit(".", 1)[0]
        self.fa = importlib.import_module(f"{package}.foundations_a")
        self.mid = mid
        self.mission = self.content.get(mid)

    def salt_for(self, wanted):
        lab = self.mission["lab"]
        for n in range(2000):
            salt = f"{n:032x}"
            if self.f.choose_plants(lab["plants"], lab["plants_at"]["beginner"], [], self.f.seed_for(salt, self.mid, 1)) == wanted:
                with self.store.connect() as conn:
                    self.store.meta_set(conn, "f_salt", salt)
                return

    def start(self, plants=()):
        self.salt_for(list(plants))
        self.aid = self.f.start(self.mid)["attempt"]["id"]

    def frozen(self):
        self.entry("recall", {"answers": ["I opened the file and it wasn't there.", "The file itself, then its date."]})
        self.entry("claim", {"text": self.mission["claim"]["text"], "author": "course"})
        self.entry("standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in self.mission["standard"]]})
        self.entry("prediction", {"checks": {c["id"]: {"expect_pass": i != 3, "confidence": 70} for i, c in enumerate(self.mission["standard"])},
                                  "where_wrong": "The last check, finding what was set up to go wrong."})

    def set_up(self):
        self.f.open_lab(self.aid)
        for which in self.content.profiles_needed(self.mission):
            self.make(which)
        self.f.plant_lab(self.aid)

    def out(self):
        view = self.f.attempt_view(self.aid)
        extra = {"snapshot": self.f.snapshot(), "mission": self.f.mission_view(self.mid), "view": view,
                 "practice": {"practice": self.practice.listing()}, "part_a": {}}
        if view["attempt"]["profile"]:
            extra["memory"] = self.practice.memory_files(view["attempt"]["profile"])
            extra["folder"] = self.practice.working_folder(view["attempt"]["profile"])
            extra["record"] = self.f.record_preview(self.aid)
            for what in ("info", "first_trips", "skills", "snapshot"):
                try:
                    extra["part_a"][what] = self.fa.page(self.aid, what)
                except ValueError:
                    pass
        extra["field_record"] = self.fr.preview()
        text = json.dumps(extra, default=str)
        for raw in {str(self.root.resolve()), str(self.root)}:
            text = text.replace(raw, "~/.hermes")
        return json.loads(text)


def _lab_a(kit, plants, try_note):
    kit.start(plants)
    kit.frozen()
    kit.set_up()
    con = kit.hf.state_db(kit.home())
    kit.hf.add_session(con, started_at=kit.hf.T0 + 1, cwd=str(kit.home()), title="Warm-up")
    con.close()
    kit.entry("try_note", try_note)
    kit.entry("read", {"step": "idea"})
    kit.entry("read", {"step": "expert"})


def fa_loop_lab(kit):
    _lab_a(kit, ["rows_short"], {"guess": 2, "rows": 6, "sentence": "I read all four files and counted every date."})


def fa_cost_try(kit):
    kit.start(["extra_connector"])
    kit.frozen()
    kit.set_up()
    con = kit.hf.state_db(kit.home())
    for n, tokens in ((1, 21400), (2, 13900)):
        sid = kit.hf.add_session(con, started_at=kit.hf.T0 + n * 600, title="Hello", api_call_count=1, input_tokens=tokens - 1200,
                                 cache_write_tokens=1200, estimated_cost_usd=0.0021 * n, cost_status="estimated")
        kit.hf.add_message(con, sid, "user", "hello", kit.hf.T0 + n * 600 + 1)
        kit.hf.add_message(con, sid, "assistant", "Hello! How can I help?", kit.hf.T0 + n * 600 + 2)
    con.close()
    kit.entry("try_note", {"total": 21400, "hello": 2})


def fa_new_chats_before_b(kit):
    """Mission 4 after the try, before academy-practice-b is made: Your turn shows the one button."""
    _lab_a(kit, ["soul_wrong_profile"], {"predicted": True, "window": 128})


def fa_new_chats_lab(kit):
    _lab_a(kit, ["soul_wrong_profile"], {"predicted": True, "window": 128})
    for which in kit.content.profiles_after_try(kit.mission):  # academy-practice-b comes after the try
        kit.make(which)
    kit.f.plant_after_try(kit.aid)


def fa_skills_try(kit):
    kit.start(["greedy_neighbor"])
    kit.frozen()
    kit.set_up()
    skill = kit.home() / "skills" / "volunteer-shift-roster"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: volunteer-shift-roster\ndescription: Use when compiling volunteer sign-up sheets into a shift roster.\n---\n"
                                    "## When to Use\nWeekly sign-up lists.\n## Procedure\n1. Group by shift.\n## Pitfalls\nLeave out anyone marked maybe; they rarely show.\n"
                                    "## Verification\nEvery name appears once.\n", encoding="utf-8")
    (kit.home() / "skills" / ".usage.json").write_text(json.dumps({"volunteer-shift-roster": {"created_by": "agent", "created_at": "2026-10-22T10:00:00Z"}}),
                                                      encoding="utf-8")
    kit.entry("try_note", {"description": "Use when compiling volunteer sign-up sheets into a shift roster.", "loaded": False})


def fa_profiles_lab(kit):
    _lab_a(kit, ["cloned_memory"], {"answer_b1": "It didn't know about any Hollis report.", "answer_b2": "The 14th.", "count_a": 2, "count_b": 1})


RECIPES_A = (("fa_loop_lab", "f.loop", fa_loop_lab), ("fa_cost_try", "f.cost", fa_cost_try), ("fa_new_chats_lab", "f.new-chats", fa_new_chats_lab),
             ("fa_new_chats_before_b", "f.new-chats", fa_new_chats_before_b),
             ("fa_skills_try", "f.skills", fa_skills_try), ("fa_profiles_lab", "f.profiles", fa_profiles_lab))
