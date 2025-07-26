from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from src.domain.entities.statistics import Statistics, StatisticCategory, StatisticType


class IStatisticsRepository(ABC):
    """Интерфейс репозитория для сохранения и извлечения статистических данных"""
    
    @abstractmethod
    async def save(self, statistic: Statistics) -> None:
        """Сохранить статистику"""
        pass
    
    @abstractmethod
    async def save_batch(self, statistics: List[Statistics]) -> None:
        """Сохранить пакет статистик"""
        pass
    
    @abstractmethod
    async def get_by_metric_name(
        self, 
        metric_name: str,
        category: Optional[StatisticCategory] = None,
        limit: int = 100
    ) -> List[Statistics]:
        """Получить статистику по имени метрики"""
        pass
    
    @abstractmethod
    async def get_latest(
        self, 
        metric_name: str,
        category: StatisticCategory,
        symbol: Optional[str] = None
    ) -> Optional[Statistics]:
        """Получить последнюю статистику по метрике"""
        pass
    
    @abstractmethod
    async def get_by_category(
        self, 
        category: StatisticCategory,
        limit: int = 100
    ) -> List[Statistics]:
        """Получить статистику по категории"""
        pass
    
    @abstractmethod
    async def get_by_type(
        self, 
        metric_type: StatisticType,
        limit: int = 100
    ) -> List[Statistics]:
        """Получить статистику по типу"""
        pass
    
    @abstractmethod
    async def get_by_symbol(
        self, 
        symbol: str,
        category: Optional[StatisticCategory] = None,
        limit: int = 100
    ) -> List[Statistics]:
        """Получить статистику по символу"""
        pass
    
    @abstractmethod
    async def get_by_tags(
        self, 
        tags: Dict[str, str],
        category: Optional[StatisticCategory] = None,
        limit: int = 100
    ) -> List[Statistics]:
        """Получить статистику по тегам"""
        pass
    
    @abstractmethod
    async def get_by_time_range(
        self, 
        start_timestamp: int,
        end_timestamp: int,
        category: Optional[StatisticCategory] = None,
        metric_name: Optional[str] = None
    ) -> List[Statistics]:
        """Получить статистику за период времени"""
        pass
    
    @abstractmethod
    async def increment_counter(
        self, 
        metric_name: str,
        category: StatisticCategory,
        delta: Union[int, float] = 1,
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Statistics:
        """Увеличить счетчик (создать или обновить)"""
        pass
    
    @abstractmethod
    async def update_gauge(
        self, 
        metric_name: str,
        category: StatisticCategory,
        value: Union[int, float],
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Statistics:
        """Обновить датчик (создать или обновить)"""
        pass
    
    @abstractmethod
    async def record_timing(
        self, 
        metric_name: str,
        category: StatisticCategory,
        duration_ms: float,
        symbol: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Statistics:
        """Записать время выполнения"""
        pass
    
    @abstractmethod
    async def get_aggregated_stats(
        self, 
        metric_name: str,
        category: StatisticCategory,
        time_window_ms: int = 3600000,  # 1 час
        aggregation: str = "avg"  # avg, sum, min, max, count
    ) -> Optional[float]:
        """Получить агрегированную статистику за период"""
        pass
    
    @abstractmethod
    async def get_performance_summary(
        self, 
        time_window_ms: int = 86400000  # 24 часа
    ) -> Dict[str, Any]:
        """Получить сводку производительности за период"""
        pass
    
    @abstractmethod
    async def get_stale_metrics(
        self, 
        max_age_seconds: float = 300
    ) -> List[Statistics]:
        """Получить устаревшие метрики"""
        pass
    
    @abstractmethod
    async def delete_old(
        self, 
        older_than_timestamp: int,
        category: Optional[StatisticCategory] = None
    ) -> int:
        """Удалить старую статистику (возвращает количество удаленных)"""
        pass
    
    @abstractmethod
    async def get_all_metric_names(
        self, 
        category: Optional[StatisticCategory] = None
    ) -> List[str]:
        """Получить все имена метрик"""
        pass
    
    @abstractmethod
    async def get_all_symbols(self) -> List[str]:
        """Получить все символы, для которых есть статистика"""
        pass