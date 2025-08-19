COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m", 
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m"
}

USER_COMMANDS = ["debug", "exit", "help", "reset"]

MATH_PATTERNS = [
    r"what\s+is\s+([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
    r"calculate\s+([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
    r"compute\s+([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
    r"solve\s+([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
    r"^([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$"
]

TEMPLATES = {
    "conversation": """
{instruction}

Knowledge: {knowledge}

Conversation history: {conversation_history}

Question: {question}

Answer:
""",

    "math": """
{instruction}

Math expressions: {expressions}

Conversation history: {conversation_history}

Question: {question}

Answer:
"""
}
