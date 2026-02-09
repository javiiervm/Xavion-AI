from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import BaseCallbackHandler

from backend.key_variables import TEMPLATES, COLORS

import sys

# Move CustomStreamingHandler to CLI frontend later or keep it as an option
# For now, we make generate_response accept callbacks

def get_model(callbacks=None):
    return OllamaLLM(
        model="llama3.1",
        callbacks=callbacks,
        num_ctx=2048,
        num_predict=512
    )

def generate_response(instruction, intent, conversation_history, user_input, keywords, callbacks=None):
    template = TEMPLATES[intent]
    params = {
        "instruction": instruction,
        "conversation_history": conversation_history,
        "question": user_input
    }

    if intent == "math":
        params["expressions"] = ", ".join(keywords)
    elif intent == "default":
        params["knowledge"] = "Xavion AI: Un asistente inteligente, útil y natural. / A smart, helpful, and natural assistant."
    
    prompt = ChatPromptTemplate.from_template(template)
    model = get_model(callbacks=callbacks)
    chain = prompt | model
    response = chain.invoke(params)
    return response