import pytest
pytest.importorskip("hypothesis")
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.streaming_engine import StreamingEngine


async def _gen(text: str):
    for part in text.split(" "):
        yield part + " "


@pytest.mark.asyncio
@given(st.text(min_size=1, max_size=200))
@settings(max_examples=50)
async def test_property_progressive_delivery(text: str):
    engine = StreamingEngine()
    chunks = []
    async for event in engine.stream_response(
        session_id="sess_prop",
        text_stream=_gen(text),
        used_tools=[],
        tool_results=[],
        usage={"total_tokens": 1, "estimated_cost": 0.0},
    ):
        chunks.append(event)
    content_events = [chunk for chunk in chunks if '"type": "content"' in chunk]
    assert content_events
