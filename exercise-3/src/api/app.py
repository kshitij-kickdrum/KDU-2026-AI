from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.dependencies import build_container
from src.api.routes import router
from src.utils.logger import setup_logging


setup_logging(logging.INFO)


app = FastAPI(title="Tri-Model AI Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_request_response(request: Request, call_next):
    logger = logging.getLogger("api.request")
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception):
    logging.getLogger("api.error").exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": "INTERNAL_ERROR"})


@app.on_event("startup")
async def startup_event() -> None:
    project_root = Path(__file__).resolve().parents[2]
    app.state.container = build_container(project_root)
    try:
        app.state.container.bart_model.load()
        app.state.container.roberta_model.load()
    except Exception as exc:
        logging.getLogger("api.startup").warning("Model preload failed; lazy loading will be used: %s", exc)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    app.state.container.session_store.cleanup()


app.include_router(router)
