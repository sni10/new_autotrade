# my_trading_app/domain/factories/order_factory.py

import time
from domain.entities.order import Order

class OrderFactory:
    """
    Фабрика для создания ордеров (buy / sell).
    """

    def __init__(self):
        pass  # Возможно, параметры по умолчанию

    def create_buy_order(self, price: float, amount: float) -> Order:
        order_id = int(time.time() * 1000000)
        return Order(
            order_id=order_id,
            side=Order.SIDE_BUY,
            order_type=Order.TYPE_LIMIT,
            price=price,
            amount=amount,
            status=Order.STATUS_OPEN,
            deal_id=None  # Установим позже (Deal сам проставит)
        )

    def create_sell_order(self, price: float, amount: float) -> Order:
        order_id = int(time.time() * 1000000)
        return Order(
            order_id=order_id,
            side=Order.SIDE_SELL,
            order_type=Order.TYPE_LIMIT,
            price=price,
            amount=amount,
            status=Order.STATUS_OPEN,
            deal_id=None
        )
