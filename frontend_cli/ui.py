"""
UI Components for Xavion AI - Gemini CLI-inspired interface
Provides rich terminal formatting, animations, and styled output
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from rich.syntax import Syntax
from rich import box
import time
import os
import platform
from langchain_core.callbacks import BaseCallbackHandler
from backend.key_variables import COLORS

# Initialize the global console
console = Console()

class CustomStreamingHandler(BaseCallbackHandler):
    def __init__(self):
        self.first_token = True

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.first_token:
            # Start bold text using original COLORS tag
            print(f"{COLORS['BOLD']}", end="", flush=True)
            self.first_token = False
        print(token, end="", flush=True)

    def on_llm_end(self, *args, **kwargs):
        # End bold text using original COLORS tag
        print(f"{COLORS['RESET']}", end="\n", flush=True)
        self.first_token = True

def detect_terminal():
    system_name = platform.system()

    if system_name == "Linux" or system_name == "Darwin":
        return "clear"
    elif system_name == "Windows":
        shell = os.environ.get("SHELL", "")
        if "bash" in shell.lower():
            return "clear"
        else:
            return "cls"
    else:
        return None

def clear_terminal():
    command = detect_terminal()
    if command:
        os.system(command)
    else:
        print("\n" * 100)

def print_welcome_banner():
    """Display the animated welcome banner"""
    banner_text = """
__  __           _                  _    ___ 
\ \/ /__ ___   _(_) ___  _ __      / \  |_ _|
 \  // _` \ \ / / |/ _ \| '_ \    / _ \  | | 
 /  \ (_| |\ V /| | (_) | | | |  / ___ \ | | 
/_/\_\__,_| \_/ |_|\___/|_| |_| /_/   \_\___|
    """
    
    # Print banner without box, just styled text (using orange from logo)
    console.print(Text(banner_text, style="bold bright_yellow"))
    console.print()

def print_welcome_image(image_path=None, width=60, height=None):
    """
    Display an image in the terminal
    
    Args:
        image_path: Path to the image file (default: uses logo_full.png from assets folder)
        width: Width of the displayed image in characters (default: 60)
        height: Height of the displayed image in characters (default: None, auto-calculated)
    """
    try:
        from PIL import Image
        import os
        
        # If no path provided, use default logo
        if image_path is None:
            # Get the directory of this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to project root, then into assets
            project_root = os.path.dirname(current_dir)
            image_path = os.path.join(project_root, "assets", "logo_full.png")
        
        # Check if image exists
        if not os.path.exists(image_path):
            console.print(f"[bold red]Error: Image not found at {image_path}[/bold red]")
            return
        
        # Load image
        img = Image.open(image_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate dimensions
        # Terminal characters are roughly 1:2 ratio (width:height)
        original_width, original_height = img.size
        aspect_ratio = original_height / original_width
        
        # Calculate target dimensions in characters
        target_width = width
        if height is None:
            target_height = int(target_width * aspect_ratio * 0.5)  # 0.5 because we use half blocks
        else:
            target_height = height
        
        # Resize image to match character dimensions
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Get pixel data
        pixels = img.load()
        
        # Render image using half-block characters
        for y in range(target_height):
            line = ""
            for x in range(target_width):
                r, g, b = pixels[x, y]
                # Use full block character with RGB color
                line += f"[rgb({r},{g},{b})]█[/rgb({r},{g},{b})]"
            console.print(line)
        
        console.print()
        
    except ImportError:
        console.print("[bold red]Error: PIL (Pillow) library is required to display images.[/bold red]")
        console.print("[yellow]Install it with: pip install Pillow[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error loading image: {e}[/bold red]")

def print_loading_message():
    """Display loading message with animation"""
    with console.status("[bold yellow]Loading Xavion AI...", spinner="dots") as status:
        time.sleep(0.5)  # Brief delay for visual effect

def print_user_message(message):
    """Format and print user input message"""
    user_text = Text()
    user_text.append("▶ ", style="bold blue")
    user_text.append("You: ", style="bold white")
    user_text.append(message, style="white")
    console.print(user_text)
    console.print()

def print_ai_message_start():
    """Print the AI message header - empty, just start the response"""
    pass

def print_ai_message_end():
    """Print newline after AI message - just one"""
    pass  # The streaming handler already adds a newline

def print_system_message(message, icon="ℹ️", style="bold yellow"):
    """Format and print system messages"""
    text = Text()
    text.append(f"{icon} ", style=style)
    text.append(message, style=style)
    console.print(text)

def print_success_message(message):
    """Print success message"""
    print_system_message(message, icon="✅", style="bold yellow")

def print_error_message(message):
    """Print error message"""
    print_system_message(message, icon="❌", style="bold red")

def print_info_message(message):
    """Print info message"""
    print_system_message(message, icon="💡", style="bold yellow")

def print_input_prompt(mode, debug_enabled):
    """Print the input prompt with status info above and simple arrow prompt"""
    import os
    
    # Get actual current working directory
    cwd = os.getcwd()
    # Format path for display (use forward slashes and tilde for home if applicable)
    home = os.path.expanduser("~")
    if cwd.startswith(home):
        display_path = "~" + cwd[len(home):].replace("\\", "/")
    else:
        display_path = cwd.replace("\\", "/")
    
    # Status bar above the input (directory, mode, debug) - using orange tones from logo
    status_parts = []
    status_parts.append(f"[dim blue]{display_path}[/dim blue]")
    status_parts.append(f"[yellow]Mode: [bold yellow]{mode.capitalize()}[/bold yellow][/yellow]")
    
    if debug_enabled:
        status_parts.append(f"[yellow]Debug: [bold yellow]Enabled[/bold yellow][/yellow]")
    else:
        status_parts.append(f"[dim yellow]Debug: Disabled[/dim yellow]")
    
    status_line = "  |  ".join(status_parts)
    console.print(status_line)
    
    # Simple arrow prompt - blue from logo
    console.print("[bold blue]▶[/bold blue] ", end="")
    user_input = input()
    
    return user_input

def print_help_panel():
    """Display help information with colored text"""
    console.print("[bold yellow]Available Commands:[/bold yellow]")
    console.print("  [bold bright_yellow]/debug[/bold bright_yellow]      - Toggle debug mode")
    console.print("  [bold bright_yellow]/exit[/bold bright_yellow]       - Close the chat")
    console.print("  [bold bright_yellow]/help[/bold bright_yellow]       - Show this command list")
    console.print("  [bold bright_yellow]/reset[/bold bright_yellow]      - Start a new conversation")
    console.print("  [bold bright_yellow]/mode[/bold bright_yellow]       - Show available response modes")
    console.print("  [bold bright_yellow]/mode:name[/bold bright_yellow]  - Switch to specific response mode")

def print_mode_list(modes):
    """Display available modes with colored text"""
    console.print("[bold yellow]Available Response Modes:[/bold yellow]")
    for mode in modes:
        console.print(f"  - [bold bright_yellow]{mode}[/bold bright_yellow]")

def print_goodbye_message():
    """Display application closing message"""
    console.print()
    console.print("[bold yellow]Closing Xavion AI...[/bold yellow]")
    console.print()

def print_debug_message(message, icon="🔍"):
    """Print debug information"""
    text = Text()
    text.append(f"{icon} ", style="dim yellow")
    text.append(message, style="dim yellow")
    console.print(text)

def render_markdown(content):
    """Render markdown content with syntax highlighting"""
    md = Markdown(content)
    console.print(md)

def clear_screen():
    """Clear the console screen"""
    console.clear()
