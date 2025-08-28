import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from domain.entities.order import Order
from infrastructure.repositories.orders_repository import InMemoryOrdersRepository


def make_order(order_id, status=Order.STATUS_OPEN, symbol="BTCUSDT"):
    return Order(
        order_id=order_id,
        side=Order.SIDE_BUY,
        order_type=Order.TYPE_LIMIT,
        price=100.0,
        amount=1.0,
        status=status,
        symbol=symbol
    )


def test_save_and_get():
    repo = InMemoryOrdersRepository()
    order = make_order(1)
    repo.save(order)
    assert repo.get_by_id(1) == order
    assert repo.get_orders_by_symbol("BTCUSDT") == [order]
    assert repo.get_open_orders() == [order]


def test_bulk_update_and_delete_old():
    repo = InMemoryOrdersRepository()
    o1 = make_order(1, status=Order.STATUS_OPEN)
    o2 = make_order(2, status=Order.STATUS_OPEN)
    repo.save(o1)
    repo.save(o2)
    repo.bulk_update_status([1, 2], Order.STATUS_CLOSED)
    assert o1.status == Order.STATUS_CLOSED
    assert o2.status == Order.STATUS_CLOSED

    old_ts = int((datetime.now() - timedelta(days=2)).timestamp() * 1000)
    o1.closed_at = old_ts
    o2.closed_at = old_ts
    deleted = repo.delete_old_orders(1)
    assert deleted == 2
    assert repo.get_all() == []