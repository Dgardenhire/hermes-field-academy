"""ai.call: one structured call with one repair try, four plain failure kinds, scrubbed inputs, tokens only.

Also the plumbing around it: register() adds the two tasks and shares the context through runtime, an older Hermes
without register_auxiliary_task still loads, and the two Settings switches."""

from __future__ import annotations

import importlib
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from support import AcademyCase  # noqa: E402
from test_ai_fakes import AuxiliaryClientUnavailable, FakeLlm, PluginLlmTrustError  # noqa: E402

SCHEMA = {"type": "object", "required": ["text"], "additionalProperties": False,
          "properties": {"text": {"type": "string", "maxLength": 40}}}


class AiCase(AcademyCase):
    def setUp(self):
        super().setUp()
        self.ai = importlib.import_module(f"{self.name}.ai")
        self.runtime = importlib.import_module(f"{self.name}.runtime")
        self.runtime.clear()

    def tearDown(self):
        self.runtime.clear()
        super().tearDown()

    def run_call(self, llm, **kw):
        args = dict(instructions="Say hi.", inputs=["hello"], schema=SCHEMA, schema_name="t", purpose="test", llm=llm)
        args.update(kw)
        return self.ai.call(self.runtime.TASK_GUIDE, **args)

    def usage_lines(self):
        path = self.runtime.data_dir() / "ai-usage.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


class CallTests(AiCase):
    def test_a_good_reply_comes_back_with_model_time_and_tokens_on_the_named_task(self):
        llm = FakeLlm([{"text": "hi"}])
        out = self.run_call(llm)
        self.assertEqual(out["parsed"], {"text": "hi"})
        self.assertEqual(out["model"], "fake-model-1")
        self.assertEqual(out["tokens"], {"input": 120, "output": 40, "total": 160})
        self.assertGreaterEqual(out["ms"], 0)
        self.assertEqual(llm.calls[0]["task"], "field_academy_guide")
        self.assertEqual(llm.calls[0]["json_schema"], SCHEMA)
        self.assertTrue(llm.calls[0]["purpose"].startswith("field_academy."))

    def test_text_only_replies_are_parsed_from_a_fenced_block(self):
        out = self.run_call(FakeLlm(['```json\n{"text": "hi"}\n```']))
        self.assertEqual(out["parsed"], {"text": "hi"})

    def test_one_repair_try_then_bad_json(self):
        llm = FakeLlm(["no json here", {"text": "fixed"}])
        out = self.run_call(llm)
        self.assertEqual(out["parsed"], {"text": "fixed"})
        self.assertTrue(out["repaired"])
        self.assertIn("could not be read", llm.calls[1]["instructions"])
        llm = FakeLlm(["nope", {"wrong": 1}, {"text": "never asked"}])
        with self.assertRaises(self.ai.AiFailure) as caught:
            self.run_call(llm)
        self.assertEqual(caught.exception.kind, "bad_json")
        self.assertEqual(len(llm.calls), 2, "exactly one repair try")
        self.assertTrue(caught.exception.next_step)

    def test_a_reply_that_breaks_the_callers_rule_gets_the_repair_try(self):
        def no_x(reply):
            if "x" in reply["text"]:
                raise ValueError("it mentioned x")

        llm = FakeLlm([{"text": "x marks"}, {"text": "fine"}])
        self.assertEqual(self.run_call(llm, validate=no_x)["parsed"], {"text": "fine"})
        self.assertIn("it mentioned x", llm.calls[1]["instructions"])

    def test_schema_limits_are_enforced_even_without_jsonschema(self):
        with self.assertRaises(self.ai.AiFailure) as caught:
            self.run_call(FakeLlm([{"text": "y" * 41}, {"text": "z" * 50}]))
        self.assertEqual(caught.exception.kind, "bad_json")

    def test_hermes_schema_errors_count_as_a_bad_reply(self):
        llm = FakeLlm([ValueError("Plugin LLM structured output did not match schema"), {"text": "ok"}])
        self.assertEqual(self.run_call(llm)["parsed"], {"text": "ok"})

    def test_the_four_failure_kinds_each_have_words_and_a_next_step(self):
        cases = [
            (AuxiliaryClientUnavailable("No LLM provider configured for task=field_academy_guide"), "no_model"),
            (TimeoutError("Auxiliary call timed out after 60s"), "timeout"),
            (RuntimeError("Auxiliary call: provider returned error envelope: 429 rate limit"), "provider_error"),
            (RuntimeError("something odd"), "provider_error"),
            (PluginLlmTrustError("Plugin 'field-academy' may not override the model"), "provider_error"),
        ]
        seen = set()
        for exc, kind in cases:
            with self.assertRaises(self.ai.AiFailure) as caught:
                self.run_call(FakeLlm([exc]))
            self.assertEqual(caught.exception.kind, kind, exc)
            payload = caught.exception.payload()
            self.assertEqual(payload["state"], kind)
            self.assertTrue(payload["message"] and payload["next_step"])
            self.assertNotIn("Auxiliary", payload["message"], "raw errors are never shown")
            seen.add(kind)
        self.assertEqual(seen, {"no_model", "timeout", "provider_error"})
        for kind in self.ai.KINDS:
            message, next_step = self.ai.MESSAGES[kind]
            self.assertTrue(message.endswith(".") and next_step.endswith("."))

    def test_no_model_when_this_process_cannot_reach_one(self):
        with self.assertRaises(self.ai.AiFailure) as caught:
            self.ai.call(self.runtime.TASK_GUIDE, instructions="x", inputs=["y"], schema=SCHEMA, schema_name="t", purpose="test")
        self.assertEqual(caught.exception.kind, "no_model")

    # Hermes's exact words (agent/plugin_llm.py, _check_task) for a task key the plugin never registered.
    UNREGISTERED = ("Plugin 'field-academy' cannot route through auxiliary task 'field_academy_guide' \u2014 a plugin may "
                    "only pass a task key it registered itself via ctx.register_auxiliary_task() (or a built-in key when "
                    "plugins.entries.field-academy.llm.allow_task_override is true).")

    def test_an_unregistered_task_falls_back_to_the_main_model_once(self):
        llm = FakeLlm([PluginLlmTrustError(self.UNREGISTERED), {"text": "hi"}])
        self.assertEqual(self.run_call(llm)["parsed"], {"text": "hi"})
        self.assertEqual(llm.calls[0]["task"], "field_academy_guide")
        self.assertNotIn("task", llm.calls[1])

    def test_an_older_hermes_without_a_task_keyword_falls_back_once(self):
        llm = FakeLlm([TypeError("complete_structured() got an unexpected keyword argument 'task'"), {"text": "hi"}])
        self.assertEqual(self.run_call(llm)["parsed"], {"text": "hi"})
        self.assertNotIn("task", llm.calls[1])

    def test_every_other_trust_refusal_is_not_allowed_and_never_retried_untasked(self):
        """Security queue item 1: a refusal that merely mentions "task" used to fall back to the main model."""
        refusals = [
            "Plugin 'field-academy' cannot route through the built-in auxiliary task 'approval' (set "
            "plugins.entries.field-academy.llm.allow_task_override to true to allow).",
            "Plugin 'field-academy' cannot override the provider (set plugins.entries.field-academy.llm."
            "allow_provider_override to true to allow).",
            "Plugin 'field-academy' cannot override the model (set plugins.entries.field-academy.llm.allow_model_override "
            "to true to allow).",
            "Plugin 'field-academy' model override 'x' is not in plugins.entries.field-academy.llm.allowed_models.",
            "task denied for this plugin",
        ]
        for words in refusals:
            with self.subTest(words=words[:50]):
                llm = FakeLlm([PluginLlmTrustError(words), {"text": "should never be asked"}])
                with self.assertRaises(self.ai.AiFailure) as caught:
                    self.run_call(llm)
                self.assertEqual(len(llm.calls), 1, "no second, untasked call")
                self.assertEqual(caught.exception.kind, "provider_error")
                self.assertEqual((caught.exception.message, caught.exception.next_step), self.ai.NOT_ALLOWED)
        other = FakeLlm([TypeError("unsupported operand type(s)"), {"text": "no"}])
        with self.assertRaises(self.ai.AiFailure):
            self.run_call(other)
        self.assertEqual(len(other.calls), 1)

    def test_a_slow_model_times_out_at_the_budget(self):
        llm = FakeLlm([{"text": "late"}], delay=1.5)
        with self.assertRaises(self.ai.AiFailure) as caught:
            self.run_call(llm, timeout=0.3)
        self.assertEqual(caught.exception.kind, "timeout")

    def test_every_input_is_scrubbed_inside_the_helper(self):
        llm = FakeLlm([{"text": "ok"}])
        secret_inputs = [
            "Connect with https://ops:hunter2@db.example.com/main",
            "or plain ops:hunter2@db.example.com",
            "url ?token=abc and api_key=sk-live-123",
            "OPENROUTER_API_KEY=sk-or-v1-" + "a" * 40,
        ]
        self.run_call(llm, instructions="Read token=abc carefully.", inputs=secret_inputs)
        sent = llm.sent_text()
        for leaked in ("hunter2", "token=abc", "sk-live-123", "a" * 40):
            self.assertNotIn(leaked, sent)
        self.assertIn("db.example.com", sent, "the host stays readable")
        self.assertEqual(self.ai.clean("At 10:41 Hermes answered."), "At 10:41 Hermes answered.")

    def test_a_password_holding_any_awkward_character_is_removed_whole(self):
        """Security queue item 2: everything between the first ':' and the last '@' before a host goes."""
        for ch in (":", "/", "@", '"', "'"):
            pw = f"hun{ch}ter2x"
            for shaped in (f"ops:{pw}@db.example.com", f"https://ops:{pw}@db.example.com/main", f"(ops:{pw}@db.example.com)"):
                with self.subTest(ch=ch, shaped=shaped):
                    out = self.ai.clean(f"connect with {shaped} now")
                    self.assertNotIn("hun", out)
                    self.assertNotIn("ter2x", out)
                    self.assertIn("db.example.com", out, "the host stays readable")
                    if "://" not in shaped:  # scrub drops a schemed address's whole user part; the bare pass keeps the name
                        self.assertIn("ops:", out, "the user name stays")
                    self.assertTrue(out.startswith("connect with ") and out.endswith(" now"))

    def test_an_address_anywhere_inside_a_token_is_caught(self):
        """Security review, Nov 9: the user name need not start the token, and only the host's start is checked."""
        cases = [
            "key=ops:hunter2x@db.example.com",
            "`ops:hunter2x@db.example.com`",
            ",ops:hunter2x@db.example.com",
            ";ops:hunter2x@db.example.com",
            "url=https://ops:hun/ter2x@db.example.com/main",
            "x(https://ops:hun:ter2x@db.example.com)",
            '{"url":"ops:hunter2x@db.example.com"}',
            '{\\"url\\":\\"https://ops:hun@ter2x@db.example.com\\"}',
            "[the database](ops:hunter2x@db.example.com)",
            "**ops:hunter2x@db.example.com**",
            "<ops:hun'ter2x@db.example.com>",
        ]
        for shaped in cases:
            with self.subTest(shaped=shaped):
                out = self.ai.clean(f"connect with {shaped} now")
                self.assertNotIn("hun", out)
                self.assertNotIn("ter2x", out)
                self.assertIn("db.example.com", out, "the host stays readable")
                out_bare = self.ai.redact_userinfo(shaped)
                self.assertNotIn("ter2x", out_bare, "the userinfo pass alone catches it, before scrub")

    def test_the_loop1_pattern_still_runs_as_a_second_pass(self):
        for shaped in ("ops:hunter2@db.example.com", "use ops:hunter2@db.example.com."):
            with self.subTest(shaped=shaped):
                self.assertNotIn("hunter2", self.ai.redact_userinfo(shaped))
        self.assertIsNotNone(self.ai._BARE_USERINFO.search("ops:hunter2@db.example.com"))

    def test_ordinary_text_with_colons_and_email_addresses_is_left_alone(self):
        """What the pass does to ordinary text: times, labels and plain email addresses are untouched. One known
        over-redaction: a label glued to an address with no space (``to:bob@example.com``) loses the name part, which is
        the safe side to err on."""
        for plain in ("At 10:41 Hermes answered.", "Email bob@example.com at 9:30.", "Note: write to bob@example.com.",
                      "Ratio 3:2 and a@b.c", "See https://example.com/a:b and mail ana@site.org",
                      "Harbor Bakery uses QuickBooks Online; the other five use Xero"):
            with self.subTest(plain=plain):
                self.assertEqual(self.ai.redact_userinfo(plain), plain)
        self.assertEqual(self.ai.redact_userinfo("to:bob@example.com"), "to:[removed]@example.com")

    def test_tokens_are_recorded_and_no_dollars_are_invented(self):
        self.run_call(FakeLlm([{"text": "ok"}]))
        with self.assertRaises(self.ai.AiFailure):
            self.run_call(FakeLlm([RuntimeError("boom")]))
        lines = self.usage_lines()
        self.assertEqual([line["ok"] for line in lines], [True, False])
        self.assertEqual(lines[0]["total"], 160)
        for line in lines:
            self.assertFalse(any("usd" in key or "cost" in key or "dollar" in key for key in line))
        totals = self.ai.usage_totals()
        self.assertEqual(totals["calls"], 2)
        self.assertEqual(totals["by_task"]["field_academy_guide"]["total"], 160)


class SwitchTests(AiCase):
    def test_switch_defaults_and_both_only_take_true_or_false(self):
        self.assertEqual(self.state.ai_settings(), {"ai_help": True, "practice_offer": False, "practice_offer_asked": False})
        self.assertEqual(self.state.set_ai_settings(ai_help=False), {"ai_help": False, "practice_offer": False, "practice_offer_asked": False})
        with self.assertRaises(ValueError):
            self.state.set_ai_settings(ai_help="yes")
        self.assertEqual(self.state.set_ai_settings(practice_offer=True, ai_help=True), {"ai_help": True, "practice_offer": True, "practice_offer_asked": True})
        self.assertEqual(self.state.set_ai_settings(practice_offer=False), {"ai_help": True, "practice_offer": False, "practice_offer_asked": True})

    def test_until_the_learner_answers_the_question_nothing_is_added_to_a_chat(self):
        calls = []
        self.state.claim_spotlight = lambda session_id="": calls.append(session_id) or {"id": "m", "title": "T", "promise": "P"}
        self.assertFalse(self.state.ai_settings()["practice_offer_asked"])
        self.assertIsNone(self.pkg._pre_llm_call(session_id="20261108_101010_abcd", platform="desktop"))
        self.assertEqual(calls, [], "claim_spotlight is not even asked before a yes")

    def test_not_now_counts_as_an_answer_so_the_page_asks_once(self):
        out = self.state.set_ai_settings(practice_offer=False)
        self.assertEqual((out["practice_offer"], out["practice_offer_asked"]), (False, True))

    def test_yes_turns_suggestions_on(self):
        self.state.claim_spotlight = lambda session_id="": {"id": "m", "title": "T", "promise": "P"}
        self.state.set_ai_settings(practice_offer=True)
        self.assertIsNotNone(self.pkg._pre_llm_call(session_id="20261108_101010_abcd", platform="desktop"))

    def test_ai_help_off_means_no_call_at_all(self):
        self.state.set_ai_settings(ai_help=False)
        llm = FakeLlm([{"text": "never"}])
        with self.assertRaises(self.ai.AiOff):
            self.run_call(llm)
        self.assertEqual(llm.calls, [])

    def test_practice_offer_off_keeps_the_chat_hook_silent_and_the_watermark_still(self):
        calls = []
        self.state.claim_spotlight = lambda session_id="": calls.append(session_id) or {"id": "m", "title": "T", "promise": "P"}
        self.state.set_ai_settings(practice_offer=True)
        self.assertIsNotNone(self.pkg._pre_llm_call(session_id="20261108_101010_abcd", platform="desktop"))
        self.state.set_ai_settings(practice_offer=False)
        self.assertIsNone(self.pkg._pre_llm_call(session_id="20261108_101010_abcd", platform="desktop"))
        self.assertEqual(len(calls), 1, "claim_spotlight is not even asked while the offer is off")


class RegisterTests(AiCase):
    def ctx(self, with_tasks=True):
        seen = {"tasks": []}

        class Ctx:
            llm = FakeLlm([{"text": "from ctx"}])

            def register_tool(self, *a, **k):
                pass

            def register_hook(self, *a, **k):
                pass

            def register_command(self, *a, **k):
                pass

            def register_skill(self, *a, **k):
                pass

        if with_tasks:
            def register_auxiliary_task(self, key, **kwargs):
                seen["tasks"].append((key, kwargs))

            Ctx.register_auxiliary_task = register_auxiliary_task
        return Ctx(), seen

    def test_register_adds_both_tasks_and_the_guide_inherits_a_fast_builtin(self):
        ctx, seen = self.ctx()
        self.pkg.register(ctx)
        keys = {key: kwargs for key, kwargs in seen["tasks"]}
        self.assertEqual(set(keys), {"field_academy_guide", "field_academy_grader"})
        self.assertEqual(keys["field_academy_guide"]["inherit_from"], "approval")
        self.assertNotIn("inherit_from", keys["field_academy_grader"])
        for kwargs in keys.values():
            self.assertTrue(kwargs["display_name"].startswith("Field Academy"))
            self.assertTrue(kwargs["description"])

    def test_the_page_copy_of_the_package_sees_the_same_context(self):
        ctx, _ = self.ctx()
        self.pkg.register(ctx)
        spec = importlib.util.spec_from_file_location("fa_other_copy", pathlib.Path(self.pkg.__file__).parent / "runtime.py")
        other = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(other)
        self.assertIs(other.context(), ctx)
        self.assertIs(other.llm(), ctx.llm)
        out = self.ai.call(self.runtime.TASK_GUIDE, instructions="x", inputs=["y"], schema=SCHEMA, schema_name="t", purpose="test")
        self.assertEqual(out["parsed"], {"text": "from ctx"})

    def test_an_older_hermes_without_aux_tasks_still_loads(self):
        ctx, seen = self.ctx(with_tasks=False)
        self.pkg.register(ctx)
        self.assertEqual(seen["tasks"], [])

    def test_a_refused_task_registration_does_not_stop_the_plugin(self):
        ctx, _ = self.ctx()

        def refuse(self, key, **kwargs):
            raise ValueError("reserved")

        type(ctx).register_auxiliary_task = refuse
        self.pkg.register(ctx)
        self.assertIs(self.runtime.context(), ctx)


if __name__ == "__main__":
    unittest.main()
