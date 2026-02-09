import argparse
from frontend_cli.workflow import start_chat
from frontend_cli.ui import print_loading_message
from frontend_web.server import start_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xavion AI - Multi-frontend Assistant")
    parser.add_argument("--CLI", action="store_true", help="Start the Command Line Interface")
    parser.add_argument("--web", action="store_true", help="Start the Web Interface")
    parser.add_argument("--port", type=int, default=8000, help="Port for the web server (default: 8000)")
    
    args = parser.parse_args()

    if args.CLI:
        print_loading_message()
        debug_mode = False
        chat_finished = False
        intent_mode = "auto"
        while not chat_finished:
            chat_finished = start_chat(debug_mode, intent_mode)
    elif args.web:
        print(f"\n[+] Starting Xavion AI Web Interface on http://localhost:{args.port}")
        start_server(port=args.port)
    else:
        print("\n[!] Please specify a frontend to start.")
        print("    Usage:")
        print("    - CLI: python main.py --CLI")
        print("    - Web: python main.py --web [--port 8000]\n")
