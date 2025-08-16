<br />
<div align="center">
  <img width="100" height="100" alt="Xavion AI logo" src="https://github.com/user-attachments/assets/f0cef913-bdf1-4b2f-a0b0-26b2bc2275b7" />
  <h1 align="center">Xavion AI</h1>
  <img src="https://img.shields.io/github/last-commit/javiiervm/Xavion-AI" />
  <img src="https://img.shields.io/badge/python-3.10%2B-yellow" />
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey" />
  <img src="https://img.shields.io/github/issues/javiiervm/Xavion-AI" />
  <img src="https://img.shields.io/github/stars/javiiervm/Xavion-AI" />
  <br />
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" />
</div>
<br /><br />

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
Xavion-AI/
├── chatbot/
│   │   └── Modules/         # Folder for class declarations
│   │       └── Command.py   # Class with the necessary methods to create a proper prompt before generating a response
│   ├── model.py             # Loads the GODEL model and tokenizer
│   ├── logic.py             # Prompt formatting and response generation
│   ├── config.py            # Presets to load configuration parameters
│   ├── keywords.py          # Keyword lists to filter results
│   └── utils.py             # Auxiliar functions
├── data/
│   ├── knowledge.json       # Initial dictionary downloaded from the internet with createDic.py
│   └── memory.json          # Custom dictionary where both user and AI can write new definitions
├── auxiliar/
│   └── test_model_load.py   # Script to test the loading of the model and tokenizer
├── main.py                  # Main chat loop logic
├── requirements.txt         # Packages which you need to install to run the chatbot
└── README.md
```

## How to Run

1. Clone the repo and set up your environment:

```bash
git clone https://github.com/javiiervm/Xavion-AI.git
cd Xavion-AI
python -m venv chatbot-env
source chatbot-env/bin/activate  # On Windows: chatbot-env\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download the [GODEL large model](https://huggingface.co/microsoft/GODEL-v1_1-large-seq2seq) and place the `GODEL-v1_1-large-seq2seq` folder in the same directory as `main.py` (for offline use).

4. Run the chatbot:

```bash
python main.py
```

## Example Usage

```
>> What is Python?
🤖 Python is a high-level programming language used for AI, automation, and data science.

>> Who is Pepe?
🤖 Pepe is a friend of the user. He loves science fiction and has a black cat.

>> Hi!
🤖 Hello! How can I help you today?
```

## How Knowledge Works

The chatbot uses a local files `data/knowledge.json` and `data/memory.json` to look up knowledge based on keywords in the user's message.

Example entry:

```json
{
  "python": {
    "knowledge": "Python is a high-level programming language used for AI, automation, and data science."
  },
  "pepe": {
    "knowledge": "Pepe is a friend of the user. He loves science fiction and has a black cat."
  }
}
```

You can expand this file with your own knowledge entries or give definitions to the chatbot during your conversations. The chatbot will automatically include the most relevant fact in its response generation.

## Model Configuration

In `config.py`, you can tweak generation parameters like:

* **mode**: Controls the generation behavior. Available options are:

  * `"default"`: Balanced for general-purpose generation.
  * `"creative"`: Generates more imaginative and open-ended responses.
  * `"precise"`: Produces focused and accurate outputs, ideal for factual or structured tasks.

### Default Mode Settings (`mode = "default"`):

* `max_length = 128`: Maximum number of tokens in the output.
* `min_length = 8`: Minimum number of tokens in the output.
* `top_p = 0.9`: Uses nucleus sampling to consider the smallest possible set of tokens with cumulative probability ≥ `top_p`.
* `do_sample = True`: Enables sampling for more diverse results.

### Creative Mode Settings (`mode = "creative"`):

* `temperature = 0.7`: Controls randomness in generation. Higher values make output more random.
* `top_p = 0.9`: As in default mode, enables nucleus sampling.
* `top_k = 50`: Limits sampling to the top 50 most likely tokens.
* `max_length = 512`: Allows for longer output.
* `do_sample = True`: Sampling is enabled for creative variety.

### Precise Mode Settings (`mode = "precise"`):

* `do_sample = False`: Disables sampling to favor deterministic results.
* `num_beams = 3`: Beam search with 3 beams to explore multiple paths.
* `early_stopping = True`: Stops generation when the best output is found early.
* `max_length = 512`: Supports longer and more complete answers.

You can switch modes or fine-tune individual parameters to fit your use case. This modular design allows for easy experimentation with different generation styles.

## 📚 Resources Used

* [Microsoft GODEL GitHub](https://github.com/microsoft/GODEL)
* [Hugging Face Transformers](https://huggingface.co/docs/transformers)
* [PyTorch](https://pytorch.org/)
* [HuggingFace Model Hub: microsoft/GODEL-v1\_1-large-seq2seq](https://huggingface.co/microsoft/GODEL-v1_1-large-seq2seq)

## TODO / Future Improvements

* [x] Add support for math operations, greetings, and thanks
* [ ] Add support for non-definition questions or other intentions
* [ ] Fix issues with polysemia and conversation context
* [ ] Add support for API-based knowledge retrieval (Wikipedia, Wolfram Alpha, etc.)
* [ ] Export logs of conversations for analysis or training
* [ ] Add a user interface for a more comfortable experience
* [ ] Other
