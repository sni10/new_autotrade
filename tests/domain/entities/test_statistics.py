import pytest
import time
from datetime import datetime

from src.domain.entities.statistics import (
    Statistics, StatisticCategory, StatisticType
)


class TestStatisticCategory:
    """Тесты для StatisticCategory enum"""
    
    def test_statistic_categories_exist(self):
        """Тест наличия всех категорий статистики"""
        assert StatisticCategory.TRADING
        assert StatisticCategory.PERFORMANCE
        assert StatisticCategory.ORDERS
        assert StatisticCategory.DEALS
        assert StatisticCategory.MARKET_DATA
        assert StatisticCategory.RISK_MANAGEMENT
        assert StatisticCategory.SYSTEM
        assert StatisticCategory.TECHNICAL_INDICATORS
        assert StatisticCategory.ORDER_BOOK
    
    def test_statistic_category_values(self):
        """Тест значений категорий"""
        assert StatisticCategory.TRADING.value == "trading"
        assert StatisticCategory.PERFORMANCE.value == "performance"
        assert StatisticCategory.SYSTEM.value == "system"


class TestStatisticType:
    """Тесты для StatisticType enum"""
    
    def test_statistic_types_exist(self):
        """Тест наличия всех типов статистики"""
        assert StatisticType.COUNTER
        assert StatisticType.GAUGE
        assert StatisticType.HISTOGRAM
        assert StatisticType.TIMING
        assert StatisticType.RATE
        assert StatisticType.PERCENTAGE
    
    def test_statistic_type_values(self):
        """Тест значений типов"""
        assert StatisticType.COUNTER.value == "counter"
        assert StatisticType.GAUGE.value == "gauge"
        assert StatisticType.TIMING.value == "timing"


class TestStatistics:
    """Тесты для Statistics"""
    
    def test_create_statistics_minimal(self):
        """Тест создания статистики с минимальными параметрами"""
        stats = Statistics(
            metric_name="orders_created",
            value=125,
            category=StatisticCategory.ORDERS
        )
        
        assert stats.metric_name == "orders_created"
        assert stats.value == 125
        assert stats.category == StatisticCategory.ORDERS
        assert stats.metric_type == StatisticType.GAUGE  # default
        assert stats.symbol is None
        assert stats.tags == {}
        assert stats.description is None
        assert stats.metric_id.startswith("orders_orders_created_")
    
    def test_create_statistics_full(self):
        """Тест создания статистики со всеми параметрами"""
        timestamp = int(time.time() * 1000)
        tags = {"exchange": "binance", "environment": "production"}
        
        stats = Statistics(
            metric_name="execution_time",
            value=125.75,
            category=StatisticCategory.PERFORMANCE,
            metric_type=StatisticType.TIMING,
            timestamp=timestamp,
            symbol="BTCUSDT",
            tags=tags,
            description="Order execution time in milliseconds"
        )
        
        assert stats.metric_name == "execution_time"
        assert stats.value == 125.75
        assert stats.category == StatisticCategory.PERFORMANCE
        assert stats.metric_type == StatisticType.TIMING
        assert stats.symbol == "BTCUSDT"
        assert stats.timestamp == timestamp
        assert stats.tags == tags
        assert stats.description == "Order execution time in milliseconds"
        assert "BTCUSDT" in stats.metric_id
    
    def test_create_counter_factory(self):
        """Тест фабричного метода create_counter"""
        counter = Statistics.create_counter(
            name="total_orders",
            category=StatisticCategory.ORDERS,
            initial_value=500,
            symbol="ETHUSDT",
            tags={"type": "limit"}
        )
        
        assert counter.metric_type == StatisticType.COUNTER
        assert counter.metric_name == "total_orders"
        assert counter.value == 500
        assert counter.symbol == "ETHUSDT"
        assert counter.tags == {"type": "limit"}
    
    def test_create_timing_factory(self):
        """Тест фабричного метода create_timing"""
        timing = Statistics.create_timing(
            name="tick_processing",
            category=StatisticCategory.PERFORMANCE,
            duration_ms=15.5,
            symbol="ADAUSDT"
        )
        
        assert timing.metric_type == StatisticType.TIMING
        assert timing.metric_name == "tick_processing"
        assert timing.value == 15.5
        assert timing.symbol == "ADAUSDT"
    
    def test_create_percentage_factory(self):
        """Тест фабричного метода create_percentage"""
        percentage = Statistics.create_percentage(
            name="order_success_rate",
            category=StatisticCategory.TRADING,
            percent_value=98.5,
            tags={"period": "daily"}
        )
        
        assert percentage.metric_type == StatisticType.PERCENTAGE
        assert percentage.metric_name == "order_success_rate"
        assert percentage.value == 98.5
        assert percentage.tags == {"period": "daily"}
    
    def test_full_metric_name_property(self):
        """Тест свойства full_metric_name"""
        stats = Statistics(
            metric_name="test_metric",
            value=100,
            category=StatisticCategory.TRADING
        )
        
        assert stats.full_metric_name == "trading.test_metric"
    
    def test_increment_counter(self):
        """Тест увеличения счетчика"""
        counter = Statistics.create_counter(
            "test_metric", StatisticCategory.SYSTEM, 10
        )
        
        old_timestamp = counter.timestamp
        
        # Увеличиваем на 1
        counter.increment()
        assert counter.value == 11
        assert counter.timestamp >= old_timestamp
        
        # Увеличиваем на 5
        counter.increment(5)
        assert counter.value == 16
    
    def test_increment_non_numeric(self):
        """Тест increment для нечисловых значений"""
        stats = Statistics(
            metric_name="text_metric",
            value="not_a_number",
            category=StatisticCategory.SYSTEM
        )
        
        # increment не должен работать для нечисловых значений
        stats.increment()
        assert stats.value == "not_a_number"  # Значение не изменилось
    
    def test_update_value(self):
        """Тест обновления значения"""
        stats = Statistics(
            metric_name="test_metric",
            value=50.0,
            category=StatisticCategory.SYSTEM
        )
        
        old_timestamp = stats.timestamp
        
        stats.update_value(75.5)
        
        assert stats.value == 75.5
        assert stats.timestamp >= old_timestamp
    
    def test_add_tag(self):
        """Тест добавления тега"""
        stats = Statistics(
            metric_name="test_metric",
            value=1,
            category=StatisticCategory.SYSTEM
        )
        
        stats.add_tag("environment", "test")
        assert stats.tags["environment"] == "test"
        
        stats.add_tag("version", "1.0")
        assert stats.tags["version"] == "1.0"
        assert len(stats.tags) == 2
    
    def test_remove_tag(self):
        """Тест удаления тега"""
        stats = Statistics(
            metric_name="test_metric",
            value=1,
            category=StatisticCategory.SYSTEM,
            tags={"env": "test", "version": "1.0"}
        )
        
        stats.remove_tag("env")
        assert "env" not in stats.tags
        assert "version" in stats.tags
        
        # Удаление несуществующего тега не должно вызывать ошибку
        stats.remove_tag("nonexistent")
    
    def test_has_tag(self):
        """Тест проверки наличия тега"""
        stats = Statistics(
            metric_name="test_metric",
            value=1,
            category=StatisticCategory.SYSTEM,
            tags={"env": "test", "version": "1.0"}
        )
        
        assert stats.has_tag("env")
        assert stats.has_tag("env", "test")
        assert not stats.has_tag("env", "production")
        assert not stats.has_tag("nonexistent")
    
    def test_age_calculation(self):
        """Тест расчета возраста статистики"""
        # Статистика "из прошлого"
        old_timestamp = int((time.time() - 300) * 1000)  # 5 минут назад
        old_stats = Statistics(
            metric_name="old_metric",
            value=1,
            category=StatisticCategory.SYSTEM,
            timestamp=old_timestamp
        )
        
        age_seconds = old_stats.age_seconds()
        assert 290 < age_seconds < 310  # Примерно 5 минут
        
        # Свежая статистика
        fresh_stats = Statistics(
            metric_name="fresh_metric",
            value=1,
            category=StatisticCategory.SYSTEM
        )
        
        age_seconds_fresh = fresh_stats.age_seconds()
        assert age_seconds_fresh < 5
    
    def test_is_stale(self):
        """Тест определения устаревших данных"""
        # Устаревшая статистика
        old_timestamp = int((time.time() - 600) * 1000)  # 10 минут назад
        old_stats = Statistics(
            metric_name="stale_metric",
            value=100.0,
            category=StatisticCategory.SYSTEM,
            timestamp=old_timestamp
        )
        
        assert old_stats.is_stale(max_age_seconds=300)  # 5 минут max
        assert not old_stats.is_stale(max_age_seconds=900)  # 15 минут max
        
        # Свежая статистика
        fresh_stats = Statistics(
            metric_name="fresh_metric",
            value=100.0,
            category=StatisticCategory.SYSTEM
        )
        
        assert not fresh_stats.is_stale(max_age_seconds=300)
    
    def test_is_numeric(self):
        """Тест определения числовых значений"""
        # Числовые значения
        numeric_int = Statistics(
            metric_name="test", value=123, category=StatisticCategory.SYSTEM
        )
        numeric_float = Statistics(
            metric_name="test", value=123.45, category=StatisticCategory.SYSTEM
        )
        
        assert numeric_int.is_numeric()
        assert numeric_float.is_numeric()
        
        # Строковое значение
        string_stats = Statistics(
            metric_name="test", value="not_a_number", category=StatisticCategory.SYSTEM
        )
        
        assert not string_stats.is_numeric()
    
    def test_get_numeric_value(self):
        """Тест получения числового значения"""
        # Числовые значения
        int_stats = Statistics(
            metric_name="test", value=42, category=StatisticCategory.SYSTEM
        )
        float_stats = Statistics(
            metric_name="test", value=3.14159, category=StatisticCategory.SYSTEM
        )
        
        assert int_stats.get_numeric_value() == 42.0
        assert abs(float_stats.get_numeric_value() - 3.14159) < 0.00001
        
        # Нечисловая строка
        string_text = Statistics(
            metric_name="test", value="not_a_number", category=StatisticCategory.SYSTEM
        )
        
        assert string_text.get_numeric_value() is None
    
    def test_is_percentage_valid(self):
        """Тест валидации процентных значений"""
        # Валидный процент
        valid_percent = Statistics(
            metric_name="test",
            value=50.0,
            category=StatisticCategory.SYSTEM,
            metric_type=StatisticType.PERCENTAGE
        )
        assert valid_percent.is_percentage_valid()
        
        # Невалидный процент (> 100)
        invalid_percent = Statistics(
            metric_name="test",
            value=150.0,
            category=StatisticCategory.SYSTEM,
            metric_type=StatisticType.PERCENTAGE
        )
        assert not invalid_percent.is_percentage_valid()
        
        # Не процентный тип
        non_percent = Statistics(
            metric_name="test",
            value=150.0,
            category=StatisticCategory.SYSTEM,
            metric_type=StatisticType.GAUGE
        )
        assert non_percent.is_percentage_valid()  # Всегда True для не-процентных
    
    def test_format_value(self):
        """Тест форматирования значений"""
        # Counter
        counter = Statistics.create_counter(
            "test", StatisticCategory.SYSTEM, 1234
        )
        assert counter.format_value() == "1234"
        
        # Gauge с плавающей точкой
        gauge = Statistics(
            metric_name="test",
            value=123.456789,
            category=StatisticCategory.SYSTEM,
            metric_type=StatisticType.GAUGE
        )
        assert gauge.format_value() == "123.4568"  # 4 decimal places
        
        # Percentage
        percentage = Statistics.create_percentage(
            "test", StatisticCategory.SYSTEM, 98.5
        )
        assert percentage.format_value() == "98.50%"
        
        # Timing (milliseconds)
        timing_ms = Statistics.create_timing(
            "test", StatisticCategory.SYSTEM, 234.5
        )
        assert timing_ms.format_value() == "234.50ms"
        
        # Timing (seconds)
        timing_s = Statistics.create_timing(
            "test", StatisticCategory.SYSTEM, 1234.5
        )
        assert timing_s.format_value() == "1.23s"
        
        # Rate
        rate = Statistics(
            metric_name="test",
            value=150.0,
            category=StatisticCategory.SYSTEM,
            metric_type=StatisticType.RATE
        )
        assert rate.format_value() == "150.00/s"
        
        # String value
        string_stats = Statistics(
            metric_name="test", value="active", category=StatisticCategory.SYSTEM
        )
        assert string_stats.format_value() == "active"
    
    def test_to_dict(self):
        """Тест сериализации в словарь"""
        tags = {"environment": "production", "version": "2.4.0"}
        
        stats = Statistics(
            metric_name="test_metric",
            value=123.45,
            category=StatisticCategory.PERFORMANCE,
            metric_type=StatisticType.TIMING,
            symbol="BTCUSDT",
            timestamp=1234567890000,
            tags=tags,
            description="Test statistic for serialization"
        )
        
        data = stats.to_dict()
        
        assert data['metric_name'] == "test_metric"
        assert data['value'] == 123.45
        assert data['category'] == "performance"
        assert data['metric_type'] == "timing"
        assert data['symbol'] == "BTCUSDT"
        assert data['timestamp'] == 1234567890000
        assert data['tags'] == tags
        assert data['description'] == "Test statistic for serialization"
        assert 'metric_id' in data
        assert 'formatted_value' in data
        assert 'age_seconds' in data
    
    def test_from_dict(self):
        """Тест десериализации из словаря"""
        data = {
            'metric_name': 'imported_metric',
            'value': 987.65,
            'category': 'trading',
            'metric_type': 'gauge',
            'symbol': 'ETHUSDT',
            'timestamp': 9876543210000,
            'tags': {'source': 'import'},
            'description': 'Imported statistic'
        }
        
        stats = Statistics.from_dict(data)
        
        assert stats.metric_name == 'imported_metric'
        assert stats.value == 987.65
        assert stats.category == StatisticCategory.TRADING
        assert stats.metric_type == StatisticType.GAUGE
        assert stats.symbol == 'ETHUSDT'
        assert stats.timestamp == 9876543210000
        assert stats.tags == {'source': 'import'}
        assert stats.description == 'Imported statistic'
    
    def test_from_dict_minimal(self):
        """Тест десериализации с минимальными данными"""
        data = {
            'metric_name': 'minimal_metric',
            'value': 42,
            'category': 'system',
            'timestamp': 1111111111000
        }
        
        stats = Statistics.from_dict(data)
        
        assert stats.metric_name == 'minimal_metric'
        assert stats.metric_type == StatisticType.GAUGE  # default
        assert stats.symbol is None
        assert stats.tags == {}
        assert stats.description is None
    
    def test_json_serialization(self):
        """Тест JSON сериализации"""
        stats = Statistics(
            metric_name="test_metric",
            value=123.45,
            category=StatisticCategory.SYSTEM
        )
        
        json_str = stats.to_json()
        assert isinstance(json_str, str)
        assert "test_metric" in json_str
        
        # Тест обратной конвертации
        restored_stats = Statistics.from_json(json_str)
        assert restored_stats.metric_name == stats.metric_name
        assert restored_stats.value == stats.value
        assert restored_stats.category == stats.category
    
    def test_to_prometheus_format(self):
        """Тест форматирования для Prometheus"""
        stats = Statistics(
            metric_name="test_metric",
            value=123.45,
            category=StatisticCategory.PERFORMANCE,
            symbol="BTCUSDT",
            tags={"env": "prod", "version": "1.0"}
        )
        
        prometheus_str = stats.to_prometheus_format()
        assert "performance.test_metric" in prometheus_str
        assert "123.45" in prometheus_str
        assert 'symbol="BTCUSDT"' in prometheus_str
        assert 'env="prod"' in prometheus_str
        assert 'version="1.0"' in prometheus_str
    
    def test_equality(self):
        """Тест равенства статистики"""
        timestamp = int(time.time() * 1000)
        
        stats1 = Statistics(
            metric_name="test_metric", value=100, category=StatisticCategory.SYSTEM,
            timestamp=timestamp
        )
        stats2 = Statistics(
            metric_name="test_metric", value=200, category=StatisticCategory.SYSTEM,
            timestamp=timestamp
        )
        stats3 = Statistics(
            metric_name="different_metric", value=100, category=StatisticCategory.SYSTEM,
            timestamp=timestamp
        )
        
        # Равенство основано на metric_id
        assert stats1 == stats2  # Same metric_id
        assert stats1 != stats3  # Different metric_id
    
    def test_string_representation(self):
        """Тест строкового представления"""
        stats = Statistics.create_timing(
            name="execution_time",
            category=StatisticCategory.PERFORMANCE,
            duration_ms=125.75,
            symbol="BTCUSDT"
        )
        
        str_repr = str(stats)
        assert "execution_time" in str_repr
        assert "125.75" in str_repr
        assert "BTCUSDT" in str_repr