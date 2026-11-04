"""Regression tests for frontend-independent image support.

Run from the repository root with: python -m unittest discover -s test -p test_vision.py
"""

from __future__ import annotations

import contextlib
import io
import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from xavion.core.images import ImageStore
from xavion.core.model_capabilities import ModelCapabilities, OllamaCapabilityProvider

# One valid, tiny PNG. Real model inference is never needed for these tests.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAF"
    "gAI/ScL/nwAAAABJRU5ErkJggg=="
)


class CapabilityTests(unittest.TestCase):
    @patch("xavion.core.model_capabilities.requests.post")
    def test_detect_and_cache(self, post):
        post.return_value.json.return_value = {
            "capabilities": ["completion", "vision", "thinking", "tools"]
        }
        provider = OllamaCapabilityProvider()
        features = provider.get("qwen3.5:9b")
        self.assertTrue(features.available)
        self.assertTrue(features.vision)
        self.assertTrue(features.thinking)
        self.assertTrue(features.tools)
        provider.get("qwen3.5:9b")
        self.assertEqual(post.call_count, 1)
        provider.get("qwen3.5:9b", refresh=True)
        self.assertEqual(post.call_count, 2)

    @patch("xavion.core.model_capabilities.requests.post")
    def test_text_only_model(self, post):
        post.return_value.json.return_value = {"capabilities": ["completion", "tools"]}
        features = OllamaCapabilityProvider().get("llama3.1:8b")
        self.assertTrue(features.available)
        self.assertFalse(features.vision)

    @patch("xavion.core.model_capabilities.requests.post")
    def test_unknown_capabilities_fail_closed(self, post):
        post.return_value.json.return_value = {"details": {"family": "qwen"}}
        features = OllamaCapabilityProvider().get("unknown")
        self.assertFalse(features.available)
        self.assertFalse(features.vision)


class ImageStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = ImageStore(self.directory.name)

    def test_save_base64_and_build_content(self):
        saved = self.store.save_many([{"data": base64.b64encode(PNG).decode("ascii")}])
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["mime_type"], "image/png")
        content = self.store.content_for_message("What's in this?", saved)
        self.assertEqual(content[0], {"type": "text", "text": "What's in this?"})
        self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_save_file_path_and_data_uri(self):
        path = Path(self.directory.name) / "input.png"
        path.write_bytes(PNG)
        results = self.store.save_many(
            [
                {"path": str(path)},
                {"data": "data:image/png;base64," + base64.b64encode(PNG).decode("ascii")},
            ]
        )
        self.assertEqual(len(results), 2)

    def test_reject_fake_mime(self):
        with self.assertRaisesRegex(ValueError, "MIME type"):
            self.store.save_many([{"data": base64.b64encode(PNG).decode(), "mime_type": "image/jpeg"}])
        self.assertEqual(list(self.store.image_dir.glob("*")), [])

    def test_reject_oversize_and_rollback(self):
        with self.assertRaises(ValueError):
            self.store.save_many([PNG, b"not an image"])
        self.assertEqual(list(self.store.image_dir.glob("*")), [])
        with self.assertRaises(ValueError):
            self.store.save_many([PNG] * 5)

    def test_reject_image_path_escape_from_history(self):
        with self.assertRaisesRegex(ValueError, "Invalid stored image ID"):
            self.store.content_for_message("hi", [{"id": "../../etc/passwd", "mime_type": "image/png"}])


class EngineTests(unittest.TestCase):
    def setUp(self):
        from xavion.core.engine import XavionAI

        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.provider = Mock()
        self.provider.get.return_value = ModelCapabilities(
            model="qwen3.5:9b", available=True, vision=True
        )
        self.ai = XavionAI(
            model_name="qwen3.5:9b",
            data_dir=self.directory.name,
            capability_provider=self.provider,
        )
        self.ai.start_new_session()

    def test_image_conversation_and_reload(self):
        model = Mock()
        model.stream.return_value = [Mock(content="A "), Mock(content="picture.")]
        with patch.object(self.ai, "_get_model", return_value=model):
            self.assertEqual(
                "".join(self.ai.chat_stream("What do you see?", images=[PNG])),
                "A picture.",
            )
        history = self.ai.history
        self.assertEqual(history[0]["assistant"], "A picture.")
        self.assertEqual(len(history[0]["images"]), 1)
        payload = json.loads((Path(self.directory.name) / (self.ai.current_session_id + ".json")).read_text())
        self.assertNotIn("iVBORw0KGgo", json.dumps(payload))
        self.assertEqual(payload["history"], history)

        restored = type(self.ai)(
            model_name="llama3.1:8b",
            data_dir=self.directory.name,
            capability_provider=self.provider,
        )
        self.assertTrue(restored.load_session(self.ai.current_session_id))
        self.assertEqual(restored.model_name, "qwen3.5:9b")
        messages, _ = restored._prepare_messages("And the color?")
        self.assertEqual(messages[1].content[1]["type"], "image_url")

    def test_refuse_images_for_text_only_model(self):
        self.provider.get.return_value = ModelCapabilities(
            model="llama3.1:8b", available=True, vision=False
        )
        self.ai.model_name = "llama3.1:8b"
        with self.assertRaisesRegex(ValueError, "does not support image input"):
            list(self.ai.chat_stream("Describe", images=[PNG]))
        self.assertFalse((Path(self.directory.name) / "images").exists())

    def test_switching_to_text_only_preserves_history_without_replaying_images(self):
        model = Mock()
        model.stream.return_value = [Mock(content="Picture.")]
        with patch.object(self.ai, "_get_model", return_value=model):
            list(self.ai.chat_stream("Describe", images=[PNG]))

        self.provider.get.return_value = ModelCapabilities(
            model="llama3.1:8b", available=True, vision=False
        )
        self.ai.model_name = "llama3.1:8b"
        messages, _ = self.ai._prepare_messages("Follow-up")
        self.assertIn("image attachments omitted", messages[1].content)
        self.assertEqual(len(self.ai.history[0]["images"]), 1)

    def test_legacy_text_history_is_compatible(self):
        self.ai.history = [{"user": "hello", "assistant": "hi"}]
        messages, _ = self.ai._prepare_messages("another")
        self.assertEqual(messages[1].content, "hello")
        self.assertEqual(messages[-1].content, "another")

    def test_failed_inference_rolls_back_binary_images(self):
        model = Mock()
        model.stream.side_effect = RuntimeError("model error")
        with patch.object(self.ai, "_get_model", return_value=model):
            with self.assertRaises(RuntimeError):
                list(self.ai.chat_stream("Describe", images=[PNG]))
        self.assertEqual(list((Path(self.directory.name) / "images").glob("*")), [])
        self.assertEqual(self.ai.history, [])


class BridgeTests(unittest.TestCase):
    def test_model_changed_reports_vision_capability(self):
        from xavion.interfaces.quickshell.bridge import handle_command

        ai = Mock()
        ai.list_available_models.return_value = ["llama3.1:8b", "qwen3.5:9b"]
        ai.get_model_capabilities.return_value = ModelCapabilities(
            model="qwen3.5:9b", available=True, vision=True
        )
        ai.model_name = "llama3.1:8b"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            handle_command(ai, {"type": "set_model", "model": "qwen3.5:9b"})
        event = json.loads(output.getvalue())
        self.assertEqual(event["type"], "model_changed")
        self.assertTrue(event["capabilities"]["vision"])

    def test_bridge_refuses_malformed_images_without_model_call(self):
        from xavion.interfaces.quickshell.bridge import handle_command

        ai = Mock()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            handle_command(ai, {"type": "chat", "images": "not-a-list"})
        self.assertEqual(json.loads(output.getvalue())["type"], "error")
        ai.chat_stream.assert_not_called()


if __name__ == "__main__":
    unittest.main()
