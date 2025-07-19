from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "microsoft/GODEL-v1_1-base-seq2seq"

print("🔁 Cargando tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
print("✅ Tokenizer cargado.")

print("🔁 Cargando modelo...")
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
print("✅ Modelo cargado.")