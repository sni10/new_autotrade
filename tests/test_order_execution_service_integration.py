import asyncio
import pytest
import time

from src.domain.entities.currency_pair import CurrencyPair
from src.domain.entities.order import Order, ExchangeInfo
from src.domain.factories.order_factory import OrderFactory
from src.domain.factories.deal_factory import DealFactory
from src.domain.entities.deal import Deal
from src.domain.services.deals.deal_service import DealService
from src.domain.services.orders.unified_order_service import UnifiedOrderService
from src.domain.services.orders.order_execution_service import OrderExecutionService
from src.domain.services.orders.balance_service import BalanceService
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector

from src.infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from src.infrastructure.repositories.deals_repository import InMemoryDealsRepository
from tests.mocks.mock_exchange_connector import MockCcxtExchangeConnector


class PatchedDealFactory(DealFactory):
    def create_new_deal(self, currency_pair: CurrencyPair, status: str = Deal.STATUS_OPEN) -> Deal:
        deal_id = int(time.time() * 1000000)
        return Deal(deal_id=deal_id, currency_pair=currency_pair, status=status)


@pytest.mark.asyncio
async def test_order_execution_service_places_orders():
    market_info = {
        "BTC/USDT": {
            "id": "BTCUSDT",
            "symbol": "BTC/USDT",
            "base": "BTC",
            "quote": "USDT",
            "baseId": "BTC",
            "quoteId": "USDT",
            "active": True,
            "type": "spot",
            "limits": {
                "amount": {"min": 0.001, "max": 100},
                "price": {"min": 0.01, "max": 100000.0},
                "cost": {"min": 1}
            },
            "precision": {"amount": 3, "price": 2},
            "info": {"last_price": 10000.0}
        }
    }
    connector = MockCcxtExchangeConnector(market_info)
    orders_repo = InMemoryOrdersRepository()
    deals_repo = InMemoryDealsRepository()

    order_factory = OrderFactory()
    symbol_info = await connector.get_symbol_info("BTC/USDT")
    order_factory.update_exchange_info("BTC/USDT", symbol_info)
    
    deal_factory = PatchedDealFactory(order_factory)
    initial_balance = {
        'free': {"USDT": 10000.0, "BTC": 10.0},
        'used': {"USDT": 0.0, "BTC": 0.0},
        'total': {"USDT": 10000.0, "BTC": 10.0}
    }
    balance_service = BalanceService(connector, initial_balance=initial_balance)
    order_service = UnifiedOrderService(orders_repo, order_factory, connector, balance_service)
    deal_service = DealService(deals_repo, order_service, deal_factory, connector)
    svc = OrderExecutionService(order_service, deal_service, connector)

    cp = CurrencyPair('BTC', 'USDT')
    strategy_result = (10000.0, 1.0, 11000.0, 1.0, {})

    report = await svc.execute_trading_strategy(cp, strategy_result)

    assert report.success
    # Проверяем, что на бирже был создан только BUY ордер
    assert len(connector.get_open_orders()) == 1
    assert connector.get_open_orders()[0]['side'] == 'buy'
    
    # Проверяем, что в репозитории есть оба ордера (BUY - OPEN, SELL - PENDING)
    all_orders = orders_repo.get_all()
    assert len(all_orders) == 2
    buy_order = next(o for o in all_orders if o.side == Order.SIDE_BUY)
    sell_order = next(o for o in all_orders if o.side == Order.SIDE_SELL)
    
    assert buy_order.status == Order.STATUS_OPEN
    assert sell_order.status == Order.STATUS_PENDING
