# src/domain/services/orders/order_service.py
import logging
from typing import Optional, List
from domain.entities.order import Order, OrderExecutionResult
from domain.factories.order_factory import OrderFactory
from infrastructure.repositories.orders_repository import OrdersRepository
from infrastructure.connectors.exchange_connector import CcxtExchangeConnector
import ccxt

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self, orders_repo: OrdersRepository, order_factory: OrderFactory, exchange_connector: CcxtExchangeConnector):
        self.orders_repo = orders_repo
        self.order_factory = order_factory
        self.exchange_connector = exchange_connector

    async def create_and_place_buy_order(self, symbol: str, amount: float, price: float, deal_id: int, order_type: str = "LIMIT") -> OrderExecutionResult:
        order = self.order_factory.create_buy_order(symbol, amount, price, deal_id, order_type)
        return await self._execute_order_on_exchange(order)

    async def create_local_sell_order(self, symbol: str, amount: float, price: float, deal_id: int, order_type: str = "LIMIT") -> OrderExecutionResult:
        order = self.order_factory.create_sell_order(symbol, amount, price, deal_id, order_type)
        order.status = Order.STATUS_PENDING
        self.orders_repo.save(order)
        return OrderExecutionResult(success=True, order=order)

    async def place_existing_order(self, order: Order) -> OrderExecutionResult:
        return await self._execute_order_on_exchange(order)

    async def _execute_order_on_exchange(self, order: Order) -> OrderExecutionResult:
        try:
            placed_order = await self.exchange_connector.create_order(order.symbol, order.side, order.order_type, order.amount, order.price)
            if isinstance(placed_order, Order):
                order.update_from_order(placed_order)
            else:
                order.update_from_exchange(placed_order)
            self.orders_repo.save(order)
            return OrderExecutionResult(success=True, order=order)
        except Exception as e:
            order.status = Order.STATUS_FAILED
            order.error_message = str(e)
            self.orders_repo.save(order)
            return OrderExecutionResult(success=False, order=order, error_message=str(e))

    async def get_order_status(self, order: Order) -> Order:
        if not order.exchange_id: return order
        try:
            exchange_order = await self.exchange_connector.fetch_order(order.exchange_id, order.symbol)
            if isinstance(exchange_order, Order):
                order.update_from_order(exchange_order)
            else:
                order.update_from_exchange(exchange_order)
            self.orders_repo.save(order)
        except Exception as e:
            logger.error(f"Error checking order status for {order.order_id}: {e}")
        return order

    async def cancel_order(self, order: Order) -> bool:
        if not order.exchange_id: return False
        try:
            cancelled_order = await self.exchange_connector.cancel_order(order.exchange_id, order.symbol)
            if isinstance(cancelled_order, Order):
                order.update_from_order(cancelled_order)
            else:
                order.update_from_exchange(cancelled_order)
            self.orders_repo.save(order)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order.order_id}: {e}")
            return False

    def get_open_orders(self) -> List[Order]: return self.orders_repo.get_open_orders()
    def get_order_by_id(self, order_id: int) -> Optional[Order]: return self.orders_repo.get_by_id(order_id)

    def get_statistics(self) -> dict:
        """Получение статистики сервиса ордеров"""
        all_orders = self.orders_repo.get_all()
        open_orders = self.get_open_orders()

        return {
            'total_orders': len(all_orders),
            'open_orders': len(open_orders),
            'completed_orders': len([o for o in all_orders if o.status == 'FILLED']),
            'cancelled_orders': len([o for o in all_orders if o.status == 'CANCELLED']),
            'failed_orders': len([o for o in all_orders if o.status == 'FAILED'])
        }

    def get_open_orders(self) -> List[Order]: return self.orders_repo.get_open_orders()
    def get_order_by_id(self, order_id: int) -> Optional[Order]: return self.orders_repo.get_by_id(order_id)
