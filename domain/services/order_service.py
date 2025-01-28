# domain/services/order_service.py
from domain.entities.order import Order
from domain.factories.order_factory import OrderFactory
from infrastructure.repositories.orders_repository import OrdersRepository
from typing import Optional

class OrderService:
    """
    Сервис для работы с ордерами:
    - создание новых ордеров (buy/sell) через фабрику,
    - сохранение/обновление ордеров в репозитории,
    - (опционально) взаимодействие с биржей через exchange_connector.
    """

    def __init__(
        self,
        orders_repo: OrdersRepository,
        order_factory: OrderFactory,
        exchange_connector=None  # Если хотите подключать реальный REST (ccxt) или websocket
    ):
        self.orders_repo = orders_repo
        self.order_factory = order_factory
        self.exchange_connector = exchange_connector  # для реального выставления ордера

    def create_buy_order(self, price: float, amount: float) -> Order:
        """
        Использует OrderFactory для создания BUY-ордера, затем сохраняет ордер в репозитории.
        """
        order = self.order_factory.create_buy_order(price, amount)
        self.save_order(order)
        return order

    def create_sell_order(self, price: float, amount: float) -> Order:
        """
        Использует OrderFactory для создания SELL-ордера, затем сохраняет ордер в репозитории.
        """
        order = self.order_factory.create_sell_order(price, amount)
        self.save_order(order)
        return order

    def save_order(self, order: Order):
        """
        Сохранение ордера в репозиторий (InMemory, БД, ...).
        """
        self.orders_repo.save(order)

    def place_order(self, order: Order):
        """
        Пример вызова реального биржевого метода, если есть exchange_connector.
        Ставим order.status = 'OPEN' и сохраняем.
        """
        if self.exchange_connector:
            # Пример асинхронного вызова (ccxt обычно sync, но можно через to_thread).
            # response = await self.exchange_connector.create_order(
            #     symbol="BTC/USDT",  # ... или order.symbol, если есть
            #     side=order.side.lower(),  # 'buy' / 'sell'
            #     order_type=order.order_type.lower(), # 'limit' / 'market'
            #     amount=order.amount,
            #     price=order.price
            # )
            # # обновить order.e_id = response['id'] и т.п.
            pass

        order.status = Order.STATUS_OPEN
        self.save_order(order)

    def cancel_order(self, order: Order):
        """
        Отмена ордера: ставим статус CANCELED, вызываем exchange_connector.
        """
        if order.is_open():
            if self.exchange_connector:
                # await self.exchange_connector.cancel_order(order_id=..., symbol=...)
                pass

            order.cancel()
            self.save_order(order)

    def close_order(self, order: Order):
        """
        Ставим статус CLOSED, например, если ордер исполнен.
        """
        if not order.is_closed():
            order.close()
            self.save_order(order)

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        return self.orders_repo.get_by_id(order_id)

    def get_orders_by_deal(self, deal_id: int):
        return self.orders_repo.get_all_by_deal(deal_id)
