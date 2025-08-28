# src/infrastructure/repositories/memory_first/memory_first_deals_repository_normalized.py
import pandas as pd
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from ..interfaces.deals_repository_interface import IDealsRepository
from ..interfaces.currency_pairs_repository_interface import ICurrencyPairsRepository
from ..base.base_repository import MemoryFirstRepository
import logging

class MemoryFirstDealsRepositoryNormalized(MemoryFirstRepository[Deal], IDealsRepository):
    """
    НОРМАЛИЗОВАННЫЙ Memory-First репозиторий сделок с синхронизацией в PostgreSQL
    
    ИСПРАВЛЯЕТ ПРОБЛЕМУ ДЕНОРМАЛИЗАЦИИ:
    - Хранит только currency_pair_id вместо дублирования данных валютной пары
    - Использует CurrencyPairsRepository для получения данных валютных пар
    - Обеспечивает правильную нормализацию базы данных
    """
    
    def __init__(self, persistent_provider=None, currency_pairs_repository: ICurrencyPairsRepository = None):
        """
        Инициализация нормализованного репозитория сделок
        
        Args:
            persistent_provider: Провайдер для синхронизации с PostgreSQL
            currency_pairs_repository: Репозиторий валютных пар для нормализации
        """
        super().__init__(persistent_provider)
        self.table_name = "deals"
        self.logger = logging.getLogger(__name__)
        self.currency_pairs_repository = currency_pairs_repository
        
        if not currency_pairs_repository:
            raise ValueError("CurrencyPairsRepository is required for normalized deals repository")
    
    def _get_dataframe_columns(self) -> List[str]:
        """Определение колонок DataFrame для нормализованных сделок"""
        return [
            'deal_id', 'currency_pair_id',  # ✅ Только ID валютной пары, не её данные!
            'status', 'created_at', 'updated_at', 'closed_at',
            'buy_order_id', 'sell_order_id', 'profit'
        ]
    
    def _get_id_column(self) -> str:
        """Имя колонки ID"""
        return 'deal_id'
    
    def _optimize_dataframe_dtypes(self):
        """Оптимизация типов данных для экономии памяти"""
        if not self.df.empty:
            self.df['deal_id'] = self.df['deal_id'].astype('int32')
            self.df['currency_pair_id'] = self.df['currency_pair_id'].astype('int32')  # ✅ Только ID!
            self.df['profit'] = self.df['profit'].astype('float64')
            self.df['status'] = self.df['status'].astype('category')
    
    def _entity_to_dict(self, deal: Deal) -> Dict[str, Any]:
        """
        ИСПРАВЛЕННОЕ преобразование Deal в словарь для DataFrame
        
        ❌ БЫЛО (денормализация):
        'currency_pair': deal.currency_pair.symbol,
        'base_currency': deal.currency_pair.base_currency,
        'quote_currency': deal.currency_pair.quote_currency,
        'deal_quota': deal.currency_pair.deal_quota,
        
        ✅ СТАЛО (нормализация):
        'currency_pair_id': currency_pair_id
        """
        # Получаем или создаём ID валютной пары
        currency_pair_id = self._get_or_create_currency_pair_id(deal.currency_pair)
        
        return {
            'deal_id': deal.deal_id if deal.deal_id else self._get_next_id(),
            'currency_pair_id': currency_pair_id,  # ✅ Только ID, не данные!
            'status': deal.status.value if hasattr(deal.status, 'value') else str(deal.status),
            'created_at': deal.created_at,
            'updated_at': deal.updated_at,
            'closed_at': deal.closed_at,
            'buy_order_id': deal.buy_order.order_id if deal.buy_order else None,
            'sell_order_id': deal.sell_order.order_id if deal.sell_order else None,
            'profit': float(deal.profit) if deal.profit else 0.0
        }
    
    def _dict_to_entity(self, data: Dict[str, Any]) -> Deal:
        """
        ИСПРАВЛЕННОЕ преобразование словаря из DataFrame в Deal
        
        ❌ БЫЛО (денормализация):
        currency_pair = CurrencyPair(
            base_currency=data['base_currency'],
            quote_currency=data['quote_currency'],
            symbol=data['currency_pair'],
            deal_quota=data['deal_quota']
        )
        
        ✅ СТАЛО (нормализация):
        currency_pair = self.currency_pairs_repository.get_by_id(data['currency_pair_id'])
        """
        # Получаем валютную пару по ID из нормализованного репозитория
        currency_pair = self.currency_pairs_repository.get_by_id(data['currency_pair_id'])
        
        if not currency_pair:
            raise ValueError(f"Currency pair with ID {data['currency_pair_id']} not found")
        
        # Создаем Deal с правильным конструктором
        deal = Deal(
            deal_id=data['deal_id'],
            currency_pair=currency_pair,  # ✅ Полный объект из нормализованного репозитория
            status=data['status'] if data['status'] in [Deal.STATUS_OPEN, Deal.STATUS_CLOSED, Deal.STATUS_CANCELED] else Deal.STATUS_OPEN,
            created_at=data.get('created_at'),
            closed_at=data.get('closed_at')
        )
        
        # Дополнительные поля (не в конструкторе)
        deal.updated_at = data.get('updated_at')
        deal.profit = data.get('profit', 0.0)
        
        # TODO: Загрузка связанных ордеров (buy_order, sell_order)
        # Это потребует интеграции с OrdersRepository
        
        return deal
    
    def _get_or_create_currency_pair_id(self, currency_pair: CurrencyPair) -> int:
        """
        Получить ID валютной пары или создать её если не существует
        
        Args:
            currency_pair: Объект валютной пары
            
        Returns:
            int: ID валютной пары
        """
        # Сначала пытаемся найти существующую валютную пару
        existing_pair = self.currency_pairs_repository.get_by_symbol(currency_pair.symbol)
        
        if existing_pair:
            return existing_pair.id
        
        # Если не найдена, создаём новую
        return self.currency_pairs_repository.save(currency_pair)
    
    # Реализация базовых методов BaseRepository
    def save(self, deal: Deal) -> None:
        """Сохранение сделки в DataFrame + фоновая синхронизация с PostgreSQL"""
        deal_data = self._entity_to_dict(deal)
        
        # Устанавливаем ID если его нет
        if deal.deal_id is None:
            deal.deal_id = deal_data['deal_id']
        
        # Инициализируем DataFrame если он пустой
        if self.df.empty:
            self.df = pd.DataFrame(columns=self._get_dataframe_columns())
        
        # Обновляем или добавляем в DataFrame
        mask = self.df['deal_id'] == deal.deal_id
        if mask.any():
            # Обновление существующей записи
            for key, value in deal_data.items():
                self.df.loc[mask, key] = value
        else:
            # Добавление новой записи (оптимизированный способ)
            if self.df.empty:
                self.df = pd.DataFrame([deal_data])
            else:
                # Используем pd.DataFrame.loc для избежания FutureWarning с pd.concat
                new_index = len(self.df)
                self.df.loc[new_index] = deal_data
        
        # Фоновая синхронизация с PostgreSQL (не блокирует торговлю)
        if self.persistent_provider:
            asyncio.create_task(self._sync_deal_to_postgres(deal_data))
    
    def get_by_id(self, deal_id: int) -> Optional[Deal]:
        """Получение сделки по ID из DataFrame (наносекунды)"""
        mask = self.df['deal_id'] == deal_id
        if not mask.any():
            return None
        
        row = self.df[mask].iloc[0]
        return self._dict_to_entity(row.to_dict())
    
    def get_all(self) -> List[Deal]:
        """Получение всех сделок из DataFrame"""
        return [self._dict_to_entity(row.to_dict()) for _, row in self.df.iterrows()]
    
    def delete_by_id(self, deal_id: int) -> bool:
        """Удаление сделки по ID"""
        mask = self.df['deal_id'] == deal_id
        if mask.any():
            self.df = self.df[~mask].reset_index(drop=True)
            # TODO: Синхронизация удаления с PostgreSQL
            return True
        return False
    
    # Реализация специализированных методов IDealsRepository
    def get_open_deals(self) -> List[Deal]:
        """Получение открытых сделок из DataFrame"""
        open_mask = self.df['status'] == Deal.STATUS_OPEN
        open_rows = self.df[open_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in open_rows.iterrows()]
    
    def get_closed_deals(self) -> List[Deal]:
        """Получение закрытых сделок из DataFrame"""
        closed_mask = self.df['status'] == Deal.STATUS_CLOSED
        closed_rows = self.df[closed_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in closed_rows.iterrows()]
    
    def get_deals_by_symbol(self, symbol: str) -> List[Deal]:
        """Получение сделок по торговой паре"""
        # Получаем ID валютной пары по символу
        currency_pair_id = self.currency_pairs_repository.get_id_by_symbol(symbol)
        if not currency_pair_id:
            return []
        
        symbol_mask = self.df['currency_pair_id'] == currency_pair_id
        symbol_rows = self.df[symbol_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in symbol_rows.iterrows()]
    
    def get_deals_by_status(self, status: str) -> List[Deal]:
        """Получение сделок по статусу"""
        status_mask = self.df['status'] == status
        status_rows = self.df[status_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in status_rows.iterrows()]
    
    def get_deals_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Deal]:
        """Получение сделок за период"""
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)
        
        date_mask = (self.df['created_at'] >= start_timestamp) & (self.df['created_at'] <= end_timestamp)
        date_rows = self.df[date_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in date_rows.iterrows()]
    
    def get_profitable_deals(self) -> List[Deal]:
        """Получение прибыльных сделок"""
        profit_mask = self.df['profit'] > 0
        profit_rows = self.df[profit_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in profit_rows.iterrows()]
    
    def get_losing_deals(self) -> List[Deal]:
        """Получение убыточных сделок"""
        loss_mask = self.df['profit'] < 0
        loss_rows = self.df[loss_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in loss_rows.iterrows()]
    
    def get_total_profit(self) -> float:
        """Получение общей прибыли"""
        if self.df.empty:
            return 0.0
        return float(self.df['profit'].sum())
    
    def get_deals_statistics(self) -> Dict[str, Any]:
        """Получение статистики по сделкам"""
        if self.df.empty:
            return {
                'total_deals': 0,
                'open_deals': 0,
                'closed_deals': 0,
                'total_profit': 0.0,
                'profitable_deals': 0,
                'losing_deals': 0,
                'average_profit': 0.0
            }
        
        total_deals = len(self.df)
        open_deals = len(self.df[self.df['status'] == Deal.STATUS_OPEN])
        closed_deals = len(self.df[self.df['status'] == Deal.STATUS_CLOSED])
        total_profit = float(self.df['profit'].sum())
        profitable_deals = len(self.df[self.df['profit'] > 0])
        losing_deals = len(self.df[self.df['profit'] < 0])
        average_profit = float(self.df['profit'].mean()) if total_deals > 0 else 0.0
        
        return {
            'total_deals': total_deals,
            'open_deals': open_deals,
            'closed_deals': closed_deals,
            'total_profit': total_profit,
            'profitable_deals': profitable_deals,
            'losing_deals': losing_deals,
            'average_profit': average_profit
        }
    
    def get_deals_by_buy_order_id(self, buy_order_id: int) -> List[Deal]:
        """Получение сделок по ID ордера на покупку"""
        buy_mask = self.df['buy_order_id'] == buy_order_id
        buy_rows = self.df[buy_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in buy_rows.iterrows()]
    
    def get_deals_by_sell_order_id(self, sell_order_id: int) -> List[Deal]:
        """Получение сделок по ID ордера на продажу"""
        sell_mask = self.df['sell_order_id'] == sell_order_id
        sell_rows = self.df[sell_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in sell_rows.iterrows()]
    
    def update_deal_profit(self, deal_id: int, profit: float) -> bool:
        """Обновление прибыли сделки"""
        mask = self.df['deal_id'] == deal_id
        if not mask.any():
            return False
        
        self.df.loc[mask, 'profit'] = profit
        self.df.loc[mask, 'updated_at'] = int(datetime.now().timestamp() * 1000)
        return True
    
    def close_deal(self, deal_id: int, sell_order_id: int, profit: float) -> bool:
        """Закрытие сделки"""
        mask = self.df['deal_id'] == deal_id
        if not mask.any():
            return False
        
        current_time = int(datetime.now().timestamp() * 1000)
        self.df.loc[mask, 'status'] = Deal.STATUS_CLOSED
        self.df.loc[mask, 'sell_order_id'] = sell_order_id
        self.df.loc[mask, 'profit'] = profit
        self.df.loc[mask, 'closed_at'] = current_time
        self.df.loc[mask, 'updated_at'] = current_time
        return True
    
    def cancel_deal(self, deal_id: int, reason: str = None) -> bool:
        """Отмена сделки"""
        mask = self.df['deal_id'] == deal_id
        if not mask.any():
            return False
        
        current_time = int(datetime.now().timestamp() * 1000)
        self.df.loc[mask, 'status'] = Deal.STATUS_CANCELED
        self.df.loc[mask, 'closed_at'] = current_time
        self.df.loc[mask, 'updated_at'] = current_time
        return True
    
    def get_active_deals_count(self) -> int:
        """Получение количества активных сделок"""
        return len(self.df[self.df['status'] == Deal.STATUS_OPEN])
    
    def get_average_deal_duration(self) -> float:
        """Получение средней продолжительности сделки в миллисекундах"""
        closed_deals = self.df[
            (self.df['status'] == Deal.STATUS_CLOSED) & 
            (self.df['closed_at'].notna())
        ]
        
        if closed_deals.empty:
            return 0.0
        
        durations = closed_deals['closed_at'] - closed_deals['created_at']
        return float(durations.mean())
    
    def get_success_rate(self) -> float:
        """Получение процента успешных сделок"""
        closed_deals = self.df[self.df['status'] == Deal.STATUS_CLOSED]
        if closed_deals.empty:
            return 0.0
        
        profitable_deals = len(closed_deals[closed_deals['profit'] > 0])
        return (profitable_deals / len(closed_deals)) * 100
    
    def get_deals_by_profit_range(self, min_profit: float, max_profit: float) -> List[Deal]:
        """Получение сделок в диапазоне прибыли"""
        profit_mask = (self.df['profit'] >= min_profit) & (self.df['profit'] <= max_profit)
        profit_rows = self.df[profit_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in profit_rows.iterrows()]
    
    async def _sync_deal_to_postgres(self, deal_data: Dict[str, Any]):
        """Синхронизация сделки с PostgreSQL"""
        try:
            if self.persistent_provider:
                # Здесь будет логика синхронизации с PostgreSQL
                # Пока заглушка
                self.logger.debug(f"Syncing deal {deal_data['deal_id']} to PostgreSQL")
        except Exception as e:
            self.logger.error(f"Error syncing deal to PostgreSQL: {e}")
    
    # Методы для совместимости с базовым классом
    def sync_to_persistent(self, deal: Deal):
        """Синхронизация с постоянным хранилищем"""
        deal_data = self._entity_to_dict(deal)
        asyncio.create_task(self._sync_deal_to_postgres(deal_data))
    
    def load_from_persistent(self):
        """Загрузка из постоянного хранилища"""
        # TODO: Реализация загрузки из PostgreSQL
        pass
    
    def backup_to_persistent(self):
        """Резервное копирование в постоянное хранилище"""
        # TODO: Реализация резервного копирования
        pass
    
    def _load_from_persistent(self):
        """Внутренний метод загрузки из постоянного хранилища"""
        # TODO: Реализация загрузки из PostgreSQL
        pass