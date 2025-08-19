from backend.key_variables import MATH_PATTERNS

import os
import platform
import re

def detect_terminal():
    system_name = platform.system()

    if system_name == "Linux" or system_name == "Darwin":
        return "clear"
    elif system_name == "Windows":
        shell = os.environ.get("SHELL", "")
        if "bash" in shell.lower():
            return "clear"
        else:
            return "cls"
    else:
        return None

def clear_terminal():
    command = detect_terminal()
    if command:
        os.system(command)
    else:
        print("\n" * 100)

def detect_math_expressions(user_input, debug_mode=False):
    text = user_input.lower().strip()
    found_expressions = []

    if debug_mode:
        print(f"🔎 Scanning for math expressions in: '{text}'")

    for pattern in MATH_PATTERNS:
        for match in re.finditer(pattern, text):
            expression = match.group(1).strip()
            if re.search(r"[\d\+\-\*\/\^]", expression) or re.search(r"\b(sqrt|log|sin|cos|tan|pi|e)\b", expression):
                found_expressions.append(expression)
            elif debug_mode:
                print(f"❌ False positive: '{expression}' is not a valid math expression.")

    if not found_expressions and debug_mode:
        print("❌ No math expressions detected.")

    return found_expressions