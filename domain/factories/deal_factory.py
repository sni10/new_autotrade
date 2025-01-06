# my_trading_app/domain/factories/deal_factory.py

import time
from typing import Optional

from domain.entities.deal import Deal
from domain.entities.order import Order
from domain.entities.currency_pair import CurrencyPair
from domain.factories.order_factory import OrderFactory

class DealFactory:
    """
    Фабрика для создания новых Сделок (Deal).
    Может сразу создавать 2 связанных ордера (buy и sell).
    """

    def __init__(self, order_factory: Optional[OrderFactory] = None):
        self.order_factory = order_factory or OrderFactory()

    def create_new_deal(
        self,
        currency_pair: CurrencyPair,
        status: str = Deal.STATUS_OPEN
    ) -> Deal:
        """
        Создаём новую сделку и два ордера (buy/sell).
        Пока что sell-ордер может быть пустым или сразу "грядущим".
        """
        deal_id = int(time.time() * 1000000)  # или счётчик

        # Создаём buy_order (с начальными нулевыми price/amount).
        buy_order = self.order_factory.create_buy_order(price=0.0, amount=0.0)

        # Создаём sell_order (тоже пустой).
        sell_order = self.order_factory.create_sell_order(price=0.0, amount=0.0)

        deal = Deal(
            deal_id=deal_id,
            currency_pair_id=currency_pair.symbol,
            status=status,
            buy_order=buy_order,
            sell_order=sell_order,
        )
        return deal
