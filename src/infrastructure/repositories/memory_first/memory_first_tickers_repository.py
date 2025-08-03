# src/infrastructure/repositories/memory_first/memory_first_tickers_repository.py
import pandas as pd
import asyncio
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from domain.entities.ticker import Ticker
from ..interfaces.tickers_repository_interface import ITickersRepository
from ..base.base_repository import MemoryFirstRepository
import logging

logger = logging.getLogger(__name__)

class MemoryFirstTickersRepository(MemoryFirstRepository[Ticker], ITickersRepository):
    """
    Двухуровневый репозиторий тикеров (ПОТОКОВЫЕ ДАННЫЕ):
    - Уровень 1: DataFrame в памяти (накопление данных)
    - Уровень 2: Parquet файлы (периодические дампы)
    
    Принципы потоковых данных:
    - Накопление в памяти до достижения batch_size
    - Автоматические дампы в Parquet каждые N минут
    - Очистка старых данных для экономии памяти
    - Высокая скорость записи (миллионы тикеров)
    """
    
    def __init__(self, persistent_provider=None, batch_size: int = 10000, 
                 dump_interval_minutes: int = 5, keep_last_n: int = 100000):
        super().__init__(persistent_provider)
        self.batch_size = batch_size
        self.dump_interval_minutes = dump_interval_minutes
        self.keep_last_n = keep_last_n
        self.parquet_dir = "data/tickers"
        
        # Создаем директорию для Parquet файлов
        os.makedirs(self.parquet_dir, exist_ok=True)
        
        self._initialize_dataframe()
        self._last_dump_time = datetime.now()
        
        # Запускаем фоновую задачу для периодических дампов
        asyncio.create_task(self._periodic_dump_task())
    
    def _get_dataframe_columns(self) -> List[str]:
        """Определяем структуру DataFrame для тикеров"""
        return [
            'symbol', 'timestamp', 'last_price', 'bid_price', 'ask_price',
            'volume', 'high', 'low', 'open', 'close', 'change', 'change_percent',
            'created_at'
        ]
    
    def _get_id_column(self) -> str:
        """ID колонка для тикеров (составной ключ symbol + timestamp)"""
        return 'timestamp'
    
    def _optimize_dataframe_dtypes(self):
        """Оптимизация типов данных для экономии памяти"""
        if not self.df.empty:
            # Оптимизируем типы данных для лучшей производительности
            self.df['symbol'] = self.df['symbol'].astype('category')
            self.df['timestamp'] = self.df['timestamp'].astype('int64')
            self.df['last_price'] = self.df['last_price'].astype('float64')
            self.df['bid_price'] = self.df['bid_price'].astype('float64')
            self.df['ask_price'] = self.df['ask_price'].astype('float64')
            self.df['volume'] = self.df['volume'].astype('float64')
    
    def _entity_to_dict(self, ticker: Ticker) -> Dict[str, Any]:
        """Преобразование Ticker в словарь для DataFrame"""
        return {
            'symbol': ticker.symbol,
            'timestamp': ticker.timestamp,
            'last_price': float(ticker.last) if ticker.last else 0.0,
            'bid_price': float(ticker.bid) if ticker.bid else 0.0,
            'ask_price': float(ticker.ask) if ticker.ask else 0.0,
            'volume': float(ticker.baseVolume) if ticker.baseVolume else 0.0,
            'high': float(ticker.high) if ticker.high else 0.0,
            'low': float(ticker.low) if ticker.low else 0.0,
            'open': float(ticker.open) if ticker.open else 0.0,
            'close': float(ticker.close) if ticker.close else 0.0,
            'change': float(ticker.change) if ticker.change else 0.0,
            'change_percent': float(ticker.percentage) if ticker.percentage else 0.0,
            'created_at': datetime.now()
        }
    
    def _dict_to_entity(self, data: Dict[str, Any]) -> Ticker:
        """Преобразование словаря из DataFrame в Ticker"""
        # Создаем базовый ticker объект
        ticker = Ticker(
            symbol=data['symbol'],
            timestamp=data['timestamp']
        )
        
        # Заполняем поля
        ticker.last = data['last_price']
        ticker.bid = data['bid_price']
        ticker.ask = data['ask_price']
        ticker.baseVolume = data['volume']
        ticker.high = data['high']
        ticker.low = data['low']
        ticker.open = data['open']
        ticker.close = data['close']
        ticker.change = data['change']
        ticker.percentage = data['change_percent']
        
        return ticker
    
    def save(self, ticker: Ticker) -> None:
        """
        Сохранение тикера в память (мгновенно) + проверка на дамп
        """
        ticker_data = self._entity_to_dict(ticker)
        
        # Добавляем в DataFrame
        if self.df.empty:
            self.df = pd.DataFrame([ticker_data])
        else:
            # Используем pd.DataFrame.loc для избежания FutureWarning с pd.concat
            new_index = len(self.df)
            self.df.loc[new_index] = ticker_data
        
        # Проверяем необходимость дампа
        if len(self.df) >= self.batch_size:
            asyncio.create_task(self._dump_to_parquet())
        
        # Проверяем необходимость очистки старых данных
        if len(self.df) > self.keep_last_n:
            self._clear_old_data()
    
    def get_by_id(self, ticker_id: int) -> Optional[Ticker]:
        """Получить тикер по timestamp"""
        mask = self.df['timestamp'] == ticker_id
        if not mask.any():
            return None
        
        row = self.df[mask].iloc[-1]  # Берем последний если несколько
        return self._dict_to_entity(row.to_dict())
    
    def get_all(self) -> List[Ticker]:
        """Получение всех тикеров из DataFrame"""
        return [self._dict_to_entity(row.to_dict()) for _, row in self.df.iterrows()]
    
    def get_latest_ticker(self, symbol: str) -> Optional[Ticker]:
        """Получить последний тикер по символу"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return None
        
        # Сортируем по timestamp и берем последний
        symbol_df = self.df[symbol_mask].sort_values('timestamp')
        latest_row = symbol_df.iloc[-1]
        
        return self._dict_to_entity(latest_row.to_dict())
    
    def get_price_history(self, symbol: str, limit: int = 100) -> List[float]:
        """Получить историю цен"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return []
        
        symbol_df = self.df[symbol_mask].sort_values('timestamp').tail(limit)
        return symbol_df['last_price'].tolist()
    
    def get_tickers_by_symbol(self, symbol: str, limit: int = 1000) -> List[Ticker]:
        """Получить тикеры по символу с лимитом"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return []
        
        symbol_df = self.df[symbol_mask].sort_values('timestamp').tail(limit)
        return [self._dict_to_entity(row.to_dict()) for _, row in symbol_df.iterrows()]
    
    def get_volume_history(self, symbol: str, limit: int = 100) -> List[float]:
        """Получить историю объемов"""
        symbol_mask = self.df['symbol'] == symbol
        if not symbol_mask.any():
            return []
        
        symbol_df = self.df[symbol_mask].sort_values('timestamp').tail(limit)
        return symbol_df['volume'].tolist()
    
    def get_last_n(self, n: int) -> List[Ticker]:
        """Получить последние N записей"""
        last_df = self.df.sort_values('timestamp').tail(n)
        return [self._dict_to_entity(row.to_dict()) for _, row in last_df.iterrows()]
    
    def get_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Ticker]:
        """Получить записи за период времени"""
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        time_mask = (self.df['timestamp'] >= start_ts) & (self.df['timestamp'] <= end_ts)
        time_df = self.df[time_mask].sort_values('timestamp')
        
        return [self._dict_to_entity(row.to_dict()) for _, row in time_df.iterrows()]
    
    async def dump_to_persistent(self, batch_size: int = 10000) -> int:
        """Сброс накопленных данных в Parquet файлы"""
        return await self._dump_to_parquet()
    
    def clear_old_data(self, keep_last_n: int = 100000) -> int:
        """Очистка старых данных из памяти"""
        return self._clear_old_data(keep_last_n)
    
    def get_memory_usage_mb(self) -> float:
        """Получить использование памяти в МБ"""
        if self.df.empty:
            return 0.0
        memory_usage = self.df.memory_usage(deep=True).sum()
        return memory_usage / (1024 * 1024)
    
    def delete_by_id(self, ticker_id: int) -> bool:
        """Удалить тикер по timestamp"""
        mask = self.df['timestamp'] == ticker_id
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
            filename = f"tickers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            filepath = os.path.join(self.parquet_dir, filename)
            
            # Сохраняем в Parquet
            self.df.to_parquet(filepath, compression='snappy', index=False)
            
            dumped_count = len(self.df)
            logger.info(f"✅ Dumped {dumped_count} tickers to {filepath}")
            
            # Очищаем DataFrame после успешного дампа
            self.df = pd.DataFrame(columns=self._get_dataframe_columns())
            self._optimize_dataframe_dtypes()
            
            self._last_dump_time = datetime.now()
            return dumped_count
            
        except Exception as e:
            logger.error(f"❌ Error dumping tickers to Parquet: {e}")
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
        logger.info(f"🧹 Cleared {removed_count} old tickers from memory")
        
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