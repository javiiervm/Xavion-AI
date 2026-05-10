import os
import time
import shutil

# Prompt Toolkit: Input UI components
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.patch_stdout import patch_stdout

# Rich: Output rendering and formatting
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import rich.box


class PlaceholderProcessor(Processor):
    """Injects placeholder text when the input buffer is empty."""
    def __init__(self, placeholder_text: str):
        self.placeholder_text = placeholder_text

    def apply_transformation(self, ti):
        if not ti.document.text:
            # Show gray placeholder if no text is typed
            return Transformation(fragments=[('fg:#6272a4', self.placeholder_text)])
        return Transformation(ti.fragments)


class XavionCLI:
    def __init__(self, ai, debug=False):
        self.ai = ai
        self.debug_mode = debug
        self.intent_mode = "auto"
        self.console = Console()

    def _status_info(self) -> str:
        """Generates the status string with cwd, mode, and model info."""
        cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
        model = self.ai.model_name
        debug_str = " [debug]" if self.debug_mode else ""
        return f" {cwd}    /mode ({self.intent_mode})    /model ({model}){debug_str}"

    def print_banner(self):
        """Displays the startup ASCII banner."""
        banner = (
            "[bold #bd93f9]\n"
            "__  __           _                  _    ___ \n"
            "\\ \\/ /__ ___   _(_) ___  _ __      / \\  |_ _|\n"
            " \\  // _` \\ \\ / / |/ _ \\| '_ \\    / _ \\  | | \n"
            " /  \\ (_| |\\ V /| | (_) | | | |  / ___ \\ | | \n"
            "/_/\\_\\__,_| \\_/ |_|\\___/|_| |_| /_/   \\_\\___|"
            "[/]"
        )
        self.console.print(banner)
        self.console.print("\nType [bold #f8f8f2]/help[/] for commands or start chatting.\n")

    def show_debug(self, message: str, icon: str = "🔍"):
        """Formats and prints debug messages."""
        self.console.print(f"[dim #6272a4]_{icon} {message}_[/]")

    def _get_input_inline(self) -> str:
        """Draws the dynamic, compact multiline input box attached to the cursor."""
        width = shutil.get_terminal_size().columns
        box_width = max(0, width - 2)
        
        top_line = '╭' + '─' * box_width + '╮'
        bottom_line = '╰' + '─' * box_width + '╯'
        status = self._status_info()

        input_buffer = Buffer(multiline=False)
        
        # Setup key bindings for the inline app
        kb = KeyBindings()
        @kb.add('enter')
        def _(event):
            event.app.exit(result=input_buffer.text)
        @kb.add('c-c')
        def _(event):
            event.app.exit(exception=KeyboardInterrupt())
        @kb.add('c-d')
        def _(event):
            event.app.exit(exception=EOFError())

        # Dynamic left border for text wrapping
        def get_prefix(line_number, wrap_count):
            if line_number == 0 and wrap_count == 0:
                return [('fg:#44475a', '│ '), ('fg:#bd93f9', '> ')]
            return [('fg:#44475a', '│   ')]

        # Define UI layout
        layout = Layout(
            HSplit([
                # 1. Top Border
                Window(FormattedTextControl(HTML(f'<style fg="#44475a">{top_line}</style>')), height=1, dont_extend_height=True),
                
                # 2. Middle Section: Left Border + Input + Right Border
                VSplit([
                    Window(
                        BufferControl(
                            buffer=input_buffer,
                            input_processors=[PlaceholderProcessor("Type your message or /help...")]
                        ), 
                        get_line_prefix=get_prefix,
                        wrap_lines=True,
                        dont_extend_height=True # THE CRITICAL FIX: prevents the massive vertical gap
                    ),
                    Window(width=1, char='│', style='fg:#44475a', dont_extend_height=True),
                ]),
                
                # 3. Bottom Border
                Window(FormattedTextControl(HTML(f'<style fg="#44475a">{bottom_line}</style>')), height=1, dont_extend_height=True),
                
                # 4. Status Info
                Window(FormattedTextControl(HTML(f'  <style fg="#6272a4">{status}</style>')), height=1, dont_extend_height=True),
            ])
        )

        # Run temporary Application
        app = Application(
            layout=layout, 
            key_bindings=kb, 
            full_screen=False, 
            erase_when_done=True
        )

        result = app.run()
        if isinstance(result, Exception):
            raise result
        return result

    def run(self):
        """Main application loop."""
        self.print_banner()
        self.ai.start_new_session()
        
        if self.debug_mode:
            self.ai.debug_callback = self.show_debug

        while True:
            try:
                # 1. Capture dynamic input
                with patch_stdout():
                    user_text = self._get_input_inline().strip()

                if not user_text:
                    continue

                # 2. Render static history block perfectly using Rich Panel
                panel_content = Text.from_markup(f" [bold #bd93f9]>[/] {user_text}")
                self.console.print(Panel(
                    panel_content,
                    border_style="#44475a",
                    box=rich.box.ROUNDED,
                    padding=(0, 0),
                    expand=True
                ))

                # 3. Process input commands or chat
                if user_text.startswith("/"):
                    self.handle_command(user_text)
                else:
                    self.generate_response(user_text)
                    
            except KeyboardInterrupt:
                continue  
            except EOFError:
                break     
                
        self.console.print("[bold #bd93f9]Goodbye![/]")

    def generate_response(self, user_text: str):
        """Streams AI response dynamically."""
        self.console.print()
        
        full_response = ""
        try:
            # Init Live with an empty dot instantly
            with Live(console=self.console, refresh_per_second=15, transient=False) as live:
                grid = Table.grid(padding=(0, 1))
                grid.add_row("[bold #bd93f9] [/]", Markdown(full_response))
                live.update(grid)

                # Process the stream
                for token in self.ai.chat_stream(user_text, intent_mode=self.intent_mode):
                    full_response += token
                    
                    grid = Table.grid(padding=(0, 1))
                    grid.add_row("[bold #bd93f9] [/]", Markdown(full_response))
                    live.update(grid)
                    
        except Exception as e:
            self.console.print(f"[bold red]**Error:**[/] {str(e)}")
        
        self.console.print()

    def handle_command(self, cmd_input: str):
        """Parses and executes internal slash commands."""
        cmd_parts = cmd_input.lower().strip().split(":")
        cmd = cmd_parts[0]
        
        if cmd in ["/exit", "/quit"]:
            raise EOFError
            
        elif cmd == "/help":
            help_text = """
**Session Control:**
- `/new`           - Start a completely new conversation
- `/reset`         - Clear history for current session

**Core Commands:**
- `/exit`          - Close the application
- `/help`          - Show this guide

**Settings:**
- `/debug`         - Toggle debug mode
- `/models`        - List installed models
- `/model:<name>`  - Switch model
- `/mode:<name>`   - Switch mode (auto, math, code, default)
"""
            self.console.print(Markdown(help_text))
            
        elif cmd == "/new":
            new_id = self.ai.start_new_session()
            self.console.print(f"[dim #6272a4]i[/] Started new session: {new_id}")
            
        elif cmd == "/reset":
            self.ai.reset_history()
            self.console.print("[dim #6272a4]i[/] Conversation history has been cleared for this session.")
            
        elif cmd == "/debug":
            self.debug_mode = not self.debug_mode
            self.ai.debug_callback = self.show_debug if self.debug_mode else None
            status = "enabled" if self.debug_mode else "disabled"
            self.console.print(f"[dim #6272a4]i[/] Debug mode {status}.")
            
        elif cmd == "/models":
            models = self.ai.list_available_models()
            if models:
                self.console.print(f"[dim #6272a4]i[/] Available models: {', '.join(models)}")
            else:
                self.console.print("[dim #6272a4]i[/] No models found.")
                
        elif cmd == "/model":
            if len(cmd_parts) > 1:
                new_model = cmd_parts[1].strip()
                self.ai.model_name = new_model
                self.console.print(f"[dim #6272a4]i[/] Model switched to: {new_model}")
            else:
                self.console.print(f"[dim #6272a4]i[/] Current model: {self.ai.model_name}")
                
        elif cmd == "/mode":
            self.console.print("[dim #6272a4]i[/] Available modes: auto, default, math, code")
            
        elif cmd.startswith("/mode:"):
            new_mode = cmd_input.split(":")[1].strip()
            if new_mode in ["auto", "default", "math", "code"]:
                self.intent_mode = new_mode
                self.console.print(f"[dim #6272a4]i[/] Mode switched to: {new_mode}")
                
        elif cmd == "/sessions":
            sessions = self.ai.list_sessions_detailed()
            if not sessions:
                self.console.print("[dim #6272a4]i[/] No previous conversations found.")
            else:
                msg = "**Previous Conversations:**\n"
                for i, s in enumerate(sessions):
                    updated_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(s['last_updated']))
                    msg += f"{i+1}. `{s['id']}` - {s['title']} ({updated_str})\n"
                msg += "\n*Use `/load:<id>` to load a session.*"
                self.console.print(Markdown(msg))
                
        elif cmd.startswith("/load:"):
            target_id = cmd_input.split(":")[1].strip()
            if self.ai.load_session(target_id):
                self.console.print(f"[dim #6272a4]i[/] Loaded session: {target_id}")
            else:
                self.console.print(f"[bold red]![/] Failed to load session: {target_id}")
                
        else:
            self.console.print(f"[bold red]![/] Unknown command: {cmd}")
            
        self.console.print()


def run_tui(ai_instance, debug=False):
    """Entry point for the terminal user interface."""
    app = XavionCLI(ai=ai_instance, debug=debug)
    app.run()