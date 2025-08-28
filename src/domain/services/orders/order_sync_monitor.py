# src/domain/services/orders/order_sync_monitor.py
import asyncio
import logging
from typing import List
from domain.services.orders.order_service import OrderService
from domain.entities.order import Order

logger = logging.getLogger(__name__)

class OrderSyncMonitor:
    """
    Периодическая синхронизация всех ордеров с биржей.
    
    Регулярно обновляет статусы всех открытых ордеров с биржи,
    логирует изменения и ведет статистику синхронизации.
    """

    def __init__(self, order_service: OrderService, sync_interval_seconds: int = 30):
        self.order_service = order_service
        self.sync_interval_seconds = sync_interval_seconds
        self.stats = {
            'syncs_performed': 0,
            'orders_updated': 0,
            'status_changes': 0,
            'fill_changes': 0,
            'errors': 0
        }
        self._is_running = False

    async def start_monitoring(self):
        """Запуск синхронизации в фоновом режиме"""
        if self._is_running:
            logger.warning("⚠️ OrderSyncMonitor уже запущен")
            return
            
        self._is_running = True
        logger.info(f"🔄 Запуск синхронизации ордеров (каждые {self.sync_interval_seconds}с)")
        
        while self._is_running:
            try:
                await self.sync_all_orders()
                await asyncio.sleep(self.sync_interval_seconds)
            except Exception as e:
                logger.error(f"❌ Ошибка в синхронизации ордеров: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(30)  # Пауза при ошибке

    def stop_monitoring(self):
        """Остановка синхронизации"""
        self._is_running = False
        logger.info("🔴 Синхронизация ордеров остановлена")

    async def sync_all_orders(self):
        """Синхронизация всех открытых ордеров с биржей"""
        try:
            self.stats['syncs_performed'] += 1
            open_orders = self.order_service.get_open_orders()
            
            if not open_orders:
                logger.debug("ℹ️ Нет открытых ордеров для синхронизации")
                return
            
            logger.debug(f"🔄 Синхронизируем {len(open_orders)} открытых ордеров")
            
            for order in open_orders:
                if order.exchange_id:  # Только размещенные на бирже
                    await self._sync_single_order(order)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации ордеров: {e}")
            self.stats['errors'] += 1

    async def _sync_single_order(self, order: Order):
        """Синхронизация одного ордера с биржей"""
        try:
            # Сохраняем старые значения для сравнения
            old_status = order.status
            old_filled = getattr(order, 'filled', 0.0)
            
            # Обновляем статус с биржи
            updated_order = await self.order_service.get_order_status(order)
            
            # Проверяем изменения и логируем их
            status_changed = old_status != updated_order.status
            filled_changed = old_filled != getattr(updated_order, 'filled', 0.0)
            
            if status_changed or filled_changed:
                self.stats['status_changes'] += 1 if status_changed else 0
                self.stats['fill_changes'] += 1 if filled_changed else 0
                
                fill_percentage = updated_order.get_fill_percentage() if hasattr(updated_order, 'get_fill_percentage') else 0.0
                
                logger.info(f"📊 ОБНОВЛЕНИЕ: {updated_order.order_id} "
                           f"статус: {old_status}→{updated_order.status}"
                           f"{', заполнено: ' + str(old_filled) + '→' + str(getattr(updated_order, 'filled', 0.0)) if filled_changed else ''} "
                           f"({fill_percentage:.1%})")
            
            self.stats['orders_updated'] += 1
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации ордера {order.order_id}: {e}")
            self.stats['errors'] += 1

    def get_statistics(self) -> dict:
        """Получение статистики синхронизации"""
        return {
            'running': self._is_running,
            'sync_interval_seconds': self.sync_interval_seconds,
            **self.stats
        }

    def configure(self, sync_interval_seconds: int = None):
        """Изменение настроек синхронизации"""
        if sync_interval_seconds is not None:
            self.sync_interval_seconds = sync_interval_seconds
            
        logger.info(f"⚙️ Настройки синхронизации обновлены: интервал={self.sync_interval_seconds}с")