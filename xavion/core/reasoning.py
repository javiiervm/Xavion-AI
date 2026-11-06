"""Fast, frontend-independent reasoning decisions for Xavion.

Auto mode uses only deterministic local signals. It does not make a second
LLM request, so the routing decision adds negligible latency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Sequence

REASONING_MODES = ("off", "on", "auto")


@dataclass(frozen=True)
class ReasoningDecision:
    """Effective reasoning decision for a single user request."""

    mode: str
    enabled: bool
    supported: bool
    reason: str
    score: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "enabled": self.enabled,
            "supported": self.supported,
            "reason": self.reason,
            "score": self.score,
        }


# These patterns are not the entire policy: message structure, task length,
# prior conversation, and intent also influence the final score.
_COMPLEX_ACTION = re.compile(
    r"\b(?:analys[ei]|analyz[ei]|analyzing|analiza|analizar|analice|"
    r"reason|razona|razonar|deduc[ei]|deducir|deriv[ea]|derivar|"
    r"demuestra|demostrar|prove|proof|prueba|justifica|justificar|"
    r"evaluate|evaluat[ei]|evaluar|compara|comparar|compare|"
    r"diagnos[ei]|diagnostica|diagnosticar|troubleshoot|"
    r"debug|depura|depurar|optimiz[ea]|optimiza|optimizar|"
    r"refactor|refactoriza|refactorizar|design|diseña|diseñar|"
    r"explain in detail|explica en detalle|planifica|planificar|"
    r"evaluate tradeoffs|evalúa alternativas|review|revisa|revisar|"
    r"fix|corrige|corregir|soluciona|solucionar|solve|"
    r"implement|implementa|implementar|implementing)\b",
    re.IGNORECASE,
)

_TECHNICAL_PROBLEM = re.compile(
    r"\b(?:algorithm|algoritmo|architecture|arquitectura|"
    r"concurren\w*|thread\w*|hilo[s]?|race condition|"
    r"deadlocks?|bloqueo mutuo|security|seguridad|vulnerab\w*|"
    r"complexity|complejidad|performance|rendimiento|"
    r"scalab\w*|escalab\w*|recursi\w*|"
    r"repository|repo\b|repositorio|codebase|source code|c[oó]digo fuente|"
    r"code|c[oó]digo|dotfiles|implementaci[oó]n|implementation|"
    r"logic|l[oó]gica|formal proof|demostraci[oó]n|"
    r"invariant|invariante|equation|ecuaci[oó]n|"
    r"probabilit\w*|probabilidad|optimization|optimizaci[oó]n)\b",
    re.IGNORECASE,
)

_ERROR_INVESTIGATION = re.compile(
    r"\b(?:traceback|stack trace|exception|segmentation fault|"
    r"error de (?:ejecuci[oó]n|compilaci[oó]n)|"
    r"doesn.t work|does not work|no funciona|"
    r"find (?:the |a )?bug|encuentra (?:el |un )?(?:fallo|error|bug)|"
    r"por qu[eé] falla|why (?:does|is|doesn.t) .* (?:fail|crash)|"
    r"fix (?:this|the) (?:bug|code|error)|"
    r"corrige (?:este|el) (?:c[oó]digo|error|fallo))\b",
    re.IGNORECASE,
)

_MULTI_STEP = re.compile(
    r"\b(?:step.by.step|paso a paso|"
    r"multiple steps|varios pasos|"
    r"first.+then|primero.+despu[eé]s|"
    r"trade.?offs?|ventajas y desventajas|"
    r"restrictions?|restricciones|constraints?|"
    r"edge cases?|casos l[ií]mite|"
    r"all possible|todos los casos|"
    r"without breaking|sin romper|"
    r"deduce|deduce|demuestre|demuestra)\b",
    re.IGNORECASE | re.DOTALL,
)

_SIMPLE_REQUEST = re.compile(
    r"^\s*(?:(?:hi|hello|hey|hola|buenas|buenos d[ií]as|"
    r"good morning|good night|gracias|thanks|thank you|"
    r"vale|ok|okay|perfecto|adi[oó]s|bye)[!?.\s]*)$",
    re.IGNORECASE,
)

_SIMPLE_FACT = re.compile(
    r"^\s*(?:what is|what.s|who is|who was|when was|where is|"
    r"cu[aá]l es|qui[eé]n es|qui[eé]n fue|cu[aá]ndo fue|"
    r"d[oó]nde est[aá])\b",
    re.IGNORECASE,
)

_TRANSLATION = re.compile(
    r"^\s*(?:translate|traduce|traducir|traducci[oó]n)\b",
    re.IGNORECASE,
)

_FOLLOWUP = re.compile(
    r"^\s*(?:why\b|how so\b|explain (?:that|why)\b|"
    r"por qu[eé]\b|expl[ií]calo\b|y si\b|what if\b|"
    r"and if\b|entonces\b)",
    re.IGNORECASE,
)

_TRIVIAL_ARITHMETIC = re.compile(
    r"^\s*(?:(?:what is|calculate|compute|solve|cu[aá]nto es|"
    r"calcula|resuelve)\s+)?[+-]?\d+(?:[.,]\d+)?"
    r"(?:\s*[-+*/x×÷^]\s*[+-]?\d+(?:[.,]\d+)?){1,3}\s*[?!.]?\s*$",
    re.IGNORECASE,
)

_MATH_STEPS = re.compile(
    r"\b(?:solve|resolver|resuelve|integral|derivative|derivada|"
    r"system of equations|sistema de ecuaciones|"
    r"limit of|l[ií]mite de|probability distribution|"
    r"distribuci[oó]n de probabilidad|induction|inducci[oó]n)\b",
    re.IGNORECASE,
)


def decide_reasoning(
    message: str,
    *,
    mode: str,
    supported: bool,
    intent: str = "default",
    history: Sequence[dict[str, Any]] = (),
    has_images: bool = False,
) -> ReasoningDecision:
    """Choose whether to enable thinking for exactly one request.

    This is a conservative heuristic, not a learned complexity classifier.
    High-stakes or difficult queries can still be misclassified; manual On
    remains available for those cases.
    """
    if mode not in REASONING_MODES:
        raise ValueError(f"Invalid reasoning mode: {mode!r}. Use off, on, or auto.")

    if not supported:
        return ReasoningDecision(mode, False, False, "model_not_supported")
    if mode == "on":
        return ReasoningDecision(mode, True, True, "manual_on")
    if mode == "off":
        return ReasoningDecision(mode, False, True, "manual_off")

    text = message.strip()
    if not text and not has_images:
        return ReasoningDecision(mode, False, True, "empty_request")
    if _SIMPLE_REQUEST.fullmatch(text) and not has_images:
        return ReasoningDecision(mode, False, True, "simple_conversation")
    if _TRIVIAL_ARITHMETIC.fullmatch(text) and not has_images:
        return ReasoningDecision(mode, False, True, "trivial_arithmetic")

    words = re.findall(r"\b[\wáéíóúüñÁÉÍÓÚÜÑ]+\b", text, re.UNICODE)
    word_count = len(words)
    lines = text.splitlines()
    score = 0

    # Task semantics: resolving a difficult task is not the same as simply
    # mentioning a technical subject in a definition or explanation.
    action = bool(_COMPLEX_ACTION.search(text))
    technical = bool(_TECHNICAL_PROBLEM.search(text))
    investigation = bool(_ERROR_INVESTIGATION.search(text))
    multi_step = bool(_MULTI_STEP.search(text))
    math_steps = bool(_MATH_STEPS.search(text))

    if action:
        score += 2
    if technical:
        score += 1
    if action and technical:
        score += 1
    if investigation:
        score += 3
    if multi_step:
        score += 2
    if math_steps:
        score += 3

    # Multiple constraints, substantial input, and real source code increase
    # the odds that careful multi-step reasoning is useful.
    if word_count >= 130:
        score += 2
    elif word_count >= 65:
        score += 1
    if len(lines) >= 12:
        score += 2
    elif len(lines) >= 6:
        score += 1
    if "```" in text:
        score += 2
    if len(re.findall(r"(?:^|\n)\s*(?:[-*]|\d+[.)])\s+", text)) >= 3:
        score += 2
    if sum(bool(re.search(r"\b(?:must|should|avoid|without|"
                          r"debe|deber[ií]a|evita|sin|mant[eé]n)\b", line, re.I))
           for line in lines) >= 2:
        score += 1
    if has_images and (action or investigation or technical):
        score += 1
    if intent == "math" and not math_steps:
        # IntentDetector also identifies trivial arithmetic. Do not require
        # slow reasoning for a straightforward calculation.
        if word_count >= 14 or action:
            score += 1
    if intent == "code" and (investigation or action or word_count >= 45):
        score += 1
    if history and _FOLLOWUP.search(text) and word_count < 25:
        last_question = str(history[-1].get("user", ""))
        if (_COMPLEX_ACTION.search(last_question)
                or _TECHNICAL_PROBLEM.search(last_question)
                or _MATH_STEPS.search(last_question)):
            score += 2

    # Inquiries such as 'what is an algorithm?' and straightforward
    # translations should default to a fast response.
    if _SIMPLE_FACT.search(text) and word_count <= 16 and not (investigation or multi_step):
        score = min(score, 2)
    if (intent == "translate" or _TRANSLATION.search(text)) and not (
        multi_step or investigation or word_count >= 100
    ):
        score = min(score, 2)

    enabled = score >= 3
    return ReasoningDecision(
        mode=mode,
        enabled=enabled,
        supported=True,
        reason="complex_request" if enabled else "direct_response",
        score=score,
    )
