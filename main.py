from chatbot.model import load_model_and_tokenizer
from chatbot.config import (
    GENERATION_CONFIG,
    switch_generation_mode
)
from chatbot.logic import generate
from chatbot.utils import (
    load_knowledge, 
    load_memory,
    extract_keywords,
    extract_teaching,
    extract_math_expression,
    evaluate_math_expression,
    delete_stopwords
)
from chatbot.keywords import (
    INSTRUCTION_MAP
)
import chatbot.Modules.Command as cmnd

import os
import json
import math

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"

# AI model that is going to be used (Microsoft GODEL)
MODEL_PATH = "./GODEL-v1_1-large-seq2seq"
DEVICE = "cpu"  # Device can be 'cpu', 'cuda' or None (auto)

MEMORY_PATH = "data/memory.json"
KNOWLEDGE_PATH = "data/knowledge.json"

KNOWLEDGE_DB = load_knowledge(KNOWLEDGE_PATH)
USER_MEMORY = load_memory(MEMORY_PATH)

USER_COMMANDS = ["exit", "help", "mode", "switch", "mode:default", "mode:creative", "mode:precise", "debug", "reset"]

def switch_debug_mode(current):
    return not current

def analyze_input(user_input, debug_mode):
    match user_input.lower():
        case "exit":
            print(f"\n{BOLD}🤖 Goodbye!{RESET}\n")
            return True, debug_mode
        case "help":
            print("Available commands:")
            print(f"- {BOLD}'help'{RESET}: Show this command list")
            print(f"- {BOLD}'mode'{RESET}: Show current generation mode")
            print(f"- {BOLD}'mode:default' / 'mode:creative' / 'mode:precise'{RESET}: Set response style")
            print(f"- {BOLD}'switch'{RESET}: Toggle generation mode")
            print(f"- {BOLD}'debug'{RESET}: Toggle debug mode")
            print(f"- {BOLD}'reset'{RESET}: Start a new conversation")
            print(f"- {BOLD}'exit'{RESET}: Close the chat\n")
        case "mode":
            print(f"{BOLD}Current generation mode: {GREEN}{GENERATION_CONFIG['mode']}\n{RESET}")
        case "switch":
            switch_generation_mode()
            print(f"{BOLD}🔁 Generation mode switched to: {GREEN}{GENERATION_CONFIG['mode']}\n{RESET}")
        case command if command.startswith("mode:"):
            requested = command.split(":")[1]
            if requested in ["default", "creative", "precise"]:
                GENERATION_CONFIG["mode"] = requested
                print(f"{BOLD}✅ Generation mode set to: {GREEN}{requested}\n{RESET}")
            else:
                print(f"{BOLD}⚠️ Invalid mode. Use 'creative' or 'precise'.\n{RESET}")
        case "debug":
            debug_mode = switch_debug_mode(debug_mode)
            print(f"{BOLD}🔁 Debug mode switched to: {GREEN}{'Enabled' if debug_mode else 'Disabled'}\n{RESET}")
        case "reset":
            return False, debug_mode
    return None, debug_mode

def start_chat(model, tokenizer, device, debug_mode):
    os.system("clear")
    print(f"{BOLD}🤖 Welcome to Xavion AI 🤖\n{RESET}Write 'help' for a list of commands, or 'exit' to finish.\n")

    conversation_history = []

    while True:
        user_input = input(">> ").strip()
        
        if user_input.lower() in USER_COMMANDS:
            user_command, debug_mode = analyze_input(user_input, debug_mode)
            if user_command is not None:
                return user_command
        
        else:
            # Update conversation history
            conversation_history.append(f"User said '{user_input}'")

            # Create a new command
            current_command = cmnd.Command()

            # Build the proper command from user input
            current_command.build_chatbot_command(user_input, KNOWLEDGE_DB, USER_MEMORY, MEMORY_PATH, debug_mode)

            if debug_mode:
                print(f"{BOLD}📝 Generating response...{RESET}")            

            # Get only the most recent conversation entries
            recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history

            # Generate a response
            response = generate(current_command.get_instruction(), current_command.get_knowledge(), recent_history, model, tokenizer)

            # Update conversation history
            conversation_history.append(f"Bot answered '{response}'")

            # Print response
            print(f"\n{BOLD}🤖 {response}{RESET}\n")


if __name__ == "__main__":
    print("Loading Xavion AI, please wait...", flush=True)
    model, tokenizer, device = load_model_and_tokenizer(MODEL_PATH, DEVICE)
    debug_mode = False
    chat_finished = False
    while not chat_finished:
        chat_finished = start_chat(model, tokenizer, device, debug_mode)