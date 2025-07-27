#!/usr/bin/env python3
"""
Тест нового умного стоп-лосса с анализом стакана
"""
import asyncio
import logging
from unittest.mock import Mock, AsyncMock

from src.domain.services.risk.stop_loss_monitor import StopLossMonitor
from src.domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer, OrderBookMetrics, OrderBookSignal
from src.domain.entities.deal import Deal
from src.domain.entities.order import Order
from src.domain.entities.currency_pair import CurrencyPair

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import pytest

@pytest.mark.asyncio
async def test_smart_stop_loss():
    """Тест умного стоп-лосса с различными сценариями"""
    
    # Создаем мок-объекты
    deal_service = Mock()
    order_execution_service = AsyncMock()
    exchange_connector = AsyncMock()
    
    # Создаем анализатор стакана
    orderbook_analyzer = OrderBookAnalyzer({
        'min_volume_threshold': 1000,
        'big_wall_threshold': 5000,
        'max_spread_percent': 0.3,
        'min_liquidity_depth': 15,
        'typical_order_size': 10
    })
    
    # Создаем монитор стоп-лосса
    stop_loss_monitor = StopLossMonitor(
        deal_service=deal_service,
        order_execution_service=order_execution_service,
        exchange_connector=exchange_connector,
        orderbook_analyzer=orderbook_analyzer,
        stop_loss_percent=2.0,
        check_interval_seconds=1,
        warning_percent=5.0,
        critical_percent=10.0,
        emergency_percent=15.0
    )
    
    # Создаем тестовую сделку
    pair = CurrencyPair(symbol="BTC/USDT", base_currency="BTC", quote_currency="USDT")
    buy_order = Order(
        order_id=1,
        deal_id=1,
        symbol="BTC/USDT",
        side=Order.SIDE_BUY,
        order_type=Order.TYPE_LIMIT,
        price=10000,
        amount=1,
        status=Order.STATUS_FILLED
    )
    sell_order = Order(
        order_id=2,
        deal_id=1,
        symbol="BTC/USDT",
        side=Order.SIDE_SELL,
        order_type=Order.TYPE_LIMIT,
        price=10500,
        amount=1,
        status=Order.STATUS_OPEN
    )
    deal = Deal(
        deal_id=1,
        currency_pair=pair,
        buy_order=buy_order,
        sell_order=sell_order,
        status=Deal.STATUS_OPEN
    )
    
    # Настраиваем мок-объекты
    deal_service.get_open_deals.return_value = [deal]
    
    # Тест 0: Проверяем наличие метода fetch_order_book
    logger.info("=== Тест 0: Проверка метода fetch_order_book ===")
    assert hasattr(exchange_connector, 'fetch_order_book'), "Метод fetch_order_book должен существовать"
    logger.info("✅ Метод fetch_order_book найден")
    
    # Тест 1: Нормальная работа без срабатывания стоп-лосса
    logger.info("=== Тест 1: Нормальная работа (цена 0.005850) ===")
    exchange_connector.fetch_ticker.return_value = {'last': 0.005850}
    exchange_connector.fetch_order_book.return_value = {
        'bids': [[0.005840, 1000], [0.005830, 2000]],
        'asks': [[0.005860, 1000], [0.005870, 2000]]
    }
    
    await stop_loss_monitor.check_open_deals()
    
    # Тест 2: Предупреждение при -5% (цена 0.005558)
    logger.info("=== Тест 2: Предупреждение при -5% (цена 0.005558) ===")
    exchange_connector.fetch_ticker.return_value = {'last': 0.005558}
    exchange_connector.fetch_order_book.return_value = {
        'bids': [[0.005550, 1000], [0.005540, 2000]],
        'asks': [[0.005570, 1000], [0.005580, 2000]]
    }
    
    await stop_loss_monitor.check_open_deals()
    
    # Тест 3: Критический уровень с пробитием поддержки
    logger.info("=== Тест 3: Критический уровень -10% + пробитие поддержки ===")
    exchange_connector.fetch_ticker.return_value = {'last': 0.005265}
    exchange_connector.fetch_order_book.return_value = {
        'bids': [[0.005260, 500], [0.005250, 1000]],  # Слабая поддержка
        'asks': [[0.005270, 3000], [0.005280, 5000]]  # Сильное сопротивление
    }
    
    # Мокаем создание маркет-ордера
    mock_market_order = Order(
        order_id=3,
        deal_id=1,
        symbol="TURBOUSDT",
        side="SELL",
        order_type="MARKET",
        price=0.005265,
        amount=4274.0,
        status="FILLED"
    )
    order_execution_service.create_market_sell_order.return_value = mock_market_order
    order_execution_service.cancel_order.return_value = True
    
    await stop_loss_monitor.check_open_deals()
    
    # Тест 4: Экстренная ликвидация при -15%
    logger.info("=== Тест 4: Экстренная ликвидация при -15% ===")
    exchange_connector.fetch_ticker.return_value = {'last': 0.004973}
    exchange_connector.fetch_order_book.return_value = {
        'bids': [[0.004970, 100], [0.004960, 200]],
        'asks': [[0.004980, 10000], [0.004990, 20000]]
    }
    
    # Сбрасываем флаг предупреждения для нового теста
    stop_loss_monitor._warned_deals.clear()
    
    await stop_loss_monitor.check_open_deals()
    
    # Выводим статистику
    logger.info("=== Статистика работы стоп-лосса ===")
    stats = stop_loss_monitor.get_statistics()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_smart_stop_loss())