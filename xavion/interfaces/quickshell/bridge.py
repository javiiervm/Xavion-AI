from __future__ import annotations

import json
import sys
from typing import Any

from xavion.core.engine import XavionAI


def emit(event_type: str, **payload: Any) -> None:
    """Write one newline-delimited JSON event for the Quickshell frontend."""
    print(
        json.dumps(
            {
                "type": event_type,
                **payload,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def handle_command(ai: XavionAI, command: dict[str, Any]) -> None:
    command_type = command.get("type")

    if command_type == "chat":
        message = str(command.get("message", "")).strip()

        if not message:
            emit("error", message="Message cannot be empty.")
            return

        intent_mode = str(command.get("intent_mode", "auto"))
        tone_mode = str(command.get("tone_mode", "adaptive"))

        emit("start")

        try:
            for chunk in ai.chat_stream(
                message,
                intent_mode=intent_mode,
                tone_mode=tone_mode,
            ):
                if chunk:
                    emit("chunk", text=chunk)

            emit("done")

        except Exception as exc:
            emit("error", message=str(exc))

        return

    if command_type == "new":
        session_id = ai.start_new_session()
        emit("new_done", session_id=session_id)
        return

    if command_type == "reset":
        ai.reset_history()
        emit("reset_done")
        return

    if command_type == "ping":
        emit("pong")
        return

    emit(
        "error",
        message=f"Unknown command type: {command_type}",
    )


def main() -> None:
    ai = XavionAI()
    ai.start_new_session()

    emit(
        "ready",
        model=ai.model_name,
    )

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()

        if not raw_line:
            continue

        try:
            command = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            emit(
                "error",
                message=f"Invalid JSON command: {exc}",
            )
            continue

        if not isinstance(command, dict):
            emit(
                "error",
                message="Command must be a JSON object.",
            )
            continue

        try:
            handle_command(ai, command)
        except Exception as exc:
            emit("error", message=str(exc))


if __name__ == "__main__":
    main()
