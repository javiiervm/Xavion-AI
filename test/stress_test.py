import json
import os
import sys
import time
import requests
import subprocess
from typing import List, Dict, Any, Tuple

# Adjust sys.path to find the 'xavion' package in the root directory
# Since this script is now in 'test/', we add the parent directory.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from xavion.core.engine import XavionAI
    from xavion.core.constants import DEFAULT_MODEL
    from langchain_ollama import OllamaLLM
    from langchain_core.prompts import ChatPromptTemplate
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError as e:
    print(f"Error: Missing dependencies or incorrect directory structure. {e}")
    print("Make sure you are in the project root and have installed requirements.txt.")
    sys.exit(1)

console = Console()

def is_ollama_running():
    """Checks if the Ollama service is active."""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', 11434)) == 0
    except Exception:
        return False

def start_ollama():
    """Attempts to start Ollama if it is not running."""
    if is_ollama_running():
        return True
    
    console.print("[*] Starting Ollama service for testing...", style="yellow")
    try:
        # Cross-platform subprocess management
        if os.name == 'nt':
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
        for i in range(15): # Increased timeout for slower environments
            time.sleep(1)
            if is_ollama_running():
                return True
            console.print(f"    Waiting for Ollama... ({i+1}/15)", style="grey50")
    except Exception as e:
        console.print(f"[!] Failed to start Ollama: {e}", style="red")
    return False

class XavionEvaluator:
    """
    Handles the execution and automated evaluation of Xavion AI.
    """
    def __init__(self, model_name=DEFAULT_MODEL):
        self.ai = XavionAI(model_name=model_name)
        # Using a dedicated LLM instance for judging with temperature 0 for reproducibility
        self.judge_llm = OllamaLLM(model=model_name, temperature=0)

    def get_response(self, question: str) -> str:
        """Runs Xavion and returns the full response string."""
        self.ai.reset_history()
        response = ""
        try:
            # chat_stream handles the internal LangChain orchestration
            for chunk in self.ai.chat_stream(question):
                response += chunk
        except Exception as e:
            return f"ERROR: {str(e)}"
        return response.strip()

    def evaluate(self, question: str, response: str, criteria: str) -> Tuple[bool, str]:
        """Evaluates a response against criteria using rules and LLM judging."""
        
        # --- Rule-Based Checks (Hard Constraints) ---
        
        # 1. Lipogram Check (No 'e')
        if "letter 'e'" in criteria.lower() and "not use" in criteria.lower():
            if 'e' in response.lower():
                return False, "Failed lipogram constraint: the letter 'e' was found."
        
        # 2. Acrostic Check (BOT)
        if "spells 'BOT'" in criteria.upper() or "spells the word 'BOT'" in criteria.upper():
            lines = [l.strip() for l in response.strip().split('\n') if l.strip()]
            if len(lines) < 3:
                return False, "Failed acrostic: response has fewer than 3 lines."
            acrostic = "".join([l[0].upper() for l in lines[:3] if l])
            if acrostic != "BOT":
                return False, f"Failed acrostic: starts with '{acrostic}' instead of 'BOT'."

        # 3. Word Count Check
        if "exactly" in criteria.lower() and "words" in criteria.lower():
            import re
            target = re.search(r'exactly (\d+) words', criteria.lower())
            if target:
                expected_count = int(target.group(1))
                actual_count = len(response.split())
                if actual_count != expected_count:
                    return False, f"Strict word count failed: Expected {expected_count}, got {actual_count}."

        # --- LLM-Based Semantic/Logical Evaluation ---
        
        judge_prompt = ChatPromptTemplate.from_template("""
        You are a strict technical auditor for an AI system.
        
        [CONTEXT]
        User Question: {question}
        AI Response: {response}
        Success Criteria: {criteria}
        
        [TASK]
        Verify if the AI Response correctly fulfills the Success Criteria.
        - Logical consistency is paramount.
        - For false premises, the AI MUST have corrected the user.
        - For technical/code questions, the solution must be optimal/correct as per criteria.
        
        [FORMAT]
        You MUST respond exactly in this format:
        VERDICT: [PASS or FAIL]
        REASON: [A concise 1-sentence explanation]
        """)
        
        try:
            chain = judge_prompt | self.judge_llm
            result = chain.invoke({
                "question": question,
                "response": response,
                "criteria": criteria
            })
            
            lines = [l.strip() for l in result.split('\n') if l.strip()]
            verdict = "FAIL"
            reason = "Evaluation inconclusive."
            
            for line in lines:
                if line.upper().startswith("VERDICT:"):
                    verdict = "PASS" if "PASS" in line.upper() else "FAIL"
                if line.upper().startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()
            
            return (verdict == "PASS"), reason
        except Exception as e:
            return False, f"Judge error: {str(e)}"

def run_stress_test():
    """Main execution loop for the stress test."""
    # Path relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    suite_path = os.path.join(script_dir, "Xavion_LLM_Stress_Test.json")
    
    if not os.path.exists(suite_path):
        console.print(f"[bold red]Error:[/] File '{suite_path}' not found.", style="red")
        return

    if not start_ollama():
        console.print("[bold red]Critical:[/] Ollama is required but not running. Aborting.", style="red")
        return

    evaluator = XavionEvaluator()
    
    with open(suite_path, 'r', encoding='utf-8') as f:
        suite = json.load(f)

    console.print(f"\n[bold white]>>> XAVION AI STRESS TEST: {suite.get('benchmark_suite', 'V2')} <<<[/]")
    console.print(f"[italic grey50]{suite.get('description', '')}[/]\n")

    global_stats = {"total": 0, "passed": 0}
    category_results = []

    for cat in suite.get('categories', []):
        section = cat.get('section', 'Unknown Section')
        tests = cat.get('tests', [])
        cat_stats = {"total": 0, "passed": 0}
        
        console.print(f"[bold cyan]SECTION: {section}[/]")
        
        for test in tests:
            q = test.get('Q')
            s = test.get('S')
            
            response = evaluator.get_response(q)
            passed, reason = evaluator.evaluate(q, response, s)
            
            cat_stats['total'] += 1
            global_stats['total'] += 1
            
            if passed:
                cat_stats['passed'] += 1
                global_stats['passed'] += 1
                console.print(f"  [bold green][PASS][/] {q[:60]}...")
            else:
                console.print(f"  [bold red][FAIL][/] {q[:60]}...")
                console.print(f"         [yellow]Reason:[/] {reason}")
        
        accuracy = (cat_stats['passed'] / cat_stats['total']) * 100 if cat_stats['total'] > 0 else 0
        category_results.append((section, accuracy))
        console.print(f"[bold]Category Score:[/] [white]{accuracy:.1f}%[/]\n")

    # Final Report
    global_acc = (global_stats['passed'] / global_stats['total']) * 100 if global_stats['total'] > 0 else 0
    
    console.print("[bold white underline]FINAL PERFORMANCE SUMMARY[/]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Success Rate", justify="right")
    
    for name, acc in category_results:
        table.add_row(name, f"{acc:.1f}%")
    
    table.add_section()
    table.add_row("[bold white]TOTAL SCORE[/]", f"[bold yellow]{global_acc:.1f}%[/]")
    
    console.print(table)
    
    if global_acc > 85:
        insight = "Elite reasoning and constraint adherence. Xavion is ready for production environments."
    elif global_acc > 70:
        insight = "Solid performance. Xavion is reliable but might struggle with nested logical traps or ultra-strict constraints."
    elif global_acc > 50:
        insight = "Moderately capable. Consider fine-tuning the System Prompt or moving to a larger parameter model for complex tasks."
    else:
        insight = "Unreliable for technical or constrained tasks. Immediate review of prompt templates and intent detection is required."
    
    console.print(Panel(insight, title="[bold]Developer Insight[/]", border_style="yellow"))

if __name__ == "__main__":
    try:
        run_stress_test()
    except KeyboardInterrupt:
        console.print("\n[bold red]Test suite interrupted.[/]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error during execution:[/] {e}")
