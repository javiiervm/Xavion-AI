from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

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
    template = """
{instruction}

This is some information about you: {ai_info}

Here are some concepts you should know: {knowledge}

Here is the conversation history: {conversation_history}

Question: {question}

Answer:
"""
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    response = chain.invoke({
        "instruction": instruction,
        "ai_info": "Your name is Xavion AI, you are an AI assistant that answers questions, helps with tasks or just have a conversation with users.",
        "knowledge": "",
        "conversation_history": conversation_history,
        "question": user_input
    })
    return response