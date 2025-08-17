from backend.keywords import (
    GREETING_KEYWORDS,
    DEFINITION_KEY_WORDS,
    THANKS_KEYWORDS
)
from backend.colors import RESET, BOLD, GREEN

INSTRUCTION_MAP = {
    "conversation": "Respond naturally and end with a question to keep the conversation going.",
    "definition": "Explain the term clearly with a simple example.",
    "greeting": "Reply warmly and briefly to greetings or thanks, showing you are ready to help."
}

def build_prompt(instruction_type: str, debug_mode: bool, response_mode: str) -> str:
    """
    Builds a prompt instruction based on the given parameters.

    Args:
        instruction_type (str): Type of instruction to build
        debug_mode (bool): If True, prints debug information
        response_mode (str): Mode of response

    Returns:
        str: The constructed instruction prompt

    Raises:
        ValueError: If the instruction_type is not found in INSTRUCTION_MAP
    """
    instruction = INSTRUCTION_MAP.get(instruction_type)
    if not instruction:
        raise ValueError(f"Instruction type '{instruction_type}' not found.")

    match response_mode:
        case "precise":
            instruction += " Provide a short and precise answer."
        case "creative":
            instruction += " Provide interesting information about the topic."
    
    if debug_mode:
        print(f"{BOLD}📝 Instruction: {GREEN}{instruction}{RESET}")
    return instruction

def detect_intent(user_input, debug_mode):
    if debug_mode:
        print(f"{BOLD}🔍 Detecting intent...{RESET}")
    text = user_input.lower().strip()
    
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

    # Defualt: conversation
    if debug_mode:
        print(f"{BOLD}💡 Detected conversation intent.{RESET}")
    return "conversation"