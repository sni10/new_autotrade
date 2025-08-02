# src/infrastructure/repositories/persistent_deals_repository.py
from typing import Dict
from domain.entities.order import Order
from domain.entities.currency_pair import CurrencyPair
from .deals_repository import InMemoryDealsRepository
from ..database.postgres_provider import PostgresPersistenceProvider

class PersistentDealsRepository(InMemoryDealsRepository):
    def __init__(self, db_provider: PostgresPersistenceProvider):
        super().__init__()
        self._db = db_provider

    async def load(self, currency_pairs: Dict[str, CurrencyPair], orders_map: Dict[int, Order]):
        deals_from_db = await self._db.load_all_deals(currency_pairs, orders_map)
        for deal in deals_from_db:
            self.save(deal)

    async def flush(self):
        await self._db.bulk_save_deals(self.get_all())
