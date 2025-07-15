# tests/domain/entities/test_order_book.py
import unittest
import time
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities.order_book import OrderBook

class TestOrderBook(unittest.TestCase):

    def setUp(self):
        """Настройка тестовых данных."""
        self.raw_data = {
            "symbol": "BTC/USDT",
            "timestamp": int(time.time() * 1000),
            "datetime": "2023-10-27T10:00:00.000Z",
            "nonce": 12345,
            "bids": [[60000.0, 1.5], [59999.5, 2.0]],
            "asks": [[60001.0, 1.2], [60001.5, 1.8]]
        }

    def test_creation_from_dict(self):
        """Тест: Сущность OrderBook корректно создается из словаря."""
        order_book = OrderBook.from_dict(self.raw_data)
        
        self.assertIsInstance(order_book, OrderBook)
        self.assertEqual(order_book.symbol, self.raw_data["symbol"])
        self.assertEqual(order_book.timestamp, self.raw_data["timestamp"])
        self.assertEqual(order_book.datetime, self.raw_data["datetime"])
        self.assertEqual(order_book.nonce, self.raw_data["nonce"])
        self.assertEqual(order_book.bids, self.raw_data["bids"])
        self.assertEqual(order_book.asks, self.raw_data["asks"])
        
        print(f"\nOK: test_creation_from_dict for OrderBook passed.")

    def test_serialization_to_dict(self):
        """Тест: Метод to_dict() корректно сериализует сущность."""
        order_book = OrderBook.from_dict(self.raw_data)
        serialized_data = order_book.to_dict()
        
        self.assertEqual(serialized_data, self.raw_data)
        print(f"OK: test_serialization_to_dict for OrderBook passed.")

    def test_dict_to_dict_consistency(self):
        """Тест: Cущность, созданная из словаря и снова сериализованная, идентична исходному словарю."""
        order_book = OrderBook.from_dict(self.raw_data)
        re_serialized_data = order_book.to_dict()
        
        self.assertDictEqual(self.raw_data, re_serialized_data)
        print(f"OK: test_dict_to_dict_consistency for OrderBook passed.")

    def test_creation_with_missing_optional_fields(self):
        """Тест: Сущность корректно создается, если отсутствуют опциональные поля."""
        minimal_data = {
            "symbol": "ETH/USDT",
            "timestamp": int(time.time() * 1000),
            "bids": [[3000.0, 10.0]],
            "asks": [[3001.0, 12.0]]
        }
        order_book = OrderBook.from_dict(minimal_data)
        
        self.assertEqual(order_book.symbol, minimal_data["symbol"])
        self.assertIsNone(order_book.datetime)
        self.assertIsNone(order_book.nonce)
        print(f"OK: test_creation_with_missing_optional_fields for OrderBook passed.")

if __name__ == '__main__':
    unittest.main()
