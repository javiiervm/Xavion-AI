INSTRUCTION_MAP = {
    "default": "Respond naturally and keep the conversation going.",
    "math": """
    Solve the math problem. 
    If it is simple (like 2+2), answer naturally in one sentence (e.g., '2+2 is 4'). 
    If it is more complex, explain the steps clearly and then give the final result.
    If the math problem is not clear, ask for clarification.
    Ask any user request about the procedure.
    Don't answer non-math questions.
    """,
    "code": """
    Answer the coding question or produce the requested script.
    If it is simple (like 'print("Hello, world!")'), answer naturally in one sentence.
    If it is more complex, explain any concept necessary to understand what you've implemented.
    If the coding question is not clear, ask for clarification.
    Ask any user request about the procedure.
    Don't answer non-code questions.
    """
}

COLORS = {
    "RESET": "\033[0m",
    "BOLD": "\033[1m", 
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m"
}

USER_COMMANDS = ["debug", "exit", "help", "reset", "mode"]

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

CODE_PATTERNS = [
    r"write\\s+code",
    r"generate\\s+code",
    r"create\\s+(?:a\\s+)?(program|script|function|class)",
    r"build\\s+(?:a\\s+)?project",
    r"explain\\s+code",
    r"what\\s+does\\s+this\\s+code\\s+do",
    r"debug\\s+code",
    r"fix\\s+code",
    r"optimize\\s+code",
    r"improve\\s+code",
    r"example\\s+code",
    r"code\\s+sample",
    r"python\\s+code",
    r"java\\s+code",
    r"c\\+\\+\\s+code",
    r"javascript\\s+code",
    r"typescript\\s+code",
    r"sql\\s+query",
    r"syntax\\s+error",
    r"compile\\s+error",
    r"runtime\\s+error",
    r"help\\s+me\\s+(with|debug|write)\\s+code",
    r"show\\s+me\\s+how\\s+to\\s+(?:write|create)",
    r"python", r"java", r"c\\+\\+", r"c#", r"javascript", r"typescript", r"ruby", r"go", r"rust", r"php", r"swift", r"kotlin", r"scala", r"perl", r"haskell", r" r ", r"matlab", r"bash", r"shell", r"sql"
]


TEMPLATES = {
    "default": """
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
""",
    "code": """
{instruction}

Conversation history: {conversation_history}

Question: {question}

Answer:
"""
}
