from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
from datetime import datetime
import json
from enum import Enum


class StatisticCategory(Enum):
    """Категории статистики"""
    TRADING = "trading"
    PERFORMANCE = "performance"
    ORDERS = "orders"
    DEALS = "deals"
    MARKET_DATA = "market_data"
    RISK_MANAGEMENT = "risk_management"
    SYSTEM = "system"
    TECHNICAL_INDICATORS = "technical_indicators"
    ORDER_BOOK = "order_book"


class StatisticType(Enum):
    """Типы статистических метрик"""
    COUNTER = "counter"        # Счетчик (увеличивается)
    GAUGE = "gauge"           # Текущее значение
    HISTOGRAM = "histogram"   # Распределение значений
    TIMING = "timing"         # Время выполнения
    RATE = "rate"            # Скорость (событий в секунду)
    PERCENTAGE = "percentage" # Процентное значение


@dataclass
class Statistics:
    """Сущность для метрик производительности и статистики торговли"""
    
    def __init__(
        self,
        metric_name: str,
        value: Union[int, float, str],
        category: StatisticCategory,
        metric_type: StatisticType = StatisticType.GAUGE,
        timestamp: Optional[int] = None,
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ):
        self.metric_name = metric_name
        self.value = value
        self.category = category
        self.metric_type = metric_type
        self.timestamp = timestamp or int(datetime.now().timestamp() * 1000)
        self.symbol = symbol
        self.tags = tags or {}
        self.description = description
        self.created_at = datetime.now()
        
        # Генерируем уникальный ID
        self.metric_id = self._generate_metric_id()
    
    def _generate_metric_id(self) -> str:
        """Генерация уникального ID метрики"""
        base = f"{self.category.value}_{self.metric_name}_{self.timestamp}"
        if self.symbol:
            base += f"_{self.symbol}"
        return base
    
    @property
    def full_metric_name(self) -> str:
        """Полное имя метрики с категорией"""
        return f"{self.category.value}.{self.metric_name}"
    
    def is_numeric(self) -> bool:
        """Проверка, является ли значение числовым"""
        return isinstance(self.value, (int, float))
    
    def get_numeric_value(self) -> Optional[float]:
        """Получение числового значения"""
        if self.is_numeric():
            return float(self.value)
        return None
    
    def is_percentage_valid(self) -> bool:
        """Проверка валидности процентного значения"""
        if self.metric_type == StatisticType.PERCENTAGE and self.is_numeric():
            return 0 <= self.get_numeric_value() <= 100
        return True
    
    def format_value(self) -> str:
        """Форматированное отображение значения"""
        if not self.is_numeric():
            return str(self.value)
        
        num_value = self.get_numeric_value()
        
        if self.metric_type == StatisticType.PERCENTAGE:
            return f"{num_value:.2f}%"
        elif self.metric_type == StatisticType.TIMING:
            if num_value < 1000:
                return f"{num_value:.2f}ms"
            else:
                return f"{num_value/1000:.2f}s"
        elif self.metric_type == StatisticType.RATE:
            return f"{num_value:.2f}/s"
        elif self.metric_type == StatisticType.COUNTER:
            return f"{int(num_value)}"
        else:
            return f"{num_value:.4f}"
    
    def add_tag(self, key: str, value: str) -> None:
        """Добавление тега"""
        self.tags[key] = value
    
    def remove_tag(self, key: str) -> None:
        """Удаление тега"""
        self.tags.pop(key, None)
    
    def has_tag(self, key: str, value: Optional[str] = None) -> bool:
        """Проверка наличия тега"""
        if key not in self.tags:
            return False
        if value is None:
            return True
        return self.tags[key] == value
    
    def increment(self, delta: Union[int, float] = 1) -> None:
        """Увеличение значения (для счетчиков)"""
        if self.is_numeric():
            self.value = self.get_numeric_value() + delta
            self.timestamp = int(datetime.now().timestamp() * 1000)
    
    def update_value(self, new_value: Union[int, float, str]) -> None:
        """Обновление значения"""
        self.value = new_value
        self.timestamp = int(datetime.now().timestamp() * 1000)
    
    def age_seconds(self) -> float:
        """Возраст метрики в секундах"""
        current_time = int(datetime.now().timestamp() * 1000)
        return (current_time - self.timestamp) / 1000.0
    
    def is_stale(self, max_age_seconds: float = 300) -> bool:
        """Проверка устарелости метрики"""
        return self.age_seconds() > max_age_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сериализации"""
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "category": self.category.value,
            "metric_type": self.metric_type.value,
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "tags": self.tags,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "formatted_value": self.format_value(),
            "age_seconds": self.age_seconds()
        }
    
    def to_json(self) -> str:
        """Конвертация в JSON строку"""
        return json.dumps(self.to_dict())
    
    def to_prometheus_format(self) -> str:
        """Конвертация в формат Prometheus метрик"""
        labels = []
        if self.symbol:
            labels.append(f'symbol="{self.symbol}"')
        
        for key, value in self.tags.items():
            labels.append(f'{key}="{value}"')
        
        label_str = "{" + ",".join(labels) + "}" if labels else ""
        
        if self.is_numeric():
            return f"{self.full_metric_name}{label_str} {self.get_numeric_value()}"
        else:
            return f"# {self.full_metric_name}{label_str} = {self.value}"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Statistics':
        """Создание из словаря"""
        stat = cls(
            metric_name=data["metric_name"],
            value=data["value"],
            category=StatisticCategory(data["category"]),
            metric_type=StatisticType(data.get("metric_type", "gauge")),
            timestamp=data.get("timestamp"),
            symbol=data.get("symbol"),
            tags=data.get("tags", {}),
            description=data.get("description")
        )
        if "created_at" in data:
            stat.created_at = datetime.fromisoformat(data["created_at"])
        return stat
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Statistics':
        """Создание из JSON строки"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def create_counter(cls, name: str, category: StatisticCategory, initial_value: int = 0, **kwargs) -> 'Statistics':
        """Создание счетчика"""
        return cls(name, initial_value, category, StatisticType.COUNTER, **kwargs)
    
    @classmethod
    def create_timing(cls, name: str, category: StatisticCategory, duration_ms: float, **kwargs) -> 'Statistics':
        """Создание метрики времени"""
        return cls(name, duration_ms, category, StatisticType.TIMING, **kwargs)
    
    @classmethod
    def create_percentage(cls, name: str, category: StatisticCategory, percent_value: float, **kwargs) -> 'Statistics':
        """Создание процентной метрики"""
        return cls(name, percent_value, category, StatisticType.PERCENTAGE, **kwargs)
    
    def __str__(self) -> str:
        return f"Statistics({self.full_metric_name}={self.format_value()}, {self.symbol or 'global'})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Statistics):
            return False
        return self.metric_id == other.metric_id