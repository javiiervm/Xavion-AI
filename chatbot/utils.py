from chatbot.keywords import (
    STOPWORDS, 
    DEFINITION_KEY_WORDS,
    TEACHING_PATTERNS,
    MATH_PATTERNS,
    SAFE_MATH_FUNCS,
    GREETING_KEYWORDS,
    THANKS_KEYWORDS
)

import re
import json
import os
import math

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

def detect_intent(user_input, restrictionList):
    """
    Detects the intent of the user's input.

    Args:
        user_input (str): The user's input.

    Returns:
        str: The detected intent
    """
    text = user_input.lower().strip()

    if "math" not in restrictionList:
        # Math operation requests
        for pattern in MATH_PATTERNS:
            if re.search(pattern, text):
                return "math"

    if "definition" not in restrictionList:
        # Definition requests
        if any(keyword in text for keyword in DEFINITION_KEY_WORDS):
            return "definition"

    if "teaching" not in restrictionList:
        # Teaching patterns - User is teaching the bot a new term
        for pattern in TEACHING_PATTERNS:
            if re.search(pattern, text):
                return "teaching"

    if "greeting" not in restrictionList:
        if any(greet in text for greet in GREETING_KEYWORDS):
            return "greeting"

    if "thanks" not in restrictionList:
        if any(thank in text for thank in THANKS_KEYWORDS):
            return "thanks"

    # Default: conversation
    return "conversation"

def extract_teaching(user_input):
    """
    Extracts the term and its definition when the user is teaching something to the bot.
    
    Args:
        user_input (str): The user's input.
        
    Returns:
        tuple: (term, definition) or (None, None) if no teaching pattern is found.
    """
    text = user_input.lower().strip()
    
    # Teaching patterns with capture groups
    teaching_patterns = [
        r"([\w\s]+) (?:is|means|is defined as|refers to) ([\w\s,\.]+)",  # X is/means Y
        r"(?:the term|the word|the concept) ([\w\s]+) (?:means|is|refers to) ([\w\s,\.]+)",  # The term X means Y
        r"([\w\s]+) (?:stands for|is understood as) ([\w\s,\.]+)",  # X stands for Y
        r"(?:learn that|remember that|you should know that) ([\w\s]+) (?:is|means) ([\w\s,\.]+)"  # Learn that X is Y
    ]
    
    for pattern in teaching_patterns:
        match = re.search(pattern, text)
        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            return term, definition
    
    return None, None

def extract_math_expression(user_input, debug_mode=False):
    cleaned_input = user_input.lower().strip()

    if debug_mode:
        print(f"🔎 Scanning for math expression in: '{cleaned_input}'")

    for pattern in MATH_PATTERNS:
        match = re.search(pattern, cleaned_input)
        if match:
            expression = match.group(1).strip()

            # Validación extra: debe contener al menos un dígito o función matemática
            if not re.search(r"[\d\+\-\*\/\^]", expression) and not re.search(r"\b(sqrt|log|sin|cos|tan|pi|e)\b", expression):
                if debug_mode:
                    print(f"❌ False positive: '{expression}' is not a valid math expression.")
                return None

            if debug_mode:
                print(f"✅ Math expression detected: '{expression}'")
            return expression

    if debug_mode:
        print("❌ No math expression detected.")
    return None

def evaluate_math_expression(expression, debug_mode=False):
    """
    Safely evaluates a mathematical expression using a restricted environment.
    
    Args:
        expression (str): A valid math expression (e.g. "2 + 2").
        debug_mode (bool): Show debug messages if True.
        
    Returns:
        float | str: The result or an error message.
    """
    try:
        cleaned_expr = expression.replace("^", "**")
        result = eval(cleaned_expr, SAFE_MATH_FUNCS)
        if debug_mode:
            print(f"✅ Evaluated result: {result}")
        return result
    except Exception as e:
        if debug_mode:
            print(f"❌ Evaluation error: {e}")
        return "Sorry, I couldn't evaluate that expression."

def delete_stopwords(text):
    """
    Removes common stopwords from a given text.
    
    Args:
        text (str): The input text.
        
    Returns:
        str: The text with stopwords removed.
    """
    words = text.split()
    filtered_words = [word for word in words if word not in STOPWORDS]
    return ' '.join(filtered_words)