"""The capability missions end to end, from the shipped content: setup, each planted problem, the checks, a fix, the
transfer and the record entry, through the real engine. A stand-in lays down what Hermes would; nothing runs Hermes."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hermes_fixture as hf  # noqa: E402
from test_foundations_missions_b import MissionCase  # noqa: E402
from test_foundations_checks_c import call  # noqa: E402


class Delegation(MissionCase):
    MID = "f.delegation"

    def setup_done(self, plants):
        aid = self.lab(plants)
        setup = self.mod("practice").setup_details("academy-practice")
        return aid, setup

    def work(self, setup, rule=True):
        """What a good run leaves: one batch, one helper per client, three right summaries."""
        con = hf.state_db(self.h)
        parent = hf.add_session(con, started_at=hf.now_epoch() + 10)
        tasks = [{"goal": f"summarise {self.folder()}/clients/{slug}/notes.txt"} for slug in setup["clients"]]
        hf.add_message(con, parent, "assistant", "", hf.now_epoch() + 11, tool_calls=call("delegate_task", tasks=tasks))
        hf.add_message(con, parent, "tool", "{\"results\": [\"ok\", \"ok\", \"ok\"]}", hf.now_epoch() + 12, tool_name="delegate_task")
        for n, slug in enumerate(setup["clients"]):
            child = hf.add_session(con, started_at=hf.now_epoch() + 20 + n, source="subagent", parent_session_id=parent)
            hf.add_message(con, child, "assistant", "", hf.now_epoch() + 21 + n, tool_calls=call("read_file", path=f"{self.folder()}/clients/{slug}/notes.txt"))
        con.close()
        for slug, client in setup["clients"].items():
            (self.folder() / "clients" / slug / "summary.md").write_text(
                f"# {client['name']}\nBudget: {client['budget']}\n" + (f"\n{setup['rule_line']}\n" if rule else ""))

    def test_setup_writes_three_clients_and_the_house_rule_in_memory(self):
        aid, setup = self.setup_done(["one_helper"])
        self.assertEqual(len(setup["clients"]), 3)
        for slug, client in setup["clients"].items():
            self.assertIn(client["budget"], (self.folder() / "clients" / slug / "notes.txt").read_text())
        memory = (self.h / "memories" / "MEMORY.md").read_text()
        self.assertIn(setup["rule_line"], memory)
        view = self.f.mission_view(self.MID)
        for hidden in ("one_helper", "helper_model_typo", "plant_fixed"):
            self.assertNotIn(hidden, json.dumps(view))

    def test_one_helper_is_planted_found_and_fixed(self):
        aid, setup = self.setup_done(["one_helper"])
        self.assertIn("max_concurrent_children: 1", (self.h / "config.yaml").read_text())
        self.work(setup)
        self.note(aid, split="One helper per client folder.", passed_on="Each folder's full path and the house rule's closing line.")
        out = self.first(aid)
        self.assertFalse(out["passed"])
        text = (self.h / "config.yaml").read_text().replace("max_concurrent_children: 1", "max_concurrent_children: 3")
        (self.h / "config.yaml").write_text(text)
        self.f.save_entry(aid, "gap_note", {"text": "The cap on helpers was one, so the batch of three was refused."})
        after = self.f.run_checks(aid, "after_fix")["outcome"]
        self.assertTrue(after["passed"], after)
        self.assertEqual(self.f.attempt_view(aid)["compare"]["plants"][0]["kind"], "one_helper")

    def test_the_helper_model_typo_is_one_letter_off_the_main_model(self):
        self.setup_done(["helper_model_typo"])
        planted = self.mod("plants_c").delegation_settings(self.h)["model"]
        main = "anthropic/claude-sonnet-4.6"
        self.assertNotEqual(planted, main)
        self.assertEqual(len(planted), len(main))
        self.assertEqual(sum(1 for a, b in zip(planted, main) if a != b), 1)

    def test_a_missing_house_rule_fails_the_summaries_check(self):
        aid, setup = self.setup_done(["one_helper"])
        self.work(setup, rule=False)
        out = self.first(aid)
        checks = {c["id"]: c for c in out["checks"]}
        self.assertFalse(checks["summaries_right"]["passed"])


class Toolsets(MissionCase):
    MID = "f.toolsets"

    def test_setup_and_the_wide_connector(self):
        aid = self.lab(["wide_connector"])
        setup = self.mod("practice").setup_details("academy-practice")
        self.assertEqual(len(list((self.folder() / "meetings").glob("*.txt"))), 3)
        wide = self.mod("plants_c").wide_servers(self.h)
        self.assertEqual([s["name"] for s in wide], ["notes"])
        # The learner trims the toolsets, tests, does the job, and narrows the connector.
        text = (self.h / "config.yaml").read_text() + "platform_toolsets:\n  cli: [file, memory]\n"
        text = text.replace(str(self.h.resolve()) + '"', str(self.folder().resolve()) + '"')
        (self.h / "config.yaml").write_text(text)
        con = hf.state_db(self.h)
        sid = hf.add_session(con, started_at=hf.now_epoch() + 50)
        hf.add_message(con, sid, "user", "Run the command date in the terminal.", hf.now_epoch() + 51)
        hf.add_message(con, sid, "assistant", "I have no terminal tool here.", hf.now_epoch() + 52)
        hf.add_message(con, sid, "tool", "{\"ok\": true}", hf.now_epoch() + 53, tool_name="write_file")
        con.close()
        (self.folder() / "brief.md").write_text("\n".join(n["title"] + ": noted." for n in setup["notes"].values()) + "\n")
        self.note(aid, actions="Read three notes, write one brief.", switched_off="Terminal, code, browser and web: the job never uses them.")
        out = self.first(aid)
        self.assertEqual(self.mod("plants_c").wide_servers(self.h), [])
        self.assertTrue(out["passed"], [(c["id"], c.get("detail")) for c in out["checks"] if not c["passed"]])


class TeachProfile(MissionCase):
    MID = "f.teach-profile"

    def test_setup_and_a_full_pass(self):
        aid = self.lab(["approvals_off"])
        person = self.mod("practice").setup_details("academy-practice")["person"]
        self.assertIn(person["never"], (self.folder() / "brief.txt").read_text())
        (self.h / "SOUL.md").write_text(f"You work for {person['first']}, who runs {person['work']}.\n{person['never']}.\n")
        hf.write_memory(self.h, memory=[person["fact"] + "."])
        text = (self.h / "config.yaml").read_text() + "platform_toolsets:\n  cli: [file, memory]\n"
        import re
        (self.h / "config.yaml").write_text(re.sub(r"mode: [\"']?off[\"']?", "mode: manual", text))
        con = hf.state_db(self.h)
        sid = hf.add_session(con, started_at=hf.now_epoch() + 50)
        hf.add_message(con, sid, "user", "Who do you work for, and what should you never do?", hf.now_epoch() + 51)
        hf.add_message(con, sid, "assistant", f"I work for {person['first']}.", hf.now_epoch() + 52)
        con.close()
        self.note(aid, from_brief="Name and rule to SOUL.md, the fact to memory, no programs in the Tools tab.")
        out = self.first(aid)
        self.assertTrue(out["passed"], [(c["id"], c.get("detail")) for c in out["checks"] if not c["passed"]])


class TeachWalkthrough(MissionCase):
    MID = "f.teach-walkthrough"

    def test_setup_draft_plant_and_a_pass(self):
        aid = self.lab(["stale_skill_name"])
        pt = self.mod("plants_t")
        self.assertTrue((self.h / "skills" / pt.SKILL / "SKILL.md").exists())
        self.assertIn("run the weekly-orders skill", (self.folder() / "draft-walkthrough.md").read_text())
        (self.folder() / "walkthrough.md").write_text(
            f"1. In academy-practice, start a new chat.\n2. Type: run the {pt.SKILL} skill.\n"
            f"3. Open {pt.OUTPUT} in the practice folder and check there's one line per order.\n")
        con = hf.state_db(self.h)
        sid = hf.add_session(con, started_at=hf.now_epoch() + 50)
        hf.add_message(con, sid, "user", f"run the {pt.SKILL} skill", hf.now_epoch() + 51)
        con.close()
        out_file = self.folder() / pt.OUTPUT
        out_file.write_text("order 1\norder 2\norder 3\n")
        import os
        os.utime(out_file, (hf.now_epoch() + 60, hf.now_epoch() + 60))
        self.note(aid, changed="Copied the real skill name from the Skills tab.")
        out = self.first(aid)
        self.assertTrue(out["passed"], [(c["id"], c.get("detail")) for c in out["checks"] if not c["passed"]])


class TeachReview(MissionCase):
    MID = "f.teach-review"

    def test_setup_writes_a_record_that_checks_until_the_plant(self):
        aid = self.lab(["edited_excerpt"])
        pt = self.mod("plants_t")
        fr = self.mod("field_record")
        folder = self.folder() / pt.RECORD_DIR
        self.assertTrue((folder / "MANIFEST.sha256").exists())
        result = fr.check_folder(folder)
        self.assertTrue(result["number_ok"])
        self.assertEqual([r["file"] for r in result["files"] if not r["ok"]], [pt.EDIT_FILE])
        setup = self.mod("practice").setup_details("academy-practice")
        first = setup["holder"].split(" ")[0]
        con = hf.state_db(self.h)
        sid = hf.add_session(con, started_at=hf.now_epoch() + 50)
        hf.add_message(con, sid, "assistant", "", hf.now_epoch() + 51, tool_calls=call("terminal", command="cd their-record && shasum -a 256 -c MANIFEST.sha256"))
        con.close()
        (self.folder() / "review.md").write_text(
            f"Record {setup['number']}.\n{first}, 01-tool-result.txt failed its fingerprint check. Your memory mission passed after a fix: "
            "1 of 4 first, 4 of 4 after.\nCan you run it again while I watch?\n")
        self.note(aid, vouch="The folder except one excerpt; the pass after a fix.")
        out = self.first(aid)
        self.assertTrue(out["passed"], [(c["id"], c.get("detail")) for c in out["checks"] if not c["passed"]])

    def test_the_overclaim_plant_keeps_every_fingerprint(self):
        self.lab(["overclaim"])
        pt = self.mod("plants_t")
        fr = self.mod("field_record")
        result = fr.check_folder(self.folder() / pt.RECORD_DIR)
        self.assertTrue(result["ok"], result)
        self.assertIn(pt.OVERCLAIM, (self.folder() / pt.RECORD_DIR / "record.md").read_text())


if __name__ == "__main__":
    unittest.main()
