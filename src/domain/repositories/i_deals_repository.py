from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from src.domain.entities.deal import Deal


class IDealsRepository(ABC):
    """Интерфейс для репозитория сделок"""

    @abstractmethod
    async def save_deal(self, deal: Deal) -> bool:
        """Сохранить сделку"""
        pass

    @abstractmethod
    async def get_deal(self, deal_id: str) -> Optional[Deal]:
        """Получить сделку по ID"""
        pass

    @abstractmethod
    async def get_all_deals(self) -> List[Deal]:
        """Получить все сделки"""
        pass

    @abstractmethod
    async def get_active_deals(self) -> List[Deal]:
        """Получить активные сделки"""
        pass

    @abstractmethod
    async def get_completed_deals(self) -> List[Deal]:
        """Получить завершенные сделки"""
        pass

    @abstractmethod
    async def update_deal(self, deal: Deal) -> bool:
        """Обновить сделку"""
        pass

    @abstractmethod
    async def delete_deal(self, deal_id: str) -> bool:
        """Удалить сделку"""
        pass

    @abstractmethod
    async def get_deals_by_symbol(self, symbol: str) -> List[Deal]:
        """Получить сделки по символу"""
        pass

    @abstractmethod
    async def get_deals_in_period(self, start_time: datetime, end_time: datetime) -> List[Deal]:
        """Получить сделки за период"""
        pass

    @abstractmethod
    async def count_active_deals(self) -> int:
        """Подсчитать количество активных сделок"""
        pass