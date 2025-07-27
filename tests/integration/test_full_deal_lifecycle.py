# tests/integration/test_full_deal_lifecycle.py
import pytest
import asyncio
from typing import Dict

from src.domain.entities.currency_pair import CurrencyPair
from src.domain.factories.deal_factory import DealFactory
from src.domain.factories.order_factory import OrderFactory
from src.infrastructure.repositories.deals_repository import InMemoryDealsRepository
from src.infrastructure.repositories.orders_repository import InMemoryOrdersRepository
from src.domain.services.deals.deal_service import DealService
from src.domain.services.orders.unified_order_service import UnifiedOrderService
from src.domain.services.orders.order_execution_service import OrderExecutionService
from src.domain.services.orders.balance_service import BalanceService
from src.domain.services.orders.buy_order_monitor import BuyOrderMonitor
from src.domain.services.orders.filled_buy_order_handler import FilledBuyOrderHandler
from src.domain.services.deals.deal_completion_monitor import DealCompletionMonitor
from tests.mocks.mock_exchange_connector import MockCcxtExchangeConnector

import pytest_asyncio

# Используем pytest-asyncio для асинхронных тестов
pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def market_info():
    """Фикстура с информацией о рынке для тестов."""
    return {
        "THE/USDT": {
            "id": "THEUSDT",
            "symbol": "THE/USDT",
            "base": "THE",
            "quote": "USDT",
            "baseId": "THE",
            "quoteId": "USDT",
            "active": True,
            "type": "spot",
            "limits": {
                "amount": {"min": 0.1, "max": 10000.0},
                "price": {"min": 0.0001, "max": 100.0},
                "cost": {"min": 10.0}
            },
            "precision": {"amount": 1, "price": 4},
            "info": {"last_price": 0.4000} # Начальная цена для тестов
        }
    }

import pytest_asyncio

@pytest.fixture
async def setup_services(market_info):
    """Фикстура для настройки всех необходимых сервисов с моками."""
    # --- Mocks and Repositories ---
    mock_exchange = MockCcxtExchangeConnector(market_info)
    mock_exchange.set_balance("USDT", 10000.0)
    deals_repo = InMemoryDealsRepository()
    orders_repo = InMemoryOrdersRepository()
    order_factory = OrderFactory()
    
    # --- Services ---
    initial_balance = {
        'free': {"USDT": 10000.0, "BTC": 10.0, "ETH": 100.0, "THE": 5000.0},
        'used': {"USDT": 0.0, "BTC": 0.0, "ETH": 0.0, "THE": 0.0},
        'total': {"USDT": 10000.0, "BTC": 10.0, "ETH": 100.0, "THE": 5000.0}
    }
    balance_service = BalanceService(mock_exchange, initial_balance=initial_balance)
    order_service = UnifiedOrderService(orders_repo, order_factory, mock_exchange, balance_service)
    deal_service = DealService(deals_repo, order_service, DealFactory(order_factory), mock_exchange)
    order_execution_service = OrderExecutionService(order_service, deal_service, mock_exchange)
    
    buy_order_monitor = BuyOrderMonitor(
        order_service=order_service,
        deal_service=deal_service,
        exchange_connector=mock_exchange,
        max_age_minutes=5, # Ускоряем для тестов
        max_price_deviation_percent=1, # Уменьшаем для тестов
        check_interval_seconds=1 
    )
    
    filled_buy_handler = FilledBuyOrderHandler(order_service, deal_service)
    deal_completion_monitor = DealCompletionMonitor(deal_service, order_service)

    # Обновляем кеш в order_factory, чтобы он знал о правилах
    symbol_info = await mock_exchange.get_symbol_info("THE/USDT")
    order_factory.update_exchange_info("THE/USDT", symbol_info)

    return {
        "mock_exchange": mock_exchange,
        "deals_repo": deals_repo,
        "orders_repo": orders_repo,
        "order_execution_service": order_execution_service,
        "buy_order_monitor": buy_order_monitor,
        "filled_buy_handler": filled_buy_handler,
        "deal_completion_monitor": deal_completion_monitor,
        "order_service": order_service
    }

async def test_happy_path_deal_lifecycle(setup_services: Dict):
    services = await setup_services
    # --- ARRANGE ---
    oes = services["order_execution_service"]
    mock_exchange = services["mock_exchange"]
    filled_handler = services["filled_buy_handler"]
    completion_monitor = services["deal_completion_monitor"]
    orders_repo = services["orders_repo"]
    deals_repo = services["deals_repo"]
    order_service = services["order_service"]

    currency_pair = CurrencyPair(
        symbol="THE/USDT",
        base_currency="THE",
        quote_currency="USDT",
        deal_quota=25,
        profit_markup=0.015
    )
    strategy_result = (0.4000, 62.5, 0.4060, 62.5, {}) # buy_price, buy_amount, sell_price, sell_amount

    # --- ACTION 1: Create Deal ---
    report = await oes.execute_trading_strategy(currency_pair, strategy_result)
    
    # --- ASSERT 1: Deal Created Correctly ---
    assert report.success
    assert report.deal_id is not None
    
    deal = deals_repo.get_by_id(report.deal_id)
    buy_order = orders_repo.get_by_id(report.buy_order.order_id)
    sell_order = orders_repo.get_by_id(report.sell_order.order_id)

    assert deal.is_open()
    assert buy_order.status == "OPEN" # Размещен на бирже
    assert buy_order.exchange_id is not None
    assert sell_order.status == "PENDING" # Только в локальном репо
    assert sell_order.exchange_id is None

    # --- ACTION 2: Fill BUY order ---
    mock_exchange.fill_order(buy_order.exchange_id, fill_price=0.4000)
    # Обновляем статус в локальном репо (это делает `sync_orders_with_exchange` в реальной жизни)
    updated_buy_order = await order_service.get_order_status(buy_order)
    assert updated_buy_order.is_filled()

    # --- ACTION 3: Run FilledBuyOrderHandler ---
    await filled_handler.check_and_place_sell_orders()

    # --- ASSERT 2: SELL order is now placed ---
    updated_sell_order = orders_repo.get_by_id(sell_order.order_id)
    assert updated_sell_order.status == "OPEN"
    assert updated_sell_order.exchange_id is not None

    # --- ACTION 4: Fill SELL order ---
    mock_exchange.fill_order(updated_sell_order.exchange_id, fill_price=0.4060)
    await order_service.get_order_status(updated_sell_order)

    # --- ACTION 5: Run DealCompletionMonitor ---
    await completion_monitor.check_deals_completion()

    # --- ASSERT 3: Deal is now CLOSED ---
    final_deal = deals_repo.get_by_id(deal.deal_id)
    assert final_deal.is_closed()


async def test_stale_order_deal_lifecycle(setup_services: Dict):
    services = await setup_services
    # --- ARRANGE ---
    oes = services["order_execution_service"]
    mock_exchange = services["mock_exchange"]
    buy_monitor = services["buy_order_monitor"]
    filled_handler = services["filled_buy_handler"]
    completion_monitor = services["deal_completion_monitor"]
    orders_repo = services["orders_repo"]
    deals_repo = services["deals_repo"]
    order_service = services["order_service"]

    currency_pair = CurrencyPair(
        symbol="THE/USDT",
        base_currency="THE",
        quote_currency="USDT",
        deal_quota=25,
        profit_markup=0.015
    )
    strategy_result = (0.4000, 62.5, 0.4060, 62.5, {})

    # --- ACTION 1: Create Deal ---
    report = await oes.execute_trading_strategy(currency_pair, strategy_result)
    original_buy_order = report.buy_order
    original_sell_order = report.sell_order
    original_sell_price = original_sell_order.price if original_sell_order else None if original_sell_order else None

    # --- ASSERT 1: Initial state is correct ---
    assert original_buy_order and original_buy_order.status == "OPEN"
    assert original_sell_order.status == "PENDING"

    # --- ACTION 2: Make the order stale and run monitor ---
    mock_exchange.set_market_price("THE/USDT", 0.4200) # Цена ушла вверх, наш BUY не исполнится
    await buy_monitor.check_stale_buy_orders()

    # --- ASSERT 2: Order was recreated, and deal updated ---
    # Старый ордер отменен
    assert orders_repo.get_by_id(original_buy_order.order_id).status == "CANCELED"
    
    # Новый BUY ордер создан
    all_orders = orders_repo.get_all()
    new_buy_order = next(o for o in all_orders if o.side == "BUY" and o.status == "OPEN")
    assert new_buy_order.order_id != original_buy_order.order_id
    
    # Сделка обновлена
    deal = deals_repo.get_by_id(report.deal_id)
    assert deal.buy_order.order_id == new_buy_order.order_id

    # Локальный SELL ордер обновлен (проверяем, что цена изменилась)
    updated_sell_order = orders_repo.get_by_id(original_sell_order.order_id)
    assert updated_sell_order.status == "PENDING"
    assert updated_sell_order.price != original_sell_price # Цена должна была пересчитаться

    # --- ACTION 3 & ASSERT 3: Complete the lifecycle ---
    # Исполняем новый BUY
    mock_exchange.fill_order(new_buy_order.exchange_id)
    await order_service.get_order_status(new_buy_order)
    assert new_buy_order.is_filled()

    # Запускаем обработчик, который разместит обновленный SELL
    await filled_handler.check_and_place_sell_orders()
    assert updated_sell_order.status == "OPEN"

    # Исполняем SELL
    mock_exchange.fill_order(updated_sell_order.exchange_id)
    await order_service.get_order_status(updated_sell_order)
    assert updated_sell_order.is_filled()

    # Запускаем монитор завершения
    await completion_monitor.check_deals_completion()
    assert deal.is_closed()
