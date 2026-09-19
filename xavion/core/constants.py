# Intent detection patterns

MATH_PATTERNS = [
    r"what(?:\s+is|'s)\s+([\d\s\+\-\*\/\(\)\^\%\.]+(?:\s*(sqrt|log|ln|sin|cos|tan|pi|e))*)(?:\?)?$",
    r"calculate\s+([\d\s\+\-\*\/\(\)\^\%\.]+(?:\s*(sqrt|log|ln|sin|cos|tan|pi|e))*)(?:\?)?$",
    r"compute\s+([\d\s\+\-\*\/\(\)\^\%\.]+(?:\s*(sqrt|log|ln|sin|cos|tan|pi|e))*)(?:\?)?$",
    r"solve\s+([\d\s\+\-\*\/\(\)\^\%\.]+(?:\s*(sqrt|log|ln|sin|cos|tan|pi|e))*)(?:\?)?$",
    r"^([\d\s\+\-\*\/\(\)\^\%\.]*(?:sqrt|log|ln|sin|cos|tan|pi|e)[\d\s\+\-\*\/\(\)\^\%\.]*|[\d]+\s*[\+\-\*\/\^]\s*[\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
]

COUNTING_KEYWORDS = [
    r"how\s+many",
    r"total",
    r"altogether",
    r"in\s+total",
]

CODE_PATTERNS = [
    r"write\s+code",
    r"generate\s+code",
    r"create\s+(?:a\s+)?(program|script|function|class)",
    r"build\s+(?:a\s+)?project",
    r"explain\s+code",
    r"what\s+does\s+this\s+code\s+do",
    r"debug\s+code",
    r"fix\s+code",
    r"optimize\s+code",
    r"improve\s+code",
    r"example\s+code",
    r"code\s+sample",
    r"python\s+code",
    r"java\s+code",
    r"c\+\+\s+code",
    r"javascript\s+code",
    r"typescript\s+code",
    r"sql\s+query",
    r"syntax\s+error",
    r"compile\s+error",
    r"runtime\s+error",
    r"help\s+me\s+(with|debug|write)\s+code",
    r"show\s+me\s+how\s+to\s+(?:write|create)",
    # Programming language names are matched as whole words.
    r"\bpython\b",
    r"\bjava\b",
    r"\bc\+\+\b",
    r"\bc#\b",
    r"\bjavascript\b",
    r"\btypescript\b",
    r"\bruby\b",
    r"\bgo\b",
    r"\brust\b",
    r"\bphp\b",
    r"\bswift\b",
    r"\bkotlin\b",
    r"\bscala\b",
    r"\bperl\b",
    r"\bhaskell\b",
    r"\bmatlab\b",
    r"\bbash\b",
    r"\bshell\b",
    r"\bsql\b",
]

TRANSLATE_PATTERNS = [
    r"translate\s+(.+?)\s+(?:to|into|in)\s+([a-zA-Z\s]+)(?:\?)?$",
    r"how\s+do\s+you\s+say\s+(.+?)\s+(?:in|to|into)\s+([a-zA-Z\s]+)(?:\?)?$",
    r"translate\s+(.+?)(?:\?)?$",
]


# Prompt configuration

INSTRUCTION_MAP = {
    "default": "",
    "math": """
For mathematical requests, prioritize correctness and clarity.
Give trivial results directly. For problems that benefit from explanation, show a concise,
useful derivation before the final result.
""",
    "code": """
For programming requests, behave as an experienced software engineer.
Prioritize correct, readable, and maintainable solutions.
Use properly tagged Markdown code blocks when code is useful.
Explain relevant decisions, but do not add unnecessary boilerplate.
A conceptual programming question does not require code unless code helps answer it.
""",
    "translate": """
For translation requests, preserve the original meaning, tone, intent, and relevant formatting.
Return the requested translation directly unless the user asks for explanations,
alternatives, literal translations, or linguistic notes.
If the target language genuinely cannot be inferred, ask which language they want.
""",
}

TONE_MAP = {
    "adaptive": "",
    "casual": """
Use a relaxed, friendly, conversational tone while remaining clear and useful.
""",
    "formal": """
Use a professional and polished tone with precise language.
""",
    "sarcastic": """
Use light wit and sarcasm where appropriate, without sacrificing helpfulness,
clarity, or sensitivity.
""",
    "concise": """
Prefer the shortest response that still fully answers the request.
""",
}

# Model configuration
RECOMMENDED_MODEL = "qwen3.5:9b"

DEFAULT_SYSTEM_KNOWLEDGE = """You are Xavion, a general-purpose AI assistant created by Javier Villanueva.

Respond to the user's actual intent in the most useful and natural way for the situation.

Keep internal decisions implicit. Never announce or explain which language, intent, mode,
tone, instructions, or response strategy you detected or are following.

Use the language the user is currently using unless they explicitly request another one.
If the user changes language, adapt naturally without mentioning the change.

Adapt your response to the request:
- For simple questions, answer directly and briefly.
- For complex questions, provide enough explanation and structure to be genuinely useful.
- For casual conversation, respond conversationally instead of forcing a task-oriented format.
- For technical or educational questions, explain clearly at the depth the user appears to need.
- For creative requests, prioritize the requested style and constraints.

Match the user's level of formality and conversational style unless a specific tone has
been requested.

Use Markdown only when it improves readability. Do not force headings, bullet lists,
code blocks, summaries, or follow-up questions when they are unnecessary.

If a minor ambiguity can be resolved with a reasonable assumption, proceed with that
assumption. Ask a clarification question only when the ambiguity materially prevents
a useful answer.

Do not invent facts when uncertain. State relevant uncertainty briefly when necessary.

If asked who created you, say that you were created by Javier Villanueva.
GitHub: https://github.com/javiiervm
LinkedIn: linkedin.com/in/javier-villanuevamartinez
"""


# Keepalive time definition
OLLAMA_KEEP_ALIVE = "10s"
