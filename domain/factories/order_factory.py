# my_trading_app/domain/factories/order_factory.py

import time
from itertools import count
from domain.entities.order import Order

# 🔧 FIX: Генератор уникальных ID на основе счетчика
_id_gen = count(int(time.time()*1e6))

def _next_id():
    """🔧 FIX: Генерация следующего уникального ID"""
    return next(_id_gen)

class OrderFactory:
    """
    Фабрика для создания ордеров (buy / sell).
    """

    def __init__(self):
        pass  # Возможно, параметры по умолчанию

    def _create_order(self, side: str, price: float, amount: float) -> Order:
        """🔧 FIX: Базовый метод создания ордера с уникальным ID"""
        return Order(
            order_id=_next_id(),
            side=side,
            order_type=Order.TYPE_LIMIT,
            price=price,
            amount=amount,
            status=Order.STATUS_OPEN,
            deal_id=None,  # Установим позже (Deal сам проставит)
        )

    def create_buy_order(self, price: float, amount: float) -> Order:
        """🔧 FIX: Создание buy ордера через общий метод"""
        return self._create_order(Order.SIDE_BUY, price, amount)

    def create_sell_order(self, price: float, amount: float) -> Order:
        """🔧 FIX: Создание sell ордера через общий метод"""
        return self._create_order(Order.SIDE_SELL, price, amount)
