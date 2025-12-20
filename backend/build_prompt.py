from backend.key_variables import MATH_PATTERNS, INSTRUCTION_MAP, CODE_PATTERNS
from backend.auxiliar import detect_math_expressions
from backend.ui_components import print_debug_message

import re

def detect_intent(user_input, debug_mode=False):
    if debug_mode:
        print_debug_message("Detecting intent...", icon="🔎")

    # Check for math intent
    if debug_mode:
        print_debug_message("Checking math intent...", icon="💡")
    expressions = detect_math_expressions(user_input, debug_mode)
    if expressions:
        if debug_mode:
            print_debug_message(f"Math expressions detected: {expressions}", icon="✅")
        return "math", expressions
    if debug_mode:
        print_debug_message("Rejected math intent.", icon="❌")

    # Check for code intent
    if debug_mode:
        print_debug_message("Checking code intent...", icon="💡")
    code_patterns = [token for token in CODE_PATTERNS if token in user_input.lower()]
    if code_patterns:
        if debug_mode:
            print_debug_message(f"Code patterns detected: {code_patterns}", icon="✅")
        return "code", None
    if debug_mode:
        print_debug_message("Rejected code intent.", icon="❌")

    # Default
    if debug_mode:
        print_debug_message("Set to conversation intent as default.", icon="✅")
    return "default", None

def build_prompt(user_input, debug_mode, intent_mode):
    if intent_mode != "auto":
        intent = intent_mode
        if intent_mode == "math":
            keywords = detect_math_expressions(user_input, debug_mode)
        else:
            keywords = None
    else:
        intent, keywords = detect_intent(user_input, debug_mode)
    instruction = INSTRUCTION_MAP.get(intent)

    if not instruction:
        raise ValueError(f"Instruction type '{instruction_type}' not found.")

    if debug_mode:
        print_debug_message(f"Instruction: {instruction}", icon="📝")
    return instruction, intent, keywords