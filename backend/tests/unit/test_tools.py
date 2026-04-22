import pytest

from app.tools.calculator_tool import CalculatorTool
from app.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_calculator_basic_expression():
    tool = CalculatorTool()
    result = await tool.execute(expression="2 + 3 * 4")
    assert result.success
    assert result.data["float"] == 14.0


@pytest.mark.asyncio
async def test_tool_registry_missing_tool():
    registry = ToolRegistry()
    result = await registry.execute_tool("unknown", {})
    assert not result.success
    assert "not registered" in result.error_message

