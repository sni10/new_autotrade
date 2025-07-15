# tests/domain/entities/test_indicator_data.py
import unittest
import time
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities.indicator_data import IndicatorData

class TestIndicatorData(unittest.TestCase):

    def setUp(self):
        """Настройка тестовых данных."""
        self.raw_data = {
            "symbol": "BTC/USDT",
            "timestamp": int(time.time() * 1000),
            "values": {
                "macd": 150.5,
                "macdsignal": 145.0,
                "macdhist": 5.5,
                "rsi_14": 65.7
            }
        }

    def test_creation_from_dict(self):
        """Тест: Сущность IndicatorData корректно создается из словаря."""
        indicator_data = IndicatorData.from_dict(self.raw_data)
        
        self.assertIsInstance(indicator_data, IndicatorData)
        self.assertEqual(indicator_data.symbol, self.raw_data["symbol"])
        self.assertEqual(indicator_data.timestamp, self.raw_data["timestamp"])
        self.assertDictEqual(indicator_data.values, self.raw_data["values"])
        
        print(f"\nOK: test_creation_from_dict for IndicatorData passed.")

    def test_serialization_to_dict(self):
        """Тест: Метод to_dict() корректно сериализует сущность."""
        indicator_data = IndicatorData.from_dict(self.raw_data)
        serialized_data = indicator_data.to_dict()
        
        self.assertEqual(serialized_data, self.raw_data)
        print(f"OK: test_serialization_to_dict for IndicatorData passed.")

    def test_dict_to_dict_consistency(self):
        """Тест: Cущность, созданная из словаря и снова сериализованная, идентична исходному словарю."""
        indicator_data = IndicatorData.from_dict(self.raw_data)
        re_serialized_data = indicator_data.to_dict()
        
        self.assertDictEqual(self.raw_data, re_serialized_data)
        print(f"OK: test_dict_to_dict_consistency for IndicatorData passed.")

    def test_creation_with_empty_values(self):
        """Тест: Сущность корректно создается с пустым словарем values."""
        minimal_data = {
            "symbol": "ETH/USDT",
            "timestamp": int(time.time() * 1000),
            "values": {}
        }
        indicator_data = IndicatorData.from_dict(minimal_data)
        
        self.assertEqual(indicator_data.symbol, minimal_data["symbol"])
        self.assertDictEqual(indicator_data.values, {})
        print(f"OK: test_creation_with_empty_values for IndicatorData passed.")

if __name__ == '__main__':
    unittest.main()
