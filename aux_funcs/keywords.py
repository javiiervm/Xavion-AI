import math

STOPWORDS = {
    "a", "an", "the",
    "i", "me", "you", "he", "him", "she", "her", "it", "we", "us", "they", "them",
    "my", "your", "his", "her", "its", "our", "their",
    "myself", "yourself", "himself", "herself", "itself", "ourselves", "yourselves", "themselves",
    "who", "whom", "whose", "which", "what", "where", "when", "why", "how",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "and", "or", "but", "nor", "so", "for", "yet",
    "in", "on", "at", "by", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from", "up",
    "down", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "not", "only", "own", "same", "so", "than", "too", "very",
    "also", "just", "even", "still", "because", "though", "although", "however",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "i'm", "you're", "he's", "she's", "it's", "we're", "they're",
    "i've", "you've", "we've", "they've",
    "i'd", "you'd", "he'd", "she'd", "we'd", "they'd",
    "i'll", "you'll", "he'll", "she'll", "we'll", "they'll",
    "isn't", "aren't", "wasn't", "weren't",
    "hasn't", "haven't", "hadn't",
    "don't", "doesn't", "didn't",
    "won't", "wouldn't", "shan't", "shouldn't", "can't", "cannot", "couldn't",
    "mustn't", "mightn't", "needn't",
    "also", "via", "per", "etc", "vs"
}

DEFINITION_KEY_WORDS = [
    "what is", "what's", "define", "definition", "explain", "explanation",
    "meaning of", "describe", "characterize", "how would you define", "interpret",
    "tell me about"
]

TEACHING_PATTERNS = [
    r"(?:let me teach you|i want to teach you|i'll teach you) (?:that|about) ([\w\s]+) (?:is|means|refers to) ([\w\s,\.]+)",
    r"(?:let me explain|i'll explain|i'm explaining) (?:that|how) ([\w\s]+) (?:is|means|refers to) ([\w\s,\.]+)",
    r"([\w\s]+) (?:is|means|is defined as|refers to) ([\w\s,\.]+)",
    r"(?:the term|the word|the concept) ([\w\s]+) (?:means|is|refers to) ([\w\s,\.]+)",
    r"(?:learn that|remember that|you should know that|note that) ([\w\s]+) (?:is|means) ([\w\s,\.]+)",
    r"(?:i'm telling you|i want you to understand|you need to know) (?:that) ([\w\s]+) (?:is|means) ([\w\s,\.]+)",
    r"(?:in|when|if) (?:learning about|studying|discussing) ([\w\s]+),? (?:it|this) (?:is|means|refers to) ([\w\s,\.]+)",
    r"([\w\s]+) (?:stands for|is understood as|can be defined as) ([\w\s,\.]+)"
]

MATH_PATTERNS = [
    r"what\s+is\s+([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
    r"calculate\s+([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
    r"compute\s+([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
    r"solve\s+([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$",
    r"^([a-z\d\s\+\-\*\/\(\)\^\%\.]+)(?:\?)?$"
]

SAFE_MATH_FUNCS = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "pow": pow,
    "__builtins__": {}
}

GREETING_KEYWORDS = [
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    "morning", "afternoon", "evening", "hi there", "hello there",
    "how are you", "how's it going", "what's up", "nice to meet you",
    "good day", "good night"
]

THANKS_KEYWORDS = [
    "thank you", "thanks", "much appreciated", "cheers", "thank you very much",
    "thanks a lot", "many thanks", "thank you so much", "appreciate it",
    "grateful", "thank you kindly", "thanks a million", "much obliged",
    "thank you indeed", "thanks ever so much", "thank you for your help"
]
