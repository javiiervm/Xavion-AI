from backend.chat_workflow import start_chat

if __name__ == "__main__":
    print("Loading Xavion AI, please wait...", flush=True)
    debug_mode = False
    chat_finished = False
    intent_mode = "default"
    while not chat_finished:
        chat_finished = start_chat(debug_mode, intent_mode)
