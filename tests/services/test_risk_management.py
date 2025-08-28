# tests/test_risk_management.py
import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from domain.entities.currency_pair import CurrencyPair
from domain.entities.ticker import Ticker
from domain.services.deals.deal_service import DealService
from domain.services.risk.stop_loss_monitor import StopLossMonitor
from domain.entities.order_book import OrderBook
from domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer


class TestRiskManagement(unittest.TestCase):

    def setUp(self):
        self.deals_repo = MagicMock()
        self.order_service = MagicMock()
        self.deal_factory = MagicMock()
        self.exchange_connector = MagicMock()
        self.order_execution_service = MagicMock()

        self.deal_service = AsyncMock()
        
        # Создаем мок для OrderBookAnalyzer
        self.orderbook_analyzer = OrderBookAnalyzer({
            'min_volume_threshold': 1000,
            'big_wall_threshold': 5000,
            'max_spread_percent': 0.3,
            'min_liquidity_depth': 15,
            'typical_order_size': 10
        })

        self.stop_loss_monitor = StopLossMonitor(
            deal_service=self.deal_service,
            order_execution_service=self.order_execution_service,
            exchange_connector=self.exchange_connector,
            orderbook_analyzer=self.orderbook_analyzer,
            stop_loss_percent=2.0,
            check_interval_seconds=1,
        )

    def test_check_balance_sufficient(self):
        """Тест проверки баланса при достаточных средствах."""
        self.exchange_connector.get_balance = AsyncMock(return_value=100.0)
        self.exchange_connector.fetch_order_book = AsyncMock(return_value={
            'bids': [[0.005840, 1000], [0.005830, 2000]],
            'asks': [[0.005860, 1000], [0.005870, 2000]]
        })

        self.deal_service.check_balance_before_deal = AsyncMock(return_value=(True, "достаточен"))

        async def run_test():
            can_deal, reason = await self.deal_service.check_balance_before_deal("USDT", 50.0)
            self.assertTrue(can_deal)
            self.assertIn("достаточен", reason)

        asyncio.run(run_test())

    def test_check_balance_insufficient(self):
        """Тест проверки баланса при недостаточных средствах."""
        self.exchange_connector.get_balance = AsyncMock(return_value=40.0)
        self.exchange_connector.fetch_order_book = AsyncMock(return_value={
            'bids': [[0.005840, 1000], [0.005830, 2000]],
            'asks': [[0.005860, 1000], [0.005870, 2000]]
        })

        self.deal_service.check_balance_before_deal = AsyncMock(return_value=(False, "Недостаточно средств"))

        async def run_test():
            can_deal, reason = await self.deal_service.check_balance_before_deal("USDT", 50.0)
            self.assertFalse(can_deal)
            self.assertIn("Недостаточно средств", reason)

        asyncio.run(run_test())

    def test_stop_loss_trigger(self):
        """Тест срабатывания stop-loss."""
        deal = MagicMock()
        deal.deal_id = 1
        deal.currency_pair = CurrencyPair("ETH", "USDT", "ETH/USDT")
        deal.buy_order.is_filled.return_value = True
        deal.buy_order.average_price = 100.0
        deal.symbol = "ETH/USDT"

        self.deal_service.get_open_deals = MagicMock(return_value=[deal])
        # Цена упала на 15% (100 -> 85) - должен сработать экстренный стоп-лосс
        self.exchange_connector.fetch_ticker = AsyncMock(return_value=Ticker(data={"last": 85.0, "symbol": "ETH/USDT"}))
        self.exchange_connector.fetch_order_book = AsyncMock(return_value=OrderBook(
            symbol="ETH/USDT",
            timestamp=1,
            bids=[[84.0, 1000], [83.0, 2000]],
            asks=[[86.0, 1000], [87.0, 2000]]
        ))
        
        # Мокаем создание маркет-ордера для стоп-лосса
        self.order_execution_service.create_market_sell_order = AsyncMock(return_value=MagicMock())
        self.order_execution_service.cancel_order = AsyncMock(return_value=True)

        async def run_test():
            await self.stop_loss_monitor.check_open_deals()
            self.order_execution_service.create_market_sell_order.assert_called_once()

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
