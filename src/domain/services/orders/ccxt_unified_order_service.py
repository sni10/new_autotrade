# domain/services/orders/ccxt_unified_order_service.py
import logging
from typing import Optional, Dict, List, Any, Tuple
import asyncio

from src.domain.entities.order import Order, OrderValidationResult, OrderExecutionResult
from src.domain.repositories.i_orders_repository import IOrdersRepository
from src.infrastructure.connectors.ccxt_exchange_connector import CCXTExchangeConnector

# Импорт CCXT-совместимых сервисов
from src.domain.services.orders.ccxt_order_execution_service import CCXTOrderExecutionService

logger = logging.getLogger(__name__)


class CCXTUnifiedOrderService:
    """
    🚀 CCXT COMPLIANT Unified Order Service
    
    Унифицированный сервис для управления ордерами с полной поддержкой CCXT.
    Координирует работу CCXT-совместимых сервисов и обеспечивает единый интерфейс
    для всех операций с ордерами.
    
    Основные возможности:
    - Создание и размещение CCXT-совместимых ордеров
    - Синхронизация с биржей через CCXT Unified API
    - Управление жизненным циклом ордеров
    - Мониторинг и статистика
    - Валидация и риск-менеджмент
    """

    def __init__(
        self,
        orders_repository: IOrdersRepository,
        exchange_connector: CCXTExchangeConnector,
        execution_service: Optional[CCXTOrderExecutionService] = None,
        deal_service: Optional[Any] = None,
        statistics_repository: Optional[Any] = None
    ):
        self.orders_repository = orders_repository
        self.exchange_connector = exchange_connector
        self.deal_service = deal_service
        self.statistics_repository = statistics_repository
        
        # Создаем execution service если не предоставлен
        self.execution_service = execution_service or CCXTOrderExecutionService(
            exchange_connector=exchange_connector,
            orders_repository=orders_repository,
            deal_service=deal_service
        )
        
        # Статистика сервиса
        self.service_stats = {
            'orders_created': 0,
            'orders_placed': 0,
            'orders_cancelled': 0,
            'orders_filled': 0,
            'total_volume': 0.0,
            'sync_operations': 0
        }
        
        # Настройки
        self.auto_sync_enabled = True
        self.sync_interval_seconds = 30
        self._sync_task: Optional[asyncio.Task] = None

    # ===== CORE ORDER OPERATIONS =====

    async def create_ccxt_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None,
        deal_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        Создание и размещение CCXT-совместимого ордера
        """
        try:
            logger.info(f"Creating CCXT order: {side.upper()} {amount} {symbol}")
            
            # Делегируем выполнение execution service
            result = await self.execution_service.execute_ccxt_order(
                symbol=symbol,
                type=type,
                side=side,
                amount=amount,
                price=price,
                params=params,
                deal_id=deal_id
            )
            
            if result.success:
                self.service_stats['orders_created'] += 1
                self.service_stats['orders_placed'] += 1
                self.service_stats['total_volume'] += amount * (price or 0)
                
                logger.info(f"✅ CCXT order created successfully: {result.order.id}")
            else:
                logger.error(f"❌ CCXT order creation failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in create_ccxt_order: {e}")
            return OrderExecutionResult(
                success=False,
                error_message=str(e)
            )

    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        deal_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> OrderExecutionResult:
        """
        Создание лимитного ордера
        """
        return await self.create_ccxt_order(
            symbol=symbol,
            type='limit',
            side=side,
            amount=amount,
            price=price,
            params=params,
            deal_id=deal_id
        )

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        deal_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> OrderExecutionResult:
        """
        Создание маркет ордера
        """
        return await self.create_ccxt_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=amount,
            price=None,
            params=params,
            deal_id=deal_id
        )

    async def cancel_order(self, order: Order) -> bool:
        """
        Отмена ордера
        """
        try:
            success = await self.execution_service.cancel_ccxt_order(order)
            
            if success:
                self.service_stats['orders_cancelled'] += 1
                logger.info(f"✅ Order cancelled: {order.id}")
            else:
                logger.error(f"❌ Failed to cancel order: {order.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error cancelling order: {e}")
            return False

    async def cancel_order_by_id(self, order_id: str) -> bool:
        """
        Отмена ордера по ID
        """
        try:
            order = await self.orders_repository.get_order(order_id)
            if not order:
                logger.warning(f"Order not found for cancellation: {order_id}")
                return False
            
            return await self.cancel_order(order)
            
        except Exception as e:
            logger.error(f"❌ Error cancelling order by ID {order_id}: {e}")
            return False

    # ===== ORDER RETRIEVAL METHODS =====

    async def get_order(self, order_id: str) -> Optional[Order]:
        """
        Получение ордера по ID
        """
        return await self.orders_repository.get_order(order_id)

    async def get_order_by_local_id(self, local_order_id: int) -> Optional[Order]:
        """
        Получение ордера по локальному ID
        """
        return await self.orders_repository.get_order_by_local_id(local_order_id)

    async def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Получение активных ордеров
        """
        if symbol:
            all_orders = await self.orders_repository.get_orders_by_symbol(symbol)
            return [order for order in all_orders if order.status in ['open', 'pending', 'partial']]
        else:
            return await self.orders_repository.get_active_orders()

    async def get_orders_by_deal_id(self, deal_id: str) -> List[Order]:
        """
        Получение ордеров по ID сделки
        """
        return await self.orders_repository.get_orders_by_deal_id(deal_id)

    async def get_recent_orders(self, limit: int = 100) -> List[Order]:
        """
        Получение последних ордеров
        """
        return await self.orders_repository.get_recent_orders(limit)

    # ===== SYNCHRONIZATION METHODS =====

    async def sync_order_with_exchange(self, order: Order) -> Order:
        """
        Синхронизация ордера с биржей
        """
        try:
            synced_order = await self.execution_service.sync_order_with_exchange(order)
            self.service_stats['sync_operations'] += 1
            
            # Обновляем статистику по исполненным ордерам
            if synced_order.is_fully_filled() and order.status != 'closed':
                self.service_stats['orders_filled'] += 1
            
            return synced_order
            
        except Exception as e:
            logger.error(f"Failed to sync order {order.id}: {e}")
            return order

    async def sync_all_active_orders(self) -> List[Order]:
        """
        Синхронизация всех активных ордеров
        """
        try:
            synced_orders = await self.execution_service.sync_all_active_orders()
            self.service_stats['sync_operations'] += len(synced_orders)
            
            logger.info(f"Synced {len(synced_orders)} active orders")
            return synced_orders
            
        except Exception as e:
            logger.error(f"Failed to sync all active orders: {e}")
            return []

    async def start_auto_sync(self):
        """
        Запуск автоматической синхронизации
        """
        if self._sync_task and not self._sync_task.done():
            logger.warning("Auto sync already running")
            return

        if not self.auto_sync_enabled:
            logger.warning("Auto sync disabled")
            return

        logger.info(f"Starting auto sync with interval {self.sync_interval_seconds}s")
        self._sync_task = asyncio.create_task(self._auto_sync_loop())

    async def stop_auto_sync(self):
        """
        Остановка автоматической синхронизации
        """
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            logger.info("Auto sync stopped")

    async def _auto_sync_loop(self):
        """
        Цикл автоматической синхронизации
        """
        try:
            while True:
                try:
                    await self.sync_all_active_orders()
                    await asyncio.sleep(self.sync_interval_seconds)
                except Exception as e:
                    logger.error(f"Error in auto sync loop: {e}")
                    await asyncio.sleep(self.sync_interval_seconds)
                    
        except asyncio.CancelledError:
            logger.info("Auto sync loop cancelled")

    # ===== BALANCE AND VALIDATION METHODS =====

    async def check_sufficient_balance(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float] = None
    ) -> Tuple[bool, str, float]:
        """
        Проверка достаточности баланса
        """
        return await self.exchange_connector.check_sufficient_balance(
            symbol, side, amount, price
        )

    async def validate_order_params(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: Optional[float] = None
    ) -> OrderValidationResult:
        """
        Валидация параметров ордера
        """
        try:
            # Создаем временный ордер для валидации
            temp_order = Order(
                symbol=symbol,
                type=type,
                side=side,
                amount=amount,
                price=price
            )
            
            # Используем CCXT валидацию
            is_valid, errors = temp_order.validate_ccxt_compliance()
            
            if not is_valid:
                return OrderValidationResult(
                    is_valid=False,
                    errors=errors
                )

            # Дополнительные проверки
            market_info = await self.exchange_connector.get_market_info(symbol)
            
            # Проверяем лимиты
            min_amount = market_info['limits']['amount']['min']
            if amount < min_amount:
                return OrderValidationResult(
                    is_valid=False,
                    errors=[f"Amount {amount} below minimum {min_amount}"]
                )

            return OrderValidationResult(is_valid=True)

        except Exception as e:
            return OrderValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )

    # ===== STATISTICS AND MONITORING =====

    async def get_order_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики ордеров
        """
        try:
            # Статистика из репозитория
            repo_stats = await self.orders_repository.get_order_statistics()
            
            # Статистика сервиса
            service_stats = self.service_stats.copy()
            
            # Статистика исполнения
            execution_stats = self.execution_service.execution_stats
            
            # Общее количество ордеров
            total_orders = await self.orders_repository.count_active_orders()
            
            return {
                'service_stats': service_stats,
                'repository_stats': repo_stats,
                'execution_stats': execution_stats,
                'total_active_orders': total_orders,
                'auto_sync_enabled': self.auto_sync_enabled,
                'sync_interval_seconds': self.sync_interval_seconds
            }
            
        except Exception as e:
            logger.error(f"Failed to get order statistics: {e}")
            return {'error': str(e)}

    async def get_service_health(self) -> Dict[str, Any]:
        """
        Проверка здоровья сервиса
        """
        try:
            # Проверка репозитория
            repo_health = await self.orders_repository.health_check()
            
            # Проверка exchange connector
            exchange_info = self.exchange_connector.get_exchange_info()
            
            # Проверка автосинхронизации
            auto_sync_status = {
                'enabled': self.auto_sync_enabled,
                'running': self._sync_task and not self._sync_task.done() if self._sync_task else False,
                'interval_seconds': self.sync_interval_seconds
            }
            
            return {
                'status': 'healthy',
                'repository_health': repo_health,
                'exchange_info': exchange_info,
                'auto_sync': auto_sync_status,
                'service_stats': self.service_stats
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    # ===== EMERGENCY OPERATIONS =====

    async def emergency_cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Экстренная отмена всех ордеров
        """
        logger.warning("🚨 EMERGENCY: Cancelling all orders through unified service")
        
        try:
            cancelled_count = await self.execution_service.emergency_cancel_all_orders(symbol)
            self.service_stats['orders_cancelled'] += cancelled_count
            
            return cancelled_count
            
        except Exception as e:
            logger.error(f"Emergency cancellation failed: {e}")
            return 0

    # ===== CONFIGURATION =====

    def configure_service(
        self,
        auto_sync_enabled: Optional[bool] = None,
        sync_interval_seconds: Optional[int] = None
    ):
        """
        Настройка сервиса
        """
        if auto_sync_enabled is not None:
            self.auto_sync_enabled = auto_sync_enabled
            
        if sync_interval_seconds is not None:
            self.sync_interval_seconds = sync_interval_seconds
        
        logger.info(f"Service configured: auto_sync={self.auto_sync_enabled}, interval={self.sync_interval_seconds}s")

    def reset_statistics(self):
        """
        Сброс статистики
        """
        self.service_stats = {
            'orders_created': 0,
            'orders_placed': 0,
            'orders_cancelled': 0,
            'orders_filled': 0,
            'total_volume': 0.0,
            'sync_operations': 0
        }
        
        # Сбрасываем статистику execution service
        self.execution_service.reset_statistics()
        
        logger.info("Service statistics reset")

    # ===== LEGACY COMPATIBILITY METHODS =====

    async def create_and_place_buy_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: Optional[int] = None,
        order_type: str = 'limit'
    ) -> OrderExecutionResult:
        """
        LEGACY: Создание и размещение BUY ордера (для обратной совместимости)
        """
        return await self.create_ccxt_order(
            symbol=symbol,
            type=order_type.lower(),
            side='buy',
            amount=amount,
            price=price,
            deal_id=str(deal_id) if deal_id else None
        )

    async def create_local_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: Optional[int] = None,
        order_type: str = 'limit'
    ) -> OrderExecutionResult:
        """
        LEGACY: Создание локального SELL ордера (для обратной совместимости)
        """
        # Создаем локальный ордер (не размещаем на бирже)
        local_order = Order(
            symbol=symbol,
            type=order_type.lower(),
            side='sell',
            amount=amount,
            price=price,
            status=Order.STATUS_PENDING,
            deal_id=deal_id
        )
        
        # Сохраняем в репозитории
        success = await self.orders_repository.save_order(local_order)
        
        if success:
            self.service_stats['orders_created'] += 1
            return OrderExecutionResult(
                success=True,
                order=local_order
            )
        else:
            return OrderExecutionResult(
                success=False,
                error_message="Failed to save local SELL order"
            )

    # ===== CLEANUP =====

    async def close(self):
        """
        Закрытие сервиса и освобождение ресурсов
        """
        await self.stop_auto_sync()
        logger.info("CCXT Unified Order Service closed")

    def __repr__(self):
        return (f"CCXTUnifiedOrderService("
                f"exchange={self.exchange_connector.exchange_name}, "
                f"orders_created={self.service_stats['orders_created']}, "
                f"auto_sync={'ON' if self.auto_sync_enabled else 'OFF'})")


# ===== FACTORY FUNCTION =====

def create_ccxt_unified_order_service(
    orders_repository: IOrdersRepository,
    exchange_connector: CCXTExchangeConnector,
    deal_service: Optional[Any] = None,
    statistics_repository: Optional[Any] = None
) -> CCXTUnifiedOrderService:
    """
    Factory function для создания CCXT Unified Order Service
    """
    return CCXTUnifiedOrderService(
        orders_repository=orders_repository,
        exchange_connector=exchange_connector,
        deal_service=deal_service,
        statistics_repository=statistics_repository
    )