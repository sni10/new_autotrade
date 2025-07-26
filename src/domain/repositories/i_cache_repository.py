from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Union
import asyncio


class ICacheRepository(ABC):
    """Интерфейс репозитория для общего кэширования данных"""
    
    @abstractmethod
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Установить значение в кэш с опциональным TTL"""
        pass
    
    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """Получить значение из кэша"""
        pass
    
    @abstractmethod
    async def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """Получить несколько значений из кэша"""
        pass
    
    @abstractmethod
    async def set_multi(
        self, 
        key_value_pairs: Dict[str, Any], 
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Установить несколько значений в кэш"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        pass
    
    @abstractmethod
    async def delete_multi(self, keys: List[str]) -> int:
        """Удалить несколько значений из кэша (возвращает количество удаленных)"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа в кэше"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Установить TTL для существующего ключа"""
        pass
    
    @abstractmethod
    async def ttl(self, key: str) -> Optional[int]:
        """Получить оставшееся время жизни ключа в секундах"""
        pass
    
    @abstractmethod
    async def increment(self, key: str, delta: Union[int, float] = 1) -> Union[int, float]:
        """Увеличить числовое значение в кэше"""
        pass
    
    @abstractmethod
    async def decrement(self, key: str, delta: Union[int, float] = 1) -> Union[int, float]:
        """Уменьшить числовое значение в кэше"""
        pass
    
    @abstractmethod
    async def append_to_list(self, key: str, value: Any, max_length: Optional[int] = None) -> int:
        """Добавить элемент в список в кэше"""
        pass
    
    @abstractmethod
    async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Получить элементы списка из кэша"""
        pass
    
    @abstractmethod
    async def list_length(self, key: str) -> int:
        """Получить длину списка в кэше"""
        pass
    
    @abstractmethod
    async def add_to_set(self, key: str, value: Any) -> bool:
        """Добавить элемент в множество в кэше"""
        pass
    
    @abstractmethod
    async def is_in_set(self, key: str, value: Any) -> bool:
        """Проверить наличие элемента в множестве"""
        pass
    
    @abstractmethod
    async def get_set_members(self, key: str) -> List[Any]:
        """Получить все элементы множества"""
        pass
    
    @abstractmethod
    async def remove_from_set(self, key: str, value: Any) -> bool:
        """Удалить элемент из множества"""
        pass
    
    @abstractmethod
    async def hash_set(self, key: str, field: str, value: Any) -> None:
        """Установить поле хэша"""
        pass
    
    @abstractmethod
    async def hash_get(self, key: str, field: str, default: Any = None) -> Any:
        """Получить поле хэша"""
        pass
    
    @abstractmethod
    async def hash_get_all(self, key: str) -> Dict[str, Any]:
        """Получить все поля хэша"""
        pass
    
    @abstractmethod
    async def hash_delete(self, key: str, field: str) -> bool:
        """Удалить поле хэша"""
        pass
    
    @abstractmethod
    async def clear_namespace(self, namespace: str) -> int:
        """Очистить все ключи с определенным префиксом"""
        pass
    
    @abstractmethod
    async def get_keys_pattern(self, pattern: str) -> List[str]:
        """Получить ключи по паттерну"""
        pass
    
    @abstractmethod
    async def clear_all(self) -> None:
        """Очистить весь кэш"""
        pass
    
    @abstractmethod
    async def get_cache_info(self) -> Dict[str, Any]:
        """Получить информацию о кэше (размер, статистика)"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Очистить просроченные ключи (возвращает количество удаленных)"""
        pass
    
    # Специализированные методы для индикаторов и сигналов
    
    async def cache_indicator(
        self, 
        symbol: str, 
        indicator_name: str, 
        value: float,
        ttl_seconds: int = 300
    ) -> None:
        """Кэшировать значение индикатора"""
        key = f"indicator:{symbol}:{indicator_name}"
        await self.set(key, value, ttl_seconds)
    
    async def get_cached_indicator(
        self, 
        symbol: str, 
        indicator_name: str
    ) -> Optional[float]:
        """Получить кэшированное значение индикатора"""
        key = f"indicator:{symbol}:{indicator_name}"
        return await self.get(key)
    
    async def cache_signal(
        self, 
        symbol: str, 
        signal_type: str, 
        signal_data: Dict[str, Any],
        ttl_seconds: int = 60
    ) -> None:
        """Кэшировать торговый сигнал"""
        key = f"signal:{symbol}:{signal_type}"
        await self.set(key, signal_data, ttl_seconds)
    
    async def get_cached_signal(
        self, 
        symbol: str, 
        signal_type: str
    ) -> Optional[Dict[str, Any]]:
        """Получить кэшированный торговый сигнал"""
        key = f"signal:{symbol}:{signal_type}"
        return await self.get(key)
    
    async def cache_orderbook_metrics(
        self, 
        symbol: str, 
        metrics: Dict[str, Any],
        ttl_seconds: int = 30
    ) -> None:
        """Кэшировать метрики стакана заявок"""
        key = f"orderbook_metrics:{symbol}"
        await self.set(key, metrics, ttl_seconds)
    
    async def get_cached_orderbook_metrics(
        self, 
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """Получить кэшированные метрики стакана заявок"""
        key = f"orderbook_metrics:{symbol}"
        return await self.get(key)