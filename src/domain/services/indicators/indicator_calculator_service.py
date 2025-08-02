# src/domain/services/indicators/indicator_calculator_service.py
import time
from typing import Dict, List
import numpy as np
import talib
from talib import MA_Type
import logging
from src.domain.entities.indicator_data import IndicatorData

logger = logging.getLogger(__name__)

class IndicatorCalculatorService:
    """
    Сервис-калькулятор для вычисления технических индикаторов.
    Не хранит состояние (stateless).
    """

    def calculate_fast_indicators(self, price_history: List[float], symbol: str = "UNKNOWN") -> IndicatorData:
        """Быстрые индикаторы (без TALIB) на основе истории цен."""
        if not price_history:
            return IndicatorData(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                values={}
            )

        current_price = price_history[-1]
        
        # SMA-7
        sma_7_window = price_history[-7:]
        sma_7 = sum(sma_7_window) / len(sma_7_window) if sma_7_window else 0

        # SMA-25
        sma_25 = 0
        if len(price_history) >= 25:
            sma_25_window = price_history[-25:]
            sma_25 = sum(sma_25_window) / len(sma_25_window)

        return IndicatorData(
            symbol=symbol,
            timestamp=int(time.time() * 1000),
            values={
                "price": current_price,
                "sma_7": round(sma_7, 8),
                "sma_25": round(sma_25, 8),
            }
        )

    def calculate_medium_indicators(self, price_history: List[float], symbol: str = "UNKNOWN") -> IndicatorData:
        """Средние индикаторы (RSI) каждые 10 тиков."""
        if len(price_history) < 30:
            return IndicatorData(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                values={}
            )

        closes = np.array(price_history[-30:])
        try:
            rsi_5 = talib.RSI(closes, timeperiod=5)
            rsi_15 = talib.RSI(closes, timeperiod=15)

            return IndicatorData(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                values={
                    "rsi_5": round(float(rsi_5[-1]), 8) if len(rsi_5) > 0 and not np.isnan(rsi_5[-1]) else 0,
                    "rsi_15": round(float(rsi_15[-1]), 8) if len(rsi_15) > 0 and not np.isnan(rsi_15[-1]) else 0,
                }
            )
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при расчете средних индикаторов: {e}")
            return IndicatorData(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                values={}
            )

    def calculate_heavy_indicators(self, price_history: List[float], symbol: str = "UNKNOWN") -> IndicatorData:
        """Тяжелые индикаторы (MACD, BBands) каждые 50 тиков."""
        if len(price_history) < 50:
            return IndicatorData(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                values={}
            )

        closes = np.array(price_history[-100:])
        try:
            macd, macdsignal, macdhist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
            upperband, middleband, lowerband = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2)

            return IndicatorData(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                values={
                    "macd": round(float(macd[-1]), 8) if len(macd) > 0 and not np.isnan(macd[-1]) else 0,
                    "macdsignal": round(float(macdsignal[-1]), 8) if len(macdsignal) > 0 and not np.isnan(macdsignal[-1]) else 0,
                    "macdhist": round(float(macdhist[-1]), 8) if len(macdhist) > 0 and not np.isnan(macdhist[-1]) else 0,
                    "bb_upper": round(float(upperband[-1]), 8) if len(upperband) > 0 and not np.isnan(upperband[-1]) else 0,
                    "bb_middle": round(float(middleband[-1]), 8) if len(middleband) > 0 and not np.isnan(middleband[-1]) else 0,
                    "bb_lower": round(float(lowerband[-1]), 8) if len(lowerband) > 0 and not np.isnan(lowerband[-1]) else 0,
                }
            )
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при расчете тяжелых индикаторов: {e}")
            return IndicatorData(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                values={}
            )
