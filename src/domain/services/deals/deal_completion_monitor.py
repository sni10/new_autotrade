# domain/services/deals/deal_completion_monitor.py
import asyncio
import logging
from typing import List

from src.domain.services.deals.deal_service import DealService

logger = logging.getLogger(__name__)


class DealCompletionMonitor:
    """
    🎯 Мониторинг завершения сделок
    
    Проверяет открытые сделки и автоматически закрывает их
    когда оба ордера (BUY и SELL) исполнены.
    """

    def __init__(
        self,
        deal_service: DealService,
        check_interval_seconds: int = 30
    ):
        self.deal_service = deal_service
        self.check_interval_seconds = check_interval_seconds
        self.running = False
        self.stats = {
            'checks_performed': 0,
            'deals_completed': 0,
            'deals_monitored': 0
        }

    async def start_monitoring(self):
        """Запуск мониторинга в фоне"""
        if self.running:
            logger.warning("⚠️ DealCompletionMonitor already running")
            return
            
        self.running = True
        logger.info(f"🎯 Запуск мониторинга завершения сделок (проверка каждые {self.check_interval_seconds}с)")
        
        while self.running:
            try:
                await self.check_deal_completion()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"❌ Ошибка в мониторинге завершения сделок: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке

    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        logger.info("🔴 Мониторинг завершения сделок остановлен")

    async def check_deal_completion(self):
        """Проверка всех открытых сделок на завершение"""
        try:
            open_deals = self.deal_service.get_open_deals()
            
            if not open_deals:
                return
                
            self.stats['checks_performed'] += 1
            self.stats['deals_monitored'] = len(open_deals)
            
            logger.debug(f"🔍 Проверяем {len(open_deals)} открытых сделок на завершение")
            
            for deal in open_deals:
                completed = await self.deal_service.close_deal_if_completed(deal)
                if completed:
                    self.stats['deals_completed'] += 1
                    logger.info(f"✅ Сделка {deal.deal_id} автоматически завершена")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка проверки завершения сделок: {e}")

    def get_statistics(self) -> dict:
        """Получение статистики работы мониторинга"""
        return {
            'running': self.running,
            'check_interval_seconds': self.check_interval_seconds,
            **self.stats
        }

    def configure(self, check_interval_seconds: int = None):
        """Изменение настроек мониторинга"""
        if check_interval_seconds is not None:
            self.check_interval_seconds = check_interval_seconds
            
        logger.info(f"⚙️ Настройки мониторинга завершения сделок обновлены: {self.get_statistics()}")