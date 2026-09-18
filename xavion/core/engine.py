import json
import os
import time
from typing import Any, Callable, Dict, Generator, List, Optional

import requests
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from xavion.core.constants import (
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_KNOWLEDGE,
    INSTRUCTION_MAP,
    OLLAMA_KEEP_ALIVE,
    TONE_MAP,
)
from xavion.core.intent import IntentDetector


class XavionAI:
    """Core engine for conversation state, intent detection, and LLM interaction."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        system_knowledge: str = DEFAULT_SYSTEM_KNOWLEDGE,
        debug_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self._model_name = model_name
        self.system_knowledge = system_knowledge
        self.history: List[Dict[str, str]] = []
        self.detector = IntentDetector(debug_callback=debug_callback)
        self._debug_callback = debug_callback
        self.current_session_id: Optional[str] = None

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        self._model_name = value

    @property
    def debug_callback(self):
        return self._debug_callback

    @debug_callback.setter
    def debug_callback(self, callback):
        self._debug_callback = callback
        self.detector.debug_callback = callback

    def _get_model(self, callbacks: Optional[List[Any]] = None):
        return ChatOllama(
            model=self.model_name,
            callbacks=callbacks,
            num_ctx=4096,
            num_predict=1024,
            keep_alive=OLLAMA_KEEP_ALIVE,
            temperature=0.6,
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

        for entry in self.history:
            messages.append(HumanMessage(content=entry["user"]))
            messages.append(AIMessage(content=entry["assistant"]))

        messages.append(HumanMessage(content=message))
        return messages, intent

    def chat_stream(
        self,
        message: str,
        intent_mode: str = "auto",
        tone_mode: str = "adaptive",
    ) -> Generator[str, None, None]:
        messages, _ = self._prepare_messages(message, intent_mode, tone_mode)
        model = self._get_model()

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

        self.history.append({"user": message, "assistant": full_response})

        if self.current_session_id:
            self.save_session(self.current_session_id)

    def reset_history(self):
        self.history = []

    def start_new_session(self):
        self.reset_history()
        self.current_session_id = time.strftime("chat_%Y%m%d_%H%M%S")
        return self.current_session_id

    def save_session(self, session_id: str):
        if not os.path.exists("data"):
            os.makedirs("data")

        filepath = os.path.join("data", f"{session_id}.json")

        title = "New Conversation"
        if self.history:
            first_message = self.history[0]["user"]
            title = (
                first_message[:40] + "..."
                if len(first_message) > 40
                else first_message
            )

        data = {
            "id": session_id,
            "title": title,
            "timestamp": (
                os.path.getmtime(filepath) if os.path.exists(filepath) else time.time()
            ),
            "last_updated": time.time(),
            "model": self.model_name,
            "history": self.history,
        }
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        self.current_session_id = session_id

    def load_session(self, session_id: str):
        filepath = os.path.join("data", f"{session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.model_name = data.get("model", self.model_name)
                self.history = data.get("history", [])
                self.current_session_id = session_id
                return True
        return False

    def list_sessions_detailed(self) -> List[Dict[str, Any]]:
        """Return saved sessions ordered by most recent update."""
        if not os.path.exists("data"):
            return []

        sessions = []
        for filename in os.listdir("data"):
            if filename.endswith(".json"):
                try:
                    with open(
                        os.path.join("data", filename), "r", encoding="utf-8"
                    ) as file:
                        data = json.load(file)
                        sessions.append(
                            {
                                "id": data.get("id", filename.replace(".json", "")),
                                "title": data.get("title", "Untitled"),
                                "last_updated": data.get("last_updated", 0),
                            }
                        )
                except Exception:
                    continue

        return sorted(sessions, key=lambda session: session["last_updated"], reverse=True)
