"""The lab builder: a disposable "client machine" as a plain folder of files.

Four labs, each a folder that imitates a Hermes home on a small client's
computer (config.yaml, a .env, scheduled jobs, logs, a profile folder, a
service file and a backup script) with one hidden problem inside. The learner
opens the folder, reads the evidence, repairs the files, and writes down what
happened. grade.py checks the result.

Safety rules this file keeps, because a past scratch Hermes home was not
isolated and rewrote real launchers:

* A lab is only ever files in a folder. Nothing here runs a program, starts a
  process, or sets an environment variable. Nothing reads or writes the real
  Hermes home.
* The folder lives under Field Academy's own data folder, in ``labs/``. It is
  refused if that data folder looks like a Hermes home itself (it holds a
  config.yaml, a .env, a cron or a profiles folder at its top).
* Every secret in a lab starts with ``FAKE-`` and the files say so. Nothing in
  a lab is a real key, a real address or a real person.
* A lab folder carries a marker file. Reset only deletes a folder that has it.

Everything about a lab is a pure function of its id and its seed: the same seed
builds the same folder byte for byte, and a different seed changes the names,
the keys, the numbers and which variant of the problem is hidden. That is what
stops two learners comparing answers. The clock never enters: dates come from a
fixed base date plus an offset taken from the seed.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import fileaccess

FAKE_ROOT = "/srv/hermes-client"
MARKER = "NOT-A-REAL-HERMES-HOME.txt"
LAB_IDS = ("lab.leak", "lab.cost", "lab.reboot", "lab.vault")
BASE_TIME = datetime(2026, 9, 14, 6, 0, tzinfo=timezone.utc)
SECRET_PREFIX = "FAKE-KEY-DO-NOT-USE-"

# Names in the labs are made up. Any likeness to a real business is chance.
CLIENTS = (
    {"name": "Birchwood Dental Partners", "owner": "Marguerite Okafor", "ops": "Daniel Whitlock", "domain": "birchwood-dental.example"},
    {"name": "Tallgrass Property Management", "owner": "Rosalind Achebe", "ops": "Evan Maddox", "domain": "tallgrass-pm.example"},
    {"name": "Copperline Plumbing and Heating", "owner": "Jorge Villanueva", "ops": "Hannah Brandt", "domain": "copperline-hvac.example"},
    {"name": "Fernhill Veterinary Clinic", "owner": "Imani Castellano", "ops": "Colin Pryce", "domain": "fernhill-vet.example"},
    {"name": "Summit Row Insurance Agency", "owner": "Nadia Kowalczyk", "ops": "Terrence Bloom", "domain": "summitrow-ins.example"},
    {"name": "Harborview Legal Services", "owner": "Priscilla Anand", "ops": "Theo Lindqvist", "domain": "harborview-legal.example"},
)
PROVIDERS = (
    {"name": "Larkspur", "var": "LARKSPUR_API_KEY", "models": ("larkspur-xl", "larkspur-std", "larkspur-mini")},
    {"name": "Cobalt Inference", "var": "COBALT_API_KEY", "models": ("cobalt-max", "cobalt-core", "cobalt-lite")},
    {"name": "Quillfeather", "var": "QUILLFEATHER_API_KEY", "models": ("quill-large", "quill-mid", "quill-small")},
)
PROFILES = ("frontdesk", "office", "main", "assistant")
JOB_NAMES = ("inbox-summary", "morning-digest", "front-desk-triage")
BOT_VARS = ("TELEGRAM_BOT_TOKEN", "SLACK_BOT_TOKEN")

TITLES = {
    "lab.leak": "The key in the open",
    "lab.cost": "The runaway bill",
    "lab.reboot": "Monday after the power cut",
    "lab.vault": "One key for everything",
}
MINUTES = {"lab.leak": 40, "lab.cost": 35, "lab.reboot": 45, "lab.vault": 50}


# ----------------------------------------------------------------- helpers --


def rng_for(lab_id: str, seed: int) -> random.Random:
    """A generator that depends only on the lab and the seed. Seeded by a string, which Python hashes the same way every run."""
    return random.Random(f"field-academy-deployer:{lab_id}:{int(seed)}")


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hex(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("0123456789abcdef") for _ in range(n))


def fake_secret(rng: random.Random, tag: str = "") -> str:
    return f"{SECRET_PREFIX}{tag}{_hex(rng, 24)}"


# -------------------------------------------------------------- tiny YAML --
#
# The lab's files use a small, regular subset of YAML: nested mappings, lists of
# plain values, and plain, quoted, number, boolean and inline-list values. The
# standard library has no YAML reader and the plugin takes no outside packages,
# so the graders read that subset here. A learner's edit that breaks it shows up
# as a plain message about the line.


class YamlError(ValueError):
    pass


def _scalar(raw: str):
    text = raw.strip()
    if text == "":
        return ""
    if text[0] in "\"'":
        quote = text[0]
        end = text.find(quote, 1)
        if end == -1:
            raise YamlError(f"a quote is never closed in {text[:30]!r}")
        return text[1:end]
    cut = re.search(r"\s#", text)
    if cut:
        text = text[: cut.start()].strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [_scalar(part) for part in inner.split(",")] if inner else []
    low = text.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~", "none"):
        return None
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    return text


def parse_yaml(text: str) -> dict:
    """Read the lab's YAML subset into dicts, lists and plain values."""
    rows = []
    for number, line in enumerate(text.splitlines(), start=1):
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise YamlError(f"line {number} is indented with a tab")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append((number, len(line) - len(line.lstrip(" ")), stripped))

    def block(index, indent):
        if index >= len(rows):
            return {}, index
        if rows[index][2].startswith("- "):
            items = []
            while index < len(rows) and rows[index][1] == indent and rows[index][2].startswith("- "):
                items.append(_scalar(rows[index][2][2:]))
                index += 1
            return items, index
        mapping = {}
        while index < len(rows):
            number, level, body = rows[index]
            if level < indent:
                break
            if level > indent:
                raise YamlError(f"line {number} is indented further than the line above it")
            if body.startswith("- "):
                raise YamlError(f"line {number} is a list item where a name was expected")
            if ":" not in body:
                raise YamlError(f"line {number} has no colon")
            key, _, rest = body.partition(":")
            key = key.strip().strip("\"'")
            rest = rest.strip()
            index += 1
            if rest == "" or rest.startswith("#"):
                if index < len(rows) and rows[index][1] > indent:
                    value, index = block(index, rows[index][1])
                elif index < len(rows) and rows[index][1] == indent and rows[index][2].startswith("- "):
                    value, index = block(index, indent)
                else:
                    value = None
                mapping[key] = value
            else:
                mapping[key] = _scalar(rest)
        return mapping, index

    if not rows:
        return {}
    value, _ = block(0, rows[0][1])
    return value if isinstance(value, dict) else {}


def dig(mapping, *path, default=None):
    node = mapping
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


# ------------------------------------------------------------------- cron --

_DOW = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
_MON = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
_ALIASES = {"@hourly": "0 * * * *", "@daily": "0 0 * * *", "@midnight": "0 0 * * *", "@weekly": "0 0 * * 0", "@monthly": "0 0 1 * *", "@yearly": "0 0 1 1 *", "@annually": "0 0 1 1 *"}
_DAYS_IN_MONTH = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}


def _field(text: str, low: int, high: int, names=None) -> set:
    out = set()
    for part in text.lower().split(","):
        if not part:
            raise ValueError("an empty part")
        step = 1
        if "/" in part:
            part, _, step_text = part.partition("/")
            if not step_text.isdigit() or int(step_text) < 1:
                raise ValueError(f"step {step_text!r}")
            step = int(step_text)
        if part == "*":
            start, end = low, high
        elif "-" in part:
            a, _, b = part.partition("-")
            start, end = _num(a, names), _num(b, names)
        else:
            start = _num(part, names)
            end = high if step > 1 else start
        if start < low or end > high or start > end:
            raise ValueError(f"{part!r} is outside {low} to {high}")
        out.update(range(start, end + 1, step))
    return out


def _num(text: str, names) -> int:
    if names and text in names:
        return names[text]
    if text.isdigit():
        return int(text)
    raise ValueError(f"{text!r} is not a number")


def parse_cron(expr: str) -> dict:
    """Read a five-field schedule. Raises ValueError with a plain reason."""
    text = _ALIASES.get(str(expr).strip().lower(), str(expr).strip())
    parts = text.split()
    if len(parts) != 5:
        raise ValueError(f"a schedule has five parts and this has {len(parts)}")
    minutes = _field(parts[0], 0, 59)
    hours = _field(parts[1], 0, 23)
    dom = _field(parts[2], 1, 31)
    months = _field(parts[3], 1, 12, _MON)
    dow = {0 if d == 7 else d for d in _field(parts[4], 0, 7, _DAYS_TO_NUM)}
    return {
        "minutes": minutes, "hours": hours, "dom": dom, "months": months, "dow": dow,
        "dom_any": parts[2] == "*", "dow_any": parts[4] == "*",
    }


_DAYS_TO_NUM = dict(_DOW)


def can_fire(expr: str) -> bool:
    """False for a schedule that names a day that never happens, such as the 31st of February."""
    spec = parse_cron(expr)
    if not spec["dom_any"] and spec["dow_any"]:
        return any(day <= _DAYS_IN_MONTH[month] for month in spec["months"] for day in spec["dom"])
    return bool(spec["months"])


def runs_per_firing_day(expr: str) -> int:
    spec = parse_cron(expr)
    return len(spec["minutes"]) * len(spec["hours"])


def runs_per_month(expr: str) -> float:
    """Average runs in a 30 day month, counting only the days the schedule is allowed to fire."""
    spec = parse_cron(expr)
    if not can_fire(expr):
        return 0.0
    per_day = len(spec["minutes"]) * len(spec["hours"])
    dom_share = len(spec["dom"]) / 31
    dow_share = len(spec["dow"]) / 7
    if spec["dom_any"] and spec["dow_any"]:
        share = 1.0
    elif spec["dom_any"]:
        share = dow_share
    elif spec["dow_any"]:
        share = dom_share
    else:
        share = min(1.0, dom_share + dow_share)
    return per_day * 30 * share * (len(spec["months"]) / 12)


# ---------------------------------------------------------------- the spec --


def spec_for(lab_id: str, seed: int) -> dict:
    """Everything about one lab, hidden facts included. A pure function of the id and the seed."""
    if lab_id not in LAB_IDS:
        raise ValueError(f"Unknown lab: {lab_id}")
    rng = rng_for(lab_id, seed)
    client = rng.choice(CLIENTS)
    provider = rng.choice(PROVIDERS)
    profile = rng.choice(PROFILES)
    premium, standard, economy = provider["models"]
    prices = {
        premium: round(rng.uniform(0.012, 0.020), 4),
        standard: round(rng.uniform(0.0025, 0.004), 4),
        economy: round(rng.uniform(0.0004, 0.0009), 4),
    }
    when = BASE_TIME + timedelta(days=rng.randint(0, 20), minutes=rng.randint(0, 59))
    spec = {
        "lab_id": lab_id,
        "seed": int(seed),
        "client": dict(client),
        "provider": {"name": provider["name"], "var": provider["var"]},
        "profile": profile,
        "models": [
            {"name": premium, "tier": "premium", "usd_per_1k_tokens": prices[premium]},
            {"name": standard, "tier": "standard", "usd_per_1k_tokens": prices[standard]},
            {"name": economy, "tier": "economy", "usd_per_1k_tokens": prices[economy]},
        ],
        "when": iso(when),
        "timezone": rng.choice(("America/Chicago", "America/Denver", "America/New_York")),
        "port": rng.choice((8642, 8643, 9119)),
        "faults": {"leak": lab_id == "lab.leak", "cost": lab_id == "lab.cost", "reboot": lab_id == "lab.reboot", "vault": lab_id == "lab.vault"},
        "calendar_secret": fake_secret(rng, "CAL-"),
    }
    if lab_id == "lab.leak":
        leaked = [{"var": provider["var"], "yaml_key": "api_key", "block": "provider", "value": fake_secret(rng), "label": "hermes-gateway", "key_id": f"key_{_hex(rng, 6)}"}]
        second = rng.random() < 0.5
        if second:
            bot_var = rng.choice(BOT_VARS)
            leaked.append({"var": bot_var, "yaml_key": "bot_token", "block": "messaging", "value": fake_secret(rng, "BOT-"), "label": "office-bot", "key_id": f"key_{_hex(rng, 6)}"})
        spec.update({
            "leak_file": rng.choice(("config.yaml", f"profiles/{profile}/config.yaml")),
            "leaked": leaked,
            "env_tracked": rng.random() < 0.5,
            "commit": _hex(rng, 7),
            "stranger_ip": f"203.0.113.{rng.randint(10, 240)}",
            "office_ip": f"198.51.100.{rng.randint(10, 240)}",
            "misuse_at": iso(when + timedelta(hours=rng.randint(3, 40))),
            "spike_requests": rng.randint(180, 420),
            "replacement_secrets": [fake_secret(rng, "NEW-") for _ in leaked],
        })
    if lab_id == "lab.cost":
        budget = rng.choice((90, 120, 150, 180))
        job = rng.choice(JOB_NAMES)
        schedule = rng.choice(("* * * * *", "*/1 * * * *", "0-59 * * * *", "* 6-20 * * *"))
        tokens = rng.randint(2400, 5200)
        spec.update({
            "budget_monthly": budget,
            "runaway_job": job,
            "runaway_schedule": schedule,
            "runaway_tokens": tokens,
            "runaway_model": premium,
            "runs_per_day": runs_per_firing_day(schedule),
            "cost_per_run": round(tokens / 1000 * prices[premium], 5),
            "budget_variant": rng.choice(("absent", "disabled")),
            "needed_by": rng.choice(("8:30", "9:00", "8:00")),
            "since_day": rng.randint(2, 4),
            "max_sane_runs": 4,
            "other_jobs": [
                {"name": "weekly-invoice-digest", "schedule": "0 8 * * 1", "model": standard, "tokens": rng.randint(3000, 6000)},
                {"name": "nightly-backup-check", "schedule": "15 3 * * *", "model": economy, "tokens": rng.randint(800, 1800)},
            ],
        })
        spec["daily_cost"] = round(spec["runs_per_day"] * spec["cost_per_run"], 2)
    if lab_id == "lab.vault":
        pair = rng.choice((("frontdesk", "bookkeeper"), ("office", "accounts"), ("reception", "billing")))
        desk_needs = ["mail:read", "calendar:read"]
        books_needs = rng.choice((["invoices:read"], ["invoices:read", "reports:read"]))
        spec["agents"] = [
            {"profile": pair[0], "role": "answers the front desk mailbox and keeps the calendar", "needs": desk_needs, "literal": False},
            {"profile": pair[1], "role": "reads invoices and prepares the weekly money summary", "needs": books_needs, "literal": rng.random() < 0.6},
        ]
        spec["profile"] = pair[0]
        spec["shared_secret"] = fake_secret(rng, "SHARED-")
        spec["shared_id"] = f"key_{_hex(rng, 6)}"
        spec["shared_scopes"] = ["mail:read", "mail:send", "calendar:read", "invoices:read", "reports:read", "admin", "billing"]
        spec["max_rotation_days"] = 90
        spec["new_secrets"] = [fake_secret(rng, "NEW-"), fake_secret(rng, "NEW-")]
        prefix = spec["provider"]["var"].replace("_API_KEY", "")
        spec["new_vars"] = [f"{prefix}_{pair[0].upper()}_KEY", f"{prefix}_{pair[1].upper()}_KEY"]
    if lab_id == "lab.reboot":
        secret_files = [".env", f"profiles/{profile}/auth.json"]
        if rng.random() < 0.5:
            secret_files.append(f"profiles/{profile}/memory.db")
        spec.update({
            "unit_fault": rng.choice(("no_install", "no_restart", "no_network")),
            "backup_fault": rng.choice(("wrong_path", "not_executable", "impossible_date")),
            "secret_files": secret_files,
            "last_good_backup": iso(when - timedelta(days=rng.randint(38, 70)))[:10],
            "power_cut": iso(when - timedelta(days=1, hours=3)),
            "backup_time": f"{rng.randint(1, 4)}:{rng.choice(('00', '15', '30', '45'))}",
        })
    return spec


# --------------------------------------------------------------- the files --


def _env_text(spec, extra):
    lines = [
        "# FAKE KEYS FOR A TRAINING LAB. Nothing in this file is real.",
        f"TZ={spec['timezone']}",
        f"GATEWAY_PORT={spec['port']}",
        f"CALENDAR_READONLY_TOKEN={spec['calendar_secret']}",
    ]
    lines += extra
    return "\n".join(lines) + "\n"


def _models_block(spec):
    lines = ["models:"]
    for model in spec["models"]:
        lines += [f"  {model['name']}:", f"    tier: {model['tier']}", f"    usd_per_1k_tokens: {model['usd_per_1k_tokens']}"]
    return lines


def _provider_block(spec, leaked_value=None, model=None):
    lines = ["provider:", f"  name: {spec['provider']['name']}", f"  model: {model or spec['models'][1]['name']}"]
    if leaked_value:
        lines.append(f"  api_key: {leaked_value}")
    else:
        lines.append(f"  api_key_env: {spec['provider']['var']}")
    return lines


def _files(spec) -> dict:
    """Every file in the lab as {relative path: (text, mode)}. Healthy except for the one hidden problem."""
    lab = spec["lab_id"]
    client, owner, ops = spec["client"]["name"], spec["client"]["owner"], spec["client"]["ops"]
    var = spec["provider"]["var"]
    profile = spec["profile"]
    files: dict = {}
    when = datetime.fromisoformat(spec["when"].replace("Z", "+00:00"))

    files[MARKER] = (
        "This folder is a training lab made by Field Academy.\n"
        "It imitates the files on a small client's computer so you can practise finding and fixing problems.\n"
        f"It stands in for {FAKE_ROOT}. Every key, address and person in it is made up.\n"
        "It is not a Hermes home. Hermes never reads it, and nothing in it runs.\n",
        0o644,
    )

    # --- config files
    leak = spec["faults"]["leak"]
    vault = spec["faults"]["vault"]
    root = [f"# Hermes settings for {client}", f"profile: {profile}", f"timezone: {spec['timezone']}"]
    profile_cfg = [f"# Profile settings for {profile}", f"persona: {client} front office helper", "memory:", "  enabled: true", "  keep_days: 90"]
    if leak:
        leaked = spec["leaked"]
        target = root if spec["leak_file"] == "config.yaml" else profile_cfg
        target.append(f"# last edited by {ops}")
        target += _provider_block(spec, leaked[0]["value"])
        if len(leaked) > 1:
            target += ["messaging:", "  platform: chat", f"  {leaked[1]['yaml_key']}: {leaked[1]['value']}"]
        if spec["leak_file"] != "config.yaml":
            root.append("# the provider and messaging settings live in the profile folder")
    elif not vault:
        root += _provider_block(spec)
    root += ["gateway:", "  host: 127.0.0.1", f"  port: {spec['port']}"]
    root += _models_block(spec)
    if spec["faults"]["cost"] and spec["budget_variant"] == "disabled":
        root += ["budget:", "  daily_usd_cap: 0", "  on_exceed: alert"]
    files["config.yaml"] = ("\n".join(root) + "\n", 0o644)
    if vault:
        for agent in spec["agents"]:
            cfg = [f"# Profile settings for {agent['profile']}", f"persona: {agent['role']}", "provider:", f"  name: {spec['provider']['name']}", f"  model: {spec['models'][1]['name']}"]
            cfg.append(f"  api_key: {spec['shared_secret']}" if agent["literal"] else f"  api_key_env: {spec['provider']['var']}")
            files[f"profiles/{agent['profile']}/config.yaml"] = ("\n".join(cfg) + "\n", 0o644)
    else:
        files[f"profiles/{profile}/config.yaml"] = ("\n".join(profile_cfg) + "\n", 0o644)

    # --- environment file
    extra = []
    if vault:
        extra.append(f"{var}={spec['shared_secret']}")
    elif not leak:
        extra.append(f"{var}={fake_secret(rng_for(lab, spec['seed']), 'ENV-')}")
    files[".env"] = (_env_text(spec, extra), 0o644 if spec["faults"]["reboot"] else 0o600)

    # --- profile files that hold secrets or memory
    auth_mode = 0o644 if spec["faults"]["reboot"] else 0o600
    files[f"profiles/{profile}/auth.json"] = (json.dumps({"profile": profile, "session_secret": "FAKE-SESSION-DO-NOT-USE-" + hashlib.sha256(str(spec["seed"]).encode()).hexdigest()[:20]}, indent=2) + "\n", auth_mode)
    memory_mode = 0o644 if spec["faults"]["reboot"] and f"profiles/{profile}/memory.db" in spec.get("secret_files", []) else 0o600
    files[f"profiles/{profile}/memory.db"] = (f"(binary stand-in for {client}'s saved notes)\n", memory_mode)

    # --- scheduled jobs
    jobs = [{"name": "weekly-invoice-digest", "schedule": "0 8 * * 1", "model": spec["models"][1]["name"], "tokens_per_run": 4200, "enabled": True, "prompt": "Read last week's invoices and list the ones still unpaid."},
            {"name": "nightly-backup-check", "schedule": "15 3 * * *", "model": spec["models"][2]["name"], "tokens_per_run": 1200, "enabled": True, "prompt": "Check that last night's backup file exists and say so in one line."}]
    if spec["faults"]["cost"]:
        jobs = [
            {"name": spec["runaway_job"], "schedule": spec["runaway_schedule"], "model": spec["runaway_model"], "tokens_per_run": spec["runaway_tokens"], "enabled": True,
             "prompt": f"Read the shared inbox and write a short summary for {owner} before the {spec['needed_by']} stand-up.", "deliver_to": f"{owner.split()[0].lower()}@{spec['client']['domain']}"},
        ] + [{"name": j["name"], "schedule": j["schedule"], "model": j["model"], "tokens_per_run": j["tokens"], "enabled": True, "prompt": "Routine job."} for j in spec["other_jobs"]]
    else:
        jobs.insert(0, {"name": "inbox-summary", "schedule": "30 7 * * 1-5", "model": spec["models"][2]["name"], "tokens_per_run": 2600, "enabled": True,
                        "prompt": f"Read the shared inbox and write a short summary for {owner}.", "deliver_to": f"{owner.split()[0].lower()}@{spec['client']['domain']}"})
    files["cron/jobs.json"] = (json.dumps({"jobs": jobs}, indent=2) + "\n", 0o644)

    # --- service, startup and backup
    unit = [
        "[Unit]",
        "Description=Hermes gateway for the front office",
        "After=network-online.target",
        "Wants=network-online.target",
        "",
        "[Service]",
        f"ExecStart={FAKE_ROOT}/bin/hermes-gateway --profile {profile}",
        f"EnvironmentFile={FAKE_ROOT}/.env",
        "Restart=on-failure",
        "RestartSec=5",
        "",
        "[Install]",
        "WantedBy=multi-user.target",
    ]
    enabled = ["multi-user units enabled on this machine:", "cups.service", "ssh.service", "cron.service", "hermes-gateway.service"]
    if spec["faults"]["reboot"]:
        fault = spec["unit_fault"]
        if fault == "no_install":
            unit = unit[:-2]
        elif fault == "no_restart":
            unit = [("Restart=no" if line.startswith("Restart=") else line) for line in unit]
        elif fault == "no_network":
            unit = [line for line in unit if not line.startswith(("After=", "Wants="))]
        enabled = [line for line in enabled if line != "hermes-gateway.service"]
    files["systemd/hermes-gateway.service"] = ("\n".join(unit) + "\n", 0o644)
    files["systemd/enabled-units.txt"] = ("\n".join(enabled) + "\n", 0o644)

    script = (
        "#!/bin/sh\n"
        "# Nightly copy of the settings and the profile, kept for 14 days.\n"
        "set -eu\n"
        f"cd {FAKE_ROOT}\n"
        "stamp=$(date +%Y-%m-%d)\n"
        "mkdir -p backups\n"
        f"tar -czf backups/hermes-$stamp.tar.gz config.yaml cron profiles/{profile}\n"
        "find backups -name 'hermes-*.tar.gz' -mtime +14 -delete\n"
        "echo \"backup ok $stamp\"\n"
    )
    script_mode = 0o755
    # Linux and macOS mark a script runnable with its mode, so cron can start it by its path alone. Windows has no
    # such mark: a scheduler there starts a script by naming the program that reads it, as Hermes runs a .sh with
    # bash. So on Windows the healthy line names /bin/sh, and the "cannot run" fault is a line that leaves it out.
    runner = "" if POSIX_MODES else "/bin/sh "
    cron_line = f"30 2 * * * {runner}{FAKE_ROOT}/scripts/backup.sh >> {FAKE_ROOT}/logs/backup.log 2>&1"
    if spec["faults"]["reboot"]:
        bt = spec["backup_time"].split(":")
        minute, hour = bt[1], bt[0]
        cron_line = f"{minute} {hour} * * * {runner}{FAKE_ROOT}/scripts/backup.sh >> {FAKE_ROOT}/logs/backup.log 2>&1"
        if spec["backup_fault"] == "wrong_path":
            cron_line = cron_line.replace(f"{FAKE_ROOT}/scripts/backup.sh", "/opt/hermes/backup.sh")
        elif spec["backup_fault"] == "impossible_date":
            cron_line = f"{minute} {hour} 31 2 * {runner}{FAKE_ROOT}/scripts/backup.sh >> {FAKE_ROOT}/logs/backup.log 2>&1"
        elif spec["backup_fault"] == "not_executable":
            script_mode = 0o644
            cron_line = cron_line.replace(runner + FAKE_ROOT, FAKE_ROOT)
    files["scripts/backup.sh"] = (script, script_mode)
    files["crontab.txt"] = ("# minute hour day month weekday command\n" + cron_line + "\n", 0o644)

    # --- ignore list and tracked files
    gitignore = ["*.log", "__pycache__/"]
    tracked = [".gitignore", "config.yaml", "cron/jobs.json", f"profiles/{profile}/config.yaml", "scripts/backup.sh", "systemd/hermes-gateway.service", "crontab.txt"]
    if vault:
        tracked = [t for t in tracked if t != f"profiles/{profile}/config.yaml"] + [f"profiles/{a['profile']}/config.yaml" for a in spec["agents"]]
    if leak and spec["env_tracked"]:
        tracked.append(".env")
    elif not leak:
        gitignore.append(".env")
    files[".gitignore"] = ("\n".join(gitignore) + "\n", 0o644)
    files["tracked-files.txt"] = ("# Files in the shared backup repository. This list stands in for the output of: git ls-files\n" + "\n".join(sorted(tracked)) + "\n", 0o644)

    # --- provider console
    keys = [{"id": f"key_{_hex(rng_for(lab, spec['seed'] + 7), 6)}", "label": "laptop-test", "status": "revoked", "created": "2026-02-11", "last_used": "2026-03-02T10:00:00Z"}]
    if vault:
        keys.append({"id": spec["shared_id"], "label": "hermes-shared", "status": "active", "created": "2026-04-20", "scopes": spec["shared_scopes"], "last4": spec["shared_secret"][-4:], "used_by": [a["profile"] for a in spec["agents"]], "last_used": iso(when)})
    elif leak:
        for item in spec["leaked"]:
            keys.append({"id": item["key_id"], "label": item["label"], "status": "active", "created": "2026-05-02", "last4": item["value"][-4:], "last_used": iso(when + timedelta(hours=1))})
    else:
        keys.append({"id": "key_" + _hex(rng_for(lab, spec["seed"] + 9), 6), "label": "hermes-gateway", "status": "active", "created": "2026-05-02", "last_used": iso(when)})
    files["provider-console/keys.json"] = (json.dumps({"provider": spec["provider"]["name"], "keys": keys}, indent=2) + "\n", 0o644)
    files["provider-console/HOW-THE-CONSOLE-WORKS.txt"] = (
        f"This file stands in for the {spec['provider']['name']} website, where keys are made and switched off.\n"
        "To rotate a key here: change the old key's status to revoked, then add a new entry with the same label,\n"
        'status "active", and a "secret" holding the new key. Use a made-up value that starts with FAKE-.\n'
        'A key can carry "scopes", the list of things it is allowed to do. Give a key only the scopes its one job needs.\n'
        "The real website shows a new secret once, when it is made, and never again.\n",
        0o644,
    )

    # --- logs and evidence, filled in per lab
    _evidence(spec, files, when)
    files["README-CLIENT.txt"] = (_client_note(spec), 0o644)
    return files


def _client_note(spec) -> str:
    """The client's note with its paragraphs on single lines, so it wraps to whatever width it is shown at."""
    head, _, body = _client_note_raw(spec).partition("\n\n")
    return head + "\n\n" + re.sub(r"(?<=\S)\n(?=\S)", " ", body)


def _client_note_raw(spec) -> str:
    lab, client, owner, ops = spec["lab_id"], spec["client"]["name"], spec["client"]["owner"], spec["client"]["ops"]
    top = f"From: {ops}, {client}\nTo: you\n\n"
    tail = f"\nThis folder stands in for {FAKE_ROOT} on their office computer. Look around, fix what is wrong, and write down what happened.\nEvery key in here is made up.\n"
    if lab == "lab.leak":
        return top + (
            f"Hi. The company that runs our AI account sent us an alert about strange traffic on our key. {owner} is the owner and wants to hear from you that it is\n"
            "fixed, and wants it written down, because the insurance form asks. I do not know how it got out. Please find out, make it safe,\n"
            "and tell me what to do so it does not happen again.\n" + tail
        )
    if lab == "lab.cost":
        return top + (
            f"Hi. Our AI bill jumped in the last few days and {owner} is not happy. We budget ${spec['budget_monthly']} a month for Hermes.\n"
            f"The one job we really need is a summary of the shared inbox before the {spec['needed_by']} stand-up on weekdays. Everything else is nice to have.\n"
            "Please find out why the bill jumped and stop it from happening again, without breaking the summary.\n" + tail
        )
    if lab == "lab.vault":
        a, b = spec["agents"]
        return top + (
            f"Hi. We run two helpers: {a['profile']} {a['role']}, and {b['profile']} {b['role']}. A consultant set them up quickly and they share one key.\n"
            f"{owner} read that this is a bad idea and wants it done properly. I do not know what a proper setup looks like. Please sort it out and leave us a note\n"
            "saying who owns each key and when it gets changed.\n" + tail
        )
    return top + (
        f"Hi. We had a power cut on {spec['power_cut'][:10]} and Hermes stayed off until someone noticed two days later.\n"
        "Separately, our accountant said the file with our keys looks open to everyone on the computer, and our IT contact asked me when the last backup ran. I could not tell him.\n"
        "Please make sure it comes back by itself after a power cut, that our keys are locked down, and that the backup really runs. Then tell me how I know.\n" + tail
    )


def _line_of(files, value):
    for text, _ in files.values():
        for number, line in enumerate(text.splitlines(), start=1):
            if value in line:
                return number
    return 0


def _evidence(spec, files, when):
    lab = spec["lab_id"]
    gateway = []
    t = when
    for step in range(6):
        t += timedelta(minutes=47 + step)
        gateway.append(f"{iso(t)} gateway info  profile={spec['profile']} heartbeat ok")
    files["logs/gateway.log"] = ("\n".join(gateway) + "\n", 0o644)
    if lab == "lab.leak":
        lines = [
            f"{iso(when)} provider-notice  key={spec['leaked'][0]['key_id']} label={spec['leaked'][0]['label']} last_seen_ip={spec['office_ip']} (office)",
            f"{spec['misuse_at']} provider-notice  key={spec['leaked'][0]['key_id']} request from {spec['stranger_ip']} (not seen before) count=41",
            f"{iso(datetime.fromisoformat(spec['misuse_at'].replace('Z', '+00:00')) + timedelta(hours=1))} provider-notice  usage_spike key={spec['leaked'][0]['key_id']} requests_last_hour={spec['spike_requests']} normal=6",
            f"{iso(when + timedelta(days=1))} repo-scan  a secret-shaped value was found in commit {spec['commit']}, line {_line_of(files, spec['leaked'][0]['value'])}. It is still in the repository.",
        ]
        if len(spec["leaked"]) > 1:
            lines.append(f"{iso(when + timedelta(days=1))} repo-scan  a second secret-shaped value was found in the same commit. The key id on the console is {spec['leaked'][1]['key_id']}.")
        files["logs/audit.log"] = ("\n".join(lines) + "\n", 0o644)
    elif lab == "lab.cost":
        start = datetime(when.year, when.month, when.day, 0, 0, tzinfo=timezone.utc) - timedelta(days=1)
        rows = []
        runs = spec["runs_per_day"]
        cost = spec["cost_per_run"]
        tokens = spec["runaway_tokens"]
        for minute in range(0, 100):
            moment = start + timedelta(hours=20, minutes=minute)
            rows.append(f"{iso(moment)} cron job={spec['runaway_job']} model={spec['runaway_model']} tokens={tokens} cost_usd={cost:.4f} status=ok")
        rows.append("... (the rest of the day is cut here to save space)")
        for back in (2, 1):
            day = (start - timedelta(days=back - 1)).strftime("%Y-%m-%d")
            rows.append(f"{day}T23:59:59Z daily_total job={spec['runaway_job']} runs={runs} cost_usd={runs * cost:.2f}")
        rows.append(f"{iso(start - timedelta(days=spec['since_day']))} config   cron/jobs.json changed by {spec['client']['ops']}: schedule edited for {spec['runaway_job']}")
        files["logs/agent.log"] = ("\n".join(rows) + "\n", 0o644)
        csv = ["date,job,model,runs,cost_usd"]
        for back in range(7, 0, -1):
            day = (start - timedelta(days=back - 1))
            heavy = back <= spec["since_day"]
            r = runs if heavy else 1
            csv.append(f"{day.strftime('%Y-%m-%d')},{spec['runaway_job']},{spec['runaway_model']},{r},{r * cost:.2f}")
        files["provider-console/usage-export.csv"] = ("\n".join(csv) + "\n", 0o644)
    elif lab == "lab.vault":
        lines = [
            f"{iso(when)} provider-notice  key={spec['shared_id']} label=hermes-shared scopes={len(spec['shared_scopes'])} used_by={','.join(a['profile'] for a in spec['agents'])}",
            f"{iso(when + timedelta(hours=2))} provider-notice  key={spec['shared_id']} admin action: created a billing contact (called by profile {spec['agents'][1]['profile']})",
            f"{iso(when + timedelta(hours=3))} provider-notice  key={spec['shared_id']} no rotation on record since 2026-04-20",
        ]
        files["logs/audit.log"] = ("\n".join(lines) + "\n", 0o644)
    else:
        boot = [
            f"{spec['power_cut']} kernel   power loss detected, unclean shutdown",
            f"{iso(datetime.fromisoformat(spec['power_cut'].replace('Z', '+00:00')) + timedelta(minutes=19))} kernel   boot",
            "boot   cron.service started",
            "boot   ssh.service started",
            "boot   hermes-gateway.service: not started. It is not enabled for boot." if spec["unit_fault"] != "no_restart" else "boot   hermes-gateway.service: not started. It is not enabled for boot.",
        ]
        files["logs/boot.log"] = ("\n".join(boot) + "\n", 0o644)
        files["logs/backup.log"] = (f"{spec['last_good_backup']} 02:30:04 backup ok {spec['last_good_backup']}\n(no later entries)\n", 0o644)
        files["backups/" + f"hermes-{spec['last_good_backup']}.tar.gz"] = ("(stand-in for an old backup file)\n", 0o644)


# ------------------------------------------------------------- build / read --


class LabError(ValueError):
    pass


def _looks_like_hermes_home(folder: Path) -> bool:
    return any((folder / name).exists() for name in ("config.yaml", ".env", "cron", "profiles", "skills"))


def safe_labs_dir(data_dir) -> Path:
    """The folder labs live in, checked. Refuses a data folder that looks like a Hermes home."""
    base = Path(data_dir).expanduser().resolve()
    home_env = os.environ.get("HERMES_HOME")
    real_home = Path(home_env).expanduser().resolve() if home_env else (Path.home() / ".hermes").resolve()
    if base == real_home:
        raise LabError("Labs are never built inside the Hermes home itself.")
    if _looks_like_hermes_home(base):
        raise LabError("That data folder looks like a Hermes home (it holds a config.yaml, a .env, a cron or a profiles folder), so no lab is built there.")
    return base / "labs"


def lab_root(data_dir, lab_id: str, seed: int) -> Path:
    if lab_id not in LAB_IDS:
        raise LabError(f"Unknown lab: {lab_id}")
    return safe_labs_dir(data_dir) / f"{lab_id.split('.')[1]}-{int(seed)}" / "client-machine"


def build_lab(lab_id: str, seed: int, data_dir) -> dict:
    """Write the lab folder, or return what is already there. Never overwrites the learner's work."""
    root = lab_root(data_dir, lab_id, seed)
    spec = spec_for(lab_id, seed)
    if root.exists() and (root / MARKER).exists():
        return manifest(spec, root)
    if root.exists():
        raise LabError("A folder already sits where this lab would go, and it is not a lab. Nothing was changed.")
    root.parent.mkdir(parents=True, exist_ok=True)
    if not fileaccess.keeps_access_lists(root.parent):
        raise LabError("This drive keeps no access lists (it may be a USB stick or a FAT32 or exFAT drive), so no file on it can be made private. Move Field Academy's data to your main drive.")
    # Windows: every account on this computer may read the lab folder, as a folder at the top of a drive allows,
    # so the files start the way the mode bits below leave them on Linux and macOS. Never through a junction or link.
    try:
        fileaccess.make_shared_folder(root)
    except FileExistsError:
        raise LabError("A folder already sits where this lab would go, and it is not a lab. Nothing was changed.")
    except OSError as exc:
        raise LabError(f"The lab folder could not be made: {exc}. Nothing was changed.")
    for rel, (text, mode) in _files(spec).items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exact bytes, LF: these stand in for a Linux server's files, and text mode would write CRLF on Windows.
        target.write_bytes(text.encode("utf-8"))
        if POSIX_MODES:
            os.chmod(target, mode)
        elif not mode & 0o077:
            fileaccess.make_private(target)
    return manifest(spec, root)


def reset_lab(lab_id: str, seed: int, data_dir) -> bool:
    """Delete one lab folder, only if it carries the lab marker. Returns True when something was removed."""
    root = lab_root(data_dir, lab_id, seed)
    if not root.exists():
        return False
    if not (root / MARKER).exists():
        raise LabError("That folder is not a lab, so it was left alone.")
    shutil.rmtree(root.parent)
    return True


# Windows has no POSIX permission bits (Python reports 0o666 or 0o444 whatever chmod was asked for). There a file's
# lock is its access list, so fingerprints and the changed-files list record whether each file is private instead.
POSIX_MODES = os.name != "nt"


def _access_now(path: Path) -> bytes:
    if POSIX_MODES:
        return oct(path.stat().st_mode & 0o777).encode()
    return b"private" if fileaccess.is_private(path) else b"shared"


def _access_built(mode: int) -> bytes:
    if POSIX_MODES:
        return oct(mode & 0o777).encode()
    return b"shared" if mode & 0o077 else b"private"


def listing(root: Path) -> list:
    """Every file under root, as forward-slash paths relative to it, the same on every platform."""
    return sorted(
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    )


def tree_fingerprint(root: Path) -> str:
    """One SHA-256 over every file's path, who may read it and its contents. Changes when any file or any permission changes."""
    digest = hashlib.sha256()
    for rel in listing(Path(root)):
        path = Path(root) / rel
        digest.update(rel.encode("utf-8") + b"\0")
        digest.update(_access_now(path) + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def read(root: Path, rel: str) -> str:
    path = Path(root) / rel
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def manifest(spec: dict, root: Path) -> dict:
    """What the learner may see: the folder, the client's note and the symptoms. Never the hidden facts."""
    lab = spec["lab_id"]
    symptoms = {
        "lab.leak": ["The provider says traffic from an address nobody recognises used the key.", "The shared backup repository holds the whole configuration.", "The owner needs it written down."],
        "lab.cost": ["The bill rose sharply in a few days.", "One job still has to run each weekday morning.", "The monthly budget is fixed."],
        "lab.reboot": ["Hermes stayed off after a power cut.", "The file with the keys looks open to anyone on the computer.", "Nobody can say when the last backup ran."],
        "lab.vault": ["Two helpers share one key.", "The provider log shows the key doing things neither helper was set up to do.", "Nobody has changed the key since it was made."],
    }[lab]
    handin = {
        "lab.leak": ["Repair the files in the folder.", "Write INCIDENT.md in the folder: what leaked, when, who was told, what you changed and how it is prevented.", "Write your diagnosis below in your own words."],
        "lab.cost": ["Repair the files in the folder.", "Write your diagnosis below in your own words, with the daily cost you found."],
        "lab.vault": ["Repair the files in the folder.", "Write ROTATION.md in the folder: each key, who owns it, how often it changes and what to do first if one leaks.", "Write your diagnosis below in your own words."],
        "lab.reboot": ["Repair the files in the folder.", "Write RESTORE-TEST.md in the folder: the day you tested a restore and what came back.", "Write your diagnosis below in your own words."],
    }[lab]
    return {
        "lab_id": lab,
        "title": TITLES[lab],
        "seed": spec["seed"],
        "minutes": MINUTES[lab],
        "path": str(root),
        "files": listing(Path(root)),
        "client": spec["client"]["name"],
        "note": _client_note(spec),
        "symptoms": symptoms,
        "hand_in": handin,
        "fake_root": FAKE_ROOT,
    }


def pristine_files(lab_id: str, seed: int) -> dict:
    """What the folder looked like when it was built: {relative path: (text, mode)}. Used to tell what the learner changed."""
    return _files(spec_for(lab_id, seed))


def pristine_fingerprint(lab_id: str, seed: int) -> str:
    digest = hashlib.sha256()
    for rel, (text, mode) in sorted(pristine_files(lab_id, seed).items()):
        digest.update(rel.encode("utf-8") + b"\0")
        digest.update(_access_built(mode) + b"\0")
        digest.update(hashlib.sha256(text.encode("utf-8")).digest())
    return digest.hexdigest()


def changed_files(lab_id: str, seed: int, root) -> list:
    """The files the learner touched, as {path, change}. Names only, never contents."""
    root = Path(root)
    before = pristine_files(lab_id, seed)
    now = set(listing(root))
    out = []
    for rel in sorted(set(before) | now):
        if rel not in now:
            out.append({"path": rel, "change": "removed"})
        elif rel not in before:
            out.append({"path": rel, "change": "added"})
        else:
            text, mode = before[rel]
            path = root / rel
            if path.read_text(encoding="utf-8") != text:
                out.append({"path": rel, "change": "edited"})
            elif _access_now(path) != _access_built(mode):
                out.append({"path": rel, "change": "permissions"})
    return out
