# Voice Features — Future Ideas

This document preserves the useful product ideas explored in the former `voice` branch without carrying over its Legacy implementation.

The original branch was built on Xavion's older web architecture and should not be reused directly. Any future voice support should be implemented from scratch on top of the current modular backend.

## Features worth revisiting

- **Push-to-talk and dictation** for quickly turning speech into user messages.
- **Continuous voice conversation mode** with automatic turn-taking between the user and Xavion.
- **Mute and resume controls** that actually disable and re-enable microphone capture.
- **Interruption handling**, so the user can stop or interrupt spoken output cleanly.
- **Self-listening prevention**, pausing speech recognition while Xavion is speaking to avoid feeding TTS output back into STT.
- **Microphone and playback activity visualization** for clear feedback while listening or speaking.
- **Automatic language handling** for both speech recognition and speech synthesis.
- **Speech-friendly response preprocessing**, such as stripping or adapting Markdown before sending text to TTS.
- **Connectivity-aware behavior** when a selected STT or TTS provider requires network access.

## Architectural direction

Voice should be treated as a reusable capability rather than as Web UI logic.

A future implementation should aim for a structure where frontends handle capture, playback, and presentation, while reusable voice services handle speech recognition and synthesis.

```text
Frontend (CLI / Web / Quickshell / Desktop)
                    |
                    v
              Voice service
              /           \
             v             v
            STT           TTS
             \             /
              v           v
                Xavion core
```

The backend should expose frontend-agnostic voice operations instead of embedding speech logic directly inside one interface.

## Provider principles

- Prefer **local-first STT and TTS providers** when practical, in line with Xavion's local-first direction.
- Keep providers replaceable so local and cloud alternatives can coexist later if useful.
- Avoid coupling the core to browser-only APIs such as `SpeechRecognition`.
- Avoid passing long TTS payloads through URL query parameters; use an appropriate request/streaming API.
- Keep language and voice selection configurable rather than hardcoding a locale.

## What not to preserve from the old branch

Do not port the old `voice` branch implementation directly. In particular, avoid reproducing:

- Voice logic embedded inside a single large HTML file.
- Tight coupling to the Legacy FastAPI backend.
- Hardcoded STT/TTS languages.
- Duplicate TTS endpoints with overlapping responsibilities.
- Dependence on a single online provider as the core voice architecture.

The old branch should be considered a product experiment whose useful outcome is the feature set above, not reusable production code.
