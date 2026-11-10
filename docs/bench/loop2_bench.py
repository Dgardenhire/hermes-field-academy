"""Loop 2 Lane A bench: replay pins and Explain my miss, Field Academy's own prompts, schemas and checks, with a real
model behind the call instead of Hermes (``grade_bench.CliLlm``: ``claude -p`` with no tools, settings, MCP servers or
saved session). Then a second model (``codex exec``) reads every output for accuracy and give-aways.

The run is mission 3 with write_approval planted, on the test practice profile whose run agrees with the check facts
(Hermes's staged line on the memory row, the held save in pending/, MEMORY.md unchanged, a fresh chat that does not
know the fact). What it proves: the prompts and checks on a real model. Not that the call works inside Hermes (S1).

Run from the repository root:
  /usr/bin/python3 docs/bench/loop2_bench.py pins [--runs 10] [--model sonnet]
  /usr/bin/python3 docs/bench/loop2_bench.py explain [--runs 10] [--model sonnet]
  /usr/bin/python3 docs/bench/loop2_bench.py read <results.json>      (codex reads it; writes <results>-read.json)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(HERE))

FACTS = ("The check facts (all true): the memory row in the chat is titled Saved to memory but its result says the save "
         "was staged for approval and not yet saved; a held save sits in the profile's pending/memory folder; MEMORY.md "
         "is unchanged (479 of 2,200 characters, no line holds the fact); the new chat did NOT use the fact (it asked "
         "which software Harbor Bakery uses); the fact the learner wanted saved is 'Harbor Bakery uses QuickBooks Online; "
         "the other five use Xero'.")


def harness():
    import test_ai_guide as tg

    case = tg.GuideCase("setUp")
    case.setUp()
    return case, tg


def pins(args):
    from grade_bench import CliLlm

    case, tg = harness()
    rows = []
    try:
        aid = case.missed("write_approval")
        replay = case.mod("recorder").replay(aid, "compare")
        joined = replay["bracket"]
        events = {e["event_id"]: e for e in replay["events"]}
        for n in range(args.runs):
            llm = CliLlm("claude", args.model)
            case.runtime.set_llm(llm)
            started = time.monotonic()
            try:
                out, err = case.guide.make_pins(aid, "compare"), ""
            except Exception as exc:  # noqa: BLE001 - a bench row records the failure
                out, err = {"state": "error"}, f"{type(exc).__name__}: {exc}"
            on_bracket = [p for p in out.get("pins", []) if p["event_id"] in (joined["from"], joined["to"])]
            rows.append({"run": n + 1, "state": out.get("state"), "error": err, "seconds": round(time.monotonic() - started, 2),
                         "pins": [{**p, "event": {k: events[p["event_id"]].get(k) for k in ("kind", "title", "text")}} for p in out.get("pins", [])],
                         "on_bracket": len(on_bracket), "words": [len(p["why"].split()) for p in out.get("pins", [])],
                         "trimmed": out.get("trimmed"), "dropped": out.get("dropped"), "tries": out.get("tries"),
                         "calls": [{k: v for k, v in c.items() if k != "prompt"} for c in llm.log]})
            print(f"run {n + 1}: {out.get('state')} pins {len(out.get('pins', []))} on bracket {len(on_bracket)} "
                  f"tries {out.get('tries')} {rows[-1]['seconds']}s {err}", flush=True)
    finally:
        case.tearDown()
    summary = {"when": time.strftime("%Y-%m-%d %H:%M %Z"), "model": args.model, "runs": len(rows),
               "runs_with_bracket_pin": sum(1 for r in rows if r["on_bracket"]),
               "whole_call_failures": sum(1 for r in rows if r["state"] != "ready"),
               "length_failures": sum(1 for r in rows if r["state"] == "too_long"),
               "max_words": max((w for r in rows for w in r["words"]), default=0),
               "median_seconds": sorted(r["seconds"] for r in rows)[len(rows) // 2] if rows else None,
               "bracket": joined, "facts": FACTS}
    write(args.out or f"pins-bench-{args.model}.json", {"summary": summary, "rows": rows})


def explain(args):
    from grade_bench import CliLlm

    case, tg = harness()
    rows = []
    try:
        aid = case.missed("write_approval")
        guide = case.guide
        with case.store.connect() as conn:
            attempt = case.f._attempt(conn, aid)
            checks = case.f._checks(conn, aid)
        results = guide._visible_results(case.mission, guide._first_run(checks))
        before = not getattr(args, "after", False)  # --after: the Compare wording, which may name the cause
        places = guide.explain_places(case.mission, guide.events(attempt, reveal=not before), before)
        for n in range(args.runs):
            llm = CliLlm("claude", args.model)
            case.runtime.set_llm(llm)
            started = time.monotonic()
            snag = "" if before else ", ".join(case.f.PLANT_TITLES.get(x, x) for x in __import__("json").loads(attempt["plants_json"] or "[]"))
            items = guide._make_explain(case.mission, results, before, aid, places, snag=snag)
            took = round(time.monotonic() - started, 2)
            for item in items:
                rows.append({"run": n + 1, "check_id": item["check_id"], "source": item.get("source"), "state": item.get("state"),
                             "sentences": item.get("sentences", []), "words": [len(s.split()) for s in item.get("sentences", [])],
                             "seconds_all_checks": took})
            print(f"run {n + 1}: {[(i['check_id'], i.get('source')) for i in items]} {took}s", flush=True)
    finally:
        case.tearDown()
    model_rows = [r for r in rows if r["source"] == "model"]
    summary = {"when": time.strftime("%Y-%m-%d %H:%M %Z"), "model": args.model, "after_compare": not before, "outputs": len(rows),
               "from_model": len(model_rows), "course_words": len(rows) - len(model_rows),
               "max_words_per_sentence": max((w for r in rows for w in r["words"]), default=0),
               "over_20_words": sum(1 for r in rows for w in r["words"] if w > 20),
               "user_md_mentions": sum(1 for r in rows if "user.md" in " ".join(r["sentences"]).lower()),
               "second_sentence_places": sorted({next((m for p in places for m in p["match"] if m.lower() in r["sentences"][1].lower()), "none")
                                                 for r in rows if len(r["sentences"]) == 2}),
               "median_seconds_all_checks": sorted(r["seconds_all_checks"] for r in rows)[len(rows) // 2] if rows else None,
               "places": places, "facts": FACTS}
    write(args.out or f"explain-bench-{args.model}.json", {"summary": summary, "rows": rows})


def read(args):
    """codex reads every output: does it contradict a check fact, and (Explain, before Compare) does it give the snag away?"""
    path = Path(args.results)
    data = json.loads(path.read_text(encoding="utf-8"))
    kind = "pins" if "pins" in path.name else "explain"
    if kind == "pins":
        items = [{"id": f"run{r['run']}-{p['event_id']}", "text": p["why"], "on": p["event"]} for r in data["rows"] for p in r["pins"]]
        task = ("These are replay notes shown AFTER the learner saw the answer, so naming the snag is fine. For each note, "
                "say whether it states anything the check facts contradict.")
    else:
        items = [{"id": f"run{r['run']}-{r['check_id']}", "text": " ".join(r["sentences"])} for r in data["rows"]]
        task = ("These are hints shown BEFORE the learner found the problem. For each, say (a) whether it states anything "
                "the check facts contradict, and (b) whether it gives the answer away by naming or pointing straight at "
                "the cause (approval, staged, pending, held, waiting, a full memory). Pointing at a place to look, like "
                "the memory row or MEMORY.md, is NOT a give-away.")
    prompt = (f"{task}\n\n{FACTS}\n\nItems (JSON):\n{json.dumps(items, ensure_ascii=False, indent=1)}\n\n"
              "Reply with only a JSON object: {\"items\": [{\"id\": ..., \"contradicts\": true|false, \"give_away\": true|false, "
              "\"why\": \"short reason\"}]}.")
    done = subprocess.run([os.path.expanduser("~/.local/bin/codex"), "exec", "--skip-git-repo-check", "--sandbox", "read-only", "-"],
                          input=prompt, capture_output=True, text=True, timeout=600, cwd=tempfile.gettempdir())
    text = done.stdout
    start, end = text.rfind('{"items"'), text.rfind("}")
    try:
        verdicts = json.loads(text[start:end + 1])["items"]
    except (ValueError, KeyError):
        verdicts = []
    out = {"reader": "codex exec (read-only)", "when": time.strftime("%Y-%m-%d %H:%M %Z"), "items": len(items),
           "read": len(verdicts), "contradictions": sum(1 for v in verdicts if v.get("contradicts")),
           "give_aways": sum(1 for v in verdicts if v.get("give_away")) if kind == "explain" else None,
           "verdicts": verdicts, "raw_tail": text[-1500:] if not verdicts else ""}
    write(path.with_name(path.stem + "-read.json").name, out)


def write(name, doc):
    (HERE / name).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(doc.get("summary", {k: v for k, v in doc.items() if k != "verdicts"}), indent=1, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("pins", "explain"):
        p = sub.add_parser(name)
        p.add_argument("--runs", type=int, default=10)
        p.add_argument("--model", default="sonnet")
        p.add_argument("--out", default="")
        p.add_argument("--after", action="store_true", help="explain only: the after-Compare wording")
    r = sub.add_parser("read")
    r.add_argument("results")
    args = parser.parse_args()
    {"pins": pins, "explain": explain, "read": read}[args.cmd](args)


if __name__ == "__main__":
    main()
