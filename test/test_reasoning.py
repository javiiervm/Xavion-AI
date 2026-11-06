"""Unit tests for Xavion's reasoning policy and structured streaming.

Target location in the repository: test/test_reasoning.py
Run from the repository root: python -m unittest discover -s test -p 'test_reasoning.py' -v
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from xavion.core import config
from xavion.core.engine import XavionAI
from xavion.core.reasoning import decide_reasoning


class DummyCapabilities:
    def __init__(self, thinking=True, vision=False):
        self.available = True
        self.thinking = thinking
        self.vision = vision


class DummyProvider:
    def __init__(self, thinking=True):
        self.capabilities = DummyCapabilities(thinking=thinking)

    def get(self, model, *, refresh=False):
        return self.capabilities


class ReasoningPolicyTests(unittest.TestCase):
    def test_simple_requests_remain_fast(self):
        for message in (
            "Hola",
            "What is the capital of France?",
            "Explain what a hash table is",
            "Solve 2 + 2",
            "Traduce hola al inglés",
        ):
            with self.subTest(message=message):
                decision = decide_reasoning(message, mode="auto", supported=True)
                self.assertFalse(decision.enabled)

    def test_hard_requests_enable_reasoning(self):
        for message in (
            "Encuentra el error en este algoritmo",
            "Diseña una arquitectura cliente-servidor escalable",
            "Find the bug in this function and explain its race condition",
            "Demuéstrame por inducción esta propiedad matemática",
            "Analyze this codebase and optimize performance bottlenecks",
        ):
            with self.subTest(message=message):
                decision = decide_reasoning(message, mode="auto", supported=True)
                self.assertTrue(decision.enabled)

    def test_manual_modes_and_model_support(self):
        self.assertTrue(
            decide_reasoning("Hi", mode="on", supported=True).enabled
        )
        self.assertFalse(
            decide_reasoning("Debug this code", mode="off", supported=True).enabled
        )
        self.assertFalse(
            decide_reasoning("Debug this code", mode="on", supported=False).enabled
        )
        with self.assertRaises(ValueError):
            decide_reasoning("Hi", mode="sometimes", supported=True)


class EngineReasoningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.conf = patch.object(config, "CONFIG_FILE", Path(self.temp.name) / "config.json")
        self.dir = patch.object(config, "CONFIG_DIR", Path(self.temp.name))
        self.conf.start()
        self.dir.start()
        self.addCleanup(self.conf.stop)
        self.addCleanup(self.dir.stop)

    def make_ai(self, *, thinking=True):
        return XavionAI(
            model_name="fake:latest",
            data_dir=Path(self.temp.name) / "sessions",
            capability_provider=DummyProvider(thinking=thinking),
        )

    def test_setting_persists_across_instances(self):
        ai = self.make_ai()
        self.assertEqual(ai.reasoning_mode, "off")
        ai.reasoning_mode = "auto"
        other_frontend = self.make_ai()
        self.assertEqual(other_frontend.reasoning_mode, "auto")
        ai.reasoning_mode = "on"
        self.assertEqual(other_frontend.reasoning_mode, "on")
        ai.reasoning_mode = "auto"
        self.assertEqual(config.load_config()["reasoning_mode"], "auto")
        with self.assertRaises(ValueError):
            ai.reasoning_mode = "invalid"
        self.assertEqual(ai.reasoning_mode, "auto")

    @patch("xavion.core.engine.ChatOllama")
    def test_thinking_events_do_not_pollute_answer(self, chat_cls):
        ai = self.make_ai()
        ai.reasoning_mode = "on"
        chat_cls.return_value.stream.return_value = iter((
            SimpleNamespace(content="", additional_kwargs={"reasoning_content": "checking..."}),
            SimpleNamespace(content="Answer", additional_kwargs={}),
            SimpleNamespace(content="!", additional_kwargs={}),
        ))
        events = list(ai.chat_events("Solve a difficult problem"))
        kinds = [event["type"] for event in events]
        self.assertEqual(kinds, [
            "start", "reasoning_start", "reasoning_chunk", "reasoning_end",
            "response_start", "response_chunk", "response_chunk", "done",
        ])
        self.assertTrue(events[0]["reasoning_enabled"])
        self.assertTrue(events[-1]["reasoning_used"])
        self.assertEqual(ai.history[-1]["assistant"], "Answer!")
        self.assertNotIn("checking...", str(ai.history))
        self.assertTrue(chat_cls.call_args.kwargs["reasoning"])

    @patch("xavion.core.engine.ChatOllama")
    def test_legacy_stream_returns_only_answer(self, chat_cls):
        ai = self.make_ai()
        ai.reasoning_mode = "on"
        chat_cls.return_value.stream.return_value = iter((
            SimpleNamespace(content="", additional_kwargs={"reasoning_content": "thinking"}),
            SimpleNamespace(content="Done.", additional_kwargs={}),
        ))
        self.assertEqual(list(ai.chat_stream("Debug this code")), ["Done."])

    @patch("xavion.core.engine.ChatOllama")
    def test_auto_routes_each_message_independently(self, chat_cls):
        ai = self.make_ai()
        ai.reasoning_mode = "auto"
        chat_cls.return_value.stream.side_effect = lambda messages: iter((
            SimpleNamespace(content="OK", additional_kwargs={}),
        ))
        list(ai.chat_events("Hola"))
        self.assertFalse(chat_cls.call_args.kwargs["reasoning"])
        list(ai.chat_events("Diseña una arquitectura cliente-servidor escalable"))
        self.assertTrue(chat_cls.call_args.kwargs["reasoning"])


if __name__ == "__main__":
    unittest.main()
