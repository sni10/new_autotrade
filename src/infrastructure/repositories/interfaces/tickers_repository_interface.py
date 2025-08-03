# src/infrastructure/repositories/interfaces/tickers_repository_interface.py
from abc import abstractmethod
from typing import List, Optional
from datetime import datetime
from domain.entities.ticker import Ticker
from ..base.base_repository import StreamingRepository

class ITickersRepository(StreamingRepository[Ticker]):
    """
    Интерфейс репозитория тикеров (ПОТОКОВЫЕ ДАННЫЕ).
    
    Принципы потоковых данных:
    - Накопление в памяти (DataFrame)
    - Периодические дампы в Parquet
    - Очистка старых данных для экономии памяти
    - Высокая скорость записи (миллионы тикеров)
    """
    
    @abstractmethod
    def get_latest_ticker(self, symbol: str) -> Optional[Ticker]:
        """Получить последний тикер по символу"""
        pass
    
    @abstractmethod
    def get_price_history(self, symbol: str, limit: int = 100) -> List[float]:
        """Получить историю цен"""
        pass
    
    @abstractmethod
    def get_tickers_by_symbol(self, symbol: str, limit: int = 1000) -> List[Ticker]:
        """Получить тикеры по символу с лимитом"""
        pass
    
    @abstractmethod
    def get_volume_history(self, symbol: str, limit: int = 100) -> List[float]:
        """Получить историю объемов"""
        pass