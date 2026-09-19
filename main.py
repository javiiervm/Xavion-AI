import argparse
import os
import signal
import subprocess
import sys
import time
import shutil

from xavion.core.config import (
    CONFIG_FILE,
    get_default_model,
    resolve_model_name,
    set_default_model,
)
from xavion.core.constants import RECOMMENDED_MODEL

def is_ollama_running():
    """Return whether the local Ollama service is accepting connections."""
    try:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(("localhost", 11434)) == 0
    except Exception:
        return False


def list_ollama_models():
    """Return models reported by the Ollama CLI."""

    result = subprocess.run(
        ["ollama", "list"],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [
        line
        for line in result.stdout.splitlines()
        if line.strip()
    ]

    if len(lines) <= 1:
        return []

    return [
        line.split()[0]
        for line in lines[1:]
    ]


def is_model_installed(model_name, installed_models=None):
    """Return whether a requested model is installed."""

    models = (
        installed_models
        if installed_models is not None
        else list_ollama_models()
    )

    if model_name in models:
        return True

    if ":" not in model_name:
        return f"{model_name}:latest" in models

    return False


def pull_model(model_name=RECOMMENDED_MODEL):
    """Download a model through the Ollama CLI."""
    print(f"[*] Downloading model '{model_name}'... This may take a while.")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"[+] Model '{model_name}' downloaded successfully.")
        return True
    except Exception as exc:
        print(f"[!] Failed to download model: {exc}")
        return False


def install_ollama():
    """Install Ollama using the official Linux installer."""

    if not sys.platform.startswith("linux"):
        print(
            "[!] Automatic Ollama installation is currently supported only on Linux."
        )
        return False

    if shutil.which("curl") is None:
        print("[!] 'curl' is required to install Ollama automatically.")
        return False

    print("[*] Installing Ollama...")

    try:
        installer = subprocess.run(
            ["curl", "-fsSL", "https://ollama.com/install.sh"],
            check=True,
            capture_output=True,
            text=True,
        )

        subprocess.run(
            ["sh"],
            input=installer.stdout,
            text=True,
            check=True,
        )

        if shutil.which("ollama") is None:
            print("[!] Ollama installation completed, but the command was not found.")
            return False

        print("[+] Ollama installed successfully.")
        return True

    except subprocess.CalledProcessError as exc:
        print(f"[!] Failed to install Ollama: {exc}")
        return False


def start_ollama():
    """Start the Ollama server when it is not already running."""
    if is_ollama_running():
        return None

    print("[*] Starting Ollama service...")
    try:
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )

        max_retries = 5
        for attempt in range(max_retries):
            time.sleep(1)
            if is_ollama_running():
                print("[+] Ollama service started successfully.")
                return process
            print(f"    Waiting for Ollama... ({attempt + 1}/{max_retries})")

        return process
    except FileNotFoundError:
        print("[!] Error: 'ollama' command not found.")
        return None
    except Exception as exc:
        print(f"[!] Failed to start Ollama: {exc}")
        return None


def stop_ollama(process):
    """Stop an Ollama process started by Xavion."""
    if process:
        print("\n[*] Stopping Ollama service...")
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            print("[+] Ollama service stopped.")
        except Exception as exc:
            print(f"[!] Error stopping Ollama: {exc}")


def run_config():
    """Run the interactive Xavion configuration wizard."""

    ollama_process = None

    print("\n=== Xavion Configuration ===\n")

    try:
        while True:
            try:
                models = list_ollama_models()
                break

            except FileNotFoundError:
                print("[!] Ollama is not installed.")
                print("1. Install Ollama")
                print("2. Exit")

                choice = input("[?] Select an option: ").strip()

                if choice == "1":
                    if not install_ollama():
                        return
                    continue

                if choice == "2":
                    return

                print("[!] Invalid option.")

            except subprocess.CalledProcessError:
                print("[!] Ollama is installed, but the service is not available.")
                print("1. Start Ollama")
                print("2. Retry")
                print("3. Exit")

                choice = input("[?] Select an option: ").strip()

                if choice == "1":
                    ollama_process = start_ollama()

                    if not is_ollama_running():
                        print("[!] Ollama could not be started.")
                        return

                elif choice == "2":
                    continue

                elif choice == "3":
                    return

                else:
                    print("[!] Invalid option.")

        current_model = get_default_model()

        while True:
            print()

            if current_model:
                print(f"Current default model: {current_model}")
            else:
                print("No default model is currently configured.")

            print()

            if models:
                print("Installed models:")

                for index, model in enumerate(models, start=1):
                    marker = " (current)" if model == current_model else ""
                    print(f"{index}. {model}{marker}")

                install_option = len(models) + 1
                exit_option = len(models) + 2

                print(f"{install_option}. Install another model")
                print(f"{exit_option}. Exit")

                choice = input("[?] Select the default model: ").strip()

                if not choice.isdigit():
                    print("[!] Invalid option.")
                    continue

                selection = int(choice)

                if 1 <= selection <= len(models):
                    selected_model = models[selection - 1]

                    set_default_model(selected_model)

                    print(f"[+] Default model set to '{selected_model}'.")
                    print(f"[+] Configuration saved to: {CONFIG_FILE}")
                    return

                if selection == install_option:
                    model_name = input(
                        f"[?] Model to install [{RECOMMENDED_MODEL}]: "
                    ).strip()

                    if not model_name:
                        model_name = RECOMMENDED_MODEL

                    if pull_model(model_name):
                        set_default_model(model_name)

                        print(f"[+] Default model set to '{model_name}'.")
                        print(f"[+] Configuration saved to: {CONFIG_FILE}")
                        return

                    continue

                if selection == exit_option:
                    return

                print("[!] Invalid option.")

            else:
                print("No Ollama models are installed.")
                print("1. Install a model")
                print("2. Exit")

                choice = input("[?] Select an option: ").strip()

                if choice == "1":
                    model_name = input(
                        f"[?] Model to install [{RECOMMENDED_MODEL}]: "
                    ).strip()

                    if not model_name:
                        model_name = RECOMMENDED_MODEL

                    if pull_model(model_name):
                        set_default_model(model_name)

                        print(f"[+] Default model set to '{model_name}'.")
                        print(f"[+] Configuration saved to: {CONFIG_FILE}")
                        return

                elif choice == "2":
                    return

                else:
                    print("[!] Invalid option.")

    finally:
        if ollama_process:
            stop_ollama(ollama_process)


def run_interface(interface_name, model_name, debug=False, port=8000):
    """Load the requested frontend interface."""
    if interface_name == "cli":
        from xavion.interfaces.cli.app import run_cli

        run_cli(
            model_name=model_name,
            debug=debug,
        )
    elif interface_name == "web":
        print("[!] Web interface is not implemented yet.")
    elif interface_name == "desktop":
        print("[!] Desktop interface is not implemented yet.")
    else:
        print(f"[!] Unknown interface: {interface_name}")


def main():
    parser = argparse.ArgumentParser(description="Xavion AI local assistant")
    parser.add_argument(
        "interface",
        choices=["cli", "web", "desktop"],
        nargs="?",
        default="cli",
        help="Select the frontend interface (default: cli)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for web/API (default: 8000)"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Configure Xavion and select the persistent default model",
    )
    parser.add_argument(
        "--model",
        help="Use a model for this execution without changing the configured default",
    )

    args = parser.parse_args()
    if args.config:
        run_config()
        return

    model_name = resolve_model_name(args.model)

    if model_name is None:
        print("[!] No default model has been configured.")
        print("[*] Run 'python main.py --config' to select one.")
        print("[*] Alternatively, use '--model <name>' for this execution.")
        return

    ollama_process = start_ollama()

    if not is_ollama_running():
        print("[!] Ollama could not be started.")
        return

    try:
        installed_models = list_ollama_models()
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[!] Failed to query installed Ollama models.")

        if ollama_process:
            stop_ollama(ollama_process)

        return

    if not is_model_installed(model_name, installed_models):
        print(f"[!] Model '{model_name}' is not installed.")
        print("[*] Run 'python main.py --config' or install it with Ollama.")

        if ollama_process:
            stop_ollama(ollama_process)

        return

    try:
        run_interface(
            args.interface,
            model_name=model_name,
            debug=args.debug,
            port=args.port,
        )
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"[!] Critical error during execution: {exc}")
    finally:
        if ollama_process:
            stop_ollama(ollama_process)
        print("\n[+] Xavion AI closed.\n")


if __name__ == "__main__":
    main()
