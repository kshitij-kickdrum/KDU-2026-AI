from __future__ import annotations

from typing import Any

from src.agents.sdk import load_agents_sdk
from src.tools.runtime import ToolRuntime

PTO_BALANCES = {"john": "15 PTO days", "jane": "18 PTO days"}


def create_hr_tools(runtime: ToolRuntime, session_id: str) -> list[Any]:
    _, _, function_tool, _ = load_agents_sdk()

    @function_tool
    def query_pto_balance(employee_name: str) -> str:
        """Return PTO balance for an employee by name."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="HRAgent",
            tool_name="query_pto_balance",
            parameters={"employee_name": employee_name},
            handler=lambda: PTO_BALANCES.get(employee_name.lower(), "PTO record not found."),
        )

    @function_tool
    def request_leave(employee_name: str, start_date: str, end_date: str) -> str:
        """Submit a leave request for an employee."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="HRAgent",
            tool_name="request_leave",
            parameters={"employee_name": employee_name, "start_date": start_date, "end_date": end_date},
            handler=lambda: f"Leave request submitted for {employee_name}: {start_date} to {end_date}.",
        )

    @function_tool
    def get_benefits_info(employee_name: str) -> str:
        """Return benefits information for an employee."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="HRAgent",
            tool_name="get_benefits_info",
            parameters={"employee_name": employee_name},
            handler=lambda: f"{employee_name} is enrolled in standard health and retirement benefits.",
        )

    @function_tool
    def query_employee_info(employee_name: str) -> str:
        """Return employee personnel information."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="HRAgent",
            tool_name="query_employee_info",
            parameters={"employee_name": employee_name},
            handler=lambda: f"{employee_name} is an active employee.",
        )

    @function_tool
    def update_employee_record(employee_name: str, field_name: str, field_value: str) -> str:
        """Update a field in an employee personnel record."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="HRAgent",
            tool_name="update_employee_record",
            parameters={"employee_name": employee_name, "field_name": field_name},
            handler=lambda: f"Updated {field_name} for {employee_name} to {field_value}.",
        )

    @function_tool
    def get_org_chart(employee_name: str) -> str:
        """Return org chart relationship for an employee."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="HRAgent",
            tool_name="get_org_chart",
            parameters={"employee_name": employee_name},
            handler=lambda: f"{employee_name} reports to the Operations Director.",
        )

    return [
        query_pto_balance,
        request_leave,
        get_benefits_info,
        query_employee_info,
        update_employee_record,
        get_org_chart,
    ]
