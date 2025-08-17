COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m", 
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m"
}

USER_COMMANDS = ["debug", "exit", "help", "reset"]

TEMPLATES = {
    "conversation": """
{instruction}

This is some information you should know: {knowledge}

Here is the conversation history: {conversation_history}

Question: {question}

Answer:
"""
}
