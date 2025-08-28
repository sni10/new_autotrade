# src/domain/services/deals/deal_completion_monitor.py
import asyncio
import logging
import time
from typing import List

from domain.services.deals.deal_service import DealService
from domain.services.orders.order_service import OrderService
from domain.entities.deal import Deal
from domain.entities.order import Order
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

logger = logging.getLogger(__name__)

class DealCompletionMonitor:
    """
    Сервис для мониторинга завершения сделок.
    Проверяет, исполнены ли оба ордера (BUY и SELL) в рамках открытой сделки,
    логирует их статус и закрывает сделку в случае полного исполнения.
    """

    def __init__(self, deal_service: DealService, order_service: OrderService, exchange_connector: CcxtExchangeConnector, check_interval_seconds: int = 30, grace_period_seconds: int = 60):
        self.deal_service = deal_service
        self.order_service = order_service
        self.exchange_connector = exchange_connector
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
            
            # Выбираем наиболее релевантные ордера по весу статуса и свежести
            def _status_weight(o: Order) -> int:
                s = o._status_upper() if hasattr(o, '_status_upper') else str(getattr(o, 'status', '')).upper()
                if s in [Order.STATUS_FILLED, Order.STATUS_CLOSED]:
                    return 100
                if s == Order.STATUS_PARTIALLY_FILLED:
                    return 80
                if s == Order.STATUS_OPEN:
                    return 60
                if s == Order.STATUS_PENDING:
                    return 40
                if s in [Order.STATUS_CANCELED, Order.STATUS_FAILED, Order.STATUS_NOT_FOUND_ON_EXCHANGE]:
                    return 0
                return 10

            def _recency(o: Order) -> int:
                return int(getattr(o, 'last_update', getattr(o, 'created_at', 0)) or 0)

            buy_orders_sorted = sorted(buy_orders, key=lambda o: (_status_weight(o), _recency(o)), reverse=True)
            sell_orders_sorted = sorted(sell_orders, key=lambda o: (_status_weight(o), _recency(o)), reverse=True)

            buy_order = buy_orders_sorted[0]
            sell_order = sell_orders_sorted[0]

            if len(buy_orders) > 1 or len(sell_orders) > 1:
                logger.debug(
                    f"Deal {deal.deal_id}: выбраны BUY {buy_order.order_id} [{buy_order.status}] и SELL {sell_order.order_id} [{sell_order.status}] из {len(buy_orders)}/{len(sell_orders)} вариантов"
                )
                try:
                    buy_list = ", ".join([f"{o.order_id}[{o.status}]@{getattr(o, 'price', 'n/a')}" for o in buy_orders_sorted])
                    sell_list = ", ".join([f"{o.order_id}[{o.status}]@{getattr(o, 'price', 'n/a')}" for o in sell_orders_sorted])
                    logger.debug(f"   BUY варианты: {buy_list}")
                    logger.debug(f"   SELL варианты: {sell_list}")
                except Exception:
                    pass
            
            # 🆕 СИНХРОНИЗАЦИЯ: Обновляем ордера с актуальными данными биржи
            # Проверяем возраст buy ордера
            buy_age_seconds = self._get_order_age_seconds(buy_order)
            if buy_age_seconds < self.grace_period_seconds:
                logger.debug(f"⏳ BUY {buy_order.order_id}: пропускаем синхронизацию (возраст {buy_age_seconds:.1f}с < {self.grace_period_seconds}с)")
                updated_buy = buy_order  # Используем текущий статус без обновления
            else:
                # Синхронизируем BUY ордер с биржей
                try:
                    if buy_order.exchange_id:
                        exchange_data = await self.exchange_connector.fetch_order(buy_order.exchange_id, buy_order.symbol)
                        if exchange_data:
                            buy_order.update_from_exchange(exchange_data)
                            self.order_service.orders_repo.update_order(buy_order)
                            self.stats["sync_operations"] += 1
                            logger.debug(f"🔄 BUY ордер {buy_order.order_id} синхронизирован с биржей")
                    updated_buy = buy_order
                except Exception as e:
                    logger.error(f"❌ Ошибка синхронизации BUY ордера {buy_order.order_id}: {e}")
                    # Fallback: используем старый метод
                    updated_buy = await self.order_service.get_order_status(buy_order)
            
            # Проверяем возраст sell ордера (если он есть на бирже)
            if sell_order.exchange_id:
                sell_age_seconds = self._get_order_age_seconds(sell_order)
                if sell_age_seconds < self.grace_period_seconds:
                    logger.debug(f"⏳ SELL {sell_order.order_id}: пропускаем синхронизацию (возраст {sell_age_seconds:.1f}с < {self.grace_period_seconds}с)")
                    updated_sell = sell_order  # Используем текущий статус без обновления
                else:
                    # Синхронизируем SELL ордер с биржей
                    try:
                        exchange_data = await self.exchange_connector.fetch_order(sell_order.exchange_id, sell_order.symbol)
                        if exchange_data:
                            sell_order.update_from_exchange(exchange_data)
                            self.order_service.orders_repo.update_order(sell_order)
                            self.stats["sync_operations"] += 1
                            logger.debug(f"🔄 SELL ордер {sell_order.order_id} синхронизирован с биржей")
                        updated_sell = sell_order
                    except Exception as e:
                        logger.error(f"❌ Ошибка синхронизации SELL ордера {sell_order.order_id}: {e}")
                        # Fallback: используем старый метод
                        updated_sell = await self.order_service.get_order_status(sell_order)
            else:
                updated_sell = sell_order
            
            # Детальная аналитика состояния сделки
            buy_fill = updated_buy.get_fill_percentage() if hasattr(updated_buy, 'get_fill_percentage') else 0.0
            sell_fill = updated_sell.get_fill_percentage() if hasattr(updated_sell, 'get_fill_percentage') else 0.0
            
            logger.info(f"📈 СДЕЛКА {deal.deal_id}: "
                       f"BUY[{updated_buy.status}, {buy_fill:.1%}] | "
                       f"SELL[{updated_sell.status}, {sell_fill:.1%}]")
            
            # ИСПРАВЛЕНИЕ: Улучшенная обработка PENDING SELL ордеров
            if updated_sell.is_pending() and updated_buy.is_filled():
                logger.info(f"🎯 BUY исполнен! Размещаем PENDING SELL ордер {updated_sell.order_id} на бирже...")
                result = await self.order_service.place_existing_order(updated_sell)
                if result.success:
                    logger.info(f"✅ SELL ордер {updated_sell.order_id} размещен на бирже")
                    self.stats["sell_orders_placed"] += 1
                    # Добавляем новую метрику для отслеживания исправленных PENDING ордеров
                    if "pending_orders_fixed" not in self.stats:
                        self.stats["pending_orders_fixed"] = 0
                    self.stats["pending_orders_fixed"] += 1
                else:
                    logger.error(f"❌ Не удалось разместить SELL: {result.error_message}")
                    return
            
            # Завершение сделки при полном исполнении (агрегатная проверка)
            buy_any_filled = any(o.is_filled() for o in buy_orders)
            sell_any_filled = any(o.is_filled() for o in sell_orders)

            # Если SELL уже filled, а BUY по выбранному не filled — сделаем разовую жесткую синхронизацию всех ордеров сделки
            if sell_any_filled and not buy_any_filled:
                try:
                    logger.debug(f"🔄 Форс-синхронизация всех ордеров сделки {deal.deal_id} (SELL filled, BUY нет)")
                    for o in buy_orders + sell_orders:
                        if getattr(o, 'exchange_id', None):
                            try:
                                data = await self.exchange_connector.fetch_order(o.exchange_id, o.symbol)
                                if data:
                                    # Используем update_from_exchange для совместимости
                                    o.update_from_exchange(data)
                                    self.order_service.orders_repo.update_order(o)
                                    self.stats["sync_operations"] += 1
                            except Exception as e:
                                logger.debug(f"   ⚠️ Ошибка форс-синхронизации ордера {o.order_id}: {e}")
                    # Пересчитываем
                    buy_any_filled = any(o.is_filled() for o in buy_orders)
                    sell_any_filled = any(o.is_filled() for o in sell_orders)
                except Exception as e:
                    logger.debug(f"⚠️ Ошибка при форс-синхронизации сделки {deal.deal_id}: {e}")

            if buy_any_filled and sell_any_filled:
                logger.info(f"🎉 СДЕЛКА {deal.deal_id} ЗАВЕРШЕНА!")
                self.deal_service.close_deal(deal.deal_id)
                self.stats["deals_completed"] += 1
                logger.info(f"✅ Сделка {deal.deal_id} успешно закрыта.")
            else:
                # ДИАГНОСТИКА: Логируем причину, почему сделка не завершается
                buy_filled = buy_any_filled
                sell_filled = sell_any_filled
                logger.debug(f"🔍 СДЕЛКА {deal.deal_id} НЕ ЗАВЕРШЕНА: "
                           f"BUY заполнен: {buy_filled}, SELL заполнен: {sell_filled}")
                
                # Дополнительная информация о статусах
                if not buy_filled:
                    logger.debug(f"   BUY ордера: {[f'{o.order_id}:{o.status}' for o in buy_orders]}")
                if not sell_filled:
                    logger.debug(f"   SELL ордера: {[f'{o.order_id}:{o.status}' for o in sell_orders]}")
                
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
