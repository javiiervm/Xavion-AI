from chatbot.model import load_model_and_tokenizer
from chatbot.logic import prepare_input, generate_response, SEP
from chatbot.config import (
    GENERATION_CONFIG,
    switch_generation_mode,
    BOT_IDENTITY
)
from chatbot.utils import (
    detect_intent,
    load_knowledge,
    extract_keyword,
    get_knowledge,
    load_user_memory,
    detect_manual_definition,
    format_identity
)

import os
import json

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"

USER_MEMORY_PATH = "data/user_memory.json"

KNOWLEDGE_DB = load_knowledge()
USER_MEMORY = load_user_memory(USER_MEMORY_PATH)

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
                break
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
                start_chat(model, tokenizer, device, debug_mode)
                return
            case _:
                # Guardar entrada del usuario
                conversation_history.append(f"User: {user_input}")
                recent_conversation = f" {SEP} ".join(conversation_history[-6:])

                # Detectar intención
                intent = detect_intent(user_input)
                if debug_mode:
                    print(f"{BOLD}🔎 Intent detected: {GREEN}{intent}{RESET}")

                # Reglas base de comportamiento
                BASE_RULES = (
                    "Do not repeat the user's input. "
                    "Use the knowledge provided. "
                    "Always end with a follow-up question. "
                    "Be clear and concise. "
                    "If you don't know the answer, say so politely."
                )

                # Construcción de instrucción
                instruction_map = {
                    "definition": f"Define the given term in a full sentence. {BASE_RULES}",
                    "knowledge_query": f"Answer the user's factual question. {BASE_RULES}",
                    "greeting": "Respond to the user's greeting.",
                    "emotional": "Respond empathetically.",
                    "conversation": "Continue the conversation."
                }
                instruction = instruction_map.get(intent, "Continue the conversation.")

                # Obtener conocimiento del término
                term_knowledge = ""
                if intent in ["definition", "knowledge_query"]:
                    keyword = extract_keyword(user_input)
                    term_knowledge = get_knowledge(keyword, KNOWLEDGE_DB, USER_MEMORY)
                    if debug_mode:
                        print(f"{BOLD}🔎 Keyword: {GREEN}{keyword}{RESET}")
                        print(f"{BOLD}🔎 Knowledge: {GREEN}{term_knowledge or 'None'}{RESET}")

                if intent in ["definition", "knowledge_query"] and not term_knowledge:
                    instruction += " If the concept is unknown, say so politely and ask the user to explain it."

                # Construir prompt para GODEL
                input_text = prepare_input(instruction, term_knowledge, recent_conversation)
                if debug_mode:
                    print(f"{BOLD}📝 Instruction: {GREEN}{instruction}{RESET}")

                # Generar respuesta
                response = generate_response(model, tokenizer, input_text, device=device)

                # Guardar conocimiento si el usuario definió algo manualmente
                defined_term = detect_manual_definition(user_input)
                if defined_term and defined_term not in USER_MEMORY:
                    USER_MEMORY[defined_term] = {"knowledge": user_input.strip()}
                    with open(USER_MEMORY_PATH, "w", encoding="utf-8") as f:
                        json.dump(USER_MEMORY, f, ensure_ascii=False, indent=2)
                    print(f"\n{BOLD}📚 Saved new knowledge: {GREEN}'{defined_term}'{RESET}")

                # Mostrar respuesta y actualizar historial
                print(f"\n{BOLD}🤖 {response}{RESET}\n")
                conversation_history.append(f"Bot: {response}")

if __name__ == "__main__":
    print("Loading ProtoAI, please wait...")
    model, tokenizer, device = load_model_and_tokenizer()
    debug_mode = False
    start_chat(model, tokenizer, device, debug_mode)