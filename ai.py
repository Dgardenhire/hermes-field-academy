"""One structured model call, used by every Field Academy AI feature.

``call(task, ...)`` runs ``ctx.llm.complete_structured`` on one of Field Academy's own auxiliary tasks with a JSON
schema, retries once with a repair note when the reply can't be read, and otherwise raises ``AiFailure`` with one of
four kinds. Each kind carries plain words and a next step, so every screen that shows a failure says the same thing:

* ``no_model``: this Hermes has no model Field Academy can use (none set, or the call can't reach Hermes at all).
* ``timeout``: no answer inside the time limit (60 seconds by default, Hermes's own default for a plugin task).
* ``bad_json``: the reply still didn't fit the shape after one repair try.
* ``provider_error``: the model's provider answered with an error, or Hermes refused the call.

Rules this file keeps, so call sites can't forget them:

* Every string that goes to the model (the instructions and each input block) passes ``scrub.scrub`` here, plus a
  token pass for ``name:password@host`` with or without a scheme, which removes a password holding ``:`` ``/`` ``@``
  or quotes whole (``scrub`` alone only catches a plain one after a scheme).
* The AI help switch (``state.ai_settings``) is read here too. With it off, ``AiOff`` is raised before any call.
* Usage is recorded from ``result.usage`` as tokens only, in ``ai-usage.jsonl`` in the plugin's data folder. No
  dollar figure is ever made up here; the practice cost comes from Hermes's own estimate (``cost.py``).
* Nothing a model returns is acted on in this file. Callers validate the parsed reply before they use it.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from typing import Any, Callable, Optional

from . import runtime, scrub

_log = logging.getLogger("hermes.plugins.field_academy")

DEFAULT_TIMEOUT = 60.0
KINDS = ("no_model", "timeout", "bad_json", "provider_error")

MESSAGES = {
    "no_model": ("Field Academy can't reach a model in this Hermes yet.",
                 "Pick a model in Settings, Models, then try again. Your checks still work without it."),
    "timeout": ("Your model didn't answer within a minute.",
                "Press Try again, or pick a faster model for Field Academy in Settings, Models."),
    "bad_json": ("Your model's reply came back in a shape Field Academy can't read, even after asking twice.",
                 "Field Academy shows the course's own words instead. Press Try again to ask your model once more."),
    "provider_error": ("Your model's provider sent back an error.",
                       "Wait a minute, then press Try again. If it keeps happening, check the model in Settings, Models."),
}
# Plainer words for a few provider errors people actually hit. Matched on the lowercased error text, never shown raw.
PROVIDER_DETAIL = (
    (("429", "rate limit", "rate_limit", "too many requests"), "Your model's provider says it is busy right now."),
    (("401", "403", "unauthorized", "forbidden", "invalid api key", "authentication"),
     "Your model's provider turned down the key Hermes sent."),
    (("overloaded", "529", "503", "502", "500", "unavailable"), "Your model's provider is having trouble right now."),
    (("context length", "context_length", "too long", "maximum context"), "The question was too long for your model."),
)
NOT_ALLOWED = ("Hermes didn't let Field Academy use your model.",
               "Open Settings, Plugins, Field Academy, and check that it may use your model. Your checks still work.")

REPAIR_NOTE = ("Your last reply could not be read as the JSON object described above. Reply again with only that "
               "JSON object, every field present, each text field short.")

# A password in an address, with or without a scheme in front: ``ops:hunter2@host``, ``https://u:p/w@host``. A
# password may hold ``:`` ``/`` ``@`` or quotes, so the pass works on whole whitespace-delimited tokens (below), and the
# address may sit anywhere inside the token: after ``key=``, a comma, a semicolon, a backtick, inside JSON quotes or a
# markdown link.
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://")
_USER_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._%+~-")
# Only the start of a host is checked: whatever follows it (a port, a path, a closing quote, JSON escapes, markdown)
# doesn't stop the pass.
_HOST_START = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9-]+)*(?![A-Za-z0-9-])")
_TOKEN = re.compile(r"\S+")
# The Loop 1 pattern, kept as a second pass so nothing it caught can get through.
_BARE_USERINFO = re.compile(r"(?<![\w/:@.-])[A-Za-z0-9._%+-]+:[^\s/@:'\"]+@(?=[A-Za-z0-9.-]+\b)")


def _redact_userinfo(token: str) -> str:
    """One whitespace-delimited token holding ``user:password@host`` anywhere in it (a scheme in front is allowed):
    everything between the user's ``:`` and the LAST ``@`` that a host follows is replaced. The user is the run of user
    characters right before that ``:`` (after ``scheme://`` when there is one, otherwise after any other character),
    so ``key=u:p@h``, ``,u:p@h``, ```u:p@h``` and ``x=https://u:p/w@h`` are all caught. Anything else is left as
    it is: ``10:41``, ``bob@example.com`` and ``Note: see bob@example.com`` pass through unchanged."""
    at = -1
    for i in range(len(token) - 1, 0, -1):
        if token[i] == "@" and _HOST_START.match(token, i + 1):
            at = i
            break
    if at <= 0:
        return token
    head = token[:at]
    colon = -1
    scheme = _SCHEME.search(head)
    if scheme:
        c = head.find(":", scheme.end())
        if c > scheme.end() and all(ch in _USER_CHARS for ch in head[scheme.end():c]):
            colon = c
    if colon < 0:
        for c in range(1, len(head)):
            if head[c] == ":" and head[c - 1] in _USER_CHARS:
                colon = c
                break
    if colon < 0 or colon + 1 >= at:
        return token
    return token[:colon + 1] + scrub.REMOVED + token[at:]

_USAGE_LOCK = threading.Lock()


class AiFailure(RuntimeError):
    """A model call that didn't give a usable answer. ``kind`` is one of ``KINDS``."""

    def __init__(self, kind: str, message: str = "", next_step: str = ""):
        if kind not in KINDS:
            kind = "provider_error"
        default_message, default_next = MESSAGES[kind]
        super().__init__(message or default_message)
        self.kind = kind
        self.message = message or default_message
        self.next_step = next_step or default_next

    def payload(self) -> dict:
        return {"state": self.kind, "message": self.message, "next_step": self.next_step}


class AiOff(RuntimeError):
    """The learner turned AI help off. No call is made."""

    def __init__(self, reason: str = "switch"):
        super().__init__("AI help is off.")
        self.reason = reason


def redact_userinfo(text) -> str:
    """The ``user:password@host`` pass on its own, token by token."""
    once = _TOKEN.sub(lambda m: _redact_userinfo(m.group(0)), str(text or ""))
    # The old pattern's match is ``user:password@``; keep the user name, as the first pass does.
    return _BARE_USERINFO.sub(lambda m: m.group(0).split(":", 1)[0] + ":" + scrub.REMOVED + "@", once)


def clean(text) -> str:
    """What every model input passes through: the ``user:password@host`` pass first (so a password holding ``/`` or
    ``@`` is removed whole, before ``scrub`` could cut it part way), then Field Academy's scrubber, then the pass again
    on what ``scrub`` left."""
    return redact_userinfo(scrub.scrub(redact_userinfo(text)))


def ai_help_on() -> bool:
    from . import state

    return bool(state.ai_settings()["ai_help"])


# ------------------------------------------------------------------ schema --


def check_schema(value: Any, schema: dict, where: str = "reply") -> None:
    """A small validator for the schemas Field Academy writes (object, array, string, integer, boolean). Raises
    ``ValueError`` naming the first problem. Hermes validates too when ``jsonschema`` is installed; this one always
    runs, so a reply is never used unchecked."""
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{where} is not an object")
        props = schema.get("properties") or {}
        for key in schema.get("required") or []:
            if key not in value:
                raise ValueError(f"{where} has no {key}")
        if schema.get("additionalProperties") is False:
            extra = [k for k in value if k not in props]
            if extra:
                raise ValueError(f"{where} has an unexpected field {extra[0]}")
        for key, sub in props.items():
            if key in value:
                check_schema(value[key], sub, f"{where}.{key}")
    elif kind == "array":
        if not isinstance(value, list):
            raise ValueError(f"{where} is not a list")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValueError(f"{where} has too many items")
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValueError(f"{where} has too few items")
        for i, item in enumerate(value):
            check_schema(item, schema.get("items") or {}, f"{where}[{i}]")
    elif kind == "string":
        if not isinstance(value, str):
            raise ValueError(f"{where} is not text")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValueError(f"{where} is too long")
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError(f"{where} is not one of the allowed values")
    elif kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{where} is not a whole number")
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{where} is too small")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(f"{where} is too large")
    elif kind == "boolean":
        if not isinstance(value, bool):
            raise ValueError(f"{where} is not true or false")


def parse_json(text: str):
    """The first complete JSON object in ``text`` (a fenced block or bare), or ``None``."""
    text = (text or "").strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


# --------------------------------------------------------------- failures --

# Hermes's words when a plugin passes a task key it never registered (agent/plugin_llm.py, _check_task). The built-in
# task refusal reads "cannot route through the built-in auxiliary task", so it does not match.
_UNREGISTERED = ("cannot route through auxiliary task", "a plugin may only pass a task key it registered itself")


def task_not_registered(exc: BaseException) -> bool:
    """True only for the explicit "task not registered here" signals; anything else is a real refusal or error."""
    if isinstance(exc, TypeError):
        return bool(re.search(r"unexpected keyword argument '?task'?", str(exc)))
    if type(exc).__name__ != "PluginLlmTrustError":
        return False
    words = " ".join(str(exc).lower().split())
    return all(needle in words for needle in _UNREGISTERED)



def classify(exc: BaseException) -> AiFailure:
    """Map anything a model call raised to one of the four kinds. The raw error is logged, never shown."""
    if isinstance(exc, AiFailure):
        return exc
    name = type(exc).__name__
    text = str(exc).lower()
    _log.warning("field-academy: model call failed: %s: %s", name, scrub.scrub(str(exc), 300))
    if name == "PluginLlmTrustError":
        return AiFailure("provider_error", *NOT_ALLOWED)
    if isinstance(exc, TimeoutError) or "timed out" in text or "timeout" in text:
        return AiFailure("timeout")
    if name == "AuxiliaryClientUnavailable" or "no llm provider" in text or "no provider" in text or "no model" in text:
        return AiFailure("no_model")
    for needles, words in PROVIDER_DETAIL:
        if any(n in text for n in needles):
            return AiFailure("provider_error", words, MESSAGES["provider_error"][1])
    return AiFailure("provider_error")


# ------------------------------------------------------------------ usage --


def _usage(result) -> dict:
    u = getattr(result, "usage", None)
    if u is None:
        return {"input": 0, "output": 0, "total": 0}
    get = (lambda k: u.get(k)) if isinstance(u, dict) else (lambda k: getattr(u, k, None))
    try:
        inp = int(get("input_tokens") or get("prompt_tokens") or 0)
        out = int(get("output_tokens") or get("completion_tokens") or 0)
        total = int(get("total_tokens") or 0) or inp + out
    except (TypeError, ValueError):
        return {"input": 0, "output": 0, "total": 0}
    return {"input": inp, "output": out, "total": total}


def record_usage(task: str, purpose: str, model: str, tokens: dict, ms: int, ok: bool, attempt_id=None) -> None:
    """One line per call in ``ai-usage.jsonl``. Tokens only."""
    from . import store

    line = json.dumps({"at": store.now(), "task": task, "purpose": purpose, "model": model, "ok": ok, "ms": int(ms),
                       "attempt_id": int(attempt_id) if isinstance(attempt_id, int) and not isinstance(attempt_id, bool) else None,
                       "input": tokens.get("input", 0), "output": tokens.get("output", 0), "total": tokens.get("total", 0)},
                      sort_keys=True)
    try:
        with _USAGE_LOCK, open(runtime.data_dir() / "ai-usage.jsonl", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:  # the ledger must never break a call
        _log.debug("field-academy: usage not recorded", exc_info=True)


def usage_totals(attempt_id=None) -> dict:
    """Tokens spent on Field Academy's own calls, by task; one attempt's only when ``attempt_id`` is given. Read by the
    record's cost line."""
    out = {"calls": 0, "input": 0, "output": 0, "total": 0, "by_task": {}}
    try:
        lines = (runtime.data_dir() / "ai-usage.jsonl").read_text(encoding="utf-8").splitlines()
    except (OSError, Exception):
        return out
    for raw in lines:
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if attempt_id is not None and row.get("attempt_id") != int(attempt_id):
            continue
        task = str(row.get("task", ""))
        slot = out["by_task"].setdefault(task, {"calls": 0, "total": 0})
        slot["calls"] += 1
        slot["total"] += int(row.get("total") or 0)
        out["calls"] += 1
        for key in ("input", "output", "total"):
            out[key] += int(row.get(key) or 0)
    return out


# ------------------------------------------------------------------- call --


def _bounded(fn: Callable[[], Any], limit: float):
    """Run ``fn`` on its own daemon thread and give up after ``limit`` seconds. Hermes's own retries can run past the
    budget it was given; the learner's screen can't. A stray call that finishes late holds nothing of ours."""
    box: dict = {}

    def run():
        try:
            box["value"] = fn()
        except BaseException as exc:  # noqa: BLE001 - handed back to the caller below
            box["error"] = exc

    worker = threading.Thread(target=run, name="field-academy-model-call", daemon=True)
    worker.start()
    worker.join(limit)
    if worker.is_alive():
        raise TimeoutError(f"no answer in {limit:.0f} seconds")
    if "error" in box:
        raise box["error"]
    return box.get("value")


_FORMAT = {"plain": False}  # set once a provider refuses the structured-output request; lasts until the plugin reloads


def format_refused(exc: BaseException) -> bool:
    """True when Hermes or the provider refused the structured-output request itself, not the answer."""
    msg = str(exc).lower()
    if "structured output is supported" in msg:
        return True
    return ("400" in msg or "invalid_request" in msg) and any(k in msg for k in (
        "additionalproperties", "output_config", "response_format", "json_schema", "structured output"))


def _plain_hint(schema: dict) -> str:
    return ("\n\nReply with one complete JSON object and nothing else: no code fence, no commentary. It must fit this "
            "JSON Schema: " + json.dumps(schema, separators=(",", ":")))


def call(task: str, *, instructions: str, inputs: list, schema: dict, schema_name: str, purpose: str,
         max_tokens: int = 800, timeout: float = DEFAULT_TIMEOUT, validate: Optional[Callable[[dict], None]] = None,
         llm=None, respect_switch: bool = True, attempt_id=None) -> dict:
    """One structured call. Returns ``{"parsed", "model", "provider", "ms", "tokens", "repaired"}``.

    ``validate`` may raise ``ValueError`` for a reply that fits the schema but not the rules (a pin on an unknown
    event, say); that counts as a bad reply and gets the one repair try. Raises ``AiOff`` or ``AiFailure``."""
    if respect_switch and not ai_help_on():
        raise AiOff("switch")
    model_api = llm if llm is not None else runtime.llm()
    if model_api is None or not hasattr(model_api, "complete_structured"):
        raise AiFailure("no_model")
    clean_instructions = clean(instructions)
    blocks = [{"type": "text", "text": clean(text)} for text in inputs if str(text or "").strip()]
    if not blocks:
        blocks = [{"type": "text", "text": "(no input)"}]
    started = time.monotonic()
    deadline = started + float(timeout)
    tokens_seen = {"input": 0, "output": 0, "total": 0}
    model_name, provider = "", ""
    use_task = True
    repaired = False
    last_problem = ""

    def send(kwargs: dict):
        nonlocal use_task
        if use_task:
            try:
                return model_api.complete_structured(task=task, **kwargs)
            except Exception as exc:
                # Only two signals mean "this Hermes can't route Field Academy's own task here": an older Hermes whose
                # complete_structured has no task keyword, and Hermes's own "a plugin may only pass a task key it
                # registered itself" refusal (agent/plugin_llm.py _check_task). Every other refusal (a built-in task,
                # a provider or model override) is a refusal: it is never retried on the main model.
                if not task_not_registered(exc):
                    raise
                _log.info("field-academy: task %s not registered here; using the main model", task)
                use_task = False
        return model_api.complete_structured(**kwargs)

    def once(note: str):
        text = clean_instructions + (("\n\n" + note) if note else "")
        kwargs = dict(input=blocks, max_tokens=max_tokens, timeout=max(1.0, deadline - time.monotonic()),
                      purpose=f"field_academy.{purpose}")
        if _FORMAT["plain"]:
            return send(dict(kwargs, instructions=text + _plain_hint(schema)))
        try:
            return send(dict(kwargs, instructions=text, json_schema=schema, schema_name=schema_name))
        except Exception as exc:
            if not format_refused(exc):
                raise
            # Claude's strict output mode can reject the schema itself (a 400 before any answer). Ask in plain words
            # from here on and read the JSON from the reply; check_schema below still holds it to the same shape.
            _log.info("field-academy: the provider refused the format request; asking for JSON in plain text")
            _FORMAT["plain"] = True
            kwargs["timeout"] = max(1.0, deadline - time.monotonic())
            return send(dict(kwargs, instructions=text + _plain_hint(schema)))

    for attempt in range(2):
        note = "" if attempt == 0 else REPAIR_NOTE + (f" (The problem: {last_problem}.)" if last_problem else "")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            record_usage(task, purpose, model_name, tokens_seen, (time.monotonic() - started) * 1000, False, attempt_id)
            raise AiFailure("timeout")
        try:
            result = _bounded(lambda: once(note), remaining)
        except ValueError as exc:  # Hermes checked the reply against the schema and it did not fit
            last_problem = "it did not match the schema"
            _log.info("field-academy: %s reply did not match the schema (%s)", purpose, scrub.scrub(str(exc), 200))
            repaired = True
            continue
        except Exception as exc:
            record_usage(task, purpose, model_name, tokens_seen, (time.monotonic() - started) * 1000, False, attempt_id)
            raise classify(exc) from exc
        used = _usage(result)
        for key in tokens_seen:
            tokens_seen[key] += used[key]
        model_name = str(getattr(result, "model", "") or model_name)
        provider = str(getattr(result, "provider", "") or provider)
        parsed = getattr(result, "parsed", None)
        if not isinstance(parsed, dict):
            parsed = parse_json(getattr(result, "text", "") or "")
        try:
            if not isinstance(parsed, dict):
                raise ValueError("the reply was not a JSON object")
            check_schema(parsed, schema)
            if validate is not None:
                validate(parsed)
        except ValueError as exc:
            last_problem = scrub.scrub(str(exc), 120)
            repaired = True
            continue
        ms = int((time.monotonic() - started) * 1000)
        record_usage(task, purpose, model_name, tokens_seen, ms, True, attempt_id)
        return {"parsed": parsed, "model": model_name, "provider": provider, "ms": ms, "tokens": dict(tokens_seen),
                "repaired": repaired and attempt > 0}
    record_usage(task, purpose, model_name, tokens_seen, (time.monotonic() - started) * 1000, False, attempt_id)
    raise AiFailure("bad_json")
