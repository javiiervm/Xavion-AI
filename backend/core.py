from backend.build_prompt import build_prompt
from backend.build_response import generate_response

def process_message(user_input, conversation_history, intent_mode="auto", debug_mode=False, callbacks=None, debug_callback=None):
    """
    Core function to process a single user message.
    Returns: (response, updated_history, debug_info)
    """
    # 1. Detect intent and build specific prompt
    instruction, intent, keywords = build_prompt(user_input, debug_mode, intent_mode, debug_callback=debug_callback)
    
    debug_info = {
        "intent": intent,
        "keywords": keywords
    }
    
    # 2. Generate response from LLM
    response = generate_response(
        instruction, 
        intent, 
        conversation_history, 
        user_input, 
        keywords,
        callbacks=callbacks
    )
    
    # 3. Update conversation history
    updated_history = conversation_history + f"""
User: {user_input}
AI: {response}"""
    
    return response, updated_history, debug_info
