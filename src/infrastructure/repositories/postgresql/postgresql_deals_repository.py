# infrastructure/repositories/postgresql/postgresql_deals_repository.py

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from src.domain.entities.deal import Deal
from src.domain.entities.order import Order
from src.domain.repositories.i_deals_repository import IDealsRepository
from src.infrastructure.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PostgreSQLDealsRepository(IDealsRepository):
    """
    PostgreSQL реализация репозитория для хранения сделок.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def save_deal(self, deal: Deal) -> None:
        """Сохраняет или обновляет сделку в базе данных."""
        query = """
            INSERT INTO deals (
                id, symbol, status, buy_order, sell_order, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                buy_order = EXCLUDED.buy_order,
                sell_order = EXCLUDED.sell_order,
                updated_at = EXCLUDED.updated_at;
        """
        params = (
            deal.deal_id,
            deal.currency_pair.symbol,
            deal.status,
            json.dumps(deal.buy_order.to_dict()) if deal.buy_order else None,
            json.dumps(deal.sell_order.to_dict()) if deal.sell_order else None,
            deal.created_at,
            datetime.now()
        )
        try:
            await self.db_manager.execute_command(query, params)
            logger.info(f"Deal {deal.deal_id} saved to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to save deal {deal.deal_id} to PostgreSQL: {e}")
            raise

    async def get_deal(self, deal_id: str) -> Optional[Deal]:
        query = "SELECT * FROM deals WHERE id = $1;"
        try:
            result = await self.db_manager.execute_query(query, (deal_id,))
            if result:
                return self._map_row_to_deal(result[0])
        except Exception as e:
            logger.error(f"Failed to get deal {deal_id} from PostgreSQL: {e}")
        return None

    async def get_all_deals(self) -> List[Deal]:
        query = "SELECT * FROM deals;"
        deals = []
        try:
            result = await self.db_manager.execute_query(query)
            if result:
                deals = [self._map_row_to_deal(row) for row in result]
        except Exception as e:
            logger.error(f"Failed to get all deals from PostgreSQL: {e}")
        return deals

    def _map_row_to_deal(self, row: Dict[str, Any]) -> Deal:
        """Преобразует строку из базы данных в объект Deal."""
        buy_order = Order.from_dict(json.loads(row['buy_order'])) if row['buy_order'] else None
        sell_order = Order.from_dict(json.loads(row['sell_order'])) if row['sell_order'] else None
        
        # This is a simplified mapping. You might need to fetch currency_pair from another table or have its info in the deal table
        from src.domain.entities.currency_pair import CurrencyPair
        currency_pair = CurrencyPair(row['symbol'])

        deal = Deal(
            deal_id=row['id'],
            currency_pair=currency_pair,
            status=row['status'],
            buy_order=buy_order,
            sell_order=sell_order,
            created_at=row['created_at']
        )
        deal.updated_at = row['updated_at']
        return deal