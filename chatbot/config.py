GENERATION_CONFIG = {
    "mode": "default",  # can be "default", "creative" or "precise"
    "default": {
        "max_length": 128,
        "min_length": 8,
        "top_p": 0.9,
        "do_sample": True
    },
    "creative": {
        "do_sample": True,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "max_length": 512,
    },
    "precise": {
        "do_sample": False,
        "num_beams": 3,
        "early_stopping": True,
        "max_length": 512,
    }
}

BOT_IDENTITY = {
    "name": "Xavion",
    "purpose": "I am an AI assistant here to help users understand concepts and answer questions.",
    "rules": [
        "Never repeat the user's input nor your last answer.",
        "Always end your response with a follow-up question to keep the conversation going.",
        "Be helpful, polite, and clear in your explanations.",
        "Stick to factual information.",
        "If you don't know something, admit it politely and ask the user for clarification."
    ]
}

BASE_RULES = (
    "Do not repeat the user's input. "
    "Use the knowledge provided. "
    "Always end with a follow-up question. "
    "Be clear and concise. "
    "If you don't know the answer, say so politely."
)

def switch_generation_mode():
    current = GENERATION_CONFIG["mode"]
    if current == "default":
        GENERATION_CONFIG["mode"] = "precise"
    elif current == "precise":
        GENERATION_CONFIG["mode"] = "creative"
    elif current == "creative":
        GENERATION_CONFIG["mode"] = "default"



"""
    PARAMETER INFO

    Generate reponse with controlled sampling
    output_tokens = model.generate(
        input_tokens,           # Input tensor with the prompt's tokens
        max_length = 512,       # Max tokens that can be generated (input + output)
        do_sample = True,       # If true, uses random sampling instead of greedy decoding
        temperature = 0.7,      # Manages how random predicitions are
        top_p = 0.9,            # Applies nucleus sampling: chooses inside a group of tokens with an accumulated probability >= 0.9
        top_k = 50              # Limits next token to the 50 more probable
                                # repetition_penalty=..., used to punish for word repetition
                                # num_return_sequences=1, how many answers generate (default 1)
    )
"""
