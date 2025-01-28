import json
import os
import pandas as pd
from typing import List, Dict
from domain.entities.ticker import Ticker


class InMemoryTickerRepository:
    def __init__(self, max_size: int = 1000, dump_file: str = "tickers_dump.json"):
        self.tickers = []  # Список тикеров
        self.max_size = max_size  # Лимит хранения в памяти
        self.dump_file = dump_file  # Файл для периодического сохранения

    def save(self, ticker: Ticker):
        """Сохраняем тикер в память, сбрасываем в файл при превышении лимита"""
        self.tickers.append(ticker)
        if len(self.tickers) >= self.max_size:
            self.dump_to_file()

    def get_last_n(self, n: int) -> List[Ticker]:
        """Возвращает последние `n` тикеров"""
        return self.tickers[-n:]

    def dump_to_file(self):
        """Сохранение данных в JSON-файл"""
        if not self.tickers:
            return

        with open(self.dump_file, "a") as f:
            for ticker in self.tickers:
                f.write(json.dumps(ticker.to_dict()) + "\n")

        self.tickers.clear()  # Очистка памяти

    def load_from_file(self):
        """Загрузка тикеров из файла"""
        if not os.path.exists(self.dump_file):
            return

        with open(self.dump_file, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                self.tickers.append(Ticker(data))

    def to_dataframe(self) -> pd.DataFrame:
        """Конвертирует тикеры в DataFrame"""
        return pd.DataFrame([t.to_dict() for t in self.tickers])
