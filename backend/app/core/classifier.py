from __future__ import annotations

from dataclasses import dataclass

from app.core.llm_client import LLMClient
from app.core.prompt_manager import PromptManager
from app.models.config import Category, Complexity, FeatureFlags


@dataclass(slots=True)
class ClassificationResult:
    category: Category
    complexity: Complexity
    confidence: float
    method: str


class HybridClassifier:
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_manager: PromptManager,
        features: FeatureFlags,
        llm_fallback_model: str = "gemini-flash-lite",
    ) -> None:
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.features = features
        self.llm_fallback_model = llm_fallback_model

    def _rule_based(self, query: str) -> ClassificationResult:
        text = query.lower()
        complaint_keywords = ["angry", "refund", "broken", "bad", "complaint"]
        booking_keywords = ["book", "appointment", "schedule", "reschedule", "slot"]
        urgency_keywords = ["urgent", "immediately", "asap", "critical"]

        complaint_score = sum(1 for k in complaint_keywords if k in text)
        booking_score = sum(1 for k in booking_keywords if k in text)

        if complaint_score > booking_score:
            category: Category = "complaint"
            score = complaint_score
        elif booking_score > complaint_score:
            category = "booking"
            score = booking_score
        else:
            category = "faq"
            score = 1

        if any(k in text for k in urgency_keywords) or len(text.split()) > 120:
            complexity: Complexity = "high"
        elif len(text.split()) > 35:
            complexity = "medium"
        else:
            complexity = "low"

        confidence = min(0.95, 0.4 + 0.15 * score)
        return ClassificationResult(
            category=category,
            complexity=complexity,
            confidence=confidence,
            method="rule_based",
        )

    async def classify(self, query: str) -> ClassificationResult:
        rule = self._rule_based(query)
        if rule.confidence >= 0.70 or not self.features.enable_llm_classification_fallback:
            return rule

        prompt, _ = self.prompt_manager.render("classifier", query)
        llm_result = await self.llm_client.classify_with_gemini(
            model_key=self.llm_fallback_model, prompt=prompt, query=query
        )
        category = llm_result.get("category", "faq")
        complexity = llm_result.get("complexity", "medium")
        if category not in {"faq", "complaint", "booking"}:
            category = "faq"
        if complexity not in {"low", "medium", "high"}:
            complexity = "medium"
        return ClassificationResult(
            category=category,  # type: ignore[arg-type]
            complexity=complexity,  # type: ignore[arg-type]
            confidence=0.69,
            method="llm_fallback",
        )
