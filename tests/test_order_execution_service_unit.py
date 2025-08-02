# tests/test_order_execution_service_unit.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from domain.entities.currency_pair import CurrencyPair
from domain.entities.ticker import Ticker
from domain.entities.order import OrderExecutionResult, ExchangeInfo
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory
from domain.services.deals.deal_service import DealService
from domain.services.orders.order_execution_service import OrderExecutionService
from infrastructure.repositories.deals_repository import InMemoryDealsRepository

class PatchedDealFactory(DealFactory):
    def create_new_deal(self, currency_pair: CurrencyPair, status: str = "OPEN"):
        import time
        deal_id = int(time.time() * 1000000)
        return super().create_new_deal(currency_pair, status)

@pytest.mark.asyncio
async def test_execute_trading_strategy_success():
    exchange = MagicMock()
    exchange.check_sufficient_balance = AsyncMock(return_value=(True, 'USDT', 1000))
    exchange.fetch_ticker = AsyncMock(return_value=Ticker(data={'symbol': 'BTC/USDT', 'last': 10.0}))
    exchange.get_symbol_info = AsyncMock(return_value=ExchangeInfo(
        symbol='BTC/USDT', min_qty=0.001, max_qty=100, step_size=0.001,
        min_price=0.01, max_price=100000.0, tick_size=0.01, min_notional=1,
        fees={'maker':0.001, 'taker':0.001}, precision={'amount': 3, 'price': 2}
    ))

    order_factory = OrderFactory()
    deal_factory = PatchedDealFactory(order_factory)
    deals_repo = InMemoryDealsRepository()

    async def make_buy_order(symbol, amount, price, deal_id):
        order = order_factory.create_buy_order(symbol, amount, price, deal_id=deal_id)
        order.mark_as_placed('ex-buy')
        return OrderExecutionResult(success=True, order=order)

    async def make_sell_order(symbol, amount, price, deal_id):
        order = order_factory.create_sell_order(symbol, amount, price, deal_id=deal_id)
        return OrderExecutionResult(success=True, order=order)

    order_service = MagicMock()
    order_service.create_and_place_buy_order = AsyncMock(side_effect=make_buy_order)
    order_service.create_local_sell_order = AsyncMock(side_effect=make_sell_order)

    deal_service = DealService(deals_repo, order_service, deal_factory, exchange)
    svc = OrderExecutionService(order_service, deal_service, exchange)

    cp = CurrencyPair('BTC/USDT', 'BTC', 'USDT')
    strategy_result = (10.0, 1.0, 11.0, 1.0, {})

    report = await svc.execute_trading_strategy(cp, strategy_result)

    assert report.success, report.error_message
    assert report.buy_order.exchange_id == 'ex-buy'
    assert report.sell_order.exchange_id is None
    assert report.deal_id is not None
