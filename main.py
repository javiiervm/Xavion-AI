import argparse
import os
import signal
import subprocess
import sys
import time

import requests

from xavion.core.constants import DEFAULT_MODEL


def is_ollama_running():
    """Return whether the local Ollama service is accepting connections."""
    try:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(("localhost", 11434)) == 0
    except Exception:
        return False


def check_for_models():
    """Return whether Ollama has at least one installed model."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            return len(response.json().get("models", [])) > 0
    except Exception:
        pass
    return False


def pull_model(model_name=DEFAULT_MODEL):
    """Download a model through the Ollama CLI."""
    print(f"[*] Downloading model '{model_name}'... This may take a while.")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"[+] Model '{model_name}' downloaded successfully.")
        return True
    except Exception as exc:
        print(f"[!] Failed to download model: {exc}")
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
        print("[!] Error: 'ollama' command not found. Please install Ollama.")
        sys.exit(1)
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


def run_interface(interface_name, debug=False, port=8000):
    """Load the requested frontend interface."""
    if interface_name == "cli":
        from xavion.interfaces.cli.app import run_cli

        run_cli(debug=debug)
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

    args = parser.parse_args()
    ollama_process = start_ollama()

    if not check_for_models():
        print("\n[!] No models found in your Ollama installation.")
        choice = input(
            f"[?] Would you like to download '{DEFAULT_MODEL}' now? (y/n): "
        ).lower()
        if choice == "y":
            if not pull_model(DEFAULT_MODEL):
                print("[!] Cannot proceed without a model. Exiting.")
                if ollama_process:
                    stop_ollama(ollama_process)
                sys.exit(1)
        else:
            print("[!] A model is required to run Xavion AI. Exiting.")
            if ollama_process:
                stop_ollama(ollama_process)
            sys.exit(1)

    try:
        run_interface(args.interface, debug=args.debug, port=args.port)
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
