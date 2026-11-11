"""Setups and planted problems for the Intermediate core missions (School of Hermes, level 2): a planter, a detector
and a fix-verifier per kind. Same rules as plants.py and plants_b.py: writes go only through practice_write.py, into
a recorded practice profile nobody has chatted in yet; names and numbers vary by the learner's seed; details stay
hidden until Compare.

Setups (``lab.setup``):

* ``delegation`` (f.delegation): three client folders under ``clients/`` in the practice folder, each with one notes
  file holding that client's own budget figure, and one house rule saved in memory. Helpers start with no memory and
  no context files (tools/delegate_tool.py: ``skip_context_files=True, skip_memory=True``), so the rule reaches them
  only if the request passes it on.
* ``toolsets`` (f.toolsets): three meeting notes in the practice folder; every toolset left as Hermes ships it.

Kinds: ``one_helper`` and ``helper_model_typo`` (f.delegation); ``wide_connector`` (f.toolsets).
"""

from __future__ import annotations

from pathlib import Path

from . import hermes_read, hermes_read_b, plants_b, practice_write, yaml_keys

CLIENTS = (("harbor-dental", "Harbor Dental"), ("quill-books", "Quill & Co Books"), ("ridgeway-farm", "Ridgeway Farm"),
           ("solace-yoga", "Solace Yoga"), ("tandem-cycles", "Tandem Cycles"), ("vale-bakery", "Vale Street Bakery"),
           ("north-pier", "North Pier Cafe"), ("brightwork", "Brightwork Cleaners"))
ISSUES = ("the website booking form sends no confirmation", "two invoices were paid twice in September",
          "the spring newsletter went to an old list", "a supplier wants a new contract signed by Friday",
          "the shop's reviews dropped after a delivery mix-up", "nobody owns the shared calendar")
OWNERS = ("Priya", "Tomasz", "Adaeze", "Mateo", "Ingrid", "Kofi")

TITLES = {
    "one_helper": "Hermes could run only one helper at a time",
    "helper_model_typo": "Helpers were set to a model that doesn't exist",
    "wide_connector": "A connector could reach Hermes's own settings and memory",
}


def _tree(home):
    found = hermes_read._read_text(home, "config.yaml")
    return (yaml_keys.parse(found[0]), found) if found is not None else (None, None)


def delegation_settings(home) -> dict:
    """The helper settings these missions read: how many run at once and which model they use."""
    tree, found = _tree(home)
    if tree is None:
        return hermes_read.unreadable("No config.yaml in the practice profile.")
    raw = yaml_keys.get(tree, "delegation.max_concurrent_children")
    model = yaml_keys.get(tree, "delegation.model")
    return {"readable": True, "mtime": found[2],
            "max_children": raw if isinstance(raw, int) and not isinstance(raw, bool) else None,
            "max_children_raw": raw if isinstance(raw, (int, str)) and not isinstance(raw, bool) else None,
            "model": model.strip() if isinstance(model, str) and not isinstance(model, yaml_keys.Text) else ""}


# ------------------------------------------------------------------ setups --


def budget_line(amount: int) -> str:
    return f"${amount:,}"


def _setup_delegation(ctx) -> dict:
    home, row, rng = ctx["home"], ctx["row"], ctx["rng"]
    folder = practice_write.ensure_practice_folder(home, row)
    picked = rng.sample(CLIENTS, 3)
    issues = rng.sample(ISSUES, 3)
    budgets = rng.sample(range(3, 40), 3)
    owner = rng.choice(OWNERS)
    clients = {}
    for (slug, name), issue, k in zip(picked, issues, budgets):
        amount = k * 250
        text = (f"Client: {name}\nQuarter budget: {budget_line(amount)}\nOpen issue: {issue}\n"
                f"Last call: {rng.choice(('Monday', 'Tuesday', 'Wednesday', 'Thursday'))}, notes taken by the office.\n")
        practice_write.write_practice_file(home, row, f"clients/{slug}/notes.txt", text)
        clients[slug] = {"name": name, "budget": budget_line(amount), "issue": issue}
    rule = f"Checked by: {owner}"
    practice_write.write_memory(home, row, "memory", [
        f"House rule for client summaries: every summary.md ends with the line \"{rule}\".",
        "Client folders live in the practice folder under clients/, one folder per client.",
    ])
    return {"folder": folder, "clients": clients, "rule_line": rule, "owner": owner}


MEETINGS = (("kitchen-refit", "Kitchen refit", "the tiler can start on the 14th"),
            ("van-lease", "Van lease", "the lease ends in March and the dealer offered two quotes"),
            ("summer-hires", "Summer hires", "two students start in June, both need keys"),
            ("rent-review", "Rent review", "the landlord proposed a 4 percent rise"),
            ("stock-count", "Stock count", "the October count was 31 items short"),
            ("website", "Website", "the booking page is slow on phones"))


def _setup_toolsets(ctx) -> dict:
    home, row, rng = ctx["home"], ctx["row"], ctx["rng"]
    folder = practice_write.ensure_practice_folder(home, row)
    notes = {}
    for slug, title, point in rng.sample(MEETINGS, 3):
        practice_write.write_practice_file(home, row, f"meetings/{slug}.txt", f"Meeting: {title}\nDecided: {point}.\n")
        notes[slug] = {"title": title, "point": point}
    return {"folder": folder, "notes": notes}


SETUPS = {"delegation": _setup_delegation, "toolsets": _setup_toolsets}


# -------------------------------------------------------------- delegation --


def _plant_one_helper(ctx) -> dict:
    practice_write.set_config(ctx["home"], ctx["row"], {"delegation.max_concurrent_children": 1})
    return {"max_children": 1}


TOO_MANY = "Too many tasks:"


def refusals(home) -> list:
    """Tool results in the profile's chats where a batch of helpers was refused for being too many."""
    found = hermes_read.messages(home)
    return [m for m in found.get("messages", []) if found.get("readable") and m.get("role") == "tool"
            and TOO_MANY in str(m.get("content") or "")]


def _detect_one_helper(home, details) -> dict:
    found = delegation_settings(home)
    refused = refusals(home)
    return {"fired": bool(refused),
            "facts": [{"label": "Helpers allowed at once", "value": str(found.get("max_children") or "10 (Hermes's default)")},
                      {"label": "Batches refused as too many", "value": str(len(refused))}],
            "evidence": [("tool_result", "state.db", str(m.get("content") or "")[:200]) for m in refused[:1]]}


def _verify_one_helper(home, details, fact="", note=None) -> dict:
    found = delegation_settings(home)
    if not found.get("readable"):
        return {"fixed": False, "why": "The practice profile's settings couldn't be read."}
    raw = found.get("max_children_raw")
    if raw is None:
        return {"fixed": True, "why": "delegation.max_concurrent_children is gone, so Hermes's default of 10 applies."}
    if isinstance(raw, int) and raw >= 3:
        return {"fixed": True, "why": f"Hermes may run {raw} helpers at once, enough for the three clients."}
    return {"fixed": False, "why": f"delegation.max_concurrent_children is {raw}, so a batch of three helpers is refused."}


def _plant_helper_model_typo(ctx) -> dict:
    found = hermes_read_b.settings(ctx["home"])
    model = found.get("model") if found.get("readable") else None
    if not model:
        raise ValueError("The practice profile has no main model set under model.default, so the helper model can't be "
                         "planted. Pick a model for your own profile, then reset the practice profile.")
    broken = plants_b.typo(model, ctx["rng"])
    practice_write.set_config(ctx["home"], ctx["row"], {"delegation.model": broken})
    return {"model": model, "typo": broken}


def helper_sessions(home) -> list:
    found = hermes_read.sessions(home)
    return [s for s in found.get("sessions", []) if found.get("readable") and s.get("source") == "subagent"]


def _detect_helper_model_typo(home, details) -> dict:
    ran = [s for s in helper_sessions(home) if s.get("model") == details.get("typo")]
    return {"fired": bool(ran),
            "facts": [{"label": "Helper model in the settings", "value": delegation_settings(home).get("model") or "same as the main model"},
                      {"label": "Helper chats on the misspelled model", "value": str(len(ran))}],
            "evidence": [("setting", "config.yaml", f"delegation.model: {details.get('typo')}")]}


def _verify_helper_model_typo(home, details, fact="", note=None) -> dict:
    found = delegation_settings(home)
    if not found.get("readable"):
        return {"fixed": False, "why": "The practice profile's settings couldn't be read."}
    if found["model"] == details.get("typo"):
        return {"fixed": False, "why": f"delegation.model is still {details.get('typo')}, a name no provider knows."}
    if not found["model"]:
        return {"fixed": True, "why": "delegation.model is empty, so helpers use the main model."}
    return {"fixed": True, "why": f"Helpers now use {found['model']}."}


# ---------------------------------------------------------------- toolsets --


WIDE = "notes"


def _plant_wide_connector(ctx) -> dict:
    """A filesystem connector that reaches the profile's settings, instructions and memory. It is aimed at
    practice_write's settings copy, a made-up stand-in for the profile's folder, never at the folder itself: Hermes
    copies the learner's sign-in (.env, auth.json, mcp-tokens/) into every new profile, and a filesystem connector has
    none of Hermes's own read guards. The lesson and the checks are the same either way."""
    target = practice_write.write_settings_copy(ctx["home"], ctx["row"])
    practice_write.set_config(ctx["home"], ctx["row"], {f"mcp_servers.{WIDE}.command": "npx",
                                                        f"mcp_servers.{WIDE}.args": ["-y", plants_b.FS_PACKAGE, target]})
    return {"server": WIDE, "reaches": target}


def wide_servers(home) -> list:
    """Enabled connectors whose folder is the profile's own folder or above it, or its settings copy (or inside it):
    they can rewrite Hermes's settings."""
    found = hermes_read_b.mcp_servers(home)
    if not found.get("readable"):
        return []
    root = Path(home).resolve(strict=False)
    copy = (Path(home) / practice_write.SETTINGS_COPY).resolve(strict=False)
    out = []
    for server in found["servers"]:
        if not server["enabled"]:
            continue
        for raw in server.get("paths") or []:
            try:
                path = Path(raw).expanduser().resolve(strict=False)
            except (OSError, ValueError):
                continue
            if path == root or path in root.parents or path == copy or copy in path.parents:
                out.append(server)
                break
    return out


def _detect_wide_connector(home, details) -> dict:
    wide = wide_servers(home)
    found = hermes_read.messages(home)
    used = [m for m in found.get("messages", []) if found.get("readable") and m.get("role") == "tool"
            and hermes_read_b.is_connector_tool(m.get("tool_name"), details.get("server", WIDE))]
    return {"fired": bool(used),
            "facts": [{"label": "Connectors that reach the profile's settings and memory", "value": ", ".join(s["name"] for s in wide) or "none"},
                      {"label": f"Tool calls through {details.get('server', WIDE)}", "value": str(len(used))}],
            "evidence": [("setting", "config.yaml", f"mcp_servers.{details.get('server', WIDE)}: reaches the profile's settings and memory")]}


def _verify_wide_connector(home, details, fact="", note=None) -> dict:
    found = hermes_read_b.mcp_servers(home)
    if not found.get("readable"):
        return {"fixed": False, "why": "The practice profile's settings couldn't be read."}
    wide = wide_servers(home)
    if wide:
        return {"fixed": False, "why": f"The connector {wide[0]['name']} still reaches the practice profile's settings and memory."}
    return {"fixed": True, "why": "No connector reaches the practice profile's settings and memory."}


REGISTRY = {
    "one_helper": {"plant": _plant_one_helper, "detect": _detect_one_helper, "verify": _verify_one_helper},
    "helper_model_typo": {"plant": _plant_helper_model_typo, "detect": _detect_helper_model_typo, "verify": _verify_helper_model_typo},
    "wide_connector": {"plant": _plant_wide_connector, "detect": _detect_wide_connector, "verify": _verify_wide_connector},
}
