from __future__ import annotations

import re
from dataclasses import dataclass

WORD_RE = re.compile(r"\w+", re.UNICODE)


@dataclass
class TokenCounter:
    """A lightweight token counter.

    This approximates token count by counting words. It is deterministic and fast,
    and suitable for boundary checks used by the fallback chain.
    """

    max_tokens: int = 512

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(WORD_RE.findall(text))

    def count_question_and_context(self, question: str, context: str) -> int:
        return self.count_tokens(question) + self.count_tokens(context)

    def exceeds_limit(self, text: str, limit: int | None = None) -> bool:
        effective_limit = self.max_tokens if limit is None else limit
        return self.count_tokens(text) > effective_limit

    def exceeds_combined_limit(self, question: str, context: str, limit: int | None = None) -> bool:
        effective_limit = self.max_tokens if limit is None else limit
        return self.count_question_and_context(question, context) > effective_limit
