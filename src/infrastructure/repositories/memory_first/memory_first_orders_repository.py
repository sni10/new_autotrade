# src/infrastructure/repositories/memory_first/memory_first_orders_repository.py
import pandas as pd
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from domain.entities.order import Order
from ..interfaces.orders_repository_interface import IOrdersRepository
from ..base.base_repository import MemoryFirstRepository
import logging

logger = logging.getLogger(__name__)

class MemoryFirstOrdersRepository(MemoryFirstRepository[Order], IOrdersRepository):
    """
    Двухуровневый репозиторий ордеров (АТОМАРНЫЕ ДАННЫЕ):
    - Уровень 1: DataFrame в памяти (все операции в наносекундах)
    - Уровень 2: PostgreSQL (мгновенная фоновая синхронизация)
    
    Принципы атомарных данных:
    - Все операции чтения/записи работают с DataFrame
    - PostgreSQL синхронизация полностью прозрачна
    - Фоновая синхронизация не блокирует торговлю
    - Автоматическое восстановление после перезапуска
    - Критически важные данные сразу в БД
    """
    
    def __init__(self, persistent_provider=None):
        super().__init__(persistent_provider)
        self._initialize_dataframe()
        
        # Загружаем существующие данные из БД при инициализации
        if persistent_provider:
            asyncio.create_task(self._load_from_persistent())
    
    def _get_dataframe_columns(self) -> List[str]:
        """Определяем структуру DataFrame для ордеров"""
        return [
            'order_id', 'exchange_order_id', 'deal_id', 'order_type', 'side',
            'symbol', 'amount', 'price', 'status', 'created_at', 'updated_at',
            'filled_amount', 'fees', 'commission'
        ]
    
    def _get_id_column(self) -> str:
        """ID колонка для ордеров"""
        return 'order_id'
    
    def _optimize_dataframe_dtypes(self):
        """Оптимизация типов данных для экономии памяти"""
        if not self.df.empty:
            # Оптимизируем типы данных для лучшей производительности
            self.df['order_id'] = self.df['order_id'].astype('int32')
            self.df['deal_id'] = self.df['deal_id'].astype('int32')
            self.df['amount'] = self.df['amount'].astype('float64')
            self.df['price'] = self.df['price'].astype('float64')
            self.df['filled_amount'] = self.df['filled_amount'].astype('float64')
            self.df['fees'] = self.df['fees'].astype('float64')
            self.df['commission'] = self.df['commission'].astype('float64')
            self.df['status'] = self.df['status'].astype('category')
            self.df['order_type'] = self.df['order_type'].astype('category')
            self.df['side'] = self.df['side'].astype('category')
            self.df['symbol'] = self.df['symbol'].astype('category')
    
    def _entity_to_dict(self, order: Order) -> Dict[str, Any]:
        """Преобразование Order в словарь для DataFrame"""
        # Функция для конвертации timestamp в datetime
        def timestamp_to_datetime(timestamp):
            if timestamp is None:
                return datetime.now()
            if isinstance(timestamp, int):
                # Конвертируем миллисекунды в секунды для datetime
                return datetime.fromtimestamp(timestamp / 1000.0)
            if isinstance(timestamp, datetime):
                return timestamp
            return datetime.now()
        
        return {
            'order_id': order.order_id if order.order_id else self._get_next_id(),
            'exchange_order_id': order.exchange_id,  # Исправлено: exchange_id вместо exchange_order_id
            'deal_id': order.deal_id,
            'order_type': order.order_type if order.order_type else Order.TYPE_LIMIT,
            'side': order.side if order.side else Order.SIDE_BUY,
            'symbol': order.symbol,
            'amount': float(order.amount) if order.amount else 0.0,
            'price': float(order.price) if order.price else 0.0,
            'status': order.status if order.status else Order.STATUS_PENDING,
            'created_at': timestamp_to_datetime(order.created_at),
            'updated_at': timestamp_to_datetime(order.last_update),  # Исправлено: last_update вместо updated_at
            'filled_amount': float(order.filled_amount) if order.filled_amount else 0.0,
            'fees': float(order.fees) if order.fees else 0.0,
            'commission': 0.0  # В Order нет поля commission, используем 0.0
        }
    
    def _dict_to_entity(self, data: Dict[str, Any]) -> Order:
        """Преобразование словаря из DataFrame в Order"""
        order = Order(
            order_id=data['order_id'],
            side=data['side'],
            order_type=data['order_type'],
            price=data['price'],
            amount=data['amount'],
            status=data['status'],
            created_at=data['created_at'],
            deal_id=data['deal_id'],
            exchange_id=data['exchange_order_id'],
            symbol=data['symbol'],
            filled_amount=data['filled_amount'],
            fees=data['fees'],
            last_update=data['updated_at']
        )
        
        return order
    
    def save(self, order: Order) -> None:
        """
        Сохранение ордера в память (мгновенно) + фоновая синхронизация с БД
        """
        order_data = self._entity_to_dict(order)
        
        if order.order_id is None:
            order.order_id = self._get_next_id()
            self._increment_next_id()
        
        # Обновляем или добавляем в DataFrame
        mask = self.df['order_id'] == order.order_id
        if mask.any():
            # Обновление существующей записи
            for key, value in order_data.items():
                self.df.loc[mask, key] = value
        else:
            # Добавление новой записи (оптимизированный способ)
            if self.df.empty:
                self.df = pd.DataFrame([order_data])
            else:
                # Используем pd.DataFrame.loc для избежания FutureWarning с pd.concat
                new_index = len(self.df)
                self.df.loc[new_index] = order_data
        
        # Фоновая синхронизация с PostgreSQL (не блокирует торговлю)
        try:
            # Проверяем, есть ли запущенный event loop
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._sync_order_to_postgres(order_data))
        except RuntimeError:
            # Если нет event loop (например, в тестах), пропускаем фоновую синхронизацию
            pass
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Чтение ордера из DataFrame (наносекунды)"""
        mask = self.df['order_id'] == order_id
        if not mask.any():
            return None
        
        row = self.df[mask].iloc[0]
        return self._dict_to_entity(row.to_dict())
    
    def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        """Получить ордер по биржевому ID"""
        mask = self.df['exchange_order_id'] == exchange_id
        if not mask.any():
            return None
        
        row = self.df[mask].iloc[0]
        return self._dict_to_entity(row.to_dict())
    
    def get_open_orders(self) -> List[Order]:
        """Получение открытых ордеров из DataFrame"""
        # ИСПРАВЛЕНИЕ: Добавлен статус 'open' для корректной работы BuyOrderMonitor
        open_statuses = ['NEW', 'PARTIALLY_FILLED', 'open']
        open_mask = self.df['status'].isin(open_statuses)
        open_rows = self.df[open_mask]
        
        return [self._dict_to_entity(row.to_dict()) for _, row in open_rows.iterrows()]
    
    def get_orders_by_deal(self, deal_id: int) -> List[Order]:
        """Получить ордера по сделке"""
        deal_mask = self.df['deal_id'] == deal_id
        deal_rows = self.df[deal_mask]
        
        return [self._dict_to_entity(row.to_dict()) for _, row in deal_rows.iterrows()]
    
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Получить ордера по символу"""
        symbol_mask = self.df['symbol'] == symbol
        symbol_rows = self.df[symbol_mask]
        
        return [self._dict_to_entity(row.to_dict()) for _, row in symbol_rows.iterrows()]
    
    def get_all(self) -> List[Order]:
        """Получение всех ордеров из DataFrame"""
        return [self._dict_to_entity(row.to_dict()) for _, row in self.df.iterrows()]
    
    def delete_by_id(self, order_id: int) -> bool:
        """Удалить ордер по ID"""
        mask = self.df['order_id'] == order_id
        if mask.any():
            self.df = self.df[~mask].reset_index(drop=True)
            # Фоновое удаление из PostgreSQL
            if self.persistent_provider:
                asyncio.create_task(self._delete_order_from_postgres(order_id))
            return True
        return False
    
    # Специализированные методы для ордеров
    
    def update_order_status(self, order_id: int, status: str, 
                           filled_amount: float = None, fees: float = None) -> bool:
        """Обновление статуса ордера"""
        mask = self.df['order_id'] == order_id
        if not mask.any():
            return False
        
        self.df.loc[mask, 'status'] = status
        self.df.loc[mask, 'updated_at'] = datetime.now()
        
        if filled_amount is not None:
            self.df.loc[mask, 'filled_amount'] = filled_amount
        
        if fees is not None:
            self.df.loc[mask, 'fees'] = fees
        
        # Фоновая синхронизация
        if self.persistent_provider:
            order_data = self.df[mask].iloc[0].to_dict()
            asyncio.create_task(self._sync_order_to_postgres(order_data))
        
        return True
    
    def cancel_order(self, order_id: int, reason: str = None) -> bool:
        """Отмена ордера"""
        return self.update_order_status(order_id, Order.STATUS_CANCELED)
    
    def fill_order(self, order_id: int, filled_amount: float, fees: float = 0.0) -> bool:
        """Исполнение ордера"""
        mask = self.df['order_id'] == order_id
        if not mask.any():
            return False
        
        # Определяем новый статус
        order_amount = self.df.loc[mask, 'amount'].iloc[0]
        if filled_amount >= order_amount:
            new_status = Order.STATUS_FILLED
        else:
            new_status = Order.STATUS_PARTIALLY_FILLED
        
        return self.update_order_status(order_id, new_status, filled_amount, fees)
    
    def get_orders_statistics(self) -> Dict[str, Any]:
        """Получить статистику по ордерам"""
        if self.df.empty:
            return {
                "total_orders": 0,
                "open_orders": 0,
                "filled_orders": 0,
                "canceled_orders": 0,
                "total_volume": 0.0,
                "avg_order_size": 0.0
            }
        
        stats = {
            "total_orders": len(self.df),
            # ИСПРАВЛЕНИЕ: Добавлен статус 'open' для консистентности с get_open_orders()
            "open_orders": len(self.df[self.df['status'].isin(['NEW', 'PARTIALLY_FILLED', 'open'])]),
            "filled_orders": len(self.df[self.df['status'] == 'FILLED']),
            "canceled_orders": len(self.df[self.df['status'] == 'CANCELED']),
            "total_volume": self.df['amount'].sum(),
            "avg_order_size": self.df['amount'].mean()
        }
        
        return stats
    
    async def _sync_order_to_postgres(self, order_data: Dict[str, Any]):
        """Фоновая синхронизация ордера с PostgreSQL"""
        if not self.persistent_provider:
            return
        
        try:
            # Функция для безопасной конвертации timestamp в datetime
            def ensure_datetime(timestamp):
                if timestamp is None:
                    return datetime.now()
                if isinstance(timestamp, int):
                    # Конвертируем миллисекунды в секунды для datetime
                    return datetime.fromtimestamp(timestamp / 1000.0)
                if isinstance(timestamp, datetime):
                    return timestamp
                # Handle pandas Timestamp objects (from DataFrame.to_dict())
                if hasattr(timestamp, 'to_pydatetime'):
                    return timestamp.to_pydatetime()
                # Handle any other timestamp-like objects
                if hasattr(timestamp, 'timestamp'):
                    return datetime.fromtimestamp(timestamp.timestamp())
                # Fallback for unknown types
                logger.warning(f"Unknown timestamp type {type(timestamp)}, using current time")
                return datetime.now()
            
            # Создаем копию order_data с правильно конвертированными timestamps
            safe_order_data = order_data.copy()
            
            # Обеспечиваем правильную конвертацию timestamp полей
            if 'created_at' in safe_order_data:
                safe_order_data['created_at'] = ensure_datetime(safe_order_data['created_at'])
            if 'updated_at' in safe_order_data:
                safe_order_data['updated_at'] = ensure_datetime(safe_order_data['updated_at'])
            
            # Add the complete order data as JSON for the 'data' field
            import json
            order_json = json.dumps(safe_order_data, default=str)
            
            async with self.persistent_provider._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO orders (order_id, exchange_order_id, deal_id, order_type, side,
                                      symbol, amount, price, status, created_at, updated_at,
                                      filled_amount, fees, commission, data)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (order_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at,
                        filled_amount = EXCLUDED.filled_amount,
                        fees = EXCLUDED.fees,
                        commission = EXCLUDED.commission,
                        exchange_order_id = EXCLUDED.exchange_order_id,
                        data = EXCLUDED.data
                """, *safe_order_data.values(), order_json)
                
        except Exception as e:
            # Логируем ошибку, но не прерываем торговлю
            logger.error(f"⚠️ PostgreSQL order sync error: {e}")
    
    async def _delete_order_from_postgres(self, order_id: int):
        """Фоновое удаление ордера из PostgreSQL"""
        if not self.persistent_provider:
            return
        
        try:
            async with self.persistent_provider._pool.acquire() as conn:
                await conn.execute("DELETE FROM orders WHERE order_id = $1", order_id)
                
        except Exception as e:
            logger.error(f"⚠️ PostgreSQL order delete error: {e}")
    
    async def _load_from_persistent(self):
        """Загрузка существующих ордеров из PostgreSQL в DataFrame"""
        try:
            orders = await self.load_from_persistent()
            
            # Используем batch подход для избежания FutureWarning с pd.concat в цикле
            if orders:
                orders_data = [self._entity_to_dict(order) for order in orders]
                new_orders_df = pd.DataFrame(orders_data)
                
                if self.df.empty:
                    self.df = new_orders_df
                else:
                    self.df = pd.concat([self.df, new_orders_df], ignore_index=True)
            
            if not self.df.empty:
                self._next_id = self.df['order_id'].max() + 1
                
            logger.info(f"✅ Loaded {len(orders)} orders from PostgreSQL")
            
        except Exception as e:
            logger.error(f"⚠️ Error loading orders from persistent storage: {e}")
    
    async def sync_to_persistent(self, order: Order) -> None:
        """Синхронизация с персистентным хранилищем"""
        if self.persistent_provider:
            order_data = self._entity_to_dict(order)
            await self._sync_order_to_postgres(order_data)
    
    async def load_from_persistent(self) -> List[Order]:
        """Загрузка из персистентного хранилища"""
        if self.persistent_provider:
            return await self.persistent_provider.load_all_orders()
        return []
    
    async def backup_to_persistent(self) -> int:
        """Резервное копирование всех ордеров в PostgreSQL"""
        if not self.persistent_provider or self.df.empty:
            return 0
        
        try:
            orders = self.get_all()
            for order in orders:
                await self.sync_to_persistent(order)
            return len(orders)
        except Exception as e:
            logger.error(f"❌ Error backing up orders to PostgreSQL: {e}")
            return 0
    
    # Недостающие методы из IOrdersRepository
    
    def get_all_by_deal(self, deal_id: int) -> List[Order]:
        """Получить все ордера по сделке (алиас для get_orders_by_deal)"""
        return self.get_orders_by_deal(deal_id)
    
    def get_orders_by_status(self, status: str) -> List[Order]:
        """Получить ордера по статусу"""
        status_mask = self.df['status'] == status
        status_rows = self.df[status_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in status_rows.iterrows()]
    
    def get_pending_orders(self) -> List[Order]:
        """Получить ордера в ожидании исполнения"""
        pending_statuses = ['NEW', 'PENDING', 'PARTIALLY_FILLED']
        pending_mask = self.df['status'].isin(pending_statuses)
        pending_rows = self.df[pending_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in pending_rows.iterrows()]
    
    def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """Получить ордера за период времени"""
        date_mask = (self.df['created_at'] >= start_date) & (self.df['created_at'] <= end_date)
        date_rows = self.df[date_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in date_rows.iterrows()]
    
    def bulk_update_status(self, order_ids: List[int], status: str) -> int:
        """Массовое обновление статуса ордеров"""
        updated_count = 0
        for order_id in order_ids:
            if self.update_order_status(order_id, status):
                updated_count += 1
        return updated_count
    
    def delete_old_orders(self, older_than_days: int) -> int:
        """Удаление старых ордеров"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        old_mask = self.df['created_at'] < cutoff_date
        old_orders = self.df[old_mask]
        
        if not old_orders.empty:
            self.df = self.df[~old_mask].reset_index(drop=True)
            return len(old_orders)
        return 0
    
    def search_orders(self, symbol: str = None, status: str = None, deal_id: int = None,
                     exchange_id: str = None, side: str = None, order_type: str = None,
                     min_amount: float = None, max_amount: float = None,
                     date_from: datetime = None, date_to: datetime = None,
                     limit: int = None) -> List[Order]:
        """Расширенный поиск ордеров по множественным критериям"""
        mask = pd.Series([True] * len(self.df), index=self.df.index)
        
        if symbol:
            mask &= (self.df['symbol'] == symbol)
        if status:
            mask &= (self.df['status'] == status)
        if deal_id:
            mask &= (self.df['deal_id'] == deal_id)
        if exchange_id:
            mask &= (self.df['exchange_order_id'] == exchange_id)
        if side:
            mask &= (self.df['side'] == side)
        if order_type:
            mask &= (self.df['order_type'] == order_type)
        if min_amount:
            mask &= (self.df['amount'] >= min_amount)
        if max_amount:
            mask &= (self.df['amount'] <= max_amount)
        if date_from:
            mask &= (self.df['created_at'] >= date_from)
        if date_to:
            mask &= (self.df['created_at'] <= date_to)
        
        filtered_df = self.df[mask]
        if limit:
            filtered_df = filtered_df.head(limit)
        
        return [self._dict_to_entity(row.to_dict()) for _, row in filtered_df.iterrows()]
    
    def get_orders_with_errors(self) -> List[Order]:
        """Получить ордера с ошибками"""
        error_statuses = ['FAILED', 'ERROR', 'REJECTED']
        error_mask = self.df['status'].isin(error_statuses)
        error_rows = self.df[error_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in error_rows.iterrows()]
    
    def get_orders_requiring_sync(self) -> List[Order]:
        """Получить ордера, требующие синхронизации с биржей"""
        # Ордера без exchange_order_id или со статусом PENDING
        sync_mask = (self.df['exchange_order_id'].isna()) | (self.df['status'] == 'PENDING')
        sync_rows = self.df[sync_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in sync_rows.iterrows()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по ордерам (алиас для get_orders_statistics)"""
        return self.get_orders_statistics()
    
    def export_to_json(self, file_path: str = None) -> str:
        """Экспорт ордеров в JSON"""
        import json
        orders_data = [self._dict_to_entity(row.to_dict()).to_dict() for _, row in self.df.iterrows()]
        json_data = json.dumps(orders_data, indent=2, default=str)
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
        
        return json_data
    
    def import_from_json(self, json_data: str = None, file_path: str = None) -> int:
        """Импорт ордеров из JSON"""
        import json
        
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = f.read()
        
        if not json_data:
            return 0
        
        orders_data = json.loads(json_data)
        imported_count = 0
        
        for order_data in orders_data:
            try:
                order = Order(**order_data)
                self.save(order)
                imported_count += 1
            except Exception as e:
                logger.error(f"Error importing order: {e}")
        
        return imported_count
    
    def rebuild_indexes(self) -> None:
        """Перестроить индексы для оптимизации поиска"""
        # Для DataFrame индексы перестраиваются автоматически
        # Оптимизируем типы данных
        self._optimize_dataframe_dtypes()
    
    def get_orders_by_side(self, side: str) -> List[Order]:
        """Получить ордера по стороне (BUY/SELL)"""
        side_mask = self.df['side'] == side
        side_rows = self.df[side_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in side_rows.iterrows()]
    
    def get_orders_by_type(self, order_type: str) -> List[Order]:
        """Получить ордера по типу (MARKET/LIMIT)"""
        type_mask = self.df['order_type'] == order_type
        type_rows = self.df[type_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in type_rows.iterrows()]
    
    def get_filled_orders(self) -> List[Order]:
        """Получить исполненные ордера"""
        filled_mask = self.df['status'] == 'FILLED'
        filled_rows = self.df[filled_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in filled_rows.iterrows()]
    
    def get_cancelled_orders(self) -> List[Order]:
        """Получить отмененные ордера"""
        cancelled_mask = self.df['status'] == 'CANCELED'
        cancelled_rows = self.df[cancelled_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in cancelled_rows.iterrows()]
    
    def get_partially_filled_orders(self) -> List[Order]:
        """Получить частично исполненные ордера"""
        partial_mask = self.df['status'] == 'PARTIALLY_FILLED'
        partial_rows = self.df[partial_mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in partial_rows.iterrows()]
    
    def update_order_filled_amount(self, order_id: int, filled_amount: float) -> bool:
        """Обновить исполненное количество ордера"""
        return self.update_order_status(order_id, None, filled_amount)
    
    def update_order_fees(self, order_id: int, fees: float) -> bool:
        """Обновить комиссии ордера"""
        return self.update_order_status(order_id, None, None, fees)
    
    def get_total_volume_by_symbol(self, symbol: str) -> float:
        """Получить общий объем торгов по символу"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return 0.0
        return float(self.df[symbol_mask]['amount'].sum())
    
    def get_average_order_size(self, symbol: str = None) -> float:
        """Получить средний размер ордера"""
        if symbol:
            symbol_mask = self.df['symbol'] == symbol
            if not symbol_mask.any():
                return 0.0
            return float(self.df[symbol_mask]['amount'].mean())
        else:
            if self.df.empty:
                return 0.0
            return float(self.df['amount'].mean())
    
    def get_order_success_rate(self) -> float:
        """Получить процент успешно исполненных ордеров"""
        if self.df.empty:
            return 0.0
        
        total_orders = len(self.df)
        filled_orders = len(self.df[self.df['status'] == 'FILLED'])
        return (filled_orders / total_orders) * 100
    
    def get_orders_by_price_range(self, symbol: str, min_price: float, max_price: float) -> List[Order]:
        """Получить ордера в диапазоне цен"""
        mask = (self.df['symbol'] == symbol) & (self.df['price'] >= min_price) & (self.df['price'] <= max_price)
        range_rows = self.df[mask]
        return [self._dict_to_entity(row.to_dict()) for _, row in range_rows.iterrows()]
    
    def get_recent_orders(self, limit: int = 100) -> List[Order]:
        """Получить последние ордера"""
        recent_df = self.df.sort_values('created_at', ascending=False).head(limit)
        return [self._dict_to_entity(row.to_dict()) for _, row in recent_df.iterrows()]
    
    def _increment_next_id(self):
        """Увеличить счетчик ID"""
        self._next_id += 1