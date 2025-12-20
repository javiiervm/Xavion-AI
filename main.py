from backend.chat_workflow import start_chat
from backend.ui_components import print_loading_message

if __name__ == "__main__":
    print_loading_message()
    debug_mode = False
    chat_finished = False
    intent_mode = "auto"
    while not chat_finished:
        chat_finished = start_chat(debug_mode, intent_mode)

"""import argparse
from backend.chat_workflow import start_chat

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xavion AI Command Line Interface")
    parser.add_argument("-r", "--request", type=str, help="Text string of any length")
    args, unknown = parser.parse_known_args()

    if unknown:
        print(f"Error: Argumento(s) desconocido(s): {', '.join(unknown)}")
        parser.print_help()
        exit(1)

    print("Loading Xavion AI, please wait...", flush=True)
    debug_mode = False
    chat_finished = False
    intent_mode = "auto"

    if args.request:
        print(f"Received request: {args.request}")
    else:
        while not chat_finished:
            chat_finished = start_chat(debug_mode, intent_mode)"""