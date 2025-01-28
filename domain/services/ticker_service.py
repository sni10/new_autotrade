import math
from typing import Dict, List

import talib
import numpy as np
from talib import MA_Type

from domain.entities.ticker import Ticker
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository


class TickerService:
    def __init__(self, repository: InMemoryTickerRepository):
        self.repository = repository

    def process_ticker(self, data: Dict):
        """Обработка нового тикера"""
        ticker = Ticker(data)

        # Добавляем сигналы (на основе истории)
        last_n_tickers = self.repository.get_last_n(100)  # Берем последние 50 значений
        signals = self.compute_signals(last_n_tickers)
        ticker.update_signals(signals)

        # Сохраняем тикер
        self.repository.save(ticker)

    def calculate_trading_strategy_improved(self, buy_price, budget, min_step,
                                            buy_fee_percent, sell_fee_percent,
                                            profit_percent):
        """Расчёт параметров сделки на покупку и продажу."""

        buy_price_with_fee_factor = buy_price * (1 + buy_fee_percent / 100)
        coin_after_sell_fee_factor = (1 - sell_fee_percent / 100)
        sell_price = buy_price * (1 + profit_percent / 100)

        if coin_after_sell_fee_factor <= 0:
            return {"comment": "❌ Комиссия продажи >= 100%. Сделка невозможна."}

        def floor_to_step(value, step):
            return math.floor(value / step) * step

        raw_max_x = budget * (coin_after_sell_fee_factor / buy_price_with_fee_factor)
        X_adjusted = floor_to_step(raw_max_x, min_step)

        if X_adjusted <= 0:
            return {"comment": "❌ Невозможно купить даже минимальный шаг."}

        total_coins_needed = X_adjusted / coin_after_sell_fee_factor
        total_usdt_needed = total_coins_needed * buy_price_with_fee_factor
        final_revenue = X_adjusted * sell_price
        net_profit = final_revenue - total_usdt_needed

        return {
            "comment": "✅ Сделка возможна.",
            "🔹 Цена покупки (без комиссии)": f"{buy_price} USDT/монету",
            "🔹 Цена покупки (с комиссией)": f"{buy_price_with_fee_factor} USDT/монету",
            "🔹 Цена продажи": f"{sell_price} USDT/монету",
            "🔹 Количество монет для продажи": f"{X_adjusted} монет",
            "🔹 Количество монет для покупки": f"{total_coins_needed} монет",
            "🔹 Общая сумма сделки": f"{total_usdt_needed} USDT",
            "🔹 Финальный доход": f"{final_revenue} USDT",
            "🔹 Чистая прибыль": f"{net_profit} USDT"
        }

    def get_signal(self) -> str:
        """
        Решение о покупке на основе сигналов.
        Условия:
        - Гистограмма HIST зеленая (восходящий тренд).
        - MACD выше SIGNAL.
        - Гистограмма HIST была зеленой 3 раза подряд.
        """

        RED = "\033[91m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RESET = "\033[0m"

        indicators = self.repository.tickers
        HIST_ANALYSIS_POINTS = 3
        ANALYSIS_POINTS = 5


        if len(indicators) < HIST_ANALYSIS_POINTS:  # Проверяем, чтобы было достаточно данных
            return "HOLD"

        # --- Извлекаем последние `HIST_ANALYSIS_POINTS` значений ---
        hist_values = [t.signals.get("histogram", 0) for t in indicators[-HIST_ANALYSIS_POINTS:]]
        macd_values = [t.signals.get("macd", 0) for t in indicators[-HIST_ANALYSIS_POINTS:]]
        signal_values = [t.signals.get("signal", 0) for t in indicators[-HIST_ANALYSIS_POINTS:]]

        sma_7_values = [t.signals.get("sma_7", 0) for t in indicators[-ANALYSIS_POINTS:]]
        sma_25_values = [t.signals.get("sma_25", 0) for t in indicators[-ANALYSIS_POINTS:]]
        sma_99_values = [t.signals.get("sma_99", 0) for t in indicators[-ANALYSIS_POINTS:]]

        hist_trend = [hist_values[i] - hist_values[i - 1] for i in range(1, HIST_ANALYSIS_POINTS)]

        sma_7_trend = [sma_7_values[i] - sma_7_values[i - 1] for i in range(1, ANALYSIS_POINTS)]
        sma_25_trend = [sma_25_values[i] - sma_25_values[i - 1] for i in range(1, ANALYSIS_POINTS)]
        sma_99_trend = [sma_99_values[i] - sma_99_values[i - 1] for i in range(1, ANALYSIS_POINTS)]

        hist_color = GREEN if all(diff > 0 for diff in hist_trend) else RED
        sma_7_color = GREEN if all(diff > 0 for diff in sma_7_trend) else RED
        sma_25_color = GREEN if all(diff > 0 for diff in sma_25_trend) else RED
        sma_99_color = GREEN if all(diff > 0 for diff in sma_99_trend) else RED

        hist_trend_green = hist_color == GREEN
        sma_7_trend_green = sma_7_color == GREEN
        sma_25_trend_green = sma_25_color == GREEN
        sma_99_trend_green = sma_99_color == GREEN

        macd_above_signal = macd_values[-1] > signal_values[-1]

        sma_trend_green = sma_7_trend_green and sma_25_trend_green and sma_99_trend_green  # Все три SMA должны расти

        # --- Финальное решение ---
        if hist_trend_green and macd_above_signal and sma_trend_green:
            return "BUY"
        else:
            return "HOLD"

    def compute_signals(self, history: List[Ticker]) -> Dict:
        if len(history) < 20:  # Недостаточно данных
            return {}

        # Конвертируем историю в массив NumPy
        closes = np.array([t.close for t in history])

        macd, macdsignal, macdhist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)

        rsi_5 = talib.RSI(closes, timeperiod=5)
        rsi_15 = talib.RSI(closes, timeperiod=15)
        rsi_30 = talib.RSI(closes, timeperiod=30)

        sma_7 = talib.MA(closes, timeperiod=7, matype=MA_Type.SMA)
        sma_25 = talib.MA(closes, timeperiod=25, matype=MA_Type.SMA)
        sma_99 = talib.MA(closes, timeperiod=75, matype=MA_Type.SMA)


        # Bollinger Bands (BBANDS) 20, 2
        upperband, middleband, lowerband = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2, matype=MA_Type.SMA)


        return {
            # MACD
            "macd": round(float(macd[-1]), 8),
            "signal": round(float(macdsignal[-1]), 8),
            "histogram": round(float(macdhist[-1]), 8),

            # RSI
            "rsi_5": round(float(rsi_5[-1]), 8),
            "rsi_15": round(float(rsi_15[-1]), 8),
            "rsi_30": round(float(rsi_30[-1]), 8),

            # SMA
            "sma_7": round(float(sma_7[-1]), 8),
            "sma_25": round(float(sma_25[-1]), 8),
            "sma_99": round(float(sma_99[-1]), 8),

            # BBANDS
            "bb_upper": round(float(upperband[-1]), 8),
            "bb_middle": round(float(middleband[-1]), 8),
            "bb_lower": round(float(lowerband[-1]), 8),

        }
