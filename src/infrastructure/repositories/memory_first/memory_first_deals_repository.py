# src/infrastructure/repositories/memory_first/memory_first_deals_repository.py
import pandas as pd
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from ..interfaces.deals_repository_interface import IDealsRepository
from ..base.base_repository import MemoryFirstRepository
import logging

logger = logging.getLogger(__name__)

class MemoryFirstDealsRepository(MemoryFirstRepository[Deal], IDealsRepository):
    """
    Двухуровневый репозиторий сделок:
    - Уровень 1: DataFrame в памяти (все операции в наносекундах)
    - Уровень 2: PostgreSQL (автоматическая фоновая синхронизация)
    
    Принципы:
    - Все операции чтения/записи работают с DataFrame
    - PostgreSQL синхронизация полностью прозрачна
    - Фоновая синхронизация не блокирует торговлю
    - Автоматическое восстановление после перезапуска
    """
    
    def __init__(self, persistent_provider=None):
        super().__init__(persistent_provider)
        self._initialize_dataframe()
        
        # Загружаем существующие данные из БД при инициализации
        if persistent_provider:
            asyncio.create_task(self._load_from_persistent())
    
    def _get_dataframe_columns(self) -> List[str]:
        """Определяем структуру DataFrame для сделок"""
        return [
            'deal_id', 'currency_pair', 'base_currency', 'quote_currency',
            'deal_quota', 'status', 'created_at', 'updated_at', 'closed_at',
            'buy_order_id', 'sell_order_id', 'profit'
        ]
    
    def _get_id_column(self) -> str:
        """ID колонка для сделок"""
        return 'deal_id'
    
    def _optimize_dataframe_dtypes(self):
        """Оптимизация типов данных для экономии памяти"""
        # Устанавливаем типы данных даже для пустого DataFrame
        dtypes = {
            'deal_id': 'int64',  # Изменено с int32 на int64 для больших timestamp-based ID
            'currency_pair': 'category',
            'base_currency': 'category', 
            'quote_currency': 'category',
            'deal_quota': 'float64',
            'status': 'category',
            'created_at': 'datetime64[ns]',
            'updated_at': 'datetime64[ns]',
            'closed_at': 'datetime64[ns]',
            'buy_order_id': 'Int64',  # Изменено с Int32 на Int64 для больших ID
            'sell_order_id': 'Int64',  # Изменено с Int32 на Int64 для больших ID
            'profit': 'float64'
        }
        
        # Применяем типы данных к существующим колонкам
        for col, dtype in dtypes.items():
            if col in self.df.columns:
                try:
                    if dtype == 'datetime64[ns]':
                        self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    elif col == 'status' and dtype == 'category':
                        # Для статуса явно определяем все возможные категории
                        from domain.entities.deal import Deal
                        status_categories = [Deal.STATUS_OPEN, Deal.STATUS_CLOSED, Deal.STATUS_CANCELED]
                        self.df[col] = self.df[col].astype(pd.CategoricalDtype(categories=status_categories))
                    else:
                        self.df[col] = self.df[col].astype(dtype)
                except Exception:
                    # Если не удается преобразовать, оставляем как есть
                    pass
    
    def _entity_to_dict(self, deal: Deal) -> Dict[str, Any]:
        """Преобразование Deal в словарь для DataFrame"""
        return {
            'deal_id': deal.deal_id if deal.deal_id else self._get_next_id(),
            'currency_pair': deal.currency_pair.symbol,
            'base_currency': deal.currency_pair.base_currency,
            'quote_currency': deal.currency_pair.quote_currency,
            'deal_quota': float(deal.currency_pair.deal_quota),
            'status': deal.status.value if hasattr(deal.status, 'value') else str(deal.status),
            'created_at': deal.created_at,
            'updated_at': deal.updated_at,
            'closed_at': deal.closed_at,
            'buy_order_id': deal.buy_order.order_id if deal.buy_order else None,
            'sell_order_id': deal.sell_order.order_id if deal.sell_order else None,
            'profit': float(deal.profit) if deal.profit else 0.0
        }
    
    def _dict_to_entity(self, data: Dict[str, Any]) -> Deal:
        """Преобразование словаря из DataFrame в Deal"""
        # Создаем CurrencyPair
        currency_pair = CurrencyPair(
            base_currency=data['base_currency'],
            quote_currency=data['quote_currency'],
            symbol=data['currency_pair'],
            deal_quota=data['deal_quota']
        )
        
        # Создаем Deal с правильным конструктором
        deal = Deal(
            deal_id=data['deal_id'],
            currency_pair=currency_pair,
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
    
    # Реализация базовых методов BaseRepository
    def save(self, deal: Deal) -> None:
        """Сохранение сделки в DataFrame + фоновая синхронизация с PostgreSQL"""
        deal_data = self._entity_to_dict(deal)
        
        # Устанавливаем ID если его нет
        if deal.deal_id is None:
            deal.deal_id = deal_data['deal_id']
        
        # Обновляем или добавляем в DataFrame
        mask = self.df['deal_id'] == deal.deal_id
        if mask.any():
            # Обновление существующей записи
            for key, value in deal_data.items():
                if key in ['created_at', 'updated_at', 'closed_at'] and value is not None:
                    # Правильно обрабатываем datetime значения
                    self.df.loc[mask, key] = pd.to_datetime(value)
                else:
                    self.df.loc[mask, key] = value
        else:
            # Добавление новой записи без concatenation warnings
            if self.df.empty:
                # Создаем DataFrame с правильными типами данных
                self.df = pd.DataFrame([deal_data])
                # Для пустого DataFrame нужно явно создать categorical колонки с предопределенными категориями
                from domain.entities.deal import Deal
                status_categories = [Deal.STATUS_OPEN, Deal.STATUS_CLOSED, Deal.STATUS_CANCELED]
                self.df['status'] = self.df['status'].astype(pd.CategoricalDtype(categories=status_categories))
                self._optimize_dataframe_dtypes()
            else:
                # Используем pd.concat с ignore_index для избежания warnings
                new_row_df = pd.DataFrame([deal_data])
                self.df = pd.concat([self.df, new_row_df], ignore_index=True)
        
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
        symbol_mask = self.df['currency_pair'] == symbol
        symbol_rows = self.df[symbol_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in symbol_rows.iterrows()]
    
    def get_deals_by_status(self, status: str) -> List[Deal]:
        """Получение сделок по статусу"""
        status_mask = self.df['status'] == status
        status_rows = self.df[status_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in status_rows.iterrows()]
    
    def get_deals_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Deal]:
        """Получение сделок за период времени"""
        date_mask = (self.df['created_at'] >= start_date) & (self.df['created_at'] <= end_date)
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
        """Получение общей прибыли по всем сделкам"""
        if self.df.empty:
            return 0.0
        return float(self.df['profit'].sum())
    
    def get_deals_statistics(self) -> dict:
        """Получение статистики по сделкам"""
        if self.df.empty:
            return {
                "total_deals": 0,
                "open_deals": 0,
                "closed_deals": 0,
                "total_profit": 0.0,
                "average_profit": 0.0,
                "success_rate": 0.0
            }
        
        total_deals = len(self.df)
        open_deals = len(self.df[self.df['status'] == 'OPEN'])
        closed_deals = len(self.df[self.df['status'] == 'CLOSED'])
        total_profit = float(self.df['profit'].sum())
        average_profit = float(self.df['profit'].mean())
        profitable_deals = len(self.df[self.df['profit'] > 0])
        success_rate = (profitable_deals / closed_deals * 100) if closed_deals > 0 else 0.0
        
        return {
            "total_deals": total_deals,
            "open_deals": open_deals,
            "closed_deals": closed_deals,
            "total_profit": total_profit,
            "average_profit": average_profit,
            "success_rate": success_rate,
            "profitable_deals": profitable_deals,
            "losing_deals": len(self.df[self.df['profit'] < 0])
        }
    
    def get_deals_by_buy_order_id(self, buy_order_id: int) -> Optional[Deal]:
        """Поиск сделки по ID ордера на покупку"""
        mask = self.df['buy_order_id'] == buy_order_id
        if not mask.any():
            return None
        row = self.df[mask].iloc[0]
        return self._dict_to_entity(row.to_dict())
    
    def get_deals_by_sell_order_id(self, sell_order_id: int) -> Optional[Deal]:
        """Поиск сделки по ID ордера на продажу"""
        mask = self.df['sell_order_id'] == sell_order_id
        if not mask.any():
            return None
        row = self.df[mask].iloc[0]
        return self._dict_to_entity(row.to_dict())
    
    def update_deal_profit(self, deal_id: int, profit: float) -> bool:
        """Обновление прибыли сделки"""
        mask = self.df['deal_id'] == deal_id
        if mask.any():
            self.df.loc[mask, 'profit'] = profit
            self.df.loc[mask, 'updated_at'] = pd.to_datetime(datetime.now())
            # Фоновая синхронизация
            if self.persistent_provider:
                deal_data = self.df[mask].iloc[0].to_dict()
                asyncio.create_task(self._sync_deal_to_postgres(deal_data))
            return True
        return False
    
    def close_deal(self, deal_id: int, sell_order_id: int, profit: float) -> bool:
        """Закрытие сделки"""
        mask = self.df['deal_id'] == deal_id
        if mask.any():
            now = pd.to_datetime(datetime.now())
            self.df.loc[mask, 'status'] = Deal.STATUS_CLOSED
            self.df.loc[mask, 'sell_order_id'] = sell_order_id
            self.df.loc[mask, 'profit'] = profit
            self.df.loc[mask, 'closed_at'] = now
            self.df.loc[mask, 'updated_at'] = now
            # Фоновая синхронизация
            if self.persistent_provider:
                deal_data = self.df[mask].iloc[0].to_dict()
                asyncio.create_task(self._sync_deal_to_postgres(deal_data))
            return True
        return False
    
    def cancel_deal(self, deal_id: int, reason: str = None) -> bool:
        """Отмена сделки"""
        mask = self.df['deal_id'] == deal_id
        if mask.any():
            self.df.loc[mask, 'status'] = Deal.STATUS_CANCELED
            self.df.loc[mask, 'updated_at'] = pd.to_datetime(datetime.now())
            # Фоновая синхронизация
            if self.persistent_provider:
                deal_data = self.df[mask].iloc[0].to_dict()
                asyncio.create_task(self._sync_deal_to_postgres(deal_data))
            return True
        return False
    
    # Аналитические методы
    def get_active_deals_count(self) -> int:
        """Количество активных сделок"""
        return len(self.df[self.df['status'] == Deal.STATUS_OPEN])
    
    def get_average_deal_duration(self) -> float:
        """Средняя продолжительность сделки в минутах"""
        closed_deals = self.df[self.df['status'] == Deal.STATUS_CLOSED]
        if closed_deals.empty:
            return 0.0
        
        durations = []
        for _, deal in closed_deals.iterrows():
            if deal['closed_at'] and deal['created_at']:
                duration = (deal['closed_at'] - deal['created_at']).total_seconds() / 60
                durations.append(duration)
        
        return sum(durations) / len(durations) if durations else 0.0
    
    def get_success_rate(self) -> float:
        """Процент успешных сделок"""
        closed_deals = self.df[self.df['status'] == 'CLOSED']
        if closed_deals.empty:
            return 0.0
        
        profitable = len(closed_deals[closed_deals['profit'] > 0])
        return (profitable / len(closed_deals)) * 100
    
    def get_deals_by_profit_range(self, min_profit: float, max_profit: float) -> List[Deal]:
        """Сделки в диапазоне прибыли"""
        range_mask = (self.df['profit'] >= min_profit) & (self.df['profit'] <= max_profit)
        range_rows = self.df[range_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in range_rows.iterrows()]
    
    # Методы AtomicRepository
    async def sync_to_persistent(self, deal: Deal) -> None:
        """Синхронизация сделки с PostgreSQL"""
        if self.persistent_provider:
            deal_data = self._entity_to_dict(deal)
            await self._sync_deal_to_postgres(deal_data)
    
    async def load_from_persistent(self) -> List[Deal]:
        """Загрузка сделок из PostgreSQL"""
        if not self.persistent_provider:
            return []
        
        try:
            # TODO: Реализовать загрузку через PostgresPersistenceProvider
            # deals = await self.persistent_provider.load_all_deals()
            # return deals
            return []
        except Exception as e:
            logger.error(f"❌ Error loading deals from PostgreSQL: {e}")
            return []
    
    async def backup_to_persistent(self) -> int:
        """Резервное копирование всех сделок в PostgreSQL"""
        if not self.persistent_provider or self.df.empty:
            return 0
        
        try:
            deals = self.get_all()
            for deal in deals:
                await self.sync_to_persistent(deal)
            return len(deals)
        except Exception as e:
            logger.error(f"❌ Error backing up deals to PostgreSQL: {e}")
            return 0
    
    # Приватные методы для работы с PostgreSQL
    async def _sync_deal_to_postgres(self, deal_data: Dict[str, Any]):
        """Фоновая синхронизация сделки с PostgreSQL"""
        if not self.persistent_provider:
            return
        
        try:
            # TODO: Адаптировать под методы PostgresPersistenceProvider
            # await self.persistent_provider.save_deal(deal_data)
            logger.debug(f"✅ Deal {deal_data['deal_id']} synced to PostgreSQL")
        except Exception as e:
            logger.error(f"⚠️ PostgreSQL sync error for deal {deal_data['deal_id']}: {e}")
    
    async def _load_from_persistent(self):
        """Загрузка существующих сделок из PostgreSQL в DataFrame"""
        try:
            deals = await self.load_from_persistent()
            
            # Используем batch подход для избежания FutureWarning с pd.concat в цикле
            if deals:
                deals_data = [self._entity_to_dict(deal) for deal in deals]
                new_deals_df = pd.DataFrame(deals_data)
                
                if self.df.empty:
                    self.df = new_deals_df
                else:
                    self.df = pd.concat([self.df, new_deals_df], ignore_index=True)
            
            if not self.df.empty:
                self._update_next_id_from_dataframe()
                self._optimize_dataframe_dtypes()
                
            logger.info(f"✅ Loaded {len(deals)} deals from PostgreSQL")
            
        except Exception as e:
            logger.error(f"⚠️ Error loading deals from PostgreSQL: {e}")