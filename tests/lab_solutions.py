"""Reference repairs for each lab, written the way a careful learner would, for the tests and the screenshot harness.

These live under tests/ on purpose. They hold the answers, so they never ship
in the plugin's own modules and the lab folder never contains them. Each takes
the lab's spec (from labs.spec_for) and the folder, repairs the files, and
returns the diagnosis text a learner would write.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from file_access import ON_WINDOWS, lock


def _write(root, rel, text, mode=None):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if mode == 0o600:
        lock(path)
    elif mode is not None:
        os.chmod(path, mode)


def _read(root, rel):
    return (Path(root) / rel).read_text(encoding="utf-8")


def solve_leak(spec, root, *, skip=()):
    cfg = _read(root, spec["leak_file"])
    for item in spec["leaked"]:
        cfg = cfg.replace(f"{item['yaml_key']}: {item['value']}", f"{item['yaml_key']}_env: {item['var']}")
    _write(root, spec["leak_file"], cfg)
    env = _read(root, ".env").rstrip("\n").splitlines()
    console = json.loads(_read(root, "provider-console/keys.json"))
    for item, new in zip(spec["leaked"], spec["replacement_secrets"]):
        env.append(f"{item['var']}={new}")
        for key in console["keys"]:
            if key["id"] == item["key_id"]:
                key["status"] = "revoked"
        console["keys"].append({"id": "key_" + new[-6:].lower(), "label": item["label"], "status": "active", "created": "2026-10-01", "secret": new})
    _write(root, ".env", "\n".join(env) + "\n", 0o600)
    if "console" not in skip:
        _write(root, "provider-console/keys.json", json.dumps(console, indent=2) + "\n")
    ignore = _read(root, ".gitignore").splitlines()
    if ".env" not in ignore:
        ignore.append(".env")
    _write(root, ".gitignore", "\n".join(ignore) + "\n")
    tracked = [line for line in _read(root, "tracked-files.txt").splitlines() if line.strip() != ".env"]
    _write(root, "tracked-files.txt", "\n".join(tracked) + "\n")
    ids = " and ".join(i["key_id"] for i in spec["leaked"])
    owner = spec["client"]["owner"]
    _write(
        root,
        "INCIDENT.md",
        f"What: the key {ids} was written in {spec['leak_file']} and saved to the shared repository.\n"
        f"When: first misused on {spec['misuse_at'][:10]} from an address nobody recognised ({spec['stranger_ip']}).\n"
        f"Told: {owner}, the owner, the same day.\n"
        "Changed: I revoked the old key on the console, made a new one and moved it to .env.\n"
        "Prevented: keys live only in .env, which is on the ignore list. Settings files name the variable.\n",
    )
    base = os.path.basename(spec["leak_file"])
    return (
        f"The key was written straight into {base}, which is saved to the shared repository (commit {spec['commit']}). "
        f"The provider log shows traffic from {spec['stranger_ip']}, an address not seen before, and a spike in requests. "
        "I revoked the old key and made a new one, put the new key in .env and pointed the settings at the variable name. "
        ".env is now on the ignore list and off the saved list, so the next key stays out of the repository."
    )


def solve_cost(spec, root, *, keep_premium=False, skip=()):
    jobs = json.loads(_read(root, "cron/jobs.json"))
    economy = spec["models"][2]["name"]
    for job in jobs["jobs"]:
        if job["name"] == spec["runaway_job"]:
            job["schedule"] = "30 7 * * 1-5"
            if not keep_premium:
                job["model"] = economy
    _write(root, "cron/jobs.json", json.dumps(jobs, indent=2) + "\n")
    cfg = _read(root, "config.yaml")
    cfg = re.sub(r"budget:\n  daily_usd_cap: 0\n  on_exceed: alert\n", "", cfg)
    if "cap" not in skip:
        cap = round(spec["budget_monthly"] / 30, 2)
        cfg += f"budget:\n  daily_usd_cap: {cap}\n  on_exceed: pause\n"
    _write(root, "config.yaml", cfg)
    return (
        f"The {spec['runaway_job']} job was scheduled to run every minute, so {spec['runs_per_day']} runs a day at about "
        f"${spec['cost_per_run']:.3f} each, which is roughly ${spec['daily_cost']:.2f} a day. I changed it to run once at 7:30 on weekdays, "
        "moved it to the cheaper model, left its prompt and recipient alone, and added a daily cap that pauses the jobs so a mistake stops itself."
    )


def solve_reboot(spec, root, *, skip=()):
    profile = spec["profile"]
    unit = (
        "[Unit]\nDescription=Hermes gateway for the front office\nAfter=network-online.target\nWants=network-online.target\n\n"
        f"[Service]\nExecStart=/srv/hermes-client/bin/hermes-gateway --profile {profile}\nEnvironmentFile=/srv/hermes-client/.env\n"
        "Restart=on-failure\nRestartSec=5\n\n[Install]\nWantedBy=multi-user.target\n"
    )
    _write(root, "systemd/hermes-gateway.service", unit)
    enabled = _read(root, "systemd/enabled-units.txt").splitlines()
    if "hermes-gateway.service" not in enabled:
        enabled.append("hermes-gateway.service")
    _write(root, "systemd/enabled-units.txt", "\n".join(enabled) + "\n")
    if "perms" not in skip:
        for rel in spec["secret_files"]:
            lock(Path(root) / rel)
    minute, hour = spec["backup_time"].split(":")[1], spec["backup_time"].split(":")[0]
    # Linux and macOS: mark the script runnable. Windows has no such mark, so the line names the program that runs it.
    runner = "/bin/sh " if ON_WINDOWS else ""
    _write(root, "crontab.txt", f"# minute hour day month weekday command\n{minute} {hour} * * * {runner}/srv/hermes-client/scripts/backup.sh >> /srv/hermes-client/logs/backup.log 2>&1\n")
    if not ON_WINDOWS:
        os.chmod(Path(root) / "scripts/backup.sh", 0o755)
    _write(
        root,
        "RESTORE-TEST.md",
        f"Tested on 2026-10-03. Restored 3 files from hermes-{spec['last_good_backup']}.tar.gz into a scratch folder. All of them opened.\n",
    )
    return (
        "The gateway service was never enabled to start at boot, so after the power cut Hermes stayed off. I fixed the service file and added it to the enabled list. "
        + ("The key files' access lists let every account on the computer read them, so I locked them to my account with icacls. The backup never ran because its schedule line was wrong, so I corrected the path and the schedule and named the program that runs the script. "
           if ON_WINDOWS else
           "The key files were readable by every user, so I set their permissions to 600. The backup never ran because its schedule line was wrong, so I corrected the path and the schedule and made the script runnable. ")
        + "To show it works I did a restore test and wrote it down."
    )


def solve_vault(spec, root, *, skip=()):
    agents = spec["agents"]
    console = json.loads(_read(root, "provider-console/keys.json"))
    names = []
    for index, agent in enumerate(agents):
        var = spec["new_vars"][index]
        names.append(var)
        _write(
            root,
            f"profiles/{agent['profile']}/config.yaml",
            f"# Profile settings for {agent['profile']}\npersona: {agent['role']}\nprovider:\n  name: {spec['provider']['name']}\n  model: {spec['models'][1]['name']}\n  api_key_env: {var}\n",
        )
        _write(root, f"profiles/{agent['profile']}/.env", f"{var}={spec['new_secrets'][index]}\n", None if "perms" in skip else 0o600)
        console["keys"].append(
            {"id": f"key_{agent['profile'][:4]}", "label": agent["profile"], "status": "active", "secret": spec["new_secrets"][index], "scopes": list(agent["needs"])}
        )
    for key in console["keys"]:
        if key["id"] == spec["shared_id"]:
            key["status"] = "revoked"
    _write(root, "provider-console/keys.json", json.dumps(console, indent=2) + "\n")
    owner = spec["client"]["owner"]
    lines = [f"- {var}: owner {owner}, changes every 60 days." for var in names]
    _write(root, "ROTATION.md", "Keys and who owns them\n" + "\n".join(lines) + "\nIf a key leaks, switch it off on the console first, then make a new one.\n")
    return (
        "Both helpers shared one key that could do everything, including admin and billing. I made one key per helper with only the scopes its job needs, "
        "gave each its own .env and its own variable, and removed the key that was written into a settings file. The old shared key is revoked. "
        "ROTATION.md says the owner changes each key every 60 days."
    )


SOLVERS = {"lab.leak": solve_leak, "lab.cost": solve_cost, "lab.reboot": solve_reboot, "lab.vault": solve_vault}
