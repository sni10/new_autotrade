from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.entities.order import Order


class IOrdersRepository(ABC):
    """
    🚀 CCXT COMPLIANT Orders Repository Interface
    
    Интерфейс для репозитория ордеров с полной поддержкой CCXT структур данных.
    Поддерживает как CCXT ID (exchange order ID), так и локальные AutoTrade ID.
    """

    # ===== CORE CRUD OPERATIONS =====

    @abstractmethod
    async def save_order(self, order: Order) -> bool:
        """Сохранить ордер (создать или обновить)"""
        pass

    @abstractmethod
    async def save_orders_batch(self, orders: List[Order]) -> int:
        """Сохранить несколько ордеров за один запрос"""
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Получить ордер по CCXT ID (exchange order ID)"""
        pass

    @abstractmethod
    async def get_order_by_local_id(self, local_order_id: int) -> Optional[Order]:
        """Получить ордер по локальному AutoTrade ID"""
        pass

    @abstractmethod
    async def update_order(self, order: Order) -> bool:
        """Обновить существующий ордер"""
        pass

    @abstractmethod
    async def delete_order(self, order_id: str) -> bool:
        """Удалить ордер (мягкое удаление)"""
        pass

    # ===== QUERY OPERATIONS =====

    @abstractmethod
    async def get_all_orders(self) -> List[Order]:
        """Получить все ордера"""
        pass

    @abstractmethod
    async def get_active_orders(self) -> List[Order]:
        """Получить активные ордера (CCXT статусы: open, pending, partial)"""
        pass

    @abstractmethod
    async def get_filled_orders(self) -> List[Order]:
        """Получить исполненные ордера (CCXT статус: closed)"""
        pass

    @abstractmethod
    async def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Получить ордера по торговой паре"""
        pass

    @abstractmethod
    async def get_orders_by_deal_id(self, deal_id: str) -> List[Order]:
        """Получить ордера по ID сделки"""
        pass

    @abstractmethod
    async def get_orders_in_period(self, start_time: datetime, end_time: datetime) -> List[Order]:
        """Получить ордера за период"""
        pass

    @abstractmethod
    async def count_active_orders(self) -> int:
        """Подсчитать количество активных ордеров"""
        pass

    @abstractmethod
    async def count_orders_by_status(self, status: str) -> int:
        """Подсчитать ордера по статусу"""
        pass

    # ===== ADVANCED QUERY OPERATIONS =====

    @abstractmethod
    async def get_orders_by_side_and_symbol(self, side: str, symbol: str) -> List[Order]:
        """Получить ордера по стороне и символу"""
        pass

    @abstractmethod
    async def get_recent_orders(self, limit: int = 100) -> List[Order]:
        """Получить последние ордера"""
        pass

    @abstractmethod
    async def get_orders_with_errors(self) -> List[Order]:
        """Получить ордера с ошибками"""
        pass

    # ===== BULK OPERATIONS =====

    @abstractmethod
    async def update_orders_batch(self, orders: List[Order]) -> int:
        """Массовое обновление ордеров"""
        pass

    # ===== UTILITY METHODS =====

    @abstractmethod
    async def cleanup_old_orders(self, days_to_keep: int = 30) -> int:
        """Очистка старых ордеров"""
        pass

    @abstractmethod
    async def get_order_statistics(self) -> Dict[str, Any]:
        """Получить статистику по ордерам"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья репозитория"""
        pass