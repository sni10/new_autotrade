import logging
from typing import Optional, Dict, List, Any, Tuple

from src.domain.entities.order import Order, OrderValidationResult, OrderExecutionResult
from src.domain.factories.order_factory import OrderFactory
from src.infrastructure.repositories.orders_repository import OrdersRepository
from src.infrastructure.connectors.exchange_connector import CcxtExchangeConnector

# Импорт специализированных сервисов
from src.domain.services.orders.order_placement_service import OrderPlacementService
from src.domain.services.orders.order_monitoring_service import OrderMonitoringService
from src.domain.services.orders.order_validation_service import OrderValidationService
from src.domain.services.orders.balance_service import BalanceService
from src.domain.services.orders.order_cancellation_service import OrderCancellationService

from src.domain.repositories.i_statistics_repository import IStatisticsRepository

logger = logging.getLogger(__name__)


class UnifiedOrderService:
    """
    Унифицированный сервис для управления ордерами.
    
    Координирует работу специализированных сервисов, соблюдающих принцип SRP:
    - OrderPlacementService: размещение ордеров
    - OrderMonitoringService: мониторинг статусов
    - OrderValidationService: валидация параметров
    - BalanceService: проверка балансов
    - OrderCancellationService: отмена ордеров
    
    Этот сервис предоставляет единый интерфейс для всех операций с ордерами,
    но делегирует выполнение специализированным сервисам.
    """
    
    def __init__(
        self,
        orders_repo: OrdersRepository,
        order_factory: OrderFactory,
        exchange_connector: CcxtExchangeConnector,
        balance_service: BalanceService,  # ❗️ ИНЪЕКЦИЯ ЗАВИСИМОСТИ
        statistics_repo: Optional[IStatisticsRepository] = None,
        currency_pair_symbol: Optional[str] = None
    ):
        self.orders_repo = orders_repo
        self.order_factory = order_factory
        self.exchange_connector = exchange_connector
        self.statistics_repo = statistics_repo
        self.currency_pair_symbol = currency_pair_symbol
        
        # Инициализация специализированных сервисов
        # BalanceService теперь передается извне
        self.balance_service = balance_service
        
        self.placement_service = OrderPlacementService(
            self.balance_service, # ❗️ ПЕРЕДАЕМ СЕРВИС БАЛАНСА
            orders_repo, 
            order_factory, 
            exchange_connector, 
            statistics_repo
        )
        
        self.monitoring_service = OrderMonitoringService(
            orders_repo, exchange_connector, statistics_repo, currency_pair_symbol
        )
        
        self.validation_service = OrderValidationService(
            self.balance_service, # ❗️ ПЕРЕДАЕМ СЕРВИС БАЛАНСА
            exchange_connector, 
            statistics_repo
        )
        
        self.cancellation_service = OrderCancellationService(
            orders_repo, exchange_connector, statistics_repo
        )
        
        self._stats = {
            'total_operations': 0,
            'delegation_errors': 0
        }
    
    # ================================
    # РАЗМЕЩЕНИЕ ОРДЕРОВ
    # ================================
    
    async def create_and_place_buy_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        Создание и размещение BUY ордера с полной валидацией
        """
        try:
            self._stats['total_operations'] += 1
            
            # 1. Валидация параметров
            validation_result = await self.validation_service.validate_order_params(
                symbol, Order.SIDE_BUY, amount, price, order_type
            )
            if not validation_result.is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )
            
            # 2. Проверка баланса
            balance_check = await self.balance_service.check_sufficient_balance(
                symbol, Order.SIDE_BUY, amount, price
            )
            if not balance_check[0]:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Insufficient balance: need {amount * price:.4f} {balance_check[1]}, have {balance_check[2]:.4f}"
                )
            
            # 3. Размещение ордера
            return await self.placement_service.place_buy_order(
                symbol, amount, price, deal_id, order_type, client_order_id
            )
            
        except Exception as e:
            logger.error(f"❌ Error in create_and_place_buy_order: {e}")
            self._stats['delegation_errors'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Service delegation error: {str(e)}"
            )
    
    async def create_and_place_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        Создание и размещение SELL ордера с полной валидацией
        """
        try:
            self._stats['total_operations'] += 1
            
            # 1. Валидация параметров
            validation_result = await self.validation_service.validate_order_params(
                symbol, Order.SIDE_SELL, amount, price, order_type
            )
            if not validation_result.is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )
            
            # 2. Проверка баланса
            balance_check = await self.balance_service.check_sufficient_balance(
                symbol, Order.SIDE_SELL, amount, price
            )
            if not balance_check[0]:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Insufficient balance: need {amount:.4f} {balance_check[1]}, have {balance_check[2]:.4f}"
                )
            
            # 3. Размещение ордера
            return await self.placement_service.place_sell_order(
                symbol, amount, price, deal_id, order_type, client_order_id
            )
            
        except Exception as e:
            logger.error(f"❌ Error in create_and_place_sell_order: {e}")
            self._stats['delegation_errors'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Service delegation error: {str(e)}"
            )
    
    async def create_local_sell_order(
        self,
        symbol: str,
        amount: float,
        price: float,
        deal_id: int,
        order_type: str = Order.TYPE_LIMIT,
        client_order_id: Optional[str] = None
    ) -> OrderExecutionResult:
        """
        Создание локального SELL ордера без размещения на бирже
        """
        try:
            self._stats['total_operations'] += 1
            
            # Валидация параметров
            validation_result = await self.validation_service.validate_order_params(
                symbol, Order.SIDE_SELL, amount, price, order_type
            )
            if not validation_result.is_valid:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Validation failed: {', '.join(validation_result.errors)}"
                )
            
            # Создание локального ордера
            order = self.order_factory.create_sell_order(
                symbol=symbol,
                amount=amount,
                price=price,
                deal_id=deal_id,
                order_type=order_type,
                client_order_id=client_order_id
            )
            
            order.status = Order.STATUS_PENDING
            self.orders_repo.save(order)
            
            logger.info(f"✅ LOCAL SELL order {order.order_id} created with PENDING status")
            
            return OrderExecutionResult(
                success=True,
                order=order,
                error_message="Created locally with PENDING status"
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating local SELL order: {e}")
            self._stats['delegation_errors'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def place_existing_order(self, order: Order) -> OrderExecutionResult:
        """
        Размещение существующего локального ордера на бирже
        """
        try:
            self._stats['total_operations'] += 1
            
            # Проверка баланса перед размещением
            balance_check = await self.balance_service.check_sufficient_balance(
                order.symbol, order.side, order.amount, order.price
            )
            if not balance_check[0]:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Insufficient balance: need {order.amount * order.price:.4f} {balance_check[1]}, have {balance_check[2]:.4f}"
                )
            
            # Размещение ордера
            return await self.placement_service.place_existing_order(order)
            
        except Exception as e:
            logger.error(f"❌ Error placing existing order: {e}")
            self._stats['delegation_errors'] += 1
            return OrderExecutionResult(
                success=False,
                error_message=f"Service delegation error: {str(e)}"
            )
    
    # ================================
    # МОНИТОРИНГ ОРДЕРОВ
    # ================================
    
    async def get_order_status(self, order: Order) -> Optional[Order]:
        """Проверка статуса ордера"""
        try:
            return await self.monitoring_service.check_order_status(order)
        except Exception as e:
            logger.error(f"❌ Error getting order status: {e}")
            self._stats['delegation_errors'] += 1
            return order
    
    async def sync_orders_with_exchange(self) -> List[Order]:
        """Синхронизация всех открытых ордеров с биржей"""
        try:
            return await self.monitoring_service.sync_orders_with_exchange()
        except Exception as e:
            logger.error(f"❌ Error syncing orders: {e}")
            self._stats['delegation_errors'] += 1
            return []
    
    # ================================
    # ОТМЕНА ОРДЕРОВ
    # ================================
    
    async def cancel_order(self, order: Order, reason: str = "User request") -> Optional[Order]:
        """Отмена ордера"""
        try:
            return await self.cancellation_service.cancel_order(order, reason)
        except Exception as e:
            logger.error(f"❌ Error cancelling order: {e}")
            self._stats['delegation_errors'] += 1
            return None
    
    async def emergency_cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """Экстренная отмена всех ордеров"""
        try:
            return await self.cancellation_service.emergency_cancel_all_orders(symbol)
        except Exception as e:
            logger.error(f"❌ Error in emergency cancellation: {e}")
            self._stats['delegation_errors'] += 1
            return 0
    
    # ================================
    # ИНФОРМАЦИОННЫЕ МЕТОДЫ
    # ================================
    
    def get_orders_by_deal(self, deal_id: int) -> List[Order]:
        """Получить все ордера по ID сделки"""
        return self.orders_repo.get_all_by_deal(deal_id)
    
    def get_open_orders(self) -> List[Order]:
        """Получить все открытые ордера"""
        all_orders = self.orders_repo.get_all()
        return [order for order in all_orders if order.is_open() or order.is_partially_filled()]
    
    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Получить ордер по ID"""
        return self.orders_repo.get_by_id(order_id)
    
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Получить все ордера по символу"""
        all_orders = self.orders_repo.get_all()
        return [order for order in all_orders if order.symbol == symbol]
    
    # ================================
    # ПРОВЕРКА БАЛАНСОВ
    # ================================
    
    async def get_account_balance(self, force_refresh: bool = False) -> Dict[str, Dict[str, float]]:
        """Получение баланса аккаунта"""
        try:
            return await self.balance_service.get_account_balance(force_refresh)
        except Exception as e:
            logger.error(f"❌ Error getting account balance: {e}")
            self._stats['delegation_errors'] += 1
            return {}
    
    async def check_sufficient_balance(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> Tuple[bool, str, float]:
        """Проверка достаточности баланса"""
        try:
            return await self.balance_service.check_sufficient_balance(symbol, side, amount, price)
        except Exception as e:
            logger.error(f"❌ Error checking balance: {e}")
            self._stats['delegation_errors'] += 1
            return False, "ERROR", 0.0
    
    # ================================
    # СТАТИСТИКА И МОНИТОРИНГ
    # ================================
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Получение объединенной статистики всех сервисов"""
        try:
            return {
                "unified_service_stats": self._stats.copy(),
                "placement_service_stats": self.placement_service.get_stats(),
                "monitoring_service_stats": self.monitoring_service.get_stats(),
                "validation_service_stats": self.validation_service.get_stats(),
                "balance_service_stats": self.balance_service.get_stats(),
                "cancellation_service_stats": self.cancellation_service.get_stats()
            }
        except Exception as e:
            logger.error(f"❌ Error getting comprehensive statistics: {e}")
            return {"error": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение совместимой статистики (для обратной совместимости)"""
        try:
            all_stats = self.get_comprehensive_statistics()
            
            # Агрегируем основные метрики для совместимости
            placement_stats = all_stats.get("placement_service_stats", {})
            monitoring_stats = all_stats.get("monitoring_service_stats", {})
            cancellation_stats = all_stats.get("cancellation_service_stats", {})
            
            # Подсчитываем общие метрики
            orders_created = placement_stats.get('orders_placed', 0)
            orders_executed = placement_stats.get('orders_placed', 0)  # В новой архитектуре размещение = исполнение
            orders_failed = placement_stats.get('orders_failed', 0)
            orders_cancelled = cancellation_stats.get('orders_cancelled', 0)
            
            total_orders = len(self.orders_repo.get_all())
            open_orders = len(self.get_open_orders())
            
            return {
                'orders_created': orders_created,
                'orders_executed': orders_executed,
                'orders_failed': orders_failed,
                'orders_cancelled': orders_cancelled,
                'total_fees': 0.0,  # Эта метрика перенесена в статистику
                'total_orders': total_orders,
                'open_orders': open_orders,
                'success_rate': (orders_executed / max(orders_created, 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {"error": str(e)}
    
    def reset_statistics(self) -> None:
        """Сброс статистики всех сервисов"""
        try:
            self._stats = {
                'total_operations': 0,
                'delegation_errors': 0
            }
            
            self.placement_service.reset_stats()
            self.monitoring_service.reset_stats()
            self.validation_service.reset_stats()
            self.balance_service.reset_stats()
            self.cancellation_service.reset_stats()
            
        except Exception as e:
            logger.error(f"❌ Error resetting statistics: {e}")
    
    def save_order(self, order: Order) -> None:
        """Сохранение ордера в репозиторий (для обратной совместимости)"""
        self.orders_repo.save(order)
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка состояния всех компонентов"""
        health = {
            "status": "healthy",
            "services": {},
            "timestamp": int(__import__('time').time() * 1000)
        }
        
        try:
            # Проверяем каждый сервис
            services = [
                ("placement", self.placement_service),
                ("monitoring", self.monitoring_service),
                ("validation", self.validation_service),
                ("balance", self.balance_service),
                ("cancellation", self.cancellation_service)
            ]
            
            for name, service in services:
                try:
                    stats = service.get_stats()
                    health["services"][name] = {
                        "status": "healthy",
                        "stats": stats
                    }
                except Exception as e:
                    health["services"][name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health