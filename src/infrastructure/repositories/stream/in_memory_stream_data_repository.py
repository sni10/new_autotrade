import asyncio
import json
import time
from typing import List, Optional, Dict, Any, Union
from collections import defaultdict, deque
import numpy as np
import logging

from src.domain.repositories.i_stream_data_repository import IStreamDataRepository

logger = logging.getLogger(__name__)


class InMemoryStreamDataRepository(IStreamDataRepository):
    """
    In-Memory реализация StreamDataRepository для высокочастотных данных
    Оптимизирована для работы с JSON-массивами напрямую
    """
    
    def __init__(self):
        # Хранилища данных как JSON-массивы для производительности
        self._ticker_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._orderbook_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Буферы индикаторов для быстрых вычислений
        self._indicator_buffers: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=100)))
        
        # Кэши для оптимизации
        self._price_cache: Dict[str, List[float]] = defaultdict(list)
        self._latest_ticker_cache: Dict[str, Dict[str, Any]] = {}
        self._latest_orderbook_cache: Dict[str, Dict[str, Any]] = {}
        
        # Статистика производительности
        self._stats = {
            "ticker_appends": 0,
            "orderbook_appends": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def append_ticker_data(
        self, 
        symbol: str, 
        ticker_data: Dict[str, Any],
        max_history_size: int = 1000
    ) -> None:
        """Добавить данные тикера в JSON-массив с оптимизацией"""
        try:
            # Валидация основных полей
            if 'timestamp' not in ticker_data or 'close' not in ticker_data:
                logger.warning(f"Invalid ticker data for {symbol}: missing timestamp or close")
                return
            
            # Обновляем размер буфера если нужно
            if self._ticker_data[symbol].maxlen != max_history_size:
                new_deque = deque(self._ticker_data[symbol], maxlen=max_history_size)
                self._ticker_data[symbol] = new_deque
            
            # Добавляем данные
            self._ticker_data[symbol].append(ticker_data.copy())
            
            # Обновляем кэш цен для быстрого доступа
            price = float(ticker_data['close'])
            price_cache = self._price_cache[symbol]
            price_cache.append(price)
            
            # Ограничиваем размер кэша цен
            if len(price_cache) > max_history_size:
                price_cache.pop(0)
            
            # Обновляем кэш последнего тикера
            self._latest_ticker_cache[symbol] = ticker_data.copy()
            
            self._stats["ticker_appends"] += 1
            
        except Exception as e:
            logger.error(f"Error appending ticker data for {symbol}: {e}")
    
    async def get_ticker_history(
        self, 
        symbol: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Получить историю тикеров как список словарей"""
        try:
            if symbol not in self._ticker_data:
                return []
            
            data = list(self._ticker_data[symbol])
            if limit > 0:
                data = data[-limit:]
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting ticker history for {symbol}: {e}")
            return []
    
    async def get_latest_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Получить последний тикер из кэша"""
        if symbol in self._latest_ticker_cache:
            self._stats["cache_hits"] += 1
            return self._latest_ticker_cache[symbol].copy()
        
        if symbol in self._ticker_data and self._ticker_data[symbol]:
            self._stats["cache_misses"] += 1
            latest = self._ticker_data[symbol][-1]
            self._latest_ticker_cache[symbol] = latest.copy()
            return latest.copy()
        
        return None
    
    async def get_price_history(
        self, 
        symbol: str, 
        limit: int = 200
    ) -> List[float]:
        """Получить только историю цен для вычисления индикаторов"""
        try:
            if symbol in self._price_cache:
                prices = self._price_cache[symbol]
                if limit > 0:
                    return prices[-limit:]
                return prices.copy()
            
            # Если кэша нет, извлекаем из тикеров
            if symbol not in self._ticker_data:
                return []
            
            prices = []
            ticker_data = list(self._ticker_data[symbol])
            if limit > 0:
                ticker_data = ticker_data[-limit:]
            
            for ticker in ticker_data:
                if 'close' in ticker:
                    prices.append(float(ticker['close']))
            
            # Обновляем кэш
            self._price_cache[symbol] = prices.copy()
            
            return prices
            
        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            return []
    
    async def append_orderbook_snapshot(
        self, 
        symbol: str, 
        orderbook_data: Dict[str, Any],
        max_history_size: int = 100
    ) -> None:
        """Добавить снимок стакана заявок"""
        try:
            # Валидация данных стакана
            if 'bids' not in orderbook_data or 'asks' not in orderbook_data:
                logger.warning(f"Invalid orderbook data for {symbol}: missing bids or asks")
                return
            
            # Обновляем размер буфера если нужно
            if self._orderbook_data[symbol].maxlen != max_history_size:
                new_deque = deque(self._orderbook_data[symbol], maxlen=max_history_size)
                self._orderbook_data[symbol] = new_deque
            
            # Добавляем timestamp если его нет
            if 'timestamp' not in orderbook_data:
                orderbook_data['timestamp'] = int(time.time() * 1000)
            
            self._orderbook_data[symbol].append(orderbook_data.copy())
            self._latest_orderbook_cache[symbol] = orderbook_data.copy()
            
            self._stats["orderbook_appends"] += 1
            
        except Exception as e:
            logger.error(f"Error appending orderbook data for {symbol}: {e}")
    
    async def get_orderbook_history(
        self, 
        symbol: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Получить историю стаканов"""
        try:
            if symbol not in self._orderbook_data:
                return []
            
            data = list(self._orderbook_data[symbol])
            if limit > 0:
                data = data[-limit:]
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting orderbook history for {symbol}: {e}")
            return []
    
    async def get_latest_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Получить последний стакан заявок из кэша"""
        if symbol in self._latest_orderbook_cache:
            self._stats["cache_hits"] += 1
            return self._latest_orderbook_cache[symbol].copy()
        
        if symbol in self._orderbook_data and self._orderbook_data[symbol]:
            self._stats["cache_misses"] += 1
            latest = self._orderbook_data[symbol][-1]
            self._latest_orderbook_cache[symbol] = latest.copy()
            return latest.copy()
        
        return None
    
    async def calculate_sma(
        self, 
        symbol: str, 
        period: int
    ) -> Optional[float]:
        """Вычислить SMA напрямую из кэшированных цен"""
        try:
            prices = await self.get_price_history(symbol, period)
            
            if len(prices) < period:
                return None
            
            # Используем numpy для быстрых вычислений
            return float(np.mean(prices[-period:]))
            
        except Exception as e:
            logger.error(f"Error calculating SMA for {symbol}: {e}")
            return None
    
    async def calculate_price_change(
        self, 
        symbol: str, 
        periods: int = 1
    ) -> Optional[Dict[str, float]]:
        """Вычислить изменение цены за N периодов"""
        try:
            prices = await self.get_price_history(symbol, periods + 1)
            
            if len(prices) < periods + 1:
                return None
            
            current_price = prices[-1]
            old_price = prices[-(periods + 1)]
            
            absolute_change = current_price - old_price
            percent_change = (absolute_change / old_price) * 100 if old_price != 0 else 0
            
            return {
                "absolute": absolute_change,
                "percent": percent_change,
                "current_price": current_price,
                "old_price": old_price
            }
            
        except Exception as e:
            logger.error(f"Error calculating price change for {symbol}: {e}")
            return None
    
    async def get_volatility(
        self, 
        symbol: str, 
        periods: int = 20
    ) -> Optional[float]:
        """Вычислить волатильность за N периодов"""
        try:
            prices = await self.get_price_history(symbol, periods)
            
            if len(prices) < periods:
                return None
            
            # Вычисляем волатильность как стандартное отклонение
            prices_array = np.array(prices[-periods:])
            returns = np.diff(prices_array) / prices_array[:-1]
            
            return float(np.std(returns) * 100)  # В процентах
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return None
    
    async def cleanup_old_data(
        self, 
        symbol: str, 
        keep_ticker_count: int = 1000,
        keep_orderbook_count: int = 100
    ) -> Dict[str, int]:
        """Очистить старые данные, оставить только последние N записей"""
        try:
            removed_tickers = 0
            removed_orderbooks = 0
            
            # Очистка тикеров
            if symbol in self._ticker_data:
                current_len = len(self._ticker_data[symbol])
                if current_len > keep_ticker_count:
                    # Пересоздаем deque с новым размером
                    new_data = deque(
                        list(self._ticker_data[symbol])[-keep_ticker_count:], 
                        maxlen=keep_ticker_count
                    )
                    removed_tickers = current_len - len(new_data)
                    self._ticker_data[symbol] = new_data
                    
                    # Обновляем кэш цен
                    if symbol in self._price_cache:
                        self._price_cache[symbol] = self._price_cache[symbol][-keep_ticker_count:]
            
            # Очистка стаканов
            if symbol in self._orderbook_data:
                current_len = len(self._orderbook_data[symbol])
                if current_len > keep_orderbook_count:
                    new_data = deque(
                        list(self._orderbook_data[symbol])[-keep_orderbook_count:], 
                        maxlen=keep_orderbook_count
                    )
                    removed_orderbooks = current_len - len(new_data)
                    self._orderbook_data[symbol] = new_data
            
            return {
                "removed_tickers": removed_tickers,
                "removed_orderbooks": removed_orderbooks
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old data for {symbol}: {e}")
            return {"removed_tickers": 0, "removed_orderbooks": 0}
    
    async def get_data_stats(self, symbol: str) -> Dict[str, Any]:
        """Получить статистику данных"""
        ticker_count = len(self._ticker_data.get(symbol, []))
        orderbook_count = len(self._orderbook_data.get(symbol, []))
        
        return {
            "symbol": symbol,
            "ticker_count": ticker_count,
            "orderbook_count": orderbook_count,
            "has_price_cache": symbol in self._price_cache,
            "price_cache_size": len(self._price_cache.get(symbol, [])),
            "has_latest_ticker": symbol in self._latest_ticker_cache,
            "has_latest_orderbook": symbol in self._latest_orderbook_cache,
            "global_stats": self._stats.copy()
        }
    
    async def bulk_append_tickers(
        self, 
        symbol: str, 
        ticker_batch: List[Dict[str, Any]],
        max_history_size: int = 1000
    ) -> None:
        """Добавить пакет тикеров за один раз"""
        try:
            if not ticker_batch:
                return
            
            # Обновляем размер буфера если нужно
            if self._ticker_data[symbol].maxlen != max_history_size:
                new_deque = deque(self._ticker_data[symbol], maxlen=max_history_size)
                self._ticker_data[symbol] = new_deque
            
            # Добавляем все тикеры
            for ticker_data in ticker_batch:
                if 'timestamp' in ticker_data and 'close' in ticker_data:
                    self._ticker_data[symbol].append(ticker_data.copy())
                    
                    # Обновляем кэш цен
                    price = float(ticker_data['close'])
                    self._price_cache[symbol].append(price)
            
            # Ограничиваем размер кэша цен
            if len(self._price_cache[symbol]) > max_history_size:
                self._price_cache[symbol] = self._price_cache[symbol][-max_history_size:]
            
            # Обновляем кэш последнего тикера
            if ticker_batch:
                self._latest_ticker_cache[symbol] = ticker_batch[-1].copy()
            
            self._stats["ticker_appends"] += len(ticker_batch)
            
        except Exception as e:
            logger.error(f"Error bulk appending tickers for {symbol}: {e}")
    
    async def get_ticker_subset(
        self, 
        symbol: str, 
        start_index: int, 
        count: int
    ) -> List[Dict[str, Any]]:
        """Получить подмножество тикеров по индексам"""
        try:
            if symbol not in self._ticker_data:
                return []
            
            data = list(self._ticker_data[symbol])
            end_index = start_index + count
            
            return data[start_index:end_index]
            
        except Exception as e:
            logger.error(f"Error getting ticker subset for {symbol}: {e}")
            return []
    
    async def get_tickers_by_time_range(
        self, 
        symbol: str,
        start_timestamp: int,
        end_timestamp: int
    ) -> List[Dict[str, Any]]:
        """Получить тикеры за временной интервал"""
        try:
            if symbol not in self._ticker_data:
                return []
            
            result = []
            for ticker in self._ticker_data[symbol]:
                if 'timestamp' in ticker:
                    timestamp = ticker['timestamp']
                    if start_timestamp <= timestamp <= end_timestamp:
                        result.append(ticker.copy())
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting tickers by time range for {symbol}: {e}")
            return []
    
    async def compress_old_data(
        self, 
        symbol: str, 
        older_than_timestamp: int
    ) -> int:
        """Сжать старые данные (агрегировать минутные данные в часовые)"""
        # В in-memory реализации просто удаляем старые данные
        try:
            if symbol not in self._ticker_data:
                return 0
            
            original_count = len(self._ticker_data[symbol])
            filtered_data = deque(maxlen=self._ticker_data[symbol].maxlen)
            
            for ticker in self._ticker_data[symbol]:
                if 'timestamp' in ticker and ticker['timestamp'] >= older_than_timestamp:
                    filtered_data.append(ticker)
            
            self._ticker_data[symbol] = filtered_data
            
            # Обновляем кэш цен
            if symbol in self._price_cache:
                new_prices = []
                for ticker in filtered_data:
                    if 'close' in ticker:
                        new_prices.append(float(ticker['close']))
                self._price_cache[symbol] = new_prices
            
            return original_count - len(filtered_data)
            
        except Exception as e:
            logger.error(f"Error compressing old data for {symbol}: {e}")
            return 0
    
    async def export_to_json(
        self, 
        symbol: str, 
        file_path: str,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> bool:
        """Экспортировать данные в JSON файл"""
        try:
            data_to_export = {
                "symbol": symbol,
                "export_timestamp": int(time.time() * 1000),
                "tickers": [],
                "orderbooks": []
            }
            
            # Экспорт тикеров
            if symbol in self._ticker_data:
                for ticker in self._ticker_data[symbol]:
                    if start_timestamp is None and end_timestamp is None:
                        data_to_export["tickers"].append(ticker)
                    elif 'timestamp' in ticker:
                        timestamp = ticker['timestamp']
                        if (start_timestamp is None or timestamp >= start_timestamp) and \
                           (end_timestamp is None or timestamp <= end_timestamp):
                            data_to_export["tickers"].append(ticker)
            
            # Экспорт стаканов
            if symbol in self._orderbook_data:
                for orderbook in self._orderbook_data[symbol]:
                    if start_timestamp is None and end_timestamp is None:
                        data_to_export["orderbooks"].append(orderbook)
                    elif 'timestamp' in orderbook:
                        timestamp = orderbook['timestamp']
                        if (start_timestamp is None or timestamp >= start_timestamp) and \
                           (end_timestamp is None or timestamp <= end_timestamp):
                            data_to_export["orderbooks"].append(orderbook)
            
            with open(file_path, 'w') as f:
                json.dump(data_to_export, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data for {symbol}: {e}")
            return False
    
    async def import_from_json(
        self, 
        symbol: str, 
        file_path: str,
        append: bool = True
    ) -> int:
        """Импортировать данные из JSON файла"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            imported_count = 0
            
            # Если не добавляем, очищаем существующие данные
            if not append:
                if symbol in self._ticker_data:
                    self._ticker_data[symbol].clear()
                if symbol in self._orderbook_data:
                    self._orderbook_data[symbol].clear()
                self._price_cache.pop(symbol, None)
                self._latest_ticker_cache.pop(symbol, None)
                self._latest_orderbook_cache.pop(symbol, None)
            
            # Импорт тикеров
            if "tickers" in data:
                for ticker in data["tickers"]:
                    await self.append_ticker_data(symbol, ticker)
                    imported_count += 1
            
            # Импорт стаканов
            if "orderbooks" in data:
                for orderbook in data["orderbooks"]:
                    await self.append_orderbook_snapshot(symbol, orderbook)
            
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing data for {symbol}: {e}")
            return 0
    
    async def get_all_symbols(self) -> List[str]:
        """Получить все символы, для которых есть данные"""
        symbols = set()
        symbols.update(self._ticker_data.keys())
        symbols.update(self._orderbook_data.keys())
        return list(symbols)
    
    async def delete_symbol_data(self, symbol: str) -> bool:
        """Удалить все данные для символа"""
        try:
            deleted = False
            
            if symbol in self._ticker_data:
                del self._ticker_data[symbol]
                deleted = True
            
            if symbol in self._orderbook_data:
                del self._orderbook_data[symbol]
                deleted = True
            
            # Очистка кэшей
            self._price_cache.pop(symbol, None)
            self._latest_ticker_cache.pop(symbol, None)
            self._latest_orderbook_cache.pop(symbol, None)
            
            if symbol in self._indicator_buffers:
                del self._indicator_buffers[symbol]
                deleted = True
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting data for {symbol}: {e}")
            return False
    
    # Методы для работы с индикаторными буферами
    
    async def update_indicator_buffer(
        self, 
        symbol: str, 
        indicator_name: str,
        value: float,
        max_buffer_size: int = 100
    ) -> None:
        """Обновить буфер индикатора"""
        try:
            if symbol not in self._indicator_buffers:
                self._indicator_buffers[symbol] = defaultdict(lambda: deque(maxlen=max_buffer_size))
            
            # Обновляем размер буфера если нужно
            if self._indicator_buffers[symbol][indicator_name].maxlen != max_buffer_size:
                new_deque = deque(
                    self._indicator_buffers[symbol][indicator_name], 
                    maxlen=max_buffer_size
                )
                self._indicator_buffers[symbol][indicator_name] = new_deque
            
            self._indicator_buffers[symbol][indicator_name].append(value)
            
        except Exception as e:
            logger.error(f"Error updating indicator buffer {indicator_name} for {symbol}: {e}")
    
    async def get_indicator_buffer(
        self, 
        symbol: str, 
        indicator_name: str,
        limit: int = 50
    ) -> List[float]:
        """Получить буфер индикатора"""
        try:
            if symbol not in self._indicator_buffers or indicator_name not in self._indicator_buffers[symbol]:
                return []
            
            buffer = list(self._indicator_buffers[symbol][indicator_name])
            if limit > 0:
                buffer = buffer[-limit:]
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error getting indicator buffer {indicator_name} for {symbol}: {e}")
            return []
    
    async def clear_indicator_buffers(self, symbol: str) -> int:
        """Очистить все буферы индикаторов для символа"""
        try:
            if symbol not in self._indicator_buffers:
                return 0
            
            count = len(self._indicator_buffers[symbol])
            del self._indicator_buffers[symbol]
            
            return count
            
        except Exception as e:
            logger.error(f"Error clearing indicator buffers for {symbol}: {e}")
            return 0