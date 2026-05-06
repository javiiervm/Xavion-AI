import re
from typing import Tuple, List, Optional, Callable
from xavion.core.constants import MATH_PATTERNS, CODE_PATTERNS, COUNTING_KEYWORDS

class IntentDetector:
    """
    Handles detection of user intent based on input text.
    """
    def __init__(self, debug_callback: Optional[Callable[[str, str], None]] = None):
        self.debug_callback = debug_callback

    def _log(self, message: str, icon: str = "🔍"):
        if self.debug_callback:
            self.debug_callback(message, icon)

    def detect_math_expressions(self, text: str) -> List[str]:
        text = text.lower().strip()
        found = []

        self._log(f"Scanning for math expressions...", icon="🔎")

        for pattern in MATH_PATTERNS:
            for match in re.finditer(pattern, text):
                expression = match.group(1).strip()
                # Validate it's not just a plain word
                if re.search(r"[+\-*/^%]", expression) or re.search(r"\b(sqrt|log|ln|sin|cos|tan|pi|e)\b", expression):
                    found.append(expression)

        if not found:
            # Check for counting keywords
            if re.search(r"\d+", text) and any(re.search(kw, text) for kw in COUNTING_KEYWORDS):
                self._log("Detected counting-style math problem.", icon="✅")
                found.append(text)

        return found

    def get_intent(self, text: str) -> Tuple[str, Optional[Any]]:
        text_lower = text.lower()

        # 1. Math Intent
        math_expr = self.detect_math_expressions(text)
        if math_expr:
            self._log(f"Math intent detected: {math_expr}", icon="✅")
            return "math", math_expr

        # 2. Code Intent
        for pattern in CODE_PATTERNS:
            if re.search(pattern, text_lower):
                self._log(f"Code intent detected (pattern: {pattern})", icon="✅")
                return "code", None

        # 3. Default Intent
        self._log("Default conversation intent.", icon="✅")
        return "default", None
