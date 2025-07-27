
import pytest
import asyncio
import time
from collections import deque

from src.infrastructure.repositories.stream.in_memory_stream_data_repository import InMemoryStreamDataRepository


@pytest.fixture
def repository():
    """Фикстура для создания чистого репозитория перед каждым тестом."""
    return InMemoryStreamDataRepository()

@pytest.fixture
def sample_ticker_data():
    """Фикстура с примером данных тикера."""
    return {
        'timestamp': int(time.time() * 1000),
        'close': 45000.5,
        'volume': 1234.5
    }

@pytest.fixture
def sample_orderbook_data():
    """Фикстура с примером данных стакана."""
    return {
        'timestamp': int(time.time() * 1000),
        'bids': [[45000.0, 1.5], [44999.0, 2.5]],
        'asks': [[45001.0, 1.0], [45002.0, 2.0]]
    }

@pytest.mark.asyncio
async def test_append_and_get_ticker(repository, sample_ticker_data):
    symbol = "BTCUSDT"
    await repository.append_ticker_data(symbol, sample_ticker_data)
    
    history = await repository.get_ticker_history(symbol, limit=1)
    assert len(history) == 1
    assert history[0]['close'] == 45000.5
    
    latest = await repository.get_latest_ticker(symbol)
    assert latest['close'] == 45000.5

@pytest.mark.asyncio
async def test_ticker_history_limit(repository, sample_ticker_data):
    symbol = "BTCUSDT"
    for i in range(5):
        data = sample_ticker_data.copy()
        data['close'] = 100 + i
        await repository.append_ticker_data(symbol, data, max_history_size=5)
        
    assert len(repository._ticker_data[symbol]) == 5
    
    # Добавляем шестой, первый должен удалиться
    data = sample_ticker_data.copy()
    data['close'] = 200
    await repository.append_ticker_data(symbol, data, max_history_size=5)
    
    history = await repository.get_ticker_history(symbol, limit=10)
    assert len(history) == 5
    assert history[0]['close'] == 101

@pytest.mark.asyncio
async def test_get_price_history(repository, sample_ticker_data):
    symbol = "BTCUSDT"
    prices = [100, 101, 102, 103, 104]
    for price in prices:
        data = sample_ticker_data.copy()
        data['close'] = price
        await repository.append_ticker_data(symbol, data)
        
    price_history = await repository.get_price_history(symbol, limit=3)
    assert price_history == [102, 103, 104]

@pytest.mark.asyncio
async def test_append_and_get_orderbook(repository, sample_orderbook_data):
    symbol = "BTCUSDT"
    await repository.append_orderbook_snapshot(symbol, sample_orderbook_data)
    
    history = await repository.get_orderbook_history(symbol, limit=1)
    assert len(history) == 1
    assert history[0]['bids'][0][0] == 45000.0
    
    latest = await repository.get_latest_orderbook(symbol)
    assert latest['bids'][0][0] == 45000.0

@pytest.mark.asyncio
async def test_calculate_sma(repository, sample_ticker_data):
    symbol = "BTCUSDT"
    prices = [10, 20, 30, 40, 50]
    for price in prices:
        data = sample_ticker_data.copy()
        data['close'] = price
        await repository.append_ticker_data(symbol, data)
        
    sma = await repository.calculate_sma(symbol, period=3)
    assert sma == (30 + 40 + 50) / 3
    
    sma_none = await repository.calculate_sma(symbol, period=10)
    assert sma_none is None

@pytest.mark.asyncio
async def test_calculate_price_change(repository, sample_ticker_data):
    symbol = "BTCUSDT"
    prices = [100, 110, 105, 120]
    for price in prices:
        data = sample_ticker_data.copy()
        data['close'] = price
        await repository.append_ticker_data(symbol, data)
        
    change = await repository.calculate_price_change(symbol, periods=2)
    assert change['absolute'] == 120 - 110
    assert change['percent'] == (10 / 110) * 100

@pytest.mark.asyncio
async def test_get_volatility(repository, sample_ticker_data):
    symbol = "BTCUSDT"
    prices = [100, 102, 98, 105, 103]
    for price in prices:
        data = sample_ticker_data.copy()
        data['close'] = price
        await repository.append_ticker_data(symbol, data)
        
    volatility = await repository.get_volatility(symbol, periods=5)
    assert volatility is not None
    assert volatility > 0

@pytest.mark.asyncio
async def test_get_data_stats(repository, sample_ticker_data):
    symbol = "BTCUSDT"
    await repository.append_ticker_data(symbol, sample_ticker_data)
    
    stats = await repository.get_data_stats(symbol)
    assert stats['ticker_count'] == 1
    assert stats['orderbook_count'] == 0

@pytest.mark.asyncio
async def test_delete_symbol_data(repository, sample_ticker_data):
    symbol = "BTCUSDT"
    await repository.append_ticker_data(symbol, sample_ticker_data)
    assert symbol in repository._ticker_data
    
    result = await repository.delete_symbol_data(symbol)
    assert result is True
    assert symbol not in repository._ticker_data
    assert symbol not in repository._price_cache
    assert symbol not in repository._latest_ticker_cache
