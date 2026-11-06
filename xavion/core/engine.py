"""Frontend-independent conversation engine for Xavion."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional

import requests
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from xavion.core.config import get_reasoning_mode, set_reasoning_mode
from xavion.core.constants import (
    DEFAULT_SYSTEM_KNOWLEDGE,
    INSTRUCTION_MAP,
    OLLAMA_KEEP_ALIVE,
    TONE_MAP,
)
from xavion.core.images import ImageStore
from xavion.core.intent import IntentDetector
from xavion.core.model_capabilities import ModelCapabilities, OllamaCapabilityProvider
from xavion.core.reasoning import ReasoningDecision, decide_reasoning


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
        # Shared persistent preference. "off" remains the safe default for
        # existing installations until the CLI and Quickshell UIs expose Auto.
        self._reasoning_mode = get_reasoning_mode()
        self.last_reasoning_decision: ReasoningDecision | None = None

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Model name must be a non-empty string.")
        self._model_name = value.strip()

    @property
    def reasoning_mode(self) -> str:
        # Pick up changes made by another running frontend before each request.
        self._reasoning_mode = get_reasoning_mode()
        return self._reasoning_mode

    @reasoning_mode.setter
    def reasoning_mode(self, value: str) -> None:
        # Property assignment remains compatible with existing frontends.
        # Persist first, so an I/O failure does not desynchronize this instance.
        set_reasoning_mode(value)
        self._reasoning_mode = value

    @property
    def debug_callback(self):
        return self._debug_callback

    @debug_callback.setter
    def debug_callback(self, callback):
        self._debug_callback = callback
        self.detector.debug_callback = callback

    def get_model_capabilities(self, *, refresh: bool = False) -> ModelCapabilities:
        """Discover active model features using Ollama."""
        return self.capability_provider.get(self.model_name, refresh=refresh)

    def supports_reasoning(self) -> bool:
        """Return whether Ollama reports thinking support for this model."""
        capabilities = self.get_model_capabilities()
        return capabilities.available and capabilities.thinking

    def decide_reasoning(
        self,
        message: str,
        *,
        intent_mode: str = "auto",
        has_images: bool = False,
    ) -> ReasoningDecision:
        """Preview effective reasoning without making an LLM request."""
        if intent_mode == "auto":
            intent, _ = self.detector.get_intent(message)
        else:
            intent = intent_mode
        return self._decide_reasoning(message, intent=intent, has_images=has_images)

    def _decide_reasoning(
        self,
        message: str,
        *,
        intent: str,
        has_images: bool,
    ) -> ReasoningDecision:
        return decide_reasoning(
            message,
            mode=self.reasoning_mode,
            supported=self.supports_reasoning(),
            intent=intent,
            history=self.history,
            has_images=has_images,
        )

    def _get_model(
        self,
        callbacks: Optional[List[Any]] = None,
        *,
        num_ctx: int = 4096,
        reasoning_enabled: bool | None = None,
    ):
        """Build a ChatOllama instance for one request's effective policy."""
        supported = self.supports_reasoning()
        if not supported:
            reasoning = None
        elif reasoning_enabled is not None:
            reasoning = reasoning_enabled
        else:
            # Preserve compatibility for direct callers of the private method.
            reasoning = self.reasoning_mode == "on"

        return ChatOllama(
            model=self.model_name,
            callbacks=callbacks,
            num_ctx=num_ctx,
            num_predict=2048 if reasoning is True else 1024,
            keep_alive=OLLAMA_KEEP_ALIVE,
            temperature=0.6,
            reasoning=reasoning,
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

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Accept plain text and LangChain's list-of-content-blocks format."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
                and part.get("type") == "text"
                and isinstance(part.get("text"), str)
            )
        return ""

    def chat_events(
        self,
        message: str,
        intent_mode: str = "auto",
        tone_mode: str = "adaptive",
        images: Optional[List[Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Yield typed events, keeping thinking separate from final answer.

        Events: start, reasoning_start, reasoning_chunk, reasoning_end,
        response_start, response_chunk, done.

        Only 'response_chunk' text is persisted as assistant history; the
        reasoning trace is kept separate and not saved in session JSON.
        Image inputs follow the same format as chat_stream().
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
            messages, intent = self._prepare_messages(
                prompt, intent_mode, tone_mode, images=attachments
            )
            decision = self._decide_reasoning(
                prompt,
                intent=intent,
                has_images=bool(images),
            )
            self.last_reasoning_decision = decision
            has_images_in_context = bool(images) or any(
                entry.get("images") for entry in self.history
            )
            model = self._get_model(
                num_ctx=8192 if has_images_in_context else 4096,
                reasoning_enabled=decision.enabled,
            )

            yield {
                "type": "start",
                "reasoning_mode": decision.mode,
                "reasoning_enabled": decision.enabled,
                "reasoning_reason": decision.reason,
            }

            full_response = ""
            reasoning_started = False
            response_started = False
            try:
                for chunk in model.stream(messages):
                    # ChatOllama stores thinking in additional_kwargs whenever
                    # reasoning=True. This field is independent from content.
                    extras = getattr(chunk, "additional_kwargs", {}) or {}
                    thinking = extras.get("reasoning_content", "")
                    if isinstance(thinking, str) and thinking:
                        if not reasoning_started:
                            reasoning_started = True
                            yield {"type": "reasoning_start"}
                        yield {"type": "reasoning_chunk", "text": thinking}

                    answer = self._extract_text(getattr(chunk, "content", ""))
                    if answer:
                        if reasoning_started and not response_started:
                            yield {"type": "reasoning_end"}
                        if not response_started:
                            response_started = True
                            yield {"type": "response_start"}
                        full_response += answer
                        yield {"type": "response_chunk", "text": answer}
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

            if reasoning_started and not response_started:
                yield {"type": "reasoning_end"}

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
            yield {
                "type": "done",
                "reasoning_enabled": decision.enabled,
                "reasoning_used": reasoning_started,
                "images": attachments,
            }
        finally:
            # A canceled or failed request should not leave orphan attachments.
            if not completed:
                self.images.remove_many(attachments)

    def chat_stream(
        self,
        message: str,
        intent_mode: str = "auto",
        tone_mode: str = "adaptive",
        images: Optional[List[Any]] = None,
    ) -> Generator[str, None, None]:
        """Backwards-compatible text-only stream for existing frontends.

        Images: bytes, {"path": "/path/to/image.png"}, or
        {"data": "<base64>", "mime_type": "image/png"}.
        """
        events = self.chat_events(
            message, intent_mode=intent_mode, tone_mode=tone_mode, images=images
        )
        try:
            for event in events:
                if event["type"] == "response_chunk":
                    yield event["text"]
        finally:
            # Closing the legacy generator must also close the underlying
            # event stream so canceled requests clean up image attachments.
            events.close()

    def reset_history(self):
        self.history = []
        self.last_reasoning_decision = None

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
                self.last_reasoning_decision = None
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
