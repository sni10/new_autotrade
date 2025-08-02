# src/infrastructure/repositories/persistent_tickers_repository.py
from .tickers_repository import InMemoryTickerRepository
from ..database.postgres_provider import PostgresPersistenceProvider

class PersistentTickersRepository(InMemoryTickerRepository):
    def __init__(self, db_provider: PostgresPersistenceProvider, max_size: int = 1000):
        super().__init__(max_size)
        self._db = db_provider

    async def flush(self):
        await self._db.bulk_save_tickers(self.tickers)
