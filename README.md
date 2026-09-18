<div align="center">
  <img width="600" height="600" alt="Xavion AI logo" src="assets/logo_name.png" />
  <br />
  <p>
    <img src="https://img.shields.io/github/last-commit/javiiervm/Xavion-AI/dev" alt="Last Commit" />
    <!-- <img src="https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey" alt="Platform Support" /> -->
    <img src="https://img.shields.io/badge/python-3.10%2B-yellow" alt="Python Version" />
    <img src="https://img.shields.io/badge/release-Spark%2026.9-orange" alt="Xavion Release" />
    <img src="https://img.shields.io/badge/inference-Ollama-blue" alt="Ollama" />
    <img src="https://img.shields.io/github/issues/javiiervm/Xavion-AI?branch=dev" alt="Issues" />
    <img src="https://img.shields.io/github/stars/javiiervm/Xavion-AI?branch=dev" alt="Stars" />
  </p>
</div>

Xavion AI is a local-first AI assistant built around a reusable Python backend. Local inference is provided by [Ollama](https://ollama.com/), while LangChain components handle prompt composition and model interaction. Its main architectural goal is to keep AI and conversation logic independent from presentation code so that multiple frontends can reuse the same backend.

The current `dev` branch targets **Xavion Spark 26.9**, the stable foundation for the first modern Xavion release.

## Current Status

The terminal interface is the primary supported frontend. A lightweight Quickshell bridge is also implemented so external shell UI components can reuse the same backend through a newline-delimited JSON protocol. Web and standalone desktop interfaces are not implemented yet.

Current capabilities include:

- Local LLM inference through Ollama.
- Streaming responses.
- Automatic intent routing for general, mathematical, programming, and translation requests.
- Manual conversation modes and response tones.
- Ollama model discovery and runtime model switching.
- Optional CodeLlama switching while using code mode.
- Persistent local conversation sessions stored as JSON.
- Interactive terminal UI built with Rich and prompt-toolkit.
- Quickshell bridge with streaming JSON events for shell integration.
- Centralized release metadata for the Xavion name and version.
- An LLM stress-test suite for reasoning, technical accuracy, and instruction following.

## Architecture

```text
Xavion-AI/
├── assets/
│   └── logo_name.png
├── docs/
│   └── voice-ideas.md
├── test/
│   ├── Xavion_LLM_Stress_Test.json
│   └── stress_test.py
├── xavion/
│   ├── core/
│   │   ├── constants.py
│   │   ├── engine.py
│   │   └── intent.py
│   ├── interfaces/
│   │   ├── cli/
│   │   │   ├── app.py
│   │   │   └── ui.py
│   │   └── quickshell/
│   │       └── bridge.py
│   └── version.py
├── main.py
├── requirements.txt
└── README.md
```

The separation is intentional:

- `xavion/core/` contains reusable assistant behavior and should not depend on a particular frontend.
- `xavion/interfaces/` contains presentation and interaction code for each client.
- `main.py` manages the local Ollama lifecycle and dispatches the selected interface.
- `xavion/version.py` is the single source of truth for the current Xavion release name and version.
- `xavion/interfaces/quickshell/bridge.py` exposes the core to Quickshell without duplicating assistant logic.
- `test/` contains the current model-level stress test.

A frontend can consume the core directly without depending on terminal-specific code:

```python
from xavion.core.engine import XavionAI

assistant = XavionAI()

for token in assistant.chat_stream("Hello, Xavion"):
    print(token, end="", flush=True)
```

This boundary already allows the CLI and Quickshell integration to share the same backend, while leaving room for future web and desktop clients.

## Release Metadata

Release identity is defined in `xavion/version.py`:

```python
NAME = "Spark"
VERSION = "26.9"
DISPLAY_NAME = f"Xavion {NAME}"
```

Components should import these values instead of hardcoding the release name or version. Xavion uses calendar-style release numbering: `26.9` for September 2026, `26.9.1` for another release in the same month, `26.10` for October 2026, and `27.1` for January 2027.

## Requirements

- Python 3.10 or newer.
- Ollama installed locally and available through the `ollama` command.
- The default `llama3.1` model installed in Ollama. Other installed models can be selected at runtime from the CLI.

The launcher can attempt to start Ollama automatically. The current lifecycle implementation is primarily designed for Unix-like systems; broader launcher portability is still a development task.

## Installation

Clone the repository:

```bash
git clone https://github.com/javiiervm/Xavion-AI.git
cd Xavion-AI
git switch dev
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Pull the default model if it is not already installed:

```bash
ollama pull llama3.1
```

## Running Xavion

Launch the terminal interface with:

```bash
python main.py cli
```

Because CLI is the default interface, this also works:

```bash
python main.py
```

Enable diagnostic output with:

```bash
python main.py cli --debug
```

## Quickshell Bridge

The Quickshell integration uses a small backend bridge rather than terminal-specific code:

```bash
python -m xavion.interfaces.quickshell.bridge
```

The bridge reads newline-delimited JSON commands from standard input and emits newline-delimited JSON events on standard output. It supports chat streaming, new sessions, history resets, health checks, model discovery, and runtime model switching. The initial `ready` event exposes the current release name, version, display name, active model, and installed models so a Quickshell frontend can initialize without hardcoding release metadata.

Supported model-control commands are `list_models` and `set_model`. The bridge reports model state through the `models` and `model_changed` events.

## CLI Commands

| Command | Description |
| --- | --- |
| `/new` | Start a new conversation session. |
| `/reset` | Clear the current conversation history. |
| `/sessions` | List saved conversations. |
| `/load:<id/idx>` | Load a saved session by ID or displayed index. |
| `/models` | List installed Ollama models. |
| `/model:<name/idx>` | Switch the active model. |
| `/mode:<name>` | Select `auto`, `default`, `math`, `code`, or `translate`. |
| `/tone:<name>` | Select `adaptive`, `casual`, `formal`, `sarcastic`, or `concise`. |
| `/copy` | Copy the last code block from the previous response. |
| `/copy:<n>` | Copy a specific code block. |
| `/debug` | Toggle debug output. |
| `/help` | Display the command reference. |
| `/exit` | Close the application. |

## Stress Test

The repository includes a lightweight benchmark for comparing Xavion's behavior across reasoning, programming, ambiguity, hallucination resistance, general knowledge, and strict instruction-following tasks.

Run it from the repository root:

```bash
python test/stress_test.py
```

The benchmark is intended as a development signal, not as a production-readiness certification.

## Development Direction

`dev` currently represents the Spark baseline: a clean, local-first, frontend-agnostic assistant foundation. Advanced capabilities that are not required for this baseline are intentionally deferred to **Xavion Ember**. New interfaces should continue to reuse `xavion/core/` rather than reimplement conversation, model, or session behavior.
