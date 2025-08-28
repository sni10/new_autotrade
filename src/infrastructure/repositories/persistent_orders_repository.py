# src/infrastructure/repositories/persistent_orders_repository.py
from .orders_repository import InMemoryOrdersRepository
from ..database.postgres_provider import PostgresPersistenceProvider

class PersistentOrdersRepository(InMemoryOrdersRepository):
    def __init__(self, db_provider: PostgresPersistenceProvider, max_orders: int = 10000):
        super().__init__(max_orders)
        self._db = db_provider

    async def load(self):
        orders_from_db = await self._db.load_all_orders()
        for order in orders_from_db:
            self.save(order)

    async def flush(self):
        await self._db.bulk_save_orders(self.get_all())
