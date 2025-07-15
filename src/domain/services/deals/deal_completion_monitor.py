# src/domain/services/deals/deal_completion_monitor.py
import asyncio
import logging
from typing import List

from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from domain.entities.deal import Deal
from domain.entities.order import Order

logger = logging.getLogger(__name__)

class DealCompletionMonitor:
    """
    Сервис для мониторинга завершения сделок.
    Проверяет, исполнены ли оба ордера (BUY и SELL) в рамках открытой сделки,
    логирует их статус и закрывает сделку в случае полного исполнения.
    """

    def __init__(self, deal_service: DealService, order_service: OrderService, check_interval_seconds: int = 30):
        self.deal_service = deal_service
        self.order_service = order_service
        self.check_interval_seconds = check_interval_seconds
        self.stats = {
            "checks_performed": 0,
            "deals_monitored": 0,
            "deals_completed": 0,
        }
        self._is_running = False

    async def start_monitoring(self):
        """Запускает мониторинг в фоновом режиме."""
        self._is_running = True
        logger.info(f"🚀 DealCompletionMonitor запущен (проверка каждые {self.check_interval_seconds}с)")
        while self._is_running:
            await self.check_deals_completion()
            await asyncio.sleep(self.check_interval_seconds)

    def stop_monitoring(self):
        """Останавливает мониторинг."""
        self._is_running = False
        logger.info("🔴 DealCompletionMonitor остановлен.")

    async def check_deals_completion(self):
        """
        Основной метод, проверяющий все открытые сделки на предмет завершения.
        """
        self.stats["checks_performed"] += 1
        open_deals = self.deal_service.get_open_deals()
        self.stats["deals_monitored"] = len(open_deals)

        if not open_deals:
            return

        logger.debug(f"Мониторинг завершения {len(open_deals)} открытых сделок...")

        for deal in open_deals:
            try:
                await self._check_single_deal(deal)
            except Exception as e:
                logger.error(f"Ошибка при проверке сделки {deal.deal_id}: {e}", exc_info=True)

    async def _check_single_deal(self, deal: Deal):
        """Проверяет и обрабатывает одну сделку."""
        buy_order = self.order_service.get_order_by_id(deal.buy_order.order_id)
        sell_order = self.order_service.get_order_by_id(deal.sell_order.order_id)

        if not buy_order or not sell_order:
            logger.warning(f"Не найден один из ордеров для сделки {deal.deal_id}. Пропускаем.")
            return

        # Логируем текущий статус ордеров в сделке
        logger.info(
            f"DEAL_STATUS | DealID: {deal.deal_id} | "
            f"BUY: {buy_order.order_id} [{buy_order.status}, {buy_order.get_fill_percentage():.0%}] | "
            f"SELL: {sell_order.order_id} [{sell_order.status}, {sell_order.get_fill_percentage():.0%}]"
        )

        # Условие для закрытия сделки: оба ордера полностью исполнены
        if buy_order.is_filled() and sell_order.is_filled():
            logger.info(f"🎉 Сделка {deal.deal_id} полностью исполнена! Закрываем...")
            self.deal_service.close_deal(deal.deal_id)
            self.stats["deals_completed"] += 1
            logger.info(f"✅ Сделка {deal.deal_id} успешно закрыта.")

    def get_statistics(self) -> dict:
        """Возвращает статистику работы монитора."""
        return self.stats
