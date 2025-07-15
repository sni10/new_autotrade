# src/domain/services/market_data/ticker_service.py
import time
from decimal import Decimal
from typing import Dict, List, Optional

from domain.entities.currency_pair import CurrencyPair
from domain.entities.ticker import Ticker
from domain.entities.indicator_data import IndicatorData
from domain.services.indicators.indicator_calculator_service import IndicatorCalculatorService
from domain.services.utils.decimal_rounding_service import DecimalRoundingService
from infrastructure.repositories.tickers_repository import InMemoryTickerRepository
from infrastructure.repositories.indicators_repository import InMemoryIndicatorsRepository


class TickerService:
    def __init__(self, 
                 tickers_repo: InMemoryTickerRepository, 
                 indicators_repo: InMemoryIndicatorsRepository):
        self.tickers_repo = tickers_repo
        self.indicators_repo = indicators_repo
        self.indicator_calculator = IndicatorCalculatorService()
        
        self.price_history_cache: List[float] = []
        self.tick_count: int = 0
        self.last_medium_update_tick: int = 0
        self.last_heavy_update_tick: int = 0
        
        if self.tickers_repo.tickers:
            self.price_history_cache = [t.last for t in self.tickers_repo.tickers]
            self.tick_count = len(self.price_history_cache)

    def _should_update_medium(self) -> bool:
        return self.tick_count - self.last_medium_update_tick >= 10

    def _should_update_heavy(self) -> bool:
        return self.tick_count - self.last_heavy_update_tick >= 50

    async def process_ticker(self, ticker: Ticker):
        """
        Обрабатывает сущность Ticker, вычисляет индикаторы и сохраняет все в репозитории.
        """
        self.price_history_cache.append(ticker.last)
        if len(self.price_history_cache) > 200:
            self.price_history_cache.pop(0)
        
        self.tick_count += 1

        all_indicators = {}
        
        fast_indicators = self.indicator_calculator.calculate_fast_indicators(self.price_history_cache)
        all_indicators.update(fast_indicators.values)
        
        if self._should_update_medium():
            medium_indicators = self.indicator_calculator.calculate_medium_indicators(self.price_history_cache)
            all_indicators.update(medium_indicators.values)
            self.last_medium_update_tick = self.tick_count

        if self._should_update_heavy():
            heavy_indicators = self.indicator_calculator.calculate_heavy_indicators(self.price_history_cache)
            all_indicators.update(heavy_indicators.values)
            self.last_heavy_update_tick = self.tick_count

        if all_indicators:
            indicator_data = IndicatorData(
                symbol=ticker.symbol,
                timestamp=ticker.timestamp,
                values=all_indicators
            )
            self.indicators_repo.save(indicator_data)

        ticker.update_signals(all_indicators)
        self.tickers_repo.save(ticker)

    async def get_signal(self) -> str:
        if len(self.tickers_repo.tickers) < 50:
            return "HOLD"
        last_ticker = self.tickers_repo.tickers[-1]
        if not last_ticker.signals:
            return "HOLD"

        macd = last_ticker.get_macd_signal()
        signal = last_ticker.get_macd_signal_line()
        hist = last_ticker.get_macd_histogram()
        sma_7 = last_ticker.get_sma_7()
        sma_25 = last_ticker.get_sma_25()

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
        price_step = Decimal(str(currency_pair.precision.get('price', '0.000001')))
        amount_step = Decimal(str(currency_pair.precision.get('amount', '0.0001')))
        price_precision = int(price_step.normalize().as_tuple().exponent * -1)
        amount_precision = int(amount_step.normalize().as_tuple().exponent * -1)
        min_notional = Decimal(str(currency_pair.limits.get('cost', {}).get('min', 10.0)))
        buy_price_dec = Decimal(str(buy_price))
        budget_dec = Decimal(str(budget))
        buy_fee_rate = Decimal(str(currency_pair.taker_fee))
        sell_fee_rate = Decimal(str(currency_pair.taker_fee))
        profit_dec = Decimal(str(profit_percent))

        if budget_dec < min_notional:
            return {"comment": f"❌ Бюджет ({budget_dec}) меньше минимально допустимого ({min_notional})"}

        coins_to_buy_raw = budget_dec / buy_price_dec
        coins_to_buy = DecimalRoundingService.ceil_to_precision(coins_to_buy_raw, amount_precision)
        coins_after_buy_fee = coins_to_buy * (1 - buy_fee_rate)
        sell_price_raw = buy_price_dec * (1 + profit_dec) / (1 - sell_fee_rate)
        sell_price = DecimalRoundingService.round_to_precision(sell_price_raw, price_precision)
        coins_to_sell = DecimalRoundingService.floor_to_precision(coins_after_buy_fee, amount_precision)
        total_cost = coins_to_buy * buy_price_dec

        if total_cost < min_notional:
             return {"comment": f"❌ Итоговая сумма ордера ({total_cost:.2f}) меньше минимально допустимой ({min_notional})"}

        final_revenue = coins_to_sell * sell_price
        net_profit = final_revenue - total_cost

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

    def get_last_price(self) -> Optional[float]:
        if self.tickers_repo.tickers:
            return self.tickers_repo.tickers[-1].last
        return None
