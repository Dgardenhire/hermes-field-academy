"""Mission 2's second planted problem (Nov 8): a pack of skills for other work, beside the unused connector.

Before this, mission 2 had one possible planted problem, the unused connector, so the warning about the connector shown
before the first practice chat named what the learner was meant to find (docs/SECURITY-AUDIT.md, second review). Now
either problem can be drawn; the connector is in the settings either way (on when it is the problem, off when it
isn't), so the warning is true for both and names neither. Each problem has its own detector and fix-verifier behind
the hidden planted-problem check, and a test-out still needs that check. Nothing runs Hermes.
"""

from __future__ import annotations

import itertools
import json
import pathlib
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from support import START  # noqa: E402
from test_foundations_part_a import Cost, call, calls  # noqa: E402

MID = "f.cost"
KINDS = ("extra_connector", "unused_skills")
NOTE = {"decision": "The job only read orders.csv and wrote totals.md with the file tools, so I'll switch off what it never used.",
        "before_tokens": 20000, "after_tokens": 13000, "share": 35, "main": "anthropic/claude-sonnet-4.6",
        "auxiliary": "auto, same as main", "subagents": "main model"}
EXPLANATION = ("Every connector adds tool descriptions to the part sent on every trip. The Context Usage panel shows it on the "
               "MCP line; switch off what you never use and keep the rest, then start a new chat. ") * 2


def switch_off_skills(home, names):
    """What the Capabilities Skills tab leaves in config.yaml: the names on the global skills.disabled list."""
    path = pathlib.Path(home) / "config.yaml"
    text = path.read_text(encoding="utf-8")
    block = "skills:\n  disabled:\n" + "".join(f"  - {n}\n" for n in names)
    path.write_text(text.replace("skills:\n", block, 1), encoding="utf-8")


def switch_off_connector(home, name):
    path = pathlib.Path(home) / "config.yaml"
    head, tail = path.read_text(encoding="utf-8").split(f"  {name}:", 1)
    path.write_text(head + f"  {name}:" + tail.replace("enabled: true", "enabled: false", 1), encoding="utf-8")


class SecondProblem(Cost):
    def planted(self, kind):
        ctx = self.planted_profile([kind], mission=MID)
        return ctx, ctx["planted"][kind]

    # ------------------------------------------------------------- the draw --

    def test_both_problems_can_be_drawn_and_each_run_gets_one(self):
        mission = self.content.get(MID)
        self.assertEqual(sorted(mission["lab"]["plants"]), sorted(KINDS))
        drawn = {tuple(self.f.choose_plants(mission["lab"]["plants"], 1, [], f"seed-{n}")) for n in range(40)}
        self.assertEqual(drawn, {(k,) for k in KINDS}, "each run plants exactly one, and both come up")
        for kind in KINDS:
            self.assertEqual(set(self.plants.REGISTRY[kind]), {"plant", "detect", "verify"})

    def test_a_started_attempt_draws_either_one(self):
        mission = self.content.get(MID)
        seen = set()
        for n in range(40):
            seed = self.f.seed_for(f"{n:032x}", MID, 1)
            seen.update(self.f.choose_plants(mission["lab"]["plants"], mission["lab"]["plants_at"]["beginner"], [], seed))
        self.assertEqual(seen, set(KINDS))

    # ---------------------------------------------------------- the planters --

    def test_the_connector_problem_has_the_connector_on_and_no_skills(self):
        ctx, details = self.planted("extra_connector")
        self.assertTrue(self.read_a.connectors(ctx["home"])["connectors"][details["connector"]]["enabled"])
        self.assertEqual(self.hermes_read.skills(ctx["home"])["skills"], [])

    def test_the_skills_problem_has_twelve_skills_on_and_the_same_connector_off(self):
        ctx, details = self.planted("unused_skills")
        names = {s["name"] for s in self.hermes_read.skills(ctx["home"])["skills"]}
        self.assertEqual(len(details["skills"]), 12)
        self.assertEqual(names, set(details["skills"]))
        connector = self.read_a.connectors(ctx["home"])["connectors"][details["connector"]]
        self.assertEqual(connector, {"enabled": False, "package": self.plants_a.FS_SERVER_PACKAGE})
        self.assertEqual(self.read_a.disabled_skills(ctx["home"])["disabled"], set())
        base = self.plants_a.base_for(ctx["planted"], MID)
        self.assertTrue((ctx["home"] / base["job_rel"] / "orders.csv").is_file(), "the job is the same whichever was drawn")

    def test_the_pack_descriptions_fit_the_skills_list_and_steer_clear_of_the_job(self):
        for theme, pack in self.plants_a.SKILL_PACKS:
            self.assertEqual(len(pack), 12, theme)
            for name, description in pack:
                self.assertRegex(f"skills/{name}/SKILL.md", self.practice_write.SKILL_FILE)
                self.assertLessEqual(len(description), 60, name)
                self.assertEqual(self.mod("foundations_checks_a").seen_line(description), description, "shown whole in the list")
                for word in ("order", "total", "amount", "csv", "sum", "count", "spreadsheet", "report"):
                    self.assertNotIn(word, f"{name} {description}".lower(), f"{name} could look relevant to the orders job")
        self.assertEqual(len({n for _, pack in self.plants_a.SKILL_PACKS for n, _ in pack}), 36, "no name repeats")

    def test_the_same_seed_plants_the_same_pack_and_connector(self):
        ctx, first = self.planted("unused_skills")
        self.assertEqual(first, self.practice.planted("academy-practice")["unused_skills"])
        rng = self.plants_a._rng(self.practice.record("academy-practice"), "m2-skills")
        self.assertEqual(rng.choice(self.plants_a.SKILL_PACKS)[0], first["theme"])

    # ------------------------------------------------- each caught by its check --

    def test_the_skills_problem_is_caught_and_fixed_only_by_switching_the_pack_off(self):
        ctx, details = self.planted("unused_skills")
        out = self.run_reader("plant.fixed_a", ctx)
        self.assertFalse(out["passed"])
        self.assertIn("12 skills for work this profile never does are still on", out["detail"])
        switch_off_connector(ctx["home"], "github")  # cutting something else doesn't fix it
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"])
        before = (ctx["home"] / "config.yaml").read_text()
        switch_off_skills(ctx["home"], details["skills"][:11])
        out = self.run_reader("plant.fixed_a", ctx)
        self.assertFalse(out["passed"])
        self.assertIn("1 skill for work this profile never does is still on", out["detail"])
        (ctx["home"] / "config.yaml").write_text(before)
        switch_off_skills(ctx["home"], details["skills"])
        self.assertTrue(self.run_reader("plant.fixed_a", ctx)["passed"])

    def test_deleting_the_skills_also_fixes_it(self):
        import shutil

        ctx, details = self.planted("unused_skills")
        for name in details["skills"]:
            shutil.rmtree(ctx["home"] / "skills" / name)
        self.assertTrue(self.run_reader("plant.fixed_a", ctx)["passed"])

    def test_a_list_kept_for_one_platform_only_does_not_count(self):
        ctx, details = self.planted("unused_skills")
        path = ctx["home"] / "config.yaml"
        block = "skills:\n  platform_disabled:\n    telegram:\n" + "".join(f"    - {n}\n" for n in details["skills"])
        path.write_text(path.read_text().replace("skills:\n", block, 1))
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"], "the desktop chat still lists them")

    def test_a_list_saved_as_one_json_string_counts(self):
        ctx, details = self.planted("unused_skills")
        path = ctx["home"] / "config.yaml"
        path.write_text(path.read_text().replace("skills:\n", "skills:\n  disabled: '" + json.dumps(details["skills"]) + "'\n", 1))
        self.assertTrue(self.run_reader("plant.fixed_a", ctx)["passed"])

    def test_the_connector_problem_is_still_caught_by_its_own_check(self):
        ctx, details = self.planted("extra_connector")
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"])
        switch_off_skills(ctx["home"], ["academy-caption-ideas"])  # the other problem's fix does nothing here
        self.assertFalse(self.run_reader("plant.fixed_a", ctx)["passed"])
        switch_off_connector(ctx["home"], details["connector"])
        self.assertTrue(self.run_reader("plant.fixed_a", ctx)["passed"])

    def test_the_detector_counts_what_is_on_and_what_the_job_opened(self):
        ctx, details = self.planted("unused_skills")
        self.session([("user", "hello", {}), ("assistant", "", {"tool_calls": call("skill_view", name=details["skills"][0])})])
        seen = self.plants.detect("unused_skills", ctx["home"], details)
        self.assertTrue(seen["fired"])
        self.assertEqual({f["label"]: f["value"] for f in seen["facts"]},
                         {"Skills for other work still on": "12 of 12", "Times a chat opened one": "1"})

    def test_a_decision_that_names_the_skills_counts_as_a_cut(self):
        ctx, details = self.planted("unused_skills")
        base = self.plants_a.base_for(ctx["planted"], MID)
        self.session([("user", self.plants_a.card_m2(base), {}),
                      ("assistant", "", {"tool_calls": calls(("read_file", {"path": "orders.csv"}), ("write_file", {"path": "totals.md"}))})])
        out = self.run_reader("cost.decision", ctx, decision="The job read and wrote files and opened no skill, so I'll switch the skills off.")
        self.assertTrue(out["passed"], out)

    def test_the_compare_step_has_words_for_both(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        for rel in ("desktop/src/foundations_a.js", "desktop/plugin.js"):  # the source and the built bundle
            text = (root / rel).read_text(encoding="utf-8")
            for kind in KINDS:
                self.assertRegex(text, rf"\b{kind}: {{ title: ", f"{rel} names {kind} on the Compare step")
        for kind in KINDS:
            self.assertIn(kind, self.f.PLANT_TITLES, "the record titles it")

    # ------------------------------------------------------- what the page sees --

    def test_the_warning_is_true_for_both_and_names_neither(self):
        note = self.content.get(MID)["practice_note"]
        low = note.lower()
        for kind in KINDS:
            self.assertNotIn(kind, note)
            self.assertNotIn(self.fa.PLANT_TITLES[kind].lower(), low)
        for word in ("skill", "unused", "never used", "extra", "switched on", "isn't used", "not used"):
            self.assertNotIn(word, low)
        for name in self.plants_a.CONNECTOR_NAMES + tuple(n for _, pack in self.plants_a.SKILL_PACKS for n, _ in pack):
            self.assertNotIn(name, note)
        self.assertIn("filesystem connector", low)
        for kind in KINDS:  # the warning holds: a filesystem connector is in the settings, reaching one folder inside the profile
            self.tearDown()
            self.setUp()
            ctx, details = self.planted(kind)
            servers = self.read_a.connectors(ctx["home"])["connectors"]
            self.assertEqual(servers[details["connector"]]["package"], self.plants_a.FS_SERVER_PACKAGE, kind)
            config = (ctx["home"] / "config.yaml").read_text()
            self.assertIn(str((ctx["home"] / "practice-folder" / "archive").resolve()), config, kind)

    def test_the_public_mission_and_the_page_never_name_either_problem(self):
        public = json.dumps(self.content.public(self.content.get(MID)))
        pack = [n for _, p in self.plants_a.SKILL_PACKS for n, _ in p]
        for kind in KINDS:
            self.assertNotIn(kind, public)
        for name in pack + list(self.plants_a.CONNECTOR_NAMES):
            self.assertNotIn(name, public)
        for kind in KINDS:
            self.tearDown()
            self.setUp()
            self.planted(kind)
            attempt = self.f.start(MID)["attempt"]["id"]
            with self.f._conn() as conn:
                conn.execute("UPDATE f_attempts SET profile = 'academy-practice' WHERE id = ?", (attempt,))
            info = json.dumps(self.fa.page(attempt, "info"))
            for word in list(KINDS) + pack + list(self.plants_a.CONNECTOR_NAMES):
                self.assertNotIn(word, info, kind)


class SecondProblemTestOut(Cost):
    """A test-out of mission 2 with the skills drawn: every visible check and the explanation can pass, and it still
    doesn't test out until the hidden planted-problem check passes too (the rule from the second review, C1)."""

    def setUp(self):
        super().setUp()
        self.f.CONTENT_DIR = None
        self.content.clear_cache()
        self.mission = self.content.get(MID)
        counter = itertools.count()
        self.store.clock = lambda: START + timedelta(minutes=2) * next(counter)

    def salt_for(self, wanted):
        for n in range(800):
            salt = f"{n:032x}"
            if self.f.choose_plants(self.mission["lab"]["plants"], 1, [], self.f.seed_for(salt, MID, 1)) == wanted:
                with self.store.connect() as conn:
                    self.store.meta_set(conn, "f_salt", salt)
                return
        self.fail("no salt found")

    def lab_test_out(self):
        self.salt_for(["unused_skills"])
        aid = self.f.start(MID, test_out=True)["attempt"]["id"]
        self.f.save_entry(aid, "claim", {"text": self.mission["claim"]["text"], "author": "course"})
        self.f.save_entry(aid, "standard", {"checks": [{"id": c["id"], "text": c["text"]} for c in self.mission["standard"]]})
        self.f.save_entry(aid, "prediction", {"checks": {c["id"]: {"expect_pass": True, "confidence": 90} for c in self.mission["standard"]},
                                              "where_wrong": "Nowhere, I hope: I trim profiles every month."})
        self.f.open_lab(aid)
        for which in self.content.profiles_needed(self.mission):
            self.ready(which)
        self.f.plant_lab(aid)
        self.assertEqual(list(self.practice.planted("academy-practice")), ["unused_skills"])
        return aid

    def job(self, base, started, error=""):
        result = json.dumps({"success": False, "error": error}) if error else "ok"
        self.session([("user", self.plants_a.card_m2(base), {}),
                      ("assistant", "", {"tool_calls": calls(("read_file", {"path": "orders.csv"}), ("write_file", {"path": "totals.md"}))}),
                      ("tool", "ok", {"tool_name": "read_file"}), ("tool", result, {"tool_name": "write_file"}), ("assistant", "Done.", {})],
                     started=started)

    def run_first(self, aid, cut_skills, error=""):
        home = self.home()
        details = self.practice.planted("academy-practice")["unused_skills"]
        base = details["base"]
        self.hello(20000, hf.T0 + 100)
        self.job(base, hf.T0 + 200)
        switch_off_connector(home, "github")
        if cut_skills:
            switch_off_skills(home, details["skills"])
        self.hello(13000, hf.T0 + 900)
        self.job(base, hf.now_epoch() - 60, error)
        (home / base["output"]).write_text(f"Orders: {base['orders']}\nTotal: {base['total']}\n")
        self.f.save_entry(aid, "lab_note", NOTE)
        self.f.save_entry(aid, "self_score", {"checks": {c["id"]: {"pass": True} for c in self.mission["standard"]}})
        outcome = self.f.run_checks(aid, "first")["outcome"]
        self.f.submit_explanation(aid, EXPLANATION)
        self.f.grade_rubric(MID, f"explain@{aid}", 3, "Why, how to see it, and a fix that keeps what she uses.")
        return outcome

    def test_the_skills_left_on_never_test_out(self):
        aid = self.lab_test_out()
        outcome = self.run_first(aid, cut_skills=False)
        self.assertTrue(all(c["passed"] for c in outcome["checks"]), outcome["checks"])
        self.assertEqual(outcome["hidden"], {"count": 1, "passed": 0})
        self.assertFalse(outcome["passed"])
        self.assertEqual(self.f.attempt_view(aid)["test_out"], {"on": True, "passed": False})
        with self.assertRaises(ValueError):
            self.f.add_to_record(aid, confirmed=True)

    def test_the_skills_switched_off_test_out(self):
        aid = self.lab_test_out()
        outcome = self.run_first(aid, cut_skills=True)
        self.assertTrue(outcome["passed"], outcome)
        self.assertEqual(outcome["hidden"], {"count": 1, "passed": 1})
        self.assertEqual(self.f.attempt_view(aid)["test_out"], {"on": True, "passed": True})

    def test_withheld_excerpts_keep_nothing_from_the_pack(self):
        """The excerpts mission 2's checks keep are tool errors from the job's chat. One that quotes a skill from the
        pack, withheld, leaves neither its text nor what its check found in the record."""
        aid = self.lab_test_out()
        details = self.practice.planted("academy-practice")["unused_skills"]
        outcome = self.run_first(aid, cut_skills=False, error=f"Skill {details['skills'][0]} has no tool for this file.")
        self.assertFalse(outcome["passed"])
        record = self.mod("field_record")
        with self.f._conn() as conn:
            ids = {r["id"] for r in conn.execute("SELECT id FROM f_evidence WHERE attempt_id = ?", (aid,))}
            self.assertTrue(ids, "the failed job left an excerpt to withhold")
            attempt = self.f._attempt(conn, aid)
            body = self.f._record_body(conn, attempt, self.mission, withhold=ids)
            kept = self.f._record_body(conn, attempt, self.mission)
            row = {"hash": "h" * 64, "prev_hash": "", "created_at": "2026-11-08T00:00:00Z", "mission_id": MID}
        self.assertIn(details["skills"][0], json.dumps(record._entry(1, row, kept, set())["evidence"]), "kept, the excerpt shows it")
        entry = record._entry(1, row, body, ids)
        for item in entry["evidence"]:
            self.assertEqual((item["withheld"], item["excerpt"], item["facts"]), (True, "", []))
        text = json.dumps(entry["evidence"]) + record.record_markdown({"entries": [entry]})
        for name in details["skills"]:
            self.assertNotIn(name, text)


if __name__ == "__main__":
    unittest.main()
