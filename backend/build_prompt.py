from backend.key_variables import COLORS, MATH_PATTERNS
from backend.auxiliar import detect_math_expressions

import re

INSTRUCTION_MAP = {
    "conversation": "Respond naturally and keep the conversation going.",
    "math": "Solve the math problem. If it is simple (like 2+2), answer naturally in one sentence (e.g., '2+2 is 4'). If it is more complex, explain the steps clearly and then give the final result."
}

def detect_intent(user_input, debug_mode=False):
    if debug_mode:
        print(f"{COLORS['BOLD']}🔎 Detecting intent...{COLORS['RESET']}")

    # Check for math intent
    if debug_mode:
        print(f"{COLORS['BOLD']}💡 Checking math intent...{COLORS['RESET']}")
    expressions = detect_math_expressions(user_input, debug_mode)
    if expressions:
        if debug_mode:
            print(f"{COLORS['BOLD']}✅ Math expressions detected: {expressions}{COLORS['RESET']}")
        return "math", expressions
    if debug_mode:
        print(f"{COLORS['BOLD']}❌ Rejected math intent.{COLORS['RESET']}")

    # Default: conversation
    if debug_mode:
        print(f"{COLORS['BOLD']}✅ Detected conversation intent.{COLORS['RESET']}")
    return "conversation", None

def build_prompt(user_input, debug_mode, no_intent=False, response_mode=None):
    if no_intent:
        intent = "conversation"
        keywords = None
    else:
        intent, keywords = detect_intent(user_input, debug_mode)
    instruction = INSTRUCTION_MAP.get(intent)

    if not instruction:
        raise ValueError(f"Instruction type '{instruction_type}' not found.")

    if debug_mode:
        print(f"{COLORS['BOLD']}📝 Instruction: {COLORS['GREEN']}{instruction}{COLORS['RESET']}")
    return instruction, intent, keywords