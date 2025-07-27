import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.infrastructure.repositories.postgresql.postgresql_configuration_repository import PostgreSQLConfigurationRepository
from src.domain.entities.configuration import Configuration, ConfigCategory, ConfigType
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


class TestPostgreSQLConfigurationRepository:
    """Тесты для PostgreSQLConfigurationRepository"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Фикстура для mock database manager"""
        return MockDatabaseManager()
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Фикстура для создания репозитория"""
        return PostgreSQLConfigurationRepository(mock_db_manager)
    
    @pytest.fixture
    def sample_string_config(self):
        """Фикстура с примером строковой конфигурации"""
        return Configuration(
            key="database_url",
            value="postgresql://user:pass@localhost/db",
            config_type=ConfigType.STRING,
            category=ConfigCategory.SYSTEM,
            description="Database connection URL",
            is_secret=True
        )
    
    @pytest.fixture
    def sample_number_config(self):
        """Фикстура с примером числовой конфигурации"""
        return Configuration(
            key="max_orders_per_minute",
            value=120,
            config_type=ConfigType.INTEGER,
            category=ConfigCategory.TRADING,
            description="Maximum orders per minute limit",
            is_secret=False,
            validation_rules={"min_value": 1, "max_value": 300}
        )
    
    @pytest.fixture
    def sample_boolean_config(self):
        """Фикстура с примером boolean конфигурации"""
        return Configuration(
            key="enable_live_trading",
            value=True,
            config_type=ConfigType.BOOLEAN,
            category=ConfigCategory.TRADING,
            description="Enable live trading mode",
            is_secret=False
        )
    
    @pytest.fixture
    def sample_json_config(self):
        """Фикстура с примером JSON конфигурации"""
        return Configuration(
            key="trading_pairs",
            value=["BTCUSDT", "ETHUSDT", "ADAUSDT"],
            config_type=ConfigType.LIST,
            category=ConfigCategory.TRADING,
            description="List of enabled trading pairs",
            is_secret=False
        )
    
    @pytest.mark.asyncio
    async def test_save_configuration(self, repository, mock_db_manager, sample_string_config):
        """Тест сохранения конфигурации"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.save_configuration(sample_string_config)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван execute
        assert mock_db_manager.cursor.execute.called
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "INSERT INTO configurations" in query
        assert "ON CONFLICT" in query
        assert params[0] == "database_url"
        assert params[1] == "postgresql://user:pass@localhost/db"
        assert params[2] == "string"
        assert params[3] == "system"
    
    @pytest.mark.asyncio
    async def test_save_configuration_failure(self, repository, mock_db_manager, sample_string_config):
        """Тест неудачного сохранения конфигурации"""
        # Настраиваем mock для ошибки
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.execute.side_effect = Exception("Database error")
        
        # Выполняем операцию
        result = await repository.save_configuration(sample_string_config)
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_configuration(self, repository, mock_db_manager, sample_string_config):
        """Тест получения конфигурации"""
        # Настраиваем mock результат
        db_row = (
            "database_url", "postgresql://user:pass@localhost/db", "string", "database",
            "Database connection URL", True, sample_string_config.created_at,
            sample_string_config.updated_at, '{"environment": "production", "version": "1.0"}'
        )
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([db_row])
        
        # Выполняем операцию
        result = await repository.get_configuration("database_url")
        
        # Проверяем результат
        assert result is not None
        assert result.key == "database_url"
        assert result.value == "postgresql://user:pass@localhost/db"
        assert result.config_type == ConfigurationType.STRING
        assert result.category == "database"
        assert result.description == "Database connection URL"
        assert result.is_secret is True
        assert result.metadata["environment"] == "production"
    
    @pytest.mark.asyncio
    async def test_get_configuration_not_found(self, repository, mock_db_manager):
        """Тест получения несуществующей конфигурации"""
        # Настраиваем mock для пустого результата
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results([])
        
        # Выполняем операцию
        result = await repository.get_configuration("nonexistent_key")
        
        # Проверяем результат
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_configurations_by_category(self, repository, mock_db_manager):
        """Тест получения конфигураций по категории"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("max_orders", "120", "number", "trading", "Max orders", False, timestamp, timestamp, '{}'),
            ("enable_trading", "true", "boolean", "trading", "Enable trading", False, timestamp, timestamp, '{}'),
            ("trading_pairs", '["BTCUSDT"]', "json", "trading", "Trading pairs", False, timestamp, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_configurations_by_category("trading")
        
        # Проверяем результат
        assert len(result) == 3
        assert all(config.category == "trading" for config in result)
        keys = [config.key for config in result]
        assert "max_orders" in keys
        assert "enable_trading" in keys
        assert "trading_pairs" in keys
    
    @pytest.mark.asyncio
    async def test_update_configuration_value(self, repository, mock_db_manager):
        """Тест обновления значения конфигурации"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.update_configuration_value("max_orders", 150)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "UPDATE configurations" in query
        assert "SET value =" in query
        assert "SET updated_at =" in query
        assert params[0] == "150"
        assert params[2] == "max_orders"
    
    @pytest.mark.asyncio
    async def test_update_configuration_value_not_found(self, repository, mock_db_manager):
        """Тест обновления несуществующей конфигурации"""
        # Настраиваем mock для отсутствия изменений
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=0)
        
        # Выполняем операцию
        result = await repository.update_configuration_value("nonexistent", "value")
        
        # Проверяем результат
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_configuration(self, repository, mock_db_manager):
        """Тест удаления конфигурации"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Выполняем операцию
        result = await repository.delete_configuration("old_config")
        
        # Проверяем результат
        assert result is True
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "DELETE FROM configurations" in query
        assert "WHERE key =" in query
        assert params[0] == "old_config"
    
    @pytest.mark.asyncio
    async def test_get_all_configurations(self, repository, mock_db_manager):
        """Тест получения всех конфигураций"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("key1", "value1", "string", "cat1", "desc1", False, timestamp, timestamp, '{}'),
            ("key2", "value2", "number", "cat2", "desc2", True, timestamp, timestamp, '{}'),
            ("key3", "value3", "boolean", "cat1", "desc3", False, timestamp, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_all_configurations(include_secrets=False)
        
        # Проверяем результат
        assert len(result) == 2  # Исключаем секретную конфигурацию
        secret_configs = [config for config in result if config.is_secret]
        assert len(secret_configs) == 0
    
    @pytest.mark.asyncio
    async def test_get_all_configurations_include_secrets(self, repository, mock_db_manager):
        """Тест получения всех конфигураций включая секретные"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("key1", "value1", "string", "cat1", "desc1", False, timestamp, timestamp, '{}'),
            ("key2", "value2", "number", "cat2", "desc2", True, timestamp, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_all_configurations(include_secrets=True)
        
        # Проверяем результат
        assert len(result) == 2
        secret_configs = [config for config in result if config.is_secret]
        assert len(secret_configs) == 1
    
    @pytest.mark.asyncio
    async def test_batch_save_configurations(self, repository, mock_db_manager, sample_string_config, sample_number_config):
        """Тест пакетного сохранения конфигураций"""
        # Создаем тестовые конфигурации
        configurations = [
            sample_string_config,
            sample_number_config,
            Configuration("test_key", "test_value", ConfigurationType.STRING, "test", "Test config")
        ]
        
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.executemany = AsyncMock()
        
        # Выполняем операцию
        result = await repository.batch_save_configurations(configurations)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван executemany
        assert mock_db_manager.cursor.executemany.called
        execute_call = mock_db_manager.cursor.executemany.call_args
        query = execute_call[0][0]
        batch_data = execute_call[0][1]
        
        assert "INSERT INTO configurations" in query
        assert len(batch_data) == 3
    
    @pytest.mark.asyncio
    async def test_get_configurations_by_pattern(self, repository, mock_db_manager):
        """Тест получения конфигураций по паттерну"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("api_key", "secret123", "string", "api", "API key", True, timestamp, timestamp, '{}'),
            ("api_url", "https://api.example.com", "string", "api", "API URL", False, timestamp, timestamp, '{}'),
            ("api_timeout", "30", "number", "api", "API timeout", False, timestamp, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_configurations_by_pattern("api_%")
        
        # Проверяем результат
        assert len(result) == 3
        assert all(config.key.startswith("api_") for config in result)
        
        # Проверяем запрос
        execute_call = mock_db_manager.cursor.execute.call_args
        query = execute_call[0][0]
        params = execute_call[0][1]
        
        assert "LIKE" in query or "ILIKE" in query
        assert params[0] == "api_%"
    
    @pytest.mark.asyncio
    async def test_backup_configurations(self, repository, mock_db_manager):
        """Тест создания резервной копии конфигураций"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("key1", "value1", "string", "cat1", "desc1", False, timestamp, timestamp, '{}'),
            ("key2", "value2", "number", "cat2", "desc2", True, timestamp, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.backup_configurations(include_secrets=True)
        
        # Проверяем результат
        assert 'timestamp' in result
        assert 'configurations' in result
        assert len(result['configurations']) == 2
        assert result['configurations'][0]['key'] == "key1"
        assert result['configurations'][1]['key'] == "key2"
    
    @pytest.mark.asyncio
    async def test_restore_configurations(self, repository, mock_db_manager, sample_string_config):
        """Тест восстановления конфигураций из резервной копии"""
        # Подготавливаем данные для восстановления
        backup_data = {
            'timestamp': int(time.time() * 1000),
            'configurations': [
                {
                    'key': 'restore_test',
                    'value': 'test_value',
                    'config_type': 'string',
                    'category': 'test',
                    'description': 'Test config',
                    'is_secret': False,
                    'metadata': {}
                }
            ]
        }
        
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.cursor.executemany = AsyncMock()
        
        # Выполняем операцию
        result = await repository.restore_configurations(backup_data)
        
        # Проверяем результат
        assert result is True
        
        # Проверяем что был вызван executemany
        assert mock_db_manager.cursor.executemany.called
    
    @pytest.mark.asyncio
    async def test_validate_configuration_value(self, repository, mock_db_manager):
        """Тест валидации значения конфигурации"""
        # Тест валидного числа
        result = await repository.validate_configuration_value("120", ConfigurationType.NUMBER)
        assert result['is_valid'] is True
        assert result['converted_value'] == 120
        
        # Тест невалидного числа
        result = await repository.validate_configuration_value("not_a_number", ConfigurationType.NUMBER)
        assert result['is_valid'] is False
        assert 'error' in result
        
        # Тест валидного boolean
        result = await repository.validate_configuration_value("true", ConfigurationType.BOOLEAN)
        assert result['is_valid'] is True
        assert result['converted_value'] is True
        
        # Тест валидного JSON
        result = await repository.validate_configuration_value('["item1", "item2"]', ConfigurationType.JSON)
        assert result['is_valid'] is True
        assert result['converted_value'] == ["item1", "item2"]
        
        # Тест невалидного JSON
        result = await repository.validate_configuration_value('invalid json', ConfigurationType.JSON)
        assert result['is_valid'] is False
    
    @pytest.mark.asyncio
    async def test_get_configuration_history(self, repository, mock_db_manager):
        """Тест получения истории изменений конфигурации"""
        # Настраиваем mock результаты для таблицы истории
        base_time = int(time.time() * 1000)
        db_rows = [
            ("max_orders", "100", "120", base_time, "admin"),
            ("max_orders", "80", "100", base_time - 3600000, "system"),
            ("max_orders", "60", "80", base_time - 7200000, "admin")
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.get_configuration_history("max_orders", limit=5)
        
        # Проверяем результат
        assert len(result) == 3
        assert result[0]['key'] == "max_orders"
        assert result[0]['old_value'] == "100"
        assert result[0]['new_value'] == "120"
        assert result[0]['changed_by'] == "admin"
    
    @pytest.mark.asyncio
    async def test_search_configurations(self, repository, mock_db_manager):
        """Тест поиска конфигураций"""
        # Настраиваем mock результаты
        timestamp = int(time.time() * 1000)
        db_rows = [
            ("database_url", "postgresql://...", "string", "database", "Database URL", True, timestamp, timestamp, '{}'),
            ("database_timeout", "30", "number", "database", "DB timeout", False, timestamp, timestamp, '{}')
        ]
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_fetch_results(db_rows)
        
        # Выполняем операцию
        result = await repository.search_configurations("database")
        
        # Проверяем результат
        assert len(result) == 2
        assert all("database" in config.key.lower() or "database" in config.description.lower() for config in result)
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, repository, mock_db_manager, sample_string_config):
        """Тест обработки ошибок подключения"""
        # Настраиваем mock для ошибки подключения
        mock_db_manager.get_connection.side_effect = Exception("Connection failed")
        
        # Выполняем операцию
        result = await repository.save_configuration(sample_string_config)
        
        # Проверяем что операция не удалась
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository, mock_db_manager):
        """Тест конкурентных операций"""
        # Настраиваем mock
        mock_db_manager.connection.cursor.return_value = mock_db_manager.cursor
        mock_db_manager.set_execute_response(rowcount=1)
        
        # Создаем тестовые конфигурации
        timestamp = int(time.time() * 1000)
        configurations = [
            Configuration(f"key_{i}", f"value_{i}", ConfigurationType.STRING, "test", f"Test config {i}")
            for i in range(10)
        ]
        
        # Создаем задачи для параллельного выполнения
        tasks = [repository.save_configuration(config) for config in configurations]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        successful_results = [r for r in results if r is True]
        assert len(successful_results) >= 5  # Хотя бы половина должна быть успешной
    
    def test_convert_db_row_to_configuration(self, repository):
        """Тест конвертации строки БД в конфигурацию"""
        timestamp = int(time.time() * 1000)
        metadata_json = '{"environment": "production"}'
        
        db_row = (
            "database_url", "postgresql://user:pass@localhost/db", "string", "database",
            "Database URL", True, timestamp, timestamp + 1000, metadata_json
        )
        
        configuration = repository._convert_db_row_to_configuration(db_row)
        
        assert configuration.key == "database_url"
        assert configuration.value == "postgresql://user:pass@localhost/db"
        assert configuration.config_type == ConfigurationType.STRING
        assert configuration.category == "database"
        assert configuration.description == "Database URL"
        assert configuration.is_secret is True
        assert configuration.created_at == timestamp
        assert configuration.updated_at == timestamp + 1000
        assert configuration.metadata["environment"] == "production"
    
    def test_convert_invalid_config_type(self, repository):
        """Тест конвертации с невалидным типом конфигурации"""
        timestamp = int(time.time() * 1000)
        db_row = (
            "key", "value", "invalid_type", "category", "description", 
            False, timestamp, timestamp, '{}'
        )
        
        configuration = repository._convert_db_row_to_configuration(db_row)
        
        # Должен вернуть None для невалидного типа
        assert configuration is None
    
    def test_prepare_configuration_data(self, repository, sample_string_config):
        """Тест подготовки данных конфигурации для БД"""
        result = repository._prepare_configuration_data(sample_string_config)
        
        expected = (
            "database_url",
            "postgresql://user:pass@localhost/db",
            "string",
            "database",
            "Database connection URL",
            True,
            sample_string_config.created_at,
            sample_string_config.updated_at,
            '{"environment": "production", "version": "1.0"}'
        )
        
        assert result == expected
    
    def test_convert_value_by_type_number(self, repository):
        """Тест конвертации числового значения"""
        # Целое число
        result = repository._convert_value_by_type("120", ConfigurationType.NUMBER)
        assert result == 120
        
        # Дробное число
        result = repository._convert_value_by_type("123.45", ConfigurationType.NUMBER)
        assert result == 123.45
        
        # Невалидное число
        with pytest.raises(ValueError):
            repository._convert_value_by_type("not_a_number", ConfigurationType.NUMBER)
    
    def test_convert_value_by_type_boolean(self, repository):
        """Тест конвертации boolean значения"""
        # True значения
        for value in ["true", "True", "TRUE", "1", "yes", "on"]:
            result = repository._convert_value_by_type(value, ConfigurationType.BOOLEAN)
            assert result is True
        
        # False значения
        for value in ["false", "False", "FALSE", "0", "no", "off"]:
            result = repository._convert_value_by_type(value, ConfigurationType.BOOLEAN)
            assert result is False
    
    def test_convert_value_by_type_json(self, repository):
        """Тест конвертации JSON значения"""
        # Валидный JSON объект
        result = repository._convert_value_by_type('{"key": "value"}', ConfigurationType.JSON)
        assert result == {"key": "value"}
        
        # Валидный JSON массив
        result = repository._convert_value_by_type('["item1", "item2"]', ConfigurationType.JSON)
        assert result == ["item1", "item2"]
        
        # Невалидный JSON
        with pytest.raises(ValueError):
            repository._convert_value_by_type('invalid json', ConfigurationType.JSON)
    
    def test_convert_value_by_type_string(self, repository):
        """Тест конвертации строкового значения"""
        result = repository._convert_value_by_type("test_string", ConfigurationType.STRING)
        assert result == "test_string"
        
        # Число как строка остается строкой
        result = repository._convert_value_by_type("123", ConfigurationType.STRING)
        assert result == "123"