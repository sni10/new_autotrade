# domain/services/deal_service.py

from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import DealsRepository
from domain.services.order_service import OrderService
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DealService:
    """
    Сервис для управления сделками:
    - Создание сделок через DealFactory,
    - Обновление и управление статусами сделок,
    - Взаимодействие с OrderService для управления ордерами.
    """

    def __init__(self, deals_repo: DealsRepository, order_service: OrderService, deal_factory: DealFactory):
        self.deals_repo = deals_repo
        self.order_service = order_service
        self.deal_factory = deal_factory

    def create_new_deal(self, currency_pair: CurrencyPair) -> Deal:
        """
        Создает новую сделку для указанной валютной пары.
        """
        deal = self.deal_factory.create_new_deal(currency_pair)
        self.deals_repo.save(deal)
        logger.info(f"Created new deal: {deal}")
        return deal

    def open_buy_order(self, price, amount, deal_id):
        """
        Проверяет и обрабатывает все открытые сделки.
        """
        buy_order = self.order_service.create_buy_order(
            price, amount
        )
        buy_order.deal_id = deal_id
        logger.info(f"Create BUY Order: {buy_order}")
        return buy_order


    def open_sell_order(self, price, amount, deal_id):
        """
        Проверяет и обрабатывает все открытые сделки.
        """
        sell_order = self.order_service.create_sell_order(
            price, amount
        )
        sell_order.deal_id = deal_id
        logger.info(f"Create SELL Order: {sell_order}")
        return sell_order

    def process_open_deals(self):
        """
        Проверяет и обрабатывает все открытые сделки.
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            if self.should_close_deal(deal):
                self.close_deal(deal)

    def close_deal(self, deal: Deal):
        """
        Закрывает сделку и связанные с ней ордера.
        """
        if deal.buy_order and deal.buy_order.is_open():
            self.order_service.cancel_order(deal.buy_order)
        if deal.sell_order and deal.sell_order.is_open():
            self.order_service.cancel_order(deal.sell_order)

        deal.close()
        self.deals_repo.save(deal)
        logger.info(f"Closed deal: {deal}")

    def should_close_deal(self, deal: Deal) -> bool:
        """
        Определяет, нужно ли закрывать сделку на основе бизнес-логики.
        """
        # Здесь может быть сложная логика с проверкой условий: времени, цен, индикаторов и т.п.
        return False  # Пример: возвращаем False, не закрываем автоматически

    def get_open_deals(self) -> List[Deal]:
        """
        Возвращает список всех открытых сделок.
        """
        return self.deals_repo.get_open_deals()

    def get_deal_by_id(self, deal_id: int) -> Optional[Deal]:
        """
        Возвращает сделку по идентификатору.
        """
        return self.deals_repo.get_by_id(deal_id)

    def force_close_all(self):
        """
        Принудительное закрытие всех открытых сделок.
        """
        for deal in self.get_open_deals():
            self.close_deal(deal)
