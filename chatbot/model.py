from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

def load_model_and_tokenizer(MODEL_PATH, device=None):
    """
    This function loads the GODEL model and its tokenizer from Hugging Face
    
    Args:
        MODEL_PATH (str): Path to the model on Hugging Face
        device (str): "cuda" or "cpu", if not specified it is automatically detected

    Returns:
        model (transformers.PreTrainedModel)
        tokenizer (transformers.PreTrainedTokenizer)
        device (torch.device)
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
    model.to(device)

    return model, tokenizer, device