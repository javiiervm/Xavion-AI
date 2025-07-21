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

DEFINITION_KEY_WORDS = [
    "what is", "what's", "define", "definition", "explain", "explanation",
    "meaning of", "describe", "characterize", "how would you define", "interpret",
    "tell me about"
]

TEACHING_PATTERNS = [
        r"([\w\s]+) (?:is|means|is defined as|refers to) ([\w\s,\.]+)",  # X is/means Y
        r"(?:the term|the word|the concept) ([\w\s]+) (?:means|is|refers to) ([\w\s,\.]+)",  # The term X means Y
        r"([\w\s]+) (?:stands for|is understood as) ([\w\s,\.]+)",  # X stands for Y
        r"(?:learn that|remember that|you should know that) ([\w\s]+) (?:is|means) ([\w\s,\.]+)"  # Learn that X is Y
    ]