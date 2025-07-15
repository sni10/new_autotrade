import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.factories.deal_factory import DealFactory
from domain.entities.currency_pair import CurrencyPair
from domain.factories.order_factory import OrderFactory


class TestDealFactory:
    def test_create_new_deal_assigns_deal_id_to_orders(self):
        of = OrderFactory()
        df = DealFactory(of)
        pair = CurrencyPair(symbol="BTC/USDT", base_currency="BTC", quote_currency="USDT")
        deal = df.create_new_deal(pair)
        # В новой логике ордера не создаются на этом этапе
        assert deal.buy_order is None
        assert deal.sell_order is None
        assert deal.currency_pair_id == 'BTC/USDT'