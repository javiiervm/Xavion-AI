from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import BaseCallbackHandler

from backend.key_variables import TEMPLATES, COLORS
from backend.ui_components import console

import sys

class CustomStreamingHandler(BaseCallbackHandler):
    def __init__(self):
        self.first_token = True

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.first_token:
            # Start bold text using original COLORS tag
            print(f"{COLORS['BOLD']}", end="", flush=True)
            self.first_token = False
        print(token, end="", flush=True)

    def on_llm_end(self, *args, **kwargs):
        # End bold text using original COLORS tag
        print(f"{COLORS['RESET']}", end="\n", flush=True)
        self.first_token = True

model = OllamaLLM(
    model="llama3.1",
    callbacks=[CustomStreamingHandler()],
    num_ctx=2048,
    num_predict=512
)

def generate_response(instruction, intent, conversation_history, user_input, keywords):
    template = TEMPLATES[intent]
    params = {
        "instruction": instruction,
        "conversation_history": conversation_history,
        "question": user_input
    }

    if intent == "math":
        params["expressions"] = ", ".join(keywords)
    elif intent == "default":
        params["knowledge"] = "Your name is Xavion AI, you are an AI assistant that answers questions, helps with tasks or just have a conversation with users."
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    response = chain.invoke(params)
    return response