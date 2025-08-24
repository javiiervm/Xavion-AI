from backend.build_prompt import build_prompt
from backend.build_response import generate_response
from backend.auxiliar import clear_terminal
from backend.key_variables import COLORS, USER_COMMANDS, INSTRUCTION_MAP

def switch_debug_mode(current):
    return not current

def switch_intent_mode(current, user_input):
    mode = user_input.lower().split("mode:")[1].strip()
    if mode in INSTRUCTION_MAP:
        print(f"{COLORS['BOLD']}🔄 Response mode switched to: {COLORS['GREEN']}{mode}{COLORS['RESET']}\n")
        return mode
    else:
        print(f"{COLORS['BOLD']}❌ Invalid mode. Available modes are:{COLORS['RESET']}")
        for mode_name in INSTRUCTION_MAP.keys():
            print(f"- {COLORS['BOLD']}{mode_name}{COLORS['RESET']}")
        print()
        return None

def analyze_input(user_input, debug_mode):
    match user_input.lower():
        case "debug":
            debug_mode = switch_debug_mode(debug_mode)
            print(f"{COLORS['BOLD']}🔁 Debug mode switched to: {COLORS['GREEN']}{'Enabled' if debug_mode else 'Disabled'}\n{COLORS['RESET']}")
        case "exit":
            print(f"\n{COLORS['BOLD']}Goodbye!{COLORS['RESET']}\n")
            return True, debug_mode
        case "help":
            print("Available commands:")
            print(f"- {COLORS['BOLD']}'debug'{COLORS['RESET']}: Toggle debug mode")
            print(f"- {COLORS['BOLD']}'exit'{COLORS['RESET']}: Close the chat")
            print(f"- {COLORS['BOLD']}'help'{COLORS['RESET']}: Show this command list")
            print(f"- {COLORS['BOLD']}'reset'{COLORS['RESET']}: Start a new conversation")
            print(f"- {COLORS['BOLD']}'mode'{COLORS['RESET']}: Show available response modes")
            print(f"- {COLORS['BOLD']}'mode:name'{COLORS['RESET']}: Switch to specific response mode\n")
        case "mode":
            print(f"{COLORS['BOLD']}Available response modes:{COLORS['RESET']}")
            for mode_name in INSTRUCTION_MAP.keys():
                print(f"- {COLORS['BOLD']}{mode_name}{COLORS['RESET']}")
            print()
        case "reset":
            return False, debug_mode
    return None, debug_mode

def start_chat(debug_mode, intent_mode):
    clear_terminal()
    print(f"{COLORS['BOLD']}🤖 Welcome to Xavion AI 🤖\n{COLORS['RESET']}Write 'help' for a list of commands, or 'exit' to finish.\n")

    conversation_history = ""

    while True:
        print(f"{COLORS['BOLD']}💡 Mode: {COLORS['GREEN']}{intent_mode}{COLORS['RESET']}\n", end="")
        user_input = input(">> ").strip()

        if user_input.lower().startswith("mode:"):
            selected_mode = switch_intent_mode(intent_mode, user_input)
            if selected_mode is not None:
                intent_mode = selected_mode
        elif user_input.lower() in USER_COMMANDS:
            user_command, debug_mode = analyze_input(user_input, debug_mode)
            if user_command is not None:
                return user_command

        else:
            instruction, intent, keywords = build_prompt(user_input, debug_mode, intent_mode)
            if debug_mode:
                print(f"{COLORS['BOLD']}📝 Generating response...{COLORS['RESET']}")
            response = generate_response(instruction, intent, conversation_history, user_input, keywords)
            conversation_history += f"\nUser: {user_input}\nAI: {response}"