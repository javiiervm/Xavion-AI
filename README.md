<div align="center"> 
   <img width="600" height="600" alt="Xavion AI logo" src="https://github.com/javiiervm/Xavion-AI/blob/develop/assets/logo_full.png" /> 
   <br /><br />
   <img src="https://img.shields.io/github/last-commit/javiiervm/Xavion-AI/develop" /> 
   <img src="https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey" /> 
   <img src="https://img.shields.io/github/issues/javiiervm/Xavion-AI?branch=develop" /> 
   <img src="https://img.shields.io/github/stars/javiiervm/Xavion-AI?branch=develop" /> 
   <br />
   <img src="https://img.shields.io/badge/python-3.10%2B-yellow" /> 
   <img src="https://img.shields.io/badge/ollama-0.5.3-blue" /> 
   <img src="https://img.shields.io/badge/langchain-0.3.27-green" /> 
   <img src="https://img.shields.io/badge/sqlalchemy-2.0.43-orange" /> 
</div>
<br /><br />

Xavion AI is a **local-first assistant** that runs entirely on your machine via **Ollama** and **LangChain**. It features a **Gemini CLI-inspired terminal interface**, streaming responses, intent detection, and easy prompt customization with beautiful, modern UI.
<br /><br />

## Latest features

- **🎨 Gemini CLI-Inspired Terminal UI**: Modern, beautiful terminal interface with rich formatting, styled panels, and smooth animations
- **✨ Enhanced Visual Experience**: Color-coded messages, loading indicators, formatted help panels, and clean status bars
- Switched to **Ollama + LangChain** (via `langchain-ollama`) using the `llama3.1` model by default (can be easily replaced for any other model).
- Centralized prompting with **`instruction` + `knowledge` + `conversation_history`** blocks and **intent detection** helpers.
- Streaming responses with **syntax highlighting** for code blocks

> If you previously followed the HF/GODEL instructions, please switch to **Ollama** and follow the guide below.

## Project Structure

```
Xavion-AI/
├── backend/
│   ├── __init__.py
│   ├── auxiliar.py            # Helper functions (terminal detection, math expression parsing)
│   ├── build_prompt.py        # Logic to detect intent and build the prompt for the model
│   ├── build_response.py      # Logic to send the prompt to the model and generate a response
│   ├── chat_workflow.py       # Logic to manage the chat interactions
│   ├── key_variables.py       # Auxiliary variables that are stored here and called when necessary
│   └── ui_components.py       # Rich terminal UI components (new!)
├── main.py
├── requirements.txt
└── README.md
```

## Requirements

1. **Install Python 3.10+** _(Program has been tested with Python 3.13)_
2. **Install Ollama**

   - macOS: `brew install ollama && ollama serve` or download from [here](https://ollama.com/download/mac)
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`
   - Windows: download from [here](https://ollama.com/download/windows), then ensure `ollama` is in PATH

3. **Install Rich library**: The terminal UI uses the `rich` library for enhanced formatting (automatically installed via requirements.txt)
4. **Pull a model** (default: `llama3.1`):

   ```bash
   ollama pull llama3.1
   ollama serve  # if not already running as a background service
   ```

## Installation and usage

1. Clone and enter the project.

```bash
git clone --branch basic --single-branch https://github.com/javiiervm/Xavion-AI.git
cd Xavion-AI
```

2. Create a virtual environment (use your preferred tool).

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Run the program.

```bash
python main.py
```

## Features Showcase

### 🎨 Beautiful Terminal UI

Xavion AI now features a Gemini CLI-inspired interface with:

- **Styled Welcome Banner**: Eye-catching startup animation
- **Color-Coded Messages**: User messages in cyan, AI responses in magenta
- **Status Bar**: Shows current mode and debug state at a glance
- **Formatted Panels**: Help commands and mode lists in beautiful tables
- **Loading Animations**: Smooth spinners during startup
- **Debug Mode**: Dimmed, non-intrusive debug information when enabled

### 💡 Smart Intent Detection

- **Auto Mode**: Automatically detects math, code, or general conversation
- **Manual Modes**: Switch to specific modes with `mode:math`, `mode:code`, or `mode:default`
- **Conversation History**: Maintains context throughout your chat session

## Troubleshooting

- **`ERR: connection refused`** — Ensure `ollama serve` is running.
- **`model not found`** — Run `ollama pull llama3.1` (or switch the name).
- **Windows** — Use `python -m venv .venv` and `.\.venv\Scripts\activate` in PowerShell.
- **Terminal colors not showing** — Ensure your terminal supports ANSI colors (most modern terminals do)

## Resources used

- [Ollama](https://ollama.com)
- [LangChain](https://python.langchain.com)
- [Rich](https://rich.readthedocs.io/) - Terminal formatting library

<br />

Feedback and PRs welcome! Enjoy your new local‑first assistant. 🎧🤖
