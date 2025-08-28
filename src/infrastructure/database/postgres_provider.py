# src/infrastructure/database/postgres_provider.py
import asyncpg
import logging
import json
from typing import List, Dict, Any
from domain.entities.deal import Deal
from domain.entities.order import Order
from domain.entities.ticker import Ticker
from domain.entities.order_book import OrderBook
from domain.entities.indicator_data import IndicatorData
from domain.entities.currency_pair import CurrencyPair

logger = logging.getLogger(__name__)

class PostgresPersistenceProvider:
    def __init__(self, db_config: Dict[str, Any]):
        self._db_config = db_config
        self._pool = None

    async def connect(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(**self._db_config)
            logger.info("Успешное подключение к PostgreSQL.")

    async def close(self):
        if self._pool:
            await self._pool.close()

    async def execute_schema(self, schema_path: str):
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        async with self._pool.acquire() as connection:
            await connection.execute(schema_sql)

    # --- Deals ---
    async def load_all_deals(self, currency_pairs: Dict[str, CurrencyPair], orders_map: Dict[int, Order]) -> List[Deal]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM deals ORDER BY created_at ASC")
        deals = []
        for row in rows:
            pair = currency_pairs.get(row['symbol'])
            if pair:
                deals.append(Deal.from_dict(dict(row), pair, orders_map))
        return deals

    async def bulk_save_deals(self, deals: List[Deal]):
        if not deals: return
        query = """
            INSERT INTO deals (deal_id, symbol, status, buy_order_id, sell_order_id, created_at, closed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (deal_id) DO UPDATE SET
                status = EXCLUDED.status, sell_order_id = EXCLUDED.sell_order_id, closed_at = EXCLUDED.closed_at;
        """
        data = [(d.deal_id, d.currency_pair.symbol, d.status, 
                 d.buy_order.order_id if d.buy_order else None, 
                 d.sell_order.order_id if d.sell_order else None, 
                 d.created_at, d.closed_at) for d in deals]
        async with self._pool.acquire() as conn:
            await conn.executemany(query, data)

    # --- Orders ---
    async def load_all_orders(self) -> List[Order]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT data FROM orders ORDER BY created_at ASC")
        return [Order.from_dict(json.loads(row['data'])) for row in rows]

    async def bulk_save_orders(self, orders: List[Order]):
        if not orders: return
        query = """
            INSERT INTO orders (order_id, exchange_id, deal_id, symbol, side, order_type, status, created_at, last_update, data)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (order_id) DO UPDATE SET
                status = EXCLUDED.status, last_update = EXCLUDED.last_update, data = EXCLUDED.data;
        """
        data = [(o.order_id, o.exchange_id, o.deal_id, o.symbol, o.side, o.order_type, o.status, o.created_at, o.last_update, json.dumps(o.to_dict())) for o in orders]
        async with self._pool.acquire() as conn:
            await conn.executemany(query, data)

    # --- Tickers ---
    async def bulk_save_tickers(self, tickers: List[Ticker]):
        if not tickers: return
        query = "INSERT INTO tickers_history (symbol, timestamp, last_price, data) VALUES ($1, $2, $3, $4) ON CONFLICT (symbol, timestamp) DO NOTHING;"
        data = [(t.symbol, t.timestamp, t.last, json.dumps(t.to_dict())) for t in tickers]
        async with self._pool.acquire() as conn:
            await conn.executemany(query, data)

    # --- Order Books ---
    async def bulk_save_order_books(self, order_books: List[OrderBook]):
        if not order_books: return
        query = "INSERT INTO order_books_history (symbol, timestamp, data) VALUES ($1, $2, $3) ON CONFLICT (symbol, timestamp) DO NOTHING;"
        data = [(ob.symbol, ob.timestamp, json.dumps(ob.to_dict())) for ob in order_books]
        async with self._pool.acquire() as conn:
            await conn.executemany(query, data)

    # --- Indicators ---
    async def bulk_save_indicators(self, indicators: List[IndicatorData]):
        if not indicators: return
        query = "INSERT INTO indicators_history (symbol, timestamp, values) VALUES ($1, $2, $3) ON CONFLICT (symbol, timestamp) DO NOTHING;"
        data = [(i.symbol, i.timestamp, json.dumps(i.values)) for i in indicators]
        async with self._pool.acquire() as conn:
            await conn.executemany(query, data)