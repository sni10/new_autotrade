# src/domain/services/orders/filled_buy_order_handler.py
import asyncio
import logging
from typing import List

from domain.entities.order import Order
from domain.services.orders.unified_order_service import UnifiedOrderService
from domain.services.deals.deal_service import DealService

logger = logging.getLogger(__name__)

class FilledBuyOrderHandler:
    """
    Сервис, который отслеживает исполненные BUY ордера и размещает
    соответствующие им PENDING SELL ордера на биржу.
    """

    def __init__(self, order_service: 'UnifiedOrderService', deal_service: DealService):
        self.order_service = order_service
        self.deal_service = deal_service
        self.processed_buy_orders = set()

    async def check_and_place_sell_orders(self):
        """
        Основной метод, который ищет исполненные BUY ордера и размещает
        связанные с ними SELL ордера.
        """
        try:
            all_orders = self.order_service.orders_repo.get_all()
            filled_buy_orders = [
                order for order in all_orders
                if order.side == Order.SIDE_BUY
                and order.is_filled()
                and order.order_id not in self.processed_buy_orders
            ]

            if not filled_buy_orders:
                return

            logger.info(f"Обнаружено {len(filled_buy_orders)} новых исполненных BUY ордеров. Обработка...")

            for buy_order in filled_buy_orders:
                await self._process_filled_buy_order(buy_order)

        except Exception as e:
            logger.error(f"Ошибка в FilledBuyOrderHandler: {e}", exc_info=True)

    async def _process_filled_buy_order(self, buy_order: Order):
        """Обрабатывает один исполненный BUY ордер."""
        try:
            deal = self.deal_service.get_deal_by_id(buy_order.deal_id)
            if not deal:
                logger.warning(f"Не найдена сделка для исполненного BUY ордера {buy_order.order_id}")
                self.processed_buy_orders.add(buy_order.order_id)
                return

            # Ищем связанный PENDING SELL ордер
            sell_order = self.order_service.get_order_by_id(deal.sell_order.order_id)
            
            if not sell_order or not sell_order.is_pending():
                logger.warning(f"Не найден PENDING SELL ордер для сделки {deal.deal_id}. Возможно, уже размещен.")
                self.processed_buy_orders.add(buy_order.order_id)
                return

            logger.info(f"Найден PENDING SELL ордер {sell_order.order_id} для сделки {deal.deal_id}. Размещаем на бирже...")

            # Размещаем SELL ордер на бирже
            execution_result = await self.order_service.place_existing_order(sell_order)

            if execution_result.success:
                logger.info(f"SELL ордер {sell_order.order_id} успешно размещен на бирже. Exchange ID: {execution_result.order.exchange_id}")
            else:
                logger.error(f"Не удалось разместить SELL ордер {sell_order.order_id}: {execution_result.error_message}")

            # Помечаем BUY ордер как обработанный, чтобы не трогать его снова
            self.processed_buy_orders.add(buy_order.order_id)

        except Exception as e:
            logger.error(f"Ошибка при обработке исполненного BUY ордера {buy_order.order_id}: {e}", exc_info=True)
            # Не добавляем в processed, чтобы повторить попытку
