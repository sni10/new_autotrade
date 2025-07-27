# infrastructure/repositories/postgresql/postgresql_orders_repository.py

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.domain.entities.order import Order
from src.domain.repositories.i_orders_repository import IOrdersRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PostgreSQLOrdersRepository(IOrdersRepository):
    """
    PostgreSQL реализация репозитория для хранения ордеров.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def save(self, order: Order) -> None:
        """Сохраняет или обновляет ордер в базе данных."""
        query = """
            INSERT INTO orders (
                id, side, type, price, amount, status, created_at, closed_at, deal_id,
                exchange_id, symbol, filled_amount, remaining_amount, average_price,
                fees, fee_currency, time_in_force, client_order_id, exchange_timestamp,
                last_update, error_message, retries, metadata, exchange_raw_data
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
                $17, $18, $19, $20, $21, $22, $23, $24
            )
            ON CONFLICT (id) DO UPDATE SET
                side = EXCLUDED.side,
                type = EXCLUDED.type,
                price = EXCLUDED.price,
                amount = EXCLUDED.amount,
                status = EXCLUDED.status,
                closed_at = EXCLUDED.closed_at,
                exchange_id = EXCLUDED.exchange_id,
                filled_amount = EXCLUDED.filled_amount,
                remaining_amount = EXCLUDED.remaining_amount,
                average_price = EXCLUDED.average_price,
                fees = EXCLUDED.fees,
                fee_currency = EXCLUDED.fee_currency,
                last_update = EXCLUDED.last_update,
                error_message = EXCLUDED.error_message,
                retries = EXCLUDED.retries,
                metadata = EXCLUDED.metadata,
                exchange_raw_data = EXCLUDED.exchange_raw_data;
        """
        params = (
            order.order_id, order.side, order.order_type, order.price, order.amount,
            order.status, datetime.fromtimestamp(order.created_at / 1000),
            datetime.fromtimestamp(order.closed_at / 1000) if order.closed_at else None,
            order.deal_id, order.exchange_id, order.symbol, order.filled_amount,
            order.remaining_amount, order.average_price, order.fees, order.fee_currency,
            order.time_in_force, order.client_order_id,
            datetime.fromtimestamp(order.exchange_timestamp / 1000) if order.exchange_timestamp else None,
            datetime.fromtimestamp(order.last_update / 1000) if order.last_update else None,
            order.error_message, order.retries, order.metadata, order.exchange_raw_data
        )
        try:
            await self.db_manager.execute_command(query, params)
            logger.info(f"Order {order.order_id} saved to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to save order {order.order_id} to PostgreSQL: {e}")
            raise

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        query = "SELECT * FROM orders WHERE id = $1;"
        try:
            result = await self.db_manager.execute_query(query, (order_id,))
            if result:
                return self._map_row_to_order(result[0])
        except Exception as e:
            logger.error(f"Failed to get order {order_id} from PostgreSQL: {e}")
        return None

    async def get_by_exchange_id(self, exchange_id: str) -> Optional[Order]:
        query = "SELECT * FROM orders WHERE exchange_id = $1;"
        try:
            result = await self.db_manager.execute_query(query, (exchange_id,))
            if result:
                return self._map_row_to_order(result[0])
        except Exception as e:
            logger.error(f"Failed to get order by exchange_id {exchange_id} from PostgreSQL: {e}")
        return None

    async def get_all_by_deal(self, deal_id: int) -> List[Order]:
        query = "SELECT * FROM orders WHERE deal_id = $1;"
        orders = []
        try:
            result = await self.db_manager.execute_query(query, (deal_id,))
            if result:
                orders = [self._map_row_to_order(row) for row in result]
        except Exception as e:
            logger.error(f"Failed to get orders for deal {deal_id} from PostgreSQL: {e}")
        return orders

    def _map_row_to_order(self, row: Dict[str, Any]) -> Order:
        """Преобразует строку из базы данных в объект Order."""
        return Order(
            order_id=row['id'],
            side=row['side'],
            order_type=row['type'],
            price=row['price'],
            amount=row['amount'],
            status=row['status'],
            created_at=int(row['created_at'].timestamp() * 1000),
            closed_at=int(row['closed_at'].timestamp() * 1000) if row['closed_at'] else None,
            deal_id=row['deal_id'],
            exchange_id=row['exchange_id'],
            symbol=row['symbol'],
            filled_amount=row['filled_amount'],
            remaining_amount=row['remaining_amount'],
            average_price=row['average_price'],
            fees=row['fees'],
            fee_currency=row['fee_currency'],
            time_in_force=row['time_in_force'],
            client_order_id=row['client_order_id'],
            exchange_timestamp=int(row['exchange_timestamp'].timestamp() * 1000) if row['exchange_timestamp'] else None,
            last_update=int(row['last_update'].timestamp() * 1000) if row['last_update'] else None,
            error_message=row['error_message'],
            retries=row['retries'],
            metadata=row['metadata'],
            exchange_raw_data=row['exchange_raw_data']
        )
