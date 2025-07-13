# domain/services/orderbook_service.py
import asyncio
import logging
from typing import Optional
from .orderbook_analyzer import OrderBookAnalyzer, OrderBookMetrics, OrderBookSignal

logger = logging.getLogger(__name__)

class OrderBookService:
    """Сервис для мониторинга стакана в фоновом режиме"""

    def __init__(self, orderbook_analyzer: OrderBookAnalyzer):
        self.orderbook_analyzer = orderbook_analyzer
        self.latest_metrics: Optional[OrderBookMetrics] = None
        self.is_monitoring = False
        self._monitoring_task = None

    async def start_monitoring(self, exchange, symbol: str):
        """Запуск мониторинга стакана в фоновом режиме"""
        if self.is_monitoring:
            logger.warning("Мониторинг стакана уже запущен")
            return

        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitor_orderbook(exchange, symbol))
        logger.info(f"🔍 Запущен мониторинг стакана для {symbol}")

    async def stop_monitoring(self):
        """Остановка мониторинга стакана"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Мониторинг стакана остановлен")

    async def _monitor_orderbook(self, exchange, symbol: str):
        """Фоновый мониторинг стакана"""
        try:
            async for metrics in self.orderbook_analyzer.get_orderbook_stream(exchange, symbol):
                if not self.is_monitoring:
                    break

                self.latest_metrics = metrics
                await asyncio.sleep(0.1)  # Небольшая пауза

        except asyncio.CancelledError:
            logger.info("Мониторинг стакана отменен")
        except Exception as e:
            logger.error(f"Ошибка в мониторинге стакана: {e}")
            self.is_monitoring = False

    def get_latest_metrics(self) -> Optional[OrderBookMetrics]:
        """Получение последних метрик стакана"""
        return self.latest_metrics

    async def get_current_metrics(self, exchange, symbol: str) -> Optional[OrderBookMetrics]:
        """Получение текущих метрик стакана (разовый запрос)"""
        try:
            orderbook = await exchange.fetch_order_book(symbol)
            return self.orderbook_analyzer.analyze_orderbook(orderbook)
        except Exception as e:
            logger.error(f"Ошибка получения стакана: {e}")
            return None

    def is_orderbook_healthy(self) -> bool:
        """Проверка здоровья стакана"""
        if not self.latest_metrics:
            return False

        return (
                self.latest_metrics.signal != OrderBookSignal.REJECT and
                self.latest_metrics.bid_ask_spread < self.orderbook_analyzer.max_spread_percent and
                self.latest_metrics.slippage_buy < 2.0
        )
