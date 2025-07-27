import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.infrastructure.repositories.postgresql.postgresql_indicator_repository import PostgreSQLIndicatorRepository
from src.domain.entities.indicator_data import IndicatorData, IndicatorType
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


class TestPostgreSQLIndicatorRepository:
    """Тесты для PostgreSQLIndicatorRepository"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Фикстура для mock database manager"""
        return MockDatabaseManager()
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Фикстура для создания репозитория"""
        return PostgreSQLIndicatorRepository(mock_db_manager)
    
    @pytest.fixture
    def sample_indicator(self):
        """Фикстура с примером индикатора"""
        return IndicatorData(
            symbol="BTCUSDT",
            indicator_type=IndicatorType.SMA,
            timeframe="1h",
            period=20,
            value=45000.0,
            timestamp=int(time.time() * 1000),
            metadata={"source": "test", "confidence": 0.95}
        )
    
    @pytest.mark.asyncio
    async def test_save_indicator(self, repository, mock_db_manager, sample_indicator):
        """Тест сохранения индикатора"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.save_indicator(sample_indicator)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван execute
        assert mock_db_manager.cursor.execute.called
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO indicators" in query
        assert "ON CONFLICT" in query
        assert params[0] == "BTCUSDT"
        assert params[1] == "sma"
        assert params[4] == 45000.0
    
    @pytest.mark.asyncio
    async def test_save_indicator_failure(self, repository, mock_db_manager, sample_indicator):
        """Тест неудачного сохранения индикатора"""
        # Настраиваем mock для ошибки
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.execute.side_effect = Exception("Database error")
        
        # Выполняем операцию
        result = await repository.save_indicator(sample_indicator)
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_indicator(self, repository, mock_db_manager, sample_indicator):
        """Тест получения индикатора"""
        # Настраиваем mock результат
        db_row = (
            "BTCUSDT", "sma", "1h", 20, 45000.0, 
            sample_indicator.timestamp, '{"source": "test", "confidence": 0.95}'
        )
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get_indicator("BTCUSDT", IndicatorType.SMA, "1h", 20)
        
        # Проверяем результат
        assert result is not None
        assert result.symbol == "BTCUSDT"
        assert result.indicator_type == IndicatorType.SMA
        assert result.timeframe == "1h"
        assert result.period == 20
        assert result.value == 45000.0
        assert result.metadata["source"] == "test"
    
    @pytest.mark.asyncio
    async def test_get_indicator_not_found(self, repository, mock_db_manager):
        """Тест получения несуществующего индикатора"""
        # Настраиваем mock для пустого результата
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([])
        
        # Выполняем операцию
        result = await repository.get_indicator("NONEXISTENT", IndicatorType.SMA, "1h", 20)
        
        # Проверяем результат
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_indicators_by_symbol(self, repository, mock_db_manager):
        """Тест получения индикаторов по символу"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "sma", "1h", 20, 45000.0, timestamp, '{"test": true}'),
            ("BTCUSDT", "ema", "1h", 10, 45100.0, timestamp, '{"test": true}'),
            ("BTCUSDT", "rsi", "1h", 14, 65.5, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_indicators_by_symbol("BTCUSDT")
        
        # Проверяем результат
        assert len(result) == 3
        assert result[0].indicator_type == IndicatorType.SMA
        assert result[1].indicator_type == IndicatorType.EMA
        assert result[2].indicator_type == IndicatorType.RSI
        assert all(indicator.symbol == "BTCUSDT" for indicator in result)
    
    @pytest.mark.asyncio
    async def test_get_indicators_by_type(self, repository, mock_db_manager):
        """Тест получения индикаторов по типу"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "sma", "1h", 20, 45000.0, timestamp, '{}'),
            ("ETHUSDT", "sma", "1h", 20, 3000.0, timestamp, '{}'),
            ("ADAUSDT", "sma", "1h", 20, 0.5, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_indicators_by_type(IndicatorType.SMA)
        
        # Проверяем результат
        assert len(result) == 3
        assert all(indicator.indicator_type == IndicatorType.SMA for indicator in result)
        symbols = [indicator.symbol for indicator in result]
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols
        assert "ADAUSDT" in symbols
    
    @pytest.mark.asyncio
    async def test_get_indicators_in_time_range(self, repository, mock_db_manager):
        """Тест получения индикаторов в временном диапазоне"""
        # Настраиваем mock результаты
        base_time = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "sma", "1h", 20, 45000.0, base_time, '{}'),
            ("BTCUSDT", "sma", "1h", 20, 45100.0, base_time + 3600000, '{}'),
            ("BTCUSDT", "sma", "1h", 20, 45200.0, base_time + 7200000, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        start_time = base_time - 1000
        end_time = base_time + 10000000
        result = await repository.get_indicators_in_time_range("BTCUSDT", start_time, end_time)
        
        # Проверяем результат
        assert len(result) == 3
        assert all(indicator.symbol == "BTCUSDT" for indicator in result)
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "timestamp BETWEEN" in query
        assert params[1] == start_time
        assert params[2] == end_time
    
    @pytest.mark.asyncio
    async def test_delete_indicator(self, repository, mock_db_manager):
        """Тест удаления индикатора"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.delete_indicator("BTCUSDT", IndicatorType.SMA, "1h", 20)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM indicators" in query
        assert params[0] == "BTCUSDT"
        assert params[1] == "sma"
        assert params[2] == "1h"
        assert params[3] == 20
    
    @pytest.mark.asyncio
    async def test_delete_indicator_not_found(self, repository, mock_db_manager):
        """Тест удаления несуществующего индикатора"""
        # Настраиваем mock для отсутствия изменений
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=0)
        
        # Выполняем операцию
        result = await repository.delete_indicator("NONEXISTENT", IndicatorType.SMA, "1h", 20)
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_old_indicators(self, repository, mock_db_manager):
        """Тест очистки старых индикаторов"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=15)
        
        # Выполняем операцию
        days_to_keep = 30
        result = await repository.cleanup_old_indicators(days_to_keep)
        
        # Проверяем результат
        assert result == 15
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM indicators" in query
        assert "timestamp <" in query
        # Проверяем что timestamp вычислен корректно (30 дней назад)
        expected_cutoff = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
        assert abs(params[0] - expected_cutoff) < 60000  # Допускаем погрешность в 1 минуту
    
    @pytest.mark.asyncio
    async def test_batch_save_indicators(self, repository, mock_db_manager):
        """Тест пакетного сохранения индикаторов"""
        # Создаем тестовые индикаторы
        timestamp = int(time.time() * 1000)
        indicators = [
            IndicatorData("BTCUSDT", IndicatorType.SMA, "1h", 20, 45000.0, timestamp),
            IndicatorData("BTCUSDT", IndicatorType.EMA, "1h", 10, 45100.0, timestamp),
            IndicatorData("ETHUSDT", IndicatorType.RSI, "1h", 14, 65.5, timestamp)
        ]
        
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.executemany = AsyncMock()
        
        # Выполняем операцию
        result = await repository.batch_save_indicators(indicators)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван executemany
        assert mock_db_manager.cursor.executemany.called
        execute_call = mock_db_manager.cursor.executemany.call_args
        query = execute_call[0][0]
        batch_data = execute_call[0][1]
        
        assert "INSERT INTO indicators" in query
        assert len(batch_data) == 3
    
    @pytest.mark.asyncio
    async def test_get_latest_indicators(self, repository, mock_db_manager):
        """Тест получения последних индикаторов"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "sma", "1h", 20, 45200.0, timestamp, '{}'),
            ("ETHUSDT", "sma", "1h", 20, 3100.0, timestamp - 1000, '{}'),
            ("ADAUSDT", "sma", "1h", 20, 0.52, timestamp - 2000, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_latest_indicators(IndicatorType.SMA, limit=3)
        
        # Проверяем результат
        assert len(result) == 3
        assert all(indicator.indicator_type == IndicatorType.SMA for indicator in result)
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "ORDER BY timestamp DESC" in query
        assert "LIMIT" in query
        assert params[0] == "sma"
        assert params[1] == 3
    
    @pytest.mark.asyncio
    async def test_get_indicator_statistics(self, repository, mock_db_manager):
        """Тест получения статистики индикаторов"""
        # Настраиваем mock результаты
        db_rows = [
            ("BTCUSDT", 150, 44000.0, 46000.0, 45000.0, 500.0)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_indicator_statistics("BTCUSDT", IndicatorType.SMA)
        
        # Проверяем результат
        assert result['symbol'] == "BTCUSDT"
        assert result['total_count'] == 150
        assert result['min_value'] == 44000.0
        assert result['max_value'] == 46000.0
        assert result['avg_value'] == 45000.0
        assert result['std_dev'] == 500.0
    
    @pytest.mark.asyncio
    async def test_get_indicators_for_analysis(self, repository, mock_db_manager):
        """Тест получения индикаторов для анализа"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "sma", "1h", 20, 45000.0, timestamp, '{}'),
            ("BTCUSDT", "ema", "1h", 10, 45100.0, timestamp, '{}'),
            ("BTCUSDT", "rsi", "1h", 14, 65.5, timestamp, '{}'),
            ("BTCUSDT", "macd", "1h", 12, 150.0, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        indicator_types = [IndicatorType.SMA, IndicatorType.EMA, IndicatorType.RSI]
        result = await repository.get_indicators_for_analysis("BTCUSDT", "1h", indicator_types)
        
        # Проверяем результат
        assert len(result) == 3  # MACD не включен в запрашиваемые типы
        types_in_result = [indicator.indicator_type for indicator in result]
        assert IndicatorType.SMA in types_in_result
        assert IndicatorType.EMA in types_in_result
        assert IndicatorType.RSI in types_in_result
    
    @pytest.mark.asyncio
    async def test_update_indicator_metadata(self, repository, mock_db_manager):
        """Тест обновления метаданных индикатора"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        new_metadata = {"updated": True, "confidence": 0.98}
        result = await repository.update_indicator_metadata(
            "BTCUSDT", IndicatorType.SMA, "1h", 20, new_metadata
        )
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "UPDATE indicators SET metadata" in query
        assert '"updated": true' in params[0] or '"updated":true' in params[0]
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, repository, mock_db_manager):
        """Тест обработки ошибок подключения"""
        # Настраиваем mock для ошибки подключения
        mock_db_manager.get_connection.side_effect = Exception("Connection failed")
        
        # Создаем тестовый индикатор
        indicator = IndicatorData("BTCUSDT", IndicatorType.SMA, "1h", 20, 45000.0, int(time.time() * 1000))
        
        # Выполняем операцию
        result = await repository.save_indicator(indicator)
        
        # Проверяем что операция не удалась
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_indicators_summary(self, repository, mock_db_manager):
        """Тест получения сводки по индикаторам"""
        # Настраиваем mock результаты
        db_rows = [
            ("sma", 500),
            ("ema", 300),
            ("rsi", 200),
            ("macd", 150)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_indicators_summary()
        
        # Проверяем результат
        assert len(result) == 4
        assert result['sma'] == 500
        assert result['ema'] == 300
        assert result['rsi'] == 200
        assert result['macd'] == 150
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        
        assert "GROUP BY indicator_type" in query
        assert "COUNT(*)" in query
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository, mock_db_manager):
        """Тест конкурентных операций"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Создаем тестовые индикаторы
        timestamp = int(time.time() * 1000)
        indicators = [
            IndicatorData(f"SYMBOL{i}", IndicatorType.SMA, "1h", 20, 1000.0 + i, timestamp)
            for i in range(10)
        ]
        
        # Создаем задачи для параллельного выполнения
        tasks = [repository.save_indicator(indicator) for indicator in indicators]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        successful_results = [r for r in results if r is True]
        assert len(successful_results) >= 5  # Хотя бы половина должна быть успешной
    
    @pytest.mark.asyncio
    async def test_invalid_indicator_type_handling(self, repository, mock_db_manager):
        """Тест обработки невалидного типа индикатора"""
        # Настраиваем mock результат с невалидным типом
        db_row = ("BTCUSDT", "invalid_type", "1h", 20, 45000.0, int(time.time() * 1000), '{}')
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get_indicator("BTCUSDT", IndicatorType.SMA, "1h", 20)
        
        # Результат должен быть None из-за невалидного типа
        assert result is None
    
    def test_convert_db_row_to_indicator(self, repository):
        """Тест конвертации строки БД в индикатор"""
        timestamp = int(time.time() * 1000)
        db_row = ("BTCUSDT", "sma", "1h", 20, 45000.0, timestamp, '{"source": "test"}')
        
        indicator = repository._convert_db_row_to_indicator(db_row)
        
        assert indicator.symbol == "BTCUSDT"
        assert indicator.indicator_type == IndicatorType.SMA
        assert indicator.timeframe == "1h"
        assert indicator.period == 20
        assert indicator.value == 45000.0
        assert indicator.timestamp == timestamp
        assert indicator.metadata["source"] == "test"
    
    def test_convert_invalid_db_row(self, repository):
        """Тест конвертации невалидной строки БД"""
        # Строка с невалидным типом индикатора
        db_row = ("BTCUSDT", "invalid_type", "1h", 20, 45000.0, int(time.time() * 1000), '{}')
        
        indicator = repository._convert_db_row_to_indicator(db_row)
        
        # Должен вернуть None для невалидного типа
        assert indicator is None
    
    def test_prepare_indicator_data(self, repository, sample_indicator):
        """Тест подготовки данных индикатора для БД"""
        result = repository._prepare_indicator_data(sample_indicator)
        
        expected = (
            "BTCUSDT",
            "sma",
            "1h",
            20,
            45000.0,
            sample_indicator.timestamp,
            '{"source": "test", "confidence": 0.95}'
        )
        
        assert result == expected