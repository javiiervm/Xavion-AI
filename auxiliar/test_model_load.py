
"""
Script to test the loading of the model and tokenizer.
"""


from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "microsoft/GODEL-v1_1-base-seq2seq"

print("🔁 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
print("✅ Tokenizer loaded.")

print("🔁 Loading model...")
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
print("✅ Model loaded.")