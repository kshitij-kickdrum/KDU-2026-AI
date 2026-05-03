"""SQLite-backed execution history viewer."""

from __future__ import annotations

from typing import Any

from src.memory.manager import MemoryManager

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None  # type: ignore[assignment]


def truncate_execution_id(execution_id: str) -> str:
    """Return a short display version of an execution id."""
    return execution_id[:8]


def load_execution_history(memory_manager: MemoryManager) -> list[dict[str, Any]]:
    """Load execution history rows in newest-first order."""
    rows = memory_manager.connection.execute(
        """
        SELECT execution_id, orchestration_mode, final_status,
               total_duration_sec, cost_estimate_usd, created_at
        FROM execution_history
        ORDER BY created_at DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def load_execution_memory(
    memory_manager: MemoryManager, execution_id: str
) -> list[dict[str, Any]]:
    """Load all memory rows for one execution id."""
    rows = memory_manager.connection.execute(
        """
        SELECT agent_role, task_id, memory_type, content, created_at
        FROM agent_memory
        WHERE execution_id = ?
        ORDER BY id
        """,
        (execution_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def render_history(memory_manager: MemoryManager) -> None:
    """Render execution history and selected memory details."""
    if st is None:
        return
    st.subheader("History")
    history = load_execution_history(memory_manager)
    if not history:
        st.info("No executions recorded yet.")
        return

    display_rows = [
        {**row, "execution_id": truncate_execution_id(str(row["execution_id"]))}
        for row in history
    ]
    st.dataframe(display_rows, hide_index=True, use_container_width=True)
    selected = st.selectbox(
        "Inspect execution",
        [str(row["execution_id"]) for row in history],
        format_func=lambda value: truncate_execution_id(str(value)),
    )
    with st.expander("Agent memory entries"):
        st.dataframe(
            load_execution_memory(memory_manager, selected),
            hide_index=True,
            use_container_width=True,
        )
