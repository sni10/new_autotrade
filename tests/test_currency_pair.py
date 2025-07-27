import sys
import os
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from domain.entities.currency_pair import CurrencyPair


def test_currency_pair_defaults_and_repr():
    pair = CurrencyPair("BTC", "USDT")
    assert pair.symbol == "BTC/USDT"
    assert pair.order_life_time == 1
    r = repr(pair)
    assert "BTC/USDT" in r


@pytest.mark.asyncio
async def test_refresh_market_info_and_active():
    market = {
        "BTC/USDT": {
            "symbol": "BTC/USDT",
            "base": "BTC",
            "quote": "USDT",
            "active": True,
            "precision": {"amount": 3, "price": 2},
            "limits": {
                "amount": {"min": 0.001, "max": 100},
                "price": {"min": 0.01, "max": 100000},
                "cost": {"min": 10},
            },
            "maker": 0.001,
            "taker": 0.001,
        }
    }
    from tests.mocks.mock_exchange_connector import MockCcxtExchangeConnector

    connector = MockCcxtExchangeConnector(market)
    pair = CurrencyPair("BTC", "USDT")
    await pair.refresh_market_info(connector)

    assert pair.precision == {"amount": 3, "price": 2}
    assert pair.limits["amount"]["min"] == 0.001
    assert pair.taker_fee == 0.001
    assert pair.is_active()
