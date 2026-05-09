import sys
from xavion.core.engine import XavionAI
from xavion.interfaces.cli import ui

def run_cli(debug: bool = False):
    """
    Main entry point for the Professional CLI interface.
    """
    ai = XavionAI(debug_callback=None) # Callback is managed by Textual now
    
    # Run the Textual application
    ui.run_tui(ai, debug=debug)

