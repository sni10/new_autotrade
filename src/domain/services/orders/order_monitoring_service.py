import asyncio
import logging
import time
from typing import Optional, Dict, List, Any
import ccxt

from src.domain.entities.order import Order
from src.infrastructure.repositories.orders_repository import OrdersRepository
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.domain.repositories.i_statistics_repository import IStatisticsRepository
from src.domain.entities.statistics import Statistics, StatisticCategory, StatisticType

logger = logging.getLogger(__name__)


class OrderMonitoringService:
    """
    Сервис для мониторинга статусов ордеров.
    Соблюдает принцип единственной ответственности (SRP).
    Отвечает ТОЛЬКО за мониторинг и синхронизацию статусов ордеров.
    """
    
    def __init__(
        self,
        orders_repo: OrdersRepository,
        exchange_connector: CcxtExchangeConnector,
        statistics_repo: Optional[IStatisticsRepository] = None,
        currency_pair_symbol: Optional[str] = None
    ):
        self.orders_repo = orders_repo
        self.exchange_connector = exchange_connector
        self.statistics_repo = statistics_repo
        self.currency_pair_symbol = currency_pair_symbol
        
        self._stats = {
            'status_checks': 0,
            'orders_updated': 0,
            'orders_not_found': 0,
            'sync_operations': 0,
            'errors': 0
        }
    
    async def check_order_status(self, order: Order) -> Optional[Order]:
        """
        Проверка статуса отдельного ордера на бирже
        
        Args:
            order: Ордер для проверки
            
        Returns:
            Обновленный ордер или None в случае ошибки
        """
        if not order.exchange_id or not self.exchange_connector:
            return order
        
        try:
            logger.debug(f"📊 Checking status for order {order.exchange_id}")
            
            # Реальный запрос к бирже
            exchange_order = await self.exchange_connector.fetch_order(
                order.exchange_id,
                order.symbol
            )
            
            # Обновляем локальный ордер данными с биржи
            old_status = order.status
            order.update_from_exchange(exchange_order)
            
            # Сохраняем обновления
            self.orders_repo.save(order)
            
            # Логируем изменения статуса
            if old_status != order.status:
                logger.info(f"📊 Order {order.order_id} status changed: {old_status} → {order.status}")
                self._stats['orders_updated'] += 1
                
                # Обновляем статистику
                await self._update_monitoring_statistics(order, "status_changed")
            
            self._stats['status_checks'] += 1
            return order
            
        except ccxt.OrderNotFound:
            logger.warning(f"⚠️ Order {order.order_id} (exchange_id: {order.exchange_id}) not found on exchange")
            order.status = Order.STATUS_NOT_FOUND_ON_EXCHANGE
            order.closed_at = int(time.time() * 1000)
            self.orders_repo.save(order)
            
            self._stats['orders_not_found'] += 1
            await self._update_monitoring_statistics(order, "not_found")
            return order
            
        except Exception as e:
            logger.error(f"❌ Error checking order status {order.order_id}: {e}")
            self._stats['errors'] += 1
            await self._update_monitoring_statistics(order, "error")
            return order
    
    async def check_multiple_orders(self, orders: List[Order]) -> List[Order]:
        """
        Проверка статусов нескольких ордеров параллельно
        
        Args:
            orders: Список ордеров для проверки
            
        Returns:
            Список обновленных ордеров
        """
        if not orders:
            return []
        
        try:
            logger.debug(f"📊 Checking status for {len(orders)} orders")
            
            # Создаем задачи для параллельной проверки
            tasks = [self.check_order_status(order) for order in orders]
            
            # Выполняем все проверки параллельно
            updated_orders = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Фильтруем результаты
            result = []
            for i, updated_order in enumerate(updated_orders):
                if isinstance(updated_order, Exception):
                    logger.error(f"Error updating order {orders[i].order_id}: {updated_order}")
                    result.append(orders[i])  # Возвращаем оригинальный ордер
                elif updated_order:
                    result.append(updated_order)
                else:
                    result.append(orders[i])  # Fallback к оригинальному
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking multiple orders: {e}")
            self._stats['errors'] += 1
            return orders
    
    async def sync_orders_with_exchange(self) -> List[Order]:
        """
        Синхронизация всех открытых ордеров с биржей
        
        Returns:
            Список обновленных ордеров
        """
        if not self.exchange_connector:
            logger.warning("⚠️ No exchange connector for sync")
            return []
        
        updated_orders = []
        
        try:
            logger.info("🔄 Starting order synchronization with exchange")
            
            # Получаем все локальные открытые ордера
            local_orders = self._get_open_orders()
            
            if not local_orders:
                logger.info("🔄 No open orders to sync")
                return []
            
            # Получаем открытые ордера с биржи
            symbol_to_fetch = self._determine_sync_symbol(local_orders)
            if not symbol_to_fetch:
                logger.warning("⚠️ No symbol available to fetch open orders. Skipping sync.")
                return []
            
            exchange_open_orders = await self.exchange_connector.fetch_open_orders(symbol=symbol_to_fetch)
            exchange_open_orders_map = {order['id']: order for order in exchange_open_orders}
            
            # Синхронизируем каждый локальный ордер
            for order in local_orders:
                if not order.exchange_id:
                    logger.warning(f"⚠️ Local order {order.order_id} has no exchange_id. Skipping sync.")
                    continue
                
                try:
                    if order.exchange_id in exchange_open_orders_map:
                        # Ордер есть на бирже и открыт - обновляем статус
                        exchange_data = exchange_open_orders_map[order.exchange_id]
                        old_status = order.status
                        order.update_from_exchange(exchange_data)
                        self.orders_repo.save(order)
                        updated_orders.append(order)
                        
                        if old_status != order.status:
                            logger.info(f"🔄 Synced order {order.order_id} status: {old_status} → {order.status}")
                    else:
                        # Ордера нет среди открытых на бирже - запрашиваем полный статус
                        await self._sync_closed_order(order, updated_orders)
                        
                except Exception as e:
                    logger.error(f"❌ Error syncing order {order.order_id}: {e}")
                    self._stats['errors'] += 1
            
            self._stats['sync_operations'] += 1
            logger.info(f"🔄 Synced {len(updated_orders)} orders with exchange")
            
            # Обновляем общую статистику
            await self._update_sync_statistics(len(updated_orders), len(local_orders))
            
            return updated_orders
            
        except Exception as e:
            logger.error(f"❌ Error syncing orders: {e}")
            self._stats['errors'] += 1
            return []
    
    async def _sync_closed_order(self, order: Order, updated_orders: List[Order]) -> None:
        """Синхронизация закрытого ордера"""
        try:
            # Запрашиваем полный статус ордера
            full_exchange_order = await self.exchange_connector.fetch_order(
                order.exchange_id,
                order.symbol
            )
            
            old_status = order.status
            order.update_from_exchange(full_exchange_order)
            self.orders_repo.save(order)
            updated_orders.append(order)
            
            logger.info(f"🔄 Synced closed order {order.order_id} status: {old_status} → {order.status}")
            
        except ccxt.OrderNotFound:
            # Ордер не найден на бирже вообще
            logger.warning(f"⚠️ Order {order.order_id} not found on exchange during sync")
            order.status = Order.STATUS_NOT_FOUND_ON_EXCHANGE
            order.closed_at = int(time.time() * 1000)
            self.orders_repo.save(order)
            updated_orders.append(order)
            self._stats['orders_not_found'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error fetching closed order {order.order_id}: {e}")
            self._stats['errors'] += 1
    
    def _get_open_orders(self) -> List[Order]:
        """Получить все открытые ордера"""
        all_orders = self.orders_repo.get_all()
        return [order for order in all_orders if order.is_open() or order.is_partially_filled()]
    
    def _determine_sync_symbol(self, local_orders: List[Order]) -> Optional[str]:
        """Определить символ для синхронизации"""
        # Используем настроенный символ или первый из локальных ордеров
        if self.currency_pair_symbol:
            return self.currency_pair_symbol
        
        if local_orders:
            return local_orders[0].symbol
        
        return None
    
    async def get_orders_by_status(self, status: str) -> List[Order]:
        """Получить ордера по статусу"""
        try:
            all_orders = self.orders_repo.get_all()
            return [order for order in all_orders if order.status == status]
            
        except Exception as e:
            logger.error(f"Error getting orders by status {status}: {e}")
            return []
    
    async def get_stale_orders(self, max_age_hours: int = 24) -> List[Order]:
        """Получить устаревшие ордера (старше указанного времени)"""
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
            
            return stale_orders
            
        except Exception as e:
            logger.error(f"Error getting stale orders: {e}")
            return []
    
    async def _update_monitoring_statistics(self, order: Order, event_type: str) -> None:
        """Обновление статистики мониторинга"""
        if not self.statistics_repo:
            return
        
        try:
            await self.statistics_repo.increment_counter(
                f"order_monitoring_{event_type}",
                StatisticCategory.ORDERS,
                tags={
                    "symbol": order.symbol,
                    "side": order.side.lower(),
                    "order_type": order.order_type.lower()
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating monitoring statistics: {e}")
    
    async def _update_sync_statistics(self, updated_count: int, total_count: int) -> None:
        """Обновление статистики синхронизации"""
        if not self.statistics_repo:
            return
        
        try:
            await self.statistics_repo.increment_counter(
                "orders_sync_operations",
                StatisticCategory.ORDERS
            )
            
            await self.statistics_repo.update_gauge(
                "orders_sync_updated_count",
                StatisticCategory.ORDERS,
                updated_count
            )
            
            await self.statistics_repo.update_gauge(
                "orders_sync_total_count",
                StatisticCategory.ORDERS,
                total_count
            )
            
        except Exception as e:
            logger.error(f"Error updating sync statistics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики сервиса"""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Сброс статистики"""
        self._stats = {
            'status_checks': 0,
            'orders_updated': 0,
            'orders_not_found': 0,
            'sync_operations': 0,
            'errors': 0
        }