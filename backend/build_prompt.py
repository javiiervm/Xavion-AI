from backend.key_variables import (
    COLORS,
    FILE_VERBS,
    FILE_TOKENS,
    SHELL_TOKENS,
    CODE_TOKENS,
    GIT_TOKENS,
    PATTERNS_STRONG,
    NEGATIVE_THEORY
)

import re
import unicodedata

INSTRUCTION_MAP = {
    "conversation": "Respond naturally and end with a question to keep the conversation going.",
    "agent": """
    Respond naturally and end with a question to keep the conversation going.
    """
}

def normalize(txt):
    t = txt.lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t

def score_agent_intent(text):
    reasons = []
    score = 0

    for pat in PATTERNS_STRONG:
        if re.search(pat, text):
            score += 3
            reasons.append(f"pattern:{pat}")

    if any(v in text for v in FILE_VERBS):
        score += 2
        reasons.append("verbs:file/code")
    if any(tok in text for tok in FILE_TOKENS):
        score += 1
        reasons.append("tokens:file")
    if any(tok in text for tok in SHELL_TOKENS):
        score += 2
        reasons.append("tokens:shell")
    if any(tok in text for tok in CODE_TOKENS):
        score += 2
        reasons.append("tokens:code")
    if any(gt in text for gt in GIT_TOKENS):
        score += 2
        reasons.append("tokens:git")

    if (any(re.search(p, text) for p in NEGATIVE_THEORY)
        and score < 2):
        score -= 2
        reasons.append("negative:theory")

    return score, reasons

def detect_intent(user_input, debug_mode):
    if debug_mode:
        print(f"{COLORS['BOLD']}🔍 Detecting intent...{COLORS['RESET']}")

    text = normalize(user_input)
    
    # Check for agent intent
    score, reasons = score_agent_intent(text)
    if debug_mode:
        print(f"{COLORS['BOLD']}🧭 Agent score: {score} (reasons={', '.join(reasons)}){COLORS['RESET']}")
    if score >= 2:
        if debug_mode:
            print(f"{COLORS['BOLD']}💡 Detected agent intent.{COLORS['RESET']}")
        return "agent"
    else:
        if debug_mode:
            print(f"{COLORS['BOLD']}❌ Rejected agent intent.{COLORS['RESET']}")
    
    # Defualt: conversation
    if debug_mode:
        print(f"{COLORS['BOLD']}💡 Detected conversation intent.{COLORS['RESET']}")
    return "conversation"

def build_prompt(user_input, debug_mode, response_mode=None):
    intent = detect_intent(user_input, debug_mode)
    instruction = INSTRUCTION_MAP.get(intent)

    # RESPONSE MODE
    
    """if debug_mode:
        print(f"{COLORS['BOLD']}📝 Instruction: {COLORS['GREEN']}{instruction}{COLORS['RESET']}")
    """
    return instruction, intent