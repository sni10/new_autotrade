# src/domain/services/orders/order_execution_service.py
import logging
from typing import Any, Tuple, List, Optional, Dict
from domain.entities.order import Order, OrderExecutionResult
from domain.entities.deal import Deal
from domain.entities.currency_pair import CurrencyPair
from domain.services.orders.order_service import OrderService
from domain.services.deals.deal_service import DealService
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector

logger = logging.getLogger(__name__)

class ExecutionReport:
    def __init__(self, success: bool, deal_id: int = None, buy_order: Order = None, sell_order: Order = None, error_message: str = None, warnings: List[str] = None):
        self.success = success
        self.deal_id = deal_id
        self.buy_order = buy_order
        self.sell_order = sell_order
        self.error_message = error_message
        self.warnings = warnings or []

class OrderExecutionService:
    def __init__(self, order_service: OrderService, deal_service: DealService, exchange_connector: CcxtExchangeConnector):
        self.order_service = order_service
        self.deal_service = deal_service
        self.exchange_connector = exchange_connector
        # Статистика выполнений
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_volume": 0.0,
            "total_fees": 0.0
        }

    async def execute_trading_strategy(self, currency_pair: CurrencyPair, strategy_result: Any) -> ExecutionReport:
        try:
            # Увеличиваем счетчик попыток выполнения
            self.stats["total_executions"] += 1
            
            is_valid, validation_error = self._validate_strategy_input(strategy_result)
            if not is_valid:
                self.stats["failed_executions"] += 1
                return ExecutionReport(success=False, error_message=f"Input validation failed: {validation_error}")

            buy_price, buy_amount, sell_price, sell_amount, _ = strategy_result
            
            can_trade, reason, _ = await self.exchange_connector.check_sufficient_balance(currency_pair.symbol, 'buy', buy_amount, buy_price)
            if not can_trade:
                self.stats["failed_executions"] += 1
                return ExecutionReport(success=False, error_message=f"Pre-execution check failed: {reason}")

            deal = self.deal_service.create_new_deal(currency_pair)
            
            buy_exec_result = await self.order_service.create_and_place_buy_order(currency_pair.symbol, buy_amount, buy_price, deal.deal_id)
            if not buy_exec_result.success:
                self.stats["failed_executions"] += 1
                return ExecutionReport(success=False, deal_id=deal.deal_id, error_message=f"BUY order failed: {buy_exec_result.error_message}")

            sell_exec_result = await self.order_service.create_local_sell_order(currency_pair.symbol, sell_amount, sell_price, deal.deal_id)
            if not sell_exec_result.success:
                await self.order_service.cancel_order(buy_exec_result.order)
                self.stats["failed_executions"] += 1
                return ExecutionReport(success=False, deal_id=deal.deal_id, buy_order=buy_exec_result.order, error_message=f"Local SELL order creation failed: {sell_exec_result.error_message}")

            deal.attach_orders(buy_exec_result.order, sell_exec_result.order)
            self.deal_service.deals_repo.save(deal)
            
            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Сохраняем обновленные ордера с правильным deal_id
            self.order_service.orders_repo.save(buy_exec_result.order)
            self.order_service.orders_repo.save(sell_exec_result.order)
            
            # Обновляем статистику успешного выполнения
            self.stats["successful_executions"] += 1
            
            return ExecutionReport(success=True, deal_id=deal.deal_id, buy_order=buy_exec_result.order, sell_order=sell_exec_result.order)

        except Exception as e:
            logger.error(f"Strategy execution failed: {e}", exc_info=True)
            # Обновляем статистику неудачных выполнений (total_executions уже увеличен в начале метода)
            self.stats["failed_executions"] += 1
            return ExecutionReport(success=False, error_message=f"Unexpected error: {str(e)}")

    def _validate_strategy_input(self, strategy_result: Any) -> Tuple[bool, str]:
        if not isinstance(strategy_result, (tuple, list)) or len(strategy_result) < 5:
            return False, "Invalid strategy result format"
        return True, ""

    async def emergency_stop_all_trading(self) -> Dict[str, Any]:
        """
        TODO: Реализовать emergency stop после интеграции с БД.
        Метод должен:
        1. Отменить все активные ордера
        2. Сохранить текущее состояние в БД
        3. Закрыть все открытые позиции (если возможно)
        4. Вернуть отчет о выполненных действиях
        """
        logger.warning("🚨 emergency_stop_all_trading вызван, но пока не реализован (заглушка)")
        return {
            "success": True,
            "message": "Emergency stop заглушка - метод будет реализован после интеграции с БД",
            "cancelled_orders": 0,
            "saved_deals": 0,
            "warnings": ["Метод пока не реализован - это заглушка"]
        }

    def get_execution_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику исполнения торговых стратегий.
        """
        success_rate = 0.0
        if self.stats["total_executions"] > 0:
            success_rate = (self.stats["successful_executions"] / self.stats["total_executions"]) * 100
        
        return {
            "total_executions": self.stats["total_executions"],
            "successful_executions": self.stats["successful_executions"],
            "failed_executions": self.stats["failed_executions"],
            "success_rate": success_rate,
            "total_volume": self.stats["total_volume"],
            "total_fees": self.stats["total_fees"],
            "average_execution_time_ms": 0.0  # TODO: Добавить измерение времени выполнения
        }
