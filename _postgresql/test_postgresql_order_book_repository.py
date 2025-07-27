import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.infrastructure.repositories.postgresql.postgresql_order_book_repository import PostgreSQLOrderBookRepository
from src.domain.entities.order_book import OrderBook, OrderBookLevel
from src.infrastructure.database.database_manager import DatabaseManager


class MockDatabaseManager:
    """Mock менеджер базы данных для тестирования"""
    
    def __init__(self):
        self.pool = MagicMock()
        self.connection = AsyncMock()
        self.cursor = AsyncMock()
        self.fetch_results = []
        self.execute_calls = []
        
    async def get_connection(self):
        return self.connection
        
    def set_fetch_results(self, results):
        """Устанавливает результаты для fetchall/fetchone"""
        self.fetch_results = results
        self.cursor.fetchall.return_value = results
        self.cursor.fetchone.return_value = results[0] if results else None
        
    def set_execute_response(self, rowcount=1):
        """Устанавливает ответ для execute"""
        self.cursor.rowcount = rowcount
        
    async def __aenter__(self):
        return self.connection
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestPostgreSQLOrderBookRepository:
    """Тесты для PostgreSQLOrderBookRepository"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Фикстура для mock database manager"""
        return MockDatabaseManager()
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Фикстура для создания репозитория"""
        return PostgreSQLOrderBookRepository(mock_db_manager)
    
    @pytest.fixture
    def sample_order_book(self):
        """Фикстура с примером order book"""
        bids = [
            [44999.0, 1.5],
            [44998.0, 2.1],
            [44997.0, 0.8]
        ]
        asks = [
            [45001.0, 1.2],
            [45002.0, 1.8],
            [45003.0, 0.6]
        ]
        
        return OrderBook(
            symbol="BTCUSDT",
            timestamp=int(time.time() * 1000),
            bids=bids,
            asks=asks
        )
    
    @pytest.mark.asyncio
    async def test_save_order_book(self, repository, mock_db_manager, sample_order_book):
        """Тест сохранения order book"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.save_order_book(sample_order_book)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван execute
        assert mock_db_manager.cursor.execute.called
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO order_books" in query
        assert params[0] == "BTCUSDT"
        assert len(params[2]) > 0  # bids_data
        assert len(params[3]) > 0  # asks_data
    
    @pytest.mark.asyncio
    async def test_save_order_book_failure(self, repository, mock_db_manager, sample_order_book):
        """Тест неудачного сохранения order book"""
        # Настраиваем mock для ошибки
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.execute.side_effect = Exception("Database error")
        
        # Выполняем операцию
        result = await repository.save_order_book(sample_order_book)
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_latest_order_book(self, repository, mock_db_manager, sample_order_book):
        """Тест получения последнего order book"""
        # Настраиваем mock результат
        bids_json = '[{"price": 44999.0, "quantity": 1.5, "orders_count": 3}]'
        asks_json = '[{"price": 45001.0, "quantity": 1.2, "orders_count": 2}]'
        metadata_json = '{"source": "binance", "depth": 6}'
        
        db_row = (
            "BTCUSDT", sample_order_book.timestamp, bids_json, asks_json, 
            2.0, 4400.0, metadata_json
        )
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get_latest_order_book("BTCUSDT")
        
        # Проверяем результат
        assert result is not None
        assert result.symbol == "BTCUSDT"
        assert result.timestamp == sample_order_book.timestamp
        assert len(result.bids) == 1
        assert len(result.asks) == 1
        assert result.bids[0].price == 44999.0
        assert result.asks[0].price == 45001.0
        assert result.metadata["source"] == "binance"
    
    @pytest.mark.asyncio
    async def test_get_latest_order_book_not_found(self, repository, mock_db_manager):
        """Тест получения order book для несуществующего символа"""
        # Настраиваем mock для пустого результата
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([])
        
        # Выполняем операцию
        result = await repository.get_latest_order_book("NONEXISTENT")
        
        # Проверяем результат
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_order_books_in_time_range(self, repository, mock_db_manager):
        """Тест получения order books в временном диапазоне"""
        # Настраиваем mock результаты
        base_time = int(time.time() * 1000)
        bids_json = '[{"price": 44999.0, "quantity": 1.5, "orders_count": 3}]'
        asks_json = '[{"price": 45001.0, "quantity": 1.2, "orders_count": 2}]'
        metadata_json = '{}'
        
        db_rows = [
            ("BTCUSDT", base_time, bids_json, asks_json, 2.0, 4400.0, metadata_json),
            ("BTCUSDT", base_time + 60000, bids_json, asks_json, 2.0, 4400.0, metadata_json),
            ("BTCUSDT", base_time + 120000, bids_json, asks_json, 2.0, 4400.0, metadata_json)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        start_time = base_time - 1000
        end_time = base_time + 180000
        result = await repository.get_order_books_in_time_range("BTCUSDT", start_time, end_time)
        
        # Проверяем результат
        assert len(result) == 3
        assert all(book.symbol == "BTCUSDT" for book in result)
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "timestamp BETWEEN" in query
        assert params[1] == start_time
        assert params[2] == end_time
    
    @pytest.mark.asyncio
    async def test_calculate_spread_analysis(self, repository, mock_db_manager):
        """Тест анализа спреда"""
        # Настраиваем mock результаты
        db_rows = [
            (5, 2.0, 0.5, 1.0, 3.0)  # count, avg_spread, min_spread, max_spread, std_dev
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.calculate_spread_analysis("BTCUSDT", hours=24)
        
        # Проверяем результат
        assert result['symbol'] == "BTCUSDT"
        assert result['period_hours'] == 24
        assert result['samples_count'] == 5
        assert result['avg_spread'] == 2.0
        assert result['min_spread'] == 0.5
        assert result['max_spread'] == 3.0
        assert result['spread_volatility'] == 1.0
    
    @pytest.mark.asyncio
    async def test_get_liquidity_analysis(self, repository, mock_db_manager):
        """Тест анализа ликвидности"""
        # Настраиваем mock результаты
        db_rows = [
            (10, 150000.0, 15000.0, 140000.0, 20000.0, 170000.0, 5000.0)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_liquidity_analysis("BTCUSDT", depth_levels=5)
        
        # Проверяем результат
        assert result['symbol'] == "BTCUSDT"
        assert result['depth_levels'] == 5
        assert result['samples_count'] == 10
        assert result['avg_bid_liquidity'] == 150000.0
        assert result['avg_ask_liquidity'] == 15000.0
        assert result['min_bid_liquidity'] == 140000.0
        assert result['max_bid_liquidity'] == 20000.0
        assert result['min_ask_liquidity'] == 170000.0
        assert result['max_ask_liquidity'] == 5000.0
    
    @pytest.mark.asyncio
    async def test_delete_old_order_books(self, repository, mock_db_manager):
        """Тест удаления старых order books"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=25)
        
        # Выполняем операцию
        hours_to_keep = 24
        result = await repository.delete_old_order_books(hours_to_keep)
        
        # Проверяем результат
        assert result == 25
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM order_books" in query
        assert "timestamp <" in query
        # Проверяем что timestamp вычислен корректно (24 часа назад)
        expected_cutoff = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
        assert abs(params[0] - expected_cutoff) < 60000  # Допускаем погрешность в 1 минуту
    
    @pytest.mark.asyncio
    async def test_get_order_book_statistics(self, repository, mock_db_manager):
        """Тест получения статистики order book"""
        # Настраиваем mock результаты
        db_rows = [
            ("BTCUSDT", 150, 2.5, 1.0, 5.0, 0.8)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_order_book_statistics("BTCUSDT")
        
        # Проверяем результат
        assert result['symbol'] == "BTCUSDT"
        assert result['total_snapshots'] == 150
        assert result['avg_spread'] == 2.5
        assert result['min_spread'] == 1.0
        assert result['max_spread'] == 5.0
        assert result['spread_std_dev'] == 0.8
    
    @pytest.mark.asyncio
    async def test_batch_save_order_books(self, repository, mock_db_manager, sample_order_book):
        """Тест пакетного сохранения order books"""
        # Создаем тестовые order books
        order_books = []
        base_time = int(time.time() * 1000)
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        for i, symbol in enumerate(symbols):
            book = OrderBook(
                symbol=symbol,
                timestamp=base_time + i * 1000,
                bids=sample_order_book.bids,
                asks=sample_order_book.asks
            )
            order_books.append(book)
        
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.executemany = AsyncMock()
        
        # Выполняем операцию
        result = await repository.batch_save_order_books(order_books)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван executemany
        assert mock_db_manager.cursor.executemany.called
        execute_call = mock_db_manager.cursor.executemany.call_args
        query = execute_call[0][0]
        batch_data = execute_call[0][1]
        
        assert "INSERT INTO order_books" in query
        assert len(batch_data) == 3
    
    @pytest.mark.asyncio
    async def test_get_symbols_with_recent_data(self, repository, mock_db_manager):
        """Тест получения символов с недавними данными"""
        # Настраиваем mock результаты
        db_rows = [
            ("BTCUSDT",),
            ("ETHUSDT",),
            ("ADAUSDT",)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_symbols_with_recent_data(hours=1)
        
        # Проверяем результат
        assert len(result) == 3
        assert "BTCUSDT" in result
        assert "ETHUSDT" in result
        assert "ADAUSDT" in result
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DISTINCT symbol" in query
        assert "timestamp >" in query
        # Проверяем что timestamp вычислен корректно (1 час назад)
        expected_cutoff = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
        assert abs(params[0] - expected_cutoff) < 60000
    
    @pytest.mark.asyncio
    async def test_calculate_depth_metrics(self, repository, mock_db_manager):
        """Тест расчета метрик глубины"""
        # Настраиваем mock результаты
        db_rows = [
            (8, 1500000.0, 1450000.0, 200000.0, 1200000.0, 1100000.0, 150000.0)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.calculate_depth_metrics("BTCUSDT", levels=10)
        
        # Проверяем результат
        assert result['symbol'] == "BTCUSDT"
        assert result['levels'] == 10
        assert result['samples_count'] == 8
        assert result['avg_bid_depth'] == 1500000.0
        assert result['avg_ask_depth'] == 1450000.0
        assert result['bid_depth_std'] == 200000.0
        assert result['ask_depth_std'] == 1200000.0
        assert result['min_total_depth'] == 1100000.0
        assert result['max_total_depth'] == 150000.0
    
    @pytest.mark.asyncio
    async def test_find_order_book_gaps(self, repository, mock_db_manager):
        """Тест поиска пропусков в данных order book"""
        # Настраиваем mock результаты для gap analysis
        base_time = int(time.time() * 1000)
        db_rows = [
            (base_time - 300000, base_time - 60000, 240000),  # 4-минутный пропуск
            (base_time - 600000, base_time - 540000, 60000)   # 1-минутный пропуск
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.find_order_book_gaps("BTCUSDT", max_gap_minutes=2)
        
        # Проверяем результат
        assert len(result) == 2
        assert result[0]['gap_duration_ms'] == 240000
        assert result[1]['gap_duration_ms'] == 60000
    
    @pytest.mark.asyncio
    async def test_get_market_impact_data(self, repository, mock_db_manager):
        """Тест получения данных о влиянии на рынок"""
        # Настраиваем mock результаты
        bids_json = '[{"price": 44999.0, "quantity": 1.5}, {"price": 44998.0, "quantity": 2.0}]'
        asks_json = '[{"price": 45001.0, "quantity": 1.2}, {"price": 45002.0, "quantity": 1.8}]'
        
        db_rows = [
            ("BTCUSDT", int(time.time() * 1000), bids_json, asks_json)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_market_impact_data("BTCUSDT", trade_size=2.0)
        
        # Проверяем результат
        assert len(result) == 1
        assert result[0]['symbol'] == "BTCUSDT"
        assert 'bid_impact' in result[0]
        assert 'ask_impact' in result[0]
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, repository, mock_db_manager, sample_order_book):
        """Тест обработки ошибок подключения"""
        # Настраиваем mock для ошибки подключения
        mock_db_manager.get_connection.side_effect = Exception("Connection failed")
        
        # Выполняем операцию
        result = await repository.save_order_book(sample_order_book)
        
        # Проверяем что операция не удалась
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository, mock_db_manager, sample_order_book):
        """Тест конкурентных операций"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Создаем тестовые order books
        order_books = []
        base_time = int(time.time() * 1000)
        
        for i in range(10):
            book = OrderBook(
                symbol=f"SYMBOL{i}",
                timestamp=base_time + i * 1000,
                bids=sample_order_book.bids,
                asks=sample_order_book.asks
            )
            order_books.append(book)
        
        # Создаем задачи для параллельного выполнения
        tasks = [repository.save_order_book(book) for book in order_books]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        successful_results = [r for r in results if r is True]
        assert len(successful_results) >= 5  # Хотя бы половина должна быть успешной
    
    def test_calculate_liquidity_score(self, repository, sample_order_book):
        """Тест расчета оценки ликвидности"""
        score = repository._calculate_liquidity_score(sample_order_book.bids, sample_order_book.asks)
        
        assert isinstance(score, float)
        assert score > 0
        # Оценка должна учитывать объемы и количество уровней
    
    def test_calculate_spread(self, repository, sample_order_book):
        """Тест расчета спреда"""
        spread = repository._calculate_spread(sample_order_book.bids, sample_order_book.asks)
        
        assert isinstance(spread, float)
        assert spread > 0
        # Спред = лучший ask - лучший bid
        expected_spread = 45001.0 - 44999.0
        assert abs(spread - expected_spread) < 0.01
    
    def test_serialize_order_book_entries(self, repository, sample_order_book):
        """Тест сериализации записей order book"""
        bids_json = repository._serialize_order_book_entries(sample_order_book.bids)
        asks_json = repository._serialize_order_book_entries(sample_order_book.asks)
        
        assert isinstance(bids_json, str)
        assert isinstance(asks_json, str)
        assert "44999.0" in bids_json
        assert "45001.0" in asks_json
    
    def test_deserialize_order_book_entries(self, repository):
        """Тест десериализации записей order book"""
        json_data = '[{"price": 44999.0, "quantity": 1.5, "orders_count": 3}]'
        
        entries = repository._deserialize_order_book_entries(json_data)
        
        assert len(entries) == 1
        assert entries[0].price == 44999.0
        assert entries[0].quantity == 1.5
        assert entries[0].orders_count == 3
    
    def test_convert_db_row_to_order_book(self, repository):
        """Тест конвертации строки БД в order book"""
        timestamp = int(time.time() * 1000)
        bids_json = '[{"price": 44999.0, "quantity": 1.5, "orders_count": 3}]'
        asks_json = '[{"price": 45001.0, "quantity": 1.2, "orders_count": 2}]'
        metadata_json = '{"source": "binance"}'
        
        db_row = ("BTCUSDT", timestamp, bids_json, asks_json, 2.0, 4500.0, metadata_json)
        
        order_book = repository._convert_db_row_to_order_book(db_row)
        
        assert order_book.symbol == "BTCUSDT"
        assert order_book.timestamp == timestamp
        assert len(order_book.bids) == 1
        assert len(order_book.asks) == 1
        assert order_book.spread == 2.0
        assert order_book.liquidity_score == 4500.0
        assert order_book.metadata["source"] == "binance"
    
    def test_prepare_order_book_data(self, repository, sample_order_book):
        """Тест подготовки данных order book для БД"""
        result = repository._prepare_order_book_data(sample_order_book)
        
        assert len(result) == 7
        assert result[0] == "BTCUSDT"
        assert result[1] == sample_order_book.timestamp
        assert isinstance(result[2], str)  # bids_json
        assert isinstance(result[3], str)  # asks_json
        assert isinstance(result[4], float)  # spread
        assert isinstance(result[5], float)  # liquidity_score
        assert isinstance(result[6], str)  # metadata_json