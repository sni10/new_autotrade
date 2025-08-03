# src/infrastructure/repositories/interfaces/deals_repository_interface.py
from abc import abstractmethod
from typing import List, Optional
from datetime import datetime
from domain.entities.deal import Deal
from ..base.base_repository import AtomicRepository

class IDealsRepository(AtomicRepository[Deal]):
    """
    Специализированный интерфейс для репозитория сделок.
    Расширяет AtomicRepository методами специфичными для Deal.
    
    Используется для:
    - Унификации всех реализаций репозиториев сделок
    - Легкого переключения между InMemory, MemoryFirst, Persistent
    - Типобезопасности и контрактов
    """
    
    @abstractmethod
    def get_open_deals(self) -> List[Deal]:
        """Получить все открытые сделки"""
        pass
    
    @abstractmethod
    def get_closed_deals(self) -> List[Deal]:
        """Получить все закрытые сделки"""
        pass
    
    @abstractmethod
    def get_deals_by_symbol(self, symbol: str) -> List[Deal]:
        """Получить сделки по торговой паре"""
        pass
    
    @abstractmethod
    def get_deals_by_status(self, status: str) -> List[Deal]:
        """Получить сделки по статусу"""
        pass
    
    @abstractmethod
    def get_deals_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Deal]:
        """Получить сделки за период времени"""
        pass
    
    @abstractmethod
    def get_profitable_deals(self) -> List[Deal]:
        """Получить прибыльные сделки"""
        pass
    
    @abstractmethod
    def get_losing_deals(self) -> List[Deal]:
        """Получить убыточные сделки"""
        pass
    
    @abstractmethod
    def get_total_profit(self) -> float:
        """Получить общую прибыль по всем сделкам"""
        pass
    
    @abstractmethod
    def get_deals_statistics(self) -> dict:
        """Получить статистику по сделкам"""
        pass
    
    @abstractmethod
    def get_deals_by_buy_order_id(self, buy_order_id: int) -> Optional[Deal]:
        """Найти сделку по ID ордера на покупку"""
        pass
    
    @abstractmethod
    def get_deals_by_sell_order_id(self, sell_order_id: int) -> Optional[Deal]:
        """Найти сделку по ID ордера на продажу"""
        pass
    
    @abstractmethod
    def update_deal_profit(self, deal_id: int, profit: float) -> bool:
        """Обновить прибыль сделки"""
        pass
    
    @abstractmethod
    def close_deal(self, deal_id: int, sell_order_id: int, profit: float) -> bool:
        """Закрыть сделку"""
        pass
    
    @abstractmethod
    def cancel_deal(self, deal_id: int, reason: str = None) -> bool:
        """Отменить сделку"""
        pass
    
    # Методы для аналитики и мониторинга
    @abstractmethod
    def get_active_deals_count(self) -> int:
        """Получить количество активных сделок"""
        pass
    
    @abstractmethod
    def get_average_deal_duration(self) -> float:
        """Получить среднюю продолжительность сделки в минутах"""
        pass
    
    @abstractmethod
    def get_success_rate(self) -> float:
        """Получить процент успешных сделок"""
        pass
    
    @abstractmethod
    def get_deals_by_profit_range(self, min_profit: float, max_profit: float) -> List[Deal]:
        """Получить сделки в диапазоне прибыли"""
        pass