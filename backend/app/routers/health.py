"""GET /api/v1/health Endpoint - Health check"""
"""GET /api/v1/symbols/search?q= Endpoint - Search stock symbols via Finnhub"""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Query
import httpx

from app.models import HealthResponse
from app.config import settings


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint. Returns 200 if service is running."""
    return HealthResponse(
        status="ok",
        version=settings.app_version
    )


@router.get("/symbols/search")
async def search_symbols(q: Annotated[str, Query(..., min_length=1)]):
    """
    Search for stock symbols using Finnhub symbol search API.
    Returns a list of matching symbols with descriptions.
    """
    url = f"https://finnhub.io/api/v1/search?q={q}&token={settings.finnhub_api_key}"
    async def fetch_quote_price(client: httpx.AsyncClient, symbol: str) -> float | None:
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={settings.finnhub_api_key}"
        try:
            quote_response = await client.get(quote_url, timeout=settings.stock_api_timeout_seconds)
            if quote_response.status_code != 200:
                return None
            quote_data = quote_response.json()
            current_price = quote_data.get("c")
            if isinstance(current_price, (int, float)) and current_price > 0:
                return float(current_price)
        except Exception:
            return None
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=settings.stock_api_timeout_seconds)
            if response.status_code != 200:
                return {"result": []}
            data = response.json()

            candidates = [
                item
                for item in data.get("result", [])
                if item.get("type") in ("Common Stock", "EQS") and "." not in item["symbol"]
            ][:10]

            prices = await asyncio.gather(
                *(fetch_quote_price(client, item["symbol"]) for item in candidates),
                return_exceptions=False,
            )

            results = [
                {
                    "symbol": item["symbol"],
                    "description": item["description"],
                    "price": price,
                }
                for item, price in zip(candidates, prices)
            ]

            return {"result": results}
    except Exception:
        return {"result": []}
