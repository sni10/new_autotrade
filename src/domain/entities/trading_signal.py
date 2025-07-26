from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from enum import Enum


class SignalType(Enum):
    """Типы торговых сигналов"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"
    WEAK_BUY = "weak_buy"
    WEAK_SELL = "weak_sell"


class SignalSource(Enum):
    """Источники сигналов"""
    MACD = "macd"
    RSI = "rsi"
    SMA_CROSSOVER = "sma_crossover"
    BOLLINGER_BANDS = "bollinger_bands"
    ORDERBOOK_ANALYSIS = "orderbook_analysis"
    VOLUME_ANALYSIS = "volume_analysis"
    COMBINED = "combined"


class SignalConfidence(Enum):
    """Уровни уверенности в сигнале"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class TradingSignal:
    """Сущность торгового сигнала"""
    
    def __init__(
        self,
        symbol: str,
        timestamp: int,
        signal_type: SignalType,
        source: SignalSource,
        strength: float,
        confidence: float = 0.5,
        price: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.symbol = symbol
        self.timestamp = timestamp
        self.signal_type = signal_type
        self.source = source
        self.strength = self._validate_strength(strength)
        self.confidence = self._validate_confidence(confidence)
        self.price = price
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        
        # Добавляем ID для уникальности
        self.signal_id = f"{symbol}_{timestamp}_{source.value}_{signal_type.value}"
    
    def _validate_strength(self, strength: float) -> float:
        """Валидация силы сигнала (0.0 - 1.0)"""
        return max(0.0, min(1.0, strength))
    
    def _validate_confidence(self, confidence: float) -> float:
        """Валидация уверенности в сигнале (0.0 - 1.0)"""
        return max(0.0, min(1.0, confidence))
    
    @property
    def is_actionable(self) -> bool:
        """Проверка, можно ли действовать по этому сигналу"""
        return (
            self.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.STRONG_BUY, SignalType.STRONG_SELL] and
            self.confidence >= 0.6 and
            self.strength >= 0.3
        )
    
    @property
    def is_strong(self) -> bool:
        """Проверка на сильный сигнал"""
        return (
            self.signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL] or
            (self.strength >= 0.7 and self.confidence >= 0.8)
        )
    
    @property
    def is_bullish(self) -> bool:
        """Проверка на бычий сигнал"""
        return self.signal_type in [SignalType.BUY, SignalType.STRONG_BUY, SignalType.WEAK_BUY]
    
    @property
    def is_bearish(self) -> bool:
        """Проверка на медвежий сигнал"""
        return self.signal_type in [SignalType.SELL, SignalType.STRONG_SELL, SignalType.WEAK_SELL]
    
    @property
    def score(self) -> float:
        """Общий скор сигнала (strength * confidence)"""
        return self.strength * self.confidence
    
    def get_recommendation(self) -> str:
        """Получение текстовой рекомендации"""
        if not self.is_actionable:
            return "HOLD - сигнал недостаточно сильный"
        
        if self.is_strong:
            action = "ПОКУПАТЬ" if self.is_bullish else "ПРОДАВАТЬ"
            return f"{action} - сильный сигнал (score: {self.score:.2f})"
        else:
            action = "рассмотреть покупку" if self.is_bullish else "рассмотреть продажу"
            return f"{action.capitalize()} - слабый сигнал (score: {self.score:.2f})"
    
    def conflicts_with(self, other_signal: 'TradingSignal') -> bool:
        """Проверка конфликта с другим сигналом"""
        if not isinstance(other_signal, TradingSignal):
            return False
        
        # Проверяем временную близость (в пределах 1 минуты)
        time_diff = abs(self.timestamp - other_signal.timestamp)
        if time_diff > 60000:  # 60 секунд в миллисекундах
            return False
        
        # Проверяем противоположные сигналы
        return (
            self.symbol == other_signal.symbol and
            (
                (self.is_bullish and other_signal.is_bearish) or
                (self.is_bearish and other_signal.is_bullish)
            )
        )
    
    def combine_with(self, other_signal: 'TradingSignal') -> Optional['TradingSignal']:
        """Комбинирование с другим сигналом того же направления"""
        if (
            not isinstance(other_signal, TradingSignal) or
            self.symbol != other_signal.symbol or
            self.conflicts_with(other_signal)
        ):
            return None
        
        # Комбинируем только сигналы одного направления
        if not ((self.is_bullish and other_signal.is_bullish) or 
                (self.is_bearish and other_signal.is_bearish)):
            return None
        
        # Создаем комбинированный сигнал
        combined_strength = (self.strength + other_signal.strength) / 2
        combined_confidence = min(self.confidence + other_signal.confidence, 1.0)
        
        # Выбираем более сильный тип сигнала
        if self.strength >= other_signal.strength:
            signal_type = self.signal_type
        else:
            signal_type = other_signal.signal_type
        
        # Метаданные комбинирования
        combined_metadata = {
            "combined_from": [self.signal_id, other_signal.signal_id],
            "sources": [self.source.value, other_signal.source.value],
            "original_scores": [self.score, other_signal.score]
        }
        
        return TradingSignal(
            symbol=self.symbol,
            timestamp=min(self.timestamp, other_signal.timestamp),
            signal_type=signal_type,
            source=SignalSource.COMBINED,
            strength=combined_strength,
            confidence=combined_confidence,
            price=self.price or other_signal.price,
            metadata=combined_metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сериализации"""
        return {
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "signal_type": self.signal_type.value,
            "source": self.source.value,
            "strength": self.strength,
            "confidence": self.confidence,
            "price": self.price,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "score": self.score,
            "is_actionable": self.is_actionable,
            "is_strong": self.is_strong
        }
    
    def to_json(self) -> str:
        """Конвертация в JSON строку"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingSignal':
        """Создание из словаря"""
        signal = cls(
            symbol=data["symbol"],
            timestamp=data["timestamp"],
            signal_type=SignalType(data["signal_type"]),
            source=SignalSource(data["source"]),
            strength=data["strength"],
            confidence=data["confidence"],
            price=data.get("price"),
            metadata=data.get("metadata", {})
        )
        if "created_at" in data:
            signal.created_at = datetime.fromisoformat(data["created_at"])
        return signal
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TradingSignal':
        """Создание из JSON строки"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        return f"TradingSignal({self.signal_type.value}, {self.source.value}, score={self.score:.2f}, {self.symbol})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TradingSignal):
            return False
        return self.signal_id == other.signal_id