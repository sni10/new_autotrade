import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
import ccxt

from src.domain.entities.order import Order
from src.infrastructure.repositories.orders_repository import OrdersRepository
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.domain.entities.statistics import Statistics, StatisticCategory, StatisticType

logger = logging.getLogger(__name__)


class OrderCancellationService:
    """
    Сервис для отмены ордеров.
    Соблюдает принцип единственной ответственности (SRP).
    Отвечает ТОЛЬКО за отмену ордеров на бирже и локально.
    """
    
    def __init__(
        self,
        orders_repo: OrdersRepository,
        exchange_connector: CcxtExchangeConnector,
        statistics_repo: Optional[IStatisticsRepository] = None
    ):
        self.orders_repo = orders_repo
        self.exchange_connector = exchange_connector
        self.statistics_repo = statistics_repo
        
        self._stats = {
            'orders_cancelled': 0,
            'orders_not_found': 0,
            'local_cancellations': 0,
            'failed_cancellations': 0,
            'emergency_cancellations': 0
        }
    
    async def cancel_order(self, order: Order, reason: str = "User request") -> Optional[Order]:
        """
        Отмена отдельного ордера
        
        Args:
            order: Ордер для отмены
            reason: Причина отмены
            
        Returns:
            Обновленный ордер в случае успеха, иначе None
        """
        try:
            if not order.is_open():
                logger.warning(f"⚠️ Order {order.order_id} is not open ({order.status})")
                return None
            
            logger.info(f"❌ Cancelling order {order.order_id}: {reason}")
            
            # Если нет exchange_id или коннектора - локальная отмена
            if not self.exchange_connector or not order.exchange_id:
                return await self._cancel_order_locally(order, reason)
            
            # Отмена на бирже
            return await self._cancel_order_on_exchange(order, reason)
            
        except Exception as e:
            logger.error(f"❌ Error cancelling order {order.order_id}: {e}")
            await self._update_cancellation_statistics(False, order, "error")
            return None
    
    async def _cancel_order_on_exchange(self, order: Order, reason: str) -> Optional[Order]:
        """Отмена ордера на бирже"""
        try:
            logger.info(f"❌ Cancelling order {order.exchange_id} on exchange")
            
            # Реальная отмена на бирже
            exchange_response = await self.exchange_connector.cancel_order(
                order.exchange_id,
                order.symbol
            )
            
            # Обновляем статус ордера
            order.cancel(reason)
            if exchange_response:
                order.update_from_exchange(exchange_response)
            
            self.orders_repo.save(order)
            self._stats['orders_cancelled'] += 1
            
            logger.info(f"✅ Order {order.order_id} cancelled successfully")
            await self._update_cancellation_statistics(True, order, "exchange")
            
            return order
            
        except ccxt.OrderNotFound:
            # Ордер не найден на бирже - возможно, уже исполнен или отменен
            logger.warning(f"⚠️ Order {order.order_id} not found on exchange. Marking as cancelled locally.")
            
            order.status = Order.STATUS_NOT_FOUND_ON_EXCHANGE
            order.closed_at = int(time.time() * 1000)
            self.orders_repo.save(order)
            
            self._stats['orders_not_found'] += 1
            await self._update_cancellation_statistics(True, order, "not_found")
            
            return order  # Считаем успешным - цель достигнута
            
        except Exception as e:
            logger.error(f"❌ Error cancelling order {order.order_id} on exchange: {e}")
            
            # Помечаем ордер как failed to cancel
            order.status = Order.STATUS_FAILED
            order.error_message = f"Cancellation failed: {str(e)}"
            self.orders_repo.save(order)
            
            self._stats['failed_cancellations'] += 1
            await self._update_cancellation_statistics(False, order, "failed")
            
            return None
    
    async def _cancel_order_locally(self, order: Order, reason: str) -> Optional[Order]:
        """Локальная отмена ордера (без обращения к бирже)"""
        try:
            order.cancel(reason)
            self.orders_repo.save(order)
            
            self._stats['local_cancellations'] += 1
            logger.warning(f"⚠️ Order {order.order_id} cancelled locally: {reason}")
            
            await self._update_cancellation_statistics(True, order, "local")
            return order
            
        except Exception as e:
            logger.error(f"❌ Error cancelling order locally: {e}")
            return None
    
    async def cancel_multiple_orders(
        self,
        orders: List[Order],
        reason: str = "Batch cancellation"
    ) -> Dict[int, Optional[Order]]: # Изменен тип возвращаемого значения
        """
        Отмена нескольких ордеров параллельно
        
        Args:
            orders: Список ордеров для отмены
            reason: Причина отмены
            
        Returns:
            Словарь {order_id: updated_order_or_None}
        """
        if not orders:
            return {}
        
        try:
            logger.info(f"❌ Cancelling {len(orders)} orders: {reason}")
            
            # Создаем задачи для параллельной отмены
            tasks = [
                self.cancel_order(order, f"{reason} (batch)")
                for order in orders
            ]
            
            # Выполняем все отмены параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            result_dict = {}
            for i, result in enumerate(results):
                order_id = orders[i].order_id
                if isinstance(result, Exception):
                    logger.error(f"Error cancelling order {order_id}: {result}")
                    result_dict[order_id] = None
                else:
                    result_dict[order_id] = result # result теперь Optional[Order]
            
            success_count = sum(1 for success in result_dict.values() if success is not None) # Проверяем на None
            logger.info(f"❌ Batch cancellation completed: {success_count}/{len(orders)} successful")
            
            return result_dict
            
        except Exception as e:
            logger.error(f"❌ Error in batch cancellation: {e}")
            return {order.order_id: None for order in orders}
    
    async def cancel_orders_by_deal(self, deal_id: int, reason: str = "Deal cancellation") -> int:
        """
        Отмена всех ордеров связанных со сделкой
        
        Args:
            deal_id: ID сделки
            reason: Причина отмены
            
        Returns:
            Количество отмененных ордеров
        """
        try:
            # Получаем все ордера сделки
            deal_orders = self.orders_repo.get_all_by_deal(deal_id)
            open_orders = [order for order in deal_orders if order.is_open()]
            
            if not open_orders:
                logger.info(f"No open orders found for deal {deal_id}")
                return 0
            
            logger.info(f"❌ Cancelling {len(open_orders)} orders for deal {deal_id}")
            
            # Отменяем все ордера
            results = await self.cancel_multiple_orders(open_orders, reason)
            cancelled_count = sum(1 for success in results.values() if success is not None) # Проверяем на None
            
            logger.info(f"❌ Deal {deal_id} cancellation: {cancelled_count}/{len(open_orders)} orders cancelled")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"❌ Error cancelling orders for deal {deal_id}: {e}")
            return 0
    
    async def cancel_orders_by_symbol(
        self,
        symbol: str,
        reason: str = "Symbol cancellation"
    ) -> int:
        """
        Отмена всех открытых ордеров для торговой пары
        
        Args:
            symbol: Торговая пара
            reason: Причина отмены
            
        Returns:
            Количество отмененных ордеров
        """
        try:
            # Получаем все ордера для символа
            all_orders = self.orders_repo.get_all()
            symbol_orders = [
                order for order in all_orders 
                if order.symbol == symbol and order.is_open()
            ]
            
            if not symbol_orders:
                logger.info(f"No open orders found for symbol {symbol}")
                return 0
            
            logger.info(f"❌ Cancelling {len(symbol_orders)} orders for symbol {symbol}")
            
            # Отменяем все ордера
            results = await self.cancel_multiple_orders(symbol_orders, reason)
            cancelled_count = sum(1 for success in results.values() if success is not None) # Проверяем на None
            
            logger.info(f"❌ Symbol {symbol} cancellation: {cancelled_count}/{len(symbol_orders)} orders cancelled")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"❌ Error cancelling orders for symbol {symbol}: {e}")
            return 0
    
    async def emergency_cancel_all_orders(
        self,
        symbol: Optional[str] = None,
        reason: str = "Emergency cancellation"
    ) -> int:
        """
        Экстренная отмена всех открытых ордеров
        
        Args:
            symbol: Опциональный фильтр по торговой паре
            reason: Причина отмены
            
        Returns:
            Количество отмененных ордеров
        """
        try:
            logger.warning(f"🚨 Emergency cancellation initiated: {reason}")
            
            # Получаем все открытые ордера
            all_orders = self.orders_repo.get_all()
            open_orders = [order for order in all_orders if order.is_open()]
            
            # Фильтруем по символу если указан
            if symbol:
                open_orders = [order for order in open_orders if order.symbol == symbol]
            
            if not open_orders:
                logger.warning("🚨 No open orders found for emergency cancellation")
                return 0
            
            logger.warning(f"🚨 Emergency cancelling {len(open_orders)} orders")
            
            # Отменяем все ордера
            results = await self.cancel_multiple_orders(open_orders, f"🚨 {reason}")
            cancelled_count = sum(1 for success in results.values() if success is not None) # Проверяем на None
            
            self._stats['emergency_cancellations'] += cancelled_count
            
            logger.warning(f"🚨 Emergency cancellation completed: {cancelled_count}/{len(open_orders)} orders cancelled")
            
            # Обновляем статистику
            await self._update_emergency_statistics(cancelled_count, len(open_orders))
            
            return cancelled_count
            
        except Exception as e:
            logger.error(f"❌ Error in emergency cancellation: {e}")
            return 0
    
    async def cancel_stale_orders(
        self,
        max_age_hours: int = 24,
        reason: str = "Stale order cleanup"
    ) -> int:
        """
        Отмена устаревших ордеров
        
        Args:
            max_age_hours: Максимальный возраст ордера в часах
            reason: Причина отмены
            
        Returns:
            Количество отмененных ордеров
        """
        try:
            current_time = int(time.time() * 1000)
            max_age_ms = max_age_hours * 60 * 60 * 1000
            
            all_orders = self.orders_repo.get_all()
            stale_orders = []
            
            for order in all_orders:
                if order.is_open() and order.created_at:
                    age_ms = current_time - order.created_at
                    if age_ms > max_age_ms:
                        stale_orders.append(order)
            
            if not stale_orders:
                logger.info(f"No stale orders found (older than {max_age_hours} hours)")
                return 0
            
            logger.info(f"❌ Cancelling {len(stale_orders)} stale orders (older than {max_age_hours}h)")
            
            # Отменяем устаревшие ордера
            results = await self.cancel_multiple_orders(stale_orders, reason)
            cancelled_count = sum(1 for success in results.values() if success is not None) # Проверяем на None
            
            logger.info(f"❌ Stale order cleanup: {cancelled_count}/{len(stale_orders)} orders cancelled")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"❌ Error cancelling stale orders: {e}")
            return 0
    
    async def _update_cancellation_statistics(
        self,
        success: bool,
        order: Order,
        cancellation_type: str
    ) -> None:
        """
        Обновление статистики отмены ордеров
        """
        if not self.statistics_repo:
            return
        
        try:
            await self.statistics_repo.increment_counter(
                f"order_cancellations_{cancellation_type}",
                StatisticCategory.ORDERS,
                tags={
                    "symbol": order.symbol,
                    "side": order.side.lower(),
                    "success": str(success).lower()
                }
            )
            
            if success:
                await self.statistics_repo.increment_counter(
                    "order_cancellations_successful",
                    StatisticCategory.ORDERS,
                    tags={"symbol": order.symbol}
                )
            else:
                await self.statistics_repo.increment_counter(
                    "order_cancellations_failed",
                    StatisticCategory.ORDERS,
                    tags={"symbol": order.symbol}
                )
                
        except Exception as e:
            logger.error(f"Error updating cancellation statistics: {e}")
    
    async def _update_emergency_statistics(self, cancelled: int, total: int) -> None:
        """
        Обновление статистики экстренных отмен
        """
        if not self.statistics_repo:
            return
        
        try:
            await self.statistics_repo.increment_counter(
                "emergency_cancellations_executed",
                StatisticCategory.ORDERS
            )
            
            await self.statistics_repo.update_gauge(
                "emergency_cancellation_success_rate",
                StatisticCategory.ORDERS,
                (cancelled / total * 100) if total > 0 else 0
            )
            
        except Exception as e:
            logger.error(f"Error updating emergency statistics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики сервиса
        """
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """
        Сброс статистики
        """
        self._stats = {
            'orders_cancelled': 0,
            'orders_not_found': 0,
            'local_cancellations': 0,
            'failed_cancellations': 0,
            'emergency_cancellations': 0
        }