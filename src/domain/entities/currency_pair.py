import asyncio
import logging
from typing import Dict, Optional


class CurrencyPair:
    """Упрощённая сущность торговой пары."""

    def __init__(
        self,
        base_currency: str,
        quote_currency: str,
        symbol: Optional[str] = None,
        order_life_time: int = 1,
        deal_quota: float = 100.0,
        profit_markup: float = 0.005,
        deal_count: int = 1,
        refresh_interval: int = 3600,
    ) -> None:
        """Создаёт объект валютной пары."""
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.symbol = symbol or f"{base_currency}/{quote_currency}"
        self.order_life_time = order_life_time
        self.deal_quota = deal_quota
        self.profit_markup = profit_markup
        self.deal_count = deal_count
        self.precision: Dict[str, any] = {}
        self.limits: Dict[str, any] = {}
        self.taker_fee = 0.001
        self.maker_fee = 0.001
        self.active = True
        self.refresh_interval = refresh_interval
        self._refresh_task: Optional[asyncio.Task] = None

    async def refresh_market_info(self, exchange, force_reload: bool = False) -> bool:
        """Обновляет данные о рынке через ``exchange.load_markets()``."""
        try:
            markets = await exchange.load_markets(force_reload)
            market = markets.get(self.symbol)
            if not market:
                logging.error("Market %s not found on exchange", self.symbol)
                return False
            self.update_exchange_info(market)
            self.active = market.get("active", True)
            return True
        except Exception as e:
            logging.error("Failed to refresh market info for %s: %s", self.symbol, e)
            return False

    async def start_periodic_refresh(
        self, exchange, interval: Optional[int] = None
    ) -> None:
        """Запускает периодическое обновление market info."""
        if self._refresh_task and not self._refresh_task.done():
            return
        self.refresh_interval = interval or self.refresh_interval
        self._refresh_task = asyncio.create_task(self._refresh_loop(exchange))

    async def stop_periodic_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            self._refresh_task = None

    async def _refresh_loop(self, exchange) -> None:
        while True:
            await self.refresh_market_info(exchange, force_reload=True)
            await asyncio.sleep(self.refresh_interval)

    def update_exchange_info(self, market_data: Dict) -> None:
        """Сохраняет precision, limits и комиссии из market data."""
        if not market_data:
            return
        self.precision = market_data.get("precision", {})
        self.limits = market_data.get("limits", {})
        self.taker_fee = market_data.get("taker", self.taker_fee)
        self.maker_fee = market_data.get("maker", self.maker_fee)
        self.active = market_data.get("active", self.active)
        logging.info(
            "Updated currency pair %s with exchange data: Precision=%s, Limits=%s, Fees(T/M)=%s/%s",
            self.symbol,
            self.precision,
            self.limits,
            self.taker_fee,
            self.maker_fee,
        )

    def is_active(self) -> bool:
        return self.active

    def __repr__(self) -> str:  # pragma: no cover - simple representation
        return (
            f"<CurrencyPair(symbol={self.symbol}, order_life_time={self.order_life_time}, "
            f"deal_quota={self.deal_quota}, active={self.active})>"
        )
