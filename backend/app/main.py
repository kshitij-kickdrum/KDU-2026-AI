from logging.config import fileConfig
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.usage import router as usage_router
from app.database.migrations import initialize_database


ROOT = Path(__file__).resolve().parents[2]
logging_config = ROOT / "config" / "logging.conf"
if logging_config.exists():
    fileConfig(logging_config, disable_existing_loggers=False)

app = FastAPI(title="Multi-Function AI Assistant", version="1.0.0", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(usage_router)
app.include_router(health_router)


@app.on_event("startup")
async def startup() -> None:
    initialize_database()

