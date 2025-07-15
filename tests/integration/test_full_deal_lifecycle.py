# tests/integration/test_full_deal_lifecycle.py
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
from domain.services.orders.buy_order_monitor import BuyOrderMonitor
from domain.services.orders.filled_buy_order_handler import FilledBuyOrderHandler
from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
from tests.mocks.mock_exchange_connector import MockCcxtExchangeConnector

pytestmark = pytest.mark.asyncio

@pytest.fixture
def setup_services():
    market_info = { "THE/USDT": { "symbol": "THE/USDT", "min_qty": 0.1, "max_qty": 10000.0, "step_size": 0.1, "min_price": 0.0001, "max_price": 100.0, "tick_size": 0.0001, "min_notional": 10.0, "fees": {"maker": 0.001, "taker": 0.001}, "precision": {"amount": 1, "price": 4}, "last_price": 0.4000 } }
    mock_exchange = MockCcxtExchangeConnector(market_info)
    deals_repo = InMemoryDealsRepository()
    orders_repo = InMemoryOrdersRepository()
    order_factory = OrderFactory()
    symbol_info = asyncio.run(mock_exchange.get_symbol_info("THE/USDT"))
    order_factory.update_exchange_info("THE/USDT", symbol_info)
    order_service = OrderService(orders_repo, order_factory, mock_exchange)
    deal_factory = DealFactory(order_factory)
    deal_service = DealService(deals_repo, order_service, deal_factory, mock_exchange)
    order_execution_service = OrderExecutionService(order_service, deal_service, mock_exchange)
    buy_order_monitor = BuyOrderMonitor(order_service=order_service, deal_service=deal_service, exchange_connector=mock_exchange, max_age_minutes=5, max_price_deviation_percent=10, check_interval_seconds=1)
    filled_buy_handler = FilledBuyOrderHandler(order_service, deal_service)
    deal_completion_monitor = DealCompletionMonitor(deal_service, order_service)
    return { "oes": order_execution_service, "mock_exchange": mock_exchange, "filled_handler": filled_buy_handler, "completion_monitor": deal_completion_monitor, "orders_repo": orders_repo, "deals_repo": deals_repo, "buy_monitor": buy_order_monitor, "order_service": order_service }

async def test_happy_path_deal_lifecycle(setup_services):
    oes = setup_services["oes"]
    mock_exchange = setup_services["mock_exchange"]
    filled_handler = setup_services["filled_handler"]
    completion_monitor = setup_services["completion_monitor"]
    orders_repo = setup_services["orders_repo"]
    deals_repo = setup_services["deals_repo"]
    currency_pair = CurrencyPair("THE", "USDT", "THE/USDT", deal_quota=25, profit_markup=0.015)
    strategy_result = (0.4000, 62.5, 0.4060, 62.5, {})
    report = await oes.execute_trading_strategy(currency_pair, strategy_result)
    assert report.success, report.error_message
    buy_order, sell_order = report.buy_order, report.sell_order
    mock_exchange.fill_order(buy_order.exchange_id)
    await oes.order_service.get_order_status(buy_order)
    await filled_handler.check_and_place_sell_orders()
    # Получаем актуальный sell_order из репозитория после размещения
    updated_sell_order = orders_repo.get_by_id(sell_order.order_id)
    mock_exchange.fill_order(updated_sell_order.exchange_id)
    await oes.order_service.get_order_status(updated_sell_order)
    await completion_monitor.check_deals_completion()
    assert deals_repo.get_by_id(report.deal_id).is_closed()

async def test_stale_order_deal_lifecycle(setup_services):
    oes = setup_services["oes"]
    mock_exchange = setup_services["mock_exchange"]
    buy_monitor = setup_services["buy_monitor"]
    orders_repo = setup_services["orders_repo"]
    deals_repo = setup_services["deals_repo"]
    currency_pair = CurrencyPair("THE", "USDT", "THE/USDT", deal_quota=25, profit_markup=0.015)
    strategy_result = (0.4000, 62.5, 0.4060, 62.5, {})
    report = await oes.execute_trading_strategy(currency_pair, strategy_result)
    assert report.success, report.error_message
    original_buy_order = report.buy_order
    mock_exchange.set_market_price("THE/USDT", 0.45)
    await buy_monitor.check_stale_buy_orders()
    old_order_in_repo = orders_repo.get_by_id(original_buy_order.order_id)
    assert old_order_in_repo.status == "CANCELED"