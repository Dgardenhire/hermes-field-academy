"""Ten Explain it answers for the grader bench, written by someone other than the AI lane: codex (``codex exec``),
told only the question, the job, and a plain description of a weak-to-strong answer in its own terms. It never sees
the rubric's level wording. The level it aimed for is the authored level. Writes grade-answers-codex.json.

Run from the repository root:  /usr/bin/python3 docs/bench/write_fair_answers.py
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
JOBS = {
    "f.memory": "The learner asked Hermes (an AI agent app) to remember a client fact in one chat, then checked whether a "
                "brand-new chat knew it. Hermes keeps memory in a MEMORY.md file in the profile; saves show as a row in "
                "the chat; some setups hold saves for approval; memory has a size limit.",
    "f.loop": "The learner asked Hermes to build a weekly report from job sheets (spreadsheet files) and write a report "
              "file. Hermes then said the report was done.",
    "f.cost": "The learner looked at what each message to the model carries in Hermes: tool descriptions from connectors "
              "and skills ride along on every trip and cost tokens, used or not.",
}
TIERS = ("1 = vague or a shrug, with no concrete step anyone could actually do. "
         "2 = one real, concrete point, but thin: only one cause or only checks Hermes's own words. "
         "3 = three solid, concrete points, each with how you would actually check it. "
         "4 = all of 3, plus something specific from the writer's own run and a sensible order of checks.")


def main():
    sys.path.insert(0, str(ROOT))
    import importlib.util

    os.environ.setdefault("FIELD_ACADEMY_DATA_DIR", tempfile.mkdtemp(prefix="fa-fair-"))
    spec = importlib.util.spec_from_file_location("fa_fair", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["fa_fair"] = pkg
    spec.loader.exec_module(pkg)
    content = __import__("fa_fair.foundations_content", fromlist=["get"])
    plan = [("f.memory", 1), ("f.memory", 2), ("f.memory", 3), ("f.memory", 4), ("f.loop", 1), ("f.loop", 3), ("f.loop", 4),
            ("f.cost", 2), ("f.cost", 3), ("f.cost", 4)]
    asks = []
    for n, (mid, level) in enumerate(plan, 1):
        q = content.get(mid)["explain"]["question"]
        asks.append({"id": f"c{n:02d}", "mission": mid, "level": level, "job": JOBS[mid], "question": q})
    prompt = ("You are writing practice answers for testing an automatic grader. For each item, write one answer, as a "
              "real learner would type it (60 to 160 words, plain words, no headings), that a fair teacher would put at "
              "the level given. Vary the voice, order and wording between answers; don't make every answer at one level "
              "look alike, and don't use the words 'level' or 'rubric'. Levels: " + TIERS + "\n\nItems:\n" +
              json.dumps(asks, indent=1) + "\n\nReply with only a JSON object: {\"answers\": [{\"id\": ..., \"answer\": ...}]}.")
    done = subprocess.run([os.path.expanduser("~/.local/bin/codex"), "exec", "--skip-git-repo-check", "--sandbox", "read-only", "-"],
                          input=prompt, capture_output=True, text=True, timeout=600, cwd=tempfile.gettempdir())
    text = done.stdout + "\n" + done.stderr
    (Path(tempfile.gettempdir()) / "fa-fair-codex-raw.txt").write_text(text, encoding="utf-8")
    got = None
    decoder = json.JSONDecoder()
    for i in reversed([i for i in range(len(text)) if text.startswith('{"answers"', i) or text.startswith('{\n  "answers"', i)]):
        try:
            got = decoder.raw_decode(text[i:])[0]["answers"]
            if got and isinstance(got[0].get("answer"), str):
                break
        except (ValueError, KeyError, IndexError, AttributeError):
            got = None
    if not got:
        raise SystemExit("codex's reply had no answers JSON; raw text in " + str(Path(tempfile.gettempdir()) / "fa-fair-codex-raw.txt"))
    by_id = {a["id"]: a["answer"] for a in got}
    answers = [{"id": a["id"], "mission": a["mission"], "level": a["level"], "answer": " ".join(by_id[a["id"]].split())}
               for a in asks if a["id"] in by_id]
    doc = {"about": ("Ten Explain it answers written by codex exec on " + time.strftime("%b %d, %Y") + ", told the question, "
                     "the job and a plain weak-to-strong description (docs/bench/write_fair_answers.py TIERS), never the "
                     "rubric's level wording. The authored level is the level codex aimed for. The AI lane did not write "
                     "or edit them."), "writer": "codex exec", "tiers_shown": TIERS, "answers": answers}
    (HERE / "grade-answers-codex.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(len(answers), "answers")


if __name__ == "__main__":
    main()
