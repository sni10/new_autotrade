# domain/services/trading_service.py
from typing import Dict, Optional
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.factories.deal_factory import DealFactory
from infrastructure.repositories.deals_repository import DealsRepository
from domain.services.orders.order_service import OrderService
import logging

logger = logging.getLogger(__name__)

class TradingService:
    """
    🎯 Главный сервис для управления торговыми операциями (TradingOrchestrator):
    - Координирует создание сделок и ордеров
    - Управляет жизненным циклом торговых операций
    - Связывает все торговые сервисы воедино

    Переписанный с учетом архитектурных принципов оркестратора.
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

    async def execute_buy_strategy(
        self,
        currency_pair: CurrencyPair,
        strategy_result: tuple
    ) -> Deal:
        """
        🛒 Исполняет стратегию покупки:
        1. Создает новую сделку
        2. Создает buy/sell ордера через OrderService
        3. Привязывает ордера к сделке
        """
        # Распаковываем результат калькулятора
        buy_price_calc, total_coins_needed, sell_price_calc, coins_to_sell, info_dict = strategy_result

        # 1. Создаем новую сделку
        new_deal = self.deal_factory.create_new_deal(currency_pair)
        self.deals_repo.save(new_deal)

        # 2. Создаем BUY ордер через OrderService
        buy_order = await self.order_service.create_and_place_buy_order(
            price=float(buy_price_calc),
            amount=float(total_coins_needed),
            deal_id=new_deal.deal_id,
            symbol=currency_pair.symbol
        )

        # 3. Создаем SELL ордер через OrderService
        sell_order = await self.order_service.create_and_place_sell_order(
            price=float(sell_price_calc),
            amount=float(coins_to_sell),
            deal_id=new_deal.deal_id,
            symbol=currency_pair.symbol
        )

        # 4. Привязываем ордера к сделке
        new_deal.attach_orders(buy_order, sell_order)
        self.deals_repo.save(new_deal)

        logger.info(f"\n🆕 Создана сделка #{new_deal.deal_id}")
        logger.info(f"   🛒 BUY: {buy_order}")
        logger.info(f"   🏷️ SELL: {sell_order}")

        return new_deal

    def process_open_deals(self):
        """
        📊 Обработка всех открытых сделок:
        - Проверка статусов ордеров
        - Закрытие завершенных сделок
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            # Проверяем статусы ордеров через OrderService
            if deal.buy_order:
                updated_buy_order = self.order_service.get_order_status(deal.buy_order)
                if updated_buy_order and updated_buy_order.is_filled():
                    logger.info(
                        f"✅ BUY ордер #{deal.buy_order.order_id} исполнен"
                    )

            if deal.sell_order:
                updated_sell_order = self.order_service.get_order_status(deal.sell_order)
                if updated_sell_order and updated_sell_order.is_filled():
                    logger.info(
                        f"✅ SELL ордер #{deal.sell_order.order_id} исполнен"
                    )
                    self.close_deal(deal)

    def close_deal(self, deal: Deal):
        """
        🔒 Закрытие сделки с отменой незавершенных ордеров
        """
        if deal.is_open():
            # Отменяем открытые ордера через OrderService
            if deal.buy_order and deal.buy_order.is_open():
                self.order_service.cancel_order(deal.buy_order)
            if deal.sell_order and deal.sell_order.is_open():
                self.order_service.cancel_order(deal.sell_order)

            # Закрываем саму сделку
            deal.close()
            self.deals_repo.save(deal)
            logger.info(f"🔒 Закрыта сделка #{deal.deal_id}")

    def cancel_deal(self, deal: Deal):
        """
        ❌ Отменяет сделку и все связанные ордера
        """
        if deal.is_open():
            if deal.buy_order and deal.buy_order.is_open():
                self.order_service.cancel_order(deal.buy_order)
            if deal.sell_order and deal.sell_order.is_open():
                self.order_service.cancel_order(deal.sell_order)

            deal.cancel()
            self.deals_repo.save(deal)
            logger.warning(f"❌ Отменена сделка #{deal.deal_id}")

    def force_close_all_deals(self):
        """
        🚨 Экстренное закрытие всех открытых сделок
        """
        open_deals = self.deals_repo.get_open_deals()
        for deal in open_deals:
            self.close_deal(deal)
        logger.warning(f"🚨 Принудительно закрыто {len(open_deals)} сделок")

    def get_trading_statistics(self) -> Dict:
        """
        📈 Получение статистики торговли
        """
        open_deals = self.deals_repo.get_open_deals()
        all_deals = self.deals_repo.get_all()

        return {
            "open_deals_count": len(open_deals),
            "total_deals_count": len(all_deals),
            "can_create_new_deal": len(open_deals) < 10  # Примерный лимит
        }

    # === СТАРЫЕ МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ ===

    def create_new_deal(self, currency_pair: CurrencyPair) -> Deal:
        """
        Создаём сделку (совместимость со старым API)
        """
        deal = self.deal_factory.create_new_deal(currency_pair)
        self.deals_repo.save(deal)
        logger.info(f"[TradingService] Created new deal: {deal}")
        return deal

    def force_close_all(self):
        """
        Утилитарный метод: закрыть все открытые сделки (совместимость)
        """
        self.force_close_all_deals()
