import pytest
import time
from datetime import datetime

from src.domain.entities.configuration import Configuration, ConfigCategory, ConfigType


class TestConfigCategory:
    """Тесты для ConfigCategory"""
    
    def test_config_categories_exist(self):
        """Тест наличия всех категорий конфигурации"""
        assert ConfigCategory.TRADING
        assert ConfigCategory.RISK_MANAGEMENT
        assert ConfigCategory.TECHNICAL_INDICATORS
        assert ConfigCategory.ORDER_BOOK
        assert ConfigCategory.EXCHANGE
        assert ConfigCategory.SYSTEM
        assert ConfigCategory.NOTIFICATIONS
        assert ConfigCategory.LOGGING
        assert ConfigCategory.PERFORMANCE
    
    def test_config_category_values(self):
        """Тест значений категорий"""
        assert ConfigCategory.TRADING.value == "trading"
        assert ConfigCategory.SYSTEM.value == "system"
        assert ConfigCategory.EXCHANGE.value == "exchange"


class TestConfigType:
    """Тесты для ConfigType"""
    
    def test_config_types_exist(self):
        """Тест наличия всех типов конфигурации"""
        assert ConfigType.STRING
        assert ConfigType.INTEGER
        assert ConfigType.FLOAT
        assert ConfigType.BOOLEAN
        assert ConfigType.JSON
        assert ConfigType.LIST
        assert ConfigType.DICT
    
    def test_config_type_values(self):
        """Тест значений типов"""
        assert ConfigType.STRING.value == "string"
        assert ConfigType.INTEGER.value == "integer"
        assert ConfigType.BOOLEAN.value == "boolean"


class TestConfiguration:
    """Тесты для Configuration"""
    
    def test_create_configuration_minimal(self):
        """Тест создания минимальной конфигурации"""
        config = Configuration(
            key="test_key",
            value="test_value",
            category=ConfigCategory.SYSTEM
        )
        
        assert config.key == "test_key"
        assert config.value == "test_value"
        assert config.category == ConfigCategory.SYSTEM
        assert config.config_type == ConfigType.STRING  # По умолчанию
        assert config.description is None
        assert config.is_secret is False
        assert config.is_required is False
    
    def test_create_configuration_full(self):
        """Тест создания полной конфигурации"""
        config = Configuration(
            key="api_key",
            value="secret123",
            category=ConfigCategory.EXCHANGE,
            config_type=ConfigType.STRING,
            description="API ключ для биржи",
            is_secret=True,
            is_required=True,
            default_value="default_key",
            validation_rules={"min_length": 8},
            tags=["security", "api"]
        )
        
        assert config.key == "api_key"
        assert config.value == "secret123"
        assert config.category == ConfigCategory.EXCHANGE
        assert config.config_type == ConfigType.STRING
        assert config.description == "API ключ для биржи"
        assert config.is_secret is True
        assert config.is_required is True
        assert config.default_value == "default_key"
        assert config.validation_rules == {"min_length": 8}
        assert config.tags == ["security", "api"]
    
    def test_full_key_property(self):
        """Тест свойства full_key"""
        config = Configuration(
            key="test_key",
            value="test_value",
            category=ConfigCategory.TRADING
        )
        
        assert config.full_key == "trading.test_key"
    
    def test_string_config_type(self):
        """Тест строкового типа конфигурации"""
        config = Configuration(
            key="string_key",
            value="string_value",
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.STRING
        )
        
        assert config.config_type == ConfigType.STRING
        assert isinstance(config.value, str)
    
    def test_integer_config_type(self):
        """Тест целочисленного типа конфигурации"""
        config = Configuration(
            key="int_key",
            value=123,
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.INTEGER
        )
        
        assert config.config_type == ConfigType.INTEGER
        assert isinstance(config.value, int)
        assert config.value == 123
    
    def test_boolean_config_type(self):
        """Тест булевого типа конфигурации"""
        config = Configuration(
            key="bool_key",
            value=True,
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.BOOLEAN
        )
        
        assert config.config_type == ConfigType.BOOLEAN
        assert isinstance(config.value, bool)
        assert config.value is True
    
    def test_list_config_type(self):
        """Тест списочного типа конфигурации"""
        config = Configuration(
            key="list_key",
            value=["item1", "item2", "item3"],
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.LIST
        )
        
        assert config.config_type == ConfigType.LIST
        assert isinstance(config.value, list)
        assert len(config.value) == 3
    
    def test_dict_config_type(self):
        """Тест словарного типа конфигурации"""
        config = Configuration(
            key="dict_key",
            value={"key1": "value1", "key2": "value2"},
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.DICT
        )
        
        assert config.config_type == ConfigType.DICT
        assert isinstance(config.value, dict)
        assert config.value["key1"] == "value1"
    
    def test_json_config_type(self):
        """Тест JSON типа конфигурации"""
        test_data = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        config = Configuration(
            key="json_key",
            value=test_data,
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.JSON
        )
        
        assert config.config_type == ConfigType.JSON
        assert config.value == test_data
    
    def test_numeric_methods(self):
        """Тест методов для работы с числами"""
        config = Configuration(
            key="numeric_key",
            value=123.45,
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.FLOAT
        )
        
        assert config.is_numeric() is True
        assert config.get_numeric_value() == 123.45
        
        # Тест с нечисловым значением
        string_config = Configuration(
            key="string_key",
            value="not_a_number",
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.STRING
        )
        
        assert string_config.is_numeric() is False
        assert string_config.get_numeric_value() is None
    
    def test_bool_value_conversion(self):
        """Тест конвертации в булево значение"""
        # Явное булево значение
        bool_config = Configuration(
            key="bool_key",
            value=True,
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.BOOLEAN
        )
        assert bool_config.get_bool_value() is True
        
        # Строковые true значения
        for true_val in ["true", "True", "TRUE", "yes", "1", "on", "enabled"]:
            config = Configuration(
                key="test_key",
                value=true_val,
                category=ConfigCategory.SYSTEM,
                config_type=ConfigType.STRING
            )
            assert config.get_bool_value() is True
    
    def test_list_value_conversion(self):
        """Тест конвертации в список"""
        # Явный список
        list_config = Configuration(
            key="list_key",
            value=["item1", "item2"],
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.LIST
        )
        assert list_config.get_list_value() == ["item1", "item2"]
        
        # JSON строка со списком
        json_config = Configuration(
            key="json_key",
            value='["item1", "item2", "item3"]',
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.STRING
        )
        assert json_config.get_list_value() == ["item1", "item2", "item3"]
        
        # Строка с разделителями
        csv_config = Configuration(
            key="csv_key",
            value="item1, item2, item3",
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.STRING
        )
        assert csv_config.get_list_value() == ["item1", "item2", "item3"]
    
    def test_dict_value_conversion(self):
        """Тест конвертации в словарь"""
        # Явный словарь
        dict_config = Configuration(
            key="dict_key",
            value={"key": "value"},
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.DICT
        )
        assert dict_config.get_dict_value() == {"key": "value"}
        
        # JSON строка со словарем
        json_config = Configuration(
            key="json_key",
            value='{"key1": "value1", "key2": "value2"}',
            category=ConfigCategory.SYSTEM,
            config_type=ConfigType.STRING
        )
        result = json_config.get_dict_value()
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
    
    def test_update_value(self):
        """Тест обновления значения"""
        config = Configuration(
            key="test_key",
            value="initial_value",
            category=ConfigCategory.SYSTEM
        )
        
        old_updated_at = config.updated_at
        
        # Ждем немного чтобы время изменилось
        import time
        time.sleep(0.01)
        
        config.update_value("new_value")
        
        assert config.value == "new_value"
        assert config.updated_at > old_updated_at
    
    def test_reset_to_default(self):
        """Тест сброса к значению по умолчанию"""
        config = Configuration(
            key="test_key",
            value="current_value",
            category=ConfigCategory.SYSTEM,
            default_value="default_value"
        )
        
        result = config.reset_to_default()
        
        assert result is True
        assert config.value == "default_value"
        
        # Тест без значения по умолчанию
        config_no_default = Configuration(
            key="test_key",
            value="current_value",
            category=ConfigCategory.SYSTEM
        )
        
        result = config_no_default.reset_to_default()
        assert result is False
        assert config_no_default.value == "current_value"
    
    def test_tag_management(self):
        """Тест управления тегами"""
        config = Configuration(
            key="test_key",
            value="test_value",
            category=ConfigCategory.SYSTEM,
            tags=["initial_tag"]
        )
        
        # Добавление тега
        config.add_tag("new_tag")
        assert "new_tag" in config.tags
        assert config.has_tag("new_tag") is True
        
        # Добавление существующего тега (не должно дублироваться)
        config.add_tag("initial_tag")
        assert config.tags.count("initial_tag") == 1
        
        # Удаление тега
        config.remove_tag("initial_tag")
        assert "initial_tag" not in config.tags
        assert config.has_tag("initial_tag") is False
        
        # Удаление несуществующего тега
        config.remove_tag("nonexistent_tag")  # Не должно вызывать ошибку
    
    def test_is_modified(self):
        """Тест проверки изменений"""
        config = Configuration(
            key="test_key",
            value="default_value",
            category=ConfigCategory.SYSTEM,
            default_value="default_value"
        )
        
        assert config.is_modified() is False
        
        config.update_value("new_value")
        assert config.is_modified() is True
    
    def test_get_display_value(self):
        """Тест отображения значения"""
        # Обычное значение
        normal_config = Configuration(
            key="normal_key",
            value="normal_value",
            category=ConfigCategory.SYSTEM
        )
        assert normal_config.get_display_value() == "normal_value"
        
        # Секретное значение
        secret_config = Configuration(
            key="secret_key",
            value="secret_value",
            category=ConfigCategory.SYSTEM,
            is_secret=True
        )
        assert secret_config.get_display_value() == "***HIDDEN***"
        
        # Секретное пустое значение
        empty_secret_config = Configuration(
            key="empty_secret",
            value="",
            category=ConfigCategory.SYSTEM,
            is_secret=True
        )
        assert empty_secret_config.get_display_value() == "***NOT_SET***"
    
    def test_to_dict(self):
        """Тест сериализации в словарь"""
        config = Configuration(
            key="test_key",
            value="test_value",
            category=ConfigCategory.TRADING,
            config_type=ConfigType.STRING,
            description="Test configuration",
            is_secret=False,
            tags=["test"]
        )
        
        data = config.to_dict()
        
        assert data["key"] == "test_key"
        assert data["value"] == "test_value"
        assert data["category"] == "trading"
        assert data["config_type"] == "string"
        assert data["description"] == "Test configuration"
        assert data["is_secret"] is False
        assert data["tags"] == ["test"]
    
    def test_to_dict_secret_excluded(self):
        """Тест исключения секретов из словаря"""
        secret_config = Configuration(
            key="secret_key",
            value="secret_value",
            category=ConfigCategory.SYSTEM,
            is_secret=True
        )
        
        # Без включения секретов
        data = secret_config.to_dict(include_secrets=False)
        assert data["value"] == "***HIDDEN***"
        
        # С включением секретов
        data_with_secrets = secret_config.to_dict(include_secrets=True)
        assert data_with_secrets["value"] == "secret_value"
    
    def test_from_dict(self):
        """Тест десериализации из словаря"""
        data = {
            "key": "test_key",
            "value": "test_value",
            "category": "system",
            "config_type": "string",
            "description": "Test config",
            "is_secret": False,
            "is_required": True,
            "tags": ["test"]
        }
        
        config = Configuration.from_dict(data)
        
        assert config.key == "test_key"
        assert config.value == "test_value"
        assert config.category == ConfigCategory.SYSTEM
        assert config.config_type == ConfigType.STRING
        assert config.description == "Test config"
        assert config.is_secret is False
        assert config.is_required is True
        assert config.tags == ["test"]
    
    def test_json_serialization(self):
        """Тест JSON сериализации"""
        config = Configuration(
            key="test_key",
            value="test_value",
            category=ConfigCategory.SYSTEM
        )
        
        json_str = config.to_json()
        assert isinstance(json_str, str)
        assert "test_key" in json_str
        
        # Тест обратной конвертации
        restored_config = Configuration.from_json(json_str)
        assert restored_config.key == config.key
        assert restored_config.value == config.value
        assert restored_config.category == config.category
    
    def test_validation_error(self):
        """Тест ошибок валидации"""
        # Неправильный тип
        with pytest.raises(ValueError):
            Configuration(
                key="int_key",
                value="not_an_integer",
                category=ConfigCategory.SYSTEM,
                config_type=ConfigType.INTEGER
            )
    
    def test_string_representation(self):
        """Тест строкового представления"""
        config = Configuration(
            key="test_key",
            value="test_value",
            category=ConfigCategory.TRADING
        )
        
        str_repr = str(config)
        assert "trading.test_key" in str_repr
        assert "test_value" in str_repr
    
    def test_equality(self):
        """Тест равенства конфигураций"""
        config1 = Configuration(
            key="test_key",
            value="test_value",
            category=ConfigCategory.SYSTEM
        )
        
        config2 = Configuration(
            key="test_key",
            value="different_value",
            category=ConfigCategory.SYSTEM
        )
        
        config3 = Configuration(
            key="different_key",
            value="test_value",
            category=ConfigCategory.SYSTEM
        )
        
        # Равенство по full_key
        assert config1 == config2  # Один ключ
        assert config1 != config3  # Разные ключи