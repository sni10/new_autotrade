# src/domain/services/monitoring/system_stats_monitor.py
import asyncio
import logging
from typing import Optional
from domain.services.orders.order_service import OrderService
from domain.services.deals.deal_service import DealService
from domain.services.orders.buy_order_monitor import BuyOrderMonitor
from domain.services.deals.deal_completion_monitor import DealCompletionMonitor
from domain.services.orders.order_sync_monitor import OrderSyncMonitor

logger = logging.getLogger(__name__)

class SystemStatsMonitor:
    """
    Периодический вывод детальной статистики всех компонентов системы.
    
    Собирает и логирует статистику от всех мониторов, сервисов ордеров и сделок
    для полного понимания состояния торговой системы.
    """

    def __init__(
        self,
        order_service: OrderService,
        deal_service: DealService,
        buy_order_monitor: Optional[BuyOrderMonitor] = None,
        deal_completion_monitor: Optional[DealCompletionMonitor] = None,
        order_sync_monitor: Optional[OrderSyncMonitor] = None,
        stats_interval_seconds: int = 60
    ):
        self.order_service = order_service
        self.deal_service = deal_service
        self.buy_order_monitor = buy_order_monitor
        self.deal_completion_monitor = deal_completion_monitor
        self.order_sync_monitor = order_sync_monitor
        self.stats_interval_seconds = stats_interval_seconds
        self._is_running = False

    async def start_monitoring(self):
        """Запуск периодического вывода статистики"""
        if self._is_running:
            logger.warning("⚠️ SystemStatsMonitor уже запущен")
            return
            
        self._is_running = True
        logger.info(f"📊 Запуск системной аналитики (каждые {self.stats_interval_seconds}с)")
        
        while self._is_running:
            try:
                await self.log_system_statistics()
                await asyncio.sleep(self.stats_interval_seconds)
            except Exception as e:
                logger.error(f"❌ Ошибка в системной аналитике: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке

    def stop_monitoring(self):
        """Остановка системной аналитики"""
        self._is_running = False
        logger.info("🔴 Системная аналитика остановлена")

    async def log_system_statistics(self):
        """Детальная статистика всей системы"""
        try:
            logger.info("=" * 80)
            logger.info("📊 СТАТИСТИКА ТОРГОВОЙ СИСТЕМЫ")
            logger.info("=" * 80)
            
            # Статистика ордеров
            await self._log_orders_statistics()
            
            # Статистика сделок
            await self._log_deals_statistics()
            
            # Статистика мониторов
            await self._log_monitors_statistics()
            
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Ошибка вывода статистики: {e}")

    async def _log_orders_statistics(self):
        """Статистика ордеров"""
        try:
            order_stats = self.order_service.get_statistics()
            open_orders = self.order_service.get_open_orders()
            
            # Разделяем по типам
            buy_orders = [o for o in open_orders if o.side == 'BUY']
            sell_orders = [o for o in open_orders if o.side == 'SELL']
            pending_orders = [o for o in open_orders if o.status == 'PENDING']
            
            logger.info(f"📋 ОРДЕРА:")
            logger.info(f"   • Всего: {order_stats['total_orders']}")
            logger.info(f"   • Открытых: {order_stats['open_orders']} (BUY: {len(buy_orders)}, SELL: {len(sell_orders)})")
            logger.info(f"   • Pending: {len(pending_orders)}")
            logger.info(f"   • Исполненных: {order_stats['completed_orders']}")
            logger.info(f"   • Отмененных: {order_stats['cancelled_orders']}")
            logger.info(f"   • Ошибок: {order_stats['failed_orders']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка статистики ордеров: {e}")

    async def _log_deals_statistics(self):
        """Статистика сделок"""
        try:
            deal_stats = self.deal_service.get_statistics()
            open_deals = self.deal_service.get_open_deals()
            
            logger.info(f"💼 СДЕЛКИ:")
            logger.info(f"   • Всего: {deal_stats['total_deals']}")
            logger.info(f"   • Открытых: {len(open_deals)}")
            logger.info(f"   • Закрытых: {deal_stats.get('completed_deals', 0)}")
            
            # Детали по открытым сделкам
            if open_deals:
                logger.info(f"   📈 Открытые сделки:")
                for deal in open_deals[:5]:  # Показываем первые 5
                    logger.info(f"      - Сделка {deal.deal_id}: {deal.symbol}, статус: {deal.status}")
                if len(open_deals) > 5:
                    logger.info(f"      ... и еще {len(open_deals) - 5} сделок")
            
        except Exception as e:
            logger.error(f"❌ Ошибка статистики сделок: {e}")

    async def _log_monitors_statistics(self):
        """Статистика мониторов"""
        try:
            logger.info(f"🔧 МОНИТОРЫ:")
            
            # BuyOrderMonitor
            if self.buy_order_monitor:
                buy_stats = self.buy_order_monitor.get_statistics()
                logger.info(f"   🕒 BUY МОНИТОР:")
                logger.info(f"      • Статус: {'🟢 Работает' if buy_stats['running'] else '🔴 Остановлен'}")
                logger.info(f"      • Проверок: {buy_stats['checks_performed']}")
                logger.info(f"      • Тухляков найдено: {buy_stats['stale_orders_found']}")
                logger.info(f"      • Ордеров отменено: {buy_stats['orders_cancelled']}")
                logger.info(f"      • Ордеров пересоздано: {buy_stats['orders_recreated']}")
                logger.info(f"      • Настройки: {buy_stats['max_age_minutes']}мин, {buy_stats['max_price_deviation_percent']}%")
            
            # DealCompletionMonitor
            if self.deal_completion_monitor:
                deal_stats = self.deal_completion_monitor.get_statistics()
                logger.info(f"   ✅ DEAL МОНИТОР:")
                logger.info(f"      • Проверок: {deal_stats['checks_performed']}")
                logger.info(f"      • Сделок отслеживается: {deal_stats['deals_monitored']}")
                logger.info(f"      • Сделок завершено: {deal_stats['deals_completed']}")
                logger.info(f"      • SELL ордеров размещено: {deal_stats.get('sell_orders_placed', 0)}")
            
            # OrderSyncMonitor
            if self.order_sync_monitor:
                sync_stats = self.order_sync_monitor.get_statistics()
                logger.info(f"   🔄 SYNC МОНИТОР:")
                logger.info(f"      • Статус: {'🟢 Работает' if sync_stats['running'] else '🔴 Остановлен'}")
                logger.info(f"      • Синхронизаций: {sync_stats['syncs_performed']}")
                logger.info(f"      • Ордеров обновлено: {sync_stats['orders_updated']}")
                logger.info(f"      • Изменений статуса: {sync_stats['status_changes']}")
                logger.info(f"      • Изменений заполнения: {sync_stats['fill_changes']}")
                logger.info(f"      • Ошибок: {sync_stats['errors']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка статистики мониторов: {e}")

    def get_statistics(self) -> dict:
        """Получение общей статистики системы"""
        return {
            'running': self._is_running,
            'stats_interval_seconds': self.stats_interval_seconds,
            'components': {
                'order_service': bool(self.order_service),
                'deal_service': bool(self.deal_service),
                'buy_order_monitor': bool(self.buy_order_monitor),
                'deal_completion_monitor': bool(self.deal_completion_monitor),
                'order_sync_monitor': bool(self.order_sync_monitor),
            }
        }