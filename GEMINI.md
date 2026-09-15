# Project: Xavion AI (Refactored)

Xavion AI is being restructured into a professional, modular AI assistant. The goal is to separate the core AI logic from the various user interfaces (CLI, Web, Desktop) to ensure maximum reusability and scalability.

## New Modular Architecture

The project now follows a package-based structure:

### 1. Core Package (`xavion/core/`)
- **`engine.py`**: Contains the `XavionAI` class, the central brain that manages conversation state, history, and LLM communication.
- **`intent.py`**: (Planned) Logic for detecting user intent (math, code, general).
- **`prompts.py`**: (Planned) Management of system instructions and templates.

### 2. Interfaces Package (`xavion/interfaces/`)
- **`cli/`**: Advanced terminal user interface implementation.
  - **`app.py`**: High-level application controller for the CLI.
  - **`ui.py`**: "Neutral Spark" TUI engine using `prompt_toolkit` (input) and `rich` (output).
- **`web/`**: (Planned) FastAPI-based web interface.
- **`desktop/`**: (Planned) Desktop interface (e.g., Tkinter/PySide).

### 3. Utilities Package (`xavion/utils/`)
- **`config.py`**: (Planned) Centralized configuration (model names, API keys, etc.).
- **`logger.py`**: (Planned) Standardized logging across the application.

### 4. Entry Point (`main.py`)
- Unified script to launch the assistant.
- **Modular Frontend Switch**: Supports selecting between `cli`, `web`, and `desktop` (CLI is currently the only one fully implemented).
- **Session Manager**: Interactive command (`/sessions`) to list and resume previous chats, ordered by recency.
- **Session Control**: Commands to start new chats (`/new`) or clear history (`/reset`).

## CLI Design System: "Neutral Spark"

The CLI has been overhauled with a modern, minimalist aesthetic:
- **Palette**: Primarily grayscale (`#FFFFFF`, `#A0A0A0`, `#555555`) with a single "Toasted Orange" accent (`#CC5500`) used for the logo and critical branding.
- **Input System**: Powered by `prompt_toolkit`. Features a dynamic, multiline inline input box that scales with terminal width and provides a themed placeholder.
- **Output System**: Powered by `rich`. Uses live-streaming Markdown rendering for AI responses and stylized Panels for user history.
- **Status Bar**: A persistent HTML-styled bar at the bottom showing CWD, active model, and intent mode.

## Status of Refactoring
- [x] New directory structure created (CLI focused).
- [x] Unified `main.py` entry point with automatic Ollama management.
- [x] Model installation wizard implemented.
- [x] `XavionAI` core class with advanced JSON persistence and title generation.
- [x] Command-based session manager (`/sessions`, `/new`).
- [x] Advanced "Neutral Spark" CLI with `prompt_toolkit` and `rich`.
- [ ] Implement Web Interface using the same core logic.

## Recent Changes
- **UI Modularization**: Separated CLI application logic (`app.py`) from rendering logic (`ui.py`).
- **Interactive TUI**: Replaced basic `input()` with a sophisticated `prompt_toolkit` application supporting multiline input and keybindings.
- **Neutral Spark Theme**: Introduced a professional color palette and compact banner design.
- **Streaming Markdown**: AI responses now stream in real-time within a Markdown-aware grid.
- **Session Metadata**: Conversations now include titles (auto-generated from the first message) and timestamps for better organization.

to 4096 tokens.
