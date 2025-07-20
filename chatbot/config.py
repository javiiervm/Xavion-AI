GENERATION_CONFIG = {
    "mode": "creative",  # can be "creative" or "precise"
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

def switch_generation_mode():
    current = GENERATION_CONFIG["mode"]
    GENERATION_CONFIG["mode"] = "precise" if current == "creative" else "creative"



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
