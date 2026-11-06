"""Persistent Xavion settings shared by every frontend."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / "xavion"

CONFIG_FILE = CONFIG_DIR / "config.json"
REASONING_MODES = frozenset({"off", "on", "auto"})


def load_config() -> dict[str, Any]:
    """Load the persistent Xavion configuration."""
    if not CONFIG_FILE.exists():
        return {}

    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def save_config(config: dict[str, Any]) -> None:
    """Persist the Xavion configuration."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_default_model() -> str | None:
    """Return the configured default model, if any."""
    model = load_config().get("default_model")
    if isinstance(model, str) and model.strip():
        return model.strip()
    return None


def set_default_model(model_name: str) -> None:
    """Set the persistent default model."""
    model_name = model_name.strip()
    if not model_name:
        raise ValueError("Model name cannot be empty.")
    config = load_config()
    config["default_model"] = model_name
    save_config(config)


def resolve_model_name(override: str | None = None) -> str | None:
    """Resolve a runtime model override or fall back to the configured default."""
    if override and override.strip():
        return override.strip()
    return get_default_model()


def get_reasoning_mode() -> str:
    """Return the shared reasoning mode (off for existing installations)."""
    mode = load_config().get("reasoning_mode", "off")
    return mode if mode in REASONING_MODES else "off"


def set_reasoning_mode(mode: str) -> None:
    """Save the reasoning preference for the CLI and graphical frontends."""
    if not isinstance(mode, str) or mode not in REASONING_MODES:
        raise ValueError("Reasoning mode must be 'off', 'on', or 'auto'.")
    config = load_config()
    config["reasoning_mode"] = mode
    save_config(config)
