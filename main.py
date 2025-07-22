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
    load_memory,
    extract_keywords,
    detect_intent,
    extract_teaching,
    extract_math_expression,
    evaluate_math_expression,
    delete_stopwords
)

from chatbot.testLogic import generate

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
                # Update conversation history
                conversation_history.append(f"'{user_input}'")

                # Detect user intent
                intent = detect_intent(user_input, [])
                if debug_mode:
                    print(f"{BOLD}🔎 Intent detected: {GREEN}{intent}{RESET}")

                # Build the instruction
                instruction_map = {
                    "definition": "Define the term in a clear sentence with a short example if possible.",
                    "teaching": "Thank the user for the new information and ask something related.",
                    "math": "Answer the math question telling the result of the expression. Avoid repeating the question.",
                    "conversation": "Reply naturally and keep the conversation going with a follow-up question."
                }
                instruction = 'Instruction: ' + instruction_map.get(intent, "given a dialog context, you need to response empathically.")
                if debug_mode:
                    print(f"{BOLD}📝 Instruction: {GREEN}{instruction}{RESET}")

                # Leave the knowldge empty
                knowledge = ''

                # Extract keywords from user input
                keywords = extract_keywords(user_input)
                
                if intent == "math":
                    expression = extract_math_expression(user_input, debug_mode)
                    if debug_mode:
                        print(f"{BOLD}🔎 Expression detected: {GREEN}{expression}{RESET}")
                    if expression:
                        result = evaluate_math_expression(expression, debug_mode)
                        if debug_mode:
                            print(f"{BOLD}🔎 Result: {GREEN}{result}{RESET}")
                        knowledge = f"The result of the expression '{expression}' is {result}."
                    else:
                        intent = detect_intent(user_input, ["math"])
                        instruction = 'Instruction: ' + instruction_map.get(intent, "given a dialog context, you need to response empathically.")
                        if debug_mode:
                            print(f"{BOLD}⚠️ No math expression detected in user input.{RESET}")
                            print(f"{BOLD}🔎 Intent detected: {GREEN}{intent}{RESET}")
                            print(f"{BOLD}📝 New instruction: {GREEN}{instruction}{RESET}")
                
                if intent != "math":
                    # Search for knowledge
                    if keywords:
                        if debug_mode:
                            print(f"{BOLD}🔎 Keywords detected: {GREEN}{keywords}{RESET}")
                        for keyword in keywords:
                            if keyword in KNOWLEDGE_DB:
                                if debug_mode:
                                    print(f"🔎 Keyword '{keyword}': {KNOWLEDGE_DB[keyword]["knowledge"]}.{RESET}")
                                knowledge += KNOWLEDGE_DB[keyword]["knowledge"] + "\n"
                            elif keyword in USER_MEMORY:
                                if debug_mode:
                                    print(f"🔎 Keyword '{keyword}': {USER_MEMORY[keyword]["knowledge"]}.{RESET}")
                                knowledge += USER_MEMORY[keyword]["knowledge"] + "\n"
                            else:
                                if debug_mode:
                                    print(f"{BOLD}⚠️ Keyword '{keyword}' not found in knowledge base.{RESET}")
                    else:
                        if debug_mode:
                            print(f"{BOLD}⚠️ No keywords detected in user input.{RESET}")

                if debug_mode:
                    print(f"{BOLD}📝 Generating response...{RESET}")

                if intent == "teaching":
                    # Add to memory new things learnt
                    term, definition = extract_teaching(user_input)
                    if term and definition:
                        term = delete_stopwords(term)
                        USER_MEMORY[term] = {"knowledge": definition}
                        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
                            json.dump(USER_MEMORY, f, ensure_ascii=False, indent=2)
                        print(f"\n{BOLD}✅ New knowledge added to memory: {GREEN}{term}{RESET}")

                # Generate a response
                response = generate(instruction, knowledge, conversation_history, model, tokenizer)

                # Update conversation history
                conversation_history.append(f"'{response}'")

                # Print response
                print(f"\n{BOLD}🤖 {response}{RESET}\n")


if __name__ == "__main__":
    print("Loading ProtoAI, please wait...", flush=True)
    model, tokenizer, device = load_model_and_tokenizer(MODEL_PATH, DEVICE)
    debug_mode = False
    chat_finished = False
    while not chat_finished:
        chat_finished = start_chat(model, tokenizer, device, debug_mode)