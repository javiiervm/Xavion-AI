from backend.key_variables import MATH_PATTERNS, COUNTING_KEYWORDS
import re

def detect_math_expressions(user_input, debug_mode=False, debug_callback=None):
    """
    Detects math expressions in user input.
    debug_callback: optional function to call for debug logging (e.g. print_debug_message)
    """
    text = user_input.lower().strip()
    found_expressions = []

    if debug_mode and debug_callback:
        debug_callback(f"Scanning for math expressions in: '{text}'", icon="🔎")

    for pattern in MATH_PATTERNS:
        for match in re.finditer(pattern, text):
            expression = match.group(1).strip()

            has_operator = re.search(r"[+\-*/^%]", expression)
            has_function = re.search(r"\b(sqrt|log|ln|sin|cos|tan|pi|e)\b", expression)

            if has_operator or has_function:
                found_expressions.append(expression)
            else:
                if debug_mode and debug_callback:
                    debug_callback(f"Rejected as plain number or text: '{expression}'", icon="❌")

    if not found_expressions:
        has_number = re.search(r"\d+", text)
        has_keyword = any(re.search(kw, text) for kw in COUNTING_KEYWORDS)

        if has_number and has_keyword:
            if debug_mode and debug_callback:
                debug_callback("Detected counting-style math problem in natural language.", icon="✅")
            found_expressions.append(text)

    if not found_expressions and debug_mode and debug_callback:
        debug_callback("No math expressions detected.", icon="❌")

    return found_expressions