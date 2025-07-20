from chatbot.model import load_model_and_tokenizer
from chatbot.logic import prepare_input, generate_response
from chatbot.config import GENERATION_CONFIG, switch_generation_mode
import os

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"

def start_chat(model, tokenizer, device):
    os.system("clear")
    print(f"{BOLD}🤖 Welcome to ProtoAI 🤖\n{RESET}Write 'help' for a list of commands, or 'exit' to finish.\n")

    # Conversation variables
    knowledge = ""  # External information
    conversation_history = []

    while True:
        user_input = input(">> ").strip()

        # Evaluate user input for key words
        match user_input.lower():
            case "exit":
                print(f"\n{BOLD}🤖 Goodbye!{RESET}\n")
                break
            case "help":
                print("Available commands:")
                print(f"- {BOLD}'help'{RESET}: Show this command list")
                print(f"- {BOLD}'mode'{RESET}: Show current generation mode")
                print(f"- {BOLD}'mode:creative' / 'mode:precise'{RESET}: Set response style")
                print(f"- {BOLD}'switch'{RESET}: Toggle generation mode between creative and precise")
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
            case "reset":
                start_chat(model, tokenizer, device)
                return
            case _:
                # Update conversation history
                conversation_history.append(f"User: {user_input}")
                context = " ".join(conversation_history[-3:])   # Last 3 interactions as provided context

                # Prepare structured input
                input_text = prepare_input(
                    instruction="act like a friendly assistant and respond appropriately",
                    knowledge=knowledge,
                    conversation=context
                )

                # Generate reponse
                reponse = generate_response(model, tokenizer, input_text, device)

                # Show reponse and update history
                print(f"\n{BOLD}🤖 ", reponse)
                print(f"{RESET}")

                # Update conversation history with bot's answer
                conversation_history.append(f"Bot: {reponse}")

if __name__ == "__main__":
    print("Loading ProtoAI, please wait...")
    # Loads model, tokenizer and device (CPU or GPU)
    model, tokenizer, device = load_model_and_tokenizer()
    start_chat(model, tokenizer, device)