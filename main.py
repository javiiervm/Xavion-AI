from chatbot.model import load_model_and_tokenizer
from chatbot.config import (
    GENERATION_CONFIG,
    switch_generation_mode
)
from chatbot.logic import (
    prepare_input,
    generate_response,
    SEP
)
from chatbot.utils import (
    load_knowledge, 
    load_memory
)

import os

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

def switch_debug_mode(current):
    return not current

def start_chat(model, tokenizer, device, debug_mode):
    os.system("clear")
    print(f"{BOLD}🤖 Welcome to ProtoAI 🤖\n{RESET}Write 'help' for a list of commands, or 'exit' to finish.\n")

    conversation_history = []

    while True:
        user_input = input(">> ").strip()

        match user_input.lower():
            case "exit":
                print(f"\n{BOLD}🤖 Goodbye!{RESET}\n")
                return True
            case "help":
                print("Available commands:")
                print(f"- {BOLD}'help'{RESET}: Show this command list")
                print(f"- {BOLD}'mode'{RESET}: Show current generation mode")
                print(f"- {BOLD}'mode:creative' / 'mode:precise'{RESET}: Set response style")
                print(f"- {BOLD}'switch'{RESET}: Toggle generation mode")
                print(f"- {BOLD}'debug'{RESET}: Toggle debug mode")
                print(f"- {BOLD}'reset'{RESET}: Start a new conversation")
                print(f"- {BOLD}'exit'{RESET}: Close the chat")
            case "mode":
                print(f"{BOLD}Current generation mode: {GREEN}{GENERATION_CONFIG['mode']}\n{RESET}")
            case "switch":
                switch_generation_mode()
                print(f"{BOLD}🔁 Generation mode switched to: {GREEN}{GENERATION_CONFIG['mode']}\n{RESET}")
            case command if command.startswith("mode:"):
                requested = command.split(":")[1]
                if requested in ["creative", "precise"]:
                    GENERATION_CONFIG["mode"] = requested
                    print(f"{BOLD}✅ Generation mode set to: {GREEN}{requested}\n{RESET}")
                else:
                    print(f"{BOLD}⚠️ Invalid mode. Use 'creative' or 'precise'.\n{RESET}")
            case "debug":
                debug_mode = switch_debug_mode(debug_mode)
                print(f"{BOLD}🔁 Debug mode switched to: {GREEN}{'Enabled' if debug_mode else 'Disabled'}\n{RESET}")
            case "reset":
                return False
            case _:
                # Add user input to conversation history
                conversation_history.append(f"User: {user_input}")
                recent_conversation = f" {SEP} ".join(conversation_history[-6:])
                
                # Detect user intention
                intent = None   # Call the detecting function
                if debug_mode:
                    print(f"{BOLD}🔎 Intent detected: {GREEN}{intent}{RESET}")

                # Instruction built
                instruction_map = {
                    "definition": f"Define the given term in a full sentence.",
                    "conversation": f"Continue the conversation or ask a question according to what the user said."
                }
                instruction = instruction_map.get(intent, "Respond to the user with a coherent, relevant, and original message to keep the conversation going.")

                # Search for knowledge
                knowledge = ""
                
                # Build prompt for GODEL
                input_text = prepare_input(instruction, knowledge, recent_conversation)
                if debug_mode:
                    print(f"{BOLD}📝 Instruction: {GREEN}{instruction}{RESET}")

                # Generate a response
                response = generate_response(model, tokenizer, input_text, device=device)

                # Update convsersation history
                conversation_history.append(f"Bot: {response}")

                # Print response
                print(f"\n{BOLD}🤖 {response}{RESET}\n")


if __name__ == "__main__":
    print("Loading ProtoAI, please wait...", flush=True)
    model, tokenizer, device = load_model_and_tokenizer(MODEL_PATH, DEVICE)
    debug_mode = False
    chat_finished = False
    while not chat_finished:
        chat_finished = start_chat(model, tokenizer, device, debug_mode)