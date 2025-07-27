import pytest
import time

from src.domain.entities.order_book import OrderBook, OrderBookLevel


class TestOrderBookLevel:
    """Тесты для OrderBookLevel"""
    
    def test_create_order_book_level(self):
        """Тест создания уровня order book"""
        level = OrderBookLevel(price=45000.0, volume=1.5)
        
        assert level.price == 45000.0
        assert level.volume == 1.5


class TestOrderBook:
    """Тесты для OrderBook"""
    
    def test_create_order_book_basic(self):
        """Тест создания базового order book"""
        timestamp = int(time.time() * 1000)
        
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=timestamp,
            bids=[[45000.0, 1.5], [44999.0, 2.0]],
            asks=[[45001.0, 1.2], [45002.0, 1.8]]
        )
        
        assert order_book.symbol == "BTCUSDT"
        assert order_book.timestamp == timestamp
        assert len(order_book.bids) == 2
        assert len(order_book.asks) == 2
        assert order_book.bids[0].price == 45000.0
        assert order_book.bids[0].volume == 1.5
    
    def test_best_bid_ask(self):
        """Тест получения лучших цен"""
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=int(time.time() * 1000),
            bids=[[45000.0, 1.5], [44999.0, 2.0]],
            asks=[[45001.0, 1.2], [45002.0, 1.8]]
        )
        
        assert order_book.best_bid == 45000.0
        assert order_book.best_ask == 45001.0
    
    def test_spread_calculation(self):
        """Тест расчета спреда"""
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=int(time.time() * 1000),
            bids=[[45000.0, 1.5]],
            asks=[[45002.0, 1.2]]
        )
        
        assert order_book.spread == 2.0  # 45002 - 45000
        
        spread_percent = order_book.spread_percent
        expected_percent = (2.0 / 45000.0) * 100
        assert abs(spread_percent - expected_percent) < 0.0001
    
    def test_empty_order_book(self):
        """Тест пустого order book"""
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=int(time.time() * 1000),
            bids=[],
            asks=[]
        )
        
        assert order_book.best_bid is None
        assert order_book.best_ask is None
        assert order_book.spread is None
        assert order_book.spread_percent is None
    
    def test_volume_calculations(self):
        """Тест расчетов объемов"""
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=int(time.time() * 1000),
            bids=[[45000.0, 3.0], [44999.0, 2.0]],
            asks=[[45001.0, 1.0], [45002.0, 1.0]]
        )
        
        assert order_book.total_bid_volume == 5.0  # 3.0 + 2.0
        assert order_book.total_ask_volume == 2.0  # 1.0 + 1.0
        
        # Volume imbalance: (5.0 - 2.0) / (5.0 + 2.0) * 100 = 42.857%
        expected_imbalance = ((5.0 - 2.0) / 7.0) * 100
        assert abs(order_book.volume_imbalance - expected_imbalance) < 0.001
    
    def test_get_levels_in_range(self):
        """Тест получения уровней в диапазоне"""
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=int(time.time() * 1000),
            bids=[[45000.0, 1.5], [44500.0, 2.0]],  # Второй далеко (1.1% от mid price)
            asks=[[45001.0, 1.2], [45500.0, 1.8]]   # Второй далеко (1.1% от mid price)
        )
        
        # Mid price = (45000 + 45001) / 2 = 45000.5
        # 1% = 450.005, диапазон: 44550.495 - 45450.505
        # 44500.0 < 44550.495 (вне диапазона), 45500.0 > 45450.505 (вне диапазона)
        levels = order_book.get_levels_in_range(1.0)
        
        # Первые уровни должны попасть в диапазон, вторые - нет
        assert len(levels['bids']) == 1  # Только 45000.0
        assert len(levels['asks']) == 1  # Только 45001.0
        assert levels['bids'][0].price == 45000.0
        assert levels['asks'][0].price == 45001.0
    
    def test_to_dict(self):
        """Тест сериализации в словарь"""
        timestamp = int(time.time() * 1000)
        
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=timestamp,
            bids=[[45000.0, 1.5]],
            asks=[[45001.0, 1.2]]
        )
        
        data = order_book.to_dict()
        
        assert data['symbol'] == "BTCUSDT"
        assert data['timestamp'] == timestamp
        assert data['bids'] == [[45000.0, 1.5]]
        assert data['asks'] == [[45001.0, 1.2]]
        assert data['spread'] == 1.0
        assert 'spread_percent' in data
        assert 'volume_imbalance' in data
    
    def test_from_dict(self):
        """Тест десериализации из словаря"""
        timestamp = int(time.time() * 1000)
        
        data = {
            'symbol': 'BTCUSDT',
            'timestamp': timestamp,
            'bids': [[45000.0, 1.5]],
            'asks': [[45001.0, 1.2]]
        }
        
        order_book = OrderBook.from_dict(data)
        
        assert order_book.symbol == "BTCUSDT"
        assert order_book.timestamp == timestamp
        assert len(order_book.bids) == 1
        assert len(order_book.asks) == 1
        assert order_book.bids[0].price == 45000.0
        assert order_book.asks[0].price == 45001.0
    
    def test_json_serialization(self):
        """Тест JSON сериализации"""
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=int(time.time() * 1000),
            bids=[[45000.0, 1.5]],
            asks=[[45001.0, 1.2]]
        )
        
        json_str = order_book.to_json()
        assert isinstance(json_str, str)
        assert "BTCUSDT" in json_str
        
        # Тест обратной конвертации
        restored_order_book = OrderBook.from_json(json_str)
        assert restored_order_book.symbol == order_book.symbol
        assert restored_order_book.timestamp == order_book.timestamp
    
    def test_string_representation(self):
        """Тест строкового представления"""
        order_book = OrderBook(
            symbol="BTCUSDT",
            timestamp=int(time.time() * 1000),
            bids=[[45000.0, 1.5], [44999.0, 2.0]],
            asks=[[45001.0, 1.2], [45002.0, 1.8]]
        )
        
        str_repr = str(order_book)
        assert "BTCUSDT" in str_repr
        assert "spread" in str_repr
        assert "2x2" in str_repr  # 2 bids x 2 asks