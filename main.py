import argparse
from frontend_cli.workflow import start_chat
from frontend_cli.ui import print_loading_message

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xavion AI - Multi-frontend Assistant")
    parser.add_argument("--CLI", action="store_true", help="Start the Command Line Interface")
    
    args = parser.parse_args()

    if args.CLI:
        print_loading_message()
        debug_mode = False
        chat_finished = False
        intent_mode = "auto"
        while not chat_finished:
            chat_finished = start_chat(debug_mode, intent_mode)
    else:
        print("\n[!] Please specify a frontend to start.")
        print("    Usage: python main.py --CLI")
        print("    (Web interface support coming soon)\n")
