import os
import sys
import time
import shutil
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Window, VSplit
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

class XavionCLI:
    def __init__(self, ai, debug=False):
        self.ai = ai
        self.debug_mode = debug
        self.intent_mode = "auto"
        self.console = Console()
        
        # 1. Hacemos la barra inferior transparente (bg:default noreverse)
        self.style = Style.from_dict({
            'bottom-toolbar': 'noreverse bg:default #6272a4',
        })
        
        self.session = PromptSession(style=self.style)



    def _status_info(self) -> str:
        """Devuelve la línea de info del workspace para imprimirla con Rich."""
        cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
        model = self.ai.model_name
        debug_str = " [debug]" if self.debug_mode else ""
        return f" {cwd}    /mode ({self.intent_mode})    /model ({model}){debug_str} "

    def print_banner(self):
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
        self.console.print(f"[dim #6272a4]_{icon} {message}_[/]")

    def _get_input_inline(self):
        width = shutil.get_terminal_size().columns
        box_width = max(0, width - 2)
        
        top_line = '╭' + '─' * box_width + '╮'
        bottom_line = '╰' + '─' * box_width + '╯'
        status = self._status_info().strip()

        input_buffer = Buffer(multiline=False)
        
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

        layout = Layout(
            HSplit([
                # 1. Tapa superior (con fg= en lugar de color= y altura bloqueada)
                Window(
                    FormattedTextControl(HTML(f'<style fg="#44475a">{top_line}</style>')), 
                    height=1, 
                    dont_extend_height=True
                ),
                
                # 2. Zona central: Pared izq -> Buffer de texto -> Pared der
                VSplit([
                    Window(
                        FormattedTextControl(HTML('<style fg="#44475a">│</style> <style fg="#bd93f9">></style> ')), 
                        width=4, 
                        dont_extend_height=True
                    ),
                    Window(
                        BufferControl(buffer=input_buffer), 
                        wrap_lines=True, 
                        dont_extend_height=True
                    ),
                    Window(
                        FormattedTextControl(HTML('<style fg="#44475a">│</style>')), 
                        width=1, 
                        dont_extend_height=True
                    ),
                ]),
                
                # 3. Tapa inferior (cerrada MIENTRAS escribes)
                Window(
                    FormattedTextControl(HTML(f'<style fg="#44475a">{bottom_line}</style>')), 
                    height=1, 
                    dont_extend_height=True
                ),
                
                # 4. Estado separado, por debajo del recuadro, sin irse al fondo de la pantalla
                Window(
                    FormattedTextControl(HTML(f'\n  <style fg="#6272a4">{status}</style>')), 
                    height=2, 
                    dont_extend_height=True
                ),
            ])
        )

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
        self.print_banner()
        self.ai.start_new_session()
        
        if self.debug_mode:
            self.ai.debug_callback = self.show_debug

        while True:
            try:
                # 1. Obtenemos el texto con la UI perfecta
                with patch_stdout():
                    user_text = self._get_input_inline().strip()

                if not user_text:
                    continue

                # 2. Imprimimos el recuadro "estático" y limpio para el historial
                width = shutil.get_terminal_size().columns
                box_width = max(0, width - 2)
                top_line = '╭' + '─' * box_width + '╮'
                bottom_line = '╰' + '─' * box_width + '╯'
                
                self.console.print(f"[#44475a]{top_line}[/]")
                self.console.print(f"[#44475a]│[/] [bold #bd93f9]>[/] {user_text}")
                self.console.print(f"[#44475a]{bottom_line}[/]")

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
        self.console.print()
        
        full_response = ""
        try:
            # Iniciamos el Live (ya no hace falta pasarle el Markdown inicial aquí)
            with Live(console=self.console, refresh_per_second=15, transient=False) as live:
                for token in self.ai.chat_stream(user_text, intent_mode=self.intent_mode):
                    full_response += token
                    
                    # Creamos una cuadrícula invisible con 1 espacio de separación horizontal
                    grid = Table.grid(padding=(0, 1))
                    
                    # Añadimos la fila: Columna 1 (Prefijo) | Columna 2 (Markdown dinámico)
                    grid.add_row("[bold #bd93f9] [/]", Markdown(full_response))
                    
                    # Actualizamos el bloque Live con la cuadrícula completa
                    live.update(grid)
                    
        except Exception as e:
            self.console.print(f"[bold red]**Error:**[/] {str(e)}")
        
        self.console.print()

    def handle_command(self, cmd_input: str):
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
    app = XavionCLI(ai=ai_instance, debug=debug)
    app.run()