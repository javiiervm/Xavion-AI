import json
import os
import re
import subprocess
import sys
import time
from typing import Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_ollama import OllamaLLM

    from xavion.core.constants import DEFAULT_MODEL
    from xavion.core.engine import XavionAI
except ImportError as exc:
    print(f"Error: Missing dependencies or incorrect directory structure. {exc}")
    print("Make sure you are in the project root and have installed requirements.txt.")
    sys.exit(1)


console = Console()


def is_ollama_running():
    """Return whether the local Ollama service is active."""
    try:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(("localhost", 11434)) == 0
    except Exception:
        return False


def start_ollama():
    """Start Ollama for the test suite when necessary."""
    if is_ollama_running():
        return True

    console.print("[*] Starting Ollama service for testing...", style="yellow")
    try:
        if os.name == "nt":
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )

        for attempt in range(15):
            time.sleep(1)
            if is_ollama_running():
                return True
            console.print(
                f"    Waiting for Ollama... ({attempt + 1}/15)", style="grey50"
            )
    except Exception as exc:
        console.print(f"[!] Failed to start Ollama: {exc}", style="red")
    return False


class XavionEvaluator:
    """Execute and evaluate Xavion AI benchmark cases."""

    def __init__(self, model_name=DEFAULT_MODEL):
        self.ai = XavionAI(model_name=model_name)
        self.judge_llm = OllamaLLM(model=model_name, temperature=0)

    def get_response(self, question: str) -> str:
        """Run Xavion and return the complete response."""
        self.ai.reset_history()
        response = ""
        try:
            for chunk in self.ai.chat_stream(question):
                response += chunk
        except Exception as exc:
            return f"ERROR: {exc}"
        return response.strip()

    def evaluate(
        self, question: str, response: str, criteria: str
    ) -> Tuple[bool, str]:
        """Evaluate a response with deterministic checks and LLM judging."""
        if "letter 'e'" in criteria.lower() and "not use" in criteria.lower():
            if "e" in response.lower():
                return False, "Failed lipogram constraint: the letter 'e' was found."

        if "spells 'BOT'" in criteria.upper() or "spells the word 'BOT'" in criteria.upper():
            lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
            if len(lines) < 3:
                return False, "Failed acrostic: response has fewer than 3 lines."
            acrostic = "".join(line[0].upper() for line in lines[:3] if line)
            if acrostic != "BOT":
                return False, f"Failed acrostic: starts with '{acrostic}' instead of 'BOT'."

        if "exactly" in criteria.lower() and "words" in criteria.lower():
            target = re.search(r"exactly (\d+) words", criteria.lower())
            if target:
                expected_count = int(target.group(1))
                actual_count = len(response.split())
                if actual_count != expected_count:
                    return (
                        False,
                        f"Strict word count failed: expected {expected_count}, got {actual_count}.",
                    )

        judge_prompt = ChatPromptTemplate.from_template(
            """
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
        """
        )

        try:
            chain = judge_prompt | self.judge_llm
            result = chain.invoke(
                {
                    "question": question,
                    "response": response,
                    "criteria": criteria,
                }
            )

            lines = [line.strip() for line in result.split("\n") if line.strip()]
            verdict = "FAIL"
            reason = "Evaluation inconclusive."

            for line in lines:
                if line.upper().startswith("VERDICT:"):
                    verdict = "PASS" if "PASS" in line.upper() else "FAIL"
                if line.upper().startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()

            return verdict == "PASS", reason
        except Exception as exc:
            return False, f"Judge error: {exc}"


def run_stress_test():
    """Run the complete Xavion LLM stress test suite."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    suite_path = os.path.join(script_dir, "Xavion_LLM_Stress_Test.json")

    if not os.path.exists(suite_path):
        console.print(
            f"[bold red]Error:[/] File '{suite_path}' not found.", style="red"
        )
        return

    if not start_ollama():
        console.print(
            "[bold red]Critical:[/] Ollama is required but not running. Aborting.",
            style="red",
        )
        return

    evaluator = XavionEvaluator()

    with open(suite_path, "r", encoding="utf-8") as file:
        suite = json.load(file)

    console.print(
        f"\n[bold white]>>> XAVION AI STRESS TEST: "
        f"{suite.get('benchmark_suite', 'V2')} <<<[/]"
    )
    console.print(f"[italic grey50]{suite.get('description', '')}[/]\n")

    global_stats = {"total": 0, "passed": 0}
    category_results = []

    for category in suite.get("categories", []):
        section = category.get("section", "Unknown Section")
        tests = category.get("tests", [])
        category_stats = {"total": 0, "passed": 0}

        console.print(f"[bold cyan]SECTION: {section}[/]")

        for test in tests:
            question = test.get("Q")
            criteria = test.get("S")

            response = evaluator.get_response(question)
            passed, reason = evaluator.evaluate(question, response, criteria)

            category_stats["total"] += 1
            global_stats["total"] += 1

            if passed:
                category_stats["passed"] += 1
                global_stats["passed"] += 1
                console.print(f"  [bold green][PASS][/] {question[:60]}...")
            else:
                console.print(f"  [bold red][FAIL][/] {question[:60]}...")
                console.print(f"         [yellow]Reason:[/] {reason}")

        accuracy = (
            (category_stats["passed"] / category_stats["total"]) * 100
            if category_stats["total"] > 0
            else 0
        )
        category_results.append((section, accuracy))
        console.print(f"[bold]Category Score:[/] [white]{accuracy:.1f}%[/]\n")

    global_accuracy = (
        (global_stats["passed"] / global_stats["total"]) * 100
        if global_stats["total"] > 0
        else 0
    )

    console.print("[bold white underline]FINAL PERFORMANCE SUMMARY[/]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Success Rate", justify="right")

    for name, accuracy in category_results:
        table.add_row(name, f"{accuracy:.1f}%")

    table.add_section()
    table.add_row(
        "[bold white]TOTAL SCORE[/]", f"[bold yellow]{global_accuracy:.1f}%[/]"
    )

    console.print(table)

    if global_accuracy > 85:
        insight = (
            "High benchmark score. Review category-level failures before drawing "
            "release-readiness conclusions."
        )
    elif global_accuracy > 70:
        insight = (
            "Good benchmark score, with remaining weaknesses in some complex or "
            "strictly constrained tasks."
        )
    elif global_accuracy > 50:
        insight = (
            "Mixed benchmark performance. Review prompt behavior and model choice "
            "for the weakest categories."
        )
    else:
        insight = (
            "Low benchmark score. Review prompt templates, intent detection, and "
            "model suitability before relying on these task categories."
        )

    console.print(
        Panel(insight, title="[bold]Benchmark Summary[/]", border_style="yellow")
    )


if __name__ == "__main__":
    try:
        run_stress_test()
    except KeyboardInterrupt:
        console.print("\n[bold red]Test suite interrupted.[/]")
    except Exception as exc:
        console.print(f"\n[bold red]Fatal error during execution:[/] {exc}")
