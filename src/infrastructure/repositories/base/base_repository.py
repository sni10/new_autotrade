# src/infrastructure/repositories/base/base_repository.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
import pandas as pd
from datetime import datetime

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    Базовый интерфейс для всех репозиториев в двухуровневой архитектуре.
    Определяет общие операции CRUD для любых сущностей.
    
    Generic параметр T - тип сущности (Deal, Order, Ticker, etc.)
    """
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """Сохранить сущность"""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Получить сущность по ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Получить все сущности"""
        pass
    
    @abstractmethod
    def delete_by_id(self, entity_id: int) -> bool:
        """Удалить сущность по ID"""
        pass
    
    def count(self) -> int:
        """Получить количество сущностей"""
        return len(self.get_all())
    
    def exists(self, entity_id: int) -> bool:
        """Проверить существование сущности по ID"""
        return self.get_by_id(entity_id) is not None


class AtomicRepository(BaseRepository[T]):
    """
    Интерфейс для атомарных данных (Deal, Order).
    
    Особенности:
    - Данные критически важны (торговые операции)
    - Сразу синхронизируются с персистентным хранилищем
    - Высокая надежность приоритетнее скорости
    - Поддержка транзакций
    """
    
    @abstractmethod
    async def sync_to_persistent(self, entity: T) -> None:
        """Синхронизация с персистентным хранилищем"""
        pass
    
    @abstractmethod
    async def load_from_persistent(self) -> List[T]:
        """Загрузка из персистентного хранилища"""
        pass
    
    @abstractmethod
    async def backup_to_persistent(self) -> int:
        """Резервное копирование всех данных в персистентное хранилище"""
        pass


class StreamingRepository(BaseRepository[T]):
    """
    Интерфейс для потоковых данных (Ticker, OrderBook, IndicatorData).
    
    Особенности:
    - Большие объемы данных (миллионы записей)
    - Накопление в памяти + периодические дампы
    - Скорость записи приоритетнее надежности
    - Автоматическая очистка старых данных
    """
    
    @abstractmethod
    def get_last_n(self, n: int) -> List[T]:
        """Получить последние N записей"""
        pass
    
    @abstractmethod
    def get_by_time_range(self, start_time: datetime, end_time: datetime) -> List[T]:
        """Получить записи за период времени"""
        pass
    
    @abstractmethod
    async def dump_to_persistent(self, batch_size: int = 10000) -> int:
        """Сброс накопленных данных в персистентное хранилище"""
        pass
    
    @abstractmethod
    def clear_old_data(self, keep_last_n: int = 100000) -> int:
        """Очистка старых данных из памяти"""
        pass
    
    @abstractmethod
    def get_memory_usage_mb(self) -> float:
        """Получить использование памяти в МБ"""
        pass


class MemoryFirstRepository(ABC, Generic[T]):
    """
    Базовый класс для двухуровневой архитектуры:
    - Уровень 1: DataFrame в памяти (скорость наносекунд)
    - Уровень 2: Персистентное хранилище (надежность)
    
    Принципы:
    - Все операции чтения/записи работают с DataFrame
    - Персистентность полностью прозрачна для клиентов
    - Фоновая синхронизация не блокирует торговлю
    - Автоматическое восстановление после перезапуска
    """
    
    def __init__(self, persistent_provider=None):
        self.df: pd.DataFrame = pd.DataFrame()
        self.persistent_provider = persistent_provider
        self._next_id = 1
        self._is_initialized = False
    
    @abstractmethod
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Преобразование сущности в словарь для DataFrame"""
        pass
    
    @abstractmethod
    def _dict_to_entity(self, data: Dict[str, Any]) -> T:
        """Преобразование словаря из DataFrame в сущность"""
        pass
    
    @abstractmethod
    def _get_dataframe_columns(self) -> List[str]:
        """Получить список колонок для DataFrame"""
        pass
    
    @abstractmethod
    def _get_id_column(self) -> str:
        """Получить имя колонки с ID"""
        pass
    
    def _initialize_dataframe(self):
        """Инициализация пустого DataFrame"""
        if self.df.empty:
            self.df = pd.DataFrame(columns=self._get_dataframe_columns())
            # Устанавливаем правильные типы данных для оптимизации
            self._optimize_dataframe_dtypes()
    
    def _optimize_dataframe_dtypes(self):
        """Оптимизация типов данных DataFrame для экономии памяти"""
        # Переопределяется в наследниках для специфичных оптимизаций
        pass
    
    async def _sync_to_persistent_async(self, entity_dict: Dict[str, Any]):
        """Фоновая синхронизация с персистентным хранилищем"""
        if self.persistent_provider:
            try:
                await self.persistent_provider.save_entity(entity_dict)
            except Exception as e:
                # Логируем ошибку, но не прерываем торговлю
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"⚠️ Persistent sync error: {e}")
    
    def _get_next_id(self) -> int:
        """Получить следующий ID для новой сущности"""
        current_id = self._next_id
        self._next_id += 1
        return current_id
    
    def _update_next_id_from_dataframe(self):
        """Обновить _next_id на основе максимального ID в DataFrame"""
        if not self.df.empty:
            id_column = self._get_id_column()
            if id_column in self.df.columns:
                max_id = self.df[id_column].max()
                if pd.notna(max_id):
                    self._next_id = int(max_id) + 1
    
    def get_dataframe_copy(self) -> pd.DataFrame:
        """Получить копию DataFrame для анализа (безопасно для внешнего использования)"""
        return self.df.copy()
    
    def get_memory_usage_info(self) -> Dict[str, Any]:
        """Получить информацию об использовании памяти"""
        if self.df.empty:
            return {"rows": 0, "memory_mb": 0, "columns": 0}
        
        memory_usage = self.df.memory_usage(deep=True).sum()
        return {
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "memory_mb": memory_usage / (1024 * 1024),
            "dtypes": dict(self.df.dtypes)
        }