import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.user_service import get_user_profile


class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )

        # load user profile into request state if user_id is in the query or body
        # routes that don't carry a user_id (health) are unaffected
        user_id = request.query_params.get("user_id")
        if user_id:
            try:
                request.state.profile = get_user_profile(user_id)
                structlog.contextvars.bind_contextvars(user_id=user_id)
            except Exception:
                request.state.profile = None

        response = await call_next(request)

        structlog.contextvars.bind_contextvars(status_code=response.status_code)
        structlog.get_logger(__name__).info("request completed")

        return response
