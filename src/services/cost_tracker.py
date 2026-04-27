from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from src.models.file_models import CostLogResponse, CostRecord, CostSummary
from src.storage.database import Database


class CostTracker:
    PRICING = {
        "gpt-4o-mini": {"input": 0.150 / 1_000_000, "output": 0.600 / 1_000_000},
        "text-embedding-3-small": {"input": 0.020 / 1_000_000, "output": 0.0},
    }

    def __init__(self, db: Database) -> None:
        self.db = db

    def calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        if model_name not in self.PRICING:
            raise ValueError(f"Unknown model for pricing: {model_name}")
        rates = self.PRICING[model_name]
        return round((input_tokens * rates["input"]) + (output_tokens * rates["output"]), 8)

    def log_api_call(
        self,
        operation_type: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        file_id: str | None = None,
        metadata: dict | None = None,
    ) -> CostLogResponse:
        total_tokens = input_tokens + output_tokens
        cost = self.calculate_cost(model_name, input_tokens, output_tokens)
        record = CostRecord(
            cost_id=str(uuid4()),
            file_id=file_id,
            operation_type=operation_type,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=json.dumps(metadata) if metadata else None,
        )
        self.db.insert_cost(record)
        return CostLogResponse(cost_id=record.cost_id, cost_usd=cost, total_tokens=total_tokens)

    def get_cost_summary(self, file_id: str | None = None) -> CostSummary:
        raw = self.db.get_cost_breakdown(file_id=file_id)
        return CostSummary(
            total_cost_usd=raw["total_cost_usd"],
            total_tokens=raw["total_tokens"],
            by_operation=raw["by_operation"],
            rows=raw["rows"],
        )
