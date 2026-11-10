"""Lane A bench for Nudge me: 20 nudges per mission 3 snag (40), each read by a second model for give-aways.

The context is real: the test harness builds mission 3 with each snag planted, a practice chat in Hermes's own
``state.db`` shape (the save, then a fresh chat that uses it), and the first check, which misses. Then the guide's own
``_make_nudge`` runs with ``claude -p`` standing in for Hermes's model (``grade_bench.CliLlm``), so the prompt, the
event list, the give-away filter, the one regenerate and the fallback are all Field Academy's own code.

A second model (``--reader``, default ``codex``) then reads each shown nudge, told which snag was planted, and answers
whether the nudge names the cause or hints at it so strongly that the learner no longer has to look. The bar: zero.

Run from the repository root:  /usr/bin/python3 docs/bench/nudge_bench.py [--per 20] [--model sonnet] [--reader codex]
Writes docs/bench/nudge-bench-results.json.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
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

SNAG_WORDS = {
    "write_approval": "the memory save was staged and is waiting for the learner's approval (memory.write_approval is on), "
                      "so it was never written to MEMORY.md",
    "memory_full": "the memory file was nearly full, so the new fact didn't fit and the save was cut or refused",
}


def contexts():
    """(snag, attempt, mission, visible results, events) for each mission 3 snag, built by the test harness."""
    import test_ai_guide as tg

    out = []
    for snag in ("write_approval", "memory_full"):
        case = tg.GuideCase("setUp")
        case.setUp()
        try:
            aid = case.missed(snag)
            attempt, mission, entries, checks, _ = case.guide._attempt_and_mission(aid)
            results = case.guide._visible_results(mission, case.guide._first_run(checks))
            found = case.guide.events(attempt)
            out.append({"snag": snag, "attempt": attempt, "mission": mission, "results": results, "events": found,
                        "guide": case.guide, "runtime": case.runtime, "case": case})
        except Exception:
            case.tearDown()
            raise
    return out


def read_for_giveaway(reader: str, snag: str, nudge: str) -> dict:
    prompt = (
        "A course plants one hidden problem in a learner's practice setup, then gives a hint before the answer is "
        f"revealed. The planted problem was: {SNAG_WORDS[snag]}.\n\nThe hint shown was:\n\"{nudge}\"\n\n"
        "Does the hint name the problem, or hint at it so strongly that the learner no longer has to look for it "
        "themselves? Pointing at a place or a moment to look is fine; naming what is wrong there is not. "
        "Reply with only JSON: {\"gives_away\": true or false, \"why\": \"one short sentence\"}."
    )
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    if reader == "codex":
        cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only", "-"]
    else:
        cmd = ["claude", "-p", "--model", reader, "--system-prompt", "You reply with JSON only.", "--tools", "",
               "--strict-mcp-config", "--setting-sources", "", "--no-session-persistence"]
    started = time.monotonic()
    text = ""
    for _ in range(2):  # one retry when the reader hangs
        try:
            done = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=240, env=env, cwd=tempfile.gettempdir())
            text = done.stdout.strip()
            break
        except subprocess.TimeoutExpired:
            continue
    verdict = None
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and "gives_away" in line:
            try:
                verdict = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if verdict is None:
        start, end = text.rfind("{"), text.rfind("}")
        try:
            verdict = json.loads(text[start:end + 1])
        except (json.JSONDecodeError, ValueError):
            verdict = {"gives_away": None, "why": "unreadable reply: " + text[-200:]}
    return {**verdict, "reader": reader, "seconds": round(time.monotonic() - started, 1)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per", type=int, default=20)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--reader", default="codex")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--reread", action="store_true", help="read the saved nudges again without making new ones")
    args = parser.parse_args()
    from grade_bench import CliLlm

    rows = []
    saved = HERE / "nudge-bench-nudges.json"
    built = [] if args.reread else contexts()
    if args.reread:
        rows = json.loads(saved.read_text(encoding="utf-8"))
    try:
        for ctx in built:
            guide, runtime = ctx["guide"], ctx["runtime"]

            # The model handle lives in a process-wide holder, so nudges run in order; the give-away reads run in
            # parallel afterwards.
            for n in range(args.per):
                llm = CliLlm("claude", args.model)
                runtime.set_llm(llm)
                started = time.monotonic()
                shown = guide._make_nudge(ctx["attempt"], ctx["mission"], ctx["results"], ctx["events"])
                rows.append({"snag": ctx["snag"], "n": n + 1, "shown": shown.get("text", ""), "source": shown.get("source"),
                             "state": shown.get("state"), "event_id": shown.get("event_id", ""),
                             "seconds": round(time.monotonic() - started, 1), "model_calls": llm.log})
                print(f"{ctx['snag']:15} {n + 1:2}  {shown.get('source')}: {shown.get('text', '')[:110]}", flush=True)
    finally:
        for ctx in built:
            ctx["case"].tearDown()
    if not args.reread:
        saved.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        verdicts = list(pool.map(lambda r: read_for_giveaway(args.reader, r["snag"], r["shown"]), rows))
    for row, verdict in zip(rows, verdicts):
        row["giveaway_read"] = verdict
    found = [r for r in rows if r["giveaway_read"].get("gives_away") is True]
    unread = [r for r in rows if r["giveaway_read"].get("gives_away") is None]
    by_source = {s: sum(1 for r in rows if r["source"] == s) for s in ("model", "course")}
    summary = {"when": time.strftime("%Y-%m-%d %H:%M %Z"), "nudges": len(rows), "per_snag": args.per,
               "writer": sorted({c["model"] for r in rows for c in r["model_calls"]}), "reader": args.reader,
               "giveaways_found": len(found), "unreadable_reads": len(unread), "shown_from": by_source,
               "bar": "40 nudges, 0 give-aways", "met": len(found) == 0 and not unread and len(rows) >= 40,
               "median_seconds_per_nudge": sorted(r["seconds"] for r in rows)[len(rows) // 2] if rows else None}
    (HERE / "nudge-bench-results.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    print(json.dumps(summary, indent=1))
    for r in found:
        print("GIVEAWAY:", r["snag"], r["shown"], "|", r["giveaway_read"].get("why"))


if __name__ == "__main__":
    main()
