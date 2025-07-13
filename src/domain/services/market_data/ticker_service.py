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
            buy_fee_percent: float,
            sell_fee_percent: float,
            profit_percent: float
    ):
        """
        Рассчитывает сделку, используя `DecimalRoundingService` и данные о 
        лимитах и точности из объекта `currency_pair`.
        """
        # 1. Получаем правила с биржи (из объекта currency_pair)
        amount_precision = currency_pair.precision.get('amount', 4) # Знаков после запятой для кол-ва
        price_precision = currency_pair.precision.get('price', 2)   # Знаков после запятой для цены
        min_notional = Decimal(str(currency_pair.limits.get('cost', {}).get('min', 10.0)))

        # 2. Конвертируем все в Decimal для точности
        buy_price_dec = Decimal(str(buy_price))
        budget_dec = Decimal(str(budget))
        buy_fee_dec = Decimal(str(buy_fee_percent)) / 100
        sell_fee_dec = Decimal(str(sell_fee_percent)) / 100
        profit_dec = Decimal(str(profit_percent)) / 100

        # 3. Проверка на минимальную сумму ордера
        if budget_dec < min_notional:
            return {"comment": f"❌ Бюджет ({budget_dec}) меньше минимально допустимого ({min_notional})"}

        # 4. Расчеты с использованием DecimalRoundingService
        buy_price_with_fee = buy_price_dec * (1 + buy_fee_dec)
        
        sell_price_raw = buy_price_dec * (1 + profit_dec)
        sell_price = DecimalRoundingService.round_to_precision(sell_price_raw, price_precision)

        # Сколько монет мы можем купить на наш бюджет
        # Округляем ВНИЗ, чтобы не выйти за рамки бюджета
        purchasable_amount = DecimalRoundingService.floor_to_precision(
            budget_dec / buy_price_with_fee, 
            amount_precision
        )

        # Учитываем комиссию на продажу. Нам нужно купить чуть больше, чтобы 
        # после уплаты комиссии осталось достаточно для продажи.
        # Но для простоты и надежности, мы просто купим то, что можем, 
        # а продадим то, что останется после комиссии.
        coins_to_buy = purchasable_amount
        
        # Проверяем, что количество монет не равно нулю
        if coins_to_buy <= 0:
            return {"comment": "❌ Невозможно купить даже минимальный шаг актива с учетом бюджета и цены"}

        # Что останется для продажи после уплаты комиссии (которая берется в том же активе)
        coins_to_sell = DecimalRoundingService.floor_to_precision(
            coins_to_buy * (1 - sell_fee_dec),
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