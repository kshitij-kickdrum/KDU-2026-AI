import pytest

from app.agent.nodes import _extract_latest_price, execute_trade_node


class _Msg:
    def __init__(self, content):
        self.content = content


def test_extract_latest_price_prefers_most_recent_valid_price():
    messages = [
        _Msg({"price": 101.5}),
        _Msg('{"price": 352.42}'),
        _Msg({"error": "rate limit"}),
    ]

    assert _extract_latest_price(messages) == pytest.approx(352.42)


def test_execute_trade_uses_tool_price_when_available():
    state = {
        "pending_action": "buy",
        "symbol": "TSLA",
        "trade_log": [],
        "portfolio": [
            {"symbol": "TSLA", "quantity": 50.0, "avg_buy_price": 340.0},
        ],
        "currency": "USD",
        "exchange_rate": None,
        "messages": [_Msg('{"price": 352.42}')],
    }

    result = execute_trade_node(state)

    assert len(result["trade_log"]) == 1
    assert "BUY 10 shares of TSLA at $352.42" in result["trade_log"][0]
    assert result["portfolio"][0]["quantity"] == pytest.approx(60.0)
    assert result["portfolio"][0]["avg_buy_price"] == pytest.approx(342.07, rel=1e-3)
    assert result["portfolio_total_usd"] == pytest.approx(20524.2)


def test_execute_trade_falls_back_to_default_price_without_tool_price():
    state = {
        "pending_action": "sell",
        "symbol": "AAPL",
        "trade_log": [],
        "portfolio": [
            {"symbol": "AAPL", "quantity": 12.0, "avg_buy_price": 200.0},
        ],
        "currency": "USD",
        "exchange_rate": None,
        "messages": [_Msg({"error": "Stock API timeout"})],
    }

    result = execute_trade_node(state)

    assert len(result["trade_log"]) == 1
    assert "SELL 10 shares of AAPL at $150.00" in result["trade_log"][0]
    assert result["portfolio"][0]["quantity"] == pytest.approx(2.0)
    assert result["portfolio_total_usd"] == pytest.approx(400.0)
