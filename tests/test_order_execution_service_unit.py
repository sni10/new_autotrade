import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from domain.entities.currency_pair import CurrencyPair
from domain.entities.order import Order, OrderExecutionResult, ExchangeInfo
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory
from domain.entities.deal import Deal
from domain.services.deal_service import DealService
from domain.services.order_execution_service import OrderExecutionService

from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from infrastructure.repositories.deals_repository import InMemoryDealsRepository


class PatchedDealFactory(DealFactory):
    def create_new_deal(self, currency_pair: CurrencyPair, status: str = Deal.STATUS_OPEN) -> Deal:
        deal_id = int(time.time() * 1000000)
        buy_order = self.order_factory.create_buy_order(symbol=currency_pair.symbol, amount=0.0, price=0.0)
        sell_order = self.order_factory.create_sell_order(symbol=currency_pair.symbol, amount=0.0, price=0.0)
        return Deal(deal_id=deal_id, currency_pair_id=currency_pair.symbol, status=status,
                    buy_order=buy_order, sell_order=sell_order)

@pytest.mark.asyncio
async def test_execute_trading_strategy_success():
    # Prepare mocks and services
    exchange = MagicMock()
    exchange.check_sufficient_balance = AsyncMock(return_value=(True, 'USDT', 1000))
    exchange.fetch_ticker = AsyncMock(return_value={'last': 10.0})
    exchange.get_symbol_info = AsyncMock(return_value=ExchangeInfo(
        symbol='BTCUSDT', min_qty=0.001, max_qty=100, step_size=0.001,
        min_price=0.01, max_price=100000.0, tick_size=0.01, min_notional=1,
        fees={'maker':0.001, 'taker':0.001}
    ))

    order_factory = OrderFactory()
    deal_factory = PatchedDealFactory(order_factory)
    deals_repo = InMemoryDealsRepository()

    async def make_buy_order(symbol, amount, price, deal_id, order_type):
        order = order_factory.create_buy_order(symbol, amount, price, deal_id=deal_id)
        order.mark_as_placed('ex-buy')
        return OrderExecutionResult(success=True, order=order)

    async def make_sell_order(symbol, amount, price, deal_id, order_type):
        order = order_factory.create_sell_order(symbol, amount, price, deal_id=deal_id)
        order.mark_as_placed('ex-sell')
        return OrderExecutionResult(success=True, order=order)

    order_service = MagicMock()
    order_service.create_and_place_buy_order = AsyncMock(side_effect=make_buy_order)
    order_service.create_and_place_sell_order = AsyncMock(side_effect=make_sell_order)
    order_service.cancel_order = AsyncMock(return_value=True)
    order_service.sync_orders_with_exchange = AsyncMock(return_value=[])
    order_service.get_open_orders = MagicMock(return_value=[])

    deal_service = DealService(deals_repo, order_service, deal_factory)

    svc = OrderExecutionService(order_service, deal_service, exchange)

    cp = CurrencyPair('BTC', 'USDT')
    strategy_result = (10.0, 1.0, 11.0, 1.0, {})

    report = await svc.execute_trading_strategy(cp, strategy_result)

    assert report.success
    assert report.buy_order.exchange_id == 'ex-buy'
    assert report.sell_order.exchange_id == 'ex-sell'
    assert report.deal_id is not None


@pytest.mark.asyncio
async def test_execute_trading_strategy_insufficient_balance():
    exchange = MagicMock()
    exchange.check_sufficient_balance = AsyncMock(return_value=(False, 'USDT', 5))
    exchange.fetch_ticker = AsyncMock(return_value={'last': 10.0})
    exchange.get_symbol_info = AsyncMock(return_value=ExchangeInfo(
        symbol='BTCUSDT', min_qty=0.001, max_qty=100, step_size=0.001,
        min_price=0.01, max_price=100000.0, tick_size=0.01, min_notional=1,
        fees={'maker':0.001, 'taker':0.001}
    ))

    order_service = MagicMock()
    deal_service = DealService(InMemoryDealsRepository(), order_service, PatchedDealFactory())

    svc = OrderExecutionService(order_service, deal_service, exchange)

    cp = CurrencyPair('BTC', 'USDT')
    strategy_result = (10.0, 1.0, 11.0, 1.0, {})

    report = await svc.execute_trading_strategy(cp, strategy_result)

    assert not report.success
    assert 'Insufficient balance' in report.error_message


@pytest.mark.asyncio
async def test_execute_trading_strategy_sell_failure_triggers_cancel():
    exchange = MagicMock()
    exchange.check_sufficient_balance = AsyncMock(return_value=(True, 'USDT', 1000))
    exchange.fetch_ticker = AsyncMock(return_value={'last': 10.0})
    exchange.get_symbol_info = AsyncMock(return_value=ExchangeInfo(
        symbol='BTCUSDT', min_qty=0.001, max_qty=100, step_size=0.001,
        min_price=0.01, max_price=100000.0, tick_size=0.01, min_notional=1,
        fees={'maker':0.001, 'taker':0.001}
    ))

    order_factory = OrderFactory()
    deal_factory = PatchedDealFactory(order_factory)

    async def make_buy_order(symbol, amount, price, deal_id, order_type):
        order = order_factory.create_buy_order(symbol, amount, price, deal_id=deal_id)
        order.mark_as_placed('ex-buy')
        return OrderExecutionResult(success=True, order=order)

    async def fail_sell(symbol, amount, price, deal_id, order_type):
        return OrderExecutionResult(success=False, error_message='fail')

    order_service = MagicMock()
    order_service.create_and_place_buy_order = AsyncMock(side_effect=make_buy_order)
    order_service.create_and_place_sell_order = AsyncMock(side_effect=fail_sell)
    order_service.cancel_order = AsyncMock(return_value=True)

    deals_repo = InMemoryDealsRepository()
    deal_service = DealService(deals_repo, order_service, deal_factory)

    svc = OrderExecutionService(order_service, deal_service, exchange)
    svc._emergency_cancel_buy_order = AsyncMock(return_value=True)

    cp = CurrencyPair('BTC', 'USDT')
    strategy_result = (10.0, 1.0, 11.0, 1.0, {})

    report = await svc.execute_trading_strategy(cp, strategy_result)

    assert not report.success
    svc._emergency_cancel_buy_order.assert_called_once()
