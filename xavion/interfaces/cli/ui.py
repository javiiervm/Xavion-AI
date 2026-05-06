import os
import platform
import time
from typing import List, Optional
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich import box
from PIL import Image

console = Console()

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
    console.print("[bold cyan]Professional Modular AI Assistant[/bold cyan]\n")

def print_logo(image_path: str = "assets/logo.png", width: int = 50):
    """Displays the logo in the terminal using half-blocks."""
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
    except Exception as e:
        console.print(f"[dim red](Logo could not be loaded: {e})[/dim red]")

def print_status_bar(mode: str, debug: bool):
    cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
    
    # Components
    path_text = Text(f" 📂 {cwd} ", style="bold blue on black")
    mode_text = Text(f" 🤖 Mode: {mode.upper()} ", style="bold black on yellow")
    
    debug_style = "bold white on green" if debug else "bold white on red"
    debug_status = "ON" if debug else "OFF"
    debug_text = Text(f" 🛠 Debug: {debug_status} ", style=debug_style)

    # Combine
    combined = Text()
    combined.append_text(path_text)
    combined.append(" ")
    combined.append_text(mode_text)
    combined.append(" ")
    combined.append_text(debug_text)
    
    console.print(combined)

def print_ai_header():
    console.print("[bold blue]▶ Xavion AI:[/bold blue] ", end="")

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
[bold yellow]Core Commands:[/bold yellow]
  [cyan]/exit[/cyan], [cyan]/quit[/cyan]  - Terminate the session
  [cyan]/reset[/cyan]         - Clear conversation history
  [cyan]/help[/cyan]          - Show this information

[bold yellow]Settings:[/bold yellow]
  [cyan]/debug[/cyan]         - Toggle debug mode
  [cyan]/models[/cyan]        - List available Ollama models
  [cyan]/model:<name>[/cyan]  - Switch to a different model
  [cyan]/mode:<name>[/cyan]   - Switch to mode (auto, math, code, default)
    """
    console.print(Panel(help_content.strip(), title="[bold white]Command Registry[/bold white]", border_style="blue", box=box.ROUNDED))

def print_mode_list(modes: List[str]):
    console.print(Panel("\n".join([f" • [bold cyan]{m}[/bold cyan]" for m in modes]), title="[bold yellow]Available Modes[/bold yellow]", border_style="yellow"))

def print_goodbye():
    console.print("\n[bold yellow]Session terminated. Xavion AI is now offline.[/bold yellow]\n")

def get_user_input() -> str:
    console.print("[bold blue]▶ You:[/bold blue] ", end="")
    return input()
