# tests/infrastructure/connectors/test_exchange_connector.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities.ticker import Ticker
from src.domain.entities.order_book import OrderBook
from src.domain.entities.order import Order
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector

@pytest.fixture
def mock_ccxt_client():
    """Мок для клиента ccxt.pro."""
    client = MagicMock()
    client.watch_ticker = AsyncMock()
    client.fetch_ticker = AsyncMock()
    client.watch_order_book = AsyncMock()
    client.fetch_order_book = AsyncMock()
    client.create_order = AsyncMock()
    client.cancel_order = AsyncMock()
    client.fetch_order = AsyncMock()
    client.fetch_open_orders = AsyncMock()
    client.load_markets = AsyncMock(return_value={}) # Добавляем мок для load_markets
    return client

@pytest.fixture
def connector(mock_ccxt_client):
    """Фикстура для создания экземпляра коннектора с моком."""
    # Мокаем __init__, чтобы не выполнять реальную загрузку конфига и кли��нта
    original_init = CcxtExchangeConnector.__init__
    CcxtExchangeConnector.__init__ = lambda self, use_sandbox=False: None
    
    conn = CcxtExchangeConnector()
    conn.client = mock_ccxt_client
    conn.exchange_info_cache = {}  # Добавляем инициализацию кэша
    conn._normalize_symbol = lambda symbol: symbol # Упрощаем нормализацию для тестов
    
    yield conn
    
    # Восстанавливаем оригинальный __init__
    CcxtExchangeConnector.__init__ = original_init

@pytest.mark.asyncio
async def test_watch_ticker_returns_ticker_entity(connector, mock_ccxt_client):
    """Тест: watch_ticker должен возвращать сущность Ticker."""
    mock_ccxt_client.watch_ticker.return_value = {"symbol": "BTC/USDT", "last": 50000.0}
    
    result = await connector.watch_ticker("BTC/USDT")
    
    assert isinstance(result, Ticker)
    assert result.symbol == "BTC/USDT"
    print("\nOK: test_watch_ticker_returns_ticker_entity passed.")

@pytest.mark.asyncio
async def test_fetch_order_book_returns_order_book_entity(connector, mock_ccxt_client):
    """Тест: fetch_order_book должен возвращать сущность OrderBook."""
    mock_ccxt_client.fetch_order_book.return_value = {"symbol": "BTC/USDT", "bids": [], "asks": []}
    
    result = await connector.fetch_order_book("BTC/USDT")
    
    assert isinstance(result, OrderBook)
    assert result.symbol == "BTC/USDT"
    print("OK: test_fetch_order_book_returns_order_book_entity passed.")

@pytest.mark.asyncio
async def test_fetch_open_orders_returns_list_of_order_entities(connector, mock_ccxt_client):
    """Тест: fetch_open_orders должен возвращать список сущностей Order."""
    mock_ccxt_client.fetch_open_orders.return_value = [
        {"id": "1", "symbol": "BTC/USDT", "side": "buy", "type": "limit", "price": 50000, "amount": 1},
        {"id": "2", "symbol": "BTC/USDT", "side": "sell", "type": "limit", "price": 51000, "amount": 1}
    ]
    
    result = await connector.fetch_open_orders("BTC/USDT")
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(o, Order) for o in result)
    assert result[0].exchange_id == "1"
    assert result[1].side == "sell"
    print("OK: test_fetch_open_orders_returns_list_of_order_entities passed.")
