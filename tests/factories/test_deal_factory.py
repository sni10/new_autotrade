# tests/test_deal_factory.py
import unittest
from domain.factories.deal_factory import DealFactory
from domain.factories.order_factory import OrderFactory
from domain.entities.currency_pair import CurrencyPair

class TestDealFactory(unittest.TestCase):
    def test_create_new_deal(self):
        of = OrderFactory()
        df = DealFactory(of)
        pair = CurrencyPair(symbol="BTC/USDT", base_currency="BTC", quote_currency="USDT")
        deal = df.create_new_deal(pair)
        self.assertIsNotNone(deal)
        self.assertEqual(deal.status, "OPEN")
        self.assertEqual(deal.symbol, "BTC/USDT")
        self.assertIsNone(deal.buy_order)
        self.assertIsNone(deal.sell_order)