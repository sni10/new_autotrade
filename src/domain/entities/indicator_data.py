# src/domain/entities/indicator_data.py
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class IndicatorData:
    """
    Сущность, представляющая снимок рассчитанных индикаторов
    для конкретной торговой пары в определенный момент времени.
    """
    symbol: str
    timestamp: int
    # Гибкий словарь для хранения любых индикаторов.
    # Например: {'macd': 123.45, 'macdsignal': 120.1, 'rsi_5': 65.7}
    values: Dict[str, float]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndicatorData':
        """Создает объект из словаря."""
        return cls(
            symbol=data.get("symbol"),
            timestamp=data.get("timestamp"),
            values=data.get("values", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует данные индикаторов в словарь."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "values": self.values,
        }

    def __repr__(self):
        return (f"<IndicatorData(symbol={self.symbol}, timestamp={self.timestamp}, "
                f"values_count={len(self.values)})>")
