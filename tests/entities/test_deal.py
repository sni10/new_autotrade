import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from domain.entities.deal import Deal
from domain.entities.order import Order
from domain.entities.currency_pair import CurrencyPair


def test_deal_attach_and_close():
    buy = Order(order_id=1, side=Order.SIDE_BUY, order_type=Order.TYPE_LIMIT, amount=1, price=10, symbol="BTC/USDT")
    sell = Order(order_id=2, side=Order.SIDE_SELL, order_type=Order.TYPE_LIMIT, amount=1, price=12, symbol="BTC/USDT")
    pair = CurrencyPair(symbol="BTC/USDT", base_currency="BTC", quote_currency="USDT")
    deal = Deal(deal_id=100, currency_pair=pair, buy_order=buy, sell_order=sell)
    assert buy.deal_id == 100
    assert sell.deal_id == 100
    deal.close()
    assert deal.is_closed()