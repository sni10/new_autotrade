import time
from typing import Dict

class Ticker:
    def __init__(self, data: Dict):
        self.timestamp = data.get("timestamp", int(time.time() * 1000))
        self.symbol = data.get("symbol", "")
        self.price = data.get("last", 0.0)
        self.open = data.get("open", 0.0)
        self.close = data.get("close", 0.0)
        self.volume = data.get("baseVolume", 0.0)
        self.high = data.get("high", 0.0)
        self.low = data.get("low", 0.0)
        self.bid = data.get("bid", 0.0)
        self.ask = data.get("ask", 0.0)
        self.trades_count = 0  # Обновится позже
        self.signals = {}  # Будем дополнять сигналами

    def update_signals(self, signals: Dict):
        """Обновляет сигналы (MACD, RSI, OBV и т. д.)"""
        self.signals.update(signals)

    def to_dict(self) -> Dict:
        """Конвертация тикера в словарь для хранения"""
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "price": self.price,
            "open": self.open,
            "close": self.close,
            "volume": self.volume,
            "high": self.high,
            "low": self.low,
            "bid": self.bid,
            "ask": self.ask,
            "trades_count": self.trades_count,
            **self.signals  # Добавляем сигналы
        }


    def __repr__(self):
        return f"<Ticker {self.symbol} {self.price} ({self.timestamp})>"