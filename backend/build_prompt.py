from backend.key_variables import COLORS

INSTRUCTION_MAP = {
    "conversation": "Respond naturally and end with a question to keep the conversation going."
}

def detect_intent(user_input, debug_mode):
    if debug_mode:
        print(f"{COLORS['BOLD']}🔍 Detecting intent...{COLORS['RESET']}")

    text = user_input.lower().strip()
    
    """
    # Check for greeting or thanks
    if any(greet in text for greet in GREETING_KEYWORDS) or any(thanks in text for thanks in THANKS_KEYWORDS):
        if debug_mode:
            print(f"{BOLD}💡 Detected greeting intent.{RESET}")
        return "greeting"

    # Check for math expression

    # Check for definition
    if any(keyword in text for keyword in DEFINITION_KEY_WORDS):
        if debug_mode:
            print(f"{BOLD}💡 Detected definition intent.{RESET}")
        return "definition"

    # Check for non-definition question

    # Check for teaching
    """

    # Defualt: conversation
    if debug_mode:
        print(f"{COLORS['BOLD']}💡 Detected conversation intent.{COLORS['RESET']}")
    return "conversation"

def build_prompt(user_input, debug_mode, response_mode=None):
    intent = detect_intent(user_input, debug_mode)
    instruction = INSTRUCTION_MAP.get(intent)

    if not instruction:
        raise ValueError(f"Instruction type '{instruction_type}' not found.")

    """
    match response_mode:
        case "precise":
            instruction += " Provide a short and precise answer."
        case "creative":
            instruction += " Provide interesting information about the topic."
    """
    
    if debug_mode:
        print(f"{COLORS['BOLD']}📝 Instruction: {COLORS['GREEN']}{instruction}{COLORS['RESET']}")
    return instruction, intent