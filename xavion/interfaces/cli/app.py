from xavion.core.engine import XavionAI
from xavion.interfaces.cli import ui


def run_cli(debug: bool = False):
    """Launch the terminal interface."""
    ai = XavionAI(debug_callback=None)
    ui.run_tui(ai, debug=debug)
