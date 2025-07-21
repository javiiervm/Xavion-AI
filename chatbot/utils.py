import re
import json
import os

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