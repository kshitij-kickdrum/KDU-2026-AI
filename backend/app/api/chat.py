from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.llm_service import LLMService
from app.services.streaming_engine import StreamingEngine
from app.services.usage_tracker import UsageRecord, UsageTracker
from app.tools.calculator_tool import CalculatorTool
from app.tools.registry import ToolRegistry
from app.tools.search_tool import SearchTool
from app.tools.weather_tool import WeatherTool
from app.utils.errors import ValidationError
from app.utils.validators import validate_message, validate_session_id


router = APIRouter(prefix="/chat", tags=["chat"])
usage_tracker = UsageTracker()
registry = ToolRegistry()
registry.register_many([WeatherTool(), CalculatorTool(), SearchTool()])
llm_service = LLMService(registry=registry)
streaming_engine = StreamingEngine()


class ChatRequest(BaseModel):
    message: Annotated[str, Field(min_length=1)]
    session_id: Annotated[str, Field(min_length=3, max_length=128)]
    stream: bool = True


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    try:
        message = validate_message(request.message)
        session_id = validate_session_id(request.session_id)
    except ValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    answer, used_tools, tool_results, llm_usage = await llm_service.generate_response(message)
    input_tokens = int(llm_usage.get("llm_input_tokens", 0))
    output_tokens = int(llm_usage.get("llm_output_tokens", 0))
    # External tool API calls are not billed through LLM token usage.
    tool_tokens = 0

    usage = usage_tracker.log_usage(
        UsageRecord(
            session_id=session_id,
            request_type="chat",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_tokens=tool_tokens,
            provider=llm_service.get_current_provider(),
            model=llm_service.current_model,
            tools_used=used_tools,
        )
    )
    usage["provider_usage_available"] = bool(llm_usage.get("provider_usage_available", False))
    usage["provider"] = llm_service.get_current_provider()
    usage["model"] = llm_service.current_model
    for tool_name, tool_result in zip(used_tools, tool_results, strict=False):
        usage_tracker.log_tool_usage(
            session_id=session_id,
            tool_name=tool_name,
            execution_time=tool_result.execution_time,
            success=tool_result.success,
            error_message=tool_result.error_message,
        )

    generator = streaming_engine.stream_response(
        session_id=session_id,
        text_stream=llm_service.stream_text(answer),
        used_tools=used_tools,
        tool_results=tool_results,
        usage=usage,
    )
    return StreamingResponse(generator, media_type="text/event-stream")
