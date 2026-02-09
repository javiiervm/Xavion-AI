<div align="center">
  <img width="600" height="600" alt="Xavion AI logo" src="https://github.com/javiiervm/Xavion-AI/blob/develop/assets/logo_full.png" />
  <br />
  <p>
    <img src="https://img.shields.io/github/last-commit/javiiervm/Xavion-AI/develop" alt="Last Commit" />
    <img src="https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey" alt="Platform Support" />
    <img src="https://img.shields.io/github/issues/javiiervm/Xavion-AI?branch=develop" alt="Issues" />
    <img src="https://img.shields.io/github/stars/javiiervm/Xavion-AI?branch=develop" alt="Stars" />
    <br />
    <img src="https://img.shields.io/badge/python-3.10%2B-yellow" alt="Python Version" />
    <img src="https://img.shields.io/badge/ollama-0.5.3-blue" alt="Ollama Version" />
    <img src="https://img.shields.io/badge/langchain-0.3.27-green" alt="LangChain Version" />
    <img src="https://img.shields.io/badge/fastapi-0.115.0-blue" alt="FastAPI Version" />
    <img src="https://img.shields.io/badge/rich-13.7.0-magenta" alt="Rich Version" />
  </p>
</div><br />

Xavion AI is a **local-first assistant** that runs entirely on your machine using **Ollama** for local inference and **LangChain** for robust orchestration, providing a seamless, low-latency experience. It features a dual-interface system: a high-fidelity **Terminal CLI** and a modern **Web Interface**, both powered by a shared, frontend-agnostic backend.

## Main Features

- **Privacy-First Offline Architecture**: Runs 100% locally on your machine. No API keys, no telemetry, no data leaks.
- **Dual Interface Support**:
  - **Terminal CLI**: Rich, interactive environment with gradient banners and syntax highlighting.
  - **Web UI**: Modern, responsive interface built with Tailwind CSS and FastAPI, supporting real-time SSE streaming.
- **Intelligent Intent Detection**: Automatically switches context between general conversation, mathematical computation, and software engineering tasks.
- **Immersive UX**: Real-time streaming output, syntax-highlighted code blocks, and adaptive status feedback across both interfaces.
- **Decoupled Backend**: Modular architecture that separates core AI logic from the UI, ensuring consistent behavior across different frontends.

## Project Architecture

```text
Xavion-AI/
├── backend/
│   ├── core.py              # Main API entry point (Frontend-agnostic)
│   ├── build_prompt.py      # Intent detection & prompt engineering
│   ├── build_response.py    # Model orchestration via LangChain
│   ├── auxiliar.py          # Math detection & general utilities
│   └── key_variables.py     # Constants, patterns, and prompt templates
├── frontend_cli/            # Terminal Interface
│   ├── ui.py                # Rich terminal UI components
│   └── workflow.py          # CLI-specific chat loop
├── frontend_web/            # Web Interface
│   ├── server.py            # FastAPI server & SSE streaming
│   ├── static/              # CSS/JS assets (Tailwind)
│   └── templates/           # Jinja2 HTML templates
├── main.py                  # Multi-frontend dispatcher
├── requirements.txt         # Dependency manifest
└── README.md                # Documentation
```

## Prerequisites

- **Python 3.10+** (Recommended: 3.13)
- **Ollama**: Ensure Ollama is installed and the background service is active.
  - [Download Ollama](https://ollama.com/download)
- **Model**: Pull the default model (or your preferred LLM):
  ```bash
  ollama pull llama3.1
  ```

## Installation & Usage

### 1. Clone the Repository
```bash
git clone https://github.com/javiiervm/Xavion-AI.git
cd Xavion-AI
```

### 2. Setup Environment
It is highly recommended to use a virtual environment:
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch Ollama
Ensure the Ollama service is running:
```bash
ollama serve
```

### 5. Launch Xavion AI
Choose your preferred interface:

**Terminal CLI:**
```bash
python main.py --CLI
```

**Web Interface:**
```bash
python main.py --web [--port 8000]
```

## Command Interface (CLI)

Xavion AI supports several internal commands in the terminal:

| Command | Action |
| :--- | :--- |
| `/help` | Displays the help panel with all available commands. |
| `/mode:<type>` | Manually switch between `auto`, `math`, `code`, or `default`. |
| `/debug` | Toggles detailed diagnostic logs. |
| `reset` | Clears the current conversation history. |
| `/exit` | Gracefully terminates the session. |

## Troubleshooting

- **Connection Refused**: Verify that `ollama serve` is running in your terminal or as a background service.
- **Model Not Found**: Ensure you have pulled the model specified in the configuration (default: `llama3.1`).
- **Web Interface Not Loading**: Check if the port (default 8000) is already in use by another application.
- **ANSI Color Issues (CLI)**: Ensure your terminal emulator supports 24-bit color (TrueColor).
