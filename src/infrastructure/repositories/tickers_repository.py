import json
import os
import pandas as pd
from typing import List, Dict
from domain.entities.ticker import Ticker


class InMemoryTickerRepository:
    def __init__(self, max_size: int = 1000, dump_file: str = "tickers_dump.json"):
        self.tickers = []
        self.max_size = max_size
        self.dump_file = dump_file

        # 🆕 Кеши для оптимизации
        self._last_n_cache = {}  # Кеш для get_last_n
        self._cache_valid_size = 0  # Размер когда кеш был создан

    def save(self, ticker: Ticker):
        """Оптимизированное сохранение"""
        self.tickers.append(ticker)

        # Очищаем кеш при изменении размера
        if len(self.tickers) != self._cache_valid_size:
            self._last_n_cache.clear()
            self._cache_valid_size = len(self.tickers)

        # Ограничиваем размер
        if len(self.tickers) > self.max_size:
            # Удаляем старые записи батчами для производительности
            remove_count = self.max_size // 10  # Удаляем 10%
            self.tickers = self.tickers[remove_count:]

    def get_last_n(self, n: int) -> List[Ticker]:
        """🚀 КЕШИРОВАННОЕ получение последних N тикеров"""

        # Проверяем кеш
        cache_key = f"last_{n}"
        current_size = len(self.tickers)

        if cache_key in self._last_n_cache and current_size == self._cache_valid_size:
            return self._last_n_cache[cache_key]

        # Создаем результат и кешируем
        result = self.tickers[-n:] if len(self.tickers) >= n else self.tickers.copy()
        self._last_n_cache[cache_key] = result
        self._cache_valid_size = current_size

        return result