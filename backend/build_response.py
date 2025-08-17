from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

from backend.key_variables import TEMPLATES

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

model = OllamaLLM(
    model="llama3.1",
    callbacks=[CustomStreamingHandler()],
    num_ctx=2048,
    num_predict=512
)

def generate_response(instruction, intent, conversation_history, user_input):
    template = TEMPLATES[intent]
    params = {
        "instruction": instruction,
        "conversation_history": conversation_history,
        "question": user_input
    }

    if intent == "conversation":
        params["knowledge"] = "Your name is Xavion AI, you are an AI assistant that answers questions, helps with tasks or just have a conversation with users."
    else:
        params["knowledge"] = ""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    response = chain.invoke(params)
    return response