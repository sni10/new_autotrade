# domain/services/orders/ccxt_order_execution_service.py
import asyncio
import logging
import time
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from src.domain.entities.order import Order, OrderExecutionResult
from src.domain.entities.deal import Deal
from src.domain.entities.currency_pair import CurrencyPair
from src.infrastructure.connectors.ccxt_exchange_connector import CCXTExchangeConnector
from src.domain.repositories.i_orders_repository import IOrdersRepository

logger = logging.getLogger(__name__)


@dataclass
class CCXTTradingContext:
    """CCXT-совместимый контекст для выполнения торговых операций"""
    currency_pair: CurrencyPair
    current_price: float
    budget: float
    strategy_result: Any
    deal: Optional[Deal] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CCXTExecutionReport:
    """CCXT-совместимый отчет о выполнении торговой операции"""
    success: bool
    deal_id: Optional[str] = None  # UUID string
    buy_order: Optional[Order] = None
    sell_order: Optional[Order] = None
    total_cost: float = 0.0
    expected_profit: float = 0.0
    fees: float = 0.0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = None
    ccxt_data: Optional[Dict[str, Any]] = None  # Полные CCXT данные


class CCXTOrderExecutionService:
    """
    🚀 CCXT COMPLIANT Order Execution Service
    
    Полностью совместимый с CCXT сервис выполнения торговых операций:
    - Использует CCXT Unified API для всех операций
    - Возвращает данные в стандартном CCXT формате
    - Поддерживает полную трассировку ордеров
    - Интегрируется с CCXT-совместимым репозиторием
    """

    def __init__(
        self,
        exchange_connector: CCXTExchangeConnector,
        orders_repository: IOrdersRepository,
        deal_service: Optional[Any] = None  # DealService инжектируется опционально
    ):
        self.exchange_connector = exchange_connector
        self.orders_repository = orders_repository
        self.deal_service = deal_service
        
        # Статистика
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'average_execution_time_ms': 0.0,
            'ccxt_compliance_score': 100.0
        }
        
        # Настройки выполнения
        self.max_execution_time_sec = 30.0
        self.enable_risk_checks = True
        self.enable_balance_checks = True
        self.enable_slippage_protection = True
        self.enable_ccxt_validation = True

    # ===== MAIN EXECUTION METHODS =====

    async def execute_ccxt_order(
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
        🎯 ГЛАВНЫЙ метод выполнения CCXT-совместимого ордера
        
        Args:
            symbol: Торговая пара в CCXT формате (BTC/USDT)
            type: Тип ордера CCXT (limit, market, stop, etc.)
            side: Сторона CCXT (buy, sell)
            amount: Количество в базовой валюте
            price: Цена (для лимитных ордеров)
            params: CCXT параметры
            deal_id: ID сделки для связки
            
        Returns:
            OrderExecutionResult с CCXT данными
        """
        start_time = time.time()
        execution_id = f"ccxt_exec_{int(start_time * 1000)}"
        
        logger.info(f"🚀 [{execution_id}] Starting CCXT order execution: {side.upper()} {amount} {symbol}")
        
        try:
            # 1. Валидация входных параметров
            validation_result = await self._validate_ccxt_order_params(
                symbol, type, side, amount, price, params
            )
            if not validation_result.success:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"CCXT validation failed: {validation_result.error_message}"
                )

            # 2. Pre-execution проверки
            pre_check_result = await self._perform_ccxt_pre_checks(
                symbol, side, amount, price
            )
            if not pre_check_result[0]:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Pre-execution checks failed: {pre_check_result[1]}"
                )

            # 3. Создание локального Order объекта
            local_order = self._create_local_order(
                symbol, type, side, amount, price, params, deal_id
            )

            # 4. Сохранение в статусе PENDING
            await self.orders_repository.save_order(local_order)
            logger.debug(f"Order {local_order.local_order_id} saved in PENDING status")

            # 5. Размещение на бирже через CCXT
            ccxt_result = await self.exchange_connector.create_order(
                symbol=symbol,
                type=type,
                side=side,
                amount=amount,
                price=price,
                params=params or {}
            )

            # 6. Обновление локального ордера данными с биржи
            local_order.update_from_ccxt_response(ccxt_result)
            local_order.mark_as_placed_on_exchange(
                ccxt_result['id'],
                ccxt_result.get('timestamp')
            )

            # 7. Сохранение обновленного ордера
            await self.orders_repository.update_order(local_order)

            # 8. Обновление статистики
            execution_time = (time.time() - start_time) * 1000
            self._update_execution_stats(True, amount * (price or 0), 0, execution_time)

            logger.info(f"✅ [{execution_id}] CCXT order executed successfully: {ccxt_result['id']}")

            return OrderExecutionResult(
                success=True,
                order=local_order,
                exchange_response=ccxt_result
            )

        except Exception as e:
            # Обработка ошибок с сохранением в Order
            execution_time = (time.time() - start_time) * 1000
            self._update_execution_stats(False, 0.0, 0.0, execution_time)

            # Обновляем локальный ордер если он был создан
            if 'local_order' in locals():
                local_order.mark_as_failed(str(e))
                await self.orders_repository.update_order(local_order)

            logger.error(f"❌ [{execution_id}] CCXT order execution failed: {e}")
            
            return OrderExecutionResult(
                success=False,
                order=locals().get('local_order'),
                error_message=str(e)
            )

    async def execute_trading_strategy(
        self,
        currency_pair: CurrencyPair,
        strategy_result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CCXTExecutionReport:
        """
        🎯 Выполнение торговой стратегии с CCXT compliance
        """
        start_time = time.time()
        execution_id = f"ccxt_strategy_{int(start_time * 1000)}"
        
        logger.info(f"🚀 [{execution_id}] Starting CCXT strategy execution for {currency_pair.symbol}")
        
        try:
            # 1. Валидация и парсинг стратегии
            strategy_data = self._parse_strategy_result(strategy_result)
            if not strategy_data:
                return CCXTExecutionReport(
                    success=False,
                    error_message="Failed to parse strategy result"
                )

            # 2. Создание контекста
            context = CCXTTradingContext(
                currency_pair=currency_pair,
                current_price=strategy_data['buy_price'],
                budget=currency_pair.deal_quota,
                strategy_result=strategy_result,
                metadata=metadata or {}
            )

            # 3. Создание сделки (если deal_service доступен)
            deal = None
            if self.deal_service:
                deal = self.deal_service.create_new_deal(currency_pair)
                context.deal = deal
                logger.info(f"✅ [{execution_id}] Deal {deal.deal_id} created")

            # 4. Выполнение BUY ордера
            buy_result = await self.execute_ccxt_order(
                symbol=currency_pair.symbol,
                type='limit',
                side='buy',
                amount=strategy_data['buy_amount'],
                price=strategy_data['buy_price'],
                deal_id=str(deal.deal_id) if deal else None
            )

            if not buy_result.success:
                return CCXTExecutionReport(
                    success=False,
                    deal_id=str(deal.deal_id) if deal else None,
                    error_message=f"BUY order failed: {buy_result.error_message}"
                )

            buy_order = buy_result.order
            logger.info(f"✅ [{execution_id}] BUY order placed: {buy_order.id}")

            # 5. Создание локального SELL ордера (PENDING)
            sell_order = self._create_local_order(
                symbol=currency_pair.symbol,
                type='limit',
                side='sell',
                amount=strategy_data['sell_amount'],
                price=strategy_data['sell_price'],
                params={'timeInForce': 'GTC'},
                deal_id=str(deal.deal_id) if deal else None
            )
            
            # Сохраняем SELL ордер в PENDING статусе
            await self.orders_repository.save_order(sell_order)
            logger.info(f"✅ [{execution_id}] Local SELL order created: {sell_order.local_order_id}")

            # 6. Связывание ордеров со сделкой
            if deal and self.deal_service:
                deal.attach_orders(buy_order, sell_order)
                self.deal_service.save_deal(deal)

            # 7. Расчет финансовых показателей
            total_cost = buy_order.amount * buy_order.price
            expected_profit = (sell_order.amount * sell_order.price) - total_cost

            # 8. Обновление статистики
            execution_time = (time.time() - start_time) * 1000
            self._update_execution_stats(True, total_cost, 0, execution_time)

            # 9. Формирование отчета
            report = CCXTExecutionReport(
                success=True,
                deal_id=str(deal.deal_id) if deal else None,
                buy_order=buy_order,
                sell_order=sell_order,
                total_cost=total_cost,
                expected_profit=expected_profit,
                execution_time_ms=execution_time,
                ccxt_data={
                    'buy_ccxt_response': buy_result.exchange_response,
                    'strategy_data': strategy_data
                }
            )

            logger.info(f"🎉 [{execution_id}] CCXT strategy executed successfully!")
            logger.info(f"   💰 Cost: {total_cost:.4f} USDT")
            logger.info(f"   📈 Expected profit: {expected_profit:.4f} USDT")
            logger.info(f"   ⏱️ Execution time: {execution_time:.1f}ms")

            return report

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._update_execution_stats(False, 0.0, 0.0, execution_time)

            logger.error(f"❌ [{execution_id}] CCXT strategy execution failed: {e}")
            return CCXTExecutionReport(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                execution_time_ms=execution_time
            )

    # ===== ORDER MANAGEMENT METHODS =====

    async def cancel_ccxt_order(self, order: Order) -> bool:
        """
        Отмена CCXT ордера
        """
        try:
            if not order.id:
                logger.warning(f"Cannot cancel order without exchange ID: local_id={order.local_order_id}")
                return False

            # Отменяем на бирже
            ccxt_result = await self.exchange_connector.cancel_order(order.id, order.symbol)
            
            # Обновляем локальный ордер
            order.update_from_ccxt_response(ccxt_result)
            order.cancel_order("Cancelled by user")
            
            # Сохраняем изменения
            await self.orders_repository.update_order(order)
            
            logger.info(f"✅ CCXT order cancelled: {order.id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to cancel CCXT order {order.id}: {e}")
            return False

    async def sync_order_with_exchange(self, order: Order) -> Order:
        """
        Синхронизация ордера с биржей
        """
        try:
            if not order.id:
                logger.warning(f"Cannot sync order without exchange ID: local_id={order.local_order_id}")
                return order

            # Получаем актуальные данные с биржи
            ccxt_order = await self.exchange_connector.fetch_order(order.id, order.symbol)
            
            # Обновляем локальный ордер
            order.update_from_ccxt_response(ccxt_order)
            
            # Сохраняем изменения
            await self.orders_repository.update_order(order)
            
            logger.debug(f"Synced order {order.id} with exchange")
            return order

        except Exception as e:
            logger.error(f"Failed to sync order {order.id}: {e}")
            return order

    async def sync_all_active_orders(self) -> List[Order]:
        """
        Синхронизация всех активных ордеров с биржей
        """
        try:
            active_orders = await self.orders_repository.get_active_orders()
            synced_orders = []

            for order in active_orders:
                synced_order = await self.sync_order_with_exchange(order)
                synced_orders.append(synced_order)

            logger.info(f"Synced {len(synced_orders)} active orders with exchange")
            return synced_orders

        except Exception as e:
            logger.error(f"Failed to sync active orders: {e}")
            return []

    # ===== VALIDATION METHODS =====

    async def _validate_ccxt_order_params(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: Optional[float],
        params: Optional[Dict[str, Any]]
    ) -> OrderExecutionResult:
        """
        Валидация параметров CCXT ордера
        """
        try:
            # Проверка обязательных параметров
            if not symbol:
                return OrderExecutionResult(
                    success=False,
                    error_message="Symbol is required"
                )

            if type not in ['limit', 'market', 'stop', 'stop_limit']:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Invalid order type: {type}"
                )

            if side not in ['buy', 'sell']:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Invalid order side: {side}"
                )

            if amount <= 0:
                return OrderExecutionResult(
                    success=False,
                    error_message="Amount must be positive"
                )

            if type == 'limit' and (not price or price <= 0):
                return OrderExecutionResult(
                    success=False,
                    error_message="Price is required for limit orders"
                )

            # Проверка рыночных лимитов
            market_info = await self.exchange_connector.get_market_info(symbol)
            
            min_amount = market_info['limits']['amount']['min']
            if amount < min_amount:
                return OrderExecutionResult(
                    success=False,
                    error_message=f"Amount {amount} below minimum {min_amount}"
                )

            if price and type == 'limit':
                min_price = market_info['limits']['price']['min']
                max_price = market_info['limits']['price']['max']
                
                if price < min_price or price > max_price:
                    return OrderExecutionResult(
                        success=False,
                        error_message=f"Price {price} outside allowed range [{min_price}, {max_price}]"
                    )

            return OrderExecutionResult(success=True)

        except Exception as e:
            return OrderExecutionResult(
                success=False,
                error_message=f"Validation error: {str(e)}"
            )

    async def _perform_ccxt_pre_checks(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float]
    ) -> Tuple[bool, str]:
        """
        Предварительные проверки перед размещением CCXT ордера
        """
        try:
            # 1. Проверка баланса
            if self.enable_balance_checks:
                has_balance, currency, available = await self.exchange_connector.check_sufficient_balance(
                    symbol, side, amount, price
                )
                
                if not has_balance:
                    required = amount * (price or 0) if side == 'buy' else amount
                    return False, f"Insufficient {currency} balance: need {required:.8f}, have {available:.8f}"

            # 2. Проверка статуса биржи
            exchange_status = await self.exchange_connector.get_exchange_status()
            if exchange_status.get('status') != 'ok':
                return False, f"Exchange not available: {exchange_status.get('error', 'Unknown error')}"

            # 3. Проверка разумности цены (если указана)
            if price and self.enable_slippage_protection:
                ticker = await self.exchange_connector.fetch_ticker(symbol)
                market_price = ticker['last']
                
                price_diff = abs(price - market_price) / market_price
                if price_diff > 0.10:  # 10% отклонение
                    logger.warning(f"Price differs from market by {price_diff*100:.1f}%")

            return True, "All checks passed"

        except Exception as e:
            return False, f"Pre-check error: {str(e)}"

    # ===== HELPER METHODS =====

    def _create_local_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: Optional[float],
        params: Optional[Dict[str, Any]],
        deal_id: Optional[str]
    ) -> Order:
        """
        Создание локального Order объекта
        """
        current_time = int(time.time() * 1000)
        
        return Order(
            # CCXT поля
            id=None,  # Будет установлен после размещения
            clientOrderId=f"autotrade_{current_time}_{deal_id or 'standalone'}",
            datetime=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            timestamp=current_time,
            status=Order.STATUS_PENDING,
            symbol=symbol,
            type=type,
            timeInForce=params.get('timeInForce', Order.TIF_GTC) if params else Order.TIF_GTC,
            side=side,
            price=price,
            amount=amount,
            filled=0.0,
            remaining=amount,
            trades=[],
            fee={'cost': 0.0, 'currency': None, 'rate': None},
            info={},
            
            # AutoTrade поля
            deal_id=int(deal_id) if deal_id and deal_id.isdigit() else None,
            created_at=current_time,
            last_update=current_time,
            metadata=params or {}
        )

    def _parse_strategy_result(self, strategy_result: Any) -> Optional[Dict[str, Any]]:
        """
        Парсинг результата стратегии
        """
        try:
            if isinstance(strategy_result, dict) and "comment" in strategy_result:
                logger.warning(f"Strategy error: {strategy_result['comment']}")
                return None

            if isinstance(strategy_result, (tuple, list)) and len(strategy_result) >= 5:
                buy_price, buy_amount, sell_price, sell_amount, info_dict = strategy_result[:5]
                
                return {
                    'buy_price': float(buy_price),
                    'buy_amount': float(buy_amount),
                    'sell_price': float(sell_price),
                    'sell_amount': float(sell_amount),
                    'info': info_dict if isinstance(info_dict, dict) else {}
                }

            return None

        except Exception as e:
            logger.error(f"Error parsing strategy result: {e}")
            return None

    def _update_execution_stats(
        self,
        success: bool,
        volume: float,
        fees: float,
        execution_time_ms: float
    ):
        """
        Обновление статистики выполнения
        """
        self.execution_stats['total_executions'] += 1
        
        if success:
            self.execution_stats['successful_executions'] += 1
            self.execution_stats['total_volume'] += volume
            self.execution_stats['total_fees'] += fees
        else:
            self.execution_stats['failed_executions'] += 1

        # Обновляем среднее время выполнения
        total_time = (self.execution_stats['average_execution_time_ms'] * 
                     (self.execution_stats['total_executions'] - 1) + execution_time_ms)
        self.execution_stats['average_execution_time_ms'] = total_time / self.execution_stats['total_executions']

        # Обновляем CCXT compliance score
        if self.execution_stats['total_executions'] > 0:
            success_rate = self.execution_stats['successful_executions'] / self.execution_stats['total_executions']
            self.execution_stats['ccxt_compliance_score'] = success_rate * 100

    # ===== MONITORING AND STATISTICS =====

    async def get_execution_report(self) -> Dict[str, Any]:
        """
        Получение детального отчета о выполнении
        """
        try:
            # Статистика ордеров
            total_orders = await self.orders_repository.count_active_orders()
            order_stats = await self.orders_repository.get_order_statistics()
            
            # Статистика подключения
            health_check = await self.orders_repository.health_check()
            exchange_info = self.exchange_connector.get_exchange_info()
            
            return {
                'execution_stats': self.execution_stats,
                'orders_stats': {
                    'total_active': total_orders,
                    'by_status_side': order_stats
                },
                'system_health': {
                    'repository': health_check,
                    'exchange': exchange_info
                },
                'settings': {
                    'max_execution_time_sec': self.max_execution_time_sec,
                    'enable_risk_checks': self.enable_risk_checks,
                    'enable_balance_checks': self.enable_balance_checks,
                    'enable_slippage_protection': self.enable_slippage_protection,
                    'enable_ccxt_validation': self.enable_ccxt_validation
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate execution report: {e}")
            return {'error': str(e), 'timestamp': datetime.now(timezone.utc).isoformat()}

    def reset_statistics(self):
        """
        Сброс статистики
        """
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'average_execution_time_ms': 0.0,
            'ccxt_compliance_score': 100.0
        }
        logger.info("Execution statistics reset")

    # ===== EMERGENCY OPERATIONS =====

    async def emergency_cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """
        Экстренная отмена всех ордеров
        """
        logger.warning("🚨 EMERGENCY: Cancelling all orders")
        
        try:
            # Получаем активные ордера
            active_orders = await self.orders_repository.get_active_orders()
            
            if symbol:
                active_orders = [order for order in active_orders if order.symbol == symbol]
            
            cancelled_count = 0
            
            for order in active_orders:
                try:
                    if await self.cancel_ccxt_order(order):
                        cancelled_count += 1
                except Exception as e:
                    logger.error(f"Failed to cancel order {order.id}: {e}")
            
            logger.warning(f"🚨 Emergency cancellation completed: {cancelled_count} orders cancelled")
            return cancelled_count

        except Exception as e:
            logger.error(f"Emergency cancellation failed: {e}")
            return 0

    # ===== CONFIGURATION =====

    def configure_execution_settings(
        self,
        max_execution_time_sec: Optional[float] = None,
        enable_risk_checks: Optional[bool] = None,
        enable_balance_checks: Optional[bool] = None,
        enable_slippage_protection: Optional[bool] = None,
        enable_ccxt_validation: Optional[bool] = None
    ):
        """
        Настройка параметров выполнения
        """
        if max_execution_time_sec is not None:
            self.max_execution_time_sec = max_execution_time_sec
        if enable_risk_checks is not None:
            self.enable_risk_checks = enable_risk_checks
        if enable_balance_checks is not None:
            self.enable_balance_checks = enable_balance_checks
        if enable_slippage_protection is not None:
            self.enable_slippage_protection = enable_slippage_protection
        if enable_ccxt_validation is not None:
            self.enable_ccxt_validation = enable_ccxt_validation

        logger.info("⚙️ CCXT execution settings updated")

    def __repr__(self):
        return (f"CCXTOrderExecutionService("
                f"exchange={self.exchange_connector.exchange_name}, "
                f"executions={self.execution_stats['total_executions']}, "
                f"success_rate={self.execution_stats.get('ccxt_compliance_score', 0):.1f}%)")


# ===== FACTORY FUNCTION =====

def create_ccxt_order_execution_service(
    exchange_connector: CCXTExchangeConnector,
    orders_repository: IOrdersRepository,
    deal_service: Optional[Any] = None
) -> CCXTOrderExecutionService:
    """
    Factory function для создания CCXT Order Execution Service
    """
    return CCXTOrderExecutionService(
        exchange_connector=exchange_connector,
        orders_repository=orders_repository,
        deal_service=deal_service
    )