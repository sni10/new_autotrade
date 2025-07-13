import sys
import os
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from domain.entities.order import Order


def test_order_mark_and_update():
    order = Order(order_id=1, side=Order.SIDE_BUY, order_type=Order.TYPE_LIMIT,
                  amount=10.0, price=100.0, symbol="BTC/USDT")
    order.mark_as_placed("ex1", 1234567890)
    assert order.exchange_id == "ex1"
    assert order.status == Order.STATUS_OPEN
    assert order.is_open()

    data = {
        'id': 'ex1',
        'filled': 5,
        'remaining': 5,
        'average': 101.0,
        'status': 'open',
        'timestamp': 1234567999
    }
    order.update_from_exchange(data)
    assert order.filled_amount == 5
    assert order.remaining_amount == 5
    assert order.average_price == 101.0
    assert order.is_partially_filled()
    assert not order.is_fully_filled()

    # close order fully
    data_filled = {
        'id': 'ex1',
        'filled': 10,
        'remaining': 0,
        'average': 101.0,
        'status': 'closed',
        'timestamp': 1234568888
    }
    order.update_from_exchange(data_filled)
    assert order.is_filled()
    assert order.get_fill_percentage() == 1.0


def test_order_dict_roundtrip():
    order = Order(order_id=2, side=Order.SIDE_SELL, order_type=Order.TYPE_MARKET,
                  amount=3.0, price=0.0, symbol="ETH/USDT")
    order.mark_as_placed("ex2")
    order_dict = order.to_dict()
    restored = Order.from_dict(order_dict)
    assert restored.to_dict() == order_dict