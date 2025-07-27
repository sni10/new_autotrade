import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.infrastructure.repositories.postgresql.postgresql_cache_repository import PostgreSQLCacheRepository
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


class TestPostgreSQLCacheRepository:
    """Тесты для PostgreSQLCacheRepository"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Фикстура для mock database manager"""
        return MockDatabaseManager()
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Фикстура для создания репозитория"""
        return PostgreSQLCacheRepository(mock_db_manager)
    
    @pytest.mark.asyncio
    async def test_set_cache_string(self, repository, mock_db_manager):
        """Тест сохранения строкового значения в кэш"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.set("test_key", "test_value", ttl_seconds=3600)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван execute
        assert mock_db_manager.cursor.execute.called
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO cache" in query
        assert "ON CONFLICT" in query
        assert params[0] == "test_key"
        assert params[1] == "test_value"
        assert params[2] == "string"
    
    @pytest.mark.asyncio
    async def test_set_cache_dict(self, repository, mock_db_manager):
        """Тест сохранения словаря в кэш"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        test_data = {"symbol": "BTCUSDT", "price": 45000.0}
        result = await repository.set("price_data", test_data, ttl_seconds=1800)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        params = execute_call[0][1]
        
        assert params[0] == "price_data"
        assert '"symbol": "BTCUSDT"' in params[1] or '"symbol":"BTCUSDT"' in params[1]
        assert params[2] == "json"
    
    @pytest.mark.asyncio
    async def test_set_cache_list(self, repository, mock_db_manager):
        """Тест сохранения списка в кэш"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        test_data = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        result = await repository.set("trading_pairs", test_data)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        params = execute_call[0][1]
        
        assert params[0] == "trading_pairs"
        assert params[2] == "json"
    
    @pytest.mark.asyncio
    async def test_set_cache_failure(self, repository, mock_db_manager):
        """Тест неудачного сохранения в кэш"""
        # Настраиваем mock для ошибки
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.execute.side_effect = Exception("Database error")
        
        # Выполняем операцию
        result = await repository.set("test_key", "test_value")
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_cache_string(self, repository, mock_db_manager):
        """Тест получения строкового значения из кэша"""
        # Настраиваем mock результат
        current_time = int(time.time() * 1000)
        expiry_time = current_time + 3600000  # Через час
        db_row = ("test_key", "test_value", "string", current_time, expiry_time)
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get("test_key")
        
        # Проверяем результат
        assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_cache_json(self, repository, mock_db_manager):
        """Тест получения JSON значения из кэша"""
        # Настраиваем mock результат
        current_time = int(time.time() * 1000)
        expiry_time = current_time + 3600000
        json_value = '{"symbol": "BTCUSDT", "price": 45000.0}'
        db_row = ("price_data", json_value, "json", current_time, expiry_time)
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get("price_data")
        
        # Проверяем результат
        assert isinstance(result, dict)
        assert result["symbol"] == "BTCUSDT"
        assert result["price"] == 45000.0
    
    @pytest.mark.asyncio
    async def test_get_cache_expired(self, repository, mock_db_manager):
        """Тест получения истекшего значения из кэша"""
        # Настраиваем mock результат с истекшим TTL
        current_time = int(time.time() * 1000)
        expiry_time = current_time - 3600000  # Час назад (истек)
        db_row = ("test_key", "test_value", "string", current_time - 7200000, expiry_time)
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get("test_key")
        
        # Проверяем результат
        assert result is None
        
        # Проверяем что была попытка удалить истекшие записи
        assert mock_db_manager.cursor.execute.call_count >= 2  # SELECT + DELETE
    
    @pytest.mark.asyncio
    async def test_get_cache_not_found(self, repository, mock_db_manager):
        """Тест получения несуществующего значения из кэша"""
        # Настраиваем mock для пустого результата
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([])
        
        # Выполняем операцию
        result = await repository.get("nonexistent_key")
        
        # Проверяем результат
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_cache(self, repository, mock_db_manager):
        """Тест удаления значения из кэша"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.delete("test_key")
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM cache" in query
        assert "WHERE key =" in query
        assert params[0] == "test_key"
    
    @pytest.mark.asyncio
    async def test_delete_cache_not_found(self, repository, mock_db_manager):
        """Тест удаления несуществующего значения из кэша"""
        # Настраиваем mock для отсутствия изменений
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=0)
        
        # Выполняем операцию
        result = await repository.delete("nonexistent_key")
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_exists(self, repository, mock_db_manager):
        """Тест проверки существования ключа в кэше"""
        # Настраиваем mock результат
        current_time = int(time.time() * 1000)
        expiry_time = current_time + 3600000
        db_row = (1,)  # COUNT result
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.exists("test_key")
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        
        assert "COUNT(*)" in query
        assert "WHERE key =" in query
        assert "AND (expires_at IS NULL OR expires_at >" in query
    
    @pytest.mark.asyncio
    async def test_exists_false(self, repository, mock_db_manager):
        """Тест проверки несуществующего ключа в кэше"""
        # Настраиваем mock результат
        db_row = (0,)  # COUNT result = 0
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.exists("nonexistent_key")
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_clear_all(self, repository, mock_db_manager):
        """Тест очистки всего кэша"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=10)
        
        # Выполняем операцию
        result = await repository.clear_all()
        
        # Проверяем результат
        assert result == 10
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        
        assert "DELETE FROM cache" in query
        assert "WHERE" not in query  # Удаляем все записи
    
    @pytest.mark.asyncio
    async def test_clear_expired(self, repository, mock_db_manager):
        """Тест очистки истекших записей кэша"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=5)
        
        # Выполняем операцию
        result = await repository.clear_expired()
        
        # Проверяем результат
        assert result == 5
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM cache" in query
        assert "WHERE expires_at IS NOT NULL AND expires_at <" in query
        # Проверяем что используется текущее время
        current_time = int(time.time() * 1000)
        assert abs(params[0] - current_time) < 5000  # Допускаем погрешность в 5 секунд
    
    @pytest.mark.asyncio
    async def test_get_keys_by_pattern(self, repository, mock_db_manager):
        """Тест получения ключей по паттерну"""
        # Настраиваем mock результаты
        db_rows = [
            ("user:123",),
            ("user:456",),
            ("user:789",)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_keys_by_pattern("user:%")
        
        # Проверяем результат
        assert len(result) == 3
        assert "user:123" in result
        assert "user:456" in result
        assert "user:789" in result
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "SELECT key FROM cache" in query
        assert "LIKE" in query or "ILIKE" in query
        assert params[0] == "user:%"
    
    @pytest.mark.asyncio
    async def test_batch_set(self, repository, mock_db_manager):
        """Тест пакетного сохранения в кэш"""
        # Подготавливаем данные
        batch_data = {
            "key1": "value1",
            "key2": {"nested": "object"},
            "key3": ["list", "items"]
        }
        
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.executemany = AsyncMock()
        
        # Выполняем операцию
        result = await repository.batch_set(batch_data, ttl_seconds=3600)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван executemany
        assert mock_db_manager.cursor.executemany.called
        execute_call = mock_db_manager.cursor.executemany.call_args
        query = execute_call[0][0]
        batch_params = execute_call[0][1]
        
        assert "INSERT INTO cache" in query
        assert len(batch_params) == 3
    
    @pytest.mark.asyncio
    async def test_batch_get(self, repository, mock_db_manager):
        """Тест пакетного получения из кэша"""
        # Настраиваем mock результаты
        current_time = int(time.time() * 1000)
        expiry_time = current_time + 3600000
        db_rows = [
            ("key1", "value1", "string", current_time, expiry_time),
            ("key2", '{"nested": "object"}', "json", current_time, expiry_time)
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        keys = ["key1", "key2", "key3"]  # key3 не существует
        result = await repository.batch_get(keys)
        
        # Проверяем результат
        assert len(result) == 3
        assert result["key1"] == "value1"
        assert result["key2"]["nested"] == "object"
        assert result["key3"] is None
    
    @pytest.mark.asyncio
    async def test_batch_delete(self, repository, mock_db_manager):
        """Тест пакетного удаления из кэша"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=2)
        
        # Выполняем операцию
        keys = ["key1", "key2", "key3"]
        result = await repository.batch_delete(keys)
        
        # Проверяем результат
        assert result == 2
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM cache" in query
        assert "WHERE key = ANY" in query or "WHERE key IN" in query
    
    @pytest.mark.asyncio
    async def test_get_cache_statistics(self, repository, mock_db_manager):
        """Тест получения статистики кэша"""
        # Настраиваем mock результаты
        db_rows = [
            (150, 25, 125)  # total_entries, expired_entries, active_entries
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_cache_statistics()
        
        # Проверяем результат
        assert result['total_entries'] == 150
        assert result['expired_entries'] == 25
        assert result['active_entries'] == 125
        assert result['hit_ratio'] is not None
    
    @pytest.mark.asyncio
    async def test_get_ttl(self, repository, mock_db_manager):
        """Тест получения времени жизни ключа"""
        # Настраиваем mock результат
        current_time = int(time.time() * 1000)
        expiry_time = current_time + 3600000  # Истекает через час
        db_row = (expiry_time,)
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get_ttl("test_key")
        
        # Проверяем результат
        assert result is not None
        assert abs(result - 3600) < 5  # Примерно час, допускаем погрешность
    
    @pytest.mark.asyncio
    async def test_get_ttl_no_expiry(self, repository, mock_db_manager):
        """Тест получения TTL для ключа без истечения"""
        # Настраиваем mock результат
        db_row = (None,)  # expires_at = NULL
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get_ttl("test_key")
        
        # Проверяем результат
        assert result == -1  # Специальное значение для ключей без истечения
    
    @pytest.mark.asyncio
    async def test_get_ttl_not_found(self, repository, mock_db_manager):
        """Тест получения TTL для несуществующего ключа"""
        # Настраиваем mock для пустого результата
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([])
        
        # Выполняем операцию
        result = await repository.get_ttl("nonexistent_key")
        
        # Проверяем результат
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_ttl(self, repository, mock_db_manager):
        """Тест установки TTL для существующего ключа"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.set_ttl("test_key", 7200)  # 2 часа
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "UPDATE cache SET expires_at =" in query
        assert "WHERE key =" in query
        assert params[1] == "test_key"
        # Проверяем что expires_at установлен корректно
        current_time = int(time.time() * 1000)
        expected_expiry = current_time + 7200 * 1000
        assert abs(params[0] - expected_expiry) < 5000
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, repository, mock_db_manager):
        """Тест обработки ошибок подключения"""
        # Настраиваем mock для ошибки подключения
        mock_db_manager.get_connection.side_effect = Exception("Connection failed")
        
        # Выполняем операцию
        result = await repository.set("test_key", "test_value")
        
        # Проверяем что операция не удалась
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository, mock_db_manager):
        """Тест конкурентных операций"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        for i in range(10):
            task = repository.set(f"key_{i}", f"value_{i}", ttl_seconds=3600)
            tasks.append(task)
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        successful_results = [r for r in results if r is True]
        assert len(successful_results) >= 5  # Хотя бы половина должна быть успешной
    
    def test_serialize_value_string(self, repository):
        """Тест сериализации строкового значения"""
        value = "test_string"
        serialized, value_type = repository._serialize_value(value)
        
        assert serialized == "test_string"
        assert value_type == "string"
    
    def test_serialize_value_dict(self, repository):
        """Тест сериализации словаря"""
        value = {"key": "value", "number": 123}
        serialized, value_type = repository._serialize_value(value)
        
        assert value_type == "json"
        # Проверяем что это валидный JSON
        import json
        parsed = json.loads(serialized)
        assert parsed["key"] == "value"
        assert parsed["number"] == 123
    
    def test_serialize_value_list(self, repository):
        """Тест сериализации списка"""
        value = ["item1", "item2", 123]
        serialized, value_type = repository._serialize_value(value)
        
        assert value_type == "json"
        # Проверяем что это валидный JSON
        import json
        parsed = json.loads(serialized)
        assert parsed == ["item1", "item2", 123]
    
    def test_deserialize_value_string(self, repository):
        """Тест десериализации строкового значения"""
        result = repository._deserialize_value("test_string", "string")
        assert result == "test_string"
    
    def test_deserialize_value_json(self, repository):
        """Тест десериализации JSON значения"""
        json_string = '{"key": "value", "number": 123}'
        result = repository._deserialize_value(json_string, "json")
        
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 123
    
    def test_deserialize_value_invalid_json(self, repository):
        """Тест десериализации невалидного JSON"""
        invalid_json = "invalid json string"
        result = repository._deserialize_value(invalid_json, "json")
        
        # Должен вернуть исходную строку при ошибке парсинга
        assert result == invalid_json
    
    def test_calculate_expiry_time(self, repository):
        """Тест расчета времени истечения"""
        ttl_seconds = 3600
        current_time = int(time.time() * 1000)
        
        expiry_time = repository._calculate_expiry_time(ttl_seconds)
        expected_expiry = current_time + ttl_seconds * 1000
        
        # Допускаем погрешность в 1 секунду
        assert abs(expiry_time - expected_expiry) < 1000
    
    def test_calculate_expiry_time_none(self, repository):
        """Тест расчета времени истечения с None TTL"""
        expiry_time = repository._calculate_expiry_time(None)
        assert expiry_time is None