#!/usr/bin/env python3
"""Render the 0.9 brief's shot list (Loop 2 desk) with headless Chrome, and run the DOM checks behind each shot.

    /usr/bin/python3 harness/shoot_desk.py <outdir>               # every shot, every size
    /usr/bin/python3 harness/shoot_desk.py <outdir> fa-11 fa-07   # only ids starting with these
    /usr/bin/python3 harness/shoot_desk.py <outdir> --checks-only
    /usr/bin/python3 harness/shoot_desk.py <outdir> fa-11 --size=1440x900-dark

Same recipe as harness/shoot.py: serves the repo on a free local port, one Chrome at a time, muted
(--mute-audio --autoplay-policy=user-gesture-required). The d_* states come from harness/desk_states.js: the real
backend's answers plus one real-model run (desk_real.json). Writes <id>--<size>.png and checks.json. Runs no Hermes
command and touches nothing under ~/.hermes.
"""

from __future__ import annotations

import functools
import http.server
import json
import re
import shutil
import subprocess
import tempfile
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FLAGS = ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--force-prefers-reduced-motion",
         "--disable-extensions", "--disable-background-networking", "--force-device-scale-factor=1",
         "--mute-audio", "--autoplay-policy=user-gesture-required", "--virtual-time-budget=14000"]

F = [("1440x900-light", 1440, 900, "theme=light"), ("1440x900-dark", 1440, 900, "theme=dark"),
     ("1280x800-light", 1280, 800, "theme=light"), ("1280x800-dark", 1280, 800, "theme=dark"),
     ("1050x800-dark", 1050, 800, "theme=dark"), ("790x800-light", 790, 800, "theme=light"),
     ("1440x900-dark-red", 1440, 900, "theme=dark&accent=red"), ("1440x900-dark-green", 1440, 900, "theme=dark&accent=green")]
C = [("1440x900-dark", 1440, 900, "theme=dark"), ("1440x900-light", 1440, 900, "theme=light"),
     ("1280x800-light", 1280, 800, "theme=light"), ("790x800-dark", 790, 800, "theme=dark")]
ONE = [("1440x900-dark", 1440, 900, "theme=dark")]
FF = "Start the practice"


def q(state, *clicks, scroll=""):
    parts = [f"state={state}"] + [f"click={quote(c)}" for c in clicks]
    if scroll:
        parts.append(f"scroll={quote(scroll)}")
    return "&".join(parts)


# id -> (query, sizes, checks). checks name the DOM statements harness.js tests when deskcheck=<names> is set.
SHOTS = {
    "fa-01-home-cold": (q("d_home"), F, "ff_card,one_primary,no_anyone,no_hscroll,min12"),
    "fa-02-sample-bracket": (q("d_home", "Watch a sample run"), F, "hero_largest,sample_tag,bracket,said_once,no_hscroll,min12"),
    "fa-03-ff-guess": (q("d_ff_guess", FF), C, "guide_visible,no_range,no_hscroll,min12"),
    "fa-04-ff-setup": (q("d_ff_setup", FF, "Practice", "Lock my answers and set up practice"), C, "progress,no_hscroll,min12"),
    "fa-06-ff-score-locked": (q("d_score", FF, "Did it work?"), C, "no_range,no_hscroll,min12"),
    "fa-07-check-miss": (q("d_check", FF), F, "guide_visible,hunt_buttons,holds_back,no_hscroll,min12"),
    "fa-08-nudge": (q("d_check", FF, "Field guide", "Give me a hint"), C, "guide_visible,nudge_text,no_hscroll,min12"),
    "fa-08b-fetching": (q("d_check_fetching", FF, "Field guide", "Give me a hint"), ONE, "guide_visible,no_hscroll,min12"),
    "fa-09-explain-miss": (q("d_compare", FF, "Compare", "Field guide", "Why did this miss?"), C, "explain_text,guide_visible,no_hscroll,min12"),
    "fa-10-grade-inline": (q("d_grade", FF, "Score my answer: explain", "Score my answer", scroll="Explain it"), C, "grade,no_hscroll,min12"),
    "fa-10b-grade-waiting": (q("d_grade_wait", FF, "Score my answer: explain", "Score my answer", scroll="Explain it"), ONE, "no_hscroll,min12"),
    "fa-11-compare-hero": (q("d_compare", FF, "Compare"), F, "hero_largest,bracket,said_once,guide_visible,no_hscroll,min12"),
    "fa-13-fix-with-me": (q("d_fix", FF, "Field guide"), C, "guide_visible,diwm,no_hscroll,min12"),
    "fa-12-compare-marker": (q("d_compare", FF, "Compare", "3:53 AM: Held for your approval", scroll="Replay your run"), C, "bracket,no_hscroll,min12"),
    "fa-14-fix-passed": (q("d_fix_passed", FF, "Fix it"), C, "no_hscroll,min12"),
    "fa-16-record-cover": (q("d_record", "Open Foundations", "Open my Field Record"), F, "no_hscroll,min12"),
    "fa-15-ask": (q("d_compare", FF, "Compare", "Field guide", "Why did the chat look like the save worked?"), C, "guide_visible,no_hscroll,min12"),
    "fa-18-ai-no-model": (q("d_ai_no_model", FF), C, "no_hscroll,min12"),
    "fa-19-ai-timeout": (q("d_ai_timeout", FF), ONE, "no_hscroll,min12"),
    "fa-20-ai-bad-json": (q("d_ai_bad_json", FF), ONE, "no_hscroll,min12"),
    "fa-21-ai-provider-error": (q("d_ai_provider", FF), ONE, "no_hscroll,min12"),
    "fa-22-ai-off": (q("d_ai_off", FF), C, "no_hscroll,min12"),
    "fa-23-testout-guide-off": (q("d_testout_off", FF), ONE, "no_hscroll,min12"),
    "fa-24-replay-empty": (q("d_replay_empty", FF, "Compare"), C, "no_hscroll,min12"),
    "fa-25-replay-schema": (q("d_replay_schema", FF, "Compare"), ONE, "no_hscroll,min12"),
    # Loop 3, from the live gate: a failed run says so with Retry; the home card resumes; a held save is a sentence.
    "fa-26-compare-replay-failed": (q("d_compare_fail", FF, "Compare"), C, "no_hscroll,min12"),
    "fa-26b-compare-after-retry": (q("d_compare_fail", FF, "Compare", "Retry"), ONE, "bracket,no_hscroll,min12"),
    "fa-27-home-resume": (q("d_home_resume"), F, "one_primary,no_hscroll,min12"),
    "fa-28-fix-held-sentence": (q("d_fix_raw", FF), C, "no_hscroll,min12"),
}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run_chrome(args, out_png=None, timeout=90):
    # Each Chrome gets its own scratch profile, deleted after, so headless runs leave no temp profiles (Loop 3).
    profile = tempfile.mkdtemp(prefix="fa-shoot-chrome-")
    try:
        return _run_chrome(args, out_png, timeout, profile)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def _run_chrome(args, out_png, timeout, profile):
    proc = subprocess.Popen([CHROME, *FLAGS, f"--user-data-dir={profile}", *args], stdout=subprocess.PIPE if out_png is None else subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, text=True)
    if out_png is None:
        try:
            out, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            return ""
        return out
    deadline, last = time.time() + timeout, -1
    while time.time() < deadline and proc.poll() is None:
        time.sleep(1)
        size = out_png.stat().st_size if out_png.exists() else -1
        if size > 0 and size == last:
            break
        last = size
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    return ""


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out = Path(argv[0]).expanduser().resolve()
    rest = argv[1:]
    checks_only = "--checks-only" in rest
    only = [a for a in rest if not a.startswith("--")]
    size_only = [a.split("=", 1)[1] for a in rest if a.startswith("--size=")]
    out.mkdir(parents=True, exist_ok=True)
    if not (ROOT / "harness" / "fixtures.json").exists():
        subprocess.run([sys.executable, str(ROOT / "harness" / "make_fixtures.py")], check=True)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    results = {}
    try:
        for sid, (query, sizes, checks) in SHOTS.items():
            if only and not any(sid.startswith(o) for o in only):
                continue
            for label, w, h, extra in sizes:
                if size_only and label not in size_only:
                    continue
                url = f"http://127.0.0.1:{port}/harness/index.html?{query}&{extra}"
                name = f"{sid}--{label}"
                if not checks_only:
                    png = out / f"{name}.png"
                    png.unlink(missing_ok=True)
                    run_chrome([f"--window-size={w},{h}", f"--screenshot={png}", url], out_png=png)
                    # A page caught before its scripts loaded is a near-blank PNG: try once more.
                    if not png.exists() or png.stat().st_size < 30_000:
                        png.unlink(missing_ok=True)
                        run_chrome([f"--window-size={w},{h}", f"--screenshot={png}", url], out_png=png)
                    print(f"{name}: {'ok' if png.exists() else 'MISSING'}", flush=True)
                dom = run_chrome([f"--window-size={w},{h}", "--dump-dom", f"{url}&deskcheck={checks}"])
                found = re.search(r'<pre id="harness-deskcheck"[^>]*>(.*?)</pre>', dom, re.S)
                results[name] = json.loads(found.group(1).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")) if found else {"error": "no check output"}
                bad = [k for k, v in results[name].items() if isinstance(v, dict) and v.get("ok") is False]
                print(f"  checks {name}: {'pass' if not bad and 'error' not in results[name] else 'FAIL ' + ', '.join(bad or ['no output'])}", flush=True)
    finally:
        server.shutdown()
    # A partial render updates its own shots' entries and keeps the rest.
    previous = json.loads((out / "checks.json").read_text(encoding="utf-8")) if (out / "checks.json").exists() and only else {}
    (out / "checks.json").write_text(json.dumps({**previous, **results}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    failed = {k: [c for c, v in r.items() if isinstance(v, dict) and v.get("ok") is False] for k, r in results.items()}
    failed = {k: v for k, v in failed.items() if v or "error" in results[k]}
    print(f"{len(results) - len(failed)} of {len(results)} shots pass every DOM check")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
