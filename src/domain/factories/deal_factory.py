from itertools import count
import time

from domain.entities.currency_pair import CurrencyPair
from domain.entities.deal import Deal
from domain.factories.order_factory import OrderFactory

# 🔧 Генератор уникальных ID на основе счетчика + timestamp
_id_gen = count(int(time.time()*1e6))

def _next_id():
    """🔧 Генерация следующего уникального ID"""
    return next(_id_gen)

class DealFactory:
    """
    Фабрика для создания сущностей Deal.
    """
    def __init__(self, order_factory: OrderFactory):
        self.order_factory = order_factory

    def create_new_deal(self, currency_pair: CurrencyPair, status: str = Deal.STATUS_OPEN) -> Deal:
        """
        Создает новую сделку с уникальным ID.
        """
        deal_id = _next_id()
        return Deal(
            deal_id=deal_id,
            currency_pair=currency_pair,
            status=status
        )