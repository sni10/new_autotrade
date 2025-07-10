import time
from typing import Dict, List
import numpy as np
import talib
from talib import MA_Type
import logging

logger = logging.getLogger(__name__)

class CachedIndicatorService:
    def __init__(self):
        # Кеши разных уровней
        self.fast_cache = {}      # Каждый тик
        self.medium_cache = {}    # Каждые 10 тиков
        self.heavy_cache = {}     # Каждые 50 тиков

        # Счетчики обновлений
        self.last_medium_update = 0
        self.last_heavy_update = 0
        self.tick_count = 0

        # Буферы для инкрементальных вычислений
        self.sma_7_buffer = []
        self.sma_25_buffer = []
        self.price_sum_7 = 0
        self.price_sum_25 = 0

    def update_fast_indicators(self, price: float) -> Dict:
        """Быстрые индикаторы каждый тик (без TALIB)"""

        if not isinstance(price, (int, float)) or np.isnan(price):
            return self.fast_cache  # Вернуть предыдущие значения

        self.tick_count += 1

        # SMA-7 инкрементально
        self.sma_7_buffer.append(price)
        self.price_sum_7 += price

        if len(self.sma_7_buffer) > 7:
            removed = self.sma_7_buffer.pop(0)
            self.price_sum_7 -= removed

        sma_7 = self.price_sum_7 / len(self.sma_7_buffer) if self.sma_7_buffer else 0

        # SMA-25 инкрементально
        self.sma_25_buffer.append(price)
        self.price_sum_25 += price

        if len(self.sma_25_buffer) > 25:
            removed = self.sma_25_buffer.pop(0)
            self.price_sum_25 -= removed

        sma_25 = self.price_sum_25 / len(self.sma_25_buffer) if len(self.sma_25_buffer) >= 25 else 0

        self.fast_cache = {
            "price": price,
            "sma_7": round(sma_7, 8),
            "sma_25": round(sma_25, 8) if sma_25 > 0 else 0,
            "timestamp": int(time.time() * 1000)
        }

        return self.fast_cache

    def should_update_medium(self) -> bool:
        return self.tick_count - self.last_medium_update >= 10

    def should_update_heavy(self) -> bool:
        return self.tick_count - self.last_heavy_update >= 50

    def update_medium_indicators(self, price_history: List[float]) -> Dict:
        """Средние индикаторы каждые 10 тиков"""
        if len(price_history) < 30:
            return {}

        closes = np.array(price_history[-30:])  # Только последние 30

        try:
            rsi_5 = talib.RSI(closes, timeperiod=5)
            rsi_15 = talib.RSI(closes, timeperiod=15)

            self.medium_cache = {
                "rsi_5": round(float(rsi_5[-1]), 8) if len(rsi_5) > 0 and not np.isnan(rsi_5[-1]) else 0,
                "rsi_15": round(float(rsi_15[-1]), 8) if len(rsi_15) > 0 and not np.isnan(rsi_15[-1]) else 0,
            }

            self.last_medium_update = self.tick_count
            logger.info(
                f"🔄 Обновлен средний кеш на тике {self.tick_count}"
            )

        except Exception as e:
            logger.warning(f"⚠️ Ошибка в medium_indicators: {e}")

        return self.medium_cache

    def update_heavy_indicators(self, price_history: List[float]) -> Dict:
        """Тяжелые индикаторы каждые 50 тиков"""
        if len(price_history) < 50:
            return {}

        closes = np.array(price_history[-100:])  # Только последние 100

        try:
            # MACD
            macd, macdsignal, macdhist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)

            # SMA-99
            sma_75 = talib.MA(closes, timeperiod=75, matype=MA_Type.SMA)

            # Bollinger Bands
            upperband, middleband, lowerband = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2)

            self.heavy_cache = {
                "macd": round(float(macd[-1]), 8) if len(macd) > 0 and not np.isnan(macd[-1]) else 0,
                "signal": round(float(macdsignal[-1]), 8) if len(macdsignal) > 0 and not np.isnan(macdsignal[-1]) else 0,
                "histogram": round(float(macdhist[-1]), 8) if len(macdhist) > 0 and not np.isnan(macdhist[-1]) else 0,
                "sma_99": round(float(sma_75[-1]), 8) if len(sma_75) > 0 and not np.isnan(sma_75[-1]) else 0,
                "bb_upper": round(float(upperband[-1]), 8) if len(upperband) > 0 and not np.isnan(upperband[-1]) else 0,
                "bb_middle": round(float(middleband[-1]), 8) if len(middleband) > 0 and not np.isnan(middleband[-1]) else 0,
                "bb_lower": round(float(lowerband[-1]), 8) if len(lowerband) > 0 and not np.isnan(lowerband[-1]) else 0,
            }

            self.last_heavy_update = self.tick_count
            logger.info(
                f"🔥 Обновлен тяжелый кеш на тике {self.tick_count}"
            )

        except Exception as e:
            logger.warning(f"⚠️ Ошибка в heavy_indicators: {e}")

        return self.heavy_cache

    def get_all_cached_signals(self) -> Dict:
        """Возвращает все кешированные сигналы"""
        return {
            **self.fast_cache,
            **self.medium_cache,
            **self.heavy_cache
        }