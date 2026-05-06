import sys
import time
import os
from xavion.core.engine import XavionAI
from xavion.interfaces.cli import ui

def select_session(ai: XavionAI):
    """Allows user to select a previous session or start a new one."""
    sessions = ai.list_sessions()
    if not sessions:
        return None

    ui.print_info("Found existing conversations:")
    for i, session in enumerate(sessions):
        print(f"  [{i+1}] {session}")
    print("  [0] Start a new conversation")
    
    try:
        choice = input("\n▶ Selection: ").strip()
        if choice == "0" or not choice:
            return None
        
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            session_id = sessions[idx]
            if ai.load_session(session_id):
                ui.print_success(f"Retrieved session: {session_id}")
                return session_id
    except ValueError:
        pass
    
    return None

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
    elif cmd == "/reset":
        ai.reset_history()
        ui.print_success("Conversation history has been reset.")
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
            ui.print_error("No models found or Ollama is unreachable.")
    elif cmd == "/model":
        if len(cmd_parts) > 1:
            new_model = cmd_parts[1].strip()
            ai.model_name = new_model
            ui.print_success(f"Model switched to: {new_model}")
        else:
            ui.print_info(f"Current model: {ai.model_name}")
            ui.print_info("Use '/model:NAME' to switch.")
    elif cmd == "/mode":
        ui.print_mode_list(["auto", "default", "math", "code"])
    elif cmd.startswith("/mode:"):
        new_mode = cmd_input.split(":")[1].strip()
        if new_mode in ["auto", "default", "math", "code"]:
            ui.print_success(f"Response mode switched to: {new_mode}")
            return new_mode, debug, False
        else:
            ui.print_error(f"Invalid mode: {new_mode}")
    else:
        ui.print_error(f"Unknown command: {cmd}")
        
    return current_mode, debug, False

def run_cli(debug: bool = False):
    """
    Main loop for the Professional CLI interface.
    """
    # Initialize engine
    ai = XavionAI(debug_callback=ui.print_debug if debug else None)
    
    # Initial setup
    ui.clear_terminal()
    ui.print_logo()
    ui.print_welcome_banner()
    
    # Session management
    current_session = select_session(ai)
    if not current_session:
        # Create a new session ID based on timestamp
        current_session = time.strftime("chat_%Y%m%d_%H%M%S")
        ai.current_session_id = current_session

    ui.print_info(f"System ready (Session: {current_session}). Type '/help' for options.")
    print()

    intent_mode = "auto"

    while True:
        try:
            # UI: Status and Input
            ui.print_status_bar(intent_mode, debug)
            user_input = ui.get_user_input().strip()
            print() # Visual spacing

            if not user_input:
                continue

            # 1. Handle Commands
            if user_input.startswith("/"):
                intent_mode, debug, should_exit = handle_command(user_input, ai, intent_mode, debug)
                if should_exit:
                    break
                print()
                continue

            # 2. Process AI Response
            ui.print_ai_header()
            
            try:
                # Use engine streaming
                for token in ai.chat_stream(user_input, intent_mode=intent_mode):
                    print(f"\033[1m{token}\033[0m", end="", flush=True)
            except Exception as e:
                print()
                ui.print_error(f"{e}")
            
            print("\n") # End of AI message

        except KeyboardInterrupt:
            ui.print_goodbye()
            break
        except Exception as e:
            ui.print_error(f"System error: {e}")
            print()
