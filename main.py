import argparse
import sys
import subprocess
import time
import os
import signal
import requests

def is_ollama_running():
    """Checks if the Ollama service is already running by checking the port or process."""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', 11434)) == 0
    except Exception:
        return False

def check_for_models():
    """Checks if any models are available in Ollama."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            return len(response.json().get("models", [])) > 0
    except Exception:
        pass
    return False

def pull_model(model_name="llama3.1"):
    """Downloads a model from Ollama."""
    print(f"[*] Downloading model '{model_name}'... This may take a while.")
    try:
        # We run this interactively so the user can see progress
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"[+] Model '{model_name}' downloaded successfully.")
        return True
    except Exception as e:
        print(f"[!] Failed to download model: {e}")
        return False

def start_ollama():
    """Starts the Ollama server in the background."""
    if is_ollama_running():
        # print("[*] Ollama service is already running.")
        return None

    print("[*] Starting Ollama service...")
    try:
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid 
        )
        
        max_retries = 5
        for i in range(max_retries):
            time.sleep(1)
            if is_ollama_running():
                print("[+] Ollama service started successfully.")
                return process
            print(f"    Waiting for Ollama... ({i+1}/{max_retries})")
        
        return process
    except FileNotFoundError:
        print("[!] Error: 'ollama' command not found. Please install Ollama.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Failed to start Ollama: {e}")
        return None

def stop_ollama(process):
    """Stops the Ollama server process."""
    if process:
        print("\n[*] Stopping Ollama service...")
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            print("[+] Ollama service stopped.")
        except Exception as e:
            print(f"[!] Error stopping Ollama: {e}")

def run_interface(interface_name, debug=False, port=8000):
    """
    Modular loader for different frontends.
    """
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
    parser = argparse.ArgumentParser(description="Xavion AI - Professional Modular Assistant")
    parser.add_argument(
        "interface", 
        choices=["cli", "web", "desktop"], 
        nargs="?", 
        default="cli",
        help="Select the frontend interface (default: cli)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=8000, help="Port for web/api (default: 8000)")

    args = parser.parse_args()

    # Automatic Ollama Lifecycle
    ollama_process = start_ollama()

    # Check for models
    if not check_for_models():
        print("\n[!] No models found in your Ollama installation.")
        choice = input("[?] Would you like to download 'llama3.1' now? (y/n): ").lower()
        if choice == 'y':
            if not pull_model("llama3.1"):
                print("[!] Cannot proceed without a model. Exiting.")
                if ollama_process: stop_ollama(ollama_process)
                sys.exit(1)
        else:
            print("[!] A model is required to run Xavion AI. Exiting.")
            if ollama_process: stop_ollama(ollama_process)
            sys.exit(1)

    try:
        run_interface(args.interface, debug=args.debug, port=args.port)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[!] Critical error during execution: {e}")
    finally:
        if ollama_process:
            stop_ollama(ollama_process)
        print("[+] Xavion AI closed.")

if __name__ == "__main__":
    main()
