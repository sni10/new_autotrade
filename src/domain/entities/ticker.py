# src/domain/entities/ticker.py
from typing import Dict, Any

class Ticker:
    """
    Сущность, представляющая рыночный тикер.
    Содержит все унифицированные поля из ccxt.
    """
    def __init__(self, data: Dict[str, Any]):
        # Основные поля
        self.symbol: str = data.get("symbol")
        self.timestamp: int = data.get("timestamp")
        self.datetime: str = data.get("datetime")
        
        # Ценовые показатели
        self.high: float = data.get("high")
        self.low: float = data.get("low")
        self.bid: float = data.get("bid")
        self.bidVolume: float = data.get("bidVolume")
        self.ask: float = data.get("ask")
        self.askVolume: float = data.get("askVolume")
        self.vwap: float = data.get("vwap")
        self.open: float = data.get("open")
        self.close: float = data.get("close")
        self.last: float = data.get("last")
        self.previousClose: float = data.get("previousClose")
        
        # Изменения
        self.change: float = data.get("change")
        self.percentage: float = data.get("percentage")
        self.average: float = data.get("average")
        
        # Объемы
        self.baseVolume: float = data.get("baseVolume")
        self.quoteVolume: float = data.get("quoteVolume")
        
        # Сырые данные и наши кастомные поля
        self.info: dict = data.get("info", {})
        self.signals: dict = {} # Для обогащения данными индикаторов

    def update_signals(self, signals: Dict[str, Any]):
        """Обновляет тикер данными от индикаторов."""
        self.signals.update(signals)
    
    # Методы для безопасного доступа к сигналам
    def get_macd_signal(self) -> float:
        """Получить MACD сигнал"""
        return self.signals.get('macd', 0.0)
    
    def get_macd_signal_line(self) -> float:
        """Получить MACD signal line"""
        return self.signals.get('macdsignal', 0.0)
    
    def get_macd_histogram(self) -> float:
        """Получить MACD гистограмму"""
        return self.signals.get('macdhist', 0.0)
    
    def get_sma_7(self) -> float:
        """Получить SMA-7"""
        return self.signals.get('sma_7', 0.0)
    
    def get_sma_25(self) -> float:
        """Получить SMA-25"""
        return self.signals.get('sma_25', 0.0)
    
    def get_rsi_5(self) -> float:
        """Получить RSI-5"""
        return self.signals.get('rsi_5', 0.0)
    
    def get_rsi_15(self) -> float:
        """Получить RSI-15"""
        return self.signals.get('rsi_15', 0.0)
    
    def get_signal(self, signal_name: str, default_value: float = 0.0) -> float:
        """Безопасный доступ к любому сигналу"""
        return self.signals.get(signal_name, default_value)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ticker':
        """Создает сущность Ticker из словаря."""
        return cls(data)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует сущность в словарь для сохранения."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "datetime": self.datetime,
            "high": self.high,
            "low": self.low,
            "bid": self.bid,
            "bidVolume": self.bidVolume,
            "ask": self.ask,
            "askVolume": self.askVolume,
            "vwap": self.vwap,
            "open": self.open,
            "close": self.close,
            "last": self.last,
            "previousClose": self.previousClose,
            "change": self.change,
            "percentage": self.percentage,
            "average": self.average,
            "baseVolume": self.baseVolume,
            "quoteVolume": self.quoteVolume,
            "info": self.info,
            "signals": self.signals
        }

    def __repr__(self):
        return f"<Ticker(symbol={self.symbol}, last_price={self.last}, timestamp={self.timestamp})>"
