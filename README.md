<br />
<div align="center">
  <h1 align="center">🤖 AI Chatbot with GODEL 🤖</h1>
</div>

A local, knowledge-aware conversational AI chatbot powered by [Microsoft GODEL](https://github.com/microsoft/GODEL). This chatbot runs entirely on your machine, supports structured prompts, and can reference custom knowledge stored in a local database.
<br /><br />

## Features

* Based on Microsoft's `GODEL-v1_1-large-seq2seq` model (via Hugging Face)
* Works offline once the model is downloaded
* Uses structured prompts with `instruction`, `knowledge`, and `conversation_history` blocks
* Supports custom external knowledge and dynamic learning using a JSON knowledge base
* Responds dynamically to the user and adapts based on detected context
* Easily extendable with your own facts, logic, or integrations

## Requirements

* Python 3.8+  *(Program has been tested with Python 3.13)*
* Virtual Python environment to install packages (recommended, not mandatory)
* Internet access (not mandatory when using the model offline)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

```
root/
├── chatbot/
│   ├── model.py             # Loads the GODEL model and tokenizer
│   ├── logic.py             # Prompt formatting and response generation
│   ├── config.py            # Presets to load configuration parameters
│   ├── keywords.py          # Keyword lists to filter results
│   └── utils.py             # Auxiliar functions
├── data/
│   ├── knowledge.json       # Initial dictionary downloaded from the internet with createDic.py
│   └── memory.json          # Custom dictionary where both user and AI can write new definitions
├── main.py                  # Main chat loop logic
├── createDic.py             # Script to download a knowledge base (customizable) and convert it to JSON format
├── requirements.txt         # Packages which you need to install to run the chatbot
└── README.md
```

## 🚀 How to Run

1. Clone the repo and set up your environment:

```bash
git clone https://github.com/your-username/godel-chatbot.git
cd godel-chatbot
python -m venv chatbot-env
source chatbot-env/bin/activate  # On Windows: chatbot-env\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the chatbot:

```bash
python main.py
```

## 💬 Example Usage

```
>> What is Python?
🤖: Python is a high-level programming language used for AI, automation, and data science.

>> Who is Pepe?
🤖: Pepe is a friend of the user. He loves science fiction and has a black cat.

>> Hi!
🤖: Hello! How can I help you today?
```

## 🧠 How Knowledge Works

The chatbot uses a local file `data/knowledge_base.json` to look up facts based on keywords in the user's message.

Example entry:

```json
{
  "python": "Python is a high-level programming language used for AI, automation, and data science.",
  "pepe": "Pepe is a friend of the user. He loves science fiction and has a black cat."
}
```

You can expand this file with your own knowledge entries. The chatbot will automatically include the most relevant fact in its response generation.

## ⚙️ Model Configuration

In `logic.py`, you can tweak generation parameters like:

* `max_length`
* `do_sample` (for creativity)
* `num_beams` (for precision)
* `temperature`, `top_p` (when sampling is enabled)

## 📚 Resources Used

* [Microsoft GODEL GitHub](https://github.com/microsoft/GODEL)
* [Hugging Face Transformers](https://huggingface.co/docs/transformers)
* [PyTorch](https://pytorch.org/)
* [HuggingFace Model Hub: microsoft/GODEL-v1\_1-base-seq2seq](https://huggingface.co/microsoft/GODEL-v1_1-base-seq2seq)

## 🔧 TODO / Future Improvements

* [ ] Add memory management for multi-turn conversations
* [ ] Integrate semantic search using sentence-transformers
* [ ] Add support for API-based knowledge retrieval (Wikipedia, Wolfram Alpha, etc.)
* [ ] Export logs of conversations for analysis or training

## 📄 License

MIT License. See `LICENSE` file (or add one if you haven't yet).

## 🤛 Author

Made with ❤️ by \[Your Name]
Feel free to fork, improve, or contribute!
