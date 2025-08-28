# src/infrastructure/repositories/persistent_order_books_repository.py
from .order_books_repository import InMemoryOrderBooksRepository
from ..database.postgres_provider import PostgresPersistenceProvider

class PersistentOrderBooksRepository(InMemoryOrderBooksRepository):
    def __init__(self, db_provider: PostgresPersistenceProvider, max_size_per_symbol: int = 10):
        super().__init__(max_size_per_symbol)
        self._db = db_provider

    async def flush(self):
        await self._db.bulk_save_order_books(self.get_all())
