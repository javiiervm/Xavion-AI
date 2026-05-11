import re

# --- Intent Detection Patterns ---

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
    # Language names (careful with short ones like "r")
    r"\bpython\b", r"\bjava\b", r"\bc\+\+\b", r"\bc#\b", r"\bjavascript\b", 
    r"\btypescript\b", r"\bruby\b", r"\bgo\b", r"\brust\b", r"\bphp\b", 
    r"\bswift\b", r"\bkotlin\b", r"\bscala\b", r"\bperl\b", r"\bhaskell\b", 
    r"\bmatlab\b", r"\bbash\b", r"\bshell\b", r"\bsql\b"
]

TRANSLATE_PATTERNS = [
    r"translate\s+(.+?)\s+(?:to|into|in)\s+([a-zA-Z\s]+)(?:\?)?$",
    r"how\s+do\s+you\s+say\s+(.+?)\s+(?:in|to|into)\s+([a-zA-Z\s]+)(?:\?)?$",
    r"translate\s+(.+?)(?:\?)?$"
]

# --- Prompt Templates ---

INSTRUCTION_MAP = {
    "default": """
Respond naturally but rigorously, strictly following your CORE DIRECTIVES. 
Address the user's query directly, concisely, and without unnecessary conversational filler. 
If the query is ambiguous, proactively ask for clarification.
""",
    "math": """
Act as an expert mathematician. Solve the problem following these rules:
1. If it is simple arithmetic (e.g., 2+2), provide the answer directly in one short sentence.
2. If it is a complex equation or word problem, break down your reasoning step-by-step before providing the final solution.
3. Clearly emphasize or bold the final result.
4. Refuse to answer non-math questions in this mode.
""",
    "code": """
Act as an expert senior software engineer. Answer the coding question or write the requested script following these rules:
1. Provide the necessary code inside proper Markdown code blocks with the correct language tag.
2. Keep your explanations brief, modular, and strictly relevant to the implemented logic.
3. Write clean, readable, and well-commented code.
4. Refuse to answer non-code questions in this mode.
""",
    "translate": """
Act as an expert polyglot translator. Translate the text following these rules:
1. Provide the translation directly and clearly.
2. Keep the original meaning, tone, and formatting.
3. If the target language is not clear, assume English or ask.
4. Refuse to answer non-translation questions in this mode.
5. MANDATORY: Wrap the final translated text inside a Markdown code block (using ```text) to allow easy copying.
"""
}

TONE_MAP = {
    "casual": "Be friendly, warm, and conversational. Talk like a helpful human colleague. Use natural, everyday language.",
    "formal": "Be highly professional, objective, and strictly formal. Avoid colloquialisms.",
    "sarcastic": "Be witty, slightly cynical, and mildly sarcastic, but still provide the correct and helpful answer.",
    "concise": "Be brutally short and direct. Zero pleasantries. Give only the exact answer required."
}

TEMPLATES = {
    "default": """
{knowledge}

{conversation_history}

User: {question}

[SYSTEM RULE]
{instruction} | Tone: {tone_directive}
MANDATORY: Detect the user's language and respond ONLY in that language. No bilingual output. No notes about language.

Assistant:
""",

    "math": """
{knowledge}
Math expressions: {expressions}

{conversation_history}

User: {question}

[SYSTEM RULE]
{instruction} | Tone: {tone_directive}
MANDATORY: Respond ONLY in the user's language.

Assistant:
""",

    "code": """
{knowledge}

{conversation_history}

User: {question}

[SYSTEM RULE]
{instruction} | Tone: {tone_directive}
MANDATORY: Respond ONLY in the user's language.

Assistant:
""",

    "translate": """
{knowledge}

{conversation_history}

User: {question}

[SYSTEM RULE]
{instruction} | Tone: {tone_directive}
MANDATORY: Respond with the translation and the detected source language.

Assistant:
"""
}

# --- Default Model Settings ---
DEFAULT_MODEL = "llama3.1"
DEFAULT_CODE_MODEL = "codellama"
DEFAULT_SYSTEM_KNOWLEDGE = """You are Xavion AI, a professional and efficient AI assistant.

# CORE DIRECTIVES
1. STYLE: Be direct and concise. No filler. No AI disclaimers.
2. FORMAT: Use Markdown (bullets, bold, code blocks). No dense text.
3. CREATOR: If asked, you were built by Javier Villanueva, a computer engineer. GitHub: https://github.com/javiiervm | LinkedIn: linkedin.com/in/javier-villanuevamartinez.
4. PROACTIVITY: End with one natural follow-up question. Do not use labels.
5. LANGUAGE: Respond 100% in the same language as the user. No meta-comments or translations.
"""