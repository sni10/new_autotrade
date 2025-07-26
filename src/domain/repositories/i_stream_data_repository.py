from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
import json


class IStreamDataRepository(ABC):
    """
    Интерфейс репозитория для высокочастотных потоковых данных (тикеры, стаканы)
    Работает с JSON-массивами напрямую для оптимизации производительности
    """
    
    @abstractmethod
    async def append_ticker_data(
        self, 
        symbol: str, 
        ticker_data: Dict[str, Any],
        max_history_size: int = 1000
    ) -> None:
        """Добавить данные тикера в JSON-массив"""
        pass
    
    @abstractmethod
    async def get_ticker_history(
        self, 
        symbol: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Получить историю тикеров как список словарей"""
        pass
    
    @abstractmethod
    async def get_latest_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Получить последний тикер"""
        pass
    
    @abstractmethod
    async def get_price_history(
        self, 
        symbol: str, 
        limit: int = 200
    ) -> List[float]:
        """Получить только историю цен для вычисления индикаторов"""
        pass
    
    @abstractmethod
    async def append_orderbook_snapshot(
        self, 
        symbol: str, 
        orderbook_data: Dict[str, Any],
        max_history_size: int = 100
    ) -> None:
        """Добавить снимок стакана заявок"""
        pass
    
    @abstractmethod
    async def get_orderbook_history(
        self, 
        symbol: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Получить историю стаканов"""
        pass
    
    @abstractmethod
    async def get_latest_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Получить последний стакан заявок"""
        pass
    
    @abstractmethod
    async def calculate_sma(
        self, 
        symbol: str, 
        period: int
    ) -> Optional[float]:
        """Вычислить SMA напрямую из JSON-данных"""
        pass
    
    @abstractmethod
    async def calculate_price_change(
        self, 
        symbol: str, 
        periods: int = 1
    ) -> Optional[Dict[str, float]]:
        """Вычислить изменение цены за N периодов"""
        pass
    
    @abstractmethod
    async def get_volatility(
        self, 
        symbol: str, 
        periods: int = 20
    ) -> Optional[float]:
        """Вычислить волатильность за N периодов"""
        pass
    
    @abstractmethod
    async def cleanup_old_data(
        self, 
        symbol: str, 
        keep_ticker_count: int = 1000,
        keep_orderbook_count: int = 100
    ) -> Dict[str, int]:
        """Очистить старые данные, оставить только последние N записей"""
        pass
    
    @abstractmethod
    async def get_data_stats(self, symbol: str) -> Dict[str, Any]:
        """Получить статистику данных (количество записей, размер, etc.)"""
        pass
    
    @abstractmethod
    async def bulk_append_tickers(
        self, 
        symbol: str, 
        ticker_batch: List[Dict[str, Any]],
        max_history_size: int = 1000
    ) -> None:
        """Добавить пакет тикеров за один раз"""
        pass
    
    @abstractmethod
    async def get_ticker_subset(
        self, 
        symbol: str, 
        start_index: int, 
        count: int
    ) -> List[Dict[str, Any]]:
        """Получить подмножество тикеров по индексам"""
        pass
    
    @abstractmethod
    async def get_tickers_by_time_range(
        self, 
        symbol: str,
        start_timestamp: int,
        end_timestamp: int
    ) -> List[Dict[str, Any]]:
        """Получить тикеры за временной интервал"""
        pass
    
    @abstractmethod
    async def compress_old_data(
        self, 
        symbol: str, 
        older_than_timestamp: int
    ) -> int:
        """Сжать старые данные (агрегировать минутные данные в часовые)"""
        pass
    
    @abstractmethod
    async def export_to_json(
        self, 
        symbol: str, 
        file_path: str,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> bool:
        """Экспортировать данные в JSON файл"""
        pass
    
    @abstractmethod
    async def import_from_json(
        self, 
        symbol: str, 
        file_path: str,
        append: bool = True
    ) -> int:
        """Импортировать данные из JSON файла"""
        pass
    
    @abstractmethod
    async def get_all_symbols(self) -> List[str]:
        """Получить все символы, для которых есть данные"""
        pass
    
    @abstractmethod
    async def delete_symbol_data(self, symbol: str) -> bool:
        """Удалить все данные для символа"""
        pass
    
    # Методы для работы с индикаторными буферами
    
    @abstractmethod
    async def update_indicator_buffer(
        self, 
        symbol: str, 
        indicator_name: str,
        value: float,
        max_buffer_size: int = 100
    ) -> None:
        """Обновить буфер индикатора"""
        pass
    
    @abstractmethod
    async def get_indicator_buffer(
        self, 
        symbol: str, 
        indicator_name: str,
        limit: int = 50
    ) -> List[float]:
        """Получить буфер индикатора"""
        pass
    
    @abstractmethod
    async def clear_indicator_buffers(self, symbol: str) -> int:
        """Очистить все буферы индикаторов для символа"""
        pass