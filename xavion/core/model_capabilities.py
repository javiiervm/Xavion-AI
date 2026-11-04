
    
  
"""Discover Ollama model features without relying on model-name heuristics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class ModelCapabilities:
    """Capabilities reported by Ollama for an installed model."""

    model: str
    available: bool
    vision: bool = False
    thinking: bool = False
    tools: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OllamaCapabilityProvider:
    """Query /api/show and cache successful capability discovery per model."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._cache: dict[str, ModelCapabilities] = {}

    def get(self, model: str, *, refresh: bool = False) -> ModelCapabilities:
        if not refresh and model in self._cache:
            return self._cache[model]

        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"model": model},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()

            raw = payload.get("capabilities") if isinstance(payload, dict) else None
            if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
                return ModelCapabilities(
                    model=model,
                    available=False,
                    error="Ollama did not return a valid capabilities list.",
                )

            features = set(raw)
            result = ModelCapabilities(
                model=model,
                available=True,
                vision="vision" in features,
                thinking="thinking" in features,
                tools="tools" in features,
            )
            self._cache[model] = result
            return result

        except (requests.RequestException, ValueError) as exc:
            # Do not cache failures: a temporarily unavailable server may recover.
            return ModelCapabilities(model=model, available=False, error=str(exc))

    def invalidate(self, model: str | None = None) -> None:
        if model is None:
            self._cache.clear()
        else:
            self._cache.pop(model, None)

