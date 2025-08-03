# src/infrastructure/repositories/interfaces/order_books_repository_interface.py
from abc import abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
from domain.entities.order_book import OrderBook
from ..base.base_repository import StreamingRepository

class IOrderBooksRepository(StreamingRepository[OrderBook]):
    """
    Интерфейс репозитория стаканов ордеров (ПОТОКОВЫЕ ДАННЫЕ).
    
    Принципы потоковых данных:
    - Накопление в памяти (DataFrame)
    - Периодические дампы в Parquet
    - Очистка старых данных для экономии памяти
    - Высокая скорость записи (тысячи обновлений в секунду)
    """
    
    @abstractmethod
    def get_latest_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Получить последний стакан по символу"""
        pass
    
    @abstractmethod
    def get_spread_history(self, symbol: str, limit: int = 100) -> List[float]:
        """Получить историю спредов"""
        pass
    
    @abstractmethod
    def get_order_books_by_symbol(self, symbol: str, limit: int = 1000) -> List[OrderBook]:
        """Получить стаканы по символу с лимитом"""
        pass
    
    @abstractmethod
    def get_liquidity_history(self, symbol: str, limit: int = 100) -> List[Tuple[float, float]]:
        """Получить историю ликвидности (bid_volume, ask_volume)"""
        pass
    
    @abstractmethod
    def get_best_prices_history(self, symbol: str, limit: int = 100) -> List[Tuple[float, float]]:
        """Получить историю лучших цен (best_bid, best_ask)"""
        pass