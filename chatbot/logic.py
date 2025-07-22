from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from chatbot.config import GENERATION_CONFIG

def generate(instruction, knowledge, dialog, model, tokenizer):
    """
    Generates a response using a language model based on provided instruction, knowledge and dialog history.
    
    Args:
        instruction (str): The instruction/task for the model to follow
        knowledge (str): Additional knowledge/context to inform the response
        dialog (list): List of previous conversation turns
        model: The language model used for generation
        tokenizer: The tokenizer associated with the model
    
    Returns:
        str: The generated response from the model
    """
    # Get generation configuration mode and parameters from config
    mode = GENERATION_CONFIG["mode"]
    generate_params = GENERATION_CONFIG[mode]
    
    # Add knowledge marker if knowledge is provided
    if knowledge != '':
        knowledge = '[KNOWLEDGE] ' + knowledge
    
    # Join dialog history with EOS separator
    dialog = ' EOS '.join(dialog)
    
    # Construct the full query by combining instruction, context and knowledge
    query = f"{instruction} [CONTEXT] {dialog} {knowledge}"
    
    # Tokenize the query into model input format
    # return_tensors="pt" returns PyTorch tensors
    input_ids = tokenizer(f"{query}", return_tensors="pt").input_ids
    
    # Generate response using the model with specified parameters
    outputs = model.generate(input_ids, **generate_params)
    
    # Decode the generated token ids back to text
    # skip_special_tokens=True removes special tokens like PAD, EOS etc.
    output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return output






"""

|=================|
|LOGIC INFORMATION|
|=================|


from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from chatbot.config import GENERATION_CONFIG

SEP = "<|endoftext|>"   # Special token used as separator in GODEL

def prepare_input(instruction, knowledge, conversation):
    inpt = f"Instruction: {instruction} {SEP} Knowledge: {knowledge} {SEP} Conversation: {conversation}"
    return inpt

def generate_response(model, tokenizer, input_text, device="cpu"):
    # Tokenize input: convert the text to a sequence of token IDs that the model can process
    input_tokens = tokenizer.encode(
        input_text,             # Text that is going to be converted
        return_tensors="pt"     # Returns a pytorch tensor (pt), required by the model
                                # Optional: max_length, to limit the number of tokens
                                # Optional: truncation=True, to enable automatic truncation if input is too long
                                # Optional: padding="max_length", to add tokens if we always want same size
                                # add_special_tokens=True (default True), adds tokens the model may need
    ).to(device)    # Moves the tensor (tokenized input) to the same computing unit than the model, "cpu" for processor or "cuda" to gpu

    # Get generation config based on current mode
    mode = GENERATION_CONFIG["mode"]
    generate_params = GENERATION_CONFIG[mode]

    # Generate reponse with controlled sampling
    output_tokens = model.generate(
        input_tokens,           # Input tensor with the prompt's tokens
        **generate_params       # Parameters for generation
    )

    # Converts the sequence of generated tokens to human-understandable text
    reponse = tokenizer.decode(
        output_tokens[0],           # Sequence of generated tokens
        skip_special_tokens = True  # Deletes special tokens that we may not need
                                    # clean_up_tokenization_spaces=True, deletes aditional spaces introduced by the tokenizer
                                    # output_ids, output tensor from generate()
        )
    return reponse

"""