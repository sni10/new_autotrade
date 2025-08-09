# domain/services/buy_order_monitor.py.new
import asyncio
import logging
import time
from datetime import datetime
from typing import List, Optional, Tuple
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
        check_interval_seconds: int = 60,
        grace_period_seconds: int = 60,  # Период ожидания перед проверкой новых ордеров
        min_time_between_recreations_minutes: float = 0.0
    ):
        self.order_service = order_service
        self.deal_service = deal_service # ❗️ ДОБАВЛЕНО
        self.exchange_connector = exchange_connector
        self.max_age_minutes = max_age_minutes
        self.max_price_deviation_percent = max_price_deviation_percent
        self.check_interval_seconds = check_interval_seconds
        self.grace_period_seconds = grace_period_seconds
        self.min_time_between_recreations_minutes = min_time_between_recreations_minutes
        
        self.running = False
        self.stats = {
            'checks_performed': 0,
            'stale_orders_found': 0,
            'orders_cancelled': 0,
            'orders_recreated': 0
        }
        
        # Улучшенное логирование
        self.quiet_checks_count = 0  # Счетчик "тихих" проверок
        self.last_summary_time = 0   # Время последней сводки
        self.summary_interval_minutes = 5  # Интервал сводки в минутах
        
        # Анти-дерганье: последняя пересозданная метка времени по deal_id
        self._last_recreation_by_deal = {}  # deal_id -> epoch seconds

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
                await asyncio.sleep(30)  # Пауза пр�� ошибке

    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("🔴 Мониторинг BUY ордеров остановлен")

    async def check_stale_buy_orders(self):
        """Активная проверка всех открытых BUY ордеров с синхронизацией биржи"""
        try:
            self.stats['checks_performed'] += 1
            
            # Получаем все открытые ордера
            open_orders = self.order_service.get_open_orders()
            
            # Фильтруем только BUY ордера
            buy_orders = [order for order in open_orders if order.side == Order.SIDE_BUY]
            
            # Умное логирование: детально только при наличии ордеров
            if buy_orders:
                logger.info(f"🔍 МОНИТОРИНГ BUY: проверяем {len(buy_orders)} ордеров")
                self.quiet_checks_count = 0  # Сбрасываем счетчик тихих проверок
            else:
                self.quiet_checks_count += 1
                logger.debug("ℹ️ Нет открытых BUY ордеров для проверки")
                
                # Периодическая сводка вместо постоянного шума
                await self._log_periodic_summary()
                return
            
            for order in buy_orders:
                # 🆕 СИНХРОНИЗАЦИЯ: Обновляем ордер с актуальными данными биржи
                try:
                    # Получаем свежие данные с биржи
                    if order.exchange_id:
                        exchange_data = await self.exchange_connector.fetch_order(order.exchange_id, order.symbol)
                        if exchange_data:
                            # Синхронизируем наш ордер с данными биржи
                            was_updated = order.sync_with_exchange_data(exchange_data)
                            if was_updated:
                                # Сохраняем обновленный ордер
                                self.order_service.orders_repo.update_order(order)
                                logger.debug(f"🔄 Ордер {order.order_id} синхронизирован с биржей")
                    
                    updated_order = order  # Используем синхронизированный ордер
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка синхронизации ордера {order.order_id}: {e}")
                    # Fallback: используем старый метод
                    try:
                        updated_order = await self.order_service.get_order_status(order)
                        if not updated_order:
                            logger.warning(f"⚠️ Не удалось получить статус ордера {order.order_id}")
                            continue
                    except Exception as e2:
                        logger.error(f"❌ Fallback ошибка получения статуса ордера {order.order_id}: {e2}")
                        continue
                
                # Детальное логирование состояния ордера
                age_minutes = self._get_order_age_minutes(updated_order)
                fill_percentage = updated_order.get_fill_percentage() if hasattr(updated_order, 'get_fill_percentage') else 0.0
                
                logger.info(f"📊 BUY {updated_order.order_id}: статус={updated_order.status}, "
                           f"заполнено={fill_percentage:.1%}, возраст={age_minutes:.1f}мин")
                
                # Проверяем на "протухание"
                is_stale, reason = await self._is_order_stale(updated_order)
                if is_stale:
                    logger.warning(f"🚨 ПРОТУХШИЙ BUY ОБНАРУЖЕН: {reason}")
                    await self._handle_stale_buy_order(updated_order)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка проверки BUY ордеров: {e}")

    async def _log_periodic_summary(self):
        """Периодическое логирование сводки вместо постоянного шума"""
        current_time = time.time()
        
        # Проверяем, нужно ли выводить сводку
        if (current_time - self.last_summary_time) >= (self.summary_interval_minutes * 60):
            self.last_summary_time = current_time
            
            # Выводим информативную сводку
            logger.info(f"📊 BUY МОНИТОР СВОДКА: "
                       f"тихих проверок за {self.summary_interval_minutes}мин: {self.quiet_checks_count}, "
                       f"всего проверок: {self.stats['checks_performed']}, "
                       f"найдено тухляков: {self.stats['stale_orders_found']}, "
                       f"пересоздано: {self.stats['orders_recreated']}")
            
            # Сбрасываем счетчик тихих проверок
            self.quiet_checks_count = 0

    def _get_order_age_seconds(self, order: Order) -> float:
        """Вычисляет возраст ордера в секундах, поддерживает int(ms), datetime, str(ISO)."""
        try:
            current_time = int(time.time() * 1000)
            created_at_ms = None

            ca = getattr(order, 'created_at', None)
            if hasattr(ca, 'timestamp'):
                created_at_ms = int(ca.timestamp() * 1000)
            elif isinstance(ca, (int, float)):
                created_at_ms = int(ca)
            elif isinstance(ca, str) and ca:
                try:
                    created_at_ms = int(datetime.fromisoformat(ca).timestamp() * 1000)
                except Exception:
                    created_at_ms = None

            if created_at_ms is None:
                logger.warning(f"⚠️ Неизвестный тип created_at для ордера {order.order_id}: {type(ca)} -> считаем 0с")
                return 0.0

            age_seconds = (current_time - created_at_ms) / 1000.0
            return max(0.0, age_seconds)
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления возраста ордера {order.order_id}: {e}")
            return 0.0

    def _get_order_age_minutes(self, order: Order) -> float:
        """Вычисляет возраст ордера в минутах, поддерживает int(ms), datetime, str(ISO)."""
        try:
            current_time = int(time.time() * 1000)
            created_at_ms = None

            ca = getattr(order, 'created_at', None)
            if hasattr(ca, 'timestamp'):
                created_at_ms = int(ca.timestamp() * 1000)
            elif isinstance(ca, (int, float)):
                created_at_ms = int(ca)
            elif isinstance(ca, str) and ca:
                try:
                    created_at_ms = int(datetime.fromisoformat(ca).timestamp() * 1000)
                except Exception:
                    created_at_ms = None

            if created_at_ms is None:
                logger.warning(f"⚠️ Неизвестный тип created_at для ордера {order.order_id}: {type(ca)} -> считаем 0мин")
                return 0.0

            age_minutes = (current_time - created_at_ms) / 1000.0 / 60.0
            return max(0.0, age_minutes)
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления возраста ордера {order.order_id}: {e}")
            return 0.0

    async def _is_order_stale(self, order: Order) -> Tuple[bool, str]:
        """ИСПРАВЛЕННАЯ проверка протухания BUY ордера с улучшенной логикой"""
        try:
            # 1. Проверка возраста ордера
            age_minutes = self._get_order_age_minutes(order)
            
            # ИСПРАВЛЕНИЕ: Более агрессивная проверка по времени
            if age_minutes > self.max_age_minutes:
                reason = f"ордер {order.order_id} протух по времени: {age_minutes:.1f} мин > {self.max_age_minutes} мин"
                return True, reason
            
            # ИСПРАВЛЕНИЕ: Дополнительная проверка для ордеров с нулевым заполнением
            fill_percentage = order.get_fill_percentage()
            if age_minutes > (self.max_age_minutes * 0.5) and fill_percentage == 0.0:
                reason = f"ордер {order.order_id} протух: {age_minutes:.1f} мин без заполнения (>{self.max_age_minutes * 0.5:.1f} мин)"
                return True, reason
            
            # 2. Проверка отклонения цены от рынка (симметрично, используем best bid из стакана)
            try:
                market_price = None
                try:
                    order_book = await self.exchange_connector.fetch_order_book(order.symbol)
                    if order_book and getattr(order_book, 'bids', None) and len(order_book.bids) > 0:
                        market_price = float(order_book.bids[0][0])
                except Exception:
                    market_price = None
                if market_price is None:
                    ticker = await self.exchange_connector.fetch_ticker(order.symbol)
                    market_price = float(getattr(ticker, 'last', 0.0))

                if order.price and market_price:
                    price_deviation_abs = abs((market_price - float(order.price)) / float(order.price)) * 100.0
                    if price_deviation_abs > self.max_price_deviation_percent and order.get_fill_percentage() == 0.0:
                        direction = 'ниже' if market_price < order.price else 'выше'
                        reason = (f"ордер {order.order_id} протух по цене: рынок {market_price}, ордер {order.price}, "
                                  f"отклонение {price_deviation_abs:.2f}% ({direction})")
                        return True, reason
            except Exception as e:
                logger.warning(f"⚠️ Не удалось проверить цену/стакан для {order.symbol}: {e}")
                # Если не можем получить цену, проверяем только по времени

            return False, ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки ордера {order.order_id}: {e}")
            return False, ""

    async def _handle_stale_buy_order(self, order: Order):
        """Обработка протухшего BUY: throttle + отмена + пересоздание + обновление PENDING SELL"""
        try:
            self.stats['stale_orders_found'] += 1

            # Анти-дерганье по deal_id
            now = time.time()
            last = self._last_recreation_by_deal.get(order.deal_id)
            min_gap = (self.min_time_between_recreations_minutes or 0.0) * 60.0
            if last is not None and (now - last) < min_gap:
                wait_left = min_gap - (now - last)
                logger.info(f"⏳ Пропускаем пересоздание BUY для сделки {order.deal_id}: подождите ещё {wait_left:.1f}с")
                return

            logger.warning(f"🚨 Обрабатываем протухший BUY ордер {order.order_id} (deal {order.deal_id})")

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
                logger.error(f"❌ Не удалось пересоздать BUY ордер")
                return

            self.stats['orders_recreated'] += 1
            logger.info(f"✅ BUY ордер пересоздан: {order.order_id} -> {new_buy_order.order_id}")

            # 3. Обновляем связанный PENDING SELL в рамках той же сделки
            try:
                deal = self.deal_service.get_deal_by_id(order.deal_id)
                profit_markup = 0.0
                if deal and getattr(deal, 'currency_pair', None):
                    profit_markup = float(getattr(deal.currency_pair, 'profit_markup', 0.0) or 0.0)

                # Ищем PENDING SELL ордер по той же сделке
                deal_orders = self.order_service.orders_repo.get_orders_by_deal(order.deal_id)
                pending_sells = [o for o in deal_orders if o.side == Order.SIDE_SELL and o.is_pending()]
                if pending_sells:
                    sell = pending_sells[0]
                    # Пересчитываем цену SELL
                    raw_new_sell_price = float(new_buy_order.price) * (1.0 + profit_markup)
                    # Корректируем точность цены/количества через фабрику
                    try:
                        adj_price = self.order_service.order_factory.adjust_price_precision(new_buy_order.symbol, raw_new_sell_price)
                    except Exception:
                        adj_price = raw_new_sell_price
                    try:
                        adj_amount = self.order_service.order_factory.adjust_amount_precision(new_buy_order.symbol, new_buy_order.amount)
                    except Exception:
                        adj_amount = new_buy_order.amount

                    sell.price = adj_price
                    sell.amount = adj_amount
                    sell.last_update = int(time.time() * 1000)
                    # Оставляем статус PENDING, exchange_id = None
                    sell.exchange_id = None
                    self.order_service.orders_repo.update_order(sell)
                    logger.info(f"🔁 Обновлён PENDING SELL {sell.order_id} в сделке {order.deal_id}: новая цена {adj_price}, объём {adj_amount}")
                else:
                    logger.debug(f"ℹ️ В сделке {order.deal_id} нет PENDING SELL для обновления")

                # Сохраняем таймер анти-дерганья
                self._last_recreation_by_deal[order.deal_id] = time.time()
            except Exception as e:
                logger.error(f"❌ Ошибка обновления связанного SELL для сделки {order.deal_id}: {e}")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки протухшего BUY ордера {order.order_id}: {e}", exc_info=True)

    async def _recreate_buy_order(self, old_order: Order) -> Optional[Order]:
        """Простое пересоздание BUY ордера по текущей рыночной цене (как в версии 2.3.4)"""
        try:
            # Получаем текущую цену
            ticker = await self.exchange_connector.fetch_ticker(old_order.symbol)
            new_price = float(ticker.last) * 0.999  # Небольшая скидка для быстрого исполнения

            logger.info(f"🔄 Пересоздаем BUY ордер: старая цена {old_order.price}, новая цена {new_price}")

            # Создаем и размещаем новый ордер
            execution_result = await self.order_service.create_and_place_buy_order(
                symbol=old_order.symbol,
                amount=old_order.amount,
                price=new_price,
                deal_id=old_order.deal_id
            )
            
            return execution_result.order if execution_result.success else None
            
        except Exception as e:
            logger.error(f"❌ Ошибка пересоздания BUY ордера: {e}", exc_info=True)
            return None


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
