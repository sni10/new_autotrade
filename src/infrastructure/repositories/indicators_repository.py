# src/infrastructure/repositories/indicators_repository.py
from typing import List, Dict, Optional
from src.domain.entities.indicator_data import IndicatorData

class InMemoryIndicatorsRepository:
    """
    In-memory repository for storing IndicatorData entities.
    Caches the latest indicator data for each symbol.
    """
    def __init__(self):
        self._storage: Dict[str, IndicatorData] = {}

    def save(self, indicator_data: IndicatorData):
        """Saves or updates indicator data for a symbol."""
        self._storage[indicator_data.symbol] = indicator_data

    def get_by_symbol(self, symbol: str) -> Optional[IndicatorData]:
        """Retrieve the latest indicator data for a given symbol."""
        return self._storage.get(symbol)

    def get_all(self) -> List[IndicatorData]:
        """Returns all stored indicator data."""
        return list(self._storage.values())

    def clear(self):
        """Clears the repository."""
        self._storage.clear()
