# domain/services/risk/stop_loss_monitor.py
import asyncio
import logging
from typing import Dict, Optional

from src.domain.services.deals.deal_service import DealService
from src.domain.services.orders.order_execution_service import OrderExecutionService
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector
from src.domain.services.market_data.orderbook_analyzer import OrderBookAnalyzer, OrderBookSignal

logger = logging.getLogger(__name__)


class StopLossMonitor:
    """
    Мониторит открытые сделки и инициирует stop-loss при падении цены.
    """

    def __init__(
        self,
        deal_service: DealService,
        order_execution_service: OrderExecutionService,
        exchange_connector: CcxtExchangeConnector,
        orderbook_analyzer: OrderBookAnalyzer,
        stop_loss_percent: float,
        check_interval_seconds: int,
        warning_percent: float = 5.0,
        critical_percent: float = 10.0,
        emergency_percent: float = 15.0,
    ):
        self.deal_service = deal_service
        self.order_execution_service = order_execution_service
        self.exchange_connector = exchange_connector
        self.orderbook_analyzer = orderbook_analyzer
        self.stop_loss_percent = stop_loss_percent
        self.warning_percent = warning_percent
        self.critical_percent = critical_percent
        self.emergency_percent = emergency_percent
        self.check_interval_seconds = check_interval_seconds
        self._is_running = False
        self._warned_deals = set()  # Отслеживаем уже предупрежденные сделки
        self._stats = {
            "checks_performed": 0,
            "warnings_sent": 0,
            "support_breaks": 0,
            "emergency_liquidations": 0,
            "stop_loss_triggered": 0,
        }

    async def start_monitoring(self):
        """Запускает мониторинг в фоновом режиме."""
        self._is_running = True
        logger.info(f"🚀 StopLossMonitor запущен с умным анализом стакана:")
        logger.info(f"   - {self.warning_percent}% предупреждение + проверка поддержки")
        logger.info(f"   - {self.critical_percent}% маркет-ордер при пробитии support_level")
        logger.info(f"   - {self.emergency_percent}% принудительная ликвидация")
        logger.info(f"   - Интервал проверки: {self.check_interval_seconds} сек.")
        while self._is_running:
            await self.check_open_deals()
            await asyncio.sleep(self.check_interval_seconds)

    def stop_monitoring(self):
        """Останавливает мониторинг."""
        self._is_running = False
        logger.info("🔴 StopLossMonitor остановлен.")

    async def check_open_deals(self, current_price: float = None, cached_orderbook: dict = None):
        """Проверяет все открытые сделки на предмет срабатывания stop-loss с анализом стакана."""
        self._stats["checks_performed"] += 1
        open_deals = self.deal_service.get_open_deals()

        for deal in open_deals:
            if not deal.buy_order or not deal.buy_order.is_filled():
                continue

            try:
                # Используем переданную цену или получаем с биржи
                if current_price is None:
                    ticker = await self.exchange_connector.fetch_ticker(deal.currency_pair_id)
                    price = ticker['last']
                else:
                    price = current_price
                    
                entry_price = deal.buy_order.price
                
                # Используем кешированный стакан или получаем новый
                if cached_orderbook is not None:
                    orderbook_metrics = self.orderbook_analyzer.analyze_orderbook(cached_orderbook)
                else:
                    orderbook = await self.exchange_connector.fetch_order_book(deal.currency_pair_id)
                    orderbook_metrics = self.orderbook_analyzer.analyze_orderbook(orderbook)

                price_drop_percent = ((entry_price - price) / entry_price) * 100

                # Уровень 1: -5% предупреждение + проверка поддержки
                if price_drop_percent >= self.warning_percent:
                    await self._handle_warning_level(deal, price_drop_percent, orderbook_metrics)
                
                # Уровень 2: -10% маркет-ордер при пробитии support_level
                if price_drop_percent >= self.critical_percent:
                    await self._handle_critical_level(deal, price_drop_percent, price, orderbook_metrics)
                
                # Уровень 3: -15% принудительная ликвидация
                if price_drop_percent >= self.emergency_percent:
                    await self._handle_emergency_level(deal, price_drop_percent, orderbook_metrics)

            except Exception as e:
                logger.error(f"Ошибка при проверке stop-loss для сделки #{deal.deal_id}: {e}")

    async def _handle_warning_level(self, deal, price_drop_percent: float, orderbook_metrics):
        """Уровень 1: -5% предупреждение + проверка поддержки"""
        if deal.deal_id not in self._warned_deals:
            support_info = ""
            if orderbook_metrics.support_level:
                support_info = f" | Поддержка: {orderbook_metrics.support_level:.6f}"
            
            logger.warning(f"⚠️  ПРЕДУПРЕЖДЕНИЕ: Просадка {price_drop_percent:.2f}% для сделки #{deal.deal_id}{support_info}")
            logger.warning(f"   Дисбаланс объемов: {orderbook_metrics.volume_imbalance:.1f}%")
            
            self._warned_deals.add(deal.deal_id)
            self._stats["warnings_sent"] += 1

    async def _handle_critical_level(self, deal, price_drop_percent: float, current_price: float, orderbook_metrics):
        """Уровень 2: -10% маркет-ордер при пробитии support_level"""
        support_broken = False
        
        if orderbook_metrics.support_level and current_price <= orderbook_metrics.support_level:
            support_broken = True
            logger.error(f"🔴 ПРОБИТИЕ ПОДДЕРЖКИ! Цена {current_price:.6f} <= поддержка {orderbook_metrics.support_level:.6f}")
            self._stats["support_breaks"] += 1
        
        # Дополнительные критерии для маркет-ордера
        critical_conditions = [
            support_broken,
            orderbook_metrics.volume_imbalance < -20,  # Сильный дисбаланс в сторону продаж
            orderbook_metrics.signal == OrderBookSignal.STRONG_SELL,
            orderbook_metrics.slippage_sell > 2.0  # Высокий слиппедж
        ]
        
        if any(critical_conditions):
            logger.error(f"🚨 КРИТИЧЕСКИЙ УРОВЕНЬ! Сделка #{deal.deal_id} - просадка {price_drop_percent:.2f}%")
            logger.error(f"   Условия: support_broken={support_broken}, imbalance={orderbook_metrics.volume_imbalance:.1f}%")
            await self._create_market_sell_order(deal)
            self._stats["stop_loss_triggered"] += 1

    async def _handle_emergency_level(self, deal, price_drop_percent: float, orderbook_metrics):
        """Уровень 3: -15% принудительная ликвидация"""
        logger.critical(f"🆘 ЭКСТРЕННАЯ ЛИКВИДАЦИЯ! Сделка #{deal.deal_id} - просадка {price_drop_percent:.2f}%")
        logger.critical(f"   Принудительная продажа по рынку!")
        
        await self._create_market_sell_order(deal, force=True)
        self._stats["emergency_liquidations"] += 1
        self._stats["stop_loss_triggered"] += 1

    async def _create_market_sell_order(self, deal, force: bool = False):
        """Создает маркет-ордер на продажу для ликвидации позиции"""
        try:
            if deal.buy_order and deal.buy_order.is_filled():
                # Отменяем существующий лимитный sell-ордер если есть
                if deal.sell_order and not deal.sell_order.is_filled():
                    await self.order_execution_service.cancel_order(deal.sell_order)
                    logger.info(f"Отменен лимитный SELL ордер для сделки #{deal.deal_id}")
                
                # Создаем маркет-ордер на продажу
                filled_amount = deal.buy_order.filled_amount
                
                market_sell_order = await self.order_execution_service.create_market_sell_order(
                    deal.currency_pair_id,
                    filled_amount,
                    deal.deal_id
                )
                
                if market_sell_order:
                    deal.sell_order = market_sell_order
                    logger.info(f"✅ Создан маркет SELL ордер #{market_sell_order.order_id} для сделки #{deal.deal_id}")
                    
                    # Закрываем сделку
                    await self.deal_service.close_deal(deal)
                    logger.info(f"Сделка #{deal.deal_id} закрыта {'принудительно' if force else 'по стоп-лоссу'}")
                else:
                    logger.error(f"Не удалось создать маркет-ордер для сделки #{deal.deal_id}")
                    
        except Exception as e:
            logger.error(f"Ошибка при создании маркет-ордера для сделки #{deal.deal_id}: {e}")
            # В крайнем случае просто закрываем сделку
            await self.deal_service.close_deal(deal)

    async def trigger_stop_loss(self, deal):
        """Старый метод для обратной совместимости"""
        logger.warning(f"🚨 Вызван старый метод trigger_stop_loss для сделки #{deal.deal_id}")
        await self._create_market_sell_order(deal)

    def get_statistics(self) -> Dict:
        """Возвращает статистику работы монитора."""
        return self._stats
