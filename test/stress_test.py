from __future__ import annotations

import argparse
import json
import math
import os
import re
import socket
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_ollama import OllamaLLM

    from xavion.core.config import resolve_model_name
    from xavion.core.engine import XavionAI
except ImportError as exc:
    print(f"Error: Missing dependencies or incorrect directory structure. {exc}")
    print("Run this script from the project environment with requirements installed.")
    sys.exit(1)


console = Console(record=True)
DEFAULT_SUITE = "Xavion_LLM_Stress_Test.json"
DEFAULT_REPORT_DIR = "benchmark_reports"
DEFAULT_LOG_DIR = "benchmark_logs"
DEFAULT_PASS_THRESHOLD = 80.0
JUDGE_SCALE_MAX = 4


@dataclass
class CheckResult:
    name: str
    kind: str
    score: float
    weight: float
    hard: bool
    passed: bool
    reason: str


@dataclass
class RunResult:
    score: float
    passed: bool
    latency_seconds: float
    response: str
    checks: List[CheckResult]
    judge_reason: str = ""
    error: Optional[str] = None


@dataclass
class TestResult:
    test_id: str
    category: str
    prompt_preview: str
    weight: float
    runs: List[RunResult]
    mean_score: float
    score_stddev: float
    pass_rate: float
    stable_pass: bool


class BenchmarkError(RuntimeError):
    pass


def is_ollama_running(host: str = "localhost", port: int = 11434) -> bool:
    """Return whether a local Ollama service is accepting TCP connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            return sock.connect_ex((host, port)) == 0
    except OSError:
        return False


def start_ollama() -> bool:
    """Start Ollama locally when it is not already running."""
    if is_ollama_running():
        return True

    console.print("[*] Starting Ollama service for benchmarking...", style="yellow")
    try:
        kwargs: Dict[str, Any] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if os.name != "nt":
            kwargs["preexec_fn"] = os.setsid

        subprocess.Popen(["ollama", "serve"], **kwargs)
        for attempt in range(20):
            time.sleep(0.75)
            if is_ollama_running():
                return True
            console.print(
                f"    Waiting for Ollama... ({attempt + 1}/20)", style="grey50"
            )
    except Exception as exc:
        console.print(f"[!] Failed to start Ollama: {exc}", style="red")
    return False


def extract_json_object(text: str) -> Dict[str, Any]:
    """Extract the first valid JSON object from a model response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)

    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stripped[index:])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue

    raise ValueError("Judge did not return a valid JSON object.")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def words(text: str) -> List[str]:
    return re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE)


def sentences(text: str) -> List[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text.strip()) if item.strip()]


def line_starts(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "".join(line[0] for line in lines if line)


def content_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def check_exact(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    expected = str(spec["expected"])
    case_sensitive = bool(spec.get("case_sensitive", False))
    actual = response.strip()
    if not case_sensitive:
        actual = actual.casefold()
        expected = expected.casefold()
    passed = actual == expected
    return passed, f"Expected exact response {spec['expected']!r}."


def check_contains_all(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    haystack = response if spec.get("case_sensitive") else response.casefold()
    values = [str(v) for v in spec.get("values", [])]
    missing = []
    for value in values:
        needle = value if spec.get("case_sensitive") else value.casefold()
        if needle not in haystack:
            missing.append(value)
    return not missing, "Missing: " + ", ".join(missing) if missing else "All required fragments found."


def check_contains_any(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    haystack = response if spec.get("case_sensitive") else response.casefold()
    values = [str(v) for v in spec.get("values", [])]
    found = []
    for value in values:
        needle = value if spec.get("case_sensitive") else value.casefold()
        if needle in haystack:
            found.append(value)
    return bool(found), "Matched: " + ", ".join(found) if found else "No accepted fragment found."


def check_not_contains_any(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    haystack = response if spec.get("case_sensitive") else response.casefold()
    values = [str(v) for v in spec.get("values", [])]
    found = []
    for value in values:
        needle = value if spec.get("case_sensitive") else value.casefold()
        if needle in haystack:
            found.append(value)
    return not found, "Forbidden fragments found: " + ", ".join(found) if found else "No forbidden fragments found."


def check_regex(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    flags = re.MULTILINE
    if not spec.get("case_sensitive"):
        flags |= re.IGNORECASE
    matched = re.search(str(spec["pattern"]), response, flags=flags) is not None
    return matched, f"Regex {'matched' if matched else 'did not match'}: {spec['pattern']}"


def check_not_regex(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    passed, _ = check_regex(response, spec)
    return not passed, f"Forbidden regex {'matched' if passed else 'did not match'}: {spec['pattern']}"


def check_word_count(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    actual = len(words(response))
    if "expected" in spec:
        expected = int(spec["expected"])
        return actual == expected, f"Expected {expected} words, got {actual}."
    minimum = int(spec["min"]) if "min" in spec else 0
    maximum = int(spec["max"]) if "max" in spec else math.inf
    expected_range = f"{minimum}-{maximum if maximum != math.inf else '∞'}"
    return minimum <= actual <= maximum, f"Expected {expected_range} words, got {actual}."


def check_line_count(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    actual = len(content_lines(response))
    expected = int(spec["expected"])
    return actual == expected, f"Expected {expected} non-empty lines, got {actual}."


def check_acrostic(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    expected = str(spec["expected"])
    actual = line_starts(response)[: len(expected)]
    case_sensitive = bool(spec.get("case_sensitive", False))
    if not case_sensitive:
        expected = expected.upper()
        actual = actual.upper()
    return actual == expected, f"Expected acrostic {expected!r}, got {actual!r}."


def check_forbidden_character(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    char = str(spec["value"])
    haystack = response if spec.get("case_sensitive") else response.casefold()
    needle = char if spec.get("case_sensitive") else char.casefold()
    count = haystack.count(needle)
    return count == 0, f"Forbidden character {char!r} occurred {count} time(s)."


def check_all_words_start_with(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    prefix = str(spec["prefix"])
    tokens = words(response)
    if not tokens:
        return False, "Response contains no words."
    cmp_prefix = prefix if spec.get("case_sensitive") else prefix.casefold()
    invalid = []
    for token in tokens:
        cmp_token = token if spec.get("case_sensitive") else token.casefold()
        if not cmp_token.startswith(cmp_prefix):
            invalid.append(token)
    preview = ", ".join(invalid[:8])
    return not invalid, f"Invalid word(s): {preview}" if invalid else "Every word satisfies the prefix constraint."


def check_max_sentences(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    actual = len(sentences(response))
    maximum = int(spec["max"])
    return actual <= maximum, f"Expected at most {maximum} sentence(s), got {actual}."


def check_numeric_range(response: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    pattern = str(spec.get("pattern", r"-?\d+(?:\.\d+)?"))
    match = re.search(pattern, response.replace(",", ""))
    if not match:
        return False, "No numeric value could be extracted."
    try:
        value = float(match.group(1) if match.lastindex else match.group(0))
    except ValueError:
        return False, "Extracted numeric value is invalid."
    minimum = float(spec.get("min", -math.inf))
    maximum = float(spec.get("max", math.inf))
    return minimum <= value <= maximum, f"Extracted value {value}; expected range [{minimum}, {maximum}]."


CHECKERS = {
    "exact": check_exact,
    "contains_all": check_contains_all,
    "contains_any": check_contains_any,
    "not_contains_any": check_not_contains_any,
    "regex": check_regex,
    "not_regex": check_not_regex,
    "word_count": check_word_count,
    "line_count": check_line_count,
    "acrostic": check_acrostic,
    "forbidden_character": check_forbidden_character,
    "all_words_start_with": check_all_words_start_with,
    "max_sentences": check_max_sentences,
    "numeric_range": check_numeric_range,
}


class XavionEvaluator:
    """Run Xavion benchmark cases and score them with hybrid evaluation."""

    def __init__(self, model_name: str, judge_model: str):
        self.model_name = model_name
        self.judge_model = judge_model
        self.ai = XavionAI(model_name=model_name)
        self.judge_llm = OllamaLLM(model=judge_model, temperature=0)
        self.judge_prompt = ChatPromptTemplate.from_template(
            """
You are a strict benchmark grader. Grade only what is present in the response.
Do not reward verbosity, style, or plausible intent unless a rubric dimension asks for it.
Do not repair the answer mentally. If an important claim is wrong, score accordingly.

USER PROMPT / CONVERSATION:
{question}

ASSISTANT RESPONSE:
{response}

RUBRIC DIMENSIONS:
{dimensions}

Score every dimension from 0 to 4 using this scale:
0 = completely fails or contradicts the criterion
1 = major errors / mostly fails
2 = partially correct, important omissions or issues
3 = correct with only minor issues
4 = fully satisfies the criterion

Return ONLY valid JSON in this exact shape:
{{
  "scores": {{"dimension_name": 0}},
  "reason": "One concise explanation focused on the most important issue."
}}
"""
        )

    def reset(self) -> None:
        self.ai.reset_history()

    def _stream(self, message: str) -> str:
        chunks: List[str] = []
        for chunk in self.ai.chat_stream(message):
            chunks.append(chunk)
        return "".join(chunks).strip()

    def run_case(self, test: Dict[str, Any]) -> Tuple[str, float, str]:
        """Execute a single- or multi-turn case and return final response + latency."""
        self.reset()
        conversation_log: List[str] = []
        started = time.perf_counter()

        try:
            if "turns" in test:
                turns = test["turns"]
                if not isinstance(turns, list) or not turns:
                    raise BenchmarkError("'turns' must be a non-empty list.")
                final_response = ""
                for turn in turns:
                    message = turn["user"] if isinstance(turn, dict) else str(turn)
                    final_response = self._stream(message)
                    conversation_log.append(f"USER: {message}\nASSISTANT: {final_response}")
            else:
                prompt = str(test["prompt"])
                final_response = self._stream(prompt)
                conversation_log.append(f"USER: {prompt}\nASSISTANT: {final_response}")

            latency = time.perf_counter() - started
            return final_response, latency, "\n\n".join(conversation_log)
        except Exception as exc:
            latency = time.perf_counter() - started
            return f"ERROR: {exc}", latency, "\n\n".join(conversation_log)

    def deterministic_checks(
        self, response: str, checks: Sequence[Dict[str, Any]]
    ) -> List[CheckResult]:
        results: List[CheckResult] = []
        for index, spec in enumerate(checks):
            kind = str(spec.get("type", ""))
            name = str(spec.get("name", f"check_{index + 1}"))
            weight = float(spec.get("weight", 1.0))
            hard = bool(spec.get("hard", False))
            checker = CHECKERS.get(kind)
            if checker is None:
                results.append(
                    CheckResult(
                        name=name,
                        kind=kind,
                        score=0.0,
                        weight=weight,
                        hard=True,
                        passed=False,
                        reason=f"Unknown deterministic check type: {kind}",
                    )
                )
                continue

            try:
                passed, reason = checker(response, spec)
            except Exception as exc:
                passed, reason = False, f"Check error: {exc}"

            results.append(
                CheckResult(
                    name=name,
                    kind=kind,
                    score=100.0 if passed else 0.0,
                    weight=weight,
                    hard=hard,
                    passed=passed,
                    reason=reason,
                )
            )
        return results

    def semantic_checks(
        self,
        question: str,
        response: str,
        dimensions: Sequence[Dict[str, Any]],
    ) -> Tuple[List[CheckResult], str]:
        if not dimensions:
            return [], ""

        dimension_payload = [
            {
                "name": str(item["name"]),
                "rubric": str(item["rubric"]),
            }
            for item in dimensions
        ]

        chain = self.judge_prompt | self.judge_llm
        last_error = ""
        for _ in range(2):
            try:
                raw = chain.invoke(
                    {
                        "question": question,
                        "response": response,
                        "dimensions": json.dumps(
                            dimension_payload, ensure_ascii=False, indent=2
                        ),
                    }
                )
                parsed = extract_json_object(raw)
                score_map = parsed.get("scores", {})
                reason = str(parsed.get("reason", ""))
                results: List[CheckResult] = []

                for item in dimensions:
                    name = str(item["name"])
                    raw_score = score_map.get(name)
                    if raw_score is None:
                        raise ValueError(f"Missing judge score for dimension '{name}'.")
                    numeric = max(0.0, min(float(raw_score), float(JUDGE_SCALE_MAX)))
                    normalized = numeric / JUDGE_SCALE_MAX * 100.0
                    threshold = float(item.get("pass_score", 3))
                    results.append(
                        CheckResult(
                            name=name,
                            kind="judge",
                            score=normalized,
                            weight=float(item.get("weight", 1.0)),
                            hard=bool(item.get("hard", False)),
                            passed=numeric >= threshold,
                            reason=f"Judge score {numeric:.1f}/{JUDGE_SCALE_MAX}.",
                        )
                    )
                return results, reason
            except Exception as exc:
                last_error = str(exc)

        failed = [
            CheckResult(
                name=str(item["name"]),
                kind="judge",
                score=0.0,
                weight=float(item.get("weight", 1.0)),
                hard=True,
                passed=False,
                reason=f"Judge failure: {last_error}",
            )
            for item in dimensions
        ]
        return failed, f"Judge failure: {last_error}"

    @staticmethod
    def combine_checks(
        checks: Sequence[CheckResult], pass_threshold: float
    ) -> Tuple[float, bool]:
        if not checks:
            return 0.0, False

        total_weight = sum(max(check.weight, 0.0) for check in checks)
        if total_weight <= 0:
            return 0.0, False

        score = sum(check.score * max(check.weight, 0.0) for check in checks) / total_weight
        hard_failed = any(check.hard and not check.passed for check in checks)
        return score, (score >= pass_threshold and not hard_failed)


def validate_suite(suite: Dict[str, Any]) -> None:
    if not isinstance(suite.get("categories"), list) or not suite["categories"]:
        raise BenchmarkError("Suite must contain a non-empty 'categories' list.")

    seen_ids = set()
    for category in suite["categories"]:
        if "section" not in category or "tests" not in category:
            raise BenchmarkError("Every category needs 'section' and 'tests'.")
        for test in category["tests"]:
            test_id = test.get("id")
            if not test_id:
                raise BenchmarkError("Every test needs a unique 'id'.")
            if test_id in seen_ids:
                raise BenchmarkError(f"Duplicate test id: {test_id}")
            seen_ids.add(test_id)
            if "prompt" not in test and "turns" not in test:
                raise BenchmarkError(f"Test {test_id} needs 'prompt' or 'turns'.")
            if not test.get("checks") and not test.get("semantic_dimensions"):
                raise BenchmarkError(f"Test {test_id} has no evaluation criteria.")


def weighted_mean(items: Iterable[Tuple[float, float]]) -> float:
    pairs = [(value, weight) for value, weight in items if weight > 0]
    if not pairs:
        return 0.0
    total_weight = sum(weight for _, weight in pairs)
    return sum(value * weight for value, weight in pairs) / total_weight


def prompt_preview(test: Dict[str, Any], max_len: int = 72) -> str:
    if "prompt" in test:
        text = str(test["prompt"])
    else:
        turns = test.get("turns", [])
        last = turns[-1] if turns else ""
        text = last.get("user", "") if isinstance(last, dict) else str(last)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def case_text(test: Dict[str, Any]) -> str:
    if "prompt" in test:
        return str(test["prompt"])
    turns = test.get("turns", [])
    rendered = []
    for index, turn in enumerate(turns, start=1):
        user = turn.get("user", "") if isinstance(turn, dict) else str(turn)
        rendered.append(f"Turn {index} user: {user}")
    return "\n".join(rendered)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hybrid deterministic + LLM-judge benchmark for Xavion."
    )
    parser.add_argument("--suite", default=None, help="Path to benchmark JSON suite.")
    parser.add_argument(
        "--model",
        default=None,
        help="Xavion model under test. Defaults to the configured model.",
    )
    parser.add_argument(
        "--judge-model",
        default=os.getenv("XAVION_JUDGE_MODEL"),
        help="Ollama model used as semantic judge. Defaults to the model under test.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="Runs per test. Overrides suite scoring.default_runs.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=[],
        help="Only run test IDs or category-name fragments containing these values.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Output JSON report path. Defaults to benchmark_reports/<timestamp>.json.",
    )
    parser.add_argument(
        "--no-report", action="store_true", help="Do not write the JSON report."
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="Stop after the first unstable failing test."
    )
    return parser


def should_run(category: str, test_id: str, filters: Sequence[str]) -> bool:
    if not filters:
        return True
    category_cf = category.casefold()
    test_cf = test_id.casefold()
    return any(item.casefold() in category_cf or item.casefold() in test_cf for item in filters)


def main() -> int:
    args = build_parser().parse_args()
    model_name = resolve_model_name(model_name)

    if model_name is None:
        console.print(
            "[bold red]Error:[/] No model was specified and no default model is configured."
        )
        return 2

    judge_model = judge_model or model_name
    script_dir = Path(__file__).resolve().parent
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = script_dir / DEFAULT_LOG_DIR / f"xavion_stress_{run_stamp}.txt"
    suite_path = Path(args.suite) if args.suite else script_dir / DEFAULT_SUITE

    if not suite_path.exists():
        console.print(f"[bold red]Error:[/] Suite not found: {suite_path}")
        return 2

    try:
        suite = json.loads(suite_path.read_text(encoding="utf-8"))
        validate_suite(suite)
    except (OSError, json.JSONDecodeError, BenchmarkError) as exc:
        console.print(f"[bold red]Invalid suite:[/] {exc}")
        return 2

    if not start_ollama():
        console.print("[bold red]Critical:[/] Ollama is required but not running.")
        return 2

    scoring = suite.get("scoring", {})
    runs_per_test = args.runs or int(scoring.get("default_runs", 1))
    pass_threshold = float(scoring.get("test_pass_threshold", DEFAULT_PASS_THRESHOLD))
    stable_pass_rate = float(scoring.get("stable_pass_rate", 1.0))
    if runs_per_test < 1:
        console.print("[bold red]Error:[/] --runs must be at least 1.")
        return 2

    evaluator = XavionEvaluator(model_name, judge_model)

    console.print(
        Panel.fit(
            f"[bold white]{suite.get('benchmark_suite', 'Xavion Benchmark')}[/]\n"
            f"[grey70]{suite.get('description', '')}[/]\n\n"
            f"Model: [cyan]{model_name}[/]  Judge: [magenta]{judge_model}[/]  "
            f"Runs/test: [yellow]{runs_per_test}[/]",
            title="XAVION AI STRESS TEST",
            border_style="cyan",
        )
    )

    if model_name == judge_model:
        console.print(
            "[yellow]Warning:[/] the model under test is also the semantic judge. "
            "Deterministic checks remain independent, but semantic scores may be biased. "
            "Use --judge-model with a stronger/different model for release comparisons.\n"
        )

    results: List[TestResult] = []
    abort = False

    for category in suite["categories"]:
        section = str(category["section"])
        selected = [
            test
            for test in category["tests"]
            if should_run(section, str(test["id"]), args.only)
        ]
        if not selected:
            continue

        console.print(f"\n[bold cyan]SECTION: {section}[/]")

        for test in selected:
            test_id = str(test["id"])
            test_weight = float(test.get("weight", 1.0))
            test_threshold = float(test.get("pass_threshold", pass_threshold))
            run_results: List[RunResult] = []

            with Progress(
                SpinnerColumn(),
                TextColumn(f"[white]{test_id}[/] {prompt_preview(test)}"),
                TimeElapsedColumn(),
                transient=True,
                console=console,
            ) as progress:
                task = progress.add_task("run", total=runs_per_test)
                for _ in range(runs_per_test):
                    response, latency, _conversation = evaluator.run_case(test)
                    deterministic = evaluator.deterministic_checks(
                        response, test.get("checks", [])
                    )
                    semantic, judge_reason = evaluator.semantic_checks(
                        case_text(test),
                        response,
                        test.get("semantic_dimensions", []),
                    )
                    checks = deterministic + semantic
                    score, passed = evaluator.combine_checks(checks, test_threshold)
                    error = response[7:] if response.startswith("ERROR: ") else None
                    if error:
                        score = 0.0
                        passed = False
                    run_results.append(
                        RunResult(
                            score=score,
                            passed=passed,
                            latency_seconds=latency,
                            response=response,
                            checks=checks,
                            judge_reason=judge_reason,
                            error=error,
                        )
                    )
                    progress.advance(task)

            scores = [run.score for run in run_results]
            passes = [run.passed for run in run_results]
            mean_score = statistics.mean(scores)
            stddev = statistics.pstdev(scores) if len(scores) > 1 else 0.0
            pass_rate = sum(1 for passed in passes if passed) / len(passes)
            stable_pass = mean_score >= test_threshold and pass_rate >= stable_pass_rate

            results.append(
                TestResult(
                    test_id=test_id,
                    category=section,
                    prompt_preview=prompt_preview(test),
                    weight=test_weight,
                    runs=run_results,
                    mean_score=mean_score,
                    score_stddev=stddev,
                    pass_rate=pass_rate,
                    stable_pass=stable_pass,
                )
            )

            status = "[bold green]PASS[/]" if stable_pass else "[bold red]FAIL[/]"
            latency_mean = statistics.mean(run.latency_seconds for run in run_results)
            console.print(
                f"  {status} [bold]{test_id}[/]  "
                f"score={mean_score:5.1f}  pass={pass_rate * 100:5.1f}%  "
                f"σ={stddev:4.1f}  latency={latency_mean:5.2f}s"
            )

            if not stable_pass:
                worst = min(run_results, key=lambda run: run.score)
                failures = [
                    check
                    for check in worst.checks
                    if not check.passed or check.score < 75
                ]
                for check in failures[:3]:
                    console.print(
                        f"       [yellow]{check.name}:[/] {check.reason} "
                        f"({check.score:.0f}/100)"
                    )
                if worst.judge_reason:
                    console.print(f"       [grey70]Judge:[/] {worst.judge_reason}")

                if args.fail_fast:
                    abort = True
                    break

        if abort:
            break

    if not results:
        console.print("[yellow]No tests matched the requested filters.[/]")
        return 1

    category_weights = {
        str(category["section"]): float(category.get("weight", 1.0))
        for category in suite["categories"]
    }

    category_scores: Dict[str, float] = {}
    category_pass_rates: Dict[str, float] = {}
    for category_name in sorted({result.category for result in results}):
        subset = [result for result in results if result.category == category_name]
        category_scores[category_name] = weighted_mean(
            (result.mean_score, result.weight) for result in subset
        )
        category_pass_rates[category_name] = weighted_mean(
            (100.0 if result.stable_pass else 0.0, result.weight) for result in subset
        )

    total_score = weighted_mean(
        (score, category_weights.get(category, 1.0))
        for category, score in category_scores.items()
    )
    total_pass_rate = weighted_mean(
        (rate, category_weights.get(category, 1.0))
        for category, rate in category_pass_rates.items()
    )

    table = Table(title="Final Performance Summary", header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Stable Pass", justify="right")
    for category_name in category_scores:
        table.add_row(
            category_name,
            f"{category_scores[category_name]:.1f}",
            f"{category_pass_rates[category_name]:.1f}%",
        )
    table.add_section()
    table.add_row(
        "[bold white]TOTAL[/]",
        f"[bold yellow]{total_score:.1f}[/]",
        f"[bold yellow]{total_pass_rate:.1f}%[/]",
    )
    console.print("\n")
    console.print(table)

    all_latencies = [run.latency_seconds for result in results for run in result.runs]
    console.print(
        f"\nMedian latency: [cyan]{statistics.median(all_latencies):.2f}s[/]  "
        f"Mean latency: [cyan]{statistics.mean(all_latencies):.2f}s[/]  "
        f"Tests: [cyan]{len(results)}[/]"
    )

    report_path: Optional[Path] = None
    if not args.no_report:
        if args.report:
            report_path = Path(args.report)
        else:
            report_path = (
                script_dir
                / DEFAULT_REPORT_DIR
                / f"xavion_stress_{run_stamp}.json"
            )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "benchmark_suite": suite.get("benchmark_suite"),
            "suite_version": suite.get("version"),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "model": model_name,
            "judge_model": judge_model,
            "runs_per_test": runs_per_test,
            "test_pass_threshold": pass_threshold,
            "stable_pass_rate_required": stable_pass_rate,
            "total_score": total_score,
            "total_stable_pass_rate": total_pass_rate,
            "category_scores": category_scores,
            "category_stable_pass_rates": category_pass_rates,
            "tests": [asdict(result) for result in results],
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    release_threshold = float(scoring.get("release_score_threshold", 80.0))
    passed_release_threshold = total_score >= release_threshold

    if passed_release_threshold:
        console.print(
            Panel(
                "Benchmark score is above the configured release threshold. "
                "Compare the JSON report against the Spark baseline before accepting Ember changes.",
                title="Benchmark Result",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "Benchmark score is below the configured release threshold. "
                "Use the per-check failures and saved responses to identify regressions.",
                title="Benchmark Result",
                border_style="yellow",
            )
        )

    console.print()
    if report_path is not None:
        console.print(f"JSON report: [green]{report_path}[/]")
    else:
        console.print("JSON report: [grey70]disabled (--no-report)[/]")
    console.print(f"Text log:    [green]{log_path}[/]")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(console.export_text(styles=False), encoding="utf-8")

    return 0 if passed_release_threshold else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Benchmark interrupted.[/]")
        raise SystemExit(130)
