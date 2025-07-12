import math
from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP, InvalidOperation, getcontext
from typing import Dict, List, Optional, Tuple
import talib
import numpy as np
from talib import MA_Type

# В начале файла добавить:
from domain.services.indicators.cached_indicator_service import CachedIndicatorService
from domain.entities.ticker import Ticker
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository

# 🆕 НОВЫЕ ИМПОРТЫ ДЛЯ СТАКАНА
from domain.services.market_data.orderbook_analyzer import OrderBookMetrics


def round_to_step(value: Decimal, step: Decimal) -> Decimal:
    """
    Округляет число value до ближайшего шага step (по математическим правилам).
    """
    # Считаем, сколько "шагов" умещается, округляем до целого, умножаем обратно
    steps = (value / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return steps * step


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    """
    Округляет число value вниз до ближайшего шага step.
    """
    steps = (value / step).to_integral_value(rounding=ROUND_DOWN)
    return steps * step


class TickerService:
    def __init__(self, repository: InMemoryTickerRepository):
        self.repository = repository
        self.cached_indicators = CachedIndicatorService()  # 🆕 Добавляем кеш
        self.price_history_cache = []  # 🆕 Кеш истории цен
        self.volatility_window = 20

    async def process_ticker(self, data: Dict):
        """🚀 ОПТИМИЗИРОВАННАЯ обработка тикера"""
        ticker = Ticker(data)
        current_price = float(data.get('close', 0))

        # 1. Обновляем историю цен
        self.price_history_cache.append(current_price)
        if len(self.price_history_cache) > 200:  # Ограничиваем размер
            self.price_history_cache.pop(0)

        # 2. Быстрые индикаторы (каждый тик)
        fast_signals = self.cached_indicators.update_fast_indicators(current_price)

        # 3. Средние индикаторы (каждые 10 тиков)
        medium_signals = {}
        if self.cached_indicators.should_update_medium():
            medium_signals = self.cached_indicators.update_medium_indicators(self.price_history_cache)

        # 4. Тяжелые индикаторы (каждые 50 тиков)
        heavy_signals = {}
        if self.cached_indicators.should_update_heavy():
            heavy_signals = self.cached_indicators.update_heavy_indicators(self.price_history_cache)

        # 5. Получаем все кешированные сигналы
        all_signals = self.cached_indicators.get_all_cached_signals()
        ticker.update_signals(all_signals)

        # 6. Сохраняем тикер
        self.repository.save(ticker)

    async def get_signal(self) -> str:
        """🎯 УПРОЩЕННАЯ логика сигналов"""
        # Получаем последние тикеры БЕЗ get_last_n каждый раз
        if len(self.repository.tickers) < 50:
            return "HOLD"

        # Берем последние несколько тикеров
        recent_tickers = self.repository.tickers[-5:]

        if not recent_tickers:
            return "HOLD"

        last_ticker = recent_tickers[-1]
        if not last_ticker.signals:
            return "HOLD"

        # Упрощенная логика принятия решений
        hist = last_ticker.signals.get('histogram', 0)
        macd = last_ticker.signals.get('macd', 0)
        signal = last_ticker.signals.get('signal', 0)
        sma_7 = last_ticker.signals.get('sma_7', 0)
        sma_25 = last_ticker.signals.get('sma_25', 0)

        # Простая логика
        macd_bullish = macd > signal
        sma_bullish = sma_7 > sma_25 if sma_25 > 0 else False
        hist_positive = hist > 0

        if macd_bullish and sma_bullish and hist_positive:
            return "BUY"
        else:
            return "HOLD"

    # 🆕 НОВЫЙ МЕТОД ДЛЯ ПРОВЕРКИ MACD
    def get_macd_signal_data(self) -> Optional[Dict]:
        """Получение данных MACD для анализа стаканом"""
        if len(self.repository.tickers) < 50:
            return None

        last_ticker = self.repository.tickers[-1]
        if not last_ticker.signals:
            return None

        macd = last_ticker.signals.get('macd', 0)
        signal = last_ticker.signals.get('signal', 0)
        hist = last_ticker.signals.get('histogram', 0)

        return {
            'macd': macd,
            'signal': signal,
            'histogram': hist,
            'is_bullish': macd > signal and hist > 0
        }

    # 🆕 НОВЫЙ МЕТОД
    def analyze_market_conditions(self) -> str:
        """Анализирует текущие рыночные условия"""
        if len(self.price_history_cache) < self.volatility_window:
            return "📊 Недостаточно данных для анализа"

        # Берем последние 20 цен
        recent_prices = self.price_history_cache[-self.volatility_window:]

        # Вычисляем изменения цен в процентах
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = abs(recent_prices[i] - recent_prices[i - 1]) / recent_prices[i - 1]
            price_changes.append(change)

        # Средняя волатильность в процентах
        avg_volatility = sum(price_changes) / len(price_changes) * 100

        # Классифицируем волатильность
        if avg_volatility > 0.15:
            return f"🔥 Экстремальная волатильность ({avg_volatility:.3f}%) - Высокий риск!"
        elif avg_volatility > 0.08:
            return f"⚡ Высокая волатильность ({avg_volatility:.3f}%) - Активный рынок"
        elif avg_volatility > 0.03:
            return f"📊 Средняя волатильность ({avg_volatility:.3f}%) - Нормальный рынок"
        else:
            return f"😴 Низкая волатильность ({avg_volatility:.3f}%) - Спокойный рынок"

    # 🆕 НОВЫЙ МЕТОД
    def get_price_trend(self) -> str:
        """Определяет общий тренд цены"""
        if len(self.price_history_cache) < 10:
            return "📊 Недостаточно данных"

        recent_prices = self.price_history_cache[-10:]
        first_price = recent_prices[0]
        last_price = recent_prices[-1]

        change_percent = (last_price - first_price) / first_price * 100

        if change_percent > 0.5:
            return f"📈 Восходящий тренд (+{change_percent:.2f}%)"
        elif change_percent < -0.5:
            return f"📉 Нисходящий тренд ({change_percent:.2f}%)"
        else:
            return f"➡️ Боковой тренд ({change_percent:.2f}%)"

    # 🆕 НОВЫЙ МЕТОД
    def should_trade_by_volatility(self) -> bool:
        """Определяет, стоит ли торговать при текущей волатильности"""
        if len(self.price_history_cache) < self.volatility_window:
            return False

        recent_prices = self.price_history_cache[-self.volatility_window:]
        price_changes = [abs(recent_prices[i] - recent_prices[i - 1]) / recent_prices[i - 1]
                         for i in range(1, len(recent_prices))]
        avg_volatility = sum(price_changes) / len(price_changes) * 100

        # Торгуем только при умеренной волатильности
        return 0.03 <= avg_volatility <= 0.12

    def calculate_strategy_with_orderbook(
            self,
            buy_price: float,  # Исходная цена монеты (без комиссии)
            budget: float,  # Бюджет в USDT
            min_step: float,  # Минимальный лот монеты (1 для целых, 0.00001 для BTC и т.д.)
            price_step: float,  # Шаг цены (0.00001, 0.001, ...)
            buy_fee_percent: float,  # Комиссия покупка (%)
            sell_fee_percent: float,  # Комиссия продажа (%)
            profit_percent: float,  # Желаемая прибыль (%)
            orderbook_modifications: Optional[Dict] = None  # 🆕 Модификации от стакана
    ):
        """
        🆕 УЛУЧШЕННЫЙ КАЛЬКУЛЯТОР с учетом анализа стакана
        """

        # Применяем модификации от стакана
        entry_price = buy_price
        budget_multiplier = 1.0
        target_price_hint = None

        if orderbook_modifications:
            if 'entry_price' in orderbook_modifications:
                entry_price = orderbook_modifications['entry_price']
            if 'budget_multiplier' in orderbook_modifications:
                budget_multiplier = orderbook_modifications['budget_multiplier']
            if 'exit_price_hint' in orderbook_modifications:
                target_price_hint = orderbook_modifications['exit_price_hint']

        # Корректируем бюджет
        adjusted_budget = budget * budget_multiplier

        # Вызываем оригинальный калькулятор с модифицированными параметрами
        strategy_result = self.calculate_strategy(
            buy_price=entry_price,
            budget=adjusted_budget,
            min_step=min_step,
            price_step=price_step,
            buy_fee_percent=buy_fee_percent,
            sell_fee_percent=sell_fee_percent,
            profit_percent=profit_percent
        )

        # Если есть подсказка по целевой цене, корректируем результат
        if target_price_hint and isinstance(strategy_result, tuple):
            buy_price_calc, total_coins_needed, sell_price_calc, coins_to_sell, info_dict = strategy_result

            # Проверяем, выгоднее ли целевая цена
            if target_price_hint > float(sell_price_calc):
                # Пересчитываем с новой целевой ценой
                new_revenue = float(coins_to_sell) * target_price_hint
                new_profit = new_revenue - (float(total_coins_needed) * float(buy_price_calc))

                # Обновляем результат
                strategy_result = (
                    buy_price_calc,
                    total_coins_needed,
                    Decimal(str(target_price_hint)),
                    coins_to_sell,
                    {
                        **info_dict,
                        "🔹 Цена продажи (корректировка по стакану)": f"{target_price_hint} USDT",
                        "🔹 Финальный доход (с учетом стакана)": f"{new_revenue:.4f} USDT",
                        "🔹 Чистая прибыль (с учетом стакана)": f"{new_profit:.4f} USDT"
                    }
                )

        return strategy_result

    def calculate_strategy(
            self, buy_price,  # Исходная цена монеты (без комиссии)
            budget,  # Бюджет в USDT
            min_step,  # Минимальный лот монеты (1 для целых, 0.00001 для BTC и т.д.)
            price_step,  # Шаг цены (0.00001, 0.001, ...)
            buy_fee_percent,  # Комиссия покупка (%)
            sell_fee_percent,  # Комиссия продажа (%)
            profit_percent  # Желаемая прибыль (%)
    ):
        """
        Рассчитываем сделку с учетом:
        - Покупки чуть большего количества монет (учет комиссии продажи).
        - Комиссии покупки (считаем реальную стоимость 1 монеты).
        - Проверки, что чистая прибыль >= 0.5% от бюджета.
        - Шагов округления (мин. лот, шаг цены).

        Возвращаем tuple (buy_price, total_coins_needed, sell_price, X_sell, info_dict)
        Либо {"comment": "..."} при неудаче.
        """

        # 0) Приведение к Decimal
        buy_price = Decimal(str(buy_price))
        budget = Decimal(str(budget))
        min_step = Decimal(str(min_step))
        price_step = Decimal(str(price_step))
        buy_fee_percent = Decimal(str(buy_fee_percent))
        sell_fee_percent = Decimal(str(sell_fee_percent))
        profit_percent = Decimal(str(profit_percent))

        # 1) Проверки входных данных
        if (buy_price <= 0 or budget <= 0 or
                min_step <= 0 or price_step <= 0):
            return {"comment": "❌ Ошибка входных данных. Проверь параметры."}

        # 2) Цена покупки c учетом комиссии (для подсчета расхода USDT)
        buy_price_with_fee = buy_price * (1 + buy_fee_percent / 100)
        # Округлим цену вниз по price_step, чтобы не выйти за бюджет (если нужно).
        buy_price_with_fee = Decimal(str(round_to_step(buy_price_with_fee, price_step)))

        # 3) Желаемая цена продажи (без учета комиссий).
        #    Но комиссию продажи компенсируем количеством монет, а не ценой.
        sell_price_raw = buy_price * (1 + profit_percent / 100)
        sell_price = Decimal(str(round_to_step(sell_price_raw, price_step)))

        # 4) Считаем максимально возможное X (кол-во монет, которые реально продадим)
        #    У нас есть budget USDT, 1 монета стоит buy_price_with_fee,
        #    а после продажи комиссия берется монетой => купленные монеты * (1 - sell_fee)
        raw_max_x = (budget / buy_price_with_fee) * (1 - sell_fee_percent / 100)

        # Округлим X вниз до min_step
        X_adjusted = Decimal(str(floor_to_step(raw_max_x, min_step)))
        if X_adjusted <= 0:
            return {"comment": "❌ Невозможно купить даже минимальный шаг"}

        # 5) Чтобы после продажи осталось X_adjusted, надо купить чуть больше:
        # total_coins_needed = X_adjusted / (1 - sell_fee)
        total_coins_needed = X_adjusted / (1 - sell_fee_percent / 100)
        # Округлим кол-во монет по min_step (обычно если lotSize=1, то целые).
        total_coins_needed = Decimal(str(floor_to_step(total_coins_needed, min_step)))

        # 6) Сколько USDT уйдет на покупку этих монет
        total_usdt_needed = total_coins_needed * buy_price_with_fee
        # Округлим по price_step, чтобы не превысить budget
        total_usdt_needed = Decimal(str(round_to_step(total_usdt_needed, price_step)))

        if total_usdt_needed > budget:
            return {"comment": "❌ Не хватает бюджета, чтобы купить нужный объём"}

        # 7) Финальная выручка от продажи X_adjusted монет по sell_price
        final_revenue = X_adjusted * sell_price
        final_revenue = Decimal(str(round_to_step(final_revenue, price_step)))

        # 8) Чистая прибыль
        net_profit = final_revenue - total_usdt_needed

        # 9) Проверка на минимальную прибыль (≥ 0.5% от бюджета)
        min_required_profit = budget * Decimal("0.005")  # 0.5%
        if net_profit < min_required_profit:
            return {"comment": f"❌ Недостаточная прибыль. Нужно ≥ {min_required_profit:.6f} USDT"}

        # 10) Возвращаем результат в «красивом» виде, как у вас
        return (
            buy_price,  # 0
            total_coins_needed,  # 1
            sell_price,  # 2
            X_adjusted,  # 3
            {
                "comment": "✅ Сделка возможна.",
                "🔹 Цена покупки (исходная)": f"{buy_price} USDT",
                "🔹 Цена покупки (с комиссией)": f"{buy_price_with_fee} USDT",
                "🔹 Цена продажи (округленная)": f"{sell_price} USDT",
                "🔹 Минимальный шаг цены": f"{price_step} USDT",
                "🔹 Минимальный шаг актива": f"{min_step} монет",
                "🔹 Количество монет для продажи": f"{X_adjusted} монет",
                "🔹 Количество монет для покупки": f"{total_coins_needed} монет",
                "🔹 Общая сумма покупки потратим": f"{total_usdt_needed} USDT",
                "🔹 Финальный доход": f"{final_revenue} USDT",
                "🔹 Чистая прибыль": f"{net_profit} USDT"
            }
        )
