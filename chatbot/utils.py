import re

def detect_greeting_request(text):
    """
    Detect if the user wants the bot to greet someone by name.
    Returns the name if found, otherwise None.
    """
    pattern = r"(?:say hi to|greet|say hello to)\s+([A-Z][a-z]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None
