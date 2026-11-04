"""Frontend-independent conversation engine for Xavion."""

import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional

import requests
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from xavion.core.constants import (
    DEFAULT_SYSTEM_KNOWLEDGE,
    INSTRUCTION_MAP,
    OLLAMA_KEEP_ALIVE,
    TONE_MAP,
)
from xavion.core.images import ImageStore
from xavion.core.intent import IntentDetector
from xavion.core.model_capabilities import ModelCapabilities, OllamaCapabilityProvider


class XavionAI:
    """Core engine for conversation state, intent detection, and LLM interaction."""

    def __init__(
        self,
        model_name: str,
        system_knowledge: str = DEFAULT_SYSTEM_KNOWLEDGE,
        debug_callback: Optional[Callable[[str, str], None]] = None,
        data_dir: str | Path = "data",
        capability_provider: OllamaCapabilityProvider | None = None,
    ):
        self._model_name = ""
        self.model_name = model_name
        self.system_knowledge = system_knowledge
        self.history: List[Dict[str, Any]] = []
        self.detector = IntentDetector(debug_callback=debug_callback)
        self._debug_callback = debug_callback
        self.current_session_id: Optional[str] = None
        self.data_dir = Path(data_dir)
        self.images = ImageStore(self.data_dir)
        self.capability_provider = capability_provider or OllamaCapabilityProvider()
        self.reasoning_mode = "off"

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Model name must be a non-empty string.")
        self._model_name = value.strip()

    @property
    def debug_callback(self):
        return self._debug_callback

    @debug_callback.setter
    def debug_callback(self, callback):
        self._debug_callback = callback
        self.detector.debug_callback = callback

    def get_model_capabilities(self, *, refresh: bool = False) -> ModelCapabilities:
        """Discover whether the active model supports vision and other features."""
        return self.capability_provider.get(self.model_name, refresh=refresh)

    def supports_reasoning(self) -> bool:
        """Check whether the active model supports reasoning."""
        capabilities = self.get_model_capabilities()
        return capabilities.available and capabilities.thinking

    def _get_model(
        self,
        callbacks: Optional[List[Any]] = None,
        *,
        num_ctx: int = 4096,
    ):
        return ChatOllama(
            model=self.model_name,
            callbacks=callbacks,
            num_ctx=num_ctx,
            num_predict=1024,
            keep_alive=OLLAMA_KEEP_ALIVE,
            temperature=0.6,
            reasoning=(
                self.reasoning_mode == "on"
                if self.supports_reasoning()
                else None
            ),
        )

    def list_available_models(self) -> List[str]:
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except Exception:
            return []

    def _prepare_messages(
        self,
        message: str,
        intent_mode: str = "auto",
        tone_mode: str = "adaptive",
        images: Optional[List[Dict[str, Any]]] = None,
    ):
        if intent_mode == "auto":
            intent, _ = self.detector.get_intent(message)
        else:
            intent = intent_mode

        instruction = INSTRUCTION_MAP.get(intent, INSTRUCTION_MAP["default"])
        tone_directive = TONE_MAP.get(tone_mode, TONE_MAP["adaptive"])

        system_parts = [self.system_knowledge.strip()]
        if instruction.strip():
            system_parts.append(instruction.strip())
        if tone_directive.strip():
            system_parts.append(tone_directive.strip())

        messages = [SystemMessage(content="\n\n".join(system_parts))]

        has_historical_images = any(entry.get("images") for entry in self.history)
        can_replay_images = True
        if has_historical_images:
            capabilities = self.get_model_capabilities()
            can_replay_images = capabilities.available and capabilities.vision

        for entry in self.history:
            previous_images = entry.get("images", [])
            if previous_images and not can_replay_images:
                # Preserve text continuity when switching to a text-only model.
                # Keep attachments intact so they can be replayed after switching back.
                content = (
                    entry["user"]
                    + "\n[Earlier image attachments omitted: selected model has no verified vision support.]"
                )
            else:
                content = self.images.content_for_message(entry["user"], previous_images)
            messages.append(HumanMessage(content=content))
            messages.append(AIMessage(content=entry["assistant"]))

        current_content = self.images.content_for_message(message, images or [])
        messages.append(HumanMessage(content=current_content))
        return messages, intent

    def chat_stream(
        self,
        message: str,
        intent_mode: str = "auto",
        tone_mode: str = "adaptive",
        images: Optional[List[Any]] = None,
    ) -> Generator[str, None, None]:
        """Stream a reply, optionally using image attachments from any frontend.

        Image inputs: bytes, {"path": "/path/to/image.png"}, or
        {"data": "<base64>", "mime_type": "image/png"}.
        The data field also accepts data:image/...;base64,... URIs.
        """
        if not isinstance(message, str):
            raise ValueError("Message must be a string.")
        if images is None:
            images = []
        if not isinstance(images, list):
            raise ValueError("Images must be a list.")
        if not message.strip() and not images:
            raise ValueError("Message cannot be empty without an image.")

        if images:
            capabilities = self.get_model_capabilities()
            if not capabilities.available:
                raise ValueError(
                    "Cannot verify vision support for the selected model: "
                    f"{capabilities.error or 'capability lookup failed'}"
                )
            if not capabilities.vision:
                raise ValueError(
                    f"Model '{self.model_name}' does not support image input. "
                    "Select a vision-capable model."
                )

        attachments: List[Dict[str, Any]] = []
        completed = False
        try:
            attachments = self.images.save_many(images)
            prompt = message.strip() or "Describe the attached image(s)."
            messages, _ = self._prepare_messages(
                prompt, intent_mode, tone_mode, images=attachments
            )
            has_images = bool(images) or any(
                entry.get("images") for entry in self.history
            )

            model = self._get_model(
                num_ctx=8192 if has_images else 4096
            )

            full_response = ""
            try:
                for chunk in model.stream(messages):
                    text = chunk.content
                    if not isinstance(text, str):
                        text = str(text)
                    full_response += text
                    yield text
            except Exception as exc:
                if "404" in str(exc) and self.model_name in str(exc):
                    available = self.list_available_models()
                    error_message = f"\n[!] Model '{self.model_name}' not found.\n"
                    if available:
                        error_message += f"Available models: {', '.join(available)}\n"
                    else:
                        error_message += (
                            f"No models found. Pull one with 'ollama pull {self.model_name}'"
                        )
                    raise Exception(error_message) from exc
                raise

            entry: Dict[str, Any] = {"user": prompt, "assistant": full_response}
            if attachments:
                entry["images"] = attachments
            self.history.append(entry)
            try:
                if self.current_session_id:
                    self.save_session(self.current_session_id)
            except Exception:
                self.history.pop()
                raise

            completed = True
        finally:
            # A canceled or failed request should not leave orphan attachments.
            if not completed:
                self.images.remove_many(attachments)

    def reset_history(self):
        self.history = []

    def start_new_session(self):
        self.reset_history()
        self.current_session_id = time.strftime("chat_%Y%m%d_%H%M%S")
        return self.current_session_id

    def save_session(self, session_id: str):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.data_dir / f"{session_id}.json"

        title = "New Conversation"
        if self.history:
            first_message = self.history[0]["user"]
            title = (
                first_message[:40] + "..." if len(first_message) > 40 else first_message
            )

        data = {
            "id": session_id,
            "title": title,
            "timestamp": (filepath.stat().st_mtime if filepath.exists() else time.time()),
            "last_updated": time.time(),
            "model": self.model_name,
            "history": self.history,
        }
        with filepath.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        self.current_session_id = session_id

    def load_session(self, session_id: str):
        filepath = self.data_dir / f"{session_id}.json"
        if filepath.exists():
            with filepath.open("r", encoding="utf-8") as file:
                data = json.load(file)
                self.model_name = data.get("model", self.model_name)
                self.history = data.get("history", [])
                self.current_session_id = session_id
                return True
        return False

    def list_sessions_detailed(self) -> List[Dict[str, Any]]:
        """Return saved sessions ordered by most recent update."""
        if not self.data_dir.exists():
            return []

        sessions = []
        for filepath in self.data_dir.glob("*.json"):
            try:
                with filepath.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                    sessions.append(
                        {
                            "id": data.get("id", filepath.stem),
                            "title": data.get("title", "Untitled"),
                            "last_updated": data.get("last_updated", 0),
                        }
                    )
            except Exception:
                continue

        return sorted(sessions, key=lambda session: session["last_updated"], reverse=True)
