<div align="center"> 
   <img width="120" height="120" alt="Xavion AI logo" src="https://github.com/javiiervm/Xavion-AI/blob/main/assets/logo-agent.png" /> 
   <h1 align="center">Xavion AI</h1> 
   <img src="https://img.shields.io/github/last-commit/javiiervm/Xavion-AI" /> 
   <img src="https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey" /> 
   <img src="https://img.shields.io/github/issues/javiiervm/Xavion-AI" /> 
   <img src="https://img.shields.io/github/stars/javiiervm/Xavion-AI" /> 
   <br />
   <img src="https://img.shields.io/badge/python-3.10%2B-yellow" /> 
   <img src="https://img.shields.io/badge/ollama-0.5.3-blue" /> 
   <img src="https://img.shields.io/badge/langchain-0.3.27-green" /> 
   <img src="https://img.shields.io/badge/sqlalchemy-2.0.43-orange" /> 
</div>
<br /><br />

Xavion AI is a **local-first assistant** that runs entirely on your machine via **Ollama** and **LangChain**. It features streaming responses, intent detection, and easy prompt customization.
<br /><br />

## Latest features
* Switched to **Ollama + LangChain** (via `langchain-ollama`) using the `llama3.1` model by default.
* Centralized prompting with **`instruction` + `knowledge` + `conversation_history`** blocks and **intent detection** helpers.
* Removed the old HuggingFace/GODEL path from the core workflow (you can still adapt the new prompt builder if you want to experiment).

> If you previously followed the HF/GODEL instructions, please switch to **Ollama** and follow the Quickstart below.

## Project Structure
```
Xavion-AI/
├── assets/
│   └── logo.png
├── backend/                 # legacy helpers (kept for reference)
│   ├── build_prompt.py
│   └── ...
├── frontend/                # **active GUI + core**
│   ├── chatbot_core.py      # ChatbotCore: LangChain + Ollama pipeline (streaming)
│   ├── build_prompt.py      # Prompt template + intent detection
│   ├── gui.py               # Tkinter app (entry point)
│   ├── gui_config.py        # Theme, colors, layout tokens
│   ├── keywords.py          # Keyword lists for greeting/thanks/definitions etc.
│   └── colors.py            # ANSI colors for logs/debug
├── requirements.txt
└── README.md
```

## Prerequisites

1. **Install Python 3.10+**  *(Program has been tested with Python 3.13)*
2. **Install Ollama**

   * macOS: `brew install ollama && ollama serve`
   * Linux: follow the instructions at [https://ollama.com](https://ollama.com)
   * Windows: install the official MSI, then ensure `ollama` is in PATH
3. **Pull a model** (default: `llama3.1`):

   ```bash
   ollama pull llama3.1
   ollama serve  # if not already running as a background service
   ```

## Quickstart

```bash
# 1) Clone and enter the project
# git clone https://github.com/javiiervm/Xavion-AI.git
cd Xavion-AI

# 2) Create a virtual environment (use your preferred tool)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run the program
python main.py
```

## Troubleshooting

* **`ERR: connection refused`** — Ensure `ollama serve` is running.
* **`model not found`** — Run `ollama pull llama3.1` (or switch the name).
* **Windows** — Use `python -m venv .venv` and `.\.venv\Scripts\activate` in PowerShell.

## Roadmap

* [ ] More response modes and prompt presets.

## 🙌 Credits

* [Ollama](https://ollama.com) · [LangChain](https://python.langchain.com)

<br /><br />
> Feedback and PRs welcome! Enjoy your new local‑first assistant. 🎧🤖

