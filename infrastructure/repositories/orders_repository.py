# my_trading_app/infrastructure/repositories/orders_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.order import Order

class OrdersRepository(ABC):
    """
    Интерфейс (абстрактный класс) для хранения и извлечения ордеров (Order).
    """

    @abstractmethod
    def save(self, order: Order) -> None:
        pass

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        pass

    @abstractmethod
    def get_all_by_deal(self, deal_id: int) -> List[Order]:
        """
        Предполагаем, что у ордера где-то хранится ссылка на deal_id
        (сейчас в Order нет этого поля, но можно добавить).
        """
        pass


class InMemoryOrdersRepository(OrdersRepository):
    """
    Простейшая InMemory-реализация.
    Хранит Order в словаре {order_id: Order}.
    """

    def __init__(self):
        self._storage = {}

    def save(self, order: Order) -> None:
        self._storage[order.order_id] = order

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self._storage.get(order_id)

    def get_all_by_deal(self, deal_id: int) -> List[Order]:
        # На этапе 1 у нас в Order нет поля deal_id,
        # так что пока вернём пустой список или все ордера :)
        # Когда будем дорабатывать, добавим в Order ссылку на deal_id,
        # или будем хранить где-то сопоставление.
        return list(self._storage.values())
