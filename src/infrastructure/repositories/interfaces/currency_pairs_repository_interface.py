# src/infrastructure/repositories/interfaces/currency_pairs_repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.currency_pair import CurrencyPair

class ICurrencyPairsRepository(ABC):
    """
    Интерфейс репозитория валютных пар
    Обеспечивает нормализованное хранение валютных пар отдельно от сделок
    """
    
    @abstractmethod
    def save(self, currency_pair: CurrencyPair) -> int:
        """
        Сохранить валютную пару и вернуть её ID
        
        Args:
            currency_pair: Объект валютной пары
            
        Returns:
            int: ID сохранённой валютной пары
        """
        pass
    
    @abstractmethod
    def get_by_id(self, currency_pair_id: int) -> Optional[CurrencyPair]:
        """
        Получить валютную пару по ID
        
        Args:
            currency_pair_id: ID валютной пары
            
        Returns:
            CurrencyPair или None если не найдена
        """
        pass
    
    @abstractmethod
    def get_by_symbol(self, symbol: str) -> Optional[CurrencyPair]:
        """
        Получить валютную пару по символу (например, "BTCUSDT")
        
        Args:
            symbol: Символ валютной пары
            
        Returns:
            CurrencyPair или None если не найдена
        """
        pass
    
    @abstractmethod
    def get_by_currencies(self, base_currency: str, quote_currency: str) -> Optional[CurrencyPair]:
        """
        Получить валютную пару по базовой и котируемой валютам
        
        Args:
            base_currency: Базовая валюта (например, "BTC")
            quote_currency: Котируемая валюта (например, "USDT")
            
        Returns:
            CurrencyPair или None если не найдена
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[CurrencyPair]:
        """
        Получить все валютные пары
        
        Returns:
            Список всех валютных пар
        """
        pass
    
    @abstractmethod
    def update(self, currency_pair: CurrencyPair) -> bool:
        """
        Обновить существующую валютную пару
        
        Args:
            currency_pair: Объект валютной пары с обновлёнными данными
            
        Returns:
            True если обновление успешно, False если валютная пара не найдена
        """
        pass
    
    @abstractmethod
    def delete_by_id(self, currency_pair_id: int) -> bool:
        """
        Удалить валютную пару по ID
        
        Args:
            currency_pair_id: ID валютной пары
            
        Returns:
            True если удаление успешно, False если валютная пара не найдена
        """
        pass
    
    @abstractmethod
    def exists_by_symbol(self, symbol: str) -> bool:
        """
        Проверить существование валютной пары по символу
        
        Args:
            symbol: Символ валютной пары
            
        Returns:
            True если валютная пара существует
        """
        pass
    
    @abstractmethod
    def get_active_pairs(self) -> List[CurrencyPair]:
        """
        Получить активные валютные пары (с deal_count > 0)
        
        Returns:
            Список активных валютных пар
        """
        pass