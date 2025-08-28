# src/infrastructure/repositories/order_books_repository.py
from typing import List, Dict, Optional
from domain.entities.order_book import OrderBook

class InMemoryOrderBooksRepository:
    """
    In-memory repository for storing OrderBook entities.
    """
    def __init__(self, max_size: int = 100):
        self._storage: Dict[str, OrderBook] = {}
        self.max_size = max_size

    def save(self, order_book: OrderBook):
        """Saves an order book for a symbol."""
        self._storage[order_book.symbol] = order_book
        # Simple mechanism to cap size
        if len(self._storage) > self.max_size:
            # Remove the oldest entry (FIFO)
            oldest_key = next(iter(self._storage))
            del self._storage[oldest_key]

    def get_by_symbol(self, symbol: str) -> Optional[OrderBook]:
        """Retrieves the last known order book for a symbol."""
        return self._storage.get(symbol)

    def get_all(self) -> List[OrderBook]:
        """Returns all stored order books."""
        return list(self._storage.values())

    def clear(self):
        """Clears the repository."""
        self._storage.clear()
