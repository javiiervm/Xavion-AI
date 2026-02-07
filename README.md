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
    <img src="https://img.shields.io/badge/rich-13.7.0-magenta" alt="Rich Version" />
  </p>
</div><br />

Xavion AI is a **local-first assistant** that runs entirely on your machine using **Ollama** for local inference and **LangChain** for robust orchestration, providing a seamless, low-latency experience. Inspired by modern CLI design patterns, it provides a rich, interactive environment featuring intent-aware responses, streaming output, and high-fidelity terminal formatting.

## Main Features

- **Privacy-First Offline Architecture**: Runs 100% locally on your machine. No API keys, no telemetry, no data leaks.
- **Intelligent Intent Detection**: Automatically switches context between general conversation, mathematical computation, and software engineering tasks.
- **Immersive Terminal UI**: Powered by `rich`, featuring:
  - Gradient-style welcome banners and loading animations.
  - Syntax-highlighted code blocks with streaming output.
  - Real-time status bars and formatted diagnostic panels.
- **Extensible Logic**: Modular architecture allows for easy customization of system prompts, model parameters, and interaction workflows.
- **Session Persistence**: Maintains context-aware conversation history for coherent multi-turn interactions.

## Project Architecture

```text
Xavion-AI/
├── backend/
│   ├── build_prompt.py      # Dynamic prompt engineering & intent classification
│   ├── build_response.py    # LLM orchestration via LangChain-Ollama
│   ├── chat_workflow.py     # Main interaction loop & session management
│   ├── ui_components.py     # Advanced terminal rendering & layout
│   ├── auxiliar.py          # Utility functions (regex, system checks)
│   └── key_variables.py     # Configuration constants & mode definitions
├── main.py                  # Application entry point
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
git clone --branch basic --single-branch https://github.com/javiiervm/Xavion-AI.git
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
```bash
ollama serve
```

### 5. Launch Xavion AI
```bash
python main.py
```

## Command Interface

Xavion AI supports several internal commands to manage the session:

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
- **ANSI Color Issues**: Ensure your terminal emulator supports 24-bit color (TrueColor). Modern versions of iTerm2, Windows Terminal, and VS Code Terminal are recommended.
