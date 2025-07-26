import logging
from typing import Dict, List, Optional, Any
import numpy as np
import talib
from talib import MA_Type

from src.domain.entities.indicator_data import IndicatorData, IndicatorType, IndicatorLevel
from src.domain.repositories.i_stream_data_repository import IStreamDataRepository
from src.domain.repositories.i_indicator_repository import IIndicatorRepository
from src.domain.repositories.i_cache_repository import ICacheRepository

logger = logging.getLogger(__name__)


class IndicatorCalculationService:
    """
    Сервис для вычисления технических индикаторов.
    Соблюдает принцип единственной ответственности (SRP).
    Отвечает ТОЛЬКО за вычисление индикаторов.
    """
    
    def __init__(
        self,
        stream_repository: IStreamDataRepository,
        indicator_repository: IIndicatorRepository,
        cache_repository: Optional[ICacheRepository] = None
    ):
        self.stream_repository = stream_repository
        self.indicator_repository = indicator_repository
        self.cache_repository = cache_repository
        
        # Настройки обновления
        self.medium_update_interval = 10  # тиков
        self.heavy_update_interval = 50   # тиков
        
        # Счетчики для управления частотой обновлений
        self._tick_counters: Dict[str, int] = {}
        self._last_medium_update: Dict[str, int] = {}
        self._last_heavy_update: Dict[str, int] = {}
        
        self._stats = {
            "fast_calculations": 0,
            "medium_calculations": 0,
            "heavy_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
    
    async def calculate_fast_indicators(self, symbol: str, current_price: float) -> Dict[str, float]:
        """
        Вычислить быстрые индикаторы (SMA 7, SMA 25)
        Вызывается при каждом тике
        """
        try:
            self._tick_counters[symbol] = self._tick_counters.get(symbol, 0) + 1
            indicators = {}
            
            # SMA 7
            sma_7 = await self._calculate_sma_incremental(symbol, 7, current_price)
            if sma_7 is not None:
                indicators['sma_7'] = sma_7
                await self._save_indicator(symbol, IndicatorType.SMA, sma_7, 7, IndicatorLevel.FAST)
            
            # SMA 25
            sma_25 = await self._calculate_sma_incremental(symbol, 25, current_price)
            if sma_25 is not None:
                indicators['sma_25'] = sma_25
                await self._save_indicator(symbol, IndicatorType.SMA, sma_25, 25, IndicatorLevel.FAST)
            
            self._stats["fast_calculations"] += 1
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating fast indicators for {symbol}: {e}")
            self._stats["errors"] += 1
            return {}
    
    async def should_update_medium_indicators(self, symbol: str) -> bool:
        """Проверить нужно ли обновлять средние индикаторы"""
        tick_count = self._tick_counters.get(symbol, 0)
        last_update = self._last_medium_update.get(symbol, 0)
        return tick_count - last_update >= self.medium_update_interval
    
    async def calculate_medium_indicators(self, symbol: str) -> Dict[str, float]:
        """
        Вычислить средние индикаторы (RSI 5, RSI 15)
        Вызывается каждые 10 тиков
        """
        try:
            if not await self.should_update_medium_indicators(symbol):
                return {}
            
            # Получаем историю цен
            prices = await self.stream_repository.get_price_history(symbol, 30)
            if len(prices) < 15:
                return {}
            
            prices_array = np.array(prices[-30:])
            indicators = {}
            
            # RSI 5
            rsi_5 = talib.RSI(prices_array, timeperiod=5)
            if len(rsi_5) > 0 and not np.isnan(rsi_5[-1]):
                indicators['rsi_5'] = round(float(rsi_5[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.RSI, indicators['rsi_5'], 5, IndicatorLevel.MEDIUM)
            
            # RSI 15
            rsi_15 = talib.RSI(prices_array, timeperiod=15)
            if len(rsi_15) > 0 and not np.isnan(rsi_15[-1]):
                indicators['rsi_15'] = round(float(rsi_15[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.RSI, indicators['rsi_15'], 15, IndicatorLevel.MEDIUM)
            
            # Обновляем счетчик
            self._last_medium_update[symbol] = self._tick_counters.get(symbol, 0)
            self._stats["medium_calculations"] += 1
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating medium indicators for {symbol}: {e}")
            self._stats["errors"] += 1
            return {}
    
    async def should_update_heavy_indicators(self, symbol: str) -> bool:
        """Проверить нужно ли обновлять тяжелые индикаторы"""
        tick_count = self._tick_counters.get(symbol, 0)
        last_update = self._last_heavy_update.get(symbol, 0)
        return tick_count - last_update >= self.heavy_update_interval
    
    async def calculate_heavy_indicators(self, symbol: str) -> Dict[str, float]:
        """
        Вычислить тяжелые индикаторы (MACD, SMA 75, Bollinger Bands)
        Вызывается каждые 50 тиков
        """
        try:
            if not await self.should_update_heavy_indicators(symbol):
                return {}
            
            # Получаем историю цен
            prices = await self.stream_repository.get_price_history(symbol, 100)
            if len(prices) < 50:
                return {}
            
            prices_array = np.array(prices[-100:])
            indicators = {}
            
            # MACD
            macd, macdsignal, macdhist = talib.MACD(prices_array, fastperiod=12, slowperiod=26, signalperiod=9)
            if len(macd) > 0 and not np.isnan(macd[-1]):
                indicators['macd'] = round(float(macd[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.MACD, indicators['macd'], None, IndicatorLevel.HEAVY)
                
            if len(macdsignal) > 0 and not np.isnan(macdsignal[-1]):
                indicators['macd_signal'] = round(float(macdsignal[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.MACD_SIGNAL, indicators['macd_signal'], None, IndicatorLevel.HEAVY)
                
            if len(macdhist) > 0 and not np.isnan(macdhist[-1]):
                indicators['macd_histogram'] = round(float(macdhist[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.MACD_HISTOGRAM, indicators['macd_histogram'], None, IndicatorLevel.HEAVY)
            
            # SMA 75
            sma_75 = talib.MA(prices_array, timeperiod=75, matype=MA_Type.SMA)
            if len(sma_75) > 0 and not np.isnan(sma_75[-1]):
                indicators['sma_75'] = round(float(sma_75[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.SMA, indicators['sma_75'], 75, IndicatorLevel.HEAVY)
            
            # Bollinger Bands
            upperband, middleband, lowerband = talib.BBANDS(prices_array, timeperiod=20, nbdevup=2, nbdevdn=2)
            
            if len(upperband) > 0 and not np.isnan(upperband[-1]):
                indicators['bb_upper'] = round(float(upperband[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.BOLLINGER_UPPER, indicators['bb_upper'], 20, IndicatorLevel.HEAVY)
                
            if len(middleband) > 0 and not np.isnan(middleband[-1]):
                indicators['bb_middle'] = round(float(middleband[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.BOLLINGER_MIDDLE, indicators['bb_middle'], 20, IndicatorLevel.HEAVY)
                
            if len(lowerband) > 0 and not np.isnan(lowerband[-1]):
                indicators['bb_lower'] = round(float(lowerband[-1]), 8)
                await self._save_indicator(symbol, IndicatorType.BOLLINGER_LOWER, indicators['bb_lower'], 20, IndicatorLevel.HEAVY)
            
            # Обновляем счетчик
            self._last_heavy_update[symbol] = self._tick_counters.get(symbol, 0)
            self._stats["heavy_calculations"] += 1
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating heavy indicators for {symbol}: {e}")
            self._stats["errors"] += 1
            return {}
    
    async def get_all_cached_indicators(self, symbol: str) -> Dict[str, float]:
        """Получить все кэшированные индикаторы для символа"""
        try:
            result = {}
            
            # Если есть кэш-репозиторий, пробуем получить из кэша
            if self.cache_repository:
                # Получаем индикаторы из кэша
                indicator_names = ['sma_7', 'sma_25', 'rsi_5', 'rsi_15', 'macd', 'macd_signal', 'macd_histogram', 'sma_75', 'bb_upper', 'bb_middle', 'bb_lower']
                
                for indicator_name in indicator_names:
                    cached_value = await self.cache_repository.get_cached_indicator(symbol, indicator_name)
                    if cached_value is not None:
                        result[indicator_name] = cached_value
                        self._stats["cache_hits"] += 1
                    else:
                        self._stats["cache_misses"] += 1
            
            # Если кэша нет или он пуст, получаем из репозитория индикаторов
            if not result:
                # Получаем последние индикаторы для каждого типа
                indicator_types = [
                    (IndicatorType.SMA, 7), (IndicatorType.SMA, 25), (IndicatorType.SMA, 75),
                    (IndicatorType.RSI, 5), (IndicatorType.RSI, 15),
                    (IndicatorType.MACD, None), (IndicatorType.MACD_SIGNAL, None), (IndicatorType.MACD_HISTOGRAM, None),
                    (IndicatorType.BOLLINGER_UPPER, 20), (IndicatorType.BOLLINGER_MIDDLE, 20), (IndicatorType.BOLLINGER_LOWER, 20)
                ]
                
                for indicator_type, period in indicator_types:
                    latest = await self.indicator_repository.get_latest(symbol, indicator_type, period)
                    if latest:
                        result[latest.indicator_name] = latest.value
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting cached indicators for {symbol}: {e}")
            return {}
    
    async def _calculate_sma_incremental(self, symbol: str, period: int, current_price: float) -> Optional[float]:
        """Инкрементальное вычисление SMA"""
        try:
            # Используем буфер индикаторов в StreamDataRepository
            buffer_name = f"sma_{period}_buffer"
            
            # Обновляем буфер
            await self.stream_repository.update_indicator_buffer(symbol, buffer_name, current_price, period)
            
            # Получаем буфер для вычисления
            buffer = await self.stream_repository.get_indicator_buffer(symbol, buffer_name, period)
            
            if len(buffer) >= period:
                return sum(buffer[-period:]) / period
            elif len(buffer) > 0:
                return sum(buffer) / len(buffer)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating incremental SMA {period} for {symbol}: {e}")
            return None
    
    async def _save_indicator(
        self, 
        symbol: str, 
        indicator_type: IndicatorType, 
        value: float, 
        period: Optional[int], 
        level: IndicatorLevel
    ) -> None:
        """Сохранить вычисленный индикатор"""
        try:
            import time
            
            indicator = IndicatorData(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                indicator_type=indicator_type,
                value=value,
                period=period,
                level=level
            )
            
            # Сохраняем в репозиторий
            await self.indicator_repository.save(indicator)
            
            # Кэшируем если есть кэш-репозиторий
            if self.cache_repository:
                await self.cache_repository.cache_indicator(
                    symbol, indicator.indicator_name, value, 300
                )
                
        except Exception as e:
            logger.error(f"Error saving indicator {indicator_type.value} for {symbol}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику сервиса"""
        return {
            **self._stats,
            "symbols_processed": len(self._tick_counters),
            "tick_counters": self._tick_counters.copy()
        }
    
    def reset_stats(self) -> None:
        """Сбросить статистику"""
        self._stats = {
            "fast_calculations": 0,
            "medium_calculations": 0,
            "heavy_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
        self._tick_counters.clear()
        self._last_medium_update.clear()
        self._last_heavy_update.clear()