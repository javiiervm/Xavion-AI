import re
from typing import Any, Callable, List, Optional, Tuple

from xavion.core.constants import (
    CODE_PATTERNS,
    COUNTING_KEYWORDS,
    MATH_PATTERNS,
    TRANSLATE_PATTERNS,
)


class IntentDetector:
    """Detect user intent from input text."""

    def __init__(
        self, debug_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.debug_callback = debug_callback

    def _log(self, message: str, icon: str = "🔍"):
        if self.debug_callback:
            self.debug_callback(message, icon)

    def detect_math_expressions(self, text: str) -> List[str]:
        text = text.lower().strip()
        found = []

        self._log("Scanning for math expressions...", icon="🔎")

        for pattern in MATH_PATTERNS:
            for match in re.finditer(pattern, text):
                expression = match.group(1).strip()
                if re.search(r"[+\-*/^%]", expression) or re.search(
                    r"\b(sqrt|log|ln|sin|cos|tan|pi|e)\b", expression
                ):
                    found.append(expression)

        if not found and re.search(r"\d+", text) and any(
            re.search(keyword, text) for keyword in COUNTING_KEYWORDS
        ):
            self._log("Detected counting-style math problem.", icon="✅")
            found.append(text)

        return found

    def get_intent(self, text: str) -> Tuple[str, Optional[Any]]:
        text_lower = text.lower()

        math_expressions = self.detect_math_expressions(text)
        if math_expressions:
            self._log(f"Math intent detected: {math_expressions}", icon="✅")
            return "math", math_expressions

        for pattern in CODE_PATTERNS:
            if re.search(pattern, text_lower):
                self._log(f"Code intent detected (pattern: {pattern})", icon="✅")
                return "code", None

        for pattern in TRANSLATE_PATTERNS:
            if re.search(pattern, text_lower):
                self._log(
                    f"Translate intent detected (pattern: {pattern})", icon="✅"
                )
                return "translate", None

        self._log("Default conversation intent.", icon="✅")
        return "default", None
