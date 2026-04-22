import time
from typing import Any

import sympy as sp

from app.database.models import ToolResult
from app.tools.base import BaseTool


class CalculatorTool(BaseTool):
    name = "calculate"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "Perform mathematical calculations and symbolic math",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate",
                        }
                    },
                    "required": ["expression"],
                },
            },
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        started = time.perf_counter()
        expression = str(kwargs.get("expression", "")).strip()
        if not expression:
            return ToolResult(success=False, data=None, error_message="expression is required")
        try:
            parsed = sp.sympify(expression)
            result = parsed.evalf(12)
            return ToolResult(
                success=True,
                data={
                    "expression": expression,
                    "result": str(result),
                    "float": float(result) if result.is_real else None,
                },
                execution_time=time.perf_counter() - started,
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                data=None,
                error_message=f"Calculation error: {exc}",
                execution_time=time.perf_counter() - started,
            )

