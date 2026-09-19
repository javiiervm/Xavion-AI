from xavion.core.engine import XavionAI
from xavion.interfaces.cli import ui


def run_cli(model_name: str, debug: bool = False):
    """Launch the terminal interface."""

    ai = XavionAI(
        model_name=model_name,
        debug_callback=None,
    )

    ui.run_tui(ai, debug=debug)