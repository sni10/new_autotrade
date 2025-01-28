# my_trading_app/domain/factories/deal_factory.py

import time
from typing import Optional
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.factories.order_factory import OrderFactory


class DealFactory:
    """
    Фабрика для создания новых Сделок (Deal).
    """

    def __init__(self, order_factory: Optional[OrderFactory] = None):
        self.order_factory = order_factory or OrderFactory()

    def create_new_deal(
            self,
            currency_pair: CurrencyPair,
            status: str = Deal.STATUS_OPEN
    ) -> Deal:
        """
        Создаём новую сделку и два "пустых" ордера (buy/sell).
        В момент создания у ордеров deal_id=None.
        Deal сам проставит им deal_id = deal.deal_id.
        """
        deal_id = int(time.time() * 1000000)

        # Создаём buy_order (с начальными нулевыми price/amount).
        buy_order = self.order_factory.create_buy_order(price=0.0, amount=0.0)

        time.sleep(0.09)

        # Создаём sell_order (тоже пустой).
        sell_order = self.order_factory.create_sell_order(price=0.0, amount=0.0)

        deal = Deal(
            deal_id=deal_id,
            currency_pair_id=currency_pair.symbol,
            status=status,
            buy_order=buy_order,
            sell_order=sell_order,
        )
        # Внутри Deal есть _sync_order_deal_id(), которая проставит
        # buy_order.deal_id = deal_id и sell_order.deal_id = deal_id
        return deal
