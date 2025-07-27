import os
import pytest
import ccxt

from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector

pytestmark = pytest.mark.asyncio

SANDBOX_API_KEY = os.getenv("BINANCE_SANDBOX_API_KEY")
SANDBOX_SECRET = os.getenv("BINANCE_SANDBOX_SECRET")


@pytest.fixture
async def connector():
    if not SANDBOX_API_KEY or not SANDBOX_SECRET:
        pytest.skip("Binance sandbox credentials not configured")
    os.environ["BINANCE_SANDBOX_API_KEY"] = SANDBOX_API_KEY
    os.environ["BINANCE_SANDBOX_SECRET"] = SANDBOX_SECRET
    conn = CcxtExchangeConnector("binance", use_sandbox=True)
    yield conn
    await conn.close()


async def watch_with_reconnect(conn, symbol, attempts=2):
    for _ in range(attempts):
        try:
            return await conn.watch_ticker(symbol)
        except ccxt.BaseError:
            await conn.close()
            conn = CcxtExchangeConnector("binance", use_sandbox=True)
    raise RuntimeError("watch_ticker failed after retries")


async def test_order_lifecycle_with_reconnect(connector):
    symbol = "BTC/USDT"

    ticker = await watch_with_reconnect(connector, symbol)
    assert "last" in ticker
    last_price = ticker["last"]

    price = round(last_price * 0.5, 2)
    amount = 0.001

    order = await connector.create_order(symbol, "buy", "limit", amount, price)
    order_id = order["id"]
    assert order_id

    fetched = await connector.fetch_order(order_id, symbol)
    assert fetched["status"] in {"open", "canceled", "closed"}

    await connector.cancel_order(order_id, symbol)
    canceled = await connector.fetch_order(order_id, symbol)
    assert canceled["status"] in {"canceled", "closed"}
    open_orders = await connector.fetch_open_orders(symbol)
    assert order_id not in [o["id"] for o in open_orders]

    await connector.client.close()
    ticker = await watch_with_reconnect(connector, symbol)
    assert "last" in ticker
