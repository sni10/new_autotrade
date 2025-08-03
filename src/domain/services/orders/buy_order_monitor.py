# domain/services/buy_order_monitor.py.new
import asyncio
import logging
import time
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
        grace_period_seconds: int = 60  # Период ожидания перед проверкой новых ордеров
    ):
        self.order_service = order_service
        self.deal_service = deal_service # ❗️ ДОБАВЛЕНО
        self.exchange = exchange_connector
        self.max_age_minutes = max_age_minutes
        self.max_price_deviation_percent = max_price_deviation_percent
        self.check_interval_seconds = check_interval_seconds
        self.grace_period_seconds = grace_period_seconds
        
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
                # Проверяем возраст ордера для определения необходимости проверки статуса
                age_seconds = self._get_order_age_seconds(order)
                
                # Пропускаем проверку статуса для новых ордеров (в пределах grace period)
                if age_seconds < self.grace_period_seconds:
                    logger.debug(f"⏳ BUY {order.order_id}: пропускаем проверку статуса (возраст {age_seconds:.1f}с < {self.grace_period_seconds}с)")
                    continue
                
                # КРИТИЧНО: Обновляем статус с биржи ТОЛЬКО после grace period
                updated_order = await self.order_service.get_order_status(order)
                
                # Детальное логирование состояния ордера
                age_minutes = self._get_order_age_minutes(updated_order)
                fill_percentage = updated_order.get_fill_percentage() if hasattr(updated_order, 'get_fill_percentage') else 0.0
                
                logger.info(f"📊 BUY {updated_order.order_id}: статус={updated_order.status}, "
                           f"заполнено={fill_percentage:.1%}, возраст={age_minutes:.1f}мин")
                
                # Проверяем на "протухание"
                is_stale, reason = await self._is_order_stale(updated_order)
                if is_stale:
                    logger.warning(f"🚨 ПРОТУХШИЙ BUY: {reason}")
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

    def _get_order_age_minutes(self, order: Order) -> float:
        """Вычисляет возраст ордера в минутах"""
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
            
            age_minutes = (current_time - created_at_ms) / 1000 / 60
            return max(0.0, age_minutes)  # Не может быть отрицательным
            
        except Exception as e:
            logger.error(f"❌ Ошибка вычисления возраста ордера {order.order_id}: {e}")
            return 0.0

    async def _is_order_stale(self, order: Order) -> Tuple[bool, str]:
        """Упрощенная проверка протухания BUY ордера (как в версии 2.3.4)"""
        try:
            # 1. Проверка возраста ордера
            age_minutes = self._get_order_age_minutes(order)
            
            if age_minutes > self.max_age_minutes:
                reason = f"ордер {order.order_id} протух по времени: {age_minutes:.1f} мин > {self.max_age_minutes} мин"
                return True, reason
            
            # 2. Простая проверка отклонения цены от рынка
            try:
                ticker = await self.exchange.fetch_ticker(order.symbol)
                current_price = float(ticker.last)
                
                # Для BUY: если рынок ушел выше нашей цены
                price_deviation = ((current_price - order.price) / order.price) * 100
                
                if price_deviation > self.max_price_deviation_percent:
                    reason = f"ордер {order.order_id} протух по цене: рынок {current_price}, ордер {order.price} (+{price_deviation:.1f}%)"
                    return True, reason
                    
            except Exception as e:
                logger.warning(f"⚠️ Не удалось проверить цену для {order.symbol}: {e}")
                # Если не можем получить цену, проверяем только по времени
                
            return False, ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки ордера {order.order_id}: {e}")
            return False, ""

    async def _handle_stale_buy_order(self, order: Order):
        """Простая обработка протухшего BUY ордера: отмена + пересоздание (как в версии 2.3.4)"""
        try:
            self.stats['stale_orders_found'] += 1
            logger.warning(f"🚨 Обрабатываем протухший BUY ордер {order.order_id}")

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

        except Exception as e:
            logger.error(f"❌ Ошибка обработки протухшего BUY ордера {order.order_id}: {e}", exc_info=True)

    async def _recreate_buy_order(self, old_order: Order) -> Optional[Order]:
        """Простое пересоздание BUY ордера по текущей рыночной цене (как в версии 2.3.4)"""
        try:
            # Получаем текущую цену
            ticker = await self.exchange.fetch_ticker(old_order.symbol)
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
