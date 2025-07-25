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

def double_check_intent(user_input, intent, debug_mode=False):
    """
    Double-checks the intent detected by the AI.

    Args:
        user_input (str): The user's input.
        intent (str): The intent detected by the AI.
        debug_mode (bool): Show debug messages if True.

    Returns:
        str: The double-checked intent.
    """
    if debug_mode:
        print(f"🔎 Double-checking intent: {intent}")

    if intent == "math":
        expression = extract_math_expression(user_input, debug_mode)
        if debug_mode:
            print(f"{BOLD}🔎 Expression detected: {GREEN}{expression}{RESET}")
        if expression:
            result = evaluate_math_expression(expression, debug_mode)
            if debug_mode:
                print(f"{BOLD}🔎 Result: {GREEN}{result}{RESET}")
            knowledge = f"The result of the expression '{expression}' is {result}."
        else:
            intent = detect_intent(user_input, ["math"])
            instruction = 'Instruction: ' + instruction_map.get(intent, "given a dialog context, you need to response empathically.")
            if debug_mode:
                print(f"{BOLD}⚠️ No math expression detected in user input.{RESET}")
                print(f"{BOLD}🔎 Intent detected: {GREEN}{intent}{RESET}")
                print(f"{BOLD}📝 New instruction: {GREEN}{instruction}{RESET}")

    return intent

def extract_teaching(user_input):
    """
    Extracts the term and its definition when the user is teaching something to the bot.
    
    Args:
        user_input (str): The user's input.
        
    Returns:
        tuple: (term, definition) or (None, None) if no teaching pattern is found.
    """
    text = user_input.lower().strip()
    
    for pattern in TEACHING_PATTERNS:
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