import os
import re
import shutil
import time
from pathlib import Path

import pyperclip
import rich.box
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from xavion.core.images import MAX_IMAGE_BYTES, MAX_IMAGES_PER_MESSAGE
from xavion.version import DISPLAY_NAME, VERSION

COLOR_SECONDARY = "#FFFFFF"
COLOR_ACCENT = "#A0A0A0"
COLOR_BORDER = "#555555"
COLOR_PLACEHOLDER = "#808080"
COLOR_ERROR = "#CC3333"


class PlaceholderProcessor(Processor):
    """Display placeholder text while the input buffer is empty."""

    def __init__(self, placeholder_text: str):
        self.placeholder_text = placeholder_text

    def apply_transformation(self, ti):
        if not ti.document.text:
            return Transformation(
                fragments=[("fg:" + COLOR_PLACEHOLDER, self.placeholder_text)]
            )
        return Transformation(ti.fragments)


class XavionCLI:
    """Handle terminal interaction and rendering for Xavion AI."""

    def __init__(self, ai, debug=False):
        self.ai = ai
        self.debug_mode = debug
        self.intent_mode = "auto"
        self.tone_mode = "adaptive"
        self.console = Console()
        self.last_code_blocks = []
        self.input_history = InMemoryHistory()
        self.last_models = []
        self.last_sessions = []
        self.pending_images: list[str] = []

    def _status_info(self) -> str:
        cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
        debug_status = " [debug]" if self.debug_mode else ""
        attachment_status = (
            f"    <style fg='{COLOR_ACCENT}' class='bold'>/images</style> "
            f"({len(self.pending_images)})"
            if self.pending_images else ""
        )
        return (
            f" {cwd}    "
            f"<style fg='{COLOR_ACCENT}' class='bold'>/mode</style> ({self.intent_mode})    "
            f"<style fg='{COLOR_ACCENT}' class='bold'>/tone</style> ({self.tone_mode})    "
            f"<style fg='{COLOR_ACCENT}' class='bold'>/model</style> ({self.ai.model_name})"
            f"{attachment_status}{debug_status}"
        )

    def print_banner(self):
        logo = (
            "      [bold #CC0000]▄[/]      \n"
            "     [bold #CC0000]▄█▄[/]     \n"
            "    [bold #CC0000]▄[/][bold #CC5500 on #CC0000]▄▄▄[/][bold #CC0000]▄[/]    \n"
            "   [bold #CC5500]▄[/][bold #CC5500 on #CC0000]▄[/][bold #D49A36 on #CC5500]▄[/][bold #FFFFFF on #D49A36]▄[/][bold #D49A36 on #CC5500]▄[/][bold #CC5500 on #CC0000]▄[/][bold #CC5500]▄[/]   \n"
            "  [bold #CC5500]██[/][bold #D49A36]█[/][bold #FFFFFF]███[/][bold #D49A36]█[/][bold #CC5500]██[/]  \n"
            "   [bold #CC5500]▀▀[/][bold #D49A36]▀[/][bold #FFFFFF]▀[/][bold #D49A36]▀[/][bold #CC5500]▀▀[/]   \n"
        )
        info = (
            f"\n{DISPLAY_NAME} CLI [bold {COLOR_SECONDARY}]v{VERSION}[/]\n\n"
            f"Model:  {self.ai.model_name} [bold {COLOR_ACCENT}]/model[/]\n"
            f"Mode:   {self.intent_mode} [bold {COLOR_ACCENT}]/mode[/]"
        )
        grid = Table.grid(padding=(0, 3))
        grid.add_row(logo, info)
        self.console.print()
        self.console.print(grid)
        self.console.print(
            f"Type [bold {COLOR_ACCENT}]/help[/] for commands or start chatting.\n"
        )

    def show_debug(self, message: str, icon: str = "🔍"):
        self.console.print(f"[dim {COLOR_ACCENT}]_{icon} {message}_[/]")

    def _get_input_inline(self) -> str:
        box_width = max(0, shutil.get_terminal_size().columns - 2)
        top_line = "╭" + "─" * box_width + "╮"
        bottom_line = "╰" + "─" * box_width + "╯"
        input_buffer = Buffer(multiline=False, history=self.input_history)
        key_bindings = KeyBindings()

        @key_bindings.add("enter")
        def _(event):
            event.app.exit(result=input_buffer.text)

        @key_bindings.add("c-c")
        def _(event):
            event.app.exit(exception=KeyboardInterrupt())

        @key_bindings.add("c-d")
        def _(event):
            event.app.exit(exception=EOFError())

        def get_prefix(line_number, wrap_count):
            if line_number == 0 and wrap_count == 0:
                return [("fg:" + COLOR_BORDER, "│ "), ("fg:" + COLOR_SECONDARY, "> ")]
            return [("fg:" + COLOR_BORDER, "│   ")]

        top = '<style fg="{}">{}</style>'.format(COLOR_BORDER, top_line)
        bottom = '<style fg="{}">{}</style>'.format(COLOR_BORDER, bottom_line)
        status = "  {}  ".format(self._status_info())
        layout = Layout(
            HSplit(
                [
                    Window(FormattedTextControl(HTML(top)), height=1, dont_extend_height=True),
                    VSplit(
                        [
                            Window(
                                BufferControl(
                                    buffer=input_buffer,
                                    input_processors=[PlaceholderProcessor("Type your message or /help...")],
                                ),
                                get_line_prefix=get_prefix,
                                wrap_lines=True,
                                dont_extend_height=True,
                            ),
                            Window(width=1, char="│", style="fg:" + COLOR_BORDER),
                        ]
                    ),
                    Window(FormattedTextControl(HTML(bottom)), height=1, dont_extend_height=True),
                    Window(FormattedTextControl(HTML(status)), height=1, dont_extend_height=True),
                ]
            )
        )
        result = Application(
            layout=layout,
            key_bindings=key_bindings,
            full_screen=False,
            erase_when_done=True,
        ).run()
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
                with patch_stdout():
                    user_text = self._get_input_inline().strip()
                if not user_text:
                    continue

                self.input_history.append_string(user_text)
                content = Text.from_markup(f" [bold {COLOR_SECONDARY}]>[/] {user_text}")
                self.console.print(
                    Panel(
                        content,
                        border_style=COLOR_BORDER,
                        box=rich.box.ROUNDED,
                        padding=(0, 0),
                        expand=True,
                    )
                )
                if user_text.startswith("/"):
                    self.handle_command(user_text)
                else:
                    self.generate_response(user_text)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

    def generate_response(self, user_text: str):
        self.console.print()
        full_response = ""
        attached_paths = list(self.pending_images)

        if attached_paths:
            try:
                capabilities = self.ai.get_model_capabilities()
            except Exception as exc:
                self._error(f"Could not check model capabilities: {exc}")
                self.console.print()
                return
            if not capabilities.available:
                self._error(
                    "Could not verify whether this model supports images: "
                    + (capabilities.error or "Ollama capability lookup failed.")
                )
                self.console.print()
                return
            if not capabilities.vision:
                self._error(
                    f"Model '{self.ai.model_name}' does not support images. "
                    "Switch to a vision model or use /clearimages."
                )
                self.console.print()
                return

            self._info(
                f"Sending {len(attached_paths)} image(s) with this message."
            )

        try:
            with Live(console=self.console, refresh_per_second=15, transient=False) as live:
                grid = Table.grid(padding=(0, 1))
                grid.add_row(f"[bold {COLOR_SECONDARY}] [/]", Markdown(full_response))
                live.update(grid)

                for token in self.ai.chat_stream(
                    user_text,
                    intent_mode=self.intent_mode,
                    tone_mode=self.tone_mode,
                    images=[{"path": path} for path in attached_paths],
                ):
                    full_response += token
                    grid = Table.grid(padding=(0, 1))
                    grid.add_row(f"[bold {COLOR_SECONDARY}] [/]", Markdown(full_response))
                    live.update(grid)

            # Clear attachments only after the engine has completed successfully.
            if attached_paths:
                del self.pending_images[:len(attached_paths)]

            self.last_code_blocks = re.findall(
                r"```(?:\w+)?\n(.*?)\n```", full_response, re.DOTALL
            )
            if self.last_code_blocks:
                count = len(self.last_code_blocks)
                suffix = "blocks" if count > 1 else "block"
                self.console.print(
                    f"\n[dim {COLOR_ACCENT}]i {count} code {suffix} detected. Type [/]"
                    f"[bold {COLOR_ACCENT}]/copy[/][dim {COLOR_ACCENT}] to copy the last one.[/]"
                )
        except Exception as exc:
            self.console.print(f"[bold {COLOR_ERROR}]Error:[/] {exc}")
            if attached_paths:
                self._info("Attachments are still queued; use /images or /clearimages.")
        self.console.print()

    def _attach_image(self, cmd_input: str):
        """Queue an image path for the next message without loading it into memory."""
        _, separator, raw_path = cmd_input.partition(":")
        if not separator:
            self._error('Usage: /image:/path/to/image.png')
            return

        raw_path = raw_path.strip()
        if len(raw_path) >= 2 and raw_path[0] == raw_path[-1] and raw_path[0] in "\"'":
            raw_path = raw_path[1:-1]
        if not raw_path:
            self._error('Usage: /image:/path/to/image.png')
            return

        if len(self.pending_images) >= MAX_IMAGES_PER_MESSAGE:
            self._error(f"A message supports at most {MAX_IMAGES_PER_MESSAGE} images.")
            return

        try:
            capabilities = self.ai.get_model_capabilities()
        except Exception as exc:
            self._error(f"Could not check model capabilities: {exc}")
            return
        if not capabilities.available:
            self._error(
                "Could not verify image support: "
                + (capabilities.error or "Ollama capability lookup failed.")
            )
            return
        if not capabilities.vision:
            self._error(
                f"Model '{self.ai.model_name}' does not support images. "
                "Select a vision-capable model first."
            )
            return

        path = Path(raw_path).expanduser()
        if not path.is_file():
            self._error(f"Image file not found: {path}")
            return
        try:
            if path.stat().st_size > MAX_IMAGE_BYTES:
                self._error("Image exceeds the 8 MiB limit.")
                return
            if path.stat().st_size == 0:
                self._error("Image cannot be empty.")
                return
        except OSError as exc:
            self._error(f"Could not read image: {exc}")
            return

        absolute_path = str(path.resolve())
        if absolute_path in self.pending_images:
            self._info("This image is already attached.")
            return

        self.pending_images.append(absolute_path)
        self._info(
            f"Image attached ({len(self.pending_images)}/{MAX_IMAGES_PER_MESSAGE}): "
            f"{absolute_path}"
        )
        self._info("Write your next message to send it with the attached image(s).")

    def _list_images(self):
        if not self.pending_images:
            self._info("No images are currently attached.")
            return
        self.console.print(Markdown("**Images pending for the next message:**"))
        for index, image_path in enumerate(self.pending_images, start=1):
            self.console.print(f"  {index}. {image_path}")

    def _clear_images(self):
        count = len(self.pending_images)
        self.pending_images.clear()
        self._info(f"Cleared {count} pending image(s).")

    def handle_command(self, cmd_input: str):
        # Lowercase the command itself, never the arguments: Linux paths are case-sensitive.
        raw_parts = cmd_input.strip().split(":")
        command = raw_parts[0].lower()
        parts = [command, *raw_parts[1:]]

        if command in ["/exit", "/quit"]:
            raise EOFError
        if command == "/help":
            self._show_help()
        elif command == "/image":
            self._attach_image(cmd_input)
        elif command == "/images":
            self._list_images()
        elif command == "/clearimages":
            self._clear_images()
        elif command == "/copy":
            self._copy_code_block(parts)
        elif command == "/new":
            session_id = self.ai.start_new_session()
            self.pending_images.clear()
            self._info(f"Started new session: {session_id}")
        elif command == "/reset":
            self.ai.reset_history()
            self.pending_images.clear()
            self._info("Conversation history has been cleared for this session.")
        elif command == "/debug":
            self.debug_mode = not self.debug_mode
            self.ai.debug_callback = self.show_debug if self.debug_mode else None
            self._info(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}.")
        elif command == "/models":
            self._list_models()
        elif command == "/model":
            self._select_model(parts)
        elif command == "/mode":
            self._select_mode(parts)
        elif command == "/tone":
            self._select_tone(parts)
        elif command == "/sessions":
            self._list_sessions()
        elif command == "/load":
            self._load_session(parts)
        else:
            self._error(f"Unknown command: {command}")
        self.console.print()

    def _show_help(self):
        self.console.print(
            Markdown(
                """
**Session Control:**
- `/new` - Start a new conversation
- `/reset` - Clear the current session history
- `/sessions` - List saved conversations
- `/load:<id/idx>` - Load a saved conversation

**Core Commands:**
- `/copy` - Copy the last code block
- `/copy:<n>` - Copy a specific code block
- `/exit` - Close the application
- `/help` - Show this guide

**Image Attachments:**
- `/image:/path/to/image.png` - Attach an image to the next message
- `/images` - List images waiting to be sent
- `/clearimages` - Remove all pending image attachments
- Supports up to 4 PNG, JPEG, or WebP images per message (8 MiB each)

**Settings:**
- `/debug` - Toggle debug mode
- `/models` - List installed models
- `/model:<name/idx>` - Switch model
- `/mode:<name>` - Select auto, default, math, code, or translate
- `/tone:<name>` - Select adaptive, casual, formal, sarcastic, or concise
"""
            )
        )

    def _copy_code_block(self, parts):
        if not self.last_code_blocks:
            self._error("No code blocks found in the last response.")
            return

        index = len(self.last_code_blocks) - 1
        if len(parts) > 1:
            try:
                index = int(parts[1]) - 1
            except ValueError:
                pass

        if not 0 <= index < len(self.last_code_blocks):
            self._error(f"Invalid block index. Available: 1-{len(self.last_code_blocks)}")
            return

        try:
            pyperclip.copy(self.last_code_blocks[index])
            self._info(f"Code block {index + 1} copied to clipboard.")
        except Exception as exc:
            self._error(f"Error copying to clipboard: {exc}")

    def _list_models(self):
        models = self.ai.list_available_models()
        self.last_models = models
        if not models:
            self._info("No models found.")
            return

        message = "**Available Models:**\n"
        for index, model in enumerate(models, start=1):
            message += f"{index}. `{model}`\n"
        message += "\n*Use `/model:<id>` to switch model.*"
        self.console.print(Markdown(message))

    def _notify_pending_image_support(self):
        if not self.pending_images:
            return
        try:
            capabilities = self.ai.get_model_capabilities()
        except Exception:
            self._info("Images remain queued, but model capabilities could not be checked.")
            return
        if not capabilities.available or not capabilities.vision:
            self._info(
                "Images remain queued, but the selected model cannot currently process "
                "them. Switch back to a vision-capable model or use /clearimages."
            )

    def _select_model(self, parts):
        models = self.ai.list_available_models()
        if not models:
            self._error("No models found via Ollama. Make sure it is running.")
            return

        if len(parts) == 1:
            current = self.ai.model_name
            current_index = next(
                (i for i, model in enumerate(models) if model == current or model.startswith(current + ":")),
                -1,
            )
            self.ai.model_name = models[(current_index + 1) % len(models)]
            self._info(f"Model cycled to: {self.ai.model_name}")
            self._notify_pending_image_support()
            return

        # Preserve Ollama tags such as qwen3.5:9b and llama3.1:8b.
        target = ":".join(parts[1:]).strip()
        model = None
        if target.isdigit():
            index = int(target) - 1
            if 0 <= index < len(self.last_models):
                model = self.last_models[index]
        if not model and target in models:
            model = target

        if model:
            self.ai.model_name = model
            self._info(f"Model switched to: {model}")
            self._notify_pending_image_support()
        else:
            self._error(f"Model '{target}' not found. Available: {', '.join(models)}")

    def _select_mode(self, parts):
        modes = ["auto", "default", "math", "code", "translate"]
        if len(parts) == 1:
            self._info(f"Available modes: {', '.join(modes)}")
            return

        new_mode = parts[1].strip()
        if new_mode not in modes:
            self._error(f"Invalid mode. Available: {', '.join(modes)}")
            return

        self.intent_mode = new_mode
        self._info(f"Mode switched to: {new_mode}")

    def _select_tone(self, parts):
        tones = ["adaptive", "casual", "formal", "sarcastic", "concise"]
        if len(parts) == 1:
            self._info(f"Available tones: {', '.join(tones)}")
            return

        tone = parts[1].strip()
        if tone not in tones:
            self._error(f"Invalid tone. Available: {', '.join(tones)}")
            return
        self.tone_mode = tone
        self._info(f"Tone switched to: {tone}")

    def _list_sessions(self):
        sessions = self.ai.list_sessions_detailed()
        self.last_sessions = sessions
        if not sessions:
            self._info("No previous conversations found.")
            return

        message = "**Previous Conversations:**\n"
        for index, session in enumerate(sessions, start=1):
            updated = time.strftime(
                "%Y-%m-%d %H:%M", time.localtime(session["last_updated"])
            )
            message += f"{index}. `{session['id']}` - {session['title']} ({updated})\n"
        message += "\n*Use `/load:<id>` to load a session.*"
        self.console.print(Markdown(message))

    def _load_session(self, parts):
        if len(parts) == 1:
            self._error(
                "Specify a session ID or index. Example: /load:1 or /load:chat_20231025_120000"
            )
            return

        target = parts[1].strip()
        target_id = target
        if target.isdigit():
            index = int(target) - 1
            if 0 <= index < len(self.last_sessions):
                target_id = self.last_sessions[index]["id"]

        if self.ai.load_session(target_id):
            self.pending_images.clear()
            self._info(f"Loaded session: {target_id}")
        else:
            self._error(f"Failed to load session: {target_id}")

    def _info(self, message):
        self.console.print(f"[dim {COLOR_ACCENT}]i[/] {message}")

    def _error(self, message):
        self.console.print(f"[bold {COLOR_ERROR}]![/] {message}")


def run_tui(ai_instance, debug=False):
    """Launch the terminal user interface."""
    XavionCLI(ai=ai_instance, debug=debug).run()
