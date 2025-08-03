# src/domain/services/deals/deal_completion_monitor.py
import asyncio
import logging
import time
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

    def __init__(self, deal_service: DealService, order_service: OrderService, check_interval_seconds: int = 30, grace_period_seconds: int = 60):
        self.deal_service = deal_service
        self.order_service = order_service
        self.check_interval_seconds = check_interval_seconds
        self.grace_period_seconds = grace_period_seconds
        self.stats = {
            "checks_performed": 0,
            "deals_monitored": 0,
            "deals_completed": 0,
            "sell_orders_placed": 0,
            "sync_operations": 0,
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
        
        # ИСПРАВЛЕНИЕ: deals_monitored должно показывать текущее количество открытых сделок
        # Добавляем отдельный счетчик для общего количества обработанных сделок
        current_open_deals = len(open_deals)
        self.stats["deals_monitored"] = current_open_deals
        
        # Обновляем максимальное количество одновременно отслеживаемых сделок
        if "max_deals_monitored" not in self.stats:
            self.stats["max_deals_monitored"] = 0
        self.stats["max_deals_monitored"] = max(self.stats["max_deals_monitored"], current_open_deals)

        if not open_deals:
            return

        logger.debug(f"Мониторинг завершения {len(open_deals)} открытых сделок...")

        for deal in open_deals:
            try:
                await self._check_single_deal(deal)
            except Exception as e:
                logger.error(f"Ошибка при проверке сделки {deal.deal_id}: {e}", exc_info=True)

    async def _check_single_deal(self, deal: Deal):
        """Активная проверка и обработка одной сделки с синхронизацией биржи"""
        try:
            # Получаем все ордера для данной сделки
            deal_orders = self.order_service.orders_repo.get_orders_by_deal(deal.deal_id)
            
            if not deal_orders:
                logger.warning(f"Сделка {deal.deal_id} не имеет связанных ордеров в репозитории. Пропускаем.")
                return
            
            # Разделяем ордера на BUY и SELL
            buy_orders = [order for order in deal_orders if order.side.upper() == 'BUY']
            sell_orders = [order for order in deal_orders if order.side.upper() == 'SELL']
            
            if not buy_orders or not sell_orders:
                logger.debug(f"Сделка {deal.deal_id}: BUY ордеров: {len(buy_orders)}, SELL ордеров: {len(sell_orders)}. Ожидаем оба типа.")
                return
            
            # Берем первые ордера каждого типа (обычно должен быть только один)
            buy_order = buy_orders[0]
            sell_order = sell_orders[0]
            
            # КРИТИЧНО: Обновляем статусы с биржи ПЕРЕД проверкой, но с учетом grace period
            # Проверяем возраст buy ордера
            buy_age_seconds = self._get_order_age_seconds(buy_order)
            if buy_age_seconds < self.grace_period_seconds:
                logger.debug(f"⏳ BUY {buy_order.order_id}: пропускаем проверку статуса (возраст {buy_age_seconds:.1f}с < {self.grace_period_seconds}с)")
                updated_buy = buy_order  # Используем текущий статус без обновления
            else:
                updated_buy = await self.order_service.get_order_status(buy_order)
            
            # Проверяем возраст sell ордера (если он есть на бирже)
            if sell_order.exchange_id:
                sell_age_seconds = self._get_order_age_seconds(sell_order)
                if sell_age_seconds < self.grace_period_seconds:
                    logger.debug(f"⏳ SELL {sell_order.order_id}: пропускаем проверку статуса (возраст {sell_age_seconds:.1f}с < {self.grace_period_seconds}с)")
                    updated_sell = sell_order  # Используем текущий статус без обновления
                else:
                    updated_sell = await self.order_service.get_order_status(sell_order)
            else:
                updated_sell = sell_order
            
            # Детальная аналитика состояния сделки
            buy_fill = updated_buy.get_fill_percentage() if hasattr(updated_buy, 'get_fill_percentage') else 0.0
            sell_fill = updated_sell.get_fill_percentage() if hasattr(updated_sell, 'get_fill_percentage') else 0.0
            
            logger.info(f"📈 СДЕЛКА {deal.deal_id}: "
                       f"BUY[{updated_buy.status}, {buy_fill:.1%}] | "
                       f"SELL[{updated_sell.status}, {sell_fill:.1%}]")
            
            # АКТИВНЫЕ ДЕЙСТВИЯ: Размещаем SELL ордер когда BUY исполнен
            if updated_buy.is_filled() and updated_sell.status == 'PENDING':
                logger.info(f"🎯 BUY исполнен! Размещаем SELL ордер на бирже...")
                result = await self.order_service.place_existing_order(updated_sell)
                if result.success:
                    logger.info(f"✅ SELL ордер {updated_sell.order_id} размещен на бирже")
                    # ИСПРАВЛЕНИЕ: Прямое увеличение счетчика без .get()
                    self.stats["sell_orders_placed"] += 1
                else:
                    logger.error(f"❌ Не удалось разместить SELL: {result.error_message}")
            
            # Завершение сделки при полном исполнении
            if updated_buy.is_filled() and updated_sell.is_filled():
                logger.info(f"🎉 СДЕЛКА {deal.deal_id} ЗАВЕРШЕНА!")
                self.deal_service.close_deal(deal.deal_id)
                self.stats["deals_completed"] += 1
                logger.info(f"✅ Сделка {deal.deal_id} успешно закрыта.")
            else:
                # ДИАГНОСТИКА: Логируем причину, почему сделка не завершается
                buy_filled = updated_buy.is_filled()
                sell_filled = updated_sell.is_filled()
                logger.debug(f"🔍 СДЕЛКА {deal.deal_id} НЕ ЗАВЕРШЕНА: "
                           f"BUY заполнен: {buy_filled}, SELL заполнен: {sell_filled}")
                
                # Дополнительная информация о статусах
                if not buy_filled:
                    logger.debug(f"   BUY ордер {updated_buy.order_id}: статус={updated_buy.status}, filled={getattr(updated_buy, 'filled', 'N/A')}")
                if not sell_filled:
                    logger.debug(f"   SELL ордер {updated_sell.order_id}: статус={updated_sell.status}, filled={getattr(updated_sell, 'filled', 'N/A')}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке сделки {deal.deal_id}: {e}", exc_info=True)

    def get_statistics(self) -> dict:
        """Возвращает статистику работы монитора."""
        return self.stats

    def _get_order_age_seconds(self, order: Order) -> float:
        """Вычисляет возраст ордера в секундах"""
        try:
            current_time = int(time.time() * 1000)
            
            # Безопасное преобразование created_at к int (миллисекунды)
            if hasattr(order.created_at, 'timestamp'):
                # Если это pandas Timestamp, конвертируем в миллисекунды
                created_at_ms = int(order.created_at.timestamp() * 1000)
            elif isinstance(order.created_at, (int, float)):
                # Если это уже число, используем как есть
                created_at_ms = int(order.created_at)
            else:
                # Fallback: возвращаем 0 (ордер считается новым)
                logger.warning(f"⚠️ Неизвестный тип created_at для ордера {order.order_id}: {type(order.created_at)}")
                return 0.0
            
            age_seconds = (current_time - created_at_ms) / 1000
            return max(0.0, age_seconds)  # Не может быть отрицательным
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления возраста ордера {order.order_id}: {e}")
            return 0.0
