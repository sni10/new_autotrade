# src/infrastructure/repositories/memory_first/memory_first_order_books_repository.py
import pandas as pd
import asyncio
import os
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from domain.entities.order_book import OrderBook
from ..interfaces.order_books_repository_interface import IOrderBooksRepository
from ..base.base_repository import MemoryFirstRepository
import logging

logger = logging.getLogger(__name__)

class MemoryFirstOrderBooksRepository(MemoryFirstRepository[OrderBook], IOrderBooksRepository):
    """
    Двухуровневый репозиторий стаканов ордеров (ПОТОКОВЫЕ ДАННЫЕ):
    - Уровень 1: DataFrame в памяти (накопление данных)
    - Уровень 2: Parquet файлы (периодические дампы)
    
    Принципы потоковых данных:
    - Накопление в памяти до достижения batch_size
    - Автоматические дампы в Parquet каждые N минут
    - Очистка старых данных для экономии памяти
    - Высокая скорость записи (тысячи обновлений в секунду)
    """
    
    def __init__(self, persistent_provider=None, batch_size: int = 5000, 
                 dump_interval_minutes: int = 3, keep_last_n: int = 50000):
        super().__init__(persistent_provider)
        self.batch_size = batch_size
        self.dump_interval_minutes = dump_interval_minutes
        self.keep_last_n = keep_last_n
        self.parquet_dir = "data/order_books"
        
        # Создаем директорию для Parquet файлов
        os.makedirs(self.parquet_dir, exist_ok=True)
        
        self._initialize_dataframe()
        self._last_dump_time = datetime.now()
        
        # Запускаем фоновую задачу для периодических дампов
        asyncio.create_task(self._periodic_dump_task())
    
    def _get_dataframe_columns(self) -> List[str]:
        """Определяем структуру DataFrame для стаканов ордеров"""
        return [
            'symbol', 'timestamp', 'best_bid', 'best_ask', 'spread',
            'bid_volume', 'ask_volume', 'total_bids', 'total_asks',
            'bids_json', 'asks_json', 'created_at'
        ]
    
    def _get_id_column(self) -> str:
        """ID колонка для стаканов (составной ключ symbol + timestamp)"""
        return 'timestamp'
    
    def _optimize_dataframe_dtypes(self):
        """Оптимизация типов данных для экономии памяти"""
        if not self.df.empty:
            # Оптимизируем типы данных для лучшей производительности
            self.df['symbol'] = self.df['symbol'].astype('category')
            self.df['timestamp'] = self.df['timestamp'].astype('int64')
            self.df['best_bid'] = self.df['best_bid'].astype('float64')
            self.df['best_ask'] = self.df['best_ask'].astype('float64')
            self.df['spread'] = self.df['spread'].astype('float64')
            self.df['bid_volume'] = self.df['bid_volume'].astype('float64')
            self.df['ask_volume'] = self.df['ask_volume'].astype('float64')
            self.df['total_bids'] = self.df['total_bids'].astype('int32')
            self.df['total_asks'] = self.df['total_asks'].astype('int32')
    
    def _entity_to_dict(self, order_book: OrderBook) -> Dict[str, Any]:
        """Преобразование OrderBook в словарь для DataFrame"""
        # Вычисляем метрики
        best_bid = order_book.bids[0][0] if order_book.bids else 0.0
        best_ask = order_book.asks[0][0] if order_book.asks else 0.0
        spread = best_ask - best_bid if best_bid > 0 and best_ask > 0 else 0.0
        
        # Вычисляем объемы
        bid_volume = sum(bid[1] for bid in order_book.bids) if order_book.bids else 0.0
        ask_volume = sum(ask[1] for ask in order_book.asks) if order_book.asks else 0.0
        
        return {
            'symbol': order_book.symbol,
            'timestamp': order_book.timestamp,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'total_bids': len(order_book.bids) if order_book.bids else 0,
            'total_asks': len(order_book.asks) if order_book.asks else 0,
            'bids_json': json.dumps(order_book.bids[:10]) if order_book.bids else '[]',  # Топ 10
            'asks_json': json.dumps(order_book.asks[:10]) if order_book.asks else '[]',  # Топ 10
            'created_at': datetime.now()
        }
    
    def _dict_to_entity(self, data: Dict[str, Any]) -> OrderBook:
        """Преобразование словаря из DataFrame в OrderBook"""
        # Восстанавливаем bids и asks из JSON
        bids = json.loads(data['bids_json']) if data['bids_json'] else []
        asks = json.loads(data['asks_json']) if data['asks_json'] else []
        
        # Создаем OrderBook объект
        order_book = OrderBook(
            symbol=data['symbol'],
            bids=bids,
            asks=asks,
            timestamp=data['timestamp']
        )
        
        return order_book
    
    def save(self, order_book: OrderBook) -> None:
        """
        Сохранение стакана в память (мгновенно) + проверка на дамп
        """
        order_book_data = self._entity_to_dict(order_book)
        
        # Добавляем в DataFrame
        if self.df.empty:
            self.df = pd.DataFrame([order_book_data])
        else:
            # Используем pd.DataFrame.loc для избежания FutureWarning с pd.concat
            new_index = len(self.df)
            self.df.loc[new_index] = order_book_data
        
        # Проверяем необходимость дампа
        if len(self.df) >= self.batch_size:
            asyncio.create_task(self._dump_to_parquet())
        
        # Проверяем необходимость очистки старых данных
        if len(self.df) > self.keep_last_n:
            self._clear_old_data()
    
    def get_by_id(self, order_book_id: int) -> Optional[OrderBook]:
        """Получить стакан по timestamp"""
        mask = self.df['timestamp'] == order_book_id
        if not mask.any():
            return None
        
        row = self.df[mask].iloc[-1]  # Берем последний если несколько
        return self._dict_to_entity(row.to_dict())
    
    def get_all(self) -> List[OrderBook]:
        """Получение всех стаканов из DataFrame"""
        return [self._dict_to_entity(row.to_dict()) for _, row in self.df.iterrows()]
    
    def get_latest_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Получить последний стакан по символу"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return None
        
        # Сортируем по timestamp и берем последний
        symbol_df = self.df[symbol_mask].sort_values('timestamp')
        latest_row = symbol_df.iloc[-1]
        
        return self._dict_to_entity(latest_row.to_dict())
    
    def get_spread_history(self, symbol: str, limit: int = 100) -> List[float]:
        """Получить историю спредов"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return []
        
        symbol_df = self.df[symbol_mask].sort_values('timestamp').tail(limit)
        return symbol_df['spread'].tolist()
    
    def get_order_books_by_symbol(self, symbol: str, limit: int = 1000) -> List[OrderBook]:
        """Получить стаканы по символу с лимитом"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return []
        
        symbol_df = self.df[symbol_mask].sort_values('timestamp').tail(limit)
        return [self._dict_to_entity(row.to_dict()) for _, row in symbol_df.iterrows()]
    
    def get_liquidity_history(self, symbol: str, limit: int = 100) -> List[Tuple[float, float]]:
        """Получить историю ликвидности (bid_volume, ask_volume)"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return []
        
        symbol_df = self.df[symbol_mask].sort_values('timestamp').tail(limit)
        return list(zip(symbol_df['bid_volume'].tolist(), symbol_df['ask_volume'].tolist()))
    
    def get_best_prices_history(self, symbol: str, limit: int = 100) -> List[Tuple[float, float]]:
        """Получить историю лучших цен (best_bid, best_ask)"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return []
        
        symbol_df = self.df[symbol_mask].sort_values('timestamp').tail(limit)
        return list(zip(symbol_df['best_bid'].tolist(), symbol_df['best_ask'].tolist()))
    
    def get_last_n(self, n: int) -> List[OrderBook]:
        """Получить последние N записей"""
        last_df = self.df.sort_values('timestamp').tail(n)
        return [self._dict_to_entity(row.to_dict()) for _, row in last_df.iterrows()]
    
    def get_by_time_range(self, start_time: datetime, end_time: datetime) -> List[OrderBook]:
        """Получить записи за период времени"""
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        time_mask = (self.df['timestamp'] >= start_ts) & (self.df['timestamp'] <= end_ts)
        time_df = self.df[time_mask].sort_values('timestamp')
        
        return [self._dict_to_entity(row.to_dict()) for _, row in time_df.iterrows()]
    
    async def dump_to_persistent(self, batch_size: int = 5000) -> int:
        """Сброс накопленных данных в Parquet файлы"""
        return await self._dump_to_parquet()
    
    def clear_old_data(self, keep_last_n: int = 50000) -> int:
        """Очистка старых данных из памяти"""
        return self._clear_old_data(keep_last_n)
    
    def get_memory_usage_mb(self) -> float:
        """Получить использование памяти в МБ"""
        if self.df.empty:
            return 0.0
        memory_usage = self.df.memory_usage(deep=True).sum()
        return memory_usage / (1024 * 1024)
    
    def delete_by_id(self, order_book_id: int) -> bool:
        """Удалить стакан по timestamp"""
        mask = self.df['timestamp'] == order_book_id
        if mask.any():
            self.df = self.df[~mask].reset_index(drop=True)
            return True
        return False
    
    async def _dump_to_parquet(self) -> int:
        """Сброс данных в Parquet файл"""
        if self.df.empty:
            return 0
        
        try:
            # Создаем имя файла с текущей датой
            filename = f"order_books_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            filepath = os.path.join(self.parquet_dir, filename)
            
            # Сохраняем в Parquet
            self.df.to_parquet(filepath, compression='snappy', index=False)
            
            dumped_count = len(self.df)
            logger.info(f"✅ Dumped {dumped_count} order books to {filepath}")
            
            # Очищаем DataFrame после успешного дампа
            self.df = pd.DataFrame(columns=self._get_dataframe_columns())
            self._optimize_dataframe_dtypes()
            
            self._last_dump_time = datetime.now()
            return dumped_count
            
        except Exception as e:
            logger.error(f"❌ Error dumping order books to Parquet: {e}")
            return 0
    
    def _clear_old_data(self, keep_last_n: int = None) -> int:
        """Очистка старых данных из памяти"""
        if keep_last_n is None:
            keep_last_n = self.keep_last_n
        
        if len(self.df) <= keep_last_n:
            return 0
        
        # Сортируем по timestamp и оставляем только последние N записей
        self.df = self.df.sort_values('timestamp').tail(keep_last_n).reset_index(drop=True)
        
        removed_count = len(self.df) - keep_last_n
        logger.info(f"🧹 Cleared {removed_count} old order books from memory")
        
        return removed_count
    
    async def _periodic_dump_task(self):
        """Фоновая задача для периодических дампов"""
        while True:
            try:
                await asyncio.sleep(self.dump_interval_minutes * 60)  # Конвертируем в секунды
                
                # Проверяем, нужен ли дамп
                time_since_last_dump = datetime.now() - self._last_dump_time
                if time_since_last_dump.total_seconds() >= self.dump_interval_minutes * 60:
                    if not self.df.empty:
                        await self._dump_to_parquet()
                        
            except Exception as e:
                logger.error(f"❌ Error in periodic dump task: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед повтором