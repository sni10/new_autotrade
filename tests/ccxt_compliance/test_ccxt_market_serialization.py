import pytest

from src.domain.entities.ccxt_currency_pair import (
    create_ccxt_currency_pair_from_market,
)


@pytest.fixture

def sample_ccxt_market():
    return {
        "id": "BTCUSDT",
        "symbol": "BTC/USDT",
        "base": "BTC",
        "quote": "USDT",
        "active": True,
        "type": "spot",
        "spot": True,
        "margin": False,
        "future": False,
        "swap": False,
        "option": False,
        "contract": False,
        "precision": {"amount": 8, "price": 2},
        "limits": {
            "amount": {"min": 0.00001, "max": 1000},
            "price": {"min": 0.01, "max": 1000000},
            "cost": {"min": 10},
        },
        "maker": 0.001,
        "taker": 0.001,
        "info": {},
    }


def test_market_serialization_roundtrip(sample_ccxt_market):
    pair = create_ccxt_currency_pair_from_market(sample_ccxt_market)

    market_dict = pair.get_ccxt_market_dict()
    assert market_dict is not None
    assert market_dict["symbol"] == sample_ccxt_market["symbol"]

    pair_restored = create_ccxt_currency_pair_from_market(market_dict)
    assert pair_restored.get_ccxt_market_dict() == market_dict
