COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m", 
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m"
}

USER_COMMANDS = ["debug", "exit", "help", "reset"]

MATH_PATTERNS = [
    r"what(?:\s+is|'s)\s+([\d\s\+\-\*\/\(\)\^\%\.]+(?:\s*(sqrt|log|ln|sin|cos|tan|pi|e))*)(?:\?)?$",
    r"calculate\s+([\d\s\+\-\*\/\(\)\^\%\.]+(?:\s*(sqrt|log|ln|sin|cos|tan|pi|e))*)(?:\?)?$",
    r"compute\s+([\d\s\+\-\*\/\(\)\^\%\.]+(?:\s*(sqrt|log|ln|sin|cos|tan|pi|e))*)(?:\?)?$",
    r"solve\s+([\d\s\+\-\*\/\(\)\^\%\.]+(?:\s*(sqrt|log|ln|sin|cos|tan|pi|e))*)(?:\?)?$",
    r"^([\d\s\+\-\*\/\(\)\^\%\.]*(?:sqrt|log|ln|sin|cos|tan|pi|e)[\d\s\+\-\*\/\(\)\^\%\.]*|[\d]+\s*[\+\-\*\/\^]\s*[\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$"
]

COUNTING_KEYWORDS = [
    r"how\s+many",
    r"total",
    r"altogether",
    r"in\s+total"
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
