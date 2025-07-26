from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.domain.entities.indicator_data import IndicatorData, IndicatorType, IndicatorLevel


class IIndicatorRepository(ABC):
    """Интерфейс репозитория для сохранения и извлечения данных индикаторов"""
    
    @abstractmethod
    async def save(self, indicator: IndicatorData) -> None:
        """Сохранить данные индикатора"""
        pass
    
    @abstractmethod
    async def save_batch(self, indicators: List[IndicatorData]) -> None:
        """Сохранить пакет индикаторов"""
        pass
    
    @abstractmethod
    async def get_by_symbol_and_type(
        self, 
        symbol: str, 
        indicator_type: IndicatorType,
        period: Optional[int] = None,
        limit: int = 100
    ) -> List[IndicatorData]:
        """Получить индикаторы по символу и типу"""
        pass
    
    @abstractmethod
    async def get_latest(
        self, 
        symbol: str, 
        indicator_type: IndicatorType,
        period: Optional[int] = None
    ) -> Optional[IndicatorData]:
        """Получить последний индикатор по символу и типу"""
        pass
    
    @abstractmethod
    async def get_by_level(
        self, 
        symbol: str, 
        level: IndicatorLevel,
        limit: int = 100
    ) -> List[IndicatorData]:
        """Получить индикаторы по уровню сложности"""
        pass
    
    @abstractmethod
    async def get_by_time_range(
        self, 
        symbol: str,
        start_timestamp: int,
        end_timestamp: int,
        indicator_type: Optional[IndicatorType] = None
    ) -> List[IndicatorData]:
        """Получить индикаторы за период времени"""
        pass
    
    @abstractmethod
    async def delete_old(self, symbol: str, older_than_timestamp: int) -> int:
        """Удалить старые индикаторы (возвращает количество удаленных)"""
        pass
    
    @abstractmethod
    async def get_available_indicators(self, symbol: str) -> Dict[str, List[int]]:
        """Получить доступные типы индикаторов и их периоды для символа"""
        pass
    
    @abstractmethod
    async def count_by_symbol(self, symbol: str) -> int:
        """Подсчитать количество индикаторов для символа"""
        pass
    
    @abstractmethod
    async def get_all_symbols(self) -> List[str]:
        """Получить все символы, для которых есть индикаторы"""
        pass