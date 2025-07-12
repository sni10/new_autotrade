# my_trading_app/infrastructure/repositories/deals_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.deal import Deal

class DealsRepository(ABC):
    """
    Интерфейс (абстрактный класс) для хранения и извлечения сделок (Deal).
    """

    @abstractmethod
    def save(self, deal: Deal) -> None:
        pass

    @abstractmethod
    def get_by_id(self, deal_id: int) -> Optional[Deal]:
        pass

    @abstractmethod
    def get_open_deals(self) -> List[Deal]:
        pass

    @abstractmethod
    def get_all(self) -> List[Deal]:
        pass


class InMemoryDealsRepository(DealsRepository):
    """
    Простейшая InMemory-реализация.
    Хранит Deal в словаре {deal_id: Deal}.
    """

    def __init__(self):
        self._storage = {}

    def save(self, deal: Deal) -> None:
        self._storage[deal.deal_id] = deal

    def get_by_id(self, deal_id: int) -> Optional[Deal]:
        return self._storage.get(deal_id)

    def get_open_deals(self) -> List[Deal]:
        return [d for d in self._storage.values() if d.is_open()]

    def get_all(self) -> List[Deal]:
        """Возвращает все сделки (открытые, закрытые, отмененные)"""
        return list(self._storage.values())
