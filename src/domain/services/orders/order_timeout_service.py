# domain/services/order_timeout_service.py.new - Система проверки протухших BUY ордеров
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from domain.entities.order import Order
from domain.entities.currency_pair import CurrencyPair
from domain.services.orders.order_service import OrderService
from domain.services.deals.deal_service import DealService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

logger = logging.getLogger(__name__)

class OrderTimeoutService:
    """
    🕒 Сервис для автоматического отслеживания и управления протухшими BUY ордерами
    
    Отслеживает только ордера на ПОКУПКУ (BUY) которые могут "протухнуть" если:
    - Ордер висит слишком долго без исполнения
    - Рыночная цена ушла слишком далеко вверх от цены ордера
    - Ордер потерял актуальность из-за изменения трендов
    
    SELL ордерами займется RiskManagementService позже
    """

    def __init__(
        self, 
        order_service: OrderService,
        deal_service: DealService,
        exchange_connector: CcxtExchangeConnector,
        config: Dict[str, Any] = None
    ):
        self.order_service = order_service
        self.deal_service = deal_service
        self.exchange = exchange_connector
        
        # Конфигурация таймаутов (по умолчанию)
        default_config = {
            'max_order_age_minutes': 15,           # Максимальный возраст ордера (15 минут)
            'max_price_deviation_percent': 3.0,    # Максимальное отклонение цены (3%)
            'check_interval_seconds': 30,          # Интервал проверки (30 секунд)
            'auto_recreate_orders': True,          # Автоматически пересоздавать ордера
            'max_recreations_per_deal': 3,         # Максимум пересозданий на сделку
            'min_time_between_recreations_minutes': 2,  # Минимум времени между пересозданиями
            'trend_validation_enabled': True       # Проверять тренд перед пересозданием
        }
        
        self.config = {**default_config, **(config or {})}
        
        # Состояние сервиса
        self.is_monitoring = False
        self.monitoring_task = None
        
        # Статистика
        self.stats = {
            'total_checks': 0,
            'stale_orders_found': 0,
            'orders_cancelled': 0,
            'orders_recreated': 0,
            'recreation_failures': 0,
            'reasons': {
                'age_timeout': 0,
                'price_deviation': 0,
                'trend_changed': 0
            }
        }
        
        # Отслеживание пересозданий для каждой сделки
        self.deal_recreations = {}  # deal_id -> count

    # 🚀 ОСНОВНЫЕ МЕТОДЫ ЗАПУСКА/ОСТАНОВКИ

    async def start_monitoring(self):
        """Запуск фонового мониторинга протухших BUY ордеров"""
        if self.is_monitoring:
            logger.warning("⚠️ Order timeout monitoring already started")
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"🕒 Order timeout monitoring started")
        logger.info(f"   ⏰ Check interval: {self.config['check_interval_seconds']}s")
        logger.info(f"   📅 Max age: {self.config['max_order_age_minutes']} minutes")
        logger.info(f"   📊 Max price deviation: {self.config['max_price_deviation_percent']}%")
        logger.info(f"   🔄 Auto recreate: {'✅' if self.config['auto_recreate_orders'] else '❌'}")

    async def stop_monitoring(self):
        """Остановка мониторинга"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
        logger.info("🔴 Order timeout monitoring stopped")

    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        logger.info("🔄 Starting order timeout monitoring loop")
        
        while self.is_monitoring:
            try:
                await self._check_stale_buy_orders()
                self.stats['total_checks'] += 1
                
                # Очистка старых записей пересозданий (старше 1 часа)
                self._cleanup_old_recreation_records()
                
                await asyncio.sleep(self.config['check_interval_seconds'])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in order timeout monitoring loop: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке

    # 🔍 ОСНОВНАЯ ЛОГИКА ПРОВЕРКИ

    async def _check_stale_buy_orders(self):
        """Проверяет все открытые BUY ордера на 'протухание'"""
        try:
            # Получаем все открытые ордера
            open_orders = self.order_service.get_open_orders()
            
            # Фильтруем только BUY ордера
            buy_orders = [order for order in open_orders if order.side == Order.SIDE_BUY]
            
            if not buy_orders:
                return
                
            logger.debug(f"🔍 Checking {len(buy_orders)} open BUY orders for staleness")
            
            for order in buy_orders:
                await self._check_single_buy_order(order)
                
        except Exception as e:
            logger.error(f"❌ Error checking stale BUY orders: {e}")

    async def _check_single_buy_order(self, order: Order):
        """Проверяет конкретный BUY ордер на протухание"""
        try:
            # Проверка по времени
            is_too_old, age_minutes = await self._check_order_age(order)
            
            # Проверка по отклонению цены
            is_price_too_far, price_deviation = await self._check_price_deviation(order)
            
            # Определяем причину протухания
            stale_reasons = []
            if is_too_old:
                stale_reasons.append(f"age_timeout (age: {age_minutes:.1f}min)")
                self.stats['reasons']['age_timeout'] += 1
                
            if is_price_too_far:
                stale_reasons.append(f"price_deviation (deviation: {price_deviation:.2f}%)")
                self.stats['reasons']['price_deviation'] += 1
            
            # Если ордер протух
            if stale_reasons:
                self.stats['stale_orders_found'] += 1
                
                logger.warning(f"🕒 STALE BUY ORDER detected: {order.order_id}")
                logger.warning(f"   📋 Reasons: {', '.join(stale_reasons)}")
                logger.warning(f"   💰 Order: {order.amount} {order.symbol} @ {order.price}")
                logger.warning(f"   🔗 Deal ID: {order.deal_id}")
                
                await self._handle_stale_buy_order(order, stale_reasons)
                
        except Exception as e:
            logger.error(f"❌ Error checking BUY order {order.order_id}: {e}")

    async def _check_order_age(self, order: Order) -> Tuple[bool, float]:
        """Проверка превышения времени жизни BUY ордера"""
        current_time = int(time.time() * 1000)
        order_age_ms = current_time - order.created_at
        order_age_minutes = order_age_ms / 1000 / 60
        
        max_age = self.config['max_order_age_minutes']
        is_too_old = order_age_minutes > max_age
        
        if is_too_old:
            logger.debug(f"⏰ Order {order.order_id} age: {order_age_minutes:.1f}min > {max_age}min")
            
        return is_too_old, order_age_minutes

    async def _check_price_deviation(self, order: Order) -> Tuple[bool, float]:
        """Проверка отклонения цены BUY ордера от рыночной"""
        try:
            ticker = await self.exchange.fetch_ticker(order.symbol)
            current_price = ticker['last']
            
            # Для BUY ордера: если рынок ушел значительно выше нашей цены покупки
            # Это означает что никто не продаст нам по нашей низкой цене
            deviation_percent = ((current_price - order.price) / order.price) * 100
            
            max_deviation = self.config['max_price_deviation_percent']
            is_too_far = deviation_percent > max_deviation
            
            if is_too_far:
                logger.debug(f"📈 Order {order.order_id} price deviation: "
                           f"{order.price} vs market {current_price} = {deviation_percent:.2f}%")
                           
            return is_too_far, deviation_percent
            
        except Exception as e:
            logger.error(f"❌ Error checking price deviation for order {order.order_id}: {e}")
            return False, 0.0

    # 🛠️ ОБРАБОТКА ПРОТУХШИХ ОРДЕРОВ

    async def _handle_stale_buy_order(self, order: Order, reasons: List[str]):
        """Обработка протухшего BUY ордера"""
        logger.info(f"🛠️ Handling stale BUY order {order.order_id}")
        logger.info(f"   📋 Reasons: {', '.join(reasons)}")
        
        try:
            # 1. Отменяем старый BUY ордер
            cancel_success = await self._cancel_stale_order(order)
            
            if not cancel_success:
                logger.error(f"❌ Failed to cancel stale BUY order {order.order_id}")
                return
                
            self.stats['orders_cancelled'] += 1
            
            # 2. Определяем нужно ли пересоздавать ордер
            if self.config['auto_recreate_orders']:
                should_recreate = await self._should_recreate_buy_order(order, reasons)
                
                if should_recreate:
                    # 3. Пересоздаем BUY ордер по новой цене
                    new_order = await self._recreate_buy_order(order)
                    
                    if new_order:
                        self.stats['orders_recreated'] += 1
                        logger.info(f"✅ BUY order recreated: {order.order_id} -> {new_order.order_id}")
                    else:
                        self.stats['recreation_failures'] += 1
                        logger.error(f"❌ Failed to recreate BUY order {order.order_id}")
                else:
                    logger.info(f"❌ BUY order {order.order_id} cancelled without recreation")
            else:
                logger.info(f"❌ BUY order {order.order_id} cancelled (auto-recreation disabled)")
                
        except Exception as e:
            logger.error(f"❌ Error handling stale BUY order {order.order_id}: {e}")

    async def _cancel_stale_order(self, order: Order) -> bool:
        """Отменяет протухший ордер"""
        try:
            logger.info(f"❌ Cancelling stale BUY order {order.order_id}")
            
            success = await self.order_service.cancel_order(order)
            
            if success:
                logger.info(f"✅ Stale BUY order {order.order_id} cancelled successfully")
            else:
                logger.error(f"❌ Failed to cancel stale BUY order {order.order_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error cancelling stale BUY order {order.order_id}: {e}")
            return False

    async def _should_recreate_buy_order(self, order: Order, reasons: List[str]) -> bool:
        """Определяет нужно ли пересоздавать BUY ордер"""
        
        # Проверяем лимит пересозданий для этой сделки
        deal_id = order.deal_id
        recreations_count = self.deal_recreations.get(deal_id, 0)
        max_recreations = self.config['max_recreations_per_deal']
        
        if recreations_count >= max_recreations:
            logger.warning(f"⚠️ Deal {deal_id} reached max recreations limit: {recreations_count}/{max_recreations}")
            return False
            
        # Проверяем минимальное время между пересозданиями
        last_recreation_time = getattr(order, 'last_recreation_time', None)
        if last_recreation_time:
            min_interval_ms = self.config['min_time_between_recreations_minutes'] * 60 * 1000
            time_since_last = int(time.time() * 1000) - last_recreation_time
            
            if time_since_last < min_interval_ms:
                logger.warning(f"⚠️ Too soon to recreate order {order.order_id}, wait {min_interval_ms - time_since_last}ms")
                return False
        
        # Не пересоздаем если только возраст проблема (возможно сделка уже не актуальна)
        age_only = len(reasons) == 1 and 'age_timeout' in reasons[0]
        if age_only:
            logger.info(f"💭 Not recreating order {order.order_id} - age timeout only, deal may be stale")
            return False
            
        # Пересоздаем если цена ушла (основная причина)
        price_deviation = any('price_deviation' in reason for reason in reasons)
        if price_deviation:
            logger.info(f"💭 Will recreate order {order.order_id} - price deviation detected")
            return True
            
        return False

    async def _recreate_buy_order(self, old_order: Order) -> Optional[Order]:
        """Пересоздает BUY ордер по текущей рыночной цене"""
        
        try:
            logger.info(f"🔄 Recreating BUY order {old_order.order_id} with current market price")
            
            # Получаем текущую цену
            ticker = await self.exchange.fetch_ticker(old_order.symbol)
            current_price = ticker['last']
            
            # Для BUY ордера: ставим цену немного ниже текущей рыночной
            # чтобы увеличить вероятность исполнения
            price_adjustment = 0.001  # -0.1%
            new_price = current_price * (1 - price_adjustment)
            
            logger.info(f"💰 New BUY price calculation:")
            logger.info(f"   📊 Market price: {current_price}")
            logger.info(f"   🎯 Old order price: {old_order.price}")
            logger.info(f"   🆕 New order price: {new_price} (-{price_adjustment*100:.1f}%)")
            
            # Создаем новый BUY ордер
            execution_result = await self.order_service.create_and_place_buy_order(
                symbol=old_order.symbol,
                amount=old_order.amount,
                price=new_price,
                deal_id=old_order.deal_id,
                order_type=old_order.order_type,
                client_order_id=f"recreated_{old_order.order_id}_{int(time.time())}"
            )
            
            if execution_result.success:
                new_order = execution_result.order
                
                # Отмечаем время пересоздания
                new_order.last_recreation_time = int(time.time() * 1000)
                
                # Увеличиваем счетчик пересозданий для сделки
                deal_id = old_order.deal_id
                self.deal_recreations[deal_id] = self.deal_recreations.get(deal_id, 0) + 1
                
                logger.info(f"✅ BUY order recreated successfully:")
                logger.info(f"   🆔 New order ID: {new_order.order_id}")
                logger.info(f"   🏷️ Exchange ID: {new_order.exchange_id}")
                logger.info(f"   💰 Price: {old_order.price} -> {new_order.price}")
                logger.info(f"   🔄 Deal recreations: {self.deal_recreations[deal_id]}")
                
                return new_order
            else:
                logger.error(f"❌ Failed to recreate BUY order: {execution_result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error recreating BUY order {old_order.order_id}: {e}")
            return None

    # 🧹 УТИЛИТНЫЕ МЕТОДЫ

    def _cleanup_old_recreation_records(self):
        """Очистка старых записей пересозданий (старше 1 часа)"""
        try:
            # Получаем все открытые сделки
            open_deals = self.deal_service.get_open_deals()
            open_deal_ids = {deal.deal_id for deal in open_deals}
            
            # Удаляем записи для закрытых сделок
            closed_deal_ids = []
            for deal_id in self.deal_recreations:
                if deal_id not in open_deal_ids:
                    closed_deal_ids.append(deal_id)
                    
            for deal_id in closed_deal_ids:
                del self.deal_recreations[deal_id]
                
            if closed_deal_ids:
                logger.debug(f"🧹 Cleaned up recreation records for {len(closed_deal_ids)} closed deals")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up recreation records: {e}")

    # 📊 СТАТИСТИКА И МОНИТОРИНГ

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики работы сервиса"""
        stats = self.stats.copy()
        
        # Дополнительные метрики
        if stats['total_checks'] > 0:
            stats['stale_rate'] = (stats['stale_orders_found'] / stats['total_checks']) * 100
        else:
            stats['stale_rate'] = 0.0
            
        if stats['orders_cancelled'] > 0:
            stats['recreation_success_rate'] = (stats['orders_recreated'] / stats['orders_cancelled']) * 100
        else:
            stats['recreation_success_rate'] = 0.0
            
        stats['active_deal_recreations'] = len(self.deal_recreations)
        stats['monitoring_status'] = 'RUNNING' if self.is_monitoring else 'STOPPED'
        
        return stats

    def get_configuration(self) -> Dict[str, Any]:
        """Получение текущей конфигурации"""
        return self.config.copy()

    def update_configuration(self, new_config: Dict[str, Any]):
        """Обновление конфигурации"""
        self.config.update(new_config)
        logger.info(f"⚙️ Order timeout configuration updated: {new_config}")

    def reset_statistics(self):
        """Сброс статистики"""
        self.stats = {
            'total_checks': 0,
            'stale_orders_found': 0,
            'orders_cancelled': 0,
            'orders_recreated': 0,
            'recreation_failures': 0,
            'reasons': {
                'age_timeout': 0,
                'price_deviation': 0,
                'trend_changed': 0
            }
        }
        self.deal_recreations.clear()
        logger.info("📊 Order timeout statistics reset")

    # 🚨 ЭКСТРЕННЫЕ МЕТОДЫ

    async def emergency_cancel_all_stale_orders(self) -> Dict[str, Any]:
        """Экстренная отмена всех протухших BUY ордеров"""
        logger.warning("🚨 EMERGENCY: Cancelling all stale BUY orders")
        
        result = {
            'cancelled_orders': 0,
            'failed_cancellations': 0,
            'errors': []
        }
        
        try:
            open_orders = self.order_service.get_open_orders()
            buy_orders = [order for order in open_orders if order.side == Order.SIDE_BUY]
            
            for order in buy_orders:
                try:
                    # Проверяем на протухание
                    is_old, _ = await self._check_order_age(order)
                    is_far, _ = await self._check_price_deviation(order)
                    
                    if is_old or is_far:
                        success = await self.order_service.cancel_order(order)
                        if success:
                            result['cancelled_orders'] += 1
                        else:
                            result['failed_cancellations'] += 1
                            
                except Exception as e:
                    result['failed_cancellations'] += 1
                    result['errors'].append(f"Order {order.order_id}: {str(e)}")
                    
            logger.warning(f"🚨 Emergency cancellation completed: "
                         f"{result['cancelled_orders']} cancelled, "
                         f"{result['failed_cancellations']} failed")
                         
        except Exception as e:
            logger.error(f"❌ Error in emergency cancellation: {e}")
            result['errors'].append(f"Emergency cancellation error: {str(e)}")
            
        return result

    def __repr__(self):
        status = "RUNNING" if self.is_monitoring else "STOPPED"
        return (f"<OrderTimeoutService(status={status}, "
                f"stale_found={self.stats['stale_orders_found']}, "
                f"recreated={self.stats['orders_recreated']})>")
