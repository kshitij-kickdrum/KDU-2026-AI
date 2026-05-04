from __future__ import annotations

import json

from openai import OpenAI

from src.models.file_models import SummaryResponse, TokenUsage
from src.services.openai_utils import call_openai_with_retry


class SummaryGenerator:
    def __init__(
        self,
        client: OpenAI,
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        base_delay: int = 2,
    ) -> None:
        self.client = client
        self.model = model
        self.max_retries = max_retries
        self.base_delay = base_delay

    def generate_summary(self, text: str) -> SummaryResponse:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Input text is empty")
        if len(cleaned_text) > 100_000:
            raise ValueError("Input text exceeds 100,000 characters")

        def _call() -> object:
            return self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate: 1) A 150-word summary, 2) 5-7 key points as bullets, "
                            "3) 3-5 topic tags. Format as JSON with keys: summary, key_points, topic_tags."
                        ),
                    },
                    {"role": "user", "content": cleaned_text},
                ],
                max_tokens=1024,
                temperature=0.3,
            )

        response = call_openai_with_retry(
            _call, max_retries=self.max_retries, base_delay=self.base_delay
        )
        usage = getattr(response, "usage", None)
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        key_points = parsed.get("key_points", [])
        topic_tags = parsed.get("topic_tags", [])
        if not isinstance(key_points, list) or not isinstance(topic_tags, list):
            raise ValueError("Malformed JSON response from summary model")

        return SummaryResponse(
            summary=str(parsed.get("summary", "")).strip(),
            key_points=[str(item).strip() for item in key_points if str(item).strip()],
            topic_tags=[str(item).strip() for item in topic_tags if str(item).strip()],
            tokens_used=TokenUsage(
                input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            ),
            cost_usd=0.0,
        )
