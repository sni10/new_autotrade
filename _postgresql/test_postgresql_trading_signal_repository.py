import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.infrastructure.repositories.postgresql.postgresql_trading_signal_repository import PostgreSQLTradingSignalRepository
from src.domain.entities.trading_signal import TradingSignal, SignalType, SignalSource, SignalConfidence
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


class TestPostgreSQLTradingSignalRepository:
    """Тесты для PostgreSQLTradingSignalRepository"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Фикстура для mock database manager"""
        return MockDatabaseManager()
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Фикстура для создания репозитория"""
        return PostgreSQLTradingSignalRepository(mock_db_manager)
    
    @pytest.fixture
    def sample_signal(self):
        """Фикстура с примером торгового сигнала"""
        return TradingSignal(
            symbol="BTCUSDT",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            confidence=0.85,
            price=45000.0,
            timestamp=int(time.time() * 1000),
            source="macd_analyzer",
            timeframe="1h",
            indicators_data={
                "macd": 150.5,
                "macd_signal": 120.0,
                "rsi": 65.0
            },
            metadata={
                "strategy": "trend_following",
                "risk_level": "medium"
            }
        )
    
    @pytest.mark.asyncio
    async def test_save_signal(self, repository, mock_db_manager, sample_signal):
        """Тест сохранения торгового сигнала"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.save_signal(sample_signal)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван execute
        assert mock_db_manager.cursor.execute.called
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO trading_signals" in query
        assert params[0] == "BTCUSDT"
        assert params[1] == "buy"
        assert params[2] == "strong"
        assert params[3] == 0.85
        assert params[4] == 45000.0
    
    @pytest.mark.asyncio
    async def test_save_signal_failure(self, repository, mock_db_manager, sample_signal):
        """Тест неудачного сохранения сигнала"""
        # Настраиваем mock для ошибки
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.execute.side_effect = Exception("Database error")
        
        # Выполняем операцию
        result = await repository.save_signal(sample_signal)
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_signals_by_symbol(self, repository, mock_db_manager):
        """Тест получения сигналов по символу"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "buy", "strong", 0.85, 45000.0, timestamp, "macd_analyzer", "1h", 
             '{"macd": 150.5}', '{"strategy": "trend"}'),
            ("BTCUSDT", "sell", "medium", 0.70, 45100.0, timestamp + 60000, "rsi_analyzer", "1h",
             '{"rsi": 70.0}', '{"strategy": "reversal"}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_signals_by_symbol("BTCUSDT", limit=10)
        
        # Проверяем результат
        assert len(result) == 2
        assert result[0].symbol == "BTCUSDT"
        assert result[0].signal_type == SignalType.BUY
        assert result[0].strength == SignalStrength.STRONG
        assert result[1].signal_type == SignalType.SELL
        assert result[1].strength == SignalStrength.MEDIUM
    
    @pytest.mark.asyncio
    async def test_get_recent_signals(self, repository, mock_db_manager):
        """Тест получения недавних сигналов"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "buy", "strong", 0.85, 45000.0, timestamp, "macd", "1h", '{}', '{}'),
            ("ETHUSDT", "sell", "medium", 0.70, 3000.0, timestamp - 30000, "rsi", "1h", '{}', '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_recent_signals(minutes=60, limit=20)
        
        # Проверяем результат
        assert len(result) == 2
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "timestamp >" in query
        assert "ORDER BY timestamp DESC" in query
        assert "LIMIT" in query
        # Проверяем что timestamp вычислен корректно (60 минут назад)
        expected_cutoff = int((datetime.now() - timedelta(minutes=60)).timestamp() * 1000)
        assert abs(params[0] - expected_cutoff) < 60000
    
    @pytest.mark.asyncio
    async def test_get_signals_by_type(self, repository, mock_db_manager):
        """Тест получения сигналов по типу"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "buy", "strong", 0.85, 45000.0, timestamp, "macd", "1h", '{}', '{}'),
            ("ETHUSDT", "buy", "medium", 0.75, 3000.0, timestamp + 60000, "rsi", "1h", '{}', '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_signals_by_type(SignalType.BUY, limit=10)
        
        # Проверяем результат
        assert len(result) == 2
        assert all(signal.signal_type == SignalType.BUY for signal in result)
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "signal_type = ?" in query or "signal_type = %s" in query
        assert params[0] == "buy"
    
    @pytest.mark.asyncio
    async def test_get_signals_by_strength(self, repository, mock_db_manager):
        """Тест получения сигналов по силе"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "buy", "strong", 0.90, 45000.0, timestamp, "macd", "1h", '{}', '{}'),
            ("ETHUSDT", "sell", "strong", 0.88, 3000.0, timestamp + 60000, "rsi", "1h", '{}', '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_signals_by_strength(SignalStrength.STRONG, limit=10)
        
        # Проверяем результат
        assert len(result) == 2
        assert all(signal.strength == SignalStrength.STRONG for signal in result)
    
    @pytest.mark.asyncio
    async def test_get_signals_in_time_range(self, repository, mock_db_manager):
        """Тест получения сигналов в временном диапазоне"""
        # Настраиваем mock результаты
        base_time = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "buy", "strong", 0.85, 45000.0, base_time, "macd", "1h", '{}', '{}'),
            ("BTCUSDT", "sell", "medium", 0.70, 45100.0, base_time + 60000, "rsi", "1h", '{}', '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        start_time = base_time - 1000
        end_time = base_time + 120000
        result = await repository.get_signals_in_time_range("BTCUSDT", start_time, end_time)
        
        # Проверяем результат
        assert len(result) == 2
        assert all(signal.symbol == "BTCUSDT" for signal in result)
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "timestamp BETWEEN" in query
        assert params[1] == start_time
        assert params[2] == end_time
    
    @pytest.mark.asyncio
    async def test_delete_old_signals(self, repository, mock_db_manager):
        """Тест удаления старых сигналов"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=50)
        
        # Выполняем операцию
        days_to_keep = 7
        result = await repository.delete_old_signals(days_to_keep)
        
        # Проверяем результат
        assert result == 50
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM trading_signals" in query
        assert "timestamp <" in query
        # Проверяем что timestamp вычислен корректно (7 дней назад)
        expected_cutoff = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
        assert abs(params[0] - expected_cutoff) < 60000
    
    @pytest.mark.asyncio
    async def test_get_signal_statistics(self, repository, mock_db_manager):
        """Тест получения статистики сигналов"""
        # Настраиваем mock результаты
        db_rows = [
            ("BTCUSDT", "buy", 25, 0.82),
            ("BTCUSDT", "sell", 18, 0.78),
            ("BTCUSDT", "hold", 5, 0.65)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_signal_statistics("BTCUSDT", days=30)
        
        # Проверяем результат
        assert result['symbol'] == "BTCUSDT"
        assert result['period_days'] == 30
        assert result['total_signals'] == 48  # 25 + 18 + 5
        assert 'by_type' in result
        assert result['by_type']['buy']['count'] == 25
        assert result['by_type']['sell']['count'] == 18
        assert result['by_type']['hold']['count'] == 5
    
    @pytest.mark.asyncio
    async def test_get_source_performance(self, repository, mock_db_manager):
        """Тест получения производительности источников"""
        # Настраиваем mock результаты
        db_rows = [
            ("macd_analyzer", 150, 0.85, 0.70, 0.95),
            ("rsi_analyzer", 100, 0.78, 0.60, 0.90),
            ("sma_crossover", 75, 0.82, 0.65, 0.92)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_source_performance(days=30)
        
        # Проверяем результат
        assert len(result) == 3
        assert result[0]['source'] == "macd_analyzer"
        assert result[0]['signals_count'] == 150
        assert result[0]['avg_confidence'] == 0.85
        assert result[0]['min_confidence'] == 0.70
        assert result[0]['max_confidence'] == 0.95
    
    @pytest.mark.asyncio
    async def test_batch_save_signals(self, repository, mock_db_manager, sample_signal):
        """Тест пакетного сохранения сигналов"""
        # Создаем тестовые сигналы
        timestamp = int(time.time() * 1000)
        signals = [
            TradingSignal("BTCUSDT", SignalType.BUY, SignalStrength.STRONG, 0.85, 45000.0, timestamp, "macd"),
            TradingSignal("ETHUSDT", SignalType.SELL, SignalStrength.MEDIUM, 0.75, 3000.0, timestamp + 60000, "rsi"),
            TradingSignal("ADAUSDT", SignalType.HOLD, SignalStrength.WEAK, 0.60, 0.5, timestamp + 120000, "sma")
        ]
        
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.executemany = AsyncMock()
        
        # Выполняем операцию
        result = await repository.batch_save_signals(signals)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван executemany
        assert mock_db_manager.cursor.executemany.called
        execute_call = mock_db_manager.cursor.executemany.call_args
        query = execute_call[0][0]
        batch_data = execute_call[0][1]
        
        assert "INSERT INTO trading_signals" in query
        assert len(batch_data) == 3
    
    @pytest.mark.asyncio
    async def test_get_signals_consensus(self, repository, mock_db_manager):
        """Тест получения консенсуса сигналов"""
        # Настраиваем mock результаты
        db_rows = [
            ("buy", 3, 0.83),
            ("sell", 1, 0.70),
            ("hold", 2, 0.65)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_signals_consensus("BTCUSDT", minutes=30)
        
        # Проверяем результат
        assert result['symbol'] == "BTCUSDT"
        assert result['period_minutes'] == 30
        assert result['total_signals'] == 6  # 3 + 1 + 2
        assert result['consensus']['type'] == "buy"  # Наибольшее количество
        assert result['consensus']['count'] == 3
        assert result['consensus']['avg_confidence'] == 0.83
    
    @pytest.mark.asyncio
    async def test_get_high_confidence_signals(self, repository, mock_db_manager):
        """Тест получения сигналов с высокой уверенностью"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("BTCUSDT", "buy", "strong", 0.95, 45000.0, timestamp, "macd", "1h", '{}', '{}'),
            ("ETHUSDT", "sell", "strong", 0.92, 3000.0, timestamp + 60000, "rsi", "1h", '{}', '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_high_confidence_signals(min_confidence=0.90, limit=10)
        
        # Проверяем результат
        assert len(result) == 2
        assert all(signal.confidence >= 0.90 for signal in result)
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "confidence >=" in query
        assert params[0] == 0.90
    
    @pytest.mark.asyncio
    async def test_update_signal_metadata(self, repository, mock_db_manager):
        """Тест обновления метаданных сигнала"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        signal_id = "signal_123"
        new_metadata = {"updated": True, "result": "profitable"}
        result = await repository.update_signal_metadata(signal_id, new_metadata)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "UPDATE trading_signals SET metadata" in query
        assert '"updated": true' in params[0] or '"updated":true' in params[0]
    
    @pytest.mark.asyncio
    async def test_get_symbols_with_signals(self, repository, mock_db_manager):
        """Тест получения символов с сигналами"""
        # Настраиваем mock результаты
        db_rows = [
            ("BTCUSDT", 25),
            ("ETHUSDT", 18),
            ("ADAUSDT", 12)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_symbols_with_signals(hours=24)
        
        # Проверяем результат
        assert len(result) == 3
        assert result[0]['symbol'] == "BTCUSDT"
        assert result[0]['signals_count'] == 25
        assert result[1]['symbol'] == "ETHUSDT"
        assert result[1]['signals_count'] == 18
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, repository, mock_db_manager, sample_signal):
        """Тест обработки ошибок подключения"""
        # Настраиваем mock для ошибки подключения
        mock_db_manager.get_connection.side_effect = Exception("Connection failed")
        
        # Выполняем операцию
        result = await repository.save_signal(sample_signal)
        
        # Проверяем что операция не удалась
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository, mock_db_manager):
        """Тест конкурентных операций"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Создаем тестовые сигналы
        timestamp = int(time.time() * 1000)
        signals = [
            TradingSignal(f"SYMBOL{i}", SignalType.BUY, SignalStrength.MEDIUM, 0.75, 1000.0 + i, timestamp)
            for i in range(10)
        ]
        
        # Создаем задачи для параллельного выполнения
        tasks = [repository.save_signal(signal) for signal in signals]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        successful_results = [r for r in results if r is True]
        assert len(successful_results) >= 5  # Хотя бы половина должна быть успешной
    
    def test_convert_db_row_to_signal(self, repository):
        """Тест конвертации строки БД в сигнал"""
        timestamp = int(time.time() * 1000)
        indicators_json = '{"macd": 150.5, "rsi": 65.0}'
        metadata_json = '{"strategy": "trend_following"}'
        
        db_row = (
            "BTCUSDT", "buy", "strong", 0.85, 45000.0, timestamp, 
            "macd_analyzer", "1h", indicators_json, metadata_json
        )
        
        signal = repository._convert_db_row_to_signal(db_row)
        
        assert signal.symbol == "BTCUSDT"
        assert signal.signal_type == SignalType.BUY
        assert signal.strength == SignalStrength.STRONG
        assert signal.confidence == 0.85
        assert signal.price == 45000.0
        assert signal.timestamp == timestamp
        assert signal.source == "macd_analyzer"
        assert signal.timeframe == "1h"
        assert signal.indicators_data["macd"] == 150.5
        assert signal.metadata["strategy"] == "trend_following"
    
    def test_convert_invalid_signal_type(self, repository):
        """Тест конвертации с невалидным типом сигнала"""
        timestamp = int(time.time() * 1000)
        db_row = (
            "BTCUSDT", "invalid_type", "strong", 0.85, 45000.0, timestamp,
            "macd", "1h", '{}', '{}'
        )
        
        signal = repository._convert_db_row_to_signal(db_row)
        
        # Должен вернуть None для невалидного типа
        assert signal is None
    
    def test_convert_invalid_signal_strength(self, repository):
        """Тест конвертации с невалидной силой сигнала"""
        timestamp = int(time.time() * 1000)
        db_row = (
            "BTCUSDT", "buy", "invalid_strength", 0.85, 45000.0, timestamp,
            "macd", "1h", '{}', '{}'
        )
        
        signal = repository._convert_db_row_to_signal(db_row)
        
        # Должен вернуть None для невалидной силы
        assert signal is None
    
    def test_prepare_signal_data(self, repository, sample_signal):
        """Тест подготовки данных сигнала для БД"""
        result = repository._prepare_signal_data(sample_signal)
        
        expected = (
            "BTCUSDT",
            "buy",
            "strong",
            0.85,
            45000.0,
            sample_signal.timestamp,
            "macd_analyzer",
            "1h",
            '{"macd": 150.5, "macd_signal": 120.0, "rsi": 65.0}',
            '{"strategy": "trend_following", "risk_level": "medium"}'
        )
        
        assert result == expected
    
    def test_calculate_consensus(self, repository):
        """Тест расчета консенсуса"""
        signals_by_type = [
            ("buy", 5, 0.85),
            ("sell", 2, 0.70),
            ("hold", 1, 0.60)
        ]
        
        consensus = repository._calculate_consensus(signals_by_type)
        
        assert consensus['type'] == "buy"
        assert consensus['count'] == 5
        assert consensus['percentage'] == 62.5  # 5/8 * 100
        assert consensus['avg_confidence'] == 0.85