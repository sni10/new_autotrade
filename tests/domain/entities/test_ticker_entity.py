# tests/test_ticker_entity.py
import unittest
import time
import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.domain.entities.ticker import Ticker

class TestTickerEntity(unittest.TestCase):

    def setUp(self):
        """Настройка полного тестового словаря для Ticker."""
        self.full_ticker_data = {
            "symbol": "BTC/USDT",
            "timestamp": int(time.time() * 1000),
            "datetime": "2023-10-27T11:00:00.000Z",
            "high": 61000.0,
            "low": 59000.0,
            "bid": 60000.0,
            "bidVolume": 1.5,
            "ask": 60001.0,
            "askVolume": 1.2,
            "vwap": 60100.0,
            "open": 59500.0,
            "close": 60500.0,
            "last": 60500.0,
            "previousClose": 59400.0,
            "change": 1000.0,
            "percentage": 1.68,
            "average": 60000.0,
            "baseVolume": 1000.0,
            "quoteVolume": 60100000.0,
            "info": {"exchange_specific": "value"}
        }

    def test_full_creation_from_dict(self):
        """Тест: Сущность Ticker корректно создается со всеми полями."""
        ticker = Ticker.from_dict(self.full_ticker_data)
        
        self.assertIsInstance(ticker, Ticker)
        self.assertEqual(ticker.symbol, self.full_ticker_data['symbol'])
        self.assertEqual(ticker.vwap, self.full_ticker_data['vwap'])
        self.assertEqual(ticker.quoteVolume, self.full_ticker_data['quoteVolume'])
        self.assertDictEqual(ticker.info, self.full_ticker_data['info'])
        
        print(f"\nOK: test_full_creation_from_dict for Ticker passed.")

    def test_full_serialization_to_dict(self):
        """Тест: Метод to_dict() корректно сериализует все поля сущности."""
        ticker = Ticker.from_dict(self.full_ticker_data)
        # Добавляем кастомное поле, чтобы проверить его сериализацию
        ticker.update_signals({'macd': 123})
        
        serialized_data = ticker.to_dict()
        
        # Сравниваем исходные данные
        for key, value in self.full_ticker_data.items():
            self.assertEqual(serialized_data[key], value)
            
        # Проверяем добавленное поле
        self.assertIn('signals', serialized_data)
        self.assertEqual(serialized_data['signals']['macd'], 123)
        
        print(f"OK: test_full_serialization_to_dict for Ticker passed.")

    def test_update_signals(self):
        """Тест: Метод update_signals корректно добавляет данные индикаторов."""
        ticker = Ticker.from_dict(self.full_ticker_data)
        self.assertDictEqual(ticker.signals, {})
        
        first_update = {'macd': 100, 'rsi': 70}
        ticker.update_signals(first_update)
        self.assertDictEqual(ticker.signals, first_update)
        
        second_update = {'rsi': 75, 'sma': 50000}
        ticker.update_signals(second_update)
        
        expected_signals = {'macd': 100, 'rsi': 75, 'sma': 50000}
        self.assertDictEqual(ticker.signals, expected_signals)
        print(f"OK: test_update_signals for Ticker passed.")

if __name__ == '__main__':
    unittest.main()
