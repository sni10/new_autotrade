import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.infrastructure.repositories.postgresql.postgresql_statistics_repository import PostgreSQLStatisticsRepository
from src.domain.entities.statistics import Statistics, StatisticType, StatisticCategory
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


class TestPostgreSQLStatisticsRepository:
    """Тесты для PostgreSQLStatisticsRepository"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Фикстура для mock database manager"""
        return MockDatabaseManager()
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Фикстура для создания репозитория"""
        return PostgreSQLStatisticsRepository(mock_db_manager)
    
    @pytest.fixture
    def sample_counter_statistic(self):
        """Фикстура с примером счетчика"""
        return Statistics(
            metric_name="orders_processed",
            metric_type=StatisticType.COUNTER,
            category=StatisticCategory.TRADING,
            value=150.0,
            timestamp=int(time.time() * 1000),
            labels={"symbol": "BTCUSDT", "side": "BUY"},
            metadata={"source": "order_service", "version": "1.0"}
        )
    
    @pytest.fixture
    def sample_gauge_statistic(self):
        """Фикстура с примером gauge"""
        return Statistics(
            metric_name="account_balance",
            metric_type=StatisticType.GAUGE,
            category=StatisticCategory.ACCOUNT,
            value=15000.50,
            timestamp=int(time.time() * 1000),
            labels={"currency": "USDT"},
            metadata={"exchange": "binance"}
        )
    
    @pytest.fixture
    def sample_timing_statistic(self):
        """Фикстура с примером timing"""
        return Statistics(
            metric_name="api_response_time",
            metric_type=StatisticType.TIMING,
            category=StatisticCategory.PERFORMANCE,
            value=125.5,
            timestamp=int(time.time() * 1000),
            labels={"endpoint": "/api/orders", "method": "POST"},
            metadata={"service": "exchange_connector"}
        )
    
    @pytest.mark.asyncio
    async def test_record_statistic(self, repository, mock_db_manager, sample_counter_statistic):
        """Тест записи статистики"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.record_statistic(sample_counter_statistic)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван execute
        assert mock_db_manager.cursor.execute.called
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO statistics" in query
        assert params[0] == "orders_processed"
        assert params[1] == "counter"
        assert params[2] == "trading"
        assert params[3] == 150.0
    
    @pytest.mark.asyncio
    async def test_record_statistic_failure(self, repository, mock_db_manager, sample_counter_statistic):
        """Тест неудачной записи статистики"""
        # Настраиваем mock для ошибки
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.execute.side_effect = Exception("Database error")
        
        # Выполняем операцию
        result = await repository.record_statistic(sample_counter_statistic)
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_increment_counter(self, repository, mock_db_manager):
        """Тест инкремента счетчика"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.increment_counter(
            "api_calls", 
            StatisticCategory.SYSTEM,
            labels={"endpoint": "/api/ticker"},
            increment=5
        )
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO statistics" in query
        assert "ON CONFLICT" in query
        assert "SET value = value +" in query or "SET value = statistics.value +" in query
        assert params[0] == "api_calls"
        assert params[1] == "counter"
        assert params[2] == "system"
        assert params[3] == 5
    
    @pytest.mark.asyncio
    async def test_update_gauge(self, repository, mock_db_manager):
        """Тест обновления gauge"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.update_gauge(
            "memory_usage_mb",
            StatisticCategory.PERFORMANCE,
            256.8,
            labels={"component": "trading_engine"}
        )
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO statistics" in query
        assert "ON CONFLICT" in query
        assert "SET value =" in query
        assert params[0] == "memory_usage_mb"
        assert params[1] == "gauge"
        assert params[2] == "performance"
        assert params[3] == 256.8
    
    @pytest.mark.asyncio
    async def test_record_timing(self, repository, mock_db_manager):
        """Тест записи timing метрики"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.record_timing(
            "database_query_time",
            StatisticCategory.PERFORMANCE,
            95.5,
            labels={"table": "orders", "operation": "SELECT"}
        )
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO statistics" in query
        assert params[0] == "database_query_time"
        assert params[1] == "timing"
        assert params[2] == "performance"
        assert params[3] == 95.5
    
    @pytest.mark.asyncio
    async def test_get_statistics_by_metric(self, repository, mock_db_manager):
        """Тест получения статистики по метрике"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("orders_processed", "counter", "trading", 150.0, timestamp, 
             '{"symbol": "BTCUSDT"}', '{"source": "order_service"}'),
            ("orders_processed", "counter", "trading", 175.0, timestamp + 60000,
             '{"symbol": "BTCUSDT"}', '{"source": "order_service"}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_statistics_by_metric("orders_processed", limit=10)
        
        # Проверяем результат
        assert len(result) == 2
        assert result[0].metric_name == "orders_processed"
        assert result[0].metric_type == StatisticType.COUNTER
        assert result[0].category == StatisticCategory.TRADING
        assert result[0].value == 150.0
        assert result[1].value == 175.0
    
    @pytest.mark.asyncio
    async def test_get_statistics_by_category(self, repository, mock_db_manager):
        """Тест получения статистики по категории"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("orders_count", "counter", "trading", 50.0, timestamp, '{}', '{}'),
            ("profit_amount", "gauge", "trading", 1250.75, timestamp, '{}', '{}'),
            ("trade_duration", "timing", "trading", 125.5, timestamp, '{}', '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_statistics_by_category(StatisticCategory.TRADING, limit=20)
        
        # Проверяем результат
        assert len(result) == 3
        assert all(stat.category == StatisticCategory.TRADING for stat in result)
        metric_names = [stat.metric_name for stat in result]
        assert "orders_count" in metric_names
        assert "profit_amount" in metric_names
        assert "trade_duration" in metric_names
    
    @pytest.mark.asyncio
    async def test_get_statistics_in_time_range(self, repository, mock_db_manager):
        """Тест получения статистики в временном диапазоне"""
        # Настраиваем mock результаты
        base_time = int(time.time() * 1000)
        db_rows = [
            ("cpu_usage", "gauge", "performance", 75.5, base_time, '{}', '{}'),
            ("cpu_usage", "gauge", "performance", 80.2, base_time + 60000, '{}', '{}'),
            ("cpu_usage", "gauge", "performance", 78.8, base_time + 120000, '{}', '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        start_time = base_time - 1000
        end_time = base_time + 180000
        result = await repository.get_statistics_in_time_range("cpu_usage", start_time, end_time)
        
        # Проверяем результат
        assert len(result) == 3
        assert all(stat.metric_name == "cpu_usage" for stat in result)
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "timestamp BETWEEN" in query
        assert params[1] == start_time
        assert params[2] == end_time
    
    @pytest.mark.asyncio
    async def test_get_aggregated_statistics(self, repository, mock_db_manager):
        """Тест получения агрегированной статистики"""
        # Настраиваем mock результаты
        db_rows = [
            (15, 75.5, 60.0, 90.0, 8.5)  # count, avg, min, max, stddev
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_aggregated_statistics("cpu_usage", hours=24)
        
        # Проверяем результат
        assert result['metric_name'] == "cpu_usage"
        assert result['period_hours'] == 24
        assert result['count'] == 15
        assert result['avg'] == 75.5
        assert result['min'] == 60.0
        assert result['max'] == 90.0
        assert result['stddev'] == 8.5
    
    @pytest.mark.asyncio
    async def test_delete_old_statistics(self, repository, mock_db_manager):
        """Тест удаления старой статистики"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=100)
        
        # Выполняем операцию
        days_to_keep = 30
        result = await repository.delete_old_statistics(days_to_keep)
        
        # Проверяем результат
        assert result == 100
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM statistics" in query
        assert "timestamp <" in query
        # Проверяем что timestamp вычислен корректно (30 дней назад)
        expected_cutoff = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
        assert abs(params[0] - expected_cutoff) < 60000
    
    @pytest.mark.asyncio
    async def test_get_latest_gauge_values(self, repository, mock_db_manager):
        """Тест получения последних значений gauge"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("memory_usage", 256.8, timestamp),
            ("cpu_usage", 75.5, timestamp - 30000),
            ("disk_usage", 45.2, timestamp - 60000)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_latest_gauge_values(StatisticCategory.PERFORMANCE)
        
        # Проверяем результат
        assert len(result) == 3
        assert result[0]['metric_name'] == "memory_usage"
        assert result[0]['value'] == 256.8
        assert result[1]['metric_name'] == "cpu_usage"
        assert result[1]['value'] == 75.5
    
    @pytest.mark.asyncio
    async def test_batch_record_statistics(self, repository, mock_db_manager, sample_counter_statistic, sample_gauge_statistic):
        """Тест пакетной записи статистики"""
        # Создаем тестовую статистику
        statistics = [
            sample_counter_statistic,
            sample_gauge_statistic,
            Statistics("api_calls", StatisticType.COUNTER, StatisticCategory.SYSTEM, 25.0, int(time.time() * 1000))
        ]
        
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.executemany = AsyncMock()
        
        # Выполняем операцию
        result = await repository.batch_record_statistics(statistics)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван executemany
        assert mock_db_manager.cursor.executemany.called
        execute_call = mock_db_manager.cursor.executemany.call_args
        query = execute_call[0][0]
        batch_data = execute_call[0][1]
        
        assert "INSERT INTO statistics" in query
        assert len(batch_data) == 3
    
    @pytest.mark.asyncio
    async def test_get_metric_trend(self, repository, mock_db_manager):
        """Тест получения трендов метрики"""
        # Настраиваем mock результаты
        base_time = int(time.time() * 1000)
        db_rows = [
            (base_time - 7200000, 70.0),     # 2 часа назад
            (base_time - 3600000, 75.5),     # 1 час назад
            (base_time, 80.2)                # сейчас
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_metric_trend("cpu_usage", hours=24, interval_minutes=60)
        
        # Проверяем результат
        assert len(result) == 3
        assert result[0]['timestamp'] == base_time - 7200000
        assert result[0]['value'] == 70.0
        assert result[2]['value'] == 80.2
    
    @pytest.mark.asyncio
    async def test_get_counter_increments(self, repository, mock_db_manager):
        """Тест получения инкрементов счетчика"""
        # Настраиваем mock результаты
        base_time = int(time.time() * 1000)
        db_rows = [
            (base_time - 3600000, 100.0),
            (base_time - 1800000, 150.0),  # +50
            (base_time, 225.0)             # +75
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_counter_increments("orders_processed", hours=2)
        
        # Проверяем результат
        assert len(result) == 2  # Один элемент меньше (первый период не имеет предыдущего значения)
        assert result[0]['increment'] == 50.0  # 150 - 100
        assert result[1]['increment'] == 75.0  # 225 - 150
    
    @pytest.mark.asyncio
    async def test_get_statistics_summary(self, repository, mock_db_manager):
        """Тест получения сводки статистики"""
        # Настраиваем mock результаты
        db_rows = [
            ("trading", "counter", 5),
            ("trading", "gauge", 3),
            ("performance", "timing", 8),
            ("system", "counter", 12)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_statistics_summary()
        
        # Проверяем результат
        assert len(result) == 4
        trading_counters = next((item for item in result if item['category'] == 'trading' and item['type'] == 'counter'), None)
        assert trading_counters is not None
        assert trading_counters['count'] == 5
    
    @pytest.mark.asyncio
    async def test_calculate_percentiles(self, repository, mock_db_manager):
        """Тест расчета процентилей"""
        # Настраиваем mock результаты для процентилей
        db_rows = [
            (50.0, 75.0, 90.0, 95.0, 99.0)  # p50, p75, p90, p95, p99
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.calculate_percentiles("api_response_time", hours=24)
        
        # Проверяем результат
        assert result['metric_name'] == "api_response_time"
        assert result['period_hours'] == 24
        assert result['p50'] == 50.0
        assert result['p75'] == 75.0
        assert result['p90'] == 90.0
        assert result['p95'] == 95.0
        assert result['p99'] == 99.0
    
    @pytest.mark.asyncio
    async def test_get_metrics_by_labels(self, repository, mock_db_manager):
        """Тест получения метрик по лейблам"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("orders_count", "counter", "trading", 25.0, timestamp, 
             '{"symbol": "BTCUSDT", "side": "BUY"}', '{}'),
            ("orders_count", "counter", "trading", 18.0, timestamp,
             '{"symbol": "BTCUSDT", "side": "SELL"}', '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_metrics_by_labels({"symbol": "BTCUSDT"})
        
        # Проверяем результат
        assert len(result) == 2
        assert all("BTCUSDT" in stat.labels.get("symbol", "") for stat in result)
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, repository, mock_db_manager, sample_counter_statistic):
        """Тест обработки ошибок подключения"""
        # Настраиваем mock для ошибки подключения
        mock_db_manager.get_connection.side_effect = Exception("Connection failed")
        
        # Выполняем операцию
        result = await repository.record_statistic(sample_counter_statistic)
        
        # Проверяем что операция не удалась
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository, mock_db_manager):
        """Тест конкурентных операций"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Создаем тестовую статистику
        timestamp = int(time.time() * 1000)
        statistics = [
            Statistics(f"metric_{i}", StatisticType.COUNTER, StatisticCategory.SYSTEM, float(i), timestamp)
            for i in range(10)
        ]
        
        # Создаем задачи для параллельного выполнения
        tasks = [repository.record_statistic(stat) for stat in statistics]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        successful_results = [r for r in results if r is True]
        assert len(successful_results) >= 5  # Хотя бы половина должна быть успешной
    
    def test_convert_db_row_to_statistic(self, repository):
        """Тест конвертации строки БД в статистику"""
        timestamp = int(time.time() * 1000)
        labels_json = '{"symbol": "BTCUSDT", "side": "BUY"}'
        metadata_json = '{"source": "order_service"}'
        
        db_row = (
            "orders_processed", "counter", "trading", 150.0, timestamp,
            labels_json, metadata_json
        )
        
        statistic = repository._convert_db_row_to_statistic(db_row)
        
        assert statistic.metric_name == "orders_processed"
        assert statistic.metric_type == StatisticType.COUNTER
        assert statistic.category == StatisticCategory.TRADING
        assert statistic.value == 150.0
        assert statistic.timestamp == timestamp
        assert statistic.labels["symbol"] == "BTCUSDT"
        assert statistic.metadata["source"] == "order_service"
    
    def test_convert_invalid_statistic_type(self, repository):
        """Тест конвертации с невалидным типом статистики"""
        timestamp = int(time.time() * 1000)
        db_row = (
            "metric", "invalid_type", "system", 100.0, timestamp, '{}', '{}'
        )
        
        statistic = repository._convert_db_row_to_statistic(db_row)
        
        # Должен вернуть None для невалидного типа
        assert statistic is None
    
    def test_convert_invalid_statistic_category(self, repository):
        """Тест конвертации с невалидной категорией статистики"""
        timestamp = int(time.time() * 1000)
        db_row = (
            "metric", "counter", "invalid_category", 100.0, timestamp, '{}', '{}'
        )
        
        statistic = repository._convert_db_row_to_statistic(db_row)
        
        # Должен вернуть None для невалидной категории
        assert statistic is None
    
    def test_prepare_statistic_data(self, repository, sample_counter_statistic):
        """Тест подготовки данных статистики для БД"""
        result = repository._prepare_statistic_data(sample_counter_statistic)
        
        expected = (
            "orders_processed",
            "counter",
            "trading",
            150.0,
            sample_counter_statistic.timestamp,
            '{"symbol": "BTCUSDT", "side": "BUY"}',
            '{"source": "order_service", "version": "1.0"}'
        )
        
        assert result == expected
    
    def test_calculate_increments(self, repository):
        """Тест расчета инкрементов"""
        data_points = [
            {'timestamp': 1000, 'value': 100.0},
            {'timestamp': 2000, 'value': 150.0},
            {'timestamp': 3000, 'value': 225.0}
        ]
        
        increments = repository._calculate_increments(data_points)
        
        assert len(increments) == 2
        assert increments[0]['increment'] == 50.0  # 150 - 100
        assert increments[1]['increment'] == 75.0  # 225 - 150
        assert increments[0]['timestamp'] == 2000
        assert increments[1]['timestamp'] == 3000