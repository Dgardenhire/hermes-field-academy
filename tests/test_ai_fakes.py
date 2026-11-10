"""A stand-in for Hermes's ``ctx.llm``, shared by the AI tests. Nothing here reaches a model.

``FakeLlm(replies)`` answers ``complete_structured`` calls in order. A reply is a dict (returned as ``parsed`` and as
JSON text), a string (text only, ``parsed`` unset), an exception (raised), or a function of the call's keyword
arguments returning one of those. Every call's keyword arguments are kept in ``calls``.
"""

from __future__ import annotations

import json
import time
import unittest
from types import SimpleNamespace


class PluginLlmTrustError(PermissionError):
    """Same class name as Hermes's, which is how ai.classify recognises it."""


class AuxiliaryClientUnavailable(RuntimeError):
    """Same class name as Hermes's error when no provider is configured."""


class FakeLlm:
    def __init__(self, replies, model="fake-model-1", delay=0.0):
        self.replies = list(replies)
        self.calls = []
        self.model = model
        self.delay = delay

    def complete_structured(self, **kw):
        self.calls.append(kw)
        if self.delay:
            time.sleep(self.delay)
        reply = self.replies.pop(0) if self.replies else {}
        if callable(reply) and not isinstance(reply, type):
            reply = reply(kw)
        if isinstance(reply, BaseException):
            raise reply
        parsed = reply if isinstance(reply, dict) else None
        text = json.dumps(reply) if isinstance(reply, dict) else str(reply)
        return SimpleNamespace(text=text, parsed=parsed, model=self.model, provider="fake", agent_id="default",
                               usage=SimpleNamespace(input_tokens=120, output_tokens=40, total_tokens=160))

    def sent_text(self) -> str:
        """Everything this stand-in was sent, as one string: instructions and every input block."""
        parts = []
        for kw in self.calls:
            parts.append(kw.get("instructions", ""))
            parts.extend(block.get("text", "") for block in kw.get("input", []))
        return "\n".join(parts)


class RoutedLlm(FakeLlm):
    """Replies by the call's ``schema_name`` (``field_academy_nudge``, ``field_academy_explain`` ...), so calls that run
    at the same time on their own threads (the nudge and every Explain my miss) each get their own reply list.
    ``default`` answers a schema with no list (or an empty one)."""

    def __init__(self, by_schema, model="fake-model-1", delay=0.0, default=None):
        super().__init__([], model=model, delay=delay)
        import threading

        self.by_schema = {k: list(v) for k, v in by_schema.items()}
        self.default = default
        self._lock = threading.Lock()

    def complete_structured(self, **kw):
        with self._lock:
            replies = self.by_schema.get(kw.get("schema_name"), [])
            reply = replies.pop(0) if replies else self.default
            self.calls.append(kw)
        if self.delay:
            time.sleep(self.delay)
        if callable(reply) and not isinstance(reply, type):
            reply = reply(kw)
        if isinstance(reply, BaseException):
            raise reply
        if reply is None:
            reply = {}
        parsed = reply if isinstance(reply, dict) else None
        text = json.dumps(reply) if isinstance(reply, dict) else str(reply)
        return SimpleNamespace(text=text, parsed=parsed, model=self.model, provider="fake", agent_id="default",
                               usage=SimpleNamespace(input_tokens=120, output_tokens=40, total_tokens=160))

    def calls_for(self, schema_name):
        return [c for c in self.calls if c.get("schema_name") == schema_name]


class FakeItself(unittest.TestCase):
    def test_replies_come_back_in_order_and_calls_are_kept(self):
        llm = FakeLlm([{"a": 1}, "not json", ValueError("bad")])
        self.assertEqual(llm.complete_structured(instructions="x", input=[{"type": "text", "text": "y"}]).parsed, {"a": 1})
        self.assertIsNone(llm.complete_structured(instructions="x", input=[]).parsed)
        with self.assertRaises(ValueError):
            llm.complete_structured(instructions="x", input=[])
        self.assertEqual(len(llm.calls), 3)
        self.assertIn("y", llm.sent_text())


if __name__ == "__main__":
    unittest.main()
