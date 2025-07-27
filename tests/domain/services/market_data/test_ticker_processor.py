import pytest
import asyncio
import time
from unittest.mock import AsyncMock

from src.domain.services.market_data.ticker_processor import TickerProcessor
from src.domain.repositories.i_stream_data_repository import IStreamDataRepository
from typing import List, Optional, Dict, Any


class MockStreamDataRepository(IStreamDataRepository):
    """Mock репозиторий для тестирования TickerProcessor."""
    
    def __init__(self):
        self.append_calls = []
        self.latest_ticker = None
        self.stats = {}

    async def append_ticker_data(self, symbol: str, ticker_data: dict, max_history_size: int = 1000):
        self.append_calls.append((symbol, ticker_data))
        return True

    async def get_latest_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self.latest_ticker

    async def get_data_stats(self, symbol: str) -> dict:
        return self.stats

    # --- Заглушки для остальных методов интерфейса ---
    async def get_ticker_history(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]: return []
    async def get_price_history(self, symbol: str, limit: int = 200) -> List[float]: return []
    async def append_orderbook_snapshot(self, symbol: str, orderbook_data: Dict[str, Any], max_history_size: int = 100) -> None: pass
    async def get_orderbook_history(self, symbol: str, limit: int = 50) -> List[Dict[str, Any]]: return []
    async def get_latest_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]: return None
    async def calculate_sma(self, symbol: str, period: int) -> Optional[float]: return None
    async def calculate_price_change(self, symbol: str, periods: int = 1) -> Optional[Dict[str, float]]: return None
    async def get_volatility(self, symbol: str, periods: int = 20) -> Optional[float]: return None
    async def cleanup_old_data(self, symbol: str, keep_ticker_count: int = 1000, keep_orderbook_count: int = 100) -> Dict[str, int]: return {}
    async def bulk_append_tickers(self, symbol: str, ticker_batch: List[Dict[str, Any]], max_history_size: int = 1000) -> None: pass
    async def get_ticker_subset(self, symbol: str, start_index: int, count: int) -> List[Dict[str, Any]]: return []
    async def get_tickers_by_time_range(self, symbol: str, start_timestamp: int, end_timestamp: int) -> List[Dict[str, Any]]: return []
    async def compress_old_data(self, symbol: str, older_than_timestamp: int) -> int: return 0
    async def export_to_json(self, symbol: str, file_path: str, start_timestamp: Optional[int] = None, end_timestamp: Optional[int] = None) -> bool: return False
    async def import_from_json(self, symbol: str, file_path: str, append: bool = True) -> int: return 0
    async def get_all_symbols(self) -> List[str]: return []
    async def delete_symbol_data(self, symbol: str) -> bool: return False
    async def update_indicator_buffer(self, symbol: str, indicator_name: str, value: float, max_buffer_size: int = 100) -> None: pass
    async def get_indicator_buffer(self, symbol: str, indicator_name: str, limit: int = 50) -> List[float]: return []
    async def clear_indicator_buffers(self, symbol: str) -> int: return 0


@pytest.fixture
def mock_stream_repo():
    """Фикстура для mock репозитория."""
    return MockStreamDataRepository()


@pytest.fixture
def ticker_processor(mock_stream_repo):
    """Фикстура для создания TickerProcessor."""
    return TickerProcessor(mock_stream_repo)


@pytest.fixture
def sample_ticker_data():
    """Фикстура с примером валидных данных тикера."""
    return {
        'timestamp': int(time.time() * 1000),
        'close': 45000.5,
        'open': 44500.0,
        'high': 46000.0,
        'low': 44000.0,
        'volume': 1234.5,
        'quoteVolume': 55555.5
    }


@pytest.mark.asyncio
async def test_process_ticker_valid_data(ticker_processor, mock_stream_repo, sample_ticker_data):
    """Тест обработки валидных данных тикера."""
    symbol = "BTCUSDT"
    
    result = await ticker_processor.process_ticker(symbol, sample_ticker_data)
    
    assert result is True
    assert len(mock_stream_repo.append_calls) == 1
    
    call_symbol, call_data = mock_stream_repo.append_calls[0]
    assert call_symbol == symbol
    assert call_data['close'] == 45000.5
    assert call_data['volume'] == 1234.5
    
    stats = ticker_processor.get_processing_stats()
    assert stats['processed_tickers'] == 1
    assert stats['invalid_tickers'] == 0
    assert stats['validation_errors'] == 0


@pytest.mark.asyncio
async def test_process_ticker_invalid_data(ticker_processor):
    """Тест обработки невалидных данных (отсутствует 'close')."""
    symbol = "BTCUSDT"
    invalid_data = {'timestamp': int(time.time() * 1000)}
    
    result = await ticker_processor.process_ticker(symbol, invalid_data)
    
    assert result is False
    stats = ticker_processor.get_processing_stats()
    assert stats['processed_tickers'] == 0
    assert stats['invalid_tickers'] == 1
    assert stats['validation_errors'] == 0


@pytest.mark.asyncio
async def test_process_ticker_repository_error(sample_ticker_data):
    """Тест обработки ошибки при сохранении в репозиторий."""
    error_repo = MockStreamDataRepository()
    error_repo.append_ticker_data = AsyncMock(side_effect=Exception("DB Error"))
    processor = TickerProcessor(error_repo)
    
    result = await processor.process_ticker("BTCUSDT", sample_ticker_data)
    
    assert result is False
    stats = processor.get_processing_stats()
    assert stats['processed_tickers'] == 0
    assert stats['invalid_tickers'] == 0
    assert stats['validation_errors'] == 1


def test_validate_ticker_data(ticker_processor):
    """Тесты для внутреннего метода валидации."""
    # Валидные
    assert ticker_processor._validate_ticker_data({'close': 1, 'timestamp': 1}) is True
    
    # Невалидные
    assert ticker_processor._validate_ticker_data({}) is False  # Пустые
    assert ticker_processor._validate_ticker_data({'close': 1}) is False # Нет timestamp
    assert ticker_processor._validate_ticker_data({'timestamp': 1}) is False # Нет close
    assert ticker_processor._validate_ticker_data({'close': 'abc', 'timestamp': 1}) is False # Неверный тип
    assert ticker_processor._validate_ticker_data({'close': -10, 'timestamp': 1}) is False # Неверное значение


def test_normalize_ticker_data(ticker_processor):
    """Тест для внутреннего метода нормализации."""
    input_data = {
        'timestamp': '1234567890',
        'close': '45000.5',
        'volume': '1234.5',
        'extra_field': 'should_be_ignored'
    }
    normalized = ticker_processor._normalize_ticker_data(input_data)
    
    assert isinstance(normalized['timestamp'], int)
    assert isinstance(normalized['close'], float)
    assert isinstance(normalized['volume'], float)
    assert normalized['timestamp'] == 1234567890
    assert normalized['close'] == 45000.5
    assert 'extra_field' not in normalized


@pytest.mark.asyncio
async def test_get_latest_price(ticker_processor, mock_stream_repo):
    """Тест получения последней цены."""
    symbol = "BTCUSDT"
    mock_stream_repo.latest_ticker = {'close': 50000.0}
    
    price = await ticker_processor.get_latest_price(symbol)
    
    assert price == 50000.0


@pytest.mark.asyncio
async def test_get_ticker_count(ticker_processor, mock_stream_repo):
    """Тест получения количества тикеров."""
    symbol = "BTCUSDT"
    mock_stream_repo.stats = {'ticker_count': 123}
    
    count = await ticker_processor.get_ticker_count(symbol)
    
    assert count == 123


def test_get_and_reset_stats(ticker_processor):
    """Тест получения и сброса статистики."""
    initial_stats = ticker_processor.get_processing_stats()
    assert initial_stats['processed_tickers'] == 0
    
    # Имитируем обработку
    ticker_processor._stats['processed_tickers'] = 10
    ticker_processor._stats['invalid_tickers'] = 2
    
    updated_stats = ticker_processor.get_processing_stats()
    assert updated_stats['processed_tickers'] == 10
    assert updated_stats['invalid_tickers'] == 2
    
    # Сбрасываем
    ticker_processor.reset_stats()
    reset_stats = ticker_processor.get_processing_stats()
    assert reset_stats['processed_tickers'] == 0
    assert reset_stats['invalid_tickers'] == 0