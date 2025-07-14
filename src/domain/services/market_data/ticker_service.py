import math
from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP
from typing import Dict, List, Optional

from domain.entities.currency_pair import CurrencyPair
from domain.entities.ticker import Ticker
from domain.services.indicators.cached_indicator_service import CachedIndicatorService
from domain.services.utils.decimal_rounding_service import DecimalRoundingService
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository


class TickerService:
    def __init__(self, repository: InMemoryTickerRepository):
        self.repository = repository
        self.cached_indicators = CachedIndicatorService()
        self.price_history_cache = []
        self.volatility_window = 20

    async def process_ticker(self, data: Dict):
        ticker = Ticker(data)
        current_price = float(data.get('close', 0))
        self.price_history_cache.append(current_price)
        if len(self.price_history_cache) > 200:
            self.price_history_cache.pop(0)

        self.cached_indicators.update_fast_indicators(current_price)

        if self.cached_indicators.should_update_medium():
            self.cached_indicators.update_medium_indicators(self.price_history_cache)

        if self.cached_indicators.should_update_heavy():
            self.cached_indicators.update_heavy_indicators(self.price_history_cache)
        
        all_signals = self.cached_indicators.get_all_cached_signals()
        ticker.update_signals(all_signals)
        self.repository.save(ticker)

    async def get_signal(self) -> str:
        if len(self.repository.tickers) < 50:
            return "HOLD"
        last_ticker = self.repository.tickers[-1]
        if not last_ticker.signals:
            return "HOLD"

        macd = last_ticker.signals.get('macd', 0)
        signal = last_ticker.signals.get('signal', 0)
        hist = last_ticker.signals.get('histogram', 0)
        sma_7 = last_ticker.signals.get('sma_7', 0)
        sma_25 = last_ticker.signals.get('sma_25', 0)

        if macd > signal and hist > 0 and sma_7 > sma_25:
            return "BUY"
        else:
            return "HOLD"

    def calculate_strategy(
            self,
            buy_price: float,
            budget: float,
            currency_pair: CurrencyPair,
            profit_percent: float
    ):
        """
        Рассчитывает сделку, используя `DecimalRoundingService` и данные о
        лимитах и точности из объекта `currency_pair`.
        """
        # 1. Получаем правила с биржи (из объекта currency_pair)
        # Получаем шаг цены и количества (tick size / step size)
        price_step = Decimal(str(currency_pair.precision.get('price', '0.000001')))
        amount_step = Decimal(str(currency_pair.precision.get('amount', '0.0001')))

        # ВЫЧИСЛЯЕМ КОЛИЧЕСТВО ЗНАКОВ ПОСЛЕ ЗАПЯТОЙ ИЗ ШАГА
        # Это ключевое исправление: мы не используем 0.01 как количество знаков, а вычисляем его.
        price_precision = int(price_step.normalize().as_tuple().exponent * -1)
        amount_precision = int(amount_step.normalize().as_tuple().exponent * -1)

        min_notional = Decimal(str(currency_pair.limits.get('cost', {}).get('min', 10.0)))

        # 2. Конвертируем все в Decimal для точности
        buy_price_dec = Decimal(str(buy_price))
        budget_dec = Decimal(str(budget))
        # Используем комиссии тейкера, так как мы исполняем ордера по рынку
        buy_fee_rate = Decimal(str(currency_pair.taker_fee))
        sell_fee_rate = Decimal(str(currency_pair.taker_fee))
        profit_dec = Decimal(str(profit_percent))

        # 3. Проверка на минимальную сумму ордера
        if budget_dec < min_notional:
            return {"comment": f"❌ Бюджет ({budget_dec}) меньше минимально допустимого ({min_notional})"}

        # 4. Расчеты с использованием DecimalRoundingService
        # Сколько монет мы можем купить на наш бюджет
        coins_to_buy_raw = budget_dec / buy_price_dec
        coins_to_buy = DecimalRoundingService.floor_to_precision(coins_to_buy_raw, amount_precision)

        # Комиссия вычитается из ПОЛУЧЕННОГО количества монет
        coins_after_buy_fee = coins_to_buy * (1 - buy_fee_rate)

        # Цена продажи, которая покрывает обе комиссии и дает желаемую прибыль
        # (Цена покупки * (1 + %профита)) / (1 - %комиссии_продажи)
        sell_price_raw = buy_price_dec * (1 + profit_dec) / (1 - sell_fee_rate)
        sell_price = DecimalRoundingService.round_to_precision(sell_price_raw, price_precision)
        
        # Что останется для продажи после уплаты комиссии (которая берется в том же активе)
        coins_to_sell = DecimalRoundingService.floor_to_precision(
            coins_after_buy_fee,
            amount_precision
        )

        # 5. Финальные проверки
        total_cost = coins_to_buy * buy_price_dec
        if total_cost < min_notional:
             return {"comment": f"❌ Итоговая сумма ордера ({total_cost:.2f}) меньше минимально допустимой ({min_notional})"}

        final_revenue = coins_to_sell * sell_price
        net_profit = final_revenue - total_cost

        # 10) Возвращаем результат
        return (
            buy_price_dec,
            coins_to_buy,
            sell_price,
            coins_to_sell,
            {
                "comment": "✅ Сделка возможна.",
                "net_profit": f"{net_profit:.4f} USDT"
            }
        )