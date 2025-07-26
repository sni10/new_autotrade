from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class OrderBookLevel:
    """Уровень стакана заявок (цена и объем)"""
    price: float
    volume: float


@dataclass 
class OrderBook:
    """Сущность данных стакана заявок"""
    
    def __init__(self, symbol: str, timestamp: int, bids: List[List[float]], asks: List[List[float]]):
        self.symbol = symbol
        self.timestamp = timestamp
        self.bids = [OrderBookLevel(price=bid[0], volume=bid[1]) for bid in bids]
        self.asks = [OrderBookLevel(price=ask[0], volume=ask[1]) for ask in asks]
        self._spread = None
        self._volume = None
    
    @property
    def best_bid(self) -> Optional[float]:
        """Лучшая цена покупки"""
        return self.bids[0].price if self.bids else None
    
    @property
    def best_ask(self) -> Optional[float]:
        """Лучшая цена продажи"""
        return self.asks[0].price if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        """Спред между лучшими ценами"""
        if self._spread is None and self.best_bid and self.best_ask:
            self._spread = self.best_ask - self.best_bid
        return self._spread
    
    @property
    def spread_percent(self) -> Optional[float]:
        """Спред в процентах"""
        if self.spread and self.best_bid:
            return (self.spread / self.best_bid) * 100
        return None
    
    @property
    def total_bid_volume(self) -> float:
        """Общий объем заявок на покупку"""
        return sum(level.volume for level in self.bids)
    
    @property
    def total_ask_volume(self) -> float:
        """Общий объем заявок на продажу"""
        return sum(level.volume for level in self.asks)
    
    @property
    def volume_imbalance(self) -> float:
        """Дисбаланс объемов в %"""
        total_volume = self.total_bid_volume + self.total_ask_volume
        if total_volume > 0:
            return ((self.total_bid_volume - self.total_ask_volume) / total_volume) * 100
        return 0.0
    
    def get_levels_in_range(self, percent_range: float = 5.0) -> Dict[str, List[OrderBookLevel]]:
        """Получить уровни в пределах заданного % от лучших цен"""
        if not self.best_bid or not self.best_ask:
            return {"bids": [], "asks": []}
        
        mid_price = (self.best_bid + self.best_ask) / 2
        price_threshold = mid_price * (percent_range / 100)
        
        filtered_bids = [
            level for level in self.bids 
            if level.price >= mid_price - price_threshold
        ]
        filtered_asks = [
            level for level in self.asks 
            if level.price <= mid_price + price_threshold
        ]
        
        return {"bids": filtered_bids, "asks": filtered_asks}
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для сериализации"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "bids": [[level.price, level.volume] for level in self.bids],
            "asks": [[level.price, level.volume] for level in self.asks],
            "spread": self.spread,
            "spread_percent": self.spread_percent,
            "volume_imbalance": self.volume_imbalance
        }
    
    def to_json(self) -> str:
        """Конвертация в JSON строку"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderBook':
        """Создание из словаря"""
        return cls(
            symbol=data["symbol"],
            timestamp=data["timestamp"],
            bids=data["bids"],
            asks=data["asks"]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'OrderBook':
        """Создание из JSON строки"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        return f"OrderBook({self.symbol}, {self.spread:.6f} spread, {len(self.bids)}x{len(self.asks)} levels)"