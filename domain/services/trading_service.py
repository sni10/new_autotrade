# domain/services/trading_service.py
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import DealsRepository
from domain.services.order_service import OrderService
from typing import Optional

class TradingService:
    """
    Основной сервис для управления сделками (Deal):
    - Создание новой сделки (create_new_deal),
    - Обновление статусов (process_open_deals),
    - Закрытие/отмена сделок (close_deal, cancel_deal),
    - Связь с OrderService для работы с ордерами.
    """

    def __init__(
        self,
        deals_repo: DealsRepository,
        order_service: OrderService,
        deal_factory: DealFactory
    ):
        self.deals_repo = deals_repo
        self.order_service = order_service
        self.deal_factory = deal_factory

    def create_new_deal(self, currency_pair: CurrencyPair) -> Deal:
        """
        Создаём сделку (Deal) через фабрику, сохраняем,
        а также сохраняем buy/sell ордера в OrdersRepository через order_service.
        """
        deal = self.deal_factory.create_new_deal(currency_pair)
        self.deals_repo.save(deal)

        if deal.buy_order:
            self.order_service.save_order(deal.buy_order)
        if deal.sell_order:
            self.order_service.save_order(deal.sell_order)

        print(f"[TradingService] Created new deal: {deal}")
        return deal

    def process_open_deals(self):
        """
        Логика проверки всех открытых сделок:
        - можно смотреть, не пора ли закрывать,
        - проверять жизнь buy_order/sell_order и т.д.
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            # например, если сделка открыта слишком давно => cancel_deal(deal)
            # или если buy_order исполнен => place_sell_order(...)
            pass

    def close_deal(self, deal: Deal):
        """
        Принудительно закрыть сделку, отменить ордера и сохранить изменения.
        """
        if deal.is_open():
            # Отменяем buy/sell, если они ещё OPEN
            if deal.buy_order and deal.buy_order.is_open():
                self.order_service.cancel_order(deal.buy_order)
            if deal.sell_order and deal.sell_order.is_open():
                self.order_service.cancel_order(deal.sell_order)

            # Закрываем саму сделку
            deal.close()
            self.deals_repo.save(deal)
            print(f"[TradingService] Closed deal: {deal}")

    def cancel_deal(self, deal: Deal):
        """
        Пометить сделку как CANCELED (отменённую).
        """
        if deal.is_open():
            if deal.buy_order and deal.buy_order.is_open():
                self.order_service.cancel_order(deal.buy_order)
            if deal.sell_order and deal.sell_order.is_open():
                self.order_service.cancel_order(deal.sell_order)

            deal.cancel()
            self.deals_repo.save(deal)
            print(f"[TradingService] Canceled deal: {deal}")

    def force_close_all(self):
        """
        Утилитарный метод: закрыть все открытые сделки.
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            self.close_deal(deal)
