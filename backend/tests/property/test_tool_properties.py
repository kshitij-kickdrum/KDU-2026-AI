import math

import pytest
pytest.importorskip("hypothesis")
from hypothesis import given, settings
from hypothesis import strategies as st

from app.tools.calculator_tool import CalculatorTool


@pytest.mark.asyncio
@given(a=st.floats(allow_nan=False, allow_infinity=False, width=16), b=st.floats(allow_nan=False, allow_infinity=False, width=16))
@settings(max_examples=100)
async def test_property_math_accuracy(a: float, b: float):
    tool = CalculatorTool()
    result = await tool.execute(expression=f"{a}+{b}")
    assert result.success
    assert math.isclose(float(result.data["float"]), a + b, rel_tol=1e-6, abs_tol=1e-6)
