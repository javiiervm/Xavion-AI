from backend.build_prompt import build_prompt
from backend.build_response import generate_response
from backend.key_variables import COLORS, USER_COMMANDS

import os

def switch_debug_mode(current):
    return not current

def analyze_input(user_input, debug_mode):
    match user_input.lower():
        case "debug":
            debug_mode = switch_debug_mode(debug_mode)
            print(f"{COLORS['BOLD']}🔁 Debug mode switched to: {COLORS['GREEN']}{'Enabled' if debug_mode else 'Disabled'}\n{COLORS['RESET']}")
        case "exit":
            print(f"\n{COLORS['BOLD']}🤖 Goodbye!{COLORS['RESET']}\n")
            return True, debug_mode
        case "help":
            print("Available commands:")
            print(f"- {COLORS['BOLD']}'debug'{COLORS['RESET']}: Toggle debug mode")
            print(f"- {COLORS['BOLD']}'exit'{COLORS['RESET']}: Close the chat\n")
            print(f"- {COLORS['BOLD']}'help'{COLORS['RESET']}: Show this command list")
            print(f"- {COLORS['BOLD']}'reset'{COLORS['RESET']}: Start a new conversation")
        case "reset":
            return False, debug_mode
    return None, debug_mode

def start_chat(debug_mode):
    os.system('clear')
    print(f"{COLORS['BOLD']}🤖 Welcome to Xavion AI 🤖\n{COLORS['RESET']}Write 'help' for a list of commands, or 'exit' to finish.\n")

    conversation_history = ""
    #response_mode = "default"

    while True:
        user_input = input(">> ").strip()

        if user_input.lower() in USER_COMMANDS:
            user_command, debug_mode = analyze_input(user_input, debug_mode)
            if user_command is not None:
                return user_command

        else:
            instruction, intent = build_prompt(user_input, debug_mode, response_mode=None)
            
            if debug_mode:
                print(f"{COLORS['BOLD']}📝 Generating response...{COLORS['RESET']}")

            response = generate_response(instruction, intent, conversation_history, user_input)

            conversation_history += f"\nUser: {user_input}\nAI: {response}"