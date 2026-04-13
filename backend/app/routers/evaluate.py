"""POST /api/v1/evaluate Endpoint - Run evaluation suite"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()


class EvaluationResponse(BaseModel):
    status: str
    total_metrics: int
    passed_metrics: int
    pass_rate: float
    results: list[dict]
    token_summary: dict | None = None
    logging_summary: dict | None = None


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    responses={503: {"description": "Evaluation dependencies are unavailable."}},
)
async def trigger_evaluation():
    """
    Run the full evaluation suite against the agent.
    Executes all test cases, scores them, and returns results.
    All runs are traced in LangSmith automatically.
    """
    try:
        from app.evaluation.evaluator import run_evaluation
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Evaluation dependencies are unavailable in this environment.",
        ) from exc

    evaluation_payload = run_evaluation()
    results = evaluation_payload["results"]

    total_metrics = sum(len(r["metrics"]) for r in results)
    passed_metrics = sum(
        sum(1 for m in r["metrics"] if m["score"] == 1)
        for r in results
    )

    # Simplify results for JSON response
    simplified = [
        {
            "name": r["name"],
            "thread_id": r["thread_id"],
            "interrupted": r["interrupted"],
            "metrics": r["metrics"],
        }
        for r in results
    ]

    return EvaluationResponse(
        status="completed",
        total_metrics=total_metrics,
        passed_metrics=passed_metrics,
        pass_rate=round(passed_metrics / total_metrics * 100, 1) if total_metrics > 0 else 0.0,
        results=simplified,
        token_summary=evaluation_payload.get("token_summary"),
        logging_summary=evaluation_payload.get("logging_summary"),
    )
