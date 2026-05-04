from __future__ import annotations

import asyncio
import argparse
import statistics
import sys
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.consensus_agent import ConsensusAgent
from agents.coordinator import Coordinator
from agents.db_agent import DBAgent
from agents.vector_agent import VectorAgent
from concurrency.queue_manager import ConcurrencyQueue
from config.settings import Settings
from llm.llm_client import LLMClient
from monitoring.monitor import Monitor
from storage.faiss_store import FAISSStore
from storage.sqlite_store import SQLiteStore


async def run_session(coordinator: Coordinator, idx: int) -> int:
    start = time.perf_counter()
    query = "What is the balance for C-00123?"
    result = await coordinator.run(query, str(uuid4()))
    latency = int((time.perf_counter() - start) * 1000)
    if result.error:
        print(f"session {idx}: {result.error}")
    return latency


async def main_async() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Opt in to live LLM consensus calls during the 100-session simulation",
    )
    args = parser.parse_args()
    settings = Settings.load(require_api_keys=False)
    monitor = Monitor(settings.log_file_path)
    sqlite_queue = ConcurrencyQueue(settings.sqlite_max_connections, settings.queue_timeout_seconds)
    faiss_queue = ConcurrencyQueue(settings.faiss_max_connections, settings.queue_timeout_seconds)
    llm = LLMClient(
        settings.openai_api_key if args.use_llm else None,
        settings.openrouter_api_key if args.use_llm else None,
        settings.openrouter_base_url,
    )
    coordinator = Coordinator(
        DBAgent(SQLiteStore(settings.sqlite_db_path), sqlite_queue, monitor),
        VectorAgent(FAISSStore(settings.faiss_index_path, settings.faiss_metadata_path), faiss_queue, monitor),
        ConsensusAgent(llm, monitor, settings.llm_model),
        monitor,
    )
    started = time.perf_counter()
    latencies = await asyncio.gather(*(run_session(coordinator, i) for i in range(100)))
    total = time.perf_counter() - started
    print(f"completed=100 total_seconds={total:.2f} median_latency_ms={statistics.median(latencies):.0f}")


if __name__ == "__main__":
    asyncio.run(main_async())
