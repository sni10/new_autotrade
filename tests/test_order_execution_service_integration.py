import sys
import os
import asyncio
import pytest
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.entities.currency_pair import CurrencyPair
from domain.entities.order import Order, ExchangeInfo
from domain.factories.order_factory import OrderFactory
from domain.factories.deal_factory import DealFactory
from domain.entities.deal import Deal
from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from domain.services.orders.order_execution_service import OrderExecutionService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

from infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from infrastructure.repositories.deals_repository import InMemoryDealsRepository


class PatchedDealFactory(DealFactory):
    def create_new_deal(self, currency_pair: CurrencyPair, status: str = Deal.STATUS_OPEN) -> Deal:
        deal_id = int(time.time() * 1000000)
        return Deal(deal_id=deal_id, currency_pair=currency_pair, status=status)


class MockExchangeConnector:
    def __init__(self):
        self.orders = []

    async def create_order(self, symbol, side, order_type, amount, price=None, params=None):
        order_id = f"mock_{len(self.orders)+1}"
        data = {
            'id': order_id,
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'amount': amount,
            'price': price,
            'filled': 0,
            'remaining': amount,
            'average': price,
            'status': 'open',
            'timestamp': int(time.time()*1000)
        }
        self.orders.append(data)
        return data

    async def check_sufficient_balance(self, symbol, side, amount, price=None):
        return True, 'USDT', 100000.0

    async def fetch_ticker(self, symbol):
        return {'last': 10.0}

    async def get_symbol_info(self, symbol):
        return ExchangeInfo(symbol=symbol, min_qty=0.001, max_qty=100, step_size=0.001,
                             min_price=0.01, max_price=100000.0, tick_size=0.01,
                             min_notional=1, fees={'maker':0.001, 'taker':0.001},
                             precision={'amount': 0.001, 'price': 0.01})


@pytest.mark.asyncio
async def test_order_execution_service_places_orders():
    connector = MockExchangeConnector()
    orders_repo = InMemoryOrdersRepository()
    deals_repo = InMemoryDealsRepository()

    order_factory = OrderFactory()
    deal_factory = PatchedDealFactory(order_factory)
    order_service = OrderService(orders_repo, order_factory, exchange_connector=connector)
    deal_service = DealService(deals_repo, order_service, deal_factory, exchange_connector=connector)
    svc = OrderExecutionService(order_service, deal_service, connector)

    cp = CurrencyPair('BTC', 'USDT')
    strategy_result = (10.0, 1.0, 11.0, 1.0, {})

    report = await svc.execute_trading_strategy(cp, strategy_result)

    assert report.success
    assert len(connector.orders) == 1 # Ожидаем только 1 ордер на бирже
    assert connector.orders[0]['side'] == 'buy'