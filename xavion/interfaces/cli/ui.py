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


# ==========================================
# COLOR PALETTE CONFIGURATION (NEUTRAL SPARK)
# ==========================================
# Edit these HEX codes to globally change the UI theme

COLOR_PRIMARY     = "#CC5500"  # Toasted Orange (Kept only for logo core and goodbye)
COLOR_SECONDARY   = "#FFFFFF"  # Pure White (User cursor, AI dot, strong highlights)
COLOR_ACCENT      = "#A0A0A0"  # Light Gray (Status bar commands, dim info texts)
COLOR_BORDER      = "#555555"  # Dark Gray (Input box borders)
COLOR_PLACEHOLDER = "#808080"  # Medium Gray (Placeholder text)
COLOR_ERROR       = "#CC3333"  # Bright Red (Error messages)

# ==========================================


class PlaceholderProcessor(Processor):
    """Injects a themed placeholder string when the input buffer is completely empty."""
    def __init__(self, placeholder_text: str):
        self.placeholder_text = placeholder_text

    def apply_transformation(self, ti):
        if not ti.document.text:
            # Replaced f-string with string concatenation to avoid Python parser bugs
            return Transformation(fragments=[('fg:' + COLOR_PLACEHOLDER, self.placeholder_text)])
        return Transformation(ti.fragments)


class XavionCLI:
    """Core Command Line Interface class handling AI interactions and UI rendering."""
    
    def __init__(self, ai, debug=False):
        self.ai = ai
        self.debug_mode = debug
        self.intent_mode = "auto"
        self.console = Console()

    def _status_info(self) -> str:
        """Generates the bottom status string containing the current working directory, mode, and model."""
        cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
        model = self.ai.model_name
        debug_str = " [debug]" if self.debug_mode else ""
        
        # Usamos la sintaxis HTML que prompt_toolkit entiende (etiquetas <style>)
        return f" {cwd}    <style fg='{COLOR_ACCENT}' bg='default' class='bold'>/mode</style> ({self.intent_mode})    <style fg='{COLOR_ACCENT}' bg='default' class='bold'>/model</style> ({model}){debug_str}"
    
    def print_banner(self):
        """Displays the compact startup banner with an organic flame ASCII and system status."""
        
        logo = (
            f"      [bold #CC0000]▄[/]      \n"
            f"     [bold #CC0000]▄█▄[/]     \n"
            f"    [bold #CC0000]▄[/][bold #CC5500 on #CC0000]▄▄▄[/][bold #CC0000]▄[/]    \n"
            f"   [bold #CC5500]▄[/][bold #CC5500 on #CC0000]▄[/][bold #D49A36 on #CC5500]▄[/][bold #FFFFFF on #D49A36]▄[/][bold #D49A36 on #CC5500]▄[/][bold #CC5500 on #CC0000]▄[/][bold #CC5500]▄[/]   \n"
            f"  [bold #CC5500]██[/][bold #D49A36]█[/][bold #FFFFFF]███[/][bold #D49A36]█[/][bold #CC5500]██[/]  \n"
            f"   [bold #CC5500]▀▀[/][bold #D49A36]▀[/][bold #FFFFFF]▀[/][bold #D49A36]▀[/][bold #CC5500]▀▀[/]   \n"
        )

        # Actual Xavion AI state data
        model = self.ai.model_name
        mode = self.intent_mode
        
        # Neutral palette for the header information
        info_text = (
            f"\n"
            f"Xavion Spark CLI [bold {COLOR_SECONDARY}]v26.05[/]\n"
            f"\n"
            f"Model:  {model} [bold {COLOR_ACCENT}]/model[/]\n"
            f"Mode:   {mode} [bold {COLOR_ACCENT}]/mode[/]"
        )

        # Use a Rich Table to align the logo and text side by side perfectly
        grid = Table.grid(padding=(0, 3))
        grid.add_row(logo, info_text)
        
        self.console.print()
        self.console.print(grid)
        self.console.print(f"\nType [bold {COLOR_ACCENT}]/help[/] for commands or start chatting.\n")

    def show_debug(self, message: str, icon: str = "🔍"):
        """Formats and prints internal debug messages."""
        self.console.print(f"[dim {COLOR_ACCENT}]_{icon} {message}_[/]")

    def _get_input_inline(self) -> str:
        """
        Draws a dynamic, compact multiline input box attached to the cursor.
        Utilizes prompt_toolkit's native VSplit layout to handle text wrapping 
        and border scaling automatically without occupying the full terminal height.
        """
        width = shutil.get_terminal_size().columns
        box_width = max(0, width - 2)
        
        top_line = '╭' + '─' * box_width + '╮'
        bottom_line = '╰' + '─' * box_width + '╯'
        status = self._status_info()

        input_buffer = Buffer(multiline=False)
        
        # Setup key bindings for the ephemeral application
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

        # Dynamically draw the left border and the input cursor prefix
        def get_prefix(line_number, wrap_count):
            if line_number == 0 and wrap_count == 0:
                # White cursor prefix `>`
                return [('fg:' + COLOR_BORDER, '│ '), ('fg:' + COLOR_SECONDARY, '> ')]
            return [('fg:' + COLOR_BORDER, '│   ')]

        # Construct HTML strings using .format() instead of f-strings to completely bypass compiler bugs
        html_top = '<style fg="{}">{}</style>'.format(COLOR_BORDER, top_line)
        html_bottom = '<style fg="{}">{}</style>'.format(COLOR_BORDER, bottom_line)
        html_status = '  {}  '.format(status) # Removed style wrapper as status uses rich markup tags now

        # Define the structural layout
        layout = Layout(
            HSplit([
                # 1. Top Border: Locked to exactly 1 line
                Window(FormattedTextControl(HTML(html_top)), height=1, dont_extend_height=True),
                
                # 2. Middle Section: Input Buffer + Right Border
                VSplit([
                    # Input Area
                    Window(
                        BufferControl(
                            buffer=input_buffer,
                            input_processors=[PlaceholderProcessor("Type your message or /help...")]
                        ), 
                        get_line_prefix=get_prefix,
                        wrap_lines=True,
                        dont_extend_height=True 
                    ),
                    # Right Wall
                    Window(
                        width=1, 
                        char='│', 
                        style='fg:' + COLOR_BORDER
                    ),
                ]),
                
                # 3. Bottom Border: Locked to exactly 1 line
                Window(FormattedTextControl(HTML(html_bottom)), height=1, dont_extend_height=True),
                
                # 4. Status Information: Locked to exactly 1 line
                Window(FormattedTextControl(HTML(html_status)), height=1, dont_extend_height=True),
            ])
        )

        # Execute the temporary inline Application
        app = Application(
            layout=layout, 
            key_bindings=kb, 
            full_screen=False,     # Prevents clearing the terminal history
            erase_when_done=True   # Removes the UI components after the user hits Enter
        )

        result = app.run()
        if isinstance(result, Exception):
            raise result
        return result

    def run(self):
        """Main application loop handling I/O operations and rendering history."""
        self.print_banner()
        self.ai.start_new_session()
        
        if self.debug_mode:
            self.ai.debug_callback = self.show_debug

        while True:
            try:
                # 1. Capture user input via the dynamic inline UI
                with patch_stdout():
                    user_text = self._get_input_inline().strip()

                if not user_text:
                    continue

                # 2. Render the submitted message into the terminal history using a Rich Panel
                panel_content = Text.from_markup(f" [bold {COLOR_SECONDARY}]>[/] {user_text}")
                self.console.print(Panel(
                    panel_content,
                    border_style=COLOR_BORDER,
                    box=rich.box.ROUNDED,
                    padding=(0, 0),
                    expand=True
                ))

                # 3. Route the input to either internal commands or AI generation
                if user_text.startswith("/"):
                    self.handle_command(user_text)
                else:
                    self.generate_response(user_text)
                    
            except KeyboardInterrupt:
                continue  
            except EOFError:
                break     
                
        self.console.print(f"[bold {COLOR_PRIMARY}]Goodbye![/]")

    def generate_response(self, user_text: str):
        """Streams the AI response dynamically with a live-updating Markdown grid."""
        self.console.print()
        
        full_response = ""
        try:
            # Initialize the Live display immediately with the original dot
            with Live(console=self.console, refresh_per_second=15, transient=False) as live:
                grid = Table.grid(padding=(0, 1))
                grid.add_row(f"[bold {COLOR_SECONDARY}] [/]", Markdown(full_response))
                live.update(grid)

                # Append tokens as they stream and update the grid
                for token in self.ai.chat_stream(user_text, intent_mode=self.intent_mode):
                    full_response += token
                    
                    grid = Table.grid(padding=(0, 1))
                    grid.add_row(f"[bold {COLOR_SECONDARY}] [/]", Markdown(full_response))
                    live.update(grid)
                    
        except Exception as e:
            # Keep errors a bit brighter red for visibility
            self.console.print(f"[bold {COLOR_ERROR}]**Error:**[/] {str(e)}")
        
        self.console.print()

    def handle_command(self, cmd_input: str):
        """Parses and executes built-in slash commands."""
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
            self.console.print(f"[dim {COLOR_ACCENT}]i[/] Started new session: {new_id}")
            
        elif cmd == "/reset":
            self.ai.reset_history()
            self.console.print(f"[dim {COLOR_ACCENT}]i[/] Conversation history has been cleared for this session.")
            
        elif cmd == "/debug":
            self.debug_mode = not self.debug_mode
            self.ai.debug_callback = self.show_debug if self.debug_mode else None
            status = "enabled" if self.debug_mode else "disabled"
            self.console.print(f"[dim {COLOR_ACCENT}]i[/] Debug mode {status}.")
            
        elif cmd == "/models":
            models = self.ai.list_available_models()
            if models:
                self.console.print(f"[dim {COLOR_ACCENT}]i[/] Available models: {', '.join(models)}")
            else:
                self.console.print(f"[dim {COLOR_ACCENT}]i[/] No models found.")
                
        elif cmd == "/model":
            if len(cmd_parts) > 1:
                new_model = cmd_parts[1].strip()
                self.ai.model_name = new_model
                self.console.print(f"[dim {COLOR_ACCENT}]i[/] Model switched to: {new_model}")
            else:
                self.console.print(f"[dim {COLOR_ACCENT}]i[/] Current model: {self.ai.model_name}")
                
        elif cmd == "/mode":
            self.console.print(f"[dim {COLOR_ACCENT}]i[/] Available modes: auto, default, math, code")
            
        elif cmd.startswith("/mode:"):
            new_mode = cmd_input.split(":")[1].strip()
            if new_mode in ["auto", "default", "math", "code"]:
                self.intent_mode = new_mode
                self.console.print(f"[dim {COLOR_ACCENT}]i[/] Mode switched to: {new_mode}")
                
        elif cmd == "/sessions":
            sessions = self.ai.list_sessions_detailed()
            if not sessions:
                self.console.print(f"[dim {COLOR_ACCENT}]i[/] No previous conversations found.")
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
                self.console.print(f"[dim {COLOR_ACCENT}]i[/] Loaded session: {target_id}")
            else:
                self.console.print(f"[bold {COLOR_ERROR}]![/] Failed to load session: {target_id}")
                
        else:
            self.console.print(f"[bold {COLOR_ERROR}]![/] Unknown command: {cmd}")
            
        self.console.print()


def run_tui(ai_instance, debug=False):
    """Entry point for the terminal user interface."""
    app = XavionCLI(ai=ai_instance, debug=debug)
    app.run()