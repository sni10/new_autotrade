from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import json
from enum import Enum


class IndicatorType(Enum):
    """Типы индикаторов"""
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    MACD_SIGNAL = "macd_signal"
    MACD_HISTOGRAM = "macd_histogram"
    BOLLINGER_UPPER = "bollinger_upper"
    BOLLINGER_MIDDLE = "bollinger_middle"
    BOLLINGER_LOWER = "bollinger_lower"
    VOLUME = "volume"
    VOLATILITY = "volatility"


class IndicatorLevel(Enum):
    """Уровень сложности вычисления индикатора"""
    FAST = "fast"      # Каждый тик
    MEDIUM = "medium"  # Каждые 10 тиков
    HEAVY = "heavy"    # Каждые 50 тиков


@dataclass
class IndicatorData:
    """Сущность для хранения вычисленных индикаторов"""
    
    def __init__(
        self,
        symbol: str,
        timestamp: int,
        indicator_type: IndicatorType,
        value: float,
        period: Optional[int] = None,
        level: IndicatorLevel = IndicatorLevel.FAST,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.symbol = symbol
        self.timestamp = timestamp
        self.indicator_type = indicator_type
        self.value = value
        self.period = period
        self.level = level
        self.metadata = metadata or {}
        self.created_at = datetime.now()
    
    @property
    def indicator_name(self) -> str:
        """Полное имя индикатора с периодом"""
        if self.period:
            return f"{self.indicator_type.value}_{self.period}"
        return self.indicator_type.value
    
    def is_valid(self) -> bool:
        """Проверка валидности данных индикатора"""
        return (
            self.symbol is not None and
            self.timestamp > 0 and
            self.value is not None and
            not (isinstance(self.value, float) and (
                self.value != self.value or  # NaN check
                abs(self.value) == float('inf')  # Infinity check
            ))
        )
    
    def is_bullish_signal(self) -> bool:
        """Определение бычьего сигнала для типичных индикаторов"""
        if self.indicator_type == IndicatorType.RSI:
            return 30 <= self.value <= 70  # Нейтральная зона
        elif self.indicator_type == IndicatorType.MACD_HISTOGRAM:
            return self.value > 0
        elif self.indicator_type in [IndicatorType.SMA, IndicatorType.EMA]:
            # Для SMA/EMA нужен контекст цены, возвращаем None
            return None
        return None
    
    def is_bearish_signal(self) -> bool:
        """Определение медвежьего сигнала для типичных индикаторов"""
        if self.indicator_type == IndicatorType.RSI:
            return self.value > 70 or self.value < 30  # Перекупленность/перепроданность
        elif self.indicator_type == IndicatorType.MACD_HISTOGRAM:
            return self.value < 0
        return None
    
    def get_signal_strength(self) -> float:
        """Получение силы сигнала от 0 до 1"""
        if self.indicator_type == IndicatorType.RSI:
            if self.value > 70:
                return min((self.value - 70) / 30, 1.0)  # Сила перекупленности
            elif self.value < 30:
                return min((30 - self.value) / 30, 1.0)  # Сила перепроданности
            else:
                return 0.0  # Нейтральная зона
        elif self.indicator_type == IndicatorType.MACD_HISTOGRAM:
            return min(abs(self.value) / 100, 1.0)  # Нормализация к [-1, 1]
        return 0.5  # Дефолтная средняя сила
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сериализации"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "indicator_type": self.indicator_type.value,
            "value": self.value,
            "period": self.period,
            "level": self.level.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Конвертация в JSON строку"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndicatorData':
        """Создание из словаря"""
        indicator = cls(
            symbol=data["symbol"],
            timestamp=data["timestamp"],
            indicator_type=IndicatorType(data["indicator_type"]),
            value=data["value"],
            period=data.get("period"),
            level=IndicatorLevel(data.get("level", "fast")),
            metadata=data.get("metadata", {})
        )
        if "created_at" in data:
            indicator.created_at = datetime.fromisoformat(data["created_at"])
        return indicator
    
    @classmethod
    def from_json(cls, json_str: str) -> 'IndicatorData':
        """Создание из JSON строки"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        return f"IndicatorData({self.indicator_name}={self.value:.6f}, {self.symbol}, level={self.level.value})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, IndicatorData):
            return False
        return (
            self.symbol == other.symbol and
            self.timestamp == other.timestamp and
            self.indicator_type == other.indicator_type and
            self.period == other.period
        )