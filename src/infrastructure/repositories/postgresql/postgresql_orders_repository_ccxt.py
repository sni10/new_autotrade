# infrastructure/repositories/postgresql/postgresql_orders_repository_ccxt.py
import json
import logging
from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncpg
from asyncpg import Connection, Pool

from src.domain.entities.order import Order
from src.domain.repositories.i_orders_repository import IOrdersRepository

logger = logging.getLogger(__name__)


class PostgreSQLOrdersRepositoryCCXT(IOrdersRepository):
    """
    🚀 CCXT COMPLIANT PostgreSQL Orders Repository
    
    Работает с новой CCXT-совместимой схемой БД (таблица ccxt_orders).
    Полная совместимость с CCXT структурами данных.
    """

    def __init__(self, connection_pool: Pool):
        self.pool = connection_pool

    # ===== CORE CRUD OPERATIONS =====

    async def save_order(self, order: Order) -> bool:
        """
        Сохранить ордер в CCXT-совместимую таблицу ccxt_orders
        """
        try:
            async with self.pool.acquire() as conn:
                # Проверяем, существует ли ордер
                existing = await self._get_order_by_id(conn, order.id)
                
                if existing:
                    # Обновляем существующий ордер
                    return await self._update_order_internal(conn, order)
                else:
                    # Создаем новый ордер
                    return await self._insert_order_internal(conn, order)
                    
        except Exception as e:
            logger.error(f"Failed to save order {order.id}: {str(e)}")
            return False

    async def get_order(self, order_id: str) -> Optional[Order]:
        """
        Получить ордер по CCXT ID (exchange order ID)
        """
        try:
            async with self.pool.acquire() as conn:
                return await self._get_order_by_id(conn, order_id)
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {str(e)}")
            return None

    async def get_order_by_local_id(self, local_order_id: int) -> Optional[Order]:
        """
        Получить ордер по локальному AutoTrade ID
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    WHERE local_order_id = $1
                """
                row = await conn.fetchrow(query, local_order_id)
                return self._row_to_order(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get order by local_id {local_order_id}: {str(e)}")
            return None

    async def update_order(self, order: Order) -> bool:
        """
        Обновить существующий ордер
        """
        try:
            async with self.pool.acquire() as conn:
                return await self._update_order_internal(conn, order)
        except Exception as e:
            logger.error(f"Failed to update order {order.id}: {str(e)}")
            return False

    async def delete_order(self, order_id: str) -> bool:
        """
        Удалить ордер (мягкое удаление - помечаем как отмененный)
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    UPDATE ccxt_orders 
                    SET status = 'canceled', 
                        updated_at = CURRENT_TIMESTAMP,
                        error_message = 'Deleted'
                    WHERE id = $1
                """
                result = await conn.execute(query, order_id)
                return result == "UPDATE 1"
        except Exception as e:
            logger.error(f"Failed to delete order {order_id}: {str(e)}")
            return False

    # ===== QUERY OPERATIONS =====

    async def get_all_orders(self) -> List[Order]:
        """
        Получить все ордера
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get all orders: {str(e)}")
            return []

    async def get_active_orders(self) -> List[Order]:
        """
        Получить активные ордера (CCXT статусы: open, pending, partial)
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    WHERE status IN ('open', 'pending', 'partial')
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get active orders: {str(e)}")
            return []

    async def get_filled_orders(self) -> List[Order]:
        """
        Получить исполненные ордера (CCXT статус: closed)
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    WHERE status = 'closed'
                    ORDER BY updated_at DESC
                """
                rows = await conn.fetch(query)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get filled orders: {str(e)}")
            return []

    async def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """
        Получить ордера по торговой паре
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    WHERE symbol = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, symbol)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get orders by symbol {symbol}: {str(e)}")
            return []

    async def get_orders_by_deal_id(self, deal_id: str) -> List[Order]:
        """
        Получить ордера по ID сделки
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    WHERE deal_id = $1
                    ORDER BY created_at ASC
                """
                rows = await conn.fetch(query, deal_id)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get orders by deal_id {deal_id}: {str(e)}")
            return []

    async def get_orders_in_period(self, start_time: datetime, end_time: datetime) -> List[Order]:
        """
        Получить ордера за период
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    WHERE created_at BETWEEN $1 AND $2
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, start_time, end_time)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get orders in period: {str(e)}")
            return []

    async def count_active_orders(self) -> int:
        """
        Подсчитать количество активных ордеров
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT COUNT(*) FROM ccxt_orders 
                    WHERE status IN ('open', 'pending', 'partial')
                """
                count = await conn.fetchval(query)
                return count or 0
        except Exception as e:
            logger.error(f"Failed to count active orders: {str(e)}")
            return 0

    async def count_orders_by_status(self, status: str) -> int:
        """
        Подсчитать ордера по статусу
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT COUNT(*) FROM ccxt_orders 
                    WHERE status = $1
                """
                count = await conn.fetchval(query, status)
                return count or 0
        except Exception as e:
            logger.error(f"Failed to count orders by status {status}: {str(e)}")
            return 0

    # ===== ADVANCED QUERY OPERATIONS =====

    async def get_orders_by_side_and_symbol(self, side: str, symbol: str) -> List[Order]:
        """
        Получить ордера по стороне и символу
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    WHERE side = $1 AND symbol = $2
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, side, symbol)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get orders by side {side} and symbol {symbol}: {str(e)}")
            return []

    async def get_recent_orders(self, limit: int = 100) -> List[Order]:
        """
        Получить последние ордера
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    ORDER BY created_at DESC
                    LIMIT $1
                """
                rows = await conn.fetch(query, limit)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get recent orders: {str(e)}")
            return []

    async def get_orders_with_errors(self) -> List[Order]:
        """
        Получить ордера с ошибками
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM ccxt_orders 
                    WHERE error_message IS NOT NULL AND error_message != ''
                    ORDER BY updated_at DESC
                """
                rows = await conn.fetch(query)
                return [self._row_to_order(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get orders with errors: {str(e)}")
            return []

    # ===== BULK OPERATIONS =====

    async def update_orders_batch(self, orders: List[Order]) -> int:
        """
        Массовое обновление ордеров
        """
        updated_count = 0
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for order in orders:
                        success = await self._update_order_internal(conn, order)
                        if success:
                            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to update orders batch: {str(e)}")
        
        return updated_count

    # ===== INTERNAL HELPER METHODS =====

    async def _get_order_by_id(self, conn: Connection, order_id: str) -> Optional[Order]:
        """
        Внутренний метод получения ордера по ID
        """
        query = """
            SELECT * FROM ccxt_orders 
            WHERE id = $1
        """
        row = await conn.fetchrow(query, order_id)
        return self._row_to_order(row) if row else None

    async def _insert_order_internal(self, conn: Connection, order: Order) -> bool:
        """
        Внутренний метод вставки нового ордера
        """
        try:
            query = """
                INSERT INTO ccxt_orders (
                    id, client_order_id, datetime, timestamp, last_trade_timestamp,
                    status, symbol, type, time_in_force, side, price, amount,
                    filled, remaining, cost, average, trades, fee, info,
                    deal_id, local_order_id, created_at, updated_at,
                    error_message, retries, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23,
                    $24, $25, $26
                )
            """
            
            # Конвертируем данные для вставки
            values = self._order_to_db_values(order)
            
            await conn.execute(query, *values)
            logger.debug(f"Inserted order {order.id} into database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert order {order.id}: {str(e)}")
            return False

    async def _update_order_internal(self, conn: Connection, order: Order) -> bool:
        """
        Внутренний метод обновления ордера
        """
        try:
            query = """
                UPDATE ccxt_orders SET
                    client_order_id = $2, datetime = $3, timestamp = $4,
                    last_trade_timestamp = $5, status = $6, symbol = $7,
                    type = $8, time_in_force = $9, side = $10, price = $11,
                    amount = $12, filled = $13, remaining = $14, cost = $15,
                    average = $16, trades = $17, fee = $18, info = $19,
                    deal_id = $20, local_order_id = $21, updated_at = $22,
                    error_message = $23, retries = $24, metadata = $25
                WHERE id = $1
            """
            
            # Конвертируем данные для обновления (без created_at)
            values = self._order_to_db_values(order, include_created_at=False)
            
            result = await conn.execute(query, *values)
            success = result == "UPDATE 1"
            
            if success:
                logger.debug(f"Updated order {order.id} in database")
            else:
                logger.warning(f"No rows updated for order {order.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update order {order.id}: {str(e)}")
            return False

    def _order_to_db_values(self, order: Order, include_created_at: bool = True) -> tuple:
        """
        Конвертирует Order в кортеж значений для БД
        """
        # Конвертируем datetime в PostgreSQL timestamp
        created_at = None
        updated_at = datetime.now(timezone.utc)
        
        if order.created_at:
            created_at = datetime.fromtimestamp(order.created_at / 1000, timezone.utc)
        
        if order.datetime:
            try:
                # Парсим ISO datetime в PostgreSQL timestamp
                order_datetime = datetime.fromisoformat(order.datetime.replace('Z', '+00:00'))
            except:
                order_datetime = created_at
        else:
            order_datetime = created_at

        # Конвертируем JSON поля
        trades_json = json.dumps(order.trades) if order.trades else '[]'
        fee_json = json.dumps(order.fee) if order.fee else '{}'
        info_json = json.dumps(order.info) if order.info else '{}'
        metadata_json = json.dumps(order.metadata) if order.metadata else '{}'

        # Конвертируем UUID
        deal_id = str(order.deal_id) if order.deal_id else None

        values = [
            order.id,                                    # $1
            order.clientOrderId,                         # $2
            order_datetime,                              # $3
            order.timestamp,                             # $4
            order.lastTradeTimestamp,                    # $5
            order.status,                                # $6
            order.symbol,                                # $7
            order.type,                                  # $8
            order.timeInForce,                           # $9
            order.side,                                  # $10
            Decimal(str(order.price)) if order.price else None,  # $11
            Decimal(str(order.amount)),                  # $12
            Decimal(str(order.filled)),                  # $13
            Decimal(str(order.remaining)) if order.remaining else None,  # $14
            Decimal(str(order.cost)) if order.cost else None,     # $15
            Decimal(str(order.average)) if order.average else None, # $16
            trades_json,                                 # $17
            fee_json,                                    # $18
            info_json,                                   # $19
            deal_id,                                     # $20
            order.local_order_id,                        # $21
        ]

        if include_created_at:
            values.extend([
                created_at,                              # $22
                updated_at,                              # $23
                order.error_message,                     # $24
                order.retries,                           # $25
                metadata_json                            # $26
            ])
        else:
            values.extend([
                updated_at,                              # $22
                order.error_message,                     # $23
                order.retries,                           # $24
                metadata_json                            # $25
            ])

        return tuple(values)

    def _row_to_order(self, row) -> Order:
        """
        Конвертирует строку БД в объект Order
        """
        if not row:
            return None

        # Парсим JSON поля
        trades = json.loads(row['trades']) if row['trades'] else []
        fee = json.loads(row['fee']) if row['fee'] else {}
        info = json.loads(row['info']) if row['info'] else {}
        metadata = json.loads(row['metadata']) if row['metadata'] else {}

        # Конвертируем datetime в ISO string
        datetime_str = None
        if row['datetime']:
            datetime_str = row['datetime'].isoformat().replace('+00:00', 'Z')

        # Конвертируем timestamp
        created_at_timestamp = None
        if row['created_at']:
            created_at_timestamp = int(row['created_at'].timestamp() * 1000)

        last_update_timestamp = None
        if row['updated_at']:
            last_update_timestamp = int(row['updated_at'].timestamp() * 1000)

        # Конвертируем Decimal в float
        price = float(row['price']) if row['price'] else None
        amount = float(row['amount']) if row['amount'] else 0.0
        filled = float(row['filled']) if row['filled'] else 0.0
        remaining = float(row['remaining']) if row['remaining'] else None
        cost = float(row['cost']) if row['cost'] else None
        average = float(row['average']) if row['average'] else None

        return Order(
            # CCXT поля
            id=row['id'],
            clientOrderId=row['client_order_id'],
            datetime=datetime_str,
            timestamp=row['timestamp'],
            lastTradeTimestamp=row['last_trade_timestamp'],
            status=row['status'],
            symbol=row['symbol'],
            type=row['type'],
            timeInForce=row['time_in_force'],
            side=row['side'],
            price=price,
            amount=amount,
            filled=filled,
            remaining=remaining,
            cost=cost,
            average=average,
            trades=trades,
            fee=fee,
            info=info,
            
            # AutoTrade поля
            deal_id=int(row['deal_id']) if row['deal_id'] else None,
            local_order_id=row['local_order_id'],
            created_at=created_at_timestamp,
            last_update=last_update_timestamp,
            error_message=row['error_message'],
            retries=row['retries'] or 0,
            metadata=metadata
        )

    # ===== UTILITY METHODS =====

    async def cleanup_old_orders(self, days_to_keep: int = 30) -> int:
        """
        Очистка старых ордеров
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    DELETE FROM ccxt_orders 
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    AND status IN ('closed', 'canceled', 'rejected', 'expired')
                """
                result = await conn.execute(query % days_to_keep)
                # Извлекаем количество удаленных строк из результата
                deleted_count = int(result.split()[-1]) if result.startswith('DELETE') else 0
                logger.info(f"Cleaned up {deleted_count} old orders")
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old orders: {str(e)}")
            return 0

    async def get_order_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику по ордерам
        """
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        status,
                        side,
                        COUNT(*) as count,
                        SUM(CASE WHEN cost IS NOT NULL THEN cost ELSE 0 END) as total_cost,
                        AVG(CASE WHEN cost IS NOT NULL THEN cost ELSE 0 END) as avg_cost
                    FROM ccxt_orders 
                    GROUP BY status, side
                    ORDER BY status, side
                """
                rows = await conn.fetch(query)
                
                statistics = {}
                for row in rows:
                    key = f"{row['status']}_{row['side']}"
                    statistics[key] = {
                        'count': row['count'],
                        'total_cost': float(row['total_cost']) if row['total_cost'] else 0.0,
                        'avg_cost': float(row['avg_cost']) if row['avg_cost'] else 0.0
                    }
                
                return statistics
        except Exception as e:
            logger.error(f"Failed to get order statistics: {str(e)}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья репозитория
        """
        try:
            async with self.pool.acquire() as conn:
                # Проверяем подключение
                await conn.fetchval("SELECT 1")
                
                # Считаем общее количество ордеров
                total_orders = await conn.fetchval("SELECT COUNT(*) FROM ccxt_orders")
                
                # Считаем активные ордера
                active_orders = await conn.fetchval(
                    "SELECT COUNT(*) FROM ccxt_orders WHERE status IN ('open', 'pending', 'partial')"
                )
                
                return {
                    'status': 'healthy',
                    'total_orders': total_orders or 0,
                    'active_orders': active_orders or 0,
                    'connection_pool_size': self.pool.get_size(),
                    'connection_pool_free': self.pool.get_size() - self.pool.get_busy_size()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }