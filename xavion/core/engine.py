import json
import os
import time
from typing import Generator, List, Optional, Dict, Any, Callable
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from xavion.core.constants import (
    DEFAULT_MODEL, DEFAULT_SYSTEM_KNOWLEDGE, 
    INSTRUCTION_MAP, TEMPLATES, TONE_MAP
)
from xavion.core.intent import IntentDetector
import requests

class XavionAI:
    """
    Core engine for Xavion AI. 
    Handles conversation state, intent detection, and LLM interaction.
    """
    def __init__(
        self, 
        model_name: str = DEFAULT_MODEL, 
        system_knowledge: str = DEFAULT_SYSTEM_KNOWLEDGE,
        debug_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.model_name = model_name
        self.system_knowledge = system_knowledge
        self.history: List[Dict[str, str]] = []
        self.detector = IntentDetector(debug_callback=debug_callback)
        self.debug_callback = debug_callback
        self.current_session_id: Optional[str] = None

    def _get_model(self, callbacks: Optional[List[Any]] = None):
        return OllamaLLM(
            model=self.model_name,
            callbacks=callbacks,
            num_ctx=4096,
            num_predict=1024
        )

    def list_available_models(self) -> List[str]:
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
            return []
        except Exception:
            return []

    def _format_history(self) -> str:
        formatted = ""
        for entry in self.history:
            formatted += f"User: {entry['user']}\nAI: {entry['assistant']}\n"
        return formatted

    def _prepare_chain(self, message: str, intent_mode: str = "auto", tone_mode: str = "casual"):
        if intent_mode == "auto":
            intent, keywords = self.detector.get_intent(message)
        else:
            intent = intent_mode
            keywords = self.detector.detect_math_expressions(message) if intent == "math" else None

        instruction = INSTRUCTION_MAP.get(intent, INSTRUCTION_MAP["default"])
        template = TEMPLATES.get(intent, TEMPLATES["default"])
        
        params = {
            "instruction": instruction,
            "conversation_history": self._format_history(),
            "question": message,
            "tone_directive": TONE_MAP.get(tone_mode, TONE_MAP["casual"]) # <--- Nuevo
        }

        if intent == "math":
            params["expressions"] = ", ".join(keywords) if keywords else "N/A"
        elif intent == "default":
            params["knowledge"] = self.system_knowledge

        prompt = ChatPromptTemplate.from_template(template)
        return prompt, params, intent

    def chat_stream(self, message: str, intent_mode: str = "auto", tone_mode: str = "casual") -> Generator[str, None, None]:
        prompt, params, _ = self._prepare_chain(message, intent_mode, tone_mode)
        model = self._get_model()
        chain = prompt | model
        
        full_response = ""
        try:
            for chunk in chain.stream(params):
                full_response += chunk
                yield chunk
        except Exception as e:
            if "404" in str(e) and self.model_name in str(e):
                available = self.list_available_models()
                error_msg = f"\n[!] Model '{self.model_name}' not found.\n"
                if available:
                    error_msg += f"Available models: {', '.join(available)}\n"
                else:
                    error_msg += f"No models found. Pull one with 'ollama pull {self.model_name}'"
                raise Exception(error_msg)
            raise e
            
        self.history.append({"user": message, "assistant": full_response})
        
        if self.current_session_id:
            self.save_session(self.current_session_id)

    def reset_history(self):
        self.history = []
        # We don't clear session_id here to allow re-starting a fresh chat in the same "slot" 
        # but usually we want a new session_id for a new chat.

    def start_new_session(self):
        self.reset_history()
        self.current_session_id = time.strftime("chat_%Y%m%d_%H%M%S")
        return self.current_session_id

    def save_session(self, session_id: str):
        if not os.path.exists("data"):
            os.makedirs("data")
        
        filepath = os.path.join("data", f"{session_id}.json")
        
        # Determine a title from first message
        title = "New Conversation"
        if self.history:
            first_msg = self.history[0]["user"]
            title = first_msg[:40] + "..." if len(first_msg) > 40 else first_msg

        data = {
            "id": session_id,
            "title": title,
            "timestamp": os.path.getmtime(filepath) if os.path.exists(filepath) else time.time(),
            "last_updated": time.time(),
            "model": self.model_name,
            "history": self.history
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.current_session_id = session_id

    def load_session(self, session_id: str):
        filepath = os.path.join("data", f"{session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.model_name = data.get("model", self.model_name)
                self.history = data.get("history", [])
                self.current_session_id = session_id
                return True
        return False

    def list_sessions_detailed(self) -> List[Dict[str, Any]]:
        """Lists sessions with metadata, ordered by last_updated descending."""
        if not os.path.exists("data"):
            return []
        
        sessions = []
        for filename in os.listdir("data"):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join("data", filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        sessions.append({
                            "id": data.get("id", filename.replace(".json", "")),
                            "title": data.get("title", "Untitled"),
                            "last_updated": data.get("last_updated", 0)
                        })
                except Exception:
                    continue
        
        return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)
