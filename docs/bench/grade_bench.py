"""Lane A bench for Score my answer: Field Academy's own prompt builder, schema and checks, with a real model behind
the call instead of Hermes.

What is real here: ``grading.grading_text`` (``rubric_prompt`` minus its tool paragraph), ``grading.INSTRUCTIONS``,
``grading.SCHEMA``, ``ai.call`` (scrub, one repair try, schema check) and ``grading.exact_quote``. What stands in for
Hermes: ``CliLlm`` sends the same instructions and input to ``claude -p`` (or ``codex exec``) with no tools, no
settings, no MCP servers and no saved session, and hands the reply back in the shape ``ctx.llm`` uses. So this
measures the prompt and the checks on a real model; it does not prove the call works inside Hermes (that is S1, run by
the QA lane).

Run from the repository root:  /usr/bin/python3 docs/bench/grade_bench.py [--cli claude|codex] [--model sonnet]
Writes docs/bench/grade-bench-results.json (or --out) (every prompt, reply, model and latency) and prints the table.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def load_package():
    os.environ.setdefault("FIELD_ACADEMY_DATA_DIR", tempfile.mkdtemp(prefix="fa-bench-"))
    spec = importlib.util.spec_from_file_location("fa_bench", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["fa_bench"] = pkg
    spec.loader.exec_module(pkg)
    return {name: importlib.import_module(f"fa_bench.{name}") for name in ("ai", "grading", "foundations_content", "runtime")}


class CliLlm:
    """``complete_structured`` over a command-line model. Keeps every exchange in ``log``."""

    def __init__(self, cli: str, model: str):
        self.cli, self.model, self.log = cli, model, []

    def _prompt(self, kw) -> str:
        parts = [kw["instructions"]]
        parts.extend(block["text"] for block in kw["input"])
        parts.append("The JSON schema your reply must fit:\n" + json.dumps(kw["json_schema"]))
        return "\n\n".join(parts)

    def complete_structured(self, **kw):
        prompt = self._prompt(kw)
        started = time.monotonic()
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        if self.cli == "claude":
            cmd = ["claude", "-p", "--output-format", "json", "--model", self.model, "--system-prompt",
                   "You are a careful grader. You reply with one JSON object and nothing else.", "--tools", "",
                   "--strict-mcp-config", "--setting-sources", "", "--no-session-persistence"]
        else:
            cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only", "-"]
        done = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=180, env=env, cwd=tempfile.gettempdir())
        seconds = time.monotonic() - started
        model, text, usage = self.model, done.stdout, SimpleNamespace(input_tokens=0, output_tokens=0, total_tokens=0)
        if self.cli == "claude":
            try:
                data = json.loads(done.stdout)
                text = data.get("result", "")
                model = next(iter(data.get("modelUsage") or {}), self.model)
                u = data.get("usage") or {}
                inp = int(u.get("input_tokens", 0)) + int(u.get("cache_creation_input_tokens", 0)) + int(u.get("cache_read_input_tokens", 0))
                usage = SimpleNamespace(input_tokens=inp, output_tokens=int(u.get("output_tokens", 0)),
                                        total_tokens=inp + int(u.get("output_tokens", 0)))
            except (json.JSONDecodeError, StopIteration):
                pass
        if done.returncode != 0 and not text:
            raise RuntimeError(f"{self.cli} exited {done.returncode}: {done.stderr[:300]}")
        self.log.append({"prompt": prompt, "reply": text, "model": model, "seconds": round(seconds, 2)})
        return SimpleNamespace(text=text, parsed=None, model=model, provider=self.cli, usage=usage)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", default="claude", choices=("claude", "codex"))
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--out", default="grade-bench-results.json")
    parser.add_argument("--answers", default="grade-answers.json", help="the answer set (in docs/bench/)")
    args = parser.parse_args()
    mods = load_package()
    ai, grading, content = mods["ai"], mods["grading"], mods["foundations_content"]
    answers = json.loads((HERE / args.answers).read_text(encoding="utf-8"))["answers"]
    rows = []
    for item in answers:
        mission = content.get(item["mission"])
        llm = CliLlm(args.cli, args.model)
        text = " ".join(item["answer"].split())
        started = time.monotonic()
        try:
            out = ai.call("field_academy_grader", instructions=grading.INSTRUCTIONS,
                          inputs=[grading.grading_text({"id": 1}, mission, text)], schema=grading.SCHEMA,
                          schema_name="field_academy_grade", purpose="grade", max_tokens=700, llm=llm, timeout=170)
            reply = out["parsed"]
            got, err = reply["level"], ""
            quote = grading.exact_quote(reply.get("quote", ""), text)
        except Exception as exc:  # noqa: BLE001 - a bench row records the failure
            reply, got, err, quote = None, None, f"{type(exc).__name__}: {exc}", ""
        rows.append({"id": item["id"], "mission": item["mission"], "authored": item["level"], "graded": got,
                     "exact": got == item["level"], "within_one": got is not None and abs(got - item["level"]) <= 1,
                     "quote_kept": bool(quote), "quote": quote, "reply": reply, "error": err,
                     "seconds": round(time.monotonic() - started, 2), "calls": llm.log})
        print(f"{item['id']:8} authored {item['level']}  graded {got}  quote {'kept' if quote else 'dropped'}  "
              f"{rows[-1]['seconds']:.1f}s {err}", flush=True)
    exact = sum(r["exact"] for r in rows)
    within = sum(r["within_one"] for r in rows)
    models = sorted({c["model"] for r in rows for c in r["calls"]})
    summary = {"when": time.strftime("%Y-%m-%d %H:%M %Z"), "cli": args.cli, "models": models, "answers": args.answers, "exact": exact,
               "within_one": within, "of": len(rows), "bar": "8 of 10 exact, 10 of 10 within one",
               "met": exact >= 8 and within == len(rows),
               "median_seconds": sorted(r["seconds"] for r in rows)[len(rows) // 2]}
    (HERE / args.out).write_text(json.dumps({"summary": summary, "rows": rows}, indent=1, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
