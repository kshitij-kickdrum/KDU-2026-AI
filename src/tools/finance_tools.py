from __future__ import annotations

from typing import Any

from src.agents.sdk import load_agents_sdk
from src.tools.runtime import ToolRuntime

EMPLOYEE_SALARIES = {"john": "$85,000", "jane": "$92,000"}
ACCOUNT_BALANCES = {"john": "$12,500.00", "jane": "$8,250.00"}


def create_finance_tools(runtime: ToolRuntime, session_id: str) -> list[Any]:
    _, _, function_tool, _ = load_agents_sdk()

    @function_tool
    def query_employee_salary(employee_name: str) -> str:
        """Return salary information for an employee by name."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="FinanceAgent",
            tool_name="query_employee_salary",
            parameters={"employee_name": employee_name},
            handler=lambda: EMPLOYEE_SALARIES.get(employee_name.lower(), "Salary record not found."),
        )

    @function_tool
    def update_salary(employee_name: str, new_salary: str) -> str:
        """Update an employee salary value."""
        def handler() -> str:
            EMPLOYEE_SALARIES[employee_name.lower()] = new_salary
            return f"Updated salary for {employee_name} to {new_salary}."

        return runtime.invoke(
            session_id=session_id,
            agent_name="FinanceAgent",
            tool_name="update_salary",
            parameters={"employee_name": employee_name, "new_salary": new_salary},
            handler=handler,
        )

    @function_tool
    def get_payroll_info(employee_name: str) -> str:
        """Return payroll status for an employee."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="FinanceAgent",
            tool_name="get_payroll_info",
            parameters={"employee_name": employee_name},
            handler=lambda: f"{employee_name} is on the monthly payroll cycle.",
        )

    @function_tool
    def update_banking_details(
        employee_name: str,
        routing_number: str,
        account_number: str | None = None,
        account_holder_name: str | None = None,
    ) -> str:
        """Update employee banking details when required banking fields are present."""
        def handler() -> str:
            missing = [
                name
                for name, value in {
                    "account_number": account_number,
                    "account_holder_name": account_holder_name,
                }.items()
                if not value
            ]
            if missing:
                return f"Missing required banking fields: {', '.join(missing)}."
            return f"Banking details updated for {employee_name} using routing number {routing_number}."

        return runtime.invoke(
            session_id=session_id,
            agent_name="FinanceAgent",
            tool_name="update_banking_details",
            parameters={
                "employee_name": employee_name,
                "routing_number": routing_number,
                "account_number": "***" if account_number else None,
                "account_holder_name": account_holder_name,
            },
            handler=handler,
        )

    @function_tool
    def query_account_balance(employee_name: str) -> str:
        """Return account balance for an employee."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="FinanceAgent",
            tool_name="query_account_balance",
            parameters={"employee_name": employee_name},
            handler=lambda: ACCOUNT_BALANCES.get(employee_name.lower(), "Account balance not found."),
        )

    @function_tool
    def process_transaction(transaction_id: str, amount: str) -> str:
        """Process a finance transaction by transaction ID and amount."""
        return runtime.invoke(
            session_id=session_id,
            agent_name="FinanceAgent",
            tool_name="process_transaction",
            parameters={"transaction_id": transaction_id, "amount": amount},
            handler=lambda: f"Transaction {transaction_id} for {amount} processed.",
        )

    return [
        query_employee_salary,
        update_salary,
        get_payroll_info,
        update_banking_details,
        query_account_balance,
        process_transaction,
    ]
