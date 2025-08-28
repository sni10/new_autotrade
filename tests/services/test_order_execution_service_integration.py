# tests/test_order_execution_service_integration.py
import pytest
import asyncio
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from domain.factories.order_factory import OrderFactory
from infrastructure.repositories.deals_repository import InMemoryDealsRepository
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from domain.services.orders.order_execution_service import OrderExecutionService
from tests.mocks.mock_exchange_connector import MockCcxtExchangeConnector

pytestmark = pytest.mark.asyncio

@pytest.fixture
def setup_services():
    market_info = { "BTC/USDT": { "symbol": "BTC/USDT", "min_qty": 0.001, "max_qty": 100, "step_size": 0.001, "min_price": 0.01, "max_price": 100000.0, "tick_size": 0.01, "min_notional": 1, "fees": {"maker":0.001, "taker":0.001}, "precision": {"amount": 3, "price": 2} } }
    connector = MockCcxtExchangeConnector(market_info)
    orders_repo = InMemoryOrdersRepository()
    deals_repo = InMemoryDealsRepository()
    order_factory = OrderFactory()
    symbol_info = asyncio.run(connector.get_symbol_info("BTC/USDT"))
    order_factory.update_exchange_info("BTC/USDT", symbol_info)
    order_service = OrderService(orders_repo, order_factory, connector)
    deal_factory = DealFactory(order_factory)
    deal_service = DealService(deals_repo, order_service, deal_factory, connector)
    svc = OrderExecutionService(order_service, deal_service, connector)
    return svc, connector

async def test_order_execution_service_places_orders(setup_services):
    svc, connector = setup_services
    cp = CurrencyPair('BTC', 'USDT', deal_quota=25)
    strategy_result = (10000.0, 1.0, 11000.0, 1.0, {})
    report = await svc.execute_trading_strategy(cp, strategy_result)
    assert report.success
    assert len(connector._orders) == 1
    assert list(connector._orders.values())[0].side == 'BUY'