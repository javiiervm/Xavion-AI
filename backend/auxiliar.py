import os
import platform

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