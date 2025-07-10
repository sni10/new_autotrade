# domain/services/order_execution_service.py.new - ГЛАВНЫЙ сервис Issue #7
import asyncio
import logging
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from domain.entities.order import Order, OrderExecutionResult
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.services.order_service import OrderService
from domain.services.deal_service import DealService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

logger = logging.getLogger(__name__)

@dataclass
class TradingContext:
    """Контекст для выполнения торговых операций"""
    currency_pair: CurrencyPair
    current_price: float
    budget: float
    strategy_result: Any  # Результат расчета стратегии
    deal: Optional[Deal] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ExecutionReport:
    """Отчет о выполнении торговой операции"""
    success: bool
    deal_id: Optional[int] = None
    buy_order: Optional[Order] = None
    sell_order: Optional[Order] = None
    total_cost: float = 0.0
    expected_profit: float = 0.0
    fees: float = 0.0
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = None

class OrderExecutionService:
    """
    🚀 ГЛАВНЫЙ сервис для выполнения торговых операций (Issue #7)
    
    Это высокоуровневый сервис, который:
    - Координирует создание сделок и ордеров
    - Выполняет полные торговые стратегии
    - Управляет рисками и валидацией
    - Обеспечивает реальное размещение ордеров на бирже
    - Мониторит исполнение и состояние ордеров
    """

    def __init__(
        self,
        order_service: OrderService,
        deal_service: DealService,
        exchange_connector: CcxtExchangeConnector
    ):
        self.order_service = order_service
        self.deal_service = deal_service
        self.exchange_connector = exchange_connector
        
        # Статистика
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'average_execution_time_ms': 0.0
        }
        
        # Настройки выполнения
        self.max_execution_time_sec = 30.0  # Максимальное время выполнения
        self.enable_risk_checks = True
        self.enable_balance_checks = True
        self.enable_slippage_protection = True

    # 🚀 ГЛАВНЫЙ МЕТОД ВЫПОЛНЕНИЯ ТОРГОВОЙ СТРАТЕГИИ

    async def execute_trading_strategy(
        self,
        currency_pair: CurrencyPair,
        strategy_result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionReport:
        """
        🎯 ГЛАВНЫЙ метод выполнения торговой стратегии
        
        Принимает результат расчета стратегии и выполняет полную торговую операцию:
        1. Создает сделку
        2. Размещает BUY ордер на бирже
        3. Размещает SELL ордер на бирже
        4. Связывает все компоненты
        5. Возвращает детальный отчет
        
        Args:
            currency_pair: Торговая пара
            strategy_result: Результат расчета стратегии (из ticker_service)
            metadata: Дополнительная информация
            
        Returns:
            ExecutionReport с результатами выполнения
        """
        start_time = datetime.now()
        execution_id = f"exec_{int(start_time.timestamp() * 1000)}"
        
        logger.info(f"🚀 [{execution_id}] Starting strategy execution for {currency_pair.symbol}")
        
        try:
            # 1. Валидация входных данных
            validation_result = self._validate_strategy_input(currency_pair, strategy_result)
            if not validation_result[0]:
                return ExecutionReport(
                    success=False,
                    error_message=f"Input validation failed: {validation_result[1]}"
                )
            
            # 2. Парсинг результатов стратегии
            strategy_data = self._parse_strategy_result(strategy_result)
            if not strategy_data:
                return ExecutionReport(
                    success=False,
                    error_message="Failed to parse strategy result"
                )
            
            # 3. Создание контекста торговли
            context = TradingContext(
                currency_pair=currency_pair,
                current_price=strategy_data['buy_price'],
                budget=currency_pair.deal_quota,
                strategy_result=strategy_result,
                metadata=metadata or {}
            )
            
            # 4. Pre-execution проверки
            pre_check_result = await self._perform_pre_execution_checks(context, strategy_data)
            if not pre_check_result[0]:
                return ExecutionReport(
                    success=False,
                    error_message=f"Pre-execution checks failed: {pre_check_result[1]}",
                    warnings=pre_check_result[2] if len(pre_check_result) > 2 else []
                )
            
            # 5. Создание сделки
            deal = self.deal_service.create_new_deal(currency_pair)
            context.deal = deal
            
            logger.info(f"✅ [{execution_id}] Deal #{deal.deal_id} created")
            
            # 6. Выполнение BUY ордера
            buy_result = await self._execute_buy_order(context, strategy_data)
            if not buy_result.success:
                return ExecutionReport(
                    success=False,
                    deal_id=deal.deal_id,
                    error_message=f"BUY order failed: {buy_result.error_message}"
                )
            
            buy_order = buy_result.order
            logger.info(f"✅ [{execution_id}] BUY order executed: {buy_order.exchange_id}")
            
            # 7. Выполнение SELL ордера
            sell_result = await self._execute_sell_order(context, strategy_data)
            if not sell_result.success:
                # Пытаемся отменить BUY ордер при неудаче SELL
                await self._emergency_cancel_buy_order(buy_order)
                return ExecutionReport(
                    success=False,
                    deal_id=deal.deal_id,
                    buy_order=buy_order,
                    error_message=f"SELL order failed: {sell_result.error_message}"
                )
            
            sell_order = sell_result.order
            logger.info(f"✅ [{execution_id}] SELL order executed: {sell_order.exchange_id}")
            
            # 8. Связывание ордеров со сделкой
            deal.attach_orders(buy_order, sell_order)
            self.deal_service.deals_repo.save(deal)
            
            # 9. Расчет финансовых показателей
            total_cost = buy_order.calculate_total_cost_with_fees()
            expected_profit = sell_order.calculate_total_cost() - buy_order.calculate_total_cost()
            total_fees = buy_order.fees + sell_order.fees
            
            # 10. Обновление статистики
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_execution_stats(True, total_cost, total_fees, execution_time)
            
            # 11. Формирование отчета
            report = ExecutionReport(
                success=True,
                deal_id=deal.deal_id,
                buy_order=buy_order,
                sell_order=sell_order,
                total_cost=total_cost,
                expected_profit=expected_profit,
                fees=total_fees,
                execution_time_ms=execution_time
            )
            
            logger.info(f"🎉 [{execution_id}] Strategy executed successfully!")
            logger.info(f"   💰 Cost: {total_cost:.4f} USDT")
            logger.info(f"   📈 Expected profit: {expected_profit:.4f} USDT")
            logger.info(f"   💸 Fees: {total_fees:.4f} USDT")
            logger.info(f"   ⏱️ Execution time: {execution_time:.1f}ms")
            
            return report
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_execution_stats(False, 0.0, 0.0, execution_time)
            
            logger.error(f"❌ [{execution_id}] Strategy execution failed: {e}")
            return ExecutionReport(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                execution_time_ms=execution_time
            )

    # 🔧 ВНУТРЕННИЕ МЕТОДЫ ВЫПОЛНЕНИЯ

    def _validate_strategy_input(
        self, 
        currency_pair: CurrencyPair, 
        strategy_result: Any
    ) -> Tuple[bool, str]:
        """Валидация входных данных для стратегии"""
        try:
            if not currency_pair:
                return False, "Currency pair is required"
            
            if not currency_pair.symbol:
                return False, "Currency pair symbol is required"
            
            if currency_pair.deal_quota <= 0:
                return False, "Deal quota must be positive"
            
            if not strategy_result:
                return False, "Strategy result is required"
            
            # Проверяем формат strategy_result
            if isinstance(strategy_result, dict) and "comment" in strategy_result:
                return False, f"Strategy calculation error: {strategy_result['comment']}"
            
            if not isinstance(strategy_result, (tuple, list)) or len(strategy_result) < 5:
                return False, "Invalid strategy result format"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _parse_strategy_result(self, strategy_result: Any) -> Optional[Dict[str, Any]]:
        """Парсинг результата стратегии в удобный формат"""
        try:
            if isinstance(strategy_result, dict) and "comment" in strategy_result:
                return None  # Ошибка в стратегии
            
            # Распаковываем tuple результат
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
            logger.error(f"❌ Error parsing strategy result: {e}")
            return None

    async def _perform_pre_execution_checks(
        self, 
        context: TradingContext, 
        strategy_data: Dict[str, Any]
    ) -> Tuple[bool, str, List[str]]:
        """Предварительные проверки перед выполнением"""
        warnings = []
        
        try:
            # 1. Проверка баланса
            if self.enable_balance_checks:
                balance_check = await self.exchange_connector.check_sufficient_balance(
                    context.currency_pair.symbol,
                    'buy',
                    strategy_data['buy_amount'],
                    strategy_data['buy_price']
                )
                
                if not balance_check[0]:
                    return False, f"Insufficient balance: need {strategy_data['buy_amount'] * strategy_data['buy_price']:.4f} {balance_check[1]}, have {balance_check[2]:.4f}", warnings
                
                # Предупреждение если баланс близок к лимиту
                required = strategy_data['buy_amount'] * strategy_data['buy_price']
                if balance_check[2] < required * 1.1:
                    warnings.append("Balance is close to required amount")
            
            # 2. Проверка цен на разумность
            ticker = await self.exchange_connector.fetch_ticker(context.currency_pair.symbol)
            current_market_price = ticker['last']
            
            buy_price_diff = abs(strategy_data['buy_price'] - current_market_price) / current_market_price
            if buy_price_diff > 0.05:  # 5% отклонение
                warnings.append(f"BUY price differs from market by {buy_price_diff*100:.1f}%")
            
            sell_price_diff = abs(strategy_data['sell_price'] - current_market_price) / current_market_price  
            if sell_price_diff > 0.10:  # 10% отклонение
                warnings.append(f"SELL price differs from market by {sell_price_diff*100:.1f}%")
            
            # 3. Проверка объемов
            symbol_info = await self.exchange_connector.get_symbol_info(context.currency_pair.symbol)
            if strategy_data['buy_amount'] < symbol_info.min_qty:
                return False, f"BUY amount {strategy_data['buy_amount']} below minimum {symbol_info.min_qty}", warnings
            
            if strategy_data['sell_amount'] < symbol_info.min_qty:
                return False, f"SELL amount {strategy_data['sell_amount']} below minimum {symbol_info.min_qty}", warnings
            
            return True, "Checks passed", warnings
            
        except Exception as e:
            return False, f"Pre-execution check error: {str(e)}", warnings

    async def _execute_buy_order(
        self, 
        context: TradingContext, 
        strategy_data: Dict[str, Any]
    ) -> OrderExecutionResult:
        """Выполнение BUY ордера"""
        try:
            return await self.order_service.create_and_place_buy_order(
                symbol=context.currency_pair.symbol,
                amount=strategy_data['buy_amount'],
                price=strategy_data['buy_price'],
                deal_id=context.deal.deal_id,
                order_type=Order.TYPE_LIMIT
            )
        except Exception as e:
            logger.error(f"❌ Error executing BUY order: {e}")
            return OrderExecutionResult(
                success=False,
                error_message=f"BUY execution error: {str(e)}"
            )

    async def _execute_sell_order(
        self, 
        context: TradingContext, 
        strategy_data: Dict[str, Any]
    ) -> OrderExecutionResult:
        """Выполнение SELL ордера"""
        try:
            return await self.order_service.create_and_place_sell_order(
                symbol=context.currency_pair.symbol,
                amount=strategy_data['sell_amount'],
                price=strategy_data['sell_price'],
                deal_id=context.deal.deal_id,
                order_type=Order.TYPE_LIMIT
            )
        except Exception as e:
            logger.error(f"❌ Error executing SELL order: {e}")
            return OrderExecutionResult(
                success=False,
                error_message=f"SELL execution error: {str(e)}"
            )

    async def _emergency_cancel_buy_order(self, buy_order: Order) -> bool:
        """Экстренная отмена BUY ордера при неудаче SELL"""
        try:
            logger.warning(f"🚨 Emergency cancelling BUY order {buy_order.order_id}")
            return await self.order_service.cancel_order(buy_order)
        except Exception as e:
            logger.error(f"❌ Failed to emergency cancel BUY order: {e}")
            return False

    def _update_execution_stats(
        self, 
        success: bool, 
        volume: float, 
        fees: float, 
        execution_time_ms: float
    ):
        """Обновление статистики выполнения"""
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

    # 📊 МЕТОДЫ МОНИТОРИНГА И УПРАВЛЕНИЯ

    async def monitor_active_orders(self) -> Dict[str, Any]:
        """
        📊 Мониторинг всех активных ордеров
        """
        try:
            # Синхронизируем ордера с биржей
            updated_orders = await self.order_service.sync_orders_with_exchange()
            
            # Группируем по статусам
            open_orders = []
            partially_filled = []
            filled_orders = []
            
            for order in updated_orders:
                if order.is_open():
                    open_orders.append(order)
                elif order.is_partially_filled():
                    partially_filled.append(order)
                elif order.is_filled():
                    filled_orders.append(order)
            
            return {
                'open_orders': len(open_orders),
                'partially_filled': len(partially_filled),
                'filled_orders': len(filled_orders),
                'total_monitored': len(updated_orders),
                'orders': {
                    'open': [order.to_dict() for order in open_orders],
                    'partially_filled': [order.to_dict() for order in partially_filled],
                    'filled': [order.to_dict() for order in filled_orders]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error monitoring orders: {e}")
            return {'error': str(e)}

    async def emergency_stop_all_trading(self, symbol: str = None) -> Dict[str, Any]:
        """
        🚨 Экстренная остановка всей торговли
        """
        logger.warning("🚨 EMERGENCY STOP - Cancelling all orders")
        
        try:
            # Отменяем все ордера через order_service
            cancelled_count = await self.order_service.emergency_cancel_all_orders(symbol)
            
            # Получаем статистику
            open_orders = self.order_service.get_open_orders()
            open_deals = self.deal_service.get_open_deals()
            
            return {
                'cancelled_orders': cancelled_count,
                'remaining_open_orders': len(open_orders),
                'open_deals': len(open_deals),
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol or 'ALL'
            }
            
        except Exception as e:
            logger.error(f"❌ Error during emergency stop: {e}")
            return {'error': str(e), 'cancelled_orders': 0}

    def get_execution_statistics(self) -> Dict[str, Any]:
        """📊 Получение статистики выполнения"""
        stats = self.execution_stats.copy()
        
        if stats['total_executions'] > 0:
            stats['success_rate'] = (stats['successful_executions'] / stats['total_executions']) * 100
            stats['average_volume_per_execution'] = stats['total_volume'] / stats['successful_executions'] if stats['successful_executions'] > 0 else 0
            stats['average_fees_per_execution'] = stats['total_fees'] / stats['successful_executions'] if stats['successful_executions'] > 0 else 0
        else:
            stats['success_rate'] = 0
            stats['average_volume_per_execution'] = 0
            stats['average_fees_per_execution'] = 0
        
        return stats

    def reset_statistics(self):
        """🔄 Сброс статистики"""
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_volume': 0.0,
            'total_fees': 0.0,
            'average_execution_time_ms': 0.0
        }

    # ⚙️ НАСТРОЙКИ

    def configure_execution_settings(
        self,
        max_execution_time_sec: float = None,
        enable_risk_checks: bool = None,
        enable_balance_checks: bool = None,
        enable_slippage_protection: bool = None
    ):
        """⚙️ Настройка параметров выполнения"""
        if max_execution_time_sec is not None:
            self.max_execution_time_sec = max_execution_time_sec
        if enable_risk_checks is not None:
            self.enable_risk_checks = enable_risk_checks
        if enable_balance_checks is not None:
            self.enable_balance_checks = enable_balance_checks
        if enable_slippage_protection is not None:
            self.enable_slippage_protection = enable_slippage_protection
        
        logger.info(f"⚙️ Execution settings updated")

    def get_current_settings(self) -> Dict[str, Any]:
        """⚙️ Получение текущих настроек"""
        return {
            'max_execution_time_sec': self.max_execution_time_sec,
            'enable_risk_checks': self.enable_risk_checks,
            'enable_balance_checks': self.enable_balance_checks,
            'enable_slippage_protection': self.enable_slippage_protection
        }
