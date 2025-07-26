from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.domain.entities.order_book import OrderBook


class IOrderBookRepository(ABC):
    """Интерфейс репозитория для сохранения и извлечения данных стакана заявок"""
    
    @abstractmethod
    async def save(self, order_book: OrderBook) -> None:
        """Сохранить данные стакана"""
        pass
    
    @abstractmethod
    async def get_latest(self, symbol: str) -> Optional[OrderBook]:
        """Получить последний стакан для символа"""
        pass
    
    @abstractmethod
    async def get_by_symbol(self, symbol: str, limit: int = 100) -> List[OrderBook]:
        """Получить историю стаканов для символа"""
        pass
    
    @abstractmethod
    async def get_by_time_range(
        self, 
        symbol: str,
        start_timestamp: int,
        end_timestamp: int
    ) -> List[OrderBook]:
        """Получить стаканы за период времени"""
        pass
    
    @abstractmethod
    async def get_spread_history(
        self, 
        symbol: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Получить историю спредов"""
        pass
    
    @abstractmethod
    async def get_volume_imbalance_history(
        self, 
        symbol: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Получить историю дисбаланса объемов"""
        pass
    
    @abstractmethod
    async def delete_old(self, symbol: str, older_than_timestamp: int) -> int:
        """Удалить старые стаканы (возвращает количество удаленных)"""
        pass
    
    @abstractmethod
    async def get_average_spread(
        self, 
        symbol: str, 
        time_window_ms: int = 300000  # 5 минут
    ) -> Optional[float]:
        """Получить средний спред за период"""
        pass
    
    @abstractmethod
    async def get_liquidity_metrics(
        self, 
        symbol: str,
        time_window_ms: int = 300000
    ) -> Dict[str, float]:
        """Получить метрики ликвидности за период"""
        pass
    
    @abstractmethod
    async def count_by_symbol(self, symbol: str) -> int:
        """Подсчитать количество записей стакана для символа"""
        pass
    
    @abstractmethod
    async def get_all_symbols(self) -> List[str]:
        """Получить все символы, для которых есть данные стакана"""
        pass