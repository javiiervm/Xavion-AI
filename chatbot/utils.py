import re
import json
import os

DEFINITION_KEY_WORDS = [
    "what is", "what's", "define", "definition", "explain", "explanation",
    "meaning of", "significado de", "¿qué es", "definir", "definición",
    "explicar", "explicación", "describe", "describir", "characterize",
    "¿cómo definirías", "how would you define", "interpret", "interpretar"
]

GREETING_KEY_WORDS = [
    "hello", "hi", "hey", "hola", "buenos días", "buenas tardes", "buenas noches",
    "qué tal", "¿cómo estás", "howdy", "greetings", "saludos", "yo", "sup",
    "¿qué onda", "qué pasa"
]

EMOTIONAL_KEY_WORDS = [
    "happy", "sad", "angry", "excited", "calm", "anxious", "confused",
    "emotional", "emotion", "mood", "stress", "anxiety", "depression",
    "tired", "sleepy", "upset", "joyful", "frustrated", "bored",
    "nervous", "relaxed", "enthusiastic", "melancholic", "furious",
    "contento", "triste", "enojado", "emocionado", "tranquilo",
    "ansioso", "confundido", "estresado", "agotado", "aburrido",
    "entusiasmado", "melancólico", "furioso"
]

YES_NO_KEY_WORDS = [
    # Modal verbs and direct yes/no
    "yes", "no", "si", "sí", "yeah", "yep", "nop", "nope",
    "maybe", "tal vez", "quizás", "quizá",
    # Question starters often leading to yes/no
    "is", "are", "am", "was", "were", "do", "does", "did",
    "can", "could", "will", "would", "should", "have", "has", "had",
    "¿es", "¿está", "¿hay", "¿puedo", "¿podría", "¿debería",
    "¿tengo", "¿tiene", "¿has", "¿ha", "¿había",
    # Phrases that imply a yes/no answer
    "right?", "¿verdad?", "correct?", "¿correcto?", "okay?", "¿vale?",
    "any good?", "¿funciona?", "¿sirve?"
]

STOPWORDS = [
    # artículos, determinantes y pronombres demostrativos/interrogativos
    "a", "an", "the", "this", "that", "these", "those", "which", "whose",
    # pronombres personales y posesivos
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "her", "its", "our", "their", "yours", "ours", "theirs",
    # preposiciones
    "about", "above", "across", "after", "against", "along", "among", "around", "at",
    "before", "behind", "below", "beneath", "beside", "besides", "between", "beyond",
    "but", "by", "despite", "down", "during", "except", "for", "from", "in", "inside",
    "into", "like", "near", "of", "off", "on", "onto", "out", "over", "past", "per",
    "since", "through", "throughout", "till", "to", "toward", "towards", "under",
    "underneath", "until", "up", "upon", "with", "within", "without",
    # conjunciones y conectores
    "and", "or", "nor", "so", "yet", "if", "though", "although", "while",
    "because", "as", "until", "than",
    # adverbios muy comunes (que no son negación ni respuestas sí/no)
    "just", "only", "even", "also", "very", "too", "then", "there", "here",
    "again", "ever", "never", "always", "sometimes", "often",
    "rather", "quite", "yet",
    # cuantificadores
    "all", "any", "both", "each", "every", "either", "neither", "some", "such",
    "more", "most", "less", "least",
    # interrogativos (sin incluir “why”, “how”, “when”, etc., que ya están cubiertos en stopwords)
    "what", "who", "whose", "whom", "which", "where", "when"
]

def detect_intent(user_input):
    """
    Detects the intent of the user's input.

    Args:
        user_input (str): The user's input.

    Returns:
        str: The detected intent: 'greeting', 'definition', 'question', 'emotional', 'knowledge_query', or 'conversation'
    """
    text = user_input.lower().strip()

    # Greeting detection has top priority
    if any(greet in text for greet in GREETING_KEY_WORDS):
        return "greeting"

    # Emotional content
    if any(feeling in text for feeling in EMOTIONAL_KEY_WORDS):
        return "emotional"

    # Definition requests
    if any(keyword in text for keyword in DEFINITION_KEY_WORDS):
        return "definition"

    # General yes/no or fact-based questions
    if text.endswith("?") or any(text.startswith(kw + " ") for kw in YES_NO_KEY_WORDS):
        return "knowledge_query"

    # Default: conversation
    return "conversation"

def load_knowledge():
    with open("data/knowledge_clean.json", "r", encoding="utf-8") as f:
        KNOWLEDGE_DB = json.load(f)
        return KNOWLEDGE_DB

def load_user_memory(user_memory_path):
    """
    Loads the user's memory from a JSON file.

    Args:
        user_memory_path (str): The path to the user's memory file.

    Returns:
        dict: The user's memory.
    """
    USER_MEMORY = {}
    if os.path.exists(user_memory_path):
        try:
            with open(user_memory_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    USER_MEMORY = json.loads(content)
        except json.JSONDecodeError:
            print(f"⚠️ The file {user_memory_path} has an invalid JSON format. An empty dictionary will be used.")
    return USER_MEMORY

def extract_keyword(text):
    """
    Tries to extract the keyword from user input.
    Uses simple regular expressions to identify this central word.

    Args:
        text (str): The user's input.

    Returns:
        str: The extracted keyword or None if not found.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    stopwords = {"is", "a", "the", "what", "do", "does", "are", "can", "have", "has", "had", "why", "how", "when", "where", "who", "which", "that", "this", "it", "to", "in", "on", "for", "with", "of", "and", "or"}
    keywords = [word for word in words if word not in stopwords]
    return keywords[0] if keywords else None

def get_knowledge(keyword, knowledge_db, user_memory):
    """
    Retrieves knowledge based on the keyword.
    If the keyword is found in the user's memory or the knowledge database,
    returns the corresponding knowledge. Otherwise, returns an empty string.

    Args:
        keyword (str): The keyword to search for.
        knowledge_db (dict): The knowledge database.
        user_memory (dict): The user's memory.

    Returns:
        str: The retrieved knowledge or an empty string.
    """
    if keyword:
        if keyword in user_memory:
            return user_memory[keyword]["knowledge"]
        if keyword in knowledge_db:
            return knowledge_db[keyword]["knowledge"]
    return ""

def detect_manual_definition(user_input):
    """
    Detecta si el usuario está proporcionando una definición explícita.
    Excluye palabras de pregunta para evitar añadir términos como "what" al diccionario.
    """
    pattern = re.compile(r"^([A-Z]?[a-z]+) (is|are) (a|an|the)? .+")
    match = pattern.match(user_input.strip())
    if match:
        term = match.group(1).lower()
        # Verificar si el término es una palabra de pregunta o stopword
        question_words = {"what", "why", "how", "when", "where", "who", "which", "whose", "whom"}
        if term in question_words or term in STOPWORDS:
            return None
        return term
    return None

def format_identity(identity_config):
    """
    Convierte la identidad del bot en un string que puede usarse como Knowledge fijo.
    """
    rules = "\n".join([f"- {rule}" for rule in identity_config["rules"]])
    return (
        f"My name is {identity_config['name']}.\n"
        f"{identity_config['purpose']}\n"
        f"Rules I always follow:\n{rules}"
    )