# src/domain/entities/order_book.py
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class OrderBook:
    """
    Сущность, представляющая снимок стакана ордеров.
    Соответствует формату данных ccxt.
    """
    symbol: str
    timestamp: int
    bids: List[List[float]] = field(default_factory=list)  # [[price, quantity], ...]
    asks: List[List[float]] = field(default_factory=list)  # [[price, quantity], ...]
    
    # Дополнительные поля из ccxt, которые могут быть полезны
    datetime: str = None
    nonce: int = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderBook':
        """
        Создает сущность OrderBook из словаря, полученного от ccxt.
        """
        return cls(
            symbol=data.get("symbol"),
            timestamp=data.get("timestamp"),
            bids=data.get("bids", []),
            asks=data.get("asks", []),
            datetime=data.get("datetime"),
            nonce=data.get("nonce"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует стакан в словарь для сохранения."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "bids": self.bids,
            "asks": self.asks,
            "datetime": self.datetime,
            "nonce": self.nonce,
        }

    def __repr__(self):
        return (f"<OrderBook(symbol={self.symbol}, timestamp={self.timestamp}, "
                f"bids_depth={len(self.bids)}, asks_depth={len(self.asks)})>")
