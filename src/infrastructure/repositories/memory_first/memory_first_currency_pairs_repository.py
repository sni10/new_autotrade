# src/infrastructure/repositories/memory_first/memory_first_currency_pairs_repository.py
import pandas as pd
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from domain.entities.currency_pair import CurrencyPair
from ..interfaces.currency_pairs_repository_interface import ICurrencyPairsRepository
from ..base.base_repository import MemoryFirstRepository
import logging

class MemoryFirstCurrencyPairsRepository(MemoryFirstRepository[CurrencyPair], ICurrencyPairsRepository):
    """
    Memory-First репозиторий валютных пар с синхронизацией в PostgreSQL
    Обеспечивает нормализованное хранение валютных пар отдельно от сделок
    """
    
    def __init__(self, persistent_provider=None):
        """
        Инициализация репозитория валютных пар
        
        Args:
            persistent_provider: Провайдер для синхронизации с PostgreSQL
        """
        super().__init__(persistent_provider)
        self.table_name = "currency_pairs"
        self.logger = logging.getLogger(__name__)
        self._symbol_to_id_cache = {}  # Кэш для быстрого поиска ID по символу
        
    def _get_dataframe_columns(self) -> List[str]:
        """Определение колонок DataFrame для валютных пар"""
        return [
            'id', 'base_currency', 'quote_currency', 'symbol', 
            'deal_quota', 'profit_markup', 'order_life_time', 'deal_count',
            'taker_fee', 'maker_fee', 'created_at', 'updated_at'
        ]
    
    def _get_id_column(self) -> str:
        """Имя колонки ID"""
        return 'id'
    
    def _optimize_dataframe_dtypes(self):
        """Оптимизация типов данных для экономии памяти"""
        if not self.df.empty:
            self.df['id'] = self.df['id'].astype('int32')
            self.df['deal_quota'] = self.df['deal_quota'].astype('float64')
            self.df['profit_markup'] = self.df['profit_markup'].astype('float64')
            self.df['order_life_time'] = self.df['order_life_time'].astype('int16')
            self.df['deal_count'] = self.df['deal_count'].astype('int16')
            self.df['taker_fee'] = self.df['taker_fee'].astype('float64')
            self.df['maker_fee'] = self.df['maker_fee'].astype('float64')
            self.df['base_currency'] = self.df['base_currency'].astype('category')
            self.df['quote_currency'] = self.df['quote_currency'].astype('category')
            self.df['symbol'] = self.df['symbol'].astype('category')
    
    def _entity_to_dict(self, currency_pair: CurrencyPair) -> Dict[str, Any]:
        """Преобразование CurrencyPair в словарь для DataFrame"""
        current_time = int(datetime.now().timestamp() * 1000)
        
        return {
            'id': getattr(currency_pair, 'id', None) or self._get_next_id(),
            'base_currency': currency_pair.base_currency,
            'quote_currency': currency_pair.quote_currency,
            'symbol': currency_pair.symbol,
            'deal_quota': float(currency_pair.deal_quota),
            'profit_markup': float(currency_pair.profit_markup),
            'order_life_time': int(currency_pair.order_life_time),
            'deal_count': int(currency_pair.deal_count),
            'taker_fee': float(currency_pair.taker_fee),
            'maker_fee': float(currency_pair.maker_fee),
            'created_at': getattr(currency_pair, 'created_at', current_time),
            'updated_at': current_time
        }
    
    def _dict_to_entity(self, data: Dict[str, Any]) -> CurrencyPair:
        """Преобразование словаря из DataFrame в CurrencyPair"""
        currency_pair = CurrencyPair(
            base_currency=data['base_currency'],
            quote_currency=data['quote_currency'],
            symbol=data['symbol'],
            order_life_time=data['order_life_time'],
            deal_quota=data['deal_quota'],
            profit_markup=data['profit_markup'],
            deal_count=data['deal_count']
        )
        
        # Дополнительные поля
        currency_pair.id = data['id']
        currency_pair.taker_fee = data['taker_fee']
        currency_pair.maker_fee = data['maker_fee']
        currency_pair.created_at = data.get('created_at')
        currency_pair.updated_at = data.get('updated_at')
        
        return currency_pair
    
    def save(self, currency_pair: CurrencyPair) -> int:
        """Сохранение валютной пары и возврат её ID"""
        currency_pair_data = self._entity_to_dict(currency_pair)
        
        # Устанавливаем ID если его нет
        if not hasattr(currency_pair, 'id') or currency_pair.id is None:
            currency_pair.id = currency_pair_data['id']
        
        # Инициализируем DataFrame если он пустой
        if self.df.empty:
            self.df = pd.DataFrame(columns=self._get_dataframe_columns())
        
        # Обновляем или добавляем в DataFrame
        mask = self.df['id'] == currency_pair.id
        if mask.any():
            # Обновление существующей записи
            for key, value in currency_pair_data.items():
                self.df.loc[mask, key] = value
        else:
            # Добавление новой записи
            if self.df.empty:
                self.df = pd.DataFrame([currency_pair_data])
            else:
                # Используем pd.DataFrame.loc для избежания FutureWarning с pd.concat
                new_index = len(self.df)
                self.df.loc[new_index] = currency_pair_data
        
        # Обновляем кэш
        self._symbol_to_id_cache[currency_pair.symbol] = currency_pair.id
        
        # Фоновая синхронизация с PostgreSQL
        if self.persistent_provider:
            asyncio.create_task(self._sync_to_postgres(currency_pair_data))
        
        return currency_pair.id
    
    def get_by_id(self, currency_pair_id: int) -> Optional[CurrencyPair]:
        """Получение валютной пары по ID"""
        mask = self.df['id'] == currency_pair_id
        if not mask.any():
            return None
        
        row = self.df[mask].iloc[0]
        return self._dict_to_entity(row.to_dict())
    
    def get_by_symbol(self, symbol: str) -> Optional[CurrencyPair]:
        """Получение валютной пары по символу"""
        if self.df.empty:
            return None
            
        mask = self.df['symbol'] == symbol
        if not mask.any():
            return None
        
        row = self.df[mask].iloc[0]
        return self._dict_to_entity(row.to_dict())
    
    def get_by_currencies(self, base_currency: str, quote_currency: str) -> Optional[CurrencyPair]:
        """Получение валютной пары по базовой и котируемой валютам"""
        mask = (self.df['base_currency'] == base_currency) & (self.df['quote_currency'] == quote_currency)
        if not mask.any():
            return None
        
        row = self.df[mask].iloc[0]
        return self._dict_to_entity(row.to_dict())
    
    def get_all(self) -> List[CurrencyPair]:
        """Получение всех валютных пар"""
        return [self._dict_to_entity(row.to_dict()) for _, row in self.df.iterrows()]
    
    def update(self, currency_pair: CurrencyPair) -> bool:
        """Обновление существующей валютной пары"""
        if not hasattr(currency_pair, 'id') or currency_pair.id is None:
            return False
        
        mask = self.df['id'] == currency_pair.id
        if not mask.any():
            return False
        
        currency_pair_data = self._entity_to_dict(currency_pair)
        for key, value in currency_pair_data.items():
            self.df.loc[mask, key] = value
        
        # Обновляем кэш
        self._symbol_to_id_cache[currency_pair.symbol] = currency_pair.id
        
        # Синхронизация с PostgreSQL
        if self.persistent_provider:
            asyncio.create_task(self._sync_to_postgres(currency_pair_data))
        
        return True
    
    def delete_by_id(self, currency_pair_id: int) -> bool:
        """Удаление валютной пары по ID"""
        mask = self.df['id'] == currency_pair_id
        if not mask.any():
            return False
        
        # Удаляем из кэша
        row = self.df[mask].iloc[0]
        symbol = row['symbol']
        if symbol in self._symbol_to_id_cache:
            del self._symbol_to_id_cache[symbol]
        
        # Удаляем из DataFrame
        self.df = self.df[~mask].reset_index(drop=True)
        
        # TODO: Синхронизация удаления с PostgreSQL
        return True
    
    def exists_by_symbol(self, symbol: str) -> bool:
        """Проверка существования валютной пары по символу"""
        return (self.df['symbol'] == symbol).any()
    
    def get_active_pairs(self) -> List[CurrencyPair]:
        """Получение активных валютных пар (с deal_count > 0)"""
        active_mask = self.df['deal_count'] > 0
        active_rows = self.df[active_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in active_rows.iterrows()]
    
    def get_id_by_symbol(self, symbol: str) -> Optional[int]:
        """Быстрое получение ID валютной пары по символу (для оптимизации)"""
        if symbol in self._symbol_to_id_cache:
            return self._symbol_to_id_cache[symbol]
        
        mask = self.df['symbol'] == symbol
        if not mask.any():
            return None
        
        currency_pair_id = self.df[mask].iloc[0]['id']
        self._symbol_to_id_cache[symbol] = currency_pair_id
        return currency_pair_id
    
    async def _sync_to_postgres(self, currency_pair_data: Dict[str, Any]):
        """Синхронизация валютной пары с PostgreSQL"""
        try:
            if self.persistent_provider:
                # Здесь будет логика синхронизации с PostgreSQL
                # Пока заглушка
                self.logger.debug(f"Syncing currency pair {currency_pair_data['symbol']} to PostgreSQL")
        except Exception as e:
            self.logger.error(f"Error syncing currency pair to PostgreSQL: {e}")
    
    def _rebuild_cache(self):
        """Перестроение кэша символ -> ID"""
        self._symbol_to_id_cache = {}
        for _, row in self.df.iterrows():
            self._symbol_to_id_cache[row['symbol']] = row['id']