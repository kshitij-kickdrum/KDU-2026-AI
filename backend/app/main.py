"""FastAPI Application Entry Point"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import ErrorResponse

# Set LangSmith env vars at startup so all traces are captured
os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


class AppException(Exception):
    """Base exception for application errors."""
    def __init__(self, code: str, message: str, http_status: int = 500):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


app = FastAPI(
    title="Stock Trading Agent",
    description="LangGraph-based trading agent with human-in-the-loop approval",
    version=settings.app_version,
)

API_PREFIX = "/api/v1"

# Allow frontend dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application-specific exceptions."""
    return JSONResponse(
        status_code=exc.http_status,
        content=ErrorResponse(code=exc.code, message=exc.message).dict()
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred"
        ).dict()
    )


@app.on_event("startup")
async def startup_event():
    """Initialize SQLite checkpoint database on startup."""
    db_path = settings.checkpoint_db_path
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)


# Register routers
from app.routers import run, approve, state, sessions, health, evaluate

app.include_router(run.router, prefix=API_PREFIX, tags=["agent"])
app.include_router(approve.router, prefix=API_PREFIX, tags=["agent"])
app.include_router(state.router, prefix=API_PREFIX, tags=["agent"])
app.include_router(sessions.router, prefix=API_PREFIX, tags=["agent"])
app.include_router(health.router, prefix=API_PREFIX, tags=["health"])
app.include_router(evaluate.router, prefix=API_PREFIX, tags=["evaluation"])
