from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from chatbot.config import GENERATION_CONFIG

SEP = "<|endoftext|>"   # Special token used as separator in GODEL

def prepare_input(instruction, knowledge, conversation):
    """
    Formats the input according to the format GODEL is expecting

    Args:
        instruction (str): What the model has to do
        knowledge (str): External information (may be empty)
        conversation (str): Recent dialogue with the user

    Returns:
        str: input formatted as text
    """
    inpt = f"Instruction: {instruction} {SEP} Knowledge: {knowledge} {SEP} Conversation: {conversation}"
    return inpt

def generate_response(model, tokenizer, input_text, device="cpu"):
    """
    Generates a reponse based on the structured input

    Args:
        model: AI model already loaded (GODEL in this case)
        tokenizer: compatible tokenizer
        input_text (str): Input formatted as a string
        device (str): "cuda" or "cpu"

    Returns:
        str: Generated reponse by the model
    """

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