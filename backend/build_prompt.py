from backend.key_variables import COLORS

INSTRUCTION_MAP = {
    "conversation": "Respond naturally and end with a question to keep the conversation going."
}

def detect_intent(user_input, debug_mode):
    if debug_mode:
        print(f"{COLORS['BOLD']}🔍 Detecting intent...{COLORS['RESET']}")

    text = user_input.lower().strip()
    
    # Defualt: conversation
    if debug_mode:
        print(f"{COLORS['BOLD']}💡 Detected conversation intent.{COLORS['RESET']}")
    return "conversation"

def build_prompt(user_input, debug_mode, response_mode=None):
    intent = detect_intent(user_input, debug_mode)
    instruction = INSTRUCTION_MAP.get(intent)

    if not instruction:
        raise ValueError(f"Instruction type '{instruction_type}' not found.")

    if debug_mode:
        print(f"{COLORS['BOLD']}📝 Instruction: {COLORS['GREEN']}{instruction}{COLORS['RESET']}")
    return instruction, intent