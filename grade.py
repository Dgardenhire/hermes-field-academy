"""Scripted graders for the labs.

Each grader reads the files in the learner's lab folder and the diagnosis they
wrote, rebuilds the lab's hidden facts from its seed (so the answer sheet never
sits in the folder), and returns what is still missing. Nothing here runs a
program or touches anything outside the folder it is given.

A grader says "met" only when every check is met, and it says what is missing in
plain words. The checks are hidden until a miss, then named one at a time through
the hint ladder in learning.py. Each lab also checks that the repair did not
break something else that worked, so deleting a job or a key never counts as a
fix.

What the checks can and cannot see. They read files. They cannot tell whether a
fix would work on a real machine, and a diagnosis is matched by plain word
groups, which is generous: a diagnosis can pass the groups and still be thin.
The brief, the scenarios and the human review are where thin reasoning is caught.
"""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path

from . import fileaccess, labs

SECRET_RE = re.compile(r"FAKE-KEY-DO-NOT-USE-[A-Za-z0-9-]+")
DIAGNOSIS_MIN_CHARS = 120


# ----------------------------------------------------------------- reading --


def _text(root: Path, rel: str) -> str:
    path = root / rel
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    except (OSError, UnicodeDecodeError):
        return ""


def _yaml(root: Path, rel: str):
    text = _text(root, rel)
    if not text:
        return None, f"{rel} is missing or empty"
    try:
        return labs.parse_yaml(text), ""
    except labs.YamlError as exc:
        return None, f"{rel} no longer reads: {exc}"


def _json(root: Path, rel: str):
    text = _text(root, rel)
    if not text:
        return None, f"{rel} is missing or empty"
    try:
        return json.loads(text), ""
    except ValueError as exc:
        return None, f"{rel} is not valid JSON ({exc})"


def parse_env(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip("\"'")
    return out


def _files_to_scan(root: Path):
    """Every file that must not hold a secret: all of them except .env files and the stand-in provider website."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if path.name == ".env" or rel.parts[0] == "provider-console":
            continue
        yield str(rel), path


def stray_secrets(root: Path) -> list:
    hits = []
    for rel, path in _files_to_scan(root):
        try:
            found = SECRET_RE.findall(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        for value in found:
            hits.append((rel, value))
    return hits


def _miss(id_, what):
    return {"id": id_, "what": what}


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _outcome(lab_id, title_ok, missing, facts=None):
    """The checks stay hidden: a miss says how many things are left and names the first, never the full list of what was tested."""
    passed = not missing
    count = len(missing)
    return {
        "passed": passed,
        "title": title_ok if passed else "Not fixed yet",
        "detail": (
            "Every check on the files and on your write-up is met."
            if passed
            else f"{count} {'thing is' if count == 1 else 'things are'} still missing. Start here: {missing[0]['what']}"
        ),
        "facts": facts or [],
        "missing": missing,
    }


def _diagnosis(text: str, concepts: list) -> list:
    clean = " ".join((text or "").split())
    if len(clean) < DIAGNOSIS_MIN_CHARS:
        return [_miss("diag_short", f"Your diagnosis is {len(clean)} characters. Write at least {DIAGNOSIS_MIN_CHARS}, so it says what happened, how you found it and what you changed.")]
    out = []
    for cid, what, patterns in concepts:
        if not any(re.search(p, clean, re.I) for p in patterns):
            out.append(_miss(cid, what))
    return out


# ------------------------------------------------------------------- leak --


def _grade_leak(spec, root: Path, diagnosis: str):
    missing = []
    leak_rel = spec["leak_file"]
    data, err = _yaml(root, leak_rel)
    root_cfg, root_err = _yaml(root, "config.yaml")
    if err or root_err:
        missing.append(_miss("config_parses", err or root_err))
        return _outcome(spec["lab_id"], "Leak closed", missing)
    for rel, value in stray_secrets(root):
        missing.append(_miss("secret_in_file", f"A leaked key is still written out in {rel}. Anything saved to the shared repository can be read by everyone who has it."))
        break
    for item in spec["leaked"]:
        block = labs.dig(data, item["block"]) or {}
        pointer = block.get(item["yaml_key"] + "_env") or block.get(item["yaml_key"])
        referenced = isinstance(pointer, str) and re.search(rf"\$\{{?{item['var']}\}}?|env[:.]{item['var']}|^{item['var']}$", pointer)
        if not referenced:
            missing.append(_miss("not_wired", f"The {item['block']} settings no longer say which environment variable holds the {item['yaml_key'].replace('_', ' ')}. Hermes would start with no key."))
            break
    if labs.dig(data, "provider", "name") != spec["provider"]["name"] and labs.dig(root_cfg, "provider", "name") != spec["provider"]["name"]:
        missing.append(_miss("config_damaged", "The provider settings lost the provider's name. Repair the setting without deleting what else was there."))
    env = parse_env(_text(root, ".env"))
    old_values = {item["value"] for item in spec["leaked"]}
    console, console_err = _json(root, "provider-console/keys.json")
    keys = (console or {}).get("keys", []) if console else []
    if console_err:
        missing.append(_miss("console_broken", console_err))
    for index, item in enumerate(spec["leaked"]):
        current = env.get(item["var"], "")
        if not current or current in old_values or not current.startswith("FAKE-"):
            missing.append(_miss("env_missing_new", f"The .env file has no new value for {item['var']}. It must hold a new key, made up for this lab starting with FAKE-, not the old one."))
            break
    for item in spec["leaked"]:
        old = next((k for k in keys if k.get("id") == item["key_id"]), None)
        if not old or old.get("status") != "revoked":
            missing.append(_miss("old_not_revoked", f"The leaked key {item['key_id']} is still active on the provider console. Changing the file does not stop someone who already copied it."))
            break
    for item in spec["leaked"]:
        current = env.get(item["var"], "")
        fresh = [k for k in keys if k.get("label") == item["label"] and k.get("status") == "active" and k.get("id") != item["key_id"] and k.get("secret")]
        if current and not any(k.get("secret") == current for k in fresh):
            missing.append(_miss("new_key_unmatched", f"The key in .env for {item['var']} is not an active {item['label']} key on the console. Make the new key on the console, then put exactly that key in .env."))
            break
    tracked = [line.strip() for line in _text(root, "tracked-files.txt").splitlines() if line.strip() and not line.startswith("#")]
    ignore = [line.strip() for line in _text(root, ".gitignore").splitlines()]
    if ".env" in tracked or not any(line in (".env", "*.env", "/.env") for line in ignore):
        missing.append(_miss("env_unprotected", "The .env file can still be saved to the shared repository. It must be on the ignore list and off the list of saved files."))
    for needed in ("CALENDAR_READONLY_TOKEN", "TZ", "GATEWAY_PORT"):
        if needed not in env:
            missing.append(_miss("env_damaged", f".env lost {needed}. Add the new keys without removing the settings that were already there."))
            break
    missing += _incident(spec, root)
    missing += _diagnosis(diagnosis, _leak_concepts(spec))
    return _outcome(spec["lab_id"], "Leak closed", missing)


def _incident(spec, root: Path) -> list:
    text = _text(root, "INCIDENT.md")
    if not text.strip():
        return [_miss("incident_missing", "There is no INCIDENT.md in the folder. The owner asked for the leak to be written down.")]
    out = []
    if not all(item["key_id"] in text for item in spec["leaked"]):
        out.append(_miss("incident_key", "INCIDENT.md does not name the key by its id from the provider console. Give the id, never the key itself."))
    date = spec["misuse_at"][:10]
    pretty = _pretty_dates(date)
    if not any(token in text for token in pretty):
        out.append(_miss("incident_when", "INCIDENT.md does not say when the key was first misused. The provider log has the date."))
    owner = spec["client"]["owner"]
    if owner.split()[-1].lower() not in text.lower():
        out.append(_miss("incident_who", "INCIDENT.md does not say who was told. Name the owner."))
    if not re.search(r"revok|rotat|replac|switch", text, re.I):
        out.append(_miss("incident_fix", "INCIDENT.md does not say what you changed on the key."))
    if not re.search(r"gitignore|(?:[.]env)|environment variable|secret scan|scanning|pre-commit|never (?:put|commit|save)", text, re.I):
        out.append(_miss("incident_prevent", "INCIDENT.md does not say how this is prevented next time."))
    return out


def _pretty_dates(iso_date: str) -> list:
    year, month, day = iso_date.split("-")
    names = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
    name = names[int(month) - 1]
    return [iso_date, f"{name} {int(day)}", f"{name[:3]} {int(day)}", f"{int(month)}/{int(day)}", f"{int(day)} {name}"]


def _leak_concepts(spec):
    base = os.path.basename(spec["leak_file"])
    return [
        ("diag_cause", "Your diagnosis does not say how the key got out: it was written into a file that is saved to the shared repository.", [r"repo", r"commit", r"tracked", r"saved (?:to|in)", r"shared backup"]),
        ("diag_where", f"Your diagnosis does not name the file the key was in ({base}).", [re.escape(base), re.escape(spec["leak_file"])]),
        ("diag_evidence", "Your diagnosis does not point to the evidence in the provider log: an address nobody recognised used the key.", [r"203\.0\.113", r"not seen before", r"unfamiliar", r"unknown (?:ip|address)", r"spike", r"strange traffic", r"unrecogni[sz]ed"]),
        ("diag_fix", "Your diagnosis does not say you switched the old key off and made a new one.", [r"revok", r"rotat", r"new key", r"replac"]),
        ("diag_prevent", "Your diagnosis does not say how the next key stays out of the repository.", [r"\.env", r"environment variable", r"gitignore", r"ignore"]),
    ]


# ------------------------------------------------------------------- cost --


def _price(spec, model):
    for item in spec["models"]:
        if item["name"] == model:
            return item["usd_per_1k_tokens"]
    return None


def projected_monthly(spec, jobs: list):
    """Dollars per 30-day month for the enabled jobs, using the lab's true prices and token counts."""
    total = 0.0
    problems = []
    for job in jobs:
        if not job.get("enabled", True):
            continue
        name = job.get("name", "")
        price = _price(spec, job.get("model"))
        if price is None:
            problems.append(f"job {name} uses a model ({job.get('model')}) that is not in the config's model list")
            continue
        tokens = spec["runaway_tokens"] if name == spec["runaway_job"] else next((j["tokens"] for j in spec["other_jobs"] if j["name"] == name), 2000)
        try:
            runs = labs.runs_per_month(job.get("schedule", ""))
        except ValueError as exc:
            problems.append(f"job {name} has a schedule that does not read ({exc})")
            continue
        total += runs * tokens / 1000 * price
    return round(total, 2), problems


def _grade_cost(spec, root: Path, diagnosis: str):
    missing = []
    data, err = _json(root, "cron/jobs.json")
    cfg, cfg_err = _yaml(root, "config.yaml")
    if err or cfg_err:
        missing.append(_miss("config_parses", err or cfg_err))
        return _outcome(spec["lab_id"], "Bill under control", missing)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    job = next((j for j in jobs if j.get("name") == spec["runaway_job"]), None)
    if job is None or not job.get("enabled", True):
        missing.append(_miss("job_removed", f"The {spec['runaway_job']} job is gone or switched off. The client still needs that summary every weekday."))
    else:
        try:
            per_day = labs.runs_per_firing_day(job.get("schedule", ""))
            fires = labs.can_fire(job.get("schedule", ""))
        except ValueError as exc:
            per_day, fires = 0, False
            missing.append(_miss("schedule_unreadable", f"The schedule for {spec['runaway_job']} does not read: {exc}."))
        else:
            if per_day > spec["max_sane_runs"]:
                missing.append(_miss("still_runaway", f"{spec['runaway_job']} still runs {per_day} times on each day it fires. The client needs one summary before the stand-up, not hundreds."))
            elif per_day < 1 or not fires:
                missing.append(_miss("never_runs", f"{spec['runaway_job']} would never run. The summary has to arrive every weekday."))
        if job.get("deliver_to") != f"{spec['client']['owner'].split()[0].lower()}@{spec['client']['domain']}" or "summar" not in str(job.get("prompt", "")).lower():
            missing.append(_miss("summary_changed", "The summary job no longer sends the summary to the same person, or no longer asks for one. Change the cost, not the job."))
    names = {j.get("name") for j in jobs}
    for other in spec["other_jobs"]:
        found = next((j for j in jobs if j.get("name") == other["name"]), None)
        if found is None or not found.get("enabled", True) or found.get("schedule") != other["schedule"]:
            missing.append(_miss("other_job_changed", f"The {other['name']} job was removed or changed. It was healthy, so it should stay as it was."))
            break
    spend, problems = projected_monthly(spec, jobs)
    if problems:
        missing.append(_miss("model_unknown", problems[0].capitalize() + "."))
    elif spend > spec["budget_monthly"]:
        missing.append(_miss("over_budget", f"At these schedules and models the jobs would cost about ${spend:.0f} a month. The client's budget is ${spec['budget_monthly']}."))
    budget = labs.dig(cfg, "budget", default={}) or {}
    daily = budget.get("daily_usd_cap") if isinstance(budget, dict) else None
    monthly = budget.get("monthly_usd_cap") if isinstance(budget, dict) else None
    daily_ok = isinstance(daily, (int, float)) and not isinstance(daily, bool) and daily > 0
    monthly_ok = isinstance(monthly, (int, float)) and not isinstance(monthly, bool) and monthly > 0
    if not daily_ok and not monthly_ok:
        missing.append(_miss("cap_missing", "There is no working spending cap in config.yaml. A cap of zero or no cap at all lets a bad schedule spend without limit."))
    elif (daily_ok and daily > spec["budget_monthly"] / 30 * 1.25) or (monthly_ok and monthly > spec["budget_monthly"]):
        missing.append(_miss("cap_too_high", f"The cap lets the jobs spend more than the ${spec['budget_monthly']} a month the client budgeted. Set it where the budget ends."))
    if (daily_ok or monthly_ok) and str(budget.get("on_exceed", "")).lower() not in ("pause", "stop", "disable"):
        missing.append(_miss("cap_soft", "The cap only warns. Make Hermes stop or pause the jobs when the cap is reached, because a warning nobody reads does not hold back a bill."))
    missing += _diagnosis(diagnosis, _cost_concepts(spec))
    missing += _cost_number(spec, diagnosis)
    return _outcome(spec["lab_id"], "Bill under control", missing)


def _cost_concepts(spec):
    return [
        ("diag_job", f"Your diagnosis does not name the job that caused it ({spec['runaway_job']}).", [re.escape(spec["runaway_job"])]),
        ("diag_cause", "Your diagnosis does not say why: the schedule made it run every minute, all day.", [r"every minute", r"each minute", r"per minute", r"once a minute", r"1,?440", r"\* \* \* \* \*", r"too often", r"every 1 min"]),
        ("diag_prevent", "Your diagnosis does not say what stops it happening again: a spending cap that pauses the jobs.", [r"\bcap\b", r"limit", r"budget", r"pause", r"alert"]),
    ]


def _cost_number(spec, diagnosis: str) -> list:
    figures = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", diagnosis)]
    low, high = spec["daily_cost"] * 0.85, spec["daily_cost"] * 1.15
    if not any(low <= f <= high for f in figures):
        return [_miss("diag_number", "Your diagnosis does not give the cost per day of the runaway job, worked out from the log (runs a day times the cost of one run), within about 15 percent.")]
    return []


# ----------------------------------------------------------------- reboot --


def _unit(text: str) -> dict:
    sections, current = {}, None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, {})
            continue
        if current and "=" in line:
            key, _, value = line.partition("=")
            sections[current].setdefault(key.strip(), []).append(value.strip())
    return sections


def _grade_reboot(spec, root: Path, diagnosis: str):
    missing = []
    unit = _unit(_text(root, "systemd/hermes-gateway.service"))
    if not unit:
        missing.append(_miss("unit_missing", "The service file is missing or empty."))
    else:
        if "multi-user.target" not in " ".join(unit.get("Install", {}).get("WantedBy", [])):
            missing.append(_miss("unit_install", "The service file does not say which startup stage wants it, so it is never started at boot."))
        if (unit.get("Service", {}).get("Restart") or ["no"])[0] not in ("on-failure", "always"):
            missing.append(_miss("unit_restart", "The service file does not restart Hermes after it stops, so one crash leaves it off until someone notices."))
        after = " ".join(unit.get("Unit", {}).get("After", []))
        if "network-online.target" not in after:
            missing.append(_miss("unit_network", "The service file does not wait for the network, so after a power cut it can start before the network is up and fail."))
        service = unit.get("Service", {})
        if not service.get("ExecStart") or not service.get("EnvironmentFile"):
            missing.append(_miss("unit_damaged", "The service file lost its start command or its keys file. Fix what was wrong without removing what was working."))
    enabled = _text(root, "systemd/enabled-units.txt").splitlines()
    if "hermes-gateway.service" not in [line.strip() for line in enabled]:
        missing.append(_miss("unit_not_enabled", "The service is not on the list of units that start at boot. Having the file is not the same as turning it on."))
    for rel in spec["secret_files"]:
        path = root / rel
        if not path.is_file():
            missing.append(_miss("secret_deleted", f"{rel} is missing. Lock the file down, do not delete it."))
            break
        if not fileaccess.is_private(path):
            missing.append(_miss("perm_open", _open_message(rel, path)))
            break
    cron = [line for line in _text(root, "crontab.txt").splitlines() if line.strip() and not line.strip().startswith("#")]
    if len(cron) != 1:
        missing.append(_miss("cron_lines", f"crontab.txt has {len(cron)} schedule lines. It should have the one backup line."))
    else:
        parts = cron[0].split(None, 5)
        if len(parts) < 6:
            missing.append(_miss("cron_read", "The backup line in crontab.txt does not have five time fields and a command."))
        else:
            expr, command = " ".join(parts[:5]), parts[5]
            try:
                fires = labs.can_fire(expr)
                monthly = labs.runs_per_month(expr)
            except ValueError as exc:
                fires, monthly = False, 0
                missing.append(_miss("cron_read", f"The backup schedule does not read: {exc}."))
            else:
                if not fires:
                    missing.append(_miss("cron_never", "The backup schedule names a day that never happens, so it never fires."))
                elif monthly < 4:
                    missing.append(_miss("cron_rare", "The backup would run less than weekly. A backup has to be frequent enough that losing a week is acceptable."))
            runner, script = _runner_and_script(command)
            if not script.startswith(labs.FAKE_ROOT + "/"):
                missing.append(_miss("cron_path", f"The backup line points at {script}, which does not exist on this machine. The script is in the scripts folder."))
            else:
                target = root / script[len(labs.FAKE_ROOT) + 1:]
                if not target.is_file():
                    missing.append(_miss("cron_path", f"The backup line points at {script}, and no such file exists."))
    script_path = root / "scripts/backup.sh"
    if not script_path.is_file() or not script_path.read_text(encoding="utf-8").startswith("#!") or "tar" not in script_path.read_text(encoding="utf-8"):
        missing.append(_miss("script_damaged", "The backup script is missing, lost its first line, or no longer copies anything."))
    elif not _can_start(script_path, cron):
        if fileaccess.ON_WINDOWS:
            missing.append(_miss("script_not_executable", "The backup line starts the script by its path alone, and nothing on this computer marks the file as runnable. Name the program that runs it at the start of the command."))
        else:
            missing.append(_miss("script_not_executable", "The backup script is not marked as runnable, so the scheduler cannot start it."))
    missing += _restore_test(spec, root)
    missing += _diagnosis(diagnosis, _reboot_concepts(spec))
    return _outcome(spec["lab_id"], "Back after a power cut", missing)


# Programs that run a shell script when a schedule line names them first, as Hermes runs a .sh script with bash.
RUNNERS = ("sh", "bash", "/bin/sh", "/bin/bash", "/usr/bin/sh", "/usr/bin/bash")


def _runner_and_script(command: str):
    """(the program named before the script, or "", the script's path) for a schedule line's command."""
    words = command.split()
    if words[:1] == ["/usr/bin/env"] and words[1:2] and words[1] in ("sh", "bash"):
        words = words[1:]
    if words and words[0] in RUNNERS:
        return words[0], (words[1] if len(words) > 1 else "")
    return "", (words[0] if words else "")


def _can_start(script_path: Path, cron_lines) -> bool:
    """Whether the scheduler can start the backup script. A line that names the program that runs it always can. On
    Linux and macOS a line naming the script alone works when the file is marked runnable (chmod +x); Windows has no
    such mark, so there the line has to name the program. With no readable schedule line there is nothing to start it,
    and the schedule checks already say so."""
    if len(cron_lines) == 1:
        parts = cron_lines[0].split(None, 5)
        if len(parts) == 6 and _runner_and_script(parts[5])[0]:
            return True
    if fileaccess.ON_WINDOWS:
        return len(cron_lines) != 1 or len(cron_lines[0].split(None, 5)) < 6
    return bool(_mode(script_path) & stat.S_IXUSR)


def _open_message(rel: str, path: Path) -> str:
    if fileaccess.ON_WINDOWS:
        return f"{rel} can be read by other accounts on this computer (its access list also lets in {', '.join(fileaccess.others(path))}). Only your account should be on it."
    return f"{rel} can be read by other users on the computer (mode {oct(_mode(path))[2:]}). Only its owner should be able to read it."


def _restore_test(spec, root: Path) -> list:
    text = _text(root, "RESTORE-TEST.md")
    if not text.strip():
        return [_miss("restore_missing", "There is no RESTORE-TEST.md. A backup nobody has restored is a hope, so write down a restore you tried.")]
    out = []
    if not re.search(r"\d{4}-\d{2}-\d{2}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? \d{1,2}", text, re.I):
        out.append(_miss("restore_date", "RESTORE-TEST.md does not give the day you did the restore test."))
    if not re.search(r"\b\d+\s+(?:files?|items?)\b|\b(?:restored|recovered)\s+\d+", text, re.I):
        out.append(_miss("restore_count", "RESTORE-TEST.md does not say how many files came back."))
    if not re.search(r"hermes-\d{4}|\.tar\.gz|backup file|archive", text, re.I):
        out.append(_miss("restore_which", "RESTORE-TEST.md does not say which backup file you restored from."))
    return out


def _reboot_concepts(spec):
    return [
        ("diag_boot", "Your diagnosis does not say why Hermes stayed off: the service was never turned on to start at boot.", [r"enabl", r"at boot", r"on boot", r"start(?:s|ed)? (?:up|at|on)", r"wanted", r"startup"]),
        ("diag_perm", "Your diagnosis does not mention the open key files: other users on the computer could read them.", [r"permission", r"world[- ]readable", r"mode", r"chmod", r"\b600\b", r"other users", r"readable", r"icacls", r"access list", r"\bACL", r"other accounts"]),
        ("diag_backup", "Your diagnosis does not say why the backup never ran.", [r"backup", r"cron", r"schedule"]),
        ("diag_proof", "Your diagnosis does not say how the client can tell it works: a restore test.", [r"restore", r"test(?:ed)? (?:a )?(?:restore|recovery)", r"recover"]),
    ]


# ------------------------------------------------------------------ vault --


def _grade_vault(spec, root: Path, diagnosis: str):
    missing = []
    agents = spec["agents"]
    for rel, value in stray_secrets(root):
        missing.append(_miss("secret_in_file", f"A key is still written out in {rel}. Configuration files hold the name of the variable, never the key."))
        break
    refs, vars_ = [], []
    for agent in agents:
        cfg, err = _yaml(root, f"profiles/{agent['profile']}/config.yaml")
        if err:
            missing.append(_miss("config_parses", err))
            return _outcome(spec["lab_id"], "Each helper has its own key", missing)
        pointer = labs.dig(cfg, "provider", "api_key_env")
        refs.append(pointer if isinstance(pointer, str) else "")
    if not all(refs):
        missing.append(_miss("not_wired", "A profile does not say which environment variable holds its key. Each profile's provider settings need a line naming its own variable."))
    elif len(set(refs)) < len(refs):
        missing.append(_miss("still_shared", "Both profiles still point at the same variable, so they still share one key."))
    envs = []
    for agent in agents:
        env_path = root / "profiles" / agent["profile"] / ".env"
        envs.append(parse_env(_text(root, f"profiles/{agent['profile']}/.env")))
        if not env_path.is_file():
            missing.append(_miss("env_missing", f"profiles/{agent['profile']}/.env does not exist. Each profile keeps its own keys in its own file."))
            break
        if not fileaccess.is_private(env_path):
            if fileaccess.ON_WINDOWS:
                missing.append(_miss("env_open", f"profiles/{agent['profile']}/.env can be read by other accounts on this computer (its access list also lets in {', '.join(fileaccess.others(env_path))}). Only your account should be on it."))
            else:
                missing.append(_miss("env_open", f"profiles/{agent['profile']}/.env can be read by other users. Only its owner should read it."))
            break
    values = []
    for agent, env, ref in zip(agents, envs, refs):
        value = env.get(ref, "") if ref else ""
        values.append(value)
    if not all(values) or len(set(values)) < len(values) or any(v == spec["shared_secret"] or not v.startswith("FAKE-") for v in values):
        missing.append(_miss("env_values", "Each profile's .env must hold its own new key, different from the other and from the old shared one, made up for this lab starting with FAKE-."))
    console, console_err = _json(root, "provider-console/keys.json")
    keys = (console or {}).get("keys", []) if console else []
    if console_err:
        missing.append(_miss("console_broken", console_err))
    old = next((k for k in keys if k.get("id") == spec["shared_id"]), None)
    if not old or old.get("status") != "revoked":
        missing.append(_miss("shared_active", "The shared key is still active on the provider console. Switch it off once each helper has its own."))
    for agent, value in zip(agents, values):
        mine = [k for k in keys if k.get("status") == "active" and k.get("secret") and k.get("secret") == value]
        if not mine:
            missing.append(_miss("no_scoped_key", f"No active key on the console matches the one {agent['profile']} uses. Make one key per helper on the console."))
            break
        scopes = set(mine[0].get("scopes") or [])
        needs = set(agent["needs"])
        if not scopes:
            missing.append(_miss("scopes_empty", f"The key for {agent['profile']} lists no scopes. A key with no limits can do anything."))
            break
        if not needs <= scopes:
            missing.append(_miss("scopes_short", f"The key for {agent['profile']} cannot do something its job needs ({', '.join(sorted(needs - scopes))})."))
            break
        if not scopes <= needs:
            missing.append(_miss("scopes_wide", f"The key for {agent['profile']} can do more than its job needs ({', '.join(sorted(scopes - needs))}). Give each key only the smallest set of scopes that still does the job."))
            break
    missing += _rotation(spec, root, refs)
    ignore = [line.strip() for line in _text(root, ".gitignore").splitlines()]
    tracked = [line.strip() for line in _text(root, "tracked-files.txt").splitlines()]
    if not any(line in (".env", "*.env", "/.env", "profiles/*/.env", "**/.env") for line in ignore) or any(t.endswith(".env") for t in tracked):
        missing.append(_miss("env_unprotected", "The .env files can still be saved to the shared repository. Put .env on the ignore list."))
    missing += _diagnosis(diagnosis, _vault_concepts(spec))
    return _outcome(spec["lab_id"], "Each helper has its own key", missing)


def _rotation(spec, root: Path, var_names) -> list:
    text = _text(root, "ROTATION.md")
    if not text.strip():
        return [_miss("rotation_missing", "There is no ROTATION.md. Nobody will change these keys unless someone writes down who and when.")]
    out = []
    names = [v for v in var_names if v]
    if not names or not all(v in text for v in names):
        out.append(_miss("rotation_keys", "ROTATION.md does not list every key by its variable name."))
    from . import documents  # the same name check the document gates use

    if not documents.has_name(text):
        out.append(_miss("rotation_owner", "ROTATION.md does not name a person who owns each key."))
    days = [int(n) for n in re.findall(r"(\d{1,3})\s*days?", text, re.I)]
    months = [int(n) * 30 for n in re.findall(r"(\d{1,2})\s*months?", text, re.I)]
    interval = days + months
    if not interval or min(interval) > spec["max_rotation_days"]:
        out.append(_miss("rotation_interval", f"ROTATION.md does not give a change interval of {spec['max_rotation_days']} days or less."))
    if not re.search(r"revok|switch(?:ed)?\s+(?:it\s+|them\s+)?off|disable|turn(?:ed)?\s+(?:it\s+|them\s+)?off", text, re.I) or not re.search(r"leak|exposed|lost|stolen|suspect", text, re.I):
        out.append(_miss("rotation_leak", "ROTATION.md does not say what to do first if a key leaks: switch it off, then replace it."))
    return out


def _vault_concepts(spec):
    return [
        ("diag_shared", "Your diagnosis does not say what was wrong: both helpers shared one key that could do everything.", [r"shared", r"same key", r"one key", r"single key"]),
        ("diag_scope", "Your diagnosis does not say what each key should be allowed to do.", [r"scope", r"only what", r"smallest", r"minimum", r"read[- ]only", r"permission"]),
        ("diag_config", "Your diagnosis does not say that a key was written into a configuration file instead of an environment variable.", [r"config", r"hard-?coded", r"written (?:in|into)", r"plain text", r"environment variable", r"\.env"]),
        ("diag_rotation", "Your diagnosis does not say who changes the keys and how often.", [r"rotat", r"every \d+", r"\d+ days", r"owner"]),
    ]


GRADERS = {"lab.leak": _grade_leak, "lab.cost": _grade_cost, "lab.reboot": _grade_reboot, "lab.vault": _grade_vault}


def grade_lab(lab_id: str, seed: int, root, diagnosis: str = "") -> dict:
    """Grade one lab folder. Reads files only. The same folder and diagnosis always give the same answer."""
    if lab_id not in GRADERS:
        raise ValueError(f"Unknown lab: {lab_id}")
    folder = Path(root)
    if not folder.is_dir() or not (folder / labs.MARKER).is_file():
        return {"passed": False, "title": "No lab folder here", "detail": "Open the lab first, so the folder exists, then check it.", "facts": [], "missing": [_miss("folder", "The lab folder is missing or is not a Field Academy lab.")]}
    spec = labs.spec_for(lab_id, seed)
    return GRADERS[lab_id](spec, folder, diagnosis)


def check_ids(lab_id: str) -> list:
    """Every check id a lab can report, so the coaching table can be tested for gaps."""
    return sorted(LAB_CHECK_IDS[lab_id])


LAB_CHECK_IDS = {
    "lab.leak": {"config_parses", "secret_in_file", "not_wired", "config_damaged", "console_broken", "env_missing_new", "old_not_revoked", "new_key_unmatched", "env_unprotected", "env_damaged", "incident_missing", "incident_key", "incident_when", "incident_who", "incident_fix", "incident_prevent", "diag_short", "diag_cause", "diag_where", "diag_evidence", "diag_fix", "diag_prevent"},
    "lab.cost": {"config_parses", "job_removed", "schedule_unreadable", "still_runaway", "never_runs", "summary_changed", "other_job_changed", "model_unknown", "over_budget", "cap_missing", "cap_too_high", "cap_soft", "diag_short", "diag_job", "diag_cause", "diag_prevent", "diag_number"},
    "lab.reboot": {"unit_missing", "unit_install", "unit_restart", "unit_network", "unit_damaged", "unit_not_enabled", "secret_deleted", "perm_open", "cron_lines", "cron_read", "cron_never", "cron_rare", "cron_path", "script_damaged", "script_not_executable", "restore_missing", "restore_date", "restore_count", "restore_which", "diag_short", "diag_boot", "diag_perm", "diag_backup", "diag_proof"},
    "lab.vault": {"secret_in_file", "config_parses", "not_wired", "still_shared", "env_missing", "env_open", "env_values", "console_broken", "shared_active", "no_scoped_key", "scopes_empty", "scopes_short", "scopes_wide", "rotation_missing", "rotation_keys", "rotation_owner", "rotation_interval", "rotation_leak", "env_unprotected", "diag_short", "diag_shared", "diag_scope", "diag_config", "diag_rotation"},
}


# ---------------------------------------------------------------- coaching --
#
# One hint and one finished example per check, in the shape learning.ladder()
# takes. The example is about a different business, so it shows the move and
# never hands over this lab's answer.

COACH = {
    "config_parses": {"hint": "Open the file named in the message and look at the line it points to. A missing colon or a wrong indent is usually all it is.", "example": "Example: \"api_key_env: MY_KEY\" has a colon and one space. \"api_key_env MY_KEY\" does not read."},
    "secret_in_file": {"hint": "Search every file for the start of the key (FAKE-KEY-DO-NOT-USE-). In a terminal, grep -r finds it. Remove it from each file that is saved to the repository.", "example": "Example: a bakery's settings said api_key: sk-abc123. The fix was api_key_env: BAKERY_API_KEY, with the value moved to the .env file."},
    "not_wired": {"hint": "Do not just delete the key line. Replace it with a line that names the environment variable, so Hermes still knows where to look.", "example": "Example: change \"api_key: <the key>\" to \"api_key_env: BAKERY_API_KEY\" and put BAKERY_API_KEY=<the new key> in .env."},
    "config_damaged": {"hint": "Compare the file to the settings around it. The provider's name and model should still be there.", "example": "Example: provider:\\n  name: Larkspur\\n  model: larkspur-std\\n  api_key_env: LARKSPUR_API_KEY"},
    "console_broken": {"hint": "The stand-in console file is JSON. Check the commas and quotes around the entry you changed.", "example": "Example: {\"id\": \"key_x\", \"status\": \"revoked\"} needs a comma after it when another entry follows."},
    "env_missing_new": {"hint": "Make a new key on the stand-in console first, then copy that exact value into .env under the variable name.", "example": "Example: NEWKEY=FAKE-ROTATED-0001 in .env, and the same FAKE-ROTATED-0001 as the secret on the console."},
    "old_not_revoked": {"hint": "Rotation has two halves: a new key and an old key that stops working. On the console, set the leaked key's status to revoked.", "example": "Example: {\"id\": \"key_77a\", \"label\": \"hermes-gateway\", \"status\": \"revoked\"}"},
    "new_key_unmatched": {"hint": "The console and .env must agree. Add a new active entry with the same label and a secret, and copy that secret into .env.", "example": "Example: console entry label \"hermes-gateway\" status \"active\" secret \"FAKE-ROTATED-0001\"; .env line KEY=FAKE-ROTATED-0001."},
    "env_unprotected": {"hint": "Add .env to the .gitignore file, and remove it from the list of saved files (tracked-files.txt).", "example": "Example: a line that says .env on its own, in .gitignore. In tracked-files.txt, no line says .env."},
    "env_damaged": {"hint": "Leave the lines that were there. Add your new lines under them.", "example": "Example: keep TZ and the calendar token, and add one new line for the key."},
    "incident_missing": {"hint": "Make a new file called INCIDENT.md in the lab folder. Five short parts is enough: what, when, who was told, what changed, how it is prevented.", "example": "Example:\\nWhat: the shop's website key was saved in the settings file. Key id key_91c.\\nWhen: first used by a stranger on 2026-08-02.\\nTold: Alice Moreno, owner, the same day.\\nChanged: switched the key off, made a new one, moved it to .env.\\nPrevented: .env is on the ignore list."},
    "incident_key": {"hint": "Write the key's id from the console (it looks like key_ followed by letters and numbers). Never write the key itself.", "example": "Example: \"The key with id key_91c was exposed.\""},
    "incident_when": {"hint": "Find the first line in logs/audit.log where an unfamiliar address used the key. Write that date.", "example": "Example: \"First misuse: 2026-08-02, from an address nobody recognised.\""},
    "incident_who": {"hint": "Write the owner's actual name from the client's note, such as Alice Moreno, rather than a role like the boss.", "example": "Example: \"I told Alice Moreno, the owner, by phone at 3 pm.\""},
    "incident_fix": {"hint": "Say what you did to the old key and what replaced it.", "example": "Example: \"Revoked the old key on the console and issued a new one.\""},
    "incident_prevent": {"hint": "Say what stops it happening again: where keys live now and what keeps them out of the repository.", "example": "Example: \"Keys live only in .env, which is on the ignore list. Settings files name the variable.\""},
    "diag_short": {"hint": "Write three or four sentences: what happened, how you found it, what you changed.", "example": "Example: \"The website key was written in the settings file, which is saved to the shared repository. I found it by searching the files, switched the key off, made a new one and moved it to .env.\""},
    "diag_cause": {"hint": "Say the cause in one sentence, using words that match what you saw.", "example": "Example: \"The job was set to run every minute, so it ran 1,440 times a day.\""},
    "diag_where": {"hint": "Name the file you found the key in.", "example": "Example: \"The key was in config.yaml.\""},
    "diag_evidence": {"hint": "Point at one line in the provider log that told you.", "example": "Example: \"The provider log showed 41 requests from an address we had not seen before.\""},
    "diag_fix": {"hint": "Say what you did to the old key and the new one.", "example": "Example: \"I revoked the old key and made a new one.\""},
    "diag_prevent": {"hint": "Say what keeps this from happening again.", "example": "Example: \"The key now lives in .env, which is ignored by the repository.\""},
    "diag_job": {"hint": "Name the job from cron/jobs.json that ran too often.", "example": "Example: \"The nightly-report job.\""},
    "diag_number": {"hint": "Take the number of runs in a day and multiply by the cost of one run from the log. The log's daily_total line checks your answer.", "example": "Example: 1,440 runs times $0.05 a run is about $72 a day."},
    "job_removed": {"hint": "Do not remove the job. Change how often it runs and which model it uses.", "example": "Example: change \"* * * * *\" to \"30 7 * * 1-5\" so it runs at 7:30 on weekdays."},
    "schedule_unreadable": {"hint": "A schedule has five parts: minute, hour, day of month, month, day of week.", "example": "Example: 30 7 * * 1-5 means 7:30 am, Monday to Friday."},
    "still_runaway": {"hint": "Work out how many times a day your schedule fires. The client needs a few, not hundreds.", "example": "Example: 30 7 * * 1-5 fires once a day, Monday to Friday."},
    "never_runs": {"hint": "Check the schedule can fire. It needs a minute and an hour that exist.", "example": "Example: 30 7 * * 1-5 fires. 30 7 31 2 * never does, because there is no February 31."},
    "summary_changed": {"hint": "Keep the job's prompt and the person it delivers to as they were. Only the schedule and the model are yours to change.", "example": "Example: leave deliver_to and the prompt alone."},
    "other_job_changed": {"hint": "Leave the healthy jobs as they were.", "example": "Example: weekly-invoice-digest keeps its Monday 8 am schedule."},
    "model_unknown": {"hint": "A job's model must be one of the names under models: in config.yaml.", "example": "Example: model: larkspur-mini, if that is a name in the list."},
    "over_budget": {"hint": "Cost a month is runs a month times tokens times the model's price. Lower the runs, or pick a cheaper model, until the total is under the budget.", "example": "Example: 22 runs a month at 3,000 tokens on a $0.004 per 1,000 model is about $0.26 a month."},
    "cap_missing": {"hint": "Add a budget section to config.yaml with a daily cap above zero.", "example": "Example:\\nbudget:\\n  daily_usd_cap: 4\\n  on_exceed: pause"},
    "cap_too_high": {"hint": "Divide the monthly budget by 30 for a daily cap.", "example": "Example: a $120 monthly budget is $4 a day."},
    "cap_soft": {"hint": "Set on_exceed to pause or stop, so reaching the cap holds the jobs back.", "example": "Example: on_exceed: pause"},
    "unit_missing": {"hint": "The service file is in the systemd folder.", "example": "Example: systemd/hermes-gateway.service"},
    "unit_install": {"hint": "A service needs an Install section that names the stage that starts it.", "example": "Example:\\n[Install]\\nWantedBy=multi-user.target"},
    "unit_restart": {"hint": "Add a restart line to the Service section so a crash does not leave Hermes off.", "example": "Example: Restart=on-failure"},
    "unit_network": {"hint": "Make the service wait for the network. It needs an After line in the Unit section.", "example": "Example: After=network-online.target"},
    "unit_damaged": {"hint": "Put back the line you removed. A service needs its start command and its keys file.", "example": "Example: ExecStart=... and EnvironmentFile=..."},
    "unit_not_enabled": {"hint": "The file alone does nothing at boot. The unit has to be on the enabled list. In this lab, that list is enabled-units.txt.", "example": "Example: add the line hermes-gateway.service to systemd/enabled-units.txt, which stands in for running systemctl enable."},
    "secret_deleted": {"hint": "Put the file back and change its permissions instead.", "example": "Example: the file stays, and its mode becomes 600."},
    "perm_open": {"hint": "In a terminal, chmod 600 on the file lets only its owner read and write it.", "example": "Example: chmod 600 .env"},
    "cron_lines": {"hint": "crontab.txt should have the one backup line and comments.", "example": "Example: one line starting with a time."},
    "cron_read": {"hint": "A schedule line has five time fields, then the command.", "example": "Example: 30 2 * * * /srv/hermes-client/scripts/backup.sh"},
    "cron_never": {"hint": "Look at the day and month fields. A day that never occurs means it never fires.", "example": "Example: 30 2 * * * fires every night. 30 2 31 2 * never fires."},
    "cron_rare": {"hint": "Make the backup daily or at least weekly.", "example": "Example: 30 2 * * * is every night at 2:30."},
    "cron_path": {"hint": "The command must be the real path of the script on this machine. In the lab that is the scripts folder under /srv/hermes-client.", "example": "Example: /srv/hermes-client/scripts/backup.sh"},
    "script_damaged": {"hint": "The script needs its first line (#!/bin/sh) and its tar command.", "example": "Example: a first line of #!/bin/sh"},
    "script_not_executable": {"hint": "The scheduler can only start a script that is marked runnable. In a terminal, chmod +x does it.", "example": "Example: chmod +x scripts/backup.sh"},
    "restore_missing": {"hint": "Restore a file from the backup archive into a scratch folder and write down what you did.", "example": "Example: RESTORE-TEST.md: Tested 2026-08-04. Restored 3 files from hermes-2026-08-03.tar.gz into a scratch folder. All opened."},
    "restore_date": {"hint": "Write the day you did the test.", "example": "Example: Tested 2026-08-04."},
    "restore_count": {"hint": "Say how many files came back.", "example": "Example: Restored 3 files."},
    "restore_which": {"hint": "Name the archive file you restored from.", "example": "Example: from hermes-2026-08-03.tar.gz."},
    "diag_boot": {"hint": "Say why it stayed off after the power cut.", "example": "Example: \"The service was never enabled, so it did not start when the computer did.\""},
    "diag_perm": {"hint": "Say what was wrong with the key files and what you changed.", "example": "Example: \"The .env file was readable by every user, so I set it to 600.\""},
    "diag_backup": {"hint": "Say why the backup never ran.", "example": "Example: \"The scheduler pointed at a script path that does not exist.\""},
    "diag_proof": {"hint": "Say how the client can tell the backup works.", "example": "Example: \"I restored a file from last night's archive and it opened.\""},
    "still_shared": {"hint": "Give each profile its own variable name, such as one for the front desk and one for the bookkeeper.", "example": "Example: DESK_KEY for the front desk profile and BOOKS_KEY for the bookkeeper."},
    "env_missing": {"hint": "Each profile folder gets its own .env with only its own key.", "example": "Example: profiles/books/.env holds BOOKS_KEY=<its key>."},
    "env_open": {"hint": "Lock the file down with chmod 600.", "example": "Example: chmod 600 profiles/books/.env"},
    "env_values": {"hint": "Make two new keys on the console. Put one in each profile's .env. They must differ from each other and from the old shared key.", "example": "Example: DESK_KEY=FAKE-DESK-001 and BOOKS_KEY=FAKE-BOOKS-001."},
    "shared_active": {"hint": "After each helper has its own key, set the shared key's status to revoked on the console.", "example": "Example: {\"id\": \"key_x\", \"status\": \"revoked\"}"},
    "no_scoped_key": {"hint": "Add one active key per helper on the console, with the same secret you put in that helper's .env.", "example": "Example: {\"label\": \"books\", \"status\": \"active\", \"secret\": \"FAKE-BOOKS-001\", \"scopes\": [\"invoices:read\"]}"},
    "scopes_empty": {"hint": "A key needs a scopes list that names what it may do.", "example": "Example: \"scopes\": [\"invoices:read\"]"},
    "scopes_short": {"hint": "Read the client's note for what the helper does, and give the key those scopes.", "example": "Example: a helper that reads mail needs mail:read."},
    "scopes_wide": {"hint": "Remove every scope the job does not use. Reading does not need sending, and nothing here needs admin.", "example": "Example: a bookkeeper that reads invoices needs invoices:read and nothing else."},
    "rotation_missing": {"hint": "Make a ROTATION.md with one line per key: its variable name, its owner, how often it changes.", "example": "Example: BOOKS_KEY, owner Alice Moreno, changes every 60 days. If it leaks: switch it off first, then make a new one."},
    "rotation_keys": {"hint": "List every key by its variable name.", "example": "Example: DESK_KEY and BOOKS_KEY."},
    "rotation_owner": {"hint": "Put a person's name next to each key.", "example": "Example: owner Alice Moreno."},
    "rotation_interval": {"hint": "Give a change interval in days, no more than the limit.", "example": "Example: changes every 60 days."},
    "rotation_leak": {"hint": "Write what to do first if a key leaks.", "example": "Example: switch the key off on the console first, then make a new one."},
    "diag_shared": {"hint": "Say what was wrong with one key for both helpers.", "example": "Example: \"Both helpers used one key that could do everything.\""},
    "diag_scope": {"hint": "Say what each key may do now.", "example": "Example: \"Each key can only do what its helper needs.\""},
    "diag_config": {"hint": "Say whether any key was written into a settings file.", "example": "Example: \"One profile had the key written in its settings file; it now names a variable.\""},
    "diag_rotation": {"hint": "Say who changes the keys and how often.", "example": "Example: \"The owner changes each key every 60 days.\""},
}

WORKED = {
    "lab.leak": {
        "title": "A finished example: a bakery's website key",
        "body": (
            "A bakery's order helper stopped working after its provider emailed a warning, and the work went in this order. "
            "First came the provider's email and the log, which showed a stranger's address using the key the night before. "
            "Then a search of the files for the start of the key found it written in the settings file, which the shared repository had saved. "
            "The old key was switched off on the provider's site before any file was edited, because the stranger already had a copy. "
            "After that a new key went into .env as BAKERY_KEY, and the line in the settings was replaced with the name BAKERY_KEY. "
            ".env went on the ignore list and came off the saved list. "
            "The last step was a note for the owner with the key's id, the date, who was told, what changed and how it is prevented. "
            "Notice that switching the old key off came before the file edits."
        ),
    },
    "lab.cost": {
        "title": "A finished example: a salon's reminder job",
        "body": (
            "A salon's reminder job tripled its bill, and the work went in this order. "
            "The usage log showed the same job appearing every minute, which is 1,440 runs a day, and 1,440 runs times $0.03 a run is about $43 a day. "
            "The jobs file showed a schedule of * * * * *, left over from a test. "
            "The fix was a schedule of 0 9 * * * so it runs once at 9 am, which is all the salon needs, with the job's text and its recipient left alone. "
            "Then came a cap of $2 a day with on_exceed set to pause, so a future mistake stops itself. "
            "The owner got a note with the cause, the daily number and the cap."
        ),
    },
    "lab.reboot": {
        "title": "A finished example: a dentist's front desk helper",
        "body": (
            "A clinic's helper stayed off after a power cut and nobody knew the date of the last backup, so the work went in this order. "
            "The boot log said the service was not enabled for boot, so the service file got an Install section, a restart line and a wait for the network, and the unit went on the enabled list. "
            "A listing of the key files with their permissions showed the keys file open to everyone, so it was set to 600. "
            "The backup schedule pointed at a path that does not exist, so the path was corrected and the script was made runnable. "
            "To finish, one file was restored from last night's archive into a scratch folder, and the day, the number of files and the archive's name were written down."
        ),
    },
    "lab.vault": {
        "title": "A finished example: a travel agency's two helpers",
        "body": (
            "A travel agency's booking helper and its mailbox helper shared one key that could also change billing, and the work went in this order. "
            "Reading what each helper does came first: booking reads trips, and the mailbox helper reads and sends mail. "
            "Two new keys were made on the provider site, one with trips:read and one with mail:read and mail:send, and neither got admin. "
            "Each helper got its own .env with its own variable, and each helper's settings point at its own variable and never at the key. "
            "Then the old shared key was switched off. "
            "The note at the end lists each key, its owner by name, how often it changes and what to do first if one leaks."
        ),
    },
}


# What changes on Windows. A Windows file has no mode bits: its lock is its access list, and nothing marks a script as
# runnable. The checks and their ids are the same everywhere; these say how to do each step on a Windows computer.
WINDOWS_COACH = {
    "secret_deleted": {"hint": "Put the file back and lock it instead.", "example": "Example: the file stays, and its access list names only your account."},
    "perm_open": {"hint": "On Windows a file's lock is its access list, the list of accounts allowed to open it. In PowerShell, in the lab folder, icacls takes everyone off the list but you. If it still lists another account after that, that account was added to the file by name: take it off too, with icacls and /remove.",
                  "example": 'Example: icacls .env /inheritance:r /grant:r "${env:USERDOMAIN}\\${env:USERNAME}:F"'},
    "script_not_executable": {"hint": "Windows has no mark that makes a file runnable. A scheduler starts a script by naming the program that reads it, the way Hermes runs a .sh script with bash. Put that program at the start of the command.",
                              "example": "Example: 30 2 * * * /bin/sh /srv/hermes-client/scripts/backup.sh"},
    "diag_perm": {"hint": "Say what was wrong with the key files and what you changed.", "example": "Example: \"The .env file's access list let every account on the computer read it, so I used icacls to leave only my own account.\""},
    "env_open": {"hint": "In PowerShell, lock the file down with icacls, so only your account is on its access list.", "example": 'Example: icacls profiles\\books\\.env /inheritance:r /grant:r "${env:USERDOMAIN}\\${env:USERNAME}:F"'},
}

WINDOWS_WORKED = {
    "lab.reboot": {
        "title": WORKED["lab.reboot"]["title"],
        "body": (
            "A clinic's helper stayed off after a power cut and nobody knew the date of the last backup, so the work went in this order. "
            "The boot log said the service was not enabled for boot, so the service file got an Install section, a restart line and a wait for the network, and the unit went on the enabled list. "
            "A look at the key files' access lists with icacls showed the keys file open to every account on the computer, so it was locked to the owner's account alone. "
            "The backup schedule pointed at a path that does not exist, so the path was corrected and the line now names the program that runs the script. "
            "To finish, one file was restored from last night's archive into a scratch folder, and the day, the number of files and the archive's name were written down."
        ),
    },
}

if fileaccess.ON_WINDOWS:
    COACH.update(WINDOWS_COACH)
    WORKED.update(WINDOWS_WORKED)
