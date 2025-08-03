# src/infrastructure/repositories/interfaces/orders_repository_interface.py
from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from domain.entities.order import Order
from ..base.base_repository import AtomicRepository

class IOrdersRepository(AtomicRepository[Order]):
    """
    Специализированный интерфейс для репозитория ордеров.
    Расширяет AtomicRepository методами специфичными для Order.
    
    Используется для:
    - Унификации всех реализаций репозиториев ордеров
    - Легкого переключения между InMemory, MemoryFirst, Persistent
    - Типобезопасности и контрактов
    - Совместимости с существующим OrdersRepository
    """
    
    # Основные методы поиска
    @abstractmethod
    def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        """Получить ордер по биржевому ID"""
        pass
    
    @abstractmethod
    def get_all_by_deal(self, deal_id: int) -> List[Order]:
        """Получить все ордера по сделке"""
        pass
    
    @abstractmethod
    def get_open_orders(self) -> List[Order]:
        """Получить все открытые ордера"""
        pass
    
    @abstractmethod
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Получить ордера по торговой паре"""
        pass
    
    @abstractmethod
    def get_orders_by_status(self, status: str) -> List[Order]:
        """Получить ордера по статусу"""
        pass
    
    @abstractmethod
    def get_pending_orders(self) -> List[Order]:
        """Получить ордера в ожидании исполнения"""
        pass
    
    @abstractmethod
    def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """Получить ордера за период времени"""
        pass
    
    # Методы для работы с группами ордеров
    @abstractmethod
    def bulk_update_status(self, order_ids: List[int], status: str) -> int:
        """Массовое обновление статуса ордеров"""
        pass
    
    @abstractmethod
    def delete_old_orders(self, older_than_days: int) -> int:
        """Удаление старых ордеров"""
        pass
    
    # Расширенный поиск
    @abstractmethod
    def search_orders(self, 
                     symbol: str = None,
                     status: str = None, 
                     deal_id: int = None,
                     exchange_id: str = None,
                     side: str = None,
                     order_type: str = None,
                     min_amount: float = None,
                     max_amount: float = None,
                     date_from: datetime = None,
                     date_to: datetime = None,
                     limit: int = None) -> List[Order]:
        """Расширенный поиск ордеров по множественным критериям"""
        pass
    
    # Методы для мониторинга и диагностики
    @abstractmethod
    def get_orders_with_errors(self) -> List[Order]:
        """Получить ордера с ошибками"""
        pass
    
    @abstractmethod
    def get_orders_requiring_sync(self) -> List[Order]:
        """Получить ордера, требующие синхронизации с биржей"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по ордерам"""
        pass
    
    # Методы для экспорта/импорта
    @abstractmethod
    def export_to_json(self, file_path: str = None) -> str:
        """Экспорт ордеров в JSON"""
        pass
    
    @abstractmethod
    def import_from_json(self, json_data: str = None, file_path: str = None) -> int:
        """Импорт ордеров из JSON"""
        pass
    
    # Методы для оптимизации производительности
    @abstractmethod
    def rebuild_indexes(self) -> None:
        """Перестроить индексы для оптимизации поиска"""
        pass
    
    # Дополнительные методы для двухуровневой архитектуры
    @abstractmethod
    def get_orders_by_side(self, side: str) -> List[Order]:
        """Получить ордера по стороне (BUY/SELL)"""
        pass
    
    @abstractmethod
    def get_orders_by_type(self, order_type: str) -> List[Order]:
        """Получить ордера по типу (MARKET/LIMIT)"""
        pass
    
    @abstractmethod
    def get_filled_orders(self) -> List[Order]:
        """Получить исполненные ордера"""
        pass
    
    @abstractmethod
    def get_cancelled_orders(self) -> List[Order]:
        """Получить отмененные ордера"""
        pass
    
    @abstractmethod
    def get_partially_filled_orders(self) -> List[Order]:
        """Получить частично исполненные ордера"""
        pass
    
    @abstractmethod
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновить статус ордера"""
        pass
    
    @abstractmethod
    def update_order_filled_amount(self, order_id: int, filled_amount: float) -> bool:
        """Обновить исполненное количество ордера"""
        pass
    
    @abstractmethod
    def update_order_fees(self, order_id: int, fees: float) -> bool:
        """Обновить комиссии ордера"""
        pass
    
    # Аналитические методы
    @abstractmethod
    def get_total_volume_by_symbol(self, symbol: str) -> float:
        """Получить общий объем торгов по символу"""
        pass
    
    @abstractmethod
    def get_average_order_size(self, symbol: str = None) -> float:
        """Получить средний размер ордера"""
        pass
    
    @abstractmethod
    def get_order_success_rate(self) -> float:
        """Получить процент успешно исполненных ордеров"""
        pass
    
    @abstractmethod
    def get_orders_by_price_range(self, symbol: str, min_price: float, max_price: float) -> List[Order]:
        """Получить ордера в диапазоне цен"""
        pass
    
    @abstractmethod
    def get_recent_orders(self, limit: int = 100) -> List[Order]:
        """Получить последние ордера"""
        pass