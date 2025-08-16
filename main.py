from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

from aux_funcs.build_prompt import build_prompt, detect_intent
from config.colors import RESET, BOLD, GREEN, RED, YELLOW

import os

USER_COMMANDS = ["debug", "exit", "help", "reset"]

class CustomStreamingHandler(BaseCallbackHandler):
    def __init__(self):
        self.first_token = True

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.first_token:
            print("\n🤖 ", end="", flush=True)
            self.first_token = False
        print(token, end="", flush=True)

    def on_llm_end(self, *args, **kwargs):
        print("\n")
        self.first_token = True


template = """
{instruction}

This is some information about you: {ai_info}

Here are some concepts you should know: {knowledge}

Here is the conversation history: {conversation_history}

Question: {question}

Answer:
"""

model = OllamaLLM(
    model="llama3.1",
    callbacks=[CustomStreamingHandler()],
    num_ctx=2048,
    num_predict=512
)
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

def switch_debug_mode(current):
    return not current

def analyze_input(user_input, debug_mode):
    match user_input.lower():
        case "debug":
            debug_mode = switch_debug_mode(debug_mode)
            print(f"{BOLD}🔁 Debug mode switched to: {GREEN}{'Enabled' if debug_mode else 'Disabled'}\n{RESET}")
        case "exit":
            print(f"\n{BOLD}🤖 Goodbye!{RESET}\n")
            return True, debug_mode
        case "help":
            print("Available commands:")
            print(f"- {BOLD}'debug'{RESET}: Toggle debug mode")
            print(f"- {BOLD}'exit'{RESET}: Close the chat\n")
            print(f"- {BOLD}'help'{RESET}: Show this command list")
            print(f"- {BOLD}'reset'{RESET}: Start a new conversation")
        case "reset":
            return False, debug_mode
    return None, debug_mode

def start_chat(debug_mode):
    os.system('clear')

    print(f"{BOLD}🤖 Welcome to Xavion AI 🤖\n{RESET}Write 'help' for a list of commands, or 'exit' to finish.\n")

    conversation_history = ""
    response_mode = "default"
    #knowledge_db = load_knowledge()

    while True:
        user_input = input(">> ").strip()

        if user_input.lower() in USER_COMMANDS:
            user_command, debug_mode = analyze_input(user_input, debug_mode)
            if user_command is not None:
                return user_command

        else:
            knowledge = ""
            intent = detect_intent(user_input, debug_mode)
            instruction = build_prompt(intent, debug_mode, response_mode)
            
            if debug_mode:
                print(f"{BOLD}📝 Generating response...{RESET}")

            response = chain.invoke(
                {"instruction": instruction, 
                    "ai_info": "Your name is Xavion AI, you are an AI assistant that answers questions, helps with tasks or just have a conversation with users.",
                    "knowledge": knowledge, 
                    "conversation_history": conversation_history, 
                    "question": user_input}
            )

            conversation_history += f"\nUser: {user_input}\nAI: {response}"

if __name__ == "__main__":
    print("Loading Xavion AI, please wait...", flush=True)
    debug_mode = False
    chat_finished = False
    while not chat_finished:
        chat_finished = start_chat(debug_mode)