# domain/services/buy_order_monitor.py.new
import asyncio
import logging
import time
from typing import List, Optional
from domain.entities.order import Order
from domain.services.orders.order_service import OrderService
from domain.services.deals.deal_service import DealService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

logger = logging.getLogger(__name__)

class BuyOrderMonitor:
    """
    🕒 Простой мониторинг протухших BUY ордеров
    
    Проверяет только BUY ордера на:
    - Время жизни (по умолчанию 15 минут)
    - Отклонение цены от рынка (по умолчанию 3%)
    
    При превышении лимитов - отменяет и пересоздает ордер по новой цене
    """

    def __init__(
        self,
        order_service: OrderService,
        deal_service: DealService, # ❗️ ДОБАВЛЕНО
        exchange_connector: CcxtExchangeConnector,
        max_age_minutes: float = 15.0,
        max_price_deviation_percent: float = 3.0,
        check_interval_seconds: int = 60
    ):
        self.order_service = order_service
        self.deal_service = deal_service # ❗️ ДОБАВЛЕНО
        self.exchange = exchange_connector
        self.max_age_minutes = max_age_minutes
        self.max_price_deviation_percent = max_price_deviation_percent
        self.check_interval_seconds = check_interval_seconds
        
        self.running = False
        self.stats = {
            'checks_performed': 0,
            'stale_orders_found': 0,
            'orders_cancelled': 0,
            'orders_recreated': 0
        }

    async def start_monitoring(self):
        """Запуск мониторинга в фоне"""
        if self.running:
            logger.warning("⚠️ BuyOrderMonitor already running")
            return
            
        self.running = True
        logger.info(f"🕒 Запуск мониторинга BUY ордеров (проверка каждые {self.check_interval_seconds}с)")
        
        while self.running:
            try:
                await self.check_stale_buy_orders()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"❌ Ошибка в мониторинге BUY ордеров: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке

    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("🔴 Мониторинг BUY ордеров остановлен")

    async def check_stale_buy_orders(self):
        """Проверка всех открытых BUY ордеров на протухание"""
        try:
            # Получаем все открытые ордера
            open_orders = self.order_service.get_open_orders()
            
            # Фильтруем только BUY ордера
            buy_orders = [order for order in open_orders if order.side == Order.SIDE_BUY]
            
            if not buy_orders:
                return
                
            self.stats['checks_performed'] += 1
            
            logger.debug(f"🔍 Проверяем {len(buy_orders)} открытых BUY ордеров")
            
            for order in buy_orders:
                is_stale = await self._is_order_stale(order)
                if is_stale:
                    await self._handle_stale_buy_order(order)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка проверки BUY ордеров: {e}")

    async def _is_order_stale(self, order: Order) -> bool:
        """Проверяет протух ли BUY ордер"""
        try:
            # 1. Проверка возраста
            current_time = int(time.time() * 1000)
            age_minutes = (current_time - order.created_at) / 1000 / 60
            
            if age_minutes > self.max_age_minutes:
                logger.info(f"🕒 BUY ордер {order.order_id} протух по времени: {age_minutes:.1f} мин")
                return True
            
            # 2. Проверка отклонения цены
            ticker = await self.exchange.fetch_ticker(order.symbol)
            current_price = float(ticker['last'])
            
            # Для BUY: если рынок ушел выше нашей цены
            price_deviation = ((current_price - order.price) / order.price) * 100
            
            if price_deviation > self.max_price_deviation_percent:
                logger.info(f"📈 BUY ордер {order.order_id} протух по цене: рынок {current_price}, ордер {order.price} (+{price_deviation:.1f}%)")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки ордера {order.order_id}: {e}")
            return False

    async def _handle_stale_buy_order(self, order: Order):
        """Обработка протухшего BUY ордера: отмена + пересоздание + обновление связанного SELL."""
        try:
            self.stats['stale_orders_found'] += 1
            logger.warning(f"🚨 Обрабатываем протухший BUY ордер {order.order_id} для сделки {order.deal_id}")

            # 1. Отменяем старый BUY ордер
            cancel_success = await self.order_service.cancel_order(order)
            if not cancel_success:
                logger.error(f"❌ Не удалось отменить BUY ордер {order.order_id}")
                return
            self.stats['orders_cancelled'] += 1
            logger.info(f"✅ BUY ордер {order.order_id} отменен")

            # 2. Пересоздаем BUY ордер по новой цене
            new_buy_order = await self._recreate_buy_order(order)
            if not new_buy_order:
                logger.error(f"❌ Не удалось пересоздать BUY ордер для сделки {order.deal_id}")
                return
            self.stats['orders_recreated'] += 1
            logger.info(f"✅ BUY ордер пересоздан: {order.order_id} -> {new_buy_order.order_id} (Exchange ID: {new_buy_order.exchange_id})")

            # 3. Обновляем сделку, привязывая к ней новый BUY ордер
            deal = self.deal_service.get_deal_by_id(order.deal_id)
            if not deal:
                logger.error(f"Критическая ошибка: не найдена сделка {order.deal_id} для обновления!")
                return
            
            deal.update_buy_order(new_buy_order)
            self.deal_service.deals_repo.save(deal)
            logger.info(f"✅ Сделка {deal.deal_id} обновлена новым BUY ордером {new_buy_order.order_id}")

            # 4. Находим и обновляем связанный PENDING SELL ордер
            await self._update_related_sell_order(deal, new_buy_order)

        except Exception as e:
            logger.error(f"❌ Ошибка обработки протухшего BUY ордера {order.order_id}: {e}", exc_info=True)

    async def _recreate_buy_order(self, old_order: Order) -> Optional[Order]:
        """Пересоздание BUY ордера по текущей рыночной цене"""
        try:
            ticker = await self.exchange.fetch_ticker(old_order.symbol)
            current_price = float(ticker['last'])
            new_price = current_price * 0.999

            logger.info(f"🔄 Пересоздаем BUY ордер: старая цена {old_order.price}, новая цена {new_price}")

            execution_result = await self.order_service.create_and_place_buy_order(
                symbol=old_order.symbol,
                amount=old_order.amount,
                price=new_price,
                deal_id=old_order.deal_id,
                order_type=old_order.order_type
            )
            
            return execution_result.order if execution_result.success else None
        except Exception as e:
            logger.error(f"❌ Ошибка пересоздания BUY ордера: {e}", exc_info=True)
            return None

    async def _update_related_sell_order(self, deal, new_buy_order: Order):
        """Находит связанный PENDING SELL и обновляет его параметры."""
        try:
            pending_sell = self.order_service.get_order_by_id(deal.sell_order.order_id)
            
            if not pending_sell or not pending_sell.is_pending():
                logger.warning(f"Не найден PENDING SELL для сделки {deal.deal_id}. Нечего обновлять.")
                return

            # Пересчитываем цену и количество для SELL на основе нового BUY
            # (Эта логика должна быть идентична той, что в TickerService/Strategy)
            profit_markup = deal.currency_pair.profit_markup
            new_sell_price = new_buy_order.price * (1 + profit_markup)
            
            # TODO: Пересчет количества, если есть комиссия в базовой валюте
            new_sell_amount = new_buy_order.amount 

            logger.info(f"🔄 Обновляем PENDING SELL ордер {pending_sell.order_id}: цена {pending_sell.price} -> {new_sell_price}, кол-во {pending_sell.amount} -> {new_sell_amount}")

            pending_sell.price = new_sell_price
            pending_sell.amount = new_sell_amount
            
            self.order_service.orders_repo.save(pending_sell)
            logger.info(f"✅ PENDING SELL ордер {pending_sell.order_id} обновлен.")

        except Exception as e:
            logger.error(f"❌ Ошибка обновления связанного SELL ордера для сделки {deal.deal_id}: {e}", exc_info=True)

    def get_statistics(self) -> dict:
        """Получение статистики работы мониторинга"""
        return {
            'running': self.running,
            'max_age_minutes': self.max_age_minutes,
            'max_price_deviation_percent': self.max_price_deviation_percent,
            'check_interval_seconds': self.check_interval_seconds,
            **self.stats
        }

    def configure(
        self,
        max_age_minutes: float = None,
        max_price_deviation_percent: float = None,
        check_interval_seconds: int = None
    ):
        """Изменение настроек мониторинга"""
        if max_age_minutes is not None:
            self.max_age_minutes = max_age_minutes
        if max_price_deviation_percent is not None:
            self.max_price_deviation_percent = max_price_deviation_percent
        if check_interval_seconds is not None:
            self.check_interval_seconds = check_interval_seconds
            
        logger.info(f"⚙️ Настройки мониторинга обновлены: {self.get_statistics()}")
