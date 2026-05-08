import sys
import time
import os
from xavion.core.engine import XavionAI
from xavion.interfaces.cli import ui

def open_session_menu(ai: XavionAI):
    """Command-based session selector."""
    sessions = ai.list_sessions_detailed()
    if not sessions:
        ui.print_info("No previous conversations found.")
        return False

    ui.print_session_selector(sessions)
    
    try:
        choice = input("\n▶ Select ID (or 'c' to cancel): ").strip().lower()
        if choice == 'c':
            return False
        
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            session_id = sessions[idx]["id"]
            if ai.load_session(session_id):
                ui.print_success(f"Loaded: {sessions[idx]['title']}")
                return True
    except (ValueError, IndexError):
        ui.print_error("Invalid selection.")
    
    return False

def handle_command(cmd_input: str, ai: XavionAI, current_mode: str, debug: bool):
    """
    Processes slash commands.
    Returns: (new_mode, new_debug, should_exit)
    """
    cmd_parts = cmd_input.lower().strip().split(":")
    cmd = cmd_parts[0]
    
    if cmd in ["/exit", "/quit"]:
        ui.print_goodbye()
        return current_mode, debug, True
    
    if cmd == "/help":
        ui.print_help_panel()
    elif cmd == "/new":
        new_id = ai.start_new_session()
        ui.print_success(f"Started new session: {new_id}")
    elif cmd == "/sessions":
        open_session_menu(ai)
    elif cmd == "/reset":
        ai.reset_history()
        ui.print_success("Conversation history has been cleared for this session.")
    elif cmd == "/debug":
        debug = not debug
        ai.debug_callback = ui.print_debug if debug else None
        status = "enabled" if debug else "disabled"
        ui.print_success(f"Debug mode {status}.")
    elif cmd == "/models":
        models = ai.list_available_models()
        if models:
            ui.print_mode_list(models)
        else:
            ui.print_error("No models found.")
    elif cmd == "/model":
        if len(cmd_parts) > 1:
            new_model = cmd_parts[1].strip()
            ai.model_name = new_model
            ui.print_success(f"Model switched to: {new_model}")
        else:
            ui.print_info(f"Current model: {ai.model_name}")
    elif cmd == "/mode":
        ui.print_mode_list(["auto", "default", "math", "code"])
    elif cmd.startswith("/mode:"):
        new_mode = cmd_input.split(":")[1].strip()
        if new_mode in ["auto", "default", "math", "code"]:
            ui.print_success(f"Mode switched to: {new_mode}")
            return new_mode, debug, False
    else:
        ui.print_error(f"Unknown command: {cmd}")
        
    return current_mode, debug, False

def run_cli(debug: bool = False):
    """
    Main loop for the Professional CLI interface.
    """
    ai = XavionAI(debug_callback=ui.print_debug if debug else None)
    
    ui.clear_terminal()
    #ui.print_logo()
    ui.print_welcome_banner()
    
    # Start a fresh session by default
    current_session = ai.start_new_session()

    #ui.print_info(f"System ready. Started new session: {current_session}")
    ui.print_info("Type '/sessions' to load previous chats or '/help' for more.")
    print()

    intent_mode = "auto"

    while True:
        try:
            ui.print_status_bar(intent_mode, debug, ai.current_session_id)
            user_input = ui.get_user_input().strip()
            print() 

            if not user_input:
                continue

            if user_input.startswith("/"):
                intent_mode, debug, should_exit = handle_command(user_input, ai, intent_mode, debug)
                if should_exit:
                    break
                print()
                continue

            ui.print_ai_header()
            try:
                for token in ai.chat_stream(user_input, intent_mode=intent_mode):
                    print(f"\033[1m{token}\033[0m", end="", flush=True)
            except Exception as e:
                print()
                ui.print_error(f"{e}")
            
            print("\n")

        except KeyboardInterrupt:
            ui.print_goodbye()
            break
        except Exception as e:
            ui.print_error(f"System error: {e}")
            print()
