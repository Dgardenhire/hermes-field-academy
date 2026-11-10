"""What the AI modules may and may not touch, read from their source.

* No AI module writes ``f_checks`` (or ``f_evidence``) itself. The only row a model can cause is the level that
  ``foundations.grade_rubric`` records; disk-check rows come only from ``run_checks`` and ``foundations_checks*.py``.
* No AI module writes into a practice profile or reads the learner's own profiles: no ``practice_write``, no plant
  writers, no Hermes home paths.
* No AI module decides whether a check passed: none writes a ``passed`` value.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AI_MODULES = ("runtime.py", "ai.py", "grading.py", "guide.py", "cost.py", "routes_ai.py",
              "content/foundations/_guide_text.py")


def sources():
    for name in AI_MODULES:
        path = ROOT / name
        if path.exists():
            yield name, path.read_text(encoding="utf-8")


class AiBoundaries(unittest.TestCase):
    def test_the_core_ai_modules_exist(self):
        for name in ("runtime.py", "ai.py", "grading.py", "routes_ai.py"):
            self.assertTrue((ROOT / name).exists(), name)

    def test_no_ai_module_writes_check_or_evidence_rows(self):
        write = re.compile(r"(?is)\b(?:insert\s+(?:or\s+\w+\s+)?into|update|delete\s+from|replace\s+into)\s+f_(?:checks|evidence)\b")
        for name, text in sources():
            self.assertIsNone(write.search(text), f"{name} writes a check or evidence row")

    def test_grading_reaches_f_checks_only_through_grade_rubric(self):
        text = (ROOT / "grading.py").read_text(encoding="utf-8")
        self.assertIn("foundations.grade_rubric(", text)
        for call in re.findall(r"foundations\.(\w+)\(", text):
            self.assertIn(call, {"grade_rubric", "submit_explanation", "rubric_prompt", "_conn", "_attempt", "_entries",
                                 "_grades", "_text", "_mission", "_is_test_out"}, f"grading.py calls foundations.{call}")
        self.assertNotIn("run_checks", text)

    def test_no_ai_module_writes_a_practice_profile_or_reads_the_learners_own(self):
        banned = ("practice_write", "plants.plant", "plant_lab", "write_memory", "HERMES_HOME", "~/.hermes", ".hermes/",
                  "auth.json", "keychain", "security find-generic-password")
        for name, text in sources():
            for word in banned:
                self.assertNotIn(word, text, f"{name} mentions {word}")

    def test_no_ai_module_sends_approves_or_deletes(self):
        for name, text in sources():
            for word in ("dispatch_tool", "subprocess", "os.remove", "shutil.rmtree", "unlink(", "deleteProfile"):
                self.assertNotIn(word, text, f"{name} uses {word}")

    def test_the_only_file_an_ai_module_writes_is_in_the_plugin_data_folder(self):
        opens = re.compile(r"open\(([^)]*)\)")
        for name, text in sources():
            for args in opens.findall(text):
                if '"a"' in args or '"w"' in args or "'w'" in args or "'a'" in args:
                    self.assertIn("runtime.data_dir()", args + text[text.find(args) - 200:text.find(args)], name)


if __name__ == "__main__":
    unittest.main()
