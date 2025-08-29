"""Repository for storing tickers in memory with optional persistence."""

import json
import os
from typing import List

from domain.entities.ticker import Ticker


class InMemoryTickerRepository:
    """In-memory repository for tickers with caching and persistence."""

    def __init__(
        self,
        max_size: int = 1000,
        dump_file: str = "tickers_dump.json",
    ):
        self.tickers: List[Ticker] = []
        self.max_size = max_size
        self.dump_file = dump_file

        # 🆕 Кеши для оптимизации
        self._last_n_cache: dict = {}  # Кеш для get_last_n
        self._cache_valid_size = 0  # Размер когда кеш был создан

        # Загружаем тикеры из файла, если он существует
        self.load_from_file()

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

        if (
            cache_key in self._last_n_cache
            and current_size == self._cache_valid_size
        ):
            return self._last_n_cache[cache_key]

        # Создаем результат и кешируем
        if len(self.tickers) >= n:
            result = self.tickers[-n:]
        else:
            result = self.tickers.copy()
        self._last_n_cache[cache_key] = result
        self._cache_valid_size = current_size

        return result

    def dump_to_file(self) -> None:
        """Сохраняет тикеры в файл."""
        with open(self.dump_file, "w", encoding="utf-8") as f:
            json.dump(
                [t.to_dict() for t in self.tickers],
                f,
                ensure_ascii=False,
                indent=2,
            )

    def load_from_file(self) -> None:
        """Загружает тикеры из файла, если он существует."""
        if not os.path.exists(self.dump_file):
            return
        try:
            with open(self.dump_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
        self.tickers = [Ticker.from_dict(item) for item in data]
        # Инвалидация кеша после загрузки
        self._last_n_cache.clear()
        self._cache_valid_size = len(self.tickers)
