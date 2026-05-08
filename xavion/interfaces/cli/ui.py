import os
import platform
import time
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box
from PIL import Image
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

console = Console()

# Global session to maintain history across inputs
prompt_session = PromptSession()

def detect_terminal_clear():
    return "cls" if platform.system() == "Windows" else "clear"

def clear_terminal():
    os.system(detect_terminal_clear())

def print_welcome_banner():
    banner_text = """
__  __           _                  _    ___ 
\ \/ /__ ___   _(_) ___  _ __      / \  |_ _|
 \  // _` \ \ / / |/ _ \| '_ \    / _ \  | | 
 /  \ (_| |\ V /| | (_) | | | |  / ___ \ | | 
/_/\_\__,_| \_/ |_|\___/|_| |_| /_/   \_\___|
    """
    console.print(Text(banner_text, style="bold bright_yellow"))
    #console.print("[bold cyan]Professional Modular AI Assistant[/bold cyan]\n")

def print_logo(image_path: str = "assets/logo.png", width: int = 50):
    if not os.path.exists(image_path):
        return
    try:
        img = Image.open(image_path).convert('RGB')
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.5)
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        pixels = img.load()
        for y in range(height):
            line = Text()
            for x in range(width):
                r, g, b = pixels[x, y]
                line.append("█", style=f"rgb({r},{g},{b})")
            console.print(line)
        console.print()
    except Exception:
        pass

def print_status_bar(mode: str, debug: bool, session_id: str):
    cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
    
    #path_text = Text(f" 📂 {cwd} ", style="bold blue on black")
    path_text = Text(f"{cwd} ", style="bold blue on black")
    #mode_text = Text(f" 🤖 Mode: {mode.upper()} ", style="bold black on yellow")
    mode_text = Text(f" Mode: {mode.upper()} ", style="bold black on yellow")
    #session_text = Text(f" 💬 Session: {session_id} ", style="bold white on blue")
    #session_text = Text(f"Session: {session_id} ", style="bold white on blue")
    
    debug_style = "bold white on green" if debug else "bold white on red"
    debug_status = "ON" if debug else "OFF"
    #debug_text = Text(f" 🛠 Debug: {debug_status} ", style=debug_style)
    debug_text = Text(f" Debug: {debug_status} ", style=debug_style)

    combined = Text()
    combined.append_text(path_text)
    combined.append(" ")
    combined.append_text(mode_text)
    combined.append(" ")
    #combined.append_text(session_text)
    #combined.append(" ")
    combined.append_text(debug_text)
    
    console.print(combined)

def print_session_selector(sessions: List[Dict[str, Any]]):
    table = Table(title="Previous Conversations", box=box.ROUNDED, border_style="blue", show_header=True)
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Title", style="white")
    table.add_column("Last Updated", style="dim")

    for i, s in enumerate(sessions):
        updated_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(s['last_updated']))
        table.add_row(str(i+1), s['title'], updated_str)

    console.print(table)

def print_ai_header():
    #console.print("[bold blue]▶ Xavion AI:[/bold blue] ", end="")
    pass

def print_info(message: str):
    console.print(f"[yellow]ℹ[/yellow] [dim white]{message}[/dim white]")

def print_success(message: str):
    console.print(f"[green]✔[/green] [bold yellow]{message}[/bold yellow]")

def print_error(message: str):
    console.print(f"[red]✘[/red] [bold red]{message}[/bold red]")

def print_debug(message: str, icon: str = "🔍"):
    console.print(f"   [dim yellow]{icon} {message}[/dim yellow]")

def print_help_panel():
    help_content = """
[bold yellow]Session Control:[/bold yellow]
  [cyan]/new[/cyan]           - Start a completely new conversation
  [cyan]/sessions[/cyan]      - Open session manager (Resume previous chats)
  [cyan]/reset[/cyan]         - Clear history for current session

[bold yellow]Core Commands:[/bold yellow]
  [cyan]/exit[/cyan]          - Close the application
  [cyan]/help[/cyan]          - Show this guide

[bold yellow]Settings:[/bold yellow]
  [cyan]/debug[/cyan]         - Toggle debug mode
  [cyan]/models[/cyan]        - List installed models
  [cyan]/model:<name>[/cyan]  - Switch model
  [cyan]/mode:<name>[/cyan]   - Switch mode (auto, math, code, default)
    """
    console.print(Panel(help_content.strip(), title="[bold white]Command Registry[/bold white]", border_style="blue", box=box.ROUNDED))

def print_mode_list(modes: List[str]):
    console.print(Panel("\n".join([f" • [bold cyan]{m}[/bold cyan]" for m in modes]), title="[bold yellow]Options[/bold yellow]", border_style="yellow"))

def print_goodbye():
    console.print("\n[bold yellow]Xavion AI is now offline. Goodbye![/bold yellow]\n")

def get_user_input() -> str:
    try:
        # Using prompt_toolkit for advanced input features (cursor navigation, history, etc.)
        return prompt_session.prompt(HTML('<ansiblue><b>▶</b></ansiblue> '))
    except EOFError:
        return "/exit"
    except KeyboardInterrupt:
        return "" # Clear line and keep going
