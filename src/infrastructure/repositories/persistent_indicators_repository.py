# src/infrastructure/repositories/persistent_indicators_repository.py
from .indicators_repository import InMemoryIndicatorsRepository
from ..database.postgres_provider import PostgresPersistenceProvider

class PersistentIndicatorsRepository(InMemoryIndicatorsRepository):
    def __init__(self, db_provider: PostgresPersistenceProvider, max_size_per_symbol: int = 1000):
        super().__init__()
        self._db = db_provider

    async def flush(self):
        await self._db.bulk_save_indicators(self.get_all())
