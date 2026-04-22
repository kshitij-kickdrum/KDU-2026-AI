import json
from dataclasses import dataclass

from app.database.connection import pool


MODEL_PRICING_PER_1M = {
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "o4-mini": {"input": 1.10, "output": 4.40},
}


@dataclass(slots=True)
class UsageRecord:
    session_id: str
    request_type: str
    input_tokens: int
    output_tokens: int
    tool_tokens: int
    provider: str
    model: str
    tools_used: list[str]
    success: bool = True
    error_message: str | None = None


class UsageTracker:
    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = MODEL_PRICING_PER_1M.get(model, MODEL_PRICING_PER_1M["gpt-4o-mini"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 8)

    def ensure_session(self, session_id: str) -> None:
        conn = pool.acquire()
        try:
            conn.execute(
                """
                INSERT INTO sessions (session_id) VALUES (?)
                ON CONFLICT(session_id) DO UPDATE SET last_activity = CURRENT_TIMESTAMP
                """,
                (session_id,),
            )
            conn.commit()
        finally:
            pool.release(conn)

    def log_tool_usage(
        self,
        session_id: str,
        tool_name: str,
        execution_time: float,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        conn = pool.acquire()
        try:
            conn.execute(
                """
                INSERT INTO tool_usage (session_id, tool_name, execution_time, success, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, tool_name, execution_time, success, error_message),
            )
            conn.commit()
        finally:
            pool.release(conn)

    def log_usage(self, record: UsageRecord) -> dict[str, int | float]:
        self.ensure_session(record.session_id)
        total_tokens = record.input_tokens + record.output_tokens + record.tool_tokens
        cost = self.estimate_cost(record.model, record.input_tokens, record.output_tokens)

        conn = pool.acquire()
        try:
            conn.execute(
                """
                INSERT INTO usage_logs
                (session_id, request_type, input_tokens, output_tokens, tool_tokens, total_tokens,
                 estimated_cost, provider, model, tools_used, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.session_id,
                    record.request_type,
                    record.input_tokens,
                    record.output_tokens,
                    record.tool_tokens,
                    total_tokens,
                    cost,
                    record.provider,
                    record.model,
                    json.dumps(record.tools_used),
                    record.success,
                    record.error_message,
                ),
            )
            conn.execute(
                """
                UPDATE sessions
                SET last_activity = CURRENT_TIMESTAMP,
                    total_requests = total_requests + 1,
                    total_tokens = total_tokens + ?,
                    total_cost = total_cost + ?
                WHERE session_id = ?
                """,
                (total_tokens, cost, record.session_id),
            )
            conn.commit()
        finally:
            pool.release(conn)
        return {
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "tool_tokens": record.tool_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": cost,
        }

    def get_session_stats(self, session_id: str, detailed: bool = False) -> dict:
        conn = pool.acquire()
        try:
            session = conn.execute(
                """
                SELECT session_id, total_requests, total_tokens, total_cost
                FROM sessions WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            if not session:
                return {}

            tools_rows = conn.execute(
                "SELECT DISTINCT tool_name FROM tool_usage WHERE session_id = ?",
                (session_id,),
            ).fetchall()
            tools_used = [row["tool_name"] for row in tools_rows]
            output = {
                "session_id": session["session_id"],
                "total_tokens": session["total_tokens"],
                "total_cost": round(session["total_cost"], 8),
                "requests_count": session["total_requests"],
                "tools_used": tools_used,
            }
            token_totals = conn.execute(
                """
                SELECT
                    COALESCE(SUM(input_tokens), 0) AS total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
                    COALESCE(SUM(tool_tokens), 0) AS total_tool_tokens
                FROM usage_logs
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            output["total_input_tokens"] = token_totals["total_input_tokens"]
            output["total_output_tokens"] = token_totals["total_output_tokens"]
            output["total_tool_tokens"] = token_totals["total_tool_tokens"]
            if detailed:
                rows = conn.execute(
                    """
                    SELECT timestamp, request_type, total_tokens, estimated_cost, provider, model, tools_used
                    FROM usage_logs
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT 100
                    """,
                    (session_id,),
                ).fetchall()
                output["detailed_breakdown"] = [dict(row) for row in rows]
            return output
        finally:
            pool.release(conn)
