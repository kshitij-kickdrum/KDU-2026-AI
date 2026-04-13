"""
LangChain Tools for External API Calls

Tools are functions the LLM can call to interact with external systems.
The @tool decorator makes a function callable by the LLM.
"""

import httpx
from langchain_core.tools import tool
from app.config import settings


@tool
def fetch_stock_price(symbol: str) -> dict:
    """
    Fetch current stock price from Finnhub API.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "TSLA")
    
    Returns:
        dict with {"price": float} or {"error": str}
    """
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={settings.finnhub_api_key}"
    
    try:
        response = httpx.get(url, timeout=settings.stock_api_timeout_seconds)
        
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            return {"error": f"Rate limit exceeded. Retry after {retry_after} seconds."}
        
        # Handle invalid symbol
        if response.status_code != 200:
            return {"error": f"Invalid symbol: {symbol}"}
        
        data = response.json()
        price = data.get("c", 0)
        
        # Validate price
        if price <= 0:
            return {"error": f"Invalid price returned: {price}"}
        
        return {"price": price}
    
    except httpx.TimeoutException:
        return {"error": "Stock API timeout"}
    
    except Exception as e:
        return {"error": f"Stock API error: {str(e)}"}


def fetch_live_exchange_rate(currency: str) -> float | None:
    """
    Fetch live exchange rate from freecurrencyapi.
    
    Args:
        currency: "INR" or "EUR"
    
    Returns:
        Exchange rate as float, or None if API call fails
    """
    url = f"https://api.freecurrencyapi.com/v1/latest?apikey={settings.freecurrency_api_key}&base_currency=USD&currencies={currency}"
    
    try:
        response = httpx.get(url, timeout=settings.stock_api_timeout_seconds)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        rate = data.get("data", {}).get(currency)
        
        return rate
    
    except Exception:
        return None
