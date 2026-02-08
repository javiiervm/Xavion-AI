from backend.core import process_message
from backend.key_variables import INSTRUCTION_MAP
from frontend_cli.ui import (
    console, print_success_message, print_info_message, print_error_message,
    print_help_panel, print_mode_list, print_goodbye_message,
    print_input_prompt, print_ai_message_start, 
    print_ai_message_end, print_debug_message, clear_terminal, print_welcome_banner,
    CustomStreamingHandler
)

def switch_debug_mode(current):
    return not current

def switch_intent_mode(current, user_input):
    # Remove "/" prefix and parse mode
    try:
        mode = user_input.lower().split("/mode:")[1].strip()
        if mode in INSTRUCTION_MAP or mode == "auto":
            print_success_message(f"Response mode switched to: {mode}")
            console.print()
            return mode
        else:
            print_error_message("Invalid mode. Available modes are:")
            console.print("  - [bold]auto[/bold]")
            for mode_name in INSTRUCTION_MAP.keys():
                console.print(f"  - [bold]{mode_name}[/bold]")
            console.print()
            return None
    except IndexError:
        return None

def analyze_input(user_input, debug_mode):
    match user_input.lower():
        case "/debug":
            debug_mode = switch_debug_mode(debug_mode)
            status = "Enabled" if debug_mode else "Disabled"
            print_success_message(f"Debug mode switched to: {status}")
            console.print()
        case "/exit":
            print_goodbye_message()
            return True, debug_mode
        case "/help":
            print_help_panel()
            console.print()
        case "/mode":
            modes = ["auto"] + list(INSTRUCTION_MAP.keys())
            print_mode_list(modes)
            console.print()
        case "/reset":
            return False, debug_mode
    return None, debug_mode

def start_chat(debug_mode, intent_mode):
    clear_terminal()
    print_welcome_banner()
    print_info_message("Write '/help' for a list of commands, or '/exit' to finish.")
    console.print()

    conversation_history = ""

    while True:
        # Show input box at bottom with status info
        user_input = print_input_prompt(intent_mode, debug_mode).strip()
        
        # Box disappears after input - add spacing
        console.print()

        if user_input.lower().startswith("/mode:"):
            selected_mode = switch_intent_mode(intent_mode, user_input)
            if selected_mode is not None:
                intent_mode = selected_mode
            console.print()
        elif user_input.lower() in ["/debug", "/exit", "/help", "/reset", "/mode"]:
            user_command, debug_mode = analyze_input(user_input, debug_mode)
            if user_command is not None:
                return user_command
            console.print()

        else:
            # Print AI header
            print_ai_message_start()
            
            # Setup CLI specific callbacks
            callbacks = [CustomStreamingHandler()]
            
            # Use core backend to process message
            response, conversation_history, debug_info = process_message(
                user_input, 
                conversation_history, 
                intent_mode=intent_mode, 
                debug_mode=debug_mode,
                callbacks=callbacks,
                debug_callback=print_debug_message
            )
            
            # debug_info is already used inside process_message via debug_callback
            # but we could do more here if needed
            
            print_ai_message_end()
            
            # Single line space before next input box appears
            console.print()
