from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.routes import chat, health, history, image, session, user
from app.core.config import settings
from app.core.exceptions import AppException, RateLimitExceededError
from app.core.limiter import limiter
from app.core.logging import setup_logging
from app.middleware.context_middleware import ContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    error = RateLimitExceededError()
    return JSONResponse(
        status_code=error.status_code,
        content={"code": error.code, "message": error.message},
    )


app = FastAPI(title="Multimodal AI Assistant", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
    )


API_PREFIX = "/api/v1"

allowed_origins = [
    origin.strip()
    for origin in settings.cors_allowed_origins.split(",")
    if origin.strip()
]

app.add_middleware(ContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(image.router, prefix=API_PREFIX)
app.include_router(history.router, prefix=API_PREFIX)
app.include_router(session.router, prefix=API_PREFIX)
app.include_router(user.router, prefix=API_PREFIX)
app.include_router(health.router, prefix=API_PREFIX)
