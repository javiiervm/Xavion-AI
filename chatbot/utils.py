import re
import json
import os

STOPWORDS = {
    # Artículos
    "a", "an", "the",
    # Pronombres personales y posesivos
    "i", "me", "you", "he", "him", "she", "her", "it", "we", "us", "they", "them",
    "my", "your", "his", "her", "its", "our", "their",
    # Pronombres reflexivos
    "myself", "yourself", "himself", "herself", "itself", "ourselves", "yourselves", "themselves",
    # Pronombres relativos e interrogativos
    "who", "whom", "whose", "which", "what", "where", "when", "why", "how",
    # Auxiliares (to be, to have, to do) y modales
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    # Conjunciones
    "and", "or", "but", "nor", "so", "for", "yet",
    # Preposiciones comunes
    "in", "on", "at", "by", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from", "up",
    "down", "over", "under", "again", "further", "then", "once",
    # Partículas y adverbios comunes
    "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "not", "only", "own", "same", "so", "than", "too", "very",
    # Conectores y palabras de relleno
    "also", "just", "even", "still", "because", "though", "although", "however",
    # Números escritos
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    # Contracciones comunes
    "i'm", "you're", "he's", "she's", "it's", "we're", "they're",
    "i've", "you've", "we've", "they've",
    "i'd", "you'd", "he'd", "she'd", "we'd", "they'd",
    "i'll", "you'll", "he'll", "she'll", "we'll", "they'll",
    "isn't", "aren't", "wasn't", "weren't",
    "hasn't", "haven't", "hadn't",
    "don't", "doesn't", "didn't",
    "won't", "wouldn't", "shan't", "shouldn't", "can't", "cannot", "couldn't",
    "mustn't", "mightn't", "needn't",
    # Otros
    "also", "via", "per", "etc", "vs"
}

def load_knowledge(knowledge_path):
    with open(knowledge_path, "r", encoding="utf-8") as f:
        KNOWLEDGE_DB = json.load(f)
        return KNOWLEDGE_DB

def load_memory(memory_path):
    """
    Loads the user's memory from a JSON file.

    Args:
        memory_path (str): The path to the user's memory file.

    Returns:
        dict: The user's memory.
    """
    MEMORY = {}
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    MEMORY = json.loads(content)
        except json.JSONDecodeError:
            print(f"⚠️ The file {memory_path} has an invalid JSON format. An empty dictionary will be used.")
    return MEMORY

def extract_keywords(text):
    """
    Tries to extract the keyword from user input.
    Uses simple regular expressions to identify this central word.

    Args:
        text (str): The user's input.

    Returns:
        str: The extracted keyword or None if not found.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    keywords = [word for word in words if word not in STOPWORDS]
    return keywords if keywords else None