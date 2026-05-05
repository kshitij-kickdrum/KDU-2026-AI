from __future__ import annotations

import json
from typing import Any


class TokenCounter:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self.encoding: Any | None = None
        try:
            import tiktoken

            try:
                self.encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            pass

    def count_text(self, text: str) -> int:
        if self.encoding is not None:
            return len(self.encoding.encode(text))
        return max(1, len(text) // 4)

    def count_payload(self, payload: Any) -> int:
        if isinstance(payload, str):
            return self.count_text(payload)
        return self.count_text(json.dumps(payload, ensure_ascii=False, default=str))

    @staticmethod
    def count_words(text: str) -> int:
        return len([word for word in text.split() if word.strip()])
