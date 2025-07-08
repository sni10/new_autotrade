# domain/services/order_service.py
import asyncio
from typing import Optional, Dict
from domain.entities.order import Order
from domain.factories.order_factory import OrderFactory
from infrastructure.repositories.orders_repository import OrdersRepository

class OrderService:
    """
    📋 Активный сервис для работы с ордерами:
    - Создание и размещение ордеров на бирже
    - Отслеживание статусов ордеров
    - Отмена и управление ордерами
    """

    def __init__(
        self,
        orders_repo: OrdersRepository,
        order_factory: OrderFactory,
        exchange_connector=None  # Коннектор к бирже для реальных операций
    ):
        self.orders_repo = orders_repo
        self.order_factory = order_factory
        self.exchange_connector = exchange_connector

    async def create_and_place_buy_order(
        self,
        price: float,
        amount: float,
        deal_id: int,
        symbol: str
    ) -> Order:
        """
        🛒 Создает и размещает BUY ордер на бирже
        """
        # 1. Создаем ордер через фабрику
        order = self.order_factory.create_buy_order(price, amount)
        order.deal_id = deal_id
        order.symbol = symbol

        # 2. Сохраняем в репозиторий
        self.orders_repo.save(order)

        # 3. Размещаем на бирже (если есть коннектор)
        if self.exchange_connector:
            try:
                # TODO: Реальное размещение через ccxt
                # exchange_response = await self.exchange_connector.create_order(
                #     symbol=symbol,
                #     side='buy',
                #     type='limit',
                #     amount=amount,
                #     price=price
                # )
                # order.exchange_id = exchange_response['id']

                # Пока эмулируем успешное размещение
                order.status = Order.STATUS_OPEN
                print(f"🛒 BUY ордер #{order.order_id} размещен на бирже (эмуляция)")

            except Exception as e:
                order.status = Order.STATUS_FAILED
                print(f"❌ Ошибка размещения BUY ордера: {e}")
        else:
            # Без коннектора - только локальное создание
            order.status = Order.STATUS_PENDING
            print(f"🛒 BUY ордер #{order.order_id} создан локально")

        # 4. Обновляем статус в репозитории
        self.orders_repo.save(order)
        return order

    async def create_and_place_sell_order(
        self,
        price: float,
        amount: float,
        deal_id: int,
        symbol: str
    ) -> Order:
        """
        🏷️ Создает и размещает SELL ордер на бирже
        """
        # 1. Создаем ордер через фабрику
        order = self.order_factory.create_sell_order(price, amount)
        order.deal_id = deal_id
        order.symbol = symbol

        # 2. Сохраняем в репозиторий
        self.orders_repo.save(order)

        # 3. Размещаем на бирже (если есть коннектор)
        if self.exchange_connector:
            try:
                # TODO: Реальное размещение через ccxt
                # exchange_response = await self.exchange_connector.create_order(
                #     symbol=symbol,
                #     side='sell',
                #     type='limit',
                #     amount=amount,
                #     price=price
                # )
                # order.exchange_id = exchange_response['id']

                # Пока эмулируем успешное размещение
                order.status = Order.STATUS_OPEN
                print(f"🏷️ SELL ордер #{order.order_id} размещен на бирже (эмуляция)")

            except Exception as e:
                order.status = Order.STATUS_FAILED
                print(f"❌ Ошибка размещения SELL ордера: {e}")
        else:
            # Без коннектора - только локальное создание
            order.status = Order.STATUS_PENDING
            print(f"🏷️ SELL ордер #{order.order_id} создан локально")

        # 4. Обновляем статус в репозитории
        self.orders_repo.save(order)
        return order

    def get_order_status(self, order: Order) -> Optional[Order]:
        """
        📊 Получает актуальный статус ордера с биржи
        """
        if not order.exchange_id or not self.exchange_connector:
            # Без биржевого ID или коннектора возвращаем как есть
            return order

        try:
            # TODO: Реальная проверка статуса через ccxt
            # exchange_order = await self.exchange_connector.fetch_order(
            #     order.exchange_id,
            #     order.symbol
            # )
            #
            # # Обновляем статус на основе ответа биржи
            # if exchange_order['status'] == 'closed':
            #     order.status = Order.STATUS_FILLED
            # elif exchange_order['status'] == 'canceled':
            #     order.status = Order.STATUS_CANCELED

            # Пока эмулируем проверку статуса
            print(f"📊 Проверен статус ордера #{order.order_id}: {order.status}")

        except Exception as e:
            print(f"⚠️ Ошибка проверки статуса ордера #{order.order_id}: {e}")

        return order

    async def cancel_order(self, order: Order) -> bool:
        """
        ❌ Отменяет ордер на бирже
        """
        if not order.is_open():
            print(f"⚠️ Ордер #{order.order_id} уже не активен")
            return False

        try:
            # Отменяем на бирже (если есть коннектор)
            if self.exchange_connector and order.exchange_id:
                # TODO: Реальная отмена через ccxt
                # await self.exchange_connector.cancel_order(
                #     order.exchange_id,
                #     order.symbol
                # )
                print(f"❌ Ордер #{order.order_id} отменен на бирже (эмуляция)")

            # Обновляем статус локально
            order.cancel()
            self.orders_repo.save(order)
            print(f"❌ Ордер #{order.order_id} отменен")
            return True

        except Exception as e:
            print(f"❌ Ошибка отмены ордера #{order.order_id}: {e}")
            return False

    def get_orders_by_deal(self, deal_id: int):
        """
        📋 Получает все ордера по ID сделки
        """
        return self.orders_repo.get_all_by_deal(deal_id)

    def get_open_orders(self):
        """
        📋 Получает все открытые ордера
        """
        all_orders = self.orders_repo.get_all()
        return [order for order in all_orders if order.is_open()]

    # Оставляем старые методы для совместимости
    def create_buy_order(self, price: float, amount: float) -> Order:
        """Создает BUY ордер (старый метод для совместимости)"""
        return self.order_factory.create_buy_order(price, amount)

    def create_sell_order(self, price: float, amount: float) -> Order:
        """Создает SELL ордер (старый метод для совместимости)"""
        return self.order_factory.create_sell_order(price, amount)

    def save_order(self, order: Order):
        """Сохраняет ордер в репозиторий (старый метод для совместимости)"""
        self.orders_repo.save(order)
